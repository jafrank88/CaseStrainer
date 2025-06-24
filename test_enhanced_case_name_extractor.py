#!/usr/bin/env python3
"""
Test script for the Enhanced Case Name Extractor

This script demonstrates how the enhanced case name extractor works,
comparing it with the original extraction method and showing how
canonical case names from CourtListener improve extraction accuracy.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from enhanced_case_name_extractor import EnhancedCaseNameExtractor, extract_case_names_enhanced
from citation_extractor import CitationExtractor

def test_enhanced_extraction():
    """Test the enhanced case name extraction with sample text."""
    
    # Sample legal text with citations and case names
    sample_text = """
    The court's prior decision in Walston v. Boeing Co. , 181 Wn.2d 391, 334 P.3d 519 (2014), 
    established that no employee could sue for wrongful termination. In Brown v. Board of Education, 
    347 U.S. 483 (1954), the Supreme Court held that separate educational facilities are inherently unequal.
    
    The plaintiff argues that under Smith v. Jones, 456 F.3d 789 (2006), the defendant's conduct 
    constitutes negligence. However, the defendant contends that Johnson v. State, 789 P.2d 123 (1990), 
    provides a complete defense to these allegations.
    
    In re Estate of Smith, 234 Wn.2d 456 (2018), the court addressed similar issues regarding 
    testamentary capacity. The case of United States v. Caraway, 534 F.3d 1290 (2008), provides 
    guidance on federal jurisdiction in these matters.
    """
    
    print("=== Enhanced Case Name Extractor Test ===\n")
    print("Sample text:")
    print("-" * 50)
    print(sample_text)
    print("-" * 50)
    
    # Test 1: Enhanced extraction with canonical guidance
    print("\n1. Testing Enhanced Extraction with Canonical Guidance:")
    print("=" * 60)
    
    try:
        extractor = EnhancedCaseNameExtractor()
        results = extractor.extract_case_names_with_canonical_guidance(
            sample_text, use_canonical_guidance=True
        )
        
        print(f"Found {len(results)} citations with case names:")
        for i, result in enumerate(results, 1):
            print(f"\nResult {i}:")
            print(f"  Citation: {result['citation']}")
            print(f"  Extracted Case Name: {result['extracted_case_name']}")
            print(f"  Extraction Method: {result['extraction_method']}")
            print(f"  Extraction Confidence: {result['extraction_confidence']:.2f}")
            print(f"  Canonical Case Name: {result['canonical_case_name']}")
            print(f"  Similarity Score: {result['similarity_score']:.2f}")
            print(f"  Final Confidence: {result['final_confidence']:.2f}")
            
            # Show context
            context_before = result['context_before'][-100:] if result['context_before'] else ""
            context_after = result['context_after'][:100] if result['context_after'] else ""
            print(f"  Context: ...{context_before} [{result['citation']}] {context_after}...")
            
    except Exception as e:
        print(f"Error in enhanced extraction: {e}")
    
    # Test 2: Enhanced extraction without canonical guidance
    print("\n\n2. Testing Enhanced Extraction WITHOUT Canonical Guidance:")
    print("=" * 60)
    
    try:
        results_no_guidance = extractor.extract_case_names_with_canonical_guidance(
            sample_text, use_canonical_guidance=False
        )
        
        print(f"Found {len(results_no_guidance)} citations with case names:")
        for i, result in enumerate(results_no_guidance, 1):
            print(f"\nResult {i}:")
            print(f"  Citation: {result['citation']}")
            print(f"  Extracted Case Name: {result['extracted_case_name']}")
            print(f"  Extraction Method: {result['extraction_method']}")
            print(f"  Extraction Confidence: {result['extraction_confidence']:.2f}")
            print(f"  Final Confidence: {result['final_confidence']:.2f}")
            
    except Exception as e:
        print(f"Error in enhanced extraction without guidance: {e}")
    
    # Test 3: Compare with original extraction method
    print("\n\n3. Comparing with Original Extraction Method:")
    print("=" * 60)
    
    try:
        original_extractor = CitationExtractor()
        original_results = original_extractor.extract_case_names_from_text(sample_text, [])
        
        print(f"Original method found {len(original_results)} case names:")
        for i, result in enumerate(original_results, 1):
            print(f"  {i}. {result['citation']} -> {result['case_name']}")
            
    except Exception as e:
        print(f"Error in original extraction: {e}")
    
    # Test 4: Test specific citation with known canonical name
    print("\n\n4. Testing Specific Citation with Known Canonical Name:")
    print("=" * 60)
    
    test_citation = "347 U.S. 483"
    test_text = f"In Brown v. Board of Education, {test_citation}, the Supreme Court held that separate educational facilities are inherently unequal."
    
    try:
        specific_result = extractor.extract_case_names_with_canonical_guidance(
            test_text, citations=[test_citation], use_canonical_guidance=True
        )
        
        if specific_result:
            result = specific_result[0]
            print(f"Citation: {result['citation']}")
            print(f"Extracted: {result['extracted_case_name']}")
            print(f"Canonical: {result['canonical_case_name']}")
            print(f"Similarity: {result['similarity_score']:.2f}")
            print(f"Confidence: {result['final_confidence']:.2f}")
            
            if result['canonical_case_name'] and result['canonical_case_name'] != "Unknown Case":
                print("✓ Successfully retrieved canonical case name from CourtListener!")
            else:
                print("✗ Could not retrieve canonical case name (may need API key)")
        else:
            print("No results found for test citation")
            
    except Exception as e:
        print(f"Error in specific citation test: {e}")

def test_integration_with_existing_pipeline():
    """Test how the enhanced extractor integrates with the existing pipeline."""
    
    print("\n\n=== Integration Test with Existing Pipeline ===")
    print("=" * 60)
    
    # Sample text
    sample_text = """
    The court's decision in Walston v. Boeing Co. , 181 Wn.2d 391, 334 P.3d 519 (2014), 
    established important precedent for employment law cases.
    """
    
    try:
        # Use the convenience function
        results = extract_case_names_enhanced(sample_text, use_canonical_guidance=True)
        
        print(f"Integration test found {len(results)} results:")
        for result in results:
            print(f"  {result['citation']} -> {result['extracted_case_name']} (confidence: {result['final_confidence']:.2f})")
            
    except Exception as e:
        print(f"Integration test error: {e}")

if __name__ == "__main__":
    print("Enhanced Case Name Extractor Test Suite")
    print("=" * 50)
    
    # Run tests
    test_enhanced_extraction()
    test_integration_with_existing_pipeline()
    
    print("\n\nTest completed!")
    print("\nKey Features Demonstrated:")
    print("1. Multiple extraction strategies with confidence scoring")
    print("2. Canonical case name lookup via CourtListener API")
    print("3. Similarity scoring between extracted and canonical names")
    print("4. Integration with existing citation extraction pipeline")
    print("5. Flexible context window analysis") 