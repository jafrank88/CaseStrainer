"""
Shared cluster display helpers for backend response preparation.
Used by rq_worker (async) so display logic lives in one place and can be reused.
"""

import re
from urllib.parse import quote_plus
from typing import Any, Dict, List, Optional

from src.utils.text_normalizer import normalize_case_name
from src.utils.verification_display_utils import (
    is_effectively_verified_citation,
)
from src.utils.case_name_cleaner import clean_extracted_case_name
from src.utils.extraction_cleaner import normalize_to_ascii_display
from src.extraction.validation import is_valid_case_name
from src.utils.strict_context_isolator import is_citation_fragment_not_case_name
from src.utils.same_case import names_are_same_case

# Signal phrases to strip from case names (shared with rq_worker display processing)
_SIGNAL_PHRASES = [
    "see also",
    "but see",
    "see",
    "but",
    "also",
    r"^But\s+see\s+",
    r"^Accord\s+",
    r"^Compare\s+",
    r"^Cf\.\s+",  # Require period so "CFPB" is not stripped to "PB"
    r"^E\.?g\.?\s*,?\s*",
    r"^I\.?e\.?\s*,?\s*",
]
_SIGNAL_PHRASES_RE = [re.compile(p, re.IGNORECASE) for p in _SIGNAL_PHRASES]


_TRUNCATED_PARTY_PREFIXES = ("co", "co.", "inc", "inc.", "llc", "ltd", "ltd.", "corp", "corp.", "corporation")


def _is_bad_submitted_name(name: str) -> bool:
    """Reject names that are not suitable for display as submitted/extracted case names.
    Catches fragments, reporter text, court names, and other non-case-name strings."""
    if not name or not isinstance(name, str):
        return True
    s = name.strip()
    if not s or s == "N/A":
        return True
    # Too short to be meaningful
    if len(s) < 5:
        return True
    # Pure citation text (e.g. "159 Wn.2d 700", "726 N.W.2d 852", "45 M.J. 491")
    if re.match(
        r"^\d+\s+(?:"
        r"U\.S\.|S\.\s*Ct\.|L\.\s*Ed"
        r"|F\.(?:\d*d|\d*th|[\s]*Supp|[\s]*App|[\s]*R\.D\.|[\s]*Cas\.)"
        r"|Fed\.\s*(?:Cl\.|App|Appx?\.)"
        r"|Ct\.\s*Cl\.|Cl\.\s*Ct\."
        r"|B\.R\.|T\.C\.|M\.J\.|F\.R\.D\."
        r"|Wn\.|Wash\.|P\.(?:\d*d|[\s]*\d)"
        r"|A\.(?:\d*d|[\s]*\d)|N\.Y\."
        r"|N\.E\.|N\.W\.|S\.E\.|S\.W\.|So\."
        r"|Cal\.|Or\.|Ill\.|Tex\.|Fla\.|Va\."
        r"|Ohio|Mich\.|Pa\.|Mass\."
        r")",
        s,
    ):
        return True
    # Pure numbers or reporter-like strings
    if re.match(r"^[\d\s,.\-]+$", s):
        return True
    # Court procedural text
    if re.match(r"^(?:Supreme Court|Court of Appeals|Superior Court|District Court|Circuit Court)", s, re.IGNORECASE):
        return True
    # Opinion/judge contamination
    bad_phrases = ("opinion of the court", "j., dissenting", "j., concurring", "c.j.,", "per curiam")
    if any(b in s.lower() for b in bad_phrases):
        return True
    # Sentence-like text contamination: if text before "v." is too long (>80 chars),
    # it's likely document narrative captured as a case name, not an actual party name.
    # E.g. "All evidence must be viewed in the light most favorable to the nonmoving party. Clements v. Travel"
    v_match = re.search(r"\bv\.\s+", s)
    if v_match and v_match.start() > 80:
        return True
    # Multiple sentences (periods followed by uppercase) indicate narrative text, not a case name
    if re.search(r"\.\s+[A-Z][a-z].*\bv\.\s+", s):
        return True
    # Excessively long names (>120 chars) are almost certainly contaminated
    if len(s) > 120:
        return True
    # ---- Narrative text without case-name structure ----
    # Real case names contain "v." or "In re" / "Ex parte" / "In the Matter of" / "Estate of".
    # Also accept "Antitrust Litig." / "Antitrust Litigation" / trailing "Litig." — these are
    # "In re" style case names where eyecite stripped the leading "In re" prefix.
    _has_case_structure = bool(
        re.search(r"\bv\.\s", s)
        or re.search(r"\b(?:In\s+re|Ex\s+parte|In\s+the\s+Matter\s+of|Estate\s+of)\b", s, re.IGNORECASE)
        or re.search(r"\bAntitrust\s+Litig(?:ation)?\b|\bLitig\.?\s*$", s, re.IGNORECASE)
    )
    if not _has_case_structure:
        # Possessive + abstract noun/verb phrase (e.g. "Cockrum's failure to demonstrate")
        if re.search(r"'s\s+\w+\s+to\s+\w+", s):
            return True
        # Infinitive phrases ("failure to demonstrate", "right to appeal")
        if re.search(r"\b(?:failure|ability|right|duty|obligation|attempt|refusal|decision|order)\s+to\s+\w+", s, re.IGNORECASE):
            return True
        # Common narrative verbs/patterns that never appear in party names
        if re.search(r"\b(?:must be|should be|was not|were not|could not|did not|does not|cannot|failed to|based on|pursuant to)\b", s, re.IGNORECASE):
            return True
        # Looks like a clause: contains possessive 's followed by a common noun
        if re.search(r"'s\s+(?:failure|refusal|ability|decision|motion|claim|argument|request|right|knowledge|conduct)\b", s, re.IGNORECASE):
            return True
    # Use imported validators for deeper checks
    if is_citation_fragment_not_case_name(s):
        return True
    return False


def _repair_truncated_llc(name: Optional[str]) -> str:
    """Fix truncated LLC: ', LL' at end -> ', LLC' (e.g. CFPB v. Consumer First Legal Group, LL)."""
    if not name or not isinstance(name, str):
        return name or ""
    s = str(name).strip()
    if re.search(r",\s*LL\s*$", s):
        s = re.sub(r",\s*LL\s*$", ", LLC", s)
    return s


def _fix_all_caps_words(name: Optional[str]) -> str:
    """Title-case ALL CAPS words from CourtListener canonical names.

    E.g. "Marks v. DISTRICT COURT, ETC." → "Marks v. District Court, Etc."
    Preserves known abbreviations (LLC, II, etc.) and dotted abbrevs (D.O., U.S.).
    """
    if not name:
        return name or ""
    _KEEP = frozenset({
        'LLC', 'LLP', 'LP', 'PC', 'PA', 'USA', 'US',
        'II', 'III', 'IV', 'VI', 'VII', 'VIII', 'IX', 'XI', 'XII',
    })
    words = name.split()
    result = []
    for w in words:
        core = re.sub(r'[,;:]+$', '', w)
        # Skip dotted abbreviations (D.O., U.S.C., L.L.C.)
        if re.search(r'\.\w', core):
            result.append(w)
            continue
        bare = core.rstrip('.')
        if bare.isupper() and len(bare) >= 2 and bare not in _KEEP:
            result.append(w[0] + w[1:].lower())
        else:
            result.append(w)
    return ' '.join(result)


def _normalize_display_name_comma_spacing(name: Optional[str]) -> str:
    """Trim space before commas so 'Door Props. , LLC' -> 'Door Props., LLC'. Applied to cluster_case_name and display names."""
    if not name:
        return ""
    s = str(name).strip()
    s = _repair_truncated_llc(s)
    s = re.sub(r"\s+,", ",", s)
    s = re.sub(r"\.\s+,", "., ", s)
    return re.sub(r"\s+", " ", s).strip()


def strip_signal_phrases(name: Optional[str]) -> Optional[str]:
    """Remove leading signal phrases from a case name."""
    if not name or name == "N/A":
        return name
    for pat in _SIGNAL_PHRASES_RE:
        name = pat.sub("", name).strip()
    return name


def _looks_truncated_extracted_name(name: Optional[str]) -> bool:
    """
    Detect extracted names that likely lost the plaintiff side and start with
    a corporate suffix token (e.g. "Inc. v. Windsor") OR an abbreviated
    single-token like "Nw., Inc. v. EEOC" or "Assocs. v. Garlock".
    """
    s = str(name or "").strip()
    if not s or s.upper() == "N/A":
        return False
    parts = re.split(r"\s+v\.?\s+", s, maxsplit=1, flags=re.IGNORECASE)
    if len(parts) < 2:
        return False
    left = parts[0].strip()
    left_lower = left.lower()
    # Original: bare entity-suffix token
    if left_lower in _TRUNCATED_PARTY_PREFIXES:
        return True
    # New: first word of plaintiff is a short abbreviation ending in "."
    # (e.g. "Nw.", "Am.", "E.", "Assocs.") — clearly the tail of a longer name
    first_token = left.split()[0] if left.split() else ""
    if first_token.endswith(".") and len(first_token) <= 7:
        return True
    return False


def _recover_truncated_name_from_context(cit: Any, truncated_name: str) -> Optional[str]:
    """
    Recover plaintiff-side text for truncated extracted names using document context only.
    Example: "Inc. v. Rullan" -> "Rio Grande Community Health Center, Inc. v. Rullan"
    """
    if not _looks_truncated_extracted_name(truncated_name):
        return None

    context = get_citation_value(cit, "context", "") or ""
    if not context:
        return None

    parts = re.split(r"\s+v\.?\s+", str(truncated_name).strip(), maxsplit=1, flags=re.IGNORECASE)
    if len(parts) < 2:
        return None
    defendant = parts[1].strip()
    if not defendant:
        return None

    # Search the citation context for a fuller "X, Inc./Corp... v. Defendant" span.
    # This intentionally uses extracted context only and never canonical fields.
    # Allow defendant abbreviations: "Detrex Corp" matches "Detrex Corporation"
    defendant_escaped = re.escape(defendant)
    defendant_alt = defendant_escaped
    if defendant.endswith(" Corporation"):
        base = defendant[:-len(" Corporation")]
        defendant_alt = defendant_escaped + r"|" + re.escape(base + " Corp") + r"\.?"
    elif defendant.endswith(" Corp.") or defendant.endswith(" Corp"):
        base = defendant.rstrip(" .")[:-4]  # remove " Corp" or " Corp."
        defendant_alt = defendant_escaped + r"|" + re.escape(base + " Corporation")
    # Primary: plaintiff must end in an entity-type suffix
    pattern = (
        r"([A-Z][A-Za-z0-9&\.\',\-\s]{2,120}?"
        r"(?:,\s*)?(?:Inc|Corp|LLC|Ltd|Corporation)\.?)\s+v\.?\s+"
        r"(?:" + defendant_alt + r")(?:\b|,)"
    )
    m = re.search(pattern, context, flags=re.IGNORECASE)
    # Secondary: broader search not requiring entity suffix — catches names like
    # "W.L. Gore & Assocs., Inc.", "Northwest Airlines", "E.I. du Pont de Nemours"
    if not m:
        pattern_broad = (
            r"([A-Z][A-Za-z0-9&\.\',\-\s]{5,100})\s+v\.?\s+"
            r"(?:" + defendant_alt + r")(?:\b|,)"
        )
        m = re.search(pattern_broad, context, flags=re.IGNORECASE)
    if not m:
        return None

    recovered_plaintiff = m.group(1).strip()

    # Reject if recovered plaintiff substantially overlaps with the defendant
    # e.g. "Reese Finer Foods, Inc." appearing as plaintiff when defendant is also "Reese Finer Foods, Inc."
    def _name_tokens(s: str):
        return set(re.sub(r'[^a-z\s]', '', s.lower()).split()) - {'inc', 'corp', 'llc', 'ltd', 'co', 'v', 'the', 'a'}

    plt_tokens = _name_tokens(recovered_plaintiff)
    def_tokens = _name_tokens(defendant)
    if plt_tokens and def_tokens:
        overlap = plt_tokens & def_tokens
        if len(overlap) >= max(1, min(len(plt_tokens), len(def_tokens)) - 1):
            return None

    # Use original defendant for output (preserve "Corporation" not "Corp")
    candidate = f"{recovered_plaintiff} v. {defendant}"
    cleaned = normalize_case_name(strip_signal_phrases(candidate) or candidate)
    return cleaned if cleaned and not _looks_truncated_extracted_name(cleaned) else None


def get_cluster_citations(cluster: Dict[str, Any]) -> List[Any]:
    """Get citations from cluster, checking both 'citations' and 'citation_objects'."""
    return cluster.get("citations", []) or cluster.get("citation_objects", [])


def _get_best_citation_text_for_cluster(cluster: Dict[str, Any]) -> Optional[str]:
    """
    Get the fullest citation text for search/display. Prefers cluster_members when
    citations have truncated text (e.g. "31 Wn. App. 2" vs "31 Wn. App. 2d 100, 110").
    """
    all_texts: List[str] = []
    for c in get_cluster_citations(cluster):
        ct = str(get_citation_value(c, "citation", "") or get_citation_value(c, "text", "") or "").strip()
        if ct:
            all_texts.append(ct)
    for m in cluster.get("cluster_members", []) or []:
        if isinstance(m, str) and m.strip():
            all_texts.append(m.strip())
        elif isinstance(m, dict):
            ct = str(m.get("citation") or m.get("text") or "").strip()
            if ct:
                all_texts.append(ct)
    if not all_texts:
        return None
    try:
        from src.utils.response_enrichment import extract_display_base_citation
    except ImportError:
        return max(all_texts, key=len)
    best = None
    best_len = -1
    for t in all_texts:
        base = extract_display_base_citation(t)
        if base and len(t) > best_len:
            best = t
            best_len = len(t)
    return best if best else max(all_texts, key=len)


def get_citation_value(cit: Any, key: str, default: Any = None) -> Any:
    """Get a value from a citation, handling both dict and object formats."""
    if isinstance(cit, dict):
        return cit.get(key, default)
    return getattr(cit, key, default)


def is_citation_verified(cit: Any) -> bool:
    """Backward-compatible alias for effective verification."""
    return is_effectively_verified_citation(cit)


def get_best_extracted_name(cluster: Dict[str, Any]) -> str:
    """Get the longest/best extracted name from citations in cluster."""
    citations = get_cluster_citations(cluster)
    valid_names = []
    truncated_names = []
    for cit in citations:
        if not cit:
            continue
        name = get_citation_value(cit, "extracted_case_name", "")
        if not name or name == "N/A":
            continue
        # Apply normalization to fix soft hyphen artifacts like "Swin dle" -> "Swindle"
        cleaned = strip_signal_phrases(name) or name
        cleaned = normalize_case_name(cleaned)
        if _is_bad_submitted_name(cleaned):
            continue
        if _looks_truncated_extracted_name(cleaned):
            repaired = _recover_truncated_name_from_context(cit, cleaned)
            if repaired and not _is_bad_submitted_name(repaired):
                valid_names.append(repaired)
            else:
                truncated_names.append(cleaned)
            continue
        valid_names.append(cleaned)
    if valid_names:
        return max(valid_names, key=len)
    # Prefer extracted-only fallbacks. Do not pull from canonical display fields.
    if truncated_names:
        return max(truncated_names, key=len)
    fallback = cluster.get("extracted_case_name") or cluster.get("submitted_display_name") or "N/A"
    if fallback and fallback != "N/A":
        fallback = normalize_case_name(fallback)
        if not _is_bad_submitted_name(fallback):
            return fallback
    return "N/A"


def get_representative_verified_citation(cluster: Dict[str, Any]) -> Optional[Any]:
    """First verified citation in cluster; use for both name and date to avoid mixing cases.
    When multiple verified citations have different canonical_dates, prefer the one whose
    canonical_date matches extracted_date (fixes TransUnion: 951 F.3d 1008 (2020) vs 594 U.S. (2021))."""
    citations = get_cluster_citations(cluster)
    verified = [c for c in citations if c and is_citation_verified(c)]
    if not verified:
        pass
    else:
        # Prefer citation whose canonical_date matches extracted_date (avoids false date mismatch)
        sub_date = cluster.get("submitted_display_date") or cluster.get("extracted_date") or ""
        sub_yr = re.search(r"(19|20)\d{2}", str(sub_date)) if sub_date else None
        if sub_yr:
            sub_yr_int = int(sub_yr.group(0))
            for cit in verified:
                if not isinstance(cit, dict):
                    continue
                cd = cit.get("canonical_date")
                if cd:
                    cd_m = re.search(r"(19|20)\d{2}", str(cd))
                    if cd_m and abs(int(cd_m.group(0)) - sub_yr_int) <= 1:
                        return cit
        return verified[0]
    # Fallback for diagnostic/unverified lanes: keep candidate canonical context visible.
    for cit in citations:
        if not isinstance(cit, dict):
            continue
        status = str(cit.get("verification_status") or "").strip().lower()
        has_canonical = bool(
            str(cit.get("canonical_name") or "").strip()
            or str(cit.get("canonical_date") or "").strip()
            or str(cit.get("canonical_url") or cit.get("url") or "").strip()
        )
        md_raw = cit.get("metadata")
        md: Dict[str, Any] = dict(md_raw) if isinstance(md_raw, dict) else {}
        has_possible_evidence = bool(
            str(md.get("possible_match_name") or "").strip()
            or str(md.get("possible_match_date") or "").strip()
            or str(md.get("possible_match_url") or "").strip()
        )
        if status in {
            "year_mismatch",
            "possible_match_with_url",
            "possible_match_gate_reject",
            "possible_match_no_canonical_url",
        } and (has_canonical or has_possible_evidence):
            return cit
        if (cit.get("possible_match") is True or cit.get("possible_match") == "true") and (
            has_canonical or has_possible_evidence
        ):
            return cit
        # date_mismatch citations carry canonical_name/date/url but status is often ''
        # Return them so the Date Differences section header shows the found name, not "Not Found".
        if cit.get("date_mismatch") is True and has_canonical:
            return cit
    return None


def _is_diagnostic_candidate_citation(cit: Dict[str, Any]) -> bool:
    if not isinstance(cit, dict):
        return False
    status = str(cit.get("verification_status") or "").strip().lower()
    md_raw = cit.get("metadata")
    md: Dict[str, Any] = dict(md_raw) if isinstance(md_raw, dict) else {}
    has_candidate = bool(
        str(cit.get("canonical_name") or "").strip()
        or str(cit.get("canonical_date") or "").strip()
        or str(cit.get("canonical_url") or cit.get("url") or "").strip()
        or str(md.get("possible_match_name") or "").strip()
        or str(md.get("possible_match_date") or "").strip()
        or str(md.get("possible_match_url") or "").strip()
    )
    if not has_candidate:
        return False
    return bool(
        cit.get("date_mismatch") is True
        or cit.get("possible_match") is True
        or cit.get("possible_match") == "true"
        or status
        in {
            "year_mismatch",
            "possible_match_with_url",
            "possible_match_gate_reject",
            "possible_match_no_canonical_url",
        }
    )


def get_representative_submitted_citation(cluster: Dict[str, Any]) -> Optional[Any]:
    """
    Pick one citation as the source of submitted/extracted identity (name+date),
    so display fields stay internally consistent and don't mix years across rows.
    CRITICAL: When cluster has verified canonical_date, prefer citation whose
    extracted_date matches it (fixes Chalkley 1928 vs Spokeo 2016 year bleed).
    """
    cits = [c for c in get_cluster_citations(cluster) if isinstance(c, dict)]
    if not cits:
        return None

    canonical_date = cluster.get("canonical_date") or ""
    can_year = None
    if canonical_date:
        ym = re.search(r"(19|20)\d{2}", str(canonical_date))
        if ym:
            can_year = int(ym.group(0))

    # When verified with canonical_date, prefer citation whose extracted_date matches
    # (avoids Chalkley 143 S.E. 631 (1928) showing 2016 from nearby Spokeo)
    if can_year:
        for c in cits:
            ed = str(c.get("extracted_date") or "").strip()
            if ed and ed != "N/A":
                em = re.search(r"(19|20)\d{2}", ed)
                if em and abs(int(em.group(0)) - can_year) <= 1:
                    en = str(c.get("extracted_case_name") or "").strip()
                    if en and en != "N/A" and not _is_bad_submitted_name(en):
                        return c

    rep = get_representative_verified_citation(cluster)
    if isinstance(rep, dict):
        en = str(rep.get("extracted_case_name") or "").strip()
        ed = str(rep.get("extracted_date") or "").strip()
        if en and en != "N/A" and ed and ed != "N/A" and not _is_bad_submitted_name(en):
            return rep

    for c in cits:
        if _is_diagnostic_candidate_citation(c):
            en = str(c.get("extracted_case_name") or "").strip()
            ed = str(c.get("extracted_date") or "").strip()
            if en and en != "N/A" and ed and ed != "N/A" and not _is_bad_submitted_name(en):
                return c

    canonical_name = str(cluster.get("canonical_name") or cluster.get("cluster_case_name") or "").strip()

    best = None
    best_score = -1
    for c in cits:
        en = str(c.get("extracted_case_name") or "").strip()
        ed = str(c.get("extracted_date") or "").strip()
        if not en or en == "N/A" or _is_bad_submitted_name(en):
            continue
        score = len(en) + (1000 if (ed and ed != "N/A") else 0)
        if canonical_name and names_are_same_case(en, canonical_name):
            score += 5000
        if score > best_score:
            best = c
            best_score = score
    return best


def _context_year_for_display(cit: Dict[str, Any]) -> Optional[str]:
    """
    Derive a document-year from citation context when extracted_date appears stale.
    Prefer the parenthetical year that immediately follows the citation text in the
    context, not the last one (which can be from a neighboring TOA entry).
    Exclude document header years (e.g. "Argued March 30, 2021-Decided June 25").
    """
    if not isinstance(cit, dict):
        return None
    context = str(cit.get("context") or "").strip()
    if not context:
        return None

    # Locate citation text in context to find the parenthetical year right after it.
    cite_text = str(cit.get("citation") or "").strip()
    search_start = 0
    if cite_text and len(cite_text) >= 6:
        # Use the reporter fragment (more stable than full text which may be truncated)
        reporter_m = re.search(r"\d+\s+\w", cite_text)
        lookup = cite_text[reporter_m.start():] if reporter_m else cite_text
        pos = context.find(lookup[:30])
        if pos >= 0:
            search_start = pos + len(lookup[:30])

    after_cite = context[search_start:]

    # Find parenthetical year tokens after the citation: "(1925)", "(8th Cir.1925)" etc.
    paren_match = re.search(r"\([^()]*?((?:17|18|19|20)\d{2})[^()]*?\)", after_cite)
    if paren_match:
        return paren_match.group(1)

    # Fallback: first bare year after citation in context.
    context_no_headers = re.sub(
        r"(?:Argued|Decided|Filed)\s+[^.]*?(?:17|18|19|20)\d{2}[^.]{0,60}",
        "",
        after_cite,
        flags=re.IGNORECASE,
    )
    context_no_headers = re.sub(
        r"(?:17|18|19|20)\d{2}\s*[-–]\s*(?:Decided|Argued|Filed)[^.]{0,40}",
        "",
        context_no_headers,
        flags=re.IGNORECASE,
    )
    m = re.search(r"\b((?:17|18|19|20)\d{2})\b", context_no_headers)
    if m:
        return m.group(1)
    return None


def get_verifying_name(cluster: Dict[str, Any]) -> str:
    """Get canonical/verifying name from canonical fields only (no extracted fallback)."""
    rep = get_representative_verified_citation(cluster)
    if rep:
        name = get_citation_value(rep, "canonical_name")
        if (not name or name == "N/A") and isinstance(rep, dict) and isinstance(rep.get("metadata"), dict):
            name = rep["metadata"].get("possible_match_name")
        if name and name != "N/A":
            # Apply normalization to fix soft hyphen artifacts like "Swin dle" -> "Swindle"
            cleaned = strip_signal_phrases(name) or name
            return normalize_case_name(cleaned)
    # FIX 2026-02-24: Check for true_by_parallel citations which have propagated canonical_name
    for cit in get_cluster_citations(cluster):
        if not cit or not isinstance(cit, dict):
            continue
        # Check top-level true_by_parallel (dict conversion puts it here, not in metadata)
        if cit.get("true_by_parallel"):
            name = cit.get("canonical_name")
            if name and name != "N/A":
                cleaned = strip_signal_phrases(name) or name
                return normalize_case_name(cleaned)
    return "Not Found"


def get_verifying_date(cluster: Dict[str, Any]) -> str:
    """Get canonical/verifying date from canonical fields only (no extracted fallback).
    Returns year-only (e.g. '1982') when canonical_date is a full date (e.g. '1982-06-15')
    so display matches submitted_display_date format and avoids false 'Different date' when years match."""
    from src.utils.date_utils import extract_year_value

    def _normalize_for_display(date_val: Optional[str]) -> Optional[str]:
        if not date_val or date_val == "N/A":
            return None
        # Full date (YYYY-MM-DD or ISO) -> use year for display consistency with submitted_display_date
        yr = extract_year_value(date_val)
        return yr if yr else date_val

    rep = get_representative_verified_citation(cluster)
    if rep:
        date = get_citation_value(rep, "canonical_date")
        if (not date or date == "N/A") and isinstance(rep, dict) and isinstance(rep.get("metadata"), dict):
            date = rep["metadata"].get("possible_match_date")
        if date and date != "N/A":
            return _normalize_for_display(date) or date
    # FIX 2026-02-24: Check for true_by_parallel citations which have propagated canonical_date
    for cit in get_cluster_citations(cluster):
        if not cit or not isinstance(cit, dict):
            continue
        # Check top-level true_by_parallel (dict conversion puts it here, not in metadata)
        if cit.get("true_by_parallel"):
            date = cit.get("canonical_date")
            if date and date != "N/A":
                return _normalize_for_display(date) or date
    return "Not Found"


def get_submitted_date(cluster: Dict[str, Any]) -> str:
    """Get extracted date from document."""
    citations = get_cluster_citations(cluster)
    for cit in citations:
        if not cit:
            continue
        date = get_citation_value(cit, "extracted_date")
        if date and date != "N/A":
            return date
    return cluster.get("extracted_date") or "N/A"


def _is_google_search_url(url: Optional[str]) -> bool:
    """True if url is a Google search URL; such URLs must never be used as canonical case URL."""
    if not url or not str(url).strip():
        return False
    u = str(url).strip()
    return u.startswith("https://www.google.com/search") or u.startswith("http://www.google.com/search")


def get_canonical_url(cluster: Dict[str, Any]) -> Optional[str]:
    """Get canonical URL from verified citation, possible-match, or cluster_members. Never returns a Google search URL."""
    def _real(url: Optional[str]) -> Optional[str]:
        if not url or not str(url).strip():
            return None
        s = str(url).strip()
        return s if not _is_google_search_url(s) else None

    # Cluster-level first (may exist when citations don't have it)
    cluster_level_url = cluster.get("canonical_url") or cluster.get("display_canonical_url")
    u = _real(cluster_level_url)
    if u:
        return u
    citations = get_cluster_citations(cluster)
    # Verified citations
    for cit in citations:
        if not cit:
            continue
        if is_citation_verified(cit):
            url = get_citation_value(cit, "canonical_url") or get_citation_value(cit, "url")
            u = _real(url)
            if u:
                return u
    # true_by_parallel citations
    for cit in citations:
        if not cit or not isinstance(cit, dict):
            continue
        if cit.get("true_by_parallel"):
            url = cit.get("url") or cit.get("canonical_url")
            u = _real(url)
            if u:
                return u
    # All citations: canonical_url, url, or possible_match_url (so possible-match case URL is never overwritten by Google)
    for cit in citations:
        if not cit or not isinstance(cit, dict):
            continue
        url = cit.get("canonical_url") or cit.get("url")
        if not url and isinstance(cit.get("metadata"), dict):
            url = cit["metadata"].get("possible_match_url")
        u = _real(url)
        if u:
            return u
    # Representative diagnostic fallback
    rep = get_representative_verified_citation(cluster)
    if isinstance(rep, dict):
        url = rep.get("canonical_url") or rep.get("url")
        if not url and isinstance(rep.get("metadata"), dict):
            url = rep["metadata"].get("possible_match_url")
        u = _real(url)
        if u:
            return u
    # cluster_members (e.g. known_federal path)
    for m in cluster.get("cluster_members", []) or []:
        if isinstance(m, dict):
            u = _real(m.get("canonical_url") or m.get("url"))
            if u:
                return u
    return None


# Trailing pinpoint pattern: ", 110" or ", 110-11" or ", 110 n.5" at end of citation.
# Used to strip pin cites from search queries so Google returns more results.
_PIN_CITE_TRAILING_RE = re.compile(
    r",\s*\d{1,4}(?:-\d{1,4})?(?:\s+n\.?\s*\d+)?\s*$"
)


def _strip_pin_cites_for_search(citation_text: str) -> str:
    """Remove trailing pin cites (e.g. ', 110', ', 110-12') from citation text for search queries."""
    if not citation_text or not isinstance(citation_text, str):
        return citation_text or ""
    s = str(citation_text).strip()
    while True:
        m = _PIN_CITE_TRAILING_RE.search(s)
        if not m:
            break
        s = s[: m.start()].rstrip()
    return s


def _google_search_url_for_cluster(cluster: Dict[str, Any]) -> Optional[str]:
    """Build a basic Google search URL from extracted case name + year, or citation fallback."""
    submitted_name = str(cluster.get("submitted_display_name") or get_best_extracted_name(cluster) or "").strip()
    submitted_year = str(cluster.get("submitted_display_date") or get_submitted_date(cluster) or "").strip()
    query = ""
    if submitted_name and submitted_name != "N/A":
        query = submitted_name
    else:
        # If name is unavailable, build search using best (fullest) citation.
        # Prefer cluster_members when citations are truncated (e.g. "31 Wn. App. 2" vs "31 Wn. App. 2d 100").
        ct = _get_best_citation_text_for_cluster(cluster)
        if ct:
            query = _strip_pin_cites_for_search(ct)
    if not query:
        return None
    if submitted_year and submitted_year not in {"N/A", "Unknown Year", "unknown"}:
        query = f"{query} {submitted_year}"
    return f"https://www.google.com/search?q={quote_plus(query)}"


def apply_display_fields_to_cluster(cluster: Dict[str, Any]) -> None:
    """Set verifying_display_name, verifying_display_date, submitted_display_name, submitted_display_date, display_canonical_url on cluster."""
    cluster["verifying_display_name"] = _normalize_display_name_comma_spacing(
        normalize_to_ascii_display(get_verifying_name(cluster) or "")
    )
    cluster["verifying_display_date"] = get_verifying_date(cluster)
    rep_sub = get_representative_submitted_citation(cluster)
    if isinstance(rep_sub, dict):
        rep_name = str(rep_sub.get("extracted_case_name") or "").strip()
        rep_date = str(rep_sub.get("extracted_date") or "").strip()
        # Only backfill from document-derived context when extracted_date is missing/unknown.
        # Do NOT backfill submitted/document date from canonical date; that contaminates the extracted field.
        if not rep_date or rep_date in {"N/A", "Unknown Year", "unknown"}:
            context_year = _context_year_for_display(rep_sub)
            if context_year:
                rep_date = context_year
        if rep_name and rep_name != "N/A" and not _is_bad_submitted_name(rep_name):
            cluster["submitted_display_name"] = _normalize_display_name_comma_spacing(normalize_case_name(rep_name))
        else:
            cluster["submitted_display_name"] = get_best_extracted_name(cluster)
        if rep_date and rep_date != "N/A":
            cluster["submitted_display_date"] = rep_date
        else:
            cluster["submitted_display_date"] = get_submitted_date(cluster)
    else:
        cluster["submitted_display_name"] = get_best_extracted_name(cluster)
        cluster["submitted_display_date"] = get_submitted_date(cluster)

    # Final guard: submitted/document fields must never be sourced from canonical.
    if not cluster.get("submitted_display_name"):
        cluster["submitted_display_name"] = "N/A"
    if not cluster.get("submitted_display_date"):
        cluster["submitted_display_date"] = "N/A"
    cluster["submitted_display_name"] = _normalize_display_name_comma_spacing(
        str(cluster.get("submitted_display_name") or "")
    )
    # Prefer longer cluster_case_name when submitted_display_name is a truncated version
    _sdn = (cluster.get("submitted_display_name") or "").strip()
    _ccn = (cluster.get("cluster_case_name") or "").strip()
    if _sdn and _ccn and len(_ccn) > len(_sdn) and not _is_bad_submitted_name(_ccn):
        # Check same case by first party match
        _sdn_fp = re.split(r"\s+v\.?\s+", _sdn, maxsplit=1, flags=re.IGNORECASE)
        _ccn_fp = re.split(r"\s+v\.?\s+", _ccn, maxsplit=1, flags=re.IGNORECASE)
        if (len(_sdn_fp) >= 2 and len(_ccn_fp) >= 2
                and _sdn_fp[0].strip().lower().rstrip(".") == _ccn_fp[0].strip().lower().rstrip(".")):
            cluster["submitted_display_name"] = _normalize_display_name_comma_spacing(
                normalize_case_name(_ccn)
            )

    # --- Additional display name upgrades ---
    _sdn = (cluster.get("submitted_display_name") or "").strip()
    _ccn = (cluster.get("cluster_case_name") or "").strip()
    _can = (cluster.get("canonical_name") or "").strip()
    _best_alt = ""
    # Pick best available alternative: canonical_name > cluster_case_name
    for _alt in [_can, _ccn]:
        if _alt and _alt != "N/A" and not _is_bad_submitted_name(_alt) and " v. " in _alt:
            _best_alt = _alt
            break

    if _sdn and _best_alt and _sdn != _best_alt:
        _needs_upgrade = False
        # (a) Fragment: submitted starts with corporate suffix before "v."
        if _looks_truncated_extracted_name(_sdn):
            _needs_upgrade = True
        # (b) Contaminated: submitted contains reporter abbreviations with numbers (citation text leaked in)
        if not _needs_upgrade and re.search(
            r"\d+\s+(?:Wn\.|Wash\.|P\.\d|N\.W\.\d|A\.\d|S\.W\.\d|S\.E\.\d|So\.\d|N\.E\.\d|F\.\d|U\.S\.|S\.\s*Ct\.|L\.\s*Ed|Conn\.\s*App\.|Conn\.\s*Supp|Neb\.|Or\.)",
            _sdn, re.IGNORECASE
        ):
            _needs_upgrade = True
        # (c) No "v." in submitted but cluster_case_name/canonical has full "v." name
        #     and submitted is a substring or an abbreviation variant
        #     (e.g. "Chong Yim" in "Chong Yim v. City of Seattle",
        #      or "Edwards Lifesciences Corporation" vs "Edwards Lifesciences Corp.")
        if not _needs_upgrade and " v. " not in _sdn and " v. " in _best_alt:
            _sdn_norm = _sdn.lower().rstrip(".")
            _alt_norm = _best_alt.lower()
            if _sdn_norm in _alt_norm:
                _needs_upgrade = True
            elif not _needs_upgrade:
                _sdn_words = set(re.sub(r"[.,;:']", "", _sdn_norm).split())
                _alt_right = _alt_norm.split(" v. ", 1)[-1] if " v. " in _alt_norm else ""
                _alt_right_words = set(re.sub(r"[.,;:']", "", _alt_right).split())
                if _sdn_words and _alt_right_words and len(_sdn_words & _alt_right_words) >= len(_sdn_words) * 0.6:
                    _needs_upgrade = True
        # (d) Context prefix contamination: submitted has extra words before the real case name
        #     e.g. "City of Seattle Ford Motor Co. v. City of Seattle" where real name is "Ford Motor Co. v. City of Seattle"
        if not _needs_upgrade and " v. " in _sdn and " v. " in _best_alt:
            if _best_alt.lower() in _sdn.lower() and len(_sdn) > len(_best_alt) + 3:
                _needs_upgrade = True
        # (e) Double "v." in submitted (e.g. "Rsrv. v. Johnson" normalized to "Rsr v. v. Johnson")
        if not _needs_upgrade and re.search(r"\bv\.\s+v\.\s", _sdn):
            _needs_upgrade = True
        # (f) Very short left party before "v." (< 5 meaningful chars, e.g. "Soc'")
        if not _needs_upgrade and " v. " in _sdn:
            _left_party = _sdn.split(" v. ", 1)[0].strip().rstrip(".'\"")
            if len(_left_party) < 5 and len(_best_alt) > len(_sdn) + 5:
                _needs_upgrade = True
        # (g) General: names_are_same_case matches and names differ meaningfully
        #     Catches context prefix (#4: sdn is LONGER but contaminated) and
        #     garbled extraction (#20: sdn has wrong words but same structure)
        if not _needs_upgrade and abs(len(_best_alt) - len(_sdn)) > 3:
            if names_are_same_case(_sdn, _best_alt):
                _needs_upgrade = True
        if _needs_upgrade:
            cluster["submitted_display_name"] = _normalize_display_name_comma_spacing(
                normalize_case_name(_best_alt)
            )

    # Fallback: if submitted_display_name is still empty, use cluster_case_name or canonical_name
    if not cluster.get("submitted_display_name") or cluster["submitted_display_name"] in ("", "N/A"):
        fallback_name = (
            (cluster.get("cluster_case_name") or "").strip()
            or (cluster.get("canonical_name") or "").strip()
            or (cluster.get("extracted_case_name") or "").strip()
        )
        if fallback_name and fallback_name != "N/A":
            cluster["submitted_display_name"] = _normalize_display_name_comma_spacing(
                normalize_case_name(fallback_name)
            )
    if cluster.get("cluster_case_name"):
        cluster["cluster_case_name"] = _normalize_display_name_comma_spacing(
            str(cluster.get("cluster_case_name") or "")
        )
    # Keep verifying_display_name as the CourtListener / canonical caption when it differs
    # from the document string; submitted_display_name carries the extracted form for comparison.
    cluster["display_canonical_url"] = get_canonical_url(cluster)
    # For non-canonical rows, provide a user-clickable web search fallback.
    if not cluster.get("display_canonical_url"):
        search_url = _google_search_url_for_cluster(cluster)
        if search_url:
            cluster["display_canonical_url"] = search_url
            # USER RULE: Google search URL = unverified. Clear true_by_parallel on all citations.
            for cit in get_cluster_citations(cluster):
                if isinstance(cit, dict) and cit.get("true_by_parallel"):
                    cit["true_by_parallel"] = False
            # UI helper label for explicit "Search Google for:" link text.
            search_label = str(cluster.get("submitted_display_name") or "").strip()
            if not search_label or search_label == "N/A":
                ct = _get_best_citation_text_for_cluster(cluster)
                if ct:
                    search_label = _strip_pin_cites_for_search(ct)
            if cluster.get("submitted_display_date") and str(cluster.get("submitted_display_date")) not in {"N/A", "Unknown Year", "unknown"}:
                if search_label and not search_label.endswith(str(cluster.get("submitted_display_date"))):
                    search_label = f"{search_label} {cluster.get('submitted_display_date')}"
            # Normalize spacing: "Door Props. , LLC" -> "Door Props., LLC", trim spaces around punctuation
            if search_label:
                search_label = re.sub(r"\s+,", ",", search_label)
                search_label = re.sub(r"\.\s+,", "., ", search_label)
                search_label = re.sub(r"\s+", " ", search_label).strip()
            cluster["search_fallback_label"] = normalize_to_ascii_display(search_label or "case")
            if str(cluster.get("verifying_display_name") or "").strip() in {"", "N/A", "Not Found"}:
                cluster["verifying_display_name"] = normalize_to_ascii_display(
                    str(cluster.get("submitted_display_name") or "Web search")
                )
            if str(cluster.get("verifying_display_date") or "").strip() in {"", "N/A", "Not Found"}:
                cluster["verifying_display_date"] = str(cluster.get("submitted_display_date") or "N/A")

    # Fix ALL CAPS words from CourtListener canonical names (applies to all clusters)
    for _fld in ("submitted_display_name", "cluster_case_name", "verifying_display_name"):
        _val = cluster.get(_fld)
        if _val and isinstance(_val, str):
            cluster[_fld] = _fix_all_caps_words(_val)


def cluster_has_effective_verified(cluster: Dict[str, Any]) -> bool:
    cits = get_cluster_citations(cluster)
    return any(is_effectively_verified_citation(c) for c in cits if isinstance(c, dict))


def cluster_has_diagnostic_candidate(cluster: Dict[str, Any]) -> bool:
    cits = get_cluster_citations(cluster)
    for c in cits:
        if not isinstance(c, dict):
            continue
        status = str(c.get("verification_status") or "").strip().lower()
        md_raw = c.get("metadata")
        md: Dict[str, Any] = dict(md_raw) if isinstance(md_raw, dict) else {}
        # FIX 2026-02-24: Include true_by_parallel citations as having diagnostic value
        # Check top-level true_by_parallel (dict conversion puts it here, not in metadata)
        if c.get("true_by_parallel"):
            return True
        has_candidate = bool(
            str(c.get("canonical_name") or "").strip()
            or str(c.get("canonical_date") or "").strip()
            or str(c.get("canonical_url") or c.get("url") or "").strip()
            or str(md.get("possible_match_name") or "").strip()
            or str(md.get("possible_match_date") or "").strip()
            or str(md.get("possible_match_url") or "").strip()
        )
        if not has_candidate:
            continue
        if c.get("date_mismatch") is True:
            return True
        if c.get("possible_match") is True or c.get("possible_match") == "true":
            return True
        if status in {
            "year_mismatch",
            "possible_match_with_url",
            "possible_match_gate_reject",
            "possible_match_no_canonical_url",
        }:
            return True
    return False


def finalize_cluster_display_identity(
    cluster: Dict[str, Any],
    *,
    clear_unverified_canonical: bool = True,
    clean_names: bool = True,
) -> None:
    """
    Single source of truth for display identity.
    - computes display fields
    - optionally cleans extracted names
    - enforces unverified identity guard
    """
    if not isinstance(cluster, dict):
        return
    apply_display_fields_to_cluster(cluster)

    if clean_names:
        cits = get_cluster_citations(cluster)
        for c in cits:
            if isinstance(c, dict):
                if c.get("extracted_case_name"):
                    c["extracted_case_name"] = clean_extracted_case_name(str(c.get("extracted_case_name")))
                # Normalize all display strings to ASCII
                for key in ("citation", "text", "canonical_name", "display_base_citation"):
                    if c.get(key):
                        c[key] = normalize_to_ascii_display(str(c[key]))
        if cluster.get("submitted_display_name"):
            cluster["submitted_display_name"] = clean_extracted_case_name(str(cluster.get("submitted_display_name")))
        if cluster.get("extracted_case_name"):
            cluster["extracted_case_name"] = clean_extracted_case_name(str(cluster.get("extracted_case_name")))

    if cluster_has_effective_verified(cluster):
        return
    if cluster_has_diagnostic_candidate(cluster):
        return

    # Unverified clusters should present explicit "not found" on the top line.
    cluster["verifying_display_name"] = "Not Found"
    cluster["verifying_display_date"] = "Not Found"
    if clear_unverified_canonical:
        _display_url = str(cluster.get("display_canonical_url") or "").strip()
        _keep_search_url = _display_url.startswith("https://www.google.com/search?")
        cluster["canonical_url"] = None
        if not _keep_search_url:
            cluster["display_canonical_url"] = None
        cluster["canonical_name"] = None
        cluster["canonical_date"] = None


def clear_unverified_citation_canonical_fields(cluster: Dict[str, Any]) -> None:
    """
    For non-effectively-verified clusters, clear canonical data on child citations
    that are not effectively verified. Keeps UI and sectioning semantics consistent.
    USER RULE: When cluster has only Google search URL, clear true_by_parallel from all
    citations so we never show "Verified by Parallel" for unverified clusters.
    """
    if not isinstance(cluster, dict):
        return
    # When cluster's display URL is Google search, no citation can be "Verified by Parallel"
    display_url = str(cluster.get("display_canonical_url") or cluster.get("canonical_url") or "").strip()
    if _is_google_search_url(display_url):
        for c in get_cluster_citations(cluster):
            if isinstance(c, dict) and c.get("true_by_parallel"):
                c["true_by_parallel"] = False
                if isinstance(c.get("metadata"), dict):
                    c["metadata"]["true_by_parallel"] = False
    if cluster_has_effective_verified(cluster):
        return
    if cluster_has_diagnostic_candidate(cluster):
        return
    for c in get_cluster_citations(cluster):
        if not isinstance(c, dict):
            continue
        if is_effectively_verified_citation(c):
            continue
        status = str(c.get("verification_status") or "").strip().lower()
        md_raw = c.get("metadata")
        md: Dict[str, Any] = dict(md_raw) if isinstance(md_raw, dict) else {}
        has_candidate = bool(
            str(c.get("canonical_name") or "").strip()
            or str(c.get("canonical_date") or "").strip()
            or str(c.get("canonical_url") or c.get("url") or "").strip()
            or str(md.get("possible_match_name") or "").strip()
            or str(md.get("possible_match_date") or "").strip()
            or str(md.get("possible_match_url") or "").strip()
        )
        if has_candidate and (
            c.get("date_mismatch") is True
            or c.get("possible_match") is True
            or c.get("possible_match") == "true"
            or status in {
                "year_mismatch",
                "possible_match_with_url",
                "possible_match_gate_reject",
                "possible_match_no_canonical_url",
            }
        ):
            continue
        c["verified"] = False
        c["is_verified"] = False
        c["canonical_name"] = None
        c["canonical_date"] = None
        c["canonical_url"] = None
        c["url"] = None


def finalize_cluster_for_response(
    cluster: Dict[str, Any],
    *,
    clean_names: bool = True,
    clear_unverified_canonical: bool = True,
    clear_unverified_citations: bool = True,
) -> None:
    """
    One-stop finalizer used by both sync/async response paths.
    """
    finalize_cluster_display_identity(
        cluster,
        clear_unverified_canonical=clear_unverified_canonical,
        clean_names=clean_names,
    )
    if clear_unverified_citations:
        clear_unverified_citation_canonical_fields(cluster)

    # Mismatch badges only make sense when we have an effective verified identity
    # (a real canonical URL / verified-by-parallel with a real URL).
    # If the cluster is unverified (including "Google search" fallback), suppress mismatch flags
    # so "Unverified" cases aren't double-flagged as name/date mismatches.
    try:
        if not cluster_has_effective_verified(cluster):
            cluster["has_name_mismatch"] = False
            cluster["has_date_mismatch"] = False
            cluster["mismatch_indices"] = []
            for c in get_cluster_citations(cluster):
                if isinstance(c, dict) and not is_effectively_verified_citation(c):
                    c["name_mismatch"] = False
                    c["date_mismatch"] = False
    except Exception:
        pass

    # ECN propagation: back-fill extracted_case_name on citations that still show N/A
    # when the cluster has a good submitted_display_name.  This ensures the citation-level
    # field matches what the cluster card displays, so downstream checks are consistent.
    try:
        best_name = (cluster.get("submitted_display_name") or "").strip()
        _good = bool(
            best_name and best_name != "N/A"
            and (re.search(r"\bv\.\s", best_name)
                 or re.search(r"\b(?:In\s+re|Ex\s+parte)\b", best_name, re.IGNORECASE))
        )
        if _good:
            for _c in get_cluster_citations(cluster):
                if isinstance(_c, dict):
                    _ecn = (_c.get("extracted_case_name") or "").strip()
                    if not _ecn or _ecn == "N/A":
                        _c["extracted_case_name"] = best_name
    except Exception:
        pass
