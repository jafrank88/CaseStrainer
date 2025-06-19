#!/usr/bin/env python3
"""
Simple test script to verify the worker is running and can process tasks.
"""

import requests
import time
import json

def test_worker():
    """Test the worker by sending a simple text task."""
    
    # Test health endpoint first
    print("Testing health endpoint...")
    try:
        response = requests.get('http://localhost:5000/health')
        if response.status_code == 200:
            health_data = response.json()
            print(f"Health check passed: {health_data}")
            print(f"Worker status: {health_data.get('worker_status')}")
            print(f"Queue size: {health_data.get('queue_size')}")
        else:
            print(f"Health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"Health check error: {e}")
        return
    
    # Test text analysis
    print("\nTesting text analysis...")
    test_data = {
        'type': 'text',
        'text': 'The court in 534 F.3d 1290 held that the plaintiff failed to state a claim.'
    }
    
    try:
        response = requests.post('http://localhost:5000/api/analyze', json=test_data)
        if response.status_code == 200:
            result = response.json()
            print(f"Analysis started: {result}")
            
            task_id = result.get('task_id')
            if task_id:
                print(f"Task ID: {task_id}")
                
                # Poll for completion
                for i in range(30):  # Wait up to 30 seconds
                    time.sleep(2)
                    status_response = requests.get(f'http://localhost:5000/api/task_status/{task_id}')
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        print(f"Status: {status_data.get('status')} - Progress: {status_data.get('progress', 0)}%")
                        
                        if status_data.get('status') == 'completed':
                            print("Task completed successfully!")
                            print(f"Citations found: {len(status_data.get('citations', []))}")
                            return
                        elif status_data.get('status') == 'failed':
                            print(f"Task failed: {status_data.get('error')}")
                            return
                    else:
                        print(f"Status check failed: {status_response.status_code}")
                
                print("Task timed out")
            else:
                print("No task ID returned")
        else:
            print(f"Analysis failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Analysis error: {e}")

if __name__ == '__main__':
    test_worker() 