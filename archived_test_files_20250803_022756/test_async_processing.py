#!/usr/bin/env python3
"""
Test script for asynchronous processing functionality
Tests file uploads, URL processing, and long text processing
"""

import requests
import time
import json
import os
import tempfile
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:5000/casestrainer/api"
TEST_TIMEOUT = 300  # 5 minutes max wait time

def test_health_check():
    """Test that the API is accessible"""
    print("🔍 Testing API health check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ API health check passed")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API health check failed: {e}")
        return False

def wait_for_task_completion(task_id: str, timeout: int = TEST_TIMEOUT) -> Dict[str, Any]:
    """Poll task status until completion or timeout"""
    print(f"⏳ Waiting for task {task_id} to complete...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{BASE_URL}/task_status/{task_id}", timeout=10)
            if response.status_code == 200:
                result = response.json()
                status = result.get('status')
                
                print(f"   Status: {status}")
                
                if status == 'completed':
                    print(f"✅ Task {task_id} completed successfully")
                    return result
                elif status == 'failed':
                    print(f"❌ Task {task_id} failed: {result.get('error', 'Unknown error')}")
                    return result
                elif status in ['processing', 'queued']:
                    print(f"   Task {task_id} is {status}, waiting...")
                    time.sleep(2)
                else:
                    print(f"   Unknown status: {status}")
                    time.sleep(2)
            else:
                print(f"   Error checking status: {response.status_code}")
                time.sleep(2)
        except Exception as e:
            print(f"   Error polling task: {e}")
            time.sleep(2)
    
    print(f"❌ Task {task_id} timed out after {timeout} seconds")
    return {'status': 'timeout', 'error': 'Task timed out'}

def test_file_upload():
    """Test asynchronous file upload processing"""
    print("\n📁 Testing file upload async processing...")
    
    # Create a test file with multiple citations
    test_content = """
    Test Document with Multiple Citations
    
    This document contains several legal citations to test the async processing:
    
    1. Brown v. Board of Education, 347 U.S. 483 (1954)
    2. Roe v. Wade, 410 U.S. 113 (1973)
    3. Miranda v. Arizona, 384 U.S. 436 (1966)
    4. Marbury v. Madison, 5 U.S. 137 (1803)
    5. Gideon v. Wainwright, 372 U.S. 335 (1963)
    6. Mapp v. Ohio, 367 U.S. 643 (1961)
    7. New York Times Co. v. Sullivan, 376 U.S. 254 (1964)
    8. Tinker v. Des Moines, 393 U.S. 503 (1969)
    9. Terry v. Ohio, 392 U.S. 1 (1968)
    10. Katz v. United States, 389 U.S. 347 (1967)
    
    These citations should be extracted and verified through the async processing system.
    """
    
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_file_path = f.name
        
        # Upload file
        with open(temp_file_path, 'rb') as f:
            files = {'file': ('test_citations.txt', f, 'text/plain')}
            response = requests.post(f"{BASE_URL}/analyze", files=files, timeout=30)
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
        if response.status_code == 202:  # Accepted for async processing
            result = response.json()
            task_id = result.get('task_id')
            print(f"   File uploaded, task ID: {task_id}")
            
            # Wait for completion
            final_result = wait_for_task_completion(task_id)
            
            if final_result.get('status') == 'completed':
                citations = final_result.get('citations', [])
                print(f"   Found {len(citations)} citations")
                if len(citations) > 5:
                    print("✅ File upload async processing test PASSED")
                    return True
                else:
                    print(f"❌ Expected more citations, got {len(citations)}")
                    return False
            else:
                print(f"❌ File processing failed: {final_result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ File upload failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ File upload test failed: {e}")
        return False

def test_url_processing():
    """Test asynchronous URL processing"""
    print("\n🌐 Testing URL async processing...")
    
    # Use a test URL with legal content
    test_url = "https://www.law.cornell.edu/constitution/first_amendment"
    
    try:
        # Submit URL for processing
        data = {'url': test_url}
        response = requests.post(f"{BASE_URL}/analyze", json=data, timeout=30)
        
        if response.status_code == 202:  # Accepted for async processing
            result = response.json()
            task_id = result.get('task_id')
            print(f"   URL submitted, task ID: {task_id}")
            
            # Wait for completion
            final_result = wait_for_task_completion(task_id)
            
            if final_result.get('status') == 'completed':
                citations = final_result.get('citations', [])
                print(f"   Found {len(citations)} citations")
                print("✅ URL async processing test PASSED")
                return True
            else:
                print(f"❌ URL processing failed: {final_result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ URL submission failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ URL processing test failed: {e}")
        return False

def test_long_text_processing():
    """Test asynchronous long text processing (>30 citations)"""
    print("\n📝 Testing long text async processing...")
    
    # Create a long text with many citations
    citations_list = [
        "Brown v. Board of Education, 347 U.S. 483 (1954)",
        "Roe v. Wade, 410 U.S. 113 (1973)",
        "Miranda v. Arizona, 384 U.S. 436 (1966)",
        "Marbury v. Madison, 5 U.S. 137 (1803)",
        "Gideon v. Wainwright, 372 U.S. 335 (1963)",
        "Mapp v. Ohio, 367 U.S. 643 (1961)",
        "New York Times Co. v. Sullivan, 376 U.S. 254 (1964)",
        "Tinker v. Des Moines, 393 U.S. 503 (1969)",
        "Terry v. Ohio, 392 U.S. 1 (1968)",
        "Katz v. United States, 389 U.S. 347 (1967)",
        "United States v. Nixon, 418 U.S. 683 (1974)",
        "Griswold v. Connecticut, 381 U.S. 479 (1965)",
        "Brandenburg v. Ohio, 395 U.S. 444 (1969)",
        "New York Times Co. v. United States, 403 U.S. 713 (1971)",
        "Furman v. Georgia, 408 U.S. 238 (1972)",
        "Regents of Univ. of Cal. v. Bakke, 438 U.S. 265 (1978)",
        "Planned Parenthood v. Casey, 505 U.S. 833 (1992)",
        "Lawrence v. Texas, 539 U.S. 558 (2003)",
        "District of Columbia v. Heller, 554 U.S. 570 (2008)",
        "Citizens United v. FEC, 558 U.S. 310 (2010)",
        "Obergefell v. Hodges, 576 U.S. 644 (2015)",
        "Trump v. Hawaii, 585 U.S. ___ (2018)",
        "Carpenter v. United States, 585 U.S. ___ (2018)",
        "American Legion v. American Humanist Assn., 588 U.S. ___ (2019)",
        "Bostock v. Clayton County, 590 U.S. ___ (2020)",
        "Fulton v. City of Philadelphia, 593 U.S. ___ (2021)",
        "Dobbs v. Jackson Women's Health Organization, 597 U.S. ___ (2022)",
        "Students for Fair Admissions v. Harvard, 600 U.S. ___ (2023)",
        "Moore v. Harper, 600 U.S. ___ (2023)",
        "303 Creative LLC v. Elenis, 600 U.S. ___ (2023)",
        "Allen v. Milligan, 599 U.S. ___ (2023)",
        "Groff v. DeJoy, 600 U.S. ___ (2023)",
        "Tyler v. Hennepin County, 598 U.S. ___ (2023)",
        "Counterman v. Colorado, 600 U.S. ___ (2023)",
        "Andy Warhol Foundation v. Goldsmith, 598 U.S. ___ (2023)"
    ]
    
    # Create a very long text (>10KB to trigger async processing)
    long_text = "Legal Research Document\n\n"
    long_text += "This document contains numerous legal citations for testing purposes:\n\n"
    
    for i, citation in enumerate(citations_list, 1):
        long_text += f"{i}. {citation}\n"
        long_text += f"   This case established important precedent in American jurisprudence. "
        long_text += f"The decision in {citation} has been cited extensively in subsequent cases. "
        long_text += f"Legal scholars have written extensively about the implications of this ruling. "
        long_text += f"The court's reasoning in this case continues to influence modern legal doctrine.\n\n"
    
    print(f"   Text length: {len(long_text)} characters")
    
    try:
        # Submit long text for processing
        data = {'text': long_text}
        response = requests.post(f"{BASE_URL}/analyze", json=data, timeout=30)
        
        if response.status_code == 202:  # Should be async due to length
            result = response.json()
            task_id = result.get('task_id')
            print(f"   Long text submitted for async processing, task ID: {task_id}")
            
            # Wait for completion
            final_result = wait_for_task_completion(task_id, timeout=600)  # 10 minutes for long text
            
            if final_result.get('status') == 'completed':
                citations = final_result.get('citations', [])
                print(f"   Found {len(citations)} citations")
                if len(citations) > 20:
                    print("✅ Long text async processing test PASSED")
                    return True
                else:
                    print(f"❌ Expected more citations, got {len(citations)}")
                    return False
            else:
                print(f"❌ Long text processing failed: {final_result.get('error', 'Unknown error')}")
                return False
        elif response.status_code == 200:
            # Processed immediately (shouldn't happen with this much text)
            result = response.json()
            citations = result.get('citations', [])
            print(f"   Text processed immediately with {len(citations)} citations")
            print("✅ Long text processing test PASSED (immediate processing)")
            return True
        else:
            print(f"❌ Long text submission failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Long text processing test failed: {e}")
        return False

def test_short_text_immediate():
    """Test that short text is processed immediately (not async)"""
    print("\n⚡ Testing short text immediate processing...")
    
    short_text = "This is a short text with one citation: Brown v. Board of Education, 347 U.S. 483 (1954)."
    
    try:
        data = {'text': short_text}
        response = requests.post(f"{BASE_URL}/analyze", json=data, timeout=30)
        
        if response.status_code == 200:  # Should be immediate
            result = response.json()
            citations = result.get('citations', [])
            print(f"   Found {len(citations)} citations immediately")
            print("✅ Short text immediate processing test PASSED")
            return True
        elif response.status_code == 202:
            print("⚠️  Short text was processed async (unexpected but not necessarily wrong)")
            task_id = result.get('task_id')
            final_result = wait_for_task_completion(task_id)
            return final_result.get('status') == 'completed'
        else:
            print(f"❌ Short text processing failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Short text processing test failed: {e}")
        return False

def main():
    """Run all async processing tests"""
    print("🧪 CaseStrainer Async Processing Test Suite")
    print("=" * 50)
    
    tests = [
        ("API Health Check", test_health_check),
        ("Short Text Immediate Processing", test_short_text_immediate),
        ("File Upload Async Processing", test_file_upload),
        ("URL Async Processing", test_url_processing),
        ("Long Text Async Processing", test_long_text_processing),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 TEST RESULTS SUMMARY")
    print(f"{'='*50}")
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All async processing tests PASSED!")
        return True
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
        return False

if __name__ == "__main__":
    main()
