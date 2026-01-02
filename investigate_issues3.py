#!/usr/bin/env python3
"""Investigate Borton/Niemann and Mountain Timber issues."""
import requests

r = requests.get('http://localhost:5000/casestrainer/api/task_status/b3c25853-ba72-4b23-b2d9-fd19a96afa17', timeout=30)
d = r.json()
clusters = d.get('clusters', [])
raw_cits = d.get('citations', [])

print(f"Total clusters: {len(clusters)}")

# Find citations 154 Wn.2d 365 and 113 P.3d 463 (the Niemann ones per CourtListener)
print("\n" + "=" * 70)
print("ISSUE 1: Looking for 154 Wn.2d 365 (should be Niemann v. Vaughn)")
print("=" * 70)
for cit in raw_cits:
    citation = cit.get('citation', '')
    if '154 Wn' in citation or '113 P.3d' in citation:
        print(f"\nCitation: {citation}")
        print(f"  extracted_case_name: {cit.get('extracted_case_name')}")
        print(f"  canonical_name: {cit.get('canonical_name')}")
        print(f"  verified: {cit.get('verified')}")
        print(f"  source: {cit.get('source')}")

# Find the cluster containing these citations
print("\n" + "=" * 70)
print("Cluster containing 154 Wn.2d 365:")
print("=" * 70)
for c in clusters:
    for cit in c.get('citations', []):
        if '154 Wn' in cit.get('citation', ''):
            print(f"Cluster name: {c.get('cluster_case_name')}")
            print(f"Extracted name: {c.get('extracted_case_name')}")
            print(f"Canonical date: {c.get('canonical_date')}")
            print("All citations in cluster:")
            for ci in c.get('citations', []):
                print(f"  - {ci.get('citation')}")
                print(f"      extracted: {ci.get('extracted_case_name')}")
                print(f"      canonical: {ci.get('canonical_name')}")
            break

# Check Mountain Timber - 75 Wash. 581
print("\n" + "=" * 70)
print("ISSUE 2: Looking for 75 Wash. 581 (Mountain Timber)")
print("=" * 70)
for cit in raw_cits:
    citation = cit.get('citation', '')
    if '75 Wash' in citation:
        print(f"\nCitation: {citation}")
        print(f"  extracted_case_name: {cit.get('extracted_case_name')}")
        print(f"  verified: {cit.get('verified')}")
        print(f"  source: {cit.get('source')}")
        print(f"  verification_error: {cit.get('verification_error')}")
        print(f"  canonical_name: {cit.get('canonical_name')}")
