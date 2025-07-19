#!/usr/bin/env python3
"""
Test script to verify ComprehensiveWebSearchEngine integration
"""

import asyncio
import logging
from src.comprehensive_websearch_engine import ComprehensiveWebSearchEngine
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_comprehensive_engine():
    """Test the comprehensive websearch engine."""
    print("=== Testing ComprehensiveWebSearchEngine Integration ===\n")
    
    try:
        # Test 1: Initialize the engine
        print("1. Testing engine initialization...")
        engine = ComprehensiveWebSearchEngine(enable_experimental_engines=True)
        print("✅ ComprehensiveWebSearchEngine initialized successfully")
        
        # Test 2: Check available search methods
        print("\n2. Checking available search methods...")
        search_methods = [m for m in dir(engine) if m.startswith('search_') and callable(getattr(engine, m))]
        print(f"✅ Found {len(search_methods)} search methods:")
        for method in sorted(search_methods):
            print(f"   - {method}")
        
        # Test 3: Test strategic query generation
        print("\n3. Testing strategic query generation...")
        test_cluster = {
            'citations': [
                {'citation': '200 Wn.2d 72'},
                {'citation': '514 P.3d 643'}
            ],
            'canonical_name': 'Convoyant, LLC v. DeepThink, LLC',
            'canonical_date': '2022'
        }
        
        queries = engine.generate_strategic_queries(test_cluster)
        print(f"✅ Generated {len(queries)} strategic queries")
        for i, query in enumerate(queries[:3]):  # Show first 3
            print(f"   {i+1}. {query['query']} (Priority: {query['priority']})")
        
        # Test 4: Test search cluster canonical
        print("\n4. Testing search_cluster_canonical...")
        results = engine.search_cluster_canonical(test_cluster, max_results=3)
        print(f"✅ Found {len(results)} search results")
        
        # Test 5: Test unified citation processor integration
        print("\n5. Testing UnifiedCitationProcessorV2 integration...")
        processor = UnifiedCitationProcessorV2()
        print("✅ UnifiedCitationProcessorV2 initialized successfully")
        
        # Test 6: Test citation processing with websearch
        print("\n6. Testing citation processing with websearch...")
        test_text = "A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022)."
        
        citations = processor.process_text(test_text)
        print(f"✅ Extracted {len(citations)} citations")
        
        for citation in citations:
            print(f"   - {citation.citation} (verified: {citation.verified})")
        
        print("\n=== Integration Test Complete ===")
        print("✅ All tests passed! ComprehensiveWebSearchEngine is fully integrated.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.exception("Test failed")

def test_sync_functions():
    """Test synchronous functions."""
    print("\n=== Testing Synchronous Functions ===\n")
    
    try:
        from src.comprehensive_websearch_engine import search_cluster_for_canonical_sources, search_all_engines
        
        # Test search_cluster_for_canonical_sources
        print("1. Testing search_cluster_for_canonical_sources...")
        test_cluster = {
            'citations': [{'citation': '200 Wn.2d 72'}],
            'canonical_name': 'Convoyant, LLC v. DeepThink, LLC',
            'canonical_date': '2022'
        }
        
        results = search_cluster_for_canonical_sources(test_cluster, max_results=2)
        print(f"✅ Found {len(results)} results from search_cluster_for_canonical_sources")
        
        # Test search_all_engines
        print("\n2. Testing search_all_engines...")
        results = search_all_engines("Convoyant LLC v DeepThink LLC", num_results=2)
        print(f"✅ Found {len(results)} results from search_all_engines")
        
        print("\n✅ All synchronous tests passed!")
        
    except Exception as e:
        print(f"❌ Synchronous test failed: {e}")
        logger.exception("Synchronous test failed")

if __name__ == "__main__":
    # Run async tests
    asyncio.run(test_comprehensive_engine())
    
    # Run sync tests
    test_sync_functions() 