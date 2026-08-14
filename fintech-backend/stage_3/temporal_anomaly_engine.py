# =====================================================
# ENGINE 3.T4 — TEMPORAL ANOMALY ENGINE
# =====================================================
# Time-aware anomaly injection that creates realistic
# financial event patterns:
#
#   - Flash crashes (sudden moves + partial recovery)
#   - Volume spikes (tied to regime transitions)
#   - Seasonal anomalies (end-of-quarter, January effect)
#   - Event clustering (fraud bursts, not isolated events)
#   - Contagion effects (crash → volume → spread widening)
#
# Extends the existing anomaly_injector.py with temporal
# context. When no temporal model exists, falls through
# to the existing static anomaly injection.
#
# Pure NumPy. No external dependencies.
# =====================================================

import numpy as np
from typing import Any, Dict, List, Optional, Tuple


def inject_temporal_anomalies(
    columns: Dict[str, np.ndarray],
    timestamps: np.ndarray,
    regime_labels: np.ndarray,
    regime_multipliers: np.ndarray,
    calendar_meta: Dict[str, np.ndarray],
    temporal_model: Dict[str, Any],
    parameters: Dict[str, Any],
    rng: np.random.Generator,
) -> Dict[str, np.ndarray]:
    """
    Inject time-aware anomalies into the generated time series.

    Unlike static anomaly injection (which sprinkles random outliers),
    temporal anomalies have structure:
    - They cluster in time (event bursts)
    - They correlate with regime transitions
    - They align with calendar events (quarter-end, holidays)
    - They cascade across variables (contagion)

    Args:
        columns:              Generated data columns
        timestamps:           Timestamp array from calendar engine
        regime_labels:        Regime state at each period
        regime_multipliers:   (n_periods, 3) multiplier array
        calendar_meta:        Calendar metadata (month-end, quarter-end, etc.)
        temporal_model:       Compiled temporal model
        parameters:           Distribution parameters
        rng:                  Seeded RNG

    Returns:
        Updated columns dict with temporal anomalies injected.
        Also adds/updates '_is_anomaly' and '_anomaly_type' columns.
    """
    n = len(timestamps)
    if n < 5:
        return columns

    base_anomaly_rate = temporal_model.get("regime", {}).get(
        "effects", {}
    ).get("normal", {}).get("anomaly_rate_mult", 1.0) * 0.05

    # ── 1. Determine anomaly positions ──
    anomaly_mask = np.zeros(n, dtype=bool)
    anomaly_types = np.array([""] * n, dtype=object)

    # 1a. Regime-transition anomalies
    _inject_regime_transition_anomalies(
        anomaly_mask, anomaly_types, regime_labels, n, rng,
    )

    # 1b. Calendar-based anomalies (quarter-end, month-end)
    _inject_calendar_anomalies(
        anomaly_mask, anomaly_types, calendar_meta, n, rng,
    )

    # 1c. Random point anomalies (flash crashes, spikes)
    _inject_point_anomalies(
        anomaly_mask, anomaly_types, regime_multipliers, n,
        base_anomaly_rate, rng,
    )

    # 1d. Clustered anomalies (fraud bursts)
    _inject_clustered_anomalies(
        anomaly_mask, anomaly_types, n, base_anomaly_rate, rng,
    )

    # ── 2. Apply anomaly effects to data columns ──
    for var_name, col in columns.items():
        if var_name.startswith("_"):
            continue
        if col.dtype == object:
            continue

        try:
            col_float = col.astype(float)
        except (ValueError, TypeError):
            continue

        if np.std(col_float) < 1e-10:
            continue

        # Get distribution parameters for scaling
        param = parameters.get(var_name, {})
        family = param.get("family", "")

        if family in ("categorical", ""):
            continue

        # Apply anomaly effects at marked positions
        for t in range(n):
            if not anomaly_mask[t]:
                continue

            atype = str(anomaly_types[t])

            if atype == "flash_crash":
                # Sudden drop: 3-8 sigma negative shock
                shock_magnitude = rng.uniform(3.0, 8.0) * np.std(col_float)
                col_float[t] -= shock_magnitude

                # Partial recovery in next 1-3 periods
                recovery_periods = min(rng.integers(1, 4), n - t - 1)
                for r in range(1, recovery_periods + 1):
                    if t + r < n:
                        recovery_frac = 0.3 + 0.2 * r  # Recover 30-70%
                        col_float[t + r] = col_float[t] + shock_magnitude * recovery_frac

            elif atype == "volume_spike":
                # 3-10× normal volume
                spike_mult = rng.uniform(3.0, 10.0)
                col_float[t] *= spike_mult

            elif atype == "quarter_end":
                # Quarter-end window dressing: 1.5-2.5× values
                col_float[t] *= rng.uniform(1.5, 2.5)

            elif atype == "month_end":
                # Month-end settlement bump: 1.2-1.8×
                col_float[t] *= rng.uniform(1.2, 1.8)

            elif atype == "regime_transition":
                # Elevated volatility at regime boundaries
                shock = rng.normal(0, 2.5) * np.std(col_float)
                col_float[t] += shock

            elif atype == "cluster_burst":
                # Sustained elevated values (fraud burst, claim surge)
                col_float[t] *= rng.uniform(2.0, 5.0)

            elif atype == "point_outlier":
                # Random outlier (3-6 sigma)
                direction = rng.choice([-1, 1])
                shock = direction * rng.uniform(3.0, 6.0) * np.std(col_float)
                col_float[t] += shock

        columns[var_name] = col_float

    # ── 3. Store anomaly metadata ──
    columns["_is_anomaly"] = anomaly_mask
    columns["_anomaly_type"] = anomaly_types

    anomaly_count = int(np.sum(anomaly_mask))
    if anomaly_count > 0:
        print(f"    [T4] Injected {anomaly_count} temporal anomalies "
              f"({anomaly_count/n*100:.1f}% of periods)")

    return columns


# ─────────────────────────────────────────────────
# ANOMALY PATTERN GENERATORS
# ─────────────────────────────────────────────────

def _inject_regime_transition_anomalies(
    mask: np.ndarray,
    types: np.ndarray,
    regime_labels: np.ndarray,
    n: int,
    rng: np.random.Generator,
) -> None:
    """Inject anomalies at regime transition boundaries."""
    for t in range(1, n):
        if str(regime_labels[t]) != str(regime_labels[t - 1]):
            # Transition detected — mark ±1 period window
            for dt in range(-1, 2):
                idx = t + dt
                if 0 <= idx < n and not mask[idx]:
                    if rng.random() < 0.70:  # 70% chance at transitions
                        mask[idx] = True
                        types[idx] = "regime_transition"

            # Flash crash on severe transitions (normal → crisis)
            current_regime = str(regime_labels[t])
            prev_regime = str(regime_labels[t - 1])
            if current_regime in ("crisis", "catastrophe", "markdown") and \
               prev_regime in ("normal", "accumulation", "stress"):
                if rng.random() < 0.60:
                    mask[t] = True
                    types[t] = "flash_crash"

            # Volume spike at any transition
            if rng.random() < 0.50:
                mask[t] = True
                types[t] = "volume_spike"


def _inject_calendar_anomalies(
    mask: np.ndarray,
    types: np.ndarray,
    calendar_meta: Dict[str, np.ndarray],
    n: int,
    rng: np.random.Generator,
) -> None:
    """Inject anomalies at calendar-significant dates."""
    is_quarter_end = calendar_meta.get("is_quarter_end", np.zeros(n, dtype=bool))
    is_month_end = calendar_meta.get("is_month_end", np.zeros(n, dtype=bool))
    month = calendar_meta.get("month", np.ones(n, dtype=int))

    for t in range(n):
        if mask[t]:
            continue

        # Quarter-end window dressing (30% chance)
        if is_quarter_end[t] and rng.random() < 0.30:
            mask[t] = True
            types[t] = "quarter_end"

        # Month-end settlement (15% chance)
        elif is_month_end[t] and rng.random() < 0.15:
            mask[t] = True
            types[t] = "month_end"

        # January effect (elevated volatility in early January)
        elif int(month[t]) == 1 and rng.random() < 0.10:
            mask[t] = True
            types[t] = "point_outlier"


def _inject_point_anomalies(
    mask: np.ndarray,
    types: np.ndarray,
    regime_multipliers: np.ndarray,
    n: int,
    base_rate: float,
    rng: np.random.Generator,
) -> None:
    """
    Inject random point anomalies with regime-modulated rate.

    v2.0: Added minimum anomaly rate floor (2%) so anomalies
    appear across the full series, not just in high-regime periods.
    Also ensures at least 1 anomaly in the final third of the series.
    """
    # Minimum floor: anomalies should always have at least 2% chance
    MIN_ANOMALY_RATE = 0.02
    last_third_start = max(0, 2 * n // 3)
    has_anomaly_in_tail = False

    for t in range(n):
        if mask[t]:
            if t >= last_third_start:
                has_anomaly_in_tail = True
            continue

        # Anomaly rate is modulated by regime
        anomaly_mult = regime_multipliers[min(t, len(regime_multipliers) - 1), 2] if len(regime_multipliers) > 0 else 1.0
        effective_rate = max(MIN_ANOMALY_RATE, min(0.30, base_rate * anomaly_mult))

        if rng.random() < effective_rate:
            mask[t] = True
            types[t] = "point_outlier"
            if t >= last_third_start:
                has_anomaly_in_tail = True

    # Guarantee at least one anomaly in the final third
    if not has_anomaly_in_tail and n > 10:
        inject_pos = rng.integers(last_third_start, n)
        if not mask[inject_pos]:
            mask[inject_pos] = True
            types[inject_pos] = "point_outlier"


def _inject_clustered_anomalies(
    mask: np.ndarray,
    types: np.ndarray,
    n: int,
    base_rate: float,
    rng: np.random.Generator,
) -> None:
    """
    Inject clustered anomaly bursts (fraud bursts, claim surges).

    Real anomalies often cluster: fraud comes in waves, insurance
    claims surge after disasters, trading anomalies cascade.
    """
    # Determine number of burst events
    expected_bursts = max(1, int(n * base_rate * 0.1))
    n_bursts = rng.poisson(expected_bursts)
    n_bursts = min(n_bursts, n // 10)  # Cap at 10% of periods

    for _ in range(n_bursts):
        # Random burst start point
        burst_start = int(rng.integers(0, max(1, n - 5)))
        burst_length = int(rng.integers(2, min(6, n - burst_start)))

        for t in range(burst_start, min(burst_start + burst_length, n)):
            if not mask[t]:
                mask[t] = True
                types[t] = "cluster_burst"
