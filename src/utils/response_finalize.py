"""
Shared API response finalization for clusters (Vue sync path and RQ worker).

Keeps merge-by-URL, re-finalize, dedupe, and optional display_citations rebuild
in one place so worker and HTTP layer do not drift.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def merge_dedupe_and_refinalize_clusters(
    clusters: List[Dict[str, Any]],
    *,
    clean_names: bool,
    rebuild_display_citations: bool = False,
) -> List[Dict[str, Any]]:
    """
    After an initial :func:`finalize_cluster_for_response` on each cluster:

    1. Merge clusters that share the same real opinion URL.
    2. Re-run :func:`finalize_cluster_for_response` on each (merged) cluster.
    3. Deduplicate cluster cards for the UI.
    4. Optionally rebuild ``display_citations`` from ``cluster_members`` (Vue only).

    Args:
        clusters: Mutable cluster dicts (modified in place).
        clean_names: Passed to ``finalize_cluster_for_response`` (worker uses True, Vue False).
        rebuild_display_citations: When True, set ``display_citations`` on each cluster.

    Returns:
        The same list instance as ``clusters`` after in-place updates and possible length change
        from deduplication (callers should use the return value).
    """
    from src.utils.cluster_display_utils import finalize_cluster_for_response
    from src.utils.response_enrichment import (
        deduplicate_cluster_citations,
        deduplicate_clusters_for_response,
        enrich_citations_with_cluster_members,
        merge_clusters_by_shared_real_canonical_url,
    )

    if not clusters:
        return clusters

    merged = merge_clusters_by_shared_real_canonical_url(clusters)
    for cl in merged:
        if isinstance(cl, dict):
            finalize_cluster_for_response(
                cl,
                clean_names=clean_names,
                clear_unverified_canonical=True,
                clear_unverified_citations=True,
            )
    out = deduplicate_clusters_for_response(merged)

    if rebuild_display_citations:
        for cl in out:
            if not isinstance(cl, dict):
                continue
            try:
                cits = enrich_citations_with_cluster_members(
                    cl.get("citations") or [],
                    cl.get("cluster_members") or [],
                )
                cl["display_citations"] = deduplicate_cluster_citations(cits)
            except Exception as ex:
                logger.debug("display_citations rebuild skipped: %s", ex)
                cl["display_citations"] = cl.get("citations") or []

    return out


def run_final_display_guard_worker(
    citations_flat: List[Dict[str, Any]],
    clusters: List[Dict[str, Any]],
    *,
    log: Optional[logging.Logger] = None,
    log_prefix: str = "",
) -> List[Dict[str, Any]]:
    """
    Full worker final guard: proprietary fallback on citations, first finalize pass,
    then :func:`merge_dedupe_and_refinalize_clusters` with ``clean_names=True``.

    Returns the updated clusters list.
    """
    from src.utils.cluster_display_utils import finalize_cluster_for_response
    from src.utils.response_enrichment import apply_proprietary_display_fallback

    lg = log or logger
    prefix = log_prefix or ""

    apply_proprietary_display_fallback(citations_flat)
    for cl in clusters or []:
        if not isinstance(cl, dict):
            continue
        apply_proprietary_display_fallback(cl.get("citations") or [])
        finalize_cluster_for_response(
            cl,
            clean_names=True,
            clear_unverified_canonical=True,
            clear_unverified_citations=True,
        )
    try:
        return merge_dedupe_and_refinalize_clusters(
            clusters,
            clean_names=True,
            rebuild_display_citations=False,
        )
    except Exception as ex:
        lg.warning("%sFinal display guard (merge/dedupe) failed: %s", prefix, ex)
        return clusters
