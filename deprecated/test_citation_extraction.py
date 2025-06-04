#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for citation extraction functionality.
"""

import os
import sys
import json
import logging
import traceback
from pprint import pprint

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Print Python and path info for debugging
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

# Try to import the required modules
try:
    from src.enhanced_validator_production import extract_citations, clean_case_name

    print("Successfully imported extract_citations and clean_case_name")
except ImportError as e:
    print(f"Failed to import required modules: {e}")
    print("Current sys.path:")
    for p in sys.path:
        print(f"  {p}")
    traceback.print_exc()
    sys.exit(1)

# Set up logging to console only
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


# Add a simple test function to verify basic functionality
def test_sanity():
    """Run a simple sanity test to verify basic functionality."""
    print("\n=== Running Sanity Test ===")
    test_text = "See Roe v. Wade, 410 U.S. 113 (1973)"
    try:
        result, _ = extract_citations(test_text, return_debug=True)
        print(f"Extracted {len(result['confirmed_citations'])} citations")
        for i, citation in enumerate(result["confirmed_citations"], 1):
            print(f"  {i}. {citation['citation_text']}")
        return True
    except Exception as e:
        print(f"Sanity test failed: {e}")
        traceback.print_exc()
        return False


def test_clean_case_name():
    """Test the clean_case_name function."""
    print("\n=== Testing clean_case_name ===")

    test_cases = [
        ("See Roe v. Wade", "Roe v. Wade"),
        ("Roe v. Wade", "Roe v. Wade"),
        ("Roe vs Wade", "Roe v. Wade"),
        ("Roe versus Wade", "Roe v. Wade"),
        ("Further, Roe v. Wade", "Roe v. Wade"),
        ("Similarly, Roe v. Wade", "Roe v. Wade"),
        ("U.S. v. Caraway", "U.S. v. Caraway"),
        ("United States v. Caraway", "U.S. v. Caraway"),
        ("US v. Caraway", "U.S. v. Caraway"),
        ("See, e.g., Roe v. Wade", "Roe v. Wade"),
        ("Id. at 123", "Id. at 123"),
    ]

    passed = 0
    failed = 0

    for input_text, expected in test_cases:
        result = clean_case_name(input_text)
        status = result == expected

        if status:
            print(f"✓ PASS: '{input_text}' -> '{result}'")
            passed += 1
        else:
            print(f"✗ FAIL: '{input_text}'")
            print(f"  - Got:      '{result}'")
            print(f"  - Expected: '{expected}'")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_extract_citations():
    """Test the extract_citations function with various inputs."""
    print("\n=== Testing extract_citations ===")

    test_cases = [
        {
            "name": "Standard citation with pin cite",
            "input": "See Roe v. Wade, 410 U.S. 113, 120 (1973).",
            "expected": {
                "case_name": "Roe v. Wade",
                "citation_text": "Roe v. Wade, 410 U.S. 113, 120",
                "has_pin_cite": True,
            },
        },
        {
            "name": "U.S. v. Caraway with pin cite",
            "input": "See U.S. v. Caraway, 1301.",
            "expected": {
                "case_name": "U.S. v. Caraway",
                "citation_text": "U.S. v. Caraway, 1301",
                "has_pin_cite": True,
            },
        },
        {
            "name": "Multiple citations in text",
            "input": "See Roe v. Wade, 410 U.S. 113 (1973); U.S. v. Caraway, 1301; and Brown v. Board, 347 U.S. 483 (1954).",
            "expected_count": 3,
        },
        {
            "name": "Citation with signal",
            "input": "See also Miranda v. Arizona, 384 U.S. 436 (1966).",
            "expected": {
                "case_name": "Miranda v. Arizona",
                "citation_text": "Miranda v. Arizona, 384 U.S. 436",
                "has_pin_cite": False,
            },
        },
        {
            "name": "Invalid citation",
            "input": "This is not a citation.",
            "expected_count": 0,
        },
    ]

    passed = 0
    failed = 0

    for test_case in test_cases:
        print(f"\n{'='*80}")
        print(f"TEST: {test_case['name']}")
        print(f"INPUT: {test_case['input']}")

        try:
            # Extract citations with debug info
            result, debug_info = extract_citations(
                test_case["input"], return_debug=True
            )

            # Print citation info
            print(f"\nFOUND {len(result['confirmed_citations'])} CITATIONS:")
            for i, citation in enumerate(result["confirmed_citations"], 1):
                print(f"  {i}. {citation['citation_text']}")
                print(f"     Case: {citation.get('case_name', 'N/A')}")
                print(f"     Source: {citation['source']}")
                if "metadata" in citation and citation["metadata"].get("has_pin_cite"):
                    print(
                        f"     Pin cite: {citation['metadata'].get('pin_cite', 'N/A')}"
                    )

            # Check expected results
            if "expected_count" in test_case:
                if len(result["confirmed_citations"]) == test_case["expected_count"]:
                    print(
                        f"✓ PASS: Found expected {test_case['expected_count']} citations"
                    )
                    passed += 1
                else:
                    print(
                        f"✗ FAIL: Expected {test_case['expected_count']} citations, got {len(result['confirmed_citations'])}"
                    )
                    failed += 1
                    continue

            if "expected" in test_case:
                if not result["confirmed_citations"]:
                    print("✗ FAIL: No citations found")
                    failed += 1
                    continue

                citation = result["confirmed_citations"][0]
                all_checks_passed = True

                # Check case name
                if "case_name" in test_case["expected"]:
                    expected = test_case["expected"]["case_name"]
                    actual = citation.get("case_name")
                    if actual == expected:
                        print(f"✓ PASS: Case name matches: '{actual}'")
                    else:
                        print(
                            f"✗ FAIL: Case name mismatch. Expected: '{expected}', Got: '{actual}'"
                        )
                        all_checks_passed = False

                # Check citation text
                if "citation_text" in test_case["expected"]:
                    expected = test_case["expected"]["citation_text"]
                    actual = citation["citation_text"]
                    if actual == expected:
                        print(f"✓ PASS: Citation text matches: '{actual}'")
                    else:
                        print(
                            f"✗ FAIL: Citation text mismatch. Expected: '{expected}', Got: '{actual}'"
                        )
                        all_checks_passed = False

                # Check pin cite
                if "has_pin_cite" in test_case["expected"]:
                    expected = test_case["expected"]["has_pin_cite"]
                    actual = citation.get("metadata", {}).get("has_pin_cite", False)
                    if actual == expected:
                        status = "has" if expected else "does not have"
                        print(f"✓ PASS: Citation {status} a pin cite as expected")
                    else:
                        print(
                            f"✗ FAIL: Pin cite mismatch. Expected: {expected}, Got: {actual}"
                        )
                        all_checks_passed = False

                if all_checks_passed:
                    print("✓ ALL CHECKS PASSED")
                    passed += 1
                else:
                    failed += 1
            else:
                passed += 1

        except Exception as e:
            print(f"✗ ERROR: {str(e)}")
            import traceback

            traceback.print_exc()
            failed += 1

    print(f"\nResults: {passed} tests passed, {failed} tests failed")
    return failed == 0


def main():
    """Run all tests and return exit code."""
    print("=== Starting Citation Extraction Tests ===\n")

    # First run a sanity test
    if not test_sanity():
        print("\n✗ SANITY TEST FAILED - Aborting further tests")
        return 1

    # Test case name cleaning
    print("\n" + "=" * 80)
    print("STARTING CASE NAME CLEANING TESTS")
    print("=" * 80)
    clean_case_passed = test_clean_case_name()

    # Test citation extraction
    print("\n" + "=" * 80)
    print("STARTING CITATION EXTRACTION TESTS")
    print("=" * 80)
    extraction_passed = test_extract_citations()

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Case Name Cleaning: {'✓ PASSED' if clean_case_passed else '✗ FAILED'}")
    print(f"Citation Extraction: {'✓ PASSED' if extraction_passed else '✗ FAILED'}")

    all_passed = clean_case_passed and extraction_passed
    if all_passed:
        print("\n✓ ALL TESTS PASSED ✓")
    else:
        print("\n✗ SOME TESTS FAILED ✗")

    # Return non-zero exit code if any test failed
    return 0 if all_passed else 1


if __name__ == "__main__":
    main()
