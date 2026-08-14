# =====================================================
# CONFIDENCE SCORER — Multi-factor confidence engine
# =====================================================
# Computes a 0.0–1.0 confidence score based on:
#   - Entity match strength (40%)
#   - Intent completeness (25%)
#   - Input clarity (20%)
#   - Source type bonus (15%)
#
# FIX: STRUCTURED_INPUT_CONFIDENCE_BOOST constant is now
# actually used in _source_type_factor instead of being
# imported and ignored.
#
# NEVER throws. ALWAYS returns a float in [0.0, 1.0].
# =====================================================

import re
from typing import Any, Dict

from stage_1.constants import STRUCTURED_INPUT_CONFIDENCE_BOOST


def score_confidence(
    routed_input: Dict[str, Any],
    entity_result: Dict[str, Any],
    intent: Dict[str, Any],
) -> float:
    """
    Compute a multi-factor confidence score.

    Args:
        routed_input: Output from input_router
        entity_result: Output from entity_resolver
        intent: Output from intent_extractor

    Returns:
        float in [0.0, 1.0]
    """
    try:
        score = 0.0

        # ── Factor 1: Entity match strength (40%) ──
        entity_score = _entity_match_factor(entity_result)
        score += entity_score * 0.40

        # ── Factor 2: Intent completeness (25%) ──
        intent_score = _intent_completeness_factor(intent)
        score += intent_score * 0.25

        # ── Factor 3: Input clarity (20%) ──
        clarity_score = _input_clarity_factor(routed_input)
        score += clarity_score * 0.20

        # ── Factor 4: Source type bonus (15%) ──
        source_score = _source_type_factor(routed_input)
        score += source_score * 0.15

        # Clamp to [0.0, 1.0]
        return round(max(0.0, min(1.0, score)), 3)

    except Exception:
        return 0.0


def _entity_match_factor(entity_result: Dict[str, Any]) -> float:
    """
    How strong was the entity match?
    Based on the top entity's score and the resolution method.
    """
    method = entity_result.get("method", "fallback")
    scores = entity_result.get("scores", {})

    if method == "structured":
        # Structured input with explicit entity → very high confidence
        return 1.0

    if method == "fallback":
        # No match at all → low confidence
        return 0.1

    # Keyword/semantic match → use the actual score
    if scores:
        top_score = max(scores.values())
        return min(top_score * 2.5, 1.0)  # Scale up since raw scores are small

    return 0.1


def _intent_completeness_factor(intent: Dict[str, Any]) -> float:
    """
    How complete is the extracted intent?
    Each non-None field contributes to the score.
    """
    total_fields = 4  # scale, risk, categories, frequency
    filled = 0

    if intent.get("scale") is not None:
        filled += 1
    if intent.get("risk") is not None:
        filled += 1
    if intent.get("categories") and len(intent["categories"]) > 0:
        filled += 1
    if intent.get("frequency") is not None:
        filled += 1

    return filled / total_fields


def _input_clarity_factor(routed_input: Dict[str, Any]) -> float:
    """
    How clear and well-formed is the input?
    Based on: length, word count, word-to-noise ratio.
    """
    prompt = routed_input.get("prompt", "")
    if not prompt:
        return 0.0

    # Word count (more words = more context = higher clarity, up to a point)
    words = prompt.split()
    word_count = len(words)
    if word_count == 0:
        return 0.0

    # Very short → low clarity
    if word_count <= 2:
        length_score = 0.3
    elif word_count <= 5:
        length_score = 0.6
    elif word_count <= 15:
        length_score = 0.9
    else:
        length_score = 1.0

    # Noise ratio: what fraction of characters are actually letters?
    alpha_chars = sum(1 for c in prompt if c.isalpha())
    total_chars = max(len(prompt), 1)
    alpha_ratio = alpha_chars / total_chars

    # Very low alpha ratio = probably garbage
    if alpha_ratio < 0.5:
        noise_score = 0.2
    elif alpha_ratio < 0.7:
        noise_score = 0.5
    else:
        noise_score = 1.0

    return (length_score * 0.5 + noise_score * 0.5)


def _source_type_factor(routed_input: Dict[str, Any]) -> float:
    """
    Structured input is inherently more reliable than free-text.
    Uses STRUCTURED_INPUT_CONFIDENCE_BOOST from constants to
    compute the relative advantage of structured input.

    Structured: 0.5 + boost (clamped to 1.0)
    Prompt:     0.5 (baseline)
    """
    source = routed_input.get("source", "prompt")
    if source == "structured":
        return min(0.5 + STRUCTURED_INPUT_CONFIDENCE_BOOST, 1.0)
    return 0.5