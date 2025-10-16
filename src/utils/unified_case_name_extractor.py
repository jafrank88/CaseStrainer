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
from typing import Optional, List, Any
from src.utils.strict_context_isolator import (
    find_all_citation_positions,
    get_strict_context_for_citation,
    extract_case_name_from_strict_context
)

logger = logging.getLogger(__name__)


def extract_case_name_with_strict_isolation(
    text: str,
    citation_text: str,
    citation_start: int,
    citation_end: int,
    all_citations: Optional[List[Any]] = None
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
        
        # Get strictly isolated context (stops at previous citation boundary)
        strict_context = get_strict_context_for_citation(
            text, 
            citation_start, 
            citation_end, 
            all_positions, 
            max_lookback=200
        )
        
        logger.debug(f"[UNIFIED-EXTRACT] Isolated context for {citation_text}: {len(strict_context)} chars")
        
        # Extract case name from isolated context
        case_name = extract_case_name_from_strict_context(strict_context, citation_text)
        
        if case_name:
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


__all__ = [
    'extract_case_name_with_strict_isolation',
    'apply_unified_extraction_to_all_citations',
]
