#!/usr/bin/env python3
"""
Test script to debug citation verification status issue.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s | %(levelname)s | %(name)s | %(message)s')

def test_courtlistener_verification():
    """Test CourtListener verification directly to see if verification status is preserved."""
    print("Testing CourtListener verification directly...")
    
    verifier = EnhancedMultiSourceVerifier()
    
    # Test with a citation that should be verified
    test_citation = "330 P.3d 168"
    
    print(f"\nTesting citation: {test_citation}")
    
    try:
        result = verifier.verify_citation_unified_workflow(test_citation)
        print(f"Raw result: {result}")
        print(f"Verified status: {result.get('verified')} (type: {type(result.get('verified'))})")
        print(f"Canonical name: {result.get('canonical_name')}")
        print(f"Canonical date: {result.get('canonical_date')}")
        print(f"URL: {result.get('url')}")
        
        # Test if the verification status is preserved when we copy the result
        copied_result = result.copy()
        print(f"Copied result verified status: {copied_result.get('verified')}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_courtlistener_verification() 