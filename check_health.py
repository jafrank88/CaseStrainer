import requests
import urllib3
import time
import sys
import json
from typing import Dict, Any, Optional

# Configuration
import os

# Get the base URL from environment variable or use localhost as default
BASE_URL = os.environ.get('HEALTH_CHECK_BASE_URL', 'http://localhost:5000')
HEALTH_CHECK_URL = f"{BASE_URL}/casestrainer/api/health"
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
TIMEOUT = 10  # seconds

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def check_health() -> Dict[str, Any]:
    """
    Check the health of the CaseStrainer API endpoint.
    Returns a dictionary with the health check results.
    """
    for attempt in range(MAX_RETRIES):
        try:
            # Make the request without verifying SSL certificate
            response = requests.get(
                HEALTH_CHECK_URL,
                verify=False,
                timeout=TIMEOUT
            )
            
            # Check if the response is valid JSON
            try:
                response_json = response.json()
                is_healthy = response.status_code == 200 and response_json.get('status') == 'healthy'
                
                return {
                    'success': True,
                    'status_code': response.status_code,
                    'response': response_json,
                    'is_healthy': is_healthy,
                    'attempts': attempt + 1
                }
                
            except json.JSONDecodeError:
                return {
                    'success': False,
                    'error': 'Invalid JSON response',
                    'status_code': response.status_code,
                    'response_text': response.text,
                    'attempts': attempt + 1
                }
                
        except requests.exceptions.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
                continue
                
            return {
                'success': False,
                'error': str(e),
                'attempts': attempt + 1
            }
    
    return {
        'success': False,
        'error': 'Max retries exceeded',
        'attempts': MAX_RETRIES
    }

def main():
    """Main function to run the health check."""
    print(f"Checking health of {HEALTH_CHECK_URL}")
    print(f"Max retries: {MAX_RETRIES}, Timeout: {TIMEOUT}s")
    
    result = check_health()
    
    # Print detailed results
    print("\n=== Health Check Results ===")
    print(f"Success: {'✅' if result.get('success', False) else '❌'}")
    
    if 'status_code' in result:
        print(f"Status Code: {result['status_code']}")
    
    if 'is_healthy' in result:
        print(f"Healthy: {'✅' if result['is_healthy'] else '❌'}")
    
    if 'response' in result:
        print("\nResponse:")
        print(json.dumps(result['response'], indent=2))
    
    if 'error' in result:
        print(f"\n❌ Error: {result['error']}")
    
    print(f"\nAttempts: {result.get('attempts', 0)}/{MAX_RETRIES}")
    
    # Exit with appropriate status code for CI/CD
    if result.get('is_healthy', False):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
