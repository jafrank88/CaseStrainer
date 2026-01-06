#!/usr/bin/env python3
"""
Debug the citation validation pattern
"""

import re

def test_pattern():
    pattern = r"(?:U\.?S\.?|F\.?(?:2d|3d|4th)?|S\.?Ct\.?|L\.?Ed\.?(?:\s*2d)?|[A-Z]{2,}\.?\s*(?:App\.?\s*Ct\.?|Sup\.?\s*Ct\.?|Ct\.?\s*App\.?))"
    
    test_cases = [
        "146 F.4th 165",
        "123 F.2d 456", 
        "789 F.3d 123",
        "523 U.S. 751",
        "100 F. 200",
    ]
    
    for citation in test_cases:
        match = re.search(pattern, citation, re.IGNORECASE)
        print(f"{citation}: {'✓' if match else '✗'}")
        if match:
            print(f"  Matched: {match.group(0)}")
        
        # Also test volume/page pattern
        vol_page = re.search(r"\d+\s+[A-Za-z\.]+\s+\d+", citation)
        print(f"  Volume/Page: {'✓' if vol_page else '✗'}")
        print()

if __name__ == "__main__":
    test_pattern()
