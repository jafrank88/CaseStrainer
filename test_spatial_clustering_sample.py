#!/usr/bin/env python3
"""
Test spatial clustering with a sample from Trump v. CASA PDF
to verify the clustering logic is working correctly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from spatial_clustering import SpatialClusterer

# Sample text from Trump v. CASA PDF table of authorities
sample_text = """
TABLE OF AUTHORITIES

Cases

Biden v. Nebraska, 600 U.S. 477 (2023) ........................... 15

Berenyi v. District Director, Immigration & Naturalization Service,
385 U.S. 630 (1967) ......................................................... 8

Chin Bak Kan v. United States, 186 U.S. 193 (1902) ........... 9

Department of Commerce v. New York, 588 U.S. 752 (2019) ... 15

Dred Scott v. Sandford, 19 How. 393 (1857) ...................... 7

Park v. Barr, 946 F.3d 1096 (2020) .................................. 10

Trump v. Hawaii, 585 U.S. 667 (2018) ............................. 12

United States v. Wong Kim Ark, 169 U.S. 649 (1898) .......... 8
"""

# Sample citations (simulated extraction)
sample_citations = [
    {"citation": "600 U.S. 477", "start_index": sample_text.find("600 U.S. 477")},
    {"citation": "385 U.S. 630", "start_index": sample_text.find("385 U.S. 630")},
    {"citation": "186 U.S. 193", "start_index": sample_text.find("186 U.S. 193")},
    {"citation": "588 U.S. 752", "start_index": sample_text.find("588 U.S. 752")},
    {"citation": "19 How. 393", "start_index": sample_text.find("19 How. 393")},
    {"citation": "946 F.3d 1096", "start_index": sample_text.find("946 F.3d 1096")},
    {"citation": "585 U.S. 667", "start_index": sample_text.find("585 U.S. 667")},
    {"citation": "169 U.S. 649", "start_index": sample_text.find("169 U.S. 649")},
]

def test_spatial_clustering():
    """Test spatial clustering on sample text."""
    print("=" * 80)
    print("SPATIAL CLUSTERING TEST")
    print("=" * 80)
    print()
    
    # Initialize spatial clustering
    clusterer = SpatialClusterer(config={"debug": True})
    
    # Run clustering
    print("Running spatial clustering on sample text...")
    print()
    clusters = clusterer.cluster_citations_spatial(sample_citations, sample_text)
    
    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()
    print(f"Total clusters created: {len(clusters)}")
    print()
    
    # Display each cluster
    for i, cluster in enumerate(clusters, 1):
        print(f"Cluster {i}:")
        print(f"  Case Name: {cluster.get('cluster_case_name')}")
        print(f"  Year: {cluster.get('cluster_year')}")
        print(f"  Size: {cluster.get('cluster_size')}")
        print(f"  Method: {cluster.get('method')}")
        
        members = cluster.get('cluster_members', [])
        citations = cluster.get('citations', [])
        
        print(f"  Members ({len(members)}):")
        for member in members:
            print(f"    - {member.get('citation')}")
        
        print(f"  Citations array ({len(citations)}):")
        for cit in citations:
            print(f"    - {cit.get('citation')} (extracted: {cit.get('extracted_case_name')}, {cit.get('extracted_date')})")
        
        print()
    
    # Verify expectations
    print("=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    print()
    
    expected_clusters = 8  # One per case in the sample
    if len(clusters) == expected_clusters:
        print(f"✅ PASS: Expected {expected_clusters} clusters, got {len(clusters)}")
    else:
        print(f"❌ FAIL: Expected {expected_clusters} clusters, got {len(clusters)}")
    
    # Check that each cluster has exactly 1 citation
    all_single = all(cluster.get('cluster_size') == 1 for cluster in clusters)
    if all_single:
        print("✅ PASS: All clusters have exactly 1 citation (no incorrect merging)")
    else:
        multi_clusters = [c for c in clusters if c.get('cluster_size') > 1]
        print(f"❌ FAIL: {len(multi_clusters)} clusters have multiple citations")
        for c in multi_clusters:
            print(f"  - {c.get('cluster_case_name')} has {c.get('cluster_size')} citations")
    
    # Check that case names are complete (not truncated)
    truncated = []
    for cluster in clusters:
        name = cluster.get('cluster_case_name', '')
        # Check for common truncation patterns
        if name.endswith(' v. District') or name.endswith(' v. United') or name.endswith(' v. New'):
            truncated.append(name)
    
    if not truncated:
        print("✅ PASS: No truncated case names detected")
    else:
        print(f"❌ FAIL: {len(truncated)} truncated case names found:")
        for name in truncated:
            print(f"  - {name}")
    
    # Check that citations array exists for frontend
    all_have_citations = all('citations' in cluster for cluster in clusters)
    if all_have_citations:
        print("✅ PASS: All clusters have 'citations' array for frontend")
    else:
        print("❌ FAIL: Some clusters missing 'citations' array")
    
    print()
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_spatial_clustering()
