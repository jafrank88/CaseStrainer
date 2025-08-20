#!/usr/bin/env python3
"""
Debug Fallback Search Results

This script helps debug why the fallback verifier is not finding citations
by showing the actual search results and HTML content returned.
"""

import asyncio
import sys
import os
import requests
from urllib.parse import quote

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def debug_fallback_search():
    """Debug the fallback search by showing actual results."""
    
    print("=== Debugging Fallback Search Results ===")
    print()
    
    # Test citation
    citation = "188 Wn.2d 114"
    case_name = "In re Marriage of Black"
    
    print(f"Testing citation: {citation}")
    print(f"Case name: {case_name}")
    print()
    
    # Test Justia search
    print("=== Testing Justia Search ===")
    try:
        search_query = f"{citation} {case_name}"
        search_url = f"https://law.justia.com/search?query={quote(search_query)}"
        
        print(f"Search URL: {search_url}")
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'CaseStrainer Citation Verifier (Educational Research)'
        })
        
        response = session.get(search_url, timeout=15)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            
            # Look for case links
            case_link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
            matches = re.findall(case_link_pattern, content, re.IGNORECASE)
            
            print(f"Found {len(matches)} total links")
            
            # Show first few links
            for i, (link_url, link_text) in enumerate(matches[:10]):
                print(f"Link {i+1}:")
                print(f"  URL: {link_url}")
                print(f"  Text: {link_text[:100]}...")
                print()
            
            # Look specifically for our citation
            if citation.replace(' ', '').lower() in content.replace(' ', '').lower():
                print("✅ Citation found in content")
            else:
                print("❌ Citation NOT found in content")
            
            # Look for case name patterns
            case_patterns = [
                r'([A-Z][a-zA-Z\s&.]+\s+v\.?\s+[A-Z][a-zA-Z\s&.]+)',  # X v. Y
                r'(In re [A-Z][a-zA-Z\s&.]+)',  # In re X
            ]
            
            for pattern in case_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    print(f"Found case name patterns: {matches[:5]}")
                    break
            
        else:
            print(f"Failed to get content: {response.status_code}")
            
    except Exception as e:
        print(f"Error testing Justia: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test FindLaw search
    print("=== Testing FindLaw Search ===")
    try:
        search_query = f"{citation} {case_name}"
        search_url = f"https://caselaw.findlaw.com/search?query={quote(search_query)}"
        
        print(f"Search URL: {search_url}")
        
        response = session.get(search_url, timeout=15)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            
            # Look for case links
            case_link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
            matches = re.findall(case_link_pattern, content, re.IGNORECASE)
            
            print(f"Found {len(matches)} total links")
            
            # Show first few links
            for i, (link_url, link_text) in enumerate(matches[:10]):
                print(f"Link {i+1}:")
                print(f"  URL: {link_url}")
                print(f"  Text: {link_text[:100]}...")
                print()
            
            # Look specifically for our citation
            if citation.replace(' ', '').lower() in content.replace(' ', '').lower():
                print("✅ Citation found in content")
            else:
                print("❌ Citation NOT found in content")
                
        else:
            print(f"Failed to get content: {response.status_code}")
            
    except Exception as e:
        print(f"Error testing FindLaw: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test CaseMine search
    print("=== Testing CaseMine Search ===")
    try:
        search_query = f"{citation} {case_name}"
        search_url = f"https://www.casemine.com/search?q={quote(search_query)}"
        
        print(f"Search URL: {search_url}")
        
        response = session.get(search_url, timeout=15)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            
            # Look for case links
            case_link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
            matches = re.findall(case_link_pattern, content, re.IGNORECASE)
            
            print(f"Found {len(matches)} total links")
            
            # Show first few links
            for i, (link_url, link_text) in enumerate(matches[:10]):
                print(f"Link {i+1}:")
                print(f"  URL: {link_url}")
                print(f"  Text: {link_text[:100]}...")
                print()
            
            # Look specifically for our citation
            if citation.replace(' ', '').lower() in content.replace(' ', '').lower():
                print("✅ Citation found in content")
            else:
                print("❌ Citation NOT found in content")
                
        else:
            print(f"Failed to get content: {response.status_code}")
            
    except Exception as e:
        print(f"Error testing CaseMine: {e}")
    
    print("\n=== Summary ===")
    print("This debug script shows what the legal database searches are actually returning.")
    print("If no citations are found, it could be due to:")
    print("1. Site structure changes")
    print("2. Rate limiting or blocking")
    print("3. Search query format changes")
    print("4. Citation format variations")
    print()
    print("Next steps:")
    print("1. Check if the search URLs are correct")
    print("2. Verify the search patterns still work")
    print("3. Test with different citation formats")
    print("4. Consider using the existing working components instead")

if __name__ == "__main__":
    import re
    asyncio.run(debug_fallback_search())
