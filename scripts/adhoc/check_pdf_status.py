import requests
import json

task_id = "9748a351-17c2-4320-9d0a-f06f94d224f2"
url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"

try:
    response = requests.get(url)
    response.raise_for_status()
    status = response.json()
    
    print(f"Status: {status.get('status')}")
    print(f"Progress: {status.get('verification_status', {}).get('progress_percent', 0)}%")
    print(f"Message: {status.get('verification_status', {}).get('current_message', 'N/A')}")
    
    if status.get('status') == 'completed':
        print("\n✅ COMPLETED!")
        if 'result' in status:
            result = status['result']
            print(f"Citations: {len(result.get('citations', []))}")
            print(f"Clusters: {len(result.get('clusters', []))}")
            
            # Show first few citations
            citations = result.get('citations', [])
            if citations:
                print("\nFirst 3 citations:")
                for i, cit in enumerate(citations[:3]):
                    verified = "✅" if cit.get('verified') else "❌"
                    print(f"  {i+1}. {cit.get('citation', 'N/A')} {verified}")
                    if cit.get('extracted_case_name'):
                        print(f"     Case: {cit.get('extracted_case_name')}")
                    
except Exception as e:
    print(f"Error: {e}")
