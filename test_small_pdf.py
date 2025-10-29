#!/usr/bin/env python
"""Quick test with a smaller PDF."""

import requests
import time

# Use the smallest PDF
file_path = "d:\\dev\\casestrainer\\gov.uscourts.wyd.64014.141.0_1.pdf"

url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
files = {'file': open(file_path, 'rb')}
data = {
    "enable_verification": True,
    "client_request_id": f"test_small_pdf_{int(time.time())}"
}

print(f"Testing with small PDF: {file_path}")
print(f"Submitting...")

try:
    response = requests.post(url, files=files, data=data, timeout=60)
    response.raise_for_status()
    result = response.json()
    
    task_id = result.get('task_id')
    if task_id:
        print(f"✅ Job submitted asynchronously: {task_id}")
        print(f"Check status at: https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}")
    else:
        print("❌ Processed synchronously (no task_id)")
        print(f"Status: {result.get('status', 'unknown')}")
        if 'result' in result:
            citations = result['result'].get('citations', [])
            print(f"Citations found: {len(citations)}")
            
except Exception as e:
    print(f"Error: {e}")
finally:
    files['file'].close()
