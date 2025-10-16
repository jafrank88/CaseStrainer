#!/usr/bin/env python3
"""
Test submitting to wolf.law.uw.edu endpoint
"""
import requests
import time
import json

url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
pdf_url = "https://www.courts.wa.gov/opinions/pdf/1034300.pdf"

print("="*60)
print("TESTING WOLF.LAW.UW.EDU ENDPOINT")
print("="*60)
print(f"Submitting: {pdf_url}")
print(f"To: {url}")
print()

payload = {
    "type": "url",
    "url": pdf_url
}

headers = {
    "Content-Type": "application/json"
}

print("Submitting request...")
response = requests.post(url, json=payload, headers=headers, timeout=120)

print(f"Status: {response.status_code}")
print(f"Response size: {len(response.text)} bytes")
print()

if response.status_code == 200:
    result = response.json()
    print("✓ Success!")
    print(f"  Citations: {len(result.get('citations', []))}")
    print(f"  Clusters: {len(result.get('clusters', []))}")
    
    # Check verification status
    verified_count = sum(1 for c in result.get('citations', []) if c.get('verified'))
    print(f"  Verified: {verified_count}/{len(result.get('citations', []))}")
    
    # Show first 3 citations
    print("\nFirst 3 citations:")
    for i, cit in enumerate(result.get('citations', [])[:3], 1):
        print(f"  {i}. {cit.get('citation')}")
        print(f"     Case: {cit.get('extracted_case_name', 'N/A')}")
        print(f"     Verified: {cit.get('verified', False)}")
        if cit.get('canonical_name'):
            print(f"     Canonical: {cit.get('canonical_name')}")
else:
    print(f"✗ Error: {response.status_code}")
    print(response.text[:500])

print("\n" + "="*60)
