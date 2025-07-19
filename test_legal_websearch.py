#!/usr/bin/env python3
"""
Test legal websearch for citation 534 F.3d 1290
"""

import sys
import os
import asyncio
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from websearch_utils import LegalWebSearchEngine, search_cluster_for_canonical_sources

def test_legal_websearch():
    """Test legal websearch for the specific citation"""
    
    print("=== Testing Legal Websearch for 534 F.3d 1290 ===")
    
    # Create a test cluster with the citation
    test_cluster = {
        'citations': [
            {'citation': '534 F.3d 1290'}
        ],
        'canonical_name': 'United States v. Caraway',
        'canonical_date': '2008-07-28',
        'extracted_case_name': 'United States v. Caraway',
        'extracted_date': '2008'
    }
    
    print(f"Test cluster: {test_cluster}")
    
    # Test the search function
    print("\n--- Testing search_cluster_for_canonical_sources ---")
    start_time = time.time()
    
    try:
        results = search_cluster_for_canonical_sources(test_cluster, max_results=5)
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"✅ Search completed in {processing_time:.2f} seconds")
        print(f"Results found: {len(results)}")
        
        for i, result in enumerate(results):
            print(f"\nResult {i+1}:")
            print(f"  URL: {result.get('url', 'N/A')}")
            print(f"  Title: {result.get('title', 'N/A')}")
            print(f"  Snippet: {result.get('snippet', 'N/A')[:100]}...")
            print(f"  Source: {result.get('source', 'N/A')}")
            print(f"  Reliability Score: {result.get('reliability_score', 'N/A')}")
            print(f"  Query Strategy: {result.get('query_strategy', 'N/A')}")
            
    except Exception as e:
        end_time = time.time()
        processing_time = end_time - start_time
        print(f"❌ Search failed after {processing_time:.2f} seconds: {e}")
        import traceback
        traceback.print_exc()
    
    # Test the LegalWebSearchEngine directly
    print("\n--- Testing LegalWebSearchEngine directly ---")
    start_time = time.time()
    
    try:
        engine = LegalWebSearchEngine()
        results = engine.search_cluster_canonical(test_cluster, max_results=5)
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"✅ Direct engine search completed in {processing_time:.2f} seconds")
        print(f"Results found: {len(results)}")
        
        for i, result in enumerate(results):
            print(f"\nResult {i+1}:")
            print(f"  URL: {result.get('url', 'N/A')}")
            print(f"  Title: {result.get('title', 'N/A')}")
            print(f"  Snippet: {result.get('snippet', 'N/A')[:100]}...")
            print(f"  Source: {result.get('source', 'N/A')}")
            print(f"  Reliability Score: {result.get('reliability_score', 'N/A')}")
            print(f"  Query Strategy: {result.get('query_strategy', 'N/A')}")
            
    except Exception as e:
        end_time = time.time()
        processing_time = end_time - start_time
        print(f"❌ Direct engine search failed after {processing_time:.2f} seconds: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_legal_websearch() 