#!/usr/bin/env python3
"""
Test async with large document (>5KB to force async)
"""
import requests
import time
import json

BASE_URL = "http://127.0.0.1:5000/casestrainer/api"

# Create a large test text (>5KB) to force async
base_text = """
In Smith v. Jones, 123 F.3d 456 (9th Cir. 2020), the court held that the defendant's actions
were not sufficient to establish liability. The precedent set in Brown v. Board of Education, 
347 U.S. 483 (1954), was cited extensively. Additionally, the court referenced Miranda v. Arizona, 
384 U.S. 436 (1966), to support the ruling regarding procedural safeguards.
"""

# Repeat to make it larger than 5KB
test_text = (base_text * 50).strip()  # About 10KB
text_size = len(test_text)

print("=" * 80)
print("ASYNC PROCESSING TEST (Large Document)")
print("=" * 80)
print(f"Text size: {text_size} bytes (threshold: 5120)")
print(f"Expected mode: {'ASYNC' if text_size >= 5120 else 'SYNC'}")
print()

# Submit job
print("[1] Submitting large document...")
try:
    response = requests.post(
        f"{BASE_URL}/analyze",
        json={"type": "text", "text": test_text},
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"ERROR: {response.status_code} - {response.text}")
        exit(1)
    
    data = response.json()
    task_id = data.get('metadata', {}).get('job_id') or data.get('task_id')
    processing_mode = data.get('metadata', {}).get('processing_mode')
    
    print(f"  Task ID: {task_id}")
    print(f"  Mode: {processing_mode}")
    print()
    
    if processing_mode == 'immediate':
        print(f"⚠️  Still SYNC! Mode is: {processing_mode}")
        print(f"  Text was {text_size} bytes but still processed sync")
        print(f"  This might be intentional or a threshold issue")
        exit(0)
    
    if processing_mode != 'queued':
        print(f"⚠️  Unexpected mode: {processing_mode}")
        exit(0)
    
    print("✅ Job queued for async processing!")
    print()
    
except Exception as e:
    print(f"ERROR submitting: {e}")
    exit(1)

# Monitor for 30 seconds
print("[2] Monitoring async job (30 seconds)...")
print()

for i in range(30):
    try:
        status_response = requests.get(f"{BASE_URL}/task_status/{task_id}", timeout=5)
        if status_response.status_code == 200:
            status_data = status_response.json()
            status = status_data.get('status', 'unknown')
            progress = status_data.get('progress', 0)
            step = status_data.get('current_step', 'unknown')
            message = status_data.get('message', '')[:30]
            
            print(f"  [{i+1:2d}s] {status:12s} {progress:3d}% {step:20s} {message}")
            
            if status in ['finished', 'completed']:
                citations = status_data.get('citations_count', 0)
                print()
                print(f"✅ JOB COMPLETED! Found {citations} citations")
                exit(0)
            elif status in ['failed', 'error']:
                error = status_data.get('error', 'Unknown')
                print()
                print(f"❌ JOB FAILED: {error}")
                exit(1)
        else:
            print(f"  [{i+1:2d}s] Error: {status_response.status_code}")
    
    except Exception as e:
        print(f"  [{i+1:2d}s] Exception: {type(e).__name__}")
    
    time.sleep(1)

print()
print("⏱️  TIMEOUT - job did not complete in 30 seconds")
print()
print("If stuck at 'Initializing', check worker logs:")
print("  docker logs casestrainer-rqworker1-prod --tail 100")
