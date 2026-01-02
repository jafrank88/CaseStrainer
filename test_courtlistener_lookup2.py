#!/usr/bin/env python3
"""Test CourtListener lookup for 75 Wash. 581."""
import requests
import os
import json

# Get API key
api_key = os.environ.get('COURTLISTENER_API_KEY', '')

# Test the citation lookup API with POST
citation = "75 Wash. 581"
url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"

headers = {
    'Authorization': f'Token {api_key}',
    'Content-Type': 'application/json'
}

payload = {"text": citation}

print(f"Testing CourtListener lookup for: {citation}")
print(f"URL: {url}")
print(f"API Key present: {'Yes' if api_key else 'No'}")
print(f"Payload: {payload}")

try:
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    print(f"Status: {resp.status_code}")
    data = resp.json()
    print(f"Response: {json.dumps(data, indent=2)[:2000]}")
except Exception as e:
    print(f"Error: {e}")
