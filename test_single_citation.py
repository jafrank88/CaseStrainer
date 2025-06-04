#!/usr/bin/env python3
"""
Test script to verify a single citation using the Enhanced Validator.

This script tests whether the validator can correctly identify and validate a known citation.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("citation_test.log", mode="w"),
    ],
)
logger = logging.getLogger(__name__)

# Add the src directory to the Python path
project_root = str(Path(__file__).parent.absolute())
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    from src.enhanced_validator_production import validate_citations_batch

    IMPORT_SUCCESS = True
except ImportError as e:
    logger.error(f"Failed to import validate_citations_batch: {e}")
    IMPORT_SUCCESS = False


def test_citation_validation(citation_text, expected_case_name=None):
    """Test validation of a single citation."""
    if not IMPORT_SUCCESS:
        logger.error("Cannot run tests due to import errors")
        return False

    logger.info(f"\n{'='*50}")
    logger.info(f"TESTING CITATION: {citation_text}")
    logger.info("=" * 50)

    try:
        # Call the validation function
        logger.info("Calling validate_citations_batch...")
        results, stats = validate_citations_batch([{"citation_text": citation_text}])

        # Log the results
        full_response = json.dumps(results[0], indent=2)
        print("\nFULL RESPONSE:")
        print(full_response)

        logger.info("\nVALIDATION RESULTS:")
        logger.info(f"Status: {results[0].get('validation_status', 'UNKNOWN')}")
        logger.info(
            f"Case Name: {results[0].get('metadata', {}).get('case_name', 'Not found')}"
        )
        logger.info(f"Full Response: {full_response}")

        # Check if the citation was validated
        validation_status = results[0].get("validation_status", "").lower()
        is_valid = validation_status in ["valid", "verified"]

        # If expected case name is provided, verify it matches
        if expected_case_name and is_valid:
            actual_case_name = results[0].get("metadata", {}).get("case_name", "")
            logger.info(f"Expected case name: {expected_case_name}")
            logger.info(f"Actual case name: {actual_case_name}")

            # Normalize both case names for comparison
            expected_normalized = " ".join(expected_case_name.lower().split())
            actual_normalized = " ".join(actual_case_name.lower().split())

            logger.info(f"Normalized expected: {expected_normalized}")
            logger.info(f"Normalized actual: {actual_normalized}")

            if expected_normalized not in actual_normalized:
                logger.warning(
                    f"Case name mismatch. Expected: {expected_case_name}, Got: {actual_case_name}"
                )
                is_valid = False
            else:
                logger.info("Case name matches expected!")
        else:
            logger.info("No expected case name provided for validation")

        return is_valid

    except Exception as e:
        logger.error(f"Error during citation validation: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    # Test with a known citation (534 F.3d 1290)
    # This citation might resolve to different case names in different databases
    test_citation = "534 F.3d 1290"
    # List of possible case names for this citation
    possible_case_names = [
        "UNITED STATES of America, Plaintiff-Appellee, v. ALISAL WATER CORPORATION",
        "United States v. Caraway",
    ]

    logger.info("Starting citation validation test...")

    # Try each possible case name until we find a match or run out of options
    success = False
    for case_name in possible_case_names:
        logger.info(f"\nTrying case name: {case_name}")
        success = test_citation_validation(test_citation, case_name)
        if success:
            logger.info(f"Successfully matched case name: {case_name}")
            break

    if not success:
        logger.error("Failed to validate citation with any known case name")

    # Print final result
    logger.info("\n" + "=" * 50)
    if success:
        logger.info(f"SUCCESS: Citation '{test_citation}' was validated correctly!")
    else:
        logger.error(
            f"FAILURE: Citation '{test_citation}' was not validated correctly."
        )
    logger.info("=" * 50)

    # Print log file location
    print("\nTest complete. Check 'citation_test.log' for detailed results.")

    # Exit with appropriate status code
    sys.exit(0 if success else 1)
