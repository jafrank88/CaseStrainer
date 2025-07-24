#!/usr/bin/env python3
"""
Test script to test the integrated clustering with the standard test paragraph.
"""

import sys
import os
sys.path.append('src')

import logging
logging.basicConfig(level=logging.DEBUG)

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
from src.citation_clustering import group_citations_into_clusters

def test_integrated_clustering():
    """Test the integrated clustering with the standard test paragraph."""
    
    # Standard test paragraph
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    print("=== TESTING INTEGRATED CLUSTERING ===")
    print(f"Test text: {test_text}")
    print()
    
    # Initialize processor
    config = ProcessingConfig(
        debug_mode=True,
        extract_case_names=True,
        extract_dates=True,
        enable_verification=True
    )
    
    processor = UnifiedCitationProcessorV2(config)
    results = processor.process_text(test_text)
    
    print(f"Found {len(results)} citations")
    
    # Test clustering
    clusters = group_citations_into_clusters(results, original_text=test_text)
    
    print(f"\n=== CLUSTERS ===")
    print(f"Found {len(clusters)} clusters")
    
    for i, cluster in enumerate(clusters, 1):
        print(f"\nCluster {i}:")
        print(f"  Cluster ID: {cluster.get('cluster_id')}")
        print(f"  Case name: {cluster.get('extracted_case_name')}")
        print(f"  Year: {cluster.get('extracted_date')}")
        print(f"  Size: {cluster.get('size')}")
        print(f"  Citations: {[c.get('citation') for c in cluster.get('citations', [])]}")
        print(f"  Has parallel citations: {cluster.get('has_parallel_citations')}")

    print("\n=== CITATION DETAILS ===")
    for i, citation in enumerate(results):
        print(f"Citation {i+1}: {citation.citation}")
        print(f"  Extracted case name: {citation.extracted_case_name}")
        print(f"  Extracted date: {citation.extracted_date}")
        print(f"  Canonical name: {citation.canonical_name}")
        print(f"  Canonical date: {citation.canonical_date}")
        print(f"  Verified: {citation.verified}")
        print(f"  URL: {citation.url}")
        print(f"  Is in cluster: {citation.metadata.get('is_in_cluster', False) if citation.metadata else False}")
        print()

    # Expected clusters from memory for the standard test paragraph
    expected_clusters = [
        {
            'case_name': 'Convoyant, LLC v. DeepThink, LLC',
            'citations': ['200 Wn.2d 72', '514 P.3d 643'],
            'year': '2022',
        },
        {
            'case_name': 'Carlson v. Glob. Client Sols., LLC',
            'citations': ['171 Wn.2d 486', '256 P.3d 321'],
            'year': '2011',
        },
        {
            'case_name': 
                
                "Dep't of Ecology v. Campbell & Gwinn, LLC",
            'citations': ['146 Wn.2d 1', '43 P.3d 4'],
            'year': '2003',
        },
    ]

    print("\n=== EXPECTED CLUSTERS ===")
    for i, cluster in enumerate(expected_clusters, 1):
        print(f"\nExpected Cluster {i}:")
        print(f"  Case name: {cluster['case_name']}")
        print(f"  Year: {cluster['year']}")
        print(f"  Citations: {cluster['citations']}")

    # Print a comparison of actual vs expected clusters
    print("\n=== COMPARISON ===")
    for i, (actual, expected) in enumerate(zip(clusters, expected_clusters), 1):
        actual_citations = sorted([c.get('citation') for c in actual.get('citations', [])])
        expected_citations = sorted(expected['citations'])
        print(f"\nCluster {i}:")
        print(f"  Actual citations:   {actual_citations}")
        print(f"  Expected citations: {expected_citations}")
        print(f"  Match: {actual_citations == expected_citations}")

if __name__ == "__main__":
    test_integrated_clustering() 