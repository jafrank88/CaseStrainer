import sys
import os
import json
import requests
from urllib.parse import urljoin

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.app_final_vue import create_app

# Base URL for the API
BASE_URL = "http://localhost:5000"
API_PREFIX = "/casestrainer/api"

def print_routes(app):
    """Print all available routes in the Flask application."""
    print("\nAvailable routes:")
    for rule in app.url_map.iter_rules():
        methods = ",".join(rule.methods)
        print(f"{rule.endpoint}: {methods} {rule}")

def test_verify_citation():
    """Test the verify-citation endpoint."""
    url = urljoin(BASE_URL, f"{API_PREFIX}/verify-citation")
    print(f"\nTesting {url}")
    
    # Test with valid citation
    data = {"citation": "410 U.S. 113 (1973)"}
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except ValueError:
            print(f"Response is not JSON: {response.text}")
    except Exception as e:
        print(f"Request failed: {str(e)}")

def test_health_check():
    """Test the health check endpoint."""
    url = urljoin(BASE_URL, f"{API_PREFIX}/health")
    print(f"\nTesting {url}")
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except ValueError:
            print(f"Response is not JSON: {response.text}")
    except Exception as e:
        print(f"Request failed: {str(e)}")

def test_api():
    """Run all API tests."""
    # Create a test client for route inspection
    app = create_app()
    app.testing = True
    
    # Print all available routes
    with app.app_context():
        print_routes(app)
    
    # Run the tests
    test_health_check()
    test_verify_citation()

if __name__ == "__main__":
    test_api()
