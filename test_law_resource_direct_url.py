#!/usr/bin/env python3
"""
Test direct access to Law Resource.org URL
"""

import requests

def test_law_resource_direct_url():
    """Test if the Law Resource.org URL pattern works"""
    
    citation = "161 F.3d 584"
    # Build direct URL based on the pattern you found
    direct_url = "https://law.resource.org/pub/us/case/reporter/F3/161/584"
    
    print(f"🔍 Testing direct URL: {direct_url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(direct_url, headers=headers, timeout=10)
        
        print(f"📊 Status code: {response.status_code}")
        print(f"📊 Content length: {len(response.text)}")
        
        if response.status_code == 200:
            content = response.text
            
            # Check if citation is in content
            if citation in content or "F.3d 161" in content:
                print("✅ SUCCESS: Citation found in content!")
                
                # Look for case name
                if "v." in content:
                    print("✅ Case name pattern found in content")
                    
                    # Extract title
                    import re
                    title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
                    if title_match:
                        print(f"📋 Title: {title_match.group(1)}")
                
                return True
            else:
                print("❌ Citation not found in content")
                print(f"📝 First 500 chars: {content[:500]}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_law_resource_direct_url()
    
    if success:
        print("\n✅ Law Resource.org direct URL is accessible!")
    else:
        print("\n❌ Law Resource.org direct URL has issues")
