#!/usr/bin/env python3
"""Check URL redirect behavior"""

import requests

url = "http://www.courts.wa.gov/opinions/pdf/D2%2059366-1-II%20Unpublished%20Opinion.pdf"

print("🔍 CHECKING URL REDIRECT BEHAVIOR")
print("=" * 50)

try:
    # Follow redirects
    response = requests.get(url, allow_redirects=True, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Final URL: {response.url}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"Content-Length: {response.headers.get('content-length')}")
    
    # Check if it's actually a PDF
    content_type = response.headers.get('content-type', '')
    if 'pdf' in content_type.lower():
        print("✅ Successfully retrieved PDF")
    else:
        print(f"⚠️  Content type is {content_type}, not PDF")
        print("First 500 chars of content:")
        print(response.text[:500])
        
except Exception as e:
    print(f"❌ Error: {e}")
