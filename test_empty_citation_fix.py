#!/usr/bin/env python3
"""
Test the fix for empty citation completion
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import requests
import json
import time

def test_empty_citation_fix():
    """Test that tasks with no citations complete properly."""
    url = "https://supreme.justia.com/cases/federal/us/390/747/"
    
    print(f"Testing empty citation completion fix with URL: {url}")
    print("This should now complete properly instead of getting stuck at 70%")
    
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
                print("\nMonitoring progress for completion...")
                
                last_progress = 0
                completion_found = False
                
                # Monitor progress for 60 seconds
                for i in range(60):
                    try:
                        progress_response = requests.get(
                            f"https://wolf.law.uw.edu/casestrainer/api/analyze/progress/{task_id}",
                            timeout=5
                        )
                        
                        if progress_response.status_code == 200:
                            progress_data = progress_response.json().get('progress_data', {})
                            progress = progress_data.get('progress', 0)
                            message = progress_data.get('message', 'Processing...')
                            
                            # Check for completion
                            if progress >= 100:
                                print(f"  [{i+1:2d}s] 🎉 COMPLETED: {progress}% - {message}")
                                completion_found = True
                                break
                            elif progress > last_progress:
                                print(f"  [{i+1:2d}s] ✅ Progress: {progress:3.0f}% - {message}")
                            elif i % 10 == 0:  # Show every 10th stuck message
                                print(f"  [{i+1:2d}s] ⏸️  Progress: {progress:3.0f}% - {message}")
                            
                            last_progress = progress
                            
                        else:
                            print(f"  [{i+1:2d}s] Error getting progress: {progress_response.status_code}")
                    
                    except Exception as e:
                        print(f"  [{i+1:2d}s] Request failed: {e}")
                    
                    time.sleep(1)
                
                if completion_found:
                    print("\n✅ SUCCESS: Task completed properly!")
                    print("   The empty citation completion fix is working")
                else:
                    print(f"\n⚠️  Task did not complete within 60 seconds (final: {last_progress}%)")
                    print("   May need further investigation")
                
                # Check final task status
                try:
                    status_response = requests.get(
                        f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}",
                        timeout=5
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        print(f"\n📋 Final Task Status:")
                        print(f"   Status: {status_data.get('status')}")
                        print(f"   Citations: {len(status_data.get('citations', []))}")
                        print(f"   Message: {status_data.get('message')}")
                        
                except Exception as e:
                    print(f"Could not check final status: {e}")
        
        else:
            print(f"❌ Submit failed: {response.status_code}")
            print(f"Error: {response.text}")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_empty_citation_fix()
