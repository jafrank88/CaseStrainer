#!/usr/bin/env python3
"""Investigate Borton/Niemann and Mountain Timber issues."""
import requests

r = requests.get('http://localhost:5000/casestrainer/api/task_status/1d51d287-cd28-4b00-9342-0873beefb358', timeout=30)
d = r.json()
clusters = d.get('clusters', [])
raw_cits = d.get('citations', [])

print(f"Total clusters: {len(clusters)}")
print(f"Total raw citations: {len(raw_cits)}")

# Find citations 154 Wn.2d 365 and 113 P.3d 463 (the Niemann/Borton ones)
print("\n" + "=" * 70)
print("Looking for 154 Wn.2d 365 and 113 P.3d 463:")
print("=" * 70)
for cit in raw_cits:
    citation = cit.get('citation', '')
    if '154 Wn' in citation or '113 P.3d' in citation or '196 Wn.2d 199' in citation or '471 P.3d 871' in citation:
        print(f"\nCitation: {citation}")
        print(f"  extracted_case_name: {cit.get('extracted_case_name')}")
        print(f"  canonical_name: {cit.get('canonical_name')}")
        print(f"  verified: {cit.get('verified')}")

# Find the cluster containing these citations
print("\n" + "=" * 70)
print("Cluster containing 154 Wn.2d 365:")
print("=" * 70)
for c in clusters:
    for cit in c.get('citations', []):
        if '154 Wn' in cit.get('citation', ''):
            print(f"Cluster name: {c.get('cluster_case_name')}")
            print(f"Extracted name: {c.get('extracted_case_name')}")
            print("All citations in cluster:")
            for ci in c.get('citations', []):
                print(f"  - {ci.get('citation')}: {ci.get('extracted_case_name')}")

# Check Mountain Timber - 75 Wash. 581
print("\n" + "=" * 70)
print("Looking for 75 Wash. 581 (Mountain Timber):")
print("=" * 70)
for cit in raw_cits:
    citation = cit.get('citation', '')
    if '75 Wash' in citation:
        print(f"\nCitation: {citation}")
        print(f"  extracted_case_name: {cit.get('extracted_case_name')}")
        print(f"  verified: {cit.get('verified')}")
        print(f"  source: {cit.get('source')}")
        print(f"  verification_error: {cit.get('verification_error')}")
