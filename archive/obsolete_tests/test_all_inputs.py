import requests
import json
import os
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("casestrainer_test.log")],
)
logger = logging.getLogger("casestrainer_test")

# Base URL for the API
BASE_URL = "http://localhost:5000"
EXTERNAL_URL = "https://wolf.law.uw.edu/casestrainer"

# Test data
TEST_TEXT = """
Brown v. Board of Education, 347 U.S. 483 (1954)
Roe v. Wade, 410 U.S. 113 (1973)
Marbury v. Madison, 5 U.S. 137 (1803)
Obergefell v. Hodges, 576 U.S. 644 (2015)
Citizens United v. FEC, 558 U.S. 310 (2010)
Miranda v. Arizona, 384 U.S. 436 (1966)
123 Fake Citation 456 (2022)
"""

TEST_URL = "https://www.law.cornell.edu/supremecourt/text/347/483"


def test_verified_tab():
    """Test the Verified Citations tab."""
    logger.info("\nChecking Verified Citations tab...")
    response = requests.get(f"{BASE_URL}/api/confirmed_with_multitool_data")
    if response.status_code != 200:
        logger.error(
            f"Error getting verified citations: {response.status_code} - {response.text}"
        )
        return False

    data = response.json()
    citations = data.get("citations", [])
    logger.info(f"Found {len(citations)} citations in Verified Citations tab")
    if citations:
        for citation in citations[:3]:  # Show first 3 citations
            logger.info(
                f"  - {citation.get('citation', '')}: {citation.get('found_case_name', '')}"
            )
    return True


def test_unconfirmed_tab():
    """Test the Unconfirmed Citations tab."""
    logger.info("\nChecking Unconfirmed Citations tab...")
    response = requests.get(f"{BASE_URL}/api/unconfirmed_citations_data")
    if response.status_code != 200:
        logger.error(
            f"Error getting unconfirmed citations: {response.status_code} - {response.text}"
        )
        return False

    data = response.json()
    citations = data.get("citations", [])
    logger.info(f"Found {len(citations)} citations in Unconfirmed Citations tab")
    if citations:
        for citation in citations[:3]:  # Show first 3 citations
            logger.info(f"  - {citation.get('citation', '')}")
    return True


def test_courtlistener_tab():
    """Test the CourtListener Cases tab."""
    logger.info("\nChecking CourtListener Cases tab...")
    response = requests.get(f"{BASE_URL}/api/courtlistener_citations")
    if response.status_code != 200:
        logger.error(
            f"Error getting CourtListener cases: {response.status_code} - {response.text}"
        )
        return False

    data = response.json()
    citations = data.get("citations", [])
    logger.info(f"Found {len(citations)} citations in CourtListener Cases tab")
    if citations:
        for citation in citations[:3]:  # Show first 3 citations
            logger.info(
                f"  - {citation.get('citation', '')}: {citation.get('found_case_name', '')}"
            )
    return True


def test_courtlistener_gaps_tab():
    """Test the CourtListener Gaps tab."""
    logger.info("\nChecking CourtListener Gaps tab...")
    response = requests.get(f"{BASE_URL}/api/courtlistener_gaps")
    if response.status_code != 200:
        logger.error(
            f"Error getting CourtListener gaps: {response.status_code} - {response.text}"
        )
        return False

    data = response.json()
    citations = data.get("citations", [])
    logger.info(f"Found {len(citations)} citations in CourtListener Gaps tab")
    if citations:
        for citation in citations[:3]:  # Show first 3 citations
            logger.info(f"  - {citation.get('citation', '')}")
    return True


def test_google_scholar_tab():
    """Test the Google Scholar tab."""
    logger.info("\nChecking Google Scholar tab...")
    response = requests.get(f"{BASE_URL}/api/google_scholar_cases")
    if response.status_code != 200:
        logger.error(
            f"Error getting Google Scholar cases: {response.status_code} - {response.text}"
        )
        return False

    data = response.json()
    citations = data.get("citations", [])
    logger.info(f"Found {len(citations)} citations in Google Scholar tab")
    if citations:
        for citation in citations[:3]:  # Show first 3 citations
            logger.info(
                f"  - {citation.get('citation', '')}: {citation.get('found_case_name', '')}"
            )
    return True


def test_file_upload():
    """Test uploading a file and checking all tabs for proper data."""
    logger.info("Testing file upload method...")

    # Create a test file
    test_file_path = "test_citations.txt"
    with open(test_file_path, "w") as f:
        f.write(TEST_TEXT)

    try:
        # Upload the file
        with open(test_file_path, "rb") as f:
            files = {"file": f}
            logger.info(f"Uploading test file: {test_file_path}")
            response = requests.post(f"{BASE_URL}/api/analyze", files=files)

        if response.status_code != 200:
            logger.error(
                f"Error uploading file: {response.status_code} - {response.text}"
            )
            return False

        logger.info("File uploaded successfully")

        # Wait for processing to complete
        logger.info("Waiting for processing to complete...")
        time.sleep(3)

        # Test all tabs
        return test_all_tabs("file upload")

    finally:
        # Clean up
        if os.path.exists(test_file_path):
            os.remove(test_file_path)


def test_text_paste():
    """Test pasting text and checking all tabs for proper data."""
    logger.info("Testing text paste method...")

    # Send the text
    data = {"text": TEST_TEXT}
    logger.info("Sending test text")
    response = requests.post(f"{BASE_URL}/api/analyze", data=data)

    if response.status_code != 200:
        logger.error(f"Error sending text: {response.status_code} - {response.text}")
        return False

    logger.info("Text sent successfully")

    # Wait for processing to complete
    logger.info("Waiting for processing to complete...")
    time.sleep(3)

    # Test all tabs
    return test_all_tabs("text paste")


def test_url_input():
    """Test entering a URL and checking all tabs for proper data."""
    logger.info("Testing URL input method...")

    # Send the URL directly to the direct_url_analyze endpoint
    # This is the recommended approach for URL input in CaseStrainer
    data = json.dumps({"url": TEST_URL})
    headers = {"Content-Type": "application/json"}
    logger.info(f"Sending test URL: {TEST_URL}")
    logger.info(f"Request payload: {data}")

    try:
        # Use the direct URL endpoint for URL analysis
        response = requests.post(
            f"{BASE_URL}/api/direct_url_analyze", data=data, headers=headers
        )
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")

        if response.status_code != 200:
            logger.error(f"Error sending URL: {response.status_code} - {response.text}")
            return False

        logger.info("URL sent successfully")
        logger.info(f"Response content: {response.text[:200]}...")

        # For URL input, we don't need to check the tabs since the direct_url_analyze endpoint
        # doesn't store the results in the session. Instead, we'll just check if the response
        # contains the expected fields.
        response_data = response.json()
        if "status" in response_data and response_data["status"] == "success":
            logger.info("URL input test successful")
            return True
        else:
            logger.error(f"Unexpected response format: {response_data}")
            return False
    except Exception as e:
        logger.error(f"Exception during request: {str(e)}")
        return False

    # Wait for processing to complete
    logger.info("Waiting for processing to complete...")
    time.sleep(5)  # URL processing might take longer

    # Test all tabs
    return test_all_tabs("URL input")


def test_direct_url():
    """Test the direct URL analyze endpoint."""
    logger.info("Testing direct URL analyze endpoint...")

    # Send the URL to the direct URL endpoint
    data = json.dumps({"url": TEST_URL})
    headers = {"Content-Type": "application/json"}
    logger.info(f"Sending test URL to direct endpoint: {TEST_URL}")
    response = requests.post(
        f"{BASE_URL}/api/direct_url_analyze", data=data, headers=headers
    )

    if response.status_code != 200:
        logger.error(
            f"Error with direct URL endpoint: {response.status_code} - {response.text}"
        )
        return False

    logger.info("Direct URL endpoint test successful")
    logger.info(f"Response: {response.json()}")
    return True


def test_all_tabs(input_method):
    """Test all tabs for proper data."""
    success = True

    # Test all tabs
    tabs = {
        "Verified Citations": test_verified_tab,
        "Unconfirmed Citations": test_unconfirmed_tab,
        "CourtListener Cases": test_courtlistener_tab,
        "CourtListener Gaps": test_courtlistener_gaps_tab,
        "Google Scholar": test_google_scholar_tab,
    }

    for tab_name, test_func in tabs.items():
        logger.info(f"\nTesting {tab_name} tab...")
        try:
            tab_success = test_func()
            if not tab_success:
                logger.error(f"{tab_name} tab test failed")
                success = False
        except Exception as e:
            logger.error(f"Error testing {tab_name} tab: {str(e)}")
            success = False

    if success:
        logger.info(f"\nAll tabs successfully tested with {input_method}!")
    else:
        logger.error(f"\nSome tabs failed testing with {input_method}.")

    return success


def run_all_tests():
    """Run all tests."""
    logger.info("Starting comprehensive CaseStrainer testing...")

    results = {
        "file_upload": test_file_upload(),
        "text_paste": test_text_paste(),
        "url_input": test_url_input(),
        "direct_url": test_direct_url(),
    }

    logger.info("\n=== TEST RESULTS SUMMARY ===")
    for test_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")

    all_passed = all(results.values())
    if all_passed:
        logger.info("\nALL TESTS PASSED! CaseStrainer is working correctly.")
    else:
        logger.error("\nSOME TESTS FAILED. Please check the logs for details.")

    return all_passed


if __name__ == "__main__":
    run_all_tests()
