#!/usr/bin/env python3
"""
Test sync processing with multiple citations
"""

import requests
import json

def test_sync_multiple():
    """Test sync processing with multiple citations"""
    
    print("Testing sync processing with multiple citations...")
    
    base_url = "http://localhost:5000/casestrainer/api"
    
    # Text with multiple citations
    text = """
    In Smith v. Jones, 123 U.S. 456 (2023), the court held that precedent.
    This was followed by Brown v. Board of Education, 345 F.2d 789 (2024).
    The appeals court in Davis v. Johnson, 567 S. Ct. 123 (2022), followed this reasoning.
    Additionally, Wilson v. Martinez, 890 F.3d 234 (2021), provides further context.
    """
    
    try:
        response = requests.post(
            f"{base_url}/analyze",
            data={'text': text, 'type': 'text'},
            timeout=30
        )
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            citations = data.get('citations', [])
            clusters = data.get('clusters', [])
            
            print(f"\nCitations found: {len(citations)}")
            for i, c in enumerate(citations):
                print(f"\nCitation {i+1}:")
                print(f"  Text: {c.get('citation', 'N/A')}")
                print(f"  Case name: {c.get('extracted_case_name', 'N/A')}")
                print(f"  Date: {c.get('extracted_date', 'N/A')}")
                print(f"  Verified: {c.get('verified', False)}")
                print(f"  Cluster ID: {c.get('cluster_id', 'None')}")
                
            print(f"\nClusters found: {len(clusters)}")
            for i, cluster in enumerate(clusters):
                print(f"\nCluster {i+1}:")
                print(f"  Name: {cluster.get('cluster_name', 'N/A')}")
                print(f"  Size: {cluster.get('size', 0)} citations")
                print(f"  Type: {cluster.get('cluster_type', 'N/A')}")
                
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_sync_multiple()
