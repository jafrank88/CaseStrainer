#!/usr/bin/env python3
"""
Test that all inferior fallback methods have been improved with isolation logic
"""

import sys
import os
sys.path.insert(0, 'src')

def test_date_extraction_isolation():
    """Test that date extraction uses isolation logic instead of inferior fallbacks"""
    
    # Test text with multiple citations close together
    test_text = """The court in Smith v. Jones, 100 A.2d 123 (2020) held that the plaintiff was entitled to damages. However, in Johnson v. Brown, 200 B.3d 456 (2021), the court reached a different conclusion. The matter was finally resolved in Matter of Bourguignon v. Coordinated Behavioral Health Servs., Inc., 114 A.D.3d 947 (3d Dep't 2014)."""
    
    print("=== Testing Date Extraction Isolation ===")
    print(f"Test text: {test_text}")
    print()
    
    try:
        from case_name_extraction_core import DateExtractor
        
        # Test extraction for the target citation
        target_citation = "114 A.D.3d 947"
        date_extractor = DateExtractor()
        result = date_extractor.extract_date_from_context(test_text, target_citation)
        
        print(f"Target Citation: {target_citation}")
        print(f"  Extracted Year: '{result}'")
        print(f"  Expected: '2014'")
        print()
        
        # Check if it extracted the correct year
        year_correct = result == "2014"
        
        print("=== Date Extraction Test Results ===")
        print(f"Year: {'✅ CORRECT' if year_correct else '❌ WRONG'}")
        
        if year_correct:
            print("\n🎉 SUCCESS: Correct year extracted with isolation!")
        else:
            print("\n⚠️  FAILED: Wrong year extracted - cross-contamination may be occurring!")
            
        return year_correct
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_context_extraction_isolation():
    """Test that context extraction uses isolation logic"""
    
    test_text = """The court in Smith v. Jones, 100 A.2d 123 (2020) held that the plaintiff was entitled to damages. However, in Johnson v. Brown, 200 B.3d 456 (2021), the court reached a different conclusion. The matter was finally resolved in Matter of Bourguignon v. Coordinated Behavioral Health Servs., Inc., 114 A.D.3d 947 (3d Dep't 2014)."""
    
    print("\n=== Testing Context Extraction Isolation ===")
    print(f"Test text: {test_text}")
    print()
    
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        processor = UnifiedCitationProcessorV2()
        
        # Test the _extract_context method
        citation_start = test_text.find("114 A.D.3d 947")
        citation_end = citation_start + len("114 A.D.3d 947")
        
        context = processor._extract_context(test_text, citation_start, citation_end)
        
        print(f"Citation: '114 A.D.3d 947'")
        print(f"Citation position: {citation_start} to {citation_end}")
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
            print("\n🎉 SUCCESS: Context extraction uses proper isolation!")
        else:
            print("\n⚠️  ISSUE: Context extraction may not be properly isolated!")
            
        return case_name_in_context and year_in_context and not other_citation_in_context
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_unified_processor_date_extraction():
    """Test that the unified processor's date extraction uses isolation"""
    
    test_text = """The court in Smith v. Jones, 100 A.2d 123 (2020) held that the plaintiff was entitled to damages. However, in Johnson v. Brown, 200 B.3d 456 (2021), the court reached a different conclusion. The matter was finally resolved in Matter of Bourguignon v. Coordinated Behavioral Health Servs., Inc., 114 A.D.3d 947 (3d Dep't 2014)."""
    
    print("\n=== Testing Unified Processor Date Extraction ===")
    print(f"Test text: {test_text}")
    print()
    
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2, CitationResult
        
        processor = UnifiedCitationProcessorV2()
        
        # Create a citation result for testing
        citation = CitationResult(
            citation="114 A.D.3d 947",
            start_index=test_text.find("114 A.D.3d 947"),
            end_index=test_text.find("114 A.D.3d 947") + len("114 A.D.3d 947")
        )
        
        # Test the date extraction method
        result = processor._extract_date_from_context(test_text, citation)
        
        print(f"Target Citation: {citation.citation}")
        print(f"  Extracted Year: '{result}'")
        print(f"  Expected: '2014'")
        print()
        
        # Check if it extracted the correct year
        year_correct = result == "2014"
        
        print("=== Unified Processor Date Extraction Test Results ===")
        print(f"Year: {'✅ CORRECT' if year_correct else '❌ WRONG'}")
        
        if year_correct:
            print("\n🎉 SUCCESS: Unified processor date extraction uses isolation!")
        else:
            print("\n⚠️  FAILED: Unified processor date extraction may have issues!")
            
        return year_correct
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_case_name_extraction_isolation():
    """Test that case name extraction uses isolation logic"""
    
    test_text = """The court in Smith v. Jones, 100 A.2d 123 (2020) held that the plaintiff was entitled to damages. However, in Johnson v. Brown, 200 B.3d 456 (2021), the court reached a different conclusion. The matter was finally resolved in Matter of Bourguignon v. Coordinated Behavioral Health Servs., Inc., 114 A.D.3d 947 (3d Dep't 2014)."""
    
    print("\n=== Testing Case Name Extraction Isolation ===")
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
        print()
        
        # Check if it extracted the correct case name and year
        case_correct = result['case_name'] == "Matter of Bourguignon v. Coordinated Behavioral Health Servs., Inc."
        year_correct = result['year'] == "2014"
        
        print("=== Case Name Extraction Test Results ===")
        print(f"Case Name: {'✅ CORRECT' if case_correct else '❌ WRONG'}")
        print(f"Year: {'✅ CORRECT' if year_correct else '❌ WRONG'}")
        
        if case_correct and year_correct:
            print("\n🎉 SUCCESS: Case name extraction uses proper isolation!")
        else:
            print("\n⚠️  FAILED: Case name extraction may have cross-contamination issues!")
            
        return case_correct and year_correct
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing that all inferior fallback methods have been improved...")
    print()
    
    test1_success = test_date_extraction_isolation()
    test2_success = test_context_extraction_isolation()
    test3_success = test_unified_processor_date_extraction()
    test4_success = test_case_name_extraction_isolation()
    
    print("\n" + "="*60)
    print("SUMMARY:")
    print(f"  Date Extraction Isolation: {'✅ PASSED' if test1_success else '❌ FAILED'}")
    print(f"  Context Extraction Isolation: {'✅ PASSED' if test2_success else '❌ FAILED'}")
    print(f"  Unified Processor Date Extraction: {'✅ PASSED' if test3_success else '❌ FAILED'}")
    print(f"  Case Name Extraction Isolation: {'✅ PASSED' if test4_success else '❌ FAILED'}")
    
    all_passed = test1_success and test2_success and test3_success and test4_success
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! All inferior fallback methods have been improved!")
        print("   The system now uses sophisticated isolation logic throughout.")
    else:
        print("\n⚠️  Some tests failed. Some inferior fallback methods may still exist.")
        print("   Further improvements may be needed.") 