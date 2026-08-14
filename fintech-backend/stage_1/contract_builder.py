# =====================================================
# CONTRACT BUILDER — Stage 1 Orchestrator
# =====================================================
# The main entry point for Stage 1.
# Calls all sub-modules in order and assembles the
# raw Stage 1 contract. This contract may be incomplete
# — that's by design. Stage 1.5 handles all fixups.
#
# NEVER throws. ALWAYS returns a dict.
# =====================================================

from typing import Any, Dict

from stage_1.input_router import route_input
from stage_1.entity_resolver import resolve_entity
from stage_1.intent_extractor import extract_intent
from stage_1.variable_mapper import map_variables
from stage_1.confidence_scorer import score_confidence
from stage_1.temporal_intent_extractor import extract_temporal_intent


def build_stage1_contract(raw_input: Any, region: str = "US") -> Dict[str, Any]:
    """
    Full Stage 1 pipeline: raw input → partial contract.

    Pipeline:
        1. Route input (detect prompt vs structured)
        2. Resolve entity (keyword + semantic + fallback)
        3. Extract intent (scale, risk, categories, frequency)
        3.5. Extract temporal intent (H2 — time-series signals)
        4. Map variables (entity → variable definitions)
        5. Score confidence
        6. Assemble contract

    Args:
        raw_input: Any — string prompt, dict, or anything else
        region: str — ISO country code for localization (e.g. 'US', 'UK', 'IN')

    Returns:
        Stage 1 contract dict (may be incomplete — that's OK)
    """
    try:
        # ── Step 1: Route Input ──
        routed = route_input(raw_input)

        # ── Step 2: Resolve Entity ──
        entity_result = resolve_entity(routed)

        # ── Step 3: Extract Intent ──
        intent = extract_intent(routed)
        intent["region"] = region.upper()  # Inject localization region

        # ── Step 3.5: Extract Temporal Intent (Horizon 2) ──
        prompt_str = routed.get("prompt", "")
        temporal_intent = extract_temporal_intent(prompt_str) if isinstance(prompt_str, str) else None

        # ── Step 4: Map Variables ──
        entities = entity_result.get("entities", ["generic"])
        variables = map_variables(entities)

        # ── Step 5: Score Confidence ──
        confidence = score_confidence(routed, entity_result, intent)

        # ── Step 6: Assemble Contract ──
        primary_entity = entity_result.get("primary_entity", "generic")
        is_multi = entity_result.get("is_multi", False)

        contract = {
            "prompt": routed.get("prompt", ""),
            "entity": primary_entity if not is_multi else "multi_entity",
            "entities": entities,
            "intent": intent,
            "temporal": temporal_intent,  # H2: None when no temporal signals
            "variables": variables,
            "meta": {
                "confidence": confidence,
                "source": routed.get("source", "prompt"),
                "method": entity_result.get("method", "fallback"),
                "is_multi": is_multi,
                "entity_scores": entity_result.get("scores", {}),
            },
        }

        _log_stage1(contract)
        return contract

    except ValueError as ve:
        if str(ve) == "NO_FINANCIAL_INTENT":
            raise ve
        return _emergency_contract(raw_input, str(ve))
    except Exception as e:
        # Absolute safety — even if everything fails, return something
        return _emergency_contract(raw_input, str(e))


def _log_stage1(contract: dict) -> None:
    """Debug logging for Stage 1 output."""
    entity = contract.get("entity", "?")
    entities = contract.get("entities", [])
    confidence = contract.get("meta", {}).get("confidence", 0)
    method = contract.get("meta", {}).get("method", "?")
    intent = contract.get("intent", {})

    print("\n" + "-"*50)
    print(f"[*] STAGE 1 CONTRACT BUILT")
    print(f"   Entity: {entity} | Entities: {entities}")
    print(f"   Method: {method} | Confidence: {confidence:.2f}")
    print(f"   Intent: scale={intent.get('scale')}, risk={intent.get('risk')}, "
          f"freq={intent.get('frequency')}, cats={intent.get('categories')}")
    print(f"   Variables: {len(contract.get('variables', {}))} fields")
    print("-"*50)


def _emergency_contract(raw_input: Any, error: str) -> Dict[str, Any]:
    """Last-resort contract when everything fails."""
    return {
        "prompt": str(raw_input)[:200] if raw_input else "",
        "entity": "generic",
        "entities": ["generic"],
        "intent": {
            "scale": None,
            "risk": None,
            "categories": [],
            "frequency": None,
        },
        "variables": {
            "record_id": {"type": "string", "description": "Unique record identifier"},
            "value": {"type": "continuous", "description": "Primary numeric value"},
            "category": {"type": "categorical", "description": "Record category"},
            "timestamp": {"type": "datetime", "description": "Record timestamp"},
        },
        "meta": {
            "confidence": 0.0,
            "source": "prompt",
            "method": "emergency_fallback",
            "is_multi": False,
            "entity_scores": {},
            "error": error,
        },
    }
