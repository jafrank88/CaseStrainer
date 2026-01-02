#!/usr/bin/env python3
"""Find where 47 Conn. Supp. 113 ended up."""
import requests

r = requests.get('http://localhost:5000/casestrainer/api/task_status/9c3139e5-e1f7-4639-87e6-1c7e7aa8122e', timeout=30)
d = r.json()
clusters = d.get('clusters', [])

print("Searching for 47 Conn. Supp. 113...")
found = False
for c in clusters:
    for cit in c.get('citations', []):
        if '47 Conn' in cit.get('citation', ''):
            found = True
            print(f"\nFound in cluster: {c.get('cluster_case_name')}")
            print(f"  Citation: {cit.get('citation')}")
            print(f"  verified: {cit.get('verified')}")
            print(f"  source: {cit.get('source')}")
            print(f"  canonical_date: {cit.get('canonical_date')}")
            print(f"  extracted_date: {cit.get('extracted_date')}")

if not found:
    print("47 Conn. Supp. 113 NOT FOUND in any cluster!")
