#!/usr/bin/env python3
"""
Test with JSON payload instead of form data
"""

import requests
import json

def test_json_payload():
    """Test with JSON payload"""
    
    print("Testing with JSON payload and enable_verification=false...")
    
    base_url = "http://localhost:5000/casestrainer/api"
    
    # Text with multiple citations
    text = "Smith v. Jones, 123 U.S. 456 (2023). Brown v. Board, 345 F.2d 789 (2024)."
    
    # Test with a new citation that hasn't been verified before
    test_data = {
        "text": "Johnson v. United States, 999 F.3d 456 (2024). This is a new test case.",
        "type": "text",
        "enable_verification": False
    }
    
    try:
        # Test with JSON payload
        response = requests.post(
            f"{base_url}/analyze",
            json=test_data,
            timeout=30
        )
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            citations = data.get('citations', [])
            clusters = data.get('clusters', [])
            
            print(f"\n✓ Success with verification disabled via JSON!")
            print(f"Citations found: {len(citations)}")
            print(f"Clusters found: {len(clusters)}")
            
            # Show citations
            for i, c in enumerate(citations[:3]):
                print(f"\nCitation {i+1}:")
                print(f"  Text: {c.get('citation', 'N/A')}")
                print(f"  Case name: {c.get('extracted_case_name', 'N/A')}")
                print(f"  Verified: {c.get('verified', False)}")
                
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_json_payload()
