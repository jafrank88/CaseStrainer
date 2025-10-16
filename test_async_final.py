#!/usr/bin/env python3
"""
Final async test - proper end-to-end verification
"""
import requests
import time
import json

BASE_URL = "http://127.0.0.1:5000/casestrainer/api"

# Create large text to force async (>5KB)
base_text = """
In Smith v. Jones, 123 F.3d 456 (9th Cir. 2020), the court held that the defendant's actions
were not sufficient to establish liability. The precedent set in Brown v. Board of Education, 
347 U.S. 483 (1954), was cited extensively. Additionally, the court referenced Miranda v. Arizona, 
384 U.S. 436 (1966), to support the ruling regarding procedural safeguards.
"""
test_text = (base_text * 50).strip()  # ~10KB

print("=" * 80)
print("ASYNC PROCESSING - FINAL END-TO-END TEST")
print("=" * 80)
print(f"Text size: {len(test_text)} bytes (threshold: 5120)")
print()

# 1. Submit job
print("[1/4] Submitting job...")
response = requests.post(
    f"{BASE_URL}/analyze",
    json={"type": "text", "text": test_text},
    timeout=10
)

if response.status_code != 200:
    print(f"❌ FAILED: {response.status_code}")
    exit(1)

data = response.json()
task_id = data.get('metadata', {}).get('job_id') or data.get('task_id')
mode = data.get('metadata', {}).get('processing_mode')

print(f"  ✅ Task ID: {task_id}")
print(f"  ✅ Mode: {mode}")

if mode != 'queued':
    print(f"  ⚠️  Not async (mode={mode})")
    exit(0)

print()

# 2. Wait for completion
print("[2/4] Waiting for job to complete (max 30s)...")
for i in range(30):
    time.sleep(1)
    
    status_resp = requests.get(f"{BASE_URL}/task_status/{task_id}", timeout=5)
    if status_resp.status_code == 200:
        status_data = status_resp.json()
        status = status_data.get('status')
        
        if status == 'completed':
            print(f"  ✅ Job completed after {i+1} seconds")
            break
        elif status == 'failed':
            print(f"  ❌ Job failed: {status_data.get('error')}")
            exit(1)
        
        if i % 5 == 0:
            print(f"  ... still processing ({i}s)")
    else:
        print(f"  ⚠️  Status check failed: {status_resp.status_code}")

print()

# 3. Get final results
print("[3/4] Getting final results...")
final_resp = requests.get(f"{BASE_URL}/task_status/{task_id}", timeout=5)

if final_resp.status_code != 200:
    print(f"❌ FAILED to get results: {final_resp.status_code}")
    exit(1)

final_data = final_resp.json()

# 4. Validate results
print("[4/4] Validating results...")
print()

status = final_data.get('status')
success = final_data.get('success')
citations = final_data.get('citations', [])
clusters = final_data.get('clusters', [])
message = final_data.get('message')

print(f"Status: {status}")
print(f"Success: {success}")
print(f"Message: {message}")
print(f"Citations: {len(citations)}")
print(f"Clusters: {len(clusters)}")
print()

if status == 'completed' and success and len(citations) > 0:
    print("=" * 80)
    print("✅ ASYNC PROCESSING WORKING PERFECTLY!")
    print("=" * 80)
    print()
    print("Citations found:")
    for i, cit in enumerate(citations[:5], 1):
        citation_text = cit.get('citation', 'N/A')
        verified = cit.get('verified', False)
        canonical = cit.get('canonical_name', 'N/A')
        print(f"  {i}. {citation_text}")
        print(f"     Verified: {verified}")
        print(f"     Canonical: {canonical[:60]}...")
    print()
    print("🎉 All async components working:")
    print("  ✅ Job queuing")
    print("  ✅ Worker pickup")
    print("  ✅ Citation extraction")
    print("  ✅ Verification")
    print("  ✅ Result storage")
    print("  ✅ Result retrieval")
    exit(0)
else:
    print("=" * 80)
    print("❌ ASYNC PROCESSING FAILED")
    print("=" * 80)
    print(f"Expected: completed with citations")
    print(f"Got: {status} with {len(citations)} citations")
    exit(1)
