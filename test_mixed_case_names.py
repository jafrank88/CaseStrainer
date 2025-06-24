#!/usr/bin/env python3
"""
Test script to verify case name extraction for various patterns including mixed-case names
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from extract_case_name import extract_case_name_from_context

def test_case_name_extraction():
    """Test case name extraction for various patterns"""
    
    test_cases = [
        # Basic cases
        ("U.S. v. Caraway , 534 F.3d 1290", "U.S. v. Caraway"),
        ("Smith v. Jones , 123 U.S. 456", "Smith v. Jones"),
        
        # Mixed-case with connectors
        ("Board of Education v. Brown , 347 U.S. 483", "Board of Education v. Brown"),
        ("City of New York v. Smith , 456 F.3d 789", "City of New York v. Smith"),
        ("Department of Energy v. Wyoming , 2006 WL 3801910", "Department of Energy v. Wyoming"),
        
        # Abbreviations
        ("U.S. v. Caraway , 534 F.3d 1290", "U.S. v. Caraway"),
        ("N.Y. v. Smith , 123 F.3d 456", "N.Y. v. Smith"),
        
        # Multi-word parties
        ("United States v. Smith , 456 U.S. 789", "United States v. Smith"),
        ("State of California v. Brown , 123 F.3d 456", "State of California v. Brown"),
    ]
    
    print("Testing case name extraction for various patterns:")
    print("=" * 60)
    
    all_passed = True
    
    for context, expected in test_cases:
        print(f"\nContext: {context}")
        print(f"Expected: {expected}")
        
        # Extract case name
        extracted = extract_case_name_from_context(context, "")
        
        print(f"Extracted: {extracted}")
        
        # Check if it matches
        if extracted == expected:
            print("✓ PASS")
        else:
            print("✗ FAIL")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED!")
    else:
        print("SOME TESTS FAILED - NEEDS IMPROVEMENT")
    
    return all_passed

if __name__ == "__main__":
    test_case_name_extraction() 