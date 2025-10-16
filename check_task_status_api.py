#!/usr/bin/env python3
"""
Check task status through API
"""
import requests
import sys

if len(sys.argv) < 2:
    print("Usage: python check_task_status_api.py <task_id>")
    sys.exit(1)

task_id = sys.argv[1]
url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"

print(f"Checking task: {task_id}")
print(f"URL: {url}\n")

response = requests.get(url, timeout=10)
print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    import json
    result = response.json()
    print(f"\nTask Status:")
    print(f"  Status: {result.get('status')}")
    print(f"  Citations: {len(result.get('citations', []))}")
    print(f"  Clusters: {len(result.get('clusters', []))}")
    print(f"  Success: {result.get('success')}")
    print(f"  Message: {result.get('message')}")
else:
    print(f"Error: {response.text}")
