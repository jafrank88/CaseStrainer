import requests

# Test direct connection to backend container
try:
    response = requests.post("http://localhost:5000/casestrainer/api/analyze", 
                           json={"text": "Smith v. Jones, 123 U.S. 456 (2020).", 
                                 "enable_verification": False,
                                 "client_request_id": "test_direct"},
                           timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
