import re
from datetime import date
from typing import Any, List, Optional, Tuple


def normalize_year(date_str: str | None) -> str | None:
    """Return 4-digit year if present; otherwise None.

    Accepts strings like '2018', '2018-12-06', 'Dec 6, 2018'.
    """
    if not date_str:
        return None
    m = re.search(r"(\d{4})", str(date_str))
    return m.group(1) if m else None


def extract_year_value(value: Optional[Any]) -> Optional[str]:
    """Extract a 4-digit year from heterogeneous inputs (int, float, str).

    Validates year is in range 1600-2100.
    """
    if value is None:
        return None

    if isinstance(value, int):
        string_value = str(value)
    elif isinstance(value, float):
        string_value = f"{value:.0f}"
    else:
        string_value = str(value)

    match = re.search(r"(\d{4})", string_value)
    if not match:
        return None

    year = match.group(1)
    try:
        numeric_year = int(year)
    except ValueError:
        return None

    if 1600 <= numeric_year <= 2100:
        return year

    return None


def extract_year_from_citation(citation: str) -> Optional[int]:
    """Extract year from citation text like '572 U.S. 782' or from parenthetical '(2014)'.

    Returns year as integer or None.
    """
    # Look for year in parentheses: (2014)
    paren_match = re.search(r"\((\d{4})\)", citation)
    if paren_match:
        return int(paren_match.group(1))

    # Look for year in reporter: 2014 WL 12345
    reporter_year = re.search(r"\b(19\d{2}|20\d{2})\s+[A-Z]+", citation)
    if reporter_year:
        return int(reporter_year.group(1))

    return None


# Pre-compiled patterns for extract_year_from_text / extract_date_from_text (used by extraction)
_YEAR_PATTERNS = [
    re.compile(r"\((\d{4})\)"),  # (2016)
    re.compile(r"\b(19|20)\d{2}\b"),  # 2016, 1997
]
_DATE_PATTERNS = [
    re.compile(r"(\w+\s+\d{1,2},?\s+\d{4})"),  # January 1, 2024 or Jan 1 2024
    re.compile(r"(\d{1,2}/\d{1,2}/\d{4})"),  # 01/01/2024
]


def extract_year_from_text(text: str) -> Optional[int]:
    """
    Extract a 4-digit year from text.

    Returns:
        Year as integer, or None if not found.
    """
    if not text:
        return None
    for pattern in _YEAR_PATTERNS:
        match = pattern.search(text)
        if match:
            year_str = match.group(1)
            if len(year_str) == 4:
                return int(year_str)
            if len(year_str) == 2:
                year_int = int(year_str)
                if year_int >= 50:
                    return 1900 + year_int
                return 2000 + year_int
    return None


def extract_date_from_text(text: str) -> Optional[str]:
    """
    Extract a full date from text (e.g. 'January 1, 2024' or '01/01/2024').

    Returns:
        Date string, or None if not found. Falls back to year only.
    """
    if not text:
        return None
    for pattern in _DATE_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1)
    year = extract_year_from_text(text)
    if year:
        return str(year)
    return None


# -----------------------------------------------------------------------------
# Year matching for verification (unified rule - single source of truth)
# Used by verification, mismatch_utils, rq_worker, unified_citation_processor_v2.
# -----------------------------------------------------------------------------


def validate_year_match(
    extracted_year: Optional[str],
    canonical_year: Optional[str],
    tolerance: int = 0,
) -> tuple[bool, int]:
    """
    Validate year matching; years must match (unified rule).
    Uses 4-digit year extraction (1600-2100) so 18xx and 17xx are supported.

    Args:
        extracted_year: Year from document
        canonical_year: Year from canonical source
        tolerance: Allowed year difference (default 0 = exact match)

    Returns:
        (is_valid, year_difference)
    """
    if not extracted_year or not canonical_year:
        return True, 0  # Can't validate, assume valid

    ext_str = extract_year_value(extracted_year)
    can_str = extract_year_value(canonical_year)

    if not ext_str or not can_str:
        return True, 0  # Can't parse, assume valid

    ext_year = int(ext_str)
    can_year = int(can_str)
    year_diff = abs(ext_year - can_year)

    return year_diff <= tolerance, year_diff


def years_match_for_verification(
    extracted_date: Optional[str],
    canonical_date: Optional[str],
    tolerance: int = 0,
) -> tuple[bool, int, bool]:
    """
    Single place for year handling in verification (unified rule).
    Returns (years_match, year_diff, extracted_clearly_wrong).
    Use: accept verification when years_match or extracted_clearly_wrong.
    Uses 4-digit year extraction (1600-2100) so 18xx and 17xx are supported.
    """
    if not extracted_date or not canonical_date:
        return True, 0, False
    ext_str = extract_year_value(extracted_date)
    can_str = extract_year_value(canonical_date)
    if not ext_str or not can_str:
        return True, 0, False
    ext_year = int(ext_str)
    can_year = int(can_str)
    year_diff = abs(ext_year - can_year)
    match = year_diff <= tolerance
    # Document/publication date contamination: extracted year recent, canonical old
    extracted_clearly_wrong = (
        (ext_year >= 2015 and can_year < 1950) or (year_diff > 50)
    )
    return match, year_diff, extracted_clearly_wrong


def apply_canonical_date_overrides(
    citations: List[Any],
    canonical_date_str: Optional[str],
    extracted_date_str: Optional[str],
    has_date_mismatch: bool,
    today: Optional[date] = None,
) -> Tuple[Optional[str], bool]:
    """
    Apply "clearly wrong canonical date" overrides (single source of truth).

    Rules:
    1. Canonical is today or future (e.g. date_modified) and extracted is past -> use extracted.
    2. abs(canonical_year - extracted_year) > 15 -> use extracted.
    3. Canonical < 1950 and extracted >= 1990 -> use extracted.

    Updates citation dicts' canonical_date in place when a correction is applied.
    Returns (corrected_canonical_date_or_none, new_has_date_mismatch).
    """
    if today is None:
        today = date.today()
    ext_str = extract_year_value(extracted_date_str) if extracted_date_str else None
    can_str = extract_year_value(canonical_date_str) if canonical_date_str else None
    extracted_year_int = int(ext_str) if ext_str else None
    can_year_int = int(can_str) if can_str else None
    corrected: Optional[str] = None
    new_mismatch = has_date_mismatch

    if extracted_year_int is not None and can_year_int is not None:
        # Rule 1: canonical is today/future (likely date_modified)
        try:
            if (
                canonical_date_str
                and "-" in str(canonical_date_str)
                and len(str(canonical_date_str)) >= 10
            ):
                from datetime import datetime as dt

                parsed = dt.strptime(
                    str(canonical_date_str)[:10], "%Y-%m-%d"
                ).date()
                if (
                    parsed >= today
                    and extracted_year_int < today.year
                ):
                    corrected = str(extracted_year_int)
                    new_mismatch = False
        except Exception:
            pass
        # Rule 2: absurd year difference
        if new_mismatch and abs(can_year_int - extracted_year_int) > 15:
            corrected = str(extracted_year_int)
            new_mismatch = False
        # Rule 3: pre-1950 canonical with post-1990 extracted
        if (
            new_mismatch
            and can_year_int < 1950
            and extracted_year_int >= 1990
        ):
            corrected = str(extracted_year_int)
            new_mismatch = False

    if corrected and citations:
        for c in citations:
            if isinstance(c, dict):
                if c.get("canonical_date"):
                    c["canonical_date"] = corrected
                c["date_mismatch"] = False
            elif hasattr(c, "canonical_date"):
                setattr(c, "canonical_date", corrected)
                if hasattr(c, "date_mismatch"):
                    setattr(c, "date_mismatch", False)

    return corrected, new_mismatch
