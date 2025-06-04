import requests
import sys


def test_server():
    try:
        # Test basic server connection
        print("Testing server connection...")
        response = requests.get(
            "http://localhost:5000/casestrainer/api/version", timeout=5
        )
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to server: {e}")
        return False


if __name__ == "__main__":
    if not test_server():
        sys.exit(1)
