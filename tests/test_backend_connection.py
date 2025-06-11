import requests


def test_backend():
    url = "http://localhost:5000/casestrainer/api/health"
    headers = {
        "Origin": "http://localhost:5174",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "content-type",
    }

    print(f"Testing connection to: {url}")

    # Test OPTIONS request (CORS preflight)
    print("\nTesting OPTIONS request:")
    try:
        response = requests.options(url, headers=headers, timeout=5)
        print(f"Status Code: {response.status_code}")
        print("Response Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"Error with OPTIONS request: {e}")

    # Test GET request
    print("\nTesting GET request:")
    try:
        response = requests.get(url, timeout=5)
        print(f"Status Code: {response.status_code}")
        print("Response Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        print("\nResponse Body:")
        print(response.text)
    except Exception as e:
        print(f"Error with GET request: {e}")


if __name__ == "__main__":
    test_backend()
