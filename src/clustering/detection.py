"""
Cluster Detection Module
========================

Detects parallel citations and structural citation groups.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)

# Helper function to safely get attribute from dict or object
def _get_attr(citation: Any, key: str, default: Any = None) -> Any:
    """Get attribute from dict or object citation."""
    if isinstance(citation, dict):
        return citation.get(key, default)
    return getattr(citation, key, default)

# Pre-compiled patterns for performance
PARALLEL_PATTERNS = {
    "washington": re.compile(r"(\d+)\s+(?:Wn\.|Wash\.)\d*d\s+\d+.*?", re.IGNORECASE),
    "federal": re.compile(r"(\d+)\s+F\.\d*d\s+\d+.*?", re.IGNORECASE),
    "supreme": re.compile(r"(\d+)\s+S\.\s*Ct\.\s+\d+.*?", re.IGNORECASE),
    "generic": re.compile(r"(\d+)\s+[A-Z][a-z]*\.\d*d?\s+\d+.*?", re.IGNORECASE),
}

SEPARATOR_PATTERN = re.compile(r"[,;]\s*")


def detect_parallel_groups(
    citations: List[Dict[str, Any]], 
    proximity_threshold: int = 150
) -> List[List[Dict[str, Any]]]:
    """
    Detect groups of parallel citations based on proximity.
    
    Args:
        citations: List of citation dictionaries with position info
        proximity_threshold: Max distance between citations to be considered parallel
        
    Returns:
        List of citation groups (each group is a list of citations)
    """
    if not citations:
        return []
    
    # Sort by position
    sorted_citations = sorted(
        citations, 
        key=lambda c: _get_attr(c, "start_index", 0) or _get_attr(c, "start_pos", 0)
    )
    
    groups = []
    current_group = [sorted_citations[0]]
    
    for citation in sorted_citations[1:]:
        prev_end = _get_attr(current_group[-1], "end_index") or _get_attr(current_group[-1], "end_pos", 0)
        curr_start = _get_attr(citation, "start_index") or _get_attr(citation, "start_pos", 0)
        
        if curr_start - prev_end <= proximity_threshold:
            current_group.append(citation)
        else:
            # Include single citations as standalone groups
            groups.append(current_group)
            current_group = [citation]
    
    # Don't forget the last group (include even if single)
    groups.append(current_group)
    
    logger.info(f"[PARALLEL-DETECTION] Found {len(groups)} groups from {len(citations)} citations")
    return groups


def detect_structural_groups(
    citations: List[Dict[str, Any]],
    text: str
) -> List[List[Dict[str, Any]]]:
    """
    Detect structural citation groups using pattern recognition.
    
    Looks for patterns like:
    - "Case Name, Citation1, Citation2, Citation3 (Year)"
    - Multiple citations in same sentence
    
    Args:
        citations: List of citation dictionaries
        text: Original document text
        
    Returns:
        List of structural citation groups
    """
    if not citations or not text:
        return []
    
    groups = []
    
    for i, citation in enumerate(citations):
        start_pos = _get_attr(citation, "start_index") or _get_attr(citation, "start_pos", 0)
        end_pos = _get_attr(citation, "end_index") or _get_attr(citation, "end_pos", 0)
        
        if start_pos is None or end_pos is None:
            continue
        
        # Look for nearby citations
        nearby = [citation]
        context_end = min(len(text), end_pos + 200)
        context = text[end_pos:context_end]
        
        # Check if followed by comma/semicolon and another citation pattern
        if SEPARATOR_PATTERN.match(context):
            # Look for subsequent citations
            for j in range(i + 1, len(citations)):
                next_cit = citations[j]
                next_start = _get_attr(next_cit, "start_index") or _get_attr(next_cit, "start_pos", 0)
                
                if next_start and next_start - end_pos < 300:
                    nearby.append(next_cit)
                else:
                    break
        
        # Always include the citation (as single or group)
        groups.append(nearby)
    
    # Remove duplicate groups
    unique_groups = _remove_duplicate_groups(groups)
    
    logger.info(f"[STRUCTURAL-DETECTION] Found {len(unique_groups)} structural groups")
    return unique_groups


def _remove_duplicate_groups(groups: List[List[Dict[str, Any]]]) -> List[List[Dict[str, Any]]]:
    """Remove duplicate groups by comparing citation IDs."""
    seen = set()
    unique = []
    
    for group in groups:
        # Create a frozenset of citation texts as unique identifier
        key = frozenset(
            _get_attr(c, "citation", str(c)) for c in group
        )
        if key not in seen:
            seen.add(key)
            unique.append(group)
    
    return unique


def find_best_cluster_seed(citations: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Find the best citation to seed a cluster from.
    
    Prefers citations with:
    1. Verified status
    2. Case name present
    3. High confidence
    
    Returns:
        Best citation or None
    """
    if not citations:
        return None
    
    def score_citation(c: Any) -> int:
        score = 0
        if _get_attr(c, "verified"):
            score += 100
        if _get_attr(c, "case_name") or _get_attr(c, "canonical_name"):
            score += 50
        score += int(_get_attr(c, "confidence", 0) * 10)
        return score
    
    return max(citations, key=score_citation)


def are_citations_parallel(
    citation1: Dict[str, Any],
    citation2: Dict[str, Any],
    max_distance: int = 150
) -> bool:
    """
    Check if two citations are parallel (close together with matching reporters).
    
    Args:
        citation1: First citation
        citation2: Second citation  
        max_distance: Maximum allowed distance between citations
        
    Returns:
        True if citations appear to be parallel
    """
    # Check distance
    pos1 = _get_attr(citation1, "end_index") or _get_attr(citation1, "end_pos", 0)
    pos2 = _get_attr(citation2, "start_index") or _get_attr(citation2, "start_pos", 0)
    
    if abs(pos2 - pos1) > max_distance:
        return False
    
    # Check if reporters match (e.g., both Washington citations)
    cit1_text = _get_attr(citation1, "citation", "")
    cit2_text = _get_attr(citation2, "citation", "")
    
    # Extract reporter patterns
    reporter1 = _extract_reporter_pattern(cit1_text)
    reporter2 = _extract_reporter_pattern(cit2_text)
    
    # Parallel if same reporter type
    return reporter1 and reporter2 and reporter1 == reporter2


def _extract_reporter_pattern(citation_text: str) -> Optional[str]:
    """Extract reporter pattern from citation text."""
    patterns = {
        "Wn.": r"Wn\.\d*d?",
        "Wash.": r"Wash\.\d*d?",
        "F.": r"F\.\d*d?",
        "U.S.": r"U\.S\.",
        "S.Ct.": r"S\.\s*Ct\.",
        "L.Ed.": r"L\.\s*Ed\.\d*d?",
        "P.": r"P\.\d*d?",
        "A.": r"A\.\d*d?",
        "So.": r"So\.\d*d?",
        "N.E.": r"N\.E\.\d*d?",
        "N.W.": r"N\.W\.\d*d?",
        "S.E.": r"S\.E\.\d*d?",
        "S.W.": r"S\.W\.\d*d?",
        "Cal.": r"Cal\.\d*d?",
        "N.Y.S.": r"N\.Y\.S\.\d*d?",
    }
    
    for reporter_type, pattern in patterns.items():
        if re.search(pattern, citation_text, re.IGNORECASE):
            return reporter_type
    
    return None
