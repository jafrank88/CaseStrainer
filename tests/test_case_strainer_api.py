#!/usr/bin/env python3
"""
Comprehensive API test suite for CaseStrainer

This script tests all major API endpoints of the CaseStrainer application,
including citation validation, text analysis, and file uploads.
"""

import os
import sys
import json
import logging
import unittest
import requests

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detailed output
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Enable requests debug logging
logging.getLogger("urllib3").setLevel(logging.DEBUG)

# Constants
BASE_URL = "http://localhost:5000/casestrainer"  # Base URL without the /api suffix
TEST_FILES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_files")
SAMPLE_CITATIONS = [
    "347 U.S. 483",  # Brown v. Board of Education
    "410 U.S. 113",  # Roe v. Wade
    "567 U.S. 519",  # NFIB v. Sebelius
    "576 U.S. 644",  # Obergefell v. Hodges
    "142 S. Ct. 2228",  # New York State Rifle & Pistol Association v. Bruen
]

# Print environment info for debugging
print("\n=== Environment Info ===")
print(f"Python: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Test files directory: {TEST_FILES_DIR}")
print(f"Base URL: {BASE_URL}")
print("======================\n")


class TestCaseStrainerAPI(unittest.TestCase):
    """Test suite for CaseStrainer API endpoints."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment before any tests run."""
        cls.session = requests.Session()
        cls.session.headers.update({"Content-Type": "application/json"})

        # Create test files directory if it doesn't exist
        os.makedirs(TEST_FILES_DIR, exist_ok=True)

        # Create a sample text file for testing
        cls.sample_text_path = os.path.join(TEST_FILES_DIR, "sample.txt")
        with open(cls.sample_text_path, "w") as f:
            f.write(
                "This is a test document with a citation to 347 U.S. 483 (Brown v. Board)."
            )

    def test_health_check(self):
        """Test the health check endpoint."""
        logger.info("\n=== Testing health check endpoint ===")
        url = f"{BASE_URL}/api/health"
        logger.debug(f"Making GET request to: {url}")

        try:
            response = self.session.get(url, timeout=10)
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")
            logger.debug(
                f"Response content: {response.text[:500]}..."
            )  # First 500 chars

            self.assertEqual(
                response.status_code,
                200,
                f"Expected status code 200, got {response.status_code}",
            )

            try:
                data = response.json()
                logger.debug(f"Response JSON: {json.dumps(data, indent=2)}")
                self.assertEqual(
                    data.get("status"),
                    "ok",
                    f"Expected status 'ok', got {data.get('status')}",
                )
                logger.info("✓ Health check passed")
            except json.JSONDecodeError as e:
                self.fail(f"Failed to parse JSON response: {e}")

        except requests.exceptions.RequestException as e:
            self.fail(f"Request failed: {e}")

    def test_verify_citation(self):
        """Test the verify_citation endpoint with various citations."""
        logger.info("\n=== Testing verify_citation endpoint ===")

        for citation in SAMPLE_CITATIONS:
            with self.subTest(citation=citation):
                url = f"{BASE_URL}/verify_citation"
                payload = {"citation": citation, "enhanced": True}

                logger.info(f"\nTesting citation: {citation}")
                logger.debug(f"URL: {url}")
                logger.debug(f"Payload: {json.dumps(payload, indent=2)}")

                try:
                    response = self.session.post(url, json=payload, timeout=30)
                    logger.debug(f"Response status: {response.status_code}")
                    logger.debug(f"Response headers: {response.headers}")

                    self.assertEqual(
                        response.status_code,
                        200,
                        f"Expected status code 200, got {response.status_code}",
                    )

                    try:
                        result = response.json()
                        logger.debug(f"Response JSON: {json.dumps(result, indent=2)}")

                        self.assertIn(
                            "exists", result, "Response missing 'exists' field"
                        )
                        self.assertIn(
                            "citation", result, "Response missing 'citation' field"
                        )

                        logger.info(f"✓ Verified citation: {citation}")
                        logger.info(f"   Exists: {result.get('exists')}")

                    except json.JSONDecodeError as e:
                        self.fail(f"Failed to parse JSON response: {e}")

                except requests.exceptions.RequestException as e:
                    self.fail(f"Request failed: {e}")

    def test_analyze_text(self):
        """Test the analyze endpoint with text input."""
        logger.info("\n=== Testing text analysis ===")

        text = """
        In Brown v. Board of Education, 347 U.S. 483 (1954), the Supreme Court 
        ruled that racial segregation in public schools was unconstitutional.
        This was later reaffirmed in cases like Obergefell v. Hodges, 576 U.S. 644 (2015).
        """

        url = f"{BASE_URL}/analyze"
        payload = {"text": text, "enhanced": True}

        logger.debug(f"URL: {url}")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")

        try:
            response = self.session.post(url, json=payload, timeout=30)
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")

            self.assertEqual(
                response.status_code,
                200,
                f"Expected status code 200, got {response.status_code}",
            )

            try:
                result = response.json()
                logger.debug(f"Response JSON: {json.dumps(result, indent=2)}")

                self.assertIn("citations", result, "Response missing 'citations' field")
                self.assertIsInstance(
                    result["citations"], list, "'citations' should be a list"
                )

                num_citations = len(result["citations"])
                logger.info(f"✓ Found {num_citations} citations in text")

                if num_citations > 0:
                    logger.debug(f"First citation: {result['citations'][0]}")

                # We expect at least 2 citations in the test text
                self.assertGreaterEqual(
                    num_citations,
                    2,
                    f"Expected at least 2 citations, found {num_citations}",
                )

            except json.JSONDecodeError as e:
                self.fail(f"Failed to parse JSON response: {e}")

        except requests.exceptions.RequestException as e:
            self.fail(f"Request failed: {e}")

    def test_analyze_file(self):
        """Test the analyze endpoint with file upload."""
        logger.info("\n=== Testing file upload analysis ===")

        # Ensure test file exists
        if not os.path.exists(self.sample_text_path):
            self.fail(f"Test file not found: {self.sample_text_path}")

        logger.info(f"Using test file: {self.sample_text_path}")

        url = f"{BASE_URL}/analyze"

        try:
            with open(self.sample_text_path, "rb") as f:
                files = {"file": ("sample.txt", f, "text/plain")}
                data = {"enhanced": "true"}

                logger.debug(f"URL: {url}")
                logger.debug(f"Files: {files}")
                logger.debug(f"Data: {data}")

                response = self.session.post(
                    url,
                    files=files,
                    data=data,
                    timeout=60,  # Longer timeout for file uploads
                )

                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Response headers: {response.headers}")

                self.assertEqual(
                    response.status_code,
                    200,
                    f"Expected status code 200, got {response.status_code}",
                )

                try:
                    result = response.json()
                    logger.debug(f"Response JSON: {json.dumps(result, indent=2)}")

                    self.assertIn(
                        "citations", result, "Response missing 'citations' field"
                    )
                    self.assertIsInstance(
                        result["citations"], list, "'citations' should be a list"
                    )

                    num_citations = len(result["citations"])
                    logger.info(f"✓ Found {num_citations} citations in file")

                    if num_citations > 0:
                        logger.debug(f"First citation: {result['citations'][0]}")

                    self.assertGreaterEqual(
                        num_citations,
                        1,
                        f"Expected at least 1 citation, found {num_citations}",
                    )

                except json.JSONDecodeError as e:
                    self.fail(f"Failed to parse JSON response: {e}")

        except FileNotFoundError as e:
            self.fail(f"Test file not found: {e}")
        except requests.exceptions.RequestException as e:
            self.fail(f"Request failed: {e}")

    def test_batch_validation(self):
        """Test the batch validation endpoint."""
        logger.info("\n=== Testing batch validation ===")

        # Skip this test if the endpoint doesn't exist
        self.skipTest("Batch validation endpoint not implemented yet")

        url = f"{BASE_URL}/batch_validate"
        payload = {"citations": SAMPLE_CITATIONS, "enhanced": True}

        logger.debug(f"URL: {url}")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")

        try:
            response = self.session.post(url, json=payload, timeout=60)
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")

            self.assertEqual(
                response.status_code,
                200,
                f"Expected status code 200, got {response.status_code}",
            )

            try:
                result = response.json()
                logger.debug(f"Response JSON: {json.dumps(result, indent=2)}")

                self.assertIn("results", result, "Response missing 'results' field")
                self.assertIsInstance(
                    result["results"], list, "'results' should be a list"
                )

                num_results = len(result["results"])
                logger.info(f"✓ Validated {num_results} citations in batch")

                self.assertEqual(
                    num_results,
                    len(SAMPLE_CITATIONS),
                    f"Expected {len(SAMPLE_CITATIONS)} results, got {num_results}",
                )

            except json.JSONDecodeError as e:
                self.fail(f"Failed to parse JSON response: {e}")

        except requests.exceptions.RequestException as e:
            self.fail(f"Request failed: {e}")

    def test_error_handling(self):
        """Test error handling for invalid requests."""
        logger.info("\n=== Testing error handling ===")

        # Test with empty citation
        url = f"{BASE_URL}/verify_citation"
        payload = {"citation": ""}

        logger.debug(f"Testing empty citation: {url}")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")

        try:
            response = self.session.post(url, json=payload, timeout=10)
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response: {response.text}")

            # Check for either 400 or 422 status code (both are common for validation errors)
            self.assertIn(
                response.status_code,
                [400, 422],
                f"Expected status code 400 or 422, got {response.status_code}",
            )

            logger.info("✓ Empty citation test passed")

        except requests.exceptions.RequestException as e:
            self.fail(f"Request failed: {e}")

        # Test with invalid endpoint
        invalid_url = f"{BASE_URL}/nonexistent_endpoint"
        logger.debug(f"Testing invalid endpoint: {invalid_url}")

        try:
            response = self.session.get(invalid_url, timeout=10)
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response: {response.text}")

            # Check for 404 status code
            self.assertEqual(
                response.status_code,
                404,
                f"Expected status code 404, got {response.status_code}",
            )

            logger.info("✓ Invalid endpoint test passed")

        except requests.exceptions.RequestException as e:
            self.fail(f"Request failed: {e}")

        logger.info("✓ All error handling tests passed")


if __name__ == "__main__":
    # Set up argument parsing
    import argparse

    parser = argparse.ArgumentParser(description="Run CaseStrainer API tests")
    parser.add_argument("--url", default=BASE_URL, help="Base URL of the API")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    parser.add_argument("--log-file", help="Log file path")
    args = parser.parse_args()

    # Update base URL if provided
    BASE_URL = args.url.rstrip("/")

    # Configure logging
    log_handlers = [logging.StreamHandler()]

    if args.log_file:
        log_handlers.append(logging.FileHandler(args.log_file))

    log_level = logging.DEBUG if args.verbose else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=log_handlers,
    )

    # Run tests
    unittest.main(argv=[sys.argv[0]])
