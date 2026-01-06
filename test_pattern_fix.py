#!/usr/bin/env python3
"""
Test the actual pattern matching
"""

import re

def test_pattern():
    """Test the pattern with actual input"""
    
    # After wn replacement
    text = "24 wash. app. 2d 377"
    print(f"Input: '{text}'")
    
    # Pattern to match
    pattern = r"wn\.?\s+app\.?\s+(\d*)d"
    print(f"Pattern: {pattern}")
    
    # But we already replaced wn with wash!
    # So we need a pattern that matches wash. app. 2d
    pattern2 = r"wash\.?\s+app\.?\s+(\d*)d"
    print(f"Pattern 2: {pattern2}")
    
    match = re.search(pattern2, text)
    print(f"Match: {match}")
    
    if match:
        print(f"Groups: {match.groups()}")
        replacement = r"wash app \1d"
        result = re.sub(pattern2, replacement, text)
        print(f"Result: '{result}'")

if __name__ == "__main__":
    test_pattern()
