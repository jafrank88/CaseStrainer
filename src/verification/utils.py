"""
Verification utility functions.

HTTP session management, citation validation, and case name overlap calculation.
Extracted from unified_verification_master.py (P1 refactoring).
"""

import os
import re
import logging
import requests
from typing import Any, Dict, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

try:
    from src.utils.legal_abbreviations import expand_abbreviations as _expand_legal_abbreviations
except Exception:  # pragma: no cover

    def _expand_legal_abbreviations(name: str) -> str:
        return name or ""


def get_retrying_session(total: int = 3, backoff: float = 0.5, statuses=None) -> requests.Session:
    """Create a requests.Session with retry/backoff for transient errors."""
    if statuses is None:
        statuses = [429, 500, 502, 503, 504]

    retry = Retry(
        total=total,
        read=total,
        connect=total,
        status=total,
        backoff_factor=backoff,
        status_forcelist=statuses,
        allowed_methods=frozenset(["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "TRACE"]),
    )
    adapter = HTTPAdapter(max_retries=retry)
    s = requests.Session()
    # Do not inherit host HTTP(S)_PROXY by default. On some deployments, stale
    # localhost proxy env vars make all CourtListener/fallback requests fail.
    trust_env_raw = (os.getenv("VERIFICATION_TRUST_ENV", "false") or "").strip().lower()
    s.trust_env = trust_env_raw in ("1", "true", "yes", "on")
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s


def build_default_headers(api_key: Optional[str] = None) -> Dict:
    """Build default headers for requests."""
    headers = {
        "User-Agent": "CaseStrainer/1.0 (+https://wolf.law.uw.edu/casestrainer)",
        "Accept": "application/json, text/html",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    if api_key:
        headers["Authorization"] = f"Token {api_key}"

    return headers


def is_citation_likely_valid(citation: str) -> bool:
    """
    Validate if a citation is likely to exist and be verifiable.

    Args:
        citation: The citation string to validate

    Returns:
        bool: True if citation is likely valid, False if obviously invalid
    """
    citation = citation.strip()

    # Skip law reviews and academic publications
    if "L. Rev." in citation or "Law Review" in citation or "L. J." in citation:
        return False

    # Skip non-case citations like statutes, codes, etc.
    if any(x in citation.upper() for x in ["U.S.C.", "CODE", "STAT.", "REG.", "F.R.", "C.F.R."]):
        return False

    # Check for reasonable Supreme Court citation ranges
    scotus_match = re.search(r"S\. Ct\.\s*(\d+)", citation, re.IGNORECASE)
    if scotus_match and int(scotus_match.group(1)) > 700:
        return False

    # Check for reasonable U.S. citation ranges
    us_match = re.search(r"(\d+)\s+U\.?S\.?\s+(\d+)", citation, re.IGNORECASE)
    if us_match and int(us_match.group(1)) > 700:
        return False

    # Proprietary citations (e.g., "2016 WL 6070490") are valid
    if re.search(r"\d{4}\s+WL\s+\d+", citation, re.IGNORECASE):
        return True

    # Must contain a reporter
    reporter_pattern = r"(?:U\.?S\.?|F\.?\s*(?:Supp\.?\s*(?:2d|3d)?|App\'x?|Cas\.?|2d|3d|4th)?|S\.?Ct\.?|L\.?Ed\.?(?:\s*2d)?|Wheat\.?|Cranch|Pet\.?|How\.?|Wall\.?|Black\.?|Dall\.?|B\.?R\.?|T\.?C\.?(?:M\.?)?|A\.?\s*(?:2d|3d)?|N\.?E\.?\s*(?:2d|3d)?|N\.?W\.?\s*(?:2d|3d)?|P\.?\s*(?:2d|3d)?|S\.?E\.?\s*(?:2d|3d)?|So\.?\s*(?:2d|3d)?|S\.?W\.?\s*(?:2d|3d)?|Cal\.?|Ill\.?|Mich\.?|Ohio|Mich|Pa\.?|N\.?Y\.?|Tex\.?|Fla\.?|La\.?|Ala\.?|Ky\.?|Mo\.?|Mont\.?|Okla\.?|Utah|R\.?I\.?|Vt\.?|Me\.?|Del\.?|Idaho|Iowa|N\.?M\.?|Colo\.?|Wash\.?|W\.?Va\.?|Alaska|D\.?C\.?|Haw\.?|Tenn\.?|N\.?C\.?|N\.?D\.?|Va\.?|Conn\.?|Mass\.?|Md\.?|N\.?J\.?|N\.?H\.?|Ariz\.?|Ark\.?|Ga\.?|Ind\.?|Kan\.?|Minn\.?|Miss\.?|Neb\.?|Or\.?|S\.?C\.?|Wyo\.?|Wis\.?|Wn\.?|N\.?Y\.?S\.?|A\.?D\.?|Misc\.?|N\.?E\.?C\.?|C\.?C\.?D\.?|[A-Z]{2,}\.?\s*(?:App\.?\s*Ct\.?|Sup\.?\s*Ct\.?|Ct\.?\s*App\.?|App\.?)?)"
    if not re.search(reporter_pattern, citation, re.IGNORECASE):
        return False

    # Must contain a volume and page number
    if not re.search(r"\d+\s+[A-Za-z\.\s]+?\d+", citation):
        return False

    return True


def _normalize_mdl_overlap_name(name: str) -> str:
    """Align MDL short captions with full 'In re … Antitrust Litigation' names for overlap."""
    if not name:
        return ""
    n = name.lower().strip()
    n = re.sub(r"^in\s+re\s+", "", n)
    n = re.sub(r"\s+antitrust\s+litig\.?$", "", n)
    n = re.sub(r"\s+antitrust\s+litigation\.?$", "", n)
    n = re.sub(r"\s+direct\s+purchaser\s+antitrust\s+litig\.?$", "", n)
    n = re.sub(r"\s+direct\s+purchaser\s+antitrust\s+litigation\.?$", "", n)
    return re.sub(r"\s+", " ", n).strip()


def calculate_case_name_overlap(extracted_name: str, canonical_name: str) -> float:
    """
    Calculate overlap between two case names with improved logic.

    Args:
        extracted_name: The extracted case name
        canonical_name: The canonical case name from search results

    Returns:
        float: Overlap score between 0.0 and 1.0
    """
    if not extracted_name or not canonical_name:
        return 0.0

    # Normalize both names (MDL / In re bridging, then strip punctuation for token comparison)
    extracted_norm = re.sub(
        r"[^\w\s]", "", _normalize_mdl_overlap_name(extracted_name)
    )
    canonical_norm = re.sub(
        r"[^\w\s]", "", _normalize_mdl_overlap_name(canonical_name)
    )

    # Check for exact match
    if extracted_norm == canonical_norm:
        return 1.0

    # Check for substring matches (very strong indicator)
    if extracted_norm in canonical_norm or canonical_norm in extracted_norm:
        return 0.9

    # Special handling for "State v. X" patterns
    state_v_pattern = re.match(r'^state\s+v\.?\s+(.+)$', extracted_norm)
    state_of_pattern = re.match(r'^state\s+of\s+\w+\s+v\.?\s+(.+)$', canonical_norm)
    if state_v_pattern and state_of_pattern:
        extracted_defendant = state_v_pattern.group(1).strip()
        canonical_defendant = state_of_pattern.group(1).strip()
        if extracted_defendant and canonical_defendant:
            if extracted_defendant in canonical_defendant or canonical_defendant in extracted_defendant:
                return 0.85
            def_words_e = set(extracted_defendant.split())
            def_words_c = set(canonical_defendant.split())
            if def_words_e & def_words_c:
                return 0.80

    # Split into words
    extracted_words = set(extracted_norm.split())
    canonical_words = set(canonical_norm.split())

    # Remove common legal words and stop words
    common_words = {
        "v", "v.", "vs", "vs.", "the", "of", "in", "a", "an", "&", "and",
        "inc", "inc.", "llc", "ltd", "ltd.", "co", "co.", "corp", "corp.",
        "dept", "dept.", "department", "city", "county", "state", "united",
        "america", "american", "national", "federal", "public", "private",
        "group", "groups", "association", "associations", "society", "societies",
    }

    extracted_words -= common_words
    canonical_words -= common_words

    # If no meaningful words left, return 0
    if not extracted_words or not canonical_words:
        return 0.0

    # Calculate Jaccard similarity
    intersection = extracted_words & canonical_words
    union = extracted_words | canonical_words

    if not union:
        return 0.0

    jaccard = len(intersection) / len(union)

    # Bonus for matching party names (words before and after 'v')
    extracted_parts = extracted_norm.split("v")
    canonical_parts = canonical_norm.split("v")

    if len(extracted_parts) >= 2 and len(canonical_parts) >= 2:
        plaintiff_extracted = extracted_parts[0].strip()
        plaintiff_canonical = canonical_parts[0].strip()

        if plaintiff_extracted and plaintiff_canonical:
            plaintiff_words_e = set(plaintiff_extracted.split())
            plaintiff_words_c = set(plaintiff_canonical.split())
            plaintiff_words_e -= common_words
            plaintiff_words_c -= common_words

            if plaintiff_words_e and plaintiff_words_c:
                plaintiff_overlap = len(plaintiff_words_e & plaintiff_words_c) / len(
                    plaintiff_words_e | plaintiff_words_c
                )
                jaccard += plaintiff_overlap * 0.2

        defendant_extracted = extracted_parts[1].strip()
        defendant_canonical = canonical_parts[1].strip()

        if defendant_extracted and defendant_canonical:
            defendant_words_e = set(defendant_extracted.split())
            defendant_words_c = set(defendant_canonical.split())
            defendant_words_e -= common_words
            defendant_words_c -= common_words

            if defendant_words_e and defendant_words_c:
                defendant_overlap = len(defendant_words_e & defendant_words_c) / len(
                    defendant_words_e | defendant_words_c
                )
                jaccard += defendant_overlap * 0.2

    # Ensure the score doesn't exceed 1.0
    return min(jaccard, 1.0)


# Year matching: single source of truth in date_utils (no utils -> verification dependency)
from src.utils.date_utils import validate_year_match, years_match_for_verification


def is_federal_citation(citation: str) -> bool:
    """Check if citation is federal (U.S., F.2d, F.3d, etc.)."""
    federal_patterns = [
        r"\bU\.?S\.?\b",
        r"\bF\.?\d*d\b",
        r"\bF\.?\s*Supp\.?\b",
        r"\bF\.?App'x\b",
    ]
    
    for pattern in federal_patterns:
        if re.search(pattern, citation, re.IGNORECASE):
            return True
    
    return False


def is_supreme_court_citation(citation: str) -> bool:
    """Check if citation is U.S. Supreme Court."""
    return bool(re.search(r"\b\d+\s+U\.?S\.?\s+\d+\b", citation, re.IGNORECASE))


def get_reporter_type(citation: str) -> Optional[str]:
    """Extract reporter type from citation."""
    reporter_patterns = [
        (r"\bU\.?S\.?\b", "U.S."),
        (r"\bS\.?\s*Ct\.?\b", "S.Ct."),
        (r"\bL\.?\s*Ed\.?\s*2d\b", "L.Ed.2d"),
        (r"\bL\.?\s*Ed\.?\b", "L.Ed."),
        (r"\bF\.?\s*Supp\.?\s*3d\b", "F.Supp.3d"),
        (r"\bF\.?\s*Supp\.?\s*2d\b", "F.Supp.2d"),
        (r"\bF\.?\s*Supp\.?\b", "F.Supp."),
        (r"\bF\.?3d\b", "F.3d"),
        (r"\bF\.?2d\b", "F.2d"),
    ]
    
    for pattern, reporter in reporter_patterns:
        if re.search(pattern, citation, re.IGNORECASE):
            return reporter
    
    return None


def normalize_citation(citation: str) -> str:
    """Normalize citation for comparison."""
    # Remove extra whitespace
    normalized = " ".join(citation.split())
    # Lowercase
    normalized = normalized.lower()
    return normalized


# Shared by batch citation-lookup and CourtListenerVerifier: reject wrong cluster when only
# generic tokens overlap (e.g. "United Food ..." vs "United States Ex Rel. ..." share "united").
_WEAK_FIRST_PARTY_TOKENS = frozenset(
    {
        "united",
        "state",
        "states",
        "u",
        "s",
        "us",
        "people",
        "ex",
        "rel",
        "in",
        "re",
        "the",
    }
)
_WEAK_SECOND_PARTY_TOKENS = frozenset(
    {
        "inc",
        "llc",
        "ltd",
        "corp",
        "co",
        "plc",
        "limited",
        "company",
        "the",
        "of",
        "and",
    }
)


def cluster_matches_extracted_case_name(cluster: Dict[str, Any], extracted_case_name: str) -> bool:
    """
    Return False when the cluster's case name is clearly a different case than the document's.
    Used when CourtListener returns exactly one cluster for a WL / reporter cite that may still
    be the wrong opinion.
    """
    if not extracted_case_name or len(extracted_case_name.strip()) < 4:
        return True
    cn = (cluster.get("case_name") or cluster.get("caseName") or "").strip()
    if not cn:
        return True
    # Match multi-cluster CL selection: spaced initials (F. D. I. C.) must expand or tokens
    # {f,d,i,c} never overlap "federal"/"deposit"/"insurance" and we reject the only cluster.
    ecn_expanded = _expand_legal_abbreviations(extracted_case_name.strip())
    cn_expanded = _expand_legal_abbreviations(cn)
    ecn_lower = ecn_expanded.lower().strip()
    cn_lower = cn_expanded.lower().strip()
    ecn_parts = re.split(r"\s+v\.?\s+", ecn_lower, maxsplit=1)
    cn_parts = re.split(r"\s+v\.?\s+", cn_lower, maxsplit=1)
    ecn_first = (ecn_parts[0].strip() if ecn_parts else "").split()
    cn_first = (cn_parts[0].strip() if cn_parts else "").split()
    if not ecn_first or not cn_first:
        return True
    stop = {"inc", "co", "ltd", "llc", "corp", "comm'n", "commission", "commissioner"}
    ecn_tokens = set(w.strip(".,'") for w in ecn_first if w.strip(".,'") and w.strip(".,'") not in stop)
    cn_tokens = set(w.strip(".,'") for w in cn_first if w.strip(".,'") and w.strip(".,'") not in stop)
    if not ecn_tokens or not cn_tokens:
        return True
    overlap_plaintiff = ecn_tokens & cn_tokens
    strong_plaintiff = overlap_plaintiff - _WEAK_FIRST_PARTY_TOKENS
    if overlap_plaintiff and not strong_plaintiff and len(ecn_parts) > 1 and len(cn_parts) > 1:
        ecn_def = (ecn_parts[1].strip() if len(ecn_parts) > 1 else "").split()
        cn_def = (cn_parts[1].strip() if len(cn_parts) > 1 else "").split()
        ecn_d = set(w.strip(".,'") for w in ecn_def if w.strip(".,'") and w.strip(".,'") not in stop)
        cn_d = set(w.strip(".,'") for w in cn_def if w.strip(".,'") and w.strip(".,'") not in stop)
        strong_def = (ecn_d & cn_d) - _WEAK_SECOND_PARTY_TOKENS
        if not strong_def:
            return False
    if ecn_tokens.isdisjoint(cn_tokens):
        ecn_str = " ".join(sorted(ecn_tokens))
        cn_str = " ".join(sorted(cn_tokens))
        # Require length >= 3 on both tokens for a in b — avoids "i" in "cipro" style noise
        if not (ecn_str in cn_str or cn_str in ecn_str or any(
            len(a) >= 3 and len(b) >= 3 and (a in b or b in a)
            for a in ecn_tokens
            for b in cn_tokens
        )):
            return False
    return True
