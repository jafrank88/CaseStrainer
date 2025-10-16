#!/usr/bin/env python3
"""
Direct test of URL processing to see if worker picks up the job
"""
import requests
import time
import json

# The PDF URL to test
url = "https://www.courts.wa.gov/opinions/pdf/1034300.pdf"
base_url = "http://localhost:5000"

print("="*60)
print("TESTING URL PROCESSING")
print("="*60)
print(f"URL: {url}")
print(f"Backend: {base_url}")
print()

# Step 1: Submit the URL
print("Step 1: Submitting URL to analyze endpoint...")
analyze_url = f"{base_url}/casestrainer/api/analyze"

payload = {
    "type": "url",
    "url": url
}

headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(analyze_url, json=payload, headers=headers, timeout=30)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("Response:")
        print(json.dumps(result, indent=2)[:500])
        
        task_id = result.get('task_id') or result.get('request_id')
        
        if task_id:
            print(f"\n✓ Job submitted successfully!")
            print(f"  Task ID: {task_id}")
            
            # Step 2: Poll for results
            print(f"\nStep 2: Polling for results (max 2 minutes)...")
            status_url = f"{base_url}/casestrainer/api/task_status/{task_id}"
            
            max_polls = 24  # 2 minutes (24 * 5 seconds)
            for i in range(max_polls):
                time.sleep(5)
                
                try:
                    status_response = requests.get(status_url, timeout=10)
                    status_data = status_response.json()
                    
                    status = status_data.get('status', 'unknown')
                    progress = status_data.get('progress', 0)
                    current_step = status_data.get('current_step', 'unknown')
                    message = status_data.get('message', '')
                    
                    print(f"  [{i+1}/{max_polls}] Status: {status} | Progress: {progress}% | Step: {current_step}")
                    
                    if status_data.get('progress_data'):
                        steps = status_data['progress_data'].get('steps', [])
                        if steps:
                            for step in steps:
                                if step.get('status') != 'pending':
                                    print(f"    - {step['name']}: {step['status']} ({step.get('progress', 0)}%)")
                    
                    if status == 'completed':
                        citations_count = len(status_data.get('citations', []))
                        clusters_count = len(status_data.get('clusters', []))
                        print(f"\n✓ SUCCESS!")
                        print(f"  Citations: {citations_count}")
                        print(f"  Clusters: {clusters_count}")
                        break
                    elif status == 'failed':
                        print(f"\n✗ FAILED: {status_data.get('error', 'Unknown error')}")
                        break
                        
                except Exception as e:
                    print(f"  Error polling: {e}")
                    
            else:
                print(f"\n✗ TIMEOUT: Job did not complete in 2 minutes")
                print(f"  Last status: {status}")
                print(f"  Last step: {current_step}")
        else:
            print("\n✗ No task_id in response!")
            print("Response keys:", list(result.keys()))
            
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text[:500])
        
except Exception as e:
    print(f"✗ Exception: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)
