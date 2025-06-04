#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for the URL tab functionality in CaseStrainer
This script tests both the fetch_url and analyze endpoints to simulate the URL tab workflow
"""

import os
import sys
import requests
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_url_tab")


def test_url_tab_workflow(url):
    """Test the complete URL tab workflow."""
    logger.info(f"Testing URL tab workflow with URL: {url}")

    # Step 1: Call the fetch_url endpoint to get the content
    fetch_url_endpoint = "http://localhost:5000/api/fetch_url"

    # Prepare the JSON payload for fetch_url
    fetch_payload = {"url": url}

    headers = {"Content-Type": "application/json"}

    # Make the request to fetch_url
    logger.info(f"Step 1: Calling fetch_url endpoint at {fetch_url_endpoint}")
    logger.info(f"Payload: {json.dumps(fetch_payload)}")

    try:
        fetch_response = requests.post(
            fetch_url_endpoint, json=fetch_payload, headers=headers
        )

        # Check response status
        logger.info(f"fetch_url response status code: {fetch_response.status_code}")

        try:
            fetch_result = fetch_response.json()
            logger.info(
                f"fetch_url response JSON: {json.dumps(fetch_result, indent=2)}"
            )

            # Check if the request was successful
            if fetch_result.get("status") == "success" and "text" in fetch_result:
                logger.info("fetch_url call successful!")

                # Check if eyecite already processed the citations
                if fetch_result.get("eyecite_processed", False):
                    logger.info(
                        f"Eyecite already processed {fetch_result.get('citations_count', 0)} citations"
                    )
                    logger.info(
                        "Skipping analyze step since eyecite already processed the citations"
                    )

                    # Test the other API endpoints to see if they have access to the citation data
                    test_other_endpoints()

                    return True

                # Step 2: Call the analyze endpoint with the text from fetch_url
                analyze_endpoint = "http://localhost:5000/api/analyze"

                # Prepare the form data for analyze
                analyze_form_data = {"text": fetch_result.get("text", "")}

                # Make the request to analyze
                logger.info(f"Step 2: Calling analyze endpoint at {analyze_endpoint}")
                logger.info(
                    f"Form data: text length = {len(analyze_form_data['text'])} characters"
                )

                analyze_response = requests.post(
                    analyze_endpoint, data=analyze_form_data
                )

                # Check response status
                logger.info(
                    f"analyze response status code: {analyze_response.status_code}"
                )

                try:
                    analyze_result = analyze_response.json()
                    logger.info(
                        f"analyze response JSON: {json.dumps(analyze_result, indent=2)}"
                    )

                    # Check if the request was successful
                    if analyze_result.get("status") == "success":
                        logger.info("analyze call successful!")

                        # Print citation results
                        citations = analyze_result.get("citations", [])
                        logger.info(f"Found {len(citations)} citations:")

                        for i, citation in enumerate(citations, 1):
                            logger.info(f"  {i}. {citation.get('citation', '')}")
                            logger.info(f"     Found: {citation.get('found', False)}")
                            logger.info(
                                f"     Case Name: {citation.get('found_case_name', '')}"
                            )
                            logger.info(f"     Source: {citation.get('source', '')}")

                        # Test the other API endpoints to see if they have access to the citation data
                        test_other_endpoints()

                        return True
                    else:
                        logger.error(
                            f"analyze call failed: {analyze_result.get('message', 'Unknown error')}"
                        )
                        return False

                except json.JSONDecodeError:
                    logger.error(
                        f"Invalid JSON response from analyze: {analyze_response.text}"
                    )
                    return False
            else:
                logger.error(
                    f"fetch_url call failed: {fetch_result.get('message', 'Unknown error')}"
                )
                return False

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response from fetch_url: {fetch_response.text}")
            return False

    except Exception as e:
        logger.error(f"Error making request to fetch_url: {str(e)}")
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

    test_url_tab_workflow(test_url)
