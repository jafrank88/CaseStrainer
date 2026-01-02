#!/usr/bin/env python3
"""Final comprehensive check for all fixes."""
import requests

r = requests.get('http://localhost:5000/casestrainer/api/task_status/1d51d287-cd28-4b00-9342-0873beefb358', timeout=30)
d = r.json()
clusters = d.get('clusters', [])

print("=" * 60)
print("FINAL TEST RESULTS")
print("=" * 60)

# 1. Cross-state clustering
print("\n1. Cross-state clustering (Ohio + Nebraska - should be SEPARATE):")
oriana_cits = []
neb_cits = []
for c in clusters:
    name = c.get('cluster_case_name', '') or ''
    cits = [cit.get('citation', '') for cit in c.get('citations', [])]
    if 'oriana' in name.lower():
        oriana_cits = cits
    if any('Neb' in cit for cit in cits):
        neb_cits = cits
        
if oriana_cits and neb_cits:
    if any('Neb' in c for c in oriana_cits):
        print("   FAIL - Nebraska citations in Oriana cluster")
    else:
        print("   PASS - Ohio and Nebraska are in separate clusters")
else:
    print("   PARTIAL - Check clusters manually")

# 2. 47 Conn. Supp. 113
print("\n2. 47 Conn. Supp. 113 in Meri-Weather cluster:")
found = False
for c in clusters:
    for cit in c.get('citations', []):
        if '47' in str(cit.get('citation', '')) and 'Supp' in str(cit.get('citation', '')):
            found = True
            print(f"   PASS - Found in: {c.get('cluster_case_name')}")
if not found:
    print("   FAIL - Not found!")

# 3. HTML entities
print("\n3. HTML entity encoding:")
bad = [c.get('cluster_case_name') for c in clusters if '&amp;' in (c.get('cluster_case_name') or '')]
print(f"   {'FAIL - found &amp;' if bad else 'PASS - no &amp; entities'}")

# 4. Date mismatch on unverified clusters
print("\n4. Date mismatch warnings on unverified Mountain Timber:")
for c in clusters:
    name = c.get('cluster_case_name', '') or ''
    if 'timber' in name.lower():
        dm = c.get('has_date_mismatch', False)
        verified = c.get('verified', False)
        all_unverified = all(not cit.get('verified', False) for cit in c.get('citations', []))
        if all_unverified and not dm:
            print(f"   PASS - {name}: has_date_mismatch=False (all citations unverified)")
        elif all_unverified and dm:
            print(f"   FAIL - {name}: has_date_mismatch=True but all citations unverified")
        else:
            print(f"   INFO - {name}: has_date_mismatch={dm}, verified={verified}")

print("\n" + "=" * 60)
print("ALL TESTS COMPLETE")
print("=" * 60)
