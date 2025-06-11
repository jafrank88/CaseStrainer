import requests
import json


def test_analyze_text():
    """Test the analyze endpoint with text input"""
    url = "http://localhost:5000/casestrainer/api/analyze"

    # Test data
    data = {
        "text": "This is a test citation: 123 F.3d 456. And another one: 987 F.2d 654.",
        "analysisType": "text",
    }

    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    print("=" * 80)
    print("TESTING ANALYZE ENDPOINT (TEXT INPUT)")
    print("=" * 80)
    print(f"URL: {url}")
    print("Method: POST")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print(f"Request data: {json.dumps(data, indent=2)}")
    print("-" * 80)

    try:
        # Send the request
        print("Sending request...")
        response = requests.post(url, json=data, headers=headers, timeout=30)

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

            # Print summary of citations found
            if "citations" in json_response:
                print(f"\nFound {len(json_response['citations'])} citations:")
                for i, citation in enumerate(json_response["citations"], 1):
                    print(
                        f"{i}. {citation.get('citation', 'N/A')} - {citation.get('case_name', 'N/A')}"
                    )

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

    print("=" * 80)


if __name__ == "__main__":
    test_analyze_text()
