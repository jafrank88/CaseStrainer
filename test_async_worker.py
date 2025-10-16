#!/usr/bin/env python3
"""
Test async worker processing
"""
import requests
import time
import json

# Test configuration
BASE_URL = "http://127.0.0.1:5000/casestrainer/api"  # Direct to backend
TEST_URL = "https://www.courts.wa.gov/opinions/pdf/1034300.pdf"

print("=" * 80)
print("ASYNC WORKER TEST")
print("=" * 80)
print()

# Submit job
print("[1/5] Submitting job to API...")
payload = {
    "type": "url",
    "url": TEST_URL
}

try:
    response = requests.post(f"{BASE_URL}/analyze", json=payload, timeout=30)
    print(f"  Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"  ERROR: {response.text}")
        exit(1)
    
    data = response.json()
    print(f"  Response: {json.dumps(data, indent=2)[:500]}...")
    
    # Try both task_id and job_id
    task_id = data.get('task_id') or data.get('metadata', {}).get('job_id')
    if not task_id:
        print("  ERROR: No task_id or job_id in response!")
        print(f"  Full response: {json.dumps(data, indent=2)}")
        exit(1)
    
    print(f"  Task ID: {task_id}")
    print()

except Exception as e:
    print(f"  ERROR: {e}")
    exit(1)

# Poll for completion
print("[2/5] Polling for completion (60 seconds max)...")
max_attempts = 60
attempt = 0

while attempt < max_attempts:
    attempt += 1
    time.sleep(1)
    
    try:
        status_response = requests.get(f"{BASE_URL}/task_status/{task_id}", timeout=10)
        if status_response.status_code == 200:
            status_data = status_response.json()
            current_status = status_data.get('status', 'unknown')
            progress = status_data.get('progress', 0)
            current_step = status_data.get('current_step', 'unknown')
            
            print(f"  Attempt {attempt}/60: status={current_status}, progress={progress}%, step={current_step}")
            
            # Check if finished
            if current_status in ['finished', 'completed']:
                print()
                print("[3/5] Job completed successfully!")
                print()
                
                # Get results
                citations_count = status_data.get('citations_count', 0)
                print(f"  Citations found: {citations_count}")
                
                if citations_count > 0:
                    print()
                    print("[4/5] ✅ ASYNC PROCESSING WORKS!")
                    print()
                    print("Worker can:")
                    print("  ✅ Pick up jobs from queue")
                    print("  ✅ Process PDFs")
                    print("  ✅ Extract citations")
                    print("  ✅ Complete successfully")
                    print()
                    print("[5/5] TEST PASSED")
                    exit(0)
                else:
                    print()
                    print("[4/5] ⚠️  Job completed but found 0 citations")
                    print("  This might indicate processing issue")
                    print()
                    print("[5/5] TEST PARTIAL - Job ran but no citations")
                    exit(0)
            
            elif current_status in ['failed', 'error']:
                print()
                print(f"[3/5] ❌ Job failed!")
                print(f"  Error: {status_data.get('error', 'Unknown error')}")
                print()
                print("[4/5] DIAGNOSING...")
                print("  Check worker logs: docker logs casestrainer-rqworker1-prod")
                print()
                print("[5/5] TEST FAILED")
                exit(1)
            
            # Check if stuck
            if attempt > 30 and current_step == 'Initializing' and progress < 20:
                print()
                print(f"[3/5] ❌ Job appears STUCK at {current_step}")
                print("  Been at Initializing for 30+ seconds")
                print()
                print("[4/5] DIAGNOSING...")
                print("  Likely causes:")
                print("    1. Import errors in worker code")
                print("    2. Worker can't access moved files")
                print("    3. Redis connection issues")
                print()
                print("  Check worker logs: docker logs casestrainer-rqworker1-prod --tail 50")
                print()
                print("[5/5] TEST FAILED - JOB STUCK")
                exit(1)
                
    except Exception as e:
        print(f"  Error polling: {e}")

print()
print("[3/5] ❌ Timeout after 60 seconds")
print("  Job did not complete in time")
print()
print("[4/5] Last known status:")
print(f"  Status: {current_status}")
print(f"  Progress: {progress}%")
print(f"  Step: {current_step}")
print()
print("[5/5] TEST TIMEOUT")
exit(1)
