import requests
import json
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print("Testing async processing after restart...\n")

# Test with TEXT (not URL to avoid rate limit issues)
text_sample = """
In State v. Johnson, 159 Wn.2d 700, the court held that evidence was admissible.
The defendant cited Lopez Demetrio v. Dep't of Lab. & Indus., 188 Wn. App. 869.
Another relevant case is Bostain v. Food Express, Inc., 159 Wn.2d 700.
"""

payload = {
    'type': 'text',
    'text': text_sample
}

print("Submitting text for analysis...")
print(f"Text length: {len(text_sample)} characters\n")

try:
    response = requests.post(
        'https://wolf.law.uw.edu/casestrainer/api/analyze',
        json=payload,
        verify=False,
        timeout=60
    )
    
    print(f"Initial response status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        exit(1)
    
    data = response.json()
    
    # Check if it was processed immediately (sync)
    if data.get('metadata', {}).get('sync_complete'):
        print("\n✅ SYNC PROCESSING (immediate result)")
        print(f"   Citations: {len(data.get('citations', []))}")
        print(f"   Clusters: {len(data.get('clusters', []))}")
        
        if data.get('citations'):
            print("\n   Citations found:")
            for i, cit in enumerate(data.get('citations', [])[:5], 1):
                text = cit.get('citation_text', 'N/A')
                case = cit.get('extracted_case_name', 'N/A')
                print(f"     {i}. {text} - {case}")
        
        print("\n✅ Sync processing WORKS!")
        exit(0)
    
    # Otherwise, it's async - poll for results
    task_id = data.get('request_id') or data.get('task_id')
    processing_mode = data.get('metadata', {}).get('processing_mode', 'unknown')
    
    print(f"\n🔄 ASYNC PROCESSING")
    print(f"   Task ID: {task_id}")
    print(f"   Mode: {processing_mode}")
    
    # Poll for completion
    url = f'https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}'
    
    for attempt in range(40):
        time.sleep(3)
        
        try:
            status_response = requests.get(url, verify=False, timeout=10)
            status_data = status_response.json()
            
            status = status_data.get('status')
            progress = status_data.get('progress', 0)
            message = status_data.get('message', '')
            
            print(f"   [{attempt+1}] {status}: {progress}% - {message}")
            
            if status == 'completed':
                print("\n✅ ASYNC PROCESSING COMPLETED!")
                citations = status_data.get('citations', [])
                clusters = status_data.get('clusters', [])
                
                print(f"   Citations: {len(citations)}")
                print(f"   Clusters: {len(clusters)}")
                
                if citations:
                    print("\n   Citations found:")
                    for i, cit in enumerate(citations[:5], 1):
                        text = cit.get('citation_text', 'N/A')
                        case = cit.get('extracted_case_name', 'N/A')
                        print(f"     {i}. {text} - {case}")
                
                print("\n✅ Async processing WORKS!")
                exit(0)
            
            elif status == 'failed':
                print(f"\n❌ Task failed: {status_data.get('error', 'Unknown error')}")
                exit(1)
        
        except Exception as e:
            print(f"   Error polling: {e}")
            continue
    
    print("\n⚠️ Timeout waiting for results")
    print("Check worker logs: docker logs casestrainer-rqworker1-prod --tail=50")
    exit(1)

except Exception as e:
    print(f"\n❌ Request failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
