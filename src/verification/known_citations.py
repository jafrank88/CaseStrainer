"""
Known citation lookup tables and helpers.

Static lookup tables for citations that are frequently misresolved by APIs.
Extracted from unified_verification_master.py (P1 refactoring).
"""

import re
from typing import Dict, Any, Optional


def _normalize_citation_for_known_lookup(citation: str) -> str:
    """Normalize citation so it matches KNOWN_FEDERAL_CITATIONS keys (e.g. '426 U. S. 26' -> '426 u.s. 26')."""
    if not citation:
        return ""
    s = re.sub(r"\s+", " ", citation.strip()).lower()
    # Collapse "u. s." to "u.s." so "426 u. s. 26" matches key "426 u.s. 26"
    s = re.sub(r"u\.\s*s\.?", "u.s.", s, flags=re.IGNORECASE)
    # Collapse "f. 3d" / "f. 2d" / "f. 4th" to "f.3d" etc. so "199 f. 3d 263" matches "199 f.3d 263"
    s = re.sub(r"f\.\s*3d\b", "f.3d", s, flags=re.IGNORECASE)
    s = re.sub(r"f\.\s*2d\b", "f.2d", s, flags=re.IGNORECASE)
    s = re.sub(r"f\.\s*4th\b", "f.4th", s, flags=re.IGNORECASE)
    return s.strip()


KNOWN_FEDERAL_CITATIONS = {
    "426 u.s. 26": {
        "canonical_name": "Simon v. Eastern Kentucky Welfare Rights Organization",
        "canonical_date": "1976-06-01",
        "canonical_year": "1976",
        "canonical_url": "https://supreme.justia.com/cases/federal/us/426/26/",
    },
    "524 u.s. 11": {
        "canonical_name": "Federal Election Commission v. Akins",
        "canonical_date": "1998-06-01",
        "canonical_year": "1998",
        "canonical_url": "https://supreme.justia.com/cases/federal/us/524/11/",
    },
    "554 u.s. 269": {
        "canonical_name": "Sprint Communications Co. v. APCC Services, Inc.",
        "canonical_date": "2008-06-23",
        "canonical_year": "2008",
        "canonical_url": "https://supreme.justia.com/cases/federal/us/554/269/",
    },
    "523 u.s. 83": {
        "canonical_name": "Steel Co. v. Citizens for a Better Environment",
        "canonical_date": "1998-01-12",
        "canonical_year": "1998",
        "canonical_url": "https://supreme.justia.com/cases/federal/us/523/83/",
    },
    "6 wheat. 264": {
        "canonical_name": "Cohens v. Virginia",
        "canonical_date": "1821-03-03",
        "canonical_year": "1821",
        "canonical_url": "https://supreme.justia.com/cases/federal/us/19/264/",
    },
    "455 u.s. 363": {
        "canonical_name": "Havens Realty Corp. v. Coleman",
        "canonical_date": "1982-02-24",
        "canonical_year": "1982",
        "canonical_url": "https://supreme.justia.com/cases/federal/us/455/363/",
    },
    "490 u.s. 605": {
        "canonical_name": "ASARCO Inc. v. Kadish",
        "canonical_date": "1989-05-30",
        "canonical_year": "1989",
        "canonical_url": "https://supreme.justia.com/cases/federal/us/490/605/",
    },
    "199 f.3d 263": {
        "canonical_name": "Washington v. CSC Credit Services, Inc.",
        "canonical_date": "2000-01-01",
        "canonical_year": "2000",
        "canonical_url": "https://law.justia.com/cases/federal/appellate-courts/F3/199/263/",
    },
    "578 u.s. 330": {
        "canonical_name": "Spokeo, Inc. v. Robins",
        "canonical_date": "2016-05-16",
        "canonical_year": "2016",
        "canonical_url": "https://supreme.justia.com/cases/federal/us/578/330/",
    },
    "568 u.s. 398": {
        "canonical_name": "Clapper v. Amnesty Int'l USA",
        "canonical_date": "2013-02-26",
        "canonical_year": "2013",
        "canonical_url": "https://supreme.justia.com/cases/federal/us/568/398/",
    },
    "555 u.s. 460": {
        "canonical_name": "Pleasant Grove City v. Summum",
        "canonical_date": "2009-02-25",
        "canonical_year": "2009",
        "canonical_url": "https://supreme.justia.com/cases/federal/us/555/460/",
    },
}

# Slip opinions (e.g. 588 U.S. ___): key = "volume year", value = list of { canonical_name, canonical_date, canonical_url }
# Used when extracted_case_name matches so we resolve to the correct case (e.g. American Legion, not Loper Bright for 588 2019)
KNOWN_SLIP_CITATIONS = {
    "588 2019": [
        {
            "canonical_name": "American Legion v. American Humanist Ass'n",
            "canonical_date": "2019-06-20",
            "canonical_url": "https://supreme.justia.com/cases/federal/us/588/17-1717/",
            "canonical_url_alt": "https://www.supremecourt.gov/opinions/18pdf/17-1717_4f14.pdf",
        },
    ],
    "592 2021": [
        {
            "canonical_name": "Uzuegbunam v. Preczewski",
            "canonical_date": "2021-03-08",
            "canonical_url": "https://supreme.justia.com/cases/federal/us/592/19-968/",
        },
    ],
}


def _lookup_known_federal(cit_str: str) -> Optional[Dict[str, Any]]:
    """Return KNOWN_FEDERAL_CITATIONS entry for citation string, or None. Shared by dict and object applicators."""
    import re as _re
    norm = _normalize_citation_for_known_lookup(cit_str or "")
    if not norm:
        return None
    lookup = norm
    if lookup not in KNOWN_FEDERAL_CITATIONS:
        base_m = (
            _re.match(r"^(\d+\s+u\.s\.\s*\d+)", norm)
            or _re.match(r"^(\d+\s+wheat\.\s*\d+)", norm)
            or _re.match(r"^(\d+\s+f\.3d\s*\d+)", norm)
            or _re.match(r"^(\d+\s+f\.2d\s*\d+)", norm)
            or _re.match(r"^(\d+\s+f\.4th\s*\d+)", norm)
        )
        if base_m:
            lookup = base_m.group(1).strip().lower()
    return KNOWN_FEDERAL_CITATIONS.get(lookup)


def _lookup_known_slip(
    citation: str, extracted_case_name: Optional[str], extracted_date: Optional[str]
) -> Optional[Dict[str, Any]]:
    """If citation is a U.S. slip (e.g. 588 U.S. ___) and we have a known slip for that volume+year matching extracted name, return it."""
    from src.verification.utils import calculate_case_name_overlap

    if not citation or not extracted_case_name or (extracted_case_name or "").strip() in ("", "N/A"):
        return None
    m = re.search(r"(\d+)\s+U\.?\s*S\.?\s+[_\u2013\u2014]+", citation, re.IGNORECASE)
    if not m:
        return None
    volume = m.group(1)
    year = None
    if extracted_date:
        ym = re.search(r"(19|20)\d{2}", str(extracted_date))
        if ym:
            year = int(ym.group(0))
    if not year:
        return None
    key = f"{volume} {year}"
    entries = KNOWN_SLIP_CITATIONS.get(key)
    if not entries:
        return None
    for entry in entries:
        canonical_name = entry.get("canonical_name") or ""
        if not canonical_name:
            continue
        overlap = calculate_case_name_overlap(extracted_case_name, canonical_name)
        if overlap >= 0.4:
            return entry
    return None
