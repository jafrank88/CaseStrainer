import requests
import json
from pathlib import Path


def load_config():
    """Load configuration from config.json"""
    try:
        config_path = Path(__file__).parent / "config.json"
        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # If config.json doesn't exist, return default config
        return {"BASE_URL": "http://localhost:5000"}
    except Exception as e:
        print(f"Error loading config.json: {e}")
        return {"BASE_URL": "http://localhost:5000"}


def test_citation():
    """Test the citation verification endpoint"""
    # Get the base URL from config or use default
    config = load_config()
    base_url = config.get("BASE_URL", "http://localhost:5000")

    # The citation to test
    citation = "123 F.3d 456"

    # Prepare the request
    url = f"{base_url}/casestrainer/api/verify-citation"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "CaseStrainer-Test/1.0",
    }
    data = {"citation": citation}

    print("=" * 50)
    print("TESTING CITATION VERIFICATION ENDPOINT")
    print("=" * 50)
    print(f"Target URL: {url}")
    print(f"Citation: {citation}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print(f"Request data: {json.dumps(data, indent=2)}")
    print("-" * 50)

    try:
        # Send the request with a timeout
        print("Sending request...")
        response = requests.post(url, json=data, headers=headers, timeout=30)

        # Print response details
        print("\nRESPONSE RECEIVED")
        print("-" * 50)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")

        # Try to parse JSON response
        try:
            json_response = response.json()
            print("Response Body (JSON):")
            print(json.dumps(json_response, indent=2))
        except ValueError:
            print(f"Response Body (raw):\n{response.text}")

        # Check for HTTP errors
        response.raise_for_status()

        print("\nTEST COMPLETED SUCCESSFULLY")

    except requests.exceptions.Timeout:
        print("\nERROR: Request timed out (30 seconds)")
    except requests.exceptions.TooManyRedirects:
        print("\nERROR: Too many redirects")
    except requests.exceptions.RequestException as e:
        print(f"\nERROR: Request failed: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            try:
                print(f"Response body: {e.response.json()}")
            except:
                print(f"Response text: {e.response.text}")
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        import traceback

        traceback.print_exc()

    print("=" * 50)


if __name__ == "__main__":
    test_citation()
