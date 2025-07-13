#!/usr/bin/env python3
"""
Test script for improved case name extraction strategy.
Tests the 1-4 word candidate extraction and canonical name-based selection.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig

def test_improved_case_name_extraction():
    """Test the improved case name extraction strategy."""
    
    # Create processor with debug mode
    config = ProcessingConfig(debug_mode=True, extract_case_names=True)
    processor = UnifiedCitationProcessorV2(config)
    
    # Test cases with different scenarios
    test_cases = [
        {
            "text": "In the case of Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022), the court held...",
            "citation": "200 Wn.2d 72",
            "expected_case_name": "Convoyant, LLC v. DeepThink, LLC"
        },
        {
            "text": "The Supreme Court in Department of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003) ruled...",
            "citation": "146 Wn.2d 1", 
            "expected_case_name": "Department of Ecology v. Campbell & Gwinn, LLC"
        },
        {
            "text": "Smith v. Jones, 150 Wn.2d 100, 75 P.3d 488 (2003) established...",
            "citation": "150 Wn.2d 100",
            "expected_case_name": "Smith v. Jones"
        },
        {
            "text": "In re Estate of Johnson, 180 Wn.2d 200, 322 P.3d 1234 (2014) addressed...",
            "citation": "180 Wn.2d 200",
            "expected_case_name": None  # Should not match, as no v.
        }
    ]
    
    print("Testing Case Name Extraction (comma rule)")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Text: {test_case['text'][:80]}...")
        print(f"Citation: {test_case['citation']}")
        
        # Create a mock citation result
        from src.unified_citation_processor_v2 import CitationResult
        
        # Find citation position in text
        citation_pos = test_case['text'].find(test_case['citation'])
        if citation_pos == -1:
            print("ERROR: Citation not found in text")
            continue
            
        citation_result = CitationResult(
            citation=test_case['citation'],
            start_index=citation_pos,
            end_index=citation_pos + len(test_case['citation'])
        )
        
        # Test full extraction
        extracted_name = processor._extract_case_name_from_context(test_case['text'], citation_result)
        print(f"Extracted Name: '{extracted_name}'")
        print(f"Expected Name: '{test_case['expected_case_name']}'")
        if extracted_name == test_case['expected_case_name']:
            print("PASS")
        else:
            print("FAIL")
        print("-" * 40)

def test_similarity_calculation():
    """Test the similarity calculation function."""
    print("\nTesting Similarity Calculation")
    print("=" * 40)
    
    config = ProcessingConfig(debug_mode=True)
    processor = UnifiedCitationProcessorV2(config)
    
    test_pairs = [
        ("Smith", "Smith v. Jones", 1.0),  # Exact word match
        ("Convoyant, LLC", "Convoyant, LLC v. DeepThink, LLC", 1.0),  # Exact match
        ("Department of Ecology", "Department of Ecology v. Campbell & Gwinn, LLC", 1.0),  # Exact match
        ("Smith", "Jones v. Smith", 1.0),  # Word appears in canonical
        ("Convoyant", "Convoyant, LLC v. DeepThink, LLC", 0.5),  # Partial match
        ("Department", "Department of Ecology v. Campbell & Gwinn, LLC", 0.33),  # Partial match
    ]
    
    for candidate, canonical, expected_similarity in test_pairs:
        similarity = processor._calculate_similarity(candidate, canonical)
        print(f"'{candidate}' vs '{canonical}': {similarity:.2f} (expected ~{expected_similarity})")

if __name__ == "__main__":
    test_improved_case_name_extraction()
    test_similarity_calculation()
    print("\nTest completed!") 