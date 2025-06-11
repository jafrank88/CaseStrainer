import requests
import json


def test_enhanced_validation(citation):
    url = "http://localhost:5000/api/enhanced-validate-citation"
    headers = {"Content-Type": "application/json"}
    data = {"citation": citation}

    print(f"\nTesting citation: {citation}")
    print("Sending request to:", url)

    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        print("Status Code:", response.status_code)

        try:
            result = response.json()
            print("Response:")
            print(json.dumps(result, indent=2))

            if "verified" in result:
                print(
                    f"\nVerification Result: {'VERIFIED' if result['verified'] else 'NOT VERIFIED'}"
                )
                if "verified_by" in result:
                    print(f"Verified by: {result['verified_by']}")

                if "components" in result:
                    print("\nCitation Components:")
                    for key, value in result["components"].items():
                        if value:  # Only print non-empty values
                            print(f"  {key}: {value}")

            if "error" in result:
                print(f"\nError: {result['error']}")

        except json.JSONDecodeError:
            print("Failed to decode JSON response")
            print("Raw response:", response.text)

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

    print("-" * 80)


if __name__ == "__main__":
    # Test with the citation that was having issues
    test_enhanced_validation("534 F.3d 1290")

    # Test with a known valid citation
    test_enhanced_validation("347 U.S. 483")  # Brown v. Board of Education

    # Test with an invalid citation
    test_enhanced_validation("999 F.999 99999")
