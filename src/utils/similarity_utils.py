"""Shared case name similarity calculation.

Canonical implementation used by clustering, verification, and deduplication.
"""

import re
from functools import lru_cache


@lru_cache(maxsize=4096)
def calculate_name_similarity(name1: str, name2: str) -> float:
    """Calculate Jaccard word similarity between two case names.

    Names are lowercased and stripped of punctuation before comparison.
    Results are cached for performance in O(n^2) loops.
    """
    if not name1 or not name2:
        return 0.0

    norm1 = _normalize_for_similarity(name1)
    norm2 = _normalize_for_similarity(name2)

    words1 = set(norm1.split())
    words2 = set(norm2.split())

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    if not union:
        return 0.0

    return len(intersection) / len(union)


def _normalize_for_similarity(name: str) -> str:
    """Normalize a case name for similarity comparison."""
    normalized = name.lower().strip()
    normalized = re.sub(r"[,.\s]+", " ", normalized)
    return normalized.strip()
