import unittest
import json
import os
import sys
import logging
import argparse
import urllib3
import time
from urllib.parse import urljoin
from urllib3.util.retry import Retry

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from typing import Dict, Any, List, Optional, Union
from unittest.mock import patch, MagicMock

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logger.info(f"Python path: {sys.path}")

from flask.testing import FlaskClient
from flask import Flask, jsonify, current_app

# Import the create_app function
from src.app_final_vue import create_app

# Import the EnhancedMultiSourceVerifier for testing
from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier


class TestCitationAPI(unittest.TestCase):
    """Test cases for the Citation API endpoints."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before running any tests."""
        # Configure root logger
        logging.basicConfig(
            level=logging.DEBUG,  # Increased to DEBUG for more detailed output
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler("test.log", mode="w"),
            ],
        )
        cls.logger = logging.getLogger(__name__)
        cls.logger.info("\n" + "=" * 70)
        cls.logger.info("Setting up test environment...")

        try:
            # Create a test SQLite database in memory
            cls.test_db_path = ":memory:"
            cls.logger.info(f"Using in-memory SQLite database: {cls.test_db_path}")

            # Create a test Flask app with explicit configuration
            cls.app = create_app()
            
            # Configure the app for testing
            cls.app.config.update(
                TESTING=True,
                DEBUG=True,
                PROPAGATE_EXCEPTIONS=True,
                SQLALCHEMY_DATABASE_URI=f"sqlite:///{cls.test_db_path}",
                SQLALCHEMY_TRACK_MODIFICATIONS=False,
                WTF_CSRF_ENABLED=False,
                SERVER_NAME='localhost:5000'  # Add server name for URL building
            )
            
            # Create a test client with explicit configuration
            cls.client = cls.app.test_client()
            cls.client.testing = True
            
            # Enable test client session transactions
            cls.app.testing = True
            
            cls.logger.info("Test Flask application created")
            cls.logger.debug(f"Available routes: {[str(rule) for rule in cls.app.url_map.iter_rules()]}")

            # Push an application context
            cls.app_context = cls.app.app_context()
            cls.app_context.push()
            cls.logger.info("Application context pushed")

            cls.logger.info("Test environment setup complete" + "\n" + "=" * 70)
            
            # Verify the test client
            with cls.app.test_request_context():
                cls.logger.info(f"Test request context established. URL map: {cls.app.url_map}")
                
                # Test a simple route to verify the app is working
                try:
                    response = cls.client.get('/casestrainer/api/health')
                    cls.logger.info(f"Health check status: {response.status_code}")
                    cls.logger.info(f"Health check response: {response.get_json()}")
                except Exception as e:
                    cls.logger.error(f"Failed to access health endpoint: {str(e)}")
                    raise

        except Exception as e:
            cls.logger.error(f"Error setting up test environment: {str(e)}")
            raise

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests have run."""
        try:
            # Pop the application context
            if hasattr(cls, "app_context"):
                cls.app_context.pop()

            # Remove the test database if it exists
            if (
                hasattr(cls, "test_db_path")
                and cls.test_db_path != ":memory:"
                and os.path.exists(cls.test_db_path)
            ):
                try:
                    os.unlink(cls.test_db_path)
                    cls.logger.info(f"Removed test database: {cls.test_db_path}")
                except Exception as e:
                    cls.logger.error(f"Error removing test database: {str(e)}")

            cls.logger.info("Test environment cleaned up")
        except Exception as e:
            cls.logger.error(f"Error during test teardown: {str(e)}")
            raise
            # Clean up the test database
            if hasattr(cls, "test_db_path") and os.path.exists(cls.test_db_path):
                os.unlink(cls.test_db_path)
        except Exception as e:
            logger.error(f"Error cleaning up test environment: {str(e)}")
            raise

    @patch(
        "src.enhanced_multi_source_verifier.EnhancedMultiSourceVerifier.verify_citation"
    )
    @patch("src.enhanced_multi_source_verifier.sqlite3")
    def test_enhanced_validate_citation(self, mock_sqlite3, mock_verify_citation):
        """Test the enhanced_validate_citation endpoint with various input formats."""
        print("\n" + "=" * 70)
        print("STARTING TEST: test_enhanced_validate_citation")
        print("=" * 70)

        # Set up logging for this test
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler("test.log", mode="w"),
            ],
        )

        logger = logging.getLogger(__name__)
        logger.info("Starting test_enhanced_validate_citation")

        # Set up mock database
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_sqlite3.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None  # No cached results by default

        # Create a test client
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()

        # Mock the verify_citation method to return different responses based on input
        def mock_verify_citation_side_effect(citation_text, case_name=None):
            # For testing different citation formats
            if citation_text == "123 F.3d 456":
                return {
                    "citation": "123 F.3d 456",
                    "verified": True,
                    "verified_by": "CourtListener",
                    "metadata": {"case_name": "Test v. Case"},
                    "backdrop": "test-backdrop",
                    "error": "",
                }
            elif citation_text == "410 U.S. 113 (1973)":
                return {
                    "citation": "410 U.S. 113",
                    "verified": True,
                    "verified_by": "CourtListener",
                    "metadata": {"case_name": "Roe v. Wade"},
                    "backdrop": "roe-v-wade-backdrop",
                    "error": "",
                }
            elif citation_text == "":
                return {
                    "citation": "",
                    "verified": False,
                    "error": "No citation provided",
                    "metadata": {},
                    "backdrop": "",
                    "verified_by": "Validation",
                }
            else:
                return {
                    "citation": citation_text,
                    "verified": False,
                    "error": "Citation not found",
                    "metadata": {},
                    "backdrop": "",
                    "verified_by": "",
                }

        mock_verify_citation.side_effect = mock_verify_citation_side_effect

        # Test cases for different scenarios
        test_cases = [
            # Valid citation format
            {
                "name": "Simple citation string (Federal Reporter)",
                "data": {"citation": "123 F.3d 456"},
                "setup_db": lambda: None,  # No special DB setup needed
                "expected_status": 200,
                "expected_response": {
                    "citation": "123 F.3d 456",
                    "verified": True,
                    "verified_by": "CourtListener",
                    "metadata": {"case_name": "Test v. Case"},
                    "backdrop": "test-backdrop",
                    "error": "",
                },
            },
            # Test case for empty citation
            {
                "name": "Empty citation",
                "data": {"citation": ""},
                "setup_db": lambda: None,
                "expected_status": 400,
                "expected_response": {
                    "citation": "",
                    "verified": False,
                    "error": "No citation provided",
                    "metadata": {},
                    "backdrop": "",
                    "verified_by": "Validation",
                },
            },
            # US Supreme Court citation
            {
                "name": "US Supreme Court citation",
                "data": {"citation": "410 U.S. 113 (1973)"},
                "setup_db": lambda: None,
                "expected_status": 200,
                "expected_response": {
                    "citation": "410 U.S. 113",
                    "verified": True,
                    "verified_by": "CourtListener",
                    "metadata": {"case_name": "Roe v. Wade"},
                    "backdrop": "roe-v-wade-backdrop",
                    "error": "",
                },
            },
            # Missing citation field
            {
                "name": "Missing citation field",
                "data": {},
                "setup_db": lambda: None,
                "expected_status": 400,
                "expected_response": {
                    "citation": "",
                    "verified": False,
                    "verified_by": "Validation",
                    "error": "No citation provided",
                    "metadata": {},
                    "backdrop": "",
                },
            },
            # US Supreme Court citation
            {
                "name": "US Supreme Court citation",
                "data": {"citation": "410 U.S. 113 (1973)"},
                "setup_db": lambda: None,
                "expected_status": 200,
                "expected_response": {
                    "citation": "410 U.S. 113",
                    "verified": True,
                    "verified_by": "CourtListener",
                    "metadata": {"case_name": "Roe v. Wade"},
                    "backdrop": "roe-v-wade-backdrop",
                    "error": "",
                },
            },
            # Citation with case name
            {
                "name": "Citation with case name",
                "data": {"citation": "123 F.3d 456", "case_name": "Test v. Case"},
                "setup_db": lambda: None,
                "expected_status": 200,
                "expected_response": {
                    "citation": "123 F.3d 456",
                    "verified": True,
                    "verified_by": "CourtListener",
                    "metadata": {"case_name": "Test v. Case"},
                    "backdrop": "test-backdrop",
                    "error": "",
                },
            },
        ]

        # Mock function for verify_citation
        def mock_verify_citation_side_effect(citation_text, case_name=None):
            if citation_text == "123 F.3d 456":
                return {
                    "citation": "123 F.3d 456",
                    "verified": True,
                    "verified_by": "CourtListener",
                    "metadata": {"case_name": case_name or "Test v. Case"},
                    "backdrop": "test-backdrop",
                    "error": "",
                }
            elif citation_text == "410 U.S. 113 (1973)":
                return {
                    "citation": "410 U.S. 113",
                    "verified": True,
                    "verified_by": "CourtListener",
                    "metadata": {"case_name": "Roe v. Wade"},
                    "backdrop": "roe-v-wade-backdrop",
                    "error": "",
                }
            elif not citation_text:
                return {
                    "citation": "",
                    "verified": False,
                    "error": "No citation provided",
                    "metadata": {},
                    "backdrop": "",
                    "verified_by": "Validation",
                }
            else:
                return {
                    "citation": citation_text,
                    "verified": False,
                    "error": "Citation not found",
                    "metadata": {},
                    "backdrop": "",
                    "verified_by": "",
                }

        mock_verify_citation.side_effect = mock_verify_citation_side_effect

        # Test cases for different scenarios
        test_cases = [
            # Citation with case name
            {
                "name": "Citation with case name",
                "data": {"citation": "123 F.3d 456", "case_name": "Test v. Case"},
                "setup_db": lambda: None,
                "expected_status": 200,
                "expected_response": {
                    "citation": "123 F.3d 456",
                    "verified": True,
                    "verified_by": "CourtListener",
                    "metadata": {"case_name": "Test v. Case"},
                    "backdrop": "test-backdrop",
                    "error": "",
                },
            },
            # Citation as object
            {
                "name": "Citation as object",
                "data": {
                    "citation": {
                        "citation_text": "123 F.3d 456",
                        "case_name": "Test v. Case",
                    }
                },
                "setup_db": lambda: None,
                "expected_status": 200,
                "expected_response": {
                    "citation": "123 F.3d 456",
                    "verified": True,
                    "verified_by": "CourtListener",
                    "metadata": {"case_name": "Test v. Case"},
                    "backdrop": "test-backdrop",
                    "error": "",
                },
            },
            # None as citation
            {
                "name": "None as citation",
                "data": {"citation": None},
                "setup_db": lambda: None,
                "expected_status": 400,
                "expected_response": {
                    "citation": "",
                    "verified": False,
                    "error": "No citation provided",
                    "metadata": {},
                    "backdrop": "",
                    "verified_by": "Validation",
                },
            },
            # Invalid JSON
            {
                "name": "Invalid JSON",
                "data": "this is not valid JSON",
                "setup_db": lambda: None,
                "expected_status": 400,
                "expected_response": {"error": "Invalid JSON data"},
            },
        ]

        # Execute test cases
        for case in test_cases:
            with self.subTest(case["name"]):
                logger.info(f"\nTest case: {case['name']}")
                logger.info(f"Request data: {json.dumps(case['data'], indent=2)}")

                try:
                    # Set up any database mocks needed for this test case
                    if "setup_db" in case and callable(case["setup_db"]):
                        case["setup_db"]()

                    # Make the request
                    # Try with and without the /casestrainer prefix
                    endpoints = [
                        "/api/validate-citation",  # Try without prefix first
                        "/casestrainer/api/validate-citation"  # Then with prefix
                    ]
                    
                    response = None
                    for endpoint in endpoints:
                        print(f"Trying endpoint: {endpoint}")
                        if case["name"] == "Invalid JSON":
                            response = self.client.post(
                                endpoint,
                                data=case["data"],
                                content_type="application/json",
                            )
                        else:
                            response = self.client.post(
                                endpoint, 
                                json=case["data"]
                            )
                        if response.status_code != 404:  # If not found, try next endpoint
                            print(f"Using endpoint: {endpoint} (Status: {response.status_code})")
                            break
                    else:
                        self.fail("No valid endpoint found for /api/validate-citation")

                    # Log response
                    logger.info(f"Status code: {response.status_code}")
                    logger.info(f"Headers: {dict(response.headers)}")

                    # Parse response if possible
                    response_data = {}
                    if response.data:
                        try:
                            response_data = response.get_json()
                            logger.info("Response JSON:")
                            logger.info(json.dumps(response_data, indent=2))
                        except Exception as e:
                            logger.warning(
                                f"Could not parse response as JSON: {response.data}"
                            )
                            logger.warning(f"Error: {str(e)}")

                    # Assert status code
                    self.assertEqual(
                        response.status_code,
                        case["expected_status"],
                        f"Expected status {case['expected_status']} but got {response.status_code}",
                    )

                    # Assert response content
                    if "expected_response" in case:
                        for key, expected_value in case["expected_response"].items():
                            self.assertIn(
                                key,
                                response_data,
                                f"Expected key '{key}' not found in response",
                            )
                            self.assertEqual(
                                response_data[key],
                                expected_value,
                                f"Mismatch for key '{key}'. Expected: {expected_value}, Got: {response_data.get(key)}",
                            )

                    logger.info(f"✓ Test case '{case['name']}' passed")

                except Exception as e:
                    logger.error(f"Test case '{case['name']}' failed: {str(e)}")
                    logger.error(traceback.format_exc())
                    raise

    def test_analyze_endpoint(self):
        """Test the /api/analyze endpoint."""
        print("\n" + "=" * 70)
        print("Testing /api/analyze endpoint")
        print("=" * 70)

        test_cases = [
            {
                "name": "Simple citation in text",
                "data": {"text": "This is a test citation: 410 U.S. 113 (1973)"},
                "expected_status": 200,
            },
            {
                "name": "Multiple citations",
                "data": {
                    "text": "This text contains multiple citations: 410 U.S. 113 (1973) and 347 U.S. 483 (1954)"
                },
                "expected_status": 200,
            },
            {
                "name": "Citation with context",
                "data": {
                    "text": "The landmark case Roe v. Wade, 410 U.S. 113 (1973), established important precedents.",
                    "include_context": True,
                },
                "expected_status": 200,
            },
            {"name": "Empty text", "data": {"text": ""}, "expected_status": 400},
        ]

        try:
            for i, test_case in enumerate(test_cases, 1):
                with self.subTest(test_case["name"]):
                    print(f"\n{'*'*50}")
                    print(f"TEST CASE {i}: {test_case['name']}")
                    print(f"Input: {test_case['data']}")

                    # Make the request
                    print("Sending request to /casestrainer/api/analyze...")
                    # Try with and without the /casestrainer prefix
                    endpoints = [
                        "/api/analyze",  # Try without prefix first
                        "/casestrainer/api/analyze"  # Then with prefix
                    ]
                    
                    response = None
                    for endpoint in endpoints:
                        print(f"Trying endpoint: {endpoint}")
                        response = self.client.post(
                            endpoint,
                            json=test_case["data"],
                            headers={"Content-Type": "application/json"},
                        )
                        if response.status_code != 404:  # If not found, try next endpoint
                            print(f"Using endpoint: {endpoint} (Status: {response.status_code})")
                            break
                    else:
                        self.fail("No valid endpoint found for /api/analyze")

                    print(f"Response status code: {response.status_code}")
                    print(f"Response headers: {dict(response.headers)}")

                    # Check the response status code
                    self.assertEqual(
                        response.status_code,
                        test_case["expected_status"],
                        f"Expected status {test_case['expected_status']} but got {response.status_code}",
                    )

                    # Parse the response if it's JSON
                    content_type = response.headers.get("Content-Type", "")
                    if "application/json" in content_type:
                        try:
                            response_data = response.get_json()
                            print(
                                f"Response data: {json.dumps(response_data, indent=2)}"
                            )

                            # Check each expected field in the response
                            if response.status_code == 200:
                                self.assertIn("status", response_data)
                                self.assertIn("results", response_data)
                                self.assertIsInstance(response_data["results"], list)

                                for result in response_data["results"]:
                                    self.assertIsInstance(result, dict)
                                    self.assertIn("citation", result)
                                    self.assertIn("exists", result)
                                    self.assertIn("method", result)

                            print("✓ Test case passed")

                        except Exception as e:
                            error_msg = f"Failed to parse JSON response: {str(e)}\nResponse text: {response.data.decode()}"
                            print(error_msg)
                            self.fail(error_msg)
                    else:
                        error_msg = f"Unexpected content type: {content_type}\nResponse: {response.data.decode()}"
                        print(error_msg)
                        self.fail(error_msg)

        except Exception as e:
            print(f"\nERROR in test execution: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            import traceback

            traceback.print_exc()
            raise
        finally:
            print("\n" + "=" * 70)
            print("TEST COMPLETED")
            print("=" * 70)

    def test_analyze_endpoint(self):
        """Test the /api/analyze endpoint with various inputs."""
        self.logger.info("\n" + "="*80)
        self.logger.info("TESTING ANALYZE ENDPOINT")
        self.logger.info("="*80)
        
        # Log available routes for debugging
        self.logger.debug("Available routes:")
        for rule in self.app.url_map.iter_rules():
            self.logger.debug(f"{rule.endpoint}: {rule.rule} {list(rule.methods - {'OPTIONS', 'HEAD'})}")
        
        # Check available methods for the endpoint
        try:
            print("\nTesting available methods for /api/analyze:")
            with self.client as client:
                response = client.open(
                    method='OPTIONS',
                    path='/api/analyze',
                    headers={"Content-Type": "application/json"}
                )
                print(f"Allowed methods: {response.headers.get('Allow', 'N/A')}")
                print(f"Status code: {response.status_code}")
                print(f"Headers: {dict(response.headers)}")
        except Exception as e:
            print(f"Error getting allowed methods: {e}")
            raise
            
        # Define test cases
        test_cases = [
            {
                "name": "Text with citation",
                "data": {
                    "text": "This is a test case citation: 123 F.3d 456 (9th Cir. 1995)",
                    "source": "test"
                },
                "method": "POST",
                "endpoint": "/api/analyze",
                "expected_status": 200,
                "expected_keys": ["citations", "metadata"]
            },
            {
                "name": "Empty text",
                "data": {
                    "text": "",
                    "source": "test"
                },
                "method": "POST",
                "endpoint": "/api/analyze",
                "expected_status": 200,
                "expected_keys": ["citations", "metadata"]
            },
            {
                "name": "Text with no citations",
                "data": {
                    "text": "This text contains no citations.",
                    "source": "test"
                },
                "method": "POST",
                "endpoint": "/api/analyze",
                "expected_status": 200,
                "expected_keys": ["citations", "metadata"]
            }
        ]
        
        # Run test cases
        for case in test_cases:
            with self.subTest(case["name"]):
                print(f"\nTest case: {case['name']}")
                print(f"Endpoint: {case['endpoint']}")
                print(f"Method: {case['method']}")
                print(f"Data: {json.dumps(case['data'], indent=2)}")
                
                response = None
                try:
                    # Make the request
                    with self.client as client:
                        response = client.open(
                            method=case["method"],
                            path=case['endpoint'],
                            json=case["data"],
                            headers={"Content-Type": "application/json"}
                        )
                    
                    # Print response details
                    print(f"Status code: {response.status_code}")
                    print(f"Response headers: {dict(response.headers)}")

                    try:
                        response_data = response.get_json()
                        print("Response:")
                        print(json.dumps(response_data, indent=2))

                        # Verify response structure
                        required_fields = case.get("expected_keys", [])
                        
                        # Check for expected keys in response
                        for field in required_fields:
                            self.assertIn(field, response_data, f"Response missing required field: {field}")
                            
                        # If we have citations, verify their structure
                        if "citations" in response_data:
                            self.assertIsInstance(
                                response_data["citations"], 
                                list,
                                "Citations should be a list"
                            )
                            
                            # Verify each citation in the list
                            for citation in response_data["citations"]:
                                self.assertIsInstance(
                                    citation, 
                                    dict,
                                    "Each citation should be a dictionary"
                                )
                                self.assertIn(
                                    "text", 
                                    citation,
                                    "Citation is missing 'text' field"
                                )
                                self.assertIn(
                                    "valid", 
                                    citation,
                                    "Citation is missing 'valid' field"
                                )
                                self.assertIn(
                                    "verified", 
                                    citation,
                                    "Citation is missing 'verified' field"
                                )
                        
                        # Check metadata structure if present
                        if "metadata" in response_data:
                            self.assertIsInstance(
                                response_data["metadata"], 
                                dict,
                                "Metadata should be a dictionary"
                            )
                        
                        # Check status code
                        self.assertEqual(
                            response.status_code, 
                            case["expected_status"],
                            f"Expected status {case['expected_status']} but got {response.status_code}"
                        )
                        
                    except json.JSONDecodeError as e:
                        self.fail(f"Failed to decode JSON response: {str(e)}\nRaw response: {response.data if response else 'No response'}")
                    except Exception as e:
                        self.fail(f"Error processing response: {str(e)}")
                        
                except Exception as e:
                    print(f"Error in test case '{case['name']}': {str(e)}")
                    import traceback
                    traceback.print_exc()
                    raise

    def test_verify_citation(self):
        """Test the verify-citation endpoint with various inputs."""
        self.logger.info("\n" + "="*80)
        self.logger.info("TESTING VERIFY-CITATION ENDPOINT")
        self.logger.info("="*80)
        
        # Log available routes for debugging
        self.logger.debug("Available routes:")
        for rule in self.app.url_map.iter_rules():
            self.logger.debug(f"{rule.endpoint}: {rule.rule} {list(rule.methods - {'OPTIONS', 'HEAD'})}")
        
        # Check available methods for the endpoint
        try:
            print("\nTesting available methods for /verify-citation:")
            with self.client as client:
                response = client.open(
                    method='OPTIONS',
                    path='/verify-citation',
                    headers={"Content-Type": "application/json"}
                )
                print(f"Allowed methods: {response.headers.get('Allow', 'N/A')}")
                print(f"Status code: {response.status_code}")
                print(f"Headers: {dict(response.headers)}")
        except Exception as e:
            print(f"Error getting allowed methods: {e}")
            raise
            
        # Define test cases
        test_cases = [
            {
                "name": "Simple citation string",
                "data": {"citation": "410 U.S. 113 (1973)"},
                "method": "POST",
                "endpoint": "/verify-citation",
                "expected_status": 200
            },
            {
                "name": "Citation with case name",
                "data": {"citation": "410 U.S. 113", "case_name": "Roe v. Wade"},
                "method": "POST",
                "endpoint": "/verify-citation",
                "expected_status": 200
            },
            {
                "name": "Empty citation",
                "data": {"citation": ""},
                "method": "POST",
                "endpoint": "/verify-citation",
                "expected_status": 400
            }
        ]
        
        # Run test cases
        for case in test_cases:
            with self.subTest(case["name"]):
                print(f"\nTest case: {case['name']}")
                print(f"Endpoint: {case['endpoint']}")
                print(f"Method: {case['method']}")
                print(f"Data: {json.dumps(case['data'], indent=2)}")
                
                try:
                    # Make the request
                    with self.client as client:
                        response = client.open(
                            method=case["method"],
                            path=case['endpoint'],
                            json=case["data"],
                            headers={"Content-Type": "application/json"}
                        )
                    
                    # Print response details
                    print(f"Status code: {response.status_code}")
                    print(f"Response headers: {dict(response.headers)}")

                    try:
                        response_data = response.get_json()
                        print("Response:")
                        print(json.dumps(response_data, indent=2))

                        # Verify response structure
                        required_fields = [
                            "citation",
                            "verified",
                            "error",
                            "metadata",
                            "backdrop",
                        ]
                        for field in required_fields:
                            self.assertIn(
                                field, response_data, f"Missing required field: {field}"
                            )

                        # Additional checks for successful responses
                        if response.status_code == 200:
                            self.assertIsInstance(response_data["verified"], bool)
                            self.assertIsInstance(response_data["metadata"], dict)

                        # Check status code
                        self.assertEqual(
                            response.status_code,
                            case["expected_status"],
                            f"Expected status {case['expected_status']} but got {response.status_code}"
                        )

                    except Exception as e:
                        print(f"Failed to parse JSON response: {str(e)}")
                        print(f"Raw response: {response.data}")
{{ ... }}
                        
                except Exception as e:
                    print(f"Error in test case '{case['name']}': {str(e)}")
                    import traceback
                    traceback.print_exc()
                    raise


def run_tests():
    """Run all tests and return the test result."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("test.log")],
    )

    logger = logging.getLogger(__name__)
    logger.info("Starting test suite...")

    try:
        # Set up test suite
        test_suite = unittest.TestLoader().loadTestsFromTestCase(TestCitationAPI)

        # Run tests with verbosity
        test_runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        test_result = test_runner.run(test_suite)

        # Log test results
        logger.info(f"Tests run: {test_result.testsRun}")
        logger.info(f"Errors: {len(test_result.errors)}")
        logger.info(f"Failures: {len(test_result.failures)}")
        logger.info(f"Skipped: {len(test_result.skipped)}")

        # Return True if all tests passed, False otherwise
        return test_result.wasSuccessful()
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}", exc_info=True)
        return False


def main():
    print("Starting test execution...")

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("test.log", mode="w"),
        ],
    )

    logger = logging.getLogger(__name__)

    try:
        # Create a test suite
        test_suite = unittest.TestLoader().loadTestsFromTestCase(TestCitationAPI)

        # Run the tests
        test_runner = unittest.TextTestRunner(verbosity=2)
        test_result = test_runner.run(test_suite)

        # Print summary
        print("\n" + "=" * 70)
        print(f"Tests run: {test_result.testsRun}")
        print(f"Errors: {len(test_result.errors)}")
        print(f"Failures: {len(test_result.failures)}")
        print(f"Skipped: {len(test_result.skipped)}")
        print("=" * 70)

        return test_result.wasSuccessful()
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
