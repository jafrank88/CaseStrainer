#!/usr/bin/env python3
"""
Test script to verify the fixes for canonical matching and case name extraction.
"""

import logging
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
from src.case_name_extraction_core import extract_case_name_triple_comprehensive

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_fixes():
    """Test both canonical matching and case name extraction fixes."""
    
    print("=== TESTING FIXES ===")
    
    # Test text with known case names
    test_text = """
    A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)
    """
    
    test_cases = [
        ("200 Wn.2d 72", "Convoyant, LLC v. DeepThink, LLC", "2022"),
        ("171 Wn.2d 486", "Carlson v. Glob. Client Sols., LLC", "2011"),
        ("146 Wn.2d 1", "Dep't of Ecology v. Campbell & Gwinn, LLC", "2003")
    ]
    
    # Test case name extraction
    print("\n--- TESTING CASE NAME EXTRACTION FIX ---")
    for citation, expected_case, expected_date in test_cases:
        print(f"\nTesting extraction for: {citation}")
        print(f"Expected case: {expected_case}")
        print(f"Expected date: {expected_date}")
        
        # Test the comprehensive extraction function
        result = extract_case_name_triple_comprehensive(
            text=test_text,
            citation=citation,
            api_key=None,
            context_window=100
        )
        
        print(f"Extraction result:")
        print(f"  Extracted name: {result.get('extracted_name')}")
        print(f"  Case name: {result.get('case_name')}")
        print(f"  Extracted date: {result.get('extracted_date')}")
        print(f"  Method: {result.get('case_name_method')}")
        
        # Check if extraction worked
        if result.get('extracted_name') == expected_case:
            print(f"  ✓ CASE NAME EXTRACTION SUCCESS!")
        else:
            print(f"  ✗ CASE NAME EXTRACTION FAILED!")
            print(f"    Expected: {expected_case}")
            print(f"    Got: {result.get('extracted_name')}")
        
        if result.get('extracted_date') == expected_date:
            print(f"  ✓ DATE EXTRACTION SUCCESS!")
        else:
            print(f"  ✗ DATE EXTRACTION FAILED!")
            print(f"    Expected: {expected_date}")
            print(f"    Got: {result.get('extracted_date')}")
    
    # Test canonical matching
    print("\n--- TESTING CANONICAL MATCHING FIX ---")
    config = ProcessingConfig(debug_mode=True)
    processor = UnifiedCitationProcessorV2(config)
    
    for citation, expected_case, expected_date in test_cases:
        print(f"\nTesting canonical matching for: {citation}")
        print(f"Expected case: {expected_case}")
        print(f"Expected date: {expected_date}")
        
        # Test the verification logic directly
        verify_result = processor._verify_with_courtlistener_search(
            citation=citation,
            extracted_case_name=expected_case,
            extracted_date=expected_date
        )
        
        print(f"Verification result:")
        print(f"  Verified: {verify_result.get('verified')}")
        print(f"  Canonical name: {verify_result.get('canonical_name')}")
        print(f"  Canonical date: {verify_result.get('canonical_date')}")
        print(f"  URL: {verify_result.get('url')}")
        
        # Check if canonical matching worked
        if verify_result.get('verified') and verify_result.get('canonical_name'):
            print(f"  ✓ CANONICAL MATCHING SUCCESS!")
            if verify_result.get('canonical_name') == expected_case:
                print(f"  ✓ CANONICAL NAME MATCHES EXPECTED!")
            else:
                print(f"  ⚠ CANONICAL NAME DIFFERENT BUT VERIFIED")
                print(f"    Expected: {expected_case}")
                print(f"    Got: {verify_result.get('canonical_name')}")
        else:
            print(f"  ✗ CANONICAL MATCHING FAILED!")

def test_end_to_end():
    """Test the complete workflow with both fixes."""
    
    print("\n=== TESTING END-TO-END WORKFLOW ===")
    
    test_text = """
    A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022).
    """
    
    citation = "200 Wn.2d 72"
    expected_case = "Convoyant, LLC v. DeepThink, LLC"
    expected_date = "2022"
    
    print(f"Testing end-to-end workflow for: {citation}")
    
    # Step 1: Extract case name and date
    extraction_result = extract_case_name_triple_comprehensive(
        text=test_text,
        citation=citation,
        api_key=None,
        context_window=100
    )
    
    extracted_case = extraction_result.get('extracted_name')
    extracted_date = extraction_result.get('extracted_date')
    
    print(f"Step 1 - Extraction:")
    print(f"  Extracted case: {extracted_case}")
    print(f"  Extracted date: {extracted_date}")
    
    # Step 2: Verify with CourtListener
    if extracted_case and extracted_date:
        config = ProcessingConfig(debug_mode=True)
        processor = UnifiedCitationProcessorV2(config)
        
        verify_result = processor._verify_with_courtlistener_search(
            citation=citation,
            extracted_case_name=extracted_case,
            extracted_date=extracted_date
        )
        
        print(f"Step 2 - Verification:")
        print(f"  Verified: {verify_result.get('verified')}")
        print(f"  Canonical name: {verify_result.get('canonical_name')}")
        print(f"  Canonical date: {verify_result.get('canonical_date')}")
        print(f"  URL: {verify_result.get('url')}")
        
        # Overall success check
        if (extraction_result.get('extracted_name') == expected_case and 
            verify_result.get('verified')):
            print(f"  ✓ END-TO-END SUCCESS!")
        else:
            print(f"  ✗ END-TO-END FAILED!")
    else:
        print(f"  ✗ EXTRACTION FAILED - CANNOT PROCEED TO VERIFICATION")

if __name__ == "__main__":
    test_fixes()
    test_end_to_end() 