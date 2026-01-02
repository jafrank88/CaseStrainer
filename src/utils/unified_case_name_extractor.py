"""
UNIFIED Case Name Extractor - Single source of truth for ALL extractions.

This module replaces all scattered extraction logic with ONE method that
ALWAYS uses strict context isolation to prevent case name bleeding.

CRITICAL PRINCIPLE:
- EVERY citation extraction MUST go through extract_case_name_with_strict_isolation()
- NO other extraction methods should be used
- This ensures 100% consistency and zero case name bleeding
"""

import logging
import re
from typing import Optional, List, Any
from src.utils.strict_context_isolator import (
    find_all_citation_positions,
    get_strict_context_for_citation,
    get_adaptive_context_for_citation,
    extract_case_name_from_strict_context
)

logger = logging.getLogger(__name__)


def extract_case_name_with_strict_isolation(
    text: str,
    citation_text: str,
    citation_start: int,
    citation_end: int,
    all_citations: Optional[List[Any]] = None,
    document_primary_case_name: Optional[str] = None
) -> Optional[str]:
    """
    THE ONLY case name extraction function that should be used.
    
    This function uses strict context isolation to prevent case name bleeding
    between nearby citations.
    
    Args:
        text: Full document text
        citation_text: The citation string (e.g., "506 U.S. 139")
        citation_start: Start position of citation in text
        citation_end: End position of citation in text
        all_citations: Optional list of all citations for better boundary detection
        document_primary_case_name: Optional document primary case name for contamination filtering
        
    Returns:
        Extracted case name or None
        
    Example:
        >>> extract_case_name_with_strict_isolation(
        ...     text="See Will v. Hallock, 546 U.S. 345 (2006) (quoting P.R. Aqueduct v. Metcalf, 506 U.S. 139)",
        ...     citation_text="506 U.S. 139",
        ...     citation_start=80,
        ...     citation_end=92
        ... )
        'P.R. Aqueduct v. Metcalf'  # Correctly isolates, not "Will v. Hallock"
    """
    try:
        logger.info(f"[UNIFIED-EXTRACT] Starting strict extraction for {citation_text} at pos {citation_start}-{citation_end}")
        
        # Get all citation positions for proper boundary detection
        all_positions = find_all_citation_positions(text)
        logger.debug(f"[UNIFIED-EXTRACT] Found {len(all_positions)} total citation positions in document")
        
        # Get adaptive context (starts small and expands until case name found)
        # USER FIX: Reduced from 300 to 100 chars to prevent cascading contamination
        # The expanding window (25→50→75→100) handles legitimate distant names
        adaptive_context = get_adaptive_context_for_citation(
            text, 
            citation_start, 
            citation_end, 
            all_positions, 
            max_lookback=100
        )
        
        logger.debug(f"[UNIFIED-EXTRACT] Adaptive context for {citation_text}: {len(adaptive_context)} chars")
        
        # Extract case name from adaptive context
        case_name = extract_case_name_from_strict_context(adaptive_context, citation_text)
        
        # NOTE: Removed strict boundary validation that was causing performance issues
        # The extraction already uses isolated context, so additional validation was redundant
        # and was rejecting valid extractions, causing retries and slowdowns
        
        # FINAL SAFETY CHECK: Reject header patterns before returning
        # This ensures no header slips through even if previous checks missed it
        if case_name:
            case_name_upper = case_name.upper()
            has_et_al = 'ET AL' in case_name_upper or 'ETAL' in case_name_upper.replace(' ', '')
            has_role_word = any(role in case_name_upper for role in ['PETITIONER', 'RESPONDENT', 'APPELLANT', 'APPELLEE', 'PLAINTIFF', 'DEFENDANT'])
            has_no = 'NO.' in case_name_upper or ' NO ' in case_name_upper or case_name_upper.endswith(' NO')
            
            # Reject if it's clearly a header (ET AL + role word, or role word + NO)
            if (has_et_al and has_role_word) or (has_role_word and has_no):
                logger.warning(f"[UNIFIED-EXTRACT-FINAL-REJECT] {citation_text} → '{case_name}' REJECTED (header pattern detected)")
                case_name = None
        
        # Apply contamination filtering if document primary case name is provided
        if case_name and document_primary_case_name:
            if _is_document_case_contamination(case_name, document_primary_case_name):
                logger.warning(f"[UNIFIED-EXTRACT-CONTAMINATION] {citation_text} → '{case_name}' REJECTED (matches document primary case '{document_primary_case_name}')")
                return None
            else:
                logger.info(f"[UNIFIED-EXTRACT-CONTAMINATION] {citation_text} → '{case_name}' PASSED (no contamination)")
        
        # CRITICAL FIX: Validate extracted case name before returning
        # This prevents contaminated names like "WPLA claim. Call v. Heard" from being returned
        if case_name:
            from src.case_name_validator import is_valid_case_name
            if not is_valid_case_name(case_name):
                logger.warning(f"[UNIFIED-EXTRACT-REJECT] {citation_text} → '{case_name}' REJECTED by validator (contamination detected)")
                return None
            logger.info(f"[UNIFIED-EXTRACT-SUCCESS] {citation_text} → '{case_name}'")
            return case_name
        else:
            logger.warning(f"[UNIFIED-EXTRACT-FAIL] No case name found for {citation_text}")
            return None
            
    except Exception as e:
        logger.error(f"[UNIFIED-EXTRACT-ERROR] Failed to extract for {citation_text}: {e}")
        return None


def apply_unified_extraction_to_all_citations(
    text: str,
    citations: List[Any],
    force_reextract: bool = False
) -> None:
    """
    Apply unified extraction to ALL citations in the list.
    
    This ensures every citation uses strict context isolation,
    regardless of how it was originally found.
    
    Args:
        text: Full document text
        citations: List of citation objects
        force_reextract: If True, re-extract even if case name exists
    """
    logger.info(f"[UNIFIED-EXTRACT-ALL] Applying unified extraction to {len(citations)} citations")
    
    extracted_count = 0
    skipped_count = 0
    failed_count = 0
    
    for citation in citations:
        # Get citation details
        if hasattr(citation, 'citation'):
            cit_text = citation.citation
            start = getattr(citation, 'start_index', None)
            end = getattr(citation, 'end_index', None)
            existing_name = getattr(citation, 'extracted_case_name', None)
        elif isinstance(citation, dict):
            cit_text = citation.get('citation')
            start = citation.get('start_index')
            end = citation.get('end_index')
            existing_name = citation.get('extracted_case_name')
        else:
            logger.warning(f"[UNIFIED-EXTRACT-ALL] Unknown citation type: {type(citation)}")
            continue
        
        # Skip if no position info
        if start is None or end is None:
            logger.debug(f"[UNIFIED-EXTRACT-ALL] Skipping {cit_text} - no position info")
            skipped_count += 1
            continue
        
        # Skip if already has good extraction (unless forcing)
        if not force_reextract and existing_name and existing_name != "N/A" and len(existing_name) > 10:
            logger.debug(f"[UNIFIED-EXTRACT-ALL] Skipping {cit_text} - already has: {existing_name}")
            skipped_count += 1
            continue
        
        # Extract using unified method
        case_name = extract_case_name_with_strict_isolation(
            text, cit_text, start, end, citations
        )
        
        if case_name:
            # Set the extracted case name
            if hasattr(citation, 'extracted_case_name'):
                citation.extracted_case_name = case_name
            elif isinstance(citation, dict):
                citation['extracted_case_name'] = case_name
            
            extracted_count += 1
            logger.info(f"[UNIFIED-EXTRACT-ALL] Set {cit_text} → '{case_name}'")
        else:
            # Set to N/A if extraction failed
            if hasattr(citation, 'extracted_case_name'):
                citation.extracted_case_name = "N/A"
            elif isinstance(citation, dict):
                citation['extracted_case_name'] = "N/A"
            
            failed_count += 1
            logger.warning(f"[UNIFIED-EXTRACT-ALL] Failed to extract for {cit_text}")
    
    logger.info(
        f"[UNIFIED-EXTRACT-ALL] Complete: "
        f"{extracted_count} extracted, {skipped_count} skipped, {failed_count} failed"
    )


def _is_document_case_contamination(extracted_name: str, document_primary_case_name: str, similarity_threshold: float = 0.95) -> bool:
    """
    Detect if extracted case name is contaminated with document's primary case name.
    
    Args:
        extracted_name: The case name that was extracted
        document_primary_case_name: The document's primary case name
        
    Returns:
        True if contaminated (should be rejected), False if clean
    """
    if not document_primary_case_name or not extracted_name:
        return False
    
    # CRITICAL FIX: First check for header patterns in extracted name
    # This catches cases where the header format is extracted even if normalization doesn't match
    
    # SIMPLE CHECK FIRST: If name contains both "ET AL" and a role word, or role word and NO, it's a header
    extracted_upper = extracted_name.upper()
    has_et_al = 'ET AL' in extracted_upper or 'ETAL' in extracted_upper.replace(' ', '')
    has_role_word = any(role in extracted_upper for role in ['PETITIONER', 'RESPONDENT', 'APPELLANT', 'APPELLEE', 'PLAINTIFF', 'DEFENDANT'])
    has_no = 'NO.' in extracted_upper or ' NO ' in extracted_upper or extracted_upper.endswith(' NO')
    
    # ENHANCED: If the case name contains "ET AL" WITH a role word, it's almost certainly a header
    # BUT: "ET AL" alone can be legitimate (e.g., "Smith et al. v. Jones")
    # Only reject if it's clearly a header pattern (ET AL + role word, or role word + NO)
    if has_et_al and has_role_word:
        logger.warning(f"[CONTAMINATION-FILTER] REJECTED header (ET AL + role word): '{extracted_name}'")
        return True
    
    # If it has a role word and NO, it's almost certainly a header
    if has_role_word and has_no:
        logger.warning(f"[CONTAMINATION-FILTER] REJECTED header (role word + NO): '{extracted_name}' (has_role_word={has_role_word}, has_no={has_no})")
        return True
    
    # If it has ET AL and a role word, it's almost certainly a header
    if has_et_al and has_role_word:
        logger.warning(f"[CONTAMINATION-FILTER] REJECTED header (ET AL + role word): '{extracted_name}' (has_et_al={has_et_al}, has_role_word={has_role_word})")
        return True
    
    # THEN: Check detailed patterns
    header_patterns = [
        # Pattern 1: "ET AL., Petitioners" anywhere in the name
        r'ET\s+AL\.?\s*,?\s*(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\b',  # "ET AL., Petitioners"
        # Pattern 2: "Respondent. NO" or "Petitioners, NO" (with or without number)
        r'\b(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*[,\.]\s*NO\b',  # "Respondent. NO" or "Petitioners, NO"
        # Pattern 3: "ET AL., Petitioners, v. ... Respondent. NO" pattern (full header format)
        r'ET\s+AL\.?\s*,?\s*(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\b.*\b(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*[,\.]\s*NO\b',  # "ET AL., Petitioners, v. ... Respondent. NO"
        # Pattern 4: ENHANCED - Catch "ET AL., Petitioners, v. ... Respondent. NO" with any spacing
        r'ET\s+AL\.?\s*,?\s*(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*,?\s*v\.\s+.*\b(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*[,\.]\s*NO',  # "ET AL., Petitioners, v. ... Respondent. NO"
        # Pattern 5: Case names that END with "Respondent. NO" or similar
        r'\b(?:Petitioners?|Appellants?|Plaintiffs?|Appellees?|Respondents?)\s*[,\.]\s*NO\.?\s*$',  # Ends with "Respondent. NO" or "Petitioners, NO"
    ]
    for pattern in header_patterns:
        if re.search(pattern, extracted_name, re.IGNORECASE):
            logger.warning(f"[CONTAMINATION-FILTER] REJECTED header pattern in extracted name: '{extracted_name}' (matched pattern: {pattern})")
            return True
    
    # Normalize both for comparison (case-insensitive, ignore punctuation, handle abbreviations)
    def normalize_for_comparison(name):
        normalized = name.lower()
        # Remove role words and docket numbers for comparison
        normalized = re.sub(r'\bet\s+al\.?\b', '', normalized)
        normalized = re.sub(r'\b(?:petitioners?|appellants?|plaintiffs?|appellees?|respondents?)\b', '', normalized)
        normalized = re.sub(r'\bno\.?\s*\d+', '', normalized)
        
        # Normalize common abbreviations to full forms for better comparison
        # This handles cases where one system uses "Inc." and another uses "Incorporated"
        abbreviation_map = {
            r'\binc\.?\b': 'incorporated',
            r'\bcorp\.?\b': 'corporation',
            r'\bco\.?\b': 'company',
            r'\bllc\.?\b': 'limited liability company',
            r'\bltd\.?\b': 'limited',
            r'\blp\.?\b': 'limited partnership',
            r'\bassoc\.?\b': 'association',
            r'\bauto\.?\b': 'automobile',
            r'\bins\.?\b': 'insurance',
            r'\bmfg\.?\b': 'manufacturing',
            r'\bmgmt\.?\b': 'management',
        }
        for abbrev, full_form in abbreviation_map.items():
            normalized = re.sub(abbrev, full_form, normalized)
        
        normalized = re.sub(r'[,\.\s]+', ' ', normalized)
        normalized = normalized.strip()
        return normalized
    
    extracted_normalized = normalize_for_comparison(extracted_name)
    primary_normalized = normalize_for_comparison(document_primary_case_name)
    
    # CRITICAL: Use similarity scoring instead of simple containment checks
    # Different systems can have different case names for the same case (abbreviations vs full names)
    # We should only reject if similarity is VERY high (>= 0.95), indicating it's likely the same case
    
    def calculate_similarity(name1: str, name2: str) -> float:
        """Calculate similarity between two normalized case names."""
        if not name1 or not name2:
            return 0.0
        
        # Exact match
        if name1 == name2:
            return 1.0
        
        # Check if one contains the other (but require high overlap)
        if name1 in name2:
            # Calculate overlap ratio
            overlap_ratio = len(name1) / len(name2) if len(name2) > 0 else 0.0
            return overlap_ratio
        elif name2 in name1:
            overlap_ratio = len(name2) / len(name1) if len(name1) > 0 else 0.0
            return overlap_ratio
        
        # Word-based similarity (Jaccard similarity)
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        if union == 0:
            return 0.0
        
        word_similarity = intersection / union
        
        # Sequence similarity (handles abbreviations better)
        from difflib import SequenceMatcher
        seq_similarity = SequenceMatcher(None, name1, name2).ratio()
        
        # Combined similarity (weighted average)
        # Word similarity is more important for case names
        combined = 0.6 * word_similarity + 0.4 * seq_similarity
        
        return combined
    
    similarity = calculate_similarity(extracted_normalized, primary_normalized)
    
    # Strategy 1: Exact match after normalization (definitely contamination)
    if extracted_normalized == primary_normalized:
        logger.warning(f"[CONTAMINATION-FILTER] Exact match: '{extracted_name}' == '{document_primary_case_name}' (similarity: {similarity:.2f})")
        return True
    
    # Strategy 2: Very high similarity (>= 0.95) - likely the same case
    # This catches cases like "Erickson v. Pharmacia LLC" vs "Erickson v. Pharmacia, LLC"
    if similarity >= 0.95:
        logger.warning(f"[CONTAMINATION-FILTER] Very high similarity: '{extracted_name}' ~= '{document_primary_case_name}' (similarity: {similarity:.2f})")
        return True
    
    # Strategy 3: Check if BOTH parties match AND similarity is high (>= 0.85)
    # This handles cases where both plaintiff and defendant match, but formatting differs
    primary_parts = primary_normalized.split(' v ')
    if len(primary_parts) == 2:
        plaintiff = primary_parts[0].strip()
        defendant = primary_parts[1].strip()
        
        if plaintiff and defendant:
            # Check if both parties appear in extracted name
            plaintiff_match = plaintiff in extracted_normalized
            defendant_match = defendant in extracted_normalized
            
            # Only reject if BOTH parties match AND overall similarity is high
            # This prevents false positives from cases that just share a common party name
            if plaintiff_match and defendant_match and similarity >= 0.85:
                logger.warning(f"[CONTAMINATION-FILTER] Both parties match with high similarity: '{extracted_name}' ~= '{document_primary_case_name}' (similarity: {similarity:.2f})")
                return True
    
    # Strategy 4: If similarity is moderate (0.7-0.95), check if it's likely contamination
    # by checking if extracted name contains the full primary name structure
    if 0.7 <= similarity < 0.95:
        # Check if primary name is contained in extracted name (but require high similarity)
        if primary_normalized in extracted_normalized:
            # Additional check: make sure it's not just a partial match
            # If extracted name is much longer, it might be a different case
            length_ratio = len(extracted_normalized) / len(primary_normalized) if len(primary_normalized) > 0 else 1.0
            if length_ratio <= 1.5:  # Extracted name shouldn't be much longer
                logger.warning(f"[CONTAMINATION-FILTER] Containment with high similarity: '{extracted_name}' contains '{document_primary_case_name}' (similarity: {similarity:.2f})")
                return True
    
    # If similarity is low (< 0.7), it's likely a different case, even if they share some words
    # Don't reject - different systems can have different case names for the same case
    logger.debug(f"[CONTAMINATION-FILTER] Similarity too low to reject: '{extracted_name}' vs '{document_primary_case_name}' (similarity: {similarity:.2f})")
    return False


__all__ = [
    'extract_case_name_with_strict_isolation',
    'apply_unified_extraction_to_all_citations',
]
