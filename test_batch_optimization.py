#!/usr/bin/env python3
"""Test batch verification optimization on production"""
import requests
import time
import json

BASE_URL = "https://wolf.law.uw.edu/casestrainer/api"
PDF_URL = "https://www.courts.wa.gov/opinions/pdf/1034300.pdf"

print("\n" + "=" * 70)
print("TESTING BATCH VERIFICATION OPTIMIZATION")
print("=" * 70)
print(f"\nPDF: {PDF_URL}")
print(f"Server: {BASE_URL}")
print("\n" + "-" * 70)

# Submit the job
print("\n[1] Submitting PDF URL for processing...")
submit_start = time.time()

response = requests.post(
    f"{BASE_URL}/analyze",
    data={
        'url': PDF_URL,
        'type': 'url'
    },
    timeout=30
)

submit_time = time.time() - submit_start

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

print(f"✅ Task submitted in {submit_time:.1f}s")
print(f"   Task ID: {task_id}")
print(f"   Mode: {data.get('metadata', {}).get('processing_mode', 'unknown')}")

# Monitor progress with detailed timing
print(f"\n[2] Monitoring job progress...")
print("=" * 70)

process_start = time.time()
last_step = -1
last_message = ""
extraction_time = None
verification_time = None

for i in range(120):  # Monitor for up to 2 minutes
    time.sleep(1)
    elapsed = int(time.time() - process_start)
    
    try:
        status_resp = requests.get(f"{BASE_URL}/task_status/{task_id}", timeout=10)
        status_data = status_resp.json()
        
        status = status_data.get('status', 'unknown')
        
        if status == 'completed':
            total_time = time.time() - process_start
            citations = len(status_data.get('citations', []))
            verified = status_data.get('statistics', {}).get('verified_citations', 0)
            
            print(f"\n{'=' * 70}")
            print(f"✅ COMPLETED in {total_time:.1f} seconds!")
            print(f"{'=' * 70}")
            print(f"\n📊 Results:")
            print(f"   Total Time: {total_time:.1f}s")
            print(f"   Citations Found: {citations}")
            print(f"   Verified: {verified}")
            print(f"   Verification Rate: {(verified/citations*100):.1f}%" if citations > 0 else "   N/A")
            
            # Show timing breakdown if available
            progress = status_data.get('progress_data', {})
            if progress.get('steps'):
                print(f"\n⏱️  Step Timing:")
                for step in progress['steps']:
                    if step.get('start_time') and step.get('end_time'):
                        step_duration = step['end_time'] - step['start_time']
                        print(f"   {step['name']}: {step_duration:.2f}s")
            
            # Compare to old performance
            print(f"\n🚀 Performance:")
            print(f"   Old system: ~250s for 132 citations")
            print(f"   New system: {total_time:.1f}s for {citations} citations")
            if citations > 0 and total_time > 0:
                speedup = 250 / total_time
                print(f"   Speedup: {speedup:.1f}x faster! ✨")
            
            exit(0)
            
        elif status == 'error' or status == 'failed':
            print(f"\n❌ FAILED: {status_data.get('error', 'Unknown error')}")
            exit(1)
        else:
            # Show progress
            progress_data = status_data.get('progress_data', {})
            current_step = progress_data.get('current_step', 0)
            total_steps = progress_data.get('total_steps', 6)
            overall_progress = progress_data.get('overall_progress', 0)
            message = progress_data.get('current_message', 'Processing')
            
            # Only print when step changes or every 10 seconds
            if current_step != last_step or elapsed % 10 == 0 or message != last_message:
                step_name = progress_data.get('steps', [{}])[current_step].get('name', 'Unknown') if current_step < len(progress_data.get('steps', [])) else 'Processing'
                print(f"  [{elapsed:3d}s] Step {current_step}/{total_steps} - {overall_progress}% - {step_name}")
                last_step = current_step
                last_message = message
                
    except Exception as e:
        print(f"  [{elapsed:3d}s] Error checking status: {e}")

print(f"\n⏱️  Timeout after 120 seconds")
print(f"   Job may still be processing...")
print(f"\n   Check manually:")
print(f"   {BASE_URL}/task_status/{task_id}")
