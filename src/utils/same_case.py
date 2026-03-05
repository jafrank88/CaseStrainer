"""Shared same-case check logic.

Canonical implementation used by:
- clustering/detection.py (_same_case_check)
- unified_citation_processor_v2.py (_are_likely_parallel_citations, ensure_bidirectional_parallels, propagate_canonical_to_cluster)
- rq_worker.py (WL-DEDUP guard)

All same-case decisions MUST go through these functions to prevent logic drift.
"""

import re
from typing import Optional

# Stop words removed before fuzzy word overlap comparison
_LEGAL_STOP_WORDS = frozenset({
    "the", "of", "in", "re", "a", "an", "no", "v", "v.",
    "inc", "inc.", "llc", "co", "co.", "corp", "corp.",
    "et", "al", "ltd", "ltd.", "llp", "lp",  # LP = Limited Partnership suffix
})


def has_case_name(ecn: Optional[str]) -> bool:
    """Return True if *ecn* is a meaningful extracted case name."""
    return bool(ecn) and ecn != "N/A" and len(ecn) > 3


def _plaintiff_last_word(ecn: str) -> str:
    """Extract the last word of the plaintiff portion of a 'v.' name."""
    parts = re.split(r"\s+v\.\s+", ecn.lower(), maxsplit=1)
    return parts[0].strip().split()[-1] if parts[0].strip() else ""


def _defendant_last_word(ecn: str) -> str:
    """Extract the last meaningful word of the defendant portion of a 'v.' name."""
    parts = re.split(r"\s+v\.\s+", ecn.lower(), maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        return ""
    # Strip trailing punctuation/abbreviations (Inc., Co., etc.) for comparison
    right = re.sub(r"[.,]+$", "", parts[1].strip())
    tokens = right.split()
    return tokens[-1] if tokens else ""


# Plaintiff names that are generic (many different cases share them) - must also match defendant
_GENERIC_PLAINTIFFS = frozenset({"state", "states", "united", "people", "in", "re", "matter"})


def _fuzzy_word_overlap(name_a: str, name_b: str) -> float:
    """Return word-overlap ratio after removing stop words and punctuation."""
    wa = {w for w in re.sub(r"[^\w\s]", " ", name_a.lower()).split()
          if w not in _LEGAL_STOP_WORDS and len(w) > 1}
    wb = {w for w in re.sub(r"[^\w\s]", " ", name_b.lower()).split()
          if w not in _LEGAL_STOP_WORDS and len(w) > 1}
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / min(len(wa), len(wb))


def names_are_same_case(name_a: Optional[str], name_b: Optional[str]) -> bool:
    """Determine whether two extracted case names refer to the same case.

    Rules
    -----
    1. Both have 'v.' -> compare plaintiff last word (must match).
    2. Both have names but at least one lacks 'v.' -> fuzzy word overlap >= 0.5.
    3. One has a name, the other doesn't -> **False** (don't merge unknown with known).
    4. Neither has a name -> **True** (allow proximity grouping as fallback).

    Parameters
    ----------
    name_a, name_b : str | None
        Raw or cleaned extracted_case_name values.  ``None``, ``""``, and
        ``"N/A"`` are all treated as "no name".
    """
    ecn_a = (name_a or "").strip()
    ecn_b = (name_b or "").strip()
    has_a = has_case_name(ecn_a)
    has_b = has_case_name(ecn_b)

    # Neither has a name -> allow proximity grouping
    if not has_a and not has_b:
        return True

    # One has a name, the other doesn't -> don't merge
    if has_a != has_b:
        return False

    # Both have names - compare using 'v.' if present
    has_v_a = " v. " in ecn_a
    has_v_b = " v. " in ecn_b

    if has_v_a and has_v_b:
        pl_a = _plaintiff_last_word(ecn_a)
        pl_b = _plaintiff_last_word(ecn_b)
        if pl_a != pl_b:
            # Plaintiff last words differ (e.g. "Pope Res." vs "Pope Res., LP")
            # Use fuzzy overlap on PLAINTIFF portion only to avoid merging different cases
            # that share defendant (e.g. Aristy-Farer v. State vs NYCLU v. State)
            parts_a = parts_b = []
            if " v. " in ecn_a:
                parts_a = ecn_a.split(" v. ", 1)[0].strip().split()
            if " v. " in ecn_b:
                parts_b = ecn_b.split(" v. ", 1)[0].strip().split()
            plaintiff_overlap = _fuzzy_word_overlap(
                " ".join(parts_a), " ".join(parts_b)
            )
            if plaintiff_overlap >= 0.5:
                return True
            return _fuzzy_word_overlap(ecn_a, ecn_b) >= 0.7
        # Plaintiff last words match
        # When plaintiff is generic (e.g. "State", "United States"), many cases share it —
        # require defendant to match so we don't merge State v. Kier with State v. Stalker
        if pl_a in _GENERIC_PLAINTIFFS or pl_b in _GENERIC_PLAINTIFFS:
            dl_a = _defendant_last_word(ecn_a)
            dl_b = _defendant_last_word(ecn_b)
            if dl_a and dl_b and dl_a != dl_b:
                def_a = ecn_a.split(" v. ", 1)[1].strip() if " v. " in ecn_a else ""
                def_b = ecn_b.split(" v. ", 1)[1].strip() if " v. " in ecn_b else ""
                if _fuzzy_word_overlap(def_a, def_b) < 0.5:
                    return False
        return True

    # Both have names but at least one lacks 'v.' - fuzzy word overlap
    return _fuzzy_word_overlap(ecn_a, ecn_b) >= 0.5
