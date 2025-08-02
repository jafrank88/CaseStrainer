"""
Test script to verify API endpoints and application state
"""
import sys
import os
import json
import requests
from urllib.parse import urljoin

BASE_URL = "http://localhost:5000/casestrainer"

def test_endpoint(endpoint, method='GET', data=None):
    """Test a single endpoint and return the response"""
    url = urljoin(BASE_URL, endpoint)
    try:
        if method.upper() == 'GET':
            response = requests.get(url)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data)
        else:
            return {
                'url': url,
                'error': f'Unsupported method: {method}'
            }
            
        return {
            'url': url,
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'content': response.text,
            'json': response.json() if 'application/json' in response.headers.get('Content-Type', '') else None
        }
    except Exception as e:
        return {
            'url': url,
            'error': str(e)
        }

def print_result(result):
    """Print test result in a readable format"""
    print(f"\n=== {result['url']} ===")
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        return
    
    print(f"Status Code: {result['status_code']}")
    
    if result['json']:
        print("\nResponse JSON:")
        print(json.dumps(result['json'], indent=2))
    else:
        print("\nResponse Content:")
        print(result['content'])
    
    print("\nResponse Headers:")
    for key, value in result['headers'].items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    print(f"Testing API endpoints at {BASE_URL}")
    
    # Test health endpoint
    health_result = test_endpoint("/api/health")
    print_result(health_result)
    
    # Test routes endpoint
    routes_result = test_endpoint("/api/routes")
    print_result(routes_result)
    
    # Test Vue API endpoint
    vue_health_result = test_endpoint("/api/health")
    print_result(vue_health_result)
    
    # Check if this is the debug API or Vue API
    if 'json' in health_result and health_result['json'] and 'message' in health_result['json']:
        if 'Debug API' in health_result['json']['message']:
            print("\n⚠️  WARNING: Debug API is active instead of Vue API")
            print("This should not happen in production!")
        else:
            print("\n✅ Vue API is working correctly")
