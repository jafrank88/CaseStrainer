#!/usr/bin/env python3
"""
Test improved case name and date extraction
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from case_name_extraction_core import extract_case_name_and_date

def test_bourguignon_extraction():
    """Test extraction for the Bourguignon case that failed"""
    
    # The actual text from the PDF around the citation
    text = """Matter of Bourguignon v. Coordinated Behavioral Health Servs., Inc., 114 A.D.3d 947 (3d Dep't 2014)"""
    
    citation = "114 A.D.3d 947"
    
    print("=== Testing Improved Extraction ===")
    print(f"Text: {text}")
    print(f"Citation: {citation}")
    print()
    
    result = extract_case_name_and_date(text, citation)
    
    print("Results:")
    print(f"  Case Name: '{result['case_name']}'")
    print(f"  Date: '{result['date']}'")
    print(f"  Year: '{result['year']}'")
    print(f"  Method: '{result['method']}'")
    print(f"  Confidence: {result['confidence']:.2f}")
    print(f"  Debug Info: {result['debug_info']}")
    print()
    
    # Check if extraction was successful
    expected_case_name = "Matter of Bourguignon v. Coordinated Behavioral Health Servs., Inc."
    expected_year = "2014"
    
    case_name_success = result['case_name'] == expected_case_name
    year_success = result['year'] == expected_year
    
    print("Validation:")
    print(f"  Case Name Match: {'✅' if case_name_success else '❌'}")
    print(f"  Year Match: {'✅' if year_success else '❌'}")
    
    if case_name_success and year_success:
        print("🎉 SUCCESS: Both case name and year extracted correctly!")
    elif case_name_success:
        print("⚠️  PARTIAL: Case name extracted, but year failed")
    elif year_success:
        print("⚠️  PARTIAL: Year extracted, but case name failed")
    else:
        print("❌ FAILED: Neither case name nor year extracted correctly")
    
    return case_name_success and year_success

def test_context_window():
    """Test with larger context to simulate real document"""
    
    # Simulate a larger document context
    text = """The district court, however, misinterpreted the law relating to the loss of earnings, ignoring Section 14 of the New York workers' Compensation Law, which permits compensation as a minimum wage worker when an injured worker lacks wage records for the prior year. Matter of Bourguignon v. Coordinated Behavioral Health Servs., Inc., 114 A.D.3d 947 (3d Dep't 2014). Specifically, the District Court overlooked key factors before its dismissal."""
    
    citation = "114 A.D.3d 947"
    
    print("\n=== Testing with Larger Context ===")
    print(f"Citation: {citation}")
    print()
    
    result = extract_case_name_and_date(text, citation)
    
    print("Results:")
    print(f"  Case Name: '{result['case_name']}'")
    print(f"  Year: '{result['year']}'")
    print(f"  Method: '{result['method']}'")
    print(f"  Confidence: {result['confidence']:.2f}")
    
    expected_case_name = "Matter of Bourguignon v. Coordinated Behavioral Health Servs., Inc."
    expected_year = "2014"
    
    success = (result['case_name'] == expected_case_name and result['year'] == expected_year)
    print(f"\n{'🎉 SUCCESS' if success else '❌ FAILED'}")
    
    return success

if __name__ == "__main__":
    print("Testing improved case name and date extraction...")
    print()
    
    test1_success = test_bourguignon_extraction()
    test2_success = test_context_window()
    
    print("\n" + "="*50)
    print("SUMMARY:")
    print(f"  Test 1 (Simple): {'✅ PASSED' if test1_success else '❌ FAILED'}")
    print(f"  Test 2 (Context): {'✅ PASSED' if test2_success else '❌ FAILED'}")
    
    if test1_success and test2_success:
        print("\n🎉 ALL TESTS PASSED! The extraction improvements are working.")
    else:
        print("\n⚠️  Some tests failed. Further improvements may be needed.") 