#!/usr/bin/env python
"""Find full details of citation #20 and look for 2017-NM-007"""
import requests
import json

task_id = "test-propagation"
url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"

response = requests.get(url, timeout=10)
data = response.json()

citations = data.get('citations', [])
clusters = data.get('clusters', [])

print("=" * 80)
print("CITATION #20 FULL DETAILS")
print("=" * 80)

# Get citation 19 (0-indexed)
if len(citations) > 19:
    cit = citations[19]
    print(json.dumps(cit, indent=2))

print("\n" + "=" * 80)
print("SEARCHING FOR '2017-NM-007' IN ALL CITATIONS")
print("=" * 80)

found_vendor_neutral = False
for i, cit in enumerate(citations, 1):
    cit_text = cit.get('citation', '')
    if '2017' in cit_text or 'NM-' in cit_text or '007' in cit_text:
        print(f"\n[{i}] {cit_text}")
        print(f"    Extracted: {cit.get('extracted_case_name', 'N/A')}")
        print(f"    Method: {cit.get('method', 'N/A')}")
        found_vendor_neutral = True

if not found_vendor_neutral:
    print("\n❌ '2017-NM-007' NOT FOUND in extracted citations")
    print("\n💡 This means the vendor-neutral citation was either:")
    print("   1. Not extracted (pattern not matching)")
    print("   2. Filtered out during deduplication")
    print("   3. Not present in the PDF text")

# Check if it's in a cluster with 388 P.3d 977
print("\n" + "=" * 80)
print("CHECKING CLUSTER FOR 388 P.3d 977")
print("=" * 80)

for cluster in clusters:
    cluster_cits = cluster.get('citations', [])
    cluster_texts = [c.get('citation', '') for c in cluster_cits]
    
    if '388 P.3d 977' in str(cluster_texts):
        print(f"\n✅ Found cluster containing 388 P.3d 977:")
        print(f"   Cluster ID: {cluster.get('cluster_id', 'N/A')}")
        print(f"   Citations in cluster: {len(cluster_cits)}")
        
        for cit in cluster_cits:
            print(f"      - {cit.get('citation', 'N/A')}")
