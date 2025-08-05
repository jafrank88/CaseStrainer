#!/usr/bin/env python3
"""
Test script to verify file upload functionality
"""

import requests
import json
import time
import sys
from pathlib import Path

def test_health_endpoint():
    """Test if the health endpoint is accessible"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get('https://wolf.law.uw.edu/casestrainer/api/health', timeout=10)
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.text}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_file_upload():
    """Test file upload functionality"""
    print("\n🔍 Testing file upload...")
    
    # Test file path
    test_file = Path("gov.uscourts.wyd.64014.141.0_1.pdf")
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"📁 Using test file: {test_file} ({test_file.stat().st_size} bytes)")
    
    try:
        # Prepare the file upload
        with open(test_file, 'rb') as f:
            files = {'file': (test_file.name, f, 'application/pdf')}
            data = {'type': 'file'}
            
            print("📤 Uploading file...")
            response = requests.post(
                'https://wolf.law.uw.edu/casestrainer/api/analyze',
                files=files,
                data=data,
                timeout=60
            )
            
            print(f"📥 Response status: {response.status_code}")
            print(f"📥 Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"✅ Upload successful!")
                    print(f"   Task ID: {result.get('task_id', 'N/A')}")
                    print(f"   Status: {result.get('status', 'N/A')}")
                    print(f"   Success: {result.get('success', 'N/A')}")
                    print(f"   Message: {result.get('message', 'N/A')}")
                    
                    # Check if we got a task ID for progress tracking
                    task_id = result.get('task_id')
                    if task_id:
                        print(f"\n🔍 Checking task progress...")
                        time.sleep(2)  # Wait a bit for processing
                        
                        progress_response = requests.get(
                            f'https://wolf.law.uw.edu/casestrainer/api/analyze/progress/{task_id}',
                            timeout=30
                        )
                        
                        if progress_response.status_code == 200:
                            progress_data = progress_response.json()
                            print(f"📊 Progress: {progress_data.get('status', 'N/A')}")
                            print(f"   Progress: {progress_data.get('progress', 'N/A')}%")
                        else:
                            print(f"⚠️  Progress check failed: {progress_response.status_code}")
                    
                    return True
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON response: {e}")
                    print(f"   Raw response: {response.text[:500]}...")
                    return False
            else:
                print(f"❌ Upload failed with status {response.status_code}")
                print(f"   Response: {response.text[:500]}...")
                return False
                
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting CaseStrainer File Upload Test")
    print("=" * 50)
    
    # Test 1: Health endpoint
    if not test_health_endpoint():
        print("\n❌ Health check failed - cannot proceed with file upload test")
        sys.exit(1)
    
    # Test 2: File upload
    if not test_file_upload():
        print("\n❌ File upload test failed")
        sys.exit(1)
    
    print("\n✅ All tests passed!")
    print("🎉 File upload functionality is working correctly")

if __name__ == "__main__":
    main() 