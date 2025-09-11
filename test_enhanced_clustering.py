#!/usr/bin/env python3
"""
Test the enhanced clustering system that integrates all improvements.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_clustering import EnhancedCitationClusterer, ClusteringConfig

def test_enhanced_clustering():
    """Test the enhanced clustering system."""
    print("🧪 Testing Enhanced Citation Clustering System")
    
    # Initialize with debug mode
    config = ClusteringConfig(debug_mode=True, proximity_threshold=50)
    clusterer = EnhancedCitationClusterer(config)
    
    # Test text with parallel citations
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    # Citations found by our enhanced extraction
    all_citations = [
        '200 Wn.2d 72',
        '514 P.3d 643',  # Parallel to 200 Wn.2d 72
        '171 Wn.2d 486', 
        '256 P.3d 321',  # Parallel to 171 Wn.2d 486
        '146 Wn.2d 1',
        '43 P.3d 4'      # Parallel to 146 Wn.2d 1
    ]
    
    print(f"Test text: {test_text[:100]}...")
    print(f"Citations found: {all_citations}")
    print()
    
    # Test the enhanced clustering
    clusters = clusterer.cluster_citations(all_citations, test_text, "test_request")
    
    print(f"\n🎉 Enhanced Clustering Results:")
    print(f"  Expected: 3 clusters with 2 citations each")
    print(f"  Actual: {len(clusters)} clusters")
    
    for i, cluster in enumerate(clusters):
        print(f"\n  Cluster {i+1}: {cluster['case_name']} ({cluster['year']})")
        print(f"    Size: {cluster['size']} citations")
        print(f"    Type: {cluster['cluster_type']}")
        print(f"    Confidence: {cluster['confidence_score']:.2f}")
        print(f"    Citations:")
        for citation in cluster['citations']:
            print(f"      - {citation}")
    
    print("\n✅ Enhanced clustering test completed!")
    
    # Test caching
    print(f"\n🔍 Testing caching (should be faster on second run):")
    start_time = time.time()
    clusters2 = clusterer.cluster_citations(all_citations, test_text, "test_request2")
    cache_time = time.time() - start_time
    print(f"  Cached run time: {cache_time:.4f} seconds")
    
    # Clear cache and test again
    clusterer.clear_cache()
    start_time = time.time()
    clusters3 = clusterer.cluster_citations(all_citations, test_text, "test_request3")
    fresh_time = time.time() - start_time
    print(f"  Fresh run time: {fresh_time:.4f} seconds")
    print(f"  Cache speedup: {fresh_time/cache_time:.1f}x")

if __name__ == "__main__":
    import time
    test_enhanced_clustering()
