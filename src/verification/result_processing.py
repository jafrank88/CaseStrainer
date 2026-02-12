"""
Post-verification result processing functions.

Functions that clean up and fix verification results after verification completes.
Extracted from unified_verification_master.py (P1 refactoring).
"""

from typing import Dict, Any, Optional, List


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
    # Clear verified when no canonical_url (user rule: no Verified without canonical URL)
    def _clear(cit: Dict[str, Any]) -> None:
        if not isinstance(cit, dict):
            return
        has_url = cit.get("canonical_url") or cit.get("url")
        if cit.get("verified") and not has_url:
            cit["verified"] = False
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
            isinstance(m, dict) and m.get("verified") and (m.get("canonical_url") or m.get("url"))
            for m in cl.get("citations", []) or []
        )
        if not any_ok and cl.get("verified"):
            cl["verified"] = False
            cl["canonical_name"] = None
            cl["canonical_url"] = None
            cl["verifying_display_name"] = cl.get("submitted_display_name") or cl.get("extracted_case_name") or "N/A"


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
        # 2) Map citation text -> member (with url) from cluster_members
        member_by_citation = {}
        for m in members:
            if isinstance(m, dict):
                ct = (m.get("citation") or "").strip()
                if ct and (m.get("canonical_url") or m.get("url")):
                    member_by_citation[ct] = m
        for cit in cits:
            if not isinstance(cit, dict):
                continue
            ct = (cit.get("citation") or "").strip()
            has_url = bool((cit.get("canonical_url") or cit.get("url") or "").strip())
            if not has_url and ct and ct in member_by_citation:
                mem = member_by_citation[ct]
                cit["canonical_url"] = mem.get("canonical_url") or mem.get("url")
                cit["url"] = mem.get("url") or mem.get("canonical_url")
                if not cit.get("canonical_name") and mem.get("canonical_name"):
                    cit["canonical_name"] = mem.get("canonical_name")
            has_url = bool((cit.get("canonical_url") or cit.get("url") or "").strip())
            if cit.get("verified") or cit.get("is_verified"):
                cit["verified"] = has_url
                cit["is_verified"] = has_url
        # 3) Propagate canonical_url/canonical_name to cluster level so display_canonical_url and top-level canonical_url are set
        best_url = cluster.get("canonical_url") or cluster.get("display_canonical_url")
        if not best_url or not (best_url or "").strip():
            for m in members:
                if isinstance(m, dict):
                    u = (m.get("canonical_url") or m.get("url") or "").strip()
                    if u:
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
                    if u:
                        best_url = c.get("canonical_url") or c.get("url")
                        cluster["canonical_url"] = best_url
                        cluster["display_canonical_url"] = best_url
                        break


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
        if has_canonical_data and not citation.get("verified", False):
            citation["verified"] = True
            citation["verification_status"] = "verified"
            fixed_count += 1
    return fixed_count
