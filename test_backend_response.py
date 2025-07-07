#!/usr/bin/env python3
"""
Test script to examine backend response structure for parallel citations.
"""

import requests
import json

def test_backend_response():
    """Test the backend analyze endpoint and examine the response structure."""
    
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    # Test with a citation that should have parallel citations
    test_text = "State v. Richardson, 177 Wn.2d 351, 357, 302 P.3d 156 (2013)."
    
    payload = {
        "type": "text",
        "text": test_text
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print("Testing backend analyze endpoint...")
        print(f"URL: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        print("-" * 50)
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print("-" * 50)
        
        if response.status_code == 200:
            data = response.json()
            print("Response Data:")
            print(json.dumps(data, indent=2))
            
            # Check for citations
            if 'citations' in data:
                print(f"\nFound {len(data['citations'])} citations")
                for i, citation in enumerate(data['citations']):
                    print(f"\nCitation {i+1}:")
                    print(f"  Citation text: {citation.get('citation', 'N/A')}")
                    print(f"  Verified: {citation.get('verified', 'N/A')}")
                    print(f"  Case name: {citation.get('case_name', 'N/A')}")
                    print(f"  Has parallels field: {'parallels' in citation}")
                    if 'parallels' in citation:
                        print(f"  Parallels count: {len(citation['parallels'])}")
                        for j, parallel in enumerate(citation['parallels']):
                            print(f"    Parallel {j+1}: {parallel.get('citation', 'N/A')}")
                    print(f"  Is parallel citation: {citation.get('is_parallel_citation', False)}")
                    print(f"  Primary citation: {citation.get('primary_citation', 'N/A')}")
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error testing backend: {e}")

if __name__ == "__main__":
    test_backend_response() 