"""
RQ Worker helper functions and constants.

Extracted from rq_worker.py to reduce monolith size and allow reuse.
Used for: jurisdiction/reporter detection, parallel citation checks, memory release.
"""

import re
from typing import Optional

# State-specific reporters for jurisdiction checking
STATE_REPORTERS = {
    "ohio": ["Ohio St.", "Ohio App.", "Ohio Misc.", "N.E.", "N.E.2d", "N.E.3d"],
    "nebraska": ["Neb.", "Neb. App.", "N.W.", "N.W.2d"],
    "washington": ["Wash.", "Wn.", "Wn.2d", "Wn. App.", "Wn. App. 2d", "P.", "P.2d", "P.3d"],
    "connecticut": ["Conn.", "Conn. App.", "Conn. Supp.", "A.", "A.2d", "A.3d"],
    "california": ["Cal.", "Cal.2d", "Cal.3d", "Cal.4th", "Cal.5th", "Cal. App.", "Cal. Rptr."],
    "new_york": ["N.Y.", "N.Y.2d", "N.Y.3d", "A.D.", "A.D.2d", "A.D.3d", "N.Y.S.", "N.Y.S.2d", "N.Y.S.3d"],
    "federal": [
        "U.S.",
        "S. Ct.",
        "L. Ed.",
        "L. Ed. 2d",
        "F.",
        "F.2d",
        "F.3d",
        "F.4th",
        "F. Supp.",
        "F. Supp. 2d",
        "F. Supp. 3d",
    ],
}

# Case history signals that indicate different court proceedings
CASE_HISTORY_SIGNALS = [
    r"\baff[']?d\b",
    r"\baffirmed\b",
    r"\brev[']?d\b",
    r"\breversed\b",
    r"\bvacated\b",
    r"\bremanded\b",
    r"\bmodified\b",
    r"\boverruled\b",
    r"\bcert\.\s*denied\b",
    r"\bcert\.\s*granted\b",
    r"\bappeal\s+from\b",
    r"\bon\s+appeal\b",
]


def _force_release_memory() -> None:
    """Force glibc to return freed pages to the OS via malloc_trim."""
    import gc
    gc.collect()
    try:
        import ctypes
        libc = ctypes.CDLL("libc.so.6")
        libc.malloc_trim(0)
    except Exception:
        pass  # noqa: BLE001


def _get_citation_state(citation_text: str) -> str:
    """Determine which state/jurisdiction a citation belongs to."""
    if not citation_text:
        return "unknown"
    cit_upper = citation_text.upper()
    for state, reporters in STATE_REPORTERS.items():
        for reporter in reporters:
            if reporter.upper() in cit_upper:
                return state
    return "unknown"


def _citations_compatible_for_parallel(cit1: str, cit2: str) -> bool:
    """Check if two citations could be parallel (same jurisdiction)."""
    state1 = _get_citation_state(cit1)
    state2 = _get_citation_state(cit2)
    if state1 == "unknown" or state2 == "unknown":
        return True
    return state1 == state2


def _has_case_history_signal_between(text: str, pos1: int, pos2: int) -> bool:
    """Check if there's a case history signal between two positions in text."""
    if not text or pos1 < 0 or pos2 < 0:
        return False
    start = min(pos1, pos2)
    end = max(pos1, pos2)
    between_text = text[start:end].lower()
    if not between_text:
        return False
    if len(between_text) > 500:
        return False
    between_text = between_text.replace("\u2019", "'").replace("\u2018", "'").replace("\u02bc", "'")  # normalize to ASCII apostrophe
    for pattern in CASE_HISTORY_SIGNALS:
        if re.search(pattern, between_text, re.IGNORECASE):
            return True
    return False


def _extract_reporter_type_simple(citation_text: str) -> str:
    """Extract simplified reporter type from citation text for parallel matching."""
    if not citation_text:
        return "unknown"
    normalized = citation_text.lower()
    if any(t in normalized for t in ("wn. app", "wash. app", "wn app", "wash app")):
        return "wash_app"
    if any(t in normalized for t in ("wn.2d", "wn. 2d", "wash.2d", "wash. 2d")):
        return "wash2d"
    if "p.3d" in normalized or "p3d" in normalized or "p. 3d" in normalized:
        return "p3d"
    if "p.2d" in normalized or "p2d" in normalized or "p. 2d" in normalized:
        return "p2d"
    if " p. " in normalized or " p " in normalized or normalized.endswith(" p."):
        return "p"
    if "u.s." in normalized:
        return "us"
    if "s. ct." in normalized or "s.ct." in normalized:
        return "sct"
    if "l. ed." in normalized or "l.ed." in normalized:
        return "led"
    if "f.3d" in normalized or "f3d" in normalized:
        return "f3d"
    if "f.2d" in normalized or "f2d" in normalized:
        return "f2d"
    if "a.2d" in normalized or "a2d" in normalized:
        return "a2d"
    if "a.3d" in normalized or "a3d" in normalized:
        return "a3d"
    if "n.e." in normalized or "n.e.2d" in normalized:
        return "ne"
    if "n.w." in normalized or "n.w.2d" in normalized:
        return "nw"
    if "s.e." in normalized or "s.e.2d" in normalized:
        return "se"
    if "s.w." in normalized or "s.w.2d" in normalized:
        return "sw"
    return "unknown"


def _are_parallel_reporter_types(cit1: str, cit2: str) -> bool:
    """Check if two citations have compatible parallel reporter types."""
    type1 = _extract_reporter_type_simple(cit1)
    type2 = _extract_reporter_type_simple(cit2)
    if type1 == "unknown" or type2 == "unknown":
        return False
    if type1 == type2:
        return False
    parallel_pairs = {
        frozenset({"wash2d", "p3d"}),
        frozenset({"wash2d", "p2d"}),
        frozenset({"wash2d", "p"}),
        frozenset({"wash_app", "p3d"}),
        frozenset({"wash_app", "p2d"}),
        frozenset({"wash_app", "p"}),
        frozenset({"us", "sct"}),
        frozenset({"us", "led"}),
        frozenset({"sct", "led"}),
        frozenset({"f3d", "us"}),
        frozenset({"f2d", "us"}),
    }
    return frozenset({type1, type2}) in parallel_pairs
