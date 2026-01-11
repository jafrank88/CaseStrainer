#!/usr/bin/env python3
"""
Test verification of 591 U.S. 1 (DHS v. Regents)
"""

import requests
import re

citation = "591 U.S. 1"
volume = "591"
page = "1"

# Try FindLaw direct URL
direct_url = f"https://caselaw.findlaw.com/court/us-supreme-court/{volume}/{page}.html"
print(f"Testing FindLaw URL: {direct_url}")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

try:
    response = requests.get(direct_url, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        content = response.text
        
        # Try to extract case name
        case_name_patterns = [
            r"<h1[^>]*>([^<]+v\.?[^<]+)</h1>",
            r"<title>([^<]+v\.?[^<]+)\s*\|",
            r'<meta\s+property="og:title"\s+content="([^"]+v\.?[^"]+)"',
        ]
        
        for pattern in case_name_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                print(f"Found case name: {match.group(1).strip()}")
                break
        else:
            print("Could not extract case name from page")
            # Print first 500 chars to see what's there
            print("\nFirst 500 chars of content:")
            print(content[:500])
    elif response.status_code == 404:
        print("❌ Case not found (404)")
        print("\nThis citation may not exist in FindLaw's database.")
        print("Possible reasons:")
        print("1. Too recent (2020) - FindLaw may not have it yet")
        print("2. Citation format issue")
        print("3. Case exists but at different URL structure")
    else:
        print(f"❌ HTTP {response.status_code}")
        
except Exception as e:
    print(f"❌ Error: {e}")

# Try CourtListener API
print("\n" + "="*60)
print("Testing CourtListener API:")
print("="*60)

courtlistener_url = f"https://www.courtlistener.com/api/rest/v3/search/?citation={citation}&type=o"
print(f"URL: {courtlistener_url}")

try:
    response = requests.get(courtlistener_url, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Results count: {data.get('count', 0)}")
        
        if data.get('results'):
            result = data['results'][0]
            print(f"Case name: {result.get('caseName', 'N/A')}")
            print(f"Date filed: {result.get('dateFiled', 'N/A')}")
            print(f"Court: {result.get('court', 'N/A')}")
        else:
            print("No results found")
    else:
        print(f"❌ HTTP {response.status_code}")
        
except Exception as e:
    print(f"❌ Error: {e}")
