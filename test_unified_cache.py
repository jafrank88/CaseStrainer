#!/usr/bin/env python3
"""
Test script for the unified cache system

This script tests the Redis-first cache approach with SQLite persistence.
"""

import sys
import os
import json
import time

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.cache_manager import get_cache_manager

def test_basic_cache_operations():
    """Test basic cache operations."""
    print("Testing basic cache operations...")
    
    cache_manager = get_cache_manager()
    
    # Test citation caching
    test_citation = "410 U.S. 113 (1973)"
    test_data = {
        'case_name': 'Brown v. Board of Education',
        'year': 1954,
        'parallel_citations': ['347 U.S. 483'],
        'verification_result': json.dumps({
            'valid': True,
            'found': True,
            'confidence': 0.95,
            'source': 'test'
        })
    }
    
    # Test set
    print(f"Setting citation: {test_citation}")
    success = cache_manager.set_citation(test_citation, test_data)
    print(f"Set result: {'Success' if success else 'Failed'}")
    
    # Test get
    print(f"Getting citation: {test_citation}")
    result = cache_manager.get_citation(test_citation)
    if result:
        print(f"Cache hit: {result.get('case_name', 'N/A')}")
        print(f"Year: {result.get('year', 'N/A')}")
        print(f"Parallel citations: {result.get('parallel_citations', [])}")
    else:
        print("Cache miss")
    
    return success and result is not None

def test_cache_performance():
    """Test cache performance with multiple operations."""
    print("\nTesting cache performance...")
    
    cache_manager = get_cache_manager()
    
    # Test multiple citations
    test_citations = [
        ("347 U.S. 483 (1954)", "Brown v. Board of Education", 1954),
        ("358 U.S. 1 (1958)", "Cooper v. Aaron", 1958),
        ("384 U.S. 436 (1966)", "Miranda v. Arizona", 1966),
        ("403 U.S. 217 (1971)", "Cohen v. California", 1971),
        ("505 U.S. 833 (1992)", "Planned Parenthood v. Casey", 1992)
    ]
    
    # Test set operations
    start_time = time.time()
    for citation, case_name, year in test_citations:
        test_data = {
            'case_name': case_name,
            'year': year,
            'parallel_citations': [],
            'verification_result': json.dumps({
                'valid': True,
                'found': True,
                'confidence': 0.9,
                'source': 'test'
            })
        }
        cache_manager.set_citation(citation, test_data)
    
    set_time = time.time() - start_time
    print(f"Set {len(test_citations)} citations in {set_time:.3f} seconds")
    
    # Test get operations
    start_time = time.time()
    hits = 0
    for citation, case_name, year in test_citations:
        result = cache_manager.get_citation(citation)
        if result and result.get('case_name') == case_name:
            hits += 1
    
    get_time = time.time() - start_time
    print(f"Retrieved {hits}/{len(test_citations)} citations in {get_time:.3f} seconds")
    print(f"Hit rate: {hits/len(test_citations)*100:.1f}%")
    
    return hits == len(test_citations)

def test_cache_stats():
    """Test cache statistics."""
    print("\nTesting cache statistics...")
    
    cache_manager = get_cache_manager()
    stats = cache_manager.get_stats()
    
    print("Cache Statistics:")
    print(f"  Redis Connected: {stats['redis_connected']}")
    
    if stats['cache_stats']:
        for cache_type, cache_stats in stats['cache_stats'].items():
            print(f"  {cache_type}:")
            print(f"    Hits: {cache_stats['hits']}")
            print(f"    Misses: {cache_stats['misses']}")
            print(f"    Hit Rate: {cache_stats['hit_rate']}")
    
    if stats['memory_usage'].get('redis'):
        redis_memory = stats['memory_usage']['redis']
        print(f"  Redis Memory: {redis_memory['used_memory']}")
    
    return stats['redis_connected']

def test_cache_warming():
    """Test cache warming from database."""
    print("\nTesting cache warming...")
    
    cache_manager = get_cache_manager()
    
    # Warm cache with a small number of citations
    warmed_count = cache_manager.warm_cache(limit=10)
    print(f"Warmed {warmed_count} citations from database")
    
    return warmed_count >= 0

def main():
    """Main test function."""
    print("=" * 60)
    print("CaseStrainer Unified Cache System Test")
    print("=" * 60)
    
    tests = [
        ("Basic Cache Operations", test_basic_cache_operations),
        ("Cache Performance", test_cache_performance),
        ("Cache Statistics", test_cache_stats),
        ("Cache Warming", test_cache_warming)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"Result: {'PASS' if result else 'FAIL'}")
        except Exception as e:
            print(f"Error: {e}")
            results.append((test_name, False))
            print("Result: FAIL")
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Unified cache system is working correctly.")
    else:
        print("❌ Some tests failed. Check the output above for details.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 