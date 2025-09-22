#!/usr/bin/env python3
"""
Test the progress endpoints to see if they're working.
"""

import requests
import json
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_progress_endpoints():
    """Test various progress endpoints."""
    
    base_url = "http://localhost:5000/casestrainer/api"
    
    print("🔍 TESTING PROGRESS ENDPOINTS")
    print("=" * 60)
    
    # Test 1: Check if processing_progress endpoint works
    print("\n1️⃣ Testing /processing_progress endpoint...")
    try:
        response = requests.get(f"{base_url}/processing_progress", timeout=5, verify=False)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 2: Start a simple analysis and check progress
    print("\n2️⃣ Testing analysis with progress tracking...")
    try:
        # Start analysis
        analysis_data = {
            "type": "text",
            "text": "In Smith v. Jones, 123 U.S. 456 (2020), the court held..."
        }
        
        print("   Starting analysis...")
        response = requests.post(
            f"{base_url}/analyze",
            json=analysis_data,
            headers={"Content-Type": "application/json"},
            timeout=30,
            verify=False
        )
        
        print(f"   Analysis Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Citations found: {len(result.get('citations', []))}")
            
            # Check if there's a task_id or request_id for progress tracking
            task_id = result.get('task_id') or result.get('request_id')
            if task_id:
                print(f"   Task ID: {task_id}")
                
                # Try to get progress for this task
                print("   Checking progress...")
                progress_response = requests.get(f"{base_url}/progress/{task_id}", timeout=5, verify=False)
                print(f"   Progress Status: {progress_response.status_code}")
                if progress_response.status_code == 200:
                    progress_data = progress_response.json()
                    print(f"   Progress Data: {json.dumps(progress_data, indent=2)}")
            else:
                print("   No task_id found in response")
        else:
            print(f"   Analysis Error: {response.text}")
            
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 3: Check if there are any active progress entries
    print("\n3️⃣ Testing progress data availability...")
    try:
        # Try different progress endpoints
        endpoints = [
            "/processing_progress",
            "/progress/test-123",
            "/analyze/progress/test-123"
        ]
        
        for endpoint in endpoints:
            print(f"   Testing {endpoint}...")
            response = requests.get(f"{base_url}{endpoint}", timeout=5, verify=False)
            print(f"     Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"     Has data: {bool(data)}")
            
    except Exception as e:
        print(f"   Exception: {e}")

if __name__ == "__main__":
    test_progress_endpoints()
