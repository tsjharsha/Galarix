# =====================================================
# SYNONYM NORMALIZER — Standardize messy user language
# =====================================================
# Converts fuzzy, informal, or variant terms into
# canonical values that the rest of the system expects.
#
# Examples:
#   "big" → "large"
#   "cheap" → "low"
#   "everyday" → "daily"
#
# FIX: Fuzzy match now uses word boundaries to prevent
# substring false positives (e.g. "wide" inside "worldwide").
#
# NEVER throws. Returns input unchanged if no synonym found.
# =====================================================

import re
from typing import Any, Dict

from stage_1_5.constants import (
    SCALE_SYNONYMS,
    RISK_SYNONYMS,
    FREQUENCY_SYNONYMS,
)


def normalize_contract_synonyms(contract: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize all string values in the contract's intent
    using synonym maps.

    Args:
        contract: Stage 1 contract dict

    Returns:
        Same contract with normalized intent values
    """
    try:
        intent = contract.get("intent", {})
        if not isinstance(intent, dict):
            contract["intent"] = {}
            return contract

        # ── Normalize scale ──
        raw_scale = intent.get("scale")
        if raw_scale is not None:
            normalized = _normalize_value(str(raw_scale).lower().strip(), SCALE_SYNONYMS)
            intent["scale"] = normalized

        # ── Normalize risk ──
        raw_risk = intent.get("risk")
        if raw_risk is not None:
            normalized = _normalize_value(str(raw_risk).lower().strip(), RISK_SYNONYMS)
            intent["risk"] = normalized

        # ── Normalize frequency ──
        raw_freq = intent.get("frequency")
        if raw_freq is not None:
            normalized = _normalize_value(str(raw_freq).lower().strip(), FREQUENCY_SYNONYMS)
            intent["frequency"] = normalized

        # ── Normalize categories (lowercase, strip whitespace) ──
        raw_cats = intent.get("categories", [])
        if isinstance(raw_cats, list):
            intent["categories"] = [
                str(c).lower().strip()
                for c in raw_cats
                if c is not None and str(c).strip()
            ]

        contract["intent"] = intent
        return contract

    except Exception:
        # Safety — return contract unchanged
        return contract


def _normalize_value(value: str, synonym_map: Dict[str, str]) -> str:
    """
    Look up a value in a synonym map.
    Returns the canonical form, or the original value if not found.

    Matching priority:
        1. Direct exact match (fastest)
        2. Word-boundary regex match (prevents substring false positives)
           e.g. "wide" will NOT match inside "worldwide"
    """
    if not value:
        return value

    # ── Direct exact match ──
    if value in synonym_map:
        return synonym_map[value]

    # ── Word-boundary fuzzy match ──
    # Sort by length descending so longer synonyms match before shorter ones.
    # e.g. "per month" matches before "month" inside "per month".
    sorted_synonyms = sorted(synonym_map.keys(), key=len, reverse=True)

    for synonym in sorted_synonyms:
        pattern = r"\b" + re.escape(synonym) + r"\b"
        if re.search(pattern, value):
            return synonym_map[synonym]

    # No match — return as-is (will be caught by validator later)
    return value