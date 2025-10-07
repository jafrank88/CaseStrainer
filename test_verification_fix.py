"""
Quick test to verify the verification fix is working
"""
import requests
import json
import time

url = "https://wolf.law.uw.edu/casestrainer/api/analyze"

# Small test with known citation
payload = {
    "type": "text",
    "text": "See State v. Johnson, 183 Wn.2d 649, 370 P.3d 157 (2016)."
}

print("Testing verification fix with small sample...")
print(f"Text: {payload['text']}\n")

response = requests.post(url, json=payload, verify=False, timeout=30)
result = response.json()

task_id = result.get('task_id') or result.get('request_id')
print(f"Task ID: {task_id}")

# Wait for completion
status_url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"

for i in range(30):
    time.sleep(2)
    status_response = requests.get(status_url, verify=False, timeout=10)
    status_data = status_response.json()
    
    status = status_data.get('status')
    if status in ['completed', 'failed']:
        print(f"\nStatus: {status}")
        break

# Get results
result_data = status_data.get('result', {})
citations = result_data.get('citations', [])

print(f"\n{'='*60}")
print(f"RESULTS")
print(f"{'='*60}")
print(f"Total Citations: {len(citations)}")

for i, cit in enumerate(citations, 1):
    print(f"\n{i}. {cit.get('citation')}")
    print(f"   extracted_case_name: {cit.get('extracted_case_name')}")
    print(f"   extracted_date: {cit.get('extracted_date')}")
    print(f"   verified: {cit.get('verified')}")
    print(f"   verification_status: {cit.get('verification_status')}")
    print(f"   canonical_name: {cit.get('canonical_name')}")
    print(f"   canonical_date: {cit.get('canonical_date')}")
    print(f"   verification_source: {cit.get('verification_source')}")

print(f"\n{'='*60}")
verified_count = sum(1 for c in citations if c.get('verified'))
print(f"Verification Rate: {verified_count}/{len(citations)} ({verified_count/len(citations)*100:.1f}%)")
print(f"{'='*60}")
