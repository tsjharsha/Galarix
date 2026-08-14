# =====================================================
# DEFAULT FILLER — Fill all missing fields
# =====================================================
# The safety net that ensures no field is ever None
# or missing. Every field gets a safe, sensible default.
#
# Called AFTER synonym normalization but BEFORE validation.
#
# NEVER throws. ALWAYS fills every gap.
# =====================================================

from typing import Any, Dict

from stage_1_5.constants import DEFAULTS


def fill_defaults(contract: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fill all missing or None fields in the contract with defaults.

    Args:
        contract: Partially complete contract from Stage 1

    Returns:
        Contract with all required fields populated
    """
    try:
        # ── Ensure top-level fields exist ──
        if not contract.get("entity"):
            contract["entity"] = DEFAULTS["entity"]

        if not contract.get("entities"):
            contract["entities"] = [contract["entity"]]

        if "intent" not in contract or not isinstance(contract.get("intent"), dict):
            contract["intent"] = {}

        if "variables" not in contract or not isinstance(contract.get("variables"), dict):
            contract["variables"] = {}

        if "meta" not in contract or not isinstance(contract.get("meta"), dict):
            contract["meta"] = {}

        # ── Fill intent fields ──
        intent = contract["intent"]

        if intent.get("scale") is None or intent.get("scale") == "":
            intent["scale"] = DEFAULTS["scale"]

        if intent.get("risk") is None or intent.get("risk") == "":
            intent["risk"] = DEFAULTS["risk"]

        if not intent.get("categories") or not isinstance(intent.get("categories"), list):
            intent["categories"] = list(DEFAULTS["categories"])  # Copy, don't reference
        elif len(intent["categories"]) == 0:
            intent["categories"] = list(DEFAULTS["categories"])

        if intent.get("frequency") is None or intent.get("frequency") == "":
            intent["frequency"] = DEFAULTS["frequency"]

        contract["intent"] = intent

        # ── Fill meta fields ──
        meta = contract["meta"]

        if "confidence" not in meta or meta["confidence"] is None:
            meta["confidence"] = DEFAULTS["confidence"]

        if not meta.get("source"):
            meta["source"] = DEFAULTS["source"]

        if "is_multi" not in meta:
            meta["is_multi"] = len(contract.get("entities", [])) > 1

        contract["meta"] = meta

        # ── Ensure prompt exists ──
        if "prompt" not in contract:
            contract["prompt"] = ""

        return contract

    except Exception:
        # Emergency: return contract with absolute minimum defaults
        contract.setdefault("entity", DEFAULTS["entity"])
        contract.setdefault("entities", [DEFAULTS["entity"]])
        contract.setdefault("intent", {
            "scale": DEFAULTS["scale"],
            "risk": DEFAULTS["risk"],
            "categories": list(DEFAULTS["categories"]),
            "frequency": DEFAULTS["frequency"],
        })
        contract.setdefault("meta", {
            "confidence": 0.0,
            "source": "prompt",
            "is_multi": False,
        })
        return contract
