import requests
import json
from datetime import datetime

def print_divider():
    print("\n" + "="*80 + "\n")

def test_verify_citation():
    base_url = "http://localhost:5000/casestrainer/api"
    
    # Test 1: Test health check endpoint first
    print("\n[TEST 1] Testing health check endpoint...")
    try:
        health_url = f"{base_url}/health"
        print(f"GET {health_url}")
        response = requests.get(health_url, timeout=5)
        print(f"Status: {response.status_code}")
        print("Response:", json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Health check failed: {str(e)}")
        return

    # Prepare test cases
    test_cases = [
        {"citation": "410 U.S. 113", "case_name": "Roe v. Wade"},
        {"citation": "347 U.S. 483", "case_name": "Brown v. Board of Education"},
        {"citation": "5 U.S. 137", "case_name": "Marbury v. Madison"},
    ]

    # Test 2: Test verify-citation endpoint with JSON
    print("\n[TEST 2] Testing verify-citation endpoint with JSON payload...")
    json_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    for i, test_case in enumerate(test_cases, 1):
        print_divider()
        print(f"TEST CASE {i}: {test_case['citation']} ({test_case['case_name']})")
        
        url = f"{base_url}/verify-citation"
        print(f"\nPOST {url}")
        print(f"Headers: {json_headers}")
        print(f"Payload: {json.dumps(test_case, indent=2)}")
        
        try:
            response = requests.post(
                url, 
                headers=json_headers, 
                json=test_case, 
                timeout=10
            )
            
            print(f"\nStatus: {response.status_code}")
            print("Response Headers:")
            for k, v in response.headers.items():
                if k.lower() in ['content-type', 'content-length']:
                    print(f"  {k}: {v}")
            
            try:
                response_json = response.json()
                print("\nResponse Body:")
                print(json.dumps(response_json, indent=2))
                
                # Check if the response indicates success
                if response.status_code == 200 and response_json.get('verified', False):
                    print("✅ Verification successful!")
                else:
                    print(f"❌ Verification failed. Status: {response.status_code}")
                    if 'error' in response_json:
                        print(f"Error: {response_json['error']}")
                        
            except ValueError:
                print(f"\nResponse (raw): {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {str(e)}")
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()

    # Test 3: Test with form data
    print("\n[TEST 3] Testing with form data...")
    form_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    for i, test_case in enumerate(test_cases, 1):
        print_divider()
        print(f"TEST CASE {i}: Form data - {test_case['citation']}")
        
        form_data = f"citation={test_case['citation']}&case_name={test_case['case_name']}"
        
        print(f"\nPOST {url}")
        print(f"Headers: {form_headers}")
        print(f"Form Data: {form_data}")
        
        try:
            response = requests.post(
                url, 
                headers=form_headers, 
                data=form_data, 
                timeout=10
            )
            
            print(f"\nStatus: {response.status_code}")
            print("Response Headers:")
            for k, v in response.headers.items():
                if k.lower() in ['content-type', 'content-length']:
                    print(f"  {k}: {v}")
            
            try:
                response_json = response.json()
                print("\nResponse Body:")
                print(json.dumps(response_json, indent=2))
                
                if response.status_code == 200 and response_json.get('verified', False):
                    print("✅ Form data verification successful!")
                else:
                    print(f"❌ Form data verification failed. Status: {response.status_code}")
                    if 'error' in response_json:
                        print(f"Error: {response_json['error']}")
                        
            except ValueError:
                print(f"\nResponse (raw): {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Form data request failed: {str(e)}")
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("=== Starting Citation Verification Tests ===")
    print(f"Test started at: {datetime.now().isoformat()}")
    test_verify_citation()
    print("\n=== Test completed ===")
