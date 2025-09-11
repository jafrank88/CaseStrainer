#!/usr/bin/env python3
"""
Debug script to test the exact API processing path and see where clustering is going wrong.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_sync_processor import EnhancedSyncProcessor, ProcessingOptions

def debug_api_processing():
    """Debug the exact API processing path."""
    
    # The test text
    test_text = """We review a trial court's findings of fact for substantial evidence, generally 
deferring to the trier of fact on questions of witness credibility, conflicting 
testimony, and persuasiveness of the evidence. In re Vulnerable Adult Petition 
for Knight, 178 Wn. App. 929, 936-37, 317 P.3d 1068 (2014). Evidence is 
substantial when sufficient to persuade a fair-minded person of the truth of the 
matter asserted. In re Marriage of Black, 188 Wn.2d 114, 127, 392 P.3d 1041 
(2017). "Competent evidence sufficient to support the trial court's decision to 
grant . . . a domestic violence protection order may contain hearsay or be wholly 
documentary." Blackmon v. Blackmon, 155 Wn. App. 715, 722, 230 P.3d 233 
(2010)."""
    
    print("=== Debugging API Processing Path ===")
    print(f"Test text length: {len(test_text)} characters")
    print()
    
    # Create processor with same options as API
    options = ProcessingOptions(
        enable_async_verification=True,
        enable_enhanced_verification=True,
        enable_confidence_scoring=True
    )
    processor = EnhancedSyncProcessor(options)
    
    # Test each step of the API processing
    print("=== Step 1: Citation Extraction ===")
    citations = processor._extract_citations_fast(test_text)
    print(f"Found {len(citations)} citations")
    
    for i, citation in enumerate(citations):
        print(f"Citation {i+1}: {citation}")
        if hasattr(citation, 'extracted_case_name'):
            print(f"  Case Name: {getattr(citation, 'extracted_case_name', 'None')}")
        if hasattr(citation, 'extracted_date'):
            print(f"  Date: {getattr(citation, 'extracted_date', 'None')}")
        print()
    
    print("=== Step 2: Citation Normalization ===")
    normalized_citations = processor._normalize_citations_local(citations, test_text)
    print(f"Normalized {len(normalized_citations)} citations")
    
    print("=== Step 3: Name/Year Extraction ===")
    enhanced_citations = processor._extract_names_years_local(normalized_citations, test_text)
    print(f"Enhanced {len(enhanced_citations)} citations")
    
    for i, citation in enumerate(enhanced_citations):
        print(f"Enhanced Citation {i+1}: {citation}")
        if isinstance(citation, dict):
            print(f"  Case Name: {citation.get('extracted_case_name', 'None')}")
            print(f"  Date: {citation.get('extracted_date', 'None')}")
        else:
            print(f"  Case Name: {getattr(citation, 'extracted_case_name', 'None')}")
            print(f"  Date: {getattr(citation, 'extracted_date', 'None')}")
        print()
    
    print("=== Step 4: Clustering ===")
    clusters = processor._cluster_citations_local(enhanced_citations, test_text, "debug")
    print(f"Created {len(clusters)} clusters")
    
    for i, cluster in enumerate(clusters):
        print(f"Cluster {i+1}: {cluster.get('case_name', 'Unknown')} ({cluster.get('year', 'Unknown')})")
        print(f"  Size: {cluster.get('size', 0)} citations")
        print(f"  Citations: {cluster.get('citations', [])}")
        print()
    
    print("=== Step 5: Full Processing ===")
    result = processor.process_any_input_enhanced(test_text, 'text', {})
    
    if result.get('success'):
        citations_list = result.get('citations', [])
        clusters_list = result.get('clusters', [])
        
        print(f"✅ Full processing successful")
        print(f"📊 Found {len(citations_list)} citations")
        print(f"📊 Created {len(clusters_list)} clusters")
        
        print("\n=== Final Clusters ===")
        for i, cluster in enumerate(clusters_list):
            print(f"Final Cluster {i+1}: {cluster.get('case_name', 'Unknown')} ({cluster.get('year', 'Unknown')})")
            print(f"  Size: {cluster.get('size', 0)} citations")
            print(f"  Citations: {cluster.get('citations', [])}")
            print()
    else:
        print(f"❌ Full processing failed: {result.get('error')}")

if __name__ == "__main__":
    debug_api_processing()
