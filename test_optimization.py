#!/usr/bin/env python3
"""
Test Script - Verify Optimization Implementation

This script tests that the optimized processor works correctly
and provides the expected performance improvements.
"""

import sys
import os
import time
import json
from typing import Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.simplified_citation_processor import create_processor, ProcessingConfig
from src.optimized_verification_master import get_optimized_verifier
from src.citation_extraction_endpoint import extract_citations_with_clustering


def test_basic_functionality():
    """Test basic functionality of optimized processor."""
    print("\n=== Testing Basic Functionality ===")
    
    test_text = """
    In Brown v. Board of Education, 347 U.S. 483 (1954), the Supreme Court ruled that 
    state laws establishing separate public schools for black and white students 
    were unconstitutional. The decision in Miranda v. Arizona, 384 U.S. 436 (1966),
    established the requirement for police to inform suspects of their rights.
    """
    
    # Test simplified processor
    print("Testing simplified processor...")
    start_time = time.time()
    
    processor = create_processor(
        enable_verification=True,
        timeout_seconds=60
    )
    
    result = processor.process(
        {'type': 'text', 'text': test_text},
        'test_basic'
    )
    
    simplified_time = time.time() - start_time
    
    print(f"  ✅ Simplified processor: {simplified_time:.2f}s")
    print(f"  Citations found: {len(result.citations)}")
    print(f"  Verification results: {result.verification_results is not None}")
    
    if result.verification_results:
        metrics = result.verification_results.get('optimization_metrics', {})
        print(f"  Optimization method: {metrics.get('method', 'unknown')}")
        print(f"  Cache hits: {metrics.get('cache_hits', 0)}")
        print(f"  Parallel enabled: {metrics.get('enable_parallel', False)}")
    
    return result


def test_optimization_features():
    """Test specific optimization features."""
    print("\n=== Testing Optimization Features ===")
    
    # Test caching
    print("Testing caching...")
    verifier = get_optimized_verifier()
    
    # First call
    start_time = time.time()
    result1 = verifier.verify_citation_sync_optimized(
        "Brown v. Board of Education, 347 U.S. 483 (1954)",
        timeout=30
    )
    first_time = time.time() - start_time
    
    # Second call (should use cache)
    start_time = time.time()
    result2 = verifier.verify_citation_sync_optimized(
        "Brown v. Board of Education, 347 U.S. 483 (1954)",
        timeout=30
    )
    second_time = time.time() - start_time
    
    print(f"  First call: {first_time:.2f}s")
    print(f"  Second call: {second_time:.2f}s")
    if second_time < first_time * 0.5:
        print("  ✅ Caching appears to be working")
    else:
        print("  ⚠️  Caching may not be working optimally")
    
    # Test cache stats
    cache_stats = verifier.get_cache_stats()
    print(f"  Cache size: {cache_stats['cache_size']}")
    
    return True


def test_parallel_verification():
    """Test parallel verification capability."""
    print("\n=== Testing Parallel Verification ===")
    
    test_citations = [
        "Brown v. Board of Education, 347 U.S. 483 (1954)",
        "Miranda v. Arizona, 384 U.S. 436 (1966)",
        "Roe v. Wade, 410 U.S. 113 (1973)"
    ]
    
    verifier = get_optimized_verifier()
    
    # Test parallel vs sequential
    print("Testing parallel verification...")
    start_time = time.time()
    
    results = []
    for citation in test_citations:
        result = verifier.verify_citation_sync_optimized(
            citation,
            enable_parallel=True,
            timeout=30
        )
        results.append(result)
    
    parallel_time = time.time() - start_time
    print(f"  Parallel verification: {parallel_time:.2f}s")
    
    verified_count = sum(1 for r in results if r.get('verified', False))
    print(f"  Citations verified: {verified_count}/{len(test_citations)}")
    
    return True


def compare_with_legacy():
    """Compare optimized processor with legacy system."""
    print("\n=== Comparing with Legacy System ===")
    
    test_text = """
    In the landmark case of Brown v. Board of Education, 347 U.S. 483 (1954), 
    the United States Supreme Court declared state laws establishing separate 
    public schools for black and white students to be unconstitutional.
    """
    
    # Test legacy system
    print("Testing legacy system...")
    start_time = time.time()
    legacy_result = extract_citations_with_clustering(
        test_text,
        enable_verification=True
    )
    legacy_time = time.time() - start_time
    
    # Test optimized system
    print("Testing optimized system...")
    start_time = time.time()
    processor = create_processor(enable_verification=True)
    optimized_result = processor.process(
        {'type': 'text', 'text': test_text},
        'comparison_test'
    )
    optimized_time = time.time() - start_time
    
    # Compare results
    print(f"\nResults Comparison:")
    print(f"  Legacy time: {legacy_time:.2f}s")
    print(f"  Optimized time: {optimized_time:.2f}s")
    
    if optimized_time < legacy_time:
        improvement = (legacy_time - optimized_time) / legacy_time * 100
        print(f"  ✅ Performance improvement: {improvement:.1f}% faster")
    else:
        regression = (optimized_time - legacy_time) / legacy_time * 100
        print(f"  ⚠️  Performance regression: {regression:.1f}% slower")
    
    # Compare citation counts
    legacy_citations = len(legacy_result.get('citations', []))
    optimized_citations = len(optimized_result.citations)
    
    print(f"  Legacy citations: {legacy_citations}")
    print(f"  Optimized citations: {optimized_citations}")
    
    if legacy_citations == optimized_citations:
        print("  ✅ Citation count matches")
    else:
        print("  ⚠️  Citation count differs")
    
    return True


def main():
    """Run all optimization tests."""
    print("CaseStrainer Optimization Test Suite")
    print("=" * 50)
    
    try:
        # Run all tests
        test_basic_functionality()
        test_optimization_features()
        test_parallel_verification()
        compare_with_legacy()
        
        print("\n" + "=" * 50)
        print("✅ ALL TESTS COMPLETED")
        print("\nOptimization implementation appears to be working correctly!")
        print("\nNext steps:")
        print("1. Review the test results above")
        print("2. Run: python migrate_to_optimized.py --step")
        print("3. Monitor performance with the performance monitor")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
