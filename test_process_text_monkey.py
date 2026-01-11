"""
Test to check if clean pipeline is actually being called in process_text
"""

import sys
import asyncio
sys.path.insert(0, 'D:/dev/casestrainer/src')

# Monkey patch to add logging
original_extract = None

def logged_extract_citations_clean(text, document_primary_case_name=None):
    print(f"[MONKEY-PATCH] extract_citations_clean called with {len(text)} chars")
    print(f"[MONKEY-PATCH] document_primary_case_name: {document_primary_case_name}")
    result = original_extract(text, document_primary_case_name)
    print(f"[MONKEY-PATCH] extract_citations_clean returning {len(result)} citations")
    for cit in result:
        print(f"[MONKEY-PATCH]   - {cit.citation}: {cit.extracted_case_name}")
    return result

async def test_process_text_with_logging():
    """Test process_text with monkey-patched clean pipeline"""
    
    # Import and patch
    import src.clean_extraction_pipeline
    global original_extract
    original_extract = src.clean_extraction_pipeline.extract_citations_clean
    src.clean_extraction_pipeline.extract_citations_clean = logged_extract_citations_clean
    
    try:
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        print("Creating processor...")
        processor = UnifiedCitationProcessorV2()
        
        test_text = "Doe v. City of New York, 2022 WL 15153410, 855 F.2d 569 (1988)."
        
        print("\nRunning process_text...")
        result = await processor.process_text(test_text)
        
        print("\nFinal results:")
        citations = result.get('citations', [])
        for cit in citations:
            print(f"  - {cit.citation}: {cit.extracted_case_name} (method: {cit.method})")
            
    finally:
        # Restore original
        src.clean_extraction_pipeline.extract_citations_clean = original_extract

# Run the test
asyncio.run(test_process_text_with_logging())
