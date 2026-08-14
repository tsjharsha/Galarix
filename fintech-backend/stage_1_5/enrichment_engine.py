# =====================================================
# ENRICHMENT ENGINE — Stage 1.5 Orchestrator
# =====================================================
# The main entry point for Stage 1.5.
# Takes a raw Stage 1 contract and transforms it into
# a clean, normalized, guaranteed-valid contract.
#
# Pipeline:
#   1. Normalize synonyms
#   2. Fill defaults
#   3. Guarantee entity
#   4. Validate intent
#   5. Attach schema (distributions, dependencies, constraints)
#   6. Final contract validation
#
# FIXES:
#   - Removed dead imports (get_distributions, get_dependencies,
#     get_constraints) — _attach_schema_data reads these directly
#     from the schema dict returned by get_schema/get_combined_schema.
#   - Variable overwrite logic no longer uses method == "fallback"
#     as a proxy. Schema registry is now always the authority for
#     variables — prevents correct Stage 1 variables being overwritten.
#
# NEVER throws. ALWAYS returns a valid contract.
# =====================================================

import copy
from typing import Any, Dict

from stage_1_5.synonym_normalizer import normalize_contract_synonyms
from stage_1_5.default_filler import fill_defaults
from stage_1_5.entity_guarantor import guarantee_entity
from stage_1_5.intent_validator import validate_intent
from stage_1_5.contract_validator import validate_contract
from stage_1_5.schema_registry import (
    get_schema,
    get_combined_schema,
)
from stage_1_5.localization_engine import apply_localization


def enrich_contract(stage1_contract: Dict[str, Any]) -> Dict[str, Any]:
    """
    Full Stage 1.5 pipeline: raw contract → guaranteed valid contract.

    This is THE safety net. No matter what Stage 1 produces,
    this function ALWAYS returns a contract that Stage 2 can
    trust blindly.

    Pipeline:
        1. Deep copy (don't mutate input)
        2. Normalize synonyms (big→large, cheap→low)
        3. Fill defaults (scale→medium, risk→low)
        4. Guarantee entity (always valid)
        5. Validate intent (all values in valid range)
        6. Attach schema data (distributions, dependencies, constraints)
        7. Final contract validation (structural checks)

    Args:
        stage1_contract: Output from Stage 1 contract_builder

    Returns:
        Always-valid contract dict with guaranteed structure
    """
    try:
        # ── Step 0: Deep copy — never mutate the original ──
        contract = copy.deepcopy(stage1_contract)

        # ── Step 1: Normalize synonyms ──
        contract = normalize_contract_synonyms(contract)

        # ── Step 2: Fill defaults ──
        contract = fill_defaults(contract)

        # ── Step 3: Guarantee entity ──
        contract = guarantee_entity(contract)

        # ── Step 4: Validate intent ──
        contract = validate_intent(contract)

        # ── Step 5: Attach schema data ──
        contract = _attach_schema_data(contract)

        # ── Step 5.5: Apply Regional Localization ──
        contract = apply_localization(contract)

        # ── Step 6: Final contract validation ──
        validation_result = validate_contract(contract)
        final_contract = validation_result["contract"]

        # ── Log result ──
        _log_enrichment(final_contract, validation_result)

        return final_contract

    except Exception as e:
        # ABSOLUTE SAFETY NET
        # Even if the entire enrichment pipeline crashes,
        # we still return a valid contract.
        print(f"\n[!] ENRICHMENT ENGINE EMERGENCY: {e}")
        return _emergency_contract(stage1_contract)


def _attach_schema_data(contract: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attach distributions, dependencies, and constraints from
    the schema registry based on the resolved entity.

    FIX: Variables are now ALWAYS sourced from the schema registry,
    which is the single source of truth. This prevents the previous
    bug where method == "fallback" was used as a proxy to decide
    whether to overwrite variables — an unreliable heuristic that
    could corrupt correct Stage 1 variable mappings.

    The schema registry variables are always more complete and
    consistent than what Stage 1 produces, so we always prefer them.
    If no schema exists for the entity, we fall back to whatever
    Stage 1 produced (preserving existing behavior for unknown entities).
    """
    entity = contract.get("entity", "generic")
    entities = contract.get("entities", [entity])

    # Always use get_combined_schema so Ontology Graph expansion applies!
    # get_combined_schema normalizes output and expands parents 
    # dynamically even if len(entities) == 1.
    combined = get_combined_schema(entities)
    
    contract["variables"] = combined.get("variables", contract.get("variables", {}))
    contract["distributions"] = combined.get("distributions", {})
    contract["dependencies"] = combined.get(
        "dependencies", {"conditionals": [], "correlations": [], "derived": []}
    )
    contract["constraints"] = combined.get("constraints", {})

    return contract


def _log_enrichment(contract: dict, validation_result: dict) -> None:
    """Debug logging for Stage 1.5 output."""
    entity = contract.get("entity", "?")
    entities = contract.get("entities", [])
    intent = contract.get("intent", {})
    confidence = contract.get("meta", {}).get("confidence", 0)
    is_valid = validation_result.get("valid", False)
    fixes = validation_result.get("fixes_applied", [])

    print("\n" + "-"*50)
    print(f"[*] STAGE 1.5 ENRICHMENT COMPLETE")
    print(f"   Entity: {entity} | Entities: {entities}")
    print(f"   Intent: {intent}")
    print(f"   Confidence: {confidence:.3f}")
    print(f"   Variables: {len(contract.get('variables', {}))} fields")
    print(f"   Distributions: {len(contract.get('distributions', {}))} defined")
    print(f"   Dependencies: {len(contract.get('dependencies', {}).get('conditionals', []))} conditionals")
    print(f"   Constraints: {len(contract.get('constraints', {}))} defined")
    print(f"   Valid: {'Yes' if is_valid else 'No (fixed)'}")
    if fixes:
        print(f"   Fixes: {len(fixes)} applied")
        for fix in fixes[:5]:
            print(f"     * {fix}")
    print("-" * 50)


def _emergency_contract(original: Dict[str, Any]) -> Dict[str, Any]:
    """
    Absolute last-resort contract when enrichment fails completely.
    Uses the generic schema as base.
    Preserves the region from the original contract to prevent
    silent localization resets.
    """
    generic = get_schema("generic") or {}
    # Preserve region from whatever the original contract had
    original_region = "US"
    if original and isinstance(original, dict):
        original_region = original.get("intent", {}).get("region", "US")

    return {
        "entity": "generic",
        "entities": ["generic"],
        "prompt": str(original.get("prompt", ""))[:200] if original else "",
        "intent": {
            "scale": "medium",
            "risk": "low",
            "categories": ["general"],
            "frequency": "monthly",
            "region": original_region,
        },
        "variables": generic.get("variables", {
            "record_id": {"type": "string", "description": "Unique record identifier"},
            "value": {"type": "continuous", "description": "Primary numeric value"},
            "category": {"type": "categorical", "description": "Record category"},
            "timestamp": {"type": "datetime", "description": "Record timestamp"},
        }),
        "distributions": generic.get("distributions", {}),
        "dependencies": generic.get(
            "dependencies", {"conditionals": [], "correlations": [], "derived": []}
        ),
        "constraints": generic.get("constraints", {}),
        "meta": {
            "confidence": 0.0,
            "source": "prompt",
            "is_multi": False,
            "validated": True,
            "enrichment_error": True,
        },
    }