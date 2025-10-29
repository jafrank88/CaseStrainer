#!/usr/bin/env python
"""Test script to check if progress updates are working in async processing."""

import sys
import os
import requests
import json
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_progress_updates():
    """Test if progress updates are working."""
    
    print("Testing progress updates...")
    
    # Test text - longer to force async processing
    test_text = """
    Smith v. Jones, 123 U.S. 456 (2020). This is a test citation that should be long enough to trigger async processing.
    Another case: Doe v. Roe, 456 F.3d 789 (2021). We need to make this text longer to ensure it goes through the async pipeline.
    Additional text to make sure the processing is async: Lorem ipsum dolor sit amet, consectetur adipiscing elit.
    Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud
    exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit
    in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident,
    sunt in culpa qui officia deserunt mollit anim id est laborum. More text to ensure async processing: 
    Additional case: Brown v. Board of Education, 347 U.S. 483 (1954). This is a famous case.
    Another citation: Miranda v. Arizona, 384 U.S. 436 (1966). Even more text to ensure async processing.
    """
    
    # Submit job
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    data = {
        "text": test_text,
        "enable_verification": True,
        "client_request_id": f"test_progress_{int(time.time())}"
    }
    
    print(f"Submitting job with ID: {data['client_request_id']}")
    
    try:
        response = requests.post(url, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        print(f"Response from analyze endpoint: {result}")
        
        task_id = result.get('task_id')
        print(f"Job submitted with task_id: {task_id}")
        
        if not task_id:
            print("ERROR: No task_id in response!")
            return
        
        # Poll for progress
        status_url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"
        
        last_progress = 0
        progress_updates = []
        
        for i in range(60):  # Check for up to 60 seconds
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

if __name__ == "__main__":
    test_progress_updates()
