#!/usr/bin/env python3
"""Test URL processing with harmonized pipeline"""

import requests
import json
import time

def test_url_harmonized():
    """Test URL processing with unified text extraction"""
    
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    data = {
        'type': 'url',
        'url': 'https://www.courts.wa.gov/opinions/pdf/863215.pdf',
        'force_mode': 'async',
        'enable_verification': 'false'  # Disable verification to avoid rate limiting
    }
    
    print(f"Testing URL with harmonized pipeline...")
    print(f"URL: {data['url']}")
    print(f"Force mode: {data['force_mode']}")
    print(f"Verification: {data['enable_verification']}")
    
    try:
        # Submit the request
        print("\nSubmitting request...")
        response = requests.post(url, json=data, timeout=30, verify=False)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('request_id')
            print(f"Task ID: {task_id}")
            print(f"Initial status: {result.get('status')}")
            print(f"Message: {result.get('message')}")
            
            # Poll for completion
            if task_id:
                print("\nPolling for task completion...")
                for i in range(36):  # Max 3 minutes
                    time.sleep(5)
                    status_response = requests.get(
                        f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}",
                        timeout=10,
                        verify=False
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        progress = status_data.get('progress_percent', 0)
                        message = status_data.get('current_message', '')
                        status = status_data.get('status', '')
                        
                        print(f"Attempt {i+1}: Progress={progress}%, Status={status}, Message={message}")
                        
                        if status == 'completed':
                            print("\n✅ Task completed successfully!")
                            citations = status_data.get('citations', [])
                            clusters = status_data.get('clusters', [])
                            print(f"Found {len(citations)} citations and {len(clusters)} clusters")
                            
                            # Show citations
                            if citations:
                                print("\nFirst 5 citations:")
                                for i, citation in enumerate(citations[:5], 1):
                                    print(f"  {i}. {citation.get('citation', 'N/A')}")
                            
                            return True
                        elif status == 'failed':
                            print(f"\n❌ Task failed: {status_data.get('message', 'Unknown error')}")
                            return False
                    else:
                        print(f"Status check failed: {status_response.status_code}")
                else:
                    print("\n⏰ Task timed out after 3 minutes")
                    return False
        else:
            print(f"Error: {response.status_code}")
            print(response.text[:1000])
            return False
            
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_url_harmonized()
    if success:
        print("\n✅ SUCCESS: Harmonized pipeline works for URL processing!")
    else:
        print("\n❌ FAILED: Harmonized pipeline still has issues")
