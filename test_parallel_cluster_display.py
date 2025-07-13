#!/usr/bin/env python3
"""
Test to demonstrate parallel citation display functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

def test_parallel_citation_display():
    """Test that parallel citations from the same cluster are displayed together"""
    
    processor = UnifiedCitationProcessorV2()
    
    # Test with text that has parallel citations that should be grouped
    test_text = """The court considered several cases: Carlson v. Global Client Solutions, LLC, 171 Wn.2d 486, 256 P.3d 321 (2011) and Department of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 43 P.3d 4 (2003)."""
    
    print("Testing parallel citation display functionality...")
    print("=" * 80)
    
    # Process the text
    result = processor.process_text(test_text)
    
    print(f"\nExtracted {len(result)} citations:")
    print("-" * 40)
    
    # Group citations by cluster for display
    clusters = {}
    for citation in result:
        if citation.metadata and citation.metadata.get('cluster_id'):
            cluster_id = citation.metadata['cluster_id']
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(citation)
    
    # Display citations grouped by cluster
    for i, citation in enumerate(result, 1):
        print(f"\n{i}. Citation: {citation.citation}")
        print(f"   Case Name: {citation.canonical_name or citation.extracted_case_name or 'N/A'}")
        print(f"   Date: {citation.canonical_date or citation.extracted_date or 'N/A'}")
        print(f"   URL: {citation.url or 'N/A'}")
        print(f"   Verified: {citation.verified}")
        
        # Show cluster information
        if citation.metadata and citation.metadata.get('is_in_cluster'):
            cluster_id = citation.metadata.get('cluster_id')
            cluster_size = citation.metadata.get('cluster_size', 0)
            cluster_members = citation.metadata.get('cluster_members', [])
            is_primary = citation.metadata.get('cluster_primary', False)
            
            print(f"   📊 CLUSTER INFO:")
            print(f"      Cluster ID: {cluster_id}")
            print(f"      Cluster Size: {cluster_size} citations")
            print(f"      Is Primary: {is_primary}")
            print(f"      All Members: {', '.join(cluster_members)}")
        
        if citation.metadata:
            print(f"   Metadata: {len(citation.metadata)} fields")
    
    # Summary
    print(f"\n{'='*80}")
    print(f"Total citations: {len(result)}")
    print(f"Citations in clusters: {len([c for c in result if c.metadata and c.metadata.get('is_in_cluster')])}")
    print(f"Number of clusters: {len(clusters)}")
    
    # Show cluster summary
    if clusters:
        print(f"\n📊 CLUSTER SUMMARY:")
        for cluster_id, cluster_citations in clusters.items():
            primary = next((c for c in cluster_citations if c.metadata.get('cluster_primary')), cluster_citations[0])
            print(f"   Cluster {cluster_id}: {len(cluster_citations)} citations")
            print(f"      Primary: {primary.citation}")
            print(f"      Case: {primary.canonical_name}")
            print(f"      Members: {', '.join([c.citation for c in cluster_citations])}")
    
    return len(clusters) > 0

if __name__ == "__main__":
    success = test_parallel_citation_display()
    sys.exit(0 if success else 1) 