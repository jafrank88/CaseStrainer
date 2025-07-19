#!/usr/bin/env python3
"""
Comprehensive Production Server Test Suite
Runs all tests including basic functionality, edge cases, performance, and security
"""

import subprocess
import sys
import time
import os

def run_test_suite(test_name, test_file, description):
    """Run a test suite and return results"""
    print(f"\n{'='*60}")
    print(f"🧪 {test_name}")
    print(f"{'='*60}")
    print(f"Description: {description}")
    print(f"Running: {test_file}")
    
    try:
        result = subprocess.run(f"python {test_file}", shell=True, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ PASSED")
            if result.stdout:
                # Show last few lines of output
                lines = result.stdout.strip().split('\n')
                if len(lines) > 10:
                    print("Output (last 10 lines):")
                    for line in lines[-10:]:
                        print(f"  {line}")
                else:
                    print("Output:")
                    print(result.stdout)
            return True
        else:
            print("❌ FAILED")
            if result.stderr:
                print("Error:")
                print(result.stderr[-500:])  # Last 500 chars
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Run all comprehensive tests"""
    print("🚀 Comprehensive Production Server Test Suite")
    print("=" * 60)
    
    # Define all test suites
    test_suites = [
        {
            "name": "Basic Functionality",
            "file": "test_production_server.py",
            "description": "Tests basic API endpoints and citation processing"
        },
        {
            "name": "Local System Integration",
            "file": "test_local_system.py", 
            "description": "Tests Docker-based system integration"
        },
        {
            "name": "Citation Processing Fix",
            "file": "test_citation_fix.py",
            "description": "Tests the citation processing fix"
        },
        {
            "name": "System Status",
            "file": "test_system_status.py",
            "description": "Tests Docker container health and connectivity"
        },
        {
            "name": "Edge Cases & Error Handling",
            "file": "test_production_edge_cases.py",
            "description": "Tests error conditions and edge cases"
        },
        {
            "name": "Performance & Load Testing",
            "file": "test_production_performance.py",
            "description": "Tests performance characteristics and load handling"
        },
        {
            "name": "Security Testing",
            "file": "test_production_security.py",
            "description": "Tests security vulnerabilities and protections"
        }
    ]
    
    # Run all test suites
    results = []
    for suite in test_suites:
        success = run_test_suite(suite["name"], suite["file"], suite["description"])
        results.append({
            "name": suite["name"],
            "success": success,
            "file": suite["file"]
        })
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 Comprehensive Test Results Summary")
    print(f"{'='*60}")
    
    passed = 0
    total = len(results)
    
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{result['name']}: {status}")
        if result['success']:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} test suites passed")
    
    # Detailed breakdown
    print(f"\n{'='*60}")
    print("📋 Test Suite Breakdown")
    print(f"{'='*60}")
    
    categories = {
        "Core Functionality": ["Basic Functionality", "Citation Processing Fix"],
        "Integration": ["Local System Integration", "System Status"],
        "Robustness": ["Edge Cases & Error Handling"],
        "Performance": ["Performance & Load Testing"],
        "Security": ["Security Testing"]
    }
    
    for category, test_names in categories.items():
        print(f"\n{category}:")
        category_passed = 0
        category_total = 0
        
        for test_name in test_names:
            for result in results:
                if result['name'] == test_name:
                    status = "✅" if result['success'] else "❌"
                    print(f"  {status} {test_name}")
                    if result['success']:
                        category_passed += 1
                    category_total += 1
                    break
        
        if category_total > 0:
            print(f"  {category_passed}/{category_total} passed")
    
    # Final assessment
    print(f"\n{'='*60}")
    print("🎯 Final Assessment")
    print(f"{'='*60}")
    
    if passed == total:
        print("🎉 EXCELLENT: All test suites passed!")
        print("The production server is fully operational and secure.")
    elif passed >= total * 0.8:
        print("✅ GOOD: Most test suites passed.")
        print("The production server is operational with minor issues.")
    elif passed >= total * 0.6:
        print("⚠️  FAIR: Some test suites failed.")
        print("The production server needs attention but is functional.")
    else:
        print("❌ POOR: Many test suites failed.")
        print("The production server needs significant attention.")
    
    print(f"\nTimestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Recommendations
    if passed < total:
        print(f"\n{'='*60}")
        print("🔧 Recommendations")
        print(f"{'='*60}")
        
        failed_tests = [r for r in results if not r['success']]
        print("Failed test suites that need attention:")
        for test in failed_tests:
            print(f"  - {test['name']} ({test['file']})")
        
        print("\nNext steps:")
        print("1. Review failed test outputs above")
        print("2. Fix issues in failed test suites")
        print("3. Re-run specific test suites to verify fixes")
        print("4. Consider running individual tests for detailed debugging")

if __name__ == "__main__":
    main() 