#!/usr/bin/env python3
"""
Improved web search test with better queries
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

def test_improved_web_search():
    """Test web search with improved approach"""
    
    citations = [
        "181 Wash. 2d 401",  # The typo - should not exist
        "192 Wash. 2d 350",  # Legitimate citation
        "197 Wash. 2d 170",  # Legitimate citation
        "199 Wash. 2d 282"   # Legitimate citation
    ]
    
    print("Testing improved web search for remaining citations:")
    print("=" * 60)
    
    # Initialize verifier
    verifier = EnhancedMultiSourceVerifier()
    
    for i, citation in enumerate(citations, 1):
        print(f"\n{i}. Testing: {citation}")
        print("-" * 40)
        
        # Create better search queries
        queries = [
            f'"{citation}" "Washington Supreme Court" case law',
            f'"{citation}" "Washington State" court opinion',
            f'"{citation}" site:courtlistener.com',
            f'"{citation}" site:justia.com'
        ]
        
        all_results = []
        
        for j, query in enumerate(queries, 1):
            print(f"   Query {j}: {query}")
            
            try:
                # Test Google search with delay
                time.sleep(2)  # Avoid rate limiting
                google_results = verifier._search_google(query)
                
                if google_results:
                    print(f"      Google: {len(google_results)} results")
                    for url in google_results[:2]:  # Show first 2 results
                        print(f"        - {url}")
                    all_results.extend(google_results)
                else:
                    print(f"      Google: No results")
                    
            except Exception as e:
                print(f"      Google ERROR: {e}")
                if "429" in str(e):
                    print("      ⚠️  RATE LIMITED (429 error)")
                elif "403" in str(e):
                    print("      ⚠️  FORBIDDEN (403 error)")
        
        # Analyze results
        print(f"\n   📊 Analysis for {citation}:")
        legal_sites = [url for url in all_results if any(site in url.lower() for site in 
                       ['courtlistener', 'justia', 'findlaw', 'casetext', 'supreme', 'court'])]
        
        if legal_sites:
            print(f"   ✅ Found {len(legal_sites)} legal site results")
            for site in legal_sites[:3]:
                print(f"      - {site}")
        else:
            print(f"   ❌ No legal site results found")
            if "181" in citation and "401" in citation:
                print(f"   💡 This appears to be the typo (181 Wash. 2d 401)")
        
        print()

if __name__ == "__main__":
    test_improved_web_search() 