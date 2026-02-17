"""
Utilities to enforce strict separation between extracted and canonical data.

CRITICAL PRINCIPLE:
- extracted_case_name and extracted_date must ONLY contain data from the user's document
- canonical_name and canonical_date must ONLY contain data from verified external sources
- NEVER copy canonical data to extracted fields
- NEVER copy extracted data to canonical fields
"""

import re
import logging
from typing import Optional, Any, Dict

logger = logging.getLogger(__name__)


def extract_year_from_any_date(date_value: Any) -> Optional[str]:
    """
    Extract a 4-digit year from any date format.

    Args:
        date_value: Any date value (string, int, etc.)

    Returns:
        4-digit year string or None
    """
    if not date_value:
        return None

    # Convert to string
    date_str = str(date_value)

    # If it's already a 4-digit year, return it
    if re.match(r"^\d{4}$", date_str):
        return date_str

    # Extract year from ISO date (YYYY-MM-DD)
    year_match = re.search(r"(\d{4})", date_str)
    if year_match:
        year = year_match.group(1)
        # Validate it's a reasonable year
        try:
            year_int = int(year)
            if 1600 <= year_int <= 2100:
                return year
        except ValueError:
            pass

    return None


def is_case_name_contaminated(case_name: str) -> bool:
    """
    Check if a case name contains contamination from canonical data.

    Args:
        case_name: The case name to check

    Returns:
        True if contamination is detected, False otherwise
    """
    if not case_name or case_name.strip().upper() == "N/A":
        return False

    # CRITICAL FIX: Never flag "In re" cases as contaminated
    # These are special case types that should never be corrupted
    if case_name.strip().lower().startswith("in re "):
        logger.debug(f"[DATA-SEPARATION] 'In re' case '{case_name[:50]}...' - NEVER contaminated")
        return False

    # Check for specific contamination patterns
    contamination_patterns = [
        r"\d{4}",  # Years (potential date contamination)
        r"\b(19|20)\d{2}\b",  # Years (potential date contamination)
        r"https?://",  # URLs
        r"www\.",  # URLs
        r"\.com",  # URLs
        r"\.gov",  # URLs
        r"\.edu",  # URLs
        r"\.org",  # URLs
        r"No\. \d+",  # Case numbers (No. 123)
        r"No\.\d+",  # Case numbers without space
        r"\b\d{2,}\b",  # Any 2+ digit numbers (potential page numbers)
        r"\b\d{1,}\b",  # Any numbers at all
    ]
    for pattern in contamination_patterns:
        if re.search(pattern, case_name, re.IGNORECASE):
            return True

    return False


def validate_extracted_date(date_value: Any, source: str = "unknown") -> Optional[str]:
    """
    Validate that an extracted_date contains ONLY a year, not a full ISO date.

    Args:
        date_value: The date value to validate
        source: Source of the date for logging

    Returns:
        Clean 4-digit year or None
    """
    if not date_value or date_value in ("N/A", "Unknown", "Unknown Year"):
        return None

    date_str = str(date_value).strip()

    # Check if it's a clean 4-digit year (allow whitespace)
    if re.match(r"^\d{4}$", date_str):
        return date_str

    # If it's a full ISO date, this is contamination - extract the year
    if re.match(r"^\d{4}-\d{2}-\d{2}", date_str):
        year = date_str[:4]
        logger.warning(
            f"[DATA-CONTAMINATION] extracted_date contained full ISO date '{date_str}' "
            f"from {source}. Extracted year: '{year}'"
        )
        return year

    # Try to extract any 4-digit year from the start of the string
    year_match = re.match(r"(\d{4})", date_str)
    if year_match:
        year = year_match.group(1)
        logger.debug(
            f"[DATE-EXTRACT] Extracted year '{year}' from '{date_str}' for {source}"
        )
        return year

    logger.error(f"[DATA-CONTAMINATION] Could not extract year from '{date_str}' from {source}")
    return None


def clean_citation_extracted_fields(citation: Any) -> None:
    """
    Clean extracted_date and extracted_case_name fields in a citation object.
    Ensures they contain only data from the user's document, not canonical data.

    Args:
        citation: Citation object (dict or CitationResult)
    """
    from src.utils.extraction_cleaner import clean_extracted_case_name

    # Handle dict citations
    if isinstance(citation, dict):
        # Clean extracted_date
        if "extracted_date" in citation and citation["extracted_date"]:
            cleaned_date = validate_extracted_date(
                citation["extracted_date"], f"citation {citation.get('citation', 'unknown')}"
            )
            citation["extracted_date"] = cleaned_date

        # Clean extracted_case_name comprehensively
        if "extracted_case_name" in citation and citation["extracted_case_name"]:
            name = str(citation["extracted_case_name"])
            cleaned_name = clean_extracted_case_name(name)
            if cleaned_name != name:
                logger.warning(f"[DATA-CONTAMINATION] Cleaned case name: '{name}' -> '{cleaned_name}'")
                citation["extracted_case_name"] = cleaned_name

    # Handle CitationResult objects
    elif hasattr(citation, "extracted_date"):
        if citation.extracted_date:
            cleaned_date = validate_extracted_date(
                citation.extracted_date, f"citation {getattr(citation, 'citation', 'unknown')}"
            )
            citation.extracted_date = cleaned_date

        if citation.extracted_case_name:
            name = str(citation.extracted_case_name)
            cleaned_name = clean_extracted_case_name(name)
            if cleaned_name != name:
                logger.warning(f"[DATA-CONTAMINATION] Cleaned case name: '{name}' -> '{cleaned_name}'")
                citation.extracted_case_name = cleaned_name


def clean_cluster_extracted_fields(cluster: Dict[str, Any]) -> None:
    """
    Clean extracted_date and extracted_case_name fields in a cluster dict.

    Args:
        cluster: Cluster dictionary
    """
    # Clean extracted_date
    if "extracted_date" in cluster and cluster["extracted_date"]:
        cleaned_date = validate_extracted_date(
            cluster["extracted_date"], f"cluster {cluster.get('cluster_id', 'unknown')}"
        )
        cluster["extracted_date"] = cleaned_date

    # Also clean the 'year' field if it exists (legacy)
    if "year" in cluster and cluster["year"]:
        cleaned_year = validate_extracted_date(
            cluster["year"], f"cluster {cluster.get('cluster_id', 'unknown')} year field"
        )
        cluster["year"] = cleaned_year


def enforce_data_separation(citations: list, clusters: list = None) -> None:
    """
    Enforce strict data separation across all citations and clusters.

    This is the master function that should be called before returning
    any results to ensure no contamination exists.

    Args:
        citations: List of citation objects
        clusters: Optional list of cluster dicts
    """
    logger.info("[DATA-SEPARATION] Enforcing strict data separation...")

    # Clean all citations
    for citation in citations:
        clean_citation_extracted_fields(citation)

    # Clean all clusters
    if clusters:
        for cluster in clusters:
            clean_cluster_extracted_fields(cluster)

    logger.info("[DATA-SEPARATION] Data separation enforcement complete")


__all__ = [
    "extract_year_from_any_date",
    "validate_extracted_date",
    "clean_citation_extracted_fields",
    "clean_cluster_extracted_fields",
    "enforce_data_separation",
]
