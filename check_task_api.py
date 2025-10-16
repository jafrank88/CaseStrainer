#!/usr/bin/env python3
"""
Check what the task_status API returns
"""
import requests
import json

task_id = "56fa947d-f29e-4883-8470-1e2643170891"
url = f"http://127.0.0.1:5000/casestrainer/api/task_status/{task_id}"

print("=" * 80)
print(f"TASK STATUS API CHECK: {task_id}")
print("=" * 80)
print()

try:
    response = requests.get(url, timeout=5)
    print(f"Status Code: {response.status_code}")
    print()
    
    if response.status_code == 200:
        data = response.json()
        
        print("Response Keys:", list(data.keys()))
        print()
        
        print("Status:", data.get('status'))
        print("Success:", data.get('success'))
        print("Message:", data.get('message'))
        print()
        
        citations = data.get('citations', [])
        print(f"Citations Count: {len(citations)}")
        
        if citations:
            print("✅ Has citations!")
            print(f"First citation: {citations[0].get('citation', 'N/A')}")
        else:
            print("❌ No citations returned")
            print()
            print("Let's check the full response:")
            print(json.dumps(data, indent=2)[:1000])
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Exception: {e}")
