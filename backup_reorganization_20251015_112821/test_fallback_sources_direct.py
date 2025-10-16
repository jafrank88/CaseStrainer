#!/usr/bin/env python
"""Test fallback verification sources directly (bypass CourtListener)"""

import asyncio
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def test_fallback_sources():
    """Test fallback sources directly"""
    from src.unified_verification_master import UnifiedVerificationMaster
    
    verifier = UnifiedVerificationMaster()
    
    # Test citations (use well-known cases that should be in Justia/Google Scholar)
    test_cases = [
        {
            'citation': '384 U.S. 436',
            'case_name': 'Miranda v. Arizona',
            'date': '1966',
            'expected': 'Should be in Justia/Google Scholar'
        },
        {
            'citation': '347 U.S. 483',
            'case_name': 'Brown v. Board of Education',
            'date': '1954',
            'expected': 'Should be in Justia/Google Scholar'
        },
        {
            'citation': '410 U.S. 113',
            'case_name': 'Roe v. Wade',
            'date': '1973',
            'expected': 'Should be in Justia/Google Scholar'
        },
        {
            'citation': '163 U.S. 537',
            'case_name': 'Plessy v. Ferguson',
            'date': '1896',
            'expected': 'Should be in Justia/Google Scholar'
        }
    ]
    
    print("="*70)
    print("TESTING FALLBACK SOURCES DIRECTLY (bypassing CourtListener)")
    print("="*70)
    print("\nWe're testing Justia, Google Scholar, FindLaw, and Bing\n")
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        citation = test['citation']
        case_name = test['case_name']
        date = test['date']
        
        print(f"\n{'-'*70}")
        print(f"Test {i}/4: {citation} - {case_name}")
        print(f"{'-'*70}")
        
        try:
            # Call the enhanced fallback directly (skip CourtListener)
            result = await verifier._verify_with_enhanced_fallback(
                citation=citation,
                extracted_case_name=case_name,
                extracted_date=date,
                remaining_timeout=30.0
            )
            
            if result.verified:
                print(f"✅ VERIFIED via {result.source}")
                print(f"   Canonical: {result.canonical_name}")
                print(f"   Date: {result.canonical_date}")
                print(f"   URL: {result.canonical_url}")
                print(f"   Confidence: {result.confidence:.2f}")
                results.append({
                    'citation': citation,
                    'status': 'verified',
                    'source': result.source
                })
            else:
                print(f"❌ NOT VERIFIED")
                print(f"   Error: {result.error}")
                results.append({
                    'citation': citation,
                    'status': 'failed',
                    'error': result.error
                })
                
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            results.append({
                'citation': citation,
                'status': 'error',
                'error': str(e)
            })
    
    # Summary
    print("\n" + "="*70)
    print("FALLBACK SOURCE TEST SUMMARY")
    print("="*70)
    
    verified_count = sum(1 for r in results if r['status'] == 'verified')
    failed_count = sum(1 for r in results if r['status'] == 'failed')
    error_count = sum(1 for r in results if r['status'] == 'error')
    
    print(f"\n📊 Results:")
    print(f"   ✅ Verified: {verified_count}/{len(test_cases)}")
    print(f"   ❌ Failed: {failed_count}/{len(test_cases)}")
    print(f"   ⚠️  Errors: {error_count}/{len(test_cases)}")
    
    if verified_count > 0:
        print(f"\n✅ SUCCESS: Fallback sources are WORKING!")
        print(f"   {verified_count} citation(s) verified via fallback")
        
        # Show which sources worked
        sources = set(r.get('source') for r in results if r['status'] == 'verified')
        if sources:
            print(f"   Working sources: {', '.join(sources)}")
    else:
        print(f"\n⚠️  WARNING: No fallback verifications succeeded")
        print(f"   Possible reasons:")
        print(f"   - Fallback sites may also be rate limiting")
        print(f"   - Network/firewall issues")
        print(f"   - Search queries not matching correctly")
    
    print("\n" + "="*70)
    
    return results

if __name__ == '__main__':
    print("\n🔍 Testing Fallback Verification Sources\n")
    print("This test bypasses CourtListener and goes directly to:")
    print("  - Justia (law.justia.com)")
    print("  - Google Scholar (scholar.google.com)")
    print("  - FindLaw (findlaw.com)")
    print("  - Bing (bing.com)")
    print("\nUsing famous Supreme Court cases that should be widely available...\n")
    
    # Run the async test
    results = asyncio.run(test_fallback_sources())
    
    # Exit with appropriate code
    verified = sum(1 for r in results if r['status'] == 'verified')
    exit(0 if verified > 0 else 1)
