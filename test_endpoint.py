import requests
import json

def test_analyze_endpoint():
    """Test the analyze endpoint with a simple citation."""
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {
        "type": "citation",
        "citation": "410 U.S. 113 (1973)"
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_analyze_endpoint() 