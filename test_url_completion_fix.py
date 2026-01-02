#!/usr/bin/env python3
"""
Test URL completion fix with the original problematic URL
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import requests
import json
import time

def test_url_completion_fix():
    """Test URL completion with the fix for empty citation tasks."""
    url = "https://supreme.justia.com/cases/federal/us/390/747/"
    
    print(f"Testing URL completion fix: {url}")
    print("This should now complete instead of getting stuck at 70%")
    
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
            
            # Check if this is a synchronous completion
            if result.get('status') == 'completed':
                print("\n🎉 Synchronous processing completed immediately!")
                citations = result.get('result', {}).get('citations', [])
                print(f"   Citations found: {len(citations)}")
                print("   ✅ URL processing completed successfully")
                return True
            
            task_id = result.get('task_id')
            
            if task_id:
                print(f"✅ Task submitted asynchronously: {task_id}")
                print("\nMonitoring for completion (should not get stuck at 70%)...")
                
                last_progress = 0
                completion_found = False
                
                # Monitor progress for 90 seconds (longer for URLs)
                for i in range(90):
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
                            elif progress != last_progress:
                                print(f"  [{i+1:2d}s] ✅ Progress: {progress:3.0f}% - {message}")
                            elif i % 15 == 0:  # Show every 15th stuck message
                                print(f"  [{i+1:2d}s] ⏸️  Progress: {progress:3.0f}% - {message}")
                            
                            last_progress = progress
                            
                        else:
                            print(f"  [{i+1:2d}s] Error getting progress: {progress_response.status_code}")
                    
                    except Exception as e:
                        print(f"  [{i+1:2d}s] Request failed: {e}")
                    
                    time.sleep(1)
                
                if completion_found:
                    print("\n✅ SUCCESS: URL task completed properly!")
                    print("   The empty citation completion fix is working for async tasks")
                    return True
                else:
                    print(f"\n⚠️  URL task did not complete within 90 seconds (final: {last_progress}%)")
                    
                    # Check final task status
                    try:
                        status_response = requests.get(
                            f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}",
                            timeout=5
                        )
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            print(f"📋 Final Task Status:")
                            print(f"   Status: {status_data.get('status')}")
                            print(f"   Citations: {len(status_data.get('citations', []))}")
                            print(f"   Message: {status_data.get('message')}")
                            
                            # If there are 0 citations, the fix should have worked
                            if len(status_data.get('citations', [])) == 0:
                                print("   ✅ Fix appears to be working but task may still be completing")
                            else:
                                print("   ❌ Task may be stuck processing citations")
                                
                    except Exception as e:
                        print(f"Could not check final status: {e}")
                    
                    return False
        
        else:
            print(f"❌ Submit failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_url_completion_fix()
    if success:
        print("\n✅ SUCCESS: The URL completion fix is working correctly")
    else:
        print("\n⚠️  ISSUE: URL tasks may still need investigation")
