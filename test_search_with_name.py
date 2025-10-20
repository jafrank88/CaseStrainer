"""Test searching CaseMine with case name"""
import requests
import re

citation = "11 F.4th 1133"
case_name = "Alam v. Garland"

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

# Test with case name + citation (what our code does now)
search_query = f"{case_name} {citation}"
url = f"https://www.casemine.com/search?q={search_query.replace(' ', '+')}"

print(f"Search query: '{search_query}'")
print(f"URL: {url}")
print()

resp = session.get(url, timeout=10)
print(f"Status: {resp.status_code}")
print(f"Length: {len(resp.text)}")

# Look for judgment links
pattern = r'(?:href="|/)(/judgeme?nt/us/[a-f0-9]+)'
matches = re.findall(pattern, resp.text, re.IGNORECASE)
matches = list(set([m if m.startswith('/') else f'/{m}' for m in matches]))

print(f"Judgment links found: {len(matches)}")
if matches:
    print(f"\nFirst 3 links:")
    for i, link in enumerate(matches[:3]):
        print(f"  {i+1}. https://www.casemine.com{link}")
