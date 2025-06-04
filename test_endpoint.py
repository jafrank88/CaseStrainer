import sys
import os
import json

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.app_final_vue import create_app


def print_routes(app):
    print("\nAvailable routes:")
    for rule in app.url_map.iter_rules():
        methods = ",".join(rule.methods)
        print(f"{rule.endpoint}: {methods} {rule}")


def test_api():
    # Create a test client
    app = create_app()
    app.testing = True

    # Print all available routes
    print_routes(app)

    # Create test client
    client = app.test_client()

    # Test the enhanced-validate-citation endpoint
    print("\nTesting /api/enhanced-validate-citation:")
    response = client.post(
        "/api/enhanced-validate-citation",
        json={"citation": "534 F.2d 1290"},  # Using the suggested format
        content_type="application/json",
    )
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.get_json(), indent=2)}")
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        print(f"Raw response: {response.data}")


if __name__ == "__main__":
    test_api()
