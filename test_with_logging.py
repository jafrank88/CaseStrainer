#!/usr/bin/env python
"""Submit URL and check task status with new logging"""
import requests
import json
import time

# Submit the URL
print("=" * 60)
print("STEP 1: Submit URL for processing")
print("=" * 60)

url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
payload = {
    "type": "url",
    "url": "https://www.courts.wa.gov/opinions/pdf/1034300.pdf",
    "client_request_id": "debug-test-logging"
}

response = requests.post(url, json=payload, timeout=60)
print(f"Status: {response.status_code}")
data = response.json()
print(f"Response: {json.dumps(data, indent=2)[:300]}...")

task_id = data.get('task_id') or data.get('request_id')
print(f"\n✅ Task ID: {task_id}")

# Wait for processing
print("\n" + "=" * 60)
print("STEP 2: Waiting for processing to complete...")
print("=" * 60)

for i in range(60):  # Wait up to 60 seconds
    time.sleep(1)
    try:
        status_url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"
        status_response = requests.get(status_url, timeout=10)
        status_data = status_response.json()
        
        status = status_data.get('status', 'unknown')
        citations_count = len(status_data.get('citations', []))
        clusters_count = len(status_data.get('clusters', []))
        
        print(f"[{i+1}s] Status: {status}, Citations: {citations_count}, Clusters: {clusters_count}")
        
        if status == 'completed':
            print("\n✅ COMPLETED!")
            print(f"Citations found: {citations_count}")
            print(f"Clusters found: {clusters_count}")
            
            if citations_count > 0:
                print("\n🎉 SUCCESS! Citations retrieved correctly!")
                print(f"\nFirst 3 citations:")
                for j, cit in enumerate(status_data['citations'][:3], 1):
                    print(f"  {j}. {cit.get('citation', 'N/A')}")
            else:
                print("\n❌ PROBLEM: Status is completed but 0 citations returned")
                print("Check backend logs for detailed job.result information")
            break
            
        elif status in ['failed', 'error']:
            print(f"\n❌ FAILED: {status_data.get('error', 'Unknown error')}")
            break
            
    except Exception as e:
        print(f"[{i+1}s] Error checking status: {e}")

print("\n" + "=" * 60)
print("Now check backend logs:")
print(f"docker logs casestrainer-backend-prod --tail 50 | findstr \"{task_id}\"")
print("=" * 60)
