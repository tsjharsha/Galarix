# =====================================================
# 3.2 -- MARGINAL SAMPLER (Pure NumPy)
# =====================================================
# Draws independent samples from each variable's
# probability distribution. Uses ONLY numpy — no scipy.
#
# Supports: normal, lognormal, beta, student_t, cauchy, categorical
# All implemented via numpy's Generator API.
# =====================================================

import numpy as np
from typing import Any, Dict, List

from stage_3.seed_engine import create_labeled_generator, create_sub_generator
from stage_3.string_generators import generate_string_column


def sample_all_marginals(
    rng: np.random.Generator,
    parameters: Dict[str, Any],
    variables: Dict[str, Any],
    entity: str,
    n_rows: int,
    tensor_signature: str = "",
    variation_salt: int = 0,
    region: str = "US",
) -> Dict[str, np.ndarray]:
    """
    Sample independent marginal columns for every variable in the model.

    Args:
        rng:        Master RNG from seed_engine
        parameters: Stage 2 distribution parameters (keyed by variable name)
        variables:  Stage 1.5 variable definitions (type info)
        entity:     Entity name (for context in string generation)
        n_rows:     Number of rows to generate

    Returns:
        Dict mapping variable_name -> numpy array of sampled values.
    """
    columns: Dict[str, np.ndarray] = {}

    # Pre-extract constraints from the contract for integer fallback bounds
    # Parameters may carry "bounds" from Stage 2's constraint_engine
    for var_name, var_def in variables.items():
        var_type = var_def.get("type", "string")
        if tensor_signature:
            var_rng = create_labeled_generator(tensor_signature, variation_salt, f"marginal:{var_name}")
        else:
            var_rng = create_sub_generator(rng, var_name)

        if var_name in parameters:
            dist_def = parameters[var_name]
            family = dist_def.get("family", "")

            if family == "categorical":
                columns[var_name] = _sample_categorical(var_rng, dist_def, n_rows)
            else:
                columns[var_name] = _sample_continuous(var_rng, dist_def, n_rows)
        else:
            # --- HARDENED FALLBACK LOGIC ---
            # Check if the variable has a distribution in the schema that
            # wasn't propagated to parameters (e.g., integer type with
            # categorical distribution like aml_flag [0,1]).
            if var_type in ("string", "datetime"):
                values = generate_string_column(var_rng, var_name, var_type, n_rows, entity, region)
                columns[var_name] = np.array(values, dtype=object)
            elif var_type == "integer":
                # Use variable definition constraints if available,
                # NOT arbitrary 1-100. Extract from var_def or schema.
                var_constraints = var_def.get("constraints", {})
                lo = int(var_constraints.get("min", 1))
                hi = int(var_constraints.get("max", 10))
                if hi <= lo:
                    hi = lo + 10
                columns[var_name] = var_rng.integers(lo, hi + 1, size=n_rows).astype(float)
            elif var_type == "continuous":
                # Pre-allocate zero array for derived targets, so formulas don't crash
                columns[var_name] = np.zeros(n_rows, dtype=float)
            else:
                # Last resort: generate string column for truly unknown types
                values = generate_string_column(var_rng, var_name, "string", n_rows, entity, region)
                columns[var_name] = np.array(values, dtype=object)

    return columns


def _sample_continuous(
    rng: np.random.Generator,
    dist_def: Dict[str, Any],
    n_rows: int,
) -> np.ndarray:
    """
    Sample from a continuous distribution using ONLY numpy.
    No scipy dependency.

    HARDENED: Now performs truncated sampling when bounds exist.
    Uses rejection sampling to draw values within [min, max] from
    the start, eliminating the boundary "shelf" artifact caused by
    post-hoc clamping.
    """
    family = dist_def.get("family", "normal")
    params = dist_def.get("params", {})
    bounds = dist_def.get("bounds", {})

    b_min = bounds.get("min", None)
    b_max = bounds.get("max", None)

    if family == "normal":
        mean = params.get("mean", 0.0)
        std = max(params.get("std", 1.0), 0.001)
        samples = _truncated_sample(rng, "normal", {"mean": mean, "std": std}, n_rows, b_min, b_max)

    elif family == "lognormal":
        mu = params.get("mu", 0.0)
        sigma = max(params.get("sigma", 1.0), 0.001)
        samples = _truncated_sample(rng, "lognormal", {"mu": mu, "sigma": sigma}, n_rows, b_min, b_max)

    elif family == "beta":
        alpha = max(params.get("alpha", 2.0), 0.01)
        beta_param = max(params.get("beta", 2.0), 0.01)
        samples = rng.beta(alpha, beta_param, size=n_rows)

    elif family == "student_t":
        df = max(params.get("df", 3.0), 1.0)
        loc = params.get("loc", 0.0)
        scale = max(params.get("scale", 1.0), 0.001)
        samples = _truncated_sample(rng, "student_t", {"df": df, "loc": loc, "scale": scale}, n_rows, b_min, b_max)

    elif family == "cauchy":
        loc = params.get("loc", 0.0)
        scale = max(params.get("scale", 1.0), 0.001)
        samples = _truncated_sample(rng, "cauchy", {"loc": loc, "scale": scale}, n_rows, b_min, b_max)

    else:
        samples = rng.normal(0, 1, size=n_rows)

    return samples


def _truncated_sample(
    rng: np.random.Generator,
    family: str,
    params: Dict[str, float],
    n_rows: int,
    b_min: float = None,
    b_max: float = None,
    max_retries: int = 5,
) -> np.ndarray:
    """
    Rejection-based truncated sampling. Draws from the base distribution
    and resamples any out-of-bounds values. Falls back to soft clamping
    with jitter after max_retries to guarantee termination.
    """
    samples = _raw_sample(rng, family, params, n_rows)

    if b_min is None and b_max is None:
        return samples

    for _ in range(max_retries):
        oob_mask = np.zeros(n_rows, dtype=bool)
        if b_min is not None:
            oob_mask |= (samples < b_min)
        if b_max is not None:
            oob_mask |= (samples > b_max)

        n_oob = np.sum(oob_mask)
        if n_oob == 0:
            break

        # Resample only the out-of-bound values
        resampled = _raw_sample(rng, family, params, int(n_oob))
        samples[oob_mask] = resampled

    # Final safety: soft clamp any remaining OOB with small jitter
    if b_min is not None:
        still_low = samples < b_min
        if np.any(still_low):
            n_low = int(np.sum(still_low))
            jitter = np.abs(rng.normal(0, 0.02, size=n_low)) * max(abs(b_min), 1.0)
            samples[still_low] = b_min + jitter
    if b_max is not None:
        still_high = samples > b_max
        if np.any(still_high):
            n_high = int(np.sum(still_high))
            jitter = np.abs(rng.normal(0, 0.02, size=n_high)) * max(abs(b_max), 1.0)
            samples[still_high] = b_max - jitter

    return samples


def _raw_sample(
    rng: np.random.Generator,
    family: str,
    params: Dict[str, float],
    n: int,
) -> np.ndarray:
    """Draw n raw (untruncated) samples from the given family."""
    if family == "normal":
        return rng.normal(params["mean"], params["std"], size=n)
    elif family == "lognormal":
        return rng.lognormal(params["mu"], params["sigma"], size=n)
    elif family == "student_t":
        return rng.standard_t(params["df"], size=n) * params["scale"] + params["loc"]
    elif family == "cauchy":
        return rng.standard_cauchy(size=n) * params["scale"] + params["loc"]
    else:
        return rng.normal(0, 1, size=n)


def _sample_categorical(
    rng: np.random.Generator,
    dist_def: Dict[str, Any],
    n_rows: int,
) -> np.ndarray:
    """Sample from a categorical distribution using weighted random choice.

    HARDENED: Preserves numeric category types (int/float) instead of
    coercing everything to strings. This is critical because downstream
    systems (derived formulas, constraint enforcer) need numeric types
    for math operations and category validation.
    """
    categories = dist_def.get("categories", [])
    weights = dist_def.get("weights", [])

    if not categories:
        return np.array(["Unknown"] * n_rows, dtype=object)

    if weights:
        total = sum(weights)
        probs = [w / total for w in weights] if total > 0 else [1.0 / len(categories)] * len(categories)
    else:
        probs = [1.0 / len(categories)] * len(categories)

    if len(probs) != len(categories):
        probs = [1.0 / len(categories)] * len(categories)

    # CRITICAL FIX: Detect if categories are all numeric.
    # If so, sample as float array to preserve type for downstream math
    # (derived formulas, constraint enforcement, conditional evaluation).
    # Previously, all categories were coerced to strings, breaking
    # loan_term_months, aml_flag, num_installments, days_to_expiration, etc.
    all_numeric = all(isinstance(c, (int, float)) for c in categories)

    if all_numeric:
        indices = rng.choice(len(categories), size=n_rows, p=probs)
        return np.array([float(categories[i]) for i in indices], dtype=float)
    else:
        str_cats = [str(c) for c in categories]
        indices = rng.choice(len(str_cats), size=n_rows, p=probs)
        return np.array([str_cats[i] for i in indices], dtype=object)



