import requests
import time

# Base URL for the API
BASE_URL = "https://wolf.law.uw.edu/casestrainer"


def test_avianca_with_eyecite():
    """Test analyzing the Avianca sanctions opinion PDF URL with eyecite integration."""
    print("\n=== TESTING AVIANCA SANCTIONS OPINION WITH EYECITE ===")

    # URL to test
    test_url = "https://www.gibbonslawalert.com/wp-content/uploads/2023/07/Mata-v.-Avianca-Sanctions-opinion.pdf"

    # Submit the URL
    print(f"Submitting URL: {test_url}")
    try:
        response = requests.post(
            f"{BASE_URL}/api/fetch_url", json={"url": test_url}, timeout=120
        )

        if response.status_code != 200:
            print(f"Error fetching URL: {response.status_code} - {response.text}")
            return False

        print(f"URL fetch response status: {response.status_code}")

        try:
            result = response.json()
            print(f"URL fetch result status: {result.get('status')}")

            if result.get("status") == "success" and result.get("text"):
                text_length = len(result.get("text"))
                print(
                    f"Successfully extracted text from URL ({text_length} characters)"
                )

                # No need to analyze the text separately as eyecite should have already processed it
                print("Eyecite should have already processed the citations")
            else:
                print(f"Error in URL fetch response: {result.get('message')}")
                return False
        except Exception as e:
            print(f"Could not parse JSON response for URL fetch: {str(e)}")
            return False
    except Exception as e:
        print(f"Exception while fetching URL: {str(e)}")
        return False

    # Give the server some time to process
    print("\nWaiting for processing to complete...")
    time.sleep(10)

    # Check all tabs
    print("\n--- Checking CourtListener Citations Tab ---")
    check_courtlistener_citations()

    print("\n--- Checking Verified Citations Tab ---")
    check_verified_citations()

    print("\n--- Checking Unconfirmed Citations Tab ---")
    check_unconfirmed_citations()

    print("\n--- Checking CourtListener Gaps Tab ---")
    check_courtlistener_gaps()

    print("\n--- Checking Eyecite Citations ---")
    check_eyecite_citations()

    return True


def check_courtlistener_citations():
    """Check the CourtListener Citations tab."""
    response = requests.get(f"{BASE_URL}/api/courtlistener_citations")

    if response.status_code != 200:
        print(
            f"Error getting CourtListener citations: {response.status_code} - {response.text}"
        )
        return False

    try:
        result = response.json()
        citations = result.get("citations", [])
        print(f"Found {len(citations)} CourtListener citations")

        # Print all citations
        for i, citation in enumerate(citations[:10]):
            print(
                f"  {i+1}. {citation.get('citation_text', 'Unknown')} - {citation.get('case_name', 'Unknown')}"
            )
            if citation.get("url"):
                print(f"     URL: {citation.get('url')}")

        if len(citations) > 10:
            print(f"  ... and {len(citations) - 10} more")
    except Exception as e:
        print(f"Could not parse JSON response: {str(e)}")
        return False

    return True


def check_verified_citations():
    """Check the Verified Citations tab."""
    response = requests.get(f"{BASE_URL}/api/confirmed_with_multitool_data")

    if response.status_code != 200:
        print(
            f"Error getting verified citations: {response.status_code} - {response.text}"
        )
        return False

    try:
        result = response.json()
        citations = result.get("citations", [])
        print(f"Found {len(citations)} verified citations")

        # Print first few citations
        for i, citation in enumerate(citations[:10]):
            print(
                f"  {i+1}. {citation.get('citation_text', 'Unknown')} - {citation.get('case_name', 'Unknown')}"
            )
            print(f"     Source: {citation.get('source', 'Unknown')}")

        if len(citations) > 10:
            print(f"  ... and {len(citations) - 10} more")
    except Exception as e:
        print(f"Could not parse JSON response: {str(e)}")
        return False

    return True


def check_unconfirmed_citations():
    """Check the Unconfirmed Citations tab."""
    response = requests.get(f"{BASE_URL}/api/unconfirmed_citations_data")

    if response.status_code != 200:
        print(
            f"Error getting unconfirmed citations: {response.status_code} - {response.text}"
        )
        return False

    try:
        result = response.json()
        citations = result.get("citations", [])
        print(f"Found {len(citations)} unconfirmed citations")

        # Print first few citations
        for i, citation in enumerate(citations[:10]):
            print(f"  {i+1}. {citation.get('citation_text', 'Unknown')}")
            print(f"     Source: {citation.get('source', 'Unknown')}")

        if len(citations) > 10:
            print(f"  ... and {len(citations) - 10} more")
    except Exception as e:
        print(f"Could not parse JSON response: {str(e)}")
        return False

    return True


def check_courtlistener_gaps():
    """Check the CourtListener Gaps tab."""
    response = requests.get(f"{BASE_URL}/api/courtlistener_gaps")

    if response.status_code != 200:
        print(
            f"Error getting CourtListener gaps: {response.status_code} - {response.text}"
        )
        return False

    try:
        result = response.json()
        citations = result.get("citations", [])
        print(f"Found {len(citations)} CourtListener gaps")

        # Print all citations
        for i, citation in enumerate(citations[:10]):
            print(f"  {i+1}. {citation.get('citation_text', 'Unknown')}")
            print(f"     Source: {citation.get('source', 'Unknown')}")

        if len(citations) > 10:
            print(f"  ... and {len(citations) - 10} more")
    except Exception as e:
        print(f"Could not parse JSON response: {str(e)}")
        return False

    return True


def check_eyecite_citations():
    """Check if eyecite citations are present in the session."""
    response = requests.get(f"{BASE_URL}/api/debug_session")

    if response.status_code != 200:
        print(f"Error getting session data: {response.status_code} - {response.text}")
        return False

    try:
        result = response.json()
        user_citations = result.get("session_data", {}).get("user_citations", [])
        eyecite_citations = [c for c in user_citations if c.get("source") == "Eyecite"]
        print(f"Found {len(eyecite_citations)} eyecite citations in session")

        # Print first few citations
        for i, citation in enumerate(eyecite_citations[:10]):
            print(
                f"  {i+1}. {citation.get('citation', 'Unknown')} - {citation.get('found_case_name', 'Unknown')}"
            )

        if len(eyecite_citations) > 10:
            print(f"  ... and {len(eyecite_citations) - 10} more")
    except Exception as e:
        print(f"Could not parse JSON response: {str(e)}")
        return False

    return True


if __name__ == "__main__":
    test_avianca_with_eyecite()
