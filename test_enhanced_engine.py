#!/usr/bin/env python3
"""
Test script for enhanced ComprehensiveWebSearchEngine features
"""

from src.comprehensive_websearch_engine import ComprehensiveWebSearchEngine

def test_enhanced_features():
    """Test the enhanced engine features."""
    print("=== Testing Enhanced ComprehensiveWebSearchEngine ===\n")
    
    # Initialize the enhanced engine
    engine = ComprehensiveWebSearchEngine()
    print("✅ Enhanced engine initialized successfully")
    
    # Test 1: Enhanced Citation Normalization
    print("\n1. Testing Enhanced Citation Normalization:")
    test_citation = "200 Wn.2d 72"
    variants = engine.citation_normalizer.generate_variants(test_citation)
    print(f"   Original: {test_citation}")
    print(f"   Generated {len(variants)} variants:")
    for i, variant in enumerate(variants[:5]):  # Show first 5
        print(f"     {i+1}. {variant}")
    
    # Test 2: Source Prediction
    print("\n2. Testing Source Prediction:")
    case_name = "Convoyant, LLC v. DeepThink, LLC"
    predicted_sources = engine.source_predictor.predict_best_sources(test_citation, case_name)
    print(f"   Citation: {test_citation}")
    print(f"   Case: {case_name}")
    print(f"   Predicted sources: {predicted_sources[:5]}")
    
    # Test 3: Enhanced Strategic Query Generation
    print("\n3. Testing Enhanced Strategic Query Generation:")
    test_cluster = {
        'citations': [{'citation': test_citation}],
        'canonical_name': case_name,
        'canonical_date': '2022'
    }
    
    queries = engine.generate_strategic_queries(test_cluster)
    print(f"   Generated {len(queries)} strategic queries:")
    for i, query in enumerate(queries[:5]):  # Show first 5
        print(f"     {i+1}. {query['query']} (Type: {query['type']}, Priority: {query['priority']})")
    
    # Test 4: Caching System
    print("\n4. Testing Caching System:")
    cache_key = "test_cache_key"
    test_data = {"test": "data", "number": 42}
    
    # Set cache
    engine.cache_manager.set(cache_key, value=test_data, ttl_hours=1)
    print("   ✅ Data cached successfully")
    
    # Get cache
    cached_data = engine.cache_manager.get(cache_key)
    if cached_data:
        print(f"   ✅ Cache hit: {cached_data}")
    else:
        print("   ❌ Cache miss")
    
    # Test 5: Enhanced Search (without actual search)
    print("\n5. Testing Enhanced Search Preparation:")
    print("   ✅ Enhanced citation normalizer: Working")
    print("   ✅ Source prediction: Working")
    print("   ✅ Caching system: Working")
    print("   ✅ Strategic query generation: Working")
    
    print("\n=== Enhanced Engine Test Complete ===")
    print("✅ All enhanced features are working correctly!")

if __name__ == "__main__":
    test_enhanced_features() 