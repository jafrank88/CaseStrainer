#!/usr/bin/env python3
"""
Test progress integration to see if verification manager updates are reaching the frontend
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import requests
import json
import time

def test_progress_endpoint():
    """Test the progress endpoint directly."""
    # Use the task ID from our previous test
    task_id = "e2fb7109-ac40-4ec0-81dd-10cc058e8c89"
    
    print(f"Testing progress endpoint for task: {task_id}")
    
    for i in range(10):
        try:
            response = requests.get(
                f"https://wolf.law.uw.edu/casestrainer/api/analyze/progress/{task_id}",
                timeout=5
            )
            
            print(f"Attempt {i+1}: Status {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                progress_data = data.get('progress_data', {})
                print(f"  Progress data: {json.dumps(progress_data, indent=2)}")
                
                # Check if there are actual progress updates
                if progress_data.get('overall_progress', 0) > 0:
                    print("  ✅ Progress is being tracked!")
                    break
                else:
                    print("  ⚠️  No progress updates found")
            else:
                print(f"  Error: {response.text}")
                
        except Exception as e:
            print(f"  Request failed: {e}")
        
        time.sleep(2)

def test_verification_status():
    """Test verification status directly to see if it has progress."""
    task_id = "e2fb7109-ac40-4ec0-81dd-10cc058e8c89"
    
    print(f"\nTesting verification status for task: {task_id}")
    
    try:
        response = requests.get(
            f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Task status: {json.dumps(data, indent=2)}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_progress_endpoint()
    test_verification_status()
