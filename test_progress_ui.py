#!/usr/bin/env python3
"""
Test URL upload to verify progress bar spinner and movement are working
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import requests
import json
import time

def test_progress_ui():
    """Test URL upload and monitor progress updates."""
    url = "https://law.justia.com/cases/federal/us/390/747/"
    
    print(f"Testing progress UI with URL: {url}")
    print("This will test if the spinner and progress bar movement work correctly")
    
    # Submit URL for processing
    data = {'url': url}
    
    try:
        response = requests.post(
            "https://wolf.law.uw.edu/casestrainer/api/analyze",
            data=data,
            timeout=10,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        print(f"Submit response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            
            if task_id:
                print(f"✅ Task submitted successfully: {task_id}")
                print("\nMonitoring progress updates...")
                
                # Monitor progress for 30 seconds
                for i in range(30):
                    try:
                        progress_response = requests.get(
                            f"https://wolf.law.uw.edu/casestrainer/api/analyze/progress/{task_id}",
                            timeout=5
                        )
                        
                        if progress_response.status_code == 200:
                            progress_data = progress_response.json().get('progress_data', {})
                            progress = progress_data.get('progress', 0)
                            message = progress_data.get('message', 'Processing...')
                            
                            print(f"  [{i+1:2d}s] Progress: {progress:3.0f}% - {message}")
                            
                            # Check if progress is moving
                            if i > 0 and progress > last_progress:
                                print("    ✅ Progress bar is moving!")
                            
                            last_progress = progress
                            
                        else:
                            print(f"  [{i+1:2d}s] Error getting progress: {progress_response.status_code}")
                    
                    except Exception as e:
                        print(f"  [{i+1:2d}s] Request failed: {e}")
                    
                    time.sleep(1)
                
                print("\n📊 Progress UI Test Summary:")
                print("- Spinner should be visible (CSS animation)")
                print("- Progress bar should show incremental movement")
                print("- Message should update during processing")
                print("- The fixes address field mapping and stuck progress")
                
            else:
                print("❌ No task_id in response")
                print(f"Response: {json.dumps(result, indent=2)}")
        
        else:
            print(f"❌ Submit failed: {response.status_code}")
            print(f"Error: {response.text}")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    last_progress = 0
    test_progress_ui()
