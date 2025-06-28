#!/usr/bin/env python3
"""
Test script to isolate and fix the regex issue in complex citation integration.
"""

import re

def test_regex_patterns():
    """Test the regex patterns to find the bad escape sequence."""
    
    # Test the problematic text
    text = "John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017)"
    
    print(f"Testing text: {text}")
    print("=" * 60)
    
    # Test each pattern individually
    patterns = {
        'case_name_pattern': r'\b([A-Z][A-Za-z\s\.,&\'\"\(\)]+v\.\s+[A-Z][A-Za-z\s\.,&\'\"\(\)]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
        'pinpoint_pattern': r',\s*(\d+)(?=\s*[,;]|\s*\(|\s*$)',
        'parallel_citation_pattern': r'([A-Z][A-Za-z\s\.,&\'\"\(\)]+v\.\s+[A-Z][A-Za-z\s\.,&\'\"\(\)]+?)\s*,\s*([^,]+?)(?:\s*,\s*(\d+))?(?:\s*,\s*([^,]+?))?(?:\s*,\s*(\d+))?(?:\s*,\s*([^,]+?))?(?:\s*,\s*(\d+))?\s*\((\d{4})\)',
        'docket_pattern': r'No\.\s*([0-9\-]+)',
        'history_pattern': r'\(([A-Za-z\s]+(?:I|II|III|IV|V|VI|VII|VIII|IX|X))\)',
        'status_pattern': r'\((unpublished|published|memorandum|per\s+curiam)\)',
        'year_pattern': r'\((\d{4})\)'
    }
    
    for name, pattern in patterns.items():
        try:
            print(f"Testing {name}:")
            result = re.search(pattern, text, re.IGNORECASE)
            if result:
                print(f"  ✓ Match found: {result.groups()}")
            else:
                print(f"  ✗ No match")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        print()

if __name__ == "__main__":
    test_regex_patterns() 