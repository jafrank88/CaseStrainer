#!/usr/bin/env python3
"""Check raw citation data for 47 Conn. Supp. 113."""
import requests

r = requests.get('http://localhost:5000/casestrainer/api/task_status/2f0b04e7-ecca-466f-8a9d-7ec2c57cc623', timeout=30)
d = r.json()

citations = d.get('citations', [])
print(f"Total raw citations: {len(citations)}")

print("\nSearching for '47 Conn. Supp. 113' in raw citations...")
for c in citations:
    cit_str = c.get('citation', '')
    if 'Supp' in cit_str and '47' in cit_str:
        print(f"\nFound: {cit_str}")
        print(f"  verified: {c.get('verified')}")
        print(f"  source: {c.get('source')}")
        print(f"  canonical_name: {c.get('canonical_name')}")
        print(f"  canonical_date: {c.get('canonical_date')}")
        print(f"  extracted_date: {c.get('extracted_date')}")
        print(f"  verification_status: {c.get('verification_status')}")
