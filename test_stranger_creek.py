#!/usr/bin/env python3
"""
Test script to investigate why the Stranger Creek case wasn't found
"""

import sys
import os
sys.path.append('src')

from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_stranger_creek():
    """Test different formats of the Stranger Creek citation"""
    
    # Initialize verifier
    verifier = EnhancedMultiSourceVerifier()
    
    # Test different citation formats
    test_citations = [
        "77 Wash. 2d 649",  # Our cleaned format
        "77 Wn. 2d 649",    # Original format from text
        "466 P.2d 508",     # Pacific Reporter format
        "In re Rts. to Waters of Stranger Creek, 77 Wn. 2d 649, 653, 466 P.2d 508 (1970)",  # Full citation
        "In re Stranger Creek, 77 Wn. 2d 649",  # Shortened case name
    ]
    
    print("Testing Stranger Creek citation formats:")
    print("=" * 60)
    
    for i, citation in enumerate(test_citations, 1):
        print(f"\n{i}. Testing: {citation}")
        
        # Test CourtListener lookup
        lookup_result = verifier._lookup_citation(citation)
        print(f"   Lookup result: {lookup_result.get('verified', False)}")
        
        if lookup_result.get('verified'):
            print(f"   Case name: {lookup_result.get('case_name', 'N/A')}")
            print(f"   URL: {lookup_result.get('url', 'N/A')}")
            print(f"   Parallel citations: {lookup_result.get('parallel_citations', [])}")
        else:
            print(f"   Error: {lookup_result.get('error', 'N/A')}")
        
        # Test exact search
        search_result = verifier._search_courtlistener_exact(citation)
        print(f"   Search result: {search_result.get('verified', False)}")
        
        if search_result.get('verified'):
            print(f"   Case name: {search_result.get('case_name', 'N/A')}")
            print(f"   URL: {search_result.get('url', 'N/A')}")
        else:
            print(f"   Search error: {search_result.get('warning', 'N/A')}")

if __name__ == "__main__":
    test_stranger_creek() 