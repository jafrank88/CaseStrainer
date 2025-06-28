#!/usr/bin/env python3
"""
Test legal citation verification using improved web search with legal modifiers
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

def test_legal_citation_verification():
    """Test legal citation verification using improved web search"""
    
    print("Testing Legal Citation Verification with Improved Web Search:")
    print("=" * 80)
    
    # Initialize verifier
    verifier = EnhancedMultiSourceVerifier()
    
    # Read citations that need web search
    with open('cleaned_citations_for_websearch.txt', 'r') as f:
        citations = [line.strip() for line in f if line.strip()]
    
    print(f"Found {len(citations)} citations to verify")
    print("=" * 80)
    
    # Test a subset of citations (first 10 to avoid rate limiting)
    test_citations = citations[:10]
    
    results = []
    
    for i, citation in enumerate(test_citations, 1):
        print(f"\n🔍 [{i}/{len(test_citations)}] Testing citation: '{citation}'")
        print("-" * 60)
        
        start_time = time.time()
        
        # Test the improved web search with legal modifiers
        try:
            # Use the new _search_with_legal_modifiers method
            urls = verifier._search_with_legal_modifiers(citation, max_results=15)
            
            # Also test direct legal site search
            direct_urls = verifier._search_legal_sites_directly(citation, max_results=10)
            
            # Combine and deduplicate
            all_urls = list(set(urls + direct_urls))
            
            # Filter for legal sites
            legal_urls = [url for url in all_urls if any(site in url.lower() for site in 
                           ['courtlistener', 'justia', 'findlaw', 'casetext', 'supreme', 'court', 'vlex', 'westlaw'])]
            
            end_time = time.time()
            search_time = end_time - start_time
            
            result = {
                'citation': citation,
                'total_urls_found': len(all_urls),
                'legal_urls_found': len(legal_urls),
                'search_time_seconds': round(search_time, 2),
                'legal_urls': legal_urls[:5],  # Show first 5 legal URLs
                'all_urls': all_urls[:5]  # Show first 5 total URLs
            }
            
            results.append(result)
            
            print(f"✅ Found {len(all_urls)} total URLs ({len(legal_urls)} legal sites)")
            print(f"⏱️  Search time: {search_time:.2f} seconds")
            
            if legal_urls:
                print(f"🏛️  Legal sites found:")
                for j, url in enumerate(legal_urls[:3], 1):
                    print(f"   {j}. {url}")
                if len(legal_urls) > 3:
                    print(f"   ... and {len(legal_urls) - 3} more")
            else:
                print("❌ No legal sites found")
            
            # Check if we found the specific case you mentioned
            if any('american-legion' in url.lower() for url in all_urls):
                print("🎯 FOUND: American Legion case!")
            
        except Exception as e:
            print(f"❌ Error searching for '{citation}': {e}")
            result = {
                'citation': citation,
                'error': str(e),
                'total_urls_found': 0,
                'legal_urls_found': 0,
                'search_time_seconds': 0,
                'legal_urls': [],
                'all_urls': []
            }
            results.append(result)
        
        # Add delay between searches to avoid rate limiting
        if i < len(test_citations):
            print("⏳ Waiting 3 seconds before next search...")
            time.sleep(3)
    
    # Summary
    print(f"\n📊 Verification Summary:")
    print("=" * 80)
    
    successful_searches = [r for r in results if 'error' not in r]
    failed_searches = [r for r in results if 'error' in r]
    
    total_legal_urls = sum(r['legal_urls_found'] for r in successful_searches)
    total_search_time = sum(r['search_time_seconds'] for r in successful_searches)
    
    print(f"✅ Successful searches: {len(successful_searches)}/{len(test_citations)}")
    print(f"❌ Failed searches: {len(failed_searches)}")
    print(f"🏛️  Total legal URLs found: {total_legal_urls}")
    print(f"⏱️  Total search time: {total_search_time:.2f} seconds")
    print(f"📈 Average legal URLs per citation: {total_legal_urls/len(successful_searches):.1f}" if successful_searches else "N/A")
    
    # Show best performing citations
    if successful_searches:
        best_citations = sorted(successful_searches, key=lambda x: x['legal_urls_found'], reverse=True)
        print(f"\n🏆 Top performing citations:")
        for i, result in enumerate(best_citations[:5], 1):
            print(f"   {i}. {result['citation']}: {result['legal_urls_found']} legal URLs")
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"legal_verification_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    test_legal_citation_verification() 