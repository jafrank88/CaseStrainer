"""
Case Name Contamination Detector
=================================

Detects when a case name has been contaminated by text from multiple citations.

CONTAMINATION PATTERN:
"Upper Skagit Indian Tribe v. Lundgren, Mills Indian Cmty."
                                        ^^^^^^^^^^^^^^^^^^
                                        This is from a DIFFERENT case!

The pattern is: "Case1 Name, Case2 Defendant" where a comma separates two case names.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def is_contaminated_case_name(case_name: str) -> bool:
    """
    Detect if a case name contains text from multiple different citations.

    CONTAMINATION INDICATORS:
    1. Pattern: "Name v. Name, OtherName" (comma followed by fragment that doesn't match)
    2. Multiple "v." patterns in suspicious positions
    3. Defendant name looks like it's from a different case

    Args:
        case_name: The extracted case name to check

    Returns:
        True if contaminated, False otherwise

    Examples:
        >>> is_contaminated_case_name("Upper Skagit Indian Tribe v. Lundgren, Mills Indian Cmty.")
        True  # "Mills Indian Cmty." is from different case

        >>> is_contaminated_case_name("Michigan v. Bay Mills Indian Community")
        False  # Clean name

        >>> is_contaminated_case_name("Spokeo, Inc. v. Robins")
        False  # Corporate name with comma is OK
    """
    if not case_name or case_name == "N/A":
        return False

    # USER FIX 2026-01-27: Reject "Opinion of the Court" contamination
    case_name_lower = case_name.lower()
    if "opinion of the court" in case_name_lower:
        logger.warning(f"[CONTAMINATION-DETECTED] Contains 'Opinion of the Court': '{case_name}'")
        return True
    
    # USER FIX 2026-01-27: Reject statute names
    if " v. " not in case_name_lower:
        if case_name_lower.endswith((" act", " code", " statute")):
            logger.warning(f"[CONTAMINATION-DETECTED] Statute name: '{case_name}'")
            return True
        if "administrative procedure" in case_name_lower and "act" in case_name_lower:
            logger.warning(f"[CONTAMINATION-DETECTED] Statute pattern: '{case_name}'")
            return True

    # USER FIX 2026-01-12: Pattern 0: Newlines indicate contamination (text spans multiple paragraphs)
    # Example: "Ibid.\n\nThese statements now ring hollow..."
    if "\n" in case_name:
        logger.warning(f"[CONTAMINATION-DETECTED] Pattern 0: '{case_name[:50]}...' contains newlines")
        return True
    
    # USER FIX 2026-01-12: Excessive length indicates contamination (>200 chars is not a case name)
    if len(case_name) > 200:
        logger.warning(f"[CONTAMINATION-DETECTED] Excessive length: '{case_name[:50]}...' is {len(case_name)} chars")
        return True

    # Check for the specific contamination pattern: "Name v. Defendant, OtherDefendant"
    # where the comma is NOT part of a corporate entity

    # Pattern 1: Name v. Defendant, then something that looks like another defendant
    # Example: "Upper Skagit Indian Tribe v. Lundgren, Mills Indian Cmty."
    pattern1 = r"\s+v\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?,\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)"
    match1 = re.search(pattern1, case_name)

    if match1:
        # Check if the part after comma looks like a corporate entity
        after_comma = match1.group(1)
        corporate_indicators = ["Inc", "LLC", "Corp", "Co", "Ltd", "Company", "L.P", "LLP"]

        # If it's NOT a corporate entity, it's likely contamination
        is_corporate = any(indicator in after_comma for indicator in corporate_indicators)

        if not is_corporate:
            logger.warning(
                f"[CONTAMINATION-DETECTED] Pattern 1: '{case_name}' - '{after_comma}' after comma looks suspicious"
            )
            return True

    # Pattern 2: Two separate case patterns in one name
    # Example: "Case1 v. Name1, Case2 v. Name2" (very obvious)
    v_pattern = r"\s+v\.\s+"
    v_matches = list(re.finditer(v_pattern, case_name))

    if len(v_matches) > 1:
        logger.warning(f"[CONTAMINATION-DETECTED] Pattern 2: '{case_name}' has multiple 'v.' patterns")
        return True

    # Pattern 3: Comma followed by capitalized text that doesn't look like continuation
    # Example: "Name v. Defendant, OtherCase v. OtherDefendant"
    pattern3 = r",\s+([A-Z][a-zA-Z\s]+)\s+v\.\s+"
    match3 = re.search(pattern3, case_name)

    if match3:
        logger.warning(f"[CONTAMINATION-DETECTED] Pattern 3: '{case_name}' has case name after comma")
        return True

    return False


def clean_contaminated_case_name(case_name: str) -> str:
    """
    Attempt to clean a contaminated case name by removing the contaminating text.

    Strategy: Take the part BEFORE the suspicious comma.

    Args:
        case_name: The contaminated case name

    Returns:
        Cleaned case name (or original if can't clean)

    Example:
        >>> clean_contaminated_case_name("Upper Skagit Indian Tribe v. Lundgren, Mills Indian Cmty.")
        "Upper Skagit Indian Tribe v. Lundgren"
    """
    if not is_contaminated_case_name(case_name):
        return case_name

    # Find the first " v. " pattern
    v_match = re.search(r"\s+v\.\s+", case_name)
    if not v_match:
        return case_name

    # Find comma after the v. pattern
    v_end = v_match.end()
    comma_pos = case_name.find(",", v_end)

    if comma_pos > 0:
        # Check if this comma is part of corporate entity
        before_comma = case_name[:comma_pos]
        after_comma = case_name[comma_pos + 1 :].strip()

        # If after comma looks like corporate entity, keep it
        corporate_indicators = ["Inc", "LLC", "Corp", "Co", "Ltd"]
        if any(after_comma.startswith(ind) for ind in corporate_indicators):
            return case_name  # Don't clean corporate names

        # Otherwise, take part before comma
        cleaned = before_comma.strip()
        logger.info(f"[CONTAMINATION-CLEANED] '{case_name}' → '{cleaned}'")
        return cleaned

    return case_name


def validate_and_clean_case_name(case_name: Optional[str]) -> Optional[str]:
    """
    Main validation function: detect and clean contaminated case names.

    Args:
        case_name: The extracted case name to validate

    Returns:
        Cleaned case name, or None if invalid
    """
    if not case_name or case_name == "N/A":
        return None

    if is_contaminated_case_name(case_name):
        return clean_contaminated_case_name(case_name)

    return case_name
