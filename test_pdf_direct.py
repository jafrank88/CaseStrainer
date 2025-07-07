#!/usr/bin/env python3
"""
Direct PDF upload test script
Tests the PDF file upload and citation extraction functionality
"""

import os
import sys
import json
import time
import requests
from pathlib import Path

def test_file_exists():
    """Test if the PDF file exists"""
    pdf_path = "gov.uscourts.wyd.64014.141.0_1.pdf"
    
    if os.path.exists(pdf_path):
        print(f"✅ File exists: {pdf_path}")
        print(f"📁 File size: {os.path.getsize(pdf_path)} bytes")
        return True, pdf_path
    else:
        print(f"❌ File not found: {pdf_path}")
        return False, None

def test_backend_health():
    """Test if the backend is running"""
    try:
        print("Testing backend health...")
        response = requests.get("http://localhost:5001/casestrainer/api/health", timeout=5)
        print(f"Health check status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Backend is running!")
            return True
        else:
            print(f"❌ Backend responded with status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running or not accessible")
        print("💡 You may need to start the backend server first")
        return False
    except Exception as e:
        print(f"❌ Error testing backend: {e}")
        return False

def upload_pdf_file(file_path):
    """Upload the PDF file to the backend"""
    try:
        print(f"\n📤 Uploading file: {file_path}")
        
        # API endpoint
        api_url = "http://localhost:5001/casestrainer/api/analyze"
        
        # Prepare the file for upload
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'application/pdf')}
            
            # Make the request
            response = requests.post(api_url, files=files, timeout=30)
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📄 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload successful!")
            print(f"📋 Task ID: {result.get('task_id')}")
            print(f"📝 Message: {result.get('message')}")
            print(f"📊 Status: {result.get('status')}")
            
            # Show metadata if available
            metadata = result.get('metadata', {})
            if metadata:
                print(f"📋 Metadata:")
                for key, value in metadata.items():
                    print(f"   {key}: {value}")
            
            return True, result.get('task_id')
            
        else:
            print(f"❌ Upload failed!")
            print(f"📄 Response text: {response.text}")
            
            # Try to parse as JSON for better error display
            try:
                error_data = response.json()
                print(f"🚨 Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"🚨 Raw error: {response.text}")
            
            return False, None
    
    except Exception as e:
        print(f"❌ Exception during upload: {e}")
        return False, None

def poll_task_status(task_id):
    """Poll for task completion"""
    try:
        print(f"\n🔄 Polling for task completion: {task_id}")
        
        api_url = f"http://localhost:5001/casestrainer/api/task_status/{task_id}"
        max_attempts = 30
        attempt = 0
        
        while attempt < max_attempts:
            try:
                response = requests.get(api_url, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get('status')
                    
                    print(f"📊 Attempt {attempt + 1}: Status = {status}")
                    
                    if status == 'completed':
                        print(f"✅ Task completed!")
                        
                        # Show results
                        results = result.get('results', {})
                        if results:
                            print(f"📋 Results summary:")
                            print(f"   Total citations: {results.get('total_citations', 0)}")
                            print(f"   Verified citations: {results.get('verified_citations', 0)}")
                            print(f"   Unverified citations: {results.get('unverified_citations', 0)}")
                            
                            # Show individual citations
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
                    
                    elif status == 'processing':
                        print(f"⏳ Still processing...")
                    
                    else:
                        print(f"❓ Unknown status: {status}")
                
                else:
                    print(f"❌ Status check failed: {response.status_code}")
                    print(f"📄 Response: {response.text}")
                
            except Exception as e:
                print(f"❌ Exception during status check: {e}")
            
            attempt += 1
            time.sleep(2)
        
        print(f"⏰ Timeout after {max_attempts} attempts")
        return False
        
    except Exception as e:
        print(f"❌ Exception during polling: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing PDF upload and citation extraction")
    print("=" * 60)
    
    # Step 1: Check if file exists
    file_exists, file_path = test_file_exists()
    if not file_exists:
        print("\n❌ Cannot proceed without the PDF file")
        return False
    
    # Step 2: Check if backend is running
    backend_running = test_backend_health()
    if not backend_running:
        print("\n❌ Cannot proceed without backend server")
        print("💡 Please start the backend server first:")
        print("   - Run: python start_app.py")
        print("   - Or use Docker: docker-compose up -d backend redis rqworker")
        return False
    
    # Step 3: Upload the file
    upload_success, task_id = upload_pdf_file(file_path)
    if not upload_success:
        print("\n❌ File upload failed")
        return False
    
    # Step 4: Poll for results
    if task_id:
        poll_success = poll_task_status(task_id)
        if poll_success:
            print("\n✅ Test completed successfully!")
            return True
        else:
            print("\n❌ Task processing failed")
            return False
    else:
        print("\n❌ No task ID received")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 