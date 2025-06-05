#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple test script for URL processing in CaseStrainer
This script tests the functionality of processing a simple text URL
"""

import os
import requests
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_url_simple")


def test_text_url(url):
    """Test processing a text URL"""
    logger.info(f"Testing URL: {url}")

    try:
        # Fetch content from URL
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        logger.info("Sending request to URL...")
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        logger.info(f"URL content type: {content_type}")

        # Get text content
        document_text = response.text
        logger.info(f"Extracted {len(document_text)} characters from URL")

        # Save extracted text to file for inspection
        os.makedirs("uploads", exist_ok=True)
        text_path = os.path.join("uploads", "test_url_simple_content.txt")
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(document_text)

        logger.info(f"Saved extracted text to {text_path}")

        # Extract and print a sample of the text
        sample_text = (
            document_text[:500] + "..." if len(document_text) > 500 else document_text
        )
        logger.info(f"Sample text: {sample_text}")

        # Test sending the URL to the analyze endpoint
        test_api_url = "http://localhost:5000/api/analyze"
        logger.info(f"Testing API endpoint: {test_api_url}")

        payload = {"content_type": "url", "url": url}

        api_response = requests.post(
            test_api_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
        )

        logger.info(f"API response status code: {api_response.status_code}")
        logger.info(f"API response content: {api_response.text}")

        return True, document_text

    except Exception as e:
        logger.error(f"Error processing URL: {str(e)}")
        return False, str(e)


if __name__ == "__main__":
    # Test URL with legal citations
    test_url = "https://www.law.cornell.edu/supremecourt/text/347/483"

    logger.info("Starting URL processing test...")
    success, result = test_text_url(test_url)

    if success:
        logger.info("URL processing test successful!")
    else:
        logger.error(f"URL processing test failed: {result}")
