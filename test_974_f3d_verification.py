#!/usr/bin/env python3
"""
Test why 974 F.3d 9 is showing as unverified
"""

import requests
import re

citation = "974 F.3d 9"
volume = "974"
page = "9"

print("=" * 80)
print(f"TESTING VERIFICATION: {citation}")
print("=" * 80)
print()

# Test Justia URL
justia_url = f"https://law.justia.com/cases/federal/appellate-courts/F3/{volume}/{page}/"
print(f"Testing Justia URL: {justia_url}")

try:
    response = requests.get(justia_url, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        content = response.text
        print(f"Content Length: {len(content)} characters")
        
        # Try to extract case name
        title_match = re.search(r'<title>([^<]+)</title>', content, re.IGNORECASE)
        if title_match:
            title = title_match.group(1)
            print(f"Page Title: {title}")
            
            # Check if it contains case name
            if 'v.' in title or 'v ' in title:
                print(f"✓ Case name found in title")
            else:
                print(f"✗ No case name pattern in title")
        else:
            print("✗ No title tag found")
            
        # Check for case name in content
        case_name_patterns = [
            r'<h1[^>]*>([^<]+v\.?[^<]+)</h1>',
            r'<h2[^>]*>([^<]+v\.?[^<]+)</h2>',
            r'class="case-name"[^>]*>([^<]+)</span>',
        ]
        
        for pattern in case_name_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                print(f"✓ Case name pattern matched: {match.group(1)[:100]}")
                break
        else:
            print("✗ No case name pattern matched in content")
            
    elif response.status_code == 404:
        print("✗ Case not found (404)")
    else:
        print(f"✗ HTTP {response.status_code}")
        
except Exception as e:
    print(f"✗ Error: {e}")

print()
print("=" * 80)
print("CHECKING VERIFICATION LOGIC")
print("=" * 80)
print()

# Check what the verification system expects
print("F.3d citations should verify via:")
print("1. Justia (primary)")
print("2. CourtListener API (fallback)")
print()

# Test CourtListener
print("Testing CourtListener API:")
courtlistener_url = f"https://www.courtlistener.com/api/rest/v3/search/?citation={citation}&type=o"
print(f"URL: {courtlistener_url}")

try:
    response = requests.get(courtlistener_url, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        count = data.get('count', 0)
        print(f"Results count: {count}")
        
        if count > 0 and data.get('results'):
            result = data['results'][0]
            print(f"✓ Case name: {result.get('caseName', 'N/A')}")
            print(f"✓ Date filed: {result.get('dateFiled', 'N/A')}")
            print(f"✓ Court: {result.get('court', 'N/A')}")
        else:
            print("✗ No results found")
    else:
        print(f"✗ HTTP {response.status_code}")
        
except Exception as e:
    print(f"✗ Error: {e}")
