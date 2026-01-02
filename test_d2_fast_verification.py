#!/usr/bin/env python3
"""
Test fast verification with D2 59366-1-II scenario
"""

import asyncio
import time
from src.enhanced_fallback_verifier import EnhancedFallbackVerifier

async def test_d2_fast_verification():
    """Test fast verification with D2 59366-1-II citations"""
    
    print("🏛️ TESTING D2 59366-1-II FAST VERIFICATION")
    print("=" * 60)
    
    # D2 59366-1-II style citations
    d2_citations = [
        "148 Wn.2d 325, 59 P.3d 771 (2002)",
        "167 Wn.2d 656, 260 P.3d 951 (2011)", 
        "168 Wn.2d 496, 229 P.3d 729 (2010)",
        "133 Wn.2d 598, 947 P.2d 1001 (1997)",
        "102 Wn. App. 745, 8 P.3d 647 (2000)",
        "191 Wn. App. 860, 361 P.3d 718 (2015)",
        "185 Wn.2d 397, 373 P.3d 185 (2016)"
    ]
    
    # Case names that would be extracted from context
    extracted_names = [
        "State v. Ladson",
        "State v. Harrington", 
        "State v. Madsen",
        "State v. Kennedy",
        "State v. Williams",
        "State v. Gorman",
        "State v. Rivera"
    ]
    
    # Initialize the verifier
    verifier = EnhancedFallbackVerifier(enable_experimental_engines=True)
    
    print(f"📋 Testing {len(d2_citations)} Washington Court of Appeals citations...")
    print()
    
    results = []
    total_start = time.time()
    
    for i, (citation, case_name) in enumerate(zip(d2_citations, extracted_names)):
        print(f"--- D2 Citation {i+1}: {citation} ---")
        print(f"Expected case: {case_name}")
        
        start_time = time.time()
        
        # Test verification with extracted case name
        result = await verifier.verify_citation(
            citation, 
            extracted_case_name=case_name,
            extracted_date="2024"
        )
        
        end_time = time.time()
        verification_time = end_time - start_time
        
        print(f"✅ Verified: {result.get('verified', False)}")
        print(f"📝 Canonical: '{result.get('canonical_name', 'N/A')}'")
        print(f"📅 Date: {result.get('canonical_date', 'N/A')}")
        print(f"🔍 Source: {result.get('source', 'N/A')}")
        print(f"📊 Confidence: {result.get('confidence', 0):.2f}")
        print(f"⏱️ Time: {verification_time:.3f}s")
        
        # Check if it's using extracted case name
        if result.get('canonical_name') == case_name:
            print(f"✅ Using extracted case name correctly")
        elif result.get('source') == 'washington_pattern':
            print(f"✅ Using Washington pattern verification")
        else:
            print(f"⚠️ Different canonical name detected")
        
        if result.get('url'):
            print(f"🔗 URL: {result['url']}")
        
        results.append({
            'citation': citation,
            'verified': result.get('verified', False),
            'time': verification_time,
            'source': result.get('source', 'N/A'),
            'confidence': result.get('confidence', 0),
            'canonical_name': result.get('canonical_name', 'N/A'),
            'used_extracted_name': result.get('canonical_name') == case_name
        })
        
        print()
    
    total_end = time.time()
    total_time = total_end - total_start
    
    # Performance analysis
    print("📊 D2 59366-1-II PERFORMANCE ANALYSIS")
    print("=" * 60)
    
    verified_count = sum(1 for r in results if r['verified'])
    avg_time = total_time / len(results)
    extracted_name_count = sum(1 for r in results if r['used_extracted_name'])
    
    print(f"Total citations: {len(results)}")
    print(f"Verified: {verified_count}/{len(results)} ({verified_count/len(results)*100:.1f}%)")
    print(f"Total time: {total_time:.2f}s")
    print(f"Average time per citation: {avg_time:.3f}s")
    print(f"Used extracted case names: {extracted_name_count}/{len(results)}")
    
    # Source breakdown
    print(f"\n📋 VERIFICATION SOURCES:")
    sources = {}
    for r in results:
        source = r['source']
        sources[source] = sources.get(source, 0) + 1
    
    for source, count in sources.items():
        print(f"  {source}: {count} citations")
    
    # Speed comparison for D2 scenario
    print(f"\n🚀 D2 59366-1-II SPEED COMPARISON:")
    print(f"  Old multi-source system: ~60+ seconds × {len(results)} = {60*len(results)}+ seconds")
    print(f"  Stub system (no verification): ~0.1 seconds total")
    print(f"  Fast verification system: ~{total_time:.1f} seconds total")
    print(f"  Speed improvement: ~{(60*len(results))/total_time:.0f}x faster than old system")
    
    # Quality assessment
    print(f"\n🎯 VERIFICATION QUALITY:")
    high_confidence = sum(1 for r in results if r['confidence'] >= 0.7)
    medium_confidence = sum(1 for r in results if 0.5 <= r['confidence'] < 0.7)
    
    print(f"  High confidence (≥0.7): {high_confidence} citations")
    print(f"  Medium confidence (0.5-0.7): {medium_confidence} citations")
    print(f"  Average confidence: {sum(r['confidence'] for r in results)/len(results):.2f}")
    
    # Assessment
    if verified_count == len(results) and avg_time < 1.0:
        print(f"\n🎉 EXCELLENT: All citations verified quickly with high quality!")
    elif verified_count >= len(results) * 0.8:
        print(f"\n✅ GOOD: Most citations verified with reasonable speed")
    else:
        print(f"\n⚠️ NEEDS IMPROVEMENT: Verification quality or speed needs work")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_d2_fast_verification())
