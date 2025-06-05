import requests
import time

# Base URL for the API
BASE_URL = "https://wolf.law.uw.edu/casestrainer"


def test_comprehensive_document():
    """Test analyzing a comprehensive document with citations that should trigger CourtListener Gaps."""
    print("\n=== TESTING COMPREHENSIVE DOCUMENT FOR COURTLISTENER GAPS ===")

    # Path to the specific gaps test document
    test_file_path = "specific_gaps_test.txt"

    # Upload the file
    print("Uploading comprehensive test document...")
    with open(test_file_path, "rb") as f:
        files = {"file": f}
        response = requests.post(f"{BASE_URL}/api/analyze", files=files)

    if response.status_code != 200:
        print(f"Error uploading file: {response.status_code} - {response.text}")
        return False

    print(f"File upload successful: {response.status_code}")

    try:
        result = response.json()
        print(f"Analysis ID: {result.get('analysis_id')}")
        print(f"Citations found: {result.get('citations_count')}")
    except Exception as e:
        print(f"Could not parse JSON response: {str(e)}")
        return False

    # Give the server some time to process
    print("Waiting for processing to complete...")
    time.sleep(10)  # Longer wait time for the comprehensive document

    # Test the CourtListener Gaps tab
    test_courtlistener_gaps()

    return True


def test_courtlistener_gaps():
    """Test the CourtListener Gaps tab."""
    print("\n--- Testing CourtListener Gaps Tab ---")

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

        # Print all citations in the CourtListener Gaps tab
        for i, citation in enumerate(citations):
            print(f"  {i+1}. {citation.get('citation_text', 'Unknown')}")

        if len(citations) == 0:
            print(
                "No CourtListener gaps found. This might indicate an issue if you expected gaps."
            )
    except Exception as e:
        print(f"Could not parse JSON response: {str(e)}")
        return False

    return True


if __name__ == "__main__":
    test_comprehensive_document()
