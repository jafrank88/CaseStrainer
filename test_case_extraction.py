#!/usr/bin/env python3
"""
Test case name extraction with the updated patterns.
"""

import sys
from src.case_name_extraction_core import extract_case_name_precise

def run_test_case(test_name, test_text, citation, expected, debug=False):
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"Citation: {citation}")
    print("-"*40)
    
    # Extract the case name
    case_name = extract_case_name_precise(test_text, citation, debug=debug)
    
    # Print results
    print(f"Extracted: {case_name}")
    print(f"Expected:  {expected}")
    
    # Simple validation
    if case_name.lower() == expected.lower():
        print("✅ Test PASSED")
        return True
    else:
        print("❌ Test FAILED")
        return False

def test_case_extraction():
    test_cases = [
        {
            "name": "Lakehaven case with ampersand and abbreviations",
            "text": """
            some text before Lakehaven Water & Sewer Dist. v. City of Fed. Way, 195 Wn.2d 742, 773, 466 P.3d 213 (2020)
            some text after
            """,
            "citation": "195 Wn.2d 742",
            "expected": "Lakehaven Water & Sewer Dist. v. City of Fed. Way"
        },
        {
            "name": "Simple State v. Defendant format",
            "text": """
            Some other text State v. Smith, 123 Wn.2d 456 (2020) and more text
            """,
            "citation": "123 Wn.2d 456",
            "expected": "State v. Smith"
        },
        {
            "name": "Multi-word plaintiff and defendant",
            "text": """
            As held in Washington State Department of Transportation v. Seattle Tunnel Partners, 195 Wn.2d 742, 773, 466 P.3d 213 (2020)
            """,
            "citation": "195 Wn.2d 742",
            "expected": "Washington State Department of Transportation v. Seattle Tunnel Partners"
        },
        {
            "name": "In re format",
            "text": """
            The court in In re Marriage of Smith, 123 Wn.2d 456 (2020) held that...
            """,
            "citation": "123 Wn.2d 456",
            "expected": "In re Marriage of Smith"
        },
        {
            "name": "Estate of format",
            "text": """
            As discussed in Estate of Johnson v. Smith, 123 Wn.2d 456 (2020), the court...
            """,
            "citation": "123 Wn.2d 456",
            "expected": "Estate of Johnson v. Smith"
        }
    ]
    
    print("Starting case name extraction tests...")
    print("="*80)
    
    # Get debug flag from command line
    debug = "--debug" in sys.argv
    
    # Run all test cases
    passed = 0
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}/{len(test_cases)}")
        if run_test_case(
            test["name"],
            test["text"],
            test["citation"],
            test["expected"],
            debug=debug
        ):
            passed += 1
    
    # Print summary
    print("\n" + "="*80)
    print(f"TEST SUMMARY: {passed} passed, {len(test_cases) - passed} failed")
    print("="*80)
    
    return passed == len(test_cases)

if __name__ == "__main__":
    success = test_case_extraction()
    sys.exit(0 if success else 1)
