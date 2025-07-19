#!/usr/bin/env python3
"""
Test the verification flow for Washington citations
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_verification_flow():
    """Test the verification flow"""
    
    print("=== Testing Verification Flow ===")
    
    # Initialize processor
    processor = UnifiedCitationProcessorV2()
    
    # Test citations
    test_citations = [
        "200 Wn.2d 72",
        "256 P.3d 321",
        "43 P.3d 4"
    ]
    
    for citation in test_citations:
        print(f"\n--- Testing: {citation} ---")
        
        try:
            # Test the unified workflow
            result = processor.verify_citation_unified_workflow(citation)
            
            print(f"Citation: {result['citation']}")
            print(f"Verified: {result.get('verified')}")
            print(f"Source: {result.get('verified_by')}")
            print(f"Canonical name: {result.get('canonical_name')}")
            print(f"Canonical date: {result.get('canonical_date')}")
            print(f"URL: {result.get('url')}")
            
            # Check sources
            sources = result.get('sources', {})
            print(f"Sources tried: {list(sources.keys())}")
            
            for source_name, source_result in sources.items():
                print(f"  {source_name}: verified={source_result.get('verified')}, error={source_result.get('error')}")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_verification_flow() 