#!/usr/bin/env python3
"""
Fast test to verify CourtListener API is working correctly.
"""

import requests
import json
import time
import sys

def test_courtlistener_api():
    """Test CourtListener API directly."""
    
    print("=== Fast CourtListener API Test ===")
    
    # Test cases
    test_cases = [
        "347 U.S. 483",  # Brown v. Board of Education
        "410 U.S. 113",  # Roe v. Wade
        "95 L.Ed.2",     # The problematic one from logs
    ]
    
    # API endpoint
    url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    
    # Prevent use of v3 CourtListener API endpoints
    if 'v3' in url:
        print("ERROR: v3 CourtListener API endpoint detected. Please use v4 only.")
        sys.exit(1)

    # Headers
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    
    # Try to get API key from config
    try:
        import os
        config_path = os.path.join("src", "config.json")
        with open(config_path, "r") as f:
            config = json.load(f)
            api_key = config.get("courtlistener_api_key")
            if api_key:
                headers["Authorization"] = f"Token {api_key}"
                print(f"Using API key: {api_key[:10]}...")
            else:
                print("No API key found in config")
    except Exception as e:
        print(f"Error loading config: {e}")
    
    for citation in test_cases:
        print(f"\nTesting citation: {citation}")
        start_time = time.time()
        
        try:
            # Prepare data
            data = {"text": citation}
            
            # Make request
            response = requests.post(url, headers=headers, data=data, timeout=10)
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            elapsed = time.time() - start_time
            
            print(f"  Response time: {elapsed:.2f}s")
            print(f"  Status: {response.status_code}")
            print(f"  Result: {json.dumps(result, indent=2)}")
            
            # Check if citation was found
            if result and len(result) > 0:
                first_result = result[0]
                if first_result.get("status") == 200 and first_result.get("clusters"):
                    cluster = first_result["clusters"][0]
                    print(f"  ✓ FOUND: {cluster.get('case_name', 'Unknown')}")
                    print(f"  URL: {cluster.get('absolute_url', 'N/A')}")
                else:
                    print(f"  ✗ NOT FOUND: {first_result.get('error_message', 'Unknown error')}")
            else:
                print("  ✗ No results returned")
                
        except requests.exceptions.Timeout:
            print(f"  ✗ TIMEOUT after {time.time() - start_time:.2f}s")
        except Exception as e:
            print(f"  ✗ ERROR: {e}")

if __name__ == "__main__":
    test_courtlistener_api() 