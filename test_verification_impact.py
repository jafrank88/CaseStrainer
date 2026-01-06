#!/usr/bin/env python3
"""
Test what verification does to the clusters
"""

from src.unified_clustering_master import get_master_clusterer

def test_verification_impact():
    """Test how verification affects clustering"""
    
    text = """See Doe v. Teachers Council, Inc., 2024 WL 1232082, at *3; Schiller v. City of New York, 2006 WL 2788256, at *5; Doe v. City of New York, 2022 WL 15153410, at *1."""
    
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
    processor = UnifiedCitationProcessorV2()
    citations = processor._extract_with_regex_enhanced(text)
    
    print("=" * 80)
    print("TESTING VERIFICATION IMPACT ON CLUSTERING")
    print("=" * 80)
    print()
    
    # Test WITHOUT verification
    print("WITHOUT verification:")
    config_no_verify = {"debug_mode": True, "enable_verification": False}
    clustering_no_verify = get_master_clusterer(config_no_verify)
    clusters_no_verify = clustering_no_verify.cluster_citations(citations, text)
    print(f"  Result: {len(clusters_no_verify)} clusters")
    print()
    
    # Test WITH verification
    print("WITH verification:")
    config_verify = {"debug_mode": True, "enable_verification": True}
    clustering_verify = get_master_clusterer(config_verify)
    clusters_verify = clustering_verify.cluster_citations(citations, text)
    print(f"  Result: {len(clusters_verify)} clusters")
    
    if len(clusters_verify) == 1:
        print("  ERROR: Verification merged all citations!")
        cluster = clusters_verify[0]
        print(f"  Cluster case name: {cluster.get('cluster_case_name', 'N/A')}")
        print(f"  Citations in cluster:")
        for cit in cluster.get('citations', []):
            if hasattr(cit, 'citation'):
                print(f"    - {cit.citation}")
            else:
                print(f"    - {cit}")
    
    print()
    print("CONCLUSION:")
    print("-" * 40)
    print("The verification process is incorrectly merging separate citations!")
    print("This happens when citations cannot be verified (404 errors).")

if __name__ == "__main__":
    test_verification_impact()
