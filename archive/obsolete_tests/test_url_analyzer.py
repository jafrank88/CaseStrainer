import json
import logging
import requests
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("url_analyzer_test.log"), logging.StreamHandler()],
)

# Create a logger for this module
logger = logging.getLogger("url_analyzer_test")

# Test configuration
BASE_URL = "http://127.0.0.1:5000"  # URL of the CaseStrainer application
TEST_URL = "https://www.law.cornell.edu/supremecourt/text/347/483"  # Brown v. Board of Education
headers = {"Content-Type": "application/json"}


def test_url_analyzer():
    """Test the URL analyzer endpoint."""
    logger.info(f"Testing URL analyzer with URL: {TEST_URL}")

    # Create JSON payload with the test URL
    data = json.dumps({"url": TEST_URL})

    try:
        # Send POST request to the URL analyzer endpoint
        response = requests.post(
            f"{BASE_URL}/api/url_analyzer", data=data, headers=headers
        )

        # Log response details
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response content type: {response.headers.get('Content-Type')}")

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            result = response.json()
            logger.info(f"Response: {result}")

            # Verify that the response contains the expected fields
            if "status" in result and result["status"] == "success":
                logger.info("URL analyzer test successful")
                return True
            else:
                logger.error(
                    f"URL analyzer test failed: {result.get('message', 'Unknown error')}"
                )
                return False
        else:
            logger.error(
                f"URL analyzer test failed with status code {response.status_code}: {response.text}"
            )
            return False
    except Exception as e:
        logger.error(f"Error during URL analyzer test: {e}")
        return False


def test_output_tabs():
    """Test the output tabs (4-7) with the URL input."""
    logger.info("Testing output tabs with URL input")

    # First, send a URL to the analyzer
    data = json.dumps({"url": TEST_URL})

    try:
        # Send POST request to the URL analyzer endpoint
        response = requests.post(
            f"{BASE_URL}/api/url_analyzer", data=data, headers=headers
        )

        # Check if the request was successful
        if response.status_code != 200:
            logger.error(
                f"URL analyzer request failed with status code {response.status_code}: {response.text}"
            )
            return False

        # Parse the JSON response
        result = response.json()
        logger.info(f"URL analyzer response: {result}")

        # Get the analysis ID from the response
        analysis_id = result.get("analysis_id")
        if not analysis_id:
            logger.error("No analysis ID found in the response")
            return False

        logger.info(f"Analysis ID: {analysis_id}")

        # Wait for processing to complete
        logger.info("Waiting for processing to complete...")
        time.sleep(3)

        # Test output tabs
        tabs = [
            "verified_citations",
            "unconfirmed_citations",
            "courtlistener_cases",
            "google_scholar_cases",
        ]

        tab_results = {}

        for tab in tabs:
            logger.info(f"Checking {tab} tab...")
            try:
                # Send GET request to the tab endpoint
                tab_response = requests.get(
                    f"{BASE_URL}/api/results/{analysis_id}/{tab}"
                )

                # Log response details
                logger.info(f"Response status code: {tab_response.status_code}")

                # Check if the request was successful
                if tab_response.status_code == 200:
                    # Parse the JSON response
                    tab_result = tab_response.json()

                    # Count the number of citations in the tab
                    citation_count = len(tab_result.get("citations", []))
                    logger.info(f"Found {citation_count} citations in {tab} tab")

                    # Log the first few citations
                    for i, citation in enumerate(tab_result.get("citations", [])[:3]):
                        logger.info(
                            f"  - {citation.get('name', 'Unknown')}: {citation.get('text', '')}"
                        )

                    tab_results[tab] = True
                else:
                    logger.error(
                        f"{tab} tab request failed with status code {tab_response.status_code}: {tab_response.text}"
                    )
                    tab_results[tab] = False
            except Exception as e:
                logger.error(f"Error checking {tab} tab: {e}")
                tab_results[tab] = False

        # Check if all tabs were successful
        all_tabs_successful = all(tab_results.values())
        if all_tabs_successful:
            logger.info("All output tabs tested successfully")
        else:
            logger.error("Some output tabs failed testing")
            for tab, result in tab_results.items():
                logger.info(f"  - {tab}: {'PASSED' if result else 'FAILED'}")

        return all_tabs_successful
    except Exception as e:
        logger.error(f"Error during output tabs test: {e}")
        return False


if __name__ == "__main__":
    logger.info("Starting URL analyzer testing...")

    # Test the URL analyzer endpoint
    url_analyzer_result = test_url_analyzer()

    # Test the output tabs with URL input
    output_tabs_result = test_output_tabs()

    # Print the test results summary
    logger.info("=== TEST RESULTS SUMMARY ===")
    logger.info(f"URL analyzer: {'PASSED' if url_analyzer_result else 'FAILED'}")
    logger.info(f"Output tabs: {'PASSED' if output_tabs_result else 'FAILED'}")

    # Overall test result
    if url_analyzer_result and output_tabs_result:
        logger.info("ALL TESTS PASSED! URL analyzer is working correctly.")
    else:
        logger.error("SOME TESTS FAILED. Please check the logs for details.")
