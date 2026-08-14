# =====================================================
# ENGINE 3.T2 — TEMPORAL REGIME ENGINE
# =====================================================
# Simulates regime shifts using a discrete-time Hidden
# Markov Model (HMM). Produces a regime path that
# modulates distribution parameters across time.
#
# Features:
#   - Markov transition matrix simulation
#   - Forced regime injection (for "market crash" prompts)
#   - Sigmoid blending for smooth regime transitions
#   - Per-regime multipliers (mean, variance, anomaly rate)
#
# Pure NumPy. No external dependencies.
# =====================================================

import numpy as np
from typing import Any, Dict, List, Tuple


def simulate_regime_path(
    temporal_model: Dict[str, Any],
    n_periods: int,
    rng: np.random.Generator,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Simulate a regime path using a Markov chain.

    Args:
        temporal_model: Compiled temporal model (contains regime config)
        n_periods:      Number of time periods to simulate
        rng:            Seeded RNG

    Returns:
        regime_labels:       np.ndarray of str — regime label at each period
                             e.g., ["normal", "normal", "stress", "crisis", ...]
        regime_multipliers:  np.ndarray of shape (n_periods, 3)
                             Columns: [mean_mult, variance_mult, anomaly_rate_mult]
        regime_indices:      np.ndarray of int — state index at each period
    """
    regime_config = temporal_model.get("regime", {})
    states = regime_config.get("states", ["normal", "stress", "crisis", "recovery"])
    transition_matrix = regime_config.get("transition_matrix", [
        [0.97, 0.02, 0.005, 0.005],
        [0.15, 0.65, 0.15, 0.05],
        [0.02, 0.05, 0.80, 0.13],
        [0.20, 0.03, 0.01, 0.76],
    ])
    effects = regime_config.get("effects", {})
    initial_state = regime_config.get("initial_state", 0)
    forced_regime_hint = regime_config.get("forced_regime_hint")
    forced_regime_period = regime_config.get("forced_regime_period")
    blend_window = regime_config.get("blend_window", 3)
    n_states = len(states)

    # ── Validate transition matrix ──
    T = _validate_transition_matrix(transition_matrix, n_states)

    # ── Simulate Markov chain ──
    raw_indices = _simulate_markov_chain(T, initial_state, n_periods, rng)

    # ── Inject forced regime if specified ──
    if forced_regime_hint and forced_regime_period is not None:
        raw_indices = _inject_forced_regime(
            raw_indices, states, forced_regime_hint,
            forced_regime_period, n_periods, blend_window,
        )

    # ── Apply sigmoid blending for smooth transitions ──
    blended_multipliers = _blend_regime_transitions(
        raw_indices, states, effects, n_periods, blend_window,
    )

    # ── Build output arrays ──
    regime_labels = np.array([states[min(idx, n_states - 1)] for idx in raw_indices], dtype=object)
    regime_indices = np.array(raw_indices, dtype=int)

    return regime_labels, blended_multipliers, regime_indices


def _validate_transition_matrix(
    T: List[List[float]],
    n_states: int,
) -> np.ndarray:
    """Validate and normalize the transition matrix."""
    T = np.array(T, dtype=float)

    # Ensure square and correct size
    if T.shape[0] != n_states or T.shape[1] != n_states:
        # Fall back to identity-like matrix
        T = np.eye(n_states) * 0.9
        off_diag = 0.1 / max(1, n_states - 1)
        T += off_diag
        np.fill_diagonal(T, 0.9)

    # Ensure non-negative
    T = np.maximum(T, 0.0)

    # Normalize rows to sum to 1
    row_sums = T.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    T = T / row_sums

    return T


def _simulate_markov_chain(
    T: np.ndarray,
    initial_state: int,
    n_periods: int,
    rng: np.random.Generator,
) -> List[int]:
    """
    Simulate a discrete-time Markov chain.

    This is the core HMM simulation. At each step, we draw from
    the categorical distribution defined by the current state's
    transition row.

    v2.0: Adaptive diagonal reduction for longer series.
    Without this, high diagonal persistence (0.90-0.97) causes
    the chain to get "stuck" in one state for the entire tail.
    For series > 30 periods, we reduce diagonal persistence to
    guarantee meaningful regime diversity.
    """
    n_states = T.shape[0]
    current_state = min(initial_state, n_states - 1)

    # ── Adaptive persistence reduction for long series ──
    # If n_periods > 30, reduce diagonal so average regime
    # duration is ~n_periods / (n_states * 1.5)
    T_adapted = T.copy()
    if n_periods > 30:
        target_avg_duration = max(4, n_periods // (n_states * 2))
        target_persistence = 1.0 - 1.0 / target_avg_duration
        target_persistence = min(target_persistence, 0.92)  # Cap at 0.92

        for i in range(n_states):
            current_diag = T_adapted[i, i]
            if current_diag > target_persistence:
                excess = current_diag - target_persistence
                T_adapted[i, i] = target_persistence
                # Distribute excess probability to off-diagonal states
                off_diag_count = n_states - 1
                if off_diag_count > 0:
                    for j in range(n_states):
                        if j != i:
                            T_adapted[i, j] += excess / off_diag_count

        # Re-normalize rows
        for i in range(n_states):
            row_sum = T_adapted[i].sum()
            if row_sum > 0:
                T_adapted[i] /= row_sum

    path = [current_state]

    for t in range(1, n_periods):
        # Get transition probabilities from current state
        probs = T_adapted[current_state]

        # Ensure valid probability distribution
        prob_sum = probs.sum()
        if prob_sum <= 0:
            probs = np.ones(n_states) / n_states
        else:
            probs = probs / prob_sum

        # Draw next state
        next_state = rng.choice(n_states, p=probs)
        path.append(int(next_state))
        current_state = next_state

    # ── Minimum transition guarantee ──
    # If the chain produced fewer than 2 transitions, force at least 2
    n_transitions = sum(1 for i in range(1, len(path)) if path[i] != path[i-1])
    if n_transitions < 2 and n_periods > 10:
        # Force transitions at ~33% and ~66% of the series
        t1 = n_periods // 3
        t2 = 2 * n_periods // 3
        # Pick different states for each forced transition
        available_states = [s for s in range(n_states) if s != path[t1]]
        if available_states:
            forced_state1 = rng.choice(available_states)
            duration1 = max(3, n_periods // 8)
            for t in range(t1, min(t1 + duration1, n_periods)):
                path[t] = int(forced_state1)
        available_states2 = [s for s in range(n_states) if s != path[min(t2, n_periods-1)]]
        if available_states2:
            forced_state2 = rng.choice(available_states2)
            duration2 = max(3, n_periods // 8)
            for t in range(t2, min(t2 + duration2, n_periods)):
                path[t] = int(forced_state2)

    return path


def _inject_forced_regime(
    path: List[int],
    states: List[str],
    forced_hint: str,
    forced_period: int,
    n_periods: int,
    blend_window: int,
) -> List[int]:
    """
    Inject a forced regime at specific periods.

    When a user says "with market crash", we ensure the crisis
    regime actually appears in the output with proper narrative:
    lead-in → crisis → recovery → (possible second event)

    v2.0: Injects TWO forced events for series > 40 periods
    to create a realistic multi-cycle narrative.
    """
    # Map hint to target state index
    hint_to_state = {
        "crisis": ["crisis", "catastrophe", "markdown"],
        "bull_market": ["normal", "markup"],
        "recession": ["stress", "elevated"],
        "recovery": ["recovery", "aftermath"],
        "stable": ["normal", "accumulation"],
        "bubble": ["stress", "markup", "distribution"],
    }

    target_state_names = hint_to_state.get(forced_hint, [])
    target_idx = None
    for ts in target_state_names:
        if ts in states:
            target_idx = states.index(ts)
            break

    if target_idx is None:
        return path

    def _inject_single_event(path, inject_start, regime_duration):
        """Inject a single forced event with lead-in and recovery."""
        inject_end = min(inject_start + regime_duration, n_periods)

        # Override the path in the injection window
        for t in range(inject_start, inject_end):
            path[t] = target_idx

        # Add a recovery/transition after the forced regime
        if forced_hint in ("crisis", "recession"):
            recovery_idx = None
            for rs in ["recovery", "aftermath", "normal", "accumulation"]:
                if rs in states:
                    recovery_idx = states.index(rs)
                    break
            if recovery_idx is not None:
                recovery_end = min(inject_end + max(2, regime_duration // 2), n_periods)
                for t in range(inject_end, recovery_end):
                    path[t] = recovery_idx

        # Add a stress lead-in before the forced regime
        if forced_hint in ("crisis", "recession") and inject_start > 2:
            stress_idx = None
            for ss in ["stress", "elevated", "distribution"]:
                if ss in states:
                    stress_idx = states.index(ss)
                    break
            if stress_idx is not None:
                lead_in_start = max(0, inject_start - max(2, regime_duration // 3))
                for t in range(lead_in_start, inject_start):
                    path[t] = stress_idx

        return path

    # Primary injection: at ~25% of the series
    inject_start = min(forced_period, n_periods - 1)
    regime_duration = max(3, n_periods // 6)  # At least 3 periods, up to ~16%
    path = _inject_single_event(path, inject_start, regime_duration)

    # Secondary injection: for longer series (>40 periods), add a second event
    # at ~65% of the series for a realistic multi-cycle pattern
    if n_periods > 40:
        second_start = int(n_periods * 0.65)
        second_duration = max(3, n_periods // 8)
        path = _inject_single_event(path, second_start, second_duration)

    return path


def _blend_regime_transitions(
    path: List[int],
    states: List[str],
    effects: Dict[str, Dict[str, float]],
    n_periods: int,
    blend_window: int,
) -> np.ndarray:
    """
    Apply sigmoid blending to smooth regime transitions.

    Instead of instant regime snaps (which look artificial),
    we interpolate between regime effects over a window of
    `blend_window` periods using a sigmoid function.

    This creates the realistic gradual onset of market stress
    and the gradual recovery that characterizes real financial data.
    """
    # ── Build raw (unblended) multiplier array ──
    raw_multipliers = np.ones((n_periods, 3), dtype=float)

    for t in range(n_periods):
        state_idx = min(path[t], len(states) - 1)
        state_name = states[state_idx]
        state_effects = effects.get(state_name, {
            "mean_mult": 1.0, "variance_mult": 1.0, "anomaly_rate_mult": 1.0
        })
        raw_multipliers[t, 0] = state_effects.get("mean_mult", 1.0)
        raw_multipliers[t, 1] = state_effects.get("variance_mult", 1.0)
        raw_multipliers[t, 2] = state_effects.get("anomaly_rate_mult", 1.0)

    if blend_window <= 1 or n_periods <= 2:
        return raw_multipliers

    # ── Detect regime transition points ──
    transitions = []
    for t in range(1, n_periods):
        if path[t] != path[t - 1]:
            transitions.append(t)

    if not transitions:
        return raw_multipliers

    # ── Apply sigmoid blending at each transition ──
    blended = raw_multipliers.copy()

    for trans_t in transitions:
        # Blending window: [trans_t - blend_window//2, trans_t + blend_window//2]
        half_w = blend_window // 2
        w_start = max(0, trans_t - half_w)
        w_end = min(n_periods, trans_t + half_w + 1)

        if w_start >= w_end:
            continue

        # Get the before and after multipliers
        before_mult = raw_multipliers[max(0, trans_t - 1)]
        after_mult = raw_multipliers[min(trans_t, n_periods - 1)]

        # Sigmoid blend
        for t in range(w_start, w_end):
            # Normalized position in [-3, 3] for sigmoid
            if w_end > w_start:
                x = 6.0 * (t - w_start) / (w_end - w_start) - 3.0
            else:
                x = 0.0

            # Sigmoid function
            sigmoid_val = 1.0 / (1.0 + np.exp(-x))

            # Interpolate
            blended[t] = before_mult * (1.0 - sigmoid_val) + after_mult * sigmoid_val

    return blended

