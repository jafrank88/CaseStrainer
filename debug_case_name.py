#!/usr/bin/env python3
"""
Debug script to test case name extraction patterns.
"""

import re

def test_patterns():
    """Test the case name extraction patterns."""
    
    # Test text with the three case names
    test_text = "Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"
    
    print("=== TESTING CASE NAME PATTERNS ===")
    print(f"Test text: {test_text}")
    print()
    
    # Enhanced patterns from the function
    patterns = [
        # Pattern 1: v. pattern (most common)
        r'\b([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\b',
        
        # Pattern 2: vs. pattern
        r'\b([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\s+vs\.\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\b',
        
        # Pattern 3: versus pattern
        r'\b([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\s+versus\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\b',
        
        # Pattern 12: Enhanced business entity pattern
        r'\b([A-Z][A-Za-z0-9&.,\'\-]+(?:\s*,\s*[A-Za-z0-9&.,\'\-]+)*)\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s*,\s*[A-Za-z0-9&.,\'\-]+)*)\b',
        
        # Pattern 13: Department cases
        r'\b(Dep\'t\s+of\s+[A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\b',
        
        # Pattern 14: Simple v. pattern
        r'\b([A-Z][a-z]+(?:\s+[A-Za-z]+)*)\s+v\.\s+([A-Z][a-z]+(?:\s+[A-Za-z]+)*)\b',
    ]
    
    for i, pattern in enumerate(patterns):
        print(f"Pattern {i+1}: {pattern}")
        matches = list(re.finditer(pattern, test_text, re.IGNORECASE))
        print(f"  Found {len(matches)} matches:")
        for j, match in enumerate(matches):
            if len(match.groups()) == 2:
                case_name = f"{match.group(1)} v. {match.group(2)}"
            else:
                case_name = match.group(0)
            print(f"    {j+1}. '{case_name}'")
        print()

if __name__ == "__main__":
    test_patterns() 