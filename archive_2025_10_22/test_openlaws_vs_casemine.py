"""
Test OpenLaws vs CaseMine for fallback verification
Compares effectiveness of both sources for finding citations
"""

import sys
sys.path.insert(0, '/app')

import asyncio
from src.unified_verification_master import UnifiedVerificationMaster

async def test_openlaws_and_casemine():
    print("\n" + "="*80)
    print("OPENLAWS vs CASEMINE COMPARISON TEST")
    print("="*80)
    
    test_citations = [
        {
            'citation': '17 F.4th 901',
            'expected_name': 'Acres Bonusing, Inc. v. Marston',
            'year': '2021',
            'type': 'Federal (recent)'
        },
        {
            'citation': '197 Wn.2d 868',
            'expected_name': 'In re Dependency of G.J.A.',
            'year': '2021',
            'type': 'Washington State'
        },
        {
            'citation': '31 Wn. App. 2d 343',
            'expected_name': 'Flying T Ranch, Inc. v. Stillaguamish Tribe',
            'year': '2024',
            'type': 'Washington State (very recent)'
        },
        {
            'citation': '388 P.3d 977',
            'expected_name': 'Hamaatsa, Inc. v. Pueblo of San Felipe',
            'year': '2016',
            'type': 'New Mexico'
        },
        {
            'citation': '548 P.3d 200',
            'expected_name': 'State v. Wallahee',
            'year': '2024',
            'type': 'Washington State (very recent)'
        },
        {
            'citation': '549 P.3d 727',
            'expected_name': 'Flying T Ranch, Inc. v. Stillaguamish Tribe',
            'year': '2024',
            'type': 'Washington State (parallel)'
        }
    ]
    
    verifier = UnifiedVerificationMaster()
    
    print(f"\n🔍 Testing {len(test_citations)} citations with fallback verification")
    print(f"⏱️  Timeout: 15 seconds per citation")
    print(f"✅ Fallback: ENABLED (CaseMine #1, OpenLaws #2)\n")
    
    results = {
        'casemine': 0,
        'openlaws': 0,
        'courtlistener': 0,
        'other': 0,
        'failed': 0
    }
    
    for i, test_case in enumerate(test_citations, 1):
        citation = test_case['citation']
        expected_name = test_case['expected_name']
        
        print(f"\n{'='*80}")
        print(f"Test {i}/{len(test_citations)}: {citation}")
        print(f"Expected: {expected_name}")
        print(f"Type: {test_case['type']}")
        print(f"{'='*80}")
        
        try:
            # Verify with fallback enabled
            result = await verifier.verify_citation(
                citation=citation,
                extracted_case_name=expected_name,
                timeout=30.0,
                enable_fallback=True
            )
            
            print(f"\n📊 Result:")
            print(f"  Verified: {result.verified}")
            print(f"  Source: {result.source if result.verified else 'N/A'}")
            print(f"  Canonical Name: {result.canonical_name if result.verified else 'N/A'}")
            print(f"  URL: {result.canonical_url if result.verified else 'N/A'}")
            
            if result.error:
                print(f"  ⚠️  Error: {result.error}")
            
            # Categorize by source
            if result.verified:
                source_lower = result.source.lower()
                if 'casemine' in source_lower:
                    results['casemine'] += 1
                    print(f"\n  ✅ VERIFIED via CASEMINE")
                elif 'openlaws' in source_lower:
                    results['openlaws'] += 1
                    print(f"\n  ✅ VERIFIED via OPENLAWS")
                elif 'courtlistener' in source_lower:
                    results['courtlistener'] += 1
                    print(f"\n  ✅ VERIFIED via COURTLISTENER")
                else:
                    results['other'] += 1
                    print(f"\n  ✅ VERIFIED via {result.source}")
            else:
                results['failed'] += 1
                print(f"\n  ❌ FAILED: Could not verify")
                
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            results['failed'] += 1
    
    # Print summary
    print("\n" + "="*80)
    print("COMPARISON SUMMARY")
    print("="*80)
    
    total_verified = results['casemine'] + results['openlaws'] + results['courtlistener'] + results['other']
    total_tested = len(test_citations)
    
    print(f"\n📊 Source Breakdown:")
    print(f"  🥇 CaseMine: {results['casemine']}/{total_tested} ({results['casemine']/total_tested*100:.1f}%)")
    print(f"  🥈 OpenLaws: {results['openlaws']}/{total_tested} ({results['openlaws']/total_tested*100:.1f}%)")
    print(f"  🥉 CourtListener: {results['courtlistener']}/{total_tested} ({results['courtlistener']/total_tested*100:.1f}%)")
    print(f"  📚 Other: {results['other']}/{total_tested} ({results['other']/total_tested*100:.1f}%)")
    print(f"  ❌ Failed: {results['failed']}/{total_tested} ({results['failed']/total_tested*100:.1f}%)")
    
    print(f"\n📈 Overall Statistics:")
    print(f"  Total Verified: {total_verified}/{total_tested} ({total_verified/total_tested*100:.1f}%)")
    print(f"  Success Rate: {total_verified/total_tested*100:.1f}%")
    
    # Determine which source is more effective
    if results['casemine'] > results['openlaws']:
        print(f"\n🏆 Winner: CaseMine (+{results['casemine'] - results['openlaws']} more verifications)")
    elif results['openlaws'] > results['casemine']:
        print(f"\n🏆 Winner: OpenLaws (+{results['openlaws'] - results['casemine']} more verifications)")
    else:
        print(f"\n🤝 Tie: Both sources equally effective")
    
    print("="*80)

if __name__ == '__main__':
    asyncio.run(test_openlaws_and_casemine())
