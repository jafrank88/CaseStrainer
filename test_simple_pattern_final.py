#!/usr/bin/env python3
"""
Test the final simple pattern
"""

import re

def test_simple_pattern_final():
    """Test the final simple pattern"""
    
    text = "Spokane Cnty. v. Wash. Dep't of Fish & Wildlife, 192 Wn.2d 453, 430 P.3d 655 (2018)"
    
    # Test the simple pattern
    pattern = r'([A-Z][^,]+?)\s+v\.\s+([A-Z][^,]+?),\s*(\d+)\s+Wn\.'
    
    print(f"Testing text: {text}")
    print(f"Pattern: {pattern}")
    print()
    
    matches = list(re.finditer(pattern, text, re.IGNORECASE))
    print(f"Matches: {len(matches)}")
    for match in matches:
        print(f"  '{match.group(0)}'")
        print(f"  Groups: {match.groups()}")
    print()

if __name__ == "__main__":
    test_simple_pattern_final()

