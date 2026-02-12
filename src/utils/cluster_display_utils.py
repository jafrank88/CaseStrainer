"""
Shared cluster display helpers for backend response preparation.
Used by rq_worker (async) so display logic lives in one place and can be reused.
"""

import re
from typing import Any, Dict, List, Optional

from src.utils.text_normalizer import normalize_case_name

# Signal phrases to strip from case names (shared with rq_worker display processing)
SIGNAL_PHRASE_PATTERNS = [
    r"^See,?\s+",
    r"^See\s+also\s+",
    r"^But\s+see\s+",
    r"^Accord\s+",
    r"^Compare\s+",
    r"^Cf\.?\s*",
    r"^E\.?g\.?\s*,?\s*",
    r"^I\.?e\.?\s*,?\s*",
]


def strip_signal_phrases(name: Optional[str]) -> Optional[str]:
    """Remove leading signal phrases from a case name."""
    if not name or name == "N/A":
        return name
    for pattern in SIGNAL_PHRASE_PATTERNS:
        name = re.sub(pattern, "", name, flags=re.IGNORECASE).strip()
    return name


def get_cluster_citations(cluster: Dict[str, Any]) -> List[Any]:
    """Get citations from cluster, checking both 'citations' and 'citation_objects'."""
    return cluster.get("citations", []) or cluster.get("citation_objects", [])


def get_citation_value(cit: Any, key: str, default: Any = None) -> Any:
    """Get a value from a citation, handling both dict and object formats."""
    if isinstance(cit, dict):
        return cit.get(key, default)
    return getattr(cit, key, default)


def is_citation_verified(cit: Any) -> bool:
    """Check if a citation is verified with canonical_url (user rule: no Verified without URL)."""
    if isinstance(cit, dict):
        url = cit.get("canonical_url") or cit.get("url")
        # FIX: If it has a valid canonical URL, it's verified
        if url and str(url).strip():
            return True
        v = cit.get("verified", False) or cit.get("is_verified", False)
        return bool(v)
    # Handle object-style citations
    url = getattr(cit, "canonical_url", None) or getattr(cit, "url", None)
    if url and str(url).strip():
        return True
    v = getattr(cit, "verified", False) or getattr(cit, "is_verified", False)
    return bool(v)


def get_best_extracted_name(cluster: Dict[str, Any]) -> str:
    """Get the longest/best extracted name from citations in cluster."""
    citations = get_cluster_citations(cluster)
    valid_names = []
    for cit in citations:
        if not cit:
            continue
        name = get_citation_value(cit, "extracted_case_name", "")
        if name and name != "N/A" and not name.startswith(("Co.", "Inc.", "LLC", "Ltd.", "Corp.")):
            # Apply normalization to fix soft hyphen artifacts like "Swin dle" -> "Swindle"
            cleaned = strip_signal_phrases(name) or name
            cleaned = normalize_case_name(cleaned)
            valid_names.append(cleaned)
    if valid_names:
        return max(valid_names, key=len)
    fallback = cluster.get("submitted_display_name") or cluster.get("extracted_case_name") or "N/A"
    return normalize_case_name(fallback) if fallback and fallback != "N/A" else fallback


def get_representative_verified_citation(cluster: Dict[str, Any]) -> Optional[Any]:
    """First verified citation in cluster; use for both name and date to avoid mixing cases."""
    citations = get_cluster_citations(cluster)
    for cit in citations:
        if not cit:
            continue
        if is_citation_verified(cit):
            return cit
    return None


def get_verifying_name(cluster: Dict[str, Any]) -> str:
    """Get canonical/verifying name from the same representative verified citation as date."""
    rep = get_representative_verified_citation(cluster)
    if rep:
        name = get_citation_value(rep, "canonical_name")
        if name and name != "N/A":
            # Apply normalization to fix soft hyphen artifacts like "Swin dle" -> "Swindle"
            cleaned = strip_signal_phrases(name) or name
            return normalize_case_name(cleaned)
    return get_best_extracted_name(cluster)


def get_verifying_date(cluster: Dict[str, Any]) -> str:
    """Get canonical date from the same representative verified citation as name."""
    rep = get_representative_verified_citation(cluster)
    if rep:
        date = get_citation_value(rep, "canonical_date")
        if date and date != "N/A":
            return date
    return cluster.get("extracted_date") or "N/A"


def get_submitted_date(cluster: Dict[str, Any]) -> str:
    """Get extracted date from document."""
    citations = get_cluster_citations(cluster)
    for cit in citations:
        if not cit:
            continue
        date = get_citation_value(cit, "extracted_date")
        if date and date != "N/A":
            return date
    return cluster.get("extracted_date") or "N/A"


def get_canonical_url(cluster: Dict[str, Any]) -> Optional[str]:
    """Get canonical URL from verified citation, or from cluster_members when citations lack it."""
    citations = get_cluster_citations(cluster)
    for cit in citations:
        if not cit:
            continue
        if is_citation_verified(cit):
            url = get_citation_value(cit, "canonical_url") or get_citation_value(cit, "url")
            if url and str(url).strip():
                return url
    # Fallback: cluster_members often have canonical_url when citation dicts don't (e.g. known_federal path)
    for m in cluster.get("cluster_members", []) or []:
        if isinstance(m, dict):
            url = m.get("canonical_url") or m.get("url")
            if url and str(url).strip():
                return url
    return None


def apply_display_fields_to_cluster(cluster: Dict[str, Any]) -> None:
    """Set verifying_display_name, verifying_display_date, submitted_display_name, submitted_display_date, display_canonical_url on cluster."""
    cluster["verifying_display_name"] = get_verifying_name(cluster)
    cluster["verifying_display_date"] = get_verifying_date(cluster)
    cluster["submitted_display_name"] = get_best_extracted_name(cluster)
    cluster["submitted_display_date"] = get_submitted_date(cluster)
    cluster["display_canonical_url"] = get_canonical_url(cluster)
