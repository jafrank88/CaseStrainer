#!/usr/bin/env python
"""Test with large text to force async processing."""

import requests
import time

# Create text larger than 5KB to force async
large_text = """
In the case of Smith v. Jones, 123 U.S. 456 (2020), the court established important precedent.
This was later affirmed in Johnson v. Smith, 456 F.2d 789 (2021).
The ruling in Brown v. Board of Education, 347 U.S. 483 (1954) remains influential.
Another important case is Roe v. Wade, 410 U.S. 113 (1973).
""" * 200  # Repeat 200 times to make it > 5KB

url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
data = {
    "text": large_text,
    "enable_verification": True,
    "client_request_id": f"test_large_{int(time.time())}"
}

print(f"Testing with large text to force async...")
print(f"Text length: {len(large_text)} chars (> 5KB threshold)")

try:
    response = requests.post(url, json=data, timeout=10)
    response.raise_for_status()
    result = response.json()
    
    print(f"\n✅ Response received!")
    print(f"Status: {result.get('status')}")
    print(f"Processing mode: {result.get('metadata', {}).get('processing_mode')}")
    
    task_id = result.get('task_id')
    if task_id:
        print(f"✅ Async processing - Task ID: {task_id}")
    else:
        print(f"❌ Sync processing - No task ID")
        
except Exception as e:
    print(f"❌ Error: {e}")
