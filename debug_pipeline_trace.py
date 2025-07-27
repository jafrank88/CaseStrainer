#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
from src.models import ProcessingConfig

def debug_pipeline_trace():
    """Debug the entire processing pipeline to trace case names."""
    
    # Test text with both citations
    test_text = """
    Municipal corporations are not typically within the zone of interest of individual constitutional guarantees. 
    See, e.g., Lakehaven Water & Sewer Dist. v. City of Fed. Way, 195 Wn.2d 742, 773, 466 P.3d 213 (2020) 
    (sewer and water district lacked standing to challenge constitutional issues).
    
    The State has a duty to actively provide criminal defense services to those who cannot afford it. 
    See Davison v. State, 196 Wn.2d 285, 293, 466 P.3d 231 (2020) 
    ("The State plainly has a duty to provide indigent defense").
    """
    
    # Configure processor
    config = ProcessingConfig(
        extract_case_names=True,
        enable_verification=False
    )
    processor = UnifiedCitationProcessorV2(config)
    
    print("=== PIPELINE TRACE ===")
    
    # Step 1: Extract citations
    print("\n1. EXTRACTING CITATIONS")
    citations = processor._extract_with_regex(test_text)
    print(f"Found {len(citations)} citations")
    
    for i, citation in enumerate(citations):
        print(f"   {i+1}. {citation.citation}")
        print(f"      Start: {citation.start_index}, End: {citation.end_index}")
        print(f"      Extracted case name: {citation.extracted_case_name}")
        print()
    
    # Step 2: Parallel citation detection
    print("\n2. PARALLEL CITATION DETECTION")
    citations_after_parallel = processor._detect_parallel_citations(citations, test_text)
    
    for i, citation in enumerate(citations_after_parallel):
        print(f"   {i+1}. {citation.citation}")
        print(f"      Extracted case name: {citation.extracted_case_name}")
        print(f"      Is parallel: {citation.is_parallel}")
        print(f"      Cluster ID: {getattr(citation, 'cluster_id', 'None')}")
        print()
    
    # Step 3: Clustering
    print("\n3. CLUSTERING")
    from src.citation_clustering import group_citations_into_clusters
    clusters = group_citations_into_clusters(citations_after_parallel, original_text=test_text)
    
    print(f"Created {len(clusters)} clusters")
    for i, cluster in enumerate(clusters):
        print(f"   Cluster {i+1}:")
        for citation in cluster.get('citations', []):
            print(f"      {citation.get('citation')}: {citation.get('extracted_case_name')}")
        print()

if __name__ == "__main__":
    debug_pipeline_trace() 