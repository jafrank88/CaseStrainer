"""
Citation-type flags for pipeline integration.

Single place to classify citation tokens so extraction, verification, and display
use the same rules. WL/Lexis and other reporter-only citations are driven by
these flags instead of scattered regex checks.
"""

import re
from typing import Optional


def is_statutory_citation(citation_text: Optional[str]) -> bool:
    """
    True if citation is a statute, public law, regulation, or other non-case authority.
    These should NOT go through case name extraction or CourtListener case verification.
    Examples: Pub. L. No. 94-435, 90 Stat. 1383; 15 U.S.C. § 26b; 21 Cong. Rec. 2457
    """
    s = str(citation_text or "").strip()
    if not s:
        return False
    return bool(re.search(
        r'\bPub\.?\s*L\.?\s*No\.?\s*\d+'      # Pub. L. No. 94-435
        r'|\b\d+\s+Stat\.?\s+\d+'              # 90 Stat. 1383
        r'|\bU\.?\s*S\.?\s*C\.?\s*§'           # U.S.C. §
        r'|\bCong\.?\s*Rec\.?\s+\d+'           # Cong. Rec. 2457
        r'|\bC\.?\s*F\.?\s*R\.?\s*§'           # C.F.R. §
        r'|\bFed\.?\s*Reg\.?\s+\d+'            # Fed. Reg.
        r'|\bExec\.?\s*Order\s+No\.?\s*\d+',   # Exec. Order No.
        s, re.IGNORECASE
    ))


def is_proprietary_only_citation(citation_text: Optional[str]) -> bool:
    """
    True if citation is WL or Lexis only (no free-database reporter).
    Drives: name+date fallback in verification, proprietary display message.
    """
    s = str(citation_text or "").strip()
    return bool(
        re.search(r"\b\d{4}\s+WL\s+\d+\b", s, re.IGNORECASE)
        or re.search(r"\b\d{4}\s+(?:U\.S\.?\s+)?LEXIS\s+\d+\b", s, re.IGNORECASE)
    )


def name_likely_in_left_context(citation_text: Optional[str]) -> bool:
    """
    True when the citation token is reporter-only (e.g. "2025 WL 1734066",
    "725 F.3d 651", "521 U.S. 811") so the case name usually appears to the
    left in the document. Drives: left-context name extraction in the main pipeline.
    """
    s = str(citation_text or "").strip()
    if not s:
        return False
    # Citation has " v. " embedded (e.g. "Raines v. Byrd, 521 U.S. 811") -> name in citation
    if " v. " in s:
        return False
    # WL/Lexis: "YYYY WL N" or "X, YYYY WL N" (optional name prefix)
    if re.search(r"\b\d{4}\s+WL\s+\d+\b", s, re.IGNORECASE):
        return bool(re.match(r"^\s*\d{4}\s+WL\s+\d+\s*$", s) or re.match(r"^[^,]*,?\s*\d{4}\s+WL\s+\d+\s*$", s))
    if re.search(r"\b\d{4}\s+(?:U\.S\.?\s+)?LEXIS\s+\d+\b", s, re.IGNORECASE):
        return bool(re.match(r"^\s*\d{4}\s+(?:U\.S\.?\s+)?LEXIS\s+\d+\s*$", s, re.IGNORECASE) or
                    re.match(r"^[^,]*,?\s*\d{4}\s+(?:U\.S\.?\s+)?LEXIS\s+\d+\s*$", s, re.IGNORECASE))
    # Reporter-only: volume + reporter + page with no " v. " (e.g. "725 F.3d 651", "521 U.S. 811")
    if re.search(r"^\s*\d+\s+\S+\s+\d+\s*$", s):
        return True
    # Multi-word reporters: "114 Wash. App. 823", "165 Wn.2d 67", "196 P.3d 691",
    # "100 Cal. App. 4th 200", "50 N.E.2d 100", "75 S.W.3d 200", "80 So. 2d 300", "90 A.2d 400"
    _MULTI_WORD_REPORTER_RE = re.compile(
        r'^\s*\d+\s+(?:'
        r'Wash\.?\s*(?:App\.?\s*)?(?:2d\s+)?'
        r'|Wn\.?\s*(?:App\.?\s*)?(?:2d\s+)?'
        r'|P\.?\s*(?:2d|3d)\s+'
        r'|Cal\.?\s*(?:App\.?\s*)?(?:2d|3d|4th|5th)?\s*'
        r'|N\.?\s*[EWY]\.?\s*(?:2d|3d)?\s*'
        r'|S\.?\s*[EW]\.?\s*(?:2d|3d)?\s*'
        r'|So\.?\s*(?:2d|3d)?\s*'
        r'|A\.?\s*(?:2d|3d)?\s*'
        r')\d+',
        re.IGNORECASE,
    )
    if _MULTI_WORD_REPORTER_RE.search(s):
        return True
    return False
