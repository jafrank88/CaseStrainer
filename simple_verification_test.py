#!/usr/bin/env python3
"""
Simple test to identify why citations are unverified
"""

import requests
import json
import os
from dotenv import load_dotenv

def simple_verification_test():
    """Test verification directly to identify the issue"""
    
    load_dotenv()
    api_key = os.getenv('COURTLISTENER_API_KEY')
    
    print("SIMPLE VERIFICATION TEST")
    print("=" * 40)
    print(f"API Key present: {'✅ Yes' if api_key else '❌ No'}")
    
    if not api_key:
        print("❌ CRITICAL: No CourtListener API key found!")
        print("This is likely why all citations are unverified.")
        return
    
    # Test direct CourtListener API call
    citation = "17 L. Ed. 2d 562"
    headers = {"Authorization": f"Token {api_key}"}
    
    print(f"\nTesting citation: {citation}")
    print("-" * 40)
    
    # Test 1: Citation field search
    search_url = "https://www.courtlistener.com/api/rest/v4/search/"
    
    try:
        response = requests.get(
            search_url,
            params={
                "type": "o",
                "q": f'citation:"{citation}"',
                "order_by": "score desc"
            },
            headers=headers,
            timeout=10
        )
        
        print(f"Citation field search status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"Results found: {len(results)}")
            
            if results:
                result = results[0]
                case_name = result.get('caseName', 'N/A')
                citations_array = result.get('citation', [])
                
                print(f"Case name: {case_name}")
                print(f"Citations array: {citations_array}")
                
                if citation in citations_array:
                    print("✅ Citation validation would PASS")
                else:
                    print("❌ Citation validation would FAIL")
                    print("This explains why citations are unverified!")
            else:
                print("❌ No results found with citation field search")
                
        elif response.status_code == 401:
            print("❌ CRITICAL: API key authentication failed!")
            print("This is why all citations are unverified.")
            
        else:
            print(f"❌ API error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 2: Try different citation formats
    print(f"\nTesting different citation formats:")
    print("-" * 40)
    
    citation_formats = [
        "17 L. Ed. 2d 562",
        "17L.Ed.2d562", 
        "17 L Ed 2d 562",
        "17 L. Ed. 2d 562",
    ]
    
    for fmt in citation_formats:
        try:
            response = requests.get(
                search_url,
                params={
                    "type": "o",
                    "q": f'citation:"{fmt}"',
                    "order_by": "score desc"
                },
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                count = data.get('count', 0)
                print(f"  {fmt}: {count} results")
            else:
                print(f"  {fmt}: Error {response.status_code}")
                
        except Exception as e:
            print(f"  {fmt}: Exception")

if __name__ == "__main__":
    simple_verification_test()
