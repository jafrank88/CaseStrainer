"""Test FindLaw main search box"""
import requests
import re

citation = "11 F.4th 1133"
case_name = "Alam v. Garland"

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
})

print(f"Testing FindLaw search box for: {citation}\n")
print("="*80)

# Try the main FindLaw search
print("\n1. FindLaw Main Search Box")
print("-"*80)

# The search box likely posts to a search endpoint
search_url = "https://caselaw.findlaw.com/search"
print(f"Search URL: {search_url}")

try:
    # Try GET request with query parameter
    params = {'q': citation}
    resp = session.get(search_url, params=params, timeout=10)
    print(f"GET Status: {resp.status_code}")
    print(f"Final URL: {resp.url}")
    print(f"Response length: {len(resp.text)}")
    
    if resp.status_code == 200:
        # Look for case results
        if 'Alam' in resp.text or 'alam' in resp.text:
            print("✅ 'Alam' found in response!")
        
        if citation in resp.text or citation.replace(' ', '') in resp.text:
            print(f"✅ Citation '{citation}' found in response!")
        
        # Look for result links
        result_pattern = r'href="(/court/[^"]+)"'
        matches = re.findall(result_pattern, resp.text)
        print(f"Court case links found: {len(matches)}")
        
        if matches:
            print(f"\nFirst 3 results:")
            for i, match in enumerate(matches[:3]):
                print(f"  {i+1}. https://caselaw.findlaw.com{match}")
                
        # Look for different result format
        case_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]*Alam[^<]*)</a>'
        case_matches = re.findall(case_pattern, resp.text, re.IGNORECASE)
        if case_matches:
            print(f"\nCase links with 'Alam': {len(case_matches)}")
            for url, text in case_matches[:2]:
                print(f"  - {text[:60]}")
                print(f"    URL: {url[:80]}")
                
    elif resp.status_code == 403:
        print("❌ 403 Forbidden - blocked")
    
except Exception as e:
    print(f"❌ Error: {e}")

# Try alternative search URL patterns
print("\n\n2. Alternative FindLaw Search Patterns")
print("-"*80)

alternative_urls = [
    f"https://caselaw.findlaw.com/search.html?q={citation.replace(' ', '+')}",
    f"https://caselaw.findlaw.com/summary/search.html?q={citation.replace(' ', '+')}",
]

for alt_url in alternative_urls:
    print(f"\nTrying: {alt_url[:80]}...")
    try:
        resp = session.get(alt_url, timeout=10, allow_redirects=True)
        print(f"  Status: {resp.status_code}")
        if resp.status_code == 200:
            if 'Alam' in resp.text:
                print(f"  ✅ Found 'Alam' in response")
                # Look for results
                result_count = resp.text.count('href="/court/')
                print(f"  Found {result_count} court case links")
        elif resp.status_code == 403:
            print(f"  ❌ 403 Forbidden")
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("\n" + "="*80)
print("Test complete!")
