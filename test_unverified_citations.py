#!/usr/bin/env python3
"""
Test web search verification for citations NOT found by CourtListener
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

def test_unverified_citations():
    """Test web search verification for citations not found by CourtListener"""
    
    print("Testing Web Search Verification for Citations NOT Found by CourtListener:")
    print("=" * 80)
    
    # Initialize verifier
    verifier = EnhancedMultiSourceVerifier()
    
    # These are the citations that were NOT found by CourtListener
    unverified_citations = [
        "181 Wash. 2d 401",
        "192 Wash. 2d 350", 
        "197 Wash. 2d 170",
        "199 Wash. 2d 282"
    ]
    
    print(f"Testing {len(unverified_citations)} citations that need web search verification")
    print("=" * 80)
    
    results = []
    
    for i, citation in enumerate(unverified_citations, 1):
        print(f"\n🔍 [{i}/{len(unverified_citations)}] Testing unverified citation: '{citation}'")
        print("-" * 60)
        
        start_time = time.time()
        
        try:
            # Test multiple search strategies
            print("🌐 Testing improved web search with legal modifiers...")
            modifier_urls = verifier._search_with_legal_modifiers(citation, max_results=15)
            
            print("🏛️ Testing direct legal site search...")
            direct_urls = verifier._search_legal_sites_directly(citation, max_results=10)
            
            print("🦆 Testing DuckDuckGo fallback...")
            duckduckgo_urls = verifier._search_duckduckgo(f'"{citation}"', max_results=10)
            
            print("🔍 Testing Bing fallback...")
            bing_urls = verifier._search_bing(f'"{citation}"', max_results=10)
            
            # Combine all results and deduplicate
            all_urls = list(set(modifier_urls + direct_urls + duckduckgo_urls + bing_urls))
            
            # Filter for legal sites
            legal_sites = ['courtlistener', 'justia', 'findlaw', 'casetext', 'supreme', 'court', 'vlex', 'westlaw', 'casemine']
            legal_urls = [url for url in all_urls if any(site in url.lower() for site in legal_sites)]
            
            end_time = time.time()
            search_time = end_time - start_time
            
            result = {
                'citation': citation,
                'total_urls_found': len(all_urls),
                'legal_urls_found': len(legal_urls),
                'search_time_seconds': round(search_time, 2),
                'modifier_urls': len(modifier_urls),
                'direct_urls': len(direct_urls),
                'duckduckgo_urls': len(duckduckgo_urls),
                'bing_urls': len(bing_urls),
                'legal_urls': legal_urls[:10],  # Show first 10 legal URLs
                'all_urls': all_urls[:10]  # Show first 10 total URLs
            }
            
            results.append(result)
            
            print(f"✅ Found {len(all_urls)} total URLs ({len(legal_urls)} legal sites)")
            print(f"⏱️  Search time: {search_time:.2f} seconds")
            print(f"📊 Breakdown:")
            print(f"   - Legal modifier search: {len(modifier_urls)} URLs")
            print(f"   - Direct legal site search: {len(direct_urls)} URLs")
            print(f"   - DuckDuckGo: {len(duckduckgo_urls)} URLs")
            print(f"   - Bing: {len(bing_urls)} URLs")
            
            if legal_urls:
                print(f"🏛️  Legal sites found:")
                for j, url in enumerate(legal_urls[:5], 1):
                    print(f"   {j}. {url}")
                if len(legal_urls) > 5:
                    print(f"   ... and {len(legal_urls) - 5} more")
                
                # Check for specific cases
                if any('american-legion' in url.lower() for url in all_urls):
                    print("🎯 FOUND: American Legion case!")
                if any('state-v-blake' in url.lower() for url in all_urls):
                    print("🎯 FOUND: State v. Blake case!")
                if any('state-v-crossguns' in url.lower() for url in all_urls):
                    print("🎯 FOUND: State v. Crossguns case!")
            else:
                print("❌ No legal sites found")
            
        except Exception as e:
            print(f"❌ Error searching for '{citation}': {e}")
            result = {
                'citation': citation,
                'error': str(e),
                'total_urls_found': 0,
                'legal_urls_found': 0,
                'search_time_seconds': 0,
                'modifier_urls': 0,
                'direct_urls': 0,
                'duckduckgo_urls': 0,
                'bing_urls': 0,
                'legal_urls': [],
                'all_urls': []
            }
            results.append(result)
        
        # Add delay between searches to avoid rate limiting
        if i < len(unverified_citations):
            print("⏳ Waiting 5 seconds before next search...")
            time.sleep(5)
    
    # Summary
    print(f"\n📊 Web Search Verification Summary:")
    print("=" * 80)
    
    successful_searches = [r for r in results if 'error' not in r]
    failed_searches = [r for r in results if 'error' in r]
    
    total_legal_urls = sum(r['legal_urls_found'] for r in successful_searches)
    total_search_time = sum(r['search_time_seconds'] for r in successful_searches)
    
    print(f"✅ Successful searches: {len(successful_searches)}/{len(unverified_citations)}")
    print(f"❌ Failed searches: {len(failed_searches)}")
    print(f"🏛️  Total legal URLs found: {total_legal_urls}")
    print(f"⏱️  Total search time: {total_search_time:.2f} seconds")
    print(f"📈 Average legal URLs per citation: {total_legal_urls/len(successful_searches):.1f}" if successful_searches else "N/A")
    
    # Show results for each citation
    print(f"\n📋 Detailed Results:")
    for result in results:
        status = "✅" if result['legal_urls_found'] > 0 else "❌"
        print(f"{status} {result['citation']}: {result['legal_urls_found']} legal URLs found")
    
    # Show best performing search method
    if successful_searches:
        print(f"\n🔍 Search Method Performance:")
        total_modifier = sum(r['modifier_urls'] for r in successful_searches)
        total_direct = sum(r['direct_urls'] for r in successful_searches)
        total_duckduckgo = sum(r['duckduckgo_urls'] for r in successful_searches)
        total_bing = sum(r['bing_urls'] for r in successful_searches)
        
        print(f"   - Legal modifier search: {total_modifier} URLs")
        print(f"   - Direct legal site search: {total_direct} URLs")
        print(f"   - DuckDuckGo: {total_duckduckgo} URLs")
        print(f"   - Bing: {total_bing} URLs")
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"unverified_citation_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    test_unverified_citations() 