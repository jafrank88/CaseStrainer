#!/usr/bin/env python3
"""Final comprehensive check for all fixes."""
import requests

r = requests.get('http://localhost:5000/casestrainer/api/task_status/482094c9-a3c6-44ab-a5c7-6124fd4d8455', timeout=30)
d = r.json()
clusters = d.get('clusters', [])
raw_cits = d.get('citations', [])

print("=" * 70)
print("FINAL TEST RESULTS")
print("=" * 70)

# 1. Check 75 Wash. 581 verification (should be State v. Mountain Timber, not Mississippi Valley)
print("\n1. 75 Wash. 581 verification (should be State v. Mountain Timber Co.):")
for cit in raw_cits:
    if '75 Wash' in cit.get('citation', ''):
        canonical = cit.get('canonical_name', '')
        source = cit.get('source', '')
        print(f"   Citation: {cit.get('citation')}")
        print(f"   Canonical: {canonical}")
        print(f"   Source: {source}")
        if 'Mountain Timber' in canonical:
            print("   PASS - Correct case found")
        elif 'Mississippi' in canonical:
            print("   FAIL - Wrong case (Mississippi Valley Trust)")
        else:
            print(f"   CHECK - Unexpected canonical name")

# 2. Check HTML entities (should NOT have &amp;)
print("\n2. HTML entity check (should NOT have &amp;):")
bad_entities = []
for cit in raw_cits:
    canonical = cit.get('canonical_name', '') or ''
    extracted = cit.get('extracted_case_name', '') or ''
    if '&amp;' in canonical or '&amp;' in extracted:
        bad_entities.append(f"{cit.get('citation')}: {canonical or extracted}")
if bad_entities:
    print(f"   FAIL - Found &amp;: {bad_entities[:3]}")
else:
    print("   PASS - No &amp; entities found")

# 3. Check Niemann cluster (should be separate from Borton)
print("\n3. Niemann cluster check:")
for c in clusters:
    name = c.get('cluster_case_name', '') or ''
    if 'niemann' in name.lower():
        print(f"   Cluster: {name}")
        cits = [ci.get('citation') for ci in c.get('citations', [])]
        print(f"   Citations: {cits}")
        # Check if Borton citations are mixed in
        borton_mixed = any('471 P.3d' in c or '196 Wn.2d 199' in c for c in cits)
        if borton_mixed:
            print("   FAIL - Borton citations mixed in")
        else:
            print("   PASS - Only Niemann citations")

# 4. Check cross-state clustering
print("\n4. Cross-state clustering (Ohio/Nebraska should be separate):")
for c in clusters:
    cits = [ci.get('citation', '') for ci in c.get('citations', [])]
    has_ohio = any('Ohio' in c or 'N.E' in c for c in cits)
    has_neb = any('Neb' in c or 'N.W' in c for c in cits)
    if has_ohio and has_neb:
        print(f"   FAIL - Mixed cluster: {c.get('cluster_case_name')}")
        break
else:
    print("   PASS - Ohio and Nebraska are in separate clusters")

print("\n" + "=" * 70)
