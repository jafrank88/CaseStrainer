"""
Benchmark all fallback sources (except CaseMine) to determine optimal ordering
Tests response speed and hit rate for each source
"""

import sys
sys.path.insert(0, '/app')

import time
from src.enhanced_fallback_verifier import EnhancedFallbackVerifier

def test_all_sources():
    print("\n" + "="*80)
    print("FALLBACK SOURCE BENCHMARK TEST")
    print("Testing all sources to determine optimal ordering")
    print("="*80)
    
    # Test citations covering different types
    test_citations = [
        {
            'citation': '17 F.4th 901',
            'name': 'Acres Bonusing, Inc. v. Marston',
            'type': 'Federal Recent (2021)'
        },
        {
            'citation': '197 Wn.2d 868',
            'name': 'In re Dependency of G.J.A.',
            'type': 'State Recent (2021)'
        },
        {
            'citation': '523 U.S. 751',
            'name': 'Kiowa Tribe of Oklahoma v. Manufacturing Technologies',
            'type': 'Federal Older (1998)'
        },
        {
            'citation': '436 U.S. 49',
            'name': 'Santa Clara Pueblo v. Martinez',
            'type': 'Federal Classic (1978)'
        },
        {
            'citation': '388 P.3d 977',
            'name': 'Hamaatsa, Inc. v. Pueblo of San Felipe',
            'type': 'State Reporter (2016)'
        },
        {
            'citation': '548 P.3d 200',
            'name': 'State v. Wallahee',
            'type': 'State Recent (2024)'
        }
    ]
    
    # Sources to test (excluding CaseMine which is #1)
    sources = [
        ('openlaws', 'OpenLaws'),
        ('courtlistener_lookup', 'CourtListener Lookup'),
        ('courtlistener_search', 'CourtListener Search'),
        ('leagle', 'Leagle'),
        ('justia', 'Justia'),
        ('bing', 'Bing'),
        ('duckduckgo', 'DuckDuckGo'),
        ('findlaw', 'FindLaw')
    ]
    
    verifier = EnhancedFallbackVerifier()
    
    # Results storage
    results = {source[0]: {'hits': 0, 'misses': 0, 'errors': 0, 'total_time': 0.0, 'avg_time': 0.0} for source in sources}
    
    print(f"\n🧪 Testing {len(test_citations)} citations across {len(sources)} sources")
    print(f"⏱️  Measuring speed and hit rate for each source\n")
    
    # Test each source with each citation
    for source_key, source_name in sources:
        print(f"\n{'='*80}")
        print(f"Testing: {source_name}")
        print(f"{'='*80}")
        
        method_name = f"_verify_with_{source_key}_sync"
        if not hasattr(verifier, method_name):
            print(f"  ⚠️  Method {method_name} not found, skipping")
            continue
        
        verify_method = getattr(verifier, method_name)
        
        for i, test_case in enumerate(test_citations, 1):
            citation = test_case['citation']
            case_name = test_case['name']
            case_type = test_case['type']
            
            print(f"\n  [{i}/{len(test_citations)}] {citation} - {case_type}")
            
            try:
                start_time = time.time()
                result = verify_method(
                    citation_text=citation,
                    citation_info={},
                    extracted_case_name=case_name,
                    extracted_date=None,
                    search_query=None
                )
                elapsed_time = time.time() - start_time
                
                if result and result.get('verified'):
                    results[source_key]['hits'] += 1
                    results[source_key]['total_time'] += elapsed_time
                    print(f"    ✅ HIT ({elapsed_time:.2f}s) - {result.get('canonical_name', 'N/A')[:50]}")
                else:
                    results[source_key]['misses'] += 1
                    results[source_key]['total_time'] += elapsed_time
                    print(f"    ❌ MISS ({elapsed_time:.2f}s)")
                    
            except Exception as e:
                results[source_key]['errors'] += 1
                print(f"    ⚠️  ERROR: {type(e).__name__}: {str(e)[:60]}")
        
        # Calculate average time
        total_attempts = results[source_key]['hits'] + results[source_key]['misses']
        if total_attempts > 0:
            results[source_key]['avg_time'] = results[source_key]['total_time'] / total_attempts
    
    # Print summary
    print("\n" + "="*80)
    print("BENCHMARK RESULTS")
    print("="*80)
    
    print(f"\n{'Source':<25} {'Hit Rate':<12} {'Avg Time':<12} {'Hits':<6} {'Misses':<6} {'Errors':<6}")
    print("-" * 80)
    
    for source_key, source_name in sources:
        data = results[source_key]
        total = data['hits'] + data['misses'] + data['errors']
        hit_rate = (data['hits'] / total * 100) if total > 0 else 0
        avg_time = data['avg_time']
        
        print(f"{source_name:<25} {hit_rate:>6.1f}%     {avg_time:>6.2f}s      {data['hits']:<6} {data['misses']:<6} {data['errors']:<6}")
    
    # Calculate scores (hit rate weighted 70%, speed weighted 30%)
    print("\n" + "="*80)
    print("RECOMMENDED ORDERING (by combined score)")
    print("Score = (Hit Rate × 0.7) + (Speed Score × 0.3)")
    print("="*80)
    
    scored_sources = []
    max_time = max([results[s[0]]['avg_time'] for s in sources if results[s[0]]['avg_time'] > 0], default=1.0)
    
    for source_key, source_name in sources:
        data = results[source_key]
        total = data['hits'] + data['misses'] + data['errors']
        
        if total == 0:
            continue
        
        hit_rate = (data['hits'] / total * 100)
        avg_time = data['avg_time']
        
        # Speed score: faster is better (inverse of normalized time)
        speed_score = (1 - (avg_time / max_time if max_time > 0 else 0)) * 100
        
        # Combined score
        combined_score = (hit_rate * 0.7) + (speed_score * 0.3)
        
        scored_sources.append({
            'key': source_key,
            'name': source_name,
            'hit_rate': hit_rate,
            'speed_score': speed_score,
            'combined_score': combined_score,
            'avg_time': avg_time,
            'hits': data['hits']
        })
    
    # Sort by combined score
    scored_sources.sort(key=lambda x: x['combined_score'], reverse=True)
    
    print(f"\n{'Rank':<6} {'Source':<25} {'Score':<10} {'Hit Rate':<12} {'Speed':<12}")
    print("-" * 80)
    
    for rank, source in enumerate(scored_sources, 1):
        print(f"{rank:<6} {source['name']:<25} {source['combined_score']:>6.1f}    {source['hit_rate']:>6.1f}%     {source['avg_time']:>6.2f}s")
    
    # Generate recommended source list
    print("\n" + "="*80)
    print("RECOMMENDED SOURCE PRIORITY LIST")
    print("="*80)
    print("\n```python")
    print("search_sources = [")
    print("    ('casemine', self._verify_with_casemine_sync, 5.0),  # #1 - Keep as priority")
    
    for rank, source in enumerate(scored_sources, 2):
        timeout = 4.0 if rank <= 4 else 3.0  # Higher timeout for top sources
        print(f"    ('{source['key']}', self._verify_with_{source['key']}_sync, {timeout}),  # #{rank} - Score: {source['combined_score']:.1f}")
    
    print("]")
    print("```")
    
    # Performance insights
    print("\n" + "="*80)
    print("KEY INSIGHTS")
    print("="*80)
    
    # Best hit rate
    best_hit = max(scored_sources, key=lambda x: x['hit_rate'])
    print(f"\n🎯 Best Hit Rate: {best_hit['name']} ({best_hit['hit_rate']:.1f}%)")
    
    # Fastest
    fastest = min(scored_sources, key=lambda x: x['avg_time'])
    print(f"⚡ Fastest: {fastest['name']} ({fastest['avg_time']:.2f}s avg)")
    
    # Best overall
    best_overall = scored_sources[0]
    print(f"🏆 Best Overall: {best_overall['name']} (Score: {best_overall['combined_score']:.1f})")
    
    # Sources to consider removing
    poor_performers = [s for s in scored_sources if s['hit_rate'] < 20 or s['hits'] == 0]
    if poor_performers:
        print(f"\n⚠️  Consider Removing (low hit rate):")
        for s in poor_performers:
            print(f"   - {s['name']} ({s['hit_rate']:.1f}% hit rate, {s['hits']} hits)")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    test_all_sources()
