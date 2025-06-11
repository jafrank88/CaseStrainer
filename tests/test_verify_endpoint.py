import requests
import json
import time

def test_verify_citation(test_cases):
    base_url = "http://localhost:5000/casestrainer/api/verify-citation"
    headers = {"Content-Type": "application/json"}
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"TEST CASE {i}: {test_case.get('name', 'Unnamed test')}")
        print(f"{'='*80}")
        
        try:
            # Print test case details
            print(f"\nSending request to: {base_url}")
            print(f"Headers: {headers}")
            print(f"Data: {json.dumps(test_case['data'], indent=2)}")
            
            # Send the request
            start_time = time.time()
            response = requests.post(
                base_url, 
                headers=headers, 
                json=test_case['data'], 
                timeout=10
            )
            elapsed = (time.time() - start_time) * 1000  # in milliseconds
            
            # Print response details
            print(f"\nResponse received in {elapsed:.2f}ms:")
            print(f"Status Code: {response.status_code}")
            
            # Print response body with pretty formatting
            try:
                response_json = response.json()
                print("\nResponse Body:")
                print(json.dumps(response_json, indent=2))
                
                # Print specific fields for easier reading
                if 'citation' in response_json:
                    print(f"\nCitation: {response_json['citation']}")
                if 'verified' in response_json:
                    print(f"Verified: {response_json['verified']}")
                if 'verified_by' in response_json:
                    print(f"Verified by: {response_json['verified_by']}")
                if 'error' in response_json and response_json['error']:
                    print(f"Error: {response_json['error']}")
                if 'metadata' in response_json and response_json['metadata']:
                    print(f"Metadata: {json.dumps(response_json['metadata'], indent=2)}")
                    
            except ValueError:
                print("\nResponse (raw):")
                print(response.text)
            
        except requests.exceptions.RequestException as e:
            print(f"\nRequest failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status Code: {e.response.status_code}")
                print("Response:", e.response.text)
        except Exception as e:
            print(f"\nUnexpected error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_cases = [
        {
            "name": "Basic citation with case name",
            "data": {
                "citation": "410 U.S. 113",
                "case_name": "Roe v. Wade"
            }
        },
        {
            "name": "Citation without case name",
            "data": {
                "citation": "347 U.S. 483"
            }
        },
        {
            "name": "Invalid citation format",
            "data": {
                "citation": "Not a real citation 123",
                "case_name": "Test Case"
            }
        },
        {
            "name": "Empty citation",
            "data": {
                "citation": "",
                "case_name": "Empty Test"
            }
        }
    ]
    
    test_verify_citation(test_cases)
