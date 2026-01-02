#!/usr/bin/env python3
"""Final check for all fixes."""
import requests

r = requests.get('http://localhost:5000/casestrainer/api/task_status/2f0b04e7-ecca-466f-8a9d-7ec2c57cc623', timeout=30)
d = r.json()
clusters = d.get('clusters', [])

print("=" * 60)
print("ISSUE 3: Meri-Weather cluster results")
print("=" * 60)

# Find 47 Conn. Supp. 113 specifically
print("\nSearching for '47 Conn. Supp. 113'...")
found_supp = False
for c in clusters:
    for cit in c.get('citations', []):
        cit_str = cit.get('citation', '')
        if 'Supp' in cit_str and '47' in cit_str:
            found_supp = True
            print(f"\nFound in cluster: {c.get('cluster_case_name')}")
            print(f"  Citation: {cit_str}")
            print(f"  verified: {cit.get('verified')}")
            print(f"  source: {cit.get('source')}")
            print(f"  canonical_date: {cit.get('canonical_date')}")
            print(f"  extracted_date: {cit.get('extracted_date')}")

if not found_supp:
    print("  NOT FOUND in any cluster!")

# Check Meri-Weather clusters
print("\n" + "=" * 60)
print("Meri-Weather related clusters:")
print("=" * 60)
for c in clusters:
    name = c.get('cluster_case_name', '') or ''
    if 'meri' in name.lower():
        print(f"\nCluster: {name}")
        print(f"  has_date_mismatch: {c.get('has_date_mismatch')}")
        for cit in c.get('citations', []):
            print(f"  - {cit.get('citation')}: verified={cit.get('verified')}, canonical_date={cit.get('canonical_date')}")

print("\n" + "=" * 60)
print("ISSUE 2: Mountain Timber cluster check")
print("=" * 60)
for c in clusters:
    name = c.get('cluster_case_name', '') or ''
    if 'timber' in name.lower():
        print(f"\nCluster: {name}")
        print(f"  has_date_mismatch: {c.get('has_date_mismatch')}")
