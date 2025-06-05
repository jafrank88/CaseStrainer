"""Test the health check endpoint and print app info."""

import requests
import sys


def test_health_endpoint(port=5000):
    """Test the health check endpoint."""
    url = f"http://127.0.0.1:{port}/casestrainer/api/health"
    print(f"Testing health endpoint: {url}")

    try:
        response = requests.get(url, timeout=5)
        print(f"Status Code: {response.status_code}")
        print("Response:", response.text)
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")


def print_app_info():
    """Print information about the Flask app."""
    print("\n=== Flask App Info ===")
    try:
        from app_final_vue import create_app

        app = create_app()

        print("App Name:", app.name)
        print("Instance Path:", app.instance_path)
        print("Root Path:", app.root_path)
        print("Debug:", app.debug)

        print("\n=== Blueprints ===")
        for name, bp in app.blueprints.items():
            print(f"- {name}: {bp}")

        print("\n=== Extensions ===")
        for name, ext in app.extensions.items():
            print(f"- {name}: {ext}")

    except Exception as e:
        print(f"Error getting app info: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    test_health_endpoint(port)
    print_app_info()
