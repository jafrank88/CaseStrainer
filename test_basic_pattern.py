#!/usr/bin/env python3
"""
Test a very basic pattern
"""

import re

def test_basic_pattern():
    """Test a very basic pattern"""
    
    text = "Spokane Cnty. v. Wash. Dep't of Fish & Wildlife, 192 Wn.2d 453, 430 P.3d 655 (2018)"
    
    # Test very basic patterns
    patterns = [
        # Just match the case name part
        r'(Spokane Cnty\.)\s+v\.\s+(Wash\. Dep\'t of Fish & Wildlife)',
        # Match with volume
        r'(Spokane Cnty\.)\s+v\.\s+(Wash\. Dep\'t of Fish & Wildlife),\s*(\d+)\s+Wn\.',
        # More flexible
        r'([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+)*)\s+v\.\s+([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+)*),\s*(\d+)\s+Wn\.',
        # Test without the & character
        r'([A-Z][a-zA-Z\',\.]+(?:\s+[A-Z][a-zA-Z\',\.]+)*)\s+v\.\s+([A-Z][a-zA-Z\',\.]+(?:\s+[A-Z][a-zA-Z\',\.]+)*),\s*(\d+)\s+Wn\.',
    ]
    
    print(f"Testing text: {text}")
    print()
    
    for i, pattern in enumerate(patterns, 1):
        print(f"Pattern {i}: {pattern}")
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        print(f"Matches: {len(matches)}")
        for match in matches:
            print(f"  '{match.group(0)}'")
            print(f"  Groups: {match.groups()}")
        print()

if __name__ == "__main__":
    test_basic_pattern()

