#!/usr/bin/env python3
"""
Test task status endpoint directly
"""

import requests
import json

def test_task_status_direct():
    """Test the task status endpoint with a fresh task"""
    
    print("TESTING TASK STATUS ENDPOINT DIRECTLY")
    print("=" * 45)
    
    base_url = "https://wolf.law.uw.edu/casestrainer"
    
    # First, submit a simple text to get a task
    print("\n1. Submitting text for async processing...")
    test_text = "Test citation: 123 U.S. 456 (2023)."
    
    response = requests.post(
        f"{base_url}/api/analyze",
        data={'text': test_text, 'type': 'text'},
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"ERROR: Failed to submit - {response.status_code}")
        print(response.text)
        return
    
    result = response.json()
    
    # Check if we got a task_id (async) or immediate results
    if 'task_id' in result:
        task_id = result['task_id']
        print(f"Got async task: {task_id}")
    else:
        print("Got immediate response, forcing async with larger text...")
        # Try with larger text to force async
        large_text = test_text * 1000
        response = requests.post(
            f"{base_url}/api/analyze",
            data={'text': large_text, 'type': 'text'},
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"ERROR: Failed to submit large text - {response.status_code}")
            return
        
        result = response.json()
        if 'task_id' not in result:
            print("ERROR: Still got immediate response")
            return
        
        task_id = result['task_id']
        print(f"Got async task with large text: {task_id}")
    
    # Now test the task status endpoint
    print(f"\n2. Testing task status endpoint for {task_id}...")
    
    status_url = f"{base_url}/api/task_status/{task_id}"
    print(f"URL: {status_url}")
    
    try:
        status_response = requests.get(status_url, timeout=10)
        print(f"Status response code: {status_response.status_code}")
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"Status response: {json.dumps(status_data, indent=2)}")
        else:
            print(f"Error response: {status_response.text}")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Also test via the backend container directly
    print(f"\n3. Testing backend container directly...")
    try:
        backend_status = requests.get(
            f"http://localhost:5000/api/task_status/{task_id}",
            timeout=10
        )
        print(f"Backend status code: {backend_status.status_code}")
        
        if backend_status.status_code == 200:
            print(f"Backend response: {backend_status.json()}")
        else:
            print(f"Backend error: {backend_status.text}")
            
    except Exception as e:
        print(f"Backend error: {e}")

if __name__ == "__main__":
    test_task_status_direct()
