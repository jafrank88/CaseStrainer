#!/usr/bin/env python3
"""
Simplified test for the /api/analyze endpoint
"""

import sys
import os
import json
import requests
from urllib.parse import urljoin

# Configuration
BASE_URL = "http://localhost:5000/casestrainer"
API_ENDPOINT = "/api/analyze"
FULL_URL = urljoin(BASE_URL, API_ENDPOINT)

# Test text with citations
TEST_TEXT = """We review a trial court's parenting plan for abuse of discretion. 
In re Marriage of Chandola, 180 Wn.2d 632, 642, 327 P.3d 644 (2014). 
A court abuses its discretion if its decision is manifestly unreasonable or 
based on untenable grounds or reasons. In re Marriage of Littlefield, 
133 Wn.2d 39, 46-47, 940 P.2d 1362 (1997). This includes a court's failure 
to apply the correct legal standard."""

def test_api_endpoint():
    """Test the /api/analyze endpoint with a simple request."""
    print(f"🚀 Testing API endpoint: {FULL_URL}")
    
    # Prepare request data
    data = {
        "text": TEST_TEXT,
        "type": "text"
    }
    
    # Headers to simulate a real browser request
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print("\n📤 Sending request...")
        print(f"URL: {FULL_URL}")
        print(f"Headers: {json.dumps(headers, indent=2)}")
        print(f"Data: {json.dumps(data, indent=2)}")
        
        # Make the request with a longer timeout
        print("Sending request to:", FULL_URL)
        print("Request data:", json.dumps(data, indent=2))
        print("Request headers:", json.dumps(headers, indent=2))
        
        response = requests.post(
            FULL_URL,
            json=data,
            headers=headers,
            timeout=120  # Increased timeout to 120 seconds
        )
        
        # Print response details
        print("\n📥 Response received:")
        print(f"Status Code: {response.status_code}")
        print("Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
            
        # Try to parse JSON response
        try:
            json_response = response.json()
            print("\n📋 JSON Response:")
            print(json.dumps(json_response, indent=2))
            
            # Check for expected fields
            if 'citations' in json_response and 'clusters' in json_response:
                print("\n✅ Found expected fields in response")
                print(f"Citations found: {len(json_response.get('citations', []))}")
                print(f"Clusters found: {len(json_response.get('clusters', []))}")
            else:
                print("\n❌ Missing expected fields in response")
                
        except ValueError:
            print("\n⚠️ Response is not valid JSON")
            print(f"Response text: {response.text[:1000]}...")
            
    except requests.exceptions.Timeout:
        print("\n❌ Request timed out after 120 seconds")
        print("This suggests the API endpoint is not responding in a timely manner.")
        print("Possible causes:")
        print("1. The Flask application might not be running or accessible")
        print("2. The request might be getting stuck in the processing pipeline")
        print("3. There might be an infinite loop or deadlock in the code")
        print("\nNext steps:")
        print("1. Check if the Flask application is running")
        print("2. Review the application logs for any errors")
        print("3. Try reducing the input size to see if it processes faster")
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response headers: {dict(e.response.headers)}")
            try:
                print(f"Response body: {e.response.text}")
            except:
                print("Could not read response body")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\nTest complete!")

if __name__ == "__main__":
    test_api_endpoint()
