#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_normalization_clustering():
    """Test the normalization function used in clustering logic."""
    
    def normalize_case_name(name):
        if not name:
            return None
        import re
        # Remove everything after the first comma followed by a number (e.g., ', 200 Wn.2d 72')
        name = re.split(r',\s*\d', name)[0]
        # Remove everything after the first parenthesis
        name = re.split(r'\(', name)[0]
        return name.strip()
    
    # Test the actual case names from the pipeline
    test_cases = [
        "Lakehaven Water & Sewer Dist. v. City of Fed. Way",
        "Davison v. State, 196 Wn.2d 285, 293",
        "Davison v. State"
    ]
    
    print("=== NORMALIZATION CLUSTERING TEST ===")
    for case_name in test_cases:
        normalized = normalize_case_name(case_name)
        print(f"Original: '{case_name}'")
        print(f"Normalized: '{normalized}'")
        print()
    
    # Test what happens when we normalize both case names
    lakehaven = "Lakehaven Water & Sewer Dist. v. City of Fed. Way"
    davison = "Davison v. State, 196 Wn.2d 285, 293"
    
    norm_lakehaven = normalize_case_name(lakehaven)
    norm_davison = normalize_case_name(davison)
    
    print("=== COMPARISON ===")
    print(f"Lakehaven: '{lakehaven}' -> '{norm_lakehaven}'")
    print(f"Davison: '{davison}' -> '{norm_davison}'")
    print(f"Same after normalization: {norm_lakehaven == norm_davison}")
    
    # Check if they're the same when converted to lowercase
    print(f"Same after lowercase: {norm_lakehaven.lower() == norm_davison.lower()}")

if __name__ == "__main__":
    test_normalization_clustering() 