"""
Test fallback verification for "In re" cases
Tests that fallback verification can find cases that CourtListener doesn't have
"""

import sys
sys.path.insert(0, '/app')

import asyncio
from src.unified_verification_master import UnifiedVerificationMaster

async def test_in_re_fallback():
    print("\n" + "="*80)
    print("FALLBACK VERIFICATION TEST: In re Cases")
    print("="*80)
    
    # Test case from user's question
    test_cases = [
        {
            'citation': '199 Wn.2d 1',
            'expected_name': 'In re Dependency of G.J.A.',
            'year': '2021'
        },
        # Additional "In re" test cases
        {
            'citation': '183 Wn.2d 649',
            'expected_name': None,  # Unknown case
            'year': None
        }
    ]
    
    verifier = UnifiedVerificationMaster()
    
    print(f"\n🔍 Testing {len(test_cases)} citations with fallback enabled...")
    print(f"⏱️  Timeout: 10 seconds per citation")
    print(f"✅ Fallback: ENABLED\n")
    
    for i, test_case in enumerate(test_cases, 1):
        citation = test_case['citation']
        expected_name = test_case['expected_name']
        
        print(f"\n{'='*80}")
        print(f"Test {i}: {citation}")
        print(f"Expected: {expected_name or 'Unknown'}")
        print(f"{'='*80}")
        
        try:
            # Verify with fallback enabled
            result = await verifier.verify_citation(
                citation=citation,
                extracted_case_name=expected_name,
                timeout=30.0,
                enable_fallback=True  # CRITICAL: Enable fallback
            )
            
            print(f"\n📊 Result:")
            print(f"  Verified: {result.verified}")
            print(f"  Source: {result.source if result.verified else 'N/A'}")
            print(f"  Canonical Name: {result.canonical_name if result.verified else 'N/A'}")
            print(f"  URL: {result.canonical_url if result.verified else 'N/A'}")
            
            if result.error:
                print(f"  ⚠️  Error: {result.error}")
            
            # Check if it matches expected
            if expected_name:
                if result.verified and expected_name.lower() in (result.canonical_name or '').lower():
                    print(f"\n  ✅ PASS: Found expected case '{expected_name}'")
                else:
                    print(f"\n  ❌ FAIL: Did not find expected case")
            else:
                status = "✅ VERIFIED" if result.verified else "⚠️  UNVERIFIED"
                print(f"\n  {status}: No expected name to compare")
                
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)

if __name__ == '__main__':
    asyncio.run(test_in_re_fallback())
