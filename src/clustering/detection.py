"""
Cluster Detection Module
========================

Detects parallel citations and structural citation groups.

Parallel citation = one case reported in multiple reporters (same name and date).
Goal: all parallel citations for the same case appear in a single cluster. Rare case:
document cites A & B here and later B & C elsewhere; then A, B, and C should all
be in one cluster (transitive merge is applied in clustering/master.py).
"""

import re
import logging
from typing import List, Dict, Any, Optional
from src.utils.same_case import has_case_name, names_are_same_case

logger = logging.getLogger(__name__)

# Helper function to safely get attribute from dict or object
def _get_attr(citation: Any, key: str, default: Any = None) -> Any:
    """Get attribute from dict or object citation."""
    if isinstance(citation, dict):
        return citation.get(key, default)
    return getattr(citation, key, default)

SEPARATOR_PATTERN = re.compile(r"[,;]\s*")

# Attribute key for semicolon segment id (same case block: "Case A, cite; Case B, cite")
SEMICOLON_SEGMENT_ATTR = "_semicolon_segment_id"


def get_semicolon_segment_id(text: str, position: int, _semicolon_indices: Optional[List[int]] = None) -> int:
    """
    Return the semicolon segment index for a character position.
    Segment 0 = from start to first ';', segment 1 = first ';' to second ';', etc.
    Used to keep clusters within the same case block when text is "Case A, 123 Rep.; Case B, 456 Rep."
    Pass _semicolon_indices from get_semicolon_indices(text) to avoid O(position) work per call (no bottleneck on long docs).
    """
    if not text or position <= 0:
        return 0
    if _semicolon_indices is not None:
        import bisect
        return bisect.bisect_left(_semicolon_indices, position)
    return text[:position].count(";")


def get_semicolon_indices(text: str) -> List[int]:
    """One-pass list of semicolon positions; use with get_semicolon_segment_id(..., _semicolon_indices=...) to avoid O(n*L) bottleneck."""
    if not text:
        return []
    return [i for i, c in enumerate(text) if c == ";"]


def _set_segment_id(citation: Any, segment_id: int) -> None:
    """Attach semicolon segment id to a citation (dict or object)."""
    if isinstance(citation, dict):
        citation[SEMICOLON_SEGMENT_ATTR] = segment_id
    else:
        setattr(citation, SEMICOLON_SEGMENT_ATTR, segment_id)


def _get_segment_id(citation: Any) -> Optional[int]:
    """Get semicolon segment id from a citation, or None if not set."""
    if isinstance(citation, dict):
        return citation.get(SEMICOLON_SEGMENT_ATTR)
    return getattr(citation, SEMICOLON_SEGMENT_ATTR, None)


# Pattern to detect TOA dotted leaders between citations
_TOA_DOTS_PATTERN = re.compile(r'\.{3,}')

# Pattern to detect parenthetical citation boundaries:
# "(quoting X v. Y, ...", "(citing X v. Y, ...", "(quoted in ...", etc.
_PAREN_SIGNAL_RE = re.compile(
    r'\(\s*(?:quoting|citing|quoted\s+in|cited\s+in|accord)\s',
    re.IGNORECASE,
)

# ECN cleaning pattern for TOA prefixes
_TOA_PREFIX_RE = re.compile(
    r'^(?:TABLE\s+OF\s+AUTHORITIES\s+)?(?:(?:I{1,3}V?|V?I{0,3})\s+)?'
    r'Cases(?:[\u2014\-\u2013]Continued)?(?:\s*:\s*|\s+)(?:Page\s+)?',
    re.IGNORECASE
)

def _clean_ecn(raw):
    """Strip TOA prefixes, docket numbers, and trailing citation text from extracted_case_name."""
    if not raw:
        return ""
    c = _TOA_PREFIX_RE.sub('', raw).strip()
    c = re.sub(r'^Page\s+(?=[A-Z])', '', c).strip()
    # Strip trailing citation text (e.g. ", 2 Cranch 64" or ", 765 F. Supp. 3d 102")
    c = re.sub(r',\s*\d+\s+(?:Cranch|Wheat|Pet|How|Wall|Black|U\.S\.|S\.Ct\.|L\.Ed|F\.\d*|F\.\s*Supp).*$', '', c).strip()
    # Strip trailing state/regional reporter citation (e.g. ", 169 Wn. 2d 81" or ", 233 P.3d 853")
    # so "Kustura v. Dep't of Lab. & Indus., 169 Wn. 2d 81, 2010" -> "Kustura v. Dep't of Lab. & Indus."
    # and same-case grouping can match parallel cites (Wn.2d + P.3d). Repeat to strip multiple trailing cites.
    for _ in range(3):
        c_prev = c
        c = re.sub(
            r',\s*\d{1,4}\s+(?:Wn\.|Wash\.|P\.|N\.W\.|S\.E\.|N\.E\.|S\.W\.|A\.|So\.|Cal\.)(?:\s*\d*d?)?\s+\d{1,5}(?:\s*,?\s*\d{4})?\s*$',
            '', c, flags=re.IGNORECASE
        ).strip()
        if c == c_prev:
            break
    # Strip docket numbers: ", No. 2", ", No. CV 25", ", No. 17", ", No. 3", or bare ", No"
    c = re.sub(r',\s*No\.?\s*(?:[\w\-\.]+(?:\s+[\w\-\.]+)*)?\s*$', '', c, flags=re.IGNORECASE).strip()
    # Strip trailing commas, numbers, and junk (e.g. ", , 1337, 2020" or ", 2010")
    c = re.sub(r'(?:,\s*)+(?:\d{1,5}\s*,?\s*)*$', '', c).strip()
    # Strip trailing comma
    c = c.rstrip(',').strip()
    return c

_PUBLIC_DOMAIN_BASE_RE = re.compile(
    # Illinois: 2025 IL 130033, 2023 IL App (1st) 220990
    r'\b(\d{4}\s+IL(?:\s+App\s+\(\d+(?:st|nd|rd|th)\))?\s+\d+)\b'
    r'|'
    # Two-letter codes (with appellate variants): CO/COA, ME, MT, ND/ND App,
    # OK/OK CIV APP/OK CR, SD, UT/UT App, VT, WI/WI App, WY
    r'\b(\d{4}\s+(?:COA|CO|ME|MT|ND(?:\s+App)?|OK(?:\s+C(?:IV\s+APP|R))?|SD|UT(?:\s+App)?|VT|WI(?:\s+App)?|WY)\s+\d+)\b'
    r'|'
    # Period-abbreviated: Ark./Ark. App., N.H., Miss.
    r'\b(\d{4}\s+(?:Ark\.(?:\s+App\.)?|N\.H\.|Miss\.)\s+\d+)\b'
    r'|'
    # Hyphenated: Ohio, NM/NMSC/NMCA, NCSC/NCCOA
    r'\b(\d{4}[\-\u2011\u2013\u2014](?:Ohio|NM(?:SC|CA)?|NC(?:SC|COA))[\-\u2011\u2013\u2014]\s*\d+)\b',
    re.IGNORECASE,
)

def _shared_base_citation(cit_a, cit_b) -> bool:
    """True if two citations share the same public domain base citation number.

    E.g. '2023 IL App (1st) 220990, 27' and '2023 IL App (1st) 220990, 31'
    both have base '2023 IL App (1st) 220990'.
    """
    text_a = (_get_attr(cit_a, "citation", "") or "").strip()
    text_b = (_get_attr(cit_b, "citation", "") or "").strip()
    if not text_a or not text_b:
        return False
    bases_a = {next(g for g in m.groups() if g).strip() for m in _PUBLIC_DOMAIN_BASE_RE.finditer(text_a)}
    bases_b = {next(g for g in m.groups() if g).strip() for m in _PUBLIC_DOMAIN_BASE_RE.finditer(text_b)}
    return bool(bases_a and bases_b and bases_a & bases_b)


def _same_case_check(cit_a, cit_b):
    """Return True if two citations plausibly belong to the same case.

    Uses canonical_name when present (verified) so parallel cites (e.g. 169 Wn.2d 81 and
    233 P.3d 853) match even when extracted_case_name is contaminated. Otherwise uses
    cleaned extracted_case_name. Delegates to src.utils.same_case.names_are_same_case.
    """
    # Public domain citations with same base number are always the same case
    if _shared_base_citation(cit_a, cit_b):
        return True
    def _best_name(cit):
        canonical = (_get_attr(cit, "canonical_name", "") or "").strip()
        if canonical and " v. " in canonical:
            return canonical
        ecn = _clean_ecn(_get_attr(cit, "extracted_case_name", "") or "")
        return ecn
    return names_are_same_case(_best_name(cit_a), _best_name(cit_b))


def _get_year(cit: Any) -> Optional[int]:
    """Extract 4-digit year from citation (dict or object): metadata first, then (YYYY) in citation text."""
    for key in ("extracted_date", "canonical_date", "date", "year"):
        val = _get_attr(cit, key, None)
        if val:
            m = re.search(r"(19|20)\d{2}", str(val))
            if m:
                return int(m.group(0))
    cit_text = _get_attr(cit, "citation", "") or _get_attr(cit, "text", "")
    if cit_text:
        m = re.search(r"\((19|20)\d{2}\)", str(cit_text))
        if m:
            return int(m.group(1))
    return None


def _year_conflict_with_group(citation: Any, group: List[Any]) -> bool:
    """True if citation's year is too far from all years in group (nested/quoting different case, e.g. Deggs 2016 vs Hubbard 1995)."""
    y = _get_year(citation)
    if y is None:
        return False
    group_years = {_get_year(c) for c in group}
    group_years.discard(None)
    if not group_years:
        return False
    if any(gy is not None and abs(y - gy) <= 2 for gy in group_years):
        return False
    return True


def detect_parallel_groups(
    citations: List[Dict[str, Any]], 
    proximity_threshold: int = 150,
    original_text: str = ""
) -> List[List[Dict[str, Any]]]:
    """
    Detect groups of parallel citations based on proximity.
    
    Args:
        citations: List of citation dictionaries with position info
        proximity_threshold: Max distance between citations to be considered parallel
        original_text: Original document text (used to detect TOA sections)
        
    Returns:
        List of citation groups (each group is a list of citations)
    """
    if not citations:
        return []
    
    # Sort by position
    sorted_citations = sorted(
        citations, 
        key=lambda c: _get_attr(c, "start_index", 0) or _get_attr(c, "start_pos", 0)
    )
    
    # Assign semicolon segment id so clustering can keep "Case A, cite; Case B, cite" as separate clusters
    # Precompute semicolon positions once to avoid O(n*L) bottleneck on long documents
    if original_text:
        _semi = get_semicolon_indices(original_text)
        for c in sorted_citations:
            pos = _get_attr(c, "start_index") or _get_attr(c, "start_pos", 0)
            _set_segment_id(c, get_semicolon_segment_id(original_text, pos, _semicolon_indices=_semi))
    
    groups = []
    current_group = [sorted_citations[0]]
    
    for citation in sorted_citations[1:]:
        prev_end = _get_attr(current_group[-1], "end_index") or _get_attr(current_group[-1], "end_pos", 0)
        curr_start = _get_attr(citation, "start_index") or _get_attr(citation, "start_pos", 0)
        
        # Fallback: if end_index is missing, estimate from start_index + citation length
        if not prev_end:
            prev_cit_text = _get_attr(current_group[-1], "citation", "")
            prev_start = _get_attr(current_group[-1], "start_index") or _get_attr(current_group[-1], "start_pos", 0)
            if prev_start and prev_cit_text:
                prev_end = prev_start + len(prev_cit_text)
        
        is_close = curr_start - prev_end <= proximity_threshold if (prev_end and curr_start) else True
        
        # TOA guard: if the text between two close citations contains dotted leaders
        # (e.g., "............"), they are separate TOA entries, not parallel citations
        # Semicolon guard: "A; B; C" = different cases (e.g. Dow; Frederick)
        if is_close and original_text and prev_end and curr_start:
            text_between = original_text[prev_end:curr_start]
            if _TOA_DOTS_PATTERN.search(text_between):
                is_close = False
            if ";" in text_between:
                is_close = False
                logger.debug(
                    f"[PARALLEL-DETECTION] Semicolon between citations - different cases: "
                    f"'{_get_attr(current_group[-1], 'citation', '')[:40]}...' and '{_get_attr(citation, 'citation', '')[:40]}...'"
                )
            if is_close and _PAREN_SIGNAL_RE.search(text_between):
                is_close = False
                logger.debug(
                    f"[PARALLEL-DETECTION] Parenthetical boundary (quoting/citing) between citations: "
                    f"'{_get_attr(current_group[-1], 'citation', '')[:40]}...' and '{_get_attr(citation, 'citation', '')[:40]}...'"
                )
        
        # Same-case check: only group if citations plausibly belong to same case
        if is_close and not _same_case_check(current_group[-1], citation):
            is_close = False
        
        # Year guard: don't group if citation year is far from group (e.g. Deggs 2016 vs Hubbard 1995 in "(quoting Hubbard ... (1995))")
        if is_close and _year_conflict_with_group(citation, current_group):
            is_close = False
            logger.debug(
                f"[PARALLEL-DETECTION] Year conflict - citation year vs group: "
                f"'{_get_attr(citation, 'citation', '')[:40]}...' not added to group"
            )
        
        if is_close:
            current_group.append(citation)
        else:
            # Include single citations as standalone groups
            groups.append(current_group)
            current_group = [citation]
    
    # Don't forget the last group (include even if single)
    groups.append(current_group)
    
    logger.info(f"[PARALLEL-DETECTION] Found {len(groups)} groups from {len(citations)} citations")
    return groups


def detect_structural_groups(
    citations: List[Dict[str, Any]],
    text: str
) -> List[List[Dict[str, Any]]]:
    """
    Detect structural citation groups using pattern recognition.
    
    Looks for patterns like:
    - "Case Name, Citation1, Citation2, Citation3 (Year)"
    - Multiple citations in same sentence
    
    Args:
        citations: List of citation dictionaries
        text: Original document text
        
    Returns:
        List of structural citation groups
    """
    if not citations or not text:
        return []
    
    groups = []
    
    for i, citation in enumerate(citations):
        start_pos = _get_attr(citation, "start_index") or _get_attr(citation, "start_pos", 0)
        end_pos = _get_attr(citation, "end_index") or _get_attr(citation, "end_pos", 0)
        
        if start_pos is None or end_pos is None:
            continue
        
        # Look for nearby citations
        nearby = [citation]
        context_end = min(len(text), end_pos + 200)
        context = text[end_pos:context_end]
        
        # Check if followed by comma/semicolon and another citation pattern
        if SEPARATOR_PATTERN.match(context):
            # Look for subsequent citations
            chain_end = end_pos
            for j in range(i + 1, len(citations)):
                next_cit = citations[j]
                next_start = _get_attr(next_cit, "start_index") or _get_attr(next_cit, "start_pos", 0)
                next_end = _get_attr(next_cit, "end_index") or _get_attr(next_cit, "end_pos", 0)
                
                if next_start and next_start - chain_end < 300:
                    # TOA guard: check for dotted leaders between citations
                    if text and chain_end and next_start:
                        text_between = text[chain_end:next_start]
                        if _TOA_DOTS_PATTERN.search(text_between):
                            break
                        # Semicolon separates different cases (e.g. "884 A.2d 667; Frederick v. City...")
                        if ";" in text_between:
                            break
                        # Parenthetical boundary: "(quoting X v. Y, ..." means inner cite is a different case
                        if _PAREN_SIGNAL_RE.search(text_between):
                            break
                    # Same-case check: only chain if same case
                    if not _same_case_check(citation, next_cit):
                        continue
                    nearby.append(next_cit)
                    if next_end:
                        chain_end = next_end
                else:
                    break
        
        # Always include the citation (as single or group)
        groups.append(nearby)
    
    # Remove duplicate groups
    unique_groups = _remove_duplicate_groups(groups)
    
    logger.info(f"[STRUCTURAL-DETECTION] Found {len(unique_groups)} structural groups")
    return unique_groups


def _remove_duplicate_groups(groups: List[List[Dict[str, Any]]]) -> List[List[Dict[str, Any]]]:
    """Remove duplicate groups by comparing citation IDs."""
    seen = set()
    unique = []
    
    for group in groups:
        # Create a frozenset of citation texts as unique identifier
        key = frozenset(
            _get_attr(c, "citation", str(c)) for c in group
        )
        if key not in seen:
            seen.add(key)
            unique.append(group)
    
    return unique


def find_best_cluster_seed(citations: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Find the best citation to seed a cluster from.
    
    Prefers citations with:
    1. Verified status
    2. Case name present
    3. High confidence
    
    Returns:
        Best citation or None
    """
    if not citations:
        return None
    
    def score_citation(c: Any) -> int:
        score = 0
        if _get_attr(c, "verified"):
            score += 100
        if _get_attr(c, "case_name") or _get_attr(c, "canonical_name"):
            score += 50
        score += int(_get_attr(c, "confidence", 0) * 10)
        return score
    
    return max(citations, key=score_citation)


def are_citations_parallel(
    citation1: Dict[str, Any],
    citation2: Dict[str, Any],
    max_distance: int = 150
) -> bool:
    """
    Check if two citations are parallel (close together with matching reporters).
    
    Args:
        citation1: First citation
        citation2: Second citation  
        max_distance: Maximum allowed distance between citations
        
    Returns:
        True if citations appear to be parallel
    """
    # Check distance
    pos1 = _get_attr(citation1, "end_index") or _get_attr(citation1, "end_pos", 0)
    pos2 = _get_attr(citation2, "start_index") or _get_attr(citation2, "start_pos", 0)
    
    if abs(pos2 - pos1) > max_distance:
        return False
    
    # Check if reporters match (e.g., both Washington citations)
    cit1_text = _get_attr(citation1, "citation", "")
    cit2_text = _get_attr(citation2, "citation", "")
    
    # Extract reporter patterns
    reporter1 = _extract_reporter_pattern(cit1_text)
    reporter2 = _extract_reporter_pattern(cit2_text)
    
    # Parallel if same reporter type
    return reporter1 and reporter2 and reporter1 == reporter2


def _extract_reporter_pattern(citation_text: str) -> Optional[str]:
    """Extract reporter pattern from citation text."""
    patterns = {
        "Wn.": r"Wn\.\d*d?",
        "Wash.": r"Wash\.\d*d?",
        "F.": r"F\.\d*d?",
        "U.S.": r"U\.S\.",
        "S.Ct.": r"S\.\s*Ct\.",
        "L.Ed.": r"L\.\s*Ed\.\d*d?",
        "P.": r"P\.\d*d?",
        "A.": r"A\.\d*d?",
        "So.": r"So\.\d*d?",
        "N.E.": r"N\.E\.\d*d?",
        "N.W.": r"N\.W\.\d*d?",
        "S.E.": r"S\.E\.\d*d?",
        "S.W.": r"S\.W\.\d*d?",
        "Cal.": r"Cal\.\d*d?",
        "N.Y.S.": r"N\.Y\.S\.\d*d?",
    }
    
    for reporter_type, pattern in patterns.items():
        if re.search(pattern, citation_text, re.IGNORECASE):
            return reporter_type
    
    return None
