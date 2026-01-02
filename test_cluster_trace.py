#!/usr/bin/env python3
"""Trace where 47 Conn. Supp. 113 is lost during clustering."""
import requests
import json

r = requests.get('http://localhost:5000/casestrainer/api/task_status/2f0b04e7-ecca-466f-8a9d-7ec2c57cc623', timeout=30)
d = r.json()

# Count citations at different stages
raw_citations = d.get('citations', [])
clusters = d.get('clusters', [])

print(f"Raw citations: {len(raw_citations)}")

# Count citations in clusters
cluster_cits = []
for c in clusters:
    cluster_cits.extend(c.get('citations', []))
print(f"Citations in clusters: {len(cluster_cits)}")

# Find citations missing from clusters
raw_cit_strs = set()
for c in raw_citations:
    cit_str = c.get('citation', '')
    raw_cit_strs.add(cit_str)

cluster_cit_strs = set()
for c in cluster_cits:
    cit_str = c.get('citation', '')
    cluster_cit_strs.add(cit_str)

missing = raw_cit_strs - cluster_cit_strs
print(f"\nMissing from clusters: {len(missing)}")
for m in sorted(missing):
    if 'Supp' in m or 'Conn' in m:
        print(f"  - {m}")

# Check if 47 Conn. Supp. 113 is in any cluster's citations
print("\nSearching for 47 Conn. Supp. 113 in cluster citations...")
for c in clusters:
    for cit in c.get('citations', []):
        if '47' in str(cit.get('citation', '')) and 'Supp' in str(cit.get('citation', '')):
            print(f"  Found in: {c.get('cluster_case_name')}")
