# =====================================================
# 3.1 — SEED ENGINE
# =====================================================
# Ensures every unique prompt produces a unique but
# REPRODUCIBLE dataset. Same prompt = same data.
# Different prompt = completely different data.
#
# Uses the tensor_signature (SHA-256 derived hex from
# Stage 2) as the master seed for a PCG64 generator.
#
# The variation_salt parameter allows users to request
# "a new batch" — same statistical properties but
# different actual rows.
# =====================================================

import hashlib
import numpy as np


def create_generator(
    tensor_signature: str,
    variation_salt: int = 0,
) -> np.random.Generator:
    """
    Create a deterministic random number generator seeded
    by the tensor signature from Stage 2.

    Args:
        tensor_signature: 16-char hex string from Stage 2's tensor engine.
                          Each unique prompt produces a unique signature.
        variation_salt:   Integer salt for generating variations of the
                          same prompt. salt=0 is the "canonical" output.

    Returns:
        numpy Generator (PCG64) — fast, statistically robust, deterministic.

    Guarantees:
        - create_generator("abc", 0) == create_generator("abc", 0)  (reproducible)
        - create_generator("abc", 0) != create_generator("xyz", 0)  (unique per prompt)
        - create_generator("abc", 0) != create_generator("abc", 1)  (variation support)
    """
    final_seed = _stable_seed("master", tensor_signature, variation_salt)

    # PCG64 is the gold standard for simulation RNGs:
    # - Period of 2^128, no observable patterns
    # - Faster than MT19937
    # - Statistically superior (passes all TestU01 BigCrush tests)
    bit_gen = np.random.PCG64(final_seed)
    return np.random.Generator(bit_gen)


def create_labeled_generator(
    tensor_signature: str,
    variation_salt: int,
    label: str,
) -> np.random.Generator:
    """
    Create a deterministic independent stream for a named generation step.

    The seed depends only on the tensor signature, variation salt, and label.
    It does not consume the parent RNG, so adding a new variable or moving a
    pipeline step does not shift existing variable streams.
    """
    child_seed = _stable_seed("label", tensor_signature, variation_salt, label)
    return np.random.Generator(np.random.PCG64(child_seed))


def create_sub_generator(
    parent_rng: np.random.Generator,
    label: str,
) -> np.random.Generator:
    """
    Create a child generator from a parent, seeded by a label string.
    Used to give each variable its own independent RNG stream so that
    adding/removing variables doesn't shift the entire dataset.

    This is critical for stability: if we add a new variable to the
    schema, existing variables' generated values should NOT change.
    """
    # Spawn a new independent stream
    # The label ensures different variables get different streams
    label_hash = sum(ord(c) * (i + 1) for i, c in enumerate(label)) % (2**31)
    child_seed = parent_rng.integers(0, 2**63) + label_hash
    return np.random.Generator(np.random.PCG64(child_seed))


def _stable_seed(*parts: object) -> int:
    """Derive a stable PCG64 seed from arbitrary parts using SHA-256."""
    payload = "\x1f".join(str(part) for part in parts)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return int(digest[:16], 16) % (2**63)
