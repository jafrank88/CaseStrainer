#!/usr/bin/env python3
"""
Test real citation verification with CourtListener API
"""

import sys
import os
import asyncio

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_real_citation_verification():
    """Test verification with real citations"""
    print("REAL CITATION VERIFICATION TEST")
    print("=" * 50)
    
    try:
        from src.unified_verification_master import UnifiedVerificationMaster
        
        # Test with some real citations from the user's data
        test_citations = [
            "463 U.S. 29",  # Supreme Court case - should be verifiable
            "548 P.3d 1086",  # Alaska case - might be verifiable
            "390 U.S. 747",  # This should be "In re Permian Basin Area Rate Cases"
        ]
        
        test_case_names = [
            "Motor Vehicle Mfrs. Ass'n of U.S., Inc. v. State Farm Mut. Auto Ins. Co.",
            "Fischer v. Kenai Peninsula Borough Sch. Dist.",
            "In re Permian Basin Area Rate Cases",
        ]
        
        test_dates = ["1983", "2024", "1968"]
        
        print(f"Testing {len(test_citations)} real citations...")
        
        verifier = UnifiedVerificationMaster()
        print(f"API Key configured: {bool(verifier.api_key)}")
        
        # Test batch verification
        results = await verifier.verify_citations_batch(
            citations=test_citations,
            extracted_case_names=test_case_names,
            extracted_dates=test_dates
        )
        
        print(f"\nRESULTS:")
        print("-" * 50)
        
        for i, result in enumerate(results):
            citation = test_citations[i]
            print(f"\n{i+1}. {citation}")
            print(f"   Verified: {result.verified}")
            print(f"   Canonical Name: {result.canonical_name}")
            print(f"   Canonical Date: {result.canonical_date}")
            print(f"   Source: {result.source}")
            print(f"   URL: {result.canonical_url}")
            if result.error:
                print(f"   Error: {result.error}")
        
        # Check success rate
        verified_count = sum(1 for r in results if r.verified)
        print(f"\nSUMMARY:")
        print(f"Verified: {verified_count}/{len(results)} ({verified_count/len(results)*100:.1f}%)")
        
        # Test the specific Permian Basin case
        permian_result = None
        for i, citation in enumerate(test_citations):
            if "390 U.S. 747" in citation:
                permian_result = results[i]
                break
        
        if permian_result:
            print(f"\nPERMIAN BASIN TEST:")
            print(f"Citation: 390 U.S. 747")
            print(f"Verified: {permian_result.verified}")
            print(f"Canonical Name: {permian_result.canonical_name}")
            print(f"Expected: In re Permian Basin Area Rate Cases")
            
            if permian_result.verified and "Permian Basin" in permian_result.canonical_name:
                print("✅ PERMIAN BASIN VERIFICATION SUCCESS!")
            elif permian_result.verified:
                print("⚠️  PERMIAN BASIN VERIFIED BUT WITH DIFFERENT NAME")
            else:
                print("❌ PERMIAN BASIN NOT VERIFIED")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_real_citation_verification())
    
    print(f"\n{'='*50}")
    if success:
        print("🎉 VERIFICATION TEST COMPLETED")
    else:
        print("❌ VERIFICATION TEST FAILED")
    print("=" * 50)
