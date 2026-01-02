#!/usr/bin/env python3
"""Check the status of the simple async task"""

import requests
import json

task_id = "6f9f9e67-bf5c-4b95-bb60-a6cb7bae1dda"

def check_status():
    """Check the status of the task"""
    
    url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"
    
    print(f"Checking status for task: {task_id}")
    
    try:
        response = requests.get(url, timeout=10, verify=False)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Extract key info
            status = result.get('status', 'unknown')
            progress = result.get('progress_percent', 0)
            message = result.get('current_message', '')
            
            print(f"Status: {status}")
            print(f"Progress: {progress}%")
            print(f"Message: {message}")
            
            if 'result' in result:
                citations = result['result'].get('citations', [])
                clusters = result['result'].get('clusters', [])
                print(f"Citations: {len(citations)}")
                print(f"Clusters: {len(clusters)}")
                
                if citations:
                    print(f"\nFirst citation: {citations[0].get('citation', 'N/A')}")
                    print(f"Case: {citations[0].get('case_name', 'N/A')}")
                    print(f"Verified: {citations[0].get('verified', False)}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    check_status()
