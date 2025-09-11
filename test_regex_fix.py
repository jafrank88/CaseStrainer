#!/usr/bin/env python3
"""
Test the fixed Washington State regex pattern.
"""

import re

def test_fixed_washington_pattern():
    """Test the fixed Washington State regex pattern."""
    
    # The fixed pattern from citation_extractor.py
    fixed_pattern = r'\b\d+\s+Wn\.\s*\d*d?\s+\d+\b'
    compiled = re.compile(fixed_pattern, re.IGNORECASE)
    
    # Test citations with different spacing
    test_citations = [
        "2 Wn. 3d\n329",      # Space between Wn. and 3d, newline before 329
        "2 Wn. 3d 329",       # Space between Wn. and 3d, space before 329
        "2 Wn.3d\n329",       # NO space between Wn. and 3d, newline before 329
        "2 Wn.3d 329",        # NO space between Wn. and 3d, space before 329
        "169 Wn.2d\n815",     # Multi-digit volume with newline
        "169 Wn.2d 815",      # Multi-digit volume with space
    ]
    
    print("=== Testing Fixed Washington State Pattern ===")
    print(f"Pattern: {fixed_pattern}")
    print()
    
    for citation in test_citations:
        match = compiled.search(citation)
        print(f"Citation: '{citation}'")
        print(f"  Match: {'✅ YES' if match else '❌ NO'}")
        if match:
            print(f"    Matched: '{match.group(0)}'")
        print()
    
    # Test with actual text from the user's example
    test_text = """We review statutory interpretation de novo. DeSean v. Sanger, 2 Wn. 3d 
329, 334-35, 536 P.3d 191 (2023). State v. Ervin, 169 Wn.2d 
815, 820, 239 P.3d 354 (2010)."""
    
    print("=== Testing with Actual Text ===")
    print(f"Text length: {len(test_text)} characters")
    print()
    
    matches = list(compiled.finditer(test_text))
    print(f"Found {len(matches)} matches:")
    for match in matches:
        print(f"  '{match.group(0)}' at position {match.start()}-{match.end()}")
    
    print()
    print("🎯 EXPECTED: Should find both '2 Wn. 3d 329' and '169 Wn.2d 815'")
    print("💡 FIX: Added \\s* to allow optional spaces between 'Wn.' and volume number")

if __name__ == "__main__":
    test_fixed_washington_pattern()
