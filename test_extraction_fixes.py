#!/usr/bin/env python3
"""
Test script to verify that the extraction fixes work correctly.
Tests case name extraction, parallel citation detection, and date extraction.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.case_name_extraction_core import extract_case_name_triple_comprehensive
from src.standalone_citation_parser import CitationParser

def test_extraction_fixes():
    """Test the extraction fixes with the problematic text."""
    
    # The problematic text from the user's example
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2002)"""
    
    # Test citations that should be parallel
    test_citations = [
        "200 Wn.2d 72",
        "514 P.3d 643", 
        "171 Wn.2d 486",
        "256 P.3d 321",
        "146 Wn.2d 1",
        "43 P.3d 4"
    ]
    
    print("=== TESTING EXTRACTION FIXES ===")
    print(f"Text: {test_text}")
    print()
    
    # Test each citation
    for i, citation in enumerate(test_citations, 1):
        print(f"Test {i}: Citation '{citation}'")
        print("-" * 50)
        
        # Test the comprehensive extraction
        result = extract_case_name_triple_comprehensive(test_text, citation)
        
        print(f"Extracted case name: '{result.get('extracted_name', 'N/A')}'")
        print(f"Extracted date: '{result.get('extracted_date', 'N/A')}'")
        print(f"Method: '{result.get('case_name_method', 'N/A')}'")
        
        # Check if extraction worked
        case_name_ok = result.get('extracted_name') != 'N/A'
        date_ok = result.get('extracted_date') != 'N/A'
        
        if case_name_ok and date_ok:
            print("✅ SUCCESS: Both case name and date extracted")
        elif case_name_ok:
            print("⚠️  PARTIAL: Case name extracted, no date")
        elif date_ok:
            print("⚠️  PARTIAL: Date extracted, no case name")
        else:
            print("❌ FAILED: No extraction")
        
        print()
    
    # Test parallel citation detection
    print("=== TESTING PARALLEL CITATION DETECTION ===")
    
    # Test the CitationParser directly
    parser = CitationParser()
    
    # Test the first parallel pair
    print("Testing parallel pair: 200 Wn.2d 72 and 514 P.3d 643")
    result1 = parser.extract_from_text(test_text, "200 Wn.2d 72")
    result2 = parser.extract_from_text(test_text, "514 P.3d 643")
    
    print(f"Citation 1 (200 Wn.2d 72):")
    print(f"  Case name: '{result1.get('case_name', 'N/A')}'")
    print(f"  Date: '{result1.get('year', 'N/A')}'")
    
    print(f"Citation 2 (514 P.3d 643):")
    print(f"  Case name: '{result2.get('case_name', 'N/A')}'")
    print(f"  Date: '{result2.get('year', 'N/A')}'")
    
    # Check if they have the same case name (should be parallel)
    if (result1.get('case_name') and result2.get('case_name') and 
        result1.get('case_name') == result2.get('case_name')):
        print("✅ SUCCESS: Parallel citations detected - same case name")
    else:
        print("❌ FAILED: Parallel citations not detected")
    
    print()
    
    # Test the second parallel pair
    print("Testing parallel pair: 171 Wn.2d 486 and 256 P.3d 321")
    result3 = parser.extract_from_text(test_text, "171 Wn.2d 486")
    result4 = parser.extract_from_text(test_text, "256 P.3d 321")
    
    print(f"Citation 3 (171 Wn.2d 486):")
    print(f"  Case name: '{result3.get('case_name', 'N/A')}'")
    print(f"  Date: '{result3.get('year', 'N/A')}'")
    
    print(f"Citation 4 (256 P.3d 321):")
    print(f"  Case name: '{result4.get('case_name', 'N/A')}'")
    print(f"  Date: '{result4.get('year', 'N/A')}'")
    
    if (result3.get('case_name') and result4.get('case_name') and 
        result3.get('case_name') == result4.get('case_name')):
        print("✅ SUCCESS: Parallel citations detected - same case name")
    else:
        print("❌ FAILED: Parallel citations not detected")
    
    print()
    
    # Test the third parallel pair
    print("Testing parallel pair: 146 Wn.2d 1 and 43 P.3d 4")
    result5 = parser.extract_from_text(test_text, "146 Wn.2d 1")
    result6 = parser.extract_from_text(test_text, "43 P.3d 4")
    
    print(f"Citation 5 (146 Wn.2d 1):")
    print(f"  Case name: '{result5.get('case_name', 'N/A')}'")
    print(f"  Date: '{result5.get('year', 'N/A')}'")
    
    print(f"Citation 6 (43 P.3d 4):")
    print(f"  Case name: '{result6.get('case_name', 'N/A')}'")
    print(f"  Date: '{result6.get('year', 'N/A')}'")
    
    if (result5.get('case_name') and result6.get('case_name') and 
        result5.get('case_name') == result6.get('case_name')):
        print("✅ SUCCESS: Parallel citations detected - same case name")
    else:
        print("❌ FAILED: Parallel citations not detected")

if __name__ == "__main__":
    test_extraction_fixes() 