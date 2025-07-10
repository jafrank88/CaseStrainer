#!/usr/bin/env python3
"""
Debug script to test the validation regex pattern
"""

import re

def test_validation_regex():
    """Test the validation regex pattern that's failing."""
    
    # The problematic regex from unified_citation_processor.py
    pattern = r'\b(?:v\.|vs\.|versus)\b'
    
    test_cases = [
        "State v. Smith",
        "Department of Ecology v. PUD No. 1", 
        "In re Estate of Smith",
        "Brown v. Board of Education",
        "This is not a case name",
        "v. Smith",
        "Smith v.",
        "v. v. Smith"
    ]
    
    print("=== Testing Validation Regex ===\n")
    print(f"Pattern: {pattern}")
    print()
    
    for case_name in test_cases:
        match = re.search(pattern, case_name, re.IGNORECASE)
        print(f"'{case_name}' -> {'✅ Match' if match else '❌ No match'}")
        if match:
            print(f"  Matched: '{match.group()}'")
    
    print("\n=== Testing with word boundaries removed ===\n")
    
    # Test without word boundaries
    pattern_no_boundaries = r'(?:v\.|vs\.|versus)'
    
    for case_name in test_cases:
        match = re.search(pattern_no_boundaries, case_name, re.IGNORECASE)
        print(f"'{case_name}' -> {'✅ Match' if match else '❌ No match'}")
        if match:
            print(f"  Matched: '{match.group()}'")
    
    print("\n=== Testing with different word boundary approach ===\n")
    
    # Test with space-based boundaries
    pattern_space_boundaries = r'(?<=\s)(?:v\.|vs\.|versus)(?=\s)'
    
    for case_name in test_cases:
        match = re.search(pattern_space_boundaries, case_name, re.IGNORECASE)
        print(f"'{case_name}' -> {'✅ Match' if match else '❌ No match'}")
        if match:
            print(f"  Matched: '{match.group()}'")

if __name__ == "__main__":
    test_validation_regex() 