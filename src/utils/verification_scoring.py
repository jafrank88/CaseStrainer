"""
Weighted multi-factor confidence scoring for citation verification results.
Adapted from rlfordon/citation-verifier scoring logic.

Factors and default weights:
  name  0.50  - case name similarity
  court 0.20  - court identifier match
  date  0.20  - year proximity
  cite  0.10  - citation/reporter match

When a factor cannot be evaluated (data missing), its weight is
redistributed proportionally to the remaining evaluable factors.
"""
import re
from typing import Optional, Dict, Any
from difflib import SequenceMatcher

try:
    from src.utils.legal_abbreviations import expand_abbreviations as _expand
except Exception:
    _expand = None


def _word_overlap(a: str, b: str) -> float:
    wa = set(re.findall(r"[a-z]+", a.lower()))
    wb = set(re.findall(r"[a-z]+", b.lower()))
    stop = {"v", "the", "of", "and", "in", "a", "an", "re", "inc", "llc", "corp", "co", "ltd"}
    wa -= stop; wb -= stop
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / max(len(wa | wb), 1)


def _name_score(submitted: Optional[str], canonical: Optional[str]) -> Optional[float]:
    """Multi-factor name similarity: sequence + word overlap + substring."""
    if not submitted or not canonical:
        return None
    sub_raw = _expand(submitted) if _expand else submitted
    can_raw = _expand(canonical) if _expand else canonical
    sub = re.sub(r"\s+", " ", sub_raw.lower().strip())
    can = re.sub(r"\s+", " ", can_raw.lower().strip())
    if not sub or not can:
        return None
    seq = SequenceMatcher(None, sub, can).ratio()
    word = _word_overlap(sub, can)
    substr = 0.0
    s1, s2 = (sub, can) if len(sub) <= len(can) else (can, sub)
    if s1 in s2:
        substr = len(s1) / max(len(s2), 1)
    combined = 0.40 * seq + 0.40 * word + 0.20 * substr
    # Abbreviated name boost: all words of short name appear in long name
    w1 = set(sub.split()); w2 = set(can.split())
    if len(w1) <= 4 and w1.issubset(w2):
        combined = max(combined, 0.85)
    elif len(w2) <= 4 and w2.issubset(w1):
        combined = max(combined, 0.85)
    return round(combined, 4)


def _date_score(submitted_year: Optional[int], canonical_year: Optional[int]) -> Optional[float]:
    if not submitted_year or not canonical_year:
        return None
    diff = abs(submitted_year - canonical_year)
    if diff == 0:
        return 1.0
    if diff == 1:
        return 0.7
    if diff == 2:
        return 0.4
    return 0.0


def _court_score(submitted_court: Optional[str], canonical_court: Optional[str]) -> Optional[float]:
    if not submitted_court or not canonical_court:
        return None
    s = re.sub(r"[^a-z0-9]", "", submitted_court.lower())
    c = re.sub(r"[^a-z0-9]", "", canonical_court.lower())
    if not s or not c:
        return None
    if s == c:
        return 1.0
    if s in c or c in s:
        return 0.7
    return 0.0


def _cite_score(submitted_cite: Optional[str], canonical_cite: Optional[str]) -> Optional[float]:
    if not submitted_cite or not canonical_cite:
        return None
    def _core(t):
        m = re.search(r"\b(\d+)\s+([A-Za-z.\s]+?)\s+(\d+)\b", str(t or ""))
        if m:
            return m.group(1), re.sub(r"\s", "", m.group(2)).lower(), m.group(3)
        return None
    sc = _core(submitted_cite)
    cc = _core(canonical_cite)
    if not sc or not cc:
        return None
    vol_match = sc[0] == cc[0]
    rep_match = sc[1] == cc[1]
    pg_match = sc[2] == cc[2]
    if vol_match and rep_match and pg_match:
        return 1.0
    if vol_match and rep_match:
        return 0.6
    return 0.0


def compute_weighted_confidence(
    submitted_name: Optional[str] = None,
    canonical_name: Optional[str] = None,
    submitted_year: Optional[int] = None,
    canonical_year: Optional[int] = None,
    submitted_court: Optional[str] = None,
    canonical_court: Optional[str] = None,
    submitted_cite: Optional[str] = None,
    canonical_cite: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Compute weighted confidence score with weight redistribution.
    Returns dict with 'score', 'factors', and 'diagnostics'.
    """
    DEFAULT_WEIGHTS = {"name": 0.50, "court": 0.20, "date": 0.20, "cite": 0.10}

    scores = {
        "name": _name_score(submitted_name, canonical_name),
        "court": _court_score(submitted_court, canonical_court),
        "date": _date_score(submitted_year, canonical_year),
        "cite": _cite_score(submitted_cite, canonical_cite),
    }

    # Redistribute weights for None (unevaluable) factors
    active = {k: v for k, v in scores.items() if v is not None}
    if not active:
        return {"score": 0.5, "factors": scores, "diagnostics": ["No factors evaluable"]}

    active_weight_sum = sum(DEFAULT_WEIGHTS[k] for k in active)
    effective_weights = {k: DEFAULT_WEIGHTS[k] / active_weight_sum for k in active}

    total = sum(scores[k] * effective_weights[k] for k in active)
    total = round(total, 4)

    # Build diagnostics
    diagnostics = []
    name_s = scores.get("name")
    date_s = scores.get("date")
    court_s = scores.get("court")
    if name_s is not None and name_s < 0.35:
        diagnostics.append(
            f"Name mismatch: '{submitted_name}' vs '{canonical_name}' (similarity {name_s:.2f})"
        )
    elif name_s is not None and name_s < 0.65:
        diagnostics.append(
            f"Partial name match: '{submitted_name}' vs '{canonical_name}' (similarity {name_s:.2f})"
        )
    if date_s is not None and date_s == 0.0:
        diagnostics.append(
            f"Year mismatch: cited {submitted_year} vs found {canonical_year}"
        )
    if court_s is not None and court_s == 0.0:
        diagnostics.append(
            f"Court mismatch: cited '{submitted_court}' vs found '{canonical_court}'"
        )

    return {"score": total, "factors": scores, "diagnostics": diagnostics}
