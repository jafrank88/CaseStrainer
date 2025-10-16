#!/usr/bin/env python
"""Test that vendor-neutral citation now appears in main list"""
import requests
import time

print("=" * 80)
print("TESTING VENDOR-NEUTRAL CITATION FIX")
print("=" * 80)

# Submit new analysis
url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
payload = {
    "type": "url",
    "url": "https://www.courts.wa.gov/opinions/pdf/1034300.pdf",
    "client_request_id": "test-vendor-neutral-fix"
}

print("\n📤 Submitting URL...")
response = requests.post(url, json=payload, timeout=60)
task_id = response.json().get('task_id') or response.json().get('request_id')
print(f"✅ Task ID: {task_id}")

# Wait for completion
print("\n⏳ Waiting for processing...")
for i in range(60):
    time.sleep(1)
    status_response = requests.get(f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}", timeout=10)
    status_data = status_response.json()
    
    if status_data.get('status') == 'completed':
        print(f"✅ Completed after {i+1} seconds!")
        break

citations = status_data.get('citations', [])
clusters = status_data.get('clusters', [])

print(f"\n📊 RESULTS:")
print(f"   Total Citations: {len(citations)}")
print(f"   Total Clusters: {len(clusters)}")

# Search for New Mexico citations
print("\n🔍 SEARCHING FOR NEW MEXICO CITATIONS:")

nm_in_main_list = []
nm_in_clusters = []

# Check main citations list
for cit in citations:
    cit_text = cit.get('citation', '')
    if 'NM-' in cit_text or '388 P.3d 977' in cit_text:
        nm_in_main_list.append(cit)
        print(f"\n  ✅ FOUND IN MAIN LIST: {cit_text}")
        print(f"     Extracted: {cit.get('extracted_case_name', 'N/A')}")

# Check clusters
for cluster in clusters:
    cluster_cits = cluster.get('citations', [])
    for cit in cluster_cits:
        cit_text = cit.get('citation', '')
        if 'NM-' in cit_text:
            nm_in_clusters.append(cit)
            if cit not in nm_in_main_list:
                print(f"\n  ⚠️  ONLY IN CLUSTER: {cit_text}")

print("\n" + "=" * 80)
print("VERIFICATION")
print("=" * 80)

if any('2017-NM-007' in c.get('citation', '') for c in nm_in_main_list):
    print("✅ SUCCESS: 2017-NM-007 IS in main citations list!")
else:
    print("❌ FAILED: 2017-NM-007 still missing from main list")

if any('388 P.3d 977' in c.get('citation', '') for c in nm_in_main_list):
    print("✅ SUCCESS: 388 P.3d 977 IS in main citations list!")
else:
    print("❌ FAILED: 388 P.3d 977 missing from main list")

print(f"\n📈 CITATION COUNT:")
print(f"   Previous run: 46 citations (missing vendor-neutral)")
print(f"   This run: {len(citations)} citations")

if len(citations) > 46:
    print(f"   ✅ INCREASED by {len(citations) - 46} (vendor-neutral added!)")
elif len(citations) == 46:
    print(f"   ⚠️  SAME COUNT (vendor-neutral may still be missing)")
