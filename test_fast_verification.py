#!/usr/bin/env python3
"""
Test the fast verification system performance and accuracy
"""

import asyncio
import time
from src.fast_verification_system import FastVerificationSystem
from src.enhanced_fallback_verifier import EnhancedFallbackVerifier

async def test_fast_verification():
    """Test the fast verification system"""
    
    print("🚀 TESTING FAST VERIFICATION SYSTEM")
    print("=" * 60)
    
    # Test citations (including D2 59366-1-II style)
    test_citations = [
        "148 Wn.2d 325, 59 P.3d 771 (2002)",  # Washington citation
        "167 Wn.2d 656, 260 P.3d 951 (2011)",  # Washington citation  
        "123 Wn.2d 456 (1998)",               # Simple Washington
        "456 P.3d 789 (2020)",                # Pacific Reporter
        "789 Wn. App. 234 (2015)",            # Washington Appeals
        "347 U.S. 483 (1954)",                # Supreme Court
        "Smith v. Jones, 123 F.3d 456 (1998)" # Federal citation
    ]
    
    # Initialize the fast verifier
    verifier = FastVerificationSystem(enable_web_verification=True, max_timeout=3.0)
    
    print(f"📋 Testing {len(test_citations)} citations...")
    print()
    
    results = []
    
    for i, citation in enumerate(test_citations):
        print(f"--- Test {i+1}: {citation} ---")
        
        start_time = time.time()
        
        # Test verification
        result = await verifier.verify_citation(
            citation, 
            extracted_case_name=f"Test Case {i+1}",
            extracted_date="2023"
        )
        
        end_time = time.time()
        verification_time = end_time - start_time
        
        print(f"✅ Verified: {result.get('verified', False)}")
        print(f"📝 Canonical: '{result.get('canonical_name', 'N/A')}'")
        print(f"📅 Date: {result.get('canonical_date', 'N/A')}")
        print(f"🔍 Source: {result.get('source', 'N/A')}")
        print(f"📊 Confidence: {result.get('confidence', 0):.2f}")
        print(f"⏱️ Time: {verification_time:.2f}s")
        
        if result.get('url'):
            print(f"🔗 URL: {result['url']}")
        
        results.append({
            'citation': citation,
            'verified': result.get('verified', False),
            'time': verification_time,
            'source': result.get('source', 'N/A'),
            'confidence': result.get('confidence', 0)
        })
        
        print()
    
    # Performance summary
    print("📊 PERFORMANCE SUMMARY")
    print("=" * 60)
    
    total_time = sum(r['time'] for r in results)
    verified_count = sum(1 for r in results if r['verified'])
    avg_time = total_time / len(results)
    
    print(f"Total citations: {len(results)}")
    print(f"Verified: {verified_count}/{len(results)} ({verified_count/len(results)*100:.1f}%)")
    print(f"Total time: {total_time:.2f}s")
    print(f"Average time per citation: {avg_time:.2f}s")
    print(f"Fastest verification: {min(r['time'] for r in results):.2f}s")
    print(f"Slowest verification: {max(r['time'] for r in results):.2f}s")
    
    # Source breakdown
    print(f"\n📋 VERIFICATION SOURCES:")
    sources = {}
    for r in results:
        source = r['source']
        sources[source] = sources.get(source, 0) + 1
    
    for source, count in sources.items():
        print(f"  {source}: {count} citations")
    
    # Speed comparison
    print(f"\n🚀 SPEED COMPARISON:")
    print(f"  Old system (7 sources × 15s): ~60+ seconds per citation")
    print(f"  Stub system: ~0.01 seconds (no verification)")
    print(f"  Fast system: ~{avg_time:.1f} seconds per citation")
    print(f"  Speed improvement: ~{60/avg_time:.0f}x faster than old system")
    
    # Test compatibility with original interface
    print(f"\n🔧 COMPATIBILITY TEST:")
    try:
        enhanced_verifier = EnhancedFallbackVerifier(enable_experimental_engines=True)
        
        # Test async method
        result1 = await enhanced_verifier.verify_citation_async("123 Wn.2d 456 (1998)")
        print(f"✅ Async method working: {result1.get('verified', False)}")
        
        # Test sync method (run in separate event loop to avoid conflicts)
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(lambda: enhanced_verifier.verify_citation_sync("456 P.3d 789 (2020)"))
            result2 = future.result(timeout=5)
        print(f"✅ Sync method working: {result2.get('verified', False)}")
        
        # Test main method
        result3 = await enhanced_verifier.verify_citation("789 Wn. App. 234 (2015)")
        print(f"✅ Main method working: {result3.get('verified', False)}")
        
        print(f"✅ All interface methods working correctly")
        
    except Exception as e:
        print(f"❌ Interface compatibility issue: {e}")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_fast_verification())
