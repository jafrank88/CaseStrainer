import requests
import json
import sys

def test_endpoint(method, url, headers=None, data=None, json_data=None, description=""):
    print(f"\n{'='*80}")
    print(f"TEST: {description}")
    print(f"URL: {method} {url}")
    if headers:
        print("HEADERS:")
        for k, v in headers.items():
            print(f"  {k}: {v}")
    if json_data:
        print("JSON DATA:")
        print(json.dumps(json_data, indent=2))
    if data:
        print("FORM DATA:")
        print(data)
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, params=data)
        elif method.upper() == 'POST':
            if json_data is not None:
                response = requests.post(url, headers=headers, json=json_data)
            else:
                response = requests.post(url, headers=headers, data=data)
        
        print(f"\nRESPONSE STATUS: {response.status_code}")
        print("RESPONSE HEADERS:")
        for k, v in response.headers.items():
            print(f"  {k}: {v}")
        
        print("\nRESPONSE BODY:")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)
            
        return response
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        return None

if __name__ == "__main__":
    base_url = "http://localhost:5000/casestrainer/api"
    
    # Test 1: Simple health check
    test_endpoint(
        "GET",
        f"{base_url}/health",
        description="Health check"
    )
    
    # Test 2: JSON request with json parameter
    test_endpoint(
        "POST",
        f"{base_url}/verify-citation",
        headers={"Content-Type": "application/json"},
        json_data={"text": "410 U.S. 113"},
        description="JSON request with json parameter"
    )
    
    # Test 3: JSON request with data parameter
    test_endpoint(
        "POST",
        f"{base_url}/verify-citation",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"text": "410 U.S. 113"}),
        description="JSON request with data parameter"
    )
    
    # Test 4: Form data
    test_endpoint(
        "POST",
        f"{base_url}/verify-citation",
        data={"text": "410 U.S. 113"},
        description="Form data request"
    )
    
    # Test 5: Minimal valid request
    test_endpoint(
        "POST",
        f"{base_url}/verify-citation",
        headers={"Content-Type": "application/json"},
        json_data={"citation": "410 U.S. 113", "case_name": "Roe v. Wade"},
        description="Minimal valid request"
    )
