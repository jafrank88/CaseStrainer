"""
Minimal fast clustering fallback - groups citations simply and quickly
"""
import re
import logging
import time
from typing import Dict, Any, List, Any

logger = logging.getLogger(__name__)


def _extract_case_name_from_citation_text(citation_text: str) -> str:
    """Extract 'Party v. Party' from the citation text itself (not metadata)."""
    if not citation_text:
        return ""
    # Match "Name v. Name" before the volume number, handling commas in names
    # e.g., "Trichell v. Midland Credit Mgmt., Inc., 964 F.3d 990"
    m = re.match(
        r"^((?:[A-Z][A-Za-z'\-]+\.?(?:\s+[A-Za-z'\-]+\.?)*)"
        r"\s+v\.\s+"
        r"(?:[A-Z][A-Za-z'\-]+\.?(?:[\s,]+[A-Za-z'\-]+\.?)*))",
        citation_text,
    )
    if m:
        return m.group(1).strip().rstrip(",").lower()
    return ""


def cluster_citations_minimal(citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ultra-fast minimal clustering - just group by extracted_case_name or citation text.
    Complexity: O(n)
    """
    if not citations:
        return []

    # Group by case name or citation text
    groups = {}

    for citation in citations:
        # Get grouping key
        case_name = citation.get("extracted_case_name") or citation.get("case_name")
        citation_text = citation.get("citation", "")

        # Normalize key
        if case_name and case_name != "N/A":
            key = case_name.lower().strip()
        else:
            # Use citation text as fallback
            key = citation_text

        # FIX 2026-02-10: Cross-check that the citation text doesn't contain
        # a DIFFERENT case name than the grouping key.  This prevents merging
        # e.g. "Trichell v. Midland" into a "Simon v. Eastern Kentucky" cluster
        # just because the case_name metadata was set wrong.
        cit_text_name = _extract_case_name_from_citation_text(citation_text)
        if cit_text_name and " v. " in cit_text_name and " v. " in key:
            # Both have "v." — extract first party from each and compare
            key_first = key.split(" v. ")[0].strip().split()[-1] if " v. " in key else ""
            cit_first = cit_text_name.split(" v. ")[0].strip().split()[-1] if " v. " in cit_text_name else ""
            if key_first and cit_first and key_first != cit_first:
                # Different first parties — use citation text name as key instead
                logger.info(
                    f"[MINIMAL-CLUSTER] Citation text name '{cit_text_name}' differs from "
                    f"metadata name '{key}' — using citation text for grouping"
                )
                key = cit_text_name

        if key not in groups:
            groups[key] = []
        groups[key].append(citation)

    # Create simple clusters
    clusters = []
    for i, (key, group_citations) in enumerate(groups.items(), 1):
        # Get best name from group
        best_name = None
        best_year = None
        any_verified = False

        for c in group_citations:
            name = c.get("extracted_case_name") or c.get("case_name")
            if name and name != "N/A" and not best_name:
                best_name = name
            year = c.get("extracted_date") or c.get("canonical_date")
            if year and year != "N/A" and not best_year:
                best_year = year
            if c.get("verified"):
                any_verified = True

        cluster = {
            "cluster_id": f"cluster_{i}",
            "cluster_key": key[:50],
            "citations": group_citations,
            "size": len(group_citations),
            "cluster_case_name": best_name or "Unknown Case",
            "cluster_year": best_year,
            "extracted_case_name": best_name,
            "extracted_date": best_year,
            "canonical_name": group_citations[0].get("canonical_name") if group_citations else None,
            "canonical_date": group_citations[0].get("canonical_date") if group_citations else None,
            "cluster_members": [c.get("citation", "") for c in group_citations],
            "confidence": 0.8 if len(group_citations) > 1 else 0.5,
            "verified": any_verified,
            "verification_status": "verified" if any_verified else "not_verified",
            "metadata": {"created_by": "minimal_clustering"},
        }
        clusters.append(cluster)

    logger.info(f"[MINIMAL-CLUSTER] Created {len(clusters)} clusters from {len(citations)} citations")
    return clusters


def cluster_citations_optimized(
    citations, original_text: str = "", enable_verification: bool = False, request_id: str = ""
):
    """
    Entry point that uses minimal clustering for speed
    """
    start = time.time()

    # Convert objects to dicts if needed
    citation_dicts = []
    for c in citations:
        if isinstance(c, dict):
            citation_dicts.append(c)
        elif hasattr(c, "__dict__"):
            citation_dicts.append(c.__dict__)
        else:
            citation_dicts.append({"citation": str(c)})

    result = cluster_citations_minimal(citation_dicts)

    elapsed = time.time() - start
    logger.info(f"[OPTIMIZED-CLUSTER] Completed in {elapsed:.3f}s: {len(result)} clusters")
    return result
