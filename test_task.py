#!/usr/bin/env python3
"""
Test script to submit a task and check results
"""

import requests
import time
import json

def test_async_task():
    """Test async task processing"""
    
    # Test data
    test_data = {
        "type": "text",
        "text": "The court in Smith v. Jones, 123 U.S. 456 (2020) held that the defendant was liable."
    }
    
    print("Submitting async task...")
    
    # Submit task
    response = requests.post('http://localhost:5000/casestrainer/api/analyze', 
                           json=test_data)
    
    if response.status_code != 200:
        print(f"Failed to submit task: {response.status_code}")
        print(response.text)
        return
    
    data = response.json()
    print(f"Task submitted: {data}")
    
    if 'task_id' not in data:
        print("No task_id returned")
        return
    
    task_id = data['task_id']
    print(f"Task ID: {task_id}")
    
    # Poll for results
    print("\nPolling for results...")
    for i in range(10):
        time.sleep(2)
        
        status_response = requests.get(f'http://localhost:5000/casestrainer/api/task_status/{task_id}')
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            status = status_data.get('status', 'unknown')
            
            print(f"Attempt {i+1}: Status = {status}")
            
            if status == 'completed':
                print("✅ Task completed!")
                print(f"Citations: {status_data.get('citations', [])}")
                return
            elif status == 'failed':
                print(f"❌ Task failed: {status_data.get('message', 'Unknown error')}")
                return
        else:
            print(f"Failed to get status: {status_response.status_code}")
    
    print("❌ Task did not complete within expected time")

if __name__ == "__main__":
    test_async_task() 