#!/usr/bin/env python3
"""
Test the normalization pattern directly
"""

import re

def test_normalization():
    """Test the normalization pattern"""
    
    cite = "24 Wn. App. 2d 377"
    print(f"Original: '{cite}'")
    
    # Remove any non-alphanumeric characters except spaces, dots, and numbers
    normalized = re.sub(r"[^a-z0-9\s.]", " ", cite.lower())
    print(f"After cleanup: '{normalized}'")
    
    # Collapse multiple spaces and standardize variations
    normalized = re.sub(r"\s+", " ", normalized).strip()
    print(f"After space collapse: '{normalized}'")
    
    # Standardize variations
    normalized = normalized.replace("washington", "wash").replace("wn ", "wash ").replace("wn. ", "wash. ")
    print(f"After wn replacement: '{normalized}'")
    
    # Handle cases like 'Wn. App. 2d' -> 'wash app 2d' (must be before general app pattern)
    pattern = r"wn\.?\s+app\.?\s*(\d*)d"
    match = re.search(pattern, normalized)
    print(f"Pattern '{pattern}' matches: {match}")
    if match:
        print(f"Match groups: {match.groups()}")
        replacement = r"wash app \1d"
        result = re.sub(pattern, replacement, normalized)
        print(f"After replacement: '{result}'")
    
    # Test with actual pattern
    normalized = re.sub(r"wn\.?\s+app\.?\s*(\d*)d", r"wash app \1d", normalized)
    print(f"After wn app 2d pattern: '{normalized}'")
    
    # Handle cases like 'Wn. App.' -> 'wash app'
    normalized = re.sub(r"wash(?:ington)?\s+app(?:\.?\s*\w*)?", "wash app", normalized)
    print(f"After general app pattern: '{normalized}'")

if __name__ == "__main__":
    test_normalization()
