#!/usr/bin/env python3
"""
Debug the character class issue
"""

import re

def debug_character_class():
    """Debug the character class issue"""
    
    text = "Spokane Cnty. v. Wash. Dep't of Fish & Wildlife, 192 Wn.2d 453, 430 P.3d 655 (2018)"
    
    # Test different character classes
    patterns = [
        # Original character class
        r'([A-Z][a-zA-Z\',\.\&]*(?:\s+[A-Z][a-zA-Z\',\.\&]*)*)',
        # More flexible character class
        r'([A-Z][a-zA-Z\',\.\&]*(?:\s+[A-Z][a-zA-Z\',\.\&]*)*)',
        # Even more flexible
        r'([A-Z][a-zA-Z\',\.\&]*(?:\s+[A-Z][a-zA-Z\',\.\&]*)*)',
        # Test with specific text
        r'(Spokane Cnty\.)',
        # Test with simpler pattern
        r'([A-Z][a-zA-Z\',\.\&]+)',
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
    
    # Test the specific problematic part
    print("=== Testing specific parts ===")
    test_parts = [
        "Spokane Cnty.",
        "Wash. Dep't of Fish & Wildlife",
        "192 Wn.2d 453",
        "430 P.3d 655"
    ]
    
    for part in test_parts:
        print(f"Testing: '{part}'")
        pattern = r'([A-Z][a-zA-Z\',\.\&]*(?:\s+[A-Z][a-zA-Z\',\.\&]*)*)'
        matches = list(re.finditer(pattern, part, re.IGNORECASE))
        print(f"Matches: {len(matches)}")
        for match in matches:
            print(f"  '{match.group(0)}'")
        print()

if __name__ == "__main__":
    debug_character_class()

