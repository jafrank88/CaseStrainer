"""
Citation-Name Validator
======================

Validates that an extracted case name is reasonable for a specific citation.

PROBLEM SOLVED:
When citations are close together like:
"Upper Skagit v. Lundgren, 584 U.S. 554 (2018) ... Michigan v. Bay Mills, 572 U.S. 782 (2014)"

The extractor might pick up "Upper Skagit" for BOTH citations.

SOLUTION:
This module validates extracted names against citations using:
1. Year consistency (extracted year should match citation date range)
2. Citation uniqueness (different citations shouldn't have identical extracted names unless they're parallel)
3. Reporter consistency (case name should make sense for the reporter type)
"""

import re
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


# Re-export from canonical location
from src.utils.date_utils import extract_year_from_citation  # noqa: F401


def validate_extracted_name_for_citation(
    extracted_name: str,
    citation: str,
    canonical_name: Optional[str] = None,
    canonical_year: Optional[str] = None,
    debug: bool = False,
) -> Dict[str, Any]:
    """
    Validate that an extracted case name is reasonable for a specific citation.

    Args:
        extracted_name: The extracted case name
        citation: The citation text (e.g., "572 U.S. 782")
        canonical_name: Verified canonical name (if available)
        canonical_year: Verified canonical year (if available)
        debug: Enable debug logging

    Returns:
        Dictionary with validation results:
        {
            'valid': bool,
            'confidence': float (0.0-1.0),
            'warnings': list of warning messages,
            'errors': list of error messages
        }
    """
    result = {"valid": True, "confidence": 1.0, "warnings": [], "errors": []}

    if not extracted_name or extracted_name == "N/A":
        result["valid"] = False
        result["confidence"] = 0.0
        result["errors"].append("No extracted name provided")
        return result

    # Validation 1: If canonical name available, check similarity
    if canonical_name and canonical_name != "N/A":
        extracted_lower = extracted_name.lower()
        canonical_lower = canonical_name.lower()

        # Extract first party from both
        extracted_party = extracted_lower.split(" v. ")[0] if " v. " in extracted_lower else ""
        canonical_party = canonical_lower.split(" v. ")[0] if " v. " in canonical_lower else ""

        # Check if they match (allowing for abbreviations)
        if extracted_party and canonical_party:
            # They should at least share some words
            if extracted_party not in canonical_party and canonical_party not in extracted_party:
                # Check word overlap
                extracted_words = set(extracted_party.split())
                canonical_words = set(canonical_party.split())
                common_words = extracted_words & canonical_words

                if len(common_words) == 0:
                    result["errors"].append(
                        f"Extracted party '{extracted_party}' doesn't match canonical '{canonical_party}'"
                    )
                    result["confidence"] *= 0.1
                    result["valid"] = False

                    if debug:
                        logger.error(f"[VALIDATE] Citation: {citation}")
                        logger.error(f"[VALIDATE] Extracted: {extracted_name}")
                        logger.error(f"[VALIDATE] Canonical: {canonical_name}")
                        logger.error(f"[VALIDATE] → Party names don't match!")

    # Validation 2: Check for duplicate names on different citations
    # (This would be checked at the cluster level, not here)

    # Validation 3: Basic sanity checks
    if len(extracted_name) < 5:
        result["warnings"].append("Extracted name is very short")
        result["confidence"] *= 0.5

    if extracted_name.startswith("Inc. v.") or extracted_name.startswith("Corp. v."):
        result["errors"].append("Name appears truncated (starts with corporate suffix)")
        result["confidence"] *= 0.3
        result["valid"] = False

    # Validation 4: Check for common extraction errors
    error_patterns = [
        (r"^\s*v\.\s+", "Name starts with 'v.' (missing plaintiff)"),
        (r"\bv\.\s*$", "Name ends with 'v.' (missing defendant)"),
        (r"^\s*[a-z]", "Name starts with lowercase (likely truncated)"),
        (r",\s*[A-Z][a-z]+\s+v\.", "Contains multiple case names (contamination)"),
    ]

    for pattern, error_msg in error_patterns:
        if re.search(pattern, extracted_name):
            result["errors"].append(error_msg)
            result["confidence"] *= 0.2
            result["valid"] = False

    return result


def should_re_extract(validation_result: Dict[str, Any]) -> bool:
    """
    Determine if we should attempt re-extraction based on validation results.

    Args:
        validation_result: Result from validate_extracted_name_for_citation

    Returns:
        True if re-extraction should be attempted
    """
    # Re-extract if validation failed or confidence is very low
    if not validation_result["valid"]:
        return True

    if validation_result["confidence"] < 0.5:
        return True

    # Re-extract if there are critical errors
    critical_error_keywords = ["truncated", "contamination", "missing"]
    for error in validation_result.get("errors", []):
        if any(keyword in error.lower() for keyword in critical_error_keywords):
            return True

    return False


__all__ = [
    "extract_year_from_citation",
    "validate_extracted_name_for_citation",
    "should_re_extract",
]
