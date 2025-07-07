#!/usr/bin/env python3
"""
Test the new precise case name extraction function to ensure it doesn't capture too much text.
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from extract_case_name import extract_case_name_precise

def test_precise_name_extraction():
    """Test the precise case name extraction function."""
    
    test_cases = [
        # Standard cases - should extract just the case name
        {
            "context": "Smith v. Jones, 123 Wn.2d 456 (1999)",
            "citation": "123 Wn.2d 456",
            "expected": "Smith v. Jones",
            "description": "Standard case name"
        },
        {
            "context": "State v. Johnson, 456 P.3d 789 (2020)",
            "citation": "456 P.3d 789", 
            "expected": "State v. Johnson",
            "description": "State case"
        },
        {
            "context": "In re Smith Estate, 789 Wn. App. 123 (2018)",
            "citation": "789 Wn. App. 123",
            "expected": "In re Smith Estate",
            "description": "In re case"
        },
        {
            "context": "Estate of Johnson, 321 P.2d 456 (2017)",
            "citation": "321 P.2d 456",
            "expected": "Estate of Johnson", 
            "description": "Estate case"
        },
        # Cases with extra text - should NOT capture too much
        {
            "context": "The court in Smith v. Jones, 123 Wn.2d 456 (1999) held that...",
            "citation": "123 Wn.2d 456",
            "expected": "Smith v. Jones",
            "description": "Case with leading text"
        },
        {
            "context": "Smith v. Jones, 123 Wn.2d 456 (1999) and other cases...",
            "citation": "123 Wn.2d 456", 
            "expected": "Smith v. Jones",
            "description": "Case with trailing text"
        },
        # Complex cases with multiple citations
        {
            "context": "Smith v. Jones, 123 Wn.2d 456, 789 P.2d 123 (1999)",
            "citation": "789 P.2d 123",
            "expected": "Smith v. Jones",
            "description": "Parallel citations"
        },
        # Edge cases - should handle gracefully
        {
            "context": "No case name here, just 123 Wn.2d 456 (1999)",
            "citation": "123 Wn.2d 456",
            "expected": "",
            "description": "No case name present"
        },
        {
            "context": "Too much text before Smith v. Jones, 123 Wn.2d 456 (1999)",
            "citation": "123 Wn.2d 456",
            "expected": "Smith v. Jones", 
            "description": "Text too far back (should still work)"
        }
    ]
    
    print("Testing precise case name extraction...")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print(f"Context: '{test_case['context']}'")
        print(f"Citation: '{test_case['citation']}'")
        print(f"Expected: '{test_case['expected']}'")
        
        # Extract the case name
        result = extract_case_name_precise(test_case['context'], test_case['citation'])
        print(f"Result: '{result}'")
        
        # Check if result matches expected
        if result == test_case['expected']:
            print("✅ PASS")
            passed += 1
        else:
            print("❌ FAIL")
            failed += 1
            
        # Additional check: if we got a result, make sure it's not too long
        if result and len(result.split()) > 8:
            print("⚠️  WARNING: Result seems too long!")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed. Review the results above.")
    
    return failed == 0

if __name__ == "__main__":
    success = test_precise_name_extraction()
    sys.exit(0 if success else 1) 