#!/usr/bin/env python3
"""
Detailed async test with real-time monitoring
"""
import requests
import time
import json

BASE_URL = "http://127.0.0.1:5000/casestrainer/api"
TEST_TEXT = "The court in Smith v. Jones, 123 F.3d 456 (9th Cir. 2020) held that..."

print("=" * 80)
print("ASYNC WORKER DETAILED TEST")
print("=" * 80)
print()

# Submit job
print("[1] Submitting job...")
try:
    response = requests.post(
        f"{BASE_URL}/analyze",
        json={"type": "text", "text": TEST_TEXT},
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"ERROR: {response.status_code} - {response.text}")
        exit(1)
    
    data = response.json()
    task_id = data.get('metadata', {}).get('job_id')
    processing_mode = data.get('metadata', {}).get('processing_mode')
    
    print(f"  Task ID: {task_id}")
    print(f"  Mode: {processing_mode}")
    print()
    
    if processing_mode != 'queued':
        print(f"⚠️  Not queued! Mode is: {processing_mode}")
        print(f"  This means it processed sync instead of async")
        exit(0)
    
except Exception as e:
    print(f"ERROR submitting: {e}")
    exit(1)

# Monitor for 20 seconds with detailed output
print("[2] Monitoring (20 seconds)...")
print()

for i in range(20):
    try:
        status_response = requests.get(f"{BASE_URL}/task_status/{task_id}", timeout=5)
        if status_response.status_code == 200:
            status_data = status_response.json()
            status = status_data.get('status', 'unknown')
            progress = status_data.get('progress', 0)
            step = status_data.get('current_step', 'unknown')
            message = status_data.get('message', '')
            
            print(f"  [{i+1:2d}s] status={status:12s} progress={progress:3d}% step={step:20s} msg={message}")
            
            if status in ['finished', 'completed']:
                print()
                print("✅ JOB COMPLETED!")
                exit(0)
            elif status in ['failed', 'error']:
                print()
                print(f"❌ JOB FAILED: {status_data.get('error', 'Unknown')}")
                exit(1)
        else:
            print(f"  [{i+1:2d}s] Error getting status: {status_response.status_code}")
    
    except Exception as e:
        print(f"  [{i+1:2d}s] Exception: {e}")
    
    time.sleep(1)

print()
print("⏱️  TIMEOUT after 20 seconds - job did not complete")
print()
print("Now check worker logs:")
print("  docker logs casestrainer-rqworker1-prod --tail 50")
