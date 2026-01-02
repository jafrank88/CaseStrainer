#!/usr/bin/env python3
"""
Test Law Resource.org search directly
"""

import requests
from urllib.parse import quote_plus

def test_law_resource_search():
    """Test Law Resource.org search functionality"""
    
    print("🔍 Testing Law Resource.org search directly...")
    
    # Test search for 161 F.3d 584
    query = "161 F.3d 584"
    search_url = f"https://law.resource.org/search?q={quote_plus(query)}"
    
    print(f"📡 Searching: {search_url}")
    
    try:
        response = requests.get(search_url, timeout=10)
        print(f"📊 Status code: {response.status_code}")
        print(f"📊 Content length: {len(response.text)}")
        
        if response.status_code == 200:
            content = response.text.lower()
            if "161 f.3d 584" in content:
                print("✅ Found citation in search results!")
                return True
            else:
                print("❌ Citation not found in search results")
                print(f"📝 First 500 chars: {response.text[:500]}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_law_resource_search()
    
    if success:
        print("\n✅ Law Resource.org search is working!")
    else:
        print("\n❌ Law Resource.org search has issues")
