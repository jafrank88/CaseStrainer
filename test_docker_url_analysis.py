"""
Test URL analysis through Docker production setup
"""
import requests
import json
import time

# Test the production endpoint
url = "https://wolf.law.uw.edu/casestrainer/api/analyze"

payload = {
    "type": "url",
    "url": "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
}

print("Testing URL analysis through Docker production setup...")
print(f"Endpoint: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print("\n" + "="*60)

try:
    # Submit the analysis request
    print("\n1. Submitting URL for analysis...")
    response = requests.post(url, json=payload, verify=False, timeout=30)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    result = response.json()
    print(f"\nResponse Body:")
    print(json.dumps(result, indent=2))
    
    # Check if it's async processing
    if 'task_id' in result or 'request_id' in result:
        task_id = result.get('task_id') or result.get('request_id')
        print(f"\n2. Task queued with ID: {task_id}")
        print("Polling for results...")
        
        # Poll for results
        status_url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"
        max_attempts = 60  # 5 minutes
        
        for attempt in range(max_attempts):
            time.sleep(5)
            status_response = requests.get(status_url, verify=False, timeout=10)
            status_data = status_response.json()
            
            status = status_data.get('status', 'unknown')
            print(f"  Attempt {attempt + 1}: Status = {status}")
            
            if status in ['completed', 'failed', 'error']:
                print(f"\n3. Final Result:")
                print(json.dumps(status_data, indent=2))
                
                # Check for citations
                citations = status_data.get('result', {}).get('citations', [])
                print(f"\n✓ Found {len(citations)} citations")
                
                if len(citations) > 0:
                    print(f"\nFirst citation: {citations[0].get('citation', 'N/A')}")
                
                break
    else:
        # Immediate result
        citations = result.get('citations', [])
        print(f"\n✓ Found {len(citations)} citations (immediate result)")
        
        if len(citations) > 0:
            print(f"\nFirst citation: {citations[0].get('citation', 'N/A')}")
    
    print("\n" + "="*60)
    print("Test completed successfully!")
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
