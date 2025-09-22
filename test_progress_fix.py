#!/usr/bin/env python3
"""
Test the progress endpoint to see if the NaN% issue is fixed.
"""

import requests
import json
import time

def test_progress_fix():
    """Test the progress endpoint to see if elapsed time is working."""
    
    print("🔍 TESTING PROGRESS FIX")
    print("=" * 60)
    
    try:
        # Test the processing progress endpoint
        response = requests.get(
            "http://localhost:5000/casestrainer/api/processing_progress",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Progress endpoint response:")
            print(f"   Status: {data.get('status')}")
            print(f"   Current step: {data.get('current_step')}")
            print(f"   Progress: {data.get('progress')}%")
            print(f"   Total progress: {data.get('total_progress')}%")
            print(f"   Message: {data.get('message')}")
            print()
            
            # Check the key fields
            print("🔧 Key fields for Vue.js:")
            print(f"   elapsed_time (snake_case): {data.get('elapsed_time')}")
            print(f"   elapsedTime (camelCase): {data.get('elapsedTime')}")
            print(f"   startTime: {data.get('startTime')}")
            print(f"   estimatedTotalTime: {data.get('estimatedTotalTime')}")
            print(f"   isActive: {data.get('isActive')}")
            print()
            
            # Check if values are valid
            elapsed_time = data.get('elapsedTime')
            estimated_total = data.get('estimatedTotalTime')
            
            if elapsed_time is not None and estimated_total and estimated_total > 0:
                progress_calc = (elapsed_time / estimated_total) * 100
                print(f"📊 Calculated progress: {progress_calc:.1f}%")
                
                if progress_calc > 0:
                    print("✅ Progress calculation should work (not NaN%)")
                else:
                    print("⚠️  Progress is 0% - might show as 0s elapsed")
            else:
                print("❌ Missing required fields for progress calculation")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_progress_fix()
