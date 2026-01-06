#!/usr/bin/env python3
"""
Test the new pattern for Washington citations with pinpoint pages
"""

import re

def test_pattern():
    """Test the new pattern"""
    
    # The new pattern
    pattern = re.compile(
        r"\b(\d+)\s+(?:Wash\.|Wn\.)\s*(?:App\.)\s*2d\s+(\d+)(?:\s*,\s*(\d+))?(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\s*(?:\(\d{4}\))?\b",
        re.IGNORECASE,
    )
    
    # Test citations
    test_cases = [
        "24 Wn. App. 2d 377, 392, 520 P.3d 470 (2022)",
        "24 Wn. App. 2d 377, 520 P.3d 470 (2022)",
        "24 Wn. App. 2d 377, 392 (2022)",
        "76 Wn.2d 733, 458 P.2d 882 (1969)",
    ]
    
    print("Testing Washington citation pattern with pinpoint pages:")
    print()
    
    for test in test_cases:
        match = pattern.search(test)
        if match:
            print(f"✅ Match: {test}")
            print(f"   Groups: {match.groups()}")
            print(f"   Volume: {match.group(1)}")
            print(f"   Page: {match.group(2)}")
            if match.group(3):
                print(f"   Pinpoint: {match.group(3)}")
            if match.group(4) and match.group(5):
                print(f"   Parallel: {match.group(4)} {match.group(5)}")
        else:
            print(f"❌ No match: {test}")
        print()

if __name__ == "__main__":
    test_pattern()
