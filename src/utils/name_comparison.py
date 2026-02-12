"""Shared case name normalization for comparison.

Canonical implementation: handles abbreviation expansion, role words, docket numbers.
"""

import re


def normalize_case_name_for_comparison(name: str) -> str:
    """Normalize a case name for comparison (case-insensitive, abbreviation-aware).

    Removes role words (petitioner, appellant, etc.), docket numbers,
    and expands common legal abbreviations.
    """
    if not name:
        return ""

    normalized = name.lower()

    # Remove role words and docket numbers
    normalized = re.sub(r"\bet\s+al\.?\b", "", normalized)
    normalized = re.sub(
        r"\b(?:petitioners?|appellants?|plaintiffs?|appellees?|respondents?)\b",
        "",
        normalized,
    )
    normalized = re.sub(r"\bno\.?\s*\d+", "", normalized)

    # Normalize common abbreviations to full forms
    abbreviation_map = {
        r"\binc\.?\b": "incorporated",
        r"\bcorp\.?\b": "corporation",
        r"\bco\.?\b": "company",
        r"\bllc\.?\b": "limited liability company",
        r"\bltd\.?\b": "limited",
        r"\blp\.?\b": "limited partnership",
        r"\bassoc\.?\b": "association",
        r"\bauto\.?\b": "automobile",
        r"\bins\.?\b": "insurance",
        r"\bmfg\.?\b": "manufacturing",
        r"\bmgmt\.?\b": "management",
        r"\bchem\.?\b": "chemical",
        r"\bcommc['']?\b": "communications",
    }
    for abbrev, full_form in abbreviation_map.items():
        normalized = re.sub(abbrev, full_form, normalized)

    normalized = re.sub(r"[,.\s]+", " ", normalized)
    return normalized.strip()
