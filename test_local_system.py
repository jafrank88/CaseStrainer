#!/usr/bin/env python3
"""
Local system test for the async processing system
Tests the Docker-based system running on localhost
"""

import requests
import time
import json
import os

# Test configuration
BASE_URL = "http://localhost:5001"
API_ENDPOINT = f"{BASE_URL}/casestrainer/api/analyze"
HEALTH_ENDPOINT = f"{BASE_URL}/casestrainer/api/health"

def test_health_check():
    """Test the health check endpoint"""
    print("Testing Health Check...")
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health check passed: {health_data.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ Health check failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_text_processing():
    """Test text processing with async system"""
    print("\nTesting Text Processing...")
    
    test_text = "In Roe v. Wade, 410 U.S. 113 (1973), the court held that..."
    
    data = {
        "text": test_text,
        "source_type": "text"
    }
    
    try:
        print("Sending text for processing...")
        start_time = time.time()
        
        response = requests.post(API_ENDPOINT, json=data, timeout=30)
        processing_time = time.time() - start_time
        
        print(f"Status: {response.status_code}")
        print(f"Processing time: {processing_time:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            print(f"✅ Text processing successful!")
            print(f"Found {len(citations)} citations")
            
            for i, citation in enumerate(citations, 1):
                print(f"  {i}. {citation.get('citation', 'N/A')}")
                print(f"     Case: {citation.get('extracted_case_name', 'N/A')}")
                print(f"     Verified: {citation.get('verified', False)}")
            
            return True
        else:
            print(f"❌ Text processing failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Text processing error: {e}")
        return False

def test_file_upload():
    """Test file upload with async processing"""
    print("\nTesting File Upload...")
    
    # Create a simple test file
    test_content = "This is a test document with citation: Roe v. Wade, 410 U.S. 113 (1973)."
    test_file_path = "test_document.txt"
    
    try:
        with open(test_file_path, 'w') as f:
            f.write(test_content)
        
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test_document.txt', f, 'text/plain')}
            
            print("Uploading file...")
            start_time = time.time()
            
            response = requests.post(API_ENDPOINT, files=files, timeout=30)
            processing_time = time.time() - start_time
            
            print(f"Status: {response.status_code}")
            print(f"Processing time: {processing_time:.2f} seconds")
            
            if response.status_code == 202:  # Accepted for async processing
                result = response.json()
                task_id = result.get('task_id')
                print(f"✅ File queued for processing! Task ID: {task_id}")
                
                # Poll for completion
                print("Polling for task completion...")
                for i in range(12):  # Wait up to 60 seconds
                    time.sleep(5)
                    
                    status_response = requests.get(f"{BASE_URL}/casestrainer/api/task_status/{task_id}", timeout=10)
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status')
                        print(f"Task status: {status}")
                        
                        if status == 'completed':
                            citations = status_data.get('citations', [])
                            print(f"✅ File processing completed!")
                            print(f"Found {len(citations)} citations")
                            return True
                        elif status == 'failed':
                            print(f"❌ File processing failed: {status_data.get('error', 'Unknown error')}")
                            return False
                    else:
                        print(f"❌ Status check failed: {status_response.status_code}")
                        return False
                
                print("⏰ Task polling timed out")
                return False
            else:
                print(f"❌ File upload failed: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ File upload error: {e}")
        return False
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

def test_url_processing():
    """Test URL processing with async system"""
    print("\nTesting URL Processing...")
    
    # Use a simple test URL (you can replace this with a real legal document URL)
    test_url = "https://www.supremecourt.gov/opinions/22pdf/21-476_8n59.pdf"
    
    data = {
        "type": "url",
        "url": test_url
    }
    
    try:
        print(f"Processing URL: {test_url}")
        start_time = time.time()
        
        response = requests.post(API_ENDPOINT, json=data, timeout=30)
        processing_time = time.time() - start_time
        
        print(f"Status: {response.status_code}")
        print(f"Processing time: {processing_time:.2f} seconds")
        
        if response.status_code == 202:  # Accepted for async processing
            result = response.json()
            task_id = result.get('task_id')
            print(f"✅ URL queued for processing! Task ID: {task_id}")
            
            # Poll for completion
            print("Polling for task completion...")
            for i in range(12):  # Wait up to 60 seconds
                time.sleep(5)
                
                status_response = requests.get(f"{BASE_URL}/casestrainer/api/task_status/{task_id}", timeout=10)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get('status')
                    print(f"Task status: {status}")
                    
                    if status == 'completed':
                        citations = status_data.get('citations', [])
                        print(f"✅ URL processing completed!")
                        print(f"Found {len(citations)} citations")
                        return True
                    elif status == 'failed':
                        print(f"❌ URL processing failed: {status_data.get('error', 'Unknown error')}")
                        return False
                else:
                    print(f"❌ Status check failed: {status_response.status_code}")
                    return False
            
            print("⏰ Task polling timed out")
            return False
        else:
            print(f"❌ URL processing failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ URL processing error: {e}")
        return False

def main():
    """Run all tests"""
    print("Local System Test Suite")
    print("=" * 50)
    
    # Check if system is running
    print("Checking if system is running...")
    if not test_health_check():
        print("❌ System is not running. Please start the Docker containers first.")
        print("Run: docker-compose -f docker-compose.prod.yml up -d")
        return
    
    print("\n✅ System is running! Starting tests...")
    
    # Run tests
    tests = [
        ("Text Processing", test_text_processing),
        ("File Upload", test_file_upload),
        ("URL Processing", test_url_processing)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("📊 Test Results Summary")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The async processing system is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    main() 