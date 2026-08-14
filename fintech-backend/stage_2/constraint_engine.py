# =====================================================
# CONSTRAINT ENGINE
# =====================================================
# Binds infinite statistical distributions inside safety
# mathematical bounds (min, max) so generation logic
# does not throw errors from impossible values.
# =====================================================

from typing import Dict, Any
import copy
import math

def apply_constraints(scaled_distributions: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
    """
    Loops through the scaled distributions and structurally
    embeds mathematical bounds from the DataContract.
    """
    final_dists = copy.deepcopy(scaled_distributions)

    for var_name, bounds in constraints.items():
        if var_name not in final_dists:
            continue
            
        # Standardize constraint formatting directly onto the distribution dict
        # Stage 3 will use this to generate TruncatedNormal or clamped values
        final_dists[var_name]["bounds"] = {}
        if "min" in bounds:
            final_dists[var_name]["bounds"]["min"] = bounds["min"]
        if "max" in bounds:
            final_dists[var_name]["bounds"]["max"] = bounds["max"]
            
        # Mathematical safety: ensure min <= max if both exist
        if "min" in bounds and "max" in bounds:
            if bounds["min"] > bounds["max"]:
                # Auto-fix user logical errors from the prompt
                final_dists[var_name]["bounds"]["min"] = bounds["max"]
                final_dists[var_name]["bounds"]["max"] = bounds["min"]

        # Hard-clamp the base mathematical parameters to survive the constraints
        params = final_dists[var_name].get("params", {})
        c_min = final_dists[var_name]["bounds"].get("min")
        c_max = final_dists[var_name]["bounds"].get("max")
        
        # Clamp normal 'mean'
        if "mean" in params:
            if c_max is not None and params["mean"] > c_max:
                params["mean"] = float(c_max)
            if c_min is not None and params["mean"] < c_min:
                params["mean"] = float(c_min)

        # Clamp morphed 'loc' (Student-T / Cauchy after Black Swan morphing)
        if "loc" in params:
            if c_max is not None and params["loc"] > c_max:
                params["loc"] = float(c_max)
            if c_min is not None and params["loc"] < c_min:
                params["loc"] = float(c_min)
                
        # Clamp lognormal 'mu'
        if "mu" in params:
            if c_max is not None and c_max > 0:
                log_max = math.log(c_max)
                if params["mu"] > log_max:
                    params["mu"] = round(log_max, 4)
            if c_min is not None and c_min > 0:
                log_min = math.log(c_min)
                if params["mu"] < log_min:
                    params["mu"] = round(log_min, 4)

    return final_dists
