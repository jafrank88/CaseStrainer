import requests
import json
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print("Testing ASYNC processing with large text...\n")

# Create a larger text sample (repeat to exceed sync threshold)
base_text = """
In State v. Johnson, 159 Wn.2d 700, 153 P.3d 846, the court held that evidence was admissible.
The defendant cited Lopez Demetrio v. Dep't of Lab. & Indus., 188 Wn. App. 869, 354 P.3d 1123.
Another relevant case is Bostain v. Food Express, Inc., 159 Wn.2d 700, 153 P.3d 846.
The court also referenced State v. Smith, 150 Wn.2d 100, and Jones v. United States, 140 Wn.2d 500.
"""

# Repeat to make it large enough for async
large_text = (base_text * 50) + "\n\nThis document contains multiple citations that should be processed asynchronously."

payload = {
    'type': 'text',
    'text': large_text
}

print(f"Submitting large text: {len(large_text)} characters")
print("(Should trigger async processing)\n")

try:
    response = requests.post(
        'https://wolf.law.uw.edu/casestrainer/api/analyze',
        json=payload,
        verify=False,
        timeout=60
    )
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        exit(1)
    
    data = response.json()
    task_id = data.get('request_id') or data.get('task_id')
    processing_mode = data.get('metadata', {}).get('processing_mode', 'unknown')
    sync_complete = data.get('metadata', {}).get('sync_complete', False)
    
    print(f"Task ID: {task_id}")
    print(f"Processing mode: {processing_mode}")
    print(f"Sync complete flag: {sync_complete}")
    
    # Check if sync or async
    if sync_complete or data.get('citations'):
        print("\n⚠️ Was processed SYNC (not async as expected)")
        print(f"Citations: {len(data.get('citations', []))}")
        print(f"Reason: Text may be below async threshold")
        
        # Show sample
        if data.get('citations'):
            print("\nSample citations:")
            for i, cit in enumerate(data.get('citations', [])[:3], 1):
                print(f"  {i}. {cit.get('citation_text', 'N/A')} - {cit.get('extracted_case_name', 'N/A')}")
        
        exit(0)
    
    # Poll for async results
    print("\n🔄 Polling for ASYNC results...")
    url = f'https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}'
    
    for attempt in range(40):
        time.sleep(3)
        
        try:
            status_response = requests.get(url, verify=False, timeout=10)
            
            if status_response.status_code == 404:
                print(f"   [{attempt+1}] ❌ Task not found (404)")
                continue
            
            status_data = status_response.json()
            status = status_data.get('status')
            progress = status_data.get('progress', 0)
            message = status_data.get('message', '')
            
            print(f"   [{attempt+1}] {status}: {progress}% - {message}")
            
            if status == 'completed':
                print("\n✅ ASYNC COMPLETED!")
                citations = status_data.get('citations', [])
                clusters = status_data.get('clusters', [])
                
                print(f"   Citations: {len(citations)}")
                print(f"   Clusters: {len(clusters)}")
                
                if citations:
                    print("\n   Sample citations:")
                    for i, cit in enumerate(citations[:5], 1):
                        text = cit.get('citation_text', 'N/A')
                        case = cit.get('extracted_case_name', 'N/A')
                        print(f"     {i}. {text} - {case}")
                else:
                    print("\n   ⚠️ No citations in response")
                    print(f"   Full response keys: {list(status_data.keys())}")
                
                print("\n✅ Async processing completed!")
                exit(0)
            
            elif status == 'failed':
                print(f"\n❌ Failed: {status_data.get('error', 'Unknown')}")
                exit(1)
        
        except Exception as e:
            print(f"   Error: {e}")
            continue
    
    print("\n❌ Timeout after 40 attempts (2 minutes)")
    exit(1)

except Exception as e:
    print(f"\n❌ Request error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
