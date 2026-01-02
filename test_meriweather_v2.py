#!/usr/bin/env python3
"""Test if Meri-Weather cluster is correctly split on aff'd."""
import requests

r = requests.get('http://localhost:5000/casestrainer/api/task_status/0cc228d8-e7ed-4465-a946-500285bb83ae', timeout=30)
d = r.json()
clusters = d.get('clusters', [])

print("=" * 70)
print("MERI-WEATHER CLUSTER CHECK")
print("=" * 70)

# Find clusters with Meri-Weather or the specific citations
meri_weather_cits = ['778 A.2d 1006', '63 Conn. App. 695', '47 Conn. Supp. 113', '778 A.2d 1038']

found_clusters = []
for c in clusters:
    name = c.get('cluster_case_name', '') or c.get('extracted_case_name', '') or ''
    citations = c.get('citations', [])
    cit_texts = [ci.get('citation', '') for ci in citations if isinstance(ci, dict)]
    
    # Check if any of the Meri-Weather citations are in this cluster
    matching = [ct for ct in cit_texts if ct in meri_weather_cits]
    if matching or 'meri' in name.lower() or 'freedom' in name.lower():
        found_clusters.append({
            'name': name,
            'citations': cit_texts,
            'matching': matching
        })

print(f"\nFound {len(found_clusters)} clusters with Meri-Weather citations:")
for i, fc in enumerate(found_clusters):
    print(f"\n  Cluster {i+1}: {fc['name']}")
    print(f"    Citations: {fc['citations']}")
    print(f"    Matching Meri-Weather cits: {fc['matching']}")

# Check if they're correctly split
if len(found_clusters) == 1:
    print("\n  FAIL - All Meri-Weather citations are in ONE cluster (should be 2)")
    print("  Expected: 778 A.2d 1006 + 63 Conn. App. 695 in one cluster")
    print("  Expected: 47 Conn. Supp. 113 + 778 A.2d 1038 in another cluster")
elif len(found_clusters) >= 2:
    print("\n  PASS - Meri-Weather citations are in MULTIPLE clusters")
else:
    print("\n  CHECK - No Meri-Weather clusters found")

print("\n" + "=" * 70)
