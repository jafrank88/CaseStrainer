#!/usr/bin/env python3
"""
Test citation isolation to ensure no cross-contamination between citations
"""

import sys
import os
sys.path.insert(0, 'src')

def test_citation_isolation():
    """Test that citations are properly isolated to prevent cross-contamination"""
    
    # Test text with multiple citations close together
    test_text = """The district court, however, misinterpreted the law relating to the loss of earnings, ignoring Section 14 of the New York workers' Compensation Law, which permits compensation as a minimum wage worker when an injured worker lacks wage records for the prior year. Matter of Bourguignon v. Coordinated Behavioral Health Servs., Inc., 114 A.D.3d 947 (3d Dep't 2014). Specifically, the District Court overlooked key factors before its dismissal. Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo."""
    
    print("=== Testing Citation Isolation ===")
    print(f"Test text: {test_text}")
    print()
    
    try:
        from case_name_extraction_core import extract_case_name_and_date
        
        # Test extraction for the first citation
        citation1 = "114 A.D.3d 947"
        result1 = extract_case_name_and_date(test_text, citation1)
        
        print(f"Citation 1: {citation1}")
        print(f"  Extracted Case Name: '{result1['case_name']}'")
        print(f"  Expected: 'Matter of Bourguignon v. Coordinated Behavioral Health Servs., Inc.'")
        print(f"  Year: '{result1['year']}'")
        print(f"  Method: '{result1['method']}'")
        print()
        
        # Test extraction for the second citation
        citation2 = "200 Wn.2d 72"
        result2 = extract_case_name_and_date(test_text, citation2)
        
        print(f"Citation 2: {citation2}")
        print(f"  Extracted Case Name: '{result2['case_name']}'")
        print(f"  Expected: 'Convoyant, LLC v. DeepThink, LLC'")
        print(f"  Year: '{result2['year']}'")
        print(f"  Method: '{result2['method']}'")
        print()
        
        # Check for cross-contamination
        case1_correct = result1['case_name'] == "Matter of Bourguignon v. Coordinated Behavioral Health Servs., Inc."
        case2_correct = result2['case_name'] == "Convoyant, LLC v. DeepThink, LLC"
        year1_correct = result1['year'] == "2014"
        year2_correct = result2['year'] == "2022"
        
        print("=== Isolation Test Results ===")
        print(f"Citation 1 Case Name: {'✅ CORRECT' if case1_correct else '❌ WRONG'}")
        print(f"Citation 2 Case Name: {'✅ CORRECT' if case2_correct else '❌ WRONG'}")
        print(f"Citation 1 Year: {'✅ CORRECT' if year1_correct else '❌ WRONG'}")
        print(f"Citation 2 Year: {'✅ CORRECT' if year2_correct else '❌ WRONG'}")
        
        # Check for cross-contamination specifically
        if case1_correct and case2_correct and year1_correct and year2_correct:
            print("\n🎉 SUCCESS: No cross-contamination detected!")
            print("   Each citation correctly extracted its own case name and year.")
        else:
            print("\n⚠️  CROSS-CONTAMINATION DETECTED!")
            print("   One or more citations extracted the wrong case name or year.")
            
        return case1_correct and case2_correct and year1_correct and year2_correct
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_single_citation_isolation():
    """Test isolation for a single citation to ensure it doesn't pick up wrong context"""
    
    # Test with text that has similar case names but different citations
    test_text = """The court in Smith v. Jones, 100 A.2d 123 (2020) held that the plaintiff was entitled to damages. However, in Johnson v. Brown, 200 B.3d 456 (2021), the court reached a different conclusion. The matter was finally resolved in Matter of Bourguignon v. Coordinated Behavioral Health Servs., Inc., 114 A.D.3d 947 (3d Dep't 2014)."""
    
    print("\n=== Testing Single Citation Isolation ===")
    print(f"Test text: {test_text}")
    print()
    
    try:
        from case_name_extraction_core import extract_case_name_and_date
        
        # Test extraction for the target citation
        target_citation = "114 A.D.3d 947"
        result = extract_case_name_and_date(test_text, target_citation)
        
        print(f"Target Citation: {target_citation}")
        print(f"  Extracted Case Name: '{result['case_name']}'")
        print(f"  Expected: 'Matter of Bourguignon v. Coordinated Behavioral Health Servs., Inc.'")
        print(f"  Year: '{result['year']}'")
        print(f"  Method: '{result['method']}'")
        print()
        
        # Check if it extracted the correct case name
        case_correct = result['case_name'] == "Matter of Bourguignon v. Coordinated Behavioral Health Servs., Inc."
        year_correct = result['year'] == "2014"
        
        print("=== Single Citation Test Results ===")
        print(f"Case Name: {'✅ CORRECT' if case_correct else '❌ WRONG'}")
        print(f"Year: {'✅ CORRECT' if year_correct else '❌ WRONG'}")
        
        if case_correct and year_correct:
            print("\n🎉 SUCCESS: Correct case name and year extracted!")
        else:
            print("\n⚠️  FAILED: Wrong case name or year extracted!")
            
        return case_correct and year_correct
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing citation isolation to prevent cross-contamination...")
    print()
    
    test1_success = test_citation_isolation()
    test2_success = test_single_citation_isolation()
    
    print("\n" + "="*50)
    print("SUMMARY:")
    print(f"  Multi-Citation Test: {'✅ PASSED' if test1_success else '❌ FAILED'}")
    print(f"  Single Citation Test: {'✅ PASSED' if test2_success else '❌ FAILED'}")
    
    if test1_success and test2_success:
        print("\n🎉 ALL TESTS PASSED! Citation isolation is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Cross-contamination may still be occurring.") 