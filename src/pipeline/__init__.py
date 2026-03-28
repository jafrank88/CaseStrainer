"""
Pipeline stages and shared context for the unified citation processing pipeline.

Modules:
- context: ProcessingContext, _is_statute_name, _is_generic_fallback_name
- extraction: run_extract_citations
- verification: run_verify_citations, run_parallel_verification
- clustering: create_clusters_from_parallel_citations, split_clusters_by_canonical,
  merge_clusters_by_canonical_name, merge_cluster_group, build_clusters
- formatting: format_response, format_error_response

**Merge order (high level)** — see ``unified_processing_pipeline`` for the exact sequence.
After clusters exist, late merges typically include: shared-citation merge
(``response_enrichment.merge_clusters_by_shared_citation``),
``merge_clusters_by_canonical_name``, shared-citation again, SCOTUS parallel merge,
then optional repeats. **API-facing** dedupe/URL merge runs later in
``utils.response_finalize`` so the Vue and RQ paths stay aligned.

**vs ``src.clustering``**
    ``src.clustering`` focuses on **forming** groups from raw citations; this package’s
    ``clustering`` submodule focuses on **pipeline-time** cluster construction and
    **canonical-name / parallel** merges that need processing context.
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
