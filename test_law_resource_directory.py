#!/usr/bin/env python3
"""
Test Law Resource.org directory structure
"""

import requests
import re

def test_law_resource_directory():
    """Test Law Resource.org directory structure"""
    
    base_url = "https://law.resource.org/pub/us/case/reporter/F3/161/"
    
    print(f"🔍 Testing directory: {base_url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(base_url, headers=headers, timeout=10)
        
        print(f"📊 Status code: {response.status_code}")
        print(f"📊 Content length: {len(response.text)}")
        
        if response.status_code == 200:
            content = response.text
            
            # Look for links to pages
            link_pattern = r'href="([^"]*)"'
            links = re.findall(link_pattern, content)
            
            print(f"📊 Found {len(links)} links")
            
            # Look for numeric links that might be page numbers
            numeric_links = []
            for link in links:
                if link.isdigit():
                    numeric_links.append(link)
            
            if numeric_links:
                print(f"✅ Found numeric links (possible page numbers): {numeric_links[:10]}")
                
                # Try the first few numeric links
                for page in numeric_links[:5]:
                    test_url = base_url + page
                    print(f"\n🔍 Testing: {test_url}")
                    
                    try:
                        page_response = requests.get(test_url, headers=headers, timeout=5)
                        if page_response.status_code == 200:
                            page_content = page_response.text
                            if "F.3d" in page_content or "v." in page_content:
                                print(f"✅ SUCCESS: Found valid page at {page}")
                                
                                # Look for case name
                                if "v." in page_content:
                                    title_match = re.search(r'<title[^>]*>([^<]+)</title>', page_content, re.IGNORECASE)
                                    if title_match:
                                        print(f"📋 Title: {title_match.group(1)}")
                                
                                return test_url
                        else:
                            print(f"❌ Status: {page_response.status_code}")
                    except Exception as e:
                        print(f"❌ Error: {e}")
            
            print(f"📝 First 1000 chars of directory:")
            print("=" * 50)
            print(content[:1000])
            print("=" * 50)
            
        else:
            print(f"❌ HTTP error: {response.status_code}")
            
        return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    result = test_law_resource_directory()
    
    if result:
        print(f"\n✅ Found working URL: {result}")
    else:
        print("\n❌ No working URL found")
