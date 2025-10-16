"""Test async processing with large content to trigger async path"""
import requests
import time
import json

# Create large text content (>5KB) to force async processing
large_text = """
East Palo Alto v. U.S. Dep't of Health & Hum. Servs., 780 F. Supp. 3d 897 (N.D. Cal. 2024)
Franklin v. Massachusetts, 505 U.S. 788 (1992)
Block v. Cmty. Nutrition Inst., 604 U.S. 650 (2024)

""" * 100  # Repeat to make it large

url = "http://localhost:5000/casestrainer/api/analyze"
print(f"[ASYNC TEST] Sending large text ({len(large_text)} bytes) to force async processing")

# Send request
response = requests.post(
    url,
    json={'text': large_text},
    timeout=5
)

print(f"[STATUS] Response status: {response.status_code}")
result = response.json()

if result.get('status') == 'processing':
    print(f"[ASYNC] Task queued: {result.get('task_id')}")
    task_id = result.get('task_id')
    
    # Poll for results
    poll_url = f"http://localhost:5000/casestrainer/api/task/{task_id}"
    max_attempts = 60
    for i in range(max_attempts):
        time.sleep(2)
        poll_response = requests.get(poll_url)
        poll_result = poll_response.json()
        
        status = poll_result.get('status', 'unknown')
        print(f"[POLL {i+1}] Status: {status}")
        
        if status == 'completed':
            citations = poll_result.get('result', {}).get('citations', [])
            print(f"\n[SUCCESS] Got {len(citations)} citations")
            
            # Show case names to check for truncations
            print(f"\n[CASE NAMES]:")
            for idx, cite in enumerate(citations[:10], 1):
                name = cite.get('extracted_case_name', 'N/A')
                citation_text = cite.get('citation', '')
                print(f"   {idx}. {citation_text:30s} -> {name}")
            break
        elif status in ('failed', 'error'):
            print(f"[ERROR] Task failed: {poll_result.get('error')}")
            break
else:
    # Immediate results (sync)
    print(f"[SYNC] Got immediate results")
    citations = result.get('citations', [])
    print(f"[SUCCESS] Got {len(citations)} citations")
    
    # Show case names
    print(f"\n[CASE NAMES]:")
    for idx, cite in enumerate(citations[:10], 1):
        name = cite.get('extracted_case_name', 'N/A')
        citation_text = cite.get('citation', '')
        print(f"   {idx}. {citation_text:30s} -> {name}")
