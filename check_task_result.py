#!/usr/bin/env python
"""Check the task result from the async processing"""
import requests
import json
import time

task_id = "client-1760644135107-jqu12go6x"
url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"

print(f"Checking task status for: {task_id}")
print(f"URL: {url}")
print("=" * 60)

for i in range(5):
    print(f"\nAttempt {i+1}:")
    try:
        response = requests.get(url, timeout=10)
        print(f"  Status code: {response.status_code}")
        
        data = response.json()
        print(f"  Task status: {data.get('status', 'unknown')}")
        print(f"  Citations: {len(data.get('citations', []))}")
        print(f"  Clusters: {len(data.get('clusters', []))}")
        
        if data.get('status') == 'completed':
            print(f"\n✅ TASK COMPLETED!")
            if data.get('citations'):
                print(f"\nFirst 5 citations:")
                for j, cit in enumerate(data['citations'][:5], 1):
                    print(f"  {j}. {cit.get('citation', 'N/A')}")
            break
        elif data.get('status') in ['failed', 'error']:
            print(f"\n❌ TASK FAILED!")
            print(f"  Error: {data.get('error', 'Unknown')}")
            break
        else:
            print(f"  Still processing...")
            time.sleep(2)
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        break
