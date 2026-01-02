#!/usr/bin/env python3
"""Investigate Borton/Niemann and Mountain Timber issues."""
import requests

r = requests.get('http://localhost:5000/casestrainer/api/task_status/1d51d287-cd28-4b00-9342-0873beefb358', timeout=30)
d = r.json()
clusters = d.get('clusters', [])
raw_cits = d.get('citations', [])

print("=" * 70)
print("ISSUE 1: Borton/Niemann cluster contamination")
print("=" * 70)
for c in clusters:
    name = c.get('cluster_case_name', '') or ''
    ext = c.get('extracted_case_name', '') or ''
    if 'niemann' in name.lower() or 'borton' in name.lower():
        print(f"\nCluster: {name}")
        print(f"Extracted: {ext}")
        print(f"Canonical date: {c.get('canonical_date')}")
        print("Citations:")
        for cit in c.get('citations', []):
            print(f"  - {cit.get('citation')}")
            print(f"    extracted_case_name: {cit.get('extracted_case_name')}")
            print(f"    canonical_name: {cit.get('canonical_name')}")
            print(f"    verified: {cit.get('verified')}")
            print(f"    source: {cit.get('source')}")

print("\n" + "=" * 70)
print("ISSUE 2: State v. Mountain Timber Co. verification")
print("=" * 70)
# Check raw citations for 75 Wash. 581
for cit in raw_cits:
    citation = cit.get('citation', '')
    if '75 Wash' in citation or 'Mountain Timber' in str(cit.get('extracted_case_name', '')):
        print(f"\nCitation: {citation}")
        print(f"  extracted_case_name: {cit.get('extracted_case_name')}")
        print(f"  verified: {cit.get('verified')}")
        print(f"  source: {cit.get('source')}")
        print(f"  canonical_name: {cit.get('canonical_name')}")
        print(f"  verification_error: {cit.get('verification_error')}")
