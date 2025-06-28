#!/usr/bin/env python3
"""
Test script to verify CourtListener API key functionality
"""

import requests
import json
import os
import sys

def test_courtlistener_api():
    """Test the CourtListener API with a known valid citation"""
    
    # Load API key from config.json
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        api_key = config.get('COURTLISTENER_API_KEY')
        if not api_key:
            print("❌ No CourtListener API key found in config.json")
            return False
    except Exception as e:
        print(f"❌ Error loading config.json: {e}")
        return False
    
    print(f"✅ Found API key: {api_key[:8]}...{api_key[-4:]}")
    
    # Test citation (a well-known Washington case)
    test_citation = "97 Wn.2d 30"
    
    # Test URL for citation lookup
    url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "CaseStrainer-Test/1.0"
    }
    
    data = {
        "text": test_citation
    }
    
    print(f"🔍 Testing citation: {test_citation}")
    print(f"🌐 URL: {url}")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API call successful!")
            print(f"📄 Response: {json.dumps(result, indent=2)}")
            return True
        elif response.status_code == 401:
            print("❌ API key is invalid or expired")
            return False
        elif response.status_code == 429:
            print("⚠️ Rate limited - API key might be working but hit rate limit")
            return False
        else:
            print(f"❌ API error: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing CourtListener API...")
    success = test_courtlistener_api()
    
    if success:
        print("\n✅ CourtListener API is working correctly!")
        print("The issue with citation verification might be elsewhere.")
    else:
        print("\n❌ CourtListener API is not working.")
        print("Please check your API key or contact CourtListener support.") 