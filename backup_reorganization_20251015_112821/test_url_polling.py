import requests
import json
import time
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

task_id = 'bcf3bd5d-2290-4eff-87b9-70754e5bd803'
url = f'https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}'

print(f"Polling task: {task_id}\n")

for i in range(20):
    try:
        response = requests.get(url, verify=False, timeout=10)
        data = response.json()
        
        status = data.get('status')
        progress = data.get('progress', 0)
        message = data.get('message', '')
        
        print(f"Attempt {i+1}: Status={status}, Progress={progress}% - {message}")
        
        if status == 'completed':
            print("\n" + "="*60)
            print("TASK COMPLETED!")
            print("="*60)
            citations = data.get('citations', [])
            clusters = data.get('clusters', [])
            print(f"\nFound {len(citations)} citations")
            print(f"Found {len(clusters)} clusters")
            
            if citations:
                print("\nFirst few citations:")
                for idx, citation in enumerate(citations[:5]):
                    print(f"\n  Citation {idx+1}:")
                    print(f"    Text: {citation.get('citation_text', 'N/A')}")
                    print(f"    Case Name: {citation.get('extracted_case_name', 'N/A')}")
                    print(f"    Verified: {citation.get('verified', False)}")
            break
            
        elif status == 'failed':
            print("\n" + "="*60)
            print("TASK FAILED!")
            print("="*60)
            print(f"Error: {data.get('error', 'Unknown error')}")
            break
            
        time.sleep(3)
        
    except Exception as e:
        print(f"Error polling task: {e}")
        break

print("\nPolling complete.")
