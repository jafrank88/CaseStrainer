#!/usr/bin/env python3
"""
Debug script for case name extraction.
"""

import re
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from case_name_extraction_core import extract_case_name_precise, find_case_name_start, is_stopword

def debug_extraction(text, citation):
    print("=" * 80)
    print(f"Testing extraction with citation: {citation}")
    print("-" * 40)
    
    # Find the citation position
    cite_pos = text.find(citation)
    if cite_pos == -1:
        print("Citation not found in text!")
        return None
    
    # Show the full text with position markers
    print("Full text with position markers:")
    for i in range(0, len(text), 20):
        chunk = text[i:i+20]
        pos_marker = f"{i:>4}"
        print(f"{pos_marker}: {chunk}")
    
    print(f"\nCitation found at position: {cite_pos}")
    
    # Try to find the case name start
    print("\nSearching for case name start...")
    case_start = find_case_name_start(text, cite_pos, citation)
    print(f"Case name starts at position: {case_start}")
    
    # Show the extracted case name
    if case_start < cite_pos:
        case_name = text[case_start:cite_pos].strip()
        # Clean up any trailing punctuation
        case_name = re.sub(r'[\s,;.]+$', '', case_name)
        print(f"\nExtracted case name: '{case_name}'")
        return case_name
    else:
        print("\nCould not determine case name start position")
        return None

def test_lakehaven():
    print("\n" + "="*40)
    print("TESTING LAKEHAVEN CASE")
    print("="*40)
    
    test_text = """
    some text before Lakehaven Water & Sewer Dist. v. City of Fed. Way, 195 Wn.2d 742, 773, 466 P.3d 213 (2020)
    some text after
    """
    
    citation = "195 Wn.2d 742"
    return debug_extraction(test_text, citation)

def test_simple():
    print("\n" + "="*40)
    print("TESTING SIMPLE CASE")
    print("="*40)
    
    test_text = """
    Some other text State v. Smith, 123 Wn.2d 456 (2020) and more text
    """
    
    citation = "123 Wn.2d 456"
    return debug_extraction(test_text, citation)

def test_context():
    print("\n" + "="*40)
    print("TESTING CASE WITH LEADING CONTEXT")
    print("="*40)
    
    test_text = """
    The court in the case of People v. Johnson, 987 Cal. 4th 123 (2023) ruled that...
    """
    
    citation = "987 Cal. 4th 123"
    return debug_extraction(test_text, citation)

if __name__ == "__main__":
    test_lakehaven()
    test_simple()
    test_context()
