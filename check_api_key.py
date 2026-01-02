#!/usr/bin/env python3
"""
Check if CourtListener API key is available
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import get_config_value

def check_api_key():
    """Check if CourtListener API key is available"""
    
    print("🔍 CHECKING COURTLISTENER API KEY")
    print("=" * 40)
    
    api_key = get_config_value("COURTLISTENER_API_KEY", "")
    
    if api_key:
        print(f"✅ API key found: {api_key[:10]}...{api_key[-10:]}")
        print(f"   Length: {len(api_key)} characters")
        
        # Test the API
        import requests
        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json"
        }
        api_url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
        data = {"text": "161 F.3d 584"}
        
        print(f"\n📋 Testing API with citation: 161 F.3d 584")
        try:
            response = requests.post(api_url, headers=headers, json=data, timeout=5.0)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result_data = response.json()
                print(f"   Results: {len(result_data)} items")
                if result_data:
                    result = result_data[0]
                    print(f"   Case name: {result.get('case_name', 'N/A')}")
                    print(f"   Date: {result.get('date', 'N/A')}")
                    print("✅ API working correctly!")
            else:
                print(f"   Error: {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    else:
        print("❌ No API key found")
        print("   Check .env file for COURTLISTENER_API_KEY")

if __name__ == "__main__":
    check_api_key()
