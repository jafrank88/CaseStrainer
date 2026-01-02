#!/usr/bin/env python3
"""Final check for all fixes."""
import requests

r = requests.get('http://localhost:5000/casestrainer/api/task_status/ebcd31ce-7d24-4e5b-a72f-d03638bc57fa', timeout=30)
d = r.json()
clusters = d.get('clusters', [])
raw_cits = d.get('citations', [])

print("=" * 60)
print(f"Summary: {len(raw_cits)} raw citations, {len(clusters)} clusters")
print("=" * 60)

# Count citations in clusters
cluster_cit_count = sum(len(c.get('citations', [])) for c in clusters)
print(f"Citations in clusters: {cluster_cit_count}")

print("\n" + "=" * 60)
print("Searching for '47 Conn. Supp. 113'...")
print("=" * 60)

# Check raw citations
for c in raw_cits:
    if '47' in str(c.get('citation', '')) and 'Supp' in str(c.get('citation', '')):
        print(f"\nIn raw citations:")
        print(f"  Citation: {c.get('citation')}")
        print(f"  verified: {c.get('verified')}")
        print(f"  source: {c.get('source')}")
        print(f"  canonical_date: {c.get('canonical_date')}")

# Check clusters
found_in_cluster = False
for c in clusters:
    for cit in c.get('citations', []):
        if '47' in str(cit.get('citation', '')) and 'Supp' in str(cit.get('citation', '')):
            found_in_cluster = True
            print(f"\nIn cluster: {c.get('cluster_case_name')}")
            print(f"  cluster_id: {c.get('cluster_id')}")
            print(f"  Citation: {cit.get('citation')}")
            print(f"  verified: {cit.get('verified')}")
            print(f"  source: {cit.get('source')}")
            print(f"  canonical_date: {cit.get('canonical_date')}")

if not found_in_cluster:
    print("\n  NOT FOUND in any cluster!")

print("\n" + "=" * 60)
print("Meri-Weather related clusters:")
print("=" * 60)
for c in clusters:
    name = c.get('cluster_case_name', '') or ''
    if 'meri' in name.lower():
        print(f"\nCluster: {name}")
        print(f"  cluster_id: {c.get('cluster_id')}")
        print(f"  has_date_mismatch: {c.get('has_date_mismatch')}")
        for cit in c.get('citations', []):
            print(f"  - {cit.get('citation')}: verified={cit.get('verified')}, source={cit.get('source')}, canonical_date={cit.get('canonical_date')}")
