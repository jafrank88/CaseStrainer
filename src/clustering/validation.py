"""
Cluster Validation Module
==========================

Validates cluster quality and calculates confidence scores.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


# Helper function to safely get attribute from dict or object
def _get_attr(citation: Any, key: str, default: Any = None) -> Any:
    """Get attribute from dict or object citation."""
    if isinstance(citation, dict):
        return citation.get(key, default)
    return getattr(citation, key, default)


def validate_cluster(
    cluster: List[Dict[str, Any]],
    min_size: int = 1,
    require_case_name: bool = False
) -> Dict[str, Any]:
    """
    Validate a cluster and return validation results.
    
    Args:
        cluster: List of citations in the cluster
        min_size: Minimum number of citations for valid cluster
        require_case_name: Whether to require at least one citation with case name
        
    Returns:
        Validation results dict with valid, issues, and metadata
    """
    issues = []
    
    # Check size
    if len(cluster) < min_size:
        issues.append(f"Cluster too small ({len(cluster)} < {min_size})")
    
    # Check for case names
    case_names = [
        _get_attr(c, "canonical_name") or _get_attr(c, "case_name") or _get_attr(c, "extracted_case_name")
        for c in cluster
    ]
    case_names = [n for n in case_names if n and n != "N/A"]
    
    if require_case_name and not case_names:
        issues.append("No case names found in cluster")
    
    # Check for consistent case names
    if len(case_names) > 1:
        name_consistency = _check_name_consistency(case_names)
        if name_consistency < 0.5:
            issues.append(f"Inconsistent case names (similarity: {name_consistency:.2f})")
    
    # Check for years
    years = [_get_attr(c, "year") or _get_attr(c, "canonical_date") or _get_attr(c, "extracted_date") for c in cluster]
    years = [y for y in years if y and y != "N/A"]
    
    # Check year consistency
    if len(years) > 1:
        year_consistency = _check_year_consistency(years)
        if year_consistency < 0.8:
            issues.append(f"Inconsistent years")
    
    # Calculate overall confidence
    confidence = calculate_cluster_confidence(cluster)
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "confidence": confidence,
        "size": len(cluster),
        "has_case_name": len(case_names) > 0,
        "has_year": len(years) > 0,
        "case_name_count": len(case_names),
    }


def calculate_cluster_confidence(cluster: List[Dict[str, Any]]) -> float:
    """
    Calculate overall confidence score for a cluster.
    
    Factors:
    - Average citation confidence
    - Case name consistency
    - Year consistency
    - Verification rate
    
    Returns:
        Confidence score 0.0-1.0
    """
    if not cluster:
        return 0.0
    
    scores = []
    
    # Average citation confidence
    confidences = [
        _get_attr(c, "confidence", 0) or _get_attr(c, "confidence_score", 0)
        for c in cluster
    ]
    if confidences:
        scores.append(sum(confidences) / len(confidences) / 100.0)
    
    # Verification rate
    verified = sum(1 for c in cluster if _get_attr(c, "verified"))
    scores.append(verified / len(cluster))
    
    # Case name consistency
    case_names = [
        _get_attr(c, "canonical_name") or _get_attr(c, "case_name") or _get_attr(c, "extracted_case_name")
        for c in cluster
    ]
    case_names = [n for n in case_names if n and n != "N/A"]
    if len(case_names) > 1:
        scores.append(_check_name_consistency(case_names))
    elif len(case_names) == 1:
        scores.append(0.8)  # Single name is okay
    else:
        scores.append(0.3)  # No names reduces confidence
    
    # Year consistency
    years = [_get_attr(c, "year") or _get_attr(c, "canonical_date") for c in cluster]
    years = [y for y in years if y and y != "N/A"]
    if len(years) > 1:
        scores.append(_check_year_consistency(years))
    elif len(years) == 1:
        scores.append(0.9)  # Single year is good
    else:
        scores.append(0.5)  # No year is okay but not great
    
    # Weighted average
    weights = [0.3, 0.3, 0.25, 0.15]
    total_weight = sum(weights[:len(scores)])
    
    if total_weight == 0:
        return 0.0
    
    confidence = sum(s * w for s, w in zip(scores, weights)) / total_weight
    return min(1.0, max(0.0, confidence))


def _check_name_consistency(names: List[str]) -> float:
    """Check consistency of case names using similarity."""
    if len(names) < 2:
        return 1.0
    
    # Compare all pairs
    similarities = []
    for i, name1 in enumerate(names):
        for name2 in names[i+1:]:
            sim = SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
            similarities.append(sim)
    
    return sum(similarities) / len(similarities) if similarities else 0.0


def _check_year_consistency(years: List[str]) -> float:
    """Check consistency of years."""
    if len(years) < 2:
        return 1.0
    
    # Extract numeric years
    numeric_years = []
    for year in years:
        match = re.search(r"\d{4}", str(year))
        if match:
            numeric_years.append(int(match.group()))
    
    if len(numeric_years) < 2:
        return 0.5
    
    # Check if all within 1 year
    year_range = max(numeric_years) - min(numeric_years)
    if year_range == 0:
        return 1.0
    elif year_range == 1:
        return 0.9
    elif year_range <= 2:
        return 0.7
    else:
        return 0.3


def is_valid_cluster_size(
    cluster: List[Dict[str, Any]],
    min_size: int = 1,
    max_size: int = 50
) -> bool:
    """Check if cluster size is within acceptable bounds."""
    return min_size <= len(cluster) <= max_size


def check_cluster_overlap(
    cluster1: List[Dict[str, Any]],
    cluster2: List[Dict[str, Any]]
) -> float:
    """
    Calculate overlap ratio between two clusters.
    
    Returns:
        Overlap ratio (0.0-1.0)
    """
    texts1 = {_get_attr(c, "citation", str(c)) for c in cluster1}
    texts2 = {_get_attr(c, "citation", str(c)) for c in cluster2}
    
    intersection = texts1 & texts2
    union = texts1 | texts2
    
    return len(intersection) / len(union) if union else 0.0


def merge_clusters_if_similar(
    cluster1: List[Dict[str, Any]],
    cluster2: List[Dict[str, Any]],
    similarity_threshold: float = 0.8
) -> Optional[List[Dict[str, Any]]]:
    """
    Merge two clusters if they are similar enough.
    
    Returns:
        Merged cluster or None if not similar enough
    """
    overlap = check_cluster_overlap(cluster1, cluster2)
    
    if overlap >= similarity_threshold:
        # Merge (remove duplicates)
        merged = list(cluster1)
        texts1 = {_get_attr(c, "citation", str(c)) for c in cluster1}
        
        for citation in cluster2:
            if _get_attr(citation, "citation", str(citation)) not in texts1:
                merged.append(citation)
        
        return merged
    
    return None
