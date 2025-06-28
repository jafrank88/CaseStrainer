#!/usr/bin/env python3
"""
Test googlesearch with 100 results and simple queries
"""

import sys
import os
import time
sys.path.append('src')

def test_google_100_results():
    """Test googlesearch with 100 results"""
    
    try:
        from googlesearch import search as google_search
        print("✅ googlesearch library imported successfully")
        
        # Test 1: Simple query with 100 results
        print("\n🔍 Test 1: Simple query with 100 results")
        print("Query: 'Washington Supreme Court'")
        
        try:
            urls = list(google_search('Washington Supreme Court', num_results=100))
            print(f"✅ Found {len(urls)} results")
            
            # Show first 10 results
            for i, url in enumerate(urls[:10], 1):
                print(f"   {i:2d}. {url}")
            if len(urls) > 10:
                print(f"   ... and {len(urls) - 10} more")
                
        except Exception as e:
            print(f"❌ Failed: {e}")
        
        # Test 2: Citation query with 100 results
        print("\n🔍 Test 2: Citation query with 100 results")
        print("Query: '192 Wash. 2d 350'")
        
        try:
            urls = list(google_search('192 Wash. 2d 350', num_results=100))
            print(f"✅ Found {len(urls)} results")
            
            # Show first 10 results
            for i, url in enumerate(urls[:10], 1):
                print(f"   {i:2d}. {url}")
            if len(urls) > 10:
                print(f"   ... and {len(urls) - 10} more")
                
            # Check for legal sites
            legal_urls = [url for url in urls if any(site in url.lower() for site in 
                           ['courtlistener', 'justia', 'findlaw', 'casetext', 'supreme', 'court'])]
            print(f"\n🏛️  Legal site results: {len(legal_urls)}")
            for url in legal_urls:
                print(f"   - {url}")
                
        except Exception as e:
            print(f"❌ Failed: {e}")
        
        # Test 3: Batch query with 100 results
        print("\n🔍 Test 3: Batch query with 100 results")
        batch_query = '"192 Wash. 2d 350" OR "197 Wash. 2d 170"'
        print(f"Query: {batch_query}")
        
        try:
            urls = list(google_search(batch_query, num_results=100))
            print(f"✅ Found {len(urls)} results")
            
            # Show first 10 results
            for i, url in enumerate(urls[:10], 1):
                print(f"   {i:2d}. {url}")
            if len(urls) > 10:
                print(f"   ... and {len(urls) - 10} more")
                
        except Exception as e:
            print(f"❌ Failed: {e}")
        
        # Test 4: Different num_results values
        print("\n🔍 Test 4: Testing different num_results values")
        test_query = 'Washington Supreme Court'
        
        for num_results in [10, 25, 50, 100]:
            print(f"\n   Testing num_results={num_results}...")
            try:
                urls = list(google_search(test_query, num_results=num_results))
                print(f"   ✅ Found {len(urls)} results")
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                break  # Stop if we hit rate limiting
        
    except ImportError:
        print("❌ googlesearch library not available")

if __name__ == "__main__":
    test_google_100_results() 