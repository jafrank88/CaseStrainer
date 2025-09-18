#!/usr/bin/env python3
"""
Test the CaseStrainer API with simple text that should definitely work
"""

import requests
import json

def test_simple_api():
    """Test the CaseStrainer API with simple text containing obvious citations"""
    
    # Simple text with obvious citations
    test_text = "This case cites 166 Wn.2d 255 and 487 U.S. 781."
    
    # CaseStrainer API endpoint
    api_url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    print(f"Testing CaseStrainer API with simple text")
    print(f"API endpoint: {api_url}")
    print(f"Test text: {test_text}")
    print("=" * 80)
    
    # Test with text input
    data = {
        'text': test_text,
        'type': 'text'
    }
    
    try:
        print("Submitting text for analysis...")
        response = requests.post(api_url, data=data, timeout=60)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            citations = result.get('citations', [])
            print(f"Citations found: {len(citations)}")
            
            if citations:
                print("\nCitations:")
                for i, citation in enumerate(citations):
                    print(f"  {i+1}. {citation.get('full_citation', citation.get('citation', 'N/A'))}")
                    if citation.get('extracted_case_name'):
                        print(f"      Case: {citation['extracted_case_name']}")
                    if citation.get('verified'):
                        print(f"      Verified: {citation['verified']}")
            else:
                print("⚠️  No citations found")
                print(f"Full response: {json.dumps(result, indent=2)}")
        else:
            print(f"✗ API request failed: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"✗ Request failed: {e}")

if __name__ == "__main__":
    test_simple_api()
