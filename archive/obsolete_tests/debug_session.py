import requests
import json
import time

# Base URL for the API
BASE_URL = "https://wolf.law.uw.edu/casestrainer"


def debug_session_data():
    """Debug the session data to understand why CourtListener Gaps aren't showing."""
    print("\n=== DEBUGGING SESSION DATA ===")

    # First, let's submit a simple citation that should be recognized
    test_text = """
    Brown v. Board of Education, 347 U.S. 483 (1954)
    R v. Smith [2005] UKHL 12
    """

    # Submit the text
    print("Submitting test text...")
    response = requests.post(f"{BASE_URL}/api/analyze", data={"text": test_text})

    if response.status_code != 200:
        print(f"Error submitting text: {response.status_code} - {response.text}")
        return False

    print(f"Text submission successful: {response.status_code}")

    try:
        result = response.json()
        print(f"Analysis ID: {result.get('analysis_id')}")
        print(f"Citations found: {result.get('citations_count')}")
    except Exception as e:
        print(f"Could not parse JSON response: {str(e)}")
        return False

    # Give the server some time to process
    print("Waiting for processing to complete...")
    time.sleep(5)

    # Check all three tabs to see what data is available
    print("\n--- Checking Verified Citations Tab ---")
    response = requests.get(f"{BASE_URL}/api/confirmed_with_multitool_data")
    if response.status_code == 200:
        try:
            result = response.json()
            citations = result.get("citations", [])
            print(f"Found {len(citations)} verified citations")
            for i, citation in enumerate(citations[:5]):
                print(
                    f"  {i+1}. {citation.get('citation_text', 'Unknown')} - {citation.get('case_name', 'Unknown')}"
                )
                print(f"     Source: {citation.get('source', 'Unknown')}")
        except Exception as e:
            print(f"Could not parse JSON response: {str(e)}")
    else:
        print(
            f"Error getting verified citations: {response.status_code} - {response.text}"
        )

    print("\n--- Checking Unconfirmed Citations Tab ---")
    response = requests.get(f"{BASE_URL}/api/unconfirmed_citations_data")
    if response.status_code == 200:
        try:
            result = response.json()
            citations = result.get("citations", [])
            print(f"Found {len(citations)} unconfirmed citations")
            for i, citation in enumerate(citations[:5]):
                print(f"  {i+1}. {citation.get('citation_text', 'Unknown')}")
                print(f"     Source: {citation.get('source', 'Unknown')}")
        except Exception as e:
            print(f"Could not parse JSON response: {str(e)}")
    else:
        print(
            f"Error getting unconfirmed citations: {response.status_code} - {response.text}"
        )

    print("\n--- Checking CourtListener Gaps Tab ---")
    response = requests.get(f"{BASE_URL}/api/courtlistener_gaps")
    if response.status_code == 200:
        try:
            result = response.json()
            citations = result.get("citations", [])
            print(f"Found {len(citations)} CourtListener gaps")
            for i, citation in enumerate(citations[:5]):
                print(f"  {i+1}. {citation.get('citation_text', 'Unknown')}")
                print(f"     Source: {citation.get('source', 'Unknown')}")
        except Exception as e:
            print(f"Could not parse JSON response: {str(e)}")
    else:
        print(
            f"Error getting CourtListener gaps: {response.status_code} - {response.text}"
        )

    # Check the raw session data if possible
    print("\n--- Checking Raw Session Data ---")
    response = requests.get(f"{BASE_URL}/api/debug_session")
    if response.status_code == 200:
        try:
            result = response.json()
            print("Session data retrieved successfully")
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Could not parse JSON response: {str(e)}")
    else:
        print(f"Error getting session data: {response.status_code} - {response.text}")

    return True


if __name__ == "__main__":
    debug_session_data()
