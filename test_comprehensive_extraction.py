#!/usr/bin/env python3
"""
Comprehensive test script to verify that all extraction fixes work correctly.
Tests case name extraction, parallel citation detection, and date extraction.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.case_name_extraction_core import extract_case_name_triple_comprehensive
from src.standalone_citation_parser import CitationParser

def test_comprehensive_extraction():
    """Test the comprehensive extraction fixes with various scenarios."""
    
    # Test cases with different scenarios
    test_cases = [
        {
            "name": "Parallel Citations with Full Case Names",
            "text": """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2002)""",
            "citations": [
                {"citation": "200 Wn.2d 72", "expected_case": "Convoyant, LLC v. DeepThink, LLC", "expected_date": "2022"},
                {"citation": "514 P.3d 643", "expected_case": "Convoyant, LLC v. DeepThink, LLC", "expected_date": "2022"},
                {"citation": "171 Wn.2d 486", "expected_case": "Carlsen v. Glob. Client Sols., LLC", "expected_date": "2011"},
                {"citation": "256 P.3d 321", "expected_case": "Carlsen v. Glob. Client Sols., LLC", "expected_date": "2011"},
                {"citation": "146 Wn.2d 1", "expected_case": "Dep't of Ecology v. Campbell & Gwinn, LLC", "expected_date": "2002"},
                {"citation": "43 P.3d 4", "expected_case": "Dep't of Ecology v. Campbell & Gwinn, LLC", "expected_date": "2002"}
            ]
        },
        {
            "name": "Simple Citation",
            "text": "The court held in Smith v. Jones, 123 U.S. 456 (2020), that the principle applies.",
            "citations": [
                {"citation": "123 U.S. 456", "expected_case": "Smith v. Jones", "expected_date": "2020"}
            ]
        },
        {
            "name": "In re Case",
            "text": "In re Estate of Johnson, 456 Wash. 789 (2019), the court found...",
            "citations": [
                {"citation": "456 Wash. 789", "expected_case": "In re Estate of Johnson", "expected_date": "2019"}
            ]
        },
        {
            "name": "State v. Case",
            "text": "State v. Smith, 789 P.2d 123 (1990), established the rule.",
            "citations": [
                {"citation": "789 P.2d 123", "expected_case": "State v. Smith", "expected_date": "1990"}
            ]
        }
    ]
    
    print("=== COMPREHENSIVE EXTRACTION TEST ===")
    print()
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"Test Case: {test_case['name']}")
        print("=" * 60)
        print(f"Text: {test_case['text'][:100]}...")
        print()
        
        case_passed = True
        
        for i, citation_test in enumerate(test_case['citations'], 1):
            citation = citation_test['citation']
            expected_case = citation_test['expected_case']
            expected_date = citation_test['expected_date']
            
            print(f"  Citation {i}: '{citation}'")
            print(f"  Expected: '{expected_case}' ({expected_date})")
            
            # Test the comprehensive extraction
            result = extract_case_name_triple_comprehensive(test_case['text'], citation)
            
            extracted_case = result.get('extracted_name', 'N/A')
            extracted_date = result.get('extracted_date', 'N/A')
            
            print(f"  Extracted: '{extracted_case}' ({extracted_date})")
            
            # Check results
            case_ok = extracted_case == expected_case
            date_ok = extracted_date == expected_date
            
            if case_ok and date_ok:
                print("  ✅ SUCCESS: Both case name and date match")
            elif case_ok:
                print(f"  ⚠️  PARTIAL: Case name matches, date mismatch (got '{extracted_date}', expected '{expected_date}')")
                case_passed = False
            elif date_ok:
                print(f"  ⚠️  PARTIAL: Date matches, case name mismatch (got '{extracted_case}', expected '{expected_case}')")
                case_passed = False
            else:
                print(f"  ❌ FAILED: Both case name and date mismatch")
                case_passed = False
            
            print()
        
        if case_passed:
            print("✅ Test case PASSED")
        else:
            print("❌ Test case FAILED")
            all_passed = False
        
        print("-" * 60)
        print()
    
    # Test parallel citation detection
    print("=== PARALLEL CITATION DETECTION TEST ===")
    print()
    
    # Test the problematic text
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2002)"""
    
    parser = CitationParser()
    
    # Test parallel pairs
    parallel_pairs = [
        ("200 Wn.2d 72", "514 P.3d 643", "Convoyant, LLC v. DeepThink, LLC"),
        ("171 Wn.2d 486", "256 P.3d 321", "Carlsen v. Glob. Client Sols., LLC"),
        ("146 Wn.2d 1", "43 P.3d 4", "Dep't of Ecology v. Campbell & Gwinn, LLC")
    ]
    
    for i, (citation1, citation2, expected_case) in enumerate(parallel_pairs, 1):
        print(f"Parallel Pair {i}: {citation1} and {citation2}")
        print(f"Expected case: {expected_case}")
        
        result1 = parser.extract_from_text(test_text, citation1)
        result2 = parser.extract_from_text(test_text, citation2)
        
        case1 = result1.get('case_name', 'N/A')
        case2 = result2.get('case_name', 'N/A')
        date1 = result1.get('year', 'N/A')
        date2 = result2.get('year', 'N/A')
        
        print(f"  Citation 1: case='{case1}', date='{date1}'")
        print(f"  Citation 2: case='{case2}', date='{date2}'")
        
        # Check if they have the same case name (should be parallel)
        if case1 == case2 and case1 != 'N/A' and case1 != 'None':
            print("  ✅ SUCCESS: Parallel citations detected - same case name")
        else:
            print("  ❌ FAILED: Parallel citations not detected")
            all_passed = False
        
        print()
    
    print("=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    
    return all_passed

if __name__ == "__main__":
    test_comprehensive_extraction() 