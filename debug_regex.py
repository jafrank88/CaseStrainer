#!/usr/bin/env python3
"""
Debug script to test regex patterns for case name extraction.
"""

import re

def test_regex_patterns():
    citation = "200 Wn.2d 72"
    
    # Test the exact pattern from the improved function
    pattern1 = r'([^,]+?)\s+v\.\s+([^,]+?)(?=,\s*\d+\s+[A-Za-z.]+).*' + re.escape(citation)
    
    test_cases = [
        "Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022)",
        "Department of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)",
        "Carlson v. Global Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011)"
    ]
    
    print("Testing Pattern 1:")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest {i+1}: '{test_case}'")
        matches = list(re.finditer(pattern1, test_case, re.IGNORECASE))
        
        if matches:
            match = matches[0]
            print(f"  Group 1: '{match.group(1)}'")
            print(f"  Group 2: '{match.group(2)}'")
            print(f"  Combined: '{match.group(1)} v. {match.group(2)}'")
        else:
            print("  No match found")
    
    # Test a different approach - look for the citation and work backwards
    print("\n\nTesting Citation-Based Approach:")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest {i+1}: '{test_case}'")
        
        # Find the citation
        citation_pos = test_case.find(citation)
        if citation_pos != -1:
            # Look backwards from the citation to find the case name
            before_citation = test_case[:citation_pos]
            
            # Find the last "v." before the citation
            v_pos = before_citation.rfind(" v. ")
            if v_pos != -1:
                # Find the start of the case name (look for common prefixes)
                case_start = v_pos
                for prefix in ["Department of Ecology ", "State ", "United States ", "In re ", "Estate of "]:
                    prefix_pos = before_citation.find(prefix)
                    if prefix_pos != -1 and prefix_pos < v_pos:
                        case_start = prefix_pos
                        break
                
                case_name = before_citation[case_start:].strip()
                print(f"  Found case name: '{case_name}'")
            else:
                print("  No 'v.' found")
        else:
            print("  Citation not found")

if __name__ == "__main__":
    test_regex_patterns() 