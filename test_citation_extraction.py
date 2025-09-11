#!/usr/bin/env python3
"""
Test script to check case name and year extraction functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from case_name_extraction_core import extract_case_name_triple_comprehensive
from standalone_citation_parser import CitationParser

def test_standard_paragraph():
    """Test the standard test paragraph for citation extraction"""
    
    # Standard test paragraph from the project
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    # Expected citations and their case names/years
    expected_results = [
        {
            'citation': '200 Wn.2d 72',
            'expected_case_name': 'Convoyant, LLC v. DeepThink, LLC',
            'expected_year': '2022'
        },
        {
            'citation': '171 Wn.2d 486',
            'expected_case_name': 'Carlson v. Glob. Client Sols., LLC',
            'expected_year': '2011'
        },
        {
            'citation': '146 Wn.2d 1',
            'expected_case_name': "Dep't of Ecology v. Campbell & Gwinn, LLC",
            'expected_year': '2003'
        }
    ]
    
    print("=== Testing Case Name and Year Extraction ===\n")
    print(f"Test text: {test_text}\n")
    
    # Test 1: Using the core extraction function
    print("--- Test 1: Core Extraction Function ---")
    for expected in expected_results:
        citation = expected['citation']
        case_name, year, confidence = extract_case_name_triple_comprehensive(test_text, citation)
        
        print(f"\nCitation: {citation}")
        print(f"  Expected case name: {expected['expected_case_name']}")
        print(f"  Extracted case name: {case_name}")
        print(f"  Expected year: {expected['expected_year']}")
        print(f"  Extracted year: {year}")
        print(f"  Confidence: {confidence}")
        
        # Check if extraction was successful
        case_name_match = case_name == expected['expected_case_name']
        year_match = year == expected['expected_year']
        
        if case_name_match and year_match:
            print("  SUCCESS: Both case name and year extracted correctly")
        elif case_name_match:
            print("  PARTIAL: Case name correct, year incorrect")
        elif year_match:
            print("  PARTIAL: Year correct, case name incorrect")
        else:
            print("  FAILED: Neither case name nor year extracted correctly")
    
    # Test 2: Using the standalone parser
    print("\n\n--- Test 2: Standalone Parser ---")
    parser = CitationParser()
    
    for expected in expected_results:
        citation = expected['citation']
        result = parser.extract_from_text(test_text, citation)
        
        print(f"\nCitation: {citation}")
        print(f"  Expected case name: {expected['expected_case_name']}")
        print(f"  Extracted case name: {result.get('case_name', 'N/A')}")
        print(f"  Expected year: {expected['expected_year']}")
        print(f"  Extracted year: {result.get('year', 'N/A')}")
        print(f"  Method: {result.get('extraction_method', 'N/A')}")
        
        # Check if extraction was successful
        case_name_match = result.get('case_name') == expected['expected_case_name']
        year_match = result.get('year') == expected['expected_year']
        
        if case_name_match and year_match:
            print("  SUCCESS: Both case name and year extracted correctly")
        elif case_name_match:
            print("  PARTIAL: Case name correct, year incorrect")
        elif year_match:
            print("  PARTIAL: Year correct, case name incorrect")
        else:
            print("  FAILED: Neither case name nor year extracted correctly")
    
    # Test 3: Test paragraph 2 from memories
    print("\n\n--- Test 3: Test Paragraph 2 ---")
    test_text_2 = """We have long held that pro se litigants are bound by the same rules of procedure and substantive law as licensed attorneys. Holder v. City of Vancouver, 136 Wn. App. 104, 106, 147 P.3d 641 (2006); In re Marriage of Olson, 69 Wn. App. 621, 626, 850 P.2d 527 (1993) (noting courts are "under no obligation to grant special favors to . . . a pro se litigant."). Thus, a pro se appellant's failure to "identify any specific legal issues . . . cite any authority" or comply with procedural rules may still preclude appellate review. State v. Marintorres, 93 Wn. App. 442, 452, 969 P.2d 501 (1999)"""
    
    expected_results_2 = [
        {
            'citation': '136 Wn. App. 104',
            'expected_case_name': 'Holder v. City of Vancouver',
            'expected_year': '2006'
        },
        {
            'citation': '69 Wn. App. 621',
            'expected_case_name': 'In re Marriage of Olson',
            'expected_year': '1993'
        },
        {
            'citation': '93 Wn. App. 442',
            'expected_case_name': 'State v. Marintorres',
            'expected_year': '1999'
        }
    ]
    
    print(f"Test text 2: {test_text_2}\n")
    
    for expected in expected_results_2:
        citation = expected['citation']
        case_name, year, confidence = extract_case_name_triple_comprehensive(test_text_2, citation)
        
        print(f"\nCitation: {citation}")
        print(f"  Expected case name: {expected['expected_case_name']}")
        print(f"  Extracted case name: {case_name}")
        print(f"  Expected year: {year}")
        print(f"  Extracted year: {year}")
        print(f"  Confidence: {confidence}")
        
        # Check if extraction was successful
        case_name_match = case_name == expected['expected_case_name']
        year_match = year == expected['expected_year']
        
        if case_name_match and year_match:
            print("  SUCCESS: Both case name and year extracted correctly")
        elif case_name_match:
            print("  PARTIAL: Case name correct, year incorrect")
        elif year_match:
            print("  PARTIAL: Year correct, case name incorrect")
        else:
            print("  FAILED: Neither case name nor year extracted correctly")

if __name__ == "__main__":
    test_standard_paragraph()
