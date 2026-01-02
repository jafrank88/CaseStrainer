#!/usr/bin/env python3
"""Test CourtListener lookup for 75 Wash. 581."""
import requests
import os

# Get API key
api_key = os.environ.get('COURTLISTENER_API_KEY', '')

# Test the citation lookup API
citation = "75 Wash. 581"
url = f"https://www.courtlistener.com/api/rest/v4/citation-lookup/?citation={citation}"

headers = {
    'Authorization': f'Token {api_key}',
    'Content-Type': 'application/json'
}

print(f"Testing CourtListener lookup for: {citation}")
print(f"URL: {url}")
print(f"API Key present: {'Yes' if api_key else 'No'}")

try:
    resp = requests.get(url, headers=headers, timeout=30)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text[:1000]}")
except Exception as e:
    print(f"Error: {e}")
