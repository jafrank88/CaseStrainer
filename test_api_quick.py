#!/usr/bin/env python
"""Quick test of the analyze API endpoint"""
import requests
import json

url = "https://wolf.law.uw.edu/casestrainer/api/analyze"

payload = {
    "type": "url",
    "url": "https://www.courts.wa.gov/opinions/pdf/1034300.pdf",
    "client_request_id": "test-quick-check"
}

print("Testing analyze endpoint...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print("\nSending request...")

try:
    response = requests.post(url, json=payload, timeout=60)
    print(f"\n✅ Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)[:500]}...")
except Exception as e:
    print(f"\n❌ Error: {e}")
