#!/usr/bin/env python3
"""
Comprehensive test runner for the CaseStrainer system
Tests all major functionality including async processing, citation extraction, and API endpoints
"""

import subprocess
import sys
import time
import os

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    print(f"Running: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ PASSED")
            if result.stdout:
                print("Output:")
                print(result.stdout[-500:])  # Last 500 chars
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

def check_system_status():
    """Check if the Docker system is running"""
    print("\n🔍 Checking System Status...")
    
    # Check if containers are running
    result = subprocess.run("docker-compose -f docker-compose.prod.yml ps", shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Docker containers are running")
        return True
    else:
        print("❌ Docker containers are not running")
        print("Please start the system with: docker-compose -f docker-compose.prod.yml up -d")
        return False

def main():
    """Run all tests"""
    print("🚀 CaseStrainer Test Suite")
    print("=" * 60)
    
    # Check system status first
    if not check_system_status():
        return
    
    # Wait for system to be ready
    print("\n⏳ Waiting for system to be ready...")
    time.sleep(5)
    
    # Define tests to run
    tests = [
        ("Production Server Test", "python -m pytest test_production_server.py -v"),
        ("Local System Test", "python test_local_system.py"),
        ("Citation Flow Test", "python test_citation_flow.py"),
        ("Upload Test", "python test_upload.py"),
        ("Docker Production Test", "python test_docker_production.py"),
    ]
    
    # Run tests
    results = []
    for test_name, cmd in tests:
        success = run_command(cmd, test_name)
        results.append((test_name, success))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 Test Results Summary")
    print(f"{'='*60}")
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 All test suites passed! The system is working correctly.")
    else:
        print("⚠️  Some test suites failed. Check the output above for details.")
    
    # Additional system checks
    print(f"\n{'='*60}")
    print("🔧 System Health Checks")
    print(f"{'='*60}")
    
    health_checks = [
        ("Redis Status", "docker logs casestrainer-redis-prod --tail 1"),
        ("Backend Status", "docker logs casestrainer-backend-prod --tail 3"),
        ("Worker Status", "docker logs casestrainer-rqworker-prod --tail 3"),
    ]
    
    for check_name, cmd in health_checks:
        print(f"\n{check_name}:")
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            if result.stdout:
                print(result.stdout.strip())
            else:
                print("No output")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
