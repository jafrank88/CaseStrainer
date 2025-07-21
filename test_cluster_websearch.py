#!/usr/bin/env python3

def test_cluster_websearch():
    print("=== Testing Cluster-Based Websearch ===\n")
    
    try:
        from src.comprehensive_websearch_engine import ComprehensiveWebSearchEngine as LegalWebSearchEngine
        
        # Test with a cluster containing both Convoyant citations
        test_cluster = {
            'citations': [
                {'citation': '200 Wn.2d 72'},
                {'citation': '514 P.3d 643'}
            ],
            'canonical_name': None,
            'canonical_date': None
        }
        
        print("Testing websearch query generation for cluster:")
        print(f"Cluster citations: {[c['citation'] for c in test_cluster['citations']]}")
        print()
        
        engine = LegalWebSearchEngine()
        queries = engine.generate_strategic_queries(test_cluster)
        
        print(f"Generated {len(queries)} queries:")
        for i, query_info in enumerate(queries[:10], 1):  # Show first 10 queries
            print(f"  {i}. {query_info['query']} (strategy: {query_info['strategy']})")
            
        print(f"\n... and {len(queries) - 10} more queries" if len(queries) > 10 else "")
        
        # Test the actual websearch
        print(f"\nTesting actual websearch for cluster:")
        results = engine.search_cluster_canonical(test_cluster, max_results=3)
        
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results[:3], 1):
            print(f"  {i}. {result.get('title', 'N/A')}")
            print(f"     URL: {result.get('url', 'N/A')}")
            print(f"     Score: {result.get('reliability_score', 'N/A')}")
            print(f"     Strategy: {result.get('query_strategy', 'N/A')}")
            print()
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cluster_websearch() 