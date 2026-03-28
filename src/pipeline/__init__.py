"""
Pipeline stages and shared context for the unified citation processing pipeline.

Modules:
- context: ProcessingContext, _is_statute_name, _is_generic_fallback_name
- extraction: run_extract_citations
- verification: run_verify_citations, run_parallel_verification
- clustering: create_clusters_from_parallel_citations, split_clusters_by_canonical,
  merge_clusters_by_canonical_name, merge_cluster_group, build_clusters
- formatting: format_response, format_error_response
"""

from src.pipeline.context import (
    ProcessingContext,
    _is_statute_name,
    _is_generic_fallback_name,
    _GENERIC_FALLBACK_NAMES,
)

__all__ = [
    "ProcessingContext",
    "_is_statute_name",
    "_is_generic_fallback_name",
    "_GENERIC_FALLBACK_NAMES",
]
