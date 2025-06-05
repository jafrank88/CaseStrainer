#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for URL processing in CaseStrainer API
This script tests the functionality of the /api/analyze endpoint with URL input
"""

import sys
import requests
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_url_api")


def test_url_processing(url):
    """Test the analyze endpoint with a URL."""
    logger.info(f"Testing analyze endpoint with URL: {url}")

    # CaseStrainer API endpoint
    api_url = "http://localhost:5000/api/analyze"

    # Prepare the JSON payload
    payload = {"content_type": "url", "url": url}

    headers = {"Content-Type": "application/json"}

    # Make the request to the CaseStrainer API
    logger.info(f"Sending URL to CaseStrainer API at {api_url}")
    logger.info(f"Payload: {json.dumps(payload)}")

    try:
        response = requests.post(api_url, json=payload, headers=headers)

        # Check response status
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")

        try:
            result = response.json()
            logger.info(f"Response JSON: {json.dumps(result, indent=2)}")

            # Check if the request was successful
            if result.get("status") == "success":
                logger.info("URL processing successful!")

                # Print citation results
                citations = result.get("citations", [])
                logger.info(f"Found {len(citations)} citations:")

                for i, citation in enumerate(citations, 1):
                    logger.info(f"  {i}. {citation.get('citation', '')}")
                    logger.info(f"     Found: {citation.get('found', False)}")
                    logger.info(
                        f"     Case Name: {citation.get('found_case_name', '')}"
                    )
                    logger.info(f"     Source: {citation.get('source', '')}")

                # Now test the other API endpoints to see if they have access to the citation data
                test_other_endpoints()

                return True
            else:
                logger.error(
                    f"URL processing failed: {result.get('message', 'Unknown error')}"
                )
                return False

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response: {response.text}")
            return False

    except Exception as e:
        logger.error(f"Error making request: {str(e)}")
        return False


def test_other_endpoints():
    """Test other API endpoints to see if they have access to the citation data."""
    endpoints = [
        "http://localhost:5000/api/courtlistener_citations",
        "http://localhost:5000/api/unconfirmed_citations_data",
        "http://localhost:5000/api/confirmed_with_multitool_data",
        "http://localhost:5000/api/courtlistener_gaps",
    ]

    for endpoint in endpoints:
        try:
            logger.info(f"Testing endpoint: {endpoint}")
            response = requests.get(endpoint)

            # Check response status
            logger.info(f"Response status code: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                logger.info(f"Response data: {json.dumps(result, indent=2)}")
            else:
                logger.error(f"Failed to get data from {endpoint}: {response.text}")

        except Exception as e:
            logger.error(f"Error testing endpoint {endpoint}: {str(e)}")


if __name__ == "__main__":
    # Get URL from command line argument or use default
    if len(sys.argv) < 2:
        # Default URL with legal citations
        test_url = "https://www.law.cornell.edu/supremecourt/text/347/483"
        logger.info(f"No URL provided, using default: {test_url}")
    else:
        test_url = sys.argv[1]

    test_url_processing(test_url)
