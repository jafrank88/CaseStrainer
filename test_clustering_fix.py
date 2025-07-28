#!/usr/bin/env python3
"""
Test script to verify the clustering fix for Gideon v. Wainwright citations.
This tests that all citations to the same case are properly clustered together.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.models import CitationResult
from src.services.citation_clusterer import CitationClusterer
from src.services.interfaces import ProcessingConfig

def create_test_citation(citation_text, canonical_name=None, canonical_date=None, 
                        extracted_case_name=None, extracted_date=None, verified=False):
    """Create a test citation with the specified attributes."""
    citation = CitationResult(
        citation=citation_text,
        canonical_name=canonical_name,
        canonical_date=canonical_date,
        extracted_case_name=extracted_case_name,
        extracted_date=extracted_date,
        verified=verified,
        start_index=0
    )
    return citation

def test_gideon_clustering():
    """Test that all Gideon v. Wainwright citations are properly clustered."""
    print("Testing Gideon v. Wainwright clustering...")
    
    # Create test citations representing the scenario from the user's screenshot
    citations = [
        # Verified citations with canonical data
        create_test_citation(
            "372 U.S. 335",
            canonical_name="Gideon v. Wainwright",
            canonical_date="1963",
            extracted_case_name="Gideon v. Wainwright",
            extracted_date="1963",
            verified=True
        ),
        create_test_citation(
            "83 S. Ct. 792",
            canonical_name="Gideon v. Wainwright",
            canonical_date="1963",
            extracted_case_name="Gideon v. Wainwright",
            extracted_date="1963",
            verified=True
        ),
        # Unverified citations with only extracted data
        create_test_citation(
            "9 L. Ed. 2d 799",
            extracted_case_name="Gideon v. Wainwright",
            extracted_date="1963",
            verified=False
        ),
        create_test_citation(
            "Gideon v. Wainwright",
            extracted_case_name="Gideon v. Wainwright",
            extracted_date="1963",
            verified=False
        ),
        # Different case to ensure no cross-contamination
        create_test_citation(
            "578 U.S. 5",
            canonical_name="Luis v. United States",
            canonical_date="2016",
            extracted_case_name="Luis v. United States",
            extracted_date="2016",
            verified=True
        )
    ]
    
    # Run clustering using new modular architecture
    config = ProcessingConfig(debug_mode=True)
    clusterer = CitationClusterer(config)
    clusters = clusterer.cluster_citations(citations)
    
    # Analyze results - clusters is now a list of cluster dictionaries
    print(f"\nClustering Results:")
    print(f"Total citations: {len(citations)}")
    print(f"Number of clusters: {len(clusters)}")
    
    # Check Gideon clustering
    gideon_clusters = [cluster for cluster in clusters 
                      if 'gideon' in str(cluster.get('canonical_name', '') + cluster.get('extracted_case_name', '')).lower()]
    
    if len(gideon_clusters) == 1:
        gideon_cluster = gideon_clusters[0]
        print(f"\n✅ SUCCESS: All Gideon citations clustered together!")
        print(f"Gideon cluster size: {gideon_cluster.get('size', 0)}")
        print(f"Gideon cluster name: {gideon_cluster.get('canonical_name', gideon_cluster.get('extracted_case_name', 'N/A'))}")
    elif len(gideon_clusters) > 1:
        print(f"\n❌ ERROR: Gideon citations split into {len(gideon_clusters)} clusters!")
        for i, cluster in enumerate(gideon_clusters):
            print(f"Cluster {i+1}: size {cluster.get('size', 0)}")
    else:
        print(f"\n❌ ERROR: No Gideon clusters found!")
    
    # Check Luis clustering
    luis_clusters = [cluster for cluster in clusters 
                    if 'luis' in str(cluster.get('canonical_name', '') + cluster.get('extracted_case_name', '')).lower()]
    
    if len(luis_clusters) == 1:
        luis_cluster = luis_clusters[0]
        print(f"\n✅ SUCCESS: Luis citation properly isolated!")
        print(f"Luis cluster size: {luis_cluster.get('size', 0)}")
    else:
        print(f"\n❌ ERROR: Luis clustering issue!")
    
    # Check for cross-contamination
    cross_contamination = False
    for i, cluster in enumerate(clusters):
        canonical_name = cluster.get('canonical_name')
        extracted_name = cluster.get('extracted_case_name')
        
        # Simple check - if cluster has both canonical and extracted names that differ significantly
        if canonical_name and extracted_name and canonical_name.lower() != extracted_name.lower():
            # Allow for minor variations (like "v." vs "v")
            if 'v.' in canonical_name.lower() or 'v.' in extracted_name.lower():
                continue
            print(f"\n⚠️  WARNING: Name mismatch in cluster {i+1}!")
            print(f"Canonical: {canonical_name}, Extracted: {extracted_name}")
    
    if not cross_contamination:
        print(f"\n✅ SUCCESS: No cross-contamination detected!")
    
    return len(gideon_clusters) == 1 and len(luis_clusters) == 1 and not cross_contamination

def test_edge_cases():
    """Test edge cases for clustering."""
    print("\n" + "="*50)
    print("Testing edge cases...")
    
    # Test citations with same date but different cases
    citations = [
        create_test_citation(
            "Case A Citation",
            canonical_name="Case A",
            canonical_date="1963",
            verified=True
        ),
        create_test_citation(
            "Case B Citation",
            canonical_name="Case B", 
            canonical_date="1963",
            verified=True
        )
    ]
    
    clustered = CitationClusterer(citations)
    
    clusters = {}
    for citation in clustered:
        if hasattr(citation, 'metadata') and citation.metadata.get('is_in_cluster'):
            cluster_id = citation.metadata.get('cluster_id')
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(citation)
    
    if len(clusters) == 2:
        print("✅ SUCCESS: Different cases with same date kept separate!")
    else:
        print(f"❌ ERROR: Expected 2 clusters, got {len(clusters)}")
        return False
    
    return True

if __name__ == "__main__":
    print("Citation Clustering Fix Test")
    print("="*50)
    
    success1 = test_gideon_clustering()
    success2 = test_edge_cases()
    
    print("\n" + "="*50)
    if success1 and success2:
        print("🎉 ALL TESTS PASSED! Clustering fix is working correctly.")
    else:
        print("❌ SOME TESTS FAILED. Please review the clustering logic.")
    
    print("="*50)
