#!/usr/bin/env python3
"""
Comprehensive test script for CaseStrainer API endpoints on production server.
Tests short/long text, file uploads, and URL analysis with both standard and enhanced endpoints.
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import Dict, Any, Optional, Union, Tuple

# Configuration
BASE_URL = "https://wolf.law.uw.edu/casestrainer/api"
TEST_FILES_DIR = Path("test_files")
TEST_FILES_DIR.mkdir(exist_ok=True)

# Test data
SHORT_TEXT = """
The Supreme Court held in Brown v. Board of Education, 347 U.S. 483 (1954), 
that racial segregation in public schools was unconstitutional.
"""

LONG_TEXT = """
In the landmark case of Brown v. Board of Education, 347 U.S. 483 (1954), 
the United States Supreme Court unanimously held that racial segregation 
in public schools was unconstitutional, overturning the "separate but equal" 
doctrine established in Plessy v. Ferguson, 163 U.S. 537 (1896).

This decision was later reinforced by Brown v. Board of Education II, 349 U.S. 294 (1955), 
which ordered the desegregation of public schools "with all deliberate speed."

In a related case, Bolling v. Sharpe, 347 U.S. 497 (1954), the Court extended 
this ruling to federal enclaves in Washington, D.C., under the Due Process 
Clause of the Fifth Amendment.
"""

TEST_URLS = [
    "https://www.courts.wa.gov/opinions/pdf/1035420.pdf",  # Short case
    "https://www.supremecourt.gov/opinions/22pdf/21-476_c185.pdf"  # Long case (Dobbs v. Jackson)
]

class TestRunner:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.test_count = 0
        self.passed_count = 0
        self.failed_tests = []

    def run_test(self, name: str, test_func):
        """Run a test and track results"""
        self.test_count += 1
        print(f"\n{'='*80}\nTEST {self.test_count}: {name}\n{'-'*40}")
        
        try:
            start_time = time.time()
            result = test_func()
            elapsed = time.time() - start_time
            
            if result.get('success', False):
                self.passed_count += 1
                status = "PASSED"
            else:
                status = "FAILED"
                self.failed_tests.append((name, result.get('error', 'Unknown error')))
            
            print(f"\n{'-'*40}\nRESULT: {status} in {elapsed:.2f}s")
            print(f"Response: {json.dumps(result, indent=2, default=str)}")
            return result
            
        except Exception as e:
            self.failed_tests.append((name, str(e)))
            print(f"\n{'-'*40}\nERROR: {str(e)}")
            return {'success': False, 'error': str(e)}

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print(f"TEST SUMMARY: {self.passed_count}/{self.test_count} tests passed")
        if self.failed_tests:
            print("\nFAILED TESTS:")
            for name, error in self.failed_tests:
                print(f"- {name}: {error}")
        print("="*80 + "\n")

    def test_health(self) -> Dict[str, Any]:
        """Test health check endpoint"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def test_analyze_text(self, text: str, use_enhanced: bool = False) -> Dict[str, Any]:
        """Test text analysis endpoint"""
        endpoint = "/analyze_enhanced" if use_enhanced else "/analyze"
        payload = {
            "text": text,
            "type": "text"
        }
        response = self.session.post(
            f"{self.base_url}{endpoint}",
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        return response.json()

    def test_analyze_url(self, url: str, use_enhanced: bool = False) -> Dict[str, Any]:
        """Test URL analysis endpoint"""
        endpoint = "/analyze_enhanced" if use_enhanced else "/analyze"
        payload = {
            "url": url,
            "type": "url"
        }
        response = self.session.post(
            f"{self.base_url}{endpoint}",
            json=payload,
            timeout=120  # Longer timeout for URL processing
        )
        response.raise_for_status()
        return response.json()

    def test_analyze_file(self, file_path: Path, use_enhanced: bool = False) -> Dict[str, Any]:
        """Test file upload endpoint"""
        endpoint = "/analyze_enhanced" if use_enhanced else "/analyze"
        with open(file_path, 'rb') as f:
            files = {
                'file': (file_path.name, f, 'application/pdf')
            }
            response = self.session.post(
                f"{self.base_url}{endpoint}",
                files=files,
                timeout=120  # Longer timeout for file processing
            )
        response.raise_for_status()
        return response.json()

def download_test_file(url: str, save_path: Path) -> bool:
    """Download a test file if it doesn't exist"""
    if save_path.exists():
        return True
        
    try:
        print(f"Downloading test file: {url}")
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Failed to download test file: {e}")
        return False

def main():
    # Initialize test runner
    tester = TestRunner(BASE_URL)
    
    # Test health check
    tester.run_test("Health Check", tester.test_health)
    
    # Test short text analysis (standard and enhanced)
    tester.run_test("Short Text Analysis (Standard)", 
                   lambda: tester.test_analyze_text(SHORT_TEXT, use_enhanced=False))
    
    tester.run_test("Short Text Analysis (Enhanced)", 
                   lambda: tester.test_analyze_text(SHORT_TEXT, use_enhanced=True))
    
    # Test long text analysis (standard and enhanced)
    tester.run_test("Long Text Analysis (Standard)", 
                   lambda: tester.test_analyze_text(LONG_TEXT, use_enhanced=False))
    
    tester.run_test("Long Text Analysis (Enhanced)", 
                   lambda: tester.test_analyze_text(LONG_TEXT, use_enhanced=True))
    
    # Test URL analysis
    for i, url in enumerate(TEST_URLS):
        # Standard endpoint first
        tester.run_test(f"URL Analysis {i+1} (Standard) - {url}", 
                       lambda u=url: tester.test_analyze_url(u, use_enhanced=False))
        
        # Then enhanced endpoint (if supported)
        tester.run_test(f"URL Analysis {i+1} (Enhanced) - {url}", 
                       lambda u=url: tester.test_analyze_url(u, use_enhanced=True))
    
    # Test file uploads
    for i, url in enumerate(TEST_URLS):
        file_path = TEST_FILES_DIR / f"test_case_{i+1}.pdf"
        if download_test_file(url, file_path):
            # Standard endpoint first
            tester.run_test(f"File Upload {i+1} (Standard) - {url}", 
                          lambda p=file_path: tester.test_analyze_file(p, use_enhanced=False))
            
            # Then enhanced endpoint (if supported)
            tester.run_test(f"File Upload {i+1} (Enhanced) - {url}", 
                          lambda p=file_path: tester.test_analyze_file(p, use_enhanced=True))
    
    # Print final summary
    tester.print_summary()
    
    # Exit with appropriate status code
    sys.exit(1 if tester.failed_tests else 0)

if __name__ == "__main__":
    main()
