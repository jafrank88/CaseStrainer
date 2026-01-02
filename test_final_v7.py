#!/usr/bin/env python3
"""Final check for all fixes."""
import requests

r = requests.get('http://localhost:5000/casestrainer/api/task_status/6b03d32e-2cf0-4464-be55-80b7fafe9151', timeout=30)
d = r.json()
clusters = d.get('clusters', [])

print("=" * 60)
print(f"Total clusters: {len(clusters)}")
print("=" * 60)

print("\n1. Oriana House clustering (should be SEPARATE from Nebraska):")
oriana_found = False
neb_found = False
for c in clusters:
    name = c.get('cluster_case_name', '') or ''
    cits = [cit.get('citation', '') for cit in c.get('citations', [])]
    if 'oriana' in name.lower():
        oriana_found = True
        print(f"   Oriana cluster: {name}")
        for cit in cits:
            print(f"      - {cit}")
    if any('Neb' in cit for cit in cits):
        neb_found = True
        print(f"   Nebraska cluster: {name}")
        for cit in cits:
            print(f"      - {cit}")

if not oriana_found:
    print("   Oriana House cluster NOT FOUND")
if not neb_found:
    print("   Nebraska cluster NOT FOUND")

print("\n2. 47 Conn. Supp. 113 check:")
for c in clusters:
    for cit in c.get('citations', []):
        if '47' in str(cit.get('citation', '')) and 'Supp' in str(cit.get('citation', '')):
            print(f"   FOUND in: {c.get('cluster_case_name')}")

print("\n3. HTML entity check:")
bad = [c.get('cluster_case_name') for c in clusters if '&amp;' in (c.get('cluster_case_name') or '')]
print(f"   {'BAD - found &amp;' if bad else 'GOOD - no &amp;'}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
