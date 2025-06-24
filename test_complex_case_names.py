#!/usr/bin/env python3
"""
Test script for complex case name extraction with periods and commas.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from extract_case_name import extract_case_name_from_text, clean_case_name

def test_complex_case_names():
    """Test complex case name extraction scenarios."""
    
    print("Testing complex case name extraction...\n")
    
    # Test cases
    test_cases = [
        {
            "name": "Complex case with M.D., P.C.",
            "text": "John Eric Jacoby, M.D., P.C. v. Loper Associates, Inc., 249 A.D.2d 277 (2d Dep't 1998)",
            "citation": "249 A.D.2d 277",
            "expected": "John Eric Jacoby, M.D., P.C. v. Loper Associates, Inc."
        },
        {
            "name": "In re case name",
            "text": "In re Estate of John Doe, 456 U.S. 789",
            "citation": "456 U.S. 789",
            "expected": "In re Estate of John Doe"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print(f"Text: {test_case['text']}")
        print(f"Citation: {test_case['citation']}")
        
        # Test the full extraction function
        result = extract_case_name_from_text(test_case['text'], test_case['citation'])
        print(f"Extracted case name: {result}")

        # Print debug info for the line and before_citation
        line = test_case['text']
        citation = test_case['citation']
        if citation in line:
            before_citation = line.split(citation)[0].strip()
            print(f"[TEST DEBUG] Full line: {repr(line)}")
            print(f"[TEST DEBUG] Before citation: {repr(before_citation)}")

        # Test the clean_case_name function on the expected result
        cleaned_expected = clean_case_name(test_case['expected'])
        print(f"Cleaned expected: {cleaned_expected}")
        
        # Check if result matches expected
        if result == test_case['expected'] or result == cleaned_expected:
            print("✓ PASS")
        else:
            print("✗ FAIL - Expected:", test_case['expected'])
            print("   Got:", result)
        
        print("-" * 80)

if __name__ == "__main__":
    test_complex_case_names() 