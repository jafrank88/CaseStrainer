import unittest
import json
import os
import sys
import logging
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("test_citation_validation.log", mode="w"),
    ],
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.app_final_vue import create_app


class TestCitationValidation(unittest.TestCase):
    """Test cases for citation validation endpoints."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before running any tests."""
        cls.logger = logging.getLogger(__name__)
        cls.logger.info("\n" + "=" * 70)
        cls.logger.info("Setting up test environment...")

        try:
            # Create a test Flask app
            cls.app = create_app()

            # Configure the app for testing
            cls.app.config.update(
                TESTING=True,
                WTF_CSRF_ENABLED=False,
                SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
                SQLALCHEMY_TRACK_MODIFICATIONS=False,
            )

            # Create a test client
            cls.client = cls.app.test_client()
            cls.logger.info("Test Flask application created")

            # Create a test directory for file operations
            cls.test_dir = tempfile.mkdtemp()
            cls.logger.info(f"Created test directory: {cls.test_dir}")

            # Push an application context
            cls.app_context = cls.app.app_context()
            cls.app_context.push()

            cls.logger.info("Test environment setup complete" + "\n" + "=" * 70)

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

            # Remove the test directory
            if hasattr(cls, "test_dir") and os.path.exists(cls.test_dir):
                shutil.rmtree(cls.test_dir)
                cls.logger.info(f"Removed test directory: {cls.test_dir}")

            cls.logger.info("Test environment cleaned up")
        except Exception as e:
            cls.logger.error(f"Error during test teardown: {str(e)}")
            raise

    def setUp(self):
        """Set up before each test method."""
        self.logger.info("\n" + "-" * 60)
        self.logger.info(f"Running test: {self._testMethodName}")

    def tearDown(self):
        """Clean up after each test method."""
        self.logger.info(f"Completed test: {self._testMethodName}")

    @patch(
        "src.enhanced_multi_source_verifier.EnhancedMultiSourceVerifier.verify_citation"
    )
    @patch("src.enhanced_multi_source_verifier.sqlite3")
    def test_enhanced_validate_citation(self, mock_sqlite3, mock_verify_citation):
        """Test the enhanced_validate_citation endpoint with various input formats."""
        # Set up mock database
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_sqlite3.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Set up mock cursor to handle different queries
        def mock_execute(query, *args):
            if "SELECT * FROM citations" in query:
                mock_cursor.fetchone.return_value = None  # No cached results by default
            return mock_cursor

        mock_cursor.execute.side_effect = mock_execute

        # Configure the mock verify_citation method
        def mock_verify_citation_side_effect(citation_text, case_name=None):
            if citation_text == "123 F.3d 456 (9th Cir. 2020)":
                return {
                    "citation": "123 F.3d 456",
                    "verified": False,
                    "verified_by": "",
                    "metadata": {},
                    "backdrop": "",
                    "error": "",
                }
            elif citation_text == "410 U.S. 113 (1973)":
                return {
                    "citation": "410 U.S. 113 (1973)",
                    "verified": True,
                    "verified_by": "CourtListener",
                    "metadata": {"case_name": "Roe v. Wade"},
                    "backdrop": "test-backdrop",
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
            # Valid citation format
            {
                "name": "Simple citation string (Federal Reporter)",
                "data": {"citation": "123 F.3d 456 (9th Cir. 2020)"},
                "expected_status": 200,
                "expected_response": {
                    "citation": "123 F.3d 456 (9th Cir. 2020)",
                    "verified": False,
                    "verified_by": "",
                    "metadata": {},
                    "backdrop": "",
                    "error": "",
                },
            },
            # Empty citation
            {
                "name": "Empty citation",
                "data": {"citation": ""},
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
                "expected_status": 200,
                "expected_response": {
                    "citation": "410 U.S. 113 (1973)",
                    "verified": True,
                    "verified_by": "CourtListener",
                    "metadata": {"case_name": "Roe v. Wade"},
                    "backdrop": "test-backdrop",
                    "error": "",
                },
            },
            # Missing citation field
            {
                "name": "Missing citation field",
                "data": {},
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
        ]

        # Run each test case
        for case in test_cases:
            with self.subTest(case["name"]):
                self.logger.info(f"\nTest case: {case['name']}")
                self.logger.info(f"Request data: {json.dumps(case['data'], indent=2)}")

                # Make the request to the endpoint
                response = self.client.post(
                    "/casestrainer/api/verify-citation",
                    data=json.dumps(case["data"]),
                    content_type="application/json",
                )

                # Log the response
                self.logger.info(f"Status code: {response.status_code}")
                try:
                    response_data = response.get_json()
                    self.logger.info(
                        f"Response data: {json.dumps(response_data, indent=2)}"
                    )
                except Exception as e:
                    self.logger.error(f"Failed to parse response as JSON: {str(e)}")
                    response_data = {}

                # Assert the response status code
                self.assertEqual(
                    response.status_code,
                    case["expected_status"],
                    f"Expected status {case['expected_status']} but got {response.status_code}",
                )

                # If we expect a successful response, check the response data
                if response.status_code == 200:
                    self.assertIsNotNone(
                        response_data, "Response data should not be None"
                    )
                    for key, expected_value in case["expected_response"].items():
                        self.assertIn(
                            key, response_data, f"Response missing key: {key}"
                        )
                        self.assertEqual(
                            response_data[key],
                            expected_value,
                            f"Mismatch for key '{key}': expected {expected_value}, got {response_data.get(key)}",
                        )


if __name__ == "__main__":
    # Run tests with detailed output
    import sys

    # Create a test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestCitationValidation)

    # Run the test suite with a test runner that shows detailed output
    runner = unittest.TextTestRunner(verbosity=2, failfast=True)
    result = runner.run(suite)

    # Exit with non-zero code if tests failed
    sys.exit(not result.wasSuccessful())
