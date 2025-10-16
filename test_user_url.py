#!/usr/bin/env python3
"""
Test with user's specific URL
"""
import requests
import time
import json

BASE_URL = "http://127.0.0.1:5000/casestrainer/api"
TEST_URL = "https://www.courts.wa.gov/opinions/pdf/1034300.pdf"

print("=" * 80)
print("TESTING USER'S URL (PDF)")
print("=" * 80)
print(f"URL: {TEST_URL}")
print()

# Submit URL
print("[1] Submitting URL for processing...")
response = requests.post(
    f"{BASE_URL}/analyze",
    json={"type": "url", "url": TEST_URL},
    timeout=15
)

if response.status_code != 200:
    print(f"❌ ERROR: {response.status_code}")
    print(response.text)
    exit(1)

data = response.json()
task_id = data.get('metadata', {}).get('job_id') or data.get('task_id')
mode = data.get('metadata', {}).get('processing_mode')

print(f"  ✅ Task ID: {task_id}")
print(f"  ✅ Mode: {mode}")
print()

if mode == 'immediate':
    print("✅ Processed SYNC (completed immediately)")
    citations = data.get('citations', [])
    print(f"  Citations found: {len(citations)}")
    if citations:
        for i, cit in enumerate(citations[:3], 1):
            print(f"    {i}. {cit.get('citation', 'N/A')}")
    exit(0)

# Monitor async job
print("[2] Monitoring job (max 60 seconds)...")
print()

for i in range(60):
    time.sleep(1)
    
    try:
        status_resp = requests.get(f"{BASE_URL}/task_status/{task_id}", timeout=5)
        if status_resp.status_code == 200:
            status_data = status_resp.json()
            status = status_data.get('status')
            
            # Get current step info
            progress_data = status_data.get('progress_data', {}).get('full_progress_data', {})
            step_index = progress_data.get('current_step', 0)
            steps = progress_data.get('steps', [])
            
            if steps and step_index < len(steps):
                step_name = steps[step_index].get('name', 'Unknown')
                step_status = steps[step_index].get('status', 'pending')
                overall_progress = progress_data.get('overall_progress', 0)
                
                print(f"  [{i+1:2d}s] {overall_progress:3d}% - {step_name:20s} ({step_status})")
            else:
                print(f"  [{i+1:2d}s] Status: {status}")
            
            if status == 'completed':
                citations = status_data.get('citations', [])
                clusters = status_data.get('clusters', [])
                print()
                print("=" * 80)
                print(f"✅ COMPLETED in {i+1} seconds!")
                print("=" * 80)
                print(f"Citations found: {len(citations)}")
                print(f"Clusters: {len(clusters)}")
                
                if citations:
                    print()
                    print("First 5 citations:")
                    for idx, cit in enumerate(citations[:5], 1):
                        citation_text = cit.get('citation', 'N/A')
                        verified = cit.get('verified', False)
                        canonical = cit.get('canonical_name', 'N/A')[:50]
                        print(f"  {idx}. {citation_text}")
                        print(f"     Verified: {verified}")
                        print(f"     Name: {canonical}...")
                
                exit(0)
                
            elif status == 'failed':
                error = status_data.get('error', 'Unknown')
                print()
                print(f"❌ FAILED: {error}")
                exit(1)
    
    except Exception as e:
        print(f"  [{i+1:2d}s] Error checking status: {type(e).__name__}")

print()
print("⏱️  TIMEOUT after 60 seconds")
print()
print("Check status manually:")
print(f"  curl http://127.0.0.1:5000/casestrainer/api/task_status/{task_id}")
