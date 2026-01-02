"""
Case Name Validation Utility

Validates extracted case names to reject:
- Text fragments that aren't case names
- Single words without "v." or "vs."
- Common phrases that get mistakenly extracted
- N/A or empty values that should be cleaned up
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def is_valid_case_name(case_name: Optional[str], min_length: int = 5) -> bool:
    """
    Validate that an extracted case name looks like an actual case name.
    
    Rejects:
    - None or empty strings
    - Single words (unless they contain "v." or "vs.")
    - Common text fragments that get mistakenly extracted
    - Names that are too short
    - Names without proper structure
    
    Args:
        case_name: The extracted case name to validate
        min_length: Minimum length for valid case name
        
    Returns:
        True if valid, False otherwise
    """
    if not case_name or case_name.strip() == '':
        logger.debug("Rejected: Empty case name")
        return False
    
    case_name = case_name.strip()
    
    # Reject if too short
    if len(case_name) < min_length:
        logger.debug(f"Rejected: Too short ({len(case_name)} chars): '{case_name}'")
        return False
    
    # Reject "N/A" explicitly
    if case_name.upper() == 'N/A':
        logger.debug("Rejected: N/A")
        return False
    
    # CRITICAL: Must contain "v." or "vs." OR be an "In re" case
    # USER FIX 2024-10-16: Also accept "In re", "Matter of", "Ex parte", "Estate of" cases
    has_v = re.search(r'\bv\.?\b|\bvs\.?\b', case_name, re.IGNORECASE)
    is_special_case = re.search(r'^(In\s+re|Matter\s+of|Ex\s+parte|Estate\s+of|In\s+the\s+matter\s+of)\b', case_name, re.IGNORECASE)
    
    if not (has_v or is_special_case):
        logger.debug(f"Rejected: No 'v.'/'vs.' and not a special case: '{case_name}'")
        return False
    
    # CRITICAL FIX: Reject if contains legal analysis phrases (not case names)
    # These are contamination from surrounding legal text
    legal_analysis_phrases = [
        'rulings de novo', 'ruling de novo', 'rulings', 'hearing', 'standard', 'test', 'review',
        'claim', 'statute', 'rule', 'evidence', 'court held', 'court found', 'court ruled',
        'we review', 'we hold', 'we conclude', 'we determine', 'we find', 'we affirm',
        'under', 'pursuant to', 'according to', 'in accordance with',
        'de novo', 'de novo review', 'de novo standard',
        'frye', 'daubert', 'kumho',  # Legal test names
        'wpla', 'wcpa', 'rcw', 'frcp', 'frcivp',  # Legal codes
        # FIX DEC 2025 v10: Removed 'er ' - too many false positives (e.g., "Fisher")
        'choice of law', 'conflict of laws',
        'appellate review', 'trial court', 'appellate court',
        'wpla claim', 'washington legislature intended',  # Specific patterns from results
    ]
    
    case_lower = case_name.lower()
    for phrase in legal_analysis_phrases:
        if phrase in case_lower:
            logger.debug(f"Rejected: Contains legal analysis phrase '{phrase}': '{case_name}'")
            return False
    
    # Reject if starts with legal analysis phrases (common contamination)
    legal_start_phrases = [
        r'^(?:frye|daubert|kumho)\s+(?:rulings?|hearings?|standards?|tests?)',
        r'^(?:wpla|wcpa|rcw|er|frcp|frcivp)\s+(?:claim|rule|statute|evidence)',
        r'^we\s+(?:review|hold|conclude|determine|find|affirm|reverse|remand)',
        r'^(?:the\s+)?(?:court|trial\s+court|appellate\s+court)\s+(?:held|found|ruled|determined)',
        r'^(?:under|pursuant\s+to|according\s+to|in\s+accordance\s+with)',
    ]
    
    for pattern in legal_start_phrases:
        if re.search(pattern, case_lower):
            logger.debug(f"Rejected: Starts with legal analysis phrase: '{case_name}'")
            return False
    
    # Reject common text fragments that aren't case names
    bad_patterns = [
        r'^dangerous\b',
        r'^doctrine\b',
        r'^immunity\b',
        r'^child\b',
        r'^origins\b',
        r'^held\b',
        r'^ruled\b',
        r'^decided\b',
        r'^matter\s+of\s+\w+$',  # "matter of X" without full name
        r'^\w+\s+and\s+its\b',  # "X and its..."
        r'^\w+\s+or\s+its\b',  # "X or its..."
    ]
    
    for pattern in bad_patterns:
        if re.search(pattern, case_name, re.IGNORECASE):
            logger.debug(f"Rejected: Matches bad pattern '{pattern}': '{case_name}'")
            return False
    
    # Reject if it's just fragments around "v."
    # e.g., "v. doctrine" or "and v. the"
    if re.match(r'^(and|the|of|in|for|with|from)\s+v\.', case_name, re.IGNORECASE):
        logger.debug(f"Rejected: Starts with article/preposition: '{case_name}'")
        return False
    
    if re.search(r'v\.\s+(and|the|of|in|for|with|from|its|his|her)$', case_name, re.IGNORECASE):
        logger.debug(f"Rejected: Ends with article/preposition: '{case_name}'")
        return False
    
    # For adversarial cases (with "v."), must have parts before and after
    parts = re.split(r'\bv\.?\b|\bvs\.?\b', case_name, flags=re.IGNORECASE)
    
    if has_v:
        # Adversarial case validation
        if len(parts) < 2:
            logger.debug(f"Rejected: Not enough parts around 'v.': '{case_name}'")
            return False
        
        plaintiff = parts[0].strip()
        defendant = parts[1].strip() if len(parts) > 1 else ''
        
        # Both sides must have actual content
        if len(plaintiff) < 2 or len(defendant) < 2:
            logger.debug(f"Rejected: Plaintiff or defendant too short: '{case_name}'")
            return False
        
        # At least one side should start with a capital letter (proper noun)
        if not (plaintiff[0].isupper() or defendant[0].isupper()):
            logger.debug(f"Rejected: Neither side starts with capital: '{case_name}'")
            return False
    else:
        # Special case validation (In re, Ex parte, etc.)
        # Just check that it's not all lowercase or obviously malformed
        if case_name.islower():
            logger.debug(f"Rejected: Special case is all lowercase: '{case_name}'")
            return False
    
    return True


def clean_case_name(case_name: Optional[str]) -> Optional[str]:
    """
    Clean and validate a case name, returning None if invalid.
    
    Args:
        case_name: The case name to clean and validate
        
    Returns:
        Cleaned case name if valid, None if invalid
    """
    if not case_name:
        return None
    
    case_name = case_name.strip()
    
    # Run validation
    if not is_valid_case_name(case_name):
        return None
    
    return case_name


def validate_and_log_case_name(case_name: Optional[str], citation: str, context: str = "") -> Optional[str]:
    """
    Validate case name with detailed logging for debugging.
    
    Args:
        case_name: The extracted case name
        citation: The citation it was extracted for
        context: Optional context for logging
        
    Returns:
        Cleaned case name if valid, "N/A" if invalid
    """
    if not case_name or case_name.strip() == '':
        logger.warning(f"Empty case name for {citation}")
        return "N/A"
    
    if not is_valid_case_name(case_name):
        logger.warning(f"Invalid case name for {citation}: '{case_name}' {context}")
        return "N/A"
    
    return case_name.strip()


__all__ = ['is_valid_case_name', 'clean_case_name', 'validate_and_log_case_name']
