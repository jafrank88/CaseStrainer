#!/usr/bin/env python3
"""
Batched web search for all remaining citations in one query
"""

import sys
import os
import time
import re
sys.path.append('src')

from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_batched_web_search():
    """Test web search with batched approach"""
    
    citations = [
        "181 Wash. 2d 401",  # The typo - should not exist
        "192 Wash. 2d 350",  # Legitimate citation
        "197 Wash. 2d 170",  # Legitimate citation
        "199 Wash. 2d 282"   # Legitimate citation
    ]
    
    print("Testing batched web search for all remaining citations:")
    print("=" * 60)
    print(f"Citations: {', '.join(citations)}")
    print()
    
    # Initialize verifier
    verifier = EnhancedMultiSourceVerifier()
    
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
        print("-" * 50)
        
        try:
            # Test Google search with delay
            time.sleep(3)  # Avoid rate limiting
            google_results = verifier._search_google(query)
            
            if google_results:
                print(f"✅ Found {len(google_results)} results")
                all_results.extend(google_results)
                
                # Show all results (up to 100)
                for j, url in enumerate(google_results, 1):
                    print(f"   {j:2d}. {url}")
                if len(google_results) > 100:
                    print(f"   ... and {len(google_results) - 100} more results")
            else:
                print(f"❌ No results found")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            if "429" in str(e):
                print("   ⚠️  RATE LIMITED (429 error)")
            elif "403" in str(e):
                print("   ⚠️  FORBIDDEN (403 error)")
        
        print()
    
    # Analyze results for each citation
    print("📊 ANALYSIS BY CITATION:")
    print("=" * 60)
    
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
            for match in matches[:5]:
                print(f"      - {match}")
            if len(matches) > 5:
                print(f"      ... and {len(matches) - 5} more")
        else:
            print(f"   ❌ No matches found")
            if "181" in citation and "401" in citation:
                print(f"   💡 This appears to be the typo (181 Wash. 2d 401)")
    
    # Summary
    print(f"\n📈 SUMMARY:")
    print("=" * 60)
    print(f"Total search results: {len(all_results)}")
    legal_sites = [url for url in all_results if any(site in url.lower() for site in 
                   ['courtlistener', 'justia', 'findlaw', 'casetext', 'supreme', 'court'])]
    print(f"Legal site results: {len(legal_sites)}")
    print(f"Non-legal results: {len(all_results) - len(legal_sites)}")
    
    # Show all legal site results
    if legal_sites:
        print(f"\n🏛️  ALL LEGAL SITE RESULTS:")
        print("-" * 40)
        for i, url in enumerate(legal_sites, 1):
            print(f"{i:2d}. {url}")

if __name__ == "__main__":
    test_batched_web_search() 