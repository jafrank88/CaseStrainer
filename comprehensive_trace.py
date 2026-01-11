"""
Comprehensive test to trace citations through the entire pipeline
"""

import sys
import asyncio
sys.path.insert(0, 'D:/dev/casestrainer/src')

async def comprehensive_trace():
    """Trace citations through each step of the pipeline"""
    
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
    
    print("Creating processor...")
    processor = UnifiedCitationProcessorV2()
    
    test_text = "Doe v. City of New York, 2022 WL 15153410, 855 F.2d 569 (1988)."
    
    # Step 1: Clean pipeline
    print("\n" + "="*60)
    print("STEP 1: CLEAN PIPELINE")
    print("="*60)
    
    from src.clean_extraction_pipeline import extract_citations_clean
    citations = extract_citations_clean(test_text)
    
    print(f"After clean pipeline:")
    for i, cit in enumerate(citations):
        print(f"  {i+1}. {cit.citation}: '{cit.extracted_case_name}' (type: {type(cit).__name__})")
    
    # Step 2: Enhancement loop (should skip due to our fix)
    print("\n" + "="*60)
    print("STEP 2: ENHANCEMENT LOOP")
    print("="*60)
    
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
    
    print(f"After enhancement loop:")
    for i, cit in enumerate(citations):
        print(f"  {i+1}. {cit.citation}: '{cit.extracted_case_name}'")
    
    # Step 3: Parallel verification
    print("\n" + "="*60)
    print("STEP 3: PARALLEL VERIFICATION")
    print("="*60)
    
    processor.propagate_canonical_to_cluster(citations)
    
    print(f"After parallel verification:")
    for i, cit in enumerate(citations):
        print(f"  {i+1}. {cit.citation}: '{cit.extracted_case_name}'")
    
    # Step 4: Clustering
    print("\n" + "="*60)
    print("STEP 4: CLUSTERING")
    print("="*60)
    
    from src.unified_clustering_master import cluster_citations_unified_master
    clusters = cluster_citations_unified_master(
        citations,
        test_text,
        enable_verification=True,
        request_id=None,
        progress_callback=None
    )
    
    print(f"After clustering (checking original objects):")
    for i, cit in enumerate(citations):
        print(f"  {i+1}. {cit.citation}: '{cit.extracted_case_name}'")
    
    print(f"\nChecking cluster data (dicts):")
    for cluster in clusters:
        for cit in cluster.get('citations', []):
            if isinstance(cit, dict):
                citation_text = cit.get('citation', 'Unknown')
                case_name = cit.get('extracted_case_name', 'N/A')
            else:
                citation_text = getattr(cit, 'citation', 'Unknown')
                case_name = getattr(cit, 'extracted_case_name', 'N/A')
            print(f"  - {citation_text}: '{case_name}' (type: {type(cit).__name__})")

# Run the test
asyncio.run(comprehensive_trace())
