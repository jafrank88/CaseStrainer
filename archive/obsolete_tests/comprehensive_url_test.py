#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Comprehensive test script for URL input handling in CaseStrainer
This script tests both the direct URL analysis and the output tabs
"""

import requests
import json
import logging
import time
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("comprehensive_url_test.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("comprehensive_url_test")

# Configuration
BASE_URL = "http://localhost:5000"  # Default local URL
TEST_URL = "https://www.law.cornell.edu/supremecourt/text/347/483"  # Brown v. Board of Education


def test_direct_url_analyze():
    """Test the direct_url_analyze endpoint."""
    logger.info(f"Testing direct URL analysis with: {TEST_URL}")

    # CaseStrainer API endpoint
    api_url = f"{BASE_URL}/api/direct_url_analyze"

    # Prepare the JSON payload
    payload = {"url": TEST_URL}

    headers = {"Content-Type": "application/json"}

    # Make the request to the CaseStrainer API
    logger.info(f"Sending request to: {api_url}")
    logger.info(f"Payload: {json.dumps(payload)}")

    try:
        response = requests.post(api_url, json=payload, headers=headers)

        # Log response details
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")

        # Check if the request was successful
        if response.status_code == 200:
            try:
                result = response.json()
                logger.info(f"Response JSON: {json.dumps(result, indent=2)}")

                # Check if the response contains the expected fields
                if "status" in result and result["status"] == "success":
                    logger.info("Direct URL analysis test successful")

                    # Return the analysis ID for further testing
                    return result.get("analysis_id")
                else:
                    logger.error(
                        f"Direct URL analysis test failed: {result.get('message', 'Unknown error')}"
                    )
                    return None
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON response: {response.text}")
                return None
        else:
            logger.error(
                f"Direct URL analysis test failed with status code {response.status_code}: {response.text}"
            )
            return None
    except Exception as e:
        logger.error(f"Error during direct URL analysis test: {e}")
        return None


def test_analyze_endpoint():
    """Test the analyze endpoint with URL input."""
    logger.info(f"Testing analyze endpoint with URL input: {TEST_URL}")

    # CaseStrainer API endpoint
    api_url = f"{BASE_URL}/api/analyze"

    # Prepare the JSON payload
    payload = {"url": TEST_URL}

    headers = {"Content-Type": "application/json"}

    # Make the request to the CaseStrainer API
    logger.info(f"Sending request to: {api_url}")
    logger.info(f"Payload: {json.dumps(payload)}")

    try:
        response = requests.post(api_url, json=payload, headers=headers)

        # Log response details
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")

        # Check if the request was successful
        if response.status_code == 200:
            try:
                result = response.json()
                logger.info(f"Response JSON: {json.dumps(result, indent=2)}")

                # Check if the response contains the expected fields
                if "status" in result and result["status"] == "success":
                    logger.info("Analyze endpoint test successful")

                    # Return the analysis ID for further testing
                    return result.get("analysis_id")
                else:
                    logger.error(
                        f"Analyze endpoint test failed: {result.get('message', 'Unknown error')}"
                    )
                    return None
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON response: {response.text}")
                return None
        else:
            logger.error(
                f"Analyze endpoint test failed with status code {response.status_code}: {response.text}"
            )
            return None
    except Exception as e:
        logger.error(f"Error during analyze endpoint test: {e}")
        return None


def test_output_tabs(analysis_id):
    """Test the output tabs with the given analysis ID."""
    if not analysis_id:
        logger.error("No analysis ID provided for output tabs test")
        return False

    logger.info(f"Testing output tabs with analysis ID: {analysis_id}")

    # Wait for processing to complete
    logger.info("Waiting for processing to complete...")
    time.sleep(5)  # Increased wait time to ensure processing is complete

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
            tab_url = f"{BASE_URL}/api/results/{analysis_id}/{tab}"
            logger.info(f"Requesting: {tab_url}")

            tab_response = requests.get(tab_url)

            # Log response details
            logger.info(f"Response status code: {tab_response.status_code}")

            # Check if the request was successful
            if tab_response.status_code == 200:
                try:
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
                except json.JSONDecodeError:
                    logger.error(
                        f"Invalid JSON response for {tab} tab: {tab_response.text}"
                    )
                    tab_results[tab] = False
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


def main():
    """Main function to run all tests."""
    logger.info("Starting comprehensive URL input testing for CaseStrainer...")

    # Parse command line arguments
    if len(sys.argv) > 1:
        global BASE_URL
        BASE_URL = sys.argv[1]
        logger.info(f"Using custom base URL: {BASE_URL}")

    # Test the direct_url_analyze endpoint
    direct_url_analysis_id = test_direct_url_analyze()

    # Test the analyze endpoint with URL input
    analyze_endpoint_analysis_id = test_analyze_endpoint()

    # Test the output tabs with the analysis IDs
    direct_url_tabs_result = False
    analyze_endpoint_tabs_result = False

    if direct_url_analysis_id:
        direct_url_tabs_result = test_output_tabs(direct_url_analysis_id)

    if analyze_endpoint_analysis_id:
        analyze_endpoint_tabs_result = test_output_tabs(analyze_endpoint_analysis_id)

    # Print the test results summary
    logger.info("=== TEST RESULTS SUMMARY ===")
    logger.info(
        f"Direct URL analyze endpoint: {'PASSED' if direct_url_analysis_id else 'FAILED'}"
    )
    logger.info(
        f"Analyze endpoint with URL input: {'PASSED' if analyze_endpoint_analysis_id else 'FAILED'}"
    )
    logger.info(
        f"Output tabs with direct URL analysis: {'PASSED' if direct_url_tabs_result else 'FAILED'}"
    )
    logger.info(
        f"Output tabs with analyze endpoint: {'PASSED' if analyze_endpoint_tabs_result else 'FAILED'}"
    )

    # Overall test result
    if (direct_url_analysis_id or analyze_endpoint_analysis_id) and (
        direct_url_tabs_result or analyze_endpoint_tabs_result
    ):
        logger.info(
            "SOME TESTS PASSED! CaseStrainer URL input functionality is partially working."
        )
    else:
        logger.error("ALL TESTS FAILED. Please check the logs for details.")


if __name__ == "__main__":
    main()
