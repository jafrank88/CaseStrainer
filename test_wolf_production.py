#!/usr/bin/env python3
"""Test CaseStrainer on wolf.law.uw.edu production"""
import requests
import time
import json

# Production URL
BASE_URL = "https://wolf.law.uw.edu/casestrainer/api"

# Test text - large enough to trigger async (>5KB)
test_text = """In Smith v. Jones, 123 F.3d 456 (9th Cir. 2020), the court held...""" * 500

print("\n" + "=" * 70)
print("TESTING WOLF.LAW.UW.EDU PRODUCTION")
print("=" * 70)
print(f"\nSubmitting text ({len(test_text)} bytes) - should trigger async...")

try:
    # Submit the job
    response = requests.post(
        f"{BASE_URL}/analyze",
        data={'text': test_text, 'type': 'text'},
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Submission failed: {response.status_code}")
        print(response.text)
        exit(1)
    
    data = response.json()
    task_id = data.get('task_id') or data.get('request_id')
    
    if not task_id:
        print("❌ No task_id in response")
        print(json.dumps(data, indent=2))
        exit(1)
    
    print(f"✅ Task ID: {task_id}")
    print(f"   Mode: {data.get('metadata', {}).get('processing_mode', 'unknown')}")
    
    # Poll for 20 seconds
    print(f"\nPolling for 20 seconds...")
    start_time = time.time()
    
    for i in range(20):
        time.sleep(1)
        elapsed = int(time.time() - start_time)
        
        try:
            status_resp = requests.get(f"{BASE_URL}/task_status/{task_id}", timeout=10)
            status_data = status_resp.json()
            
            status = status_data.get('status', 'unknown')
            progress = status_data.get('progress', 0)
            
            if status == 'completed':
                citations = len(status_data.get('citations', []))
                print(f"\n✅ COMPLETED in {elapsed}s!")
                print(f"   Citations: {citations}")
                exit(0)
            elif status == 'error' or status == 'failed':
                print(f"\n❌ FAILED: {status_data.get('error', 'Unknown error')}")
                exit(1)
            else:
                # Show progress
                current_step = status_data.get('progress_data', {}).get('current_step', 0)
                total_steps = status_data.get('progress_data', {}).get('total_steps', 6)
                message = status_data.get('progress_data', {}).get('current_message', 'Processing')
                print(f"  [{elapsed:2d}s] Step {current_step}/{total_steps} - {progress}% - {message[:40]}")
                
        except Exception as e:
            print(f"  [{elapsed:2d}s] Error checking status: {e}")
    
    # After 20 seconds
    print(f"\n⚠️  Still processing after 20 seconds")
    print(f"   This means the async fix may not be deployed yet")
    print(f"\n   Check manually: {BASE_URL}/task_status/{task_id}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
