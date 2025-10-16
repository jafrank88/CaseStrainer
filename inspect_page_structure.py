"""
Inspect the HTML page structure for frames, iframes, or dynamic content
"""

import requests
from bs4 import BeautifulSoup

url = "https://www.courtlistener.com/opinion/10320728/grace-v-perkins-restaurant/"

print("="*80)
print("INSPECTING PAGE STRUCTURE")
print("="*80)
print(f"\nURL: {url}")

# Fetch the HTML page (NOT the API)
print(f"\n1. Fetching HTML page...")
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

response = requests.get(url, headers=headers, timeout=30)
print(f"   Status: {response.status_code}")
print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
print(f"   Content Length: {len(response.text):,} chars")

html_content = response.text

# Parse with BeautifulSoup
soup = BeautifulSoup(html_content, 'html.parser')

# Check for frames and iframes
print(f"\n2. Checking for frames...")
frames = soup.find_all('frame')
iframes = soup.find_all('iframe')
print(f"   <frame> tags: {len(frames)}")
print(f"   <iframe> tags: {len(iframes)}")

if iframes:
    for i, iframe in enumerate(iframes, 1):
        src = iframe.get('src', 'N/A')
        print(f"     iframe {i}: {src}")

# Check page title
title = soup.find('title')
print(f"\n3. Page Title:")
print(f"   {title.text if title else 'N/A'}")

# Look for case name in common locations
print(f"\n4. Searching for case name in HTML...")

# Check meta tags
case_name_meta = soup.find('meta', {'property': 'og:title'}) or soup.find('meta', {'name': 'title'})
if case_name_meta:
    print(f"   Meta title: {case_name_meta.get('content', 'N/A')}")

# Check h1, h2 headers
headers_found = []
for tag in ['h1', 'h2', 'h3']:
    for header in soup.find_all(tag):
        text = header.get_text(strip=True)
        if text and len(text) < 200:
            headers_found.append((tag, text))

print(f"\n5. Headers found:")
for tag, text in headers_found[:10]:
    print(f"   <{tag}>: {text[:100]}")

# Check for "Grace" in the page
print(f"\n6. Searching for 'Grace' in page...")
grace_mentions = html_content.count('Grace')
print(f"   'Grace' appears {grace_mentions} times")

if grace_mentions > 0:
    # Find context around "Grace"
    import re
    grace_contexts = re.findall(r'.{0,50}Grace.{0,50}', html_content, re.IGNORECASE)
    print(f"\n   First 5 contexts:")
    for i, context in enumerate(grace_contexts[:5], 1):
        print(f"   {i}. ...{context}...")

# Check for "System Agency" (the wrong case)
print(f"\n7. Searching for 'System Agency' in page...")
system_mentions = html_content.count('System Agency')
print(f"   'System Agency' appears {system_mentions} times")

# Look for JavaScript data
print(f"\n8. Checking for JavaScript data...")
scripts = soup.find_all('script')
print(f"   Found {len(scripts)} <script> tags")

# Look for JSON-LD structured data
json_ld = soup.find_all('script', type='application/ld+json')
if json_ld:
    print(f"\n   Found {len(json_ld)} JSON-LD script(s)")
    import json
    for i, script in enumerate(json_ld, 1):
        try:
            data = json.loads(script.string)
            print(f"\n   JSON-LD {i}:")
            print(f"   {json.dumps(data, indent=2)[:500]}")
        except:
            pass

# Check for data attributes
print(f"\n9. Checking for data-* attributes...")
elements_with_data = soup.find_all(attrs={'data-case-name': True})
if elements_with_data:
    for elem in elements_with_data[:5]:
        print(f"   Found: data-case-name = {elem.get('data-case-name')}")

# Look for Vue.js or React data
vue_app = soup.find(id='app') or soup.find(class_='vue-app')
if vue_app:
    print(f"\n10. Vue.js app found!")
    print(f"   {str(vue_app)[:200]}...")

# Check if there's a redirect
if response.history:
    print(f"\n11. REDIRECT DETECTED!")
    print(f"   Original URL: {response.history[0].url}")
    print(f"   Final URL: {response.url}")

print("\n" + "="*80)
print("INSPECTION COMPLETE")
print("="*80)
