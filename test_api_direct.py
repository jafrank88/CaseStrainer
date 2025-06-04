#!/usr/bin/env python3
"""
Direct API test script for CaseStrainer

This script tests the API endpoints directly without using unittest.
"""

import os
import sys
import json
import logging
import requests
import re
from pathlib import Path
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Enable requests debug logging
logging.getLogger("urllib3").setLevel(logging.DEBUG)

# Constants
BASE_URL = "http://localhost:5000/casestrainer/api"  # Base URL with /api suffix
TEST_FILES_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "tests", "test_files"
)
SAMPLE_CITATIONS = [
    "347 U.S. 483",  # Brown v. Board of Education
    "410 U.S. 113",  # Roe v. Wade
    "567 U.S. 519",  # NFIB v. Sebelius
]


def check_courtlistener_version():
    """Check if the CourtListener API is using the correct version (v4)."""
    try:
        # Get the API key from environment or config
        api_key = os.getenv("COURTLISTENER_API_KEY")
        if not api_key:
            logger.warning("COURTLISTENER_API_KEY not found in environment variables")
            return False

        # Make a test request to the API
        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json",
        }

        test_url = "https://www.courtlistener.com/api/rest/v4/citations/"

        response = requests.get(test_url, headers=headers, timeout=10)

        # Check if the URL was redirected to a different version
        if response.history:
            final_url = response.url
            if "v3" in final_url:
                logger.error(
                    f"CourtListener API is using v3 instead of v4. Final URL: {final_url}"
                )
                return False

        # Check the response status code
        if response.status_code == 200:
            logger.info("✓ CourtListener API v4 is accessible and working")
            return True
        else:
            logger.error(
                f"CourtListener API returned status code: {response.status_code}"
            )
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"Error checking CourtListener API version: {e}")
        return False


def test_health_check():
    """Test the health check endpoint."""
    logger.info("\n=== Testing health check endpoint ===")
    url = f"{BASE_URL}/api/health"  # The health check endpoint is at /api/health relative to the base URL
    logger.debug(f"Making GET request to: {url}")

    try:
        response = requests.get(url, timeout=10)
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response headers: {response.headers}")
        logger.debug(f"Response content: {response.text[:500]}...")

        if response.status_code == 200:
            try:
                data = response.json()
                logger.debug(f"Response JSON: {json.dumps(data, indent=2)}")
                if data.get("status") == "ok":
                    logger.info("✓ Health check passed")
                    return True
                else:
                    logger.error(f"Unexpected status: {data.get('status')}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
        else:
            logger.error(f"Expected status code 200, got {response.status_code}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")

    return False


def test_verify_citation(citation):
    """Test the verify_citation endpoint with a single citation."""
    logger.info(f"\n=== Testing verify_citation: {citation} ===")
    url = f"{BASE_URL}/verify-citation"  # Using kebab-case to match the actual endpoint
    payload = {
        "citation": {"text": citation},
        "enhanced": True,
    }  # Updated payload format to match API expectations

    logger.debug(f"URL: {url}")
    logger.debug(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, json=payload, timeout=30)
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response headers: {response.headers}")

        if response.status_code == 200:
            try:
                result = response.json()
                logger.debug(f"Response JSON: {json.dumps(result, indent=2)}")

                if "exists" in result and "citation" in result:
                    logger.info(f"✓ Verified citation: {citation}")
                    logger.info(f"   Exists: {result.get('exists')}")
                    return True
                else:
                    logger.error("Missing required fields in response")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
        else:
            logger.error(f"Expected status code 200, got {response.status_code}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")

    return False


def test_analyze_text():
    """Test the analyze endpoint with text input."""
    logger.info("\n=== Testing text analysis ===")

    text = """
    In Brown v. Board of Education, 347 U.S. 483 (1954), the Supreme Court 
    ruled that racial segregation in public schools was unconstitutional.
    This was later reaffirmed in cases like Obergefell v. Hodges, 576 U.S. 644 (2015).
    """

    url = f"{BASE_URL}/analyze-text"  # Using the correct endpoint for text analysis
    payload = {"text": text, "enhanced": True}  # Payload format is correct

    logger.debug(f"URL: {url}")
    logger.debug(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, json=payload, timeout=30)
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response headers: {response.headers}")

        if response.status_code == 200:
            try:
                result = response.json()
                logger.debug(f"Response JSON: {json.dumps(result, indent=2)}")

                if "citations" in result and isinstance(result["citations"], list):
                    num_citations = len(result["citations"])
                    logger.info(f"✓ Found {num_citations} citations in text")

                    if num_citations > 0:
                        logger.debug(f"First citation: {result['citations'][0]}")

                    return num_citations >= 2  # We expect at least 2 citations
                else:
                    logger.error("Invalid or missing 'citations' field in response")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
        else:
            logger.error(f"Expected status code 200, got {response.status_code}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")

    return False


def test_analyze_file():
    """Test the analyze endpoint with file upload."""
    logger.info("\n=== Testing file upload analysis ===")

    sample_file_path = os.path.join(TEST_FILES_DIR, "sample_legal_doc.txt")

    # Ensure test file exists
    if not os.path.exists(sample_file_path):
        logger.error(f"Test file not found: {sample_file_path}")
        return False

    logger.info(f"Using test file: {sample_file_path}")
    url = f"{BASE_URL}/analyze-file"  # Using the correct endpoint for file analysis

    try:
        with open(sample_file_path, "rb") as f:
            files = {"file": ("sample_legal_doc.txt", f, "text/plain")}
            data = {"enhanced": "true"}

            logger.debug(f"URL: {url}")
            logger.debug(f"Files: {files}")
            logger.debug(f"Data: {data}")

            response = requests.post(
                url,
                files=files,
                data=data,
                timeout=60,  # Longer timeout for file uploads
            )

            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")

            if response.status_code == 200:
                try:
                    result = response.json()
                    logger.debug(f"Response JSON: {json.dumps(result, indent=2)}")

                    if "citations" in result and isinstance(result["citations"], list):
                        num_citations = len(result["citations"])
                        logger.info(f"✓ Found {num_citations} citations in file")

                        if num_citations > 0:
                            logger.debug(f"First citation: {result['citations'][0]}")

                        return num_citations >= 1  # We expect at least 1 citation
                    else:
                        logger.error("Invalid or missing 'citations' field in response")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
            else:
                logger.error(f"Expected status code 200, got {response.status_code}")

    except FileNotFoundError as e:
        logger.error(f"Test file not found: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")

    return False


def test_error_handling():
    """Test error handling for invalid requests."""
    logger.info("\n=== Testing error handling ===")

    # Test with empty citation
    url = f"{BASE_URL}/verify_citation"
    payload = {"citation": ""}

    logger.debug(f"Testing empty citation: {url}")
    logger.debug(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, json=payload, timeout=10)
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response: {response.text}")

        # Check for either 400 or 422 status code (both are common for validation errors)
        if response.status_code in [400, 422]:
            logger.info("✓ Empty citation test passed (expected error)")
        else:
            logger.error(f"Expected status code 400 or 422, got {response.status_code}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")

    # Test with invalid endpoint
    invalid_url = f"{BASE_URL}/nonexistent_endpoint"
    logger.debug(f"Testing invalid endpoint: {invalid_url}")

    try:
        response = requests.get(invalid_url, timeout=10)
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response: {response.text}")

        # Check for 404 status code
        if response.status_code == 404:
            logger.info("✓ Invalid endpoint test passed (expected 404)")
        else:
            logger.error(f"Expected status code 404, got {response.status_code}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")


if __name__ == "__main__":
    print("\n=== Starting CaseStrainer API Tests ===\n")

    # First, check CourtListener API version
    print("Checking CourtListener API version...")
    if not check_courtlistener_version():
        print(
            "\nWARNING: CourtListener API version check failed. Some tests may not work correctly."
        )
        print(
            "Please ensure you're using CourtListener API v4 for full functionality.\n"
        )
        if input("Continue with tests anyway? (y/n): ").lower() != "y":
            print("Tests aborted by user.")
            sys.exit(1)

    # Run tests
    test_health_check()

    # Test citation verification
    for citation in SAMPLE_CITATIONS:
        test_verify_citation(citation)

    # Test text analysis
    test_analyze_text()

    # Test file upload analysis
    test_analyze_file()

    # Test error handling
    test_error_handling()

    print("\n=== Test completed ===\n")
