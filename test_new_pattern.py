#!/usr/bin/env python3
"""
Test the new regex pattern that handles newlines and spaces.
"""

import re

def test_new_pattern():
    """Test the new regex pattern."""
    
    # Test the current pattern
    current_pattern = r'\b\d+\s+Wn\.\d+d[\s\n]+\d+\b'
    current_compiled = re.compile(current_pattern, re.IGNORECASE)
    
    # Test a pattern that allows optional spaces between Wn. and 3d
    flexible_pattern = r'\b\d+\s+Wn\.\s*\d+d[\s\n]+\d+\b'
    flexible_compiled = re.compile(flexible_pattern, re.IGNORECASE)
    
    # Test citations with different spacing
    test_citations = [
        "2 Wn. 3d\n329",      # Space between Wn. and 3d, newline before 329
        "2 Wn. 3d 329",       # Space between Wn. and 3d, space before 329
        "2 Wn.3d\n329",       # NO space between Wn. and 3d, newline before 329
        "2 Wn.3d 329",        # NO space between Wn. and 3d, space before 329
        "169 Wn.2d\n815",     # Multi-digit volume with newline
        "169 Wn.2d 815",      # Multi-digit volume with space
    ]
    
    print("=== Testing Current vs Flexible Patterns ===")
    print(f"Current pattern: {current_pattern}")
    print(f"Flexible pattern: {flexible_pattern}")
    print()
    
    for citation in test_citations:
        current_match = current_compiled.search(citation)
        flexible_match = flexible_compiled.search(citation)
        
        print(f"Citation: '{citation}'")
        print(f"  Current pattern: {'✅ YES' if current_match else '❌ NO'}")
        print(f"  Flexible pattern: {'✅ YES' if flexible_match else '❌ NO'}")
        
        if current_match:
            print(f"    Current match: '{current_match.group(0)}'")
        if flexible_match:
            print(f"    Flexible match: '{flexible_match.group(0)}'")
        print()
    
    # Test with actual text
    test_text = """We review statutory interpretation de novo. DeSean v. Sanger, 2 Wn. 3d 
329, 334-35, 536 P.3d 191 (2023). State v. Ervin, 169 Wn.2d 
815, 820, 239 P.3d 354 (2010)."""
    
    print("=== Testing with Actual Text ===")
    print(f"Text length: {len(test_text)} characters")
    print()
    
    print("🔍 CURRENT PATTERN RESULTS:")
    current_matches = list(current_compiled.finditer(test_text))
    print(f"  Found {len(current_matches)} matches:")
    for match in current_matches:
        print(f"    '{match.group(0)}' at position {match.start()}-{match.end()}")
    
    print()
    print("🔧 FLEXIBLE PATTERN RESULTS:")
    flexible_matches = list(flexible_compiled.finditer(test_text))
    print(f"  Found {len(flexible_matches)} matches:")
    for match in flexible_matches:
        print(f"    '{match.group(0)}' at position {match.start()}-{match.end()}")
    
    print()
    print("🎯 EXPECTED: Should find both '2 Wn. 3d 329' and '169 Wn.2d 815'")
    print()
    print("💡 THEORY: The issue might be the space between 'Wn.' and '3d'")
    print("   - Current pattern: requires space after Wn.")
    print("   - Flexible pattern: allows optional space after Wn.")

if __name__ == "__main__":
    test_new_pattern()
