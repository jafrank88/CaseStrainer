#!/usr/bin/env python3

def test_comprehensive_websearch():
    print("=== Testing Comprehensive Web Search Engine ===\n")
    
    try:
        from src.comprehensive_websearch_engine import ComprehensiveWebSearchEngine
        
        # Test cluster with Convoyant case
        test_cluster = {
            'citations': [
                {'citation': '200 Wn.2d 72'},
                {'citation': '514 P.3d 643'}
            ],
            'canonical_name': 'Convoyant, LLC v. DeepThink, LLC',
            'canonical_date': '2022'
        }
        
        print("Initializing ComprehensiveWebSearchEngine...")
        engine = ComprehensiveWebSearchEngine(enable_experimental_engines=True)
        
        print("\nTesting query generation:")
        queries = engine.generate_strategic_queries(test_cluster)
        print(f"Generated {len(queries)} strategic queries")
        
        for i, query in enumerate(queries[:5]):  # Show first 5 queries
            print(f"  {i+1}. {query['query']} (Priority: {query['priority']}, Type: {query['type']})")
        
        print("\nTesting citation variants:")
        from src.citation_normalizer import generate_citation_variants
        citation_variants = generate_citation_variants('200 Wn.2d 72')
        print(f"Citation variants for '200 Wn.2d 72':")
        for variant in citation_variants:
            print(f"  - {variant}")
        
        print("\nTesting case name variants:")
        case_variants = engine.extract_case_name_variants('Convoyant, LLC v. DeepThink, LLC')
        print(f"Case name variants:")
        for variant in case_variants:
            print(f"  - {variant}")
        
        print("\n✅ Comprehensive websearch engine is working correctly!")
        
    except Exception as e:
        print(f"❌ Error testing comprehensive websearch: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_comprehensive_websearch() 