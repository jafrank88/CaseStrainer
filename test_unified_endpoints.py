#!/usr/bin/env python3
"""
Comprehensive test script for unified /analyze endpoint
Tests URL, text, and file uploads for all supported file types
"""

import requests
import json
import time
import os
import sys
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:5000"
API_PREFIX = "/casestrainer/api"
ANALYZE_ENDPOINT = f"{BASE_URL}{API_PREFIX}/analyze"

# Test data with more citations
TEST_TEXT = """
This is a test document with legal citations.
The case of Brown v. Board of Education, 347 U.S. 483 (1954) established important precedent.
Additionally, Roe v. Wade, 410 U.S. 113 (1973) is another landmark case.
The court in Marbury v. Madison, 5 U.S. 137 (1803) established judicial review.
In Miranda v. Arizona, 384 U.S. 436 (1966), the Court established important procedural rights.
The case of Gideon v. Wainwright, 372 U.S. 335 (1963) guaranteed the right to counsel.
"""

TEST_URL = "https://www.law.cornell.edu/supct/html/02-102.ZS.html"

# Test file paths (create if they don't exist) - only supported types
TEST_FILES = {
    "txt": "test_files/test.txt",
    "pdf": "test_files/test.pdf", 
    "docx": "test_files/test.docx",
    "doc": "test_files/test.doc",
    "rtf": "test_files/test.rtf",
    "html": "test_files/test.html",
    "htm": "test_files/test.htm"
}

def create_test_files():
    """Create test files for different formats"""
    print("Creating test files...")
    
    # Create test_files directory
    os.makedirs("test_files", exist_ok=True)
    
    # Create text file
    with open(TEST_FILES["txt"], "w", encoding="utf-8") as f:
        f.write(TEST_TEXT)
    
    # Create a simple PDF-like file (just for testing)
    # Note: This won't be a real PDF, but it will test the file upload mechanism
    with open(TEST_FILES["pdf"], "w", encoding="utf-8") as f:
        f.write("%PDF-1.4\n")
        f.write("1 0 obj\n")
        f.write("<<\n")
        f.write("/Type /Catalog\n")
        f.write("/Pages 2 0 R\n")
        f.write(">>\n")
        f.write("endobj\n")
        f.write("2 0 obj\n")
        f.write("<<\n")
        f.write("/Type /Pages\n")
        f.write("/Kids [3 0 R]\n")
        f.write("/Count 1\n")
        f.write(">>\n")
        f.write("endobj\n")
        f.write("3 0 obj\n")
        f.write("<<\n")
        f.write("/Type /Page\n")
        f.write("/Parent 2 0 R\n")
        f.write("/MediaBox [0 0 612 792]\n")
        f.write("/Contents 4 0 R\n")
        f.write(">>\n")
        f.write("endobj\n")
        f.write("4 0 obj\n")
        f.write("<<\n")
        f.write("/Length 44\n")
        f.write(">>\n")
        f.write("stream\n")
        f.write("BT\n")
        f.write("/F1 12 Tf\n")
        f.write("72 720 Td\n")
        f.write("(" + TEST_TEXT.replace('\n', ' ') + ") Tj\n")
        f.write("ET\n")
        f.write("endstream\n")
        f.write("endobj\n")
        f.write("xref\n")
        f.write("0 5\n")
        f.write("0000000000 65535 f \n")
        f.write("0000000009 00000 n \n")
        f.write("0000000058 00000 n \n")
        f.write("0000000115 00000 n \n")
        f.write("0000000204 00000 n \n")
        f.write("trailer\n")
        f.write("<<\n")
        f.write("/Size 5\n")
        f.write("/Root 1 0 R\n")
        f.write(">>\n")
        f.write("startxref\n")
        f.write("273\n")
        f.write("%%EOF\n")
    
    print("Test files created successfully")

def test_health_endpoint():
    """Test the health endpoint"""
    print("\n" + "="*60)
    print("TESTING HEALTH ENDPOINT")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Health endpoint working correctly")
            return True
        else:
            print("❌ Health endpoint failed")
            return False
            
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False

def test_text_analysis():
    """Test text analysis through /analyze endpoint"""
    print("\n" + "="*60)
    print("TESTING TEXT ANALYSIS")
    print("="*60)
    
    try:
        # Test JSON format
        print("Testing JSON format...")
        response = requests.post(
            ANALYZE_ENDPOINT,
            json={"type": "text", "text": TEST_TEXT},
            timeout=30
        )
        print(f"JSON Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Text analysis successful")
            print(f"Response keys: {list(result.keys())}")
            print(f"Status: {result.get('status', 'Unknown')}")
            
            # Check if it's async or sync
            if result.get('task_id'):
                print(f"Task ID: {result['task_id']}")
                print("This is an async task, checking status...")
                return check_task_status(result['task_id'])
            else:
                print("This is a sync response")
                citations = result.get('citations', [])
                print(f"Citations found: {len(citations)}")
                if citations:
                    print("Sample citations:")
                    for i, citation in enumerate(citations[:3]):
                        print(f"  {i+1}. {citation}")
                return True
        else:
            print(f"❌ Text analysis failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Text analysis error: {e}")
        return False

def test_url_analysis():
    """Test URL analysis through /analyze endpoint"""
    print("\n" + "="*60)
    print("TESTING URL ANALYSIS")
    print("="*60)
    
    try:
        print(f"Testing URL: {TEST_URL}")
        response = requests.post(
            ANALYZE_ENDPOINT,
            json={"type": "url", "url": TEST_URL},
            timeout=60
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ URL analysis successful")
            print(f"Response keys: {list(result.keys())}")
            print(f"Status: {result.get('status', 'Unknown')}")
            
            # Check if it's async or sync
            if result.get('task_id'):
                print(f"Task ID: {result['task_id']}")
                print("This is an async task, checking status...")
                return check_task_status(result['task_id'])
            else:
                print("This is a sync response")
                citations = result.get('citations', [])
                print(f"Citations found: {len(citations)}")
                return True
        else:
            print(f"❌ URL analysis failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ URL analysis error: {e}")
        return False

def check_task_status(task_id):
    """Check the status of an async task"""
    print(f"Checking task status for {task_id}...")
    
    for i in range(15):  # Check up to 15 times (30 seconds)
        try:
            time.sleep(2)
            status_response = requests.get(
                f"{BASE_URL}{API_PREFIX}/task_status/{task_id}",
                timeout=10
            )
            
            if status_response.status_code == 200:
                status_result = status_response.json()
                status = status_result.get('status', 'Unknown')
                print(f"Task status: {status}")
                
                if status == 'completed':
                    print("✅ Async task completed successfully")
                    # Show results
                    citations = status_result.get('citations', [])
                    print(f"Citations found: {len(citations)}")
                    if citations:
                        print("Sample citations:")
                        for i, citation in enumerate(citations[:3]):
                            print(f"  {i+1}. {citation}")
                    return True
                elif status == 'failed':
                    print("❌ Async task failed")
                    print(f"Error: {status_result.get('error', 'Unknown error')}")
                    return False
                elif status == 'processing':
                    print(f"Still processing... ({i+1}/15)")
                else:
                    print(f"Unknown status: {status}")
            else:
                print(f"❌ Task status check failed: {status_response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error checking task status: {e}")
            return False
    
    print("⚠️  Async task timed out")
    return False

def test_file_upload(file_type, file_path):
    """Test file upload for a specific file type"""
    print(f"\nTesting {file_type.upper()} file upload...")
    
    if not os.path.exists(file_path):
        print(f"⚠️  Test file {file_path} not found, skipping")
        return False
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (f'test.{file_type}', f, f'application/{file_type}')}
            response = requests.post(
                ANALYZE_ENDPOINT,
                files=files,
                timeout=60
            )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {file_type.upper()} file upload successful")
            print(f"Response keys: {list(result.keys())}")
            print(f"Status: {result.get('status', 'Unknown')}")
            
            # Check if it's async or sync
            if result.get('task_id'):
                print(f"Task ID: {result['task_id']}")
                print("This is an async task, checking status...")
                return check_task_status(result['task_id'])
            else:
                print("This is a sync response")
                citations = result.get('citations', [])
                print(f"Citations found: {len(citations)}")
                return True
        else:
            print(f"❌ {file_type.upper()} file upload failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ {file_type.upper()} file upload error: {e}")
        return False

def test_all_file_types():
    """Test file uploads for all supported file types"""
    print("\n" + "="*60)
    print("TESTING FILE UPLOADS")
    print("="*60)
    
    results = {}
    
    for file_type, file_path in TEST_FILES.items():
        results[file_type] = test_file_upload(file_type, file_path)
    
    return results

def test_async_processing():
    """Test async processing for large text"""
    print("\n" + "="*60)
    print("TESTING ASYNC PROCESSING")
    print("="*60)
    
    # Create a large text with many citations
    large_text = TEST_TEXT * 20  # Repeat the test text 20 times
    
    try:
        print("Testing async processing with large text...")
        response = requests.post(
            ANALYZE_ENDPOINT,
            json={"type": "text", "text": large_text},
            timeout=30
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Async processing successful")
            print(f"Task ID: {result.get('task_id', 'None')}")
            print(f"Status: {result.get('status', 'Unknown')}")
            
            # If it's async, check task status
            if result.get('task_id'):
                return check_task_status(result['task_id'])
            else:
                print("✅ Synchronous processing completed")
                return True
        else:
            print(f"❌ Async processing failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Async processing error: {e}")
        return False

def test_error_handling():
    """Test error handling for invalid inputs"""
    print("\n" + "="*60)
    print("TESTING ERROR HANDLING")
    print("="*60)
    
    test_cases = [
        {"name": "Empty text", "data": {"type": "text", "text": ""}},
        {"name": "Invalid URL", "data": {"type": "url", "url": "not-a-valid-url"}},
        {"name": "Missing type", "data": {"text": "some text"}},
        {"name": "Invalid type", "data": {"type": "invalid", "text": "some text"}},
    ]
    
    results = {}
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        try:
            response = requests.post(
                ANALYZE_ENDPOINT,
                json=test_case['data'],
                timeout=10
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code in [400, 422]:  # Expected error codes
                print(f"✅ Error handling working correctly for {test_case['name']}")
                results[test_case['name']] = True
            else:
                print(f"⚠️  Unexpected response for {test_case['name']}: {response.text}")
                results[test_case['name']] = False
                
        except Exception as e:
            print(f"❌ Error in {test_case['name']}: {e}")
            results[test_case['name']] = False
    
    return results

def main():
    """Run all tests"""
    print("CaseStrainer Unified Endpoint Tests")
    print("="*60)
    
    # Check if server is running
    print("Checking if server is running...")
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not responding correctly")
            print("Please start the CaseStrainer server first")
            return
    except:
        print("❌ Cannot connect to server")
        print("Please start the CaseStrainer server first")
        return
    
    print("✅ Server is running")
    
    # Create test files
    create_test_files()
    
    # Run tests
    test_results = {}
    
    # Health check
    test_results['health'] = test_health_endpoint()
    
    # Text analysis
    test_results['text'] = test_text_analysis()
    
    # URL analysis
    test_results['url'] = test_url_analysis()
    
    # File uploads
    test_results['files'] = test_all_file_types()
    
    # Async processing
    test_results['async'] = test_async_processing()
    
    # Error handling
    test_results['errors'] = test_error_handling()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    print(f"Health Endpoint: {'✅ PASS' if test_results['health'] else '❌ FAIL'}")
    print(f"Text Analysis: {'✅ PASS' if test_results['text'] else '❌ FAIL'}")
    print(f"URL Analysis: {'✅ PASS' if test_results['url'] else '❌ FAIL'}")
    print(f"Async Processing: {'✅ PASS' if test_results['async'] else '❌ FAIL'}")
    
    print("\nFile Upload Results:")
    for file_type, result in test_results['files'].items():
        status = '✅ PASS' if result else '❌ FAIL'
        print(f"  {file_type.upper()}: {status}")
    
    print("\nError Handling Results:")
    for test_name, result in test_results['errors'].items():
        status = '✅ PASS' if result else '❌ FAIL'
        print(f"  {test_name}: {status}")
    
    # Overall result
    all_passed = all([
        test_results['health'],
        test_results['text'],
        test_results['url'],
        test_results['async'],
        all(test_results['files'].values()),
        all(test_results['errors'].values())
    ])
    
    print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")

if __name__ == "__main__":
    main() 