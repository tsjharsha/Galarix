# =====================================================
# 3.5 -- ANOMALY INJECTOR
# =====================================================
# Injects statistically controlled "Black Swan" outlier
# events into the dataset using the anomaly_rate from
# Stage 2's behavior tensor.
#
# Real financial data is not smooth. It has fraud spikes,
# market crashes, and rare catastrophic events. This
# engine makes synthetic data FEEL real by injecting
# anomalies that cluster (power-law spacing), have fat
# tails (Pareto multipliers), and flag themselves for
# explainability (_is_anomaly column).
# =====================================================

import numpy as np
from typing import Any, Dict, List


def inject_anomalies(
    columns: Dict[str, np.ndarray],
    parameters: Dict[str, Any],
    anomaly_rate: float,
    rng: np.random.Generator,
) -> Dict[str, np.ndarray]:
    """
    Inject Black Swan anomaly events into the dataset.

    Args:
        columns:      Dict of variable_name -> numpy array
        parameters:   Stage 2 distribution parameters (identifies continuous vars)
        anomaly_rate: Float 0.0-1.0 from Stage 2's tensor engine
                      (e.g., 0.15 means 15% of rows get anomalies)
        rng:          Seeded RNG for deterministic anomaly selection

    Returns:
        Updated columns dict with:
        - Anomaly rows modified with extreme values
        - New "_is_anomaly" boolean column added
    """
    n_rows = _get_row_count(columns)
    if n_rows == 0 or anomaly_rate <= 0:
        columns["_is_anomaly"] = np.zeros(n_rows, dtype=bool)
        return columns

    # ── Calculate number of anomalies ──
    n_anomalies = max(1, int(n_rows * min(anomaly_rate, 0.5)))

    # ── Select anomaly row indices using power-law clustering ──
    # Real anomalies cluster (e.g., fraud rings, flash crashes)
    # rather than being uniformly distributed
    anomaly_indices = _select_clustered_indices(rng, n_rows, n_anomalies)

    # ── Create anomaly flag column ──
    is_anomaly = np.zeros(n_rows, dtype=bool)
    is_anomaly[anomaly_indices] = True
    columns["_is_anomaly"] = is_anomaly

    # ── Classify continuous variables by domain semantics ──
    spikeable_vars = []   # amounts, balances — Pareto spikes are realistic
    bounded_vars = []     # scores, rates — shift toward tail, don't spike

    for name, dist in parameters.items():
        if dist.get("family", "") in ("categorical", ""):
            continue
        if name not in columns or columns[name].dtype == object:
            continue

        name_lower = name.lower()
        if _is_bounded_identity(name_lower):
            bounded_vars.append(name)
        else:
            spikeable_vars.append(name)

    all_anomalizable = spikeable_vars + bounded_vars
    if not all_anomalizable:
        return columns

    # ── For each anomaly row, spike 1-2 variables ──
    for idx in anomaly_indices:
        n_spike = min(rng.integers(1, 3), len(all_anomalizable))

        # Prefer spikeable vars (amounts) for Pareto spikes
        spike_pool = spikeable_vars if spikeable_vars else bounded_vars
        spike_vars = rng.choice(spike_pool, size=min(n_spike, len(spike_pool)), replace=False)

        for var_name in spike_vars:
            try:
                original_value = float(columns[var_name][idx])
                name_lower = var_name.lower()

                if _is_bounded_identity(name_lower):
                    # ── Bounded anomaly: shift toward distribution tail ──
                    bounds = parameters.get(var_name, {}).get("bounds", {})
                    b_min = bounds.get("min", 0.0)
                    b_max = bounds.get("max", None)

                    direction = rng.choice([-1, 1])
                    if direction > 0 and b_max is not None:
                        # Push toward upper bound
                        shift = float(rng.uniform(0.70, 0.95))
                        new_value = original_value + (b_max - original_value) * shift
                    elif direction < 0 and b_min is not None:
                        # Push toward lower bound
                        shift = float(rng.uniform(0.70, 0.95))
                        new_value = original_value - (original_value - b_min) * shift
                    else:
                        # Fallback if no specific bounds
                        shift = float(rng.uniform(0.15, 0.40))
                        new_value = original_value * (1.0 + shift) if direction > 0 else original_value * (1.0 - shift)
                        new_value = max(new_value, b_min)
                else:
                    # ── Spikeable anomaly: Pareto fat-tail multiplier ──
                    pareto_mult = float(rng.pareto(a=1.5) + 1.0)
                    pareto_mult = min(pareto_mult, 50.0)
                    direction = rng.choice([-1, 1])

                    if direction > 0:
                        new_value = abs(original_value) * pareto_mult
                    else:
                        new_value = abs(original_value) * 0.01

                columns[var_name][idx] = round(new_value, 4)

            except (ValueError, TypeError, IndexError):
                continue

    return columns


def _is_bounded_identity(name_lower: str) -> bool:
    """Check if a variable is a bounded identity (score, rate, ratio)
    that should NOT receive Pareto spikes."""
    bounded_keywords = [
        "credit_score", "fico", "risk_score",
        "interest_rate", "rate", "ratio",
        "utilization", "ltv", "volatility",
    ]
    return any(kw in name_lower for kw in bounded_keywords)


def _select_clustered_indices(
    rng: np.random.Generator,
    n_rows: int,
    n_anomalies: int,
) -> np.ndarray:
    """
    Select anomaly row indices with power-law clustering.

    Instead of uniform random selection, anomalies cluster
    in bursts (mimicking real-world fraud rings, flash crashes, etc.)

    Algorithm:
    1. Choose n_clusters center points uniformly
    2. Around each center, place anomalies with geometric spacing
    3. Clip to valid range and deduplicate
    """
    if n_anomalies >= n_rows:
        return np.arange(n_rows)

    # Number of clusters (fewer clusters = tighter clustering)
    n_clusters = max(1, n_anomalies // 5)
    anomalies_per_cluster = n_anomalies // n_clusters

    all_indices = []

    # Pick cluster centers
    centers = rng.integers(0, n_rows, size=n_clusters)

    for center in centers:
        for j in range(anomalies_per_cluster):
            # Geometric spread around center
            offset = int(rng.geometric(p=0.3)) * rng.choice([-1, 1])
            idx = center + offset
            idx = max(0, min(n_rows - 1, idx))
            all_indices.append(idx)

    # Add remaining anomalies uniformly (to reach exact count)
    remaining = n_anomalies - len(all_indices)
    if remaining > 0:
        uniform_extra = rng.integers(0, n_rows, size=remaining)
        all_indices.extend(uniform_extra.tolist())

    # Deduplicate and clip to exact count
    unique_indices = sorted(set(all_indices))
    if len(unique_indices) > n_anomalies:
        unique_indices = unique_indices[:n_anomalies]
    elif len(unique_indices) < n_anomalies:
        # Fill with uniform random to reach target
        while len(unique_indices) < n_anomalies:
            new_idx = int(rng.integers(0, n_rows))
            if new_idx not in unique_indices:
                unique_indices.append(new_idx)

    return np.array(unique_indices, dtype=int)


def _get_row_count(columns: Dict[str, np.ndarray]) -> int:
    """Get number of rows from any column."""
    for arr in columns.values():
        return len(arr)
    return 0
