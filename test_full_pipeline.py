#!/usr/bin/env python3
"""Check what citations are extracted and sent to verification."""
import requests
import json

# Get the most recent task result
r = requests.get('http://localhost:5000/casestrainer/api/task_status/5451e387-04b9-4ac0-ab7a-5512c89e2a24', timeout=30)
d = r.json()
clusters = d.get('clusters', [])

print("=" * 60)
print("Searching for Meri-Weather and Conn. Supp. citations")
print("=" * 60)

# Find all citations with "47" or "Conn" or "Meri" 
for c in clusters:
    name = c.get('cluster_case_name', '') or ''
    if 'meri' in name.lower() or 'conn' in name.lower():
        print(f"\nCluster: {name}")
        print(f"  has_date_mismatch: {c.get('has_date_mismatch')}")
        for cit in c.get('citations', []):
            cit_str = cit.get('citation', '')
            print(f"\n  Citation: '{cit_str}'")
            print(f"    verified: {cit.get('verified')}")
            print(f"    source: {cit.get('source')}")
            print(f"    canonical_date: {cit.get('canonical_date')}")
            print(f"    extracted_date: {cit.get('extracted_date')}")
            print(f"    verification_status: {cit.get('verification_status')}")

# Also check for any citation containing "47" 
print("\n" + "=" * 60)
print("All citations containing '47':")
print("=" * 60)
for c in clusters:
    for cit in c.get('citations', []):
        cit_str = cit.get('citation', '')
        if '47' in cit_str:
            print(f"\n  Citation: '{cit_str}'")
            print(f"    Cluster: {c.get('cluster_case_name', '')}")
            print(f"    verified: {cit.get('verified')}")
            print(f"    source: {cit.get('source')}")
