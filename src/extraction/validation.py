"""
Case Extraction Validation Module
==================================

Validates extracted case names for quality and correctness.
"""

import re
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def validate_case_name(name: str) -> Dict[str, Any]:
    """
    Validate a case name and return validation results.
    
    Returns:
        Dict with valid (bool), issues (list), and quality_score (float)
    """
    issues = []
    score = 1.0
    
    if not name or not name.strip():
        return {"valid": False, "issues": ["Empty name"], "quality_score": 0.0}
    
    name = name.strip()
    
    # Check minimum length
    if len(name) < 10:
        issues.append("Name too short")
        score -= 0.3
    
    # Check for proper format (should have v. or similar)
    has_vs = any(marker in name.lower() for marker in [" v.", " v ", " vs.", " vs "])
    has_in_re = name.lower().startswith("in re ")
    has_ex_parte = name.lower().startswith("ex parte ")
    
    if not (has_vs or has_in_re or has_ex_parte):
        issues.append("Missing 'v.' or 'In re' marker")
        score -= 0.2
    
    # Check for truncation
    if name.endswith("...") or name.endswith(".."):
        issues.append("Appears truncated")
        score -= 0.25
    
    # Check for statute-like content
    statute_words = ["act", "code", "statute", "regulation", "title", "section"]
    if any(word in name.lower() for word in statute_words):
        issues.append("May be statute, not case")
        score -= 0.3
    
    # Check for citation contamination
    citation_patterns = [
        r"\d+\s+(?:U\.S\.|S\.\s*Ct\.|L\.\s*Ed|F\.\d*d|F\.\s*Supp)",
        r"\d+\s+(?:Wn\.|Wash\.|P\.\d*d|A\.\d*d)",
    ]
    for pattern in citation_patterns:
        if re.search(pattern, name):
            issues.append("Contains citation text")
            score -= 0.2
            break
    
    # Check for opinion/judge contamination
    bad_patterns = [
        "opinion of the court",
        "j., dissenting",
        "j., concurring",
        "c.j.,",
    ]
    for pattern in bad_patterns:
        if pattern in name.lower():
            issues.append(f"Contains: {pattern}")
            score -= 0.4
    
    return {
        "valid": len(issues) == 0 or score > 0.5,
        "issues": issues,
        "quality_score": max(0.0, score),
        "has_vs": has_vs,
        "has_in_re": has_in_re,
    }


def is_valid_case_name(name: str) -> bool:
    """Re-export from single source of truth (src.utils.case_name_utils)."""
    from src.utils.case_name_utils import is_valid_case_name as _is_valid
    return _is_valid(name)


def is_truncated(name: str) -> bool:
    """Check if name appears truncated."""
    if not name:
        return True
    
    # Ends with truncation indicators
    if name.endswith(("...", "..", " v.", " v ")):
        return True
    
    # Too short
    if len(name) < 15:
        return True
    
    # Ends mid-word (no period at end of last word)
    words = name.split()
    if words and len(words[-1]) > 1:
        last_word = words[-1]
        if last_word[-1].isalpha() and not last_word.endswith((".", ",", ";")):
            # Check if it looks incomplete
            if len(words) < 3:
                return True
    
    return False


def calculate_name_similarity(name1: str, name2: str) -> float:
    """Calculate similarity between two case names."""
    from difflib import SequenceMatcher
    
    if not name1 or not name2:
        return 0.0
    
    # Normalize
    n1 = _normalize_name(name1)
    n2 = _normalize_name(name2)
    
    return SequenceMatcher(None, n1, n2).ratio()


def _normalize_name(name: str) -> str:
    """Normalize case name for comparison."""
    # Lowercase
    name = name.lower()
    
    # Remove punctuation except 'v.'
    name = re.sub(r"[^\w\s\.v]", " ", name)
    
    # Normalize whitespace
    name = " ".join(name.split())
    
    return name
