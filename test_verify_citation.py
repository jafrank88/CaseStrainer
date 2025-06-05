import requests
import json


def test_verify_citation():
    url = "http://localhost:5000/casestrainer/api/verify-citation"
    headers = {"Content-Type": "application/json"}

    test_cases = [
        {"citation": "410 U.S. 113", "case_name": "Roe v. Wade"},
        {"citation": "347 U.S. 483", "case_name": "Brown v. Board of Education"},
        {"citation": "5 U.S. 137", "case_name": "Marbury v. Madison"},
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n=== Test Case {i}: {test_case['citation']} ===")
        print(f"Testing citation: {test_case['citation']} ({test_case['case_name']})")

        try:
            response = requests.post(url, headers=headers, json=test_case, timeout=10)
            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print("Response:")
                print(json.dumps(result, indent=2))

                if result.get("verified"):
                    print(f"✅ Successfully verified citation: {test_case['citation']}")
                else:
                    print(f"❌ Failed to verify citation: {test_case['citation']}")
                    if "error" in result and result["error"]:
                        print(f"Error: {result['error']}")
            else:
                print(f"❌ Error: Received status code {response.status_code}")
                try:
                    error_data = response.json()
                    print(json.dumps(error_data, indent=2))
                except (ValueError, requests.exceptions.JSONDecodeError):
                    print(f"Response: {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {str(e)}")
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response: {str(e)}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    print("=== Starting Citation Verification Tests ===")
    test_verify_citation()
    print("\n=== Test Execution Complete ===")
