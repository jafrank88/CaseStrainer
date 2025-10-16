#!/usr/bin/env python3
"""
Simple test to verify the analyze endpoint is working
"""

import requests
import urllib3
import json

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_analyze_endpoint():
    """Test the analyze endpoint with a simple request"""
    
    base_url = "http://localhost"
    
    # Test small text (should be sync)
    test_data = {
        "type": "text", 
        "text": "In Miranda v. Arizona, 384 U.S. 436 (1966), the Supreme Court established important precedent."
    }
    
    print("Testing analyze endpoint...")
    print(f"URL: {base_url}/casestrainer/api/analyze")
    print(f"Data: {test_data}")
    print()
    
    try:
        response = requests.post(
            f"{base_url}/casestrainer/api/analyze",
            json=test_data,
            headers={"Content-Type": "application/json"},
            verify=False,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"JSON Response: {json.dumps(result, indent=2)}")
                
                # Check for citations
                citations = result.get('result', {}).get('citations', result.get('citations', []))
                print(f"Citations found: {len(citations)}")
                
                if citations:
                    print("First citation:", citations[0])
                
                return True
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                return False
        else:
            print(f"Request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Exception occurred: {e}")
        return False

if __name__ == "__main__":
    success = test_analyze_endpoint()
    if success:
        print("\n✅ Test passed!")
    else:
        print("\n❌ Test failed!")
