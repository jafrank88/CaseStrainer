#!/usr/bin/env python3
"""Test URL processing after fixing worker issues"""

import requests
import json
import time

def test_url_processing():
    """Test URL processing with async mode"""
    
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    # Test data
    data = {
        'type': 'url',
        'url': 'https://www.courts.wa.gov/opinions/pdf/863215.pdf',
        'force_mode': 'async',
        'enable_verification': 'true'
    }
    
    print("Testing URL processing...")
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
                for i in range(60):  # Max 5 minutes
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
                            break
                        elif status == 'failed':
                            print(f"\n❌ Task failed: {status_data.get('message', 'Unknown error')}")
                            break
                    else:
                        print(f"Status check failed: {status_response.status_code}")
                else:
                    print("\n⏰ Task timed out after 5 minutes")
        else:
            print(f"Error: {response.status_code}")
            print(response.text[:1000])
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_url_processing()
