import requests
import json
import time
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print("Testing async URL processing with rate limit fix...\n")

# Submit a new URL job
payload = {
    'type': 'url',
    'url': 'https://www.courtlistener.com/opinion/10460933/robert-cassell-v-state-of-alaska-department-of-fish-game-board-of-game/'
}

print(f"Submitting URL: {payload['url']}\n")

try:
    response = requests.post('https://wolf.law.uw.edu/casestrainer/api/analyze', 
                            json=payload, 
                            verify=False, 
                            timeout=60)

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        exit(1)

    data = response.json()
    task_id = data.get('request_id') or data.get('task_id')
    print(f"✓ Task submitted: {task_id}")
    print(f"  Status: {data.get('message', 'N/A')}")
    print(f"  Document length: {data.get('document_length', 'N/A')} characters")
    print(f"  Processing mode: {data.get('metadata', {}).get('processing_mode', 'N/A')}\n")

    # Poll for results
    print("Polling for results (max 2 minutes)...\n")
    url = f'https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}'

    for i in range(40):
        try:
            response = requests.get(url, verify=False, timeout=10)
            result = response.json()
            
            status = result.get('status')
            progress = result.get('progress', 0)
            message = result.get('message', '')
            
            print(f"[{i+1}] {status}: {progress}% - {message}")
            
            if status == 'completed':
                print("\n" + "="*60)
                print("✅ SUCCESS! ASYNC PROCESSING WORKS!")
                print("="*60)
                citations = result.get('citations', [])
                clusters = result.get('clusters', [])
                print(f"\nFound {len(citations)} citations")
                print(f"Found {len(clusters)} clusters")
                
                if citations:
                    print("\nFirst 5 citations:")
                    for idx, citation in enumerate(citations[:5]):
                        text = citation.get('citation_text', 'N/A')
                        case_name = citation.get('extracted_case_name', 'N/A')
                        verified = citation.get('verified', False)
                        print(f"  {idx+1}. {text}")
                        print(f"     Case: {case_name}, Verified: {verified}")
                
                print("\n✅ Async processing is NOW WORKING!")
                break
                
            elif status == 'failed':
                print("\n" + "="*60)
                print("❌ TASK FAILED")
                print("="*60)
                print(f"Error: {result.get('error', 'Unknown error')}")
                break
                
            time.sleep(3)
            
        except Exception as e:
            print(f"Error polling: {e}")
            break
    else:
        print("\n⚠️ Polling timeout - check worker logs")

except Exception as e:
    print(f"\n❌ Request error: {e}")
    import traceback
    traceback.print_exc()

print("\nTest complete.")
