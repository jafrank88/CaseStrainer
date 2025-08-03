#!/usr/bin/env python3
"""
Core endpoint test script for CaseStrainer API.
Tests the four main input scenarios:
1. File upload to /analyze
2. URL analysis to /analyze
3. Text analysis to /analyze_enhanced
4. Text analysis to /analyze (fallback)
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://wolf.law.uw.edu/casestrainer/api"
TEST_FILES_DIR = Path("test_files")
TEST_FILES_DIR.mkdir(exist_ok=True)

# Test data
TEST_TEXT = """
The Supreme Court held in Brown v. Board of Education, 347 U.S. 483 (1954), 
that racial segregation in public schools was unconstitutional.

This was later reinforced by Bolling v. Sharpe, 347 U.S. 497 (1954).
"""

TEST_URL = "https://www.courts.wa.gov/opinions/pdf/1035420.pdf"

def print_header(title: str):
    """Print a formatted test header"""
    print(f"\n{'='*80}\n{title}\n{'-'*40}")

def test_health() -> Dict[str, Any]:
    """Test health check endpoint"""
    print_header("1. Testing Health Check")
    response = requests.get(f"{BASE_URL}/health", timeout=10)
    response.raise_for_status()
    return response.json()

def test_file_upload() -> Dict[str, Any]:
    """Test file upload to /analyze"""
    print_header("2. Testing File Upload (/analyze)")
    
    # Download test file if needed
    file_path = TEST_FILES_DIR / "test_case.pdf"
    if not file_path.exists():
        print(f"Downloading test file from {TEST_URL}")
        response = requests.get(TEST_URL, stream=True, timeout=30)
        response.raise_for_status()
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    
    # Upload file
    with open(file_path, 'rb') as f:
        files = {'file': (file_path.name, f, 'application/pdf')}
        response = requests.post(
            f"{BASE_URL}/analyze",
            files=files,
            timeout=120
        )
    response.raise_for_status()
    return response.json()

def test_url_analysis() -> Dict[str, Any]:
    """Test URL analysis with /analyze"""
    print_header(f"3. Testing URL Analysis (/analyze)\nURL: {TEST_URL}")
    
    payload = {
        "url": TEST_URL,
        "type": "url"
    }
    response = requests.post(
        f"{BASE_URL}/analyze",
        json=payload,
        timeout=120
    )
    response.raise_for_status()
    return response.json()

def test_enhanced_text_analysis() -> Dict[str, Any]:
    """Test text analysis with /analyze_enhanced"""
    print_header("4. Testing Enhanced Text Analysis (/analyze_enhanced)")
    
    payload = {
        "text": TEST_TEXT,
        "type": "text"
    }
    response = requests.post(
        f"{BASE_URL}/analyze_enhanced",
        json=payload,
        timeout=60
    )
    
    # Enhanced endpoint might not be available, fallback to standard
    if response.status_code == 404:
        print("Enhanced endpoint not found, falling back to standard /analyze")
        return test_standard_text_analysis()
        
    response.raise_for_status()
    return response.json()

def test_standard_text_analysis() -> Dict[str, Any]:
    """Test text analysis with /analyze"""
    print_header("5. Testing Standard Text Analysis (/analyze)")
    
    payload = {
        "text": TEST_TEXT,
        "type": "text"
    }
    response = requests.post(
        f"{BASE_URL}/analyze",
        json=payload,
        timeout=60
    )
    response.raise_for_status()
    return response.json()

def print_result(result: Dict[str, Any], success: bool = True):
    """Print test result"""
    status = "SUCCESS" if success else "FAILED"
    print(f"\n{'='*40}")
    print(f"RESULT: {status}")
    print(f"Response: {json.dumps(result, indent=2, default=str)}")
    print("="*40)

def main():
    """Run all tests"""
    tests = [
        ("Health Check", test_health),
        ("File Upload (/analyze)", test_file_upload),
        ("URL Analysis (/analyze)", test_url_analysis),
        ("Enhanced Text Analysis (/analyze_enhanced)", test_enhanced_text_analysis),
        ("Standard Text Analysis (/analyze)", test_standard_text_analysis)
    ]
    
    results = {}
    
    try:
        # Run all tests
        for name, test_func in tests:
            print(f"\n{'*'*80}")
            print(f"RUNNING TEST: {name}")
            print(f"{'*'*80}")
            
            try:
                start_time = time.time()
                result = test_func()
                elapsed = time.time() - start_time
                print(f"\nTest completed in {elapsed:.2f} seconds")
                print_result(result, True)
                results[name] = {"status": "PASSED", "time": f"{elapsed:.2f}s"}
            except Exception as e:
                error_msg = str(e)
                print(f"\nTest failed: {error_msg}")
                print_result({"error": error_msg}, False)
                results[name] = {"status": "FAILED", "error": error_msg}
    finally:
        # Print summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        for name, result in results.items():
            status = result.get('status', 'UNKNOWN')
            if status == 'PASSED':
                print(f"✓ {name}: {status} ({result.get('time', '?')})")
            else:
                print(f"✗ {name}: {status} - {result.get('error', 'Unknown error')}")
        print("="*80)

if __name__ == "__main__":
    main()
