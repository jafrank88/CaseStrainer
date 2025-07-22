#!/usr/bin/env python3
"""
Test script to check citation extraction for '534 F.3d 1290'
"""

import sys
import os
sys.path.insert(0, 'src')

from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
import logging

# Set up logging to see debug output
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_citation_extraction():
    """Test citation extraction with the problematic citation."""
    
    # Create processor with verification enabled
    config = ProcessingConfig(
        use_eyecite=True,
        use_regex=True,
        extract_case_names=True,
        extract_dates=True,
        enable_clustering=True,
        enable_deduplication=True,
        enable_verification=True,
        debug_mode=True
    )
    
    processor = UnifiedCitationProcessorV2(config)
    
    # Test the citation
    text = '534 F.3d 1290'
    print(f'Testing text: "{text}"')
    print('=' * 50)
    
    results = processor.process_text(text)
    
    print(f'\nFound {len(results)} citations:')
    print('=' * 50)
    
    for i, result in enumerate(results):
        print(f'  {i+1}. Citation: "{result.citation}"')
        print(f'     Pattern: {result.pattern}')
        print(f'     Method: {result.method}')
        print(f'     Verified: {result.verified}')
        print(f'     Case name: {result.extracted_case_name}')
        print(f'     Date: {result.extracted_date}')
        print(f'     Confidence: {result.confidence}')
        print(f'     Source: {result.source}')
        print()
    
    # Also test with a longer text that includes a case name
    print('\n' + '=' * 50)
    print('Testing with case name context:')
    text_with_case = 'Smith v. Jones, 534 F.3d 1290 (2008)'
    print(f'Testing text: "{text_with_case}"')
    print('=' * 50)
    
    results_with_case = processor.process_text(text_with_case)
    
    print(f'\nFound {len(results_with_case)} citations:')
    for i, result in enumerate(results_with_case):
        print(f'  {i+1}. Citation: "{result.citation}"')
        print(f'     Pattern: {result.pattern}')
        print(f'     Method: {result.method}')
        print(f'     Verified: {result.verified}')
        print(f'     Case name: {result.extracted_case_name}')
        print(f'     Date: {result.extracted_date}')
        print(f'     Confidence: {result.confidence}')
        print(f'     Source: {result.source}')
        print()

if __name__ == '__main__':
    test_citation_extraction() 