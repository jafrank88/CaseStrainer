"""
Post-verification result processing functions.

Functions that clean up and fix verification results after verification completes.
Extracted from unified_verification_master.py (P1 refactoring).
"""

from typing import Dict, Any, Optional, List
from src.utils.cluster_display_utils import finalize_cluster_for_response, cluster_has_effective_verified, _is_google_search_url


def apply_known_federal_to_citation_objects(citations: List[Any]) -> None:
    """
    No-op: verification comes from live sources (CourtListener, Cornell LII, FindLaw),
    not a static list, so the tool works with new cases.
    """
    pass


def apply_known_federal_citations_and_clear_verified_without_url(
    citations_list: List[Dict[str, Any]],
    clusters_list: List[Dict[str, Any]],
) -> None:
    """
    Last-mile fix for ALL pathways (sync and async).
    No static list: verification comes from live sources (CourtListener, Cornell LII, FindLaw).
    Clear verified/canonical when there is no canonical_url (user rule: no Verified without URL).
    Mutates citations_list and clusters_list in place.
    """
    if not citations_list and not clusters_list:
        return
    # Clear verified/true_by_parallel when no canonical_url or URL is Google search
    # (user rule: Google search URL = unverified; never show "Verified" or "Verified by Parallel")
    def _clear(cit: Dict[str, Any]) -> None:
        if not isinstance(cit, dict):
            return
        url = cit.get("canonical_url") or cit.get("url")
        has_real_url = url and not _is_google_search_url(str(url or ""))
        if not has_real_url:
            cit["verified"] = False
            cit["true_by_parallel"] = False
            cit["canonical_name"] = None
            cit["canonical_date"] = None
            cit["canonical_url"] = None
            cit["url"] = None
    for c in citations_list or []:
        _clear(c)
    for cl in clusters_list or []:
        if not isinstance(cl, dict):
            continue
        for m in cl.get("citations", []) or []:
            _clear(m)
        any_ok = any(
            isinstance(m, dict)
            and m.get("verified")
            and (m.get("canonical_url") or m.get("url"))
            and not _is_google_search_url(str(m.get("canonical_url") or m.get("url") or ""))
            for m in cl.get("citations", []) or []
        )
        if not any_ok and cl.get("verified"):
            cl["verified"] = False
            cl["canonical_name"] = None
            cl["canonical_url"] = None
            finalize_cluster_for_response(
                cl,
                clean_names=True,
                clear_unverified_canonical=True,
                clear_unverified_citations=True,
            )


def apply_last_mile_cluster_display_sync(
    citations_list: List[Dict[str, Any]],
    clusters_list: List[Dict[str, Any]],
) -> None:
    """
    Last-mile sync for BOTH sync and async paths so the UI shows correct
    "Extracted from Document" and "Verified" (with URL when applicable).
    1) submitted_display_name from cluster_members when cluster has N/A
    2) citation url/canonical_url from cluster_members when citation missing them;
       verified/is_verified only true when URL present.
    Mutates clusters_list and citations in place.
    """
    if not clusters_list:
        return
    for cluster in clusters_list:
        if not isinstance(cluster, dict):
            continue
        members = cluster.get("cluster_members", []) or []
        cits = cluster.get("citations", []) or cluster.get("citation_objects", []) or []
        # 1) submitted_display_name from first member/citation with extracted_case_name if cluster has N/A
        sub_name = (cluster.get("submitted_display_name") or "").strip()
        if not sub_name or sub_name.upper() == "N/A":
            for m in members:
                if isinstance(m, dict):
                    en = (m.get("extracted_case_name") or "").strip()
                    if en and en.upper() != "N/A":
                        cluster["submitted_display_name"] = en
                        break
            if not (cluster.get("submitted_display_name") or "").strip():
                for c in cits:
                    if isinstance(c, dict):
                        en = (c.get("extracted_case_name") or "").strip()
                        if en and en.upper() != "N/A":
                            cluster["submitted_display_name"] = en
                            break
        # 2) Map citation text -> member (with real url) from cluster_members
        member_by_citation = {}
        for m in members:
            if isinstance(m, dict):
                ct = (m.get("citation") or "").strip()
                u = (m.get("canonical_url") or m.get("url") or "").strip()
                if ct and u and not _is_google_search_url(u):
                    member_by_citation[ct] = m
        for cit in cits:
            if not isinstance(cit, dict):
                continue
            ct = (cit.get("citation") or "").strip()
            url = (cit.get("canonical_url") or cit.get("url") or "").strip()
            has_real_url = bool(url) and not _is_google_search_url(url)
            if not has_real_url and ct and ct in member_by_citation:
                mem = member_by_citation[ct]
                u = mem.get("canonical_url") or mem.get("url")
                if u and not _is_google_search_url(str(u)):
                    cit["canonical_url"] = mem.get("canonical_url") or mem.get("url")
                    cit["url"] = mem.get("url") or mem.get("canonical_url")
                    if not cit.get("canonical_name") and mem.get("canonical_name"):
                        cit["canonical_name"] = mem.get("canonical_name")
            url = (cit.get("canonical_url") or cit.get("url") or "").strip()
            has_real_url = bool(url) and not _is_google_search_url(url)
            if cit.get("verified") or cit.get("is_verified"):
                cit["verified"] = has_real_url
                cit["is_verified"] = has_real_url
            elif has_real_url:
                # Mirror the flat-list fix from _format_response (line 494-496):
                # A cluster-embedded citation that carries a real case URL must be
                # marked verified=True so cluster_has_effective_verified() returns
                # True and finalize_cluster_display_identity does NOT clear
                # canonical_name / canonical_date to null ("Not Found").
                cit["verified"] = True
                cit["is_verified"] = True
        # 3) Propagate canonical_url/canonical_name to cluster level so display_canonical_url and top-level canonical_url are set.
        # Never overwrite or set a real case URL with a Google search URL.
        best_url = cluster.get("canonical_url") or cluster.get("display_canonical_url")
        if best_url and _is_google_search_url(best_url):
            best_url = None
        if not best_url or not (best_url or "").strip():
            for m in members:
                if isinstance(m, dict):
                    u = (m.get("canonical_url") or m.get("url") or "").strip()
                    if u and not _is_google_search_url(u):
                        best_url = m.get("canonical_url") or m.get("url")
                        cluster["canonical_url"] = best_url
                        cluster["display_canonical_url"] = best_url
                        if not cluster.get("canonical_name") and m.get("canonical_name"):
                            cluster["canonical_name"] = m.get("canonical_name")
                        if not cluster.get("canonical_date") and m.get("canonical_date"):
                            cluster["canonical_date"] = m.get("canonical_date")
                        break
        if not best_url or not (best_url or "").strip():
            for c in cits:
                if isinstance(c, dict):
                    u = (c.get("canonical_url") or c.get("url") or "").strip()
                    if u and not _is_google_search_url(u):
                        best_url = c.get("canonical_url") or c.get("url")
                        cluster["canonical_url"] = best_url
                        cluster["display_canonical_url"] = best_url
                        break

        # Finalize with centralized display identity + canonical clearing semantics.
        finalize_cluster_for_response(
            cluster,
            clean_names=True,
            clear_unverified_canonical=True,
            clear_unverified_citations=True,
        )
        # Sync cluster-level verified flag after finalization so the frontend
        # sections the cluster correctly (Verified vs Unverified).
        if cluster_has_effective_verified(cluster) and not cluster.get("verified"):
            cluster["verified"] = True


def apply_verification_paradox_fix(citations_list: List[Dict[str, Any]]) -> int:
    """
    Set verified=True when citation has full canonical data but verified is False (paradox fix).
    Used by both sync (vue_api) and async (rq_worker) paths for consistency.
    Returns the number of citations fixed.
    """
    fixed_count = 0
    for citation in citations_list or []:
        if not isinstance(citation, dict):
            continue
        has_canonical_data = (
            citation.get("canonical_name")
            and citation.get("canonical_date")
            and citation.get("canonical_url")
        )
        url = citation.get("canonical_url") or citation.get("url")
        is_google = url and _is_google_search_url(str(url))
        if has_canonical_data and not citation.get("verified", False) and not is_google:
            citation["verified"] = True
            citation["verification_status"] = "verified"
            fixed_count += 1
    return fixed_count
