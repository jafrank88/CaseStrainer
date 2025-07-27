#!/usr/bin/env python3
"""
Test the improved case name extraction logic.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from case_name_extraction_core import extract_case_name_precise, find_case_name_start

def test_case_extraction():
    # Test with the Lakehaven case
    test_text = """
    some text before Lakehaven Water & Sewer Dist. v. City of Fed. Way, 195 Wn.2d 742, 773, 466 P.3d 213 (2020)
    some text after
    """
    
    # The citation we're looking for
    citation = "195 Wn.2d 742"
    
    # Test the find_case_name_start function
    cite_pos = test_text.find(citation)
    case_start = find_case_name_start(test_text, cite_pos)
    print(f"Case name starts at position: {case_start}")
    print(f"Context: '{test_text[case_start-10:cite_pos+10]}...'")
    
    # Test the full extraction
    case_name = extract_case_name_precise(test_text, citation)
    
    print(f"\nExtracted case name: '{case_name}'")
    print(f"Expected case name: 'Lakehaven Water & Sewer Dist. v. City of Fed. Way'")
    
    # Test with a simpler case
    test_text2 = """
    Some other text State v. Smith, 123 Wn.2d 456 (2020) and more text
    """
    
    case_name2 = extract_case_name_precise(test_text2, "123 Wn.2d 456")
    print(f"\nExtracted case name 2: '{case_name2}'")
    print(f"Expected case name 2: 'State v. Smith'")
    
    # Test with a case that has text before the case name
    test_text3 = """
    The court in the case of People v. Johnson, 987 Cal. 4th 123 (2023) ruled that...
    """
    
    case_name3 = extract_case_name_precise(test_text3, "987 Cal. 4th 123")
    print(f"\nExtracted case name 3: '{case_name3}'")
    print(f"Expected case name 3: 'People v. Johnson'")

if __name__ == "__main__":
    test_case_extraction()
