# =====================================================
# TEMPORAL MODEL COMPILER — Horizon 2, Stage 2
# =====================================================
# Compiles the temporal contract (from Stage 1/1.5) into
# a deterministic mathematical temporal model that Stage 3's
# temporal engines consume.
#
# Produces:
#   1. Calendar configuration (frequency, business days, holidays)
#   2. Regime transition matrix (Markov chain parameters)
#   3. Seasonal decomposition coefficients (per-entity)
#   4. Autocorrelation configuration (AR, GARCH, OU, GBM)
#   5. Trend component (drift parameters)
#
# All parameters are grounded in empirical financial data
# characteristics. Pure Python + numpy. No scipy.
# =====================================================

import hashlib
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════
# 1. HOLIDAY CALENDARS — Per Region
# ═══════════════════════════════════════════════════════

HOLIDAY_CALENDARS = {
    "US": {
        "name": "US Federal / NYSE",
        "holidays": [
            # (month, day) — fixed holidays
            (1, 1),   # New Year's Day
            (1, 15),  # MLK Day (approx — 3rd Monday)
            (2, 19),  # Presidents' Day (approx)
            (5, 27),  # Memorial Day (approx)
            (6, 19),  # Juneteenth
            (7, 4),   # Independence Day
            (9, 2),   # Labor Day (approx)
            (10, 14), # Columbus Day (approx)
            (11, 11), # Veterans Day
            (11, 28), # Thanksgiving (approx)
            (12, 25), # Christmas
        ],
        "weekend_days": [5, 6],  # Saturday, Sunday
        "trading_hours": (9, 30, 16, 0),  # 9:30 AM - 4:00 PM ET
    },
    "UK": {
        "name": "UK Bank / LSE",
        "holidays": [
            (1, 1), (4, 18), (4, 21), (5, 5), (5, 26),
            (8, 25), (12, 25), (12, 26),
        ],
        "weekend_days": [5, 6],
        "trading_hours": (8, 0, 16, 30),
    },
    "EU": {
        "name": "ECB / Eurex",
        "holidays": [
            (1, 1), (4, 18), (4, 21), (5, 1), (12, 25), (12, 26),
        ],
        "weekend_days": [5, 6],
        "trading_hours": (9, 0, 17, 30),
    },
    "JP": {
        "name": "TSE / Japanese",
        "holidays": [
            (1, 1), (1, 2), (1, 3), (1, 13), (2, 11), (2, 23),
            (3, 20), (4, 29), (5, 3), (5, 4), (5, 5), (5, 6),
            (7, 21), (8, 11), (9, 15), (9, 23), (10, 13),
            (11, 3), (11, 23), (12, 31),
        ],
        "weekend_days": [5, 6],
        "trading_hours": (9, 0, 15, 0),
    },
    "IN": {
        "name": "NSE / BSE Indian",
        "holidays": [
            (1, 1), (1, 26), (3, 14), (3, 29), (4, 14),
            (5, 1), (8, 15), (8, 26), (10, 2), (10, 24),
            (11, 1), (11, 15), (12, 25),
        ],
        "weekend_days": [5, 6],
        "trading_hours": (9, 15, 15, 30),
    },
    "AU": {
        "name": "ASX Australian",
        "holidays": [
            (1, 1), (1, 26), (4, 18), (4, 21), (4, 25),
            (6, 9), (12, 25), (12, 26),
        ],
        "weekend_days": [5, 6],
        "trading_hours": (10, 0, 16, 0),
    },
    "BR": {
        "name": "B3 / Bovespa Brazilian",
        "holidays": [
            (1, 1), (2, 12), (2, 13), (4, 18), (4, 21),
            (5, 1), (6, 19), (9, 7), (10, 12), (11, 2),
            (11, 15), (11, 20), (12, 25),
        ],
        "weekend_days": [5, 6],
        "trading_hours": (10, 0, 17, 0),
    },
}


# ═══════════════════════════════════════════════════════
# 2. REGIME TRANSITION MATRICES
# ═══════════════════════════════════════════════════════
# Calibrated to approximate real market regime durations.
# P[i,j] = probability of transitioning FROM state i TO state j.
#
# Average regime durations (in periods):
#   Normal:   ~33 periods (1/0.03)
#   Stress:   ~7 periods  (1/0.15)
#   Crisis:   ~5 periods  (1/0.20)
#   Recovery: ~5 periods  (1/0.20)

DEFAULT_REGIME_STATES = ["normal", "stress", "crisis", "recovery"]

DEFAULT_TRANSITION_MATRIX = [
    # From normal:   high persistence, small chance of stress
    [0.970, 0.020, 0.005, 0.005],
    # From stress:   can escalate to crisis or recover
    [0.150, 0.650, 0.150, 0.050],
    # From crisis:   tends to move to recovery
    [0.020, 0.050, 0.800, 0.130],
    # From recovery: tends to normalize
    [0.200, 0.030, 0.010, 0.760],
]

# Per-regime multipliers: [mean_shift, variance_shift, anomaly_rate_mult]
DEFAULT_REGIME_EFFECTS = {
    "normal":   {"mean_mult": 1.00, "variance_mult": 1.00, "anomaly_rate_mult": 1.0},
    "stress":   {"mean_mult": 0.92, "variance_mult": 1.80, "anomaly_rate_mult": 2.0},
    "crisis":   {"mean_mult": 0.70, "variance_mult": 3.50, "anomaly_rate_mult": 4.0},
    "recovery": {"mean_mult": 1.08, "variance_mult": 1.60, "anomaly_rate_mult": 1.5},
}

# Entity-specific regime overrides
ENTITY_REGIME_OVERRIDES = {
    "insurance_claims": {
        "states": ["normal", "elevated", "catastrophe", "aftermath"],
        "transition_matrix": [
            [0.980, 0.015, 0.003, 0.002],
            [0.100, 0.750, 0.120, 0.030],
            [0.010, 0.040, 0.800, 0.150],
            [0.250, 0.020, 0.010, 0.720],
        ],
        "effects": {
            "normal":      {"mean_mult": 1.00, "variance_mult": 1.00, "anomaly_rate_mult": 1.0},
            "elevated":    {"mean_mult": 1.30, "variance_mult": 1.50, "anomaly_rate_mult": 2.0},
            "catastrophe": {"mean_mult": 3.00, "variance_mult": 5.00, "anomaly_rate_mult": 6.0},
            "aftermath":   {"mean_mult": 1.50, "variance_mult": 2.00, "anomaly_rate_mult": 2.5},
        },
    },
    "crypto_trading_log": {
        "states": ["accumulation", "markup", "distribution", "markdown"],
        "transition_matrix": [
            [0.920, 0.060, 0.010, 0.010],
            [0.020, 0.880, 0.080, 0.020],
            [0.010, 0.020, 0.900, 0.070],
            [0.080, 0.010, 0.010, 0.900],
        ],
        "effects": {
            "accumulation": {"mean_mult": 0.95, "variance_mult": 0.80, "anomaly_rate_mult": 0.5},
            "markup":       {"mean_mult": 1.30, "variance_mult": 1.50, "anomaly_rate_mult": 1.5},
            "distribution": {"mean_mult": 1.10, "variance_mult": 2.00, "anomaly_rate_mult": 2.0},
            "markdown":     {"mean_mult": 0.65, "variance_mult": 4.00, "anomaly_rate_mult": 5.0},
        },
    },
}


# ═══════════════════════════════════════════════════════
# 3. SEASONAL PROFILES
# ═══════════════════════════════════════════════════════
# Multiplicative seasonal factors. 1.0 = no effect.

DEFAULT_DAY_OF_WEEK_FACTORS = {
    0: 1.05,  # Monday: slightly elevated (market open, batch processing)
    1: 1.02,  # Tuesday
    2: 1.00,  # Wednesday: baseline
    3: 0.98,  # Thursday
    4: 1.10,  # Friday: settlement, paydays
    5: 0.35,  # Saturday: minimal financial activity
    6: 0.25,  # Sunday: near-zero
}

DEFAULT_MONTH_FACTORS = {
    1: 0.85,   # January: post-holiday lull
    2: 0.90,
    3: 1.05,   # March: quarter-end, tax season
    4: 1.00,
    5: 0.95,
    6: 1.05,   # June: mid-year, quarter-end
    7: 0.90,   # July: summer lull
    8: 0.88,
    9: 1.10,   # September: back-to-business, quarter-end
    10: 1.05,
    11: 1.08,  # November: pre-holiday
    12: 1.25,  # December: year-end, holiday spending, window dressing
}

ENTITY_SEASONAL_PROFILES = {
    "credit_card_activity": {
        "month": {1: 0.75, 2: 0.82, 3: 0.90, 4: 0.95, 5: 0.93, 6: 1.00,
                  7: 1.02, 8: 0.98, 9: 0.95, 10: 1.00, 11: 1.20, 12: 1.45},
        "day_of_week": {0: 0.95, 1: 0.90, 2: 0.88, 3: 0.92, 4: 1.15, 5: 1.25, 6: 0.95},
        "holiday_proximity_mult": 1.60,
    },
    "payroll": {
        "month": {m: 1.0 for m in range(1, 13)},  # Payroll is consistent
        "day_of_week": {0: 0.10, 1: 0.10, 2: 0.15, 3: 0.15, 4: 1.80, 5: 0.05, 6: 0.05},
        # Payroll clusters on Fridays (biweekly) or 1st/15th
        "holiday_proximity_mult": 1.0,
    },
    "investment_statement": {
        "month": {1: 1.05, 2: 0.95, 3: 1.10, 4: 1.08, 5: 0.90, 6: 1.05,
                  7: 0.85, 8: 0.82, 9: 1.15, 10: 1.10, 11: 1.05, 12: 1.12},
        "day_of_week": {0: 1.10, 1: 1.05, 2: 1.00, 3: 1.02, 4: 1.08, 5: 0.0, 6: 0.0},
        "holiday_proximity_mult": 0.50,  # Markets closed on holidays
    },
    "pnl_statement": {
        "month": {1: 0.80, 2: 0.85, 3: 1.10, 4: 0.90, 5: 0.95, 6: 1.10,
                  7: 0.85, 8: 0.88, 9: 1.10, 10: 0.95, 11: 1.05, 12: 1.30},
        "day_of_week": {d: 1.0 for d in range(7)},  # P&L is typically period-end
        "holiday_proximity_mult": 1.0,
    },
    "saas_billing": {
        "month": {1: 0.92, 2: 0.95, 3: 1.05, 4: 1.00, 5: 0.98, 6: 1.08,
                  7: 0.90, 8: 0.88, 9: 1.10, 10: 1.05, 11: 1.08, 12: 0.95},
        "day_of_week": {0: 1.20, 1: 1.15, 2: 1.00, 3: 0.95, 4: 0.90, 5: 0.10, 6: 0.05},
        "holiday_proximity_mult": 0.80,
    },
    "forex_transactions": {
        "month": {m: 1.0 for m in range(1, 13)},
        "day_of_week": {0: 1.05, 1: 1.10, 2: 1.08, 3: 1.05, 4: 0.95, 5: 0.05, 6: 0.02},
        "holiday_proximity_mult": 0.30,
    },
    "crypto_trading_log": {
        "month": {1: 1.10, 2: 1.05, 3: 1.00, 4: 0.95, 5: 1.05, 6: 0.90,
                  7: 0.85, 8: 0.88, 9: 0.92, 10: 1.10, 11: 1.25, 12: 1.15},
        # Crypto trades 24/7 — weekends have lower but nonzero volume
        "day_of_week": {0: 1.05, 1: 1.08, 2: 1.05, 3: 1.02, 4: 1.00, 5: 0.75, 6: 0.70},
        "holiday_proximity_mult": 0.90,
    },
}


# ═══════════════════════════════════════════════════════
# 4. AUTOCORRELATION PROFILES
# ═══════════════════════════════════════════════════════
# AR(1) and GARCH(1,1) parameters per variable archetype.

# Variable keyword → autocorrelation config
AUTOCORRELATION_PROFILES = {
    # Prices: near unit-root (random walk) with GARCH volatility clustering
    "price": {
        "model": "gbm",         # Geometric Brownian Motion
        "ar1_phi": 0.98,        # Near-unit-root
        "drift_annual": 0.08,   # ~8% annual drift (equity-like)
        "garch_omega": 0.000002,
        "garch_alpha": 0.09,    # Innovation impact
        "garch_beta": 0.90,     # Persistence
    },
    # Revenue / amounts: mean-reverting with moderate persistence
    "revenue": {
        "model": "ar1",
        "ar1_phi": 0.85,
        "mean_reversion_speed": 0.15,
    },
    "amount": {
        "model": "ar1",
        "ar1_phi": 0.65,
        "mean_reversion_speed": 0.35,
    },
    # Balances: Ornstein-Uhlenbeck mean-reversion
    "balance": {
        "model": "ou",
        "theta": 0.10,          # Mean-reversion speed
        "mu_scale": 1.0,        # Reverts to sample mean
        "sigma_scale": 0.15,    # Volatility relative to mean
    },
    # Rates: slow-moving, very persistent
    "rate": {
        "model": "ar1",
        "ar1_phi": 0.97,
        "mean_reversion_speed": 0.03,
    },
    # Scores: moderately persistent
    "score": {
        "model": "ar1",
        "ar1_phi": 0.80,
        "mean_reversion_speed": 0.20,
    },
    # Counts / volumes: moderate persistence with Poisson-like jumps
    "count": {
        "model": "ar1",
        "ar1_phi": 0.55,
        "mean_reversion_speed": 0.45,
    },
    "volume": {
        "model": "ar1",
        "ar1_phi": 0.60,
        "mean_reversion_speed": 0.40,
    },
    # Spreads: fast mean-reverting
    "spread": {
        "model": "ou",
        "theta": 0.40,
        "mu_scale": 1.0,
        "sigma_scale": 0.10,
    },
    # Default: moderate persistence
    "_default": {
        "model": "ar1",
        "ar1_phi": 0.50,
        "mean_reversion_speed": 0.50,
    },
}


# ═══════════════════════════════════════════════════════
# MAIN COMPILER FUNCTION
# ═══════════════════════════════════════════════════════

def compile_temporal_model(
    temporal_config: Dict[str, Any],
    behavior_mods: Dict[str, Any],
    contract: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Compile the temporal intent into a mathematical temporal model.

    Args:
        temporal_config: From Stage 1/1.5 temporal extraction
        behavior_mods:   From Stage 2 behavior mapper (tensor engine)
        contract:        Full enriched contract from Stage 1.5

    Returns:
        Temporal model dict consumed by Stage 3's temporal engines.
    """
    entity = contract.get("entity", "generic")
    region = contract.get("intent", {}).get("region", "US")
    variables = contract.get("variables", {})
    frequency = temporal_config.get("frequency", "monthly")
    periods = temporal_config.get("periods", 24)

    # ── 1. Calendar Configuration ──
    calendar_config = _build_calendar_config(
        frequency=frequency,
        start_date=temporal_config.get("start_date"),
        end_date=temporal_config.get("end_date"),
        periods=periods,
        region=region,
        entity=entity,
    )

    # ── 2. Regime Configuration ──
    entities_list = contract.get("entities", [entity])
    regime_config = _build_regime_config(
        entity=entity,
        regime_hint=temporal_config.get("regime_hint"),
        behavior_mods=behavior_mods,
        periods=periods,
        entities=entities_list,
    )

    # ── 3. Seasonal Configuration ──
    seasonal_config = _build_seasonal_config(
        entity=entity,
        frequency=frequency,
    )

    # ── 4. Autocorrelation Configuration ──
    autocorrelation_config = _build_autocorrelation_config(
        variables=variables,
        entity=entity,
        temporal_pattern=temporal_config.get("temporal_pattern"),
        behavior_mods=behavior_mods,
    )

    # ── 5. Trend Configuration ──
    trend_config = _build_trend_config(
        temporal_pattern=temporal_config.get("temporal_pattern"),
        periods=periods,
        frequency=frequency,
        behavior_mods=behavior_mods,
    )

    temporal_model = {
        "enabled": True,
        "frequency": frequency,
        "periods": periods,
        "calendar": calendar_config,
        "regime": regime_config,
        "seasonal": seasonal_config,
        "autocorrelation": autocorrelation_config,
        "trend": trend_config,
        "temporal_pattern": temporal_config.get("temporal_pattern"),
        "regime_hint": temporal_config.get("regime_hint"),
        # Signature for reproducibility
        "temporal_signature": _temporal_signature(temporal_config, entity),
    }

    print(f"\n[*] TEMPORAL MODEL COMPILED:")
    print(f"    Frequency: {frequency} | Periods: {periods}")
    print(f"    Regime states: {regime_config['states']}")
    print(f"    Seasonal profiles: {len(seasonal_config)} variables")
    print(f"    Autocorrelation configs: {len(autocorrelation_config)} variables")
    print(f"    Trend drift: {trend_config.get('drift_per_period', 0):.6f}")

    return temporal_model


# ═══════════════════════════════════════════════════════
# SUB-COMPILERS
# ═══════════════════════════════════════════════════════

def _build_calendar_config(
    frequency: str,
    start_date: Optional[str],
    end_date: Optional[str],
    periods: int,
    region: str,
    entity: str,
) -> Dict[str, Any]:
    """Build the calendar grid configuration."""
    holiday_cal = HOLIDAY_CALENDARS.get(region, HOLIDAY_CALENDARS["US"])

    # Determine if this entity trades on weekends/holidays
    # Crypto trades 24/7, most financial instruments don't
    always_open = entity in ("crypto_trading_log",)
    includes_weekends = entity in (
        "credit_card_activity", "atm_withdrawals", "crypto_trading_log",
        "buy_now_pay_later",
    )

    return {
        "frequency": frequency,
        "start_date": start_date or "2024-01-01",
        "end_date": end_date or "2025-12-31",
        "periods": periods,
        "region": region,
        "holidays": holiday_cal["holidays"],
        "weekend_days": [] if always_open else holiday_cal["weekend_days"],
        "trading_hours": holiday_cal.get("trading_hours"),
        "skip_holidays": not always_open,
        "includes_weekends": includes_weekends or always_open,
        "calendar_name": holiday_cal["name"],
    }


def _build_regime_config(
    entity: str,
    regime_hint: Optional[str],
    behavior_mods: Dict[str, Any],
    periods: int,
    entities: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Build the regime transition matrix and effects."""

    # Check for entity-specific regime overrides
    # For multi_entity, check all constituent entities for overrides
    override = ENTITY_REGIME_OVERRIDES.get(entity)
    if not override and entities:
        for sub_entity in entities:
            override = ENTITY_REGIME_OVERRIDES.get(sub_entity)
            if override:
                break
    if override:
        states = override["states"]
        transition_matrix = [row[:] for row in override["transition_matrix"]]
        effects = dict(override["effects"])
    else:
        states = list(DEFAULT_REGIME_STATES)
        transition_matrix = [row[:] for row in DEFAULT_TRANSITION_MATRIX]
        effects = dict(DEFAULT_REGIME_EFFECTS)

    # Modulate transition matrix based on behavior tensors
    # High-risk prompts → higher probability of stress/crisis transitions
    var_mult = behavior_mods.get("variance_multiplier", 1.0)
    if var_mult > 1.5:
        # Increase transition probability to stress/crisis
        stress_boost = min(0.15, (var_mult - 1.0) * 0.05)
        # Normal → Stress gets boosted
        if len(transition_matrix) >= 2 and len(transition_matrix[0]) >= 2:
            transition_matrix[0][1] += stress_boost
            transition_matrix[0][0] -= stress_boost
            # Re-normalize rows
            for row in transition_matrix:
                row_sum = sum(row)
                if row_sum > 0:
                    for i in range(len(row)):
                        row[i] /= row_sum

    # If regime_hint forces a specific starting state
    initial_state = 0  # Default: start in normal/first state
    forced_regime_period = None

    if regime_hint:
        # Map hint to state index
        state_map = {s: i for i, s in enumerate(states)}
        hint_map = {
            "crisis": ["crisis", "catastrophe", "markdown"],
            "bull_market": ["normal", "markup"],
            "recession": ["stress", "elevated"],
            "recovery": ["recovery", "aftermath"],
            "stable": ["normal", "accumulation"],
            "bubble": ["stress", "markup", "distribution"],
        }
        target_states = hint_map.get(regime_hint, [])
        for ts in target_states:
            if ts in state_map:
                # Force this regime to appear at a random point
                forced_regime_period = max(2, periods // 4)  # ~25% in
                initial_state = state_map.get(ts, 0)
                break

    # Sigmoid blending window for smooth regime transitions
    blend_window = max(2, min(5, periods // 10))

    return {
        "states": states,
        "transition_matrix": transition_matrix,
        "effects": effects,
        "initial_state": initial_state,
        "forced_regime_hint": regime_hint,
        "forced_regime_period": forced_regime_period,
        "blend_window": blend_window,
        "n_states": len(states),
    }


def _build_seasonal_config(
    entity: str,
    frequency: str,
) -> Dict[str, Any]:
    """Build seasonal decomposition coefficients."""
    # Get entity-specific profile or default
    profile = ENTITY_SEASONAL_PROFILES.get(entity, {})

    month_factors = profile.get("month", dict(DEFAULT_MONTH_FACTORS))
    dow_factors = profile.get("day_of_week", dict(DEFAULT_DAY_OF_WEEK_FACTORS))
    holiday_mult = profile.get("holiday_proximity_mult", 1.20)

    # Only apply day-of-week seasonality for daily/weekly frequencies
    if frequency in ("monthly", "quarterly", "yearly"):
        dow_factors = {d: 1.0 for d in range(7)}

    # Only apply month seasonality for sub-yearly frequencies
    if frequency == "yearly":
        month_factors = {m: 1.0 for m in range(1, 13)}

    return {
        "month_factors": month_factors,
        "day_of_week_factors": dow_factors,
        "holiday_proximity_mult": holiday_mult,
        "holiday_proximity_days": 3,  # ±3 days around holidays
    }


def _build_autocorrelation_config(
    variables: Dict[str, Any],
    entity: str,
    temporal_pattern: Optional[str],
    behavior_mods: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """Build per-variable autocorrelation configurations."""
    configs = {}

    for var_name, var_def in variables.items():
        var_type = var_def.get("type", "string")

        # Only configure autocorrelation for numeric variables
        if var_type not in ("continuous", "integer"):
            continue

        # Find the best matching autocorrelation profile
        profile = _match_autocorrelation_profile(var_name, entity)

        # Override model type based on temporal_pattern
        if temporal_pattern:
            if temporal_pattern == "random_walk" and profile["model"] != "gbm":
                profile = dict(profile)
                profile["model"] = "gbm"
                profile["ar1_phi"] = 0.99
                profile["drift_annual"] = 0.0
            elif temporal_pattern == "mean_reverting":
                profile = dict(profile)
                profile["model"] = "ou"
                profile["theta"] = profile.get("theta", 0.15)
            elif temporal_pattern == "volatile":
                profile = dict(profile)
                if "garch_alpha" not in profile:
                    profile["garch_omega"] = 0.000005
                    profile["garch_alpha"] = 0.12
                    profile["garch_beta"] = 0.86

        # Modulate by behavior tensors
        var_mult = behavior_mods.get("variance_multiplier", 1.0)
        if var_mult > 1.5 and "garch_alpha" in profile:
            # Higher risk → more volatile (boost GARCH alpha)
            profile = dict(profile)
            profile["garch_alpha"] = min(0.25, profile["garch_alpha"] * (var_mult / 1.5))

        configs[var_name] = profile

    return configs


def _match_autocorrelation_profile(var_name: str, entity: str) -> Dict[str, Any]:
    """Match a variable name to its best autocorrelation profile."""
    name_lower = var_name.lower()

    for keyword, profile in AUTOCORRELATION_PROFILES.items():
        if keyword == "_default":
            continue
        if keyword in name_lower:
            return dict(profile)

    # Entity-based heuristics
    if entity in ("forex_transactions", "options_trading"):
        if "amount" in name_lower or "value" in name_lower:
            return dict(AUTOCORRELATION_PROFILES["price"])

    return dict(AUTOCORRELATION_PROFILES["_default"])


def _build_trend_config(
    temporal_pattern: Optional[str],
    periods: int,
    frequency: str,
    behavior_mods: Dict[str, Any],
) -> Dict[str, Any]:
    """Build trend/drift configuration."""
    # Base drift per period
    drift = 0.0
    trend_type = "flat"

    if temporal_pattern:
        # Annualize then convert to per-period
        periods_per_year = {
            "daily": 252, "weekly": 52, "monthly": 12,
            "quarterly": 4, "yearly": 1,
        }.get(frequency, 12)

        if temporal_pattern == "trending_up":
            annual_drift = 0.08  # ~8% annual growth
            drift = annual_drift / periods_per_year
            trend_type = "linear_up"
        elif temporal_pattern == "trending_down":
            annual_drift = -0.06  # ~6% annual decline
            drift = annual_drift / periods_per_year
            trend_type = "linear_down"
        elif temporal_pattern == "exponential_growth":
            annual_drift = 0.25  # ~25% annual compound growth
            drift = annual_drift / periods_per_year
            trend_type = "exponential"
        elif temporal_pattern == "volatile":
            drift = 0.0
            trend_type = "flat"  # Volatile = no drift, just high variance

    # Behavior tensor modulation
    mean_mult = behavior_mods.get("mean_multiplier", 1.0)
    if mean_mult > 1.5:
        drift *= 1.2  # Amplify trend for "large" prompts

    return {
        "drift_per_period": round(drift, 8),
        "trend_type": trend_type,
        "periods": periods,
    }


def _temporal_signature(temporal_config: Dict[str, Any], entity: str) -> str:
    """Generate a deterministic signature for the temporal configuration."""
    payload = f"{entity}|{temporal_config.get('frequency')}|{temporal_config.get('periods')}|{temporal_config.get('temporal_pattern')}|{temporal_config.get('regime_hint')}"
    return hashlib.sha256(payload.encode()).hexdigest()[:16]
