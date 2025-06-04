#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Direct test script for URL processing in CaseStrainer
This script tests the direct URL processing functionality
"""

import requests
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_direct_url")


def test_direct_url_processing():
    """Test direct URL processing with the analyze endpoint."""

    # Test URL with legal citations
    url = "https://www.law.cornell.edu/supremecourt/text/347/483"
    logger.info(f"Testing direct URL processing with: {url}")

    # CaseStrainer API endpoint
    api_url = "http://localhost:5000/api/analyze"

    # Prepare the JSON payload for direct URL processing
    payload = {"content_type": "url", "url": url}

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
            return True
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error making request: {str(e)}")
        return False


if __name__ == "__main__":
    test_direct_url_processing()
