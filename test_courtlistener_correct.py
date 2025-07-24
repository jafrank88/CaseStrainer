#!/usr/bin/env python3
"""
Test CourtListener API with correct format.
"""

import requests
import json
import time
import sys

def test_courtlistener_correct():
    """Test CourtListener API with correct format."""
    
    print("=== CourtListener API Test (Correct Format) ===")
    
    # Test cases
    test_cases = [
        "347 U.S. 483",  # Brown v. Board of Education
        "410 F.2d 123",  # Invalid but should fail fast
        "95 L.Ed.2d 123"  # Invalid but should fail fast
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
        api_key = config.get("courtlistener_api_key", "")
        if api_key:
            headers["Authorization"] = f"Token {api_key}"
            print(f"Using API key: {api_key[:10]}...")
        else:
            print("No API key found")
    except Exception as e:
        print(f"Error loading config: {e}")
    
    for i, citation in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {citation} ---")
        
        start_time = time.time()
        
        try:
            # Make the API request with correct format
            data = {"text": citation}  # Use 'text' parameter, not 'citation'
            response = requests.post(url, headers=headers, data=data, timeout=10)
            
            response_time = time.time() - start_time
            print(f"Response time: {response_time:.2f}s")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                
                if data.get("count", 0) > 0:
                    print("✅ Found results")
                else:
                    print("❌ No results found")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"❌ Request timed out after {time.time() - start_time:.2f}s")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_courtlistener_correct() 