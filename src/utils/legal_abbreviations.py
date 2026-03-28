"""Legal abbreviation expansion for case name normalization.
Adapted from rlfordon/citation-verifier (name_matcher.py).
"""
import re

LEGAL_ABBREVIATIONS = {
    r"\bInc\.?\b": "Incorporated",
    r"\bCorp\.?\b": "Corporation",
    r"\bLtd\.?\b": "Limited",
    r"\bLLC\b": "Limited Liability Company",
    r"\bCo\.?\b": "Company",
    r"\bAss'n\b": "Association",
    r"\bCnty\.?\b": "County",
    r"\bDep't\b": "Department",
    r"\bDept\.?\b": "Department",
    r"\bComm'n\b": "Commission",
    r"\bComm'r\b": "Commissioner",
    r"\bBd\.?\b": "Board",
    r"\bCtr\.?\b": "Center",
    r"\bUniv\.?\b": "University",
    r"\bColl\.?\b": "College",
    r"\bSch\.?\b": "School",
    r"\bHosp\.?\b": "Hospital",
    r"\bNat'l\b": "National",
    r"\bNatl\.?\b": "National",
    r"\bInt'l\b": "International",
    r"\bIntl\.?\b": "International",
    r"\bMfg\.?\b": "Manufacturing",
    r"\bIns\.?\b": "Insurance",
    r"\bPub\.?\b": "Public",
    r"\bAtty\.?\b": "Attorney",
    r"\bGen\.?\b": "General",
    r"\bSec'y\b": "Secretary",
    r"\bAdm'r\b": "Administrator",
    r"\bAdmin\.?\b": "Administrator",
    r"\bDist\.?\b": "District",
    r"\bDiv\.?\b": "Division",
    r"\bEnt\.?\b": "Entertainment",
    r"\bComput\.?\b": "Computer",
    r"\bRecs\.?\b": "Records",
    r"\bServ\.?\b": "Service",
    r"\bServs\.?\b": "Services",
}

NONDISTINCTIVE_SURNAMES = frozenset({
    "american", "national", "united", "general", "federal",
    "first", "central", "western", "eastern", "northern",
    "southern", "international", "new", "state", "mutual",
    "pacific", "atlantic", "continental", "metropolitan",
})


def expand_abbreviations(name: str) -> str:
    """Expand legal abbreviations in a case name for better matching."""
    if not name:
        return name
    result = name.replace("\u2018", "'").replace("\u2019", "'")
    for pattern, replacement in LEGAL_ABBREVIATIONS.items():
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


def normalize_for_comparison(name: str) -> str:
    """Full normalization pipeline: expand abbreviations, lowercase, remove punctuation."""
    if not name:
        return ""
    expanded = expand_abbreviations(name)
    normalized = expanded.lower().strip()
    normalized = re.sub(r"[^\w\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized
