"""Citation patterns for legal citation extraction."""

# Standard citation patterns
CITATION_PATTERNS = {
    # Federal Reporter (e.g., 123 F. 456, 123 F.2d 456, 123 F.3d 456, 123 F.4th 456, 123 F.5th 456, 123 F.6th 456 (9th Cir. 2020))
    # Also handles variations like 2nd and 3rd (will be normalized to 2d/3d)
    "federal_reporter": r"\b(\d{1,3})\s+F\.(?:\s*(\d*(?:st|nd|rd|th|d)))?\s+(\d+)\b(?:\s*,\s*\d+\s*[a-zA-Z\.\s,]*\d{4}\)?)?",
    # U.S. Reports (e.g., 410 U.S. 113, 123 U.S. 456 (2020))
    "us_reports": r"\b\d{1,3}\s+U\.?\s*S\.?\s*\d+\b(?:\s*,\s*\d+\s*[a-zA-Z\.\s,]*\d{4}\)?)?",
    # Supreme Court Reporter (e.g., 100 S. Ct. 1234, 100 S. Ct. 1234 (2020))
    "supreme_court_reporter": r"\b\d{1,3}\s+S\.?\s*Ct\.?\s*\d+\b(?:\s*,\s*\d+\s*[a-zA-Z\.\s,]*\d{4}\)?)?",
    # WestLaw (e.g., 2020 WL 1234567)
    "westlaw": r"\b\d{4}\s+WL\s+\d+\b",
    # LEXIS (e.g., 2020 U.S. LEXIS 1234)
    "lexis": r"\b\d{4}\s+[A-Za-z\.\s]+LEXIS\s+\d+\b",
    # Case citations with v. (e.g., Roe v. Wade, 410 U.S. 113 (1973))
    "case_citation": r"\b[A-Z][A-Za-z]+\s+v\.\s+[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*\s*,\s*\d+\s+[A-Za-z\.\s]+\d+\b",
    # Washington State Reports (e.g., 104 Wn.2d 142, 27 Wn. App. 451)
    "washington_reports": r"\b(\d{1,3})\s+Wn\.(?:\s*(\d*(?:d|nd|rd|th)))?(?:\s+App\.)?\s+(\d+)\b(?:\s*,\s*\d+\s*[a-zA-Z\.\s,]*\d{4}\)?)?",
}

# Common legal citation formats that might appear in text
COMMON_CITATION_FORMATS = [
    # Standard case citation: Roe v. Wade, 410 U.S. 113 (1973)
    r"\b[A-Z][A-Za-z]+\s+v\.\s+[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*\s*,\s*\d+\s+[A-Za-z\.\s]+\d+\b",
    # Short form with just volume and reporter: 410 U.S. 113
    r"\b\d{1,3}\s+[A-Za-z\.\s]+\d+\b",
    # With pin cite: 410 U.S. 113, 120
    r"\b\d{1,3}\s+[A-Za-z\.\s]+\d+\s*,\s*\d+\b",
    # With year: 410 U.S. 113 (1973)
    r"\b\d{1,3}\s+[A-Za-z\.\s]+\d+\s*\(\d{4}\)",
    # WestLaw and LEXIS
    r"\b\d{4}\s+WL\s+\d+\b",
    r"\b\d{4}\s+[A-Za-z\.\s]+LEXIS\s+\d+\b",
]

# Common legal reporters and their abbreviations
LEGAL_REPORTERS = {
    "U.S.": "United States Reports",
    "S. Ct.": "Supreme Court Reporter",
    "L. Ed.": "Lawyers Edition",
    "L. Ed. 2d": "Lawyers Edition, Second Series",
    "F.": "Federal Reporter",
    "F.2d": "Federal Reporter, Second Series",
    "F.3d": "Federal Reporter, Third Series",
    "F.4th": "Federal Reporter, Fourth Series",
    "F.5th": "Federal Reporter, Fifth Series",
    "F.6th": "Federal Reporter, Sixth Series",
    "F. Supp.": "Federal Supplement",
    "F. Supp. 2d": "Federal Supplement, Second Series",
    "F. Supp. 3d": "Federal Supplement, Third Series",
    "A.": "Atlantic Reporter",
    "A.2d": "Atlantic Reporter, Second Series",
    "A.3d": "Atlantic Reporter, Third Series",
    "N.E.": "Northeastern Reporter",
    "N.E.2d": "Northeastern Reporter, Second Series",
    "N.E.3d": "Northeastern Reporter, Third Series",
    "N.W.": "North Western Reporter",
    "N.W.2d": "North Western Reporter, Second Series",
    "P.": "Pacific Reporter",
    "P.2d": "Pacific Reporter, Second Series",
    "P.3d": "Pacific Reporter, Third Series",
    "S.E.": "Southeastern Reporter",
    "S.E.2d": "Southeastern Reporter, Second Series",
    "So.": "Southern Reporter",
    "So.2d": "Southern Reporter, Second Series",
    "So.3d": "Southern Reporter, Third Series",
    "S.W.": "South Western Reporter",
    "S.W.2d": "South Western Reporter, Second Series",
    "S.W.3d": "South Western Reporter, Third Series",
    "Wn.": "Washington Reports",
    "Wn.2d": "Washington Reports, Second Series",
    "Wash. App.": "Washington Appellate Reports",
}


def normalize_washington_citation(citation_text):
    """
    Normalize Washington state citations to standard format.
    Converts 'Wn.' to 'Wash.' and handles series indicators.

    Args:
        citation_text (str): The citation text to normalize

    Returns:
        str: Normalized citation text
    """
    import re

    # Pattern to match Washington citations with series
    pattern = r"(\d{1,3})\s+Wn\.(?:\s*(\d*[a-z]*))?(?:\s+App\.)?\s+(\d+)"

    def replacer(match):
        volume = match.group(1)
        series = (match.group(2) or "").lower()
        page = match.group(3)

        # Check if this is an appellate case (App. appears in the original)
        is_appellate = "app" in match.group(0).lower()

        # Convert series to standard format
        if "2" in series:
            series = "2d"
        elif "3" in series:
            series = "3d"
        elif "4" in series:
            series = "4th"
        else:
            series = ""

        # Build the normalized citation
        parts = [volume, "Wash."]
        if series:
            parts.append(series)
        if is_appellate:
            parts.append("App.")
        parts.append(page)

        return " ".join(parts)

    # Apply the normalization
    normalized = re.sub(pattern, replacer, citation_text, flags=re.IGNORECASE)

    # Clean up any remaining spaces
    normalized = re.sub(r"\\s+", " ", normalized).strip()

    return normalized


def normalize_federal_reporter_citation(citation_text):
    """
    Normalize Federal Reporter citations to standard format.
    Converts variations like '2nd' to '2d', '3rd' to '3d', etc.

    Args:
        citation_text (str): The citation text to normalize

    Returns:
        str: Normalized citation text
    """
    import re

    # Pattern to match Federal Reporter citations with series
    pattern = r"(\d{1,3}\s+F\.)\s*(\d*)(st|nd|rd|th|d)(\s+\d+)"

    def replacer(match):
        series_map = {
            "1st": "1st",
            "2nd": "2d",
            "3rd": "3d",
            "4th": "4th",
            "5th": "5th",
            "6th": "6th",
            "1th": "1st",  # Handle potential typos
            "2th": "2d",
            "3th": "3d",
        }

        prefix = match.group(1)
        number = match.group(2)
        suffix = match.group(3)
        rest = match.group(4)

        # Handle cases where the number is separate from the suffix (e.g., '2 nd')
        series = f"{number or ''}{suffix}"
        normalized_series = series_map.get(series.lower(), series)

        # Special case for first series (just 'F.' with no number)
        if normalized_series == "1st":
            return f"{prefix}{rest}"

        return f"{prefix} {normalized_series}{rest}"

    # Apply the normalization
    normalized = re.sub(pattern, replacer, citation_text, flags=re.IGNORECASE)

    # Clean up any remaining spaces
    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized
