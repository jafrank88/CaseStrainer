#!/usr/bin/env python3
"""
Test US citation regex pattern.
"""

import re

def test_us_pattern():
    """Test the US citation regex pattern."""
    print("Testing US citation regex pattern...")
    
    # The pattern from the code
    pattern = re.compile(r"\b\d+\s+U\.?\s*S\.?\s+\d+\b")
    
    # Test cases
    test_cases = [
        "347 U.S. 483",
        "410 U.S. 113",
        "123 US 456",
        "456 U.S. 789",
        "347 U.S. 483 (1954)",
        "The court in Brown v. Board of Education, 347 U.S. 483 (1954) held that segregation was unconstitutional."
    ]
    
    for test_case in test_cases:
        matches = pattern.findall(test_case)
        print(f"Text: '{test_case}'")
        print(f"  Matches: {matches}")
        print(f"  Match count: {len(matches)}")
        print()
    
    # Test with the exact pattern from the unified processor
    unified_pattern = re.compile(r'\b(\d+)\s+U\.\s*S\.\s+(\d+)\b')
    
    print("Testing unified processor pattern...")
    for test_case in test_cases:
        matches = unified_pattern.findall(test_case)
        print(f"Text: '{test_case}'")
        print(f"  Matches: {matches}")
        print(f"  Match count: {len(matches)}")
        print()

if __name__ == "__main__":
    test_us_pattern() 