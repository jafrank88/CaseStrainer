import requests
from pprint import pprint


def test_citation_verification(citation):
    url = "http://localhost:5000/api/enhanced-validate-citation"
    headers = {"Content-Type": "application/json"}
    data = {"citation": citation}

    print(f"\n{'='*80}")
    print(f"Testing citation: {citation}")
    print(f"Sending request to: {url}")

    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        print(f"\nStatus Code: {response.status_code}")

        try:
            json_response = response.json()
            print("\nResponse JSON:")
            pprint(json_response, indent=2, width=100)

            # Print important fields
            print("\nKey Information:")
            print(f"Verified: {json_response.get('verified', 'N/A')}")
            print(f"Verified By: {json_response.get('verified_by', 'N/A')}")

            if "components" in json_response:
                print("\nCitation Components:")
                for key, value in json_response["components"].items():
                    if value:  # Only print non-empty values
                        print(f"  {key}: {value}")

            if "error" in json_response:
                print(f"\nError: {json_response['error']}")

        except ValueError as e:
            print(f"\nError parsing JSON response: {e}")
            print(f"Raw response: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"\nRequest failed: {e}")

    print("=" * 80)


if __name__ == "__main__":
    # Test with the citation that was having issues
    test_citation_verification("534 F.3d 1290")

    # Test with a few other citations to verify different scenarios
    test_citation_verification("410 U.S. 113")  # Roe v. Wade
    test_citation_verification("347 U.S. 483")  # Brown v. Board of Ed
