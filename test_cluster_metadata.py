#!/usr/bin/env python3
"""
Test script to verify cluster metadata is being added to citations.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from api.services.citation_service import CitationService

def test_cluster_metadata():
    """Test that cluster metadata is added to citations."""
    
    print("🧪 Testing cluster metadata addition...")
    
    # Test text with parallel citations
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    # Create service
    service = CitationService()
    
    # Process the text
    result = service.process_immediately({
        'type': 'text',
        'text': test_text
    })
    
    print(f"📊 Processing result: {result['status']}")
    print(f"📝 Citations found: {len(result.get('citations', []))}")
    print(f"🔗 Clusters found: {len(result.get('clusters', []))}")
    
    # Check if citations have metadata
    citations = result.get('citations', [])
    clusters = result.get('clusters', [])
    
    print(f"\n🔍 Checking cluster metadata...")
    
    # Count citations with cluster metadata
    citations_with_metadata = 0
    citations_in_clusters = 0
    
    for citation in citations:
        metadata = citation.get('metadata', {})
        if metadata:
            citations_with_metadata += 1
            if metadata.get('is_in_cluster', False):
                citations_in_clusters += 1
                print(f"  ✅ Citation '{citation['citation']}' is in cluster {metadata.get('cluster_id')} (size: {metadata.get('cluster_size')})")
            else:
                print(f"  ⚪ Citation '{citation['citation']}' is not in a cluster")
        else:
            print(f"  ❌ Citation '{citation['citation']}' has no metadata")
    
    print(f"\n📈 Summary:")
    print(f"  Total citations: {len(citations)}")
    print(f"  Citations with metadata: {citations_with_metadata}")
    print(f"  Citations in clusters: {citations_in_clusters}")
    print(f"  Total clusters: {len(clusters)}")
    
    # Show cluster details
    print(f"\n🔗 Cluster details:")
    for i, cluster in enumerate(clusters, 1):
        cluster_id = cluster.get('cluster_id', 'unknown')
        cluster_size = len(cluster.get('citations', []))
        canonical_name = cluster.get('canonical_name', 'Unknown')
        print(f"  Cluster {i}: {canonical_name} (ID: {cluster_id}, Size: {cluster_size})")
        
        for citation in cluster.get('citations', []):
            print(f"    - {citation.get('citation', 'N/A')}")
    
    # Verify the fix worked
    if citations_with_metadata == len(citations) and citations_in_clusters > 0:
        print(f"\n✅ SUCCESS: All citations have metadata and clustering is working!")
        return True
    else:
        print(f"\n❌ FAILURE: Cluster metadata not working correctly")
        return False

if __name__ == "__main__":
    success = test_cluster_metadata()
    sys.exit(0 if success else 1) 