#!/usr/bin/env python3
"""
Check Law Resource.org site structure
"""

import requests
import re

def check_law_resource_structure():
    """Check Law Resource.org site structure and find search method"""
    
    print("🔍 Checking Law Resource.org site structure...")
    
    try:
        # Check main page
        response = requests.get("https://law.resource.org", timeout=10)
        print(f"📊 Main page status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            
            # Look for search forms or patterns
            search_patterns = [
                r'<form[^>]*action="([^"]*search[^"]*)"',
                r'<input[^>]*name="([^"]*)"[^>]*type="search"',
                r'href="([^"]*search[^"]*)"',
                r'href="([^"]*161[^"]*)"',  # Look for direct links to 161 F.3d 584
            ]
            
            for pattern in search_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    print(f"✅ Found pattern: {pattern}")
                    for match in matches[:3]:  # Show first 3 matches
                        print(f"   - {match}")
            
            # Look for any links that might contain legal opinions
            link_pattern = r'href="([^"]*\.(pdf|html|htm))"'
            links = re.findall(link_pattern, content, re.IGNORECASE)
            print(f"📊 Found {len(links)} links to documents")
            
            # Look specifically for federal reporter patterns
            reporter_pattern = r'(\d+\s+F\.\d+(?:\s+\d+)?)'
            reporter_matches = re.findall(reporter_pattern, content)
            if reporter_matches:
                print(f"✅ Found reporter citations: {reporter_matches[:5]}")
            
            # Save a sample of the content for inspection
            print(f"\n📝 First 1000 chars of homepage:")
            print("=" * 50)
            print(content[:1000])
            print("=" * 50)
            
        else:
            print(f"❌ Cannot access main page: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_law_resource_structure()
