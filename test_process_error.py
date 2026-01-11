"""
Test to see what error happens in process_text when calling clean pipeline
"""

import sys
import asyncio
sys.path.insert(0, 'D:/dev/casestrainer/src')

async def test_process_text_error():
    """Test to see what error occurs when clean pipeline is called from process_text"""
    
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
    
    print("Creating processor...")
    processor = UnifiedCitationProcessorV2()
    
    test_text = "Doe v. City of New York, 2022 WL 15153410, 855 F.2d 569 (1988)."
    
    # Patch the clean pipeline call to catch any errors
    import src.unified_citation_processor_v2
    original_process = processor.process_text
    
    async def debug_process_text(self, text):
        print("\n[DEBUG] Starting process_text...")
        
        # Set document_primary_case_name
        self.document_primary_case_name = None
        
        try:
            from src.clean_extraction_pipeline import extract_citations_clean
            print(f"[DEBUG] About to call extract_citations_clean with {len(text)} chars")
            citations = extract_citations_clean(text, document_primary_case_name=self.document_primary_case_name)
            print(f"[DEBUG] Clean pipeline returned {len(citations)} citations")
            
            # Check the results
            for i, cit in enumerate(citations):
                print(f"  {i+1}. {cit.citation}: '{cit.extracted_case_name}'")
                
        except Exception as e:
            print(f"[ERROR] Clean pipeline failed: {e}")
            import traceback
            traceback.print_exc()
            # Fall back to regex extraction
            print("[DEBUG] Falling back to regex extraction...")
            citations = self._extract_with_regex_enhanced(text)
        
        print(f"[DEBUG] Total citations after extraction: {len(citations)}")
        
        # Return minimal result
        return {'citations': citations, 'clusters': []}
    
    processor.process_text = debug_process_text.__get__(processor, UnifiedCitationProcessorV2)
    
    try:
        print("\nRunning process_text with error handling...")
        result = await processor.process_text(test_text)
        
        print("\nFinal results:")
        for cit in result.get('citations', []):
            print(f"  - {cit.citation}: '{cit.extracted_case_name}'")
            
    finally:
        processor.process_text = original_process

# Run the test
asyncio.run(test_process_text_error())
