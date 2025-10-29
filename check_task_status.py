#!/usr/bin/env python3
"""
Check the status of the async task
"""

import requests
import json

def check_task_status():
    task_id = "773de729-1d50-45c8-b973-9f88922e4aad"
    
    try:
        response = requests.get(f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}")
        
        if response.status_code == 200:
            result = response.json()
            print(json.dumps(result, indent=2))
        else:
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_task_status()
