#!/usr/bin/env python3
"""
Test which fallback verification sources actually work
"""
import asyncio
import time
import sys
import os

# Add src to path
sys.path.insert(0, '/app')

from src.enhanced_fallback_verifier import EnhancedFallbackVerifier

# Test citation: known case that should be verifiable
TEST_CITATIONS = [
    {
        'citation': '198 Cal.App.3d 449',
        'case_name': 'Carman v. Adventure Bound',
        'date': '1986'
    },
    {
        'citation': '410 U.S. 113',
        'case_name': 'Roe v. Wade',
        'date': '1973'
    }
]

async def test_source(verifier, source_name, method, citation_text, case_name, date):
    """Test a single source"""
    print(f"\n{'='*60}")
    print(f"Testing: {source_name}")
    print(f"Citation: {citation_text}")
    print(f"{'='*60}")
    
    start = time.time()
    timeout = 5.0  # 5 second timeout per source
    
    try:
        # Call the method with timeout
        result = await asyncio.wait_for(
            method(citation_text, {}, case_name, date, timeout),
            timeout=timeout
        )
        elapsed = time.time() - start
        
        if result and result.get('verified'):
            print(f"✅ SUCCESS ({elapsed:.2f}s)")
            print(f"   Canonical Name: {result.get('canonical_name')}")
            print(f"   Canonical Date: {result.get('canonical_date')}")
            print(f"   URL: {result.get('canonical_url', result.get('url'))}")
            return {'source': source_name, 'status': 'working', 'time': elapsed}
        else:
            print(f"⚠️  FAILED: No verification ({elapsed:.2f}s)")
            print(f"   Error: {result.get('error') if result else 'No result'}")
            return {'source': source_name, 'status': 'no_results', 'time': elapsed}
            
    except asyncio.TimeoutError:
        print(f"⏱️  TIMEOUT after {timeout}s")
        return {'source': source_name, 'status': 'timeout', 'time': timeout}
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ ERROR ({elapsed:.2f}s): {str(e)[:100]}")
        return {'source': source_name, 'status': 'error', 'time': elapsed, 'error': str(e)}


async def test_all_sources():
    """Test all fallback sources"""
    verifier = EnhancedFallbackVerifier()
    
    # List of sources to test
    sources = [
        ('vLex', verifier._verify_with_vlex),
        ('CaseMine', verifier._verify_with_casemine),
        ('Leagle', verifier._verify_with_leagle),
        ('Justia', verifier._verify_with_justia),
        ('DuckDuckGo', verifier._verify_with_duckduckgo),
        ('FindLaw', verifier._verify_with_findlaw),
        ('Google Scholar', verifier._verify_with_google_scholar),
        # Note: Bing is sync only, skip for now
    ]
    
    results = []
    
    for citation_info in TEST_CITATIONS:
        citation = citation_info['citation']
        case_name = citation_info['case_name']
        date = citation_info['date']
        
        print(f"\n{'#'*60}")
        print(f"# Testing Citation: {citation}")
        print(f"# Expected: {case_name} ({date})")
        print(f"{'#'*60}")
        
        for source_name, method in sources:
            result = await test_source(verifier, source_name, method, citation, case_name, date)
            results.append({
                'citation': citation,
                **result
            })
            
            # Small delay between sources
            await asyncio.sleep(0.5)
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    working_sources = [r for r in results if r['status'] == 'working']
    timeout_sources = [r for r in results if r['status'] == 'timeout']
    error_sources = [r for r in results if r['status'] == 'error']
    no_result_sources = [r for r in results if r['status'] == 'no_results']
    
    print(f"\n✅ WORKING SOURCES ({len(working_sources)}):")
    for r in working_sources:
        print(f"   • {r['source']} - {r['time']:.2f}s")
    
    print(f"\n⚠️  NO RESULTS ({len(no_result_sources)}):")
    for r in no_result_sources:
        print(f"   • {r['source']} - {r['time']:.2f}s")
    
    print(f"\n⏱️  TIMEOUT ({len(timeout_sources)}):")
    for r in timeout_sources:
        print(f"   • {r['source']}")
    
    print(f"\n❌ ERRORS ({len(error_sources)}):")
    for r in error_sources:
        print(f"   • {r['source']}: {r.get('error', 'Unknown')[:50]}")
    
    # Recommendations
    print(f"\n{'='*60}")
    print("RECOMMENDATIONS")
    print(f"{'='*60}")
    
    if working_sources:
        print("✅ Enable these sources:")
        for r in working_sources:
            print(f"   • {r['source']}")
    else:
        print("❌ NO WORKING SOURCES FOUND")
    
    print("\n⚠️  Consider disabling:")
    for r in timeout_sources + error_sources:
        print(f"   • {r['source']}")
    
    return results


if __name__ == '__main__':
    print("="*60)
    print("FALLBACK SOURCE TESTING")
    print("="*60)
    print("\nTesting which fallback verification sources actually work...")
    print("This will test each source with 5-second timeout\n")
    
    asyncio.run(test_all_sources())
