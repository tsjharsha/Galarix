# =====================================================
# ENTITY RESOLVER — Multi-layer entity detection
# =====================================================
# The most critical component in Stage 1.
#
# Resolution layers (in order):
#   1. Structured shortcut — if input has "entity" field
#   2. Keyword scoring — weighted keyword matching
#   3. Semantic phrase matching — indirect language
#   4. Multi-entity detection — if top scores are close
#   5. Fallback — "generic" entity
#
# NEVER throws. ALWAYS returns at least one entity.
# =====================================================

import re
from typing import Any, Dict, List, Tuple
from stage_1.agentic_retriever import expand_prompt_agentically

from stage_1.constants import (
    ENTITY_KEYWORDS,
    SEMANTIC_PHRASES,
    GENERIC_TERMS,
    SUPPORTED_ENTITIES,
    DEFAULT_FALLBACK_ENTITY,
    KEYWORD_MATCH_BASE_WEIGHT,
    SEMANTIC_PHRASE_WEIGHT,
    GENERIC_TERM_BOOST,
    GENERIC_TERM_BOOST_CAP,
    CROSS_DOMAIN_PENALTY,
    MULTI_ENTITY_THRESHOLD,
    MULTI_ENTITY_GAP,
)


def resolve_entity(routed_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolve the financial entity(ies) from routed input.

    Args:
        routed_input: Output from input_router.route_input()

    Returns:
        {
            "entities": ["loans"],             # Primary entity list
            "scores": {"loans": 0.85, ...},    # All entity scores
            "method": "keyword|structured|semantic|fallback",
            "is_multi": False,
            "primary_entity": "loans",         # Top scoring entity
        }
    """
    try:
        source = routed_input.get("source", "prompt")
        prompt = routed_input.get("prompt", "")
        structured = routed_input.get("structured")

        # ── LAYER 1: Structured shortcut ──
        if source == "structured" and structured:
            entity_field = structured.get("entity", "")
            if entity_field and str(entity_field) in SUPPORTED_ENTITIES:
                return _make_result(
                    entities=[str(entity_field)],
                    scores={str(entity_field): 1.0},
                    method="structured",
                )

        # ── LAYER 2 + 3: Keyword + Semantic scoring ──
        if prompt:
            scores = _score_all_entities(prompt)
        else:
            scores = {e: 0.0 for e in SUPPORTED_ENTITIES}

        # ── LAYER 4: Multi-entity detection ──
        sorted_entities = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # ── LAYER 4: Agentic Expansion (The Brain) ──
        # If the static engine failed to reach the confidence threshold,
        # reach out to the agentic layer to expand the prompt and try again.
        was_agentic = False
        agentic_offline = False
        if prompt and (not sorted_entities or sorted_entities[0][1] < MULTI_ENTITY_THRESHOLD):
            expanded_prompt, is_offline = expand_prompt_agentically(prompt)
            agentic_offline = is_offline
            if expanded_prompt != prompt:
                # Re-score with expanded prompt!
                scores = _score_all_entities(expanded_prompt)
                sorted_entities = sorted(scores.items(), key=lambda x: x[1], reverse=True)
                was_agentic = True

        if not sorted_entities or sorted_entities[0][1] <= 0.0:
            # No signal at all even after expansion → Hard Reject
            raise ValueError("NO_FINANCIAL_INTENT")

        top_entity, top_score = sorted_entities[0]

        # Check for multi-entity
        if len(sorted_entities) >= 2:
            second_entity, second_score = sorted_entities[1]
            gap = top_score - second_score

            if (
                second_score >= MULTI_ENTITY_THRESHOLD
                and gap < MULTI_ENTITY_GAP
            ):
                # Multiple entities detected
                multi_entities = [
                    e for e, s in sorted_entities
                    if s >= MULTI_ENTITY_THRESHOLD
                ]
                return _make_result(
                    entities=multi_entities,
                    scores=scores,
                    method="agentic_retrieval" if was_agentic else "keyword",
                    is_multi=True,
                    agentic_offline=agentic_offline,
                )

        # Single entity
        return _make_result(
            entities=[top_entity],
            scores=scores,
            method="agentic_retrieval" if was_agentic else "keyword",
            agentic_offline=agentic_offline,
        )

    except ValueError as ve:
        if str(ve) == "NO_FINANCIAL_INTENT":
            raise ve
        return _make_result(
            entities=[DEFAULT_FALLBACK_ENTITY],
            scores={},
            method="fallback",
        )
    except Exception:
        # Absolute safety — never crash for other reasons
        return _make_result(
            entities=[DEFAULT_FALLBACK_ENTITY],
            scores={},
            method="fallback",
        )


def _score_all_entities(prompt: str) -> Dict[str, float]:
    """
    Score every supported entity against the prompt using
    weighted keyword matching + semantic phrase matching.
    """
    prompt_lower = prompt.lower().strip()
    prompt_clean = re.sub(r"[^a-z0-9\s]", " ", prompt_lower)
    prompt_clean = re.sub(r"\s+", " ", prompt_clean).strip()

    scores: Dict[str, float] = {}
    has_any_domain_match = False

    for entity in SUPPORTED_ENTITIES:
        score = 0.0

        # ── Keyword scoring ──
        keywords = ENTITY_KEYWORDS.get(entity, {})
        keyword_hits = 0
        keyword_weight_sum = 0.0

        for keyword, weight in keywords.items():
            if keyword in prompt_clean:
                keyword_hits += 1
                keyword_weight_sum += weight

        if keyword_hits > 0:
            has_any_domain_match = True
            # Single strong keyword (1.0) is enough to max out keyword contribution
            keyword_score = min(keyword_weight_sum, 1.0)
            score += keyword_score * KEYWORD_MATCH_BASE_WEIGHT

        # ── Semantic phrase scoring ──
        phrases = SEMANTIC_PHRASES.get(entity, [])
        phrase_hits = 0
        for phrase in phrases:
            if phrase in prompt_clean:
                phrase_hits += 1

        if phrase_hits > 0:
            has_any_domain_match = True
            # Single phrase is enough to max out phrase contribution
            phrase_score = min(phrase_hits * 1.0, 1.0)
            score += phrase_score * SEMANTIC_PHRASE_WEIGHT

        scores[entity] = round(score, 4)

    # ── Generic term boost ──
    # Only applies if at least one domain keyword matched
    if has_any_domain_match:
        generic_hits = sum(1 for term in GENERIC_TERMS if term in prompt_clean)
        generic_boost = min(generic_hits * GENERIC_TERM_BOOST, GENERIC_TERM_BOOST_CAP)

        for entity in scores:
            if scores[entity] > 0:
                scores[entity] = round(scores[entity] + generic_boost, 4)

    # ── Cross-domain penalty ──
    # If multiple distinct domains triggered, slightly penalize so weak overlaps
    # fall below the threshold while strong multi-intent inputs survive.
    active_entities = [e for e, s in scores.items() if s > (0.1 * KEYWORD_MATCH_BASE_WEIGHT)]
    if len(active_entities) > 1:
        for entity in scores:
            if scores[entity] > 0:
                scores[entity] = round(
                    max(0.0, scores[entity] - CROSS_DOMAIN_PENALTY),
                    4,
                )

    # ── Normalize scores to 0-1 range ──
    max_score = max(scores.values()) if scores else 0.0
    if max_score > 1.0:
        for entity in scores:
            scores[entity] = round(scores[entity] / max_score, 4)

    return scores


def _make_result(
    entities: List[str],
    scores: Dict[str, float],
    method: str,
    is_multi: bool = False,
    agentic_offline: bool = False,
) -> Dict[str, Any]:
    """Build standard entity resolution result."""
    primary = entities[0] if entities else DEFAULT_FALLBACK_ENTITY
    return {
        "entities": entities,
        "scores": scores,
        "method": method,
        "is_multi": is_multi or len(entities) > 1,
        "primary_entity": primary,
        "agentic_offline": agentic_offline,
    }
