#!/usr/bin/env python3
"""
Test the improved progress tracking with verification phase updates
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import requests
import json
import time

def test_full_progress():
    """Test URL upload with improved progress tracking."""
    url = "https://law.justia.com/cases/federal/us/390/747/"
    
    print(f"Testing improved progress tracking with URL: {url}")
    print("This should now show progress beyond 12% during verification")
    
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
                print("\nMonitoring improved progress updates...")
                
                last_progress = 0
                progress_stuck_count = 0
                
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
                            
                            # Check for progress improvements
                            if progress > last_progress:
                                print(f"  [{i+1:2d}s] ✅ Progress: {progress:3.0f}% - {message}")
                                progress_stuck_count = 0
                            elif progress == last_progress:
                                progress_stuck_count += 1
                                if progress_stuck_count <= 5:  # Only show first few stuck messages
                                    print(f"  [{i+1:2d}s] ⏸️  Progress: {progress:3.0f}% - {message}")
                            else:
                                print(f"  [{i+1:2d}s] ⬇️  Progress: {progress:3.0f}% - {message}")
                            
                            last_progress = progress
                            
                            # Check if completed
                            if progress >= 100:
                                print(f"\n🎉 Processing completed at {i+1} seconds!")
                                break
                            
                        else:
                            print(f"  [{i+1:2d}s] Error getting progress: {progress_response.status_code}")
                    
                    except Exception as e:
                        print(f"  [{i+1:2d}s] Request failed: {e}")
                    
                    time.sleep(1)
                
                print(f"\n📊 Final Progress: {last_progress}%")
                
                if last_progress > 12:
                    print("✅ SUCCESS: Progress moved beyond 12%!")
                    print("   The verification phase now provides progress updates")
                else:
                    print("⚠️  Progress still stuck at 12% - may need further investigation")
                
                print("\n🔧 Improvements Made:")
                print("   - Added progress_callback parameter to verify_citations_enhanced()")
                print("   - Added progress updates during verification phases:")
                print("     * 15%: Starting citation verification")
                print("     * 20%: Running enhanced verification")
                print("     * 25%: Running fallback verification")
                print("     * 80%: Processing verification results")
                print("     * 90%: Assessing result quality")
                print("     * 95%: Finalizing verification results")
                print("     * 100%: Processing completed successfully")
        
        else:
            print(f"❌ Submit failed: {response.status_code}")
            print(f"Error: {response.text}")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_full_progress()
