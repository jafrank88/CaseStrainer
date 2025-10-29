#!/usr/bin/env python
"""Test script to check if progress updates are working with a small file."""

import sys
import os
import requests
import json
import time

def test_progress_updates():
    """Test if progress updates are working with a small file upload."""
    
    print("Testing progress updates with small file upload...")
    
    # Test file path - using small text file
    file_path = "d:\\dev\\casestrainer\\test_small.txt"
    
    # Submit job
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    files = {'file': open(file_path, 'rb')}
    data = {
        "enable_verification": True,
        "client_request_id": f"test_small_{int(time.time())}"
    }
    
    print(f"Submitting file upload with ID: {data['client_request_id']}")
    
    try:
        response = requests.post(url, files=files, data=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        print(f"Response from analyze endpoint: {result}")
        
        task_id = result.get('task_id')
        print(f"Job submitted with task_id: {task_id}")
        
        if not task_id:
            print("ERROR: No task_id in response!")
            print("This might mean the file was processed synchronously")
            return
        
        # Poll for progress
        status_url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"
        
        last_progress = 0
        progress_updates = []
        
        for i in range(60):  # Check for up to 1 minute
            try:
                status_response = requests.get(status_url, timeout=5)
                status_response.raise_for_status()
                status = status_response.json()
                
                # Check verification status for progress
                if 'verification_status' in status:
                    ver_status = status['verification_status']
                    if isinstance(ver_status, dict):
                        progress = ver_status.get('progress_percent', 0)
                        message = ver_status.get('current_message', '')
                        
                        if progress != last_progress:
                            progress_updates.append((progress, message))
                            print(f"Progress update: {progress}% - {message}")
                            last_progress = progress
                
                if status.get('status') == 'completed':
                    print("Job completed!")
                    break
                    
                time.sleep(1)
                
            except Exception as e:
                print(f"Error checking status: {e}")
                time.sleep(1)
        
        # Summary
        print("\nProgress Update Summary:")
        print(f"Total progress updates: {len(progress_updates)}")
        for progress, message in progress_updates:
            print(f"  {progress}% - {message}")
            
        if len(progress_updates) <= 3:
            print("\n⚠️  WARNING: Progress bar appears stuck (only 3 or fewer updates)")
            print("Expected: Multiple updates from 0% to 100%")
        else:
            print("\n✅ Progress updates working correctly!")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close file
        if 'files' in locals():
            files['file'].close()

if __name__ == "__main__":
    test_progress_updates()
