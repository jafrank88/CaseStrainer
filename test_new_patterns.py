#!/usr/bin/env python3
"""
Test the new patterns
"""

import re

def test_new_patterns():
    """Test the new patterns"""
    
    text = "Spokane Cnty. v. Wash. Dep't of Fish & Wildlife, 192 Wn.2d 453, 430 P.3d 655 (2018)"
    
    # Test the new patterns
    patterns = [
        # Pattern 1: Original with 2d
        r'([A-Z][a-zA-Z\',\.\&]*(?:\s+[A-Z][a-zA-Z\',\.\&]*)*)\s+v\.\s+([A-Z][a-zA-Z\',\.\&]*(?:\s+[A-Z][a-zA-Z\',\.\&]*)*),\s*(\d+)\s+Wn\.(?:2d\s+\d+)?',
        # Pattern 1b: More flexible Washington pattern - non-greedy
        r'([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+)*?)\s+v\.\s+([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+)*?),\s*(\d+)\s+Wn\.',
        # Pattern 2: Original with 3d
        r'([A-Z][a-zA-Z\',\.\&]*(?:\s+[A-Z][a-zA-Z\',\.\&]*)*)\s+v\.\s+([A-Z][a-zA-Z\',\.\&]*(?:\s+[A-Z][a-zA-Z\',\.\&]*)*),\s*(\d+)\s+P\.(?:3d\s+\d+)?',
        # Pattern 2b: More flexible Pacific pattern - non-greedy
        r'([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+)*?)\s+v\.\s+([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+)*?),\s*(\d+)\s+P\.',
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
    test_new_patterns()
