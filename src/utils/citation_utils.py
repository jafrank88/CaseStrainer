"""
Single entrypoint for citation string normalization and variants.

Re-exports from src.citation_utils_consolidated so callers can import from
src.utils.citation_utils. Add more re-exports as callers are migrated.
"""

from src.citation_utils_consolidated import (
    normalize_citation,
    generate_citation_variants,
)

__all__ = [
    "normalize_citation",
    "generate_citation_variants",
]
