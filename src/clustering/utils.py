"""
Clustering Utilities Module
=============================

Utility functions for clustering operations.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


REPORTER_PATTERNS = {
    "Wn.": re.compile(r"Wn\.\d*d?"),
    "Wash.": re.compile(r"Wash\.\d*d?"),
    "F.": re.compile(r"F\.\d*d?"),
    "F.Supp.": re.compile(r"F\.\s*Supp\.\d*d?"),
    "U.S.": re.compile(r"U\.S\."),
    "S.Ct.": re.compile(r"S\.\s*Ct\."),
    "L.Ed.": re.compile(r"L\.\s*Ed\.\d*d?"),
    "L.Ed.2d": re.compile(r"L\.\s*Ed\.\s*2d"),
    "P.": re.compile(r"P\.\d*d?"),
    "P.2d": re.compile(r"P\.\s*2d"),
    "P.3d": re.compile(r"P\.\s*3d"),
    "A.": re.compile(r"A\.\d*d?"),
    "A.2d": re.compile(r"A\.\s*2d"),
    "So.": re.compile(r"So\.\d*d?"),
    "So.2d": re.compile(r"So\.\s*2d"),
    "So.3d": re.compile(r"So\.\s*3d"),
    "N.E.": re.compile(r"N\.E\.\d*d?"),
    "N.E.2d": re.compile(r"N\.E\.\s*2d"),
    "N.E.3d": re.compile(r"N\.E\.\s*3d"),
    "N.W.": re.compile(r"N\.W\.\d*d?"),
    "N.W.2d": re.compile(r"N\.W\.\s*2d"),
    "S.E.": re.compile(r"S\.E\.\d*d?"),
    "S.E.2d": re.compile(r"S\.E\.\s*2d"),
    "S.W.": re.compile(r"S\.W\.\d*d?"),
    "S.W.2d": re.compile(r"S\.W\.\s*2d"),
    "S.W.3d": re.compile(r"S\.W\.\s*3d"),
    "Cal.": re.compile(r"Cal\.\d*d?"),
    "Cal.2d": re.compile(r"Cal\.\s*2d"),
    "Cal.3d": re.compile(r"Cal\.\s*3d"),
    "Cal.4th": re.compile(r"Cal\.\s*4th"),
    "Cal.App.": re.compile(r"Cal\.\s*App\."),
    "N.Y.S.": re.compile(r"N\.Y\.S\.\d*d?"),
    "N.Y.S.2d": re.compile(r"N\.Y\.S\.\s*2d"),
    "N.Y.S.3d": re.compile(r"N\.Y\.S\.\s*3d"),
}


def sort_citations_by_position(
    citations: List[Dict[str, Any]],
    descending: bool = False
) -> List[Dict[str, Any]]:
    """
    Sort citations by their position in the document.
    
    Args:
        citations: List of citation dictionaries
        descending: Sort in descending order if True
        
    Returns:
        Sorted list of citations
    """
    def get_position(c):
        pos = c.get("start_index") or c.get("start_pos", 0)
        return pos if pos is not None else 0
    
    return sorted(citations, key=get_position, reverse=descending)


def extract_reporter_type_safe(citation_text: str) -> Optional[str]:
    """
    Safely extract reporter type from citation text.
    
    Returns:
        Reporter type string or None if not found
    """
    if not citation_text:
        return None
    
    for reporter_type, pattern in REPORTER_PATTERNS.items():
        if pattern.search(citation_text):
            return reporter_type
    
    return None


def group_citations_by_reporter(
    citations: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group citations by their reporter type.
    
    Args:
        citations: List of citation dictionaries
        
    Returns:
        Dict mapping reporter types to lists of citations
    """
    groups = defaultdict(list)
    
    for citation in citations:
        text = citation.get("citation", "")
        reporter = extract_reporter_type_safe(text)
        
        if reporter:
            groups[reporter].append(citation)
        else:
            groups["unknown"].append(citation)
    
    return dict(groups)


def get_citation_distance(
    citation1: Dict[str, Any],
    citation2: Dict[str, Any]
) -> Optional[int]:
    """
    Calculate distance between two citations in the text.
    
    Returns:
        Distance in characters, or None if positions not available
    """
    end1 = citation1.get("end_index") or citation1.get("end_pos")
    start2 = citation2.get("start_index") or citation2.get("start_pos")
    
    if end1 is None or start2 is None:
        return None
    
    return abs(start2 - end1)


def are_citations_adjacent(
    citation1: Dict[str, Any],
    citation2: Dict[str, Any],
    max_distance: int = 50
) -> bool:
    """
    Check if two citations are adjacent (close together).
    
    Args:
        citation1: First citation
        citation2: Second citation
        max_distance: Maximum distance to be considered adjacent
        
    Returns:
        True if citations are adjacent
    """
    distance = get_citation_distance(citation1, citation2)
    if distance is None:
        return False
    
    return distance <= max_distance


def extract_year_from_citation(citation_text: str) -> Optional[int]:
    """
    Extract 4-digit year from citation text.
    Delegates to src.utils.date_utils (single source of truth).
    """
    from src.utils.date_utils import extract_year_from_citation as _extract
    return _extract(citation_text)


def clean_case_name(name: str) -> str:
    """Re-export from single source of truth (src.utils.case_name_utils)."""
    from src.utils.case_name_utils import clean_case_name as _clean
    return _clean(name)


def is_truncated_name(name: str) -> bool:
    """
    Check if a case name appears to be truncated.
    
    Returns:
        True if name appears truncated
    """
    if not name:
        return True
    
    # Check for common truncation patterns
    truncation_indicators = [
        "...",
        " v.",  # Ends with v. (missing defendant)
        " v ",
        "Inc. v.",
        "Corp. v.",
        "Co. v.",
        "Ltd. v.",
        "LLC v.",
    ]
    
    for indicator in truncation_indicators:
        if name.endswith(indicator) or indicator in name[-20:]:
            return True
    
    # Check if too short to be a full case name
    if len(name) < 15:
        return True
    
    # Check for incomplete party names (ends mid-word)
    if re.search(r"[a-zA-Z]$", name) and not name.endswith("."):
        # Could be truncated
        words = name.split()
        if len(words) < 3:
            return True
    
    return False


def calculate_position_overlap(
    start1: int, end1: int,
    start2: int, end2: int
) -> int:
    """
    Calculate overlap between two position ranges.
    
    Returns:
        Number of overlapping characters
    """
    overlap_start = max(start1, start2)
    overlap_end = min(end1, end2)
    
    return max(0, overlap_end - overlap_start)


def merge_citation_data(
    primary: Dict[str, Any],
    secondary: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge two citation dictionaries, preferring primary data.
    
    Returns:
        Merged citation dictionary
    """
    merged = primary.copy()
    
    for key, value in secondary.items():
        if key not in merged or not merged[key]:
            merged[key] = value
    
    return merged
