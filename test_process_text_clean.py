"""
Test to reproduce the exact error in process_text
"""

import sys
import asyncio
sys.path.insert(0, 'D:/dev/casestrainer/src')

# Enable logging to see all errors
import logging
logging.basicConfig(level=logging.DEBUG)

async def test_process_text_clean_pipeline():
    """Test the exact clean pipeline call from process_text"""
    
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
    
    # Create processor
    processor = UnifiedCitationProcessorV2()
    
    # Set document_primary_case_name like process_text does
    processor.document_primary_case_name = None
    
    test_text = "Doe v. City of New York, 2022 WL 15153410, 855 F.2d 569 (1988)."
    
    print("Testing clean pipeline import and call...")
    
    # This is the exact code from process_text
    try:
        from src.clean_extraction_pipeline import extract_citations_clean
        
        print(f"[UNIFIED-DEBUG] About to call extract_citations_clean with {len(test_text)} chars")
        citations = extract_citations_clean(test_text, document_primary_case_name=processor.document_primary_case_name)
        print(f"[UNIFIED_PIPELINE] Clean pipeline extracted {len(citations)} citations with 100% accuracy")
        
        # Check if citations have the series fix
        print("\nChecking series citation fix:")
        for cit in citations:
            print(f"  - {cit.citation}: {cit.extracted_case_name}")
            if hasattr(cit, 'metadata') and cit.metadata:
                print(f"    Metadata: {cit.metadata}")
        
    except Exception as e:
        print(f"[UNIFIED_PIPELINE] Clean pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        print(f"[UNIFIED-DEBUG] Exception type: {type(e).__name__}")

# Run the test
asyncio.run(test_process_text_clean_pipeline())
