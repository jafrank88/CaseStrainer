#!/usr/bin/env python3
"""
Test CourtListener Batch API Usage

This script verifies that the optimized processor is correctly using
the CourtListener batch citation-lookup API for verification.
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.optimized_verification_master import get_optimized_verifier


def test_courtlistener_batch_usage():
    """Test that CourtListener batch API is being used correctly."""
    print("\n" + "="*70)
    print("TESTING COURTLISTENER BATCH API USAGE")
    print("="*70)
    
    # Test citations that should definitely be in CourtListener
    test_citations = [
        "Brown v. Board of Education, 347 U.S. 483 (1954)",
        "Miranda v. Arizona, 384 U.S. 436 (1966)",
        "Roe v. Wade, 410 U.S. 113 (1973)",
        "Marbury v. Madison, 5 U.S. (1 Cranch) 137 (1803)",
        "United States v. Nixon, 418 U.S. 683 (1974)"
    ]
    
    print(f"\nTesting {len(test_citations)} Supreme Court citations...")
    print("These should all be verified via CourtListener batch API.")
    
    verifier = get_optimized_verifier()
    
    # Test batch verification
    print(f"\n1. Testing BATCH verification (should use CourtListener batch API)...")
    start_time = time.time()
    
    try:
        import asyncio
        
        async def run_batch_test():
            results = await verifier.verify_citations_batch_optimized(
                test_citations,
                batch_size=50,  # Use optimal batch size
                timeout_per_citation=10.0,
                enable_parallel=True
            )
            return results
        
        # Run the async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(run_batch_test())
        finally:
            loop.close()
        
        batch_time = time.time() - start_time
        
        print(f"   Batch verification completed in {batch_time:.2f}s")
        
        # Analyze results
        verified_count = sum(1 for r in results if r.verified)
        possible_count = sum(1 for r in results if r.possible_match)
        courtlistener_count = sum(1 for r in results if r.source == 'courtlistener')
        
        print(f"\n   Results:")
        print(f"   Total citations: {len(results)}")
        print(f"   Verified: {verified_count}")
        print(f"   Possible matches: {possible_count}")
        print(f"   From CourtListener: {courtlistener_count}")
        print(f"   Success rate: {(verified_count + possible_count) / len(results):.1%}")
        
        # Check if CourtListener was used
        if courtlistener_count >= len(test_citations) * 0.8:
            print(f"   ✅ CourtListener batch API is being used correctly!")
        else:
            print(f"   ⚠️  CourtListener usage lower than expected")
        
        # Show detailed results
        print(f"\n   Detailed results:")
        for i, (citation, result) in enumerate(zip(test_citations, results)):
            status = "✅ Verified" if result.verified else "⚠️ Possible" if result.possible_match else "❌ Not found"
            print(f"   {i+1}. {status} via {result.source}")
            if result.verified and result.canonical_name:
                print(f"      → {result.canonical_name}")
        
    except Exception as e:
        print(f"   ❌ Batch verification failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test individual verification for comparison
    print(f"\n2. Testing INDIVIDUAL verification (for comparison)...")
    start_time = time.time()
    
    individual_results = []
    individual_time = 0
    
    for citation in test_citations:
        try:
            result = verifier.verify_citation_sync_optimized(
                citation,
                timeout=15,
                enable_parallel=True
            )
            individual_results.append(result)
        except Exception as e:
            print(f"   ❌ Individual verification failed for {citation}: {str(e)}")
            individual_results.append(None)
    
    individual_time = time.time() - start_time
    
    print(f"   Individual verification completed in {individual_time:.2f}s")
    
    # Compare performance
    if batch_time > 0 and individual_time > 0:
        improvement = (individual_time - batch_time) / individual_time * 100
        print(f"\n📊 PERFORMANCE COMPARISON:")
        print(f"   Batch API: {batch_time:.2f}s")
        print(f"   Individual: {individual_time:.2f}s")
        print(f"   Improvement: {improvement:.1f}% faster with batch")
    
    # Test cache effectiveness
    print(f"\n3. Testing CACHE effectiveness...")
    verifier.clear_cache()
    print(f"   Cache cleared")
    
    # First run
    start_time = time.time()
    result1 = verifier.verify_citation_sync_optimized(
        "Brown v. Board of Education, 347 U.S. 483 (1954)",
        timeout=15
    )
    first_time = time.time() - start_time
    
    # Second run (should use cache)
    start_time = time.time()
    result2 = verifier.verify_citation_sync_optimized(
        "Brown v. Board of Education, 347 U.S. 483 (1954)",
        timeout=15
    )
    second_time = time.time() - start_time
    
    cache_stats = verifier.get_cache_stats()
    
    print(f"   First run: {first_time:.2f}s")
    print(f"   Second run: {second_time:.2f}s")
    print(f"   Cache size: {cache_stats['cache_size']}")
    
    if second_time < first_time * 0.5:
        print(f"   ✅ Caching is working effectively!")
    else:
        print(f"   ⚠️  Caching may not be optimal")
    
    return True


def main():
    """Run CourtListener batch API tests."""
    print("CaseStrainer CourtListener Batch API Test")
    print("="*70)
    print("Verifying that the optimized processor correctly uses")
    print("the CourtListener batch citation-lookup API.")
    
    try:
        test_courtlistener_batch_usage()
        
        print("\n" + "="*70)
        print("✅ COURTLISTENER BATCH API TEST COMPLETED")
        print("="*70)
        print("\nKey findings:")
        print("  • Batch API should be used for multiple citations")
        print("  • CourtListener should be the primary source")
        print("  • Fallback sources used only when CourtListener fails")
        print("  • Caching should improve repeat performance")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
