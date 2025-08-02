#!/usr/bin/env python3
"""
Enhanced Health Check Script for CaseStrainer

This script provides comprehensive health checking for the CaseStrainer application,
including API endpoint health, service status, and performance metrics.
"""

import os
import sys
import json
import time
import logging
import socket
import subprocess
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

import requests
import urllib3
import psutil
from redis import Redis
from rq import Queue

# Configuration
import os
from typing import Optional

# Environment detection
ENV = os.environ.get('CASE_STRAINER_ENV', 'development').lower()
IS_PRODUCTION = ENV == 'production'

# Default configuration for development
DEFAULT_BASE_URL = 'https://wolf.law.uw.edu/casestrainer/api' if IS_PRODUCTION else 'http://localhost:5000/casestrainer/api'
DEFAULT_REDIS_URL = 'redis://localhost:6379/0'
DEFAULT_TIMEOUT = 30 if IS_PRODUCTION else 10  # seconds
DEFAULT_MAX_RETRIES = 5 if IS_PRODUCTION else 3
DEFAULT_RETRY_DELAY = 5  # seconds

# Get configuration from environment variables
BASE_URL = os.environ.get('HEALTH_CHECK_BASE_URL', DEFAULT_BASE_URL)
REDIS_URL = os.environ.get('REDIS_URL', DEFAULT_REDIS_URL)
TIMEOUT = int(os.environ.get('HEALTH_CHECK_TIMEOUT', DEFAULT_TIMEOUT))
MAX_RETRIES = int(os.environ.get('HEALTH_CHECK_MAX_RETRIES', DEFAULT_MAX_RETRIES))
RETRY_DELAY = int(os.environ.get('HEALTH_CHECK_RETRY_DELAY', DEFAULT_RETRY_DELAY))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('health_check.log')
    ]
)
logger = logging.getLogger('healthcheck')

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class HealthCheckError(Exception):
    """Custom exception for health check failures."""
    pass

def check_redis_connection() -> Dict[str, Any]:
    """Check Redis connection and basic operations."""
    if IS_PRODUCTION and not os.environ.get('CHECK_REDIS_IN_PRODUCTION', 'false').lower() == 'true':
        return {
            'status': 'skipped',
            'message': 'Redis check skipped in production by default',
            'check_required': False
        }
        
    try:
        start_time = time.time()
        redis_url = os.environ.get('REDIS_URL', REDIS_URL)
        redis = Redis.from_url(redis_url, socket_connect_timeout=5, socket_timeout=5)
        
        # Test connection
        if not redis.ping():
            raise HealthCheckError("Redis ping failed")
        
        # Skip destructive tests in production
        if not IS_PRODUCTION:
            # Test basic operations
            test_key = f"healthcheck:{int(time.time())}"
            redis.set(test_key, "test", ex=10)
            if redis.get(test_key) != b"test":
                raise HealthCheckError("Redis get/set test failed")
        
        result = {
            'status': 'healthy',
            'version': redis.info().get('redis_version'),
            'used_memory': redis.info().get('used_memory_human'),
            'connected_clients': redis.info().get('connected_clients'),
            'response_time_ms': int((time.time() - start_time) * 1000)
        }
        
        # Only check queues in development or if explicitly enabled
        if not IS_PRODUCTION or os.environ.get('CHECK_REDIS_QUEUES', 'false').lower() == 'true':
            queue = Queue(connection=redis)
            result['queue_status'] = {
                'queued': len(queue),
                'failed': len(Queue('failed', connection=redis)),
                'scheduled': len(Queue('scheduled', connection=redis)),
            }
        
        return result
        
    except Exception as e:
        if IS_PRODUCTION:
            return {
                'status': 'warning',
                'message': f'Redis check failed but not critical in production: {str(e)}',
                'check_required': False
            }
        raise HealthCheckError(f"Redis check failed: {str(e)}")

def check_api_health() -> Dict[str, Any]:
    """Check the health of the CaseStrainer API endpoint."""
    # Determine the health endpoint based on environment
    health_endpoint = f"{BASE_URL}/health"
    
    # For production, we might need to handle different authentication or headers
    headers = {'Accept': 'application/json'}
    
    # For production, we might need to verify SSL certs
    verify_ssl = not IS_PRODUCTION or os.environ.get('VERIFY_SSL', 'true').lower() == 'true'
    
    for attempt in range(MAX_RETRIES):
        try:
            start_time = time.time()
            
            # First try the direct health endpoint
            try:
                response = requests.get(
                    health_endpoint,
                    headers=headers,
                    timeout=TIMEOUT,
                    verify=verify_ssl
                )
            except requests.exceptions.SSLError as e:
                if IS_PRODUCTION:
                    # In production, we should fail on SSL errors
                    raise HealthCheckError(f"SSL verification failed: {str(e)}")
                # In development, try without SSL verification
                response = requests.get(
                    health_endpoint,
                    headers=headers,
                    timeout=TIMEOUT,
                    verify=False
                )
                
            response_time = (time.time() - start_time) * 1000  # ms
            
            # Handle non-200 responses
            if response.status_code != 200:
                if response.status_code == 404 and not IS_PRODUCTION:
                    # In development, the endpoint might be at the root
                    return check_api_health_root()
                raise HealthCheckError(f"Unexpected status code: {response.status_code}")
            
            try:
                data = response.json()
            except ValueError:
                raise HealthCheckError("Invalid JSON response")
            
            # Check if the API reports as healthy
            status = data.get('status', '').lower()
            if status not in ['healthy', 'ok']:
                raise HealthCheckError(f"API reports unhealthy: {data.get('message', 'No message')}")
            
            return {
                'status': 'healthy',
                'version': data.get('version', 'unknown'),
                'timestamp': data.get('timestamp', datetime.utcnow().isoformat()),
                'response_time_ms': int(response_time),
                'details': data
            }
            
        except requests.exceptions.RequestException as e:
            if IS_PRODUCTION and not verify_ssl and 'CERTIFICATE_VERIFY_FAILED' in str(e):
                # If we're in production and SSL verification failed, try without it
                return check_api_health()
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
                continue
            raise HealthCheckError(f"API request failed after {MAX_RETRIES} attempts: {str(e)}")
    
    raise HealthCheckError("Max retries exceeded for API health check")

def check_system_metrics() -> Dict[str, Any]:
    """Collect system-level metrics."""
    try:
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'percent': psutil.virtual_memory().percent,
                'used': psutil.virtual_memory().used,
                'free': psutil.virtual_memory().free
            },
            'disk_usage': {
                mount.mountpoint: {
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': usage.percent
                }
                for mount in psutil.disk_partitions()
                if not mount.mountpoint.startswith(('/snap', '/boot'))
                for usage in [psutil.disk_usage(mount.mountpoint)]
            },
            'process_count': len(psutil.pids()),
            'boot_time': psutil.boot_time(),
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HealthCheckError(f"Failed to collect system metrics: {str(e)}")

def check_api_health_root() -> Dict[str, Any]:
    """Check the health endpoint at the root URL."""
    try:
        root_url = BASE_URL.rsplit('/api', 1)[0]  # Remove /api if present
        response = requests.get(
            f"{root_url}/health",
            headers={'Accept': 'application/json'},
            timeout=TIMEOUT,
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'status': 'healthy',
                'version': data.get('version', 'unknown'),
                'timestamp': data.get('timestamp'),
                'response_time_ms': 0,  # Not measured
                'details': data,
                'note': 'Using root health endpoint'
            }
            
    except Exception as e:
        pass  # Ignore errors, we'll handle them in the main function
        
    raise HealthCheckError("Health endpoint not found at standard locations")

def check_health() -> Dict[str, Any]:
    """
    Run comprehensive health checks for the CaseStrainer application.
    Returns a dictionary with detailed health information.
    """
    health_report = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'environment': ENV,
        'base_url': BASE_URL,
        'services': {},
        'errors': []
    }
    
    # Check API health
    try:
        api_health = check_api_health()
        health_report['services']['api'] = api_health
        if api_health.get('status') != 'healthy':
            health_report['status'] = 'degraded'
            health_report['errors'].append('API is not healthy')
    except Exception as e:
        health_report['services']['api'] = {'status': 'unhealthy', 'error': str(e)}
        health_report['status'] = 'unhealthy'
        health_report['errors'].append(f'API check failed: {str(e)}')
    
    # Check Redis health
    try:
        redis_health = check_redis_connection()
        health_report['services']['redis'] = redis_health
    except Exception as e:
        health_report['services']['redis'] = {'status': 'unhealthy', 'error': str(e)}
        health_report['status'] = 'unhealthy'
        health_report['errors'].append(f'Redis check failed: {str(e)}')
    
    # Collect system metrics
    try:
        system_metrics = check_system_metrics()
        health_report['system'] = system_metrics
    except Exception as e:
        health_report['system'] = {'status': 'error', 'error': str(e)}
        health_report['errors'].append(f'System metrics collection failed: {str(e)}')
    
    # Calculate total response time
    health_report['response_time_ms'] = int((time.time() - start_time) * 1000)
    
    # Log the health check result
    if health_report['status'] == 'healthy':
        logger.info('Health check completed successfully')
    else:
        logger.warning(f'Health check completed with issues: {health_report["errors"]}')
    
    return health_report

def main():
    """
    Main function to run comprehensive health checks and print results.
    """
    try:
        print("🚀 Starting comprehensive health check...")
        print(f"• Base URL: {BASE_URL}")
        print(f"• Redis URL: {REDIS_URL}")
        print("-" * 50)
        
        # Run health checks
        start_time = time.time()
        health_report = check_health()
        elapsed_time = (time.time() - start_time) * 1000  # ms
        
        # Print summary
        print("\n📊 Health Check Summary:")
        print("-" * 50)
        print(f"Status: {'✅ HEALTHY' if health_report['status'] == 'healthy' else '⚠️ DEGRADED' if health_report['status'] == 'degraded' else '❌ UNHEALTHY'}")
        print(f"Timestamp: {health_report['timestamp']}")
        print(f"Response Time: {elapsed_time:.2f}ms")
        
        # Print service status
        print("\n🔧 Services:")
        for service, status in health_report.get('services', {}).items():
            status_emoji = '✅' if status.get('status') == 'healthy' else '❌'
            print(f"  {status_emoji} {service.upper()}: {status.get('status', 'unknown')}")
            
            # Print additional service details
            if 'response_time_ms' in status:
                print(f"    • Response Time: {status['response_time_ms']}ms")
            if 'version' in status:
                print(f"    • Version: {status['version']}")
            if 'error' in status:
                print(f"    • Error: {status['error']}")
        
        # Print system metrics if available
        if 'system' in health_report and 'error' not in health_report['system']:
            sys_info = health_report['system']
            print("\n💻 System Metrics:")
            print(f"  • CPU Usage: {sys_info['cpu_percent']}%")
            print(f"  • Memory Usage: {sys_info['memory']['percent']}% ({sys_info['memory']['used']/1024/1024:.1f} MB used of {sys_info['memory']['total']/1024/1024:.1f} MB)")
            print(f"  • Process Count: {sys_info['process_count']}")
        
        # Print any errors
        if health_report.get('errors'):
            print("\n❌ Errors:")
            for error in health_report['errors']:
                print(f"  • {error}")
        
        # Exit with appropriate status code
        if health_report['status'] == 'healthy':
            print("\n✨ All systems operational!")
            sys.exit(0)
        elif health_report['status'] == 'degraded':
            print("\n⚠️  Service is running with degraded performance")
            sys.exit(1)
        else:
            print("\n❌ Health check failed!")
            sys.exit(2)
            
    except Exception as e:
        logger.exception("Health check failed with unexpected error")
        print(f"\n❌ CRITICAL: Health check failed with unexpected error: {str(e)}")
        print("Check the health_check.log file for more details.")
        sys.exit(3)
    print(f"\nAttempts: {result.get('attempts', 0)}/{MAX_RETRIES}")
    
    # Exit with appropriate status code for CI/CD
    if result.get('is_healthy', False):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
