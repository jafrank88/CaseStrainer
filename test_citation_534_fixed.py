import json
import requests
from urllib.parse import urljoin


def test_citation(citation_text):
    """Test the citation verification endpoint with the given citation."""
    base_url = "http://localhost:5000/casestrainer/api"
    endpoint = "/verify_citation"
    url = urljoin(base_url, endpoint)

    print(f"Testing citation: {citation_text}")
    print(f"URL: {url}")

    try:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        data = {"citation": citation_text, "case_name": None}  # Optional

        print("Sending request...")
        response = requests.post(url, json=data, headers=headers, timeout=30)
        print(f"Status code: {response.status_code}")

        try:
            result = response.json()
            print("Response JSON:")
            print(json.dumps(result, indent=2))
            return result
        except ValueError as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Raw response: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


if __name__ == "__main__":
    # Test with the specific citation
    test_citation("534 F.3d 1290")

    # Test with a known working citation for comparison
    print("\nTesting with a known working citation for comparison...")
    test_citation("347 U.S. 483")
