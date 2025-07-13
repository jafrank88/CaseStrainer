#!/usr/bin/env python3
"""
Test script to directly call the backend /casestrainer/api/analyze endpoint
and inspect the response structure for clusters and metadata.
"""

import requests
import json
import sys

def test_backend_api():
    # Test paragraph with 3 clusters of 2 cases each
    test_text = '''A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)'''

    # Test different backend URLs
    urls = [
        "http://localhost:5000/casestrainer/api/analyze",
        "http://localhost:80/casestrainer/api/analyze", 
        "http://localhost/casestrainer/api/analyze",
        "http://127.0.0.1:5000/casestrainer/api/analyze"
    ]

    payload = {
        "type": "text",
        "text": test_text
    }

    headers = {
        "Content-Type": "application/json"
    }

    print("Testing backend API endpoints...")
    print(f"Test text: {test_text[:100]}...")
    print("-" * 80)

    for url in urls:
        print(f"\nTesting: {url}")
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response keys: {list(data.keys())}")
                
                # Check citations
                citations = data.get('citations', [])
                print(f"Citations found: {len(citations)}")
                
                # Check clusters
                clusters = data.get('clusters', [])
                print(f"Clusters found: {len(clusters)}")
                
                # Check metadata in citations
                citations_with_metadata = 0
                citations_in_clusters = 0
                
                for i, citation in enumerate(citations):
                    print(f"\nCitation {i+1}: {citation.get('citation', 'N/A')}")
                    print(f"  extracted_case_name: {citation.get('extracted_case_name', 'MISSING')}")
                    print(f"  extracted_date: {citation.get('extracted_date', 'MISSING')}")
                    
                    metadata = citation.get('metadata', {})
                    if metadata:
                        citations_with_metadata += 1
                        print(f"  metadata: {metadata}")
                        
                        if metadata.get('is_in_cluster'):
                            citations_in_clusters += 1
                            print(f"  -> IN CLUSTER: {metadata.get('cluster_id')} (size: {metadata.get('cluster_size')})")
                    else:
                        print(f"  metadata: MISSING")
                
                print(f"\nSummary:")
                print(f"  Citations with metadata: {citations_with_metadata}/{len(citations)}")
                print(f"  Citations in clusters: {citations_in_clusters}/{len(citations)}")
                print(f"  Total clusters: {len(clusters)}")
                
                # Show cluster details
                if clusters:
                    print(f"\nCluster details:")
                    for i, cluster in enumerate(clusters):
                        print(f"  Cluster {i+1}: {cluster.get('cluster_id', 'unknown')}")
                        print(f"    Size: {len(cluster.get('citations', []))}")
                        print(f"    Members: {[c.get('citation', 'N/A') for c in cluster.get('citations', [])]}")
                
                return data  # Return the first successful response
                
            else:
                print(f"Error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}")
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    print("\nNo working endpoints found!")
    return None

if __name__ == "__main__":
    result = test_backend_api()
    if result:
        print("\n" + "="*80)
        print("FULL RESPONSE:")
        print(json.dumps(result, indent=2)) 