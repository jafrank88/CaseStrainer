#!/usr/bin/env python
"""Test extracted name propagation"""
import requests
import json
import time

print("=" * 80)
print("TESTING EXTRACTED NAME PROPAGATION")
print("=" * 80)

# Submit new analysis
url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
payload = {
    "type": "url",
    "url": "https://www.courts.wa.gov/opinions/pdf/1034300.pdf",
    "client_request_id": "test-propagation"
}

print("\n📤 Submitting URL for analysis...")
response = requests.post(url, json=payload, timeout=60)
data = response.json()
task_id = data.get('task_id') or data.get('request_id')
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

# Check the Flying T Ranch citations
print("\n" + "=" * 80)
print("CHECKING FLYING T RANCH CITATIONS")
print("=" * 80)

citations = status_data.get('citations', [])
clusters = status_data.get('clusters', [])

# Find the cluster with 549 P.3d 727 and 31 Wn. App. 2d 343
for cluster in clusters:
    cluster_citations = cluster.get('citations', [])
    cluster_texts = [c.get('citation', '') for c in cluster_citations]
    
    if '549 P.3d 727' in str(cluster_texts) or '31 Wn. App. 2d 343' in str(cluster_texts):
        print(f"\n🔗 Found Cluster: {cluster.get('cluster_id', 'N/A')}")
        print(f"   Cluster Name: {cluster.get('cluster_case_name', 'N/A')}")
        print(f"   Total Citations: {len(cluster_citations)}")
        
        # Check extracted names
        extracted_names = set()
        print(f"\n   Citations in cluster:")
        for i, cit in enumerate(cluster_citations, 1):
            cit_text = cit.get('citation', 'N/A')
            extracted = cit.get('extracted_case_name', 'N/A')
            extracted_names.add(extracted)
            
            print(f"   [{i}] {cit_text}")
            print(f"       Extracted: {extracted}")
        
        print(f"\n   📊 UNIQUE EXTRACTED NAMES: {len(extracted_names)}")
        if len(extracted_names) == 1:
            print(f"   ✅ SUCCESS! All citations have the same extracted name:")
            print(f"      '{list(extracted_names)[0]}'")
        else:
            print(f"   ❌ FAILED! Different extracted names found:")
            for name in extracted_names:
                print(f"      - '{name}'")

# Also check if canonical names stayed independent
print("\n" + "=" * 80)
print("CHECKING CANONICAL NAME INDEPENDENCE")
print("=" * 80)

flying_t_cits = [c for c in citations if 'stillaguamish' in c.get('extracted_case_name', '').lower()]
print(f"\nFound {len(flying_t_cits)} Flying T Ranch citations:")

for cit in flying_t_cits:
    print(f"\n  {cit.get('citation', 'N/A')}")
    print(f"    Extracted: {cit.get('extracted_case_name', 'N/A')}")
    print(f"    Canonical: {cit.get('canonical_name') or 'None'}")
    print(f"    Verified: {'✅' if cit.get('verified') else '❌'}")
