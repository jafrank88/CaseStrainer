#!/usr/bin/env python3
"""Final check for all fixes."""
import requests

r = requests.get('http://localhost:5000/casestrainer/api/task_status/9eeeeba2-f1fb-411e-a46a-8a0e149a8719', timeout=30)
d = r.json()
clusters = d.get('clusters', [])
raw_cits = d.get('citations', [])

print("=" * 60)
print(f"Summary: {len(raw_cits)} raw citations, {len(clusters)} clusters")
print("=" * 60)

# Count citations in clusters
cluster_cit_count = sum(len(c.get('citations', [])) for c in clusters)
print(f"Citations in clusters: {cluster_cit_count}")

# Check specific issues
print("\n" + "=" * 60)
print("ISSUE CHECKS")
print("=" * 60)

# 1. Check Mountain Timber date mismatch (should be False for unverified)
print("\n1. Mountain Timber date_mismatch (should be False for unverified):")
for c in clusters:
    name = c.get('cluster_case_name', '') or ''
    if 'timber' in name.lower():
        dm = c.get('has_date_mismatch', 'N/A')
        verified = c.get('verified', False)
        print(f"   {name}: has_date_mismatch={dm}, verified={verified}")

# 2. Check Oriana House (should NOT have Nebraska citations)
print("\n2. Oriana House clustering (Ohio vs Nebraska):")
for c in clusters:
    name = c.get('cluster_case_name', '') or ''
    if 'oriana' in name.lower():
        print(f"   Cluster: {name}")
        for cit in c.get('citations', []):
            print(f"      - {cit.get('citation')}")

# 3. Check Niemann/Borton mismatch
print("\n3. Niemann cluster (check for Borton contamination):")
for c in clusters:
    name = c.get('cluster_case_name', '') or ''
    if 'niemann' in name.lower():
        ext = c.get('extracted_case_name', 'N/A')
        nm = c.get('has_name_mismatch', False)
        print(f"   Cluster: {name}")
        print(f"   Extracted: {ext}")
        print(f"   has_name_mismatch: {nm}")

# 4. Check Manufactured Housing/Shavlik mismatch  
print("\n4. Manufactured Housing (check for Shavlik contamination):")
for c in clusters:
    name = c.get('cluster_case_name', '') or ''
    if 'manufactured' in name.lower() or 'shavlik' in name.lower():
        ext = c.get('extracted_case_name', 'N/A')
        nm = c.get('has_name_mismatch', False)
        print(f"   Cluster: {name}")
        print(f"   Extracted: {ext}")
        print(f"   has_name_mismatch: {nm}")

# 5. Check 47 Conn. Supp. 113 (should be in cluster)
print("\n5. 47 Conn. Supp. 113 (should be in Meri-Weather cluster):")
found = False
for c in clusters:
    for cit in c.get('citations', []):
        if '47' in str(cit.get('citation', '')) and 'Supp' in str(cit.get('citation', '')):
            found = True
            print(f"   FOUND in: {c.get('cluster_case_name')}")
            print(f"   Citation: {cit.get('citation')}")
            print(f"   verified: {cit.get('verified')}, source: {cit.get('source')}")
if not found:
    print("   NOT FOUND!")

# 6. Check HTML entities (&amp; should be &)
print("\n6. HTML entity check (should see & not &amp;):")
for c in clusters:
    name = c.get('cluster_case_name', '') or ''
    ext = c.get('extracted_case_name', '') or ''
    if '&amp;' in name or '&amp;' in ext:
        print(f"   BAD: {name} / {ext}")
    elif '&' in name or '&' in ext:
        print(f"   GOOD: {name}")
