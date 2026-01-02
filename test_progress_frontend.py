#!/usr/bin/env python3
"""
Test to see if the progress data includes the isActive field
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import requests
import json

def test_progress_fields():
    """Test what fields are in the progress response."""
    task_id = "e2fb7109-ac40-4ec0-81dd-10cc058e8c89"
    
    print(f"Testing progress fields for task: {task_id}")
    
    try:
        response = requests.get(
            f"https://wolf.law.uw.edu/casestrainer/api/analyze/progress/{task_id}",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            progress_data = data.get('progress_data', {})
            
            print("All progress fields:")
            for key, value in progress_data.items():
                print(f"  {key}: {value}")
            
            # Check for specific fields the frontend needs
            print("\nFrontend field check:")
            print(f"  overall_progress: {progress_data.get('overall_progress', 'MISSING')}")
            print(f"  total_progress: {progress_data.get('total_progress', 'MISSING')}")
            print(f"  progress: {progress_data.get('progress', 'MISSING')}")
            print(f"  current_message: {progress_data.get('current_message', 'MISSING')}")
            print(f"  message: {progress_data.get('message', 'MISSING')}")
            print(f"  status: {progress_data.get('status', 'MISSING')}")
            
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_progress_fields()
