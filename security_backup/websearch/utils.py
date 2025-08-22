"""
Web Search Utilities Module
Standalone utility functions for web search operations.
"""

from typing import Dict, List, Optional
import asyncio


async def search_cluster_for_canonical_sources(cluster: Dict, max_results: int = 10) -> List[Dict]:
    """Convenience function to search for canonical sources."""
    from .engine import ComprehensiveWebSearchEngine
    engine = ComprehensiveWebSearchEngine()
    return await engine.search_cluster_canonical(cluster, max_results)


def search_all_engines(query: str, num_results: int = 5, engines: Optional[List[str]] = None) -> List[Dict]:
    """Convenience function to search all engines."""
    if engines is None:
        engines = ['google', 'bing']
    
    from .engine import ComprehensiveWebSearchEngine
    engine = ComprehensiveWebSearchEngine()
    all_results = []
    
    for search_engine in engines:
        results = engine.search_with_engine(query, search_engine, num_results)
        all_results.extend(results)
    
    return all_results


async def test_comprehensive_web_search():
    """Test the comprehensive web search engine."""
    print("=== Testing Comprehensive Web Search Engine ===\n")
    
    # Test cluster
    test_cluster = {
        'citations': [
            {'citation': '200 Wn.2d 72'},
            {'citation': '514 P.3d 643'}
        ],
        'canonical_name': 'Convoyant, LLC v. DeepThink, LLC',
        'canonical_date': '2022'
    }
    
    from .engine import ComprehensiveWebSearchEngine
    engine = ComprehensiveWebSearchEngine()
    
    print("Testing query generation:")
    queries = engine.generate_strategic_queries(test_cluster)
    for i, query in enumerate(queries[:5]):  # Show first 5 queries
        print(f"  {i+1}. {query['query']} (Priority: {query['priority']}, Type: {query['type']})")
    
    print("\nTesting search (limited to 3 results):")
    results = await engine.search_cluster_canonical(test_cluster, max_results=3)
    
    for i, result in enumerate(results):
        print(f"\nResult {i+1}:")
        print(f"  Title: {result.get('title', 'N/A')}")
        print(f"  URL: {result.get('url', 'N/A')}")
        print(f"  Reliability Score: {result.get('reliability_score', 0):.2f}")
        print(f"  Source: {result.get('source', 'N/A')}")
        if result.get('extracted_info'):
            extracted = result['extracted_info']
            print(f"  Extracted Case Name: {extracted.get('case_name', 'N/A')}")
            print(f"  Extracted Date: {extracted.get('date', 'N/A')}")
            print(f"  Confidence: {extracted.get('confidence', 0):.2f}") 