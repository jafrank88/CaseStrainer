#!/usr/bin/env python3
"""
Test script to verify the updated clustering logic in UnifiedCitationProcessorV2
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2

def test_clustering_logic():
    """Test the updated clustering logic with sample text"""
    
    # Test text with multiple citations
    test_text = """A federal court may ask this court to answer a question of Washington law 
when a resolution of that question is necessary to resolve a case before the 
federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d
72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review
de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 
(2011). We also review the meaning of a statute de novo. Dep't of Ecology v.
Campbell & Gwinn, LLC, 146 Wn.2d 1, 9 (2003)"""
    
    print("Testing clustering logic with sample text:")
    print("=" * 60)
    print(test_text)
    print("=" * 60)
    
    # Initialize processor
    processor = UnifiedCitationProcessorV2()
    
    # Process the text
    results = processor.process_text(test_text)
    
    print(f"\nFound {len(results)} citation groups:")
    print("-" * 60)
    
    cluster_count = 0
    single_count = 0
    citation_count = 0
    
    for i, result in enumerate(results, 1):
        if getattr(result, 'is_cluster', False):
            cluster_count += 1
            citation_count += len(result.cluster_members)
            print(f"\nGroup {i}: CLUSTER")
            print(f"  Citations: {result.cluster_members}")
            print(f"  Cluster Size: {len(result.cluster_members)}")
            print(f"  Extracted Case Name: {result.extracted_case_name}")
            print(f"  Extracted Date: {result.extracted_date}")
            print(f"  Confidence: {result.confidence}")
        else:
            single_count += 1
            citation_count += 1
            print(f"\nGroup {i}: SINGLE")
            print(f"  Citation: {result.citation}")
            print(f"  Extracted Case Name: {result.extracted_case_name}")
            print(f"  Extracted Date: {result.extracted_date}")
            print(f"  Confidence: {result.confidence}")
    
    print(f"\nSummary:")
    print(f"  Total citation groups: {len(results)}")
    print(f"  Clusters: {cluster_count}")
    print(f"  Singles: {single_count}")
    print(f"  Total citations (including all in clusters): {citation_count}")

if __name__ == "__main__":
    test_clustering_logic() 