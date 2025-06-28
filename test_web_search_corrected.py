#!/usr/bin/env python3
"""
Corrected web search test using googlesearch library properly
"""

import sys
import os
import time
import random
sys.path.append('src')

from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_corrected_web_search():
    """Test web search with corrected approach"""
    
    citations = [
        "181 Wash. 2d 401",  # The typo - should not exist
        "192 Wash. 2d 350",  # Legitimate citation
        "197 Wash. 2d 170",  # Legitimate citation
        "199 Wash. 2d 282"   # Legitimate citation
    ]
    
    print("Testing corrected web search for remaining citations:")
    print("=" * 70)
    print(f"Citations: {', '.join(citations)}")
    print()
    
    # Initialize verifier
    verifier = EnhancedMultiSourceVerifier()
    
    # Test 1: Simple batch query without site limiters
    batch_query = ' OR '.join([f'"{citation}"' for citation in citations])
    print(f"Query: {batch_query}")
    print("-" * 60)
    
    # Test googlesearch with higher num_results
    try:
        from googlesearch import search as google_search
        print("🔍 Testing Google search with num_results=100...")
        
        # Test different num_results values
        for num_results in [10, 50, 100]:
            print(f"   Testing with num_results={num_results}...")
            try:
                urls = list(google_search(batch_query, num_results=num_results))
                print(f"   ✅ Found {len(urls)} results")
                
                # Show first 10 results
                for i, url in enumerate(urls[:10], 1):
                    print(f"      {i:2d}. {url}")
                if len(urls) > 10:
                    print(f"      ... and {len(urls) - 10} more")
                    
                # Analyze results for each citation
                print(f"\n   📊 Analysis for num_results={num_results}:")
                for citation in citations:
                    matches = [url for url in urls if any(part in url for part in citation.split())]
                    legal_matches = [url for url in matches if any(site in url.lower() for site in 
                                   ['courtlistener', 'justia', 'findlaw', 'casetext', 'supreme', 'court'])]
                    print(f"      {citation}: {len(matches)} total, {len(legal_matches)} legal")
                
                break  # If successful, don't try higher numbers
                
            except Exception as e:
                print(f"   ❌ Failed with num_results={num_results}: {e}")
                if "429" in str(e) or "Too Many Requests" in str(e):
                    print(f"   ⚠️  Rate limited - will try fallbacks")
                    break
                    
    except ImportError:
        print("❌ googlesearch library not available")
    
    print("\n" + "="*70)
    print("🔍 Testing fallback search engines...")
    
    # Test Bing fallback
    print("\n🦆 Testing DuckDuckGo fallback...")
    try:
        duckduckgo_results = verifier._search_duckduckgo(batch_query, max_results=20)
        if duckduckgo_results:
            print(f"✅ DuckDuckGo found {len(duckduckgo_results)} results")
            for i, url in enumerate(duckduckgo_results[:10], 1):
                print(f"   {i:2d}. {url}")
            if len(duckduckgo_results) > 10:
                print(f"   ... and {len(duckduckgo_results) - 10} more")
        else:
            print("❌ DuckDuckGo found no results")
    except Exception as e:
        print(f"❌ DuckDuckGo failed: {e}")
    
    # Test Bing fallback
    print("\n🔍 Testing Bing fallback...")
    try:
        bing_results = verifier._search_bing(batch_query)
        if bing_results:
            print(f"✅ Bing found {len(bing_results)} results")
            for i, url in enumerate(bing_results[:10], 1):
                print(f"   {i:2d}. {url}")
            if len(bing_results) > 10:
                print(f"   ... and {len(bing_results) - 10} more")
        else:
            print("❌ Bing found no results")
    except Exception as e:
        print(f"❌ Bing failed: {e}")
    
    print("\n" + "="*70)
    print("🔍 Testing individual citation searches...")
    
    # Test individual citations to see if any work
    for citation in citations:
        print(f"\n📋 Testing individual citation: {citation}")
        try:
            urls = list(google_search(f'"{citation}"', num_results=20))
            print(f"   ✅ Found {len(urls)} results")
            
            # Check for legal sites
            legal_urls = [url for url in urls if any(site in url.lower() for site in 
                           ['courtlistener', 'justia', 'findlaw', 'casetext', 'supreme', 'court'])]
            
            if legal_urls:
                print(f"   🏛️  Found {len(legal_urls)} legal site results:")
                for url in legal_urls:
                    print(f"      - {url}")
            else:
                print(f"   ⚠️  No legal site results found")
                if "181" in citation and "401" in citation:
                    print(f"   💡 This confirms the typo (181 Wash. 2d 401)")
                    
        except Exception as e:
            print(f"   ❌ Failed: {e}")

if __name__ == "__main__":
    test_corrected_web_search() 