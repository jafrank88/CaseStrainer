#!/usr/bin/env python3
"""
Test script to check the regex patterns in _clean_citation_for_lookup.
"""

import re

def test_regex_patterns():
    """Test the regex patterns in _clean_citation_for_lookup."""
    
    print("=== TESTING REGEX PATTERNS ===")
    
    # Test citations
    test_citations = [
        "399 P.3d 1195",
        "399 P. 3d 1195",
        "199 Wn. App. 280"
    ]
    
    for citation in test_citations:
        print(f"\nTesting citation: '{citation}'")
        
        # Test the first regex pattern
        pattern1 = r'(\d+)([A-Za-z]+\.)'
        match1 = re.search(pattern1, citation)
        if match1:
            print(f"  Pattern 1 matched: '{match1.group(0)}'")
            print(f"    Group 1: '{match1.group(1)}'")
            print(f"    Group 2: '{match1.group(2)}'")
            result1 = re.sub(pattern1, r'\1 \2', citation)
            print(f"    After substitution: '{result1}'")
        else:
            print(f"  Pattern 1 did not match")
        
        # Test the second regex pattern
        pattern2 = r'([A-Za-z]+\.)(\d+)'
        match2 = re.search(pattern2, citation)
        if match2:
            print(f"  Pattern 2 matched: '{match2.group(0)}'")
            print(f"    Group 1: '{match2.group(1)}'")
            print(f"    Group 2: '{match2.group(2)}'")
            result2 = re.sub(pattern2, r'\1 \2', citation)
            print(f"    After substitution: '{result2}'")
        else:
            print(f"  Pattern 2 did not match")

if __name__ == "__main__":
    test_regex_patterns() 