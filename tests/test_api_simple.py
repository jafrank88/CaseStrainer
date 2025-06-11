import requests
import json
import sys

def test_endpoint(url, method="GET", data=None):
    """Test an API endpoint and print the response."""
    try:
        headers = {"Content-Type": "application/json"}
        print(f"\nTesting {method} {url}")
        if data:
            print(f"Request data: {json.dumps(data, indent=2)}")
            
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        else:
            print(f"Unsupported method: {method}")
            return False
            
        print(f"Status code: {response.status_code}")
        try:
            print("Response:")
            print(json.dumps(response.json(), indent=2))
        except:
            print(f"Response text: {response.text}")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def main():
    base_url = "http://localhost:5000"
    
    # Test health check
    test_endpoint(f"{base_url}/health")
    
    # Test API version
    test_endpoint(f"{base_url}/api/version")
    
    # Test citation verification
    test_endpoint(
        f"{base_url}/api/verify-citation",
        method="POST",
        data={"citation_text": "410 U.S. 113"}
    )
    
    # Test analyze endpoint
    test_endpoint(
        f"{base_url}/api/analyze",
        method="POST",
        data={"text": "This is a test with citation 410 U.S. 113"}
    )

if __name__ == "__main__":
    main()
