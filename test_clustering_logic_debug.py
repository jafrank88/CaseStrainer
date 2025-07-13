#!/usr/bin/env python3
"""
Debug script to test the clustering logic directly with citations that have parallel_citations set.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig, CitationResult

def test_clustering_logic_debug():
    """Test the clustering logic directly with parallel citations."""
    
    print("🧪 Testing clustering logic directly...")
    
    # Create test citations with parallel_citations set
    citations = [
        CitationResult(
            citation="200 Wn.2d",
            extracted_case_name="N/A",
            extracted_date="2022",
            parallel_citations=[]
        ),
        CitationResult(
            citation="200 Wn.2d 72",
            extracted_case_name="N/A", 
            extracted_date="2022",
            parallel_citations=["514 P.3d 643"]
        ),
        CitationResult(
            citation="514 P.3d 643",
            extracted_case_name="N/A",
            extracted_date="2022", 
            parallel_citations=["200 Wn.2d 72"]
        ),
        CitationResult(
            citation="171 Wn.2d",
            extracted_case_name="N/A",
            extracted_date="2011",
            parallel_citations=[]
        ),
        CitationResult(
            citation="171 Wn.2d 486",
            canonical_name="Carlsen v. Global Client Solutions, LLC",
            canonical_date="2011-05-12",
            extracted_case_name="N/A",
            extracted_date="2011",
            parallel_citations=["256 P.3d 321"]
        ),
        CitationResult(
            citation="256 P.3d 321",
            canonical_name="Carlsen v. Global Client Solutions, LLC", 
            canonical_date="2011-05-12",
            extracted_case_name="N/A",
            extracted_date="2011",
            parallel_citations=["171 Wn.2d 486"]
        ),
        CitationResult(
            citation="146 Wn.2d",
            extracted_case_name="N/A",
            extracted_date="2003",
            parallel_citations=[]
        ),
        CitationResult(
            citation="146 Wn.2d 1",
            canonical_name="Department of Ecology v. Campbell & Gwinn, L.L.C.",
            canonical_date="2002-03-28",
            extracted_case_name="N/A",
            extracted_date="2003",
            parallel_citations=["43 P.3d 4"]
        ),
        CitationResult(
            citation="43 P.3d 4",
            canonical_name="State, Dept. of Ecology v. Campbell & Gwinn",
            canonical_date="2002-03-28",
            extracted_case_name="N/A",
            extracted_date="2003",
            parallel_citations=["146 Wn.2d 1"]
        )
    ]
    
    print(f"Input citations: {len(citations)}")
    for i, citation in enumerate(citations, 1):
        print(f"  {i}. '{citation.citation}' - parallels: {citation.parallel_citations}")
    
    # Initialize processor
    config = ProcessingConfig(debug_mode=True)
    processor = UnifiedCitationProcessorV2(config)
    
    # Test clustering logic
    print("\n🔗 Testing clustering logic...")
    clusters = processor.group_citations_into_clusters(citations)
    
    print(f"\n📦 Clustering results: {len(clusters)} clusters")
    for i, cluster in enumerate(clusters, 1):
        print(f"\n  Cluster {i}:")
        print(f"    Case: {cluster.get('canonical_name', 'N/A')}")
        print(f"    Date: {cluster.get('canonical_date', 'N/A')}")
        print(f"    Size: {cluster.get('size', 0)}")
        print(f"    Has parallel: {cluster.get('has_parallel_citations', False)}")
        print(f"    Citations:")
        for j, citation in enumerate(cluster.get('citations', []), 1):
            print(f"      {j}. {citation.get('citation')} (parallels: {citation.get('parallel_citations', [])})")
    
    # Check if we got the expected 3 clusters
    expected_clusters = 3
    if len(clusters) == expected_clusters:
        print(f"\n✅ SUCCESS: Got {len(clusters)} clusters as expected!")
    else:
        print(f"\n❌ FAILURE: Got {len(clusters)} clusters, expected {expected_clusters}")
    
    # Check if parallel citations are in the same cluster
    print(f"\n🎯 Checking parallel citation grouping...")
    parallel_pairs = [
        ("200 Wn.2d 72", "514 P.3d 643"),
        ("171 Wn.2d 486", "256 P.3d 321"), 
        ("146 Wn.2d 1", "43 P.3d 4")
    ]
    
    for pair1, pair2 in parallel_pairs:
        cluster1 = None
        cluster2 = None
        
        for i, cluster in enumerate(clusters):
            cluster_citations = [c.get('citation') for c in cluster.get('citations', [])]
            if pair1 in cluster_citations:
                cluster1 = i
            if pair2 in cluster_citations:
                cluster2 = i
        
        if cluster1 == cluster2 and cluster1 is not None:
            print(f"  ✅ {pair1} and {pair2} are in the same cluster ({cluster1})")
        else:
            print(f"  ❌ {pair1} (cluster {cluster1}) and {pair2} (cluster {cluster2}) are in different clusters")

if __name__ == "__main__":
    test_clustering_logic_debug() 