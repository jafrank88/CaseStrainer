import requests
import json

def test_verify_citation():
    url = "http://localhost:5000/casestrainer/api/verify-citation"
    headers = {"Content-Type": "application/json"}
    data = {"citation": "410 U.S. 113", "case_name": "Roe v. Wade"}
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_verify_citation()
