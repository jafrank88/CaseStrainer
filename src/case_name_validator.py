"""
Case Name Validation Utility

Validates extracted case names to reject:
- Text fragments that aren't case names
- Single words without "v." or "vs."
- Common phrases that get mistakenly extracted
- N/A or empty values that should be cleaned up
- Case names with docket numbers (treated as unverified)
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def has_docket_number(case_name: str) -> bool:
    """Check if case name contains docket number patterns"""
    docket_patterns = [
        r":\d{1,4}[:-]\s*CV-\s*\d{4,}[\w\-]*",  # ":2:24-CV- 00074-APG-NJK"
        r":\d{1,4}[:-]\s*CV-\d{4,}[\w\-]*",      # ":2:24-CV-00074"
        r":\d{1,4}(?::[:-])?\d{3,4}[\w\-]*",     # General: ":2:24-CV-00074" or ":2023-CV-456"
        r",\s*No\.\s*[\d\-\w:]+",               # ", No. 2:24-CV-00074"
        r"\bNo\.\s*[\d\-\w:]+",                 # "No. 2:24-CV-00074"
    ]
    return any(re.search(pattern, case_name, re.IGNORECASE) for pattern in docket_patterns)


def clean_docket_from_case_name(case_name: str) -> str:
    """Remove docket number from case name"""
    cleaned = case_name
    docket_patterns = [
        r":\d{1,4}[:-]\s*CV-\s*\d{4,}[\w\-]*",
        r":\d{1,4}[:-]\s*CV-\d{4,}[\w\-]*",
        r":\d{1,4}(?::[:-])?\d{3,4}[\w\-]*",
        r",\s*No\.\s*[\d\-\w:]+",
        r"\bNo\.\s*[\d\-\w:]+",
    ]
    for pattern in docket_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*,\s*$", "", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip()


def validate_and_clean_case_name(case_name: Optional[str], min_length: int = 5) -> tuple[bool, Optional[str]]:
    """
    Validate case name and optionally clean it if it contains docket numbers.
    
    Returns:
        (is_valid, cleaned_name_or_original)
        - If valid without docket: (True, case_name)
        - If has docket: (False, cleaned_case_name)  # treated as unverified
        - If invalid: (False, None)
    """
    if not case_name or case_name.strip() == "":
        return False, None
    
    case_name = case_name.strip()
    
    # Check for docket numbers
    if has_docket_number(case_name):
        cleaned = clean_docket_from_case_name(case_name)
        logger.warning(f"Case name has docket number - treating as unverified: '{case_name}' → '{cleaned}'")
        return False, cleaned  # Return False to indicate unverified, but provide cleaned version
    
    # Normal validation
    if is_valid_case_name(case_name, min_length):
        return True, case_name
    else:
        return False, None


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
    if not case_name or case_name.strip() == "":
        logger.debug("Rejected: Empty case name")
        return False

    case_name = case_name.strip()

    # Reject if too short
    if len(case_name) < min_length:
        logger.debug(f"Rejected: Too short ({len(case_name)} chars): '{case_name}'")
        return False

    # Reject "N/A" explicitly
    if case_name.upper() == "N/A":
        logger.debug("Rejected: N/A")
        return False

    # CRITICAL: Must contain "v." or "vs." OR be an "In re" case
    # USER FIX 2024-10-16: Also accept "In re", "Matter of", "Ex parte", "Estate of" cases
    has_v = re.search(r"\bv\.?\b|\bvs\.?\b", case_name, re.IGNORECASE)
    is_special_case = re.search(
        r"^(In\s+re|Matter\s+of|Ex\s+parte|Estate\s+of|In\s+the\s+matter\s+of)\b", case_name, re.IGNORECASE
    )

    if not (has_v or is_special_case):
        logger.debug(f"Rejected: No 'v.'/'vs.' and not a special case: '{case_name}'")
        return False

    # FIX JAN 2026: Check for docket numbers and treat as unverified
    if has_docket_number(case_name):
        logger.warning(f"Rejected: Contains docket number (treated as unverified): '{case_name}'")
        return False

    # CRITICAL FIX: Reject if contains legal analysis phrases (not case names)
    # These are contamination from surrounding legal text
    legal_analysis_phrases = [
        "rulings de novo",
        "ruling de novo",
        "rulings",
        "hearing",
        "standard",
        "test",
        "review",
        "claim",
        "statute",
        "rule",
        "evidence",
        "court held",
        "court found",
        "court ruled",
        "we review",
        "we hold",
        "we conclude",
        "we determine",
        "we find",
        "we affirm",
        "under",
        "pursuant to",
        "according to",
        "in accordance with",
        "de novo",
        "de novo review",
        "de novo standard",
        "frye",
        "daubert",
        "kumho",  # Legal test names
        "wpla",
        "wcpa",
        "rcw",
        "frcp",
        "frcivp",  # Legal codes
        # FIX DEC 2025 v10: Removed 'er ' - too many false positives (e.g., "Fisher")
        "choice of law",
        "conflict of laws",
        "appellate review",
        "trial court",
        "appellate court",
        "wpla claim",
        "washington legislature intended",  # Specific patterns from results
    ]

    case_lower = case_name.lower()
    for phrase in legal_analysis_phrases:
        if phrase in case_lower:
            logger.debug(f"Rejected: Contains legal analysis phrase '{phrase}': '{case_name}'")
            return False

    # Reject if starts with legal analysis phrases (common contamination)
    legal_start_phrases = [
        r"^(?:frye|daubert|kumho)\s+(?:rulings?|hearings?|standards?|tests?)",
        r"^(?:wpla|wcpa|rcw|er|frcp|frcivp)\s+(?:claim|rule|statute|evidence)",
        r"^we\s+(?:review|hold|conclude|determine|find|affirm|reverse|remand)",
        r"^(?:the\s+)?(?:court|trial\s+court|appellate\s+court)\s+(?:held|found|ruled|determined)",
        r"^(?:under|pursuant\s+to|according\s+to|in\s+accordance\s+with)",
    ]

    for pattern in legal_start_phrases:
        if re.search(pattern, case_lower):
            logger.debug(f"Rejected: Starts with legal analysis phrase: '{case_name}'")
            return False

    # Reject common text fragments that aren't case names
    bad_patterns = [
        r"^dangerous\b",
        r"^doctrine\b",
        r"^immunity\b",
        r"^child\b",
        r"^origins\b",
        r"^held\b",
        r"^ruled\b",
        r"^decided\b",
        r"^matter\s+of\s+\w+$",  # "matter of X" without full name
        r"^\w+\s+and\s+its\b",  # "X and its..."
        r"^\w+\s+or\s+its\b",  # "X or its..."
    ]

    for pattern in bad_patterns:
        if re.search(pattern, case_name, re.IGNORECASE):
            logger.debug(f"Rejected: Matches bad pattern '{pattern}': '{case_name}'")
            return False

    # Reject if it's just fragments around "v."
    # e.g., "v. doctrine" or "and v. the"
    if re.match(r"^(and|the|of|in|for|with|from)\s+v\.", case_name, re.IGNORECASE):
        logger.debug(f"Rejected: Starts with article/preposition: '{case_name}'")
        return False

    if re.search(r"v\.\s+(and|the|of|in|for|with|from|its|his|her)$", case_name, re.IGNORECASE):
        logger.debug(f"Rejected: Ends with article/preposition: '{case_name}'")
        return False

    # For adversarial cases (with "v."), must have parts before and after
    parts = re.split(r"\bv\.?\b|\bvs\.?\b", case_name, flags=re.IGNORECASE)

    if has_v:
        # Adversarial case validation
        if len(parts) < 2:
            logger.debug(f"Rejected: Not enough parts around 'v.': '{case_name}'")
            return False

        plaintiff = parts[0].strip()
        defendant = parts[1].strip() if len(parts) > 1 else ""

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
    if not case_name or case_name.strip() == "":
        logger.warning(f"Empty case name for {citation}")
        return "N/A"

    if not is_valid_case_name(case_name):
        logger.warning(f"Invalid case name for {citation}: '{case_name}' {context}")
        return "N/A"

    return case_name.strip()


__all__ = ["is_valid_case_name", "clean_case_name", "validate_and_log_case_name"]
