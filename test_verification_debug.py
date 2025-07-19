#!/usr/bin/env python3
"""
Debug test for verification workflow
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_verification_debug():
    """Test verification with debug output"""
    
    print("=== Testing Verification with Debug ===")
    
    # Initialize processor
    processor = UnifiedCitationProcessorV2()
    
    # Test citation
    citation = "200 Wn.2d 72"
    
    print(f"Testing citation: {citation}")
    
    try:
        # Test the unified workflow
        result = processor.verify_citation_unified_workflow(citation)
        
        print(f"Citation: {result['citation']}")
        print(f"Verified: {result.get('verified')}")
        print(f"Source: {result.get('verified_by')}")
        print(f"Canonical name: {result.get('canonical_name')}")
        print(f"Canonical date: {result.get('canonical_date')}")
        
        # Check sources
        sources = result.get('sources', {})
        print(f"Sources tried: {list(sources.keys())}")
        
        for source_name, source_result in sources.items():
            print(f"  {source_name}: verified={source_result.get('verified')}, error={source_result.get('error')}")
            
        # Check if legal websearch was tried
        if 'legal_websearch' in sources:
            print(f"Legal websearch result: {sources['legal_websearch']}")
        else:
            print("Legal websearch was NOT tried")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_verification_debug() 