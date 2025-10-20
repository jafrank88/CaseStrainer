"""Test FindLaw, Justia, and VLex for Alam v. Garland"""
import requests
import re

citation = "11 F.4th 1133"
case_name = "Alam v. Garland"

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

print("Testing additional legal sources for: 11 F.4th 1133 (Alam v. Garland)\n")
print("="*80)

# Test FindLaw
print("\n1. FINDLAW")
print("-"*80)
findlaw_search = f"https://caselaw.findlaw.com/search.html?q={citation.replace(' ', '+')}"
print(f"Search URL: {findlaw_search}")
try:
    resp = session.get(findlaw_search, timeout=10)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        # Look for case links
        case_pattern = r'href="(/court/[^"]+)"[^>]*>([^<]*Alam[^<]*)</a>'
        matches = re.findall(case_pattern, resp.text, re.IGNORECASE)
        print(f"Case links found: {len(matches)}")
        if matches:
            print(f"First match: {matches[0]}")
            # Try fetching the case page
            case_url = f"https://caselaw.findlaw.com{matches[0][0]}"
            print(f"\nFetching case page: {case_url}")
            case_resp = session.get(case_url, timeout=10)
            print(f"Case page status: {case_resp.status_code}")
            if case_resp.status_code == 200:
                # Look for case name in title
                title_match = re.search(r'<title>([^<]*v\.[^<]*)</title>', case_resp.text, re.IGNORECASE)
                if title_match:
                    print(f"✅ Case name extracted: '{title_match.group(1)}'")
    elif resp.status_code == 403:
        print("⚠️ 403 Forbidden - Anti-bot protection")
except Exception as e:
    print(f"❌ Error: {e}")

# Test Justia
print("\n\n2. JUSTIA")
print("-"*80)
justia_search = f"https://law.justia.com/search?query={citation.replace(' ', '+')}"
print(f"Search URL: {justia_search}")
try:
    resp = session.get(justia_search, timeout=10)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        # Look for case links
        case_pattern = r'href="(https://law\.justia\.com/cases/[^"]+)"[^>]*>([^<]*)</a>'
        matches = re.findall(case_pattern, resp.text, re.IGNORECASE)
        print(f"Case links found: {len(matches)}")
        
        # Filter for ones with "Alam" or "v."
        relevant = [(url, text) for url, text in matches if 'v.' in text.lower() or 'alam' in text.lower()]
        print(f"Relevant links: {len(relevant)}")
        
        if relevant:
            case_url, link_text = relevant[0]
            print(f"First relevant: {link_text[:60]}")
            print(f"URL: {case_url[:80]}")
            
            # Fetch the case page
            print(f"\nFetching case page...")
            case_resp = session.get(case_url, timeout=10)
            print(f"Case page status: {case_resp.status_code}")
            if case_resp.status_code == 200:
                # Look for case name
                title_match = re.search(r'<h1[^>]*>([^<]*v\.[^<]*)</h1>', case_resp.text, re.IGNORECASE)
                if not title_match:
                    title_match = re.search(r'<title>([^<]*v\.[^<]*)</title>', case_resp.text, re.IGNORECASE)
                if title_match:
                    print(f"✅ Case name extracted: '{title_match.group(1)[:60]}'")
except Exception as e:
    print(f"❌ Error: {e}")

# Test VLex
print("\n\n3. VLEX")
print("-"*80)
vlex_search = f"https://vlex.com/search?q={citation.replace(' ', '+')}"
print(f"Search URL: {vlex_search}")
try:
    resp = session.get(vlex_search, timeout=10)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"Response length: {len(resp.text)}")
        # Look for case links
        if 'Alam' in resp.text or 'alam' in resp.text:
            print("✅ 'Alam' found in response")
        if citation in resp.text or citation.replace(' ', '') in resp.text:
            print(f"✅ Citation '{citation}' found in response")
            
        # Look for VLex case URLs
        case_pattern = r'href="(/vid/[^"]+)"'
        matches = re.findall(case_pattern, resp.text)
        print(f"VLex case links found: {len(matches)}")
        if matches:
            print(f"First link: /vid/{matches[0]}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*80)
print("Test complete!")
