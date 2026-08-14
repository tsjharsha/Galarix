# =====================================================
# UNIFIED PIPELINE — Stage 1 → Stage 1.5 → Contract
# =====================================================
# The single entry point for the entire system.
#
# Accepts: str (prompt) or dict (structured input)
# Returns: Always-valid contract dict
#
# NEVER throws. NEVER returns None. NEVER returns incomplete data.
# =====================================================

from typing import Any, Dict

from stage_1.contract_builder import build_stage1_contract
from stage_1_5.enrichment_engine import enrich_contract


def run_pipeline(raw_input: Any) -> Dict[str, Any]:
    """
    Full Stage 1 → Stage 1.5 pipeline.

    This function is the ONLY thing the rest of the system
    (Stage 2, API, etc.) needs to call. Everything else is
    internal implementation detail.

    Args:
        raw_input: Any — string prompt, dict, or anything else

    Returns:
        Always-valid contract dict with guaranteed structure:
        {
            "entity": str,              # ALWAYS present
            "entities": [str],          # ALWAYS present
            "intent": {
                "scale": str,           # ALWAYS present
                "risk": str,            # ALWAYS present
                "categories": [str],    # ALWAYS present
                "frequency": str,       # ALWAYS present
            },
            "variables": {...},         # ALWAYS present
            "distributions": {...},     # ALWAYS present
            "dependencies": {...},      # ALWAYS present
            "constraints": {...},       # ALWAYS present
            "meta": {
                "confidence": float,    # ALWAYS present
                "source": str,          # ALWAYS present
                "is_multi": bool,       # ALWAYS present
            },
        }
    """
    try:
        print(f"\n{'='*60}")
        print(f"[START] GALARIX PIPELINE — Processing Input")
        print(f"   Input type: {type(raw_input).__name__}")
        if isinstance(raw_input, str):
            print(f"   Prompt: \"{raw_input[:80]}{'...' if len(str(raw_input)) > 80 else ''}\"")
        elif isinstance(raw_input, dict):
            print(f"   Structured: {list(raw_input.keys())}")
        print(f"{'='*60}")

        # ── Stage 1: Intent & Contract Builder ──
        stage1_contract = build_stage1_contract(raw_input)

        # ── Stage 1.5: Normalization & Enrichment ──
        final_contract = enrich_contract(stage1_contract)

        print(f"\n{'='*60}")
        print(f"[OK] PIPELINE COMPLETE")
        print(f"   Entity: {final_contract.get('entity')}")
        print(f"   Confidence: {final_contract.get('meta', {}).get('confidence', 0):.3f}")
        print(f"{'='*60}\n")

        return final_contract

    except Exception as e:
        # This should NEVER happen because both stages have their own
        # safety nets, but just in case...
        print(f"\n[ERROR] PIPELINE EMERGENCY: {e}")
        return _absolute_fallback(raw_input)


def _absolute_fallback(raw_input: Any) -> Dict[str, Any]:
    """
    Nuclear fallback. If absolutely everything fails,
    return a minimal valid contract.
    """
    return {
        "entity": "generic",
        "entities": ["generic"],
        "prompt": str(raw_input)[:200] if raw_input else "",
        "intent": {
            "scale": "medium",
            "risk": "low",
            "categories": ["general"],
            "frequency": "monthly",
        },
        "variables": {
            "record_id": {"type": "string", "description": "Unique record identifier"},
            "value": {"type": "continuous", "description": "Primary numeric value"},
            "category": {"type": "categorical", "description": "Record category"},
            "timestamp": {"type": "datetime", "description": "Record timestamp"},
        },
        "distributions": {},
        "dependencies": {"conditionals": [], "correlations": [], "derived": []},
        "constraints": {},
        "meta": {
            "confidence": 0.0,
            "source": "prompt",
            "is_multi": False,
            "validated": True,
            "pipeline_error": True,
        },
    }
