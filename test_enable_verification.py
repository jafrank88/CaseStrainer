#!/usr/bin/env python3
"""
Test the enable_verification parameter
"""

import requests
import json

def test_enable_verification():
    """Test with enable_verification=false"""
    
    print("Testing with enable_verification=false...")
    
    base_url = "http://localhost:5000/casestrainer/api"
    
    # Text with multiple citations
    text = """
    In Smith v. Jones, 123 U.S. 456 (2023), the court held that precedent.
    This was followed by Brown v. Board of Education, 345 F.2d 789 (2024).
    The appeals court in Davis v. Johnson, 567 S. Ct. 123 (2022), followed this reasoning.
    Additionally, Wilson v. Martinez, 890 F.3d 234 (2021), provides further context.
    """
    
    try:
        # Test with verification disabled
        response = requests.post(
            f"{base_url}/analyze",
            data={
                'text': text, 
                'type': 'text',
                'enable_verification': 'false'  # Disable verification
            },
            timeout=30
        )
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            citations = data.get('citations', [])
            clusters = data.get('clusters', [])
            
            print(f"\n✓ Success with verification disabled!")
            print(f"Citations found: {len(citations)}")
            print(f"Clusters found: {len(clusters)}")
            
            # Show citations
            for i, c in enumerate(citations[:5]):
                print(f"\nCitation {i+1}:")
                print(f"  Text: {c.get('citation', 'N/A')}")
                print(f"  Case name: {c.get('extracted_case_name', 'N/A')}")
                print(f"  Date: {c.get('extracted_date', 'N/A')}")
                print(f"  Verified: {c.get('verified', False)}")
                print(f"  Cluster ID: {c.get('cluster_id', 'None')}")
                
            # Show clusters
            for i, cluster in enumerate(clusters[:3]):
                print(f"\nCluster {i+1}:")
                print(f"  Name: {cluster.get('cluster_name', 'N/A')}")
                print(f"  Size: {cluster.get('size', 0)} citations")
                
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

def test_verification_enabled():
    """Test with verification enabled (default)"""
    
    print("\n" + "="*60)
    print("Testing with verification enabled (default)...")
    
    base_url = "http://localhost:5000/casestrainer/api"
    
    # Simple text (to avoid timeout)
    text = "Smith v. Jones, 123 U.S. 456 (2023)."
    
    try:
        # Test with verification enabled (default)
        response = requests.post(
            f"{base_url}/analyze",
            data={
                'text': text, 
                'type': 'text'
                # No enable_verification parameter - should default to True
            },
            timeout=30
        )
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            citations = data.get('citations', [])
            
            print(f"\n✓ Success with verification enabled!")
            print(f"Citations found: {len(citations)}")
            
            if citations:
                c = citations[0]
                print(f"  Text: {c.get('citation', 'N/A')}")
                print(f"  Verified: {c.get('verified', False)}")
                
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_enable_verification()
    test_verification_enabled()
