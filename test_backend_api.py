import requests
import sys


def test_backend_connection(base_url):
    print(f"Testing connection to {base_url}")

    # Test health endpoint
    try:
        health_url = f"{base_url}/casestrainer/api/health"
        print(f"\n1. Testing health endpoint: {health_url}")
        response = requests.get(health_url, timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {str(e)}")
        return False

    # Test a sample API endpoint
    try:
        test_url = f"{base_url}/casestrainer/api/test"
        print(f"\n2. Testing sample endpoint: {test_url}")
        response = requests.get(test_url, timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {str(e)}")

    return True


if __name__ == "__main__":
    base_url = "http://localhost:5000"  # Default port, change if different
    if len(sys.argv) > 1:
        base_url = sys.argv[1]

    print("CaseStrainer Backend API Tester")
    print("=" * 50)

    if not test_backend_connection(base_url):
        print(
            "\n[ERROR] Backend connection test failed. Make sure the backend is running."
        )
        sys.exit(1)

    print("\n[SUCCESS] Backend tests completed.")
