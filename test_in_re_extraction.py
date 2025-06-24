#!/usr/bin/env python3
"""
Test script for the enhanced "in re" case name extraction functionality.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from extract_case_name import extract_in_re_case_name_from_context, extract_case_name_from_text

def test_in_re_extraction():
    """Test various "in re" case name extraction scenarios."""
    
    print("Testing 'in re' case name extraction...\n")
    
    # Test cases
    test_cases = [
        {
            "name": "Basic 'in re' case",
            "text": "In re Smith, 123 F.3d 456",
            "citation": "123 F.3d 456",
            "expected": "In re Smith"
        },
        {
            "name": "'in re' with multiple words",
            "text": "In re Estate of John Doe, 456 U.S. 789",
            "citation": "456 U.S. 789",
            "expected": "In re Estate of John Doe"
        },
        {
            "name": "'in re' within 15 words",
            "text": "The court considered the matter of In re Johnson Corporation bankruptcy proceedings, 789 F.2d 123",
            "citation": "789 F.2d 123",
            "expected": "In re Johnson Corporation"
        },
        {
            "name": "'in re' with intervening citation (should not match)",
            "text": "In re First Case, 111 F.2d 222, and then In re Second Case, 333 F.4d 444",
            "citation": "333 F.4d 444",
            "expected": "In re Second Case"
        },
        {
            "name": "Case insensitive 'in re'",
            "text": "IN RE WASHINGTON STATE, 555 Wash. 666",
            "citation": "555 Wash. 666",
            "expected": "IN RE WASHINGTON STATE"
        },
        {
            "name": "'in re' with punctuation",
            "text": "In re Smith & Associates, Inc., 777 S.Ct. 888",
            "citation": "777 S.Ct. 888",
            "expected": "In re Smith & Associates, Inc."
        },
        {
            "name": "No 'in re' present",
            "text": "Smith v. Jones, 999 F.3d 111",
            "citation": "999 F.3d 111",
            "expected": None  # Should not find "in re" case name
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print(f"Text: {test_case['text']}")
        print(f"Citation: {test_case['citation']}")
        
        # Test the specialized function
        result = extract_in_re_case_name_from_context(test_case['text'], test_case['citation'])
        print(f"Specialized result: {result}")
        
        # Test the full extraction function
        full_result = extract_case_name_from_text(test_case['text'], test_case['citation'])
        print(f"Full extraction result: {full_result}")
        
        # Check if expected result is found
        if test_case['expected']:
            if result == test_case['expected'] or full_result == test_case['expected']:
                print("✓ PASS")
            else:
                print("✗ FAIL - Expected:", test_case['expected'])
        else:
            if not result and not full_result:
                print("✓ PASS (correctly found no 'in re' case)")
            else:
                print("✗ FAIL - Should not have found 'in re' case")
        
        print("-" * 60)

if __name__ == "__main__":
    test_in_re_extraction() 