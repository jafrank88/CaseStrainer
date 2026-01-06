#!/usr/bin/env python3
"""
Test the full clustering pipeline to see where merging happens
"""

from src.unified_clustering_master import get_master_clusterer

def test_full_pipeline():
    """Test the complete clustering pipeline"""
    
    text = """See Doe v. Teachers Council, Inc., 2024 WL 1232082, at *3; Schiller v. City of New York, 2006 WL 2788256, at *5; Doe v. City of New York, 2022 WL 15153410, at *1."""
    
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
    processor = UnifiedCitationProcessorV2()
    citations = processor._extract_with_regex_enhanced(text)
    
    print("=" * 80)
    print("TESTING FULL CLUSTERING PIPELINE")
    print("=" * 80)
    print()
    
    config = {"enable_verification": True}
    clustering = get_master_clusterer(config)
    
    # Run the full clustering pipeline
    clusters = clustering.cluster_citations(citations, text)
    
    print(f"\nFinal result: {len(clusters)} clusters")
    
    if len(clusters) == 1:
        print("ERROR: All citations were merged into one cluster!")
        print("\nCluster contents:")
        cluster = clusters[0]
        cits = cluster.get("citations", [])
        for i, cit in enumerate(cits):
            if isinstance(cit, dict):
                print(f"  {i+1}. {cit.get('citation', 'N/A')}")
            else:
                print(f"  {i+1}. {cit.citation}")
        
        # Check if cross-document merge happened
        if cluster.get('cross_document_merge'):
            print(f"\n⚠️  This was merged by cross-document deduplication!")
            print(f"   Merge source count: {cluster.get('merge_source_count')}")
    else:
        print("SUCCESS: Citations remain in separate clusters")
        for i, cluster in enumerate(clusters):
            cits = cluster.get("citations", [])
            print(f"\nCluster {i+1}: {len(cits)} citations")
            for cit in cits:
                if isinstance(cit, dict):
                    print(f"  - {cit.get('citation', 'N/A')}")
                else:
                    print(f"  - {cit.citation}")

if __name__ == "__main__":
    test_full_pipeline()
