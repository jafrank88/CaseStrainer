"""
Canonical post-cluster pipeline shared by sync and async paths.

This keeps court-tier/WL/canonical split behavior in one place so
`unified_processing_pipeline` and `rq_worker_pipeline` cannot drift.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from src.utils.post_verify_split import (
    split_clusters_by_canonical_name,
    split_clusters_by_date_conflict,
    split_clusters_by_extracted_name,
    split_clusters_by_court_tier_and_wl,
)
from src.utils.same_case import names_are_same_case

logger = logging.getLogger(__name__)


def _best_name_from_citations(cits: List[Dict[str, Any]]) -> Optional[str]:
    """Pick the best case name from a cluster's own citations."""
    names = []
    for c in cits:
        if not isinstance(c, dict):
            continue
        for key, score in [("canonical_name", 100), ("case_name", 50), ("extracted_case_name", 25)]:
            name = (c.get(key) or "").strip()
            if not name or name == "N/A":
                continue
            # Reject narrative text
            has_structure = " v. " in name or bool(re.search(r"\b(?:In\s+re|Ex\s+parte)\b", name, re.IGNORECASE))
            if not has_structure and (len(name) > 40 or " the " in name):
                continue
            names.append((score, name))
    if not names:
        return None
    names.sort(key=lambda x: x[0], reverse=True)
    return names[0][1]


def _name_matches_any_citation(name: str, cits: List[Dict[str, Any]]) -> bool:
    """Check if cluster_case_name matches any citation's own names."""
    if not name or name == "N/A":
        return False
    for c in cits:
        if not isinstance(c, dict):
            continue
        for key in ("canonical_name", "case_name", "extracted_case_name"):
            cit_name = (c.get(key) or "").strip()
            if cit_name and cit_name != "N/A" and names_are_same_case(name, cit_name):
                return True
    return False


def _recalc_cluster_case_names(clusters: List[Dict[str, Any]], run_id: str = "") -> List[Dict[str, Any]]:
    """Fix cluster_case_name only when it doesn't match any citation in the cluster.

    After splits, child clusters inherit the parent's cluster_case_name which
    may not match the child's actual citations. This only replaces mismatched
    names, leaving correct ones untouched.
    """
    for cl in clusters:
        if not isinstance(cl, dict):
            continue
        cits = cl.get("citations", [])
        if not cits:
            continue
        old = (cl.get("cluster_case_name") or "").strip()
        if old and _name_matches_any_citation(old, cits):
            continue  # Current name matches at least one citation — keep it
        best = _best_name_from_citations(cits)
        if best and best != old:
            logger.info(
                f"[POST-SPLIT-RENAME-{run_id}] cluster {cl.get('cluster_id','?')}: "
                f"'{old[:50]}' -> '{best[:50]}'"
            )
            cl["cluster_case_name"] = best
    return clusters


def _deduplicate_citations_across_clusters(
    clusters: List[Dict[str, Any]],
    run_id: str = "",
) -> List[Dict[str, Any]]:
    """Ensure each citation key appears in at most one cluster.

    When merges/splits leave the same citation string in multiple clusters,
    keep it in the cluster where it is **verified** (preferred) or the
    *largest* cluster as a fallback.  Empty clusters are dropped.

    Uses ``citation_core_key`` so abbreviation variants (Wn.2d vs Wash. 2d)
    are recognized as the same citation.
    """
    from src.utils.verification_display_utils import citation_core_key

    def _cit_keys(c: Dict[str, Any]) -> List[str]:
        """Return both the core key and the lowered-text key for matching."""
        raw = (c.get("citation", "") if isinstance(c, dict) else str(c)).strip()
        text_key = re.sub(r"\s+", " ", raw.lower())
        core = citation_core_key(raw)
        keys = []
        if core:
            keys.append(core)
        if text_key and text_key != core:
            keys.append(text_key)
        return keys

    def _is_verified(c: Dict[str, Any]) -> bool:
        return bool(c.get("verified") or c.get("is_verified"))

    def _canonical_matches_cluster(cit: Dict[str, Any], cl: Dict[str, Any]) -> bool:
        """True when the citation's CourtListener (etc.) name matches this cluster's identity."""
        cit_cn = (cit.get("canonical_name") or "").strip()
        if not cit_cn or cit_cn.upper() == "N/A":
            return False
        try:
            from src.utils.same_case import names_are_same_case
        except Exception:
            return False
        for fld in ("canonical_name", "cluster_case_name"):
            cc = (cl.get(fld) or "").strip()
            if not cc or cc.upper() == "N/A":
                continue
            if names_are_same_case(cit_cn, cc):
                return True
        return False

    def _owner_score(tup):
        """Higher is better. Verified beats unverified; then name-cluster alignment; then tie-break."""
        idx, v, cl_size, c, cl = tup
        vg = 1 if v else 0
        align = 1 if _canonical_matches_cluster(c, cl) else 0
        if v:
            # Two clusters can both show verified=True after wrong propagation (e.g. Carlsen
            # absorbing Frias cites). Prefer the cluster whose card identity matches the cite's
            # canonical_name; if still tied, prefer the *smaller* cluster (correct case card).
            third = -cl_size
        else:
            third = cl_size  # unverified: keep legacy "prefer larger cluster" fallback
        return (vg, align, third)

    # Build per-key map: key -> list of (cluster_idx, is_verified, cluster_size, citation, cluster).
    key_candidates: Dict[str, List[tuple]] = {}
    for idx, cl in enumerate(clusters):
        cl_size = len(cl.get("citations", []))
        for c in cl.get("citations", []):
            v = _is_verified(c)
            for k in _cit_keys(c):
                if k:
                    key_candidates.setdefault(k, []).append((idx, v, cl_size, c, cl))

    seen: Dict[str, int] = {}
    for k, candidates in key_candidates.items():
        if k in seen:
            continue
        best = max(candidates, key=_owner_score)
        seen[k] = best[0]

    changed = 0
    result: List[Dict[str, Any]] = []
    for idx, cl in enumerate(clusters):
        kept: List[Dict[str, Any]] = []
        for c in cl.get("citations", []):
            keys = _cit_keys(c)
            owner = None
            for k in keys:
                owner = seen.get(k)
                if owner is not None:
                    break
            if owner is None or owner == idx:
                kept.append(c)
            else:
                changed += 1
        if not kept:
            continue
        cl["citations"] = kept
        cl["size"] = len(kept)
        cl["cluster_size"] = len(kept)
        members = [c.get("citation", "") if isinstance(c, dict) else str(c) for c in kept]
        cl["cluster_members"] = [{"citation": m} if isinstance(m, str) else m for m in members]
        result.append(cl)
    if changed:
        logger.info(f"[DEDUP-CLUSTERS-{run_id}] Removed {changed} duplicate citations across clusters")
    return result


def apply_post_verify_cluster_splits(
    clusters: List[Dict[str, Any]],
    *,
    run_id: str = "",
) -> List[Dict[str, Any]]:
    """
    Apply deterministic post-verification split passes.

    Order matters and matches existing production behavior:
      1) Split by extracted case name (Soo Line vs In re Southwest -> separate clusters)
      2) Split by date conflict (Deggs 2016 vs Hubbard 1995 in same cluster -> separate by year)
      3) Split by reporter court-tier
      4) Split WL from lower-federal where appropriate
      5) Split distinct WL document IDs
      6) Split by canonical name buckets
      7) Recalculate cluster_case_name from each cluster's own citations
      8) Global dedup: ensure each citation key lives in exactly one cluster
    """
    if not clusters:
        return clusters
    try:
        out = split_clusters_by_extracted_name(clusters, task_id=run_id)
        out = split_clusters_by_date_conflict(out, task_id=run_id)
        out = split_clusters_by_court_tier_and_wl(out, task_id=run_id)
        out = split_clusters_by_canonical_name(out, task_id=run_id)
        out = _recalc_cluster_case_names(out, run_id=run_id)
        out = _deduplicate_citations_across_clusters(out, run_id=run_id)
        return out
    except Exception as e:
        logger.warning(f"[POST-CLUSTER-{run_id}] Split pipeline failed: {e}")
        return clusters

