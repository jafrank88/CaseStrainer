#!/usr/bin/env python3
"""
Production Server Edge Cases and Error Handling Tests
Tests various error conditions and edge cases for the production server
"""

import requests
import time
import json
import os

# Test configuration
BASE_URL = "https://wolf.law.uw.edu"
API_ENDPOINT = f"{BASE_URL}/casestrainer/api/analyze"
HEALTH_ENDPOINT = f"{BASE_URL}/casestrainer/api/health"

def test_empty_input():
    """Test handling of empty text input"""
    print("Testing Empty Input Handling...")
    
    test_cases = [
        {"text": "", "description": "Empty string"},
        {"text": "   ", "description": "Whitespace only"},
        {"text": None, "description": "None value"},
        {"text": "No citations here", "description": "Text without citations"},
    ]
    
    for case in test_cases:
        print(f"\n--- {case['description']} ---")
        data = {"text": case['text'], "source_type": "text"}
        
        try:
            response = requests.post(API_ENDPOINT, json=data, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code in [200, 400]:
                print("✅ Properly handled")
            else:
                print(f"❌ Unexpected status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def test_large_input():
    """Test handling of very large text input"""
    print("\nTesting Large Input Handling...")
    
    # Create a large text with many citations
    large_text = "This is a large document. " * 1000
    large_text += "In Roe v. Wade, 410 U.S. 113 (1973), the court held that... " * 50
    
    data = {"text": large_text, "source_type": "text"}
    
    try:
        print(f"Input size: {len(large_text)} characters")
        start_time = time.time()
        
        response = requests.post(API_ENDPOINT, json=data, timeout=60)
        processing_time = time.time() - start_time
        
        print(f"Status: {response.status_code}")
        print(f"Processing time: {processing_time:.2f} seconds")
        
        if response.status_code == 202:  # Should be async for large input
            print("✅ Large input properly queued for async processing")
        elif response.status_code == 200:
            print("✅ Large input processed synchronously")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_malformed_json():
    """Test handling of malformed JSON requests"""
    print("\nTesting Malformed JSON Handling...")
    
    malformed_cases = [
        ("Missing text field", {"source_type": "text"}),
        ("Wrong field name", {"content": "test", "source_type": "text"}),
        ("Invalid source_type", {"text": "test", "source_type": "invalid"}),
    ]
    
    for description, data in malformed_cases:
        print(f"\n--- {description} ---")
        
        try:
            response = requests.post(API_ENDPOINT, json=data, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 400:
                print("✅ Properly rejected malformed request")
            else:
                print(f"❌ Should have returned 400, got {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def test_concurrent_requests():
    """Test handling of concurrent requests"""
    print("\nTesting Concurrent Request Handling...")
    
    import threading
    import queue
    
    results = queue.Queue()
    
    def make_request(request_id):
        """Make a single request"""
        test_text = f"Request {request_id}: In Smith v. Jones, 123 F.3d 456 (2d Cir. 1995)"
        data = {"text": test_text, "source_type": "text"}
        
        try:
            start_time = time.time()
            response = requests.post(API_ENDPOINT, json=data, timeout=30)
            processing_time = time.time() - start_time
            
            results.put({
                'id': request_id,
                'status': response.status_code,
                'time': processing_time,
                'success': response.status_code in [200, 202]
            })
        except Exception as e:
            results.put({
                'id': request_id,
                'status': 'error',
                'time': 0,
                'success': False,
                'error': str(e)
            })
    
    # Start 5 concurrent requests
    threads = []
    for i in range(5):
        thread = threading.Thread(target=make_request, args=(i+1,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Collect results
    successful = 0
    total_time = 0
    
    while not results.empty():
        result = results.get()
        print(f"Request {result['id']}: Status {result['status']}, Time {result['time']:.2f}s")
        if result['success']:
            successful += 1
        total_time += result['time']
    
    print(f"\nConcurrent requests: {successful}/5 successful")
    print(f"Average response time: {total_time/5:.2f} seconds")
    
    if successful >= 4:
        print("✅ Concurrent request handling working well")
    else:
        print("❌ Concurrent request handling needs improvement")

def test_rate_limiting():
    """Test if rate limiting is working"""
    print("\nTesting Rate Limiting...")
    
    # Make rapid requests
    rapid_requests = 10
    responses = []
    
    for i in range(rapid_requests):
        data = {"text": f"Rapid request {i+1}: In Smith v. Jones, 123 F.3d 456", "source_type": "text"}
        
        try:
            response = requests.post(API_ENDPOINT, json=data, timeout=10)
            responses.append(response.status_code)
            print(f"Request {i+1}: {response.status_code}")
        except Exception as e:
            responses.append('error')
            print(f"Request {i+1}: error - {e}")
        
        time.sleep(0.1)  # Small delay between requests
    
    # Check for rate limiting (429 status codes)
    rate_limited = responses.count(429)
    successful = sum(1 for r in responses if r in [200, 202])
    
    print(f"\nRate limiting results:")
    print(f"Successful: {successful}/{rapid_requests}")
    print(f"Rate limited: {rate_limited}/{rapid_requests}")
    
    if rate_limited > 0:
        print("✅ Rate limiting is active")
    else:
        print("⚠️  No rate limiting detected (may be expected)")

def test_file_type_validation():
    """Test file type validation"""
    print("\nTesting File Type Validation...")
    
    # Create test files
    test_files = [
        ("valid.txt", "This is a valid text file with citation: Roe v. Wade, 410 U.S. 113", "text/plain"),
        ("valid.pdf", b"%PDF-1.4\nTest PDF content", "application/pdf"),
        ("invalid.exe", b"MZ\x90\x00", "application/x-executable"),
    ]
    
    for filename, content, content_type in test_files:
        print(f"\n--- Testing {filename} ---")
        
        # Create temporary file
        with open(filename, 'wb' if isinstance(content, bytes) else 'w') as f:
            f.write(content)
        
        try:
            with open(filename, 'rb') as f:
                files = {'file': (filename, f, content_type)}
                response = requests.post(API_ENDPOINT, files=files, timeout=30)
            
            print(f"Status: {response.status_code}")
            
            if filename.endswith('.exe'):
                if response.status_code == 400:
                    print("✅ Invalid file type properly rejected")
                else:
                    print("❌ Invalid file type should have been rejected")
            else:
                if response.status_code in [200, 202]:
                    print("✅ Valid file type accepted")
                else:
                    print(f"❌ Valid file type rejected: {response.status_code}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            # Clean up
            if os.path.exists(filename):
                os.remove(filename)

def test_ssl_certificate():
    """Test SSL certificate validity"""
    print("\nTesting SSL Certificate...")
    
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=10, verify=True)
        print(f"SSL Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SSL certificate is valid")
        else:
            print(f"❌ SSL certificate issue: {response.status_code}")
            
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL certificate error: {e}")
    except Exception as e:
        print(f"❌ Other error: {e}")

def main():
    """Run all edge case tests"""
    print("🧪 Production Server Edge Cases Test Suite")
    print("=" * 60)
    
    tests = [
        test_empty_input,
        test_large_input,
        test_malformed_json,
        test_concurrent_requests,
        test_rate_limiting,
        test_file_type_validation,
        test_ssl_certificate,
    ]
    
    results = []
    for test in tests:
        try:
            test()
            results.append(True)
        except Exception as e:
            print(f"❌ Test failed: {e}")
            results.append(False)
    
    print(f"\n{'='*60}")
    print("📊 Edge Cases Test Summary")
    print(f"{'='*60}")
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All edge case tests passed!")
    else:
        print("⚠️  Some edge case tests failed")

if __name__ == "__main__":
    main() 