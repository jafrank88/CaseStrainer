#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for the direct_url_analyze endpoint in CaseStrainer
This script tests the direct URL analysis functionality
"""

import requests
import json
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_direct_url_endpoint")


def test_direct_url_endpoint():
    """Test the direct_url_analyze endpoint."""

    # Test URL with legal citations
    url = "https://www.law.cornell.edu/supremecourt/text/347/483"
    logger.info(f"Testing direct URL endpoint with: {url}")

    # CaseStrainer API endpoint
    api_url = "http://localhost:5000/api/direct_url_analyze"

    # Prepare the JSON payload for direct URL processing
    payload = {"url": url}

    headers = {"Content-Type": "application/json"}

    # Make the request to the CaseStrainer API
    logger.info(f"Sending direct URL request to: {api_url}")
    logger.info(f"Payload: {json.dumps(payload)}")

    try:
        response = requests.post(api_url, json=payload, headers=headers)

        # Log the raw response for debugging
        logger.info(f"Raw response: {response.text}")

        # Check response status
        logger.info(f"Response status code: {response.status_code}")

        try:
            result = response.json()
            logger.info(f"Response JSON: {json.dumps(result, indent=2)}")

            # If successful, test the output tabs
            if response.status_code == 200 and result.get("status") == "success":
                analysis_id = result.get("analysis_id")
                if analysis_id:
                    logger.info(f"Analysis ID: {analysis_id}")
                    test_output_tabs(analysis_id)
                else:
                    logger.error("No analysis ID found in the response")

            return response.status_code == 200
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error making request: {str(e)}")
        return False


def test_output_tabs(analysis_id):
    """Test the output tabs (4-7) with the given analysis ID."""
    logger.info(f"Testing output tabs with analysis ID: {analysis_id}")

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
            tab_url = f"http://localhost:5000/api/results/{analysis_id}/{tab}"
            logger.info(f"Requesting: {tab_url}")

            tab_response = requests.get(tab_url)

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


if __name__ == "__main__":
    success = test_direct_url_endpoint()
    if success:
        logger.info("Direct URL endpoint test completed successfully")
    else:
        logger.error("Direct URL endpoint test failed")
