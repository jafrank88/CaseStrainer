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

# Signal phrases to strip from case names (shared with rq_worker display processing)
SIGNAL_PHRASE_PATTERNS = [
    r"^See,?\s+",
    r"^See\s+also\s+",
    r"^But\s+see\s+",
    r"^Accord\s+",
    r"^Compare\s+",
    r"^Cf\.\s+",  # Require period so "CFPB" is not stripped to "PB"
    r"^E\.?g\.?\s*,?\s*",
    r"^I\.?e\.?\s*,?\s*",
]


_TRUNCATED_PARTY_PREFIXES = ("co", "co.", "inc", "inc.", "llc", "ltd", "ltd.", "corp", "corp.", "corporation")


def _repair_truncated_llc(name: Optional[str]) -> str:
    """Fix truncated LLC: ', LL' at end -> ', LLC' (e.g. CFPB v. Consumer First Legal Group, LL)."""
    if not name or not isinstance(name, str):
        return name or ""
    s = str(name).strip()
    if re.search(r",\s*LL\s*$", s):
        s = re.sub(r",\s*LL\s*$", ", LLC", s)
    return s


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
    for pattern in SIGNAL_PHRASE_PATTERNS:
        name = re.sub(pattern, "", name, flags=re.IGNORECASE).strip()
    return name


def _looks_truncated_extracted_name(name: Optional[str]) -> bool:
    """
    Detect extracted names that likely lost the plaintiff side and start with
    a corporate suffix token, e.g. "Inc. v. Windsor".
    """
    s = str(name or "").strip()
    if not s or s.upper() == "N/A":
        return False
    parts = re.split(r"\s+v\.?\s+", s, maxsplit=1, flags=re.IGNORECASE)
    if len(parts) < 2:
        return False
    left = parts[0].strip().lower()
    return left in _TRUNCATED_PARTY_PREFIXES


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
    pattern = (
        r"([A-Z][A-Za-z0-9&\.\',\-\s]{2,120}?"
        r"(?:,\s*)?(?:Inc|Corp|LLC|Ltd|Corporation)\.?)\s+v\.?\s+"
        r"(?:" + defendant_alt + r")\b"
    )
    m = re.search(pattern, context, flags=re.IGNORECASE)
    if not m:
        return None

    # Use original defendant for output (preserve "Corporation" not "Corp")
    candidate = f"{m.group(1).strip()} v. {defendant}"
    cleaned = normalize_case_name(strip_signal_phrases(candidate) or candidate)
    return cleaned if cleaned and not _looks_truncated_extracted_name(cleaned) else None


def get_cluster_citations(cluster: Dict[str, Any]) -> List[Any]:
    """Get citations from cluster, checking both 'citations' and 'citation_objects'."""
    return cluster.get("citations", []) or cluster.get("citation_objects", [])


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
        if _looks_truncated_extracted_name(cleaned):
            repaired = _recover_truncated_name_from_context(cit, cleaned)
            if repaired:
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
    return normalize_case_name(fallback) if fallback and fallback != "N/A" else fallback


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
                    if en and en != "N/A":
                        return c

    rep = get_representative_verified_citation(cluster)
    if isinstance(rep, dict):
        en = str(rep.get("extracted_case_name") or "").strip()
        ed = str(rep.get("extracted_date") or "").strip()
        if en and en != "N/A" and ed and ed != "N/A":
            return rep

    for c in cits:
        if _is_diagnostic_candidate_citation(c):
            en = str(c.get("extracted_case_name") or "").strip()
            ed = str(c.get("extracted_date") or "").strip()
            if en and en != "N/A" and ed and ed != "N/A":
                return c

    best = None
    best_score = -1
    for c in cits:
        en = str(c.get("extracted_case_name") or "").strip()
        ed = str(c.get("extracted_date") or "").strip()
        if not en or en == "N/A":
            continue
        score = len(en) + (1000 if (ed and ed != "N/A") else 0)
        if score > best_score:
            best = c
            best_score = score
    return best


def _context_year_for_display(cit: Dict[str, Any]) -> Optional[str]:
    """
    Derive a document-year from citation context when extracted_date appears stale.
    Prefer years that appear in parentheticals near the citation text.
    Exclude document header years (e.g. "Argued March 30, 2021-Decided June 25") that
    contaminate citations like Detroit Timber (1906) with TransUnion's 2021.
    """
    if not isinstance(cit, dict):
        return None
    context = str(cit.get("context") or "").strip()
    if not context:
        return None
    # Prefer parenthetical year tokens: "(1990)", "(D.N.H. 2021)" etc.
    paren_years = re.findall(r"\((?:[^)]*?)(?:17|18|19|20)\d{2}(?:[^)]*?)\)", context)
    if paren_years:
        m = re.search(r"((?:17|18|19|20)\d{2})", paren_years[-1])
        if m:
            return m.group(1)
    # Fallback: last year in context, but EXCLUDE document header years.
    # Strip header patterns (e.g. "Argued March 30, 2021-Decided June 25") that contaminate
    # citations like Detroit Timber (1906) with the document's 2021.
    context_no_headers = re.sub(
        r"(?:Argued|Decided|Filed)\s+[^.]*?(?:17|18|19|20)\d{2}[^.]{0,60}",
        "",
        context,
        flags=re.IGNORECASE,
    )
    context_no_headers = re.sub(
        r"(?:17|18|19|20)\d{2}\s*[-–]\s*(?:Decided|Argued|Filed)[^.]{0,40}",
        "",
        context_no_headers,
        flags=re.IGNORECASE,
    )
    years = re.findall(r"\b((?:17|18|19|20)\d{2})\b", context_no_headers)
    if years:
        return years[-1]
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
    """Get canonical/verifying date from canonical fields only (no extracted fallback)."""
    rep = get_representative_verified_citation(cluster)
    if rep:
        date = get_citation_value(rep, "canonical_date")
        if (not date or date == "N/A") and isinstance(rep, dict) and isinstance(rep.get("metadata"), dict):
            date = rep["metadata"].get("possible_match_date")
        if date and date != "N/A":
            return date
    # FIX 2026-02-24: Check for true_by_parallel citations which have propagated canonical_date
    for cit in get_cluster_citations(cluster):
        if not cit or not isinstance(cit, dict):
            continue
        # Check top-level true_by_parallel (dict conversion puts it here, not in metadata)
        if cit.get("true_by_parallel"):
            date = cit.get("canonical_date")
            if date and date != "N/A":
                return date
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


def _google_search_url_for_cluster(cluster: Dict[str, Any]) -> Optional[str]:
    """Build a basic Google search URL from extracted case name + year, or citation fallback."""
    submitted_name = str(cluster.get("submitted_display_name") or get_best_extracted_name(cluster) or "").strip()
    submitted_year = str(cluster.get("submitted_display_date") or get_submitted_date(cluster) or "").strip()
    query = ""
    if submitted_name and submitted_name != "N/A":
        query = submitted_name
    else:
        # If name is unavailable, build search using first citation text.
        cits = get_cluster_citations(cluster)
        for cit in cits:
            ct = str(get_citation_value(cit, "citation", "") or get_citation_value(cit, "text", "") or "").strip()
            if ct:
                query = ct
                break
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
        # Only backfill from context when extracted_date is missing/unknown.
        # Do NOT overwrite existing extracted year; context windows can contain
        # nearby unrelated years (e.g., subsequent parentheticals in the same sentence).
        if not rep_date or rep_date in {"N/A", "Unknown Year", "unknown"}:
            context_year = _context_year_for_display(rep_sub)
            if context_year:
                rep_date = context_year
        if rep_name and rep_name != "N/A":
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
    cluster["submitted_display_name"] = _normalize_display_name_comma_spacing(
        str(cluster.get("submitted_display_name") or "")
    )
    if cluster.get("cluster_case_name"):
        cluster["cluster_case_name"] = _normalize_display_name_comma_spacing(
            str(cluster.get("cluster_case_name") or "")
        )
    cluster["display_canonical_url"] = get_canonical_url(cluster)
    # For non-canonical rows, provide a user-clickable web search fallback.
    if not cluster.get("display_canonical_url"):
        search_url = _google_search_url_for_cluster(cluster)
        if search_url:
            cluster["display_canonical_url"] = search_url
            # UI helper label for explicit "Search Google for:" link text.
            search_label = str(cluster.get("submitted_display_name") or "").strip()
            if not search_label or search_label == "N/A":
                cits = get_cluster_citations(cluster)
                for cit in cits:
                    ct = str(get_citation_value(cit, "citation", "") or get_citation_value(cit, "text", "") or "").strip()
                    if ct:
                        search_label = ct
                        break
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
    """
    if not isinstance(cluster, dict):
        return
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
