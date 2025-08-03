"""
Test Analyze Endpoint Script

This script tests the main analysis endpoint of the CaseStrainer API with
a sample legal citation to verify the extraction and processing functionality.
"""

import requests
import json
import sys
from urllib.parse import urljoin

def test_analyze_endpoint(base_url='http://localhost:5000'):
    """Test the analyze endpoint with a sample legal citation."""
    analyze_url = urljoin(base_url, '/casestrainer/api/analyze')
    
    # Sample legal citation for testing
    test_data = {
        "text": "See Roe v. Wade, 410 U.S. 113 (1973) for the landmark case on abortion rights.",
        "options": {
            "include_context": True,
            "verify_citations": True
        }
    }
    
    print(f"=== Testing Analyze Endpoint ===")
    print(f"URL: {analyze_url}")
    print("\n=== Request Payload ===")
    print(json.dumps(test_data, indent=2))
    
    try:
        # Make the POST request with JSON payload
        headers = {'Content-Type': 'application/json'}
        response = requests.post(
            analyze_url,
            json=test_data,
            headers=headers,
            timeout=30  # Increased timeout for processing
        )
        
        # Print response details
        print(f"\n=== Response Status ===")
        print(f"Status Code: {response.status_code}")
        
        # Print response headers
        print("\n=== Response Headers ===")
        for key, value in response.headers.items():
            print(f"{key}: {value}")
        
        # Try to parse and pretty-print JSON response
        try:
            if response.text.strip():  # Only try to parse if there's content
                json_data = response.json()
                print("\n=== Response Body (JSON) ===")
                print(json.dumps(json_data, indent=2, sort_keys=False))
            else:
                print("\n=== Response Body (Empty) ===")
                print("No content in response")
        except json.JSONDecodeError:
            print("\n=== Response Body (Raw) ===")
            print(response.text)
        
        # Check if the response indicates success
        if response.status_code == 200:
            print("\n✅ Analyze endpoint test completed successfully!")
            return True
        else:
            print(f"\n⚠️  Analyze endpoint returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error making request to {analyze_url}")
        print(f"Error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Allow specifying a different base URL via command line
    base_url = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:5000'
    test_analyze_endpoint(base_url)
