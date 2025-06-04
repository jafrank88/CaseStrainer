import requests
import sys


def test_health():
    try:
        response = requests.get("http://localhost:5000/casestrainer/api/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    print("Testing backend health...")
    if test_health():
        print("Backend is running and responding correctly!")
    else:
        print("Could not connect to the backend.")
