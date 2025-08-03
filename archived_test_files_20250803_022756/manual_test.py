#!/usr/bin/env python3
"""
Manual test script - run this by importing and calling functions directly
"""

import sys
import os
import requests
import json
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

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
        response = requests.get("http://10.158.120.151:5000/casestrainer/api/health", timeout=10)
        print(f"Health check status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Backend is running!")
            return True
        else:
            print(f"❌ Backend responded with status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running or not accessible")
        return False
    except Exception as e:
        print(f"❌ Error testing backend: {e}")
        return False

def test_pdf_extraction(file_path):
    """Test PDF text extraction"""
    try:
        print(f"\n📖 Testing PDF text extraction...")
        
        # Import the file extraction module
        from file_utils import extract_text_from_file
        
        # Extract text from the PDF
        start_time = time.time()
        extracted_text = extract_text_from_file(file_path)
        extraction_time = time.time() - start_time
        
        if extracted_text:
            print(f"✅ Text extraction successful!")
            print(f"⏱️  Extraction time: {extraction_time:.2f} seconds")
            print(f"📝 Text length: {len(extracted_text)} characters")
            print(f"📄 First 500 characters:")
            print("-" * 50)
            print(extracted_text[:500])
            print("-" * 50)
            
            return True, extracted_text
        else:
            print(f"❌ No text extracted from PDF")
            return False, None
            
    except Exception as e:
        print(f"❌ PDF extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_citation_extraction(text):
    """Test citation extraction from text"""
    try:
        print(f"\n🔍 Testing citation extraction...")
        
        # Import the citation extraction module
        from citation_utils import extract_all_citations
        
        # Extract citations from the text
        start_time = time.time()
        citations = extract_all_citations(text)
        extraction_time = time.time() - start_time
        
        print(f"✅ Citation extraction successful!")
        print(f"⏱️  Extraction time: {extraction_time:.2f} seconds")
        print(f"📚 Found {len(citations)} citations")
        
        if citations:
            print(f"\n📋 Citations found:")
            for i, citation in enumerate(citations, 1):
                print(f"  {i}. {citation}")
        else:
            print(f"\n📚 No citations found in the document")
        
        return True, citations
        
    except Exception as e:
        print(f"❌ Citation extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_api_upload(file_path):
    """Test API file upload"""
    try:
        print(f"\n📤 Testing API file upload...")
        
        # API endpoint
        api_url = "http://10.158.120.151:5000/casestrainer/api/analyze"
        
        # Prepare the file for upload
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'application/pdf')}
            
            # Make the request
            response = requests.post(api_url, files=files, timeout=30)
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload successful!")
            print(f"📋 Task ID: {result.get('task_id')}")
            print(f"📝 Message: {result.get('message')}")
            print(f"📊 Status: {result.get('status')}")
            
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

def test_task_status(task_id):
    """Test task status polling"""
    try:
        print(f"\n🔄 Testing task status polling...")
        
        api_url = f"http://10.158.120.151:5000/casestrainer/api/task_status/{task_id}"
        max_attempts = 10
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

def run_all_tests():
    """Run all tests"""
    print("🧪 Running all PDF tests")
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
        return False
    
    # Step 3: Test PDF text extraction
    extraction_success, extracted_text = test_pdf_extraction(file_path)
    if not extraction_success:
        print("\n❌ PDF extraction failed")
        return False
    
    # Step 4: Test citation extraction
    citation_success, citations = test_citation_extraction(extracted_text)
    if not citation_success:
        print("\n❌ Citation extraction failed")
        return False
    
    # Step 5: Test API upload
    upload_success, task_id = test_api_upload(file_path)
    if not upload_success:
        print("\n❌ API upload failed")
        return False
    
    # Step 6: Test task status polling
    if task_id:
        poll_success = test_task_status(task_id)
        if poll_success:
            print("\n✅ All tests completed successfully!")
            return True
        else:
            print("\n❌ Task processing failed")
            return False
    else:
        print("\n❌ No task ID received")
        return False

# Make functions available for manual execution
if __name__ == "__main__":
    success = run_all_tests()
    if not success:
        sys.exit(1) 