import requests
import json
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time

# Configure session with retries and timeouts
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["POST", "GET"],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)


def make_request(method, url, **kwargs):
    """Helper function to make HTTP requests with timeouts and error handling"""
    try:
        start_time = time.time()
        response = session.request(method, url, timeout=30, **kwargs)
        response_time = time.time() - start_time

        print(f"\n{'='*80}")
        print(f"Request: {method} {url}")
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {response_time:.2f} seconds")

        try:
            print("Response:", json.dumps(response.json(), indent=2))
        except ValueError:
            print(
                "Response (non-JSON):", response.text[:500]
            )  # Print first 500 chars if not JSON

        return response

    except requests.exceptions.RequestException as e:
        print(f"\nError making request to {url}:")
        print(str(e))
        return None


def test_single_citation():
    """Test single citation verification"""
    url = "http://localhost:5000/casestrainer/api/verify_citation"
    data = {"citation": "347 U.S. 483"}  # Brown v. Board of Education
    return make_request("POST", url, json=data)


def test_paste_text():
    """Test paste text endpoint"""
    url = "http://localhost:5000/casestrainer/api/text"
    data = {
        "text": "In Brown v. Board of Education, 347 U.S. 483 (1954), the Supreme Court ruled that segregation was unconstitutional."
    }
    return make_request("POST", url, json=data)


def test_file_upload():
    """Test file upload endpoint"""
    url = "http://localhost:5000/casestrainer/api/upload"
    test_file = "test_files/test.pdf"

    if not os.path.exists(test_file):
        print(f"\nTest file not found: {test_file}")
        print("Skipping file upload test")
        return None

    try:
        with open(test_file, "rb") as f:
            files = {"file": (os.path.basename(test_file), f, "application/pdf")}
            return make_request("POST", url, files=files)
    except Exception as e:
        print(f"\nError reading test file: {e}")
        return None


def test_url_processing():
    """Test URL processing endpoint"""
    url = "http://localhost:5000/casestrainer/api/url"
    data = {"url": "https://en.wikipedia.org/wiki/Brown_v._Board_of_Education"}
    return make_request("POST", url, json=data)


def run_tests():
    """Run all test cases"""
    print("=" * 80)
    print("STARTING API TESTS")
    print("=" * 80)

    # Run tests
    test_single_citation()
    test_paste_text()
    test_file_upload()
    test_url_processing()

    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    run_tests()
