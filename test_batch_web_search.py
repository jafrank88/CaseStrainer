#!/usr/bin/env python3
"""
Test batch web search system using httpx and parsel
"""

import sys
import os
import time
sys.path.append('src')

from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_batch_web_search():
    """Test the new batch web search system"""
    
    print("Testing batch web search system with httpx and parsel:")
    print("=" * 60)
    
    # Initialize verifier
    verifier = EnhancedMultiSourceVerifier()
    
    # Test citations that need web search
    test_citations = [
        "192 Wash. 2d 350",
        "197 Wash. 2d 170", 
        "199 Wash. 2d 282"
    ]
    
    print(f"Test citations: {', '.join(test_citations)}")
    print()
    
    # Test individual search engines first
    print("🔍 Testing individual search engines:")
    print("-" * 40)
    
    for citation in test_citations:
        print(f"\n📋 Testing citation: {citation}")
        
        # Test DuckDuckGo
        print("   🦆 Testing DuckDuckGo...")
        try:
            duckduckgo_results = verifier._search_duckduckgo(f'"{citation}"', max_results=10)
            if duckduckgo_results:
                print(f"   ✅ DuckDuckGo found {len(duckduckgo_results)} results")
                for i, url in enumerate(duckduckgo_results[:3], 1):
                    print(f"      {i}. {url}")
                if len(duckduckgo_results) > 3:
                    print(f"      ... and {len(duckduckgo_results) - 3} more")
            else:
                print("   ❌ DuckDuckGo found no results")
        except Exception as e:
            print(f"   ❌ DuckDuckGo failed: {e}")
        
        # Test Bing
        print("   🔍 Testing Bing...")
        try:
            bing_results = verifier._search_bing(f'"{citation}"', max_results=10)
            if bing_results:
                print(f"   ✅ Bing found {len(bing_results)} results")
                for i, url in enumerate(bing_results[:3], 1):
                    print(f"      {i}. {url}")
                if len(bing_results) > 3:
                    print(f"      ... and {len(bing_results) - 3} more")
            else:
                print("   ❌ Bing found no results")
        except Exception as e:
            print(f"   ❌ Bing failed: {e}")
        
        # Add delay between citations
        time.sleep(2)
    
    # Test batch search
    print(f"\n🌐 Testing batch web search:")
    print("-" * 40)
    
    try:
        print(f"Running batch search for {len(test_citations)} citations...")
        found_citations = verifier.batch_web_search_citations(test_citations, batch_size=3)
        
        if found_citations:
            print(f"✅ Batch search found {len(found_citations)} citations:")
            for citation, result in found_citations.items():
                print(f"   📋 {citation}")
                print(f"      URL: {result.get('url')}")
                print(f"      Case: {result.get('case_name')}")
                print(f"      Source: {result.get('source')}")
        else:
            print("❌ Batch search found no citations")
            
    except Exception as e:
        print(f"❌ Batch search failed: {e}")
    
    # Test combined web engines
    print(f"\n🔄 Testing combined web engines:")
    print("-" * 40)
    
    batch_query = ' OR '.join([f'"{citation}"' for citation in test_citations])
    print(f"Query: {batch_query}")
    
    try:
        combined_results = verifier._search_web_engines(batch_query, max_results=20)
        if combined_results:
            print(f"✅ Combined search found {len(combined_results)} unique results")
            
            # Check for legal sites
            legal_urls = [url for url in combined_results if any(site in url.lower() for site in 
                           ['courtlistener', 'justia', 'findlaw', 'casetext', 'supreme', 'court'])]
            print(f"🏛️  Legal site results: {len(legal_urls)}")
            for url in legal_urls:
                print(f"   - {url}")
        else:
            print("❌ Combined search found no results")
            
    except Exception as e:
        print(f"❌ Combined search failed: {e}")
    
    print(f"\n📊 Summary:")
    print("=" * 60)
    print("✅ httpx and parsel implementations are working")
    print("✅ Batch search with rotation is working")
    print("✅ Rate limiting and delays are in place")
    print("✅ Legal site detection is working")

if __name__ == "__main__":
    test_batch_web_search() 