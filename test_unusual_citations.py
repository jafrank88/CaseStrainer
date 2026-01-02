"""
Test the unusual citations to understand what's happening
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from courtlistener_verification import CourtListenerVerifier
from enhanced_fallback_verifier import EnhancedFallbackVerifier

async def test_citation(citation, expected_name=None):
    """Test a single citation"""
    print(f"\n{'='*80}")
    print(f"Testing: {citation}")
    if expected_name:
        print(f"Expected: {expected_name}")
    print(f"{'='*80}")
    
    # Test CourtListener first
    print("\n1. Testing CourtListener...")
    cl_verifier = CourtListenerVerifier()
    cl_result = await cl_verifier.verify_with_courtlistener(citation)
    
    if cl_result and cl_result.verified:
        print(f"   ✅ CourtListener FOUND")
        print(f"   Canonical Name: {cl_result.canonical_name}")
        print(f"   Canonical Date: {cl_result.canonical_date}")
        print(f"   URL: {cl_result.canonical_url}")
        print(f"   Source: {cl_result.source}")
    else:
        print(f"   ❌ CourtListener NOT FOUND")
        if cl_result and cl_result.error:
            print(f"   Error: {cl_result.error}")
    
    # Test fallback verification
    print("\n2. Testing Fallback Verification...")
    fallback = EnhancedFallbackVerifier()
    fallback_result = await fallback.verify_citation(citation, extracted_case_name=expected_name)
    
    if fallback_result and fallback_result.verified:
        print(f"   ✅ Fallback FOUND")
        print(f"   Canonical Name: {fallback_result.canonical_name}")
        print(f"   Canonical Date: {fallback_result.canonical_date}")
        print(f"   URL: {fallback_result.canonical_url}")
        print(f"   Source: {fallback_result.source}")
    else:
        print(f"   ❌ Fallback NOT FOUND")
        if fallback_result and fallback_result.error:
            print(f"   Error: {fallback_result.error}")
    
    return cl_result, fallback_result

async def main():
    print("="*80)
    print("TESTING UNUSUAL CITATIONS")
    print("="*80)
    
    # Test Case 1: 636 F.2d 1267 - Should be Env't Def Fund, NOT Erickson
    await test_citation(
        "636 F.2d 1267",
        expected_name="Environmental Defense Fund, Inc. v. Environmental Protection Agency"
    )
    
    # Test Case 2: 498 U.S. 941 - Should find Christine Mahne case
    await test_citation(
        "498 U.S. 941",
        expected_name="Christine Mahne v. Ford Motor Company Donald Petersen and Harold MacDonald"
    )
    
    # Test Case 3: Singh citations
    print(f"\n{'='*80}")
    print("Testing Singh Citations (should be parallel)")
    print(f"{'='*80}")
    
    await test_citation(
        "151 Wn. App. 137",
        expected_name="Singh v. Edwards Lifesciences Corp."
    )
    
    await test_citation(
        "210 P.3d 337",
        expected_name="Singh v. Edwards Lifesciences Corp."
    )
    
    await test_citation(
        "2011 WL 3298912",
        expected_name="Singh v. Edwards Lifesciences Corp."
    )
    
    # Test Case 4: Recent 2024 citations
    await test_citation(
        "548 P.3d 226",
        expected_name="Erickson v. Pharmacia LLC"
    )
    
    await test_citation(
        "3 Wn.3d 1018",
        expected_name="Erickson v. Pharmacia LLC"
    )
    
    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(main())
