#!/usr/bin/env python3
"""
Simple debug script for case name extraction.
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

# Import the extraction function
try:
    from src.case_name_extraction_core import extract_case_name_precise
    print("✅ Successfully imported extract_case_name_precise")
except ImportError as e:
    print(f"❌ Error importing extract_case_name_precise: {e}")
    sys.exit(1)

def test_extraction(text, citation, expected):
    print("\n" + "="*80)
    print(f"Testing citation: {citation}")
    print("-" * 40)
    print(f"Input text: {text}")
    
    try:
        result = extract_case_name_precise(text, citation, debug=True)
        print(f"\nExtracted: {result}")
        print(f"Expected:  {expected}")
        
        if result.lower() == expected.lower():
            print("✅ Test PASSED")
            return True
        else:
            print("❌ Test FAILED")
            return False
    except Exception as e:
        print(f"\n❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    test_cases = [
        {
            "name": "Simple State v. Defendant",
            "text": "Some other text State v. Smith, 123 Wn.2d 456 (2020) and more text",
            "citation": "123 Wn.2d 456",
            "expected": "State v. Smith"
        },
        {
            "name": "Lakehaven case with ampersand",
            "text": "some text before Lakehaven Water & Sewer Dist. v. City of Fed. Way, 195 Wn.2d 742, 773, 466 P.3d 213 (2020) some text after",
            "citation": "195 Wn.2d 742",
            "expected": "Lakehaven Water & Sewer Dist. v. City of Fed. Way"
        }
    ]
    
    print("Starting debug tests...\n")
    
    passed = 0
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['name']}")
        if test_extraction(test['text'], test['citation'], test['expected']):
            passed += 1
    
    print("\n" + "="*80)
    print(f"TEST SUMMARY: {passed} passed, {len(test_cases) - passed} failed")
    print("="*80)
    
    return 0 if passed == len(test_cases) else 1

if __name__ == "__main__":
    sys.exit(main())
