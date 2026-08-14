# =====================================================
# VALIDATOR
# =====================================================
# The absolute strict gatekeeper for Stage 2. 
# Enforces basic mathematical reality across the model.
# Returns (is_valid, repairs_applied) so the orchestrator
# can log exactly what was auto-fixed.
# =====================================================

from typing import Dict, Any, List, Tuple

def validate_statistical_model(model: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Ensures that standard deviations are positive, 
    categorical weights sum to 1.0 (or > 0), and all
    required parameters exist before handing off to Stage 3.
    
    Returns:
        (was_originally_valid, list_of_repairs_applied)
    """
    repairs = []
    try:
        parameters = model.get("parameters", {})
        
        # H2: Fix temporal GARCH parameters
        temporal = model.get("temporal")
        if temporal:
            profiles = temporal.get("temporal_profiles", {})
            for var_name, profile in profiles.items():
                if "garch" in profile:
                    alpha = profile["garch"].get("alpha", 0)
                    beta = profile["garch"].get("beta", 0)
                    if alpha + beta >= 1.0:
                        # Cap at 0.99 for stationarity
                        scale_factor = 0.99 / (alpha + beta)
                        profile["garch"]["alpha"] = alpha * scale_factor
                        profile["garch"]["beta"] = beta * scale_factor
                        repairs.append(f"{var_name}: GARCH α+β was {alpha+beta} (non-stationary) → scaled to 0.99")

        for var_name, dist_def in parameters.items():
            family = dist_def.get("family")
            
            # 1. Normal distributions must have std > 0
            if family == "normal":
                std = dist_def.get("params", {}).get("std", 0)
                if std <= 0:
                    dist_def["params"]["std"] = 0.01
                    repairs.append(f"{var_name}: normal std was {std} → set to 0.01")
            
            # 2. Lognormal distributions must have sigma > 0
            elif family == "lognormal":
                sigma = dist_def.get("params", {}).get("sigma", 0)
                if sigma <= 0:
                    dist_def["params"]["sigma"] = 0.01
                    repairs.append(f"{var_name}: lognormal sigma was {sigma} → set to 0.01")

            # 3. Student-T must have degrees of freedom > 0
            elif family == "student_t":
                df = dist_def.get("params", {}).get("df", 0)
                if df <= 0:
                    dist_def["params"]["df"] = 1.0
                    repairs.append(f"{var_name}: student_t df was {df} → set to 1.0")
                if dist_def["params"].get("scale", 0) <= 0:
                    dist_def["params"]["scale"] = 0.01
                    repairs.append(f"{var_name}: student_t scale was ≤0 → set to 0.01")

            # 4. Cauchy must have scale > 0
            elif family == "cauchy":
                if dist_def.get("params", {}).get("scale", 0) <= 0:
                    dist_def["params"]["scale"] = 1.0
                    repairs.append(f"{var_name}: cauchy scale was ≤0 → set to 1.0")

            # 5. Categoricals must have valid weights
            elif family == "categorical":
                weights = dist_def.get("weights", [])
                if not weights or sum(weights) <= 0:
                    length = len(weights) if weights else 1
                    dist_def["weights"] = [1.0 / length] * length
                    repairs.append(f"{var_name}: categorical weights were invalid → set uniform")
                    
        was_valid = len(repairs) == 0
        return (was_valid, repairs)
    except Exception as e:
        print(f"[Stage 2 Validator Error] {e}")
        return (False, [f"validator exception: {str(e)}"])

