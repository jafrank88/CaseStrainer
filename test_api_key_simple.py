#!/usr/bin/env python3
"""
Simple test to verify the CourtListener API key is working
"""

import os
import requests
import sys

def test_courtlistener_api():
    """Test the CourtListener API with the configured key"""
    print("🔑 Testing CourtListener API Key")
    print("=" * 40)
    
    # Get API key from environment
    api_key = os.environ.get('COURTLISTENER_API_KEY')
    print(f"API Key: {api_key[:10]}..." if api_key else "No API key found")
    
    if not api_key:
        print("❌ No API key found in environment")
        return False
    
    # Test with a simple citation
    url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    
    # Prevent use of v3 CourtListener API endpoints
    if 'v3' in url:
        print("ERROR: v3 CourtListener API endpoint detected. Please use v4 only.")
        sys.exit(1)

    headers = {"Authorization": f"Token {api_key}"}
    data = {"citations": ["123 F.3d 456"]}
    
    try:
        print("Testing API connection...")
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API key is valid!")
            print(f"Found {len(result)} result clusters")
            return True
        elif response.status_code == 401:
            print("❌ API key is invalid")
            return False
        else:
            print(f"⚠️  API returned status {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

if __name__ == "__main__":
    test_courtlistener_api() 