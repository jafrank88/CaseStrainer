#!/usr/bin/env python3
"""
Test script to demonstrate the case name extraction bug.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.standalone_citation_parser import CitationParser

def test_case_name_bug():
    """Test to demonstrate the case name extraction bug."""
    
    # The original text with multiple citations
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2002)"""
    
    # Test citations - using the exact citations as they appear in the text
    test_citations = [
        "200 Wn.2d 72, 73, 514 P.3d 643 (2022)",
        "171 Wn.2d 486, 493, 256 P.3d 321 (2011)", 
        "146 Wn.2d 1, 9, 43 P.3d 4 (2002)"
    ]
    
    print("=== TESTING CASE NAME EXTRACTION BUG ===")
    print(f"Text: {test_text}")
    print()
    
    parser = CitationParser()
    
    for i, citation in enumerate(test_citations, 1):
        print(f"Test {i}: Citation '{citation}'")
        print("-" * 50)
        
        # Test the extraction
        result = parser.extract_from_text(test_text, citation)
        
        print(f"Extracted case name: '{result.get('case_name', 'N/A')}'")
        print(f"Extracted date: '{result.get('year', 'N/A')}'")
        print(f"Method: '{result.get('extraction_method', 'N/A')}'")
        print(f"Full citation found: {result.get('full_citation_found', False)}")
        print()
    
    print("=== EXPECTED RESULTS ===")
    print("Citation 1 (200 Wn.2d 72): Should be 'Convoyant, LLC v. DeepThink, LLC'")
    print("Citation 2 (171 Wn.2d 486): Should be 'Carlsen v. Glob. Client Sols., LLC'") 
    print("Citation 3 (146 Wn.2d 1): Should be 'Dep't of Ecology v. Campbell & Gwinn, LLC'")
    print()
    print("=== BUG ANALYSIS ===")
    print("If all case names are the same, there's a bug in the extraction logic.")
    print("The issue is likely that the regex patterns are finding the first case name")
    print("in the text and applying it to all citations instead of finding the")
    print("specific case name for each citation.")

if __name__ == "__main__":
    test_case_name_bug() 