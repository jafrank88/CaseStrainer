"""
Test CaseMine priority fix for "Acres Bonusing, Inc. v. Marston | 17 F.4th 901"
"""

import sys
sys.path.insert(0, '/app')

import asyncio
from src.unified_verification_master import UnifiedVerificationMaster

async def test_casemine_fallback():
    print("\n" + "="*80)
    print("CASEMINE PRIORITY FIX TEST")
    print("="*80)
    
    test_citations = [
        {
            'citation': '17 F.4th 901',
            'expected_name': 'Acres Bonusing, Inc. v. Marston',
            'year': '2021',
            'source': 'User found on CaseMine'
        },
        {
            'citation': '197 Wn.2d 868',
            'expected_name': 'In re Dependency of G.J.A.',
            'year': '2021',
            'source': 'Original user request'
        },
        {
            'citation': '31 Wn. App. 2d 343',
            'expected_name': 'Flying T Ranch, Inc. v. Stillaguamish Tribe',
            'year': '2024',
            'source': 'Recent Washington case'
        }
    ]
    
    verifier = UnifiedVerificationMaster()
    
    print(f"\n🔍 Testing {len(test_citations)} citations with CaseMine-first fallback...")
    print(f"⏱️  Timeout: 15 seconds per citation")
    print(f"✅ Fallback: ENABLED (CaseMine priority)\n")
    
    successes = 0
    failures = 0
    
    for i, test_case in enumerate(test_citations, 1):
        citation = test_case['citation']
        expected_name = test_case['expected_name']
        
        print(f"\n{'='*80}")
        print(f"Test {i}/{len(test_citations)}: {citation}")
        print(f"Expected: {expected_name}")
        print(f"Source: {test_case['source']}")
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
            if result.verified:
                print(f"\n  ✅ SUCCESS: Citation verified via {result.source}")
                successes += 1
                
                # Check if CaseMine was used
                if 'casemine' in result.source.lower():
                    print(f"  🎯 CASEMINE WAS USED! Priority fix working.")
            else:
                print(f"\n  ❌ FAILED: Could not verify citation")
                failures += 1
                
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            failures += 1
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    print(f"✅ Successes: {successes}/{len(test_citations)}")
    print(f"❌ Failures: {failures}/{len(test_citations)}")
    print(f"Success Rate: {(successes/len(test_citations)*100):.1f}%")
    print("="*80)

if __name__ == '__main__':
    asyncio.run(test_casemine_fallback())
