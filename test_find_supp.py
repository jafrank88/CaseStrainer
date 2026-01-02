#!/usr/bin/env python3
"""Find 47 Conn. Supp. 113 specifically."""
import requests

r = requests.get('http://localhost:5000/casestrainer/api/task_status/9c3139e5-e1f7-4639-87e6-1c7e7aa8122e', timeout=30)
d = r.json()
clusters = d.get('clusters', [])

print("Searching for '47 Conn. Supp. 113' specifically...")
found = False
for c in clusters:
    for cit in c.get('citations', []):
        cit_str = cit.get('citation', '')
        if 'Supp' in cit_str and '47' in cit_str:
            found = True
            print(f"\nFound in cluster: {c.get('cluster_case_name')}")
            print(f"  Citation: {cit_str}")
            print(f"  verified: {cit.get('verified')}")
            print(f"  source: {cit.get('source')}")
            print(f"  canonical_date: {cit.get('canonical_date')}")
            print(f"  extracted_date: {cit.get('extracted_date')}")
            print(f"  verification_status: {cit.get('verification_status')}")

if not found:
    print("\n47 Conn. Supp. 113 NOT FOUND in any cluster!")
    print("\nAll citations containing 'Supp':")
    for c in clusters:
        for cit in c.get('citations', []):
            if 'Supp' in cit.get('citation', ''):
                print(f"  {cit.get('citation')} in {c.get('cluster_case_name')}")
