import requests
import json
import sys

def test_endpoint(method, url, headers=None, data=None, json_data=None):
    print(f"\n{'='*80}")
    print(f"Testing {method} {url}")
    print(f"Headers: {headers}")
    if json_data:
        print(f"JSON Data: {json_data}")
    if data:
        print(f"Form Data: {data}")
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, params=data)
        elif method.upper() == 'POST':
            if json_data is not None:
                response = requests.post(url, headers=headers, json=json_data)
            else:
                response = requests.post(url, headers=headers, data=data)
        
        print(f"Status Code: {response.status_code}")
        print("Response Headers:")
        for k, v in response.headers.items():
            print(f"  {k}: {v}")
        print("Response Body:")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)
    except Exception as e:
        print(f"Request failed: {str(e)}")

if __name__ == "__main__":
    base_url = "http://localhost:5000/casestrainer/api"
    
    # Test 1: JSON content type with json parameter
    test_endpoint(
        "POST",
        f"{base_url}/verify-citation",
        headers={"Content-Type": "application/json"},
        json_data={"text": "410 U.S. 113"}
    )
    
    # Test 2: JSON content type with data parameter
    test_endpoint(
        "POST",
        f"{base_url}/verify-citation",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"text": "410 U.S. 113"})
    )
    
    # Test 3: Form data
    test_endpoint(
        "POST",
        f"{base_url}/verify-citation",
        data={"text": "410 U.S. 113"}
    )
    
    # Test 4: Health check
    test_endpoint("GET", f"{base_url}/health")
