#!/usr/bin/env python3
"""
Quick test to verify clustering fix works.
"""

import requests
import json

def test_clustering():
    """Test citation clustering with the test paragraph."""
    test_text = '''A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)'''

    payload = {
        "type": "text",
        "text": test_text
    }

    headers = {
        "Content-Type": "application/json"
    }

    # Test the backend
    url = "http://localhost:5001/casestrainer/api/analyze"
    
    try:
        print(f"Testing: {url}")
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            citations = data.get('citations', [])
            clusters = data.get('clusters', [])
            
            print(f"✅ Success!")
            print(f"Citations: {len(citations)}")
            print(f"Clusters: {len(clusters)}")
            
            # Check metadata
            citations_with_metadata = 0
            citations_in_clusters = 0
            
            for i, citation in enumerate(citations):
                metadata = citation.get('metadata', {})
                if metadata:
                    citations_with_metadata += 1
                    if metadata.get('is_in_cluster'):
                        citations_in_clusters += 1
                        print(f"  Citation {i+1}: IN CLUSTER {metadata.get('cluster_id')}")
                    else:
                        print(f"  Citation {i+1}: NO CLUSTER")
                else:
                    print(f"  Citation {i+1}: NO METADATA")
            
            print(f"\nSummary:")
            print(f"  Citations with metadata: {citations_with_metadata}/{len(citations)}")
            print(f"  Citations in clusters: {citations_in_clusters}/{len(citations)}")
            
            # Check if we have the expected 3 clusters
            if len(clusters) == 3 and citations_in_clusters > 0:
                print(f"\n🎉 SUCCESS! Clustering is working correctly!")
                return True
            else:
                print(f"\n❌ ISSUE: Expected 3 clusters with citations in clusters")
                return False
                
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    success = test_clustering()
    exit(0 if success else 1)
