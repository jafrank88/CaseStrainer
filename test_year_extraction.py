#!/usr/bin/env python3
"""
Test the new year extraction function with various citation patterns.
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from case_name_extraction_core import extract_year_after_last_citation

def test_year_extraction():
    """Test the year extraction function with various patterns."""
    
    test_cases = [
        # Basic patterns
        {
            "text": "Smith v. Jones, 123 Wn.2d 456 (1999)",
            "expected": "1999",
            "description": "name, citation, year"
        },
        {
            "text": "Smith v. Jones, 123 Wn.2d 456, 459 (1999)",
            "expected": "1999", 
            "description": "name, citation, page, year"
        },
        {
            "text": "Smith v. Jones, 123 Wn.2d 456, 789 P.2d 123 (1999)",
            "expected": "1999",
            "description": "name, citation, citation, year (parallel citations)"
        },
        {
            "text": "Smith v. Jones, 123 Wn.2d 456, 459, 789 P.2d 123 (1999)",
            "expected": "1999",
            "description": "name, citation, page, citation, year"
        },
        {
            "text": "Smith v. Jones, 123 Wn.2d 456, 789 P.2d 123, 456 (1999)",
            "expected": "1999",
            "description": "name, citation, citation, page, year"
        },
        # More complex patterns
        {
            "text": "In re Estate of Johnson, 123 Wn.2d 456, 789 P.2d 123, 456 F.3d 789 (2019)",
            "expected": "2019",
            "description": "multiple parallel citations"
        },
        {
            "text": "State v. Brown, 123 Wn.2d 456, at 459, 789 P.2d 123 (2020)",
            "expected": "2020",
            "description": "with 'at' pinpoint citation"
        },
        # Edge cases
        {
            "text": "Smith v. Jones, 123 Wn.2d 456 (1999), cert. denied",
            "expected": "1999",
            "description": "with additional text after year"
        },
        {
            "text": "Smith v. Jones, 123 Wn.2d 456, 789 P.2d 123 (1999) (en banc)",
            "expected": "1999",
            "description": "with en banc designation"
        },
        # No year cases
        {
            "text": "Smith v. Jones, 123 Wn.2d 456",
            "expected": "",
            "description": "no year present"
        },
        {
            "text": "Smith v. Jones, 123 Wn.2d 456, 789 P.2d 123",
            "expected": "",
            "description": "parallel citations but no year"
        },
        # Different year formats
        {
            "text": "Smith v. Jones, 123 Wn.2d 456, 789 P.2d 123 2021",
            "expected": "2021",
            "description": "year without parentheses"
        },
        {
            "text": "Smith v. Jones, 123 Wn.2d 456, 789 P.2d 123 (2021)",
            "expected": "2021",
            "description": "year in parentheses"
        }
    ]
    
    print("Testing year extraction function...")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        text = test_case["text"]
        expected = test_case["expected"]
        description = test_case["description"]
        
        result = extract_year_after_last_citation(text)
        
        if result == expected:
            print(f"✓ Test {i}: {description}")
            print(f"  Text: {text}")
            print(f"  Expected: '{expected}', Got: '{result}'")
            passed += 1
        else:
            print(f"✗ Test {i}: {description}")
            print(f"  Text: {text}")
            print(f"  Expected: '{expected}', Got: '{result}'")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False

if __name__ == "__main__":
    test_year_extraction() 