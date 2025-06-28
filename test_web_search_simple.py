#!/usr/bin/env python3
"""
Simple test to check web search and rate limiting
"""

import sys
import os
sys.path.append('src')

from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_simple_web_search():
    """Test web search with simple approach"""
    
    citations = [
        "181 Wash. 2d 401",  # The typo - should not exist
        "192 Wash. 2d 350",  # Legitimate citation
        "197 Wash. 2d 170",  # Legitimate citation
        "199 Wash. 2d 282"   # Legitimate citation
    ]
    
    print("Testing web search for remaining citations:")
    print("=" * 50)
    
    # Initialize verifier
    verifier = EnhancedMultiSourceVerifier()
    
    for i, citation in enumerate(citations, 1):
        print(f"\n{i}. Testing: {citation}")
        print("-" * 30)
        
        try:
            # Test Google search first
            print("Testing Google search...")
            google_results = verifier._search_google(f'"{citation}" Washington Supreme Court case')
            print(f"   Google results: {len(google_results) if google_results else 0} URLs found")
            if google_results:
                print(f"   First result: {google_results[0]}")
            
            # Test DuckDuckGo search
            print("Testing DuckDuckGo search...")
            ddg_results = verifier._search_duckduckgo(f'"{citation}" Washington Supreme Court case')
            print(f"   DuckDuckGo results: {len(ddg_results) if ddg_results else 0} URLs found")
            if ddg_results:
                print(f"   First result: {ddg_results[0]}")
            
            # Test Bing search
            print("Testing Bing search...")
            bing_results = verifier._search_bing(f'"{citation}" Washington Supreme Court case')
            print(f"   Bing results: {len(bing_results) if bing_results else 0} URLs found")
            if bing_results:
                print(f"   First result: {bing_results[0]}")
                
        except Exception as e:
            print(f"   ERROR: {e}")
            if "429" in str(e):
                print("   ⚠️  RATE LIMITED (429 error)")
            elif "403" in str(e):
                print("   ⚠️  FORBIDDEN (403 error)")
        
        print()

if __name__ == "__main__":
    test_simple_web_search() 