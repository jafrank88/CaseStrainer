#!/usr/bin/env python3
"""
Debug script to test Carlson case name extraction specifically.
"""

import re

def test_carlson_pattern():
    """Test the Carlson case name extraction specifically."""
    
    # Test text with Carlson case
    test_text = "Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011)"
    
    print("=== TESTING CARLSON CASE NAME EXTRACTION ===")
    print(f"Test text: {test_text}")
    print()
    
    # Pattern 1 from the function
    pattern1 = r'\b([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\s+v\.\s+(.+?)(?=,\s*\d|\s*\(|$)'
    
    print("Pattern 1 test:")
    matches = list(re.finditer(pattern1, test_text, re.IGNORECASE))
    print(f"  Found {len(matches)} matches:")
    for i, match in enumerate(matches):
        print(f"    {i+1}. Group 1 (before v.): '{match.group(1)}'")
        print(f"       Group 2 (after v.): '{match.group(2)}'")
        case_name = f"{match.group(1)} v. {match.group(2)}"
        print(f"       Full extracted: '{case_name}'")
    print()

if __name__ == "__main__":
    test_carlson_pattern() 