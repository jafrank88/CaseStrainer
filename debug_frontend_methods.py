#!/usr/bin/env python3
import requests
import json
import time
import os
from pathlib import Path

def test_backend_endpoint():
    """Test if the backend endpoint is reachable"""
    print("=== TESTING BACKEND ENDPOINT ===")
    try:
        response = requests.get("http://localhost:5000/casestrainer/api/analyze", timeout=5)
        print(f"✅ Backend is reachable - Status: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend is not reachable: {e}")
        return False

def test_text_paste_method():
    """Test the text paste method (equivalent to frontend text input)"""
    print("\n=== TESTING TEXT PASTE METHOD ===")
    
    test_text = """
    Seattle Times Co. v. Ishikawa, 97 Wn.2d 30, 640 P.2d 716 (1982)
    John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017)
    """
    
    try:
        # Simulate frontend text paste request
        response = requests.post(
            "http://localhost:5000/casestrainer/api/analyze",
            json={
                "text": test_text.strip(),
                "type": "text"
            },
            timeout=60
        )
        
        print(f"✅ Text paste request successful - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response data: {json.dumps(data, indent=2)}")
            
            # Check for async processing
            if data.get('status') == 'processing' and data.get('task_id'):
                print(f"🔄 Async processing detected - Task ID: {data['task_id']}")
                return poll_task_status(data['task_id'])
            else:
                print("✅ Immediate response received")
                return data
        else:
            print(f"❌ Text paste failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Text paste error: {e}")
        return None

def test_file_upload_method():
    """Test the file upload method"""
    print("\n=== TESTING FILE UPLOAD METHOD ===")
    
    # Use the PDF file we know exists
    pdf_path = r"C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\1029764.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ Test file not found: {pdf_path}")
        return None
    
    try:
        # Simulate frontend file upload request
        with open(pdf_path, 'rb') as f:
            files = {'file': ('1029764.pdf', f, 'application/pdf')}
            
            response = requests.post(
                "http://localhost:5000/casestrainer/api/analyze",
                files=files,
                timeout=120  # Longer timeout for file uploads
            )
        
        print(f"✅ File upload request successful - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response data: {json.dumps(data, indent=2)}")
            
            # Check for async processing
            if data.get('status') == 'processing' and data.get('task_id'):
                print(f"🔄 Async processing detected - Task ID: {data['task_id']}")
                return poll_task_status(data['task_id'])
            else:
                print("✅ Immediate response received")
                return data
        else:
            print(f"❌ File upload failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ File upload error: {e}")
        return None

def test_url_upload_method():
    """Test the URL upload method"""
    print("\n=== TESTING URL UPLOAD METHOD ===")
    
    # Test with a sample URL (you can replace this with a real legal document URL)
    test_url = "https://www.courts.wa.gov/opinions/pdf/1029764.pdf"
    
    try:
        # Simulate frontend URL upload request
        response = requests.post(
            "http://localhost:5000/casestrainer/api/analyze",
            json={
                "url": test_url,
                "type": "url"
            },
            timeout=300  # 5 minutes for URL processing
        )
        
        print(f"✅ URL upload request successful - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response data: {json.dumps(data, indent=2)}")
            
            # Check for async processing
            if data.get('status') == 'processing' and data.get('task_id'):
                print(f"🔄 Async processing detected - Task ID: {data['task_id']}")
                return poll_task_status(data['task_id'])
            else:
                print("✅ Immediate response received")
                return data
        else:
            print(f"❌ URL upload failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ URL upload error: {e}")
        return None

def poll_task_status(task_id, max_wait=300):
    """Poll for task status until completion"""
    print(f"🔄 Polling task status for task ID: {task_id}")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(
                f"http://localhost:5000/casestrainer/api/task_status/{task_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                
                print(f"Task status: {status}")
                
                if status == 'completed':
                    print("✅ Task completed successfully!")
                    return data.get('results')
                elif status == 'failed':
                    print(f"❌ Task failed: {data.get('error', 'Unknown error')}")
                    return None
                elif status == 'processing':
                    print("⏳ Task still processing...")
                else:
                    print(f"⚠️ Unknown status: {status}")
            else:
                print(f"❌ Status check failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Status check error: {e}")
        
        time.sleep(2)  # Wait 2 seconds before next poll
    
    print(f"❌ Task polling timed out after {max_wait} seconds")
    return None

def analyze_results(method_name, results):
    """Analyze and display results"""
    print(f"\n=== {method_name.upper()} RESULTS ANALYSIS ===")
    
    if not results:
        print("❌ No results to analyze")
        return
    
    # Handle different result structures
    if isinstance(results, list):
        citations = results
    else:
        citations = results.get('citations', [])
    
    print(f"📊 Total citations found: {len(citations)}")
    
    # Count verification statuses
    verified_count = 0
    unverified_count = 0
    parallel_count = 0
    
    for i, citation in enumerate(citations):
        verified = citation.get('verified', False)
        if verified == True:
            verified_count += 1
        elif verified == False:
            unverified_count += 1
        elif verified == 'true_by_parallel':
            parallel_count += 1
        
        print(f"\nCitation {i+1}:")
        print(f"  - Citation: {citation.get('citation', 'N/A')}")
        print(f"  - Case Name: {citation.get('case_name', 'N/A')}")
        print(f"  - Verified: {citation.get('verified', 'N/A')}")
        print(f"  - Source: {citation.get('source', 'N/A')}")
        if citation.get('url'):
            print(f"  - URL: {citation.get('url')}")
    
    print(f"\n📈 Summary:")
    print(f"  - Verified: {verified_count}")
    print(f"  - Not verified: {unverified_count}")
    print(f"  - Verified by parallel: {parallel_count}")

def main():
    """Main debugging function"""
    print("🔍 FRONTEND METHODS DEBUGGING SCRIPT")
    print("=" * 50)
    
    # Test backend connectivity first
    if not test_backend_endpoint():
        print("\n❌ Cannot proceed - backend is not reachable")
        print("Please ensure the backend server is running on localhost:5000")
        return
    
    # Test all three methods
    methods = [
        ("Text Paste", test_text_paste_method),
        ("File Upload", test_file_upload_method),
        ("URL Upload", test_url_upload_method)
    ]
    
    results = {}
    
    for method_name, test_func in methods:
        try:
            result = test_func()
            results[method_name] = result
            analyze_results(method_name, result)
        except Exception as e:
            print(f"❌ {method_name} test failed with exception: {e}")
            results[method_name] = None
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 DEBUGGING SUMMARY")
    print("=" * 50)
    
    for method_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{method_name}: {status}")
    
    print("\n💡 RECOMMENDATIONS:")
    if not any(results.values()):
        print("- All methods are failing - check backend server and API endpoints")
    elif all(results.values()):
        print("- All methods are working correctly")
    else:
        print("- Some methods are working, others need attention")
        for method_name, result in results.items():
            if not result:
                print(f"  - {method_name} needs debugging")

if __name__ == "__main__":
    main() 