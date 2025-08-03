#!/usr/bin/env python3
"""
Test script for CaseStrainer API endpoints.

This script tests the /casestrainer/api/analyze endpoint with different input types
and verifies the responses.
"""
import os
import sys
import json
import requests
from urllib.parse import urljoin

# Configuration
BASE_URL = os.environ.get('CASE_STRAINER_URL', 'http://localhost:5000/casestrainer/api')
TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "test_files")
TEST_PDF = os.path.join(TEST_FILES_DIR, "test_case.pdf")

# Test text with citations
TEST_TEXT = """
The Supreme Court held in Brown v. Board of Education, 347 U.S. 483 (1954),
that racial segregation in public schools was unconstitutional. This decision
overruled the "separate but equal" doctrine established in Plessy v. Ferguson,
163 U.S. 537 (1896).

In more recent years, the Court has addressed issues such as same-sex marriage
in Obergefell v. Hodges, 576 U.S. 644 (2015), and healthcare reform in
National Federation of Independent Business v. Sebelius, 567 U.S. 519 (2012).
"""

def print_section(title):
    """Print a section header"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}")

def test_health():
    """Test the health check endpoint"""
    print_section("Testing Health Check")
    
    endpoints = [
        f"{BASE_URL}/health",
        f"{BASE_URL.rsplit('/api', 1)[0]}/health",
        f"{BASE_URL.rsplit('/casestrainer', 1)[0]}/health"
    ]
    
    for url in endpoints:
        try:
            print(f"Trying: {url}")
            response = requests.get(url, timeout=5, verify=False)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            if response.status_code == 200:
                return True
        except Exception as e:
            print(f"Error: {e}")
    
    return False

def test_text_analysis():
    """Test text analysis endpoint"""
    print_section("Testing Text Analysis")
    
    url = f"{BASE_URL}/analyze"
    headers = {'Content-Type': 'application/json'}
    payload = {
        'text': TEST_TEXT,
        'options': {
            'extract_case_names': True,
            'verify_citations': True
        }
    }
    
    try:
        print(f"POST {url}")
        print(f"Headers: {headers}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=10, verify=False)
        print(f"Status: {response.status_code}")
        
        try:
            result = response.json()
            print("Response JSON:")
            print(json.dumps(result, indent=2))
            return True
        except ValueError:
            print(f"Response (raw): {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_file_upload():
    """Test file upload endpoint"""
    print_section("Testing File Upload")
    
    url = f"{BASE_URL}/analyze"
    
    if not os.path.exists(TEST_PDF):
        print(f"Test PDF not found at {TEST_PDF}")
        return False
    
    try:
        with open(TEST_PDF, 'rb') as f:
            files = {'file': ('test.pdf', f, 'application/pdf')}
            print(f"POST {url} (multipart/form-data)")
            
            response = requests.post(
                url,
                files=files,
                timeout=30,
                verify=False
            )
            
        print(f"Status: {response.status_code}")
        
        try:
            result = response.json()
            print("Response JSON:")
            print(json.dumps(result, indent=2))
            return True
        except ValueError:
            print(f"Response (raw): {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Run all tests"""
    print("CaseStrainer API Test Script")
    print(f"Base URL: {BASE_URL}")
    
    # Run tests
    tests = [
        ("Health Check", test_health),
        ("Text Analysis", test_text_analysis),
        ("File Upload", test_file_upload)
    ]
    
    results = {}
    for name, test_func in tests:
        print_section(f"RUNNING: {name}")
        results[name] = test_func()
    
    # Print summary
    print_section("Test Results")
    all_passed = True
    for name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
