#!/usr/bin/env python3
"""Final check for all fixes."""
import requests

r = requests.get('http://localhost:5000/casestrainer/api/task_status/2802db24-082a-4034-b50c-a669c2a7d460', timeout=30)
d = r.json()
clusters = d.get('clusters', [])
raw_cits = d.get('citations', [])

print("=" * 60)
print(f"Summary: {len(raw_cits)} raw citations, {len(clusters)} clusters")
print("=" * 60)

cluster_cit_count = sum(len(c.get('citations', [])) for c in clusters)
print(f"Citations in clusters: {cluster_cit_count}")

print("\n" + "=" * 60)
print("ISSUE CHECKS")
print("=" * 60)

# 1. Mountain Timber date_mismatch
print("\n1. Mountain Timber date_mismatch (should be False for unverified):")
for c in clusters:
    name = c.get('cluster_case_name', '') or ''
    if 'timber' in name.lower():
        dm = c.get('has_date_mismatch', 'N/A')
        verified = c.get('verified', False)
        print(f"   {name}: has_date_mismatch={dm}, verified={verified}")

# 2. Oriana House (should NOT have Nebraska citations)
print("\n2. Oriana House clustering (Ohio vs Nebraska - should be separate):")
for c in clusters:
    name = c.get('cluster_case_name', '') or ''
    if 'oriana' in name.lower() or 'neb' in str(c.get('citations', [])).lower():
        print(f"   Cluster: {name}")
        for cit in c.get('citations', []):
            print(f"      - {cit.get('citation')}")

# 3. 47 Conn. Supp. 113
print("\n3. 47 Conn. Supp. 113 (should be in cluster):")
found = False
for c in clusters:
    for cit in c.get('citations', []):
        if '47' in str(cit.get('citation', '')) and 'Supp' in str(cit.get('citation', '')):
            found = True
            print(f"   FOUND in: {c.get('cluster_case_name')}")
if not found:
    print("   NOT FOUND!")

# 4. HTML entities
print("\n4. HTML entity check:")
bad_entities = []
for c in clusters:
    name = c.get('cluster_case_name', '') or ''
    if '&amp;' in name:
        bad_entities.append(name)
if bad_entities:
    print(f"   BAD - Found &amp;: {bad_entities}")
else:
    print("   GOOD - No &amp; found")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
