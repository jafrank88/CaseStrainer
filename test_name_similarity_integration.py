#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify name similarity matching integration with CourtListener verification.
This tests the specific case of 136 S. Ct. 1083 which returns multiple results.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from courtlistener_verification import verify_with_courtlistener

def test_name_similarity_integration():
    """Test the integrated name similarity matching with CourtListener API."""
    
    # Load API key from environment variable or use the known API key
    api_key = os.environ.get('COURTLISTENER_API_KEY') or "***REDACTED_COURTLISTENER_KEY***"
    
    if not api_key:
        print("ERROR: No API key found")
        return
    
    print("Testing CourtListener name similarity matching integration")
    print("=" * 60)
    
    # Test citation that returns multiple results
    citation = "136 S. Ct. 1083"
    extracted_case_name = "Luis v. United States"
    
    print(f"Citation: {citation}")
    print(f"Extracted case name: {extracted_case_name}")
    print()
    
    # Test with name similarity matching
    print("Testing WITH name similarity matching:")
    print("-" * 40)
    result_with_matching = verify_with_courtlistener(api_key, citation, extracted_case_name)
    
    print(f"Verified: {result_with_matching.get('verified')}")
    print(f"Canonical name: {result_with_matching.get('canonical_name')}")
    print(f"Canonical date: {result_with_matching.get('canonical_date')}")
    print(f"URL: {result_with_matching.get('url')}")
    print()
    
    # Test without name similarity matching (old behavior)
    print("Testing WITHOUT name similarity matching (old behavior):")
    print("-" * 40)
    result_without_matching = verify_with_courtlistener(api_key, citation, None)
    
    print(f"Verified: {result_without_matching.get('verified')}")
    print(f"Canonical name: {result_without_matching.get('canonical_name')}")
    print(f"Canonical date: {result_without_matching.get('canonical_date')}")
    print(f"URL: {result_without_matching.get('url')}")
    print()
    
    # Compare results
    print("COMPARISON:")
    print("-" * 40)
    
    with_matching_name = result_with_matching.get('canonical_name', '')
    without_matching_name = result_without_matching.get('canonical_name', '')
    
    if with_matching_name != without_matching_name:
        print(f"✓ Name similarity matching changed the result!")
        print(f"  Without matching: '{without_matching_name}'")
        print(f"  With matching:    '{with_matching_name}'")
        
        # Check if the result with matching is better
        if "Luis" in with_matching_name and "Luis" not in without_matching_name:
            print(f"✓ Name similarity matching selected the correct case!")
        else:
            print(f"? Name similarity matching selected a different case")
    else:
        print(f"- Name similarity matching did not change the result")
        print(f"  Both returned: '{with_matching_name}'")
    
    print()
    print("Test completed!")

if __name__ == '__main__':
    test_name_similarity_integration()
