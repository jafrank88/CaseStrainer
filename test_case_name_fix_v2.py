#!/usr/bin/env python3
"""
Test script to verify case name extraction fixes.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig

def test_case_name_extraction():
    """Test case name extraction with the problematic examples."""
    
    # Test cases from the problematic response
    test_cases = [
        {
            'text': 'RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022).',
            'expected_case_name': 'Convoyant, LLC v. DeepThink, LLC',
            'citation': '200 Wn.2d 72'
        },
        {
            'text': 'Dep\'t of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003).',
            'expected_case_name': 'Dep\'t of Ecology v. Campbell & Gwinn, LLC',
            'citation': '146 Wn.2d 1'
        }
    ]
    
    print("=== TESTING CASE NAME EXTRACTION ===")
    
    # Configure processor with debug mode and no confidence filtering
    config = ProcessingConfig(
        use_eyecite=False,
        use_regex=True,
        extract_case_names=True,
        extract_dates=True,
        enable_clustering=True,
        enable_deduplication=False,  # Disable deduplication for testing
        enable_verification=True,  # Enable verification for canonical fields
        debug_mode=True,
        min_confidence=0.0  # Accept all citations
    )
    
    processor = UnifiedCitationProcessorV2(config)
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest Case {i+1}:")
        print(f"Text: {test_case['text']}")
        print(f"Expected case name: {test_case['expected_case_name']}")
        print(f"Citation: {test_case['citation']}")
        
        # Process the text
        results = processor.process_text(test_case['text'])
        
        print(f"Found {len(results)} citations:")
        for j, result in enumerate(results):
            print(f"  Citation {j+1}: {result.citation}")
            print(f"    Extracted case name: {result.extracted_case_name}")
            print(f"    Canonical name: {result.canonical_name}")
            print(f"    Verified: {result.verified}")
            print(f"    URL: {result.url}")
            print(f"    Parallel citations: {result.parallel_citations}")
            print(f"    Confidence: {result.confidence}")
            print(f"    Method: {result.method}")
        
        print("-" * 80)

if __name__ == "__main__":
    test_case_name_extraction() 