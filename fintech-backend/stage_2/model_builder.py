# =====================================================
# STAGE 2: MODEL BUILDER (Orchestrator)
# =====================================================
# The primary entry point for Stage 2.
# Transforms a declarative Data Contract from Stage 1.5
# into a deterministic mathematical Statistical Model Config.
# =====================================================

from typing import Dict, Any

from stage_2.behavior_mapper import map_behavior
from stage_2.scaling_engine import apply_scale_to_distributions
from stage_2.dependency_engine import register_dependencies
from stage_2.covariance_engine import build_covariance_matrix
from stage_2.constraint_engine import apply_constraints
from stage_2.validator import validate_statistical_model
from stage_2.fallback_system import get_fallback_model
from stage_2.temporal_model_compiler import compile_temporal_model



def build_statistical_model(contract: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main orchestration function for Stage 2.
    Accepts: Stage 1.5 Guaranteed Contract
    Returns: Stage 2 Mathematically Valid Statistical Model
    """
    try:
        # 1. Map intent to continuous behaviors (Tensors)
        prompt = contract.get("prompt", "")
        intent = contract.get("intent", {})
        behavior_mods = map_behavior(prompt, intent)

        # 2. Scale distributions mathematically
        raw_distributions = contract.get("distributions", {})
        scaled_distributions = apply_scale_to_distributions(raw_distributions, behavior_mods)

        # 3. Apply min/max constraints
        raw_constraints = contract.get("constraints", {})
        bounded_distributions = apply_constraints(scaled_distributions, raw_constraints)

        # 4. Generate the Dynamic Covariance Matrix (Patentable Correlation Logic)
        variables = contract.get("variables", {})
        covariance_matrix = build_covariance_matrix(bounded_distributions, behavior_mods, variables)

        # 4.5. Compile Temporal Model (Horizon 2 — Time-Series Engine)
        temporal_config = contract.get("temporal")
        temporal_model = None
        if temporal_config and temporal_config.get("is_temporal"):
            temporal_model = compile_temporal_model(temporal_config, behavior_mods, contract)
            print(f"[Stage 2] Temporal model compiled: {temporal_config.get('frequency')} × {temporal_config.get('periods')} periods")

        # 5. Standardize dependencies for Stage 3
        raw_dependencies = contract.get("dependencies", {})
        execution_dependencies = register_dependencies(raw_dependencies)

        # 6. Build the final "Monster" model payload
        model = {
            "entity": contract.get("entity", "unknown"),
            "meta": {
                "confidence": contract.get("meta", {}).get("confidence", 1.0),
                "is_multi": contract.get("meta", {}).get("is_multi", False),
                "tensor_signature": behavior_mods.get("tensor_signature"),
                "is_temporal": temporal_model is not None,
            },
            "behavior_used": behavior_mods,
            "parameters": bounded_distributions,
            "variables": contract.get("variables", {}),
            "constraints": raw_constraints,
            "covariance": covariance_matrix,
            "dependencies": execution_dependencies,
            "temporal": temporal_model,  # H2: None when static
        }


        # 7. Validate math sanity
        was_valid, repairs = validate_statistical_model(model)
        if not was_valid:
            print(f"[Stage 2] Validator auto-repaired {len(repairs)} issue(s):")
            for r in repairs[:5]:
                print(f"  → {r}")
            
        return model

    except Exception as e:
        print(f"\n⚠️ STAGE 2 CRITICAL ERROR: {e}")
        return get_fallback_model()
