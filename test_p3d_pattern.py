#!/usr/bin/env python3
"""
Test script to check if the P.3d regex pattern is matching correctly.
"""

import re

def test_p3d_pattern():
    """Test the P.3d regex pattern."""
    
    print("=== TESTING P.3D PATTERN ===")
    
    # Test text
    test_text = "399 P.3d 1195"
    print(f"Test text: '{test_text}'")
    
    # Pattern from complex_citation_integration.py
    pattern = r'\b(\d+)\s+P\.3d\s+(\d+)\b'
    print(f"Pattern: '{pattern}'")
    
    # Test the pattern
    match = re.search(pattern, test_text)
    if match:
        print(f"✓ Pattern matched!")
        print(f"  Volume: '{match.group(1)}'")
        print(f"  Page: '{match.group(2)}'")
        print(f"  Full match: '{match.group(0)}'")
    else:
        print("✗ Pattern did not match")
        
        # Try without word boundaries
        pattern_no_boundaries = r'(\d+)\s+P\.3d\s+(\d+)'
        print(f"Trying without word boundaries: '{pattern_no_boundaries}'")
        match2 = re.search(pattern_no_boundaries, test_text)
        if match2:
            print(f"✓ Pattern without boundaries matched!")
            print(f"  Volume: '{match2.group(1)}'")
            print(f"  Page: '{match2.group(2)}'")
            print(f"  Full match: '{match2.group(0)}'")
        else:
            print("✗ Still no match")
    
    print("\n=== TESTING IN FULL TEXT CONTEXT ===")
    
    # Test with full text that includes comma
    full_text = "199 Wn. App. 280, 399 P.3d 1195"
    print(f"Full text: '{full_text}'")
    
    # Test the pattern in full text
    match_full = re.search(pattern, full_text)
    if match_full:
        print(f"✓ Pattern matched in full text!")
        print(f"  Volume: '{match_full.group(1)}'")
        print(f"  Page: '{match_full.group(2)}'")
        print(f"  Full match: '{match_full.group(0)}'")
    else:
        print("✗ Pattern did not match in full text")
        
        # Try without word boundaries
        pattern_no_boundaries = r'(\d+)\s+P\.3d\s+(\d+)'
        print(f"Trying without word boundaries: '{pattern_no_boundaries}'")
        match2_full = re.search(pattern_no_boundaries, full_text)
        if match2_full:
            print(f"✓ Pattern without boundaries matched in full text!")
            print(f"  Volume: '{match2_full.group(1)}'")
            print(f"  Page: '{match2_full.group(2)}'")
            print(f"  Full match: '{match2_full.group(0)}'")
        else:
            print("✗ Still no match in full text")

if __name__ == "__main__":
    test_p3d_pattern() 