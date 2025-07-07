#!/usr/bin/env python3
"""
Test script to upload the specific PDF file and test citation extraction
"""

import requests
import json
import time
import os

def test_pdf_upload():
    """Test uploading the specific PDF file"""
    
    # File path
    pdf_path = "gov.uscourts.wyd.64014.141.0_1.pdf"
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return False
    
    print(f"✅ Found file: {pdf_path}")
    print(f"📁 File size: {os.path.getsize(pdf_path)} bytes")
    
    # API endpoint
    api_url = "http://localhost:5000/api/upload"
    
    try:
        # Upload the file
        print(f"\n📤 Uploading file to: {api_url}")
        
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_path, f, 'application/pdf')}
            response = requests.post(api_url, files=files)
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📄 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload successful!")
            print(f"📋 Task ID: {result.get('task_id')}")
            print(f"📝 Message: {result.get('message')}")
            
            # Poll for results
            task_id = result.get('task_id')
            if task_id:
                print(f"\n🔄 Polling for results...")
                poll_results(task_id)
            
        else:
            print(f"❌ Upload failed!")
            print(f"📄 Response text: {response.text}")
            
            # Try to parse as JSON for better error display
            try:
                error_data = response.json()
                print(f"🚨 Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"🚨 Raw error: {response.text}")
    
    except Exception as e:
        print(f"❌ Exception during upload: {e}")
        return False
    
    return True

def poll_results(task_id):
    """Poll for task results"""
    
    api_url = f"http://localhost:5000/api/status/{task_id}"
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = requests.get(api_url)
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status')
                
                print(f"📊 Attempt {attempt + 1}: Status = {status}")
                
                if status == 'completed':
                    print(f"✅ Task completed!")
                    print(f"📋 Results: {json.dumps(result.get('results', {}), indent=2)}")
                    
                    # Show citations if found
                    citations = result.get('results', {}).get('citations', [])
                    if citations:
                        print(f"\n📚 Found {len(citations)} citations:")
                        for i, citation in enumerate(citations, 1):
                            print(f"  {i}. {citation}")
                    else:
                        print(f"\n📚 No citations found")
                    
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

if __name__ == "__main__":
    print("🧪 Testing PDF upload and citation extraction")
    print("=" * 50)
    
    success = test_pdf_upload()
    
    if success:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed!") 