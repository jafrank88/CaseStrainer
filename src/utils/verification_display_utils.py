"""
Shared verification/display helpers used across backend response paths.
"""

from __future__ import annotations

import re
from typing import Any


def has_canonical_url(cit: Any) -> bool:
    if isinstance(cit, dict):
        u = cit.get("canonical_url") or cit.get("url")
    else:
        u = getattr(cit, "canonical_url", None) or getattr(cit, "url", None)
    return bool(u and str(u).strip())


def is_effectively_verified_citation(cit: Any) -> bool:
    if not cit:
        return False
    if isinstance(cit, dict):
        verified = bool(cit.get("verified") is True or cit.get("verified") == "true" or cit.get("is_verified") is True)
        hard_mismatch = bool(cit.get("date_mismatch") is True)
        status = str(cit.get("verification_status") or "").strip().lower()
    else:
        verified = bool(getattr(cit, "verified", False) or getattr(cit, "is_verified", False))
        hard_mismatch = bool(getattr(cit, "date_mismatch", False))
        status = str(getattr(cit, "verification_status", "") or "").strip().lower()
    # CRITICAL FIX: Preserve real canonical URLs even with date mismatch
    # Check if citation has a real (non-Google) canonical URL
    has_real_url = False
    if isinstance(cit, dict):
        url = cit.get("canonical_url") or cit.get("url")
    else:
        url = getattr(cit, "canonical_url", None) or getattr(cit, "url", None)
    if url and str(url).strip():
        url_str = str(url).lower()
        has_real_url = not (url_str.startswith('https://www.google.com') or 
                           url_str.startswith('http://www.google.com'))
    # Reject on hard mismatch only if no real URL present
    # If there's a real URL, keep it even with date mismatch (for "Date Differences" section)
    if (hard_mismatch or status in {"year_mismatch", "possible_match_with_url", "possible_match_gate_reject"}) and not has_real_url:
        return False
    # USER RULE: Google search URL = unverified. Do not treat as effectively verified.
    if not has_real_url:
        return False
    return verified and has_canonical_url(cit)


def is_proprietary_citation(citation_text: str) -> bool:
    s = str(citation_text or "")
    return bool(
        re.search(r"\b\d{4}\s+WL\s+\d+\b", s, re.IGNORECASE)
        or re.search(r"\b\d{4}\s+(?:U\.S\.?\s+)?LEXIS\s+\d+\b", s, re.IGNORECASE)
    )


def citation_core_key(citation_text: str) -> str:
    s = str(citation_text or "").strip()
    if not s:
        return ""
    # Normalize Wash./Wn. spacing so both spellings produce the same key.
    # "Wash. 2d" -> "Wn.2d", "Wn. 2d" -> "Wn.2d", "Wn.2d" stays "Wn.2d"
    s = re.sub(r"\bWash\.\s*App\.\s*", "Wn.App. ", s)
    s = re.sub(r"\bWash\.\s*", "Wn.", s)
    s = re.sub(r"\bWn\.\s*App\.\s*", "Wn.App. ", s)
    s = re.sub(r"\bWn\.\s*(\d)", r"Wn.\1", s)

    m = re.search(r"\b((?:17|18|19|20)\d{2})\s*(WL|U\.?\s*S\.?\s*LEXIS|LEXIS)\s*(\d+)\b", s, re.IGNORECASE)
    if m:
        return f"{m.group(1)} {m.group(2).lower()} {m.group(3)}"
    m = re.search(
        r"\b\d+\s+(?:U\.?\s*S\.?|F\.?\s*Supp\.?\s*(?:\d+d)?|F\.?\d+d|F\.?\d+th|F\.?\s*R\.?\s*D\.?|"
        r"Wn\.?\s*App\.?\s*[23]d|Wn\.?\s*[23]d|P\.?\s*[23]d|N\.?E\.?\s*[23]d|S\.?E\.?\s*[23]d|"
        r"S\.?W\.?\s*[23]d|N\.?W\.?\s*2d|A\.?\s*[23]d|Cal\.?\s*(?:App\.?\s*)?[234](?:th|d)|"
        r"Ohio\s+St\.?\s*[23]d|Ill\.?\s*App\.?\s*[23]d|"
        r"App\.?\s*D\.?\s*C\.?|L\.?\s*Ed\.?\s*(?:2d)?|S\.?\s*Ct\.?|"
        r"Cranch|Wheat\.?|Wall\.?|Pet\.?|How\.?|Black|Dall\.?|"
        r"Va\.?\s*|Pa\.?\s*|N\.?\s*C\.?\s*)\s+\d+\b",
        s,
        re.IGNORECASE,
    )
    if m:
        return re.sub(r"\s+", " ", m.group(0).strip()).lower()
    return re.sub(r"\s+", " ", s.strip()).lower()

