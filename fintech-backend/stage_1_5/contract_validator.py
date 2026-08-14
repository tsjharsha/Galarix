# =====================================================
# CONTRACT VALIDATOR — Final structural validation
# =====================================================
# The last gate before the contract leaves Stage 1.5.
# Ensures the contract has the EXACT shape Stage 2 expects.
#
# Checks:
#   - All required top-level keys exist
#   - All required intent keys exist
#   - All required meta keys exist
#   - Variables dict is non-empty
#   - Entity is valid
#   - No None values in critical fields
#
# NEVER throws. Fixes everything silently.
# =====================================================

from typing import Any, Dict, List

from stage_1_5.constants import (
    REQUIRED_CONTRACT_KEYS,
    REQUIRED_INTENT_KEYS,
    REQUIRED_META_KEYS,
    DEFAULTS,
    SUPPORTED_ENTITIES,
)


def validate_contract(contract: Dict[str, Any]) -> Dict[str, Any]:
    """
    Final structural validation of the contract.

    Args:
        contract: Nearly-complete contract from enrichment pipeline

    Returns:
        {
            "valid": True/False,
            "fixes_applied": [...],
            "contract": {...}  # The validated/fixed contract
        }
    """
    fixes = []

    try:
        # ── Check top-level keys ──
        for key in REQUIRED_CONTRACT_KEYS:
            if key not in contract:
                contract[key] = _get_default_for_key(key)
                fixes.append(f"added missing key: '{key}'")

        # ── Check intent keys ──
        intent = contract.get("intent", {})
        if not isinstance(intent, dict):
            contract["intent"] = {
                "scale": DEFAULTS["scale"],
                "risk": DEFAULTS["risk"],
                "categories": list(DEFAULTS["categories"]),
                "frequency": DEFAULTS["frequency"],
            }
            fixes.append("intent was not a dict → reset")
        else:
            for key in REQUIRED_INTENT_KEYS:
                if key not in intent or intent[key] is None:
                    intent[key] = DEFAULTS.get(key, "")
                    fixes.append(f"intent.{key} was missing/None → set default")
            contract["intent"] = intent

        # ── Check meta keys ──
        meta = contract.get("meta", {})
        if not isinstance(meta, dict):
            contract["meta"] = {
                "confidence": 0.0,
                "source": DEFAULTS["source"],
                "is_multi": False,
            }
            fixes.append("meta was not a dict → reset")
        else:
            for key in REQUIRED_META_KEYS:
                if key not in meta or meta[key] is None:
                    if key == "confidence":
                        meta[key] = 0.0
                    elif key == "source":
                        meta[key] = DEFAULTS["source"]
                    elif key == "is_multi":
                        meta[key] = len(contract.get("entities", [])) > 1
                    fixes.append(f"meta.{key} was missing/None → set default")
            contract["meta"] = meta

        # ── Check entity validity ──
        entity = contract.get("entity", "")
        if not entity or entity not in SUPPORTED_ENTITIES:
            contract["entity"] = DEFAULTS["entity"]
            fixes.append(f"entity '{entity}' invalid → set to '{DEFAULTS['entity']}'")

        # ── Check entities list ──
        entities = contract.get("entities", [])
        if not isinstance(entities, list) or not entities:
            contract["entities"] = [contract["entity"]]
            fixes.append("entities list was empty/invalid → set from entity")

        # ── Check variables ──
        variables = contract.get("variables", {})
        if not isinstance(variables, dict) or not variables:
            contract["variables"] = {
                "record_id": {"type": "string", "description": "Unique record identifier"},
                "value": {"type": "continuous", "description": "Primary numeric value"},
                "category": {"type": "categorical", "description": "Record category"},
                "timestamp": {"type": "datetime", "description": "Record timestamp"},
            }
            fixes.append("variables was empty → set generic defaults")

        # ── Check distributions ──
        if not isinstance(contract.get("distributions"), dict):
            contract["distributions"] = {}

        # ── Check dependencies ──
        if not isinstance(contract.get("dependencies"), dict):
            contract["dependencies"] = {
                "conditionals": [],
                "correlations": [],
                "derived": [],
            }
        else:
            deps = contract["dependencies"]
            deps.setdefault("conditionals", [])
            deps.setdefault("correlations", [])
            deps.setdefault("derived", [])

        # ── Check constraints ──
        if not isinstance(contract.get("constraints"), dict):
            contract["constraints"] = {}

        # ── Confidence clamp ──
        conf = contract.get("meta", {}).get("confidence", 0)
        if not isinstance(conf, (int, float)):
            contract["meta"]["confidence"] = 0.0
            fixes.append("confidence was not numeric → set to 0.0")
        else:
            contract["meta"]["confidence"] = round(max(0.0, min(1.0, float(conf))), 3)

        # ── Record validation metadata ──
        contract["meta"]["validated"] = True
        if fixes:
            contract["meta"]["validation_fixes"] = fixes

        is_valid = len(fixes) == 0

        return {
            "valid": is_valid,
            "fixes_applied": fixes,
            "contract": contract,
        }

    except Exception as e:
        # Even the validator can't crash
        return {
            "valid": False,
            "fixes_applied": [f"validator exception: {str(e)}"],
            "contract": _get_emergency_contract(),
        }


def _get_default_for_key(key: str) -> Any:
    """Get the default value for a missing top-level key."""
    defaults_map = {
        "entity": DEFAULTS["entity"],
        "entities": [DEFAULTS["entity"]],
        "intent": {
            "scale": DEFAULTS["scale"],
            "risk": DEFAULTS["risk"],
            "categories": list(DEFAULTS["categories"]),
            "frequency": DEFAULTS["frequency"],
        },
        "variables": {},
        "distributions": {},
        "dependencies": {"conditionals": [], "correlations": [], "derived": []},
        "constraints": {},
        "meta": {"confidence": 0.0, "source": DEFAULTS["source"], "is_multi": False},
    }
    return defaults_map.get(key, {})


def _get_emergency_contract() -> Dict[str, Any]:
    """Absolute fallback contract."""
    return {
        "entity": DEFAULTS["entity"],
        "entities": [DEFAULTS["entity"]],
        "intent": {
            "scale": DEFAULTS["scale"],
            "risk": DEFAULTS["risk"],
            "categories": list(DEFAULTS["categories"]),
            "frequency": DEFAULTS["frequency"],
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
            "validation_fixes": ["emergency_fallback"],
        },
    }
