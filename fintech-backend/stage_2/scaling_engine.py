# =====================================================
# SCALING ENGINE
# =====================================================
# Iterates through the schema constraints and distributions
# and applies the numeric multipliers extracted by the Mapper.
# =====================================================

from typing import Dict, Any
import copy
import math

def apply_scale_to_distributions(base_distributions: Dict[str, Any], behavior: Dict[str, float]) -> Dict[str, Any]:
    """
    Takes the pure baseline distributions defined in the schema registry
    and forcefully shifts them mathematically based on the behavior config.

    Example:
        base normal(mu=5000, sigma=1000) + scale=large (mean_mult=2.5, var_mult=1.0)
        -> modified normal(mu=12500, sigma=1000)
    """
    scaled_dists = copy.deepcopy(base_distributions)
    mean_multi = behavior.get("mean_multiplier", 1.0)
    var_multi = behavior.get("variance_multiplier", 1.0)

    for var_name, dist_def in scaled_dists.items():
        family = dist_def.get("family")
        params = dist_def.get("params", {})

        # ── Skip non-parametric distributions ──
        # Categorical weights are structural, not numerical — they are
        # modified by the dependency engine, not the scaling engine.
        if family == "categorical":
            continue

        # ── MORPHOLOGY ENGINE (Black Swan Logic) ──
        # If variance is extreme, simple scaling isn't enough for a "Demon" model.
        # We must change the fundamental shape of the reality.
        if family == "normal" and var_multi > 3.0:
            # Shift from Normal to Student-T for fatter "financial tails"
            dist_def["family"] = "student_t"
            params["df"] = round(10.0 / var_multi, 2) # Degrees of freedom drops as risk rises
            # Apply scaling DURING morph — the standard scaling block won't reach 'loc'
            if "mean" in params: params["loc"] = round(params.pop("mean") * mean_multi, 4)
            if "std" in params: params["scale"] = round(params.pop("std") * var_multi, 4)
            
        elif family == "lognormal" and var_multi > 4.5:
            # Extreme event: Morph to Cauchy distribution (Infinite Variance)
            dist_def["family"] = "cauchy"
            if "mu" in params and mean_multi > 0:
                # Convert mu to linear space because cauchy operates in linear space
                params["loc"] = round(math.exp(params.pop("mu")) * mean_multi, 4)
            params["scale"] = round(math.exp(var_multi) if var_multi < 10 else 10000.0, 4)
            params.pop("sigma", None)

        # ── Standard Scaling ──
        if dist_def["family"] == "normal":
            if "mean" in params:
                params["mean"] = round(params["mean"] * mean_multi, 4)
            if "std" in params:
                params["std"] = round(params["std"] * var_multi, 4)
        
        elif dist_def["family"] == "lognormal":
            if "mu" in params and mean_multi > 0:
                params["mu"] = round(params["mu"] + math.log(mean_multi), 4)
            if "sigma" in params:
                params["sigma"] = max(0.01, round(params["sigma"] * var_multi, 4))

        # ── Beta Distribution Scaling ──
        # Used by fraud_score, verification_score, sanctions_match.
        # Higher risk → shift probability mass toward 1.0 (more fraud/risk).
        # Lower risk → shift toward 0.0 (safer population).
        # Method: Scale alpha inversely and beta proportionally with variance.
        elif dist_def["family"] == "beta":
            if "alpha" in params and "beta" in params:
                alpha = params["alpha"]
                beta_param = params["beta"]
                # Risk multiplier > 1.0 means higher risk: boost alpha, shrink beta
                # This shifts the mode toward 1.0 (more anomalies)
                if var_multi > 1.0:
                    risk_shift = min(var_multi, 5.0)  # Cap to prevent degenerate shapes
                    params["alpha"] = round(alpha * risk_shift, 4)
                    params["beta"] = round(max(0.5, beta_param / risk_shift), 4)
                elif var_multi < 1.0:
                    # Lower risk: boost beta, shrink alpha → safer distribution
                    safety_shift = max(var_multi, 0.2)
                    params["alpha"] = round(max(0.5, alpha * safety_shift), 4)
                    params["beta"] = round(beta_param / safety_shift, 4)

    return scaled_dists
