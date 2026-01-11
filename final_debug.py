"""
Final debug test to check the full process
"""

import sys
import asyncio
sys.path.insert(0, 'D:/dev/casestrainer/src')

async def final_debug():
    """Final debug to see exactly where the name is lost"""
    
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
    
    print("Creating processor...")
    processor = UnifiedCitationProcessorV2()
    
    test_text = "Doe v. City of New York, 2022 WL 15153410, 855 F.2d 569 (1988)."
    
    # Patch process_text to add logging at key points
    import src.unified_citation_processor_v2
    import types
    
    original_process_text = processor.process_text
    
    def logged_process_text(self, text):
        # Call original but capture intermediate results
        async def inner():
            # Step 1: Clean pipeline
            from src.clean_extraction_pipeline import extract_citations_clean
            self.document_primary_case_name = None
            citations = extract_citations_clean(text, document_primary_case_name=self.document_primary_case_name)
            
            print("\n[AFTER CLEAN PIPELINE]")
            for i, cit in enumerate(citations):
                print(f"  {i+1}. {cit.citation}: '{cit.extracted_case_name}'")
            
            # Step 2: Enhancement loop (should skip due to our fix)
            self._update_progress(30, "Enhancing", "Enhancing citation data with case names and dates")
            extraction_cache = {}
            
            for c in citations:
                current_name = getattr(c, "extracted_case_name", None) or ""
                citation_method = getattr(c, "method", None)
                
                if current_name and citation_method == "clean_pipeline_v1":
                    is_series_citation = (hasattr(c, 'metadata') and 
                                         c.metadata and 
                                         c.metadata.get('is_series_citation', False))
                    
                    if current_name != "N/A":
                        print(f"  Keeping '{current_name}' for {c.citation} (not series)")
                    elif is_series_citation:
                        print(f"  Keeping 'N/A' for series citation {c.citation}")
            
            print("\n[AFTER ENHANCEMENT LOOP]")
            for i, cit in enumerate(citations):
                print(f"  {i+1}. {cit.citation}: '{cit.extracted_case_name}'")
            
            # Step 3: Parallel verification
            self.propagate_canonical_to_cluster(citations)
            
            print("\n[AFTER PARALLEL VERIFICATION]")
            for i, cit in enumerate(citations):
                print(f"  {i+1}. {cit.citation}: '{cit.extracted_case_name}'")
            
            # Step 4: Clustering
            from src.unified_clustering_master import cluster_citations_unified_master
            clusters = cluster_citations_unified_master(
                citations,
                text,
                enable_verification=True,
                request_id=None,
                progress_callback=self._update_progress
            )
            
            print("\n[AFTER CLUSTERING - before return]")
            for i, cit in enumerate(citations):
                print(f"  {i+1}. {cit.citation}: '{cit.extracted_case_name}'")
            
            return {'citations': citations, 'clusters': clusters}
        
        return inner()
    
    processor.process_text = types.MethodType(logged_process_text, processor)
    
    try:
        print("\nRunning process_text with logging...")
        result = await processor.process_text(test_text)
        
        print("\n[FINAL RETURNED RESULTS]")
        citations = result.get('citations', [])
        for i, cit in enumerate(citations):
            print(f"  {i+1}. {cit.citation}: '{cit.extracted_case_name}'")
            
    finally:
        processor.process_text = original_process_text

# Run the test
asyncio.run(final_debug())
