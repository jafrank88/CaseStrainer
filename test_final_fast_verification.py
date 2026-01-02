#!/usr/bin/env python3
"""
Final comprehensive test of the fast verification system
"""

import asyncio
import time
from src.enhanced_fallback_verifier import EnhancedFallbackVerifier

async def test_final_fast_verification():
    """Final comprehensive test of the fast verification system"""
    
    print("🎯 FINAL FAST VERIFICATION SYSTEM TEST")
    print("=" * 60)
    
    # Test cases including D2 59366-1-II style citations
    test_cases = [
        {
            "citation": "148 Wn.2d 325, 59 P.3d 771 (2002)",
            "case_name": "State v. Ladson",
            "date": "2002",
            "expected_source": "washington_pattern"
        },
        {
            "citation": "167 Wn.2d 656, 260 P.3d 951 (2011)",
            "case_name": "State v. Harrington", 
            "date": "2011",
            "expected_source": "washington_pattern"
        },
        {
            "citation": "347 U.S. 483 (1954)",
            "case_name": "Brown v. Board of Education",
            "date": "1954", 
            "expected_source": "calculated_fallback"
        },
        {
            "citation": "123 F.3d 456 (9th Cir. 1998)",
            "case_name": "Test Case Federal",
            "date": "1998",
            "expected_source": "calculated_fallback"
        }
    ]
    
    verifier = EnhancedFallbackVerifier(enable_experimental_engines=True)
    
    print(f"📋 Testing {len(test_cases)} citations with fast verification system...")
    print()
    
    results = []
    total_start = time.time()
    
    for i, test_case in enumerate(test_cases):
        print(f"--- Test {i+1}: {test_case['citation']} ---")
        print(f"Expected source: {test_case['expected_source']}")
        
        start_time = time.time()
        
        result = await verifier.verify_citation_async(
            test_case['citation'],
            test_case['case_name'],
            test_case['date'],
            timeout=10.0
        )
        
        end_time = time.time()
        verification_time = end_time - start_time
        
        print(f"✅ Verified: {result.get('verified', False)}")
        print(f"📝 Canonical: '{result.get('canonical_name', 'N/A')}'")
        print(f"📅 Date: {result.get('canonical_date', 'N/A')}")
        print(f"🔍 Source: {result.get('source', 'N/A')}")
        print(f"📊 Confidence: {result.get('confidence', 0):.2f}")
        print(f"⏱️ Time: {verification_time:.3f}s")
        
        # Check if source matches expectation
        actual_source = result.get('source', 'N/A')
        if actual_source == test_case['expected_source']:
            print(f"✅ Source matches expectation")
        else:
            print(f"⚠️ Source mismatch: expected {test_case['expected_source']}, got {actual_source}")
        
        results.append({
            'citation': test_case['citation'],
            'verified': result.get('verified', False),
            'time': verification_time,
            'source': actual_source,
            'confidence': result.get('confidence', 0),
            'expected_source': test_case['expected_source'],
            'source_match': actual_source == test_case['expected_source']
        })
        
        print()
    
    total_end = time.time()
    total_time = total_end - total_start
    
    # Comprehensive analysis
    print("📊 COMPREHENSIVE ANALYSIS")
    print("=" * 60)
    
    verified_count = sum(1 for r in results if r['verified'])
    source_match_count = sum(1 for r in results if r['source_match'])
    avg_time = total_time / len(results)
    
    print(f"Total citations: {len(results)}")
    print(f"Verified: {verified_count}/{len(results)} ({verified_count/len(results)*100:.1f}%)")
    print(f"Source predictions correct: {source_match_count}/{len(results)} ({source_match_count/len(results)*100:.1f}%)")
    print(f"Total time: {total_time:.2f}s")
    print(f"Average time per citation: {avg_time:.3f}s")
    
    # Source breakdown
    print(f"\n📋 VERIFICATION SOURCES:")
    sources = {}
    for r in results:
        source = r['source']
        sources[source] = sources.get(source, 0) + 1
    
    for source, count in sources.items():
        print(f"  {source}: {count} citations")
    
    # Performance comparison
    print(f"\n🚀 PERFORMANCE COMPARISON:")
    print(f"  Old multi-source system: 60+ seconds per citation")
    print(f"  Stub system (no verification): 0.01 seconds per citation")
    print(f"  Fast verification system: {avg_time:.3f} seconds per citation")
    print(f"  Speed improvement: ~{60/avg_time:.0f}x faster than old system")
    
    # Quality assessment
    print(f"\n🎯 QUALITY ASSESSMENT:")
    high_confidence = sum(1 for r in results if r['confidence'] >= 0.7)
    medium_confidence = sum(1 for r in results if 0.5 <= r['confidence'] < 0.7)
    
    print(f"  High confidence (≥0.7): {high_confidence} citations")
    print(f"  Medium confidence (0.5-0.7): {medium_confidence} citations")
    print(f"  Average confidence: {sum(r['confidence'] for r in results)/len(results):.2f}")
    
    # Final assessment
    if verified_count == len(results) and source_match_count >= len(results) * 0.75 and avg_time < 2.0:
        print(f"\n🎉 EXCELLENT: Fast verification system working perfectly!")
        print(f"   ✅ All citations verified")
        print(f"   ✅ Source predictions accurate") 
        print(f"   ✅ Speed under 2 seconds per citation")
    elif verified_count >= len(results) * 0.8 and avg_time < 5.0:
        print(f"\n✅ GOOD: Fast verification system working well")
        print(f"   ✅ Most citations verified")
        print(f"   ✅ Reasonable speed")
    else:
        print(f"\n⚠️ NEEDS IMPROVEMENT: Fast verification system needs tuning")
    
    # D2 59366-1-II specific assessment
    washington_citations = [r for r in results if 'Wn' in r['citation'] or 'P.3d' in r['citation']]
    if washington_citations:
        print(f"\n🏛️ D2 59366-1-II STYLE CITATIONS:")
        washington_verified = sum(1 for r in washington_citations if r['verified'])
        washington_avg_time = sum(r['time'] for r in washington_citations) / len(washington_citations)
        
        print(f"  Washington citations: {len(washington_citations)}")
        print(f"  Verified: {washington_verified}/{len(washington_citations)}")
        print(f"  Average time: {washington_avg_time:.3f}s")
        
        if washington_verified == len(washington_citations) and washington_avg_time < 0.1:
            print(f"  🎉 PERFECT: Washington citations verified instantly!")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_final_fast_verification())
