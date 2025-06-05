import requests
import time

# Base URL for the API
BASE_URL = "https://wolf.law.uw.edu/casestrainer"


def test_simple_citations():
    """Test the tab structure with a simple set of citations."""
    print("\n=== TESTING SIMPLE CITATIONS ===")

    # Create a simple test with known citations
    test_text = """
    This is a test with citations to Supreme Court cases:
    
    Brown v. Board of Education, 347 U.S. 483 (1954)
    Roe v. Wade, 410 U.S. 113 (1973)
    Marbury v. Madison, 5 U.S. 137 (1803)
    Obergefell v. Hodges, 576 U.S. 644 (2015)
    Miranda v. Arizona, 384 U.S. 436 (1966)
    
    And some circuit court cases:
    Smith v. Jones, 123 F.3d 456 (9th Cir. 1999)
    United States v. Johnson, 456 F.3d 789 (2d Cir. 2006)
    
    And some district court cases:
    Jones v. Smith, 123 F. Supp. 2d 456 (S.D.N.Y. 2001)
    United States v. Doe, 456 F. Supp. 3d 789 (N.D. Cal. 2020)
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
        for i, citation in enumerate(citations):
            print(
                f"  {i+1}. {citation.get('citation_text', 'Unknown')} - {citation.get('case_name', 'Unknown')}"
            )
            if citation.get("url"):
                print(f"     URL: {citation.get('url')}")
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
        for i, citation in enumerate(citations):
            print(f"  {i+1}. {citation.get('citation_text', 'Unknown')}")
            print(f"     Source: {citation.get('source', 'Unknown')}")
    except Exception as e:
        print(f"Could not parse JSON response: {str(e)}")
        return False

    return True


if __name__ == "__main__":
    test_simple_citations()
