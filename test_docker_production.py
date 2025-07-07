#!/usr/bin/env python3
"""
Test script for Docker production server
"""

import requests
import os
import json
import time

def test_health():
    """Test the health endpoint"""
    try:
        print("Testing health endpoint...")
        response = requests.get("http://localhost:5001/casestrainer/api/health", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_file_upload():
    """Test file upload to the production server"""
    try:
        pdf_path = "gov.uscourts.wyd.64014.141.0_1.pdf"
        if not os.path.exists(pdf_path):
            print(f"File not found: {pdf_path}")
            return None
            
        print(f"Uploading file: {pdf_path}")
        print(f"File size: {os.path.getsize(pdf_path)} bytes")
        
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_path, f, 'application/pdf')}
            response = requests.post(
                "http://localhost:5001/casestrainer/api/analyze",
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
            f"http://localhost:5001/casestrainer/api/task_status/{task_id}",
            timeout=10
        )
        
        print(f"Status check: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            status = result.get('status')
            print(f"Task status: {status}")
            
            if status == 'completed':
                print("✅ Task completed!")
                results = result.get('results', {})
                if results:
                    print(f"📋 Results summary:")
                    print(f"   Total citations: {results.get('total_citations', 0)}")
                    print(f"   Verified citations: {results.get('verified_citations', 0)}")
                    print(f"   Unverified citations: {results.get('unverified_citations', 0)}")
                    
                    citations = results.get('citations', [])
                    if citations:
                        print(f"\n📚 Found {len(citations)} citations:")
                        for i, citation in enumerate(citations, 1):
                            print(f"  {i}. {citation.get('citation', 'Unknown')}")
                            print(f"     Verified: {citation.get('verified', 'Unknown')}")
                            if citation.get('case_name'):
                                print(f"     Case: {citation.get('case_name')}")
                            if citation.get('court'):
                                print(f"     Court: {citation.get('court')}")
                            print()
                    else:
                        print(f"\n📚 No citations found in the document")
                
                return True
            elif status == 'failed':
                print(f"❌ Task failed!")
                print(f"🚨 Error: {result.get('error', 'Unknown error')}")
                return False
            else:
                return False
        else:
            print(f"Status check failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"Status check failed: {e}")
        return False

def main():
    print("🧪 Testing Docker Production Server")
    print("=" * 40)
    
    # Test health
    if not test_health():
        print("❌ Health check failed")
        print("💡 Make sure the Docker production server is running:")
        print("   Run: fix_docker_production.bat")
        return
    
    print("✅ Health check passed")
    
    # Test file upload
    task_id = test_file_upload()
    if task_id:
        print(f"✅ Upload successful, task ID: {task_id}")
        
        # Test task status
        print("Waiting for task completion...")
        for i in range(15):  # Wait up to 45 seconds
            time.sleep(3)
            if test_task_status(task_id):
                print("✅ Task completed successfully!")
                break
        else:
            print("⏰ Task timeout")
    else:
        print("❌ Upload failed")

if __name__ == "__main__":
    main() 