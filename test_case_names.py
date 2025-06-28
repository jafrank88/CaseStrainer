#!/usr/bin/env python3
"""
Test script to verify case name extraction is working
"""

import requests
import json

def test_case_name_extraction():
    """Test if case name extraction is working in the backend."""
    
    # Test text with clear case names
    test_text = "John Doe A v. Washington State Patrol, 185 Wn.2d 363 (2016). John Doe P v. Thurston County, 199 Wn. App. 280 (2017)."
    
    # Make request to backend - use the correct endpoint
    url = "http://localhost:5000/casestrainer/api/analyze"
    headers = {"Content-Type": "application/json"}
    data = {"text": test_text}
    
    try:
        print("Testing case name extraction...")
        print(f"Test text: {test_text}")
        print()
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Backend responded successfully!")
            print(f"Status: {result.get('status', 'unknown')}")
            
            if 'citations' in result:
                citations = result['citations']
                print(f"Found {len(citations)} citations")
                print()
                
                for i, citation in enumerate(citations, 1):
                    print(f"Citation {i}:")
                    print(f"  Citation: {citation.get('citation', 'N/A')}")
                    print(f"  Extracted Case Name: '{citation.get('extracted_case_name', 'N/A')}'")
                    print(f"  Hinted Case Name: '{citation.get('hinted_case_name', 'N/A')}'")
                    print(f"  Canonical Case Name: '{citation.get('canonical_case_name', 'N/A')}'")
                    print()
            else:
                print("❌ No citation results found in response")
                print(f"Response keys: {list(result.keys())}")
        else:
            print(f"❌ Backend error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing backend: {e}")

if __name__ == "__main__":
    test_case_name_extraction() 