import requests
import json
import sys


def test_endpoint():
    """Test the API endpoint directly with detailed output"""
    url = "http://localhost:5000/casestrainer/api/verify-citation"

    # Test citation
    citation = "123 F.3d 456"

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "CaseStrainer-Test/1.0",
    }

    data = {"citation": citation}

    print("=" * 80)
    print("TESTING CITATION VERIFICATION ENDPOINT")
    print("=" * 80)
    print(f"URL: {url}")
    print(f"Method: POST")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print(f"Request data: {json.dumps(data, indent=2)}")
    print("-" * 80)

    try:
        # Send the request
        print("Sending request...")
        response = requests.post(
            url,
            json=data,
            headers=headers,
            timeout=10,
            verify=False,  # Disable SSL verification for testing
        )

        # Print response details
        print("\nRESPONSE RECEIVED")
        print("-" * 80)
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
        print("\nERROR: Request timed out (10 seconds)")
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

    print("=" * 80)


if __name__ == "__main__":
    test_endpoint()
