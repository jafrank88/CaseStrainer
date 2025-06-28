#!/usr/bin/env python3
"""
High-volume web search test that gets 100+ results
"""

import sys
import os
import time
import requests
from bs4 import BeautifulSoup
import random
sys.path.append('src')

from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def search_google_high_volume(query: str, max_results: int = 100) -> list:
    """Search Google with high volume results"""
    try:
        # Add delay to prevent rate limiting
        time.sleep(random.uniform(2, 5))
        
        # Use multiple user agents to avoid detection
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        urls = []
        
        # Search multiple pages to get more results
        for start in range(0, max_results, 10):
            params = {
                'q': query,
                'num': 10,  # Results per page
                'hl': 'en',
                'start': start,
                'safe': 'active',
                'source': 'hp',
                'ie': 'UTF-8',
                'oe': 'UTF-8'
            }
            
            response = requests.get(
                'https://www.google.com/search',
                params=params,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 429:
                print(f"⚠️  Rate limited at page {start//10 + 1}")
                break
                
            response.raise_for_status()
            
            # Parse results
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract URLs from search results
            for result in soup.find_all('a', href=True):
                href = result['href']
                if href.startswith('/url?q='):
                    # Extract actual URL from Google redirect
                    actual_url = href.split('/url?q=')[1].split('&')[0]
                    if actual_url.startswith('http') and actual_url not in urls:
                        urls.append(actual_url)
                elif href.startswith('http') and 'google.com' not in href and href not in urls:
                    urls.append(href)
            
            # If we got fewer than 10 results, we've reached the end
            if len(urls) < start + 10:
                break
                
            # Small delay between pages
            time.sleep(random.uniform(1, 3))
        
        return urls[:max_results]
        
    except Exception as e:
        print(f"❌ Error with high-volume search: {e}")
        return []

def test_high_volume_web_search():
    """Test web search with high volume approach"""
    
    citations = [
        "181 Wash. 2d 401",  # The typo - should not exist
        "192 Wash. 2d 350",  # Legitimate citation
        "197 Wash. 2d 170",  # Legitimate citation
        "199 Wash. 2d 282"   # Legitimate citation
    ]
    
    print("Testing high-volume web search for all remaining citations:")
    print("=" * 70)
    print(f"Citations: {', '.join(citations)}")
    print()
    
    # Create batched search queries
    batched_queries = [
        f'("181 Wash. 2d 401" OR "192 Wash. 2d 350" OR "197 Wash. 2d 170" OR "199 Wash. 2d 282") "Washington Supreme Court"',
        f'("181 Wash. 2d 401" OR "192 Wash. 2d 350" OR "197 Wash. 2d 170" OR "199 Wash. 2d 282") site:courtlistener.com',
        f'("181 Wash. 2d 401" OR "192 Wash. 2d 350" OR "197 Wash. 2d 170" OR "199 Wash. 2d 282") site:justia.com',
        f'("181 Wash. 2d 401" OR "192 Wash. 2d 350" OR "197 Wash. 2d 170" OR "199 Wash. 2d 282") site:findlaw.com'
    ]
    
    all_results = []
    
    for i, query in enumerate(batched_queries, 1):
        print(f"Query {i}: {query}")
        print("-" * 60)
        
        # Use high-volume search
        google_results = search_google_high_volume(query, max_results=100)
        
        if google_results:
            print(f"✅ Found {len(google_results)} results")
            all_results.extend(google_results)
            
            # Show all results
            for j, url in enumerate(google_results, 1):
                print(f"   {j:3d}. {url}")
        else:
            print(f"❌ No results found")
        
        print()
    
    # Analyze results for each citation
    print("📊 ANALYSIS BY CITATION:")
    print("=" * 70)
    
    for citation in citations:
        print(f"\n🔍 {citation}:")
        
        # Count matches for this citation
        matches = []
        legal_matches = []
        
        for url in all_results:
            # Check if URL contains citation parts
            citation_parts = citation.split()
            if any(part in url for part in citation_parts):
                matches.append(url)
                
                # Check if it's a legal site
                if any(site in url.lower() for site in ['courtlistener', 'justia', 'findlaw', 'casetext', 'supreme', 'court']):
                    legal_matches.append(url)
        
        print(f"   Total matches: {len(matches)}")
        print(f"   Legal site matches: {len(legal_matches)}")
        
        if legal_matches:
            print(f"   ✅ Found {len(legal_matches)} legal site matches:")
            for match in legal_matches:
                print(f"      - {match}")
        elif matches:
            print(f"   ⚠️  Found {len(matches)} non-legal matches:")
            for match in matches[:10]:
                print(f"      - {match}")
            if len(matches) > 10:
                print(f"      ... and {len(matches) - 10} more")
        else:
            print(f"   ❌ No matches found")
            if "181" in citation and "401" in citation:
                print(f"   💡 This appears to be the typo (181 Wash. 2d 401)")
    
    # Summary
    print(f"\n📈 SUMMARY:")
    print("=" * 70)
    print(f"Total search results: {len(all_results)}")
    legal_sites = [url for url in all_results if any(site in url.lower() for site in 
                   ['courtlistener', 'justia', 'findlaw', 'casetext', 'supreme', 'court'])]
    print(f"Legal site results: {len(legal_sites)}")
    print(f"Non-legal results: {len(all_results) - len(legal_sites)}")
    
    # Show all legal site results
    if legal_sites:
        print(f"\n🏛️  ALL LEGAL SITE RESULTS:")
        print("-" * 50)
        for i, url in enumerate(legal_sites, 1):
            print(f"{i:2d}. {url}")

if __name__ == "__main__":
    test_high_volume_web_search() 