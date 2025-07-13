#!/usr/bin/env python3
"""Simple test for clustering fix."""

import requests
import json
import time

def test_clustering():
    """Test clustering with a simple request."""
    test_text = "RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"
    
    payload = {
        "type": "text",
        "text": test_text
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("Testing clustering fix...")
    
    try:
        # Submit request
        response = requests.post("http://localhost:5001/casestrainer/api/analyze", 
                               json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response status: {data.get('status')}")
            
            if data.get('status') == 'processing' and data.get('task_id'):
                task_id = data['task_id']
                print(f"Async task: {task_id}")
                
                # Poll for results
                for attempt in range(30):
                    time.sleep(1)
                    
                    status_response = requests.get(f"http://localhost:5001/casestrainer/api/task_status/{task_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        
                        if status_data.get('status') == 'completed':
                            print("Task completed!")
                            
                            citations = status_data.get('citations', [])
                            clusters = status_data.get('clusters', [])
                            
                            print(f"Citations: {len(citations)}")
                            print(f"Clusters: {len(clusters)}")
                            
                            # Check metadata
                            with_metadata = 0
                            in_clusters = 0
                            
                            for citation in citations:
                                metadata = citation.get('metadata', {})
                                if metadata:
                                    with_metadata += 1
                                    if metadata.get('is_in_cluster'):
                                        in_clusters += 1
                                        print(f"✅ IN CLUSTER: {citation.get('citation')}")
                                    else:
                                        print(f"❌ NO CLUSTER: {citation.get('citation')}")
                                else:
                                    print(f"❌ NO METADATA: {citation.get('citation')}")
                            
                            print(f"\nSummary:")
                            print(f"  With metadata: {with_metadata}/{len(citations)}")
                            print(f"  In clusters: {in_clusters}/{len(citations)}")
                            
                            if in_clusters > 0:
                                print("\n🎉 SUCCESS: Clustering is working!")
                                return True
                            else:
                                print("\n❌ ISSUE: No citations have cluster metadata")
                                return False
                            
                        elif status_data.get('status') == 'failed':
                            print(f"Task failed: {status_data.get('error')}")
                            return False
                        else:
                            print(f"Status: {status_data.get('status')}")
                
                print("Polling timed out")
                return False
            else:
                print("Unexpected response format")
                return False
        else:
            print(f"Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = test_clustering()
    exit(0 if success else 1) 