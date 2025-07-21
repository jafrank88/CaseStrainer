#!/usr/bin/env python3

def test_websearch_normalization():
    print("=== Testing Websearch Citation Normalization ===\n")
    
    try:
        from src.comprehensive_websearch_engine import ComprehensiveWebSearchEngine as LegalWebSearchEngine
        
        # Test the normalization function directly
        engine = LegalWebSearchEngine()
        
        test_citations = [
            "200 Wn.2d 72",
            "200 Wash.2d 72", 
            "171 Wn.2d 486",
            "146 Wn.2d 1"
        ]
        
        print("Testing citation normalization:")
        for citation in test_citations:
            normalized = engine.normalize_citation(citation)
            print(f"  Original: {citation}")
            print(f"  Normalized: {normalized.get('normalized', 'No normalization')}")
            print(f"  Reporter: {normalized.get('reporter', 'N/A')}")
            print()
        
        # Test websearch query generation
        print("Testing websearch query generation:")
        test_cluster = {
            'citations': [{'citation': '200 Wn.2d 72'}],
            'canonical_name': None,
            'canonical_date': None
        }
        
        queries = engine.generate_strategic_queries(test_cluster)
        print(f"Generated {len(queries)} queries:")
        for i, query_info in enumerate(queries[:5], 1):  # Show first 5 queries
            print(f"  {i}. {query_info['query']} (strategy: {query_info['strategy']})")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_websearch_normalization() 