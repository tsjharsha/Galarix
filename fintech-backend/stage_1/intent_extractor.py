# =====================================================
# INTENT EXTRACTOR — Extract behavioral signals
# =====================================================
# Extracts scale, risk, categories, and frequency from
# both prompt text and structured input. Returns None
# for any signal it can't confidently extract — Stage 1.5
# will fill defaults for anything missing.
#
# NEVER throws. Returns partial results when unsure.
# =====================================================

import re
from typing import Any, Dict, List, Optional

from stage_1.constants import (
    SCALE_KEYWORDS,
    SCALE_NUMERIC_THRESHOLDS,
    RISK_KEYWORDS,
    FREQUENCY_KEYWORDS,
    CATEGORY_KEYWORDS,
)


def extract_intent(routed_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract behavioral intent signals from routed input.

    Args:
        routed_input: Output from input_router.route_input()

    Returns:
        {
            "scale": "small" | "medium" | "large" | None,
            "risk": "low" | "medium" | "high" | None,
            "categories": ["grocery", "travel"] | [],
            "frequency": "daily" | "weekly" | "monthly" | ... | None,
        }
    """
    try:
        source = routed_input.get("source", "prompt")
        prompt = routed_input.get("prompt", "")
        structured = routed_input.get("structured")

        # Start with empty intent
        intent = {
            "scale": None,
            "risk": None,
            "categories": [],
            "frequency": None,
            "num_rows": None,
        }

        # ── Extract from structured input first (higher priority) ──
        if source == "structured" and structured:
            intent = _extract_from_structured(structured, intent)

        # ── Extract from prompt text (fills remaining Nones) ──
        if prompt:
            intent = _extract_from_prompt(prompt, intent)

        return intent

    except Exception:
        # Safety net
        return {
            "scale": None,
            "risk": None,
            "categories": [],
            "frequency": None,
            "num_rows": None,
        }


def _extract_from_structured(data: dict, intent: dict) -> dict:
    """Extract intent fields directly from structured input."""
    # Direct fields
    if "scale" in data and data["scale"]:
        intent["scale"] = str(data["scale"]).lower().strip()

    if "risk" in data and data["risk"]:
        intent["risk"] = str(data["risk"]).lower().strip()

    if "frequency" in data and data["frequency"]:
        intent["frequency"] = str(data["frequency"]).lower().strip()

    if "categories" in data and isinstance(data["categories"], list):
        intent["categories"] = [str(c).lower().strip() for c in data["categories"] if c]

    # Also check nested intent dict
    nested_intent = data.get("intent", {})
    if isinstance(nested_intent, dict):
        if not intent["scale"] and nested_intent.get("scale"):
            intent["scale"] = str(nested_intent["scale"]).lower().strip()
        if not intent["risk"] and nested_intent.get("risk"):
            intent["risk"] = str(nested_intent["risk"]).lower().strip()
        if not intent["frequency"] and nested_intent.get("frequency"):
            intent["frequency"] = str(nested_intent["frequency"]).lower().strip()
        if not intent["categories"] and nested_intent.get("categories"):
            cats = nested_intent["categories"]
            if isinstance(cats, list):
                intent["categories"] = [str(c).lower().strip() for c in cats if c]

    return intent


def _extract_from_prompt(prompt: str, intent: dict) -> dict:
    """Extract intent signals from free-text prompt using keyword matching."""
    prompt_lower = prompt.lower().strip()

    # ── Exact row count extraction ──
    if not intent.get("num_rows"):
        intent["num_rows"] = _extract_num_rows(prompt_lower)

    # ── Scale extraction ──
    if not intent["scale"]:
        intent["scale"] = _extract_scale(prompt_lower)

    # ── Risk extraction ──
    if not intent["risk"]:
        intent["risk"] = _extract_risk(prompt_lower)

    # ── Frequency extraction ──
    if not intent["frequency"]:
        intent["frequency"] = _extract_frequency(prompt_lower)

    # ── Categories extraction (additive — merge with structured) ──
    prompt_categories = _extract_categories(prompt_lower)
    existing_cats = set(intent["categories"])
    for cat in prompt_categories:
        if cat not in existing_cats:
            intent["categories"].append(cat)

    return intent


def _extract_scale(prompt: str) -> Optional[str]:
    """Detect scale from prompt text."""
    # Check keyword matches (longest match first to handle phrases)
    for scale_value, keywords in SCALE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in prompt:
                return scale_value

    # Check for numeric indicators (e.g., "500 records", "10k rows")
    numbers = _extract_numbers(prompt)
    for num in numbers:
        for scale_value, (low, high) in SCALE_NUMERIC_THRESHOLDS.items():
            if low <= num <= high:
                return scale_value

    return None


def _extract_risk(prompt: str) -> Optional[str]:
    """Detect risk level from prompt text."""
    # 1. Catch explicit low/no risk phrases FIRST to prevent false positives
    # from partial matches (e.g., "not risky" matching "risky" in high).
    low_explicit = ["no risk", "zero risk", "risk free", "not risky", "0 risk", "without risk"]
    for kw in low_explicit:
        if kw in prompt:
            return "low"

    # Check most extreme/specific levels first, then fall back to generic
    priority_order = ["extreme", "high", "medium", "low"]
    for risk_value in priority_order:
        keywords = RISK_KEYWORDS.get(risk_value, [])
        for keyword in keywords:
            if keyword in prompt:
                return risk_value
    return None


def _extract_frequency(prompt: str) -> Optional[str]:
    """Detect frequency from prompt text."""
    for freq_value, keywords in FREQUENCY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in prompt:
                return freq_value
    return None


def _extract_categories(prompt: str) -> List[str]:
    """Detect category mentions from prompt text."""
    found = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in prompt:
                if category not in found:
                    found.append(category)
                break  # One match per category is enough
    return found


def _extract_num_rows(prompt: str) -> Optional[int]:
    """
    Extract the exact number of rows requested from the prompt.
    Looks for patterns like:
      "500 rows", "generate 10k records", "1,000 lines",
      "5000 entries", "generate 500", "500 data points"

    Returns the exact integer, or None if no row count found.
    """
    # Pattern: number (with optional k/m suffix) followed by a row-like word
    row_pattern = re.search(
        r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*([kmb])?\s*(?:rows?|records?|lines?|entries|data\s*points?|samples?|transactions?|items?)',
        prompt, re.IGNORECASE
    )
    if row_pattern:
        num_str, suffix = row_pattern.group(1), row_pattern.group(2)
        try:
            num = float(num_str.replace(",", ""))
            if suffix:
                suffix = suffix.lower()
                if suffix == "k": num *= 1_000
                elif suffix == "m": num *= 1_000_000
            num = int(num)
            # Clamp to reasonable range: min 10, max 1,000,000
            return max(10, min(num, 1_000_000))
        except (ValueError, OverflowError):
            pass

    # Fallback: look for "generate <number>" pattern without row-like word
    gen_pattern = re.search(
        r'(?:generate|create|make|produce|give\s+me)\s+(\d+(?:,\d{3})*(?:\.\d+)?)\s*([kmb])?',
        prompt, re.IGNORECASE
    )
    if gen_pattern:
        num_str, suffix = gen_pattern.group(1), gen_pattern.group(2)
        try:
            num = float(num_str.replace(",", ""))
            if suffix:
                suffix = suffix.lower()
                if suffix == "k": num *= 1_000
                elif suffix == "m": num *= 1_000_000
            num = int(num)
            if num >= 10:  # Only treat as row count if >= 10
                return max(10, min(num, 1_000_000))
        except (ValueError, OverflowError):
            pass

    return None


def _extract_numbers(prompt: str) -> List[int]:
    """
    Extract numeric values from prompt.
    Handles: "500", "10k", "1,000", "1M"
    """
    numbers = []

    # Match patterns like "10k", "1M", "500"
    patterns = re.findall(r"(\d+(?:,\d{3})*(?:\.\d+)?)\s*([kmb])?", prompt, re.IGNORECASE)

    for num_str, suffix in patterns:
        try:
            num = float(num_str.replace(",", ""))
            suffix = suffix.lower() if suffix else ""
            if suffix == "k":
                num *= 1_000
            elif suffix == "m":
                num *= 1_000_000
            elif suffix == "b":
                num *= 1_000_000_000
            numbers.append(int(num))
        except (ValueError, OverflowError):
            continue

    return numbers
