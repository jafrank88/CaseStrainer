"""
Verification data models.

Contains VerificationSource enum and VerificationResult dataclass.
Extracted from unified_verification_master.py (P1 refactoring).
"""

import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class VerificationSource(Enum):
    """Enumeration of verification sources in priority order."""

    COURTLISTENER_LOOKUP = "courtlistener_lookup"
    COURTLISTENER_SEARCH = "courtlistener_search"
    JUSTIA = "justia"
    GOOGLE_SCHOLAR = "google_scholar"
    FINDLAW = "findlaw"
    LEAGLE = "leagle"
    CASEMINE = "casemine"
    VLEX = "vlex"
    LAW_RESOURCE = "law_resource"
    BING = "bing"
    DUCKDUCKGO = "duckduckgo"
    SCRAPINGBEE = "scrapingbee"


@dataclass
class VerificationResult:
    """Standardized result from verification."""

    citation: str
    verified: bool = False
    possible_match: bool = False  # NEW: Case name found but citation not verified
    canonical_name: Optional[str] = None
    canonical_date: Optional[str] = None
    canonical_url: Optional[str] = None
    source: Optional[str] = None
    confidence: float = 0.0
    method: str = "none"
    raw_data: Optional[Dict] = None
    validation_warning: Optional[str] = None  # Warning if canonical/extracted names don't match
    warnings: List[str] = None
    error: Optional[str] = None

    @classmethod
    def create_verified(
        cls,
        citation: str,
        canonical_name: Optional[str],
        canonical_date: Optional[str],
        canonical_url: Optional[str],
        source: Optional[str] = None,
        confidence: float = 1.0,
        method: str = "verified",
        **kwargs,
    ):
        """
        Create a VerificationResult with automatic verification status based on canonical data presence.

        USER RULE: verified=True ONLY if ALL three canonical fields are present:
        - canonical_name (required)
        - canonical_date (required)
        - canonical_url (required)

        If any field is missing, verified=False even if source found the citation.
        """
        # Check if ALL required canonical fields are present
        has_all_canonical_data = (
            canonical_name is not None
            and canonical_name.strip() != ""
            and canonical_date is not None
            and str(canonical_date).strip() != ""
            and canonical_url is not None
            and canonical_url.strip() != ""
        )

        return cls(
            citation=citation,
            verified=has_all_canonical_data,  # Auto-set based on data presence
            possible_match=False,  # Not a possible match if we have all data
            canonical_name=canonical_name,
            canonical_date=canonical_date,
            canonical_url=canonical_url,
            source=source,
            confidence=confidence if has_all_canonical_data else 0.0,
            method=method if has_all_canonical_data else "partial_data",
            error=(
                None
                if has_all_canonical_data
                else f"Missing canonical data (name={canonical_name is not None}, date={canonical_date is not None}, url={canonical_url is not None})"
            ),
            **kwargs,
        )

    @classmethod
    def create_possible_match(
        cls,
        citation: str,
        canonical_name: Optional[str],
        canonical_url: Optional[str],
        canonical_date: Optional[str] = None,
        extracted_date: Optional[str] = None,
        source: Optional[str] = None,
        confidence: float = 0.6,
        method: str = "possible_match",
        **kwargs,
    ):
        """
        Create a VerificationResult for a possible match (case name found but citation not verified).

        This is used when we find a case with matching name but the specific citation is not found
        on the page or doesn't match exactly.

        IMPORTANT: Years must match for this to be a valid possible match.
        """
        # Extract years for validation
        extracted_year = None
        canonical_year = None

        if extracted_date:
            year_match = re.search(r"(\d{4})", str(extracted_date))
            if year_match:
                extracted_year = year_match.group(1)

        if canonical_date:
            year_match = re.search(r"(\d{4})", str(canonical_date))
            if year_match:
                canonical_year = year_match.group(1)

        # Validate year matching
        year_mismatch_error = None
        if extracted_year and canonical_year and extracted_year != canonical_year:
            year_mismatch_error = f"Years don't match (extracted: {extracted_year}, canonical: {canonical_year})"
            confidence = 0.2  # Very low confidence for year mismatch

        return cls(
            citation=citation,
            verified=False,  # Not fully verified
            possible_match=year_mismatch_error is None,  # Only possible match if years match
            canonical_name=canonical_name,
            canonical_date=canonical_date,
            canonical_url=canonical_url,
            source=source,
            confidence=confidence,
            method=method,
            error=year_mismatch_error
            or f"Possible match found: case name '{canonical_name}' found but citation '{citation}' not verified",
            **kwargs,
        )
