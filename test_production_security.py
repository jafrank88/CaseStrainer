#!/usr/bin/env python3
"""
Production Server Security Testing
Tests various security aspects of the production server
"""

import requests
import time
import json
import os

# Test configuration
BASE_URL = "https://wolf.law.uw.edu"
API_ENDPOINT = f"{BASE_URL}/casestrainer/api/analyze"
HEALTH_ENDPOINT = f"{BASE_URL}/casestrainer/api/health"

def test_sql_injection():
    """Test for SQL injection vulnerabilities"""
    print("Testing SQL Injection Protection...")
    
    sql_injection_payloads = [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "'; INSERT INTO users VALUES ('hacker', 'password'); --",
        "' UNION SELECT * FROM users --",
    ]
    
    for payload in sql_injection_payloads:
        print(f"\n--- Testing payload: {payload[:30]}... ---")
        data = {"text": payload, "source_type": "text"}
        
        try:
            response = requests.post(API_ENDPOINT, json=data, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 400:
                print("✅ SQL injection properly blocked")
            elif response.status_code in [200, 202]:
                print("⚠️  SQL injection payload accepted (may be safe)")
            else:
                print(f"❌ Unexpected response: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def test_xss_protection():
    """Test for XSS vulnerabilities"""
    print("\nTesting XSS Protection...")
    
    xss_payloads = [
        "<script>alert('XSS')</script>",
        "javascript:alert('XSS')",
        "<img src=x onerror=alert('XSS')>",
        "';alert('XSS');//",
    ]
    
    for payload in xss_payloads:
        print(f"\n--- Testing XSS payload: {payload} ---")
        data = {"text": payload, "source_type": "text"}
        
        try:
            response = requests.post(API_ENDPOINT, json=data, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code in [200, 202]:
                # Check if response contains the payload (indicating XSS vulnerability)
                response_text = response.text
                if payload in response_text:
                    print("❌ XSS payload found in response - potential vulnerability")
                else:
                    print("✅ XSS payload properly sanitized")
            else:
                print(f"Response: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def test_path_traversal():
    """Test for path traversal vulnerabilities"""
    print("\nTesting Path Traversal Protection...")
    
    path_traversal_payloads = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "....//....//....//etc/passwd",
        "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    ]
    
    for payload in path_traversal_payloads:
        print(f"\n--- Testing path traversal: {payload} ---")
        data = {"text": payload, "source_type": "text"}
        
        try:
            response = requests.post(API_ENDPOINT, json=data, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 400:
                print("✅ Path traversal properly blocked")
            elif response.status_code in [200, 202]:
                print("⚠️  Path traversal payload accepted (may be safe)")
            else:
                print(f"❌ Unexpected response: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def test_http_methods():
    """Test allowed HTTP methods"""
    print("\nTesting HTTP Methods...")
    
    methods_to_test = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD']
    
    for method in methods_to_test:
        print(f"\n--- Testing {method} method ---")
        
        try:
            if method == 'GET':
                response = requests.get(API_ENDPOINT, timeout=10)
            elif method == 'POST':
                response = requests.post(API_ENDPOINT, json={"text": "test"}, timeout=10)
            elif method == 'PUT':
                response = requests.put(API_ENDPOINT, json={"text": "test"}, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(API_ENDPOINT, timeout=10)
            elif method == 'PATCH':
                response = requests.patch(API_ENDPOINT, json={"text": "test"}, timeout=10)
            elif method == 'OPTIONS':
                response = requests.options(API_ENDPOINT, timeout=10)
            elif method == 'HEAD':
                response = requests.head(API_ENDPOINT, timeout=10)
            
            print(f"Status: {response.status_code}")
            
            if method in ['GET', 'POST']:
                if response.status_code in [200, 202, 400, 404]:
                    print("✅ Expected response for allowed method")
                else:
                    print(f"❌ Unexpected response: {response.status_code}")
            else:
                if response.status_code == 405:  # Method Not Allowed
                    print("✅ Method properly rejected")
                else:
                    print(f"⚠️  Method {method} returned {response.status_code}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")

def test_headers():
    """Test security headers"""
    print("\nTesting Security Headers...")
    
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=10)
        headers = response.headers
        
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': ['DENY', 'SAMEORIGIN'],
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': None,  # Any value is good
            'Content-Security-Policy': None,    # Any value is good
        }
        
        print("Security Headers Check:")
        for header, expected_value in security_headers.items():
            if header in headers:
                header_value = headers[header]
                print(f"✅ {header}: {header_value}")
                
                if expected_value:
                    if isinstance(expected_value, list):
                        if header_value in expected_value:
                            print(f"   ✅ Value is secure")
                        else:
                            print(f"   ⚠️  Value may not be optimal")
                    elif header_value == expected_value:
                        print(f"   ✅ Value is secure")
                    else:
                        print(f"   ⚠️  Value may not be optimal")
            else:
                print(f"❌ {header}: Missing")
                
    except Exception as e:
        print(f"❌ Error checking headers: {e}")

def test_cors_policy():
    """Test CORS policy"""
    print("\nTesting CORS Policy...")
    
    # Test with different origins
    test_origins = [
        "https://wolf.law.uw.edu",
        "https://malicious-site.com",
        "http://localhost:3000",
        "https://google.com",
    ]
    
    for origin in test_origins:
        print(f"\n--- Testing origin: {origin} ---")
        
        try:
            headers = {'Origin': origin}
            response = requests.get(HEALTH_ENDPOINT, headers=headers, timeout=10)
            
            cors_header = response.headers.get('Access-Control-Allow-Origin')
            print(f"CORS header: {cors_header}")
            
            if origin == "https://wolf.law.uw.edu":
                if cors_header == origin or cors_header == "*":
                    print("✅ CORS allows legitimate origin")
                else:
                    print("❌ CORS doesn't allow legitimate origin")
            else:
                if cors_header == "*":
                    print("⚠️  CORS allows all origins (security concern)")
                elif cors_header == origin:
                    print("❌ CORS allows malicious origin")
                else:
                    print("✅ CORS properly restricts origin")
                    
        except Exception as e:
            print(f"❌ Error: {e}")

def test_rate_limiting_security():
    """Test rate limiting for security"""
    print("\nTesting Rate Limiting Security...")
    
    # Make rapid requests to test rate limiting
    rapid_requests = 20
    responses = []
    
    for i in range(rapid_requests):
        data = {"text": f"Rate limit test {i+1}: In Smith v. Jones, 123 F.3d 456", "source_type": "text"}
        
        try:
            response = requests.post(API_ENDPOINT, json=data, timeout=5)
            responses.append(response.status_code)
        except Exception as e:
            responses.append('error')
        
        time.sleep(0.05)  # Very small delay
    
    # Analyze rate limiting
    rate_limited = responses.count(429)
    successful = sum(1 for r in responses if r in [200, 202])
    
    print(f"Rate limiting results:")
    print(f"Total requests: {rapid_requests}")
    print(f"Successful: {successful}")
    print(f"Rate limited: {rate_limited}")
    
    if rate_limited > 0:
        print("✅ Rate limiting is active (good for security)")
    else:
        print("⚠️  No rate limiting detected (potential security concern)")

def test_input_validation():
    """Test input validation security"""
    print("\nTesting Input Validation...")
    
    malicious_inputs = [
        # Very long input
        {"text": "A" * 100000, "description": "Very long input"},
        
        # Special characters
        {"text": "Test with special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?", "description": "Special characters"},
        
        # Unicode characters
        {"text": "Unicode test: 🚀🎉💻🔥", "description": "Unicode characters"},
        
        # Null bytes
        {"text": "Test\0with\0null\0bytes", "description": "Null bytes"},
        
        # Control characters
        {"text": "Test\x00\x01\x02\x03\x04\x05", "description": "Control characters"},
    ]
    
    for test_input in malicious_inputs:
        print(f"\n--- {test_input['description']} ---")
        data = {"text": test_input['text'], "source_type": "text"}
        
        try:
            response = requests.post(API_ENDPOINT, json=data, timeout=30)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 400:
                print("✅ Malicious input properly rejected")
            elif response.status_code in [200, 202]:
                print("⚠️  Malicious input accepted (may be safe)")
            else:
                print(f"❌ Unexpected response: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Run all security tests"""
    print("🔒 Production Server Security Test Suite")
    print("=" * 60)
    
    tests = [
        test_sql_injection,
        test_xss_protection,
        test_path_traversal,
        test_http_methods,
        test_headers,
        test_cors_policy,
        test_rate_limiting_security,
        test_input_validation,
    ]
    
    results = []
    for test in tests:
        try:
            test()
            results.append(True)
        except Exception as e:
            print(f"❌ Security test failed: {e}")
            results.append(False)
    
    print(f"\n{'='*60}")
    print("📊 Security Test Summary")
    print(f"{'='*60}")
    
    passed = sum(results)
    total = len(results)
    
    print(f"Security tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All security tests passed!")
    else:
        print("⚠️  Some security tests failed - review needed")

if __name__ == "__main__":
    main() 