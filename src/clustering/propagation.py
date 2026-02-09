"""
Cluster Metadata Propagation Module
====================================

Propagates metadata (case names, dates, URLs) within clusters.
"""

import logging
from typing import List, Dict, Any, Optional, Set
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


def _get_attr(citation, key, default=None):
    """Get attribute from citation whether it's a dict or object."""
    if isinstance(citation, dict):
        return citation.get(key, default)
    return getattr(citation, key, default)


def _set_attr(citation, key, value):
    """Set attribute on citation whether it's a dict or object."""
    if isinstance(citation, dict):
        citation[key] = value
    else:
        setattr(citation, key, value)


def propagate_metadata(
    cluster: List[Dict[str, Any]],
    source_citation: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Propagate metadata from verified/authoritative citations to others in cluster.
    
    Args:
        cluster: List of citations in the cluster
        source_citation: Optional specific citation to propagate from
        
    Returns:
        Updated cluster metadata
    """
    if not cluster:
        return {}
    
    # Find best source if not specified
    if source_citation is None:
        source_citation = _find_best_source(cluster)
    
    if not source_citation:
        return {}
    
    # Extract metadata from source
    canonical_name = (
        _get_attr(source_citation, "canonical_name") or 
        _get_attr(source_citation, "case_name") or 
        _get_attr(source_citation, "extracted_case_name")
    )
    canonical_date = (
        _get_attr(source_citation, "canonical_date") or 
        _get_attr(source_citation, "year") or 
        _get_attr(source_citation, "extracted_date")
    )
    canonical_url = _get_attr(source_citation, "canonical_url") or _get_attr(source_citation, "url")
    
    if not canonical_name:
        return {}
    
    # Propagate to other citations
    propagated_count = 0
    for citation in cluster:
        if citation is source_citation:
            continue
        
        # Only fill in missing data, don't overwrite
        if not _get_attr(citation, "canonical_name") and not _get_attr(citation, "case_name"):
            _set_attr(citation, "case_name", canonical_name)
            meta = _get_attr(citation, "metadata", {})
            if not isinstance(meta, dict):
                meta = {}
            meta["inherited_name"] = True
            _set_attr(citation, "metadata", meta)
            propagated_count += 1
        
        if not _get_attr(citation, "canonical_date") and not _get_attr(citation, "year"):
            _set_attr(citation, "year", canonical_date)
            meta = _get_attr(citation, "metadata", {})
            if not isinstance(meta, dict):
                meta = {}
            meta["inherited_date"] = True
            _set_attr(citation, "metadata", meta)
        
        if not _get_attr(citation, "canonical_url") and not _get_attr(citation, "url"):
            _set_attr(citation, "url", canonical_url)
    
    logger.info(
        f"[METADATA-PROPAGATION] Propagated from '{canonical_name[:50]}...' "
        f"to {propagated_count}/{len(cluster)-1} citations"
    )
    
    return {
        "source": source_citation,
        "propagated_count": propagated_count,
        "cluster_size": len(cluster),
        "canonical_name": canonical_name,
        "canonical_date": canonical_date,
    }


def merge_cluster_metadata(
    clusters: List[List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """
    Merge metadata across multiple clusters.
    
    Args:
        clusters: List of citation clusters
        
    Returns:
        List of cluster metadata dictionaries
    """
    merged = []
    
    for i, cluster in enumerate(clusters):
        # Get best case name from cluster
        case_name = _select_best_case_name(cluster)
        case_year = _select_best_year(cluster)
        
        metadata = {
            "cluster_id": f"cluster_{i}",
            "size": len(cluster),
            "case_name": case_name,
            "case_year": case_year,
            "citations": [_get_attr(c, "citation", str(c)) for c in cluster],
        }
        
        merged.append(metadata)
    
    return merged


def _find_best_source(cluster: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Find the best citation to propagate metadata from."""
    if not cluster:
        return None
    
    # Priority: verified > has canonical data > high confidence
    verified = [c for c in cluster if _get_attr(c, "verified")]
    if verified:
        # Pick verified citation with most complete data
        return max(verified, key=lambda c: (
            bool(_get_attr(c, "canonical_name")),
            bool(_get_attr(c, "canonical_date")),
            _get_attr(c, "confidence", 0)
        ))
    
    # No verified citations, pick one with most metadata
    return max(cluster, key=lambda c: (
        bool(_get_attr(c, "canonical_name") or _get_attr(c, "case_name")),
        bool(_get_attr(c, "canonical_date") or _get_attr(c, "year")),
        _get_attr(c, "confidence", 0)
    ))


def _select_best_case_name(cluster: List[Dict[str, Any]]) -> Optional[str]:
    """Select the best case name from a cluster."""
    names = []
    
    for citation in cluster:
        for key in ["canonical_name", "case_name", "extracted_case_name"]:
            name = _get_attr(citation, key)
            if name and name != "N/A":
                # Score based on source quality
                score = 100 if key == "canonical_name" else 50 if key == "case_name" else 25
                names.append((score, name))
    
    if not names:
        return None
    
    # Sort by score and pick highest
    names.sort(key=lambda x: x[0], reverse=True)
    return names[0][1]


def _select_best_year(cluster: List[Dict[str, Any]]) -> Optional[str]:
    """Select the best year from a cluster."""
    years = []
    
    for citation in cluster:
        for key in ["canonical_date", "year", "extracted_date"]:
            year = _get_attr(citation, key)
            if year and year != "N/A":
                # Score based on source quality
                score = 100 if key == "canonical_date" else 50 if key == "year" else 25
                years.append((score, year))
    
    if not years:
        return None
    
    # Sort by score and pick highest
    years.sort(key=lambda x: x[0], reverse=True)
    return years[0][1]


def propagate_parallel_status(
    citations: List[Dict[str, Any]],
    parallel_citations: List[str]
) -> None:
    """
    Mark citations as parallel and link them together.
    
    Args:
        citations: List of all citations
        parallel_citations: List of citation texts that are parallel
    """
    parallel_set = set(parallel_citations)
    
    for citation in citations:
        cit_text = _get_attr(citation, "citation", "")
        if cit_text in parallel_set:
            _set_attr(citation, "is_parallel", True)
            _set_attr(citation, "parallel_citations", [
                c for c in parallel_citations if c != cit_text
            ])
