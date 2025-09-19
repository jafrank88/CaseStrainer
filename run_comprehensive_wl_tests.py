#!/usr/bin/env python3
"""
Comprehensive WL Citation Test Runner

This script runs comprehensive tests for WL citation extraction across:
- Input types: Text, Files, URLs  
- Processing modes: Sync, Async
- Performance benchmarks
- Metadata consistency checks

Usage:
    python run_comprehensive_wl_tests.py [--api-url http://localhost:5000]
"""

import argparse
import sys
import time
import requests
from pathlib import Path
import subprocess
import json

def check_api_availability(base_url):
    """Check if the CaseStrainer API is available."""
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        return response.status_code == 200
    except requests.RequestException:
        try:
            # Try the main endpoint if health check fails
            response = requests.get(base_url, timeout=10)
            return response.status_code in [200, 404]  # 404 is OK, means server is running
        except requests.RequestException:
            return False

def run_unit_tests():
    """Run the unit tests for WL citation extraction."""
    print("=" * 60)
    print("RUNNING UNIT TESTS")
    print("=" * 60)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_wl_citation_extraction.py", 
            "-v", "--tb=short"
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        print("UNIT TEST OUTPUT:")
        print(result.stdout)
        if result.stderr:
            print("UNIT TEST ERRORS:")
            print(result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"Error running unit tests: {e}")
        return False

def run_performance_tests():
    """Run the performance tests for WL citation extraction."""
    print("=" * 60)
    print("RUNNING PERFORMANCE TESTS")
    print("=" * 60)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_wl_performance.py", 
            "-v", "-s", "--tb=short"
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        print("PERFORMANCE TEST OUTPUT:")
        print(result.stdout)
        if result.stderr:
            print("PERFORMANCE TEST ERRORS:")
            print(result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"Error running performance tests: {e}")
        return False

def run_integration_tests(api_url):
    """Run the comprehensive integration tests."""
    print("=" * 60)
    print("RUNNING INTEGRATION TESTS")
    print("=" * 60)
    
    # Set environment variable for API URL
    import os
    os.environ['CASESTRAINER_API_URL'] = api_url
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_comprehensive_wl_integration.py", 
            "-v", "-s", "--tb=short"
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        print("INTEGRATION TEST OUTPUT:")
        print(result.stdout)
        if result.stderr:
            print("INTEGRATION TEST ERRORS:")
            print(result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"Error running integration tests: {e}")
        return False

def test_direct_extraction():
    """Test direct citation extraction without API."""
    print("=" * 60)
    print("RUNNING DIRECT EXTRACTION TESTS")
    print("=" * 60)
    
    try:
        # Add src to path
        sys.path.append(str(Path(__file__).parent / 'src'))
        from citation_extractor import CitationExtractor
        
        extractor = CitationExtractor()
        
        test_cases = [
            "See Smith v. Jones, 2006 WL 3801910 (W.D. Wash. 2006)",
            "In re Doe, 2023 WL 1234567 (9th Cir. 2023)", 
            "Example v. Test, 2001 WL 9876543 (D.C. Cir. 2001)",
            "Multiple citations: 2020 WL 5555555 and 2019 WL 7777777"
        ]
        
        total_wl_citations = 0
        
        for i, text in enumerate(test_cases, 1):
            print(f"\nTest Case {i}: {text}")
            
            start_time = time.time()
            citations = extractor.extract_citations(text)
            extraction_time = (time.time() - start_time) * 1000
            
            wl_citations = [c for c in citations if "WL" in c.citation]
            total_wl_citations += len(wl_citations)
            
            print(f"  Extraction time: {extraction_time:.2f}ms")
            print(f"  Total citations: {len(citations)}")
            print(f"  WL citations: {len(wl_citations)}")
            
            for citation in wl_citations:
                print(f"    - {citation.citation} (confidence: {citation.confidence})")
                if hasattr(citation, 'metadata') and citation.metadata:
                    metadata = citation.metadata
                    print(f"      Year: {metadata.get('year')}, Doc: {metadata.get('document_number')}")
        
        print(f"\nDIRECT EXTRACTION SUMMARY:")
        print(f"  Total test cases: {len(test_cases)}")
        print(f"  Total WL citations found: {total_wl_citations}")
        print(f"  Expected WL citations: 6")
        
        return total_wl_citations >= 6
        
    except Exception as e:
        print(f"Error in direct extraction test: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_test_report(results):
    """Generate a comprehensive test report."""
    print("\n" + "=" * 80)
    print("COMPREHENSIVE WL CITATION TEST REPORT")
    print("=" * 80)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"Test Summary: {passed_tests}/{total_tests} test suites passed")
    print()
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<30} {status}")
    
    print()
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! WL citation extraction is working correctly.")
        print()
        print("✅ WL citations are properly extracted from:")
        print("   - Direct text input")
        print("   - File uploads") 
        print("   - URL processing")
        print("   - Both sync and async processing modes")
        print("   - With correct metadata and performance")
        return True
    else:
        print("⚠️  SOME TESTS FAILED. Please review the output above.")
        print()
        failed_tests = [name for name, passed in results.items() if not passed]
        print("Failed test suites:")
        for test in failed_tests:
            print(f"   - {test}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run comprehensive WL citation tests")
    parser.add_argument("--api-url", default="http://localhost:5000", 
                       help="Base URL for CaseStrainer API")
    parser.add_argument("--skip-api", action="store_true",
                       help="Skip API-dependent tests")
    
    args = parser.parse_args()
    
    print("🔍 COMPREHENSIVE WL CITATION EXTRACTION TEST SUITE")
    print(f"API URL: {args.api_url}")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {}
    
    # Always run direct extraction tests (no API required)
    results["Direct Extraction"] = test_direct_extraction()
    
    # Always run unit tests (no API required)
    results["Unit Tests"] = run_unit_tests()
    
    # Always run performance tests (no API required)  
    results["Performance Tests"] = run_performance_tests()
    
    if not args.skip_api:
        # Check API availability
        print("Checking API availability...")
        if check_api_availability(args.api_url):
            print(f"✅ API is available at {args.api_url}")
            results["Integration Tests"] = run_integration_tests(args.api_url)
        else:
            print(f"❌ API is not available at {args.api_url}")
            print("   Make sure CaseStrainer is running with: ./cslaunch")
            print("   Skipping integration tests...")
            results["Integration Tests"] = False
    else:
        print("Skipping API-dependent tests as requested")
    
    # Generate final report
    success = generate_test_report(results)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
