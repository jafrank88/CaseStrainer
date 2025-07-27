#!/usr/bin/env python3
"""
Test case for the Lakehaven Water & Sewer Dist. v. City of Fed. Way case.
"""

import re
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from case_name_extraction_core import extract_case_name_precise

def test_lakehaven():
    print("Testing Lakehaven case name extraction...")
    
    test_text = """
    some text before Lakehaven Water & Sewer Dist. v. City of Fed. Way, 195 Wn.2d 742, 773, 466 P.3d 213 (2020)
    some text after
    """
    
    citation = "195 Wn.2d 742"
    
    # Extract the case name
    case_name = extract_case_name_precise(test_text, citation)
    
    print(f"\nInput text: {test_text}")
    print(f"Citation: {citation}")
    print(f"Extracted case name: '{case_name}'")
    print(f"Expected case name: 'Lakehaven Water & Sewer Dist. v. City of Fed. Way'")
    
    # Check if the extraction was successful
    expected = 'Lakehaven Water & Sewer Dist. v. City of Fed. Way'
    if case_name == expected:
        print("\n✅ Test passed!")
        return True
    else:
        print("\n❌ Test failed!")
        return False

if __name__ == "__main__":
    test_lakehaven()
