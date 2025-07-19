#!/usr/bin/env python3
"""
Test legal websearch directly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from websearch_utils import LegalWebSearchEngine

def test_legal_websearch():
    """Test legal websearch directly"""
    
    print("=== Testing Legal Websearch Directly ===")
    
    # Initialize engine
    engine = LegalWebSearchEngine(enable_experimental_engines=True)
    
    # Test cluster
    test_cluster = {
        'citations': [{'citation': '200 Wn.2d 72'}],
        'canonical_name': None,
        'canonical_date': None
    }
    
    print(f"Testing cluster: {test_cluster}")
    
    try:
        # Search for results
        results = engine.search_cluster_canonical(test_cluster, max_results=5)
        
        print(f"Found {len(results)} results")
        
        for i, result in enumerate(results[:3], 1):
            print(f"{i}. {result.get('title', 'N/A')}")
            print(f"   URL: {result.get('url', 'N/A')}")
            print(f"   Score: {result.get('reliability_score', 0)}")
            print(f"   Strategy: {result.get('query_strategy', 'N/A')}")
            print()
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_legal_websearch() 