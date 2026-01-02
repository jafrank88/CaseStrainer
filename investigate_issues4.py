#!/usr/bin/env python3
"""Investigate remaining issues."""
import requests

r = requests.get('http://localhost:5000/casestrainer/api/task_status/b3c25853-ba72-4b23-b2d9-fd19a96afa17', timeout=30)
d = r.json()
clusters = d.get('clusters', [])
raw_cits = d.get('citations', [])

# Check 196 Wn.2d 199 and 471 P.3d 871 - user says these are in Borton cluster
print("=" * 70)
print("Looking for 196 Wn.2d 199 and 471 P.3d 871:")
print("=" * 70)
for cit in raw_cits:
    citation = cit.get('citation', '')
    if '196 Wn.2d 199' in citation or '471 P.3d 871' in citation:
        print(f"\nCitation: {citation}")
        print(f"  extracted_case_name: {cit.get('extracted_case_name')}")
        print(f"  canonical_name: {cit.get('canonical_name')}")
        print(f"  verified: {cit.get('verified')}")
        print(f"  source: {cit.get('source')}")

# Find cluster containing these
print("\n" + "=" * 70)
print("Cluster containing 196 Wn.2d 199:")
print("=" * 70)
for c in clusters:
    for cit in c.get('citations', []):
        if '196 Wn.2d 199' in cit.get('citation', ''):
            print(f"Cluster name: {c.get('cluster_case_name')}")
            print(f"Extracted name: {c.get('extracted_case_name')}")
            print("All citations in cluster:")
            for ci in c.get('citations', []):
                print(f"  - {ci.get('citation')}: {ci.get('extracted_case_name')}")
            break

# Check what CourtListener returns for 75 Wash. 581
# This citation is being wrongly verified as Mississippi Valley Trust
print("\n" + "=" * 70)
print("75 Wash. 581 verification details:")
print("=" * 70)
for cit in raw_cits:
    if '75 Wash. 581' in cit.get('citation', ''):
        print(f"Citation: {cit.get('citation')}")
        print(f"Source: {cit.get('source')}")
        print(f"Canonical: {cit.get('canonical_name')}")
        print(f"URL: {cit.get('canonical_url')}")
        # This is wrong - it should be State v. Mountain Timber Co.
        # The correct URL is: https://www.courtlistener.com/opinion/4925488/state-v-mountain-timber-co/
