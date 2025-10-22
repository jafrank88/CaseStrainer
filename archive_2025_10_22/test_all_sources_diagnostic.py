"""
Diagnostic test for all fallback sources (except CaseMine)
Checks if each source is properly configured and finding results
"""

import sys
sys.path.insert(0, '/app')

import time
from src.enhanced_fallback_verifier import EnhancedFallbackVerifier

def test_source(source_name, method_name, test_citation, extracted_name):
    """Test a single source and report findings."""
    print(f"\n{'='*80}")
    print(f"Testing: {source_name}")
    print(f"{'='*80}")
    print(f"Citation: {test_citation}")
    print(f"Expected: {extracted_name}")
    
    verifier = EnhancedFallbackVerifier()
    
    if not hasattr(verifier, method_name):
        print(f"❌ Method {method_name} not found")
        return None
    
    verify_method = getattr(verifier, method_name)
    
    try:
        start_time = time.time()
        result = verify_method(
            citation_text=test_citation,
            citation_info={},
            extracted_case_name=extracted_name,
            extracted_date=None,
            search_query=None
        )
        elapsed_time = time.time() - start_time
        
        print(f"\n⏱️  Time: {elapsed_time:.2f}s")
        
        if result and result.get('verified'):
            print(f"✅ SUCCESS!")
            print(f"   Found: {result.get('canonical_name', 'N/A')[:60]}")
            print(f"   URL: {result.get('url', 'N/A')[:80]}")
            print(f"   Source: {result.get('source', 'N/A')}")
            print(f"   Confidence: {result.get('confidence', 0)}")
            return {'status': 'success', 'time': elapsed_time, 'result': result}
        else:
            print(f"❌ MISS - No verification found")
            return {'status': 'miss', 'time': elapsed_time}
            
    except Exception as e:
        print(f"⚠️  ERROR: {type(e).__name__}: {str(e)[:100]}")
        import traceback
        traceback.print_exc()
        return {'status': 'error', 'time': 0, 'error': str(e)}

def main():
    print("\n" + "="*80)
    print("COMPREHENSIVE FALLBACK SOURCE DIAGNOSTIC")
    print("="*80)
    
    # Test cases - mix of older and newer
    test_cases = [
        {
            'citation': '436 U.S. 49',
            'name': 'Santa Clara Pueblo v. Martinez',
            'year': '1978',
            'type': 'Older federal (should work)'
        },
        {
            'citation': '523 U.S. 751',
            'name': 'Kiowa Tribe of Oklahoma v. Manufacturing Technologies',
            'year': '1998',
            'type': 'Federal'
        },
        {
            'citation': '17 F.4th 901',
            'name': 'Acres Bonusing, Inc. v. Marston',
            'year': '2021',
            'type': 'Recent federal (CaseMine only?)'
        }
    ]
    
    # Sources to test (excluding CaseMine - we know it works)
    sources = [
        ('Leagle', '_verify_with_leagle_sync'),
        ('CourtListener Lookup', '_verify_with_courtlistener_lookup_sync'),
        ('CourtListener Search', '_verify_with_courtlistener_search_sync'),
        ('Justia', '_verify_with_justia_sync'),
        ('OpenLaws', '_verify_with_openlaws_sync'),
    ]
    
    # Results tracking
    results_by_source = {s[0]: {'hits': 0, 'misses': 0, 'errors': 0, 'total_time': 0} for s in sources}
    
    print(f"\n📊 Testing {len(sources)} sources with {len(test_cases)} citations")
    
    for test_case in test_cases:
        print(f"\n{'#'*80}")
        print(f"TEST CASE: {test_case['citation']} - {test_case['type']}")
        print(f"Expected: {test_case['name']}")
        print(f"{'#'*80}")
        
        for source_name, method_name in sources:
            result = test_source(source_name, method_name, test_case['citation'], test_case['name'])
            
            if result:
                if result['status'] == 'success':
                    results_by_source[source_name]['hits'] += 1
                    results_by_source[source_name]['total_time'] += result['time']
                elif result['status'] == 'miss':
                    results_by_source[source_name]['misses'] += 1
                    results_by_source[source_name]['total_time'] += result['time']
                elif result['status'] == 'error':
                    results_by_source[source_name]['errors'] += 1
    
    # Print summary
    print("\n" + "="*80)
    print("DIAGNOSTIC SUMMARY")
    print("="*80)
    
    print(f"\n{'Source':<30} {'Hits':<8} {'Misses':<8} {'Errors':<8} {'Avg Time':<10}")
    print("-" * 80)
    
    for source_name, method_name in sources:
        data = results_by_source[source_name]
        total = data['hits'] + data['misses'] + data['errors']
        avg_time = (data['total_time'] / total) if total > 0 else 0
        print(f"{source_name:<30} {data['hits']:<8} {data['misses']:<8} {data['errors']:<8} {avg_time:<10.2f}s")
    
    # Analysis
    print("\n" + "="*80)
    print("CONFIGURATION ANALYSIS")
    print("="*80)
    
    for source_name, method_name in sources:
        data = results_by_source[source_name]
        total = data['hits'] + data['misses'] + data['errors']
        
        if total == 0:
            continue
        
        hit_rate = (data['hits'] / total * 100) if total > 0 else 0
        
        print(f"\n{source_name}:")
        
        if data['errors'] > 0:
            print(f"  ⚠️  {data['errors']} errors - May be misconfigured or have API issues")
        
        if hit_rate == 0 and data['errors'] == 0:
            print(f"  ⚠️  0% hit rate but no errors - Configuration may be okay, just not finding recent cases")
            print(f"     Recommendation: Test with older citations (pre-2020)")
        
        if hit_rate > 0:
            print(f"  ✅ Working! {hit_rate:.0f}% hit rate")
            if hit_rate < 50:
                print(f"     Recommendation: Could be optimized for better coverage")
        
        if data['hits'] > 0 and data['misses'] > 0:
            print(f"  🔍 Partial success - Works for some citations but not others")
            print(f"     Recommendation: Check which types of citations work (federal vs state, old vs new)")
    
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    
    working_sources = [s for s in sources if results_by_source[s[0]]['hits'] > 0]
    broken_sources = [s for s in sources if results_by_source[s[0]]['errors'] > 0]
    zero_hit_sources = [s for s in sources if results_by_source[s[0]]['hits'] == 0 and results_by_source[s[0]]['errors'] == 0]
    
    if working_sources:
        print(f"\n✅ Working Sources ({len(working_sources)}):")
        for s in working_sources:
            print(f"   - {s[0]}")
    
    if broken_sources:
        print(f"\n⚠️  Sources with Errors ({len(broken_sources)}):")
        for s in broken_sources:
            print(f"   - {s[0]} - Needs configuration review")
    
    if zero_hit_sources:
        print(f"\n📊 Zero Hits (May be okay for older cases) ({len(zero_hit_sources)}):")
        for s in zero_hit_sources:
            print(f"   - {s[0]} - Test with pre-2020 citations")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    main()
