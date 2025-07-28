#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test to verify name similarity matching is working.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from courtlistener_verification import verify_with_courtlistener

def test_simple_name_similarity():
    """Test name similarity matching directly with CourtListener verification."""
    
    print("Testing Name Similarity Matching Directly")
    print("=" * 50)
    
    # Use the known API key
    api_key = "***REDACTED_COURTLISTENER_KEY***"
    
    # Test the problematic citation
    citation = "136 S. Ct. 1083"
    extracted_case_name = "Luis v. United States"
    
    print(f"Citation: {citation}")
    print(f"Extracted case name: {extracted_case_name}")
    print()
    
    # Test WITH name similarity matching
    print("Testing WITH name similarity matching:")
    print("-" * 30)
    result_with_matching = verify_with_courtlistener(api_key, citation, extracted_case_name)
    
    print(f"Verified: {result_with_matching.get('verified')}")
    print(f"Canonical name: {result_with_matching.get('canonical_name')}")
    print(f"Canonical date: {result_with_matching.get('canonical_date')}")
    print()
    
    # Test WITHOUT name similarity matching (old behavior)
    print("Testing WITHOUT name similarity matching:")
    print("-" * 30)
    result_without_matching = verify_with_courtlistener(api_key, citation, None)
    
    print(f"Verified: {result_without_matching.get('verified')}")
    print(f"Canonical name: {result_without_matching.get('canonical_name')}")
    print(f"Canonical date: {result_without_matching.get('canonical_date')}")
    print()
    
    # Compare results
    print("COMPARISON:")
    print("-" * 30)
    
    with_matching_name = result_with_matching.get('canonical_name', '')
    without_matching_name = result_without_matching.get('canonical_name', '')
    
    if with_matching_name != without_matching_name:
        print(f"✅ Name similarity matching changed the result!")
        print(f"  Without matching: '{without_matching_name}'")
        print(f"  With matching:    '{with_matching_name}'")
        
        if "Luis" in with_matching_name and "Luis" not in without_matching_name:
            print(f"✅ Name similarity matching selected the correct case!")
        else:
            print(f"? Name similarity matching selected a different case")
    else:
        print(f"❌ Name similarity matching did not change the result")
        print(f"  Both returned: '{with_matching_name}'")
    
    print("\nTest completed!")

if __name__ == '__main__':
    test_simple_name_similarity()
