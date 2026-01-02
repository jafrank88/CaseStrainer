#!/usr/bin/env python3
"""Check final results for Meri-Weather citations."""
import requests

r = requests.get('http://localhost:5000/casestrainer/api/task_status/9c3139e5-e1f7-4639-87e6-1c7e7aa8122e', timeout=30)
d = r.json()
clusters = d.get('clusters', [])

print("=" * 60)
print("Meri-Weather cluster results:")
print("=" * 60)

for c in clusters:
    name = c.get('cluster_case_name', '') or ''
    if 'meri' in name.lower():
        print(f"\nCluster: {name}")
        print(f"  has_date_mismatch: {c.get('has_date_mismatch')}")
        for cit in c.get('citations', []):
            print(f"\n  Citation: '{cit.get('citation')}'")
            print(f"    verified: {cit.get('verified')}")
            print(f"    source: {cit.get('source')}")
            print(f"    canonical_date: {cit.get('canonical_date')}")
            print(f"    extracted_date: {cit.get('extracted_date')}")
            print(f"    verification_status: {cit.get('verification_status')}")

print("\n" + "=" * 60)
print("Mountain Timber cluster check:")
print("=" * 60)
for c in clusters:
    name = c.get('cluster_case_name', '') or ''
    if 'timber' in name.lower():
        print(f"\nCluster: {name}")
        print(f"  has_date_mismatch: {c.get('has_date_mismatch')}")
