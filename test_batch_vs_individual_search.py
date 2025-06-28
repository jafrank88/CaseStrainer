#!/usr/bin/env python3
"""
Test batch vs individual search efficiency for unverified citations
"""

import sys
import os
import time
import json
from datetime import datetime
sys.path.append('src')

from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_batch_vs_individual_search():
    """Compare batch vs individual search efficiency"""
    
    print("Testing Batch vs Individual Search Efficiency:")
    print("=" * 80)
    
    # Initialize verifier
    verifier = EnhancedMultiSourceVerifier()
    
    # Unverified citations that need web search
    unverified_citations = [
        "181 Wash. 2d 401",
        "192 Wash. 2d 350", 
        "197 Wash. 2d 170",
        "199 Wash. 2d 282"
    ]
    
    print(f"Testing {len(unverified_citations)} unverified citations")
    print("=" * 80)
    
    # Test 1: Individual searches (current method)
    print("\n🔍 Test 1: Individual Searches (Current Method)")
    print("-" * 60)
    
    individual_start = time.time()
    individual_results = []
    
    for i, citation in enumerate(unverified_citations, 1):
        print(f"  [{i}/{len(unverified_citations)}] Searching: '{citation}'")
        start_time = time.time()
        
        try:
            # Use the current individual search method
            urls = verifier._search_with_legal_modifiers(citation, max_results=15)
            direct_urls = verifier._search_legal_sites_directly(citation, max_results=10)
            all_urls = list(set(urls + direct_urls))
            
            legal_urls = [url for url in all_urls if any(site in url.lower() for site in 
                           ['courtlistener', 'justia', 'findlaw', 'casetext', 'supreme', 'court', 'vlex', 'westlaw'])]
            
            end_time = time.time()
            search_time = end_time - start_time
            
            individual_results.append({
                'citation': citation,
                'legal_urls_found': len(legal_urls),
                'search_time': search_time,
                'urls': legal_urls[:3]  # Show first 3
            })
            
            print(f"    ✅ Found {len(legal_urls)} legal URLs in {search_time:.2f}s")
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
            individual_results.append({
                'citation': citation,
                'legal_urls_found': 0,
                'search_time': 0,
                'urls': []
            })
        
        # Delay between individual searches
        if i < len(unverified_citations):
            time.sleep(3)
    
    individual_end = time.time()
    individual_total_time = individual_end - individual_start
    
    # Test 2: Batch search with site limits
    print(f"\n🌐 Test 2: Batch Search with Site Limits")
    print("-" * 60)
    
    batch_start = time.time()
    batch_results = []
    
    try:
        print(f"  Creating batch query for {len(unverified_citations)} citations...")
        
        # Test different batch strategies
        citations_quoted = [f'"{citation}"' for citation in unverified_citations]
        citations_or = ' OR '.join(citations_quoted)
        
        batch_strategies = [
            # Strategy 1: Simple OR batch
            {
                'name': 'Simple OR Batch',
                'query': citations_or
            },
            # Strategy 2: Batch with legal site limits
            {
                'name': 'Batch with Legal Sites',
                'query': f'({citations_or}) AND (site:courtlistener.com OR site:justia.com OR site:vlex.com OR site:findlaw.com)'
            },
            # Strategy 3: Batch with Washington focus
            {
                'name': 'Batch with Washington Focus',
                'query': f'({citations_or}) AND "Washington" AND (site:courtlistener.com OR site:justia.com OR site:vlex.com)'
            }
        ]
        
        for strategy in batch_strategies:
            print(f"  Testing: {strategy['name']}")
            strategy_start = time.time()
            
            # Test with DuckDuckGo
            try:
                duckduckgo_urls = verifier._search_duckduckgo(strategy['query'], max_results=20)
                print(f"    🦆 DuckDuckGo: {len(duckduckgo_urls)} URLs")
            except Exception as e:
                print(f"    🦆 DuckDuckGo failed: {e}")
                duckduckgo_urls = []
            
            # Test with Bing
            try:
                bing_urls = verifier._search_bing(strategy['query'], max_results=20)
                print(f"    🔍 Bing: {len(bing_urls)} URLs")
            except Exception as e:
                print(f"    🔍 Bing failed: {e}")
                bing_urls = []
            
            # Combine and filter
            all_batch_urls = list(set(duckduckgo_urls + bing_urls))
            legal_batch_urls = [url for url in all_batch_urls if any(site in url.lower() for site in 
                                   ['courtlistener', 'justia', 'findlaw', 'casetext', 'supreme', 'court', 'vlex', 'westlaw'])]
            
            strategy_end = time.time()
            strategy_time = strategy_end - strategy_start
            
            batch_results.append({
                'strategy': strategy['name'],
                'total_urls': len(all_batch_urls),
                'legal_urls': len(legal_batch_urls),
                'search_time': strategy_time,
                'urls': legal_batch_urls[:5]  # Show first 5
            })
            
            print(f"    ✅ Found {len(legal_batch_urls)} legal URLs in {strategy_time:.2f}s")
            print(f"    📊 Total URLs: {len(all_batch_urls)}")
            
            # Check if we found our specific citations
            for citation in unverified_citations:
                citation_found = any(citation.replace(' ', '').lower() in url.lower() for url in legal_batch_urls)
                print(f"    {'🎯' if citation_found else '❌'} {citation}: {'Found' if citation_found else 'Not found'}")
            
            time.sleep(5)  # Delay between strategies
        
    except Exception as e:
        print(f"  ❌ Batch search error: {e}")
    
    batch_end = time.time()
    batch_total_time = batch_end - batch_start
    
    # Summary
    print(f"\n📊 Efficiency Comparison Summary:")
    print("=" * 80)
    
    print(f"🔍 Individual Searches:")
    print(f"   Total time: {individual_total_time:.2f} seconds")
    print(f"   Average per citation: {individual_total_time/len(unverified_citations):.2f} seconds")
    total_individual_legal = sum(r['legal_urls_found'] for r in individual_results)
    print(f"   Total legal URLs found: {total_individual_legal}")
    print(f"   Average legal URLs per citation: {total_individual_legal/len(unverified_citations):.1f}")
    
    print(f"\n🌐 Batch Searches:")
    print(f"   Total time: {batch_total_time:.2f} seconds")
    print(f"   Average per citation: {batch_total_time/len(unverified_citations):.2f} seconds")
    total_batch_legal = sum(r['legal_urls'] for r in batch_results)
    print(f"   Total legal URLs found: {total_batch_legal}")
    
    # Efficiency calculation
    individual_efficiency = total_individual_legal / individual_total_time if individual_total_time > 0 else 0
    batch_efficiency = total_batch_legal / batch_total_time if batch_total_time > 0 else 0
    
    print(f"\n⚡ Efficiency (legal URLs per second):")
    print(f"   Individual: {individual_efficiency:.2f}")
    print(f"   Batch: {batch_efficiency:.2f}")
    
    # Save results
    results = {
        'individual': individual_results,
        'batch': batch_results,
        'timing': {
            'individual_total': individual_total_time,
            'batch_total': batch_total_time
        },
        'efficiency': {
            'individual': individual_efficiency,
            'batch': batch_efficiency
        }
    }
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"batch_vs_individual_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    test_batch_vs_individual_search() 