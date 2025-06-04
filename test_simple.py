import requests
import json


def test_endpoint():
    url = "http://localhost:5000/api/enhanced-validate-citation"
    headers = {"Content-Type": "application/json"}
    data = {"citation": "534 F.2d 1290"}

    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_endpoint()
