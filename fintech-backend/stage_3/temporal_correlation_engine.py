# =====================================================
# ENGINE 3.T3 — TEMPORAL CORRELATION ENGINE
# =====================================================
# The most mathematically sophisticated engine in H2.
# Transforms independent row samples into temporally
# coherent time series using:
#
#   1. AR(1) Autocorrelation
#   2. GARCH(1,1) Volatility Clustering
#   3. Ornstein-Uhlenbeck Mean-Reversion
#   4. Geometric Brownian Motion (random walk with drift)
#   5. Seasonal modulation
#   6. Regime-based parameter shifting
#
# Each continuous variable gets its own temporal model
# selected from the autocorrelation config.
#
# v2.0 — Bulletproof Edition:
#   - Domain-aware price/value clamping
#   - GARCH normalized residual feedback (no explosion)
#   - Zero-value floor enforcement per variable archetype
#   - IQR rescale with capped scale factor
#   - Per-step sanity checks on all models
#
# Pure NumPy. No scipy. No external dependencies.
# =====================================================

import numpy as np
from typing import Any, Dict, Optional, Tuple


# ═══════════════════════════════════════════════════════
# DOMAIN-AWARE VALUE BOUNDS
# ═══════════════════════════════════════════════════════
# These prevent any temporal model from producing values
# outside physically/financially meaningful ranges.
# The key insight: we clamp based on WHAT the variable
# represents, not just on relative deviations.

_VARIABLE_BOUNDS = {
    # (keyword_in_name): (absolute_min, absolute_max, min_positive_floor)
    # Order matters — more specific entries FIRST (first match wins)
    "purchase_price":(10.0,     500_000,     10.0),   # Stock purchase prices ($10+ minimum)
    "current_price": (1.0,      500_000,     1.0),    # Stock current prices
    "price_usd":     (0.001,    500_000,     0.01),   # Crypto prices (altcoins can be cheap)
    "price":         (0.01,     500_000,     0.01),   # Generic price fallback
    "market_value":  (0.0,      1e10,        0.0),
    "amount":        (0.0,      1e9,         0.0),
    "fee":           (0.0,      10_000,      0.0),    # Fees capped at $10K
    "balance":       (-1e8,     1e10,        0.0),
    "volume":        (0.0,      1e9,         0.0),
    "quantity":      (0.0,      1e7,         0.0),
    "rate":          (0.0,      100.0,       0.0),
    "score":         (0.0,      1000.0,      0.0),
    "emi":           (0.0,      1e7,         0.0),
    "principal":     (0.0,      1e9,         0.0),
    "revenue":       (-1e9,     1e12,        0.0),
    "count":         (0.0,      1e8,         0.0),
}


def _get_variable_bounds(var_name: str) -> Tuple[float, float, float]:
    """Get domain-aware bounds for a variable by matching its name."""
    name_lower = var_name.lower()
    for keyword, bounds in _VARIABLE_BOUNDS.items():
        if keyword in name_lower:
            return bounds
    # Default: allow wide range but nothing astronomical
    return (-1e10, 1e10, 0.0)


def _clamp_value(value: float, vmin: float, vmax: float) -> float:
    """Clamp a single value to [vmin, vmax]."""
    return max(vmin, min(value, vmax))


def _clamp_series(series: np.ndarray, var_name: str) -> np.ndarray:
    """Apply domain-aware clamping to an entire series."""
    vmin, vmax, _ = _get_variable_bounds(var_name)
    return np.clip(series, vmin, vmax)


# ═══════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════

def apply_temporal_correlations(
    columns: Dict[str, np.ndarray],
    temporal_model: Dict[str, Any],
    regime_multipliers: np.ndarray,
    seasonal_factors: np.ndarray,
    rng: np.random.Generator,
) -> Dict[str, np.ndarray]:
    """
    Apply temporal autocorrelation and dynamics to all continuous
    columns, transforming i.i.d. samples into realistic time series.

    This is the engine that makes the data look like real financial
    time series when plotted. Without this, the data is just
    noise with a timestamp column.

    Args:
        columns:              Dict of column_name → np.ndarray
        temporal_model:       Compiled temporal model from Stage 2
        regime_multipliers:   (n_periods, 3) from regime engine
        seasonal_factors:     (n_periods,) from calendar engine
        rng:                  Seeded RNG

    Returns:
        Updated columns dict with temporally-correlated values.
    """
    autocorrelation_configs = temporal_model.get("autocorrelation", {})
    trend_config = temporal_model.get("trend", {})
    frequency = temporal_model.get("calendar", {}).get("frequency", "monthly")
    n = len(seasonal_factors)

    for var_name, ac_config in autocorrelation_configs.items():
        if var_name not in columns:
            continue

        col = columns[var_name]

        # Skip non-numeric columns
        if col.dtype == object:
            continue

        try:
            col_float = col.astype(float)
        except (ValueError, TypeError):
            continue

        # Skip constant or near-constant columns
        col_std = np.std(col_float)
        if col_std < 1e-10:
            continue

        model_type = ac_config.get("model", "ar1")

        if model_type == "gbm":
            new_col = _apply_gbm(
                col_float, ac_config, regime_multipliers,
                seasonal_factors, trend_config, rng, n, var_name, frequency,
            )
        elif model_type == "ou":
            new_col = _apply_ornstein_uhlenbeck(
                col_float, ac_config, regime_multipliers,
                seasonal_factors, rng, n, var_name,
            )
        elif model_type == "ar1":
            new_col = _apply_ar1(
                col_float, ac_config, regime_multipliers,
                seasonal_factors, trend_config, rng, n, var_name,
            )
        else:
            new_col = _apply_ar1(
                col_float, ac_config, regime_multipliers,
                seasonal_factors, trend_config, rng, n, var_name,
            )

        # Apply GARCH volatility clustering if configured
        if "garch_alpha" in ac_config:
            new_col = _apply_garch_overlay(
                new_col, ac_config, regime_multipliers, rng, n, var_name,
            )

        # ── FINAL DOMAIN CLAMP ──
        new_col = _clamp_series(new_col, var_name)

        columns[var_name] = new_col

    return columns


# ═══════════════════════════════════════════════════════
# MODEL IMPLEMENTATIONS
# ═══════════════════════════════════════════════════════

def _apply_ar1(
    base_samples: np.ndarray,
    config: Dict[str, Any],
    regime_multipliers: np.ndarray,
    seasonal_factors: np.ndarray,
    trend_config: Dict[str, Any],
    rng: np.random.Generator,
    n: int,
    var_name: str = "",
) -> np.ndarray:
    """
    AR(1) autoregressive process with regime and seasonal modulation.

    X_t = φ × X_{t-1} + (1-φ) × μ + σ√(1-φ²) × ε_t

    Where:
        φ = AR(1) coefficient (persistence)
        μ = unconditional mean (from base samples)
        σ = innovation standard deviation
        ε_t = i.i.d. innovation from base_samples (rank-preserved)

    The beauty: we use the base samples (from marginal sampler) as
    the innovation source, so the marginal distribution is preserved
    while temporal structure is imposed.
    """
    phi = config.get("ar1_phi", 0.50)
    phi = max(0.0, min(phi, 0.999))  # Clamp to stationary range

    n_actual = min(n, len(base_samples))
    samples = base_samples[:n_actual].copy()

    # Target statistics from base samples
    mu = np.mean(samples)
    sigma = np.std(samples)
    if sigma < 1e-10:
        sigma = max(abs(mu) * 0.01, 1e-6)

    # Drift per period
    drift = trend_config.get("drift_per_period", 0.0)

    # ── Convert to standardized innovations ──
    innovations = (samples - mu) / sigma

    # ── Build AR(1) process ──
    result = np.zeros(n_actual, dtype=float)
    innovation_scale = np.sqrt(max(0.0, 1.0 - phi ** 2))

    # Initialize with first sample
    result[0] = samples[0]

    # Get domain bounds for per-step clamping
    vmin, vmax, _ = _get_variable_bounds(var_name)

    for t in range(1, n_actual):
        # Regime-adjusted mean and variance
        mean_mult = regime_multipliers[min(t, len(regime_multipliers) - 1), 0] if len(regime_multipliers) > 0 else 1.0
        var_mult = regime_multipliers[min(t, len(regime_multipliers) - 1), 1] if len(regime_multipliers) > 0 else 1.0

        # Cap var_mult to prevent explosion
        var_mult = min(var_mult, 10.0)

        # Trend-adjusted target mean
        target_mu = mu * mean_mult * (1.0 + drift * t)

        # Seasonal modulation
        s_factor = seasonal_factors[min(t, len(seasonal_factors) - 1)] if len(seasonal_factors) > 0 else 1.0

        # AR(1) recursion
        result[t] = (
            phi * result[t - 1] +
            (1.0 - phi) * target_mu +
            sigma * innovation_scale * np.sqrt(var_mult) * innovations[t]
        )

        # Apply seasonal factor (multiplicative)
        result[t] *= s_factor

        # Per-step domain clamp
        result[t] = _clamp_value(result[t], vmin, vmax)

    return result


def _apply_ornstein_uhlenbeck(
    base_samples: np.ndarray,
    config: Dict[str, Any],
    regime_multipliers: np.ndarray,
    seasonal_factors: np.ndarray,
    rng: np.random.Generator,
    n: int,
    var_name: str = "",
) -> np.ndarray:
    """
    Ornstein-Uhlenbeck mean-reverting process.

    dX_t = θ(μ - X_t)dt + σ dW_t

    Discretized:
    X_t = X_{t-1} + θ(μ - X_{t-1}) + σ × ε_t

    Used for variables that naturally revert to an equilibrium:
    bank balances, credit scores, interest rate spreads.
    """
    theta = config.get("theta", 0.10)  # Mean-reversion speed
    sigma_scale = config.get("sigma_scale", 0.15)

    n_actual = min(n, len(base_samples))
    samples = base_samples[:n_actual].copy()

    mu = np.mean(samples)
    sigma = np.std(samples) * sigma_scale
    if sigma < 1e-10:
        sigma = max(abs(mu) * 0.01, 1e-6)

    result = np.zeros(n_actual, dtype=float)
    result[0] = samples[0]

    vmin, vmax, _ = _get_variable_bounds(var_name)

    for t in range(1, n_actual):
        # Regime modulation
        mean_mult = regime_multipliers[min(t, len(regime_multipliers) - 1), 0] if len(regime_multipliers) > 0 else 1.0
        var_mult = regime_multipliers[min(t, len(regime_multipliers) - 1), 1] if len(regime_multipliers) > 0 else 1.0
        var_mult = min(var_mult, 10.0)

        target_mu = mu * mean_mult
        s_factor = seasonal_factors[min(t, len(seasonal_factors) - 1)] if len(seasonal_factors) > 0 else 1.0

        # OU discretization
        innovation = rng.normal(0, 1)
        result[t] = (
            result[t - 1] +
            theta * (target_mu - result[t - 1]) +
            sigma * np.sqrt(var_mult) * innovation
        )

        # Seasonal modulation (multiplicative for mean-reverting)
        result[t] *= s_factor

        # Per-step domain clamp
        result[t] = _clamp_value(result[t], vmin, vmax)

    return result


def _apply_gbm(
    base_samples: np.ndarray,
    config: Dict[str, Any],
    regime_multipliers: np.ndarray,
    seasonal_factors: np.ndarray,
    trend_config: Dict[str, Any],
    rng: np.random.Generator,
    n: int,
    var_name: str = "",
    frequency: str = "monthly",
) -> np.ndarray:
    """
    Geometric Brownian Motion for price-like variables.

    S_t = S_{t-1} × exp((μ - σ²/2)Δt + σ√Δt × ε_t)

    v3.0 — Frequency-aware edition:
      - Step return caps scale with frequency (daily=8%, weekly=12%, monthly=25%)
      - Implied vol caps scale with frequency
      - Tighter relative bounds (S0 × 15 instead of S0 × 100)
      - Higher purchase_price floors for stocks
    """
    drift_annual = config.get("drift_annual", 0.08)
    ar1_phi = config.get("ar1_phi", 0.98)

    n_actual = min(n, len(base_samples))
    samples = base_samples[:n_actual].copy()

    # ── Frequency-aware parameters ──
    # Key insight: a 30% weekly return compounds to 10^7 over 2 years.
    # Real-world max weekly returns: even BTC rarely exceeds 15%/week.
    FREQ_PARAMS = {
        "daily":     {"max_return": 0.08, "max_sigma": 0.12, "vol_cap": 0.60, "range_mult": 5.0},
        "weekly":    {"max_return": 0.12, "max_sigma": 0.25, "vol_cap": 1.00, "range_mult": 10.0},
        "monthly":   {"max_return": 0.25, "max_sigma": 0.50, "vol_cap": 1.50, "range_mult": 15.0},
        "quarterly": {"max_return": 0.40, "max_sigma": 0.80, "vol_cap": 2.00, "range_mult": 20.0},
        "yearly":    {"max_return": 0.60, "max_sigma": 1.20, "vol_cap": 2.50, "range_mult": 30.0},
    }
    fp = FREQ_PARAMS.get(frequency, FREQ_PARAMS["monthly"])
    MAX_STEP_RETURN = fp["max_return"]
    MAX_SIGMA_PER_STEP = fp["max_sigma"]
    VOL_CAP = fp["vol_cap"]
    RANGE_MULT = fp["range_mult"]

    # Use median as starting price (more robust than mean for lognormal)
    S0 = np.median(np.abs(samples))
    if S0 <= 0:
        S0 = np.mean(np.abs(samples)) + 1e-6

    # Get domain-aware bounds
    vmin, vmax, min_floor = _get_variable_bounds(var_name)
    # Relative bounds: S0 × [1/RANGE, RANGE] — tighter than before
    rel_min = max(vmin, S0 / RANGE_MULT)
    rel_max = min(vmax, S0 * RANGE_MULT)

    # Calculate implied volatility from the cross-section
    positive_samples = np.maximum(np.abs(samples), 1e-10)
    log_samples = np.log(positive_samples)
    sigma_implied = np.std(log_samples)
    # Cap implied vol based on frequency
    sigma_implied = max(0.01, min(sigma_implied, VOL_CAP))

    # Per-period parameters
    drift_per_period = trend_config.get("drift_per_period", drift_annual / 252)

    result = np.zeros(n_actual, dtype=float)
    result[0] = S0

    prev_return = 0.0

    for t in range(1, n_actual):
        # Regime modulation
        mean_mult = regime_multipliers[min(t, len(regime_multipliers) - 1), 0] if len(regime_multipliers) > 0 else 1.0
        var_mult = regime_multipliers[min(t, len(regime_multipliers) - 1), 1] if len(regime_multipliers) > 0 else 1.0

        # Cap variance multiplier
        var_mult = min(var_mult, 5.0)

        s_factor = seasonal_factors[min(t, len(seasonal_factors) - 1)] if len(seasonal_factors) > 0 else 1.0

        # Regime-adjusted drift and volatility
        mu_t = drift_per_period * mean_mult
        sigma_t = sigma_implied * np.sqrt(var_mult)

        # Cap per-step volatility (frequency-aware)
        sigma_t = min(sigma_t, MAX_SIGMA_PER_STEP)

        # Innovation with autocorrelated returns (momentum)
        innovation = rng.normal(0, 1)
        log_return = (
            (mu_t - 0.5 * sigma_t ** 2) +
            sigma_t * innovation
        )

        # AR(1) in returns for momentum/mean-reversion
        log_return = ar1_phi * prev_return + (1 - ar1_phi) * log_return + sigma_t * innovation * (1 - ar1_phi)

        # ── CRITICAL: Frequency-aware return cap ──
        log_return = max(-MAX_STEP_RETURN, min(log_return, MAX_STEP_RETURN))
        prev_return = log_return

        # GBM evolution
        result[t] = result[t - 1] * np.exp(log_return)

        # Seasonal modulation (multiplicative)
        result[t] *= s_factor

        # Per-step domain + relative clamp
        result[t] = _clamp_value(result[t], rel_min, rel_max)

    # ── Rescale to match original distribution's range ──
    original_q25 = np.percentile(positive_samples, 25)
    original_q75 = np.percentile(positive_samples, 75)
    result_q25 = np.percentile(result, 25)
    result_q75 = np.percentile(result, 75)

    original_iqr = max(original_q75 - original_q25, 1e-6)
    result_iqr = max(result_q75 - result_q25, 1e-6)

    # Cap the scale factor (tighter cap: 5× instead of 10×)
    scale = original_iqr / result_iqr
    scale = min(scale, 5.0)    # Never scale up more than 5×
    scale = max(scale, 0.2)    # Never scale down more than 5×

    # Scale and shift to match original IQR and median
    original_median = np.median(positive_samples)
    result_median = np.median(result)

    result = (result - result_median) * scale + original_median

    # Final domain clamp after rescale
    result = np.clip(result, vmin, vmax)

    # Ensure no zeros for price-like variables
    if min_floor > 0:
        result = np.maximum(result, min_floor)

    return result


def _apply_garch_overlay(
    series: np.ndarray,
    config: Dict[str, Any],
    regime_multipliers: np.ndarray,
    rng: np.random.Generator,
    n: int,
    var_name: str = "",
) -> np.ndarray:
    """
    GARCH(1,1) volatility clustering overlay.

    σ²_t = ω + α × ε²_{t-1} + β × σ²_{t-1}

    This modulates the innovation magnitudes to create realistic
    volatility clustering. Periods of high volatility are followed
    by more high volatility.

    v2.0 fix: Uses NORMALIZED residuals for the feedback loop
    instead of raw (result[t] - mu), which prevents the positive
    feedback explosion that caused quadrillion-dollar values.
    """
    omega = config.get("garch_omega", 0.000002)
    alpha = config.get("garch_alpha", 0.09)
    beta = config.get("garch_beta", 0.90)

    # Ensure stationarity: alpha + beta < 1
    if alpha + beta >= 1.0:
        total = alpha + beta
        alpha = alpha / total * 0.98
        beta = beta / total * 0.98

    n_actual = min(n, len(series))
    if n_actual < 3:
        return series

    result = series.copy()
    mu = np.mean(series)
    sigma = np.std(series)
    if sigma < 1e-10:
        sigma = max(abs(mu) * 0.01, 1e-6)

    unconditional_var = sigma ** 2

    # Initialize conditional variance at unconditional level
    h_t = unconditional_var
    epsilon_prev_normalized = 0.0  # NORMALIZED residual

    # Domain bounds for clamping
    vmin, vmax, _ = _get_variable_bounds(var_name)

    for t in range(1, n_actual):
        # GARCH recursion for conditional variance
        # Uses NORMALIZED squared residual (epsilon/sigma)² to prevent explosion
        h_t = omega + alpha * (epsilon_prev_normalized ** 2) * unconditional_var + beta * h_t
        h_t = max(h_t, 1e-15)    # Prevent collapse
        h_t = min(h_t, unconditional_var * 25.0)  # Cap at 25× unconditional (5σ events)

        # Regime modulation of volatility
        var_mult = regime_multipliers[min(t, len(regime_multipliers) - 1), 1] if len(regime_multipliers) > 0 else 1.0
        var_mult = min(var_mult, 8.0)

        # Compute volatility ratio: GARCH vol / unconditional vol
        vol_ratio = np.sqrt(h_t * var_mult) / sigma
        vol_ratio = max(0.1, min(vol_ratio, 5.0))  # Clamp extremes

        # Scale the deviation from mean
        deviation = result[t] - mu
        result[t] = mu + deviation * vol_ratio

        # Per-step domain clamp
        result[t] = _clamp_value(result[t], vmin, vmax)

        # Update NORMALIZED epsilon for next iteration
        # This is the critical fix: divide by sigma so the feedback
        # is scale-invariant and doesn't explode
        epsilon_prev_normalized = (result[t] - mu) / sigma

    return result


# ═══════════════════════════════════════════════════════
# TREND APPLICATION
# ═══════════════════════════════════════════════════════

def apply_trend(
    columns: Dict[str, np.ndarray],
    temporal_model: Dict[str, Any],
    n_periods: int,
) -> Dict[str, np.ndarray]:
    """
    Apply global trend component to all continuous columns.
    This is a secondary effect — the primary trend is already
    incorporated in the AR/GBM models. This handles any
    residual trend from the prompt intent.
    """
    trend_config = temporal_model.get("trend", {})
    trend_type = trend_config.get("trend_type", "flat")
    drift = trend_config.get("drift_per_period", 0.0)

    if trend_type == "flat" or abs(drift) < 1e-10:
        return columns

    autocorrelation_configs = temporal_model.get("autocorrelation", {})

    for var_name, ac_config in autocorrelation_configs.items():
        if var_name not in columns:
            continue

        col = columns[var_name]
        if col.dtype == object:
            continue

        try:
            col_float = col.astype(float)
        except (ValueError, TypeError):
            continue

        n_actual = min(n_periods, len(col_float))

        if trend_type == "exponential":
            # Compound growth — cap the maximum growth factor
            growth = np.exp(drift * np.arange(n_actual))
            # Cap exponential growth at 10× over the full series
            growth = np.minimum(growth, 10.0)
            col_float[:n_actual] *= growth
        elif trend_type in ("linear_up", "linear_down"):
            # Linear drift (already handled in AR1/GBM, but reinforce)
            # Only apply a fraction to avoid double-counting
            reinforcement = 0.3
            trend_factor = 1.0 + drift * reinforcement * np.arange(n_actual)
            # Cap trend factor
            trend_factor = np.clip(trend_factor, 0.1, 10.0)
            col_float[:n_actual] *= trend_factor

        # Final domain clamp after trend application
        col_float = _clamp_series(col_float, var_name).astype(float)
        columns[var_name] = col_float

    return columns
