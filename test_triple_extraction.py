#!/usr/bin/env python3
"""
Simple test for extract_case_name_triple_from_text function.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

print("Starting test script...")
print(f"Python path: {sys.path}")

try:
    from src.extract_case_name import extract_case_name_triple_from_text
    print("Successfully imported extract_case_name_triple_from_text")
except Exception as e:
    print(f"Import error: {e}")
    sys.exit(1)

def test_triple_extraction():
    """Test the extract_case_name_triple_from_text function."""
    
    test_cases = [
        {
            "text": "The court held that quoting Ellis v. City of Seattle, 142 Wash. 2d 450, 13 P.3d 1065 (2000), establishes the standard.",
            "citation": "142 Wash. 2d 450",
            "canonical": "Ellis v. City of Seattle",
            "description": "Basic case name extraction"
        },
        {
            "text": "As stated in Smith v. Jones, 123 U.S. 456 (2020), the principle applies.",
            "citation": "123 U.S. 456",
            "canonical": "Smith v. Jones",
            "description": "Simple case name with 'As stated in'"
        },
        {
            "text": "The judge in Brown v. Board of Education, 347 U.S. 483 (1954), ruled that...",
            "citation": "347 U.S. 483",
            "canonical": "Brown v. Board of Education",
            "description": "Case name with 'The judge in'"
        },
        {
            "text": "See Roe v. Wade, 410 U.S. 113 (1973), for the precedent.",
            "citation": "410 U.S. 113",
            "canonical": "Roe v. Wade",
            "description": "Case name with 'See'"
        },
        {
            "text": "the trial court's findings are not sufficient to satisfy GR 15 or Seattle Times Co. v. Ishikawa, 97 Wn.2d 30, 640 P.2d 716 (1982).",
            "citation": "97 Wn.2d 30",
            "canonical": "Seattle Times Co. v. Ishikawa",
            "description": "Ishikawa citation with minimal context"
        }
    ]

    print("Testing extract_case_name_triple_from_text function...")
    print("=" * 60)
    
    all_passed = True
    
    for idx, case in enumerate(test_cases):
        print(f"\nTest {idx+1}: {case['description']}")
        print(f"Text: {case['text']}")
        print(f"Citation: {case['citation']}")
        print(f"Canonical: {case['canonical']}")
        # Call with debug=True to print debug output
        result = extract_case_name_triple_from_text(case['text'], case['citation'], case['canonical'], debug=True)
        print("Result:")
        print(f"  Canonical name: {result['canonical_name']}")
        print(f"  Extracted name: {result['extracted_name']}")
        print(f"  Hinted name: {result['hinted_name']}")
        
        # Basic validation
        if result['canonical_name'] == case['canonical']:
            print("  ✓ Canonical name matches")
        else:
            print(f"  ✗ Canonical name mismatch: expected '{case['canonical']}', got '{result['canonical_name']}'")
            all_passed = False
            
        if result['extracted_name']:
            print("  ✓ Extracted name found")
        else:
            print("  ✗ No extracted name found")
            all_passed = False
            
        if result['hinted_name']:
            print("  ✓ Hinted name found")
        else:
            print("  ⚠ No hinted name found (this might be expected)")
        
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed!")
    
    return all_passed

if __name__ == '__main__':
    print("Running main test...")
    success = test_triple_extraction()
    print(f"Test completed with success: {success}")
    sys.exit(0 if success else 1)

# Add a debug run for Doe P v. Thurston County
print("\nDebug run for Doe P v. Thurston County:")
debug_text = '... records must be released." John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017) (Doe I), modified on other grounds on remand, No. 48000-0-II (Wash. Ct. App. Oct. 2, 2018) (Doe II) (unpublished), ...'
debug_citation = '199 Wn. App. 280'
debug_canonical = 'Doe P V Thurston County'
from src.extract_case_name import extract_case_name_triple_from_text
extract_case_name_triple_from_text(debug_text, debug_citation, debug_canonical, debug=True) 