#!/usr/bin/env python3
"""
Test script to check API response for extracted_case_name and extracted_date fields.
"""

import requests
import json

def test_api_response():
    """Test the API response to see if extracted fields are present."""
    
    # Test data
    test_data = {
        "type": "text",
        "text": "In State v. Johnson, 123 Wn.2d 456 (2020), the Washington Supreme Court held that the defendant's rights were violated. The court also cited Brown v. Board, 123 Wn.2d 789 (2019).",
        "citations": ["123 Wn.2d 456", "123 Wn.2d 789"],
        "api_key": None
    }
    
    # API endpoint
    url = "http://localhost:5000/casestrainer/api/analyze_enhanced"
    
    try:
        print("Sending request to API...")
        print(f"URL: {url}")
        print(f"Data: {json.dumps(test_data, indent=2)}")
        
        response = requests.post(url, json=test_data, headers={'Content-Type': 'application/json'})
        
        print(f"\nResponse status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nResponse JSON:")
            print(json.dumps(result, indent=2))
            
            # Check if citations are present
            if 'citations' in result:
                citations = result['citations']
                print(f"\nFound {len(citations)} citations:")
                
                for i, citation in enumerate(citations):
                    print(f"\nCitation {i+1}: {citation.get('citation', 'N/A')}")
                    print(f"  extracted_case_name: {citation.get('extracted_case_name', 'MISSING')}")
                    print(f"  extracted_date: {citation.get('extracted_date', 'MISSING')}")
                    print(f"  canonical_name: {citation.get('canonical_name', 'MISSING')}")
                    print(f"  canonical_date: {citation.get('canonical_date', 'MISSING')}")
                    print(f"  verified: {citation.get('verified', 'MISSING')}")
                    
                    # Check if extracted fields are present
                    has_extracted_name = 'extracted_case_name' in citation
                    has_extracted_date = 'extracted_date' in citation
                    
                    print(f"  extracted_case_name present: {has_extracted_name}")
                    print(f"  extracted_date present: {has_extracted_date}")
            else:
                print("No 'citations' field in response")
        else:
            print(f"Error response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Connection error: Make sure the backend server is running on localhost:5000")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api_response() 