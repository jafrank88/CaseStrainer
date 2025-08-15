#!/usr/bin/env python3
"""
Test script to debug file upload and URL processing issues.
This will help identify where the processing pipeline is failing.
"""

import requests
import json
import time
import os

def test_file_upload():
    """Test file upload processing."""
    print("=== Testing File Upload ===")
    
    # Test with a simple text file
    test_file_path = "test_files/test.txt"
    if not os.path.exists(test_file_path):
        print(f"❌ Test file not found: {test_file_path}")
        return
    
    print(f"📁 Testing with file: {test_file_path}")
    
    try:
        with open(test_file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                'http://localhost:5000/casestrainer/api/analyze',
                files=files,
                timeout=30
            )
        
        print(f"📤 Response Status: {response.status_code}")
        print(f"📤 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success Response: {json.dumps(result, indent=2)}")
            
            # Check if we got a task_id for async processing
            if 'task_id' in result:
                print(f"🔄 Got task_id: {result['task_id']}")
                print("⏳ This indicates async processing - checking task status...")
                
                # Wait a bit and check task status
                time.sleep(2)
                status_response = requests.get(
                    f'http://localhost:5000/casestrainer/api/analyze/progress/{result["task_id"]}',
                    timeout=10
                )
                
                if status_response.status_code == 200:
                    status_result = status_response.json()
                    print(f"📊 Task Status: {json.dumps(status_result, indent=2)}")
                else:
                    print(f"❌ Failed to get task status: {status_response.status_code}")
            else:
                print("✅ Got immediate results (no task_id)")
                
        else:
            print(f"❌ Error Response: {response.text}")
            
    except Exception as e:
        print(f"❌ File upload test failed: {str(e)}")

def test_url_processing():
    """Test URL processing."""
    print("\n=== Testing URL Processing ===")
    
    # Test with a simple URL that should work
    test_url = "https://www.courts.wa.gov/opinions/pdf/853996.pdf"
    print(f"🌐 Testing with URL: {test_url}")
    
    try:
        data = {
            'type': 'url',
            'url': test_url
        }
        
        response = requests.post(
            'http://localhost:5000/casestrainer/api/analyze',
            json=data,
            timeout=30
        )
        
        print(f"📤 Response Status: {response.status_code}")
        print(f"📤 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success Response: {json.dumps(result, indent=2)}")
            
            # Check if we got a task_id for async processing
            if 'task_id' in result:
                print(f"🔄 Got task_id: {result['task_id']}")
                print("⏳ This indicates async processing - checking task status...")
                
                # Wait a bit and check task status
                time.sleep(2)
                status_response = requests.get(
                    f'http://localhost:5000/casestrainer/api/analyze/progress/{result["task_id"]}',
                    timeout=10
                )
                
                if status_response.status_code == 200:
                    status_result = status_response.json()
                    print(f"📊 Task Status: {json.dumps(status_result, indent=2)}")
                else:
                    print(f"❌ Failed to get task status: {status_response.status_code}")
            else:
                print("✅ Got immediate results (no task_id)")
                
        else:
            print(f"❌ Error Response: {response.text}")
            
    except Exception as e:
        print(f"❌ URL processing test failed: {str(e)}")

def test_text_processing():
    """Test text processing for comparison."""
    print("\n=== Testing Text Processing (Control) ===")
    
    test_text = "This is a test case: In re Marriage of Chandola, 180 Wn.2d 632, 327 P.3d 644 (2014)."
    print(f"📝 Testing with text: {test_text}")
    
    try:
        data = {
            'type': 'text',
            'text': test_text
        }
        
        response = requests.post(
            'http://localhost:5000/casestrainer/api/analyze',
            json=data,
            timeout=30
        )
        
        print(f"📤 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Error Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Text processing test failed: {str(e)}")

if __name__ == "__main__":
    print("🔍 CaseStrainer File/URL Processing Debug Test")
    print("=" * 50)
    
    # Test all three input types
    test_file_upload()
    test_url_processing()
    test_text_processing()
    
    print("\n" + "=" * 50)
    print("🏁 Testing complete. Check backend logs for detailed processing information.")
