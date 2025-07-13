#!/usr/bin/env python3
"""Debug clustering matching issue."""

import requests
import json
import time

def debug_clustering():
    """Debug the clustering matching issue."""
    test_text = "RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"
    
    payload = {
        "type": "text",
        "text": test_text
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("Debugging clustering matching...")
    
    try:
        # Submit request
        response = requests.post("http://localhost:5001/casestrainer/api/analyze", 
                               json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
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
                            
                            print(f"\nCitations ({len(citations)}):")
                            for i, citation in enumerate(citations):
                                print(f"  {i+1}. '{citation.get('citation')}'")
                            
                            print(f"\nClusters ({len(clusters)}):")
                            for i, cluster in enumerate(clusters):
                                print(f"  Cluster {i+1}: {cluster.get('cluster_id')}")
                                print(f"    Canonical: {cluster.get('canonical_name')}")
                                print(f"    Citations in cluster:")
                                for citation in cluster.get('citations', []):
                                    print(f"      - '{citation.get('citation')}'")
                                print()
                            
                            # Check metadata
                            print("Citation metadata:")
                            for i, citation in enumerate(citations):
                                metadata = citation.get('metadata', {})
                                print(f"  {i+1}. '{citation.get('citation')}'")
                                print(f"     Metadata: {metadata}")
                                print()
                            
                            return True
                            
                        elif status_data.get('status') == 'failed':
                            print(f"Task failed: {status_data.get('error')}")
                            return False
                
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
    debug_clustering() 