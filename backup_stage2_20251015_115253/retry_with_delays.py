"""
Retry fetching with delays and different methods
"""

import requests
import time
from src.config import COURTLISTENER_API_KEY

url = "https://www.courtlistener.com/opinion/10320728/grace-v-perkins-restaurant/"

print("="*80)
print("TESTING DIFFERENT FETCH METHODS")
print("="*80)

# Method 1: Simple GET
print(f"\n1. Simple GET request...")
response = requests.get(url, timeout=30)
print(f"   Status: {response.status_code}")
print(f"   Content-Length: {len(response.text)}")
print(f"   Headers: {dict(response.headers)}")

# Method 2: With User-Agent
print(f"\n2. GET with User-Agent...")
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
response = requests.get(url, headers=headers, timeout=30)
print(f"   Status: {response.status_code}")
print(f"   Content-Length: {len(response.text)}")

# Method 3: With API Key
print(f"\n3. GET with API Key...")
headers = {
    'Authorization': f'Token {COURTLISTENER_API_KEY}',
    'User-Agent': 'Mozilla/5.0'
}
response = requests.get(url, headers=headers, timeout=30)
print(f"   Status: {response.status_code}")
print(f"   Content-Length: {len(response.text)}")

# Method 4: Wait and retry (for 202 responses)
if response.status_code == 202:
    print(f"\n4. Got 202 - waiting 3 seconds and retrying...")
    time.sleep(3)
    response = requests.get(url, headers=headers, timeout=30)
    print(f"   Status: {response.status_code}")
    print(f"   Content-Length: {len(response.text)}")

# Method 5: Try without the slug (just the ID)
print(f"\n5. Trying URL without slug...")
url_no_slug = "https://www.courtlistener.com/opinion/10320728/"
response = requests.get(url_no_slug, headers=headers, timeout=30)
print(f"   Status: {response.status_code}")
print(f"   Content-Length: {len(response.text)}")

# Method 6: Check if it redirects
print(f"\n6. Following redirects...")
response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
print(f"   Status: {response.status_code}")
print(f"   Final URL: {response.url}")
print(f"   Redirect history: {[r.url for r in response.history]}")
print(f"   Content-Length: {len(response.text)}")

if response.text:
    print(f"\n   Content preview:")
    print(f"   {response.text[:300]}")

# Method 7: Try the actual cluster URL (from our earlier search)
print(f"\n7. Trying actual Grace case cluster URL...")
grace_cluster_url = "https://www.courtlistener.com/opinion/cluster/10320728/grace-v-perkins-restaurant/"
response = requests.get(grace_cluster_url, headers=headers, timeout=30)
print(f"   Status: {response.status_code}")
print(f"   Content-Length: {len(response.text)}")

if response.text:
    print(f"\n   Content preview:")
    print(f"   {response.text[:300]}")

print("\n" + "="*80)
