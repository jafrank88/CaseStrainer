#!/usr/bin/env python3
"""
Test script to check if F.3d citations are being recognized correctly.
"""

import re

def test_f3d_patterns():
    """Test various F.3d citation patterns."""
    
    test_citation = "534 F.3d 1290"
    print(f"Testing citation: '{test_citation}'")
    print("=" * 50)
    
    # Patterns from the backend
    patterns = {
        'f3d_basic': r'\b(\d+)\s+F\.3d\s+(\d+)\b',
        'f3d_flexible': r'\b(\d+)\s+F\.3d\s+(\d+)\b',
        'f3d_with_spaces': r'\b(\d+)\s+F\.\s*3d\s+(\d+)\b',
        'f3d_alt': r'\b(\d+)\s+F\.3d\s+(\d+)\b',
        'federal_reporter': r'\b(\d+)\s+F\.(?:\s*(\d*(?:st|nd|rd|th|d)))?\s+(\d+)\b',
    }
    
    for name, pattern in patterns.items():
        print(f"Testing pattern '{name}': {pattern}")
        match = re.search(pattern, test_citation, re.IGNORECASE)
        if match:
            print(f"  ✓ MATCH: {match.groups()}")
        else:
            print(f"  ✗ NO MATCH")
        print()
    
    # Test with context
    test_text = f"In the case of Smith v. Jones, {test_citation}, the court held..."
    print(f"Testing in context: '{test_text}'")
    print("=" * 50)
    
    for name, pattern in patterns.items():
        print(f"Testing pattern '{name}' in context:")
        match = re.search(pattern, test_text, re.IGNORECASE)
        if match:
            print(f"  ✓ MATCH: {match.groups()}")
        else:
            print(f"  ✗ NO MATCH")
        print()

if __name__ == "__main__":
    test_f3d_patterns() 