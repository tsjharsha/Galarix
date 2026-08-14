# =====================================================
# INPUT ROUTER — Detect prompt vs structured input
# =====================================================
# The first gate in the pipeline. Normalizes ANY input
# into a consistent internal format so downstream modules
# never need to worry about input type detection.
#
# Handles: str, dict, None, list, int, float, bool — anything.
# NEVER throws. ALWAYS returns a valid routed dict.
# =====================================================

from typing import Any, Dict


def route_input(raw_input: Any) -> Dict[str, Any]:
    """
    Detect whether input is a prompt (string) or structured (dict).
    Normalize into a consistent format for downstream processing.

    Args:
        raw_input: Literally anything — str, dict, None, list, int, etc.

    Returns:
        {
            "source": "prompt" | "structured",
            "prompt": str,              # Always present, never empty
            "structured": dict | None,  # Original structured data if dict input
            "raw_input": Any,           # Original input for debugging
        }
    """
    try:
        # ── CASE 1: String (prompt mode) ──
        if isinstance(raw_input, str):
            prompt = raw_input.strip()
            if not prompt:
                # Empty string → treat as garbage input
                return _make_routed("prompt", prompt="", raw=raw_input)
            return _make_routed("prompt", prompt=prompt, raw=raw_input)

        # ── CASE 2: Dict (structured mode) ──
        if isinstance(raw_input, dict):
            # Extract prompt if provided inside dict
            prompt = str(raw_input.get("prompt", "")).strip()

            # If no explicit prompt, build one from structured fields
            if not prompt:
                prompt = _build_prompt_from_struct(raw_input)

            return _make_routed(
                "structured",
                prompt=prompt,
                structured=raw_input,
                raw=raw_input,
            )

        # ── CASE 3: None ──
        if raw_input is None:
            return _make_routed("prompt", prompt="", raw=raw_input)

        # ── CASE 4: List → join into prompt ──
        if isinstance(raw_input, list):
            joined = " ".join(str(item) for item in raw_input if item is not None)
            return _make_routed("prompt", prompt=joined.strip(), raw=raw_input)

        # ── CASE 5: Numeric / bool / other → stringify ──
        return _make_routed("prompt", prompt=str(raw_input).strip(), raw=raw_input)

    except Exception:
        # Absolute safety net — should never reach here, but guarantees no crash
        return _make_routed("prompt", prompt="", raw=raw_input)


def _make_routed(
    source: str,
    prompt: str,
    raw: Any = None,
    structured: Dict = None,
) -> Dict[str, Any]:
    """Build the standard routed output dict."""
    return {
        "source": source,
        "prompt": prompt,
        "structured": structured,
        "raw_input": raw,
    }


def _build_prompt_from_struct(data: dict) -> str:
    """
    Generate a pseudo-prompt from structured input fields.
    This allows downstream keyword/semantic matching to work
    even when the user provides only structured data.

    Example:
        {"entity": "loans", "scale": "large", "risk": "high"}
        → "large high risk loans"
    """
    parts = []

    # Scale first (adjective position)
    scale = data.get("scale", "")
    if scale:
        parts.append(str(scale))

    # Risk
    risk = data.get("risk", "")
    if risk and risk != "low":  # "low" is default, skip to avoid noise
        if "risk" not in str(risk).lower():
            parts.append(f"{risk} risk")
        else:
            parts.append(str(risk))

    # Entity is the noun
    entity = data.get("entity", "")
    if entity:
        # Convert snake_case to readable: "credit_card_activity" → "credit card activity"
        parts.append(str(entity).replace("_", " "))

    # Categories
    categories = data.get("categories", [])
    if categories and isinstance(categories, list):
        parts.append("with " + ", ".join(str(c) for c in categories))

    # Frequency
    frequency = data.get("frequency", "")
    if frequency:
        parts.append(str(frequency))

    # Intent sub-fields
    intent = data.get("intent", {})
    if isinstance(intent, dict):
        for key in ["scale", "risk", "frequency"]:
            val = intent.get(key, "")
            if val and str(val) not in " ".join(parts):
                parts.append(str(val))

    return " ".join(parts).strip() if parts else ""
