#!/usr/bin/env python3
"""
Comprehensive test to verify all citation extraction improvements are working
"""

import sys
import os
sys.path.insert(0, 'src')

def test_bourguignon_extraction():
    """Test the specific Bourguignon case that was failing"""
    
    test_text = """The district court, however, misinterpreted the law relating to the loss of earnings, ignoring Section 14 of the New York workers' Compensation Law, which permits compensation as a minimum wage worker when an injured worker lacks wage records for the prior year. Matter of Bourguignon v. Coordinated Behavioral Health Servs., Inc., 114 A.D.3d 947 (3d Dep't 2014). Specifically, the District Court overlooked key factors before its dismissal."""
    
    print("=== Testing Bourguignon Extraction (Original Problem) ===")
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
        print(f"  Extracted Year: '{result['year']}'")
        print(f"  Expected: '2014'")
        print(f"  Method: '{result['method']}'")
        print(f"  Confidence: {result['confidence']:.2f}")
        print()
        
        # Check if it extracted the correct case name and year
        case_correct = result['case_name'] == "Matter of Bourguignon v. Coordinated Behavioral Health Servs., Inc."
        year_correct = result['year'] == "2014"
        
        print("=== Bourguignon Test Results ===")
        print(f"Case Name: {'✅ CORRECT' if case_correct else '❌ WRONG'}")
        print(f"Year: {'✅ CORRECT' if year_correct else '❌ WRONG'}")
        
        if case_correct and year_correct:
            print("\n🎉 SUCCESS: Bourguignon extraction is now working correctly!")
        else:
            print("\n⚠️  FAILED: Bourguignon extraction still has issues!")
            
        return case_correct and year_correct
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_citations_isolation():
    """Test that multiple citations don't interfere with each other"""
    
    test_text = """The court in Smith v. Jones, 100 A.2d 123 (2020) held that the plaintiff was entitled to damages. However, in Johnson v. Brown, 200 B.3d 456 (2021), the court reached a different conclusion. The matter was finally resolved in Matter of Bourguignon v. Coordinated Behavioral Health Servs., Inc., 114 A.D.3d 947 (3d Dep't 2014)."""
    
    print("\n=== Testing Multiple Citations Isolation ===")
    print(f"Test text: {test_text}")
    print()
    
    try:
        from case_name_extraction_core import extract_case_name_and_date
        
        # Test all three citations
        citations = [
            ("100 A.2d 123", "Smith v. Jones", "2020"),
            ("200 B.3d 456", "Johnson v. Brown", "2021"),
            ("114 A.D.3d 947", "Matter of Bourguignon v. Coordinated Behavioral Health Servs., Inc.", "2014")
        ]
        
        all_correct = True
        
        for citation, expected_case, expected_year in citations:
            result = extract_case_name_and_date(test_text, citation)
            
            print(f"Citation: {citation}")
            print(f"  Extracted Case: '{result['case_name']}'")
            print(f"  Expected Case: '{expected_case}'")
            print(f"  Extracted Year: '{result['year']}'")
            print(f"  Expected Year: '{expected_year}'")
            
            case_correct = result['case_name'] == expected_case
            year_correct = result['year'] == expected_year
            
            print(f"  Case: {'✅' if case_correct else '❌'}, Year: {'✅' if year_correct else '❌'}")
            print()
            
            if not (case_correct and year_correct):
                all_correct = False
        
        print("=== Multiple Citations Test Results ===")
        if all_correct:
            print("🎉 SUCCESS: All citations extracted correctly with proper isolation!")
        else:
            print("⚠️  FAILED: Some citations had cross-contamination issues!")
            
        return all_correct
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_unified_processor_isolation():
    """Test that the unified processor uses isolation logic"""
    
    test_text = """The court in Smith v. Jones, 100 A.2d 123 (2020) held that the plaintiff was entitled to damages. However, in Johnson v. Brown, 200 B.3d 456 (2021), the court reached a different conclusion. The matter was finally resolved in Matter of Bourguignon v. Coordinated Behavioral Health Servs., Inc., 114 A.D.3d 947 (3d Dep't 2014)."""
    
    print("\n=== Testing Unified Processor Isolation ===")
    print(f"Test text: {test_text}")
    print()
    
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        processor = UnifiedCitationProcessorV2()
        
        # Test the isolated context helper
        citation_start = test_text.find("114 A.D.3d 947")
        citation_end = citation_start + len("114 A.D.3d 947")
        
        context_start, context_end = processor._get_isolated_context_for_citation(
            test_text, citation_start, citation_end
        )
        
        if context_start is not None and context_end is not None:
            context = test_text[context_start:context_end]
            print(f"Citation: '114 A.D.3d 947'")
            print(f"Isolated context: '{context}'")
            print()
            
            # Check if context contains the correct case name and year
            case_name_in_context = "Matter of Bourguignon v. Coordinated Behavioral Health Servs., Inc." in context
            year_in_context = "(3d Dep't 2014)" in context
            
            # Check if context avoids other citations
            other_citation_in_context = "100 A.2d 123" in context or "200 B.3d 456" in context
            
            print("=== Unified Processor Isolation Test Results ===")
            print(f"Case name in context: {'✅ YES' if case_name_in_context else '❌ NO'}")
            print(f"Year in context: {'✅ YES' if year_in_context else '❌ NO'}")
            print(f"Other citations in context: {'❌ YES' if other_citation_in_context else '✅ NO'}")
            
            if case_name_in_context and year_in_context and not other_citation_in_context:
                print("\n🎉 SUCCESS: Unified processor isolation is working!")
                return True
            else:
                print("\n⚠️  ISSUE: Unified processor isolation may have problems!")
                return False
        else:
            print("❌ FAILED: Could not get isolated context")
            return False
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_date_extraction_isolation():
    """Test that date extraction uses isolation logic"""
    
    test_text = """The court in Smith v. Jones, 100 A.2d 123 (2020) held that the plaintiff was entitled to damages. However, in Johnson v. Brown, 200 B.3d 456 (2021), the court reached a different conclusion. The matter was finally resolved in Matter of Bourguignon v. Coordinated Behavioral Health Servs., Inc., 114 A.D.3d 947 (3d Dep't 2014)."""
    
    print("\n=== Testing Date Extraction Isolation ===")
    print(f"Test text: {test_text}")
    print()
    
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        processor = UnifiedCitationProcessorV2()
        
        # Test the isolated date extraction
        citation_start = test_text.find("114 A.D.3d 947")
        citation_end = citation_start + len("114 A.D.3d 947")
        
        result = processor.extract_date_from_context_isolated(test_text, citation_start, citation_end)
        
        print(f"Target Citation: '114 A.D.3d 947'")
        print(f"  Extracted Year: '{result}'")
        print(f"  Expected: '2014'")
        print()
        
        # Check if it extracted the correct year
        year_correct = result == "2014"
        
        print("=== Date Extraction Test Results ===")
        print(f"Year: {'✅ CORRECT' if year_correct else '❌ WRONG'}")
        
        if year_correct:
            print("\n🎉 SUCCESS: Date extraction isolation is working!")
        else:
            print("\n⚠️  FAILED: Date extraction isolation may have issues!")
            
        return year_correct
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_context_extraction_improvements():
    """Test that context extraction uses improved logic"""
    
    test_text = """The court in Smith v. Jones, 100 A.2d 123 (2020) held that the plaintiff was entitled to damages. However, in Johnson v. Brown, 200 B.3d 456 (2021), the court reached a different conclusion. The matter was finally resolved in Matter of Bourguignon v. Coordinated Behavioral Health Servs., Inc., 114 A.D.3d 947 (3d Dep't 2014)."""
    
    print("\n=== Testing Context Extraction Improvements ===")
    print(f"Test text: {test_text}")
    print()
    
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        processor = UnifiedCitationProcessorV2()
        
        # Test the improved context extraction
        citation_start = test_text.find("114 A.D.3d 947")
        citation_end = citation_start + len("114 A.D.3d 947")
        
        context = processor._extract_context(test_text, citation_start, citation_end)
        
        print(f"Citation: '114 A.D.3d 947'")
        print(f"Extracted context: '{context}'")
        print()
        
        # Check if context contains the correct case name and year
        case_name_in_context = "Matter of Bourguignon v. Coordinated Behavioral Health Servs., Inc." in context
        year_in_context = "(3d Dep't 2014)" in context
        
        # Check if context avoids other citations
        other_citation_in_context = "100 A.2d 123" in context or "200 B.3d 456" in context
        
        print("=== Context Extraction Test Results ===")
        print(f"Case name in context: {'✅ YES' if case_name_in_context else '❌ NO'}")
        print(f"Year in context: {'✅ YES' if year_in_context else '❌ NO'}")
        print(f"Other citations in context: {'❌ YES' if other_citation_in_context else '✅ NO'}")
        
        if case_name_in_context and year_in_context and not other_citation_in_context:
            print("\n🎉 SUCCESS: Context extraction improvements are working!")
            return True
        else:
            print("\n⚠️  ISSUE: Context extraction improvements may have problems!")
            return False
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing comprehensive citation extraction improvements...")
    print()
    
    test1_success = test_bourguignon_extraction()
    test2_success = test_multiple_citations_isolation()
    test3_success = test_unified_processor_isolation()
    test4_success = test_date_extraction_isolation()
    test5_success = test_context_extraction_improvements()
    
    print("\n" + "="*70)
    print("COMPREHENSIVE TEST SUMMARY:")
    print(f"  Bourguignon Extraction: {'✅ PASSED' if test1_success else '❌ FAILED'}")
    print(f"  Multiple Citations Isolation: {'✅ PASSED' if test2_success else '❌ FAILED'}")
    print(f"  Unified Processor Isolation: {'✅ PASSED' if test3_success else '❌ FAILED'}")
    print(f"  Date Extraction Isolation: {'✅ PASSED' if test4_success else '❌ FAILED'}")
    print(f"  Context Extraction Improvements: {'✅ PASSED' if test5_success else '❌ FAILED'}")
    
    all_passed = test1_success and test2_success and test3_success and test4_success and test5_success
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! All improvements are working correctly!")
        print("   The citation extraction system now has comprehensive isolation logic.")
        print("   Ready to proceed with deprecation of inferior functions.")
    else:
        print("\n⚠️  Some tests failed. Further improvements may be needed.")
        print("   Review failed tests before proceeding with deprecation.") 