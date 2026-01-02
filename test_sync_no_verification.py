#!/usr/bin/env python3
"""
Test sync processing with verification disabled
"""

import requests
import json

def test_sync_no_verification():
    """Test sync processing without verification"""
    
    print("Testing sync processing without verification...")
    
    base_url = "http://localhost:5000/casestrainer/api"
    
    # Simple text
    text = "Smith v. Jones, 123 U.S. 456 (2023). This was followed by Brown v. Board, 345 F.2d 789 (2024)."
    
    try:
        # Use the analyze_no_verification endpoint if it exists, or pass a parameter
        response = requests.post(
            f"{base_url}/analyze",
            data={'text': text, 'type': 'text', 'enable_verification': 'false'},
            timeout=30
        )
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            
            if 'citations' in data:
                citations = data['citations']
                print(f"Citations found: {len(citations)}")
                for i, c in enumerate(citations[:3]):
                    print(f"  Citation {i+1}: {c.get('citation', 'N/A')}")
                    print(f"    Case name: {c.get('extracted_case_name', 'N/A')}")
                    print(f"    Verified: {c.get('verified', False)}")
                    
            if 'clusters' in data:
                clusters = data['clusters']
                print(f"Clusters found: {len(clusters)}")
                for i, cluster in enumerate(clusters[:3]):
                    print(f"  Cluster {i+1}: {cluster.get('cluster_name', 'N/A')} ({cluster.get('size', 0)} citations)")
                    
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_sync_no_verification()
