#!/usr/bin/env python3
"""
Simple API test for the running backend
"""

import requests
import json
import os

def test_health():
    """Test the health endpoint"""
    try:
        print("Testing health endpoint...")
        response = requests.get("http://10.158.120.151:5000/casestrainer/api/health", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_file_upload():
    """Test file upload"""
    try:
        pdf_path = "gov.uscourts.wyd.64014.141.0_1.pdf"
        if not os.path.exists(pdf_path):
            print(f"File not found: {pdf_path}")
            return False
            
        print(f"Uploading file: {pdf_path}")
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_path, f, 'application/pdf')}
            response = requests.post(
                "http://10.158.120.151:5000/casestrainer/api/analyze",
                files=files,
                timeout=30
            )
        
        print(f"Upload status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"Task ID: {task_id}")
            return task_id
        else:
            return None
            
    except Exception as e:
        print(f"Upload failed: {e}")
        return None

def test_task_status(task_id):
    """Test task status polling"""
    if not task_id:
        return False
        
    try:
        print(f"Polling task status: {task_id}")
        response = requests.get(
            f"http://10.158.120.151:5000/casestrainer/api/task_status/{task_id}",
            timeout=10
        )
        
        print(f"Status check: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Task status: {result.get('status')}")
            return result.get('status') == 'completed'
        else:
            print(f"Status check failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"Status check failed: {e}")
        return False

def main():
    print("🧪 Simple API Test")
    print("=" * 30)
    
    # Test health
    if not test_health():
        print("❌ Health check failed")
        return
    
    print("✅ Health check passed")
    
    # Test file upload
    task_id = test_file_upload()
    if task_id:
        print(f"✅ Upload successful, task ID: {task_id}")
        
        # Test task status
        import time
        print("Waiting for task completion...")
        for i in range(10):
            time.sleep(2)
            if test_task_status(task_id):
                print("✅ Task completed successfully!")
                break
        else:
            print("⏰ Task timeout")
    else:
        print("❌ Upload failed")

if __name__ == "__main__":
    main() 