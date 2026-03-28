"""
Case Extraction Utilities Module
=================================

Utility functions for case name extraction.
"""

import re
import logging
from typing import Optional, List, Dict, Any

from src.utils.date_utils import extract_year_from_text, extract_date_from_text

logger = logging.getLogger(__name__)

# Re-export from single source (src.utils.date_utils)
__all__ = ["extract_year_from_text", "extract_date_from_text", "clean_case_name", "calculate_name_similarity"]


def clean_case_name(name: str) -> str:
    """Re-export from single source of truth."""
    from src.utils.case_name_utils import clean_case_name as _clean
    return _clean(name)


def calculate_name_similarity(name1: str, name2: str) -> float:
    """
    Calculate similarity between two case names.
    
    Uses word overlap and sequence matching.
    """
    if not name1 or not name2:
        return 0.0
    
    from difflib import SequenceMatcher
    
    # Normalize both names
    n1 = _normalize_for_comparison(name1)
    n2 = _normalize_for_comparison(name2)
    
    # Word overlap
    words1 = set(n1.split())
    words2 = set(n2.split())
    
    if not words1 or not words2:
        return 0.0
    
    # Jaccard similarity for words
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    word_sim = intersection / union if union > 0 else 0.0
    
    # Sequence similarity
    seq_sim = SequenceMatcher(None, n1, n2).ratio()
    
    # Weighted combination
    return 0.6 * word_sim + 0.4 * seq_sim


def _normalize_for_comparison(name: str) -> str:
    """Normalize case name for comparison."""
    # Lowercase
    name = name.lower()
    
    # Remove common words
    stop_words = {"the", "of", "in", "and", "a", "an", "for", "to", "v", "vs"}
    words = [w for w in name.split() if w not in stop_words]
    
    return " ".join(words)


def extract_context_around_citation(
    text: str,
    citation_start: int,
    citation_end: int,
    context_size: int = 200
) -> str:
    """
    Extract text context around a citation position.
    
    Args:
        text: Full document text
        citation_start: Start position of citation
        citation_end: End position of citation
        context_size: Characters of context to extract on each side
        
    Returns:
        Context string
    """
    if not text:
        return ""
    
    start = max(0, citation_start - context_size)
    end = min(len(text), citation_end + context_size)
    
    return text[start:end]


def find_case_name_in_context(
    context: str,
    strategies: Optional[List] = None
) -> Optional[Dict[str, Any]]:
    """
    Try to find a case name in context using available strategies.
    
    Args:
        context: Text context to search
        strategies: List of extraction strategies to try
        
    Returns:
        Best extraction result, or None
    """
    if not context:
        return None
    
    # Default: try common patterns
    best_result = None
    best_confidence = 0.0
    
    # Pattern 1: "Case v. Case" format
    pattern = re.compile(
        r"([A-Z][A-Za-z0-9&\'\s,\.]+?)\s+v\.\s+([A-Z][A-Za-z0-9&\'\s,\.]+?)(?:,\s*\d+|$)",
        re.IGNORECASE
    )
    match = pattern.search(context)
    if match:
        name = match.group(0)
        # Calculate confidence
        confidence = 0.7
        if len(name) > 20:
            confidence += 0.1
        if " v." in name or " v " in name.lower():
            confidence += 0.1
        
        if confidence > best_confidence:
            best_confidence = confidence
            best_result = {
                "case_name": clean_case_name(name),
                "confidence": confidence,
                "method": "context_pattern",
            }
    
    return best_result


def is_likely_statute(text: str) -> bool:
    """Check if text is likely a statute rather than case name."""
    statute_indicators = [
        " act",
        " code",
        " statute",
        " regulation",
        " rule ",
        "title ",
        "section ",
        "u.s.c.",
        "usc",
        "c.f.r.",
        "administrative procedure",
        "freedom of information",
        "civil rights act",
        "fair housing",
        "bankruptcy code",
    ]
    
    text_lower = text.lower()
    return any(indicator in text_lower for indicator in statute_indicators)
