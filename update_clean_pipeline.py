
def extract_citations_clean(text: str, document_primary_case_name: Optional[str] = None) -> List[CitationResult]:
    """
    Main entry point for clean citation extraction.
    
    DEPRECATED: This function is deprecated. Use extract_citations_unified from unified_case_extraction_master.py instead.
    
    This function now delegates to the unified extraction master to reduce code duplication.
    
    Args:
        text: Document text
        document_primary_case_name: Optional document primary case name for contamination filtering
        
    Returns:
        List of CitationResult objects with extracted_case_name set using strict context isolation
    """
    import warnings
    warnings.warn(
        "extract_citations_clean is deprecated. Use extract_citations_unified from unified_case_extraction_master.py instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    print(f"extract_citations_clean CALLED with {len(text)} chars [DEPRECATED]")
    
    # Use the new unified function
    from src.unified_case_extraction_master import extract_citations_unified
    
    citations = extract_citations_unified(text, document_primary_case_name)
    
    # Add proprietary format marking for WL citations
    import re
    proprietary_count = 0
    for cit in citations:
        if not cit.verified:
            if re.search(r"\d{4}\s+WL\s+\d+", cit.citation) or re.search(r"Lexis\s+\d+", cit.citation, re.IGNORECASE):
                cit.verification_status = "proprietary_format"
                cit.verification_error = "Unverified due to proprietary format"
                proprietary_count += 1
    
    if proprietary_count > 0:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[PROPRIETARY] Marked {proprietary_count} WL/Lexis citations as unverified due to proprietary format")
    
    # Validate position data preservation
    missing_position_count = 0
    for i, cit in enumerate(citations):
        if cit.start_index is None or cit.end_index is None:
            missing_position_count += 1
            logger.warning(f"[CLEAN-PIPELINE] Missing position data for citation {i+1}: {cit.citation}")
    
    if missing_position_count > 0:
        logger.error(
            f"[CLEAN-PIPELINE] {missing_position_count} citations missing position data - parallel verification may fail"
        )
    else:
        logger.info(f"[CLEAN-PIPELINE] All {len(citations)} citations have valid position data")
    
    print(f"extract_citations_clean returning {len(citations)} citations (position data: {len(citations) - missing_position_count}/{len(citations)} valid) [DEPRECATED]")
    return citations
