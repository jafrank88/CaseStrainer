#!/usr/bin/env python3
"""
Debug the volume/page pattern more carefully
"""

import re

def test_pattern():
    # Test different patterns
    patterns = [
        r"\d+\s+[A-Za-z\.]+\s+\d+",  # Original
        r"\d+\s+[A-Za-z\.]+\s*\d+",  # Allow optional space
        r"\d+\s+[A-Za-z\.]+\d+",     # No space required
        r"\d+\s+[A-Za-z\.]+\.*\s*\d+",  # Multiple dots
    ]
    
    test_cases = [
        "146 F.4th 165",
        "123 F.2d 456", 
        "789 F.3d 123",
        "523 U.S. 751",
        "100 F. 200",
    ]
    
    for i, pattern in enumerate(patterns):
        print(f"\nPattern {i+1}: {pattern}")
        for citation in test_cases:
            match = re.search(pattern, citation)
            print(f"  {citation}: {'✓' if match else '✗'}")

if __name__ == "__main__":
    test_pattern()
