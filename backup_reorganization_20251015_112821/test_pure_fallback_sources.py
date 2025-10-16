#!/usr/bin/env python
"""Test ONLY fallback sources (Justia, Google Scholar, etc.) by skipping CourtListener"""

import asyncio
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def test_pure_fallback_sources():
    """Test pure fallback sources (skip CourtListener)"""
    from src.unified_verification_master import UnifiedVerificationMaster
    
    verifier = UnifiedVerificationMaster()
    
    # Test citations
    test_cases = [
        {
            'citation': '384 U.S. 436',
            'case_name': 'Miranda v. Arizona',
            'date': '1966'
        },
        {
            'citation': '347 U.S. 483',
            'case_name': 'Brown v. Board of Education',
            'date': '1954'
        },
        {
            'citation': '410 U.S. 113',
            'case_name': 'Roe v. Wade',
            'date': '1973'
        }
    ]
    
    print("="*70)
    print("TESTING PURE FALLBACK SOURCES (Justia, Google Scholar, etc.)")
    print("="*70)
    print("\nSkipping CourtListener to test alternative sources...\n")
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        citation = test['citation']
        case_name = test['case_name']
        date = test['date']
        
        print(f"\n{'-'*70}")
        print(f"Test {i}/{len(test_cases)}: {citation} - {case_name}")
        print(f"{'-'*70}")
        
        try:
            # Test each fallback source individually
            print("\n🔍 Testing Justia...")
            justia_result = await verifier._verify_with_justia(
                citation=citation,
                extracted_case_name=case_name,
                extracted_date=date,
                timeout=10.0
            )
            
            if justia_result.verified:
                print(f"   ✅ VERIFIED via Justia")
                print(f"      Name: {justia_result.canonical_name}")
                print(f"      URL: {justia_result.canonical_url}")
                results.append({'citation': citation, 'source': 'Justia', 'verified': True})
            else:
                print(f"   ❌ Not verified: {justia_result.error}")
                
            print("\n🔍 Testing Google Scholar...")
            scholar_result = await verifier._verify_with_google_scholar(
                citation=citation,
                extracted_case_name=case_name,
                extracted_date=date,
                timeout=10.0
            )
            
            if scholar_result.verified:
                print(f"   ✅ VERIFIED via Google Scholar")
                print(f"      Name: {scholar_result.canonical_name}")
                print(f"      URL: {scholar_result.canonical_url}")
                results.append({'citation': citation, 'source': 'Google Scholar', 'verified': True})
            else:
                print(f"   ❌ Not verified: {scholar_result.error}")
            
            print("\n🔍 Testing FindLaw...")
            findlaw_result = await verifier._verify_with_findlaw(
                citation=citation,
                extracted_case_name=case_name,
                extracted_date=date,
                timeout=10.0
            )
            
            if findlaw_result.verified:
                print(f"   ✅ VERIFIED via FindLaw")
                print(f"      Name: {findlaw_result.canonical_name}")
                print(f"      URL: {findlaw_result.canonical_url}")
                results.append({'citation': citation, 'source': 'FindLaw', 'verified': True})
            else:
                print(f"   ❌ Not verified: {findlaw_result.error}")
                
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*70)
    print("PURE FALLBACK SOURCE TEST SUMMARY")
    print("="*70)
    
    verified_count = len(results)
    
    print(f"\n📊 Total verifications: {verified_count}")
    
    if verified_count > 0:
        print(f"\n✅ SUCCESS: Pure fallback sources are WORKING!")
        
        # Group by source
        by_source = {}
        for r in results:
            source = r['source']
            by_source[source] = by_source.get(source, 0) + 1
        
        print(f"\nVerifications by source:")
        for source, count in by_source.items():
            print(f"   {source}: {count}")
    else:
        print(f"\n⚠️  WARNING: No pure fallback verifications succeeded")
        print(f"   Possible reasons:")
        print(f"   - Fallback sites may be rate limiting")
        print(f"   - Search queries not matching correctly")
        print(f"   - Case names too specific/generic")
    
    print("\n" + "="*70)
    
    return results

if __name__ == '__main__':
    print("\n🔍 Testing Pure Fallback Verification Sources\n")
    print("This test skips CourtListener and directly tests:")
    print("  - Justia (law.justia.com)")
    print("  - Google Scholar (scholar.google.com)")
    print("  - FindLaw (findlaw.com)")
    print("\nTesting with famous Supreme Court cases...\n")
    
    # Run the async test
    results = asyncio.run(test_pure_fallback_sources())
    
    # Exit with appropriate code
    exit(0 if len(results) > 0 else 1)
