"""
Utility function for filtering cluster members.
This is in a separate module to avoid circular imports.
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Reporter series that use volume numbers that grow over time (regional, state).
# Same reporter + volume diff > VOLUME_ERA_THRESHOLD = different cases (different decades).
VOLUME_ERA_THRESHOLD = 150
# Same reporter + ANY different volume = different case (parallel cites are different reporters).
# Exception: same canonical case (e.g. CFE I 86 N.Y.2d + CFE II 100 N.Y.2d) allowed via _same_canonical_case.


def _parse_vol_rep(citation_text: str) -> Optional[Tuple[str, int]]:
    """Parse volume and reporter from citation. Returns (normalized_reporter, volume) or None."""
    if not citation_text or not isinstance(citation_text, str):
        return None
    s = citation_text.strip()
    # L. Ed. 2d must be parsed before generic "L. Ed." (otherwise page is misread as "2").
    m_led2 = re.match(r"(\d+)\s+L\.\s*Ed\.\s*2d\s+(\d+|____|___)", s, re.IGNORECASE)
    if m_led2 and m_led2.group(1).isdigit():
        return ("l.ed.2d", int(m_led2.group(1)))
    # First-series L. Ed. (not 2d)
    m_led1 = re.match(r"(\d+)\s+L\.\s*Ed\.\s+(?!2d)(\d+|____|___)", s, re.IGNORECASE)
    if m_led1 and m_led1.group(1).isdigit():
        return ("l.ed.", int(m_led1.group(1)))
    # Reporter can include digits (e.g. S.E.2d, P.3d, F.Supp.2d)
    m = re.match(r"(\d+)\s+([A-Za-z0-9\.\s]+?)\s+(\d+|____|___)", s)
    if not m:
        return None
    vol_str, rep, _ = m.group(1), m.group(2).strip(), m.group(3)
    if vol_str.isdigit() and not rep.upper().startswith("WL"):
        vol = int(vol_str)
        # Normalize reporter for comparison (S.E. 2d -> S.E.2d)
        rep_norm = re.sub(r"\s+", "", rep).lower()
        return (rep_norm, vol)
    return None


def _citation_text(c: Dict[str, Any]) -> str:
    return str(c.get("citation") or c.get("text") or "").strip()


def _is_wl_or_lexis_cite(cit_text: str) -> bool:
    """Westlaw / Lexis-style cites often sit next to reporter cites in TOAs; metadata year bleeds from neighbors."""
    if not cit_text:
        return False
    s = cit_text.upper()
    return bool(re.search(r"\bWL\b", s) or "LEXIS" in s)


def _trailing_paren_year_from_citation_text(cit_text: str) -> Optional[int]:
    """
    Decision year in the final parenthetical after the citation pin (Bluebook-style).
    Ignores '(quoting ...)' / '(citing ...)' prefixes the same way as minimal clustering.
    """
    if not cit_text:
        return None
    main = cit_text.strip()
    for sep in ("(quoting ", "(citing ", "(quoted in ", "(cited in "):
        ix = main.find(sep)
        if ix != -1:
            main = main[:ix].strip()
            break
    if re.search(r"\((?:scotus|ca\d+)\s+(?:19|20)\d{2}\s*\)\s*$", main, re.IGNORECASE):
        return None
    m = re.search(r"\(([^)]*?)\)\s*$", main)
    if not m:
        return None
    inner = m.group(1) or ""
    ym = re.search(r"\b((?:17|18|19|20)\d{2})\b", inner)
    if not ym:
        return None
    y = int(ym.group(1))
    return y if 1700 <= y <= 2030 else None


def _extract_year_from_metadata_only(c: Dict[str, Any]) -> Optional[int]:
    for key in ("extracted_date", "canonical_date", "date"):
        val = c.get(key)
        if not val:
            continue
        m = re.search(r"(19|20)\d{2}", str(val))
        if m:
            return int(m.group(0))
    return None


def _extract_year(c: Dict[str, Any]) -> Optional[int]:
    """
    Extract 4-digit decision year for clustering / conflict checks.

    Westlaw/Lexis pins: prefer the year on the citation line (trailing parenthetical or any
    (YYYY)) so TOA neighbor bleed onto extracted_date does not merge e.g. Heinz 2001 with
    Evanston 2007 WL.
    """
    ct = _citation_text(c)
    meta_y = _extract_year_from_metadata_only(c)
    trail_y = _trailing_paren_year_from_citation_text(ct)

    if _is_wl_or_lexis_cite(ct):
        if trail_y is not None:
            return trail_y
        if ct:
            m = re.search(r"\((19\d{2}|20\d{2})\)", ct)
            if m:
                return int(m.group(1))
        return meta_y

    if meta_y is not None and trail_y is not None and abs(meta_y - trail_y) > 2:
        return trail_y

    if meta_y is not None:
        return meta_y
    if trail_y is not None:
        return trail_y
    if ct:
        m = re.search(r"\((19\d{2}|20\d{2})\)", ct)
        if m:
            return int(m.group(1))
    return None


def _same_canonical_case(citation: Dict[str, Any], group_citations: List[Dict[str, Any]]) -> bool:
    """True if citation and group share canonical_name (e.g. CFE I 1995 + CFE II 2003)."""
    cit_cn = (citation.get("canonical_name") or "").strip().lower()
    if not cit_cn or " v. " not in cit_cn:
        return False
    for m in group_citations or []:
        m_cn = (m.get("canonical_name") or m.get("extracted_case_name") or "").strip().lower()
        if not m_cn or " v. " not in m_cn:
            continue
        # Same case: exact match or plaintiff last word match (Campaign for Fiscal Equity)
        if cit_cn == m_cn:
            return True
        cit_pl = cit_cn.split(" v. ")[0].strip().split()[-1] if " v. " in cit_cn else ""
        m_pl = m_cn.split(" v. ")[0].strip().split()[-1] if " v. " in m_cn else ""
        if cit_pl and m_pl and cit_pl == m_pl:
            return True
    return False


def citation_conflicts_with_group(citation: Dict[str, Any], group_citations: List[Dict[str, Any]]) -> bool:
    """
    Return True if adding this citation to the group would create a conflict.
    Same reporter + very different volumes (e.g. S.E.2d 67 vs 431) = different cases.
    Prevents clustering e.g. Buchanan 67 S.E.2d 289 (1951) with 431 S.E.2d 289 (1993).
    Also: different years (e.g. 2005 vs 2015) = different cases when semicolon-separated.
    EXCEPTION: Same canonical_name (e.g. CFE I 1995 + CFE II 2003) = same case line, allow merge.
    """
    cit_text = (citation.get("citation") or citation.get("text") or "").strip()

    # Year conflict must run for WL / administrative cites too (_parse_vol_rep returns None for WL).
    # Otherwise adjacent TOA lines with wrong extracted_case_name merge (e.g. Heinz F.3d + Evanston WL).
    if not _same_canonical_case(citation, group_citations):
        cit_year = _extract_year(citation)
        if cit_year is not None:
            for member in group_citations or []:
                y = _extract_year(member)
                if y is not None and abs(cit_year - y) > 2:
                    logger.info(
                        f"[CLUSTER-FILTER] Citation '{cit_text[:50]}...' conflicts with group "
                        f"(year {cit_year} vs {y} - different cases)"
                    )
                    return True

    parsed = _parse_vol_rep(cit_text)
    if not parsed:
        return False
    rep_new, vol_new = parsed

    for member in group_citations or []:
        m_text = (member.get("citation") or member.get("text") or "").strip()
        m_parsed = _parse_vol_rep(m_text)
        if not m_parsed:
            continue
        rep_m, vol_m = m_parsed
        if rep_m != rep_new:
            continue
        if vol_m == vol_new:
            continue
        # Same reporter, different volume = different case (e.g. 209 P. 1102 vs 214 P. 146).
        # Exception 1: same canonical_url (same verified opinion) = true parallel.
        # Exception 2: same canonical case by name (e.g. CFE I 86 N.Y.2d + CFE II 100 N.Y.2d)
        # — applies to state/regional lines, not U.S. Reports: 441 U.S. and 446 U.S. are always
        # different merits volumes (e.g. Broadcast Music vs Catalano in one sentence).
        cit_url = (citation.get("canonical_url") or "").strip()
        mem_url = (member.get("canonical_url") or "").strip()
        if cit_url and mem_url and cit_url == mem_url:
            continue
        # Federal reporters where different volumes are always different published opinions;
        # do not apply state-court multi-opinion (_same_canonical_case) merge exceptions.
        _federal_vol_strict = rep_new == rep_m and rep_new in (
            "u.s.",
            "s.ct.",
            "l.ed.",
            "l.ed.2d",
            "f.3d",
            "f.2d",
            "f.4th",
        )
        if _federal_vol_strict:
            logger.info(
                f"[CLUSTER-FILTER] Federal reporter volume mismatch: '{cit_text}' vs '{m_text}' "
                f"(reporter '{rep_new}', volumes {vol_new} vs {vol_m}) — separate cases"
            )
            return True
        if _same_canonical_case(citation, [member]):
            continue
        logger.info(
            f"[CLUSTER-FILTER] Citation '{cit_text}' conflicts with group (same reporter '{rep_new}', "
            f"volumes {vol_new} vs {vol_m} = different cases)"
        )
        return True
    return False


def filter_cluster_members_by_reporter(citation_text: str, member_citations: List[str]) -> List[str]:
    """
    Filter cluster members to exclude:
    1. Same-reporter/different-volume citations (different cases)
    2. Placeholder citations (with ____ or ___ page numbers)
    
    Parallel citations MUST be from DIFFERENT reporters for the same case.
    Same reporter + different volumes = DIFFERENT CASES entirely.
    """
    filtered = []
    
    # NOTE: We no longer skip bare placeholders here. They may have resolved
    # extracted_case_name values that aren't visible in the citation text string.
    # Unresolved placeholders are cleaned up later by _is_unresolved_placeholder
    # in unified_processing_pipeline.py after placeholder resolution.
    
    # Parse current citation
    parsed_current = None
    match = re.match(r"(\d+)\s+([A-Za-z\.\s]+)\s+(\d+|____|___)", citation_text)
    if match:
        parsed_current = {
            "volume": match.group(1),
            "reporter": match.group(2).strip(),
            "page": match.group(3)
        }
    
    for member in member_citations:
        if member == citation_text:
            continue
        
        # NOTE: No longer skipping bare placeholder members here.
        # Resolved placeholders are kept; unresolved ones cleaned up later.
            
        # Parse member citation
        parsed_member = None
        match_m = re.match(r"(\d+)\s+([A-Za-z\.\s]+)\s+(\d+|____|___)", member)
        if match_m:
            parsed_member = {
                "volume": match_m.group(1),
                "reporter": match_m.group(2).strip(),
                "page": match_m.group(3)
            }
        
        # Check if same reporter but different volume
        if parsed_current and parsed_member:
            vol_c, rep_c = parsed_current.get("volume"), parsed_current.get("reporter")
            vol_m, rep_m = parsed_member.get("volume"), parsed_member.get("reporter")
            
            if rep_c and rep_m and rep_c == rep_m and vol_c and vol_m and vol_c != vol_m:
                logger.warning(
                    f"[CLUSTER-FILTER] Excluding {member} from cluster of {citation_text}: "
                    f"same reporter '{rep_c}' but different volumes ({vol_c} vs {vol_m})"
                )
                continue
        
        filtered.append(member)
    
    return filtered


def remove_bogus_same_reporter_citations(citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove bogus citations that are same reporter + same page but different (small) volume.
    E.g. "67 S.E.2d 289" when "431 S.E.2d 289" is present - the 67 is Va. page bleed, not a real cite.
    Keeps the citation with the larger volume (the real one).
    """
    if len(citations) < 2:
        return citations
    parsed = []
    for i, c in enumerate(citations):
        ct = (c.get("citation") or c.get("citation_text") or c.get("text") or "").strip()
        p = _parse_vol_rep(ct)
        parsed.append((i, ct, p))
    # Find pairs: same reporter, same page, different volumes
    to_remove = set()
    for i, ct_i, p_i in parsed:
        if not p_i:
            continue
        rep_i, vol_i = p_i
        for j, ct_j, p_j in parsed:
            if i >= j or not p_j:
                continue
            rep_j, vol_j = p_j
            if rep_i != rep_j:
                continue
            # Same reporter - check if same page (different volumes = different cases, but one may be bogus)
            m_i = re.match(r"(\d+)\s+([A-Za-z0-9\.\s]+?)\s+(\d+|____|___)", ct_i)
            m_j = re.match(r"(\d+)\s+([A-Za-z0-9\.\s]+?)\s+(\d+|____|___)", ct_j)
            if not m_i or not m_j:
                continue
            page_i, page_j = m_i.group(3), m_j.group(3)
            if page_i != page_j:
                continue
            # Same reporter, same page, different volumes - remove the one with smaller volume
            # when it's likely page bleed from a parallel cite (e.g. U.S. App. D.C. 139 -> "139 F.2d 1267")
            vol_i_int, vol_j_int = int(vol_i), int(vol_j)
            smaller, larger = min(vol_i_int, vol_j_int), max(vol_i_int, vol_j_int)
            # Original: vol < 100 (e.g. 67 S.E.2d from Va. 67)
            # Extended: for F.2d/F.3d, vol < 300 and larger/smaller >= 2 (e.g. 139 F.2d from U.S. App. D.C. 139)
            is_f_reporter = rep_i in ("f.2d", "f.3d", "f.4th")
            remove_smaller = (
                smaller < 100
                or (is_f_reporter and smaller < 300 and larger >= 2 * smaller)
            )
            if vol_i_int < vol_j_int and remove_smaller:
                to_remove.add(i)
            elif vol_j_int < vol_i_int and remove_smaller:
                to_remove.add(j)
    if not to_remove:
        return citations
    return [c for i, c in enumerate(citations) if i not in to_remove]
