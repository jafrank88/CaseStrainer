#!/usr/bin/env python3
"""
Test the enhanced batch fallback verification
"""

import asyncio
from src.unified_verification_master import UnifiedVerificationMaster

async def test_enhanced_fallback():
    """Test the enhanced batch fallback with more unverified citations"""
    
    print("=" * 80)
    print("TESTING ENHANCED BATCH FALLBACK VERIFICATION")
    print("=" * 80)
    print()
    
    verifier = UnifiedVerificationMaster()
    
    # Test citations - mix of verifiable and unverified
    test_citations = [
        # These should be verified by CourtListener
        "523 U.S. 751",
        "789 F.3d 123",
        "146 S. Ct. 1540",
        
        # These might need fallback (older or state citations)
        "123 N.E.2d 456",
        "456 N.W.2d 789",
        "789 S.E.2d 123",
        "234 Cal. 567",
        "345 N.Y. 890",
        "456 Tex. 234",
        
        # Federal citations that might need Law Resource.org
        "123 F.2d 456",
        "456 F.3d 789",
        "789 F.4th 123",
        
        # More citations to test the limit
        "234 F.2d 567",
        "345 F.3d 890",
        "456 F.4th 234",
    ]
    
    print(f"Testing {len(test_citations)} citations with enhanced fallback...")
    print()
    
    # Test with different fallback limits
    for max_fallback in [5, 10, 50]:
        print(f"\n{'-'*60}")
        print(f"TEST WITH max_fallback_citations = {max_fallback}")
        print(f"{'-'*60}")
        
        results = await verifier.verify_citations_batch(
            citations=test_citations,
            enable_fallback=True,
            max_fallback_citations=max_fallback
        )
        
        verified = sum(1 for r in results if r.verified)
        unverified = len(results) - verified
        
        print(f"\nResults: {verified}/{len(results)} verified ({verified/len(results)*100:.1f}%)")
        print(f"Unverified: {unverified}")
        
        # Show sources
        sources = {}
        for r in results:
            if r.verified and r.source:
                sources[r.source] = sources.get(r.source, 0) + 1
        
        print("\nVerification sources:")
        for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
            print(f"  {source}: {count}")
    
    print("\n" + "="*80)
    print("ENHANCED FALLBACK TEST COMPLETE")
    print("="*80)
    print("\nKey improvements:")
    print("1. Can handle up to 50 unverified citations (configurable)")
    print("2. Prioritizes citations with case names (higher success rate)")
    print("3. Uses parallel processing with semaphore (max 5 concurrent)")
    print("4. Tries multiple sources in order of likelihood:")
    print("   - CaseMine (best for recent cases)")
    print("   - VLex (if case name available)")
    print("   - Justia (direct URL)")
    print("   - Law Resource.org (for Federal citations)")

if __name__ == "__main__":
    asyncio.run(test_enhanced_fallback())
