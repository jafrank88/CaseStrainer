#!/usr/bin/env python3
"""
Debug script to test case name extraction regex patterns.
"""

import re

def test_case_name_regex():
    """Test the current regex patterns with problematic cases."""
    
    # Test cases that are failing
    test_cases = [
        "Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022)",
        "Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)",
        "Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011)"
    ]
    
    # Current regex pattern from the code
    pattern = r'([A-Z][A-Za-z0-9&.,\'\\-]*(?:\s+[A-Za-z0-9&.,\'\\-]+)*\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9&.,\'\\-]*(?:\s+[A-Za-z0-9&.,\'\\-]+)*)(?:\s*,\s*(?:LLC|Inc\.|Corp\.|Co\.|Ltd\.|L\.L\.C\.|P\.C\.|LLP|PLLC|PC|LP|PL|PLC))?(?:,|\(|$)'
    
    print("Testing current regex pattern:")
    print(f"Pattern: {pattern}")
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test case {i}: {test_case}")
        match = re.search(pattern, test_case)
        if match:
            print(f"  Match: '{match.group(1)}'")
            if len(match.groups()) > 1 and match.group(2):
                print(f"  Business suffix: '{match.group(2)}'")
        else:
            print("  No match!")
        print()
    
    # Test improved pattern
    print("Testing improved pattern:")
    improved_pattern = r'([A-Z][A-Za-z0-9&.,\'\\-]*(?:\s+[A-Za-z0-9&.,\'\\-]+)*\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9&.,\'\\-]*(?:\s+[A-Za-z0-9&.,\'\\-]+)*)(?:\s*,\s*(?:LLC|Inc\.|Corp\.|Co\.|Ltd\.|L\.L\.C\.|P\.C\.|LLP|PLLC|PC|LP|PL|PLC))?'
    print(f"Improved pattern: {improved_pattern}")
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test case {i}: {test_case}")
        match = re.search(improved_pattern, test_case)
        if match:
            print(f"  Match: '{match.group(1)}'")
            if len(match.groups()) > 1 and match.group(2):
                print(f"  Business suffix: '{match.group(2)}'")
        else:
            print("  No match!")
        print()

if __name__ == "__main__":
    test_case_name_regex() 