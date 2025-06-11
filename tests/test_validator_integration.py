#!/usr/bin/env python3
"""
Integration tests for the Enhanced Validator functionality in CaseStrainer.

This script tests the core functionality of the enhanced validator, including:
- Batch citation validation
- Text analysis and citation extraction
- Error handling and edge cases
- Integration with the CourtListener API
"""

import os
import sys
import logging
import unittest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("validator_integration_test.log", mode="w"),
    ],
)
logger = logging.getLogger(__name__)

# Add the src directory to the Python path
project_root = str(Path(__file__).parent.absolute())
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    from src.enhanced_validator_production import (
        validate_citations_batch,
        analyze_text,
        extract_citations,
        validate_extracted_citations,
    )

    IMPORT_SUCCESS = True
except ImportError as e:
    logger.error(f"Failed to import enhanced validator modules: {e}")
    IMPORT_SUCCESS = False

# Test data
TEST_CITATIONS = [
    # Standard Supreme Court citation
    "384 U.S. 436",  # Miranda v. Arizona
    # Federal Reporter citation
    "534 F.3d 1290",  # United States v. Alisal Water Corp.
    # State court citation
    "123 P.3d 1",  # Example state citation
    # Invalid citation
    "123 F.999 9999",
    # Short form citation
    "Miranda, 384 U.S. at 439",
]

SAMPLE_TEXT = """
In Miranda v. Arizona, 384 U.S. 436 (1966), the Supreme Court held that 
the Fifth Amendment requires law enforcement officials to advise suspects 
of their right to remain silent and to obtain an attorney during interrogations.

In the case of United States v. Alisal Water Corp., 534 F.3d 1290 (9th Cir. 2008),
the court addressed issues of water rights under federal law.

An example of an invalid citation would be 123 F.999 9999 which doesn't exist.
"""


class TestEnhancedValidatorIntegration(unittest.TestCase):
    """Integration tests for the Enhanced Validator functionality"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before any tests are run"""
        if not IMPORT_SUCCESS:
            raise unittest.SkipTest("Could not import required modules")

        # Create a temporary directory for test files
        cls.test_dir = tempfile.mkdtemp()
        cls.sample_file = os.path.join(cls.test_dir, "sample.txt")

        # Write sample text to file
        with open(cls.sample_file, "w", encoding="utf-8") as f:
            f.write(SAMPLE_TEXT)

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests have run"""
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)

    def test_validate_citations_batch(self):
        """Test batch validation of citations"""
        logger.info("Testing validate_citations_batch with multiple citations")

        # Prepare test data
        citations = [{"citation_text": cite} for cite in TEST_CITATIONS]

        # Call the function
        results, stats = validate_citations_batch(citations)

        # Assert basic structure
        self.assertIsInstance(results, list)
        self.assertIsInstance(stats, dict)
        self.assertEqual(len(results), len(TEST_CITATIONS))

        # Check each result
        for i, result in enumerate(results):
            self.assertIn("citation_text", result)
            self.assertIn("validation_status", result)
            logger.info(f"{result['citation_text']} - {result['validation_status']}")

        # Check stats
        self.assertIn("total", stats)
        self.assertIn("valid", stats)
        self.assertIn("invalid", stats)
        logger.info(f"Validation stats: {stats}")

    def test_analyze_text(self):
        """Test text analysis and citation extraction"""
        logger.info("Testing analyze_text with sample legal text")

        # Call the function
        result = analyze_text(SAMPLE_TEXT, batch_process=True, return_debug=True)

        # Assert basic structure
        self.assertIsInstance(result, dict)
        self.assertIn("citations", result)
        self.assertIn("stats", result)

        # Check citations
        self.assertGreater(len(result["citations"]), 0)
        for citation in result["citations"]:
            self.assertIn("citation_text", citation)
            self.assertIn("validation_status", citation)

        logger.info(f"Found {len(result['citations'])} citations in sample text")

    def test_extract_citations(self):
        """Test citation extraction from text"""
        logger.info("Testing extract_citations function")

        # Call the function
        citations, debug_info = extract_citations(
            SAMPLE_TEXT, return_debug=True, batch_process=False
        )

        # Assert basic structure
        self.assertIsInstance(citations, list)
        self.assertIsInstance(debug_info, dict)
        self.assertGreater(len(citations), 0)

        # Check citation format
        for citation in citations:
            self.assertIn("citation_text", citation)
            self.assertIn("context", citation)

        logger.info(f"Extracted {len(citations)} citations with debug info")

    def test_validate_extracted_citations(self):
        """Test validation of extracted citations"""
        logger.info("Testing validate_extracted_citations function")

        # First extract citations
        citations, _ = extract_citations(
            SAMPLE_TEXT, return_debug=False, batch_process=True
        )

        # Then validate them
        result = validate_extracted_citations(citations, return_debug=True)

        # Assert basic structure
        self.assertIsInstance(result, dict)
        self.assertIn("citations", result)
        self.assertIn("stats", result)

        # Check validation results
        self.assertGreater(len(result["citations"]), 0)
        for citation in result["citations"]:
            self.assertIn("citation_text", citation)
            self.assertIn("validation_status", citation)

        logger.info(f"Validated {len(result['citations'])} citations")


def run_tests() -> Dict[str, Any]:
    """Run all tests and return results as a dictionary"""
    if not IMPORT_SUCCESS:
        return {"status": "error", "message": "Failed to import required modules"}

    # Configure test runner
    test_loader = unittest.TestLoader()
    test_suite = test_loader.loadTestsFromTestCase(TestEnhancedValidatorIntegration)

    # Run tests
    result = unittest.TestResult()
    test_suite.run(result)

    # Format results
    return {
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "was_successful": result.wasSuccessful(),
        "test_cases": [
            {
                "name": str(test),
                "success": test
                not in [f[0] for f in (result.failures + result.errors)],
            }
            for test in test_suite
        ],
    }


if __name__ == "__main__":
    # Run tests directly
    print("Running Enhanced Validator Integration Tests...\n" + "=" * 50 + "\n")

    # Run tests and get results
    test_results = run_tests()

    # Print summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Tests Run: {test_results['tests_run']}")
    print(f"Failures: {test_results['failures']}")
    print(f"Errors: {test_results['errors']}")
    print(f"Skipped: {test_results['skipped']}")
    print(f"\nOverall: {'SUCCESS' if test_results['was_successful'] else 'FAILED'}")

    # Print detailed results
    if not test_results["was_successful"]:
        print("\nFailed/Error Tests:")
        for test in test_results["test_cases"]:
            if not test["success"]:
                print(f"- {test['name']}")

    print("\n" + "=" * 50 + "\n")

    # Exit with appropriate status code
    sys.exit(0 if test_results["was_successful"] else 1)
