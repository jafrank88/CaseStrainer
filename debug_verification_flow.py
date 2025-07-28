#!/usr/bin/env python3
"""
Debug script to trace why CourtListener verification is not happening
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
from src.config import get_config_value

def test_verification_flow():
    print("=== DEBUGGING COURTLISTENER VERIFICATION FLOW ===")
    
    # Test 1: Check API key loading
    api_key = get_config_value("COURTLISTENER_API_KEY")
    print(f"1. API Key loaded: {bool(api_key)}")
    if api_key:
        print(f"   API Key (first 10 chars): {api_key[:10]}...")
    
    # Test 2: Check ProcessingConfig defaults
    config = ProcessingConfig()
    print(f"2. ProcessingConfig defaults:")
    print(f"   enable_verification: {config.enable_verification}")
    print(f"   debug_mode: {config.debug_mode}")
    
    # Test 3: Initialize processor and check its state
    print(f"3. Initializing UnifiedCitationProcessorV2...")
    processor = UnifiedCitationProcessorV2(config)
    print(f"   Processor API key loaded: {bool(processor.courtlistener_api_key)}")
    print(f"   Processor config.enable_verification: {processor.config.enable_verification}")
    
    # Test 4: Process a simple citation
    test_text = "See Luis v. United States, 578 U.S. 5 (2016)."
    print(f"4. Processing test citation: '{test_text}'")
    
    # Enable debug mode for more verbose output
    processor.config.debug_mode = True
    
    result = processor.process_text(test_text)
    
    print(f"5. Results:")
    print(f"   Citations found: {len(result['citations'])}")
    
    for i, citation in enumerate(result['citations']):
        print(f"   Citation {i+1}:")
        print(f"     citation: {citation.citation}")
        print(f"     verified: {citation.verified}")
        print(f"     source: {citation.source}")
        print(f"     canonical_name: {citation.canonical_name}")
        print(f"     canonical_date: {citation.canonical_date}")
        print(f"     extracted_case_name: {citation.extracted_case_name}")
        print(f"     extracted_date: {citation.extracted_date}")

if __name__ == "__main__":
    test_verification_flow()
