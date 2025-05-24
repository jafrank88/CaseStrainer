import requests
import json


def test_fetch_url():
    # Point this to your running Flask backend
    api_url = "http://127.0.0.1:5000/enhanced-validator/api/fetch_url"
    test_url = "https://www.courts.wa.gov/opinions/pdf/1026803.pdf"  # Use a real legal doc URL or any PDF
    resp = requests.post(api_url, json={"url": test_url})
    print(f"Status code: {resp.status_code}")
    try:
        data = resp.json()
        print("Response JSON:")
        print(json.dumps(data, indent=2))
        assert isinstance(data, dict), "Response should be a dict"
        assert "citations" in data, "Response should have 'citations' key"
        assert isinstance(data["citations"], list), "'citations' should be a list"
        print("Test passed: API returns consistent structure.")
    except Exception as e:
        print(f"Error parsing response: {e}")
        print(resp.text)


if __name__ == "__main__":
    test_fetch_url()
