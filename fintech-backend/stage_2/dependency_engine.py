# =====================================================
# DEPENDENCY ENGINE
# =====================================================
# Processes conditional logic (IF X THEN Y) mapped in 
# the schema registry into pre-calculated parameters
# for generation.
# =====================================================

from typing import Dict, Any, List

def register_dependencies(contract_deps: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts conditionals, correlations, and derived formulas.
    Stage 2 simply validates and standardizes these rules 
    so Stage 3 can execute them procedurally during row generation.
    """
    # Stage 3 uses this block to evaluate rows procedurally.
    # Stage 2 simply sanitizes it.
    
    clean_deps = {
        "conditionals": contract_deps.get("conditionals", []),
        "correlations": contract_deps.get("correlations", []),
        "derived": contract_deps.get("derived", [])
    }
    
    # Ensure all conditionals have valid structural shapes
    validated_conditionals = []
    for cond in clean_deps["conditionals"]:
        if "if" in cond and "then" in cond:
            validated_conditionals.append(cond)
    clean_deps["conditionals"] = validated_conditionals
    
    return clean_deps
