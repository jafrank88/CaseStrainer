import requests
import sys
from urllib3.exceptions import MaxRetryError, NewConnectionError


def test_endpoint(url):
    try:
        response = requests.get(f"http://localhost:5000{url}", timeout=5)
        print(f"URL: {url}")
        print(f"Status: {response.status_code}")
        print(
            f"Response: {response.text[:200]}..."
            if len(response.text) > 200
            else f"Response: {response.text}"
        )
        return True
    except (
        requests.exceptions.RequestException,
        ConnectionError,
        MaxRetryError,
        NewConnectionError,
    ) as e:
        print(f"Error connecting to {url}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error with {url}: {e}")
        return False


if __name__ == "__main__":
    endpoints = ["/casestrainer/api/version", "/casestrainer/api/health"]

    print("Testing API endpoints...")
    results = [test_endpoint(ep) for ep in endpoints]

    if not any(results):
        print(
            "\nNone of the endpoints responded successfully. The server may not be running or is not accessible."
        )
        print(
            "Please ensure the server is running and accessible at http://localhost:5000"
        )
        sys.exit(1)
