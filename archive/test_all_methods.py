import requests
import json
import time
import os
from bs4 import BeautifulSoup

# Base URL for the API
BASE_URL = "https://wolf.law.uw.edu/casestrainer"


def test_file_upload():
    """Test uploading a file and checking all three output tabs."""
    print("\n=== TESTING FILE UPLOAD ===")

    # Create a simple test file with citations
    test_file_path = "test_citations.txt"
    with open(test_file_path, "w") as f:
        f.write("This is a test file with some citations:\n")
        f.write("Brown v. Board of Education, 347 U.S. 483 (1954)\n")
        f.write("Roe v. Wade, 410 U.S. 113 (1973)\n")
        f.write("Marbury v. Madison, 5 U.S. 137 (1803)\n")
        f.write(
            "Some unverified citation: Smith v. Jones, 123 F.3d 456 (9th Cir. 1999)\n"
        )

    # Upload the file
    print("Uploading test file...")
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
    except:
        print("Could not parse JSON response")

    # Give the server some time to process
    print("Waiting for processing to complete...")
    time.sleep(5)

    # Test all three output tabs
    test_verified_citations()
    test_unconfirmed_citations()
    test_courtlistener_gaps()

    # Clean up
    if os.path.exists(test_file_path):
        os.remove(test_file_path)

    return True


def test_text_paste():
    """Test pasting text and checking all three output tabs."""
    print("\n=== TESTING TEXT PASTE ===")

    # Create test text with citations
    test_text = """This is a test with some citations:
    Brown v. Board of Education, 347 U.S. 483 (1954)
    Roe v. Wade, 410 U.S. 113 (1973)
    Marbury v. Madison, 5 U.S. 137 (1803)
    Some unverified citation: Smith v. Jones, 123 F.3d 456 (9th Cir. 1999)"""

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
    except:
        print("Could not parse JSON response")

    # Give the server some time to process
    print("Waiting for processing to complete...")
    time.sleep(5)

    # Test all three output tabs
    test_verified_citations()
    test_unconfirmed_citations()
    test_courtlistener_gaps()

    return True


def test_url_input():
    """Test URL input and checking all three output tabs."""
    print("\n=== TESTING URL INPUT ===")

    # Use a simpler URL with known citations
    test_url = "https://supreme.justia.com/cases/federal/us/347/483/"

    # Submit the URL
    print(f"Submitting URL: {test_url}")
    try:
        response = requests.post(
            f"{BASE_URL}/api/fetch_url", json={"url": test_url}, timeout=30
        )

        if response.status_code != 200:
            print(f"Error fetching URL: {response.status_code} - {response.text}")
            return False

        print(f"URL fetch successful: {response.status_code}")

        try:
            result = response.json()
            if result.get("status") == "success" and result.get("text"):
                print(
                    f"Successfully extracted text from URL ({len(result.get('text'))} characters)"
                )

                # Now analyze the text
                response = requests.post(
                    f"{BASE_URL}/api/analyze", data={"text": result.get("text")}
                )

                if response.status_code != 200:
                    print(
                        f"Error analyzing URL text: {response.status_code} - {response.text}"
                    )
                    return False

                print(f"URL text analysis successful: {response.status_code}")

                try:
                    analysis_result = response.json()
                    print(f"Analysis ID: {analysis_result.get('analysis_id')}")
                    print(f"Citations found: {analysis_result.get('citations_count')}")
                except Exception as e:
                    print(f"Could not parse JSON response for analysis: {str(e)}")
                    return False
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
    print("Waiting for processing to complete...")
    time.sleep(5)

    # Test all three output tabs
    test_verified_citations()
    test_unconfirmed_citations()
    test_courtlistener_gaps()

    return True


def test_verified_citations():
    """Test the Verified Citations tab."""
    print("\n--- Testing Verified Citations Tab ---")

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
        for i, citation in enumerate(citations[:3]):
            print(
                f"  {i+1}. {citation.get('citation_text', 'Unknown')} - {citation.get('case_name', 'Unknown')}"
            )

        if len(citations) > 3:
            print(f"  ... and {len(citations) - 3} more")
    except:
        print("Could not parse JSON response")
        return False

    return True


def test_unconfirmed_citations():
    """Test the Unconfirmed Citations tab."""
    print("\n--- Testing Unconfirmed Citations Tab ---")

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
        for i, citation in enumerate(citations[:3]):
            print(f"  {i+1}. {citation.get('citation_text', 'Unknown')}")

        if len(citations) > 3:
            print(f"  ... and {len(citations) - 3} more")
    except:
        print("Could not parse JSON response")
        return False

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

        # Print first few citations
        for i, citation in enumerate(citations[:3]):
            print(f"  {i+1}. {citation.get('citation_text', 'Unknown')}")

        if len(citations) > 3:
            print(f"  ... and {len(citations) - 3} more")
    except:
        print("Could not parse JSON response")
        return False

    return True


def run_all_tests():
    """Run all tests for all input methods and output tabs."""
    print("=== STARTING COMPREHENSIVE TESTING ===")
    print("Testing all 3 input methods with all 3 output tabs (9 combinations)")

    # Test file upload
    file_success = test_file_upload()

    # Test text paste
    text_success = test_text_paste()

    # Test URL input
    url_success = test_url_input()

    # Summary
    print("\n=== TEST SUMMARY ===")
    print(f"File Upload: {'SUCCESS' if file_success else 'FAILED'}")
    print(f"Text Paste: {'SUCCESS' if text_success else 'FAILED'}")
    print(f"URL Input: {'SUCCESS' if url_success else 'FAILED'}")

    if file_success and text_success and url_success:
        print("\nAll tests PASSED!")
    else:
        print("\nSome tests FAILED!")


if __name__ == "__main__":
    run_all_tests()
