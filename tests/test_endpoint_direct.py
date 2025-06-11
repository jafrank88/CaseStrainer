import requests
import json
import sys
from datetime import datetime

def print_divider():
    print("\n" + "="*80 + "\n")

def test_endpoint():
    """Test the API endpoint directly with detailed output"""
    base_url = "http://localhost:5000/casestrainer/api"
    endpoint = "/verify-citation"
    url = f"{base_url}{endpoint}"
    
    # Test cases
    test_cases = [
        {"citation": "410 U.S. 113", "case_name": "Roe v. Wade"},
        {"citation": "347 U.S. 483", "case_name": "Brown v. Board of Education"},
        {"citation": "5 U.S. 137", "case_name": "Marbury v. Madison"},
    ]
    
    # Common headers
    json_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "CaseStrainer-Test/1.0",
    }
    
    # Test 1: Check health endpoint first
    print("[TEST 1] Checking health endpoint...")
    try:
        health_url = f"{base_url}/health"
        print(f"GET {health_url}")
        response = requests.get(health_url, timeout=5)
        print(f"Status: {response.status_code}")
        print("Response:", json.dumps(response.json(), indent=2))
        print("✅ Health check passed")
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return
    
    # Test 2: Test JSON endpoint
    print("\n[TEST 2] Testing JSON endpoint...")
    for i, test_case in enumerate(test_cases, 1):
        print_divider()
        print(f"TEST CASE {i}: {test_case['citation']} ({test_case['case_name']})")
        
        # Print request details
        print(f"\nPOST {url}")
        print("Headers:", json.dumps(json_headers, indent=2))
        print("Body:", json.dumps(test_case, indent=2))
        
        try:
            # Make the request
            response = requests.post(
                url,
                headers=json_headers,
                json=test_case,
                timeout=10
            )
            
            # Print response details
            print(f"\nStatus: {response.status_code}")
            print("Response Headers:")
            for k, v in response.headers.items():
                if k.lower() in ['content-type', 'content-length']:
                    print(f"  {k}: {v}")
            
            # Try to parse JSON response
            try:
                response_json = response.json()
                print("\nResponse Body:")
                print(json.dumps(response_json, indent=2))
                
                # Check if verification was successful
                if response.status_code == 200 and response_json.get('verified', False):
                    print("✅ Verification successful!")
                else:
                    print(f"❌ Verification failed. Status: {response.status_code}")
                    if 'error' in response_json:
                        print(f"Error: {response_json['error']}")
                        
            except ValueError:
                print(f"\nCould not parse JSON response. Raw response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Request failed: {str(e)}")
        except Exception as e:
            print(f"\n❌ Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()
    print("=" * 80)

if __name__ == "__main__":
    print(f"\n{'='*40} Starting Test at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {'='*40}")
    try:
        test_endpoint()
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
    print(f"\n{'='*40} Test Completed {'='*40}")
    
    # Add a small delay to keep the window open if run directly
    if sys.platform == "win32":
        import time
        time.sleep(2)
