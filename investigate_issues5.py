#!/usr/bin/env python3
"""Check all clusters for mixed Niemann/Borton citations."""
import requests

r = requests.get('http://localhost:5000/casestrainer/api/task_status/b3c25853-ba72-4b23-b2d9-fd19a96afa17', timeout=30)
d = r.json()
clusters = d.get('clusters', [])

# Find cluster containing 471 P.3d 871
print("=" * 70)
print("Cluster containing 471 P.3d 871 (Borton):")
print("=" * 70)
for c in clusters:
    for cit in c.get('citations', []):
        if '471 P.3d 871' in cit.get('citation', ''):
            print(f"Cluster name: {c.get('cluster_case_name')}")
            print(f"Extracted name: {c.get('extracted_case_name')}")
            print("All citations in cluster:")
            for ci in c.get('citations', []):
                print(f"  - {ci.get('citation')}: {ci.get('extracted_case_name')}")
            break

# Check if Niemann cluster has any Borton citations
print("\n" + "=" * 70)
print("Niemann cluster - check for contamination:")
print("=" * 70)
for c in clusters:
    name = c.get('cluster_case_name', '') or ''
    if 'niemann' in name.lower():
        print(f"Cluster name: {name}")
        print("All citations:")
        for ci in c.get('citations', []):
            ext = ci.get('extracted_case_name', '')
            print(f"  - {ci.get('citation')}: extracted='{ext}'")
            if 'borton' in ext.lower():
                print("    *** BORTON CONTAMINATION FOUND ***")

# Check all cluster names
print("\n" + "=" * 70)
print("All cluster names:")
print("=" * 70)
for i, c in enumerate(clusters):
    name = c.get('cluster_case_name', '') or 'N/A'
    ext = c.get('extracted_case_name', '') or 'N/A'
    if name != ext and name != 'N/A' and ext != 'N/A':
        print(f"{i+1}. {name}")
        print(f"   Extracted: {ext}")
        print("   ** NAME MISMATCH **")
