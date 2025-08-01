#!/usr/bin/env python3
"""
CI Health Check Script for CaseStrainer

This script is specifically designed to run in CI environments to verify
that all services are running correctly after deployment.
"""

import os
import sys
import time
import socket
import requests
from typing import Dict, Any, Optional
from urllib.parse import urlparse

# Configuration
SERVICE_TIMEOUT = int(os.getenv('SERVICE_TIMEOUT', '60'))  # seconds
MAX_RETRIES = 5
RETRY_DELAY = 5  # seconds

# Service endpoints - these should match your docker-compose service names
SERVICES = {
    'backend': {
        'port': 5000,
        'path': '/casestrainer/api/health',
        'expected_status': 200,
        'timeout': 10,
    },
    'redis': {
        'port': 6379,
        'timeout': 5,
    },
}

def check_port(host: str, port: int, timeout: int = 5) -> bool:
    """Check if a TCP port is open on the given host."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False

def check_http_service(service: str, config: Dict[str, Any], host: str = 'localhost') -> Dict[str, Any]:
    """Check an HTTP service endpoint."""
    url = f"http://{host}:config['port']{config.get('path', '')}"
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                url,
                timeout=config.get('timeout', 10),
                headers={'Accept': 'application/json'}
            )
            
            if response.status_code == config.get('expected_status', 200):
                try:
                    data = response.json()
                    return {
                        'status': 'healthy',
                        'version': data.get('version', 'unknown'),
                        'response_time_ms': response.elapsed.total_seconds() * 1000,
                        'details': data
                    }
                except ValueError:
                    return {
                        'status': 'degraded',
                        'error': 'Invalid JSON response',
                        'response_text': response.text[:200]
                    }
            else:
                return {
                    'status': 'unhealthy',
                    'error': f'Unexpected status code: {response.status_code}',
                    'response_text': response.text[:200]
                }
                
        except requests.exceptions.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
                continue
                
            return {
                'status': 'unhealthy',
                'error': f'Connection failed: {str(e)}'
            }
    
    return {
        'status': 'unhealthy',
        'error': 'Max retries exceeded'
    }

def main():
    """Run health checks for all services."""
    print("🚀 Starting CI Health Checks")
    print("-" * 50)
    
    # Add initial delay to ensure services have time to start
    initial_delay = int(os.getenv('INITIAL_DELAY', '30'))  # Default 30 seconds
    print(f"⏳ Waiting {initial_delay} seconds for services to initialize...")
    time.sleep(initial_delay)
    print("🏁 Starting health checks...")
    
    # Get the host from environment or use default
    host = os.getenv('SERVICE_HOST', 'localhost')
    
    all_healthy = True
    results = {}
    
    # Check each service
    for service, config in SERVICES.items():
        print(f"🔍 Checking {service}...")
        
        # First check if the port is open
        port = config['port']
        if not check_port(host, port, config.get('timeout', 5)):
            print(f"❌ {service} port {port} is not accessible")
            results[service] = {'status': 'unhealthy', 'error': f'Port {port} not accessible'}
            all_healthy = False
            continue
            
        print(f"   ✅ Port {port} is open")
        
        # If it's an HTTP service, check the endpoint
        if 'path' in config:
            print(f"   🔄 Testing {service} endpoint...")
            result = check_http_service(service, config, host)
            results[service] = result
            
            if result['status'] == 'healthy':
                print(f"   ✅ {service} is healthy")
                if 'version' in result:
                    print(f"      Version: {result['version']}")
            else:
                print(f"   ❌ {service} is unhealthy: {result.get('error', 'Unknown error')}")
                all_healthy = False
        else:
            results[service] = {'status': 'healthy'}
            print(f"   ✅ {service} is healthy (port check only)")
        
        print()
    
    # Print summary
    print("\n📊 Health Check Summary:")
    print("-" * 50)
    for service, result in results.items():
        status_emoji = '✅' if result.get('status') == 'healthy' else '❌'
        print(f"{status_emoji} {service.upper()}: {result.get('status', 'unknown')}")
        if 'error' in result:
            print(f"   Error: {result['error']}")
    
    # Exit with appropriate status code
    if all_healthy:
        print("\n✨ All services are healthy!")
        sys.exit(0)
    else:
        print("\n❌ Some services are not healthy")
        sys.exit(1)

if __name__ == "__main__":
    main()
