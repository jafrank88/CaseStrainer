#!/usr/bin/env python3
"""
Test script to call the /analyze endpoint and see debug logging output
"""

import requests
import json

def test_analyze_endpoint():
    """Test the /analyze endpoint with a sample citation"""
    
    url = "http://127.0.0.1:5000/casestrainer/api/analyze"
    
    # Test data - a simple citation
    test_data = {
        "type": "text",
        "text": "Punx v Smithers, 123 Wash. 2d 456, 789 P.2d 123 (1990)"
    }
    
    print("Testing /analyze endpoint...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    print("-" * 50)
    
    try:
        response = requests.post(url, json=test_data, timeout=30)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response JSON: {json.dumps(result, indent=2)}")
            
            # Check for citations in the response
            if 'citations' in result and result['citations']:
                print("\n" + "="*50)
                print("CITATIONS FOUND:")
                print("="*50)
                for i, citation in enumerate(result['citations']):
                    print(f"\nCitation {i}:")
                    print(f"  extracted_case_name: '{citation.get('extracted_case_name')}'")
                    print(f"  extracted_date: '{citation.get('extracted_date')}'")
                    print(f"  canonical_name: '{citation.get('canonical_name')}'")
                    print(f"  canonical_date: '{citation.get('canonical_date')}'")
                    print(f"  citation: '{citation.get('citation')}'")
            else:
                print("\nNo citations found in response")
        else:
            print(f"Error response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response: {e}")
        print(f"Raw response: {response.text}")

if __name__ == "__main__":
    test_analyze_endpoint() 