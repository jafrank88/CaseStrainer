"""
Test full text with async processing
"""
import requests
import time

api_url = "http://localhost:5000/casestrainer/api/analyze"

# Read the full text
with open('1033940_extracted.txt', 'r', encoding='utf-8') as f:
    text_content = f.read()

print(f"Text length: {len(text_content)} characters")

# Send to API
payload = {
    "type": "text",
    "text": text_content
}

print(f"\nSending to API...")
response = requests.post(api_url, json=payload, timeout=10)
data = response.json()

print(f"Status: {response.status_code}")
print(f"Success: {data.get('success')}")

# Check if async
task_id = data.get('task_id') or data.get('metadata', {}).get('job_id')
if task_id:
    print(f"Task ID: {task_id}")
    print(f"Processing mode: {data.get('metadata', {}).get('processing_mode')}")
    
    # Wait for completion
    status_url = f"http://localhost:5000/casestrainer/api/task_status/{task_id}"
    print(f"\nWaiting for async processing...")
    
    for i in range(60):
        time.sleep(2)
        try:
            status_response = requests.get(status_url, timeout=5)
            status_data = status_response.json()
            
            status = status_data.get('status')
            if status in ['completed', 'failed']:
                print(f"\nCompleted in {i*2} seconds")
                print(f"Citations: {len(status_data.get('citations', []))}")
                print(f"Clusters: {len(status_data.get('clusters', []))}")
                
                citations = status_data.get('citations', [])
                if citations:
                    print(f"\nFirst 10 citations:")
                    for j, cit in enumerate(citations[:10], 1):
                        print(f"  {j}. {cit.get('citation')} - {cit.get('extracted_case_name', 'N/A')[:50]}")
                else:
                    print("\n❌ No citations found!")
                break
            elif i % 5 == 0:
                progress = status_data.get('progress_data', {}).get('overall_progress', 0)
                print(f"  Progress: {progress}%")
        except Exception as e:
            print(f"  Error checking status: {e}")
            break
else:
    print("No task ID - processed synchronously")
    print(f"Citations: {len(data.get('citations', []))}")
