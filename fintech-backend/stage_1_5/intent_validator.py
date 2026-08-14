# =====================================================
# INTENT VALIDATOR — Validate all intent field values
# =====================================================
# Ensures every intent field contains a valid, recognized
# value. Invalid values are clamped to their closest
# valid match or reset to defaults.
#
# Called AFTER default filler (all fields are present).
#
# NEVER throws. Fixes everything in-place.
# =====================================================

from typing import Any, Dict

from stage_1_5.constants import (
    VALID_SCALES,
    VALID_RISKS,
    VALID_FREQUENCIES,
    DEFAULTS,
)


def validate_intent(contract: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate all intent fields and clamp invalid values.

    Args:
        contract: Contract with intent fields populated

    Returns:
        Contract with all intent values guaranteed valid
    """
    try:
        intent = contract.get("intent", {})
        if not isinstance(intent, dict):
            contract["intent"] = _get_default_intent()
            return contract

        fixes = []

        # ── Validate scale ──
        scale = intent.get("scale", "")
        if scale not in VALID_SCALES:
            intent["scale"] = DEFAULTS["scale"]
            if scale:
                fixes.append(f"scale '{scale}' → '{DEFAULTS['scale']}'")

        # ── Validate risk ──
        risk = intent.get("risk", "")
        if risk not in VALID_RISKS:
            intent["risk"] = DEFAULTS["risk"]
            if risk:
                fixes.append(f"risk '{risk}' → '{DEFAULTS['risk']}'")

        # ── Validate frequency ──
        frequency = intent.get("frequency", "")
        if frequency not in VALID_FREQUENCIES:
            intent["frequency"] = DEFAULTS["frequency"]
            if frequency:
                fixes.append(f"frequency '{frequency}' → '{DEFAULTS['frequency']}'")

        # ── Validate categories ──
        categories = intent.get("categories", [])
        if not isinstance(categories, list):
            intent["categories"] = list(DEFAULTS["categories"])
            fixes.append("categories was not a list → reset")
        elif len(categories) == 0:
            intent["categories"] = list(DEFAULTS["categories"])
        else:
            # Clean up: ensure all items are non-empty strings
            cleaned = [
                str(c).strip().lower()
                for c in categories
                if c is not None and str(c).strip()
            ]
            intent["categories"] = cleaned if cleaned else list(DEFAULTS["categories"])

        contract["intent"] = intent

        # Log fixes if any
        if fixes:
            meta = contract.get("meta", {})
            meta["intent_fixes"] = fixes
            contract["meta"] = meta

        return contract

    except Exception:
        contract["intent"] = _get_default_intent()
        return contract


def _get_default_intent() -> Dict[str, Any]:
    """Return a complete default intent."""
    return {
        "scale": DEFAULTS["scale"],
        "risk": DEFAULTS["risk"],
        "categories": list(DEFAULTS["categories"]),
        "frequency": DEFAULTS["frequency"],
    }
