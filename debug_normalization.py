#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_normalization():
    """Test the normalization function to see what's happening to case names."""
    
    def normalize_case_name(name):
        if not name:
            return None
        import re
        # Remove everything after the first comma followed by a number (e.g., ', 200 Wn.2d 72')
        name = re.split(r',\s*\d', name)[0]
        # Remove everything after the first parenthesis
        name = re.split(r'\(', name)[0]
        return name.strip()
    
    # Test cases
    test_cases = [
        "Lakehaven Water & Sewer Dist. v. City of Fed. Way",
        "Davison v. State, 196 Wn.2d 285, 293",
        "Davison v. State",
        "Lakehaven Water & Sewer Dist. v. City of Fed. Way, 195 Wn.2d 742, 773"
    ]
    
    print("=== NORMALIZATION TEST ===")
    for case_name in test_cases:
        normalized = normalize_case_name(case_name)
        print(f"Original: '{case_name}'")
        print(f"Normalized: '{normalized}'")
        print()

if __name__ == "__main__":
    test_normalization() 