"""
Test the complete URL workflow: submit -> poll -> get results
"""
import requests
import json
import time

# Disable SSL warnings for testing
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

base_url = "https://wolf.law.uw.edu/casestrainer/api"

# Step 1: Submit URL for analysis
print("=" * 60)
print("STEP 1: Submitting URL for analysis")
print("=" * 60)

test_data = {
    "type": "url",
    "url": "https://www.courts.wa.gov/opinions/pdf/1034300.pdf",
    "client_request_id": f"test-{int(time.time())}"
}

response = requests.post(
    f"{base_url}/analyze",
    json=test_data,
    timeout=30,
    verify=False
)

print(f"Status: {response.status_code}")
result = response.json()
print(f"Response: {json.dumps(result, indent=2)[:800]}")

# Extract job_id for polling
job_id = result.get('metadata', {}).get('job_id')
task_id = result.get('task_id')
request_id = test_data['client_request_id']

print(f"\n📋 Job ID: {job_id}")
print(f"📋 Task ID: {task_id}")
print(f"📋 Request ID: {request_id}")

if not job_id and not task_id:
    print("\n❌ No job_id or task_id received - cannot poll for results")
    exit(1)

# Step 2: Poll for results
print("\n" + "=" * 60)
print("STEP 2: Polling for results")
print("=" * 60)

poll_id = task_id or job_id
max_attempts = 30
attempt = 0

while attempt < max_attempts:
    attempt += 1
    print(f"\nAttempt {attempt}/{max_attempts}...")
    
    # Try task_status endpoint
    try:
        status_response = requests.get(
            f"{base_url}/task_status/{poll_id}",
            timeout=10,
            verify=False
        )
        print(f"  task_status endpoint: {status_response.status_code}")
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"  Status: {status_data.get('status', 'unknown')}")
            
            if status_data.get('status') == 'completed':
                print("\n✅ PROCESSING COMPLETE!")
                print(f"\nFinal result:")
                print(json.dumps(status_data, indent=2)[:1500])
                
                citations = status_data.get('result', {}).get('citations', [])
                print(f"\n📊 Found {len(citations)} citations")
                break
            elif status_data.get('status') == 'failed':
                print(f"\n❌ Processing failed: {status_data.get('error')}")
                break
    except Exception as e:
        print(f"  task_status error: {e}")
    
    # Also try processing_progress endpoint
    try:
        progress_response = requests.get(
            f"{base_url}/processing_progress",
            params={'request_id': request_id},
            timeout=10,
            verify=False
        )
        print(f"  processing_progress endpoint: {progress_response.status_code}")
        
        if progress_response.status_code == 200:
            progress_data = progress_response.json()
            print(f"  Progress: {progress_data.get('progress', 0)}%")
            print(f"  Message: {progress_data.get('message', 'N/A')}")
    except Exception as e:
        print(f"  processing_progress error: {e}")
    
    time.sleep(2)

if attempt >= max_attempts:
    print("\n⏱️ Timeout - processing taking longer than expected")
    print("Check RQ worker logs for issues")
