"""
Debug script to check registered Flask routes and test API endpoints.
"""

import sys
import requests
from app_final_vue import create_app


def print_routes():
    """Print all registered routes in the Flask app."""
    print("\n=== Registered Routes ===")
    app = create_app()
    with app.app_context():
        for rule in app.url_map.iter_rules():
            methods = list(rule.methods)
            if "HEAD" in methods:
                methods.remove("HEAD")
            if "OPTIONS" in methods:
                methods.remove("OPTIONS")
            print(f"{rule.rule} -> {rule.endpoint} [{', '.join(methods)}]")


def test_health_check(port=5000):
    """Test the health check endpoint."""
    print(
        f"\n=== Testing Health Check (http://127.0.0.1:{port}/casestrainer/api/health) ==="
    )
    try:
        response = requests.get(
            f"http://127.0.0.1:{port}/casestrainer/api/health", timeout=5
        )
        print(f"Status Code: {response.status_code}")
        print("Response:", response.text)
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print_routes()
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_health_check()
