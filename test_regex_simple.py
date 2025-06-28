#!/usr/bin/env python3
"""
Simple debug script to test the regex pattern.
"""

import re

def test_regex():
    citation = "199 Wn. App. 280, 283, 399 P.3d 1195 (2017)"
    
    # Test the basic citation pattern
    single_citation = r"\d+\s+[A-Za-z\.]+\s+\d+(?:-\d+)?"
    print(f"Single citation pattern: {single_citation}")
    print(f"Matches '199 Wn. App. 280': {bool(re.match(single_citation, '199 Wn. App. 280'))}")
    print(f"Matches '399 P.3d 1195': {bool(re.match(single_citation, '399 P.3d 1195'))}")
    print()
    
    # Test pinpoint pattern
    pinpoint = r"\d+(?:-\d+)?"
    print(f"Pinpoint pattern: {pinpoint}")
    print(f"Matches '283': {bool(re.match(pinpoint, '283'))}")
    print()
    
    # Test a simpler approach - just check if it contains valid citations
    print("Testing if citation contains valid citation patterns:")
    citation_patterns = [
        r'\d+\s+[A-Za-z\.]+\s+\d+',  # Basic citation
        r'\d+\s+Wn\.\s*App\.\s+\d+',  # Washington App
        r'\d+\s+P\.\d+\s+\d+',        # Pacific reporter
    ]
    
    for pattern in citation_patterns:
        if re.search(pattern, citation):
            print(f"  ✓ Found match with pattern: {pattern}")
        else:
            print(f"  ✗ No match with pattern: {pattern}")

if __name__ == "__main__":
    test_regex() 