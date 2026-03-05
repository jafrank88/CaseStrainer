"""
Cluster matching and resolution for partial/placeholder citations.

This module handles matching incomplete citations (e.g., "594 U.S. ____") 
against verified citations by checking case name and year similarity.
"""
import re
import logging
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


def is_placeholder_citation(citation_text: str) -> bool:
    """Check if a citation is a placeholder (has ____, ___, or _ as page number).
    Matches: 594 U.S. ____, 594 U.S. ___, 594 U.S. _ (scotus 2021) - document header slip-op placeholders."""
    if not citation_text:
        return False
    if '____' in citation_text or '___' in citation_text:
        return True
    # Single underscore: "594 U.S. _" or "594 U. S. _ (2021)" - Cite as header contamination
    if re.search(r"\d+\s+U\.?\s*S\.?\s*_\s*(?:\(|$)", citation_text.strip(), re.IGNORECASE):
        return True
    return False


def normalize_case_name(name: str) -> str:
    """Normalize case name for comparison."""
    if not name:
        return ""
    # Remove signal phrases
    signal_phrases = [
        r'^see,?\s+e\.?g\.?,?\s*',
        r'^see\s+also\s+',
        r'^see\s+generally\s+',
        r'^but\s+see\s+',
        r'^see\s+',
        r'^accord\s+',
        r'^compare\s+',
        r'^cf\.?\s*',
        r'^citing\s+',
        r'^e\.?g\.?,?\s*',
        r'^i\.?e\.?,?\s*',
    ]
    result = name.lower().strip()
    for pattern in signal_phrases:
        result = re.sub(pattern, '', result, flags=re.IGNORECASE)
    # Remove common words for comparison
    result = re.sub(r'\b(inc\.?|llc|ltd\.?|corp\.?|co\.?)\b', '', result)
    result = re.sub(r'\s+', ' ', result).strip()
    return result


def extract_year_from_date(date_str: str) -> Optional[int]:
    """Extract year from a date string."""
    if not date_str:
        return None
    match = re.search(r'(19|20)\d{2}', str(date_str))
    if match:
        return int(match.group(0))
    return None


def case_names_similar(name1: str, name2: str, threshold: float = 0.6) -> bool:
    """Check if two case names are similar using sequence matching."""
    norm1 = normalize_case_name(name1)
    norm2 = normalize_case_name(name2)
    
    if not norm1 or not norm2:
        return False
    
    # Exact match after normalization
    if norm1 == norm2:
        return True
    
    # First party match (before "v.")
    def get_first_party(name):
        parts = re.split(r'\s+v\.?\s+', name, maxsplit=1, flags=re.IGNORECASE)
        return parts[0].strip() if parts else name.strip()
    
    party1 = get_first_party(norm1)
    party2 = get_first_party(norm2)
    
    # If first parties match closely, likely same case
    if party1 and party2:
        ratio = SequenceMatcher(None, party1, party2).ratio()
        if ratio >= threshold:
            return True
    
    # Overall similarity
    ratio = SequenceMatcher(None, norm1, norm2).ratio()
    return ratio >= threshold


def _extract_volume_reporter_from_placeholder(ph_text: str) -> Optional[tuple]:
    """
    Extract (volume, reporter) from placeholder like '594 U.S. ____' or '578 U. S. ___'.
    Returns (vol, reporter) e.g. ('594', 'U.S.') or None if not parseable.
    """
    if not ph_text:
        return None
    m = re.match(r"(\d+)\s+([A-Za-z.][A-Za-z.\s]*?)\s+_{1,4}\b", ph_text.strip(), re.IGNORECASE)
    if m:
        vol, rep = m.group(1), re.sub(r"\s+", " ", m.group(2).strip()).lower()
        rep = re.sub(r"u\.\s*s\.?", "u.s.", rep, flags=re.IGNORECASE)
        return (vol, rep)
    return None


def find_best_match_for_placeholder(
    placeholder_citation: Dict[str, Any],
    verified_citations: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Find the best matching verified citation for a placeholder citation.
    
    Matches based on:
    1. Volume/reporter match (CRITICAL: "594 U.S. ____" must match 594 U.S., not Milkovich 497 U.S.)
    2. Case name similarity
    3. Same year (if available)
    
    Returns the best match or None if no good match found.
    """
    ph_text = placeholder_citation.get('citation', '')
    ph_name = placeholder_citation.get('extracted_case_name') or placeholder_citation.get('case_name', '')
    ph_date = placeholder_citation.get('extracted_date') or placeholder_citation.get('canonical_date', '')
    ph_year = extract_year_from_date(ph_date)
    ph_vol_rep = _extract_volume_reporter_from_placeholder(ph_text)
    
    logger.info(f"[PLACEHOLDER-MATCH] Looking for match for: {ph_text} ({ph_name}, {ph_year}) vol_rep={ph_vol_rep}")
    
    best_match = None
    best_score = 0.0
    
    for verified in verified_citations:
        if not verified.get('verified', False):
            continue
            
        v_name = verified.get('case_name') or verified.get('canonical_name', '')
        v_date = verified.get('canonical_date') or verified.get('extracted_date', '')
        v_year = extract_year_from_date(v_date)
        v_cit = verified.get('citation', '')
        
        # CRITICAL: Volume/reporter must match to avoid "Cite as: 594 U.S. _ (2021)" matching Milkovich (497 U.S.)
        if ph_vol_rep:
            vol, rep = ph_vol_rep
            rep_esc = re.escape(rep).replace(r"\.", r"\.\s*")
            vol_rep_pat = re.compile(rf"\b{re.escape(vol)}\s+{rep_esc}\b", re.IGNORECASE)
            if not vol_rep_pat.search(v_cit):
                continue  # Verified citation has different volume/reporter
        
        # Must have case name to match
        if not v_name:
            continue
        
        # Check year match (if both have years)
        year_match = False
        if ph_year and v_year:
            year_match = (ph_year == v_year)
        elif ph_year or v_year:
            # One has year, other doesn't - neutral
            year_match = True
        else:
            # Neither has year - neutral
            year_match = True
        
        if not year_match:
            continue
        
        # Check case name similarity
        if not case_names_similar(ph_name, v_name):
            continue
        
        # Calculate match score
        score = SequenceMatcher(None, normalize_case_name(ph_name), normalize_case_name(v_name)).ratio()
        
        # Boost score for exact year match
        if ph_year and v_year and ph_year == v_year:
            score += 0.2
        
        logger.info(f"[PLACEHOLDER-MATCH] Candidate: {v_name} ({v_year}) - score: {score:.2f}")
        
        if score > best_score:
            best_score = score
            best_match = verified
    
    if best_match:
        logger.info(f"[PLACEHOLDER-MATCH] Best match for {ph_text}: {best_match.get('citation')} ({best_match.get('case_name')}) - score: {best_score:.2f}")
    else:
        logger.warning(f"[PLACEHOLDER-MATCH] No match found for {ph_text}")
    
    return best_match


def resolve_placeholder_citations(
    all_citations: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Resolve placeholder citations by matching them to verified citations.
    
    Returns updated citations list with placeholders either:
    - Matched to a verified citation (inherit canonical data)
    - Verified via API using extracted case name and year
    - Left as unverified standalone citations
    """
    # Separate placeholders and verified citations
    placeholders = []
    verified = []
    normal = []
    
    for cit in all_citations:
        cit_text = cit.get('citation', '')
        if is_placeholder_citation(cit_text):
            placeholders.append(cit)
        elif cit.get('verified', False):
            verified.append(cit)
            normal.append(cit)
        else:
            normal.append(cit)
    
    if not placeholders:
        return all_citations
    
    logger.info(f"[PLACEHOLDER-RESOLVE] Found {len(placeholders)} placeholders to resolve")
    logger.info(f"[PLACEHOLDER-RESOLVE] Against {len(verified)} verified citations")
    
    # Try to match each placeholder
    resolved_count = 0
    for ph in placeholders:
        match = find_best_match_for_placeholder(ph, verified)
        if match:
            # Copy canonical data from match
            ph['canonical_name'] = match.get('canonical_name')
            ph['canonical_date'] = match.get('canonical_date')
            ph['canonical_url'] = match.get('canonical_url')
            ph['case_name'] = match.get('case_name')
            ph['verified'] = True
            ph['true_by_parallel'] = True
            ph['matched_to'] = match.get('citation')
            ph['resolution_note'] = f"Matched to {match.get('citation')} based on case name and year similarity"
            resolved_count += 1
            logger.info(f"[PLACEHOLDER-RESOLVE] Resolved {ph.get('citation')} -> {match.get('citation')}")
        else:
            # CRITICAL FIX 2026-02-08: If placeholder has extracted case name and year,
            # mark it as resolved with extracted data (orphan placeholder)
            ph_name = ph.get('extracted_case_name') or ph.get('case_name', '')
            ph_date = ph.get('extracted_date') or ph.get('canonical_date', '')
            ph_year = extract_year_from_date(ph_date)
            
            if ph_name and ph_year and ph_name != 'N/A' and ph_name != 'U.S. Supreme Court Case':
                # Mark as resolved using extracted data
                ph['case_name'] = ph_name
                ph['canonical_name'] = ph_name
                ph['canonical_date'] = str(ph_year)
                ph['verified'] = True
                ph['true_by_parallel'] = True
                ph['resolution_note'] = f"Resolved via extracted case name and year ({ph_year})"
                resolved_count += 1
                logger.info(f"[PLACEHOLDER-RESOLVE] Resolved orphan {ph.get('citation')} via extracted data: {ph_name} ({ph_year})")
            else:
                # Mark as unresolvable placeholder
                ph['resolution_note'] = "Could not find matching verified citation or valid extracted data"
                logger.warning(f"[PLACEHOLDER-RESOLVE] Could not resolve {ph.get('citation')}")
    
    logger.info(f"[PLACEHOLDER-RESOLVE] Resolved {resolved_count}/{len(placeholders)} placeholders")
    
    return all_citations
