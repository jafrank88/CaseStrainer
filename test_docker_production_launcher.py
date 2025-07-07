#!/usr/bin/env python3
"""
Test script to verify Docker Production Mode (Option 4) functionality
This script tests the enhanced launcher.ps1 Option 4 implementation
"""

import requests
import time
import subprocess
import sys
import json
from datetime import datetime

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def test_docker_status():
    """Test if Docker containers are running properly"""
    log("Testing Docker container status...")
    
    try:
        # Check if containers are running
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=casestrainer", "--format", "{{.Names}}\t{{.Status}}"],
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode == 0:
            containers = result.stdout.strip().split('\n')
            log(f"Found {len(containers)} casestrainer containers")
            
            for container in containers:
                if container.strip():
                    log(f"  {container}")
                    
            # Check for specific containers
            expected_containers = [
                "casestrainer-redis-prod",
                "casestrainer-backend-prod", 
                "casestrainer-rqworker-prod",
                "casestrainer-frontend-prod",
                "casestrainer-nginx-prod"
            ]
            
            running_containers = [line.split('\t')[0] for line in containers if line.strip()]
            
            for expected in expected_containers:
                if expected in running_containers:
                    log(f"✅ {expected} is running", "SUCCESS")
                else:
                    log(f"❌ {expected} is NOT running", "ERROR")
                    
            return len(running_containers) >= 3  # At least Redis, backend, and one other
        else:
            log(f"Docker command failed: {result.stderr}", "ERROR")
            return False
            
    except subprocess.TimeoutExpired:
        log("Docker command timed out", "ERROR")
        return False
    except Exception as e:
        log(f"Error checking Docker status: {e}", "ERROR")
        return False

def test_redis_health():
    """Test Redis container health"""
    log("Testing Redis health...")
    
    try:
        # Test Redis ping
        result = subprocess.run(
            ["docker", "exec", "casestrainer-redis-prod", "redis-cli", "ping"],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0 and "PONG" in result.stdout:
            log("✅ Redis is responding with PONG", "SUCCESS")
            return True
        else:
            log(f"❌ Redis health check failed: {result.stderr}", "ERROR")
            return False
            
    except subprocess.TimeoutExpired:
        log("Redis health check timed out", "ERROR")
        return False
    except Exception as e:
        log(f"Error checking Redis health: {e}", "ERROR")
        return False

def test_backend_health():
    """Test backend API health"""
    log("Testing backend API health...")
    
    try:
        response = requests.get(
            "http://localhost:5001/casestrainer/api/health",
            timeout=10
        )
        
        if response.status_code == 200:
            log("✅ Backend API is healthy", "SUCCESS")
            return True
        else:
            log(f"❌ Backend API returned status {response.status_code}", "ERROR")
            return False
            
    except requests.exceptions.RequestException as e:
        log(f"❌ Backend API health check failed: {e}", "ERROR")
        return False

def test_api_functionality():
    """Test basic API functionality"""
    log("Testing API functionality...")
    
    try:
        # Test citation analysis
        test_data = {
            "type": "text",
            "text": "Seattle Times Co. v. Ishikawa, 97 Wn.2d 30"
        }
        
        response = requests.post(
            "http://localhost:5001/casestrainer/api/analyze",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            log("✅ API citation analysis working", "SUCCESS")
            return True
        else:
            log(f"❌ API returned status {response.status_code}", "ERROR")
            return False
            
    except requests.exceptions.RequestException as e:
        log(f"❌ API functionality test failed: {e}", "ERROR")
        return False

def test_nginx_access():
    """Test nginx frontend access"""
    log("Testing nginx frontend access...")
    
    try:
        # Test HTTP access
        response = requests.get("http://localhost:80", timeout=10)
        if response.status_code == 200:
            log("✅ Nginx HTTP access working", "SUCCESS")
            return True
        else:
            log(f"❌ Nginx HTTP returned status {response.status_code}", "ERROR")
            return False
            
    except requests.exceptions.RequestException as e:
        log(f"❌ Nginx access test failed: {e}", "ERROR")
        return False

def test_frontend_prod():
    """Test frontend production container"""
    log("Testing frontend production container...")
    
    try:
        response = requests.get("http://localhost:8080", timeout=10)
        if response.status_code == 200:
            log("✅ Frontend production container working", "SUCCESS")
            return True
        else:
            log(f"❌ Frontend production returned status {response.status_code}", "ERROR")
            return False
            
    except requests.exceptions.RequestException as e:
        log(f"❌ Frontend production test failed: {e}", "ERROR")
        return False

def get_docker_logs(container_name, lines=10):
    """Get recent Docker logs for a container"""
    try:
        result = subprocess.run(
            ["docker", "logs", container_name, "--tail", str(lines)],
            capture_output=True, text=True, timeout=15
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error getting logs: {result.stderr}"
    except Exception as e:
        return f"Exception getting logs: {e}"

def main():
    """Main test function"""
    log("Starting Docker Production Mode (Option 4) test suite...")
    
    # Wait a bit for services to stabilize
    log("Waiting 10 seconds for services to stabilize...")
    time.sleep(10)
    
    tests = [
        ("Docker Container Status", test_docker_status),
        ("Redis Health", test_redis_health),
        ("Backend API Health", test_backend_health),
        ("API Functionality", test_api_functionality),
        ("Nginx Access", test_nginx_access),
        ("Frontend Production", test_frontend_prod)
    ]
    
    results = {}
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        log(f"\n--- Running {test_name} Test ---")
        try:
            result = test_func()
            results[test_name] = result
            if result:
                passed += 1
                log(f"✅ {test_name} PASSED", "SUCCESS")
            else:
                log(f"❌ {test_name} FAILED", "ERROR")
        except Exception as e:
            log(f"❌ {test_name} EXCEPTION: {e}", "ERROR")
            results[test_name] = False
    
    # Summary
    log(f"\n=== TEST SUMMARY ===")
    log(f"Passed: {passed}/{total} tests")
    
    if passed == total:
        log("🎉 ALL TESTS PASSED! Docker Production Mode is working correctly.", "SUCCESS")
    else:
        log("⚠️  Some tests failed. Checking logs for troubleshooting...", "WARNING")
        
        # Show logs for failed services
        log("\n=== TROUBLESHOOTING LOGS ===")
        
        if not results.get("Redis Health", True):
            log("Redis logs:")
            print(get_docker_logs("casestrainer-redis-prod", 20))
            
        if not results.get("Backend API Health", True):
            log("Backend logs:")
            print(get_docker_logs("casestrainer-backend-prod", 20))
            
        if not results.get("Nginx Access", True):
            log("Nginx logs:")
            print(get_docker_logs("casestrainer-nginx-prod", 20))
    
    # Provide troubleshooting commands
    log("\n=== TROUBLESHOOTING COMMANDS ===")
    log("If tests failed, try these commands:")
    log("  docker logs casestrainer-redis-prod --tail 50")
    log("  docker logs casestrainer-backend-prod --tail 50")
    log("  docker logs casestrainer-nginx-prod --tail 50")
    log("  docker-compose -f docker-compose.prod.yml restart")
    log("  docker-compose -f docker-compose.prod.yml down && docker-compose -f docker-compose.prod.yml up -d")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 