#!/usr/bin/env python3
"""
Test Washington state citation patterns.
"""

import re

def test_washington_citation_patterns():
    """Test Washington state citation patterns."""
    print("=" * 80)
    print("TESTING WASHINGTON CITATION PATTERNS")
    print("=" * 80)
    
    # Test cases with various spacing and formatting
    test_cases = [
        # Wn patterns
        "123Wn.2d456",
        "123 Wn.2d 456",
        "123Wn.2d 456",
        "123 Wn.2d456",
        "123-Wn.-2d-456",
        "123Wn2d456",
        "123 Wn 2d 456",
        "123WnApp456",
        "123 Wn. App. 456",
        "123WnApp 456",
        "123 WnApp456",
        
        # Wash patterns
        "123Wash.2d456",
        "123 Wash.2d 456",
        "123Wash.2d 456",
        "123 Wash.2d456",
        "123-Wash.-2d-456",
        "123Wash2d456",
        "123 Wash 2d 456",
        "123WashApp456",
        "123 Wash. App. 456",
        "123WashApp 456",
        "123 WashApp456",
        
        # With different series
        "123Wn.3d456",
        "123 Wn.4th 456",
        "123Wash.3d 456",
        "123 Wash.4th 456"
    ]
    
    # Base patterns for Washington state reporters
    wn_patterns = [
        # Wn.2d, Wn.3d, Wn.4th, etc.
        r'(\d+)[\s-]*(Wn\.?)[\s-]*(2d|3d|4th|App\.?|\d+)[\s-]*(\d+)',
        # Wn (no series)
        r'(\d+)[\s-]*(Wn\.?)[\s-]*(\d+)',
    ]
    
    # Washington patterns (full word)
    wash_patterns = [
        # Wash.2d, Wash.3d, Wash.4th, etc.
        r'(\d+)[\s-]*(Wash\.?)[\s-]*(2d|3d|4th|App\.?|\d+)[\s-]*(\d+)',
        # Wash (no series)
        r'(\d+)[\s-]*(Wash\.?)[\s-]*(\d+)',
    ]
    
    # Combine all patterns
    patterns = [re.compile(p, re.IGNORECASE) for p in wn_patterns + wash_patterns]
    
    # Test each pattern against each test case
    for test in test_cases:
        print(f"\nTesting: {test}")
        matched = False
        
        for i, pattern in enumerate(patterns):
            match = pattern.search(test)
            if match:
                matched = True
                print(f"  ✓ Matched pattern {i+1}: {pattern.pattern}")
                print(f"     Groups: {match.groups()}")
                
        if not matched:
            print("  ✗ No match")
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_washington_citation_patterns()
