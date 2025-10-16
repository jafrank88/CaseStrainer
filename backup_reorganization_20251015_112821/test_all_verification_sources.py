#!/usr/bin/env python
"""Test all verification sources including new OpenJurist"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)

async def test_all_sources():
    """Test CourtListener, Justia, and OpenJurist"""
    from src.unified_verification_master import UnifiedVerificationMaster
    
    verifier = UnifiedVerificationMaster()
    
    test_cases = [
        ("384 U.S. 436", "Miranda v. Arizona"),
        ("347 U.S. 483", "Brown v. Board of Education"),
        ("163 F.3d 952", "United States v. McFerron"),
    ]
    
    print("="*70)
    print("COMPREHENSIVE VERIFICATION SOURCE TEST")
    print("="*70)
    print("\nTesting: CourtListener, Justia, and OpenJurist\n")
    
    results = {
        'courtlistener': [],
        'justia': [],
        'openjurist': []
    }
    
    for citation, case_name in test_cases:
        print(f"\n{'='*70}")
        print(f"Testing: {citation} - {case_name}")
        print('='*70)
        
        # Test Justia
        print("\n1️⃣ Justia Direct URL:")
        justia_result = await verifier._verify_with_justia(citation, case_name, None, 10.0)
        if justia_result.verified:
            print(f"   ✅ VERIFIED: {justia_result.canonical_name}")
            results['justia'].append(citation)
        else:
            print(f"   ❌ Failed: {justia_result.error}")
        
        # Test OpenJurist
        print("\n2️⃣ OpenJurist Direct URL:")
        openjurist_result = await verifier._verify_with_openjurist(citation, case_name, None, 10.0)
        if openjurist_result.verified:
            print(f"   ✅ VERIFIED: {openjurist_result.canonical_name}")
            results['openjurist'].append(citation)
        else:
            print(f"   ❌ Failed: {openjurist_result.error}")
        
        # Test CourtListener (via full verification which tries it first)
        print("\n3️⃣ CourtListener API:")
        full_result = await verifier.verify_citation(citation, case_name, None, 10.0, enable_fallback=False)
        if full_result.verified and full_result.source in ['courtlistener_lookup', 'courtlistener_search']:
            print(f"   ✅ VERIFIED: {full_result.canonical_name}")
            results['courtlistener'].append(citation)
        else:
            print(f"   ❌ Not found in CourtListener")
    
    # Summary
    print("\n" + "="*70)
    print("VERIFICATION SOURCE SUMMARY")
    print("="*70)
    
    print(f"\n✅ CourtListener: {len(results['courtlistener'])}/{len(test_cases)}")
    print(f"✅ Justia: {len(results['justia'])}/{len(test_cases)}")
    print(f"✅ OpenJurist: {len(results['openjurist'])}/{len(test_cases)}")
    
    total_working = len([s for s in results.values() if len(s) > 0])
    
    print(f"\n📊 Total working sources: {total_working}/3")
    
    if total_working >= 2:
        print("\n✅ SUCCESS: Multiple verification sources working!")
        print("   Your system has redundancy and comprehensive coverage.")
    elif total_working == 1:
        print("\n⚠️  WARNING: Only one source working")
    else:
        print("\n❌ FAILURE: No sources working")
    
    print("\n" + "="*70)
    print("FALLBACK CHAIN")
    print("="*70)
    print("""
Your verification will try sources in this order:
1. CourtListener API (comprehensive, current)
2. Justia Direct URL (federal cases, no anti-bot)
3. OpenJurist Direct URL (federal cases, alternative)
4. Other sources (mostly blocked by anti-bot)

This gives you excellent coverage for federal cases!
""")

if __name__ == '__main__':
    print("\n🔍 Testing All Verification Sources\n")
    asyncio.run(test_all_sources())
