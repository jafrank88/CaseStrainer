#!/usr/bin/env python3
"""
Test the actual CaseStrainer API endpoint with the problematic PDF URL
"""

import requests
import json
import time

def test_api_url():
    """Test the CaseStrainer API with the URL that's not working"""
    
    # The URL that's not finding citations
    test_url = "https://www.courts.wa.gov/opinions/pdf/400611_pub.pdf"
    
    # CaseStrainer API endpoint (based on memory about unified endpoint)
    api_url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    print(f"Testing CaseStrainer API with URL: {test_url}")
    print(f"API endpoint: {api_url}")
    print("=" * 80)
    
    # Prepare the request data
    data = {
        'url': test_url,
        'type': 'url'
    }
    
    try:
        print("Submitting URL for analysis...")
        response = requests.post(api_url, data=data, timeout=60)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"Full response: {json.dumps(result, indent=2)}")
            
            # Check for task_id in different locations
            task_id = None
            if 'task_id' in result:
                task_id = result['task_id']
            elif 'result' in result and 'job_id' in result['result']['metadata']:
                task_id = result['result']['metadata']['job_id']
            elif 'request_id' in result:
                task_id = result['request_id']
            
            if task_id:
                print(f"✓ Task submitted successfully")
                print(f"Task ID: {task_id}")
                
                # Poll for results
                status_url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"
                
                print(f"\nPolling for results at: {status_url}")
                
                max_attempts = 30  # 5 minutes max
                attempt = 0
                
                while attempt < max_attempts:
                    attempt += 1
                    print(f"Attempt {attempt}/{max_attempts}...")
                    
                    try:
                        status_response = requests.get(status_url, timeout=30)
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            
                            print(f"Status: {status_data.get('status', 'unknown')}")
                            
                            if status_data.get('status') == 'completed':
                                print("✓ Task completed!")
                                
                                citations = status_data.get('result', {}).get('citations', [])
                                print(f"Citations found: {len(citations)}")
                                
                                if citations:
                                    print("\nFirst 10 citations:")
                                    for i, citation in enumerate(citations[:10]):
                                        print(f"  {i+1}. {citation.get('full_citation', 'N/A')}")
                                        if citation.get('extracted_case_name'):
                                            print(f"      Case: {citation['extracted_case_name']}")
                                else:
                                    print("⚠️  No citations found by CaseStrainer API")
                                    
                                    # Show any errors and full result for debugging
                                    if status_data.get('result', {}).get('errors'):
                                        print(f"Errors: {status_data['result']['errors']}")
                                    print(f"\nFull task result: {json.dumps(status_data, indent=2)[:1000]}...")
                                
                                return
                                
                            elif status_data.get('status') == 'failed':
                                print("✗ Task failed")
                                print(f"Error: {status_data.get('error', 'Unknown error')}")
                                return
                                
                            elif status_data.get('status') in ['pending', 'processing']:
                                print("Task still processing...")
                                time.sleep(10)  # Wait 10 seconds
                            else:
                                print(f"Unknown status: {status_data.get('status')}")
                                time.sleep(10)
                        else:
                            print(f"Status check failed: {status_response.status_code}")
                            print(f"Response: {status_response.text[:200]}")
                            time.sleep(10)
                            
                    except Exception as e:
                        print(f"Status check error: {e}")
                        time.sleep(10)
                
                print("⚠️  Timeout waiting for results")
                
            else:
                print("✓ Direct result received")
                citations = result.get('citations', [])
                print(f"Citations found: {len(citations)}")
                
                if citations:
                    print("\nFirst 10 citations:")
                    for i, citation in enumerate(citations[:10]):
                        print(f"  {i+1}. {citation.get('full_citation', 'N/A')}")
                else:
                    print("⚠️  No citations found")
        else:
            print(f"✗ API request failed: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"✗ Request failed: {e}")

if __name__ == "__main__":
    test_api_url()
