"""
Test to trace where N/A is being lost
"""

import sys
import asyncio
sys.path.insert(0, 'D:/dev/casestrainer/src')

async def trace_n_a_loss():
    """Trace exactly where N/A is being lost"""
    
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
    
    print("Creating processor...")
    processor = UnifiedCitationProcessorV2()
    
    test_text = "Doe v. City of New York, 2022 WL 15153410, 855 F.2d 569 (1988)."
    
    # Patch the clean pipeline to add tracking
    import src.clean_extraction_pipeline
    original_extract = src.clean_extraction_pipeline.extract_citations_clean
    
    def tracked_extract(text, document_primary_case_name=None):
        result = original_extract(text, document_primary_case_name)
        print("\n[AFTER CLEAN PIPELINE]")
        for i, cit in enumerate(result):
            print(f"  {i+1}. {cit.citation}: '{cit.extracted_case_name}'")
            if hasattr(cit, 'metadata') and cit.metadata:
                print(f"     metadata: {cit.metadata}")
            # Add a tracking flag
            if not hasattr(cit, 'metadata') or cit.metadata is None:
                cit.metadata = {}
            cit.metadata['_clean_pipeline_result'] = True
        return result
    
    src.clean_extraction_pipeline.extract_citations_clean = tracked_extract
    
    # Patch clustering to check before and after
    import src.unified_clustering_master
    original_cluster = src.unified_clustering_master.UnifiedClusteringMaster.cluster_citations
    
    def tracked_cluster(self, citations, original_text="", enable_verification=True, request_id=None, progress_callback=None):
        print("\n[BEFORE CLUSTERING]")
        for i, cit in enumerate(citations):
            print(f"  {i+1}. {cit.citation}: '{cit.extracted_case_name}'")
            if hasattr(cit, 'metadata') and cit.metadata:
                if cit.metadata.get('is_series_citation'):
                    print(f"     *** IS SERIES CITATION ***")
        
        result = original_cluster(self, citations, original_text, enable_verification, request_id, progress_callback)
        
        print("\n[AFTER CLUSTERING]")
        for cluster in result:
            for cit in cluster.get('citations', []):
                print(f"  {cit.citation}: '{cit.extracted_case_name}'")
        
        return result
    
    src.unified_clustering_master.UnifiedClusteringMaster.cluster_citations = tracked_cluster
    
    try:
        print("\nRunning process_text...")
        result = await processor.process_text(test_text)
        
        print("\n[FINAL RESULTS]")
        citations = result.get('citations', [])
        for i, cit in enumerate(citations):
            print(f"  {i+1}. {cit.citation}: '{cit.extracted_case_name}'")
            if hasattr(cit, 'metadata') and cit.metadata:
                if cit.metadata.get('is_series_citation'):
                    print(f"     *** WAS SERIES CITATION ***")
                    
    finally:
        # Restore
        src.clean_extraction_pipeline.extract_citations_clean = original_extract
        src.unified_clustering_master.UnifiedClusteringMaster.cluster_citations = original_cluster

# Run the test
asyncio.run(trace_n_a_loss())
