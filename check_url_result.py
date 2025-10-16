#!/usr/bin/env python3
import requests
import json

task_id = "ef0981b6-7743-4274-8edc-bb01c1a2eb18"
url = f"http://127.0.0.1:5000/casestrainer/api/task_status/{task_id}"

response = requests.get(url, timeout=10)
data = response.json()

print("Status:", data.get('status'))
print("Success:", data.get('success'))
print("Citations:", len(data.get('citations', [])))
print()

if data.get('citations'):
    print("First 5 citations:")
    for cit in data.get('citations', [])[:5]:
        canonical = cit.get('canonical_name') or 'N/A'
        print(f"  - {cit.get('citation')}: {canonical[:50]}")
