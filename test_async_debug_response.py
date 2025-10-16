#!/usr/bin/env python3
"""
Debug async response to see exactly what we're getting
"""
import requests
import json

base_url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
pdf_url = "https://www.courts.wa.gov/opinions/pdf/1034300.pdf"

print("="*60)
print("DEBUG ASYNC RESPONSE")
print("="*60)

print("\nSubmitting PDF URL for async processing...")
response = requests.post(base_url, json={
    "type": "url",
    "url": pdf_url
}, timeout=30)

print(f"Status Code: {response.status_code}")
print(f"Response size: {len(response.text)} bytes")
print("\nFull Response JSON:")
print(json.dumps(response.json(), indent=2))

print("\n" + "="*60)
