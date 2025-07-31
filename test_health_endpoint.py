"""
Test Health Endpoint Script

This script tests the health endpoint of the CaseStrainer API and displays
detailed information about the response.
"""

import requests
import json
import sys
from urllib.parse import urljoin

def test_health_endpoint(base_url='http://localhost:5000'):
    """Test the health endpoint and display detailed results."""
    health_url = urljoin(base_url, '/casestrainer/api/health')
    
    print(f"=== Testing Health Endpoint ===")
    print(f"URL: {health_url}")
    
    try:
        # Make the request with a timeout
        response = requests.get(health_url, timeout=10)
        
        # Print response details
        print(f"\n=== Response Status ===")
        print(f"Status Code: {response.status_code}")
        print("\n=== Response Headers ===")
        for key, value in response.headers.items():
            print(f"{key}: {value}")
        
        # Try to parse and pretty-print JSON response
        try:
            json_data = response.json()
            print("\n=== Response Body (JSON) ===")
            print(json.dumps(json_data, indent=2, sort_keys=True))
        except ValueError:
            print("\n=== Response Body (Raw) ===")
            print(response.text)
        
        # Check if the response indicates a healthy system
        if response.status_code == 200 and json_data.get('status') == 'healthy':
            print("\n✅ Health check passed successfully!")
            return True
        else:
            print("\n⚠️  Health check did not pass. See details above.")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error making request to {health_url}")
        print(f"Error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    # Allow specifying a different base URL via command line
    base_url = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:5000'
    test_health_endpoint(base_url)
