#!/usr/bin/env python3
"""
Simple comparison of citation-lookup vs search API for key citations.
"""

import json
import requests
import time

def load_api_key():
    """Load API key from config.json"""
    try:
        with open('config/config.json', 'r') as f:
            config = json.load(f)
            return config.get('COURTLISTENER_API_KEY') or config.get('courtlistener_api_key')
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

def test_citation_lookup(api_key, citation):
    """Test single citation with citation-lookup API"""
    url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    headers = {
        'Authorization': f'Token {api_key}',
        'Content-Type': 'application/json'
    }
    data = {'text': citation}
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            results = response.json()
            if results and results[0].get('clusters'):
                cluster = results[0]['clusters'][0]
                return {
                    'found': True,
                    'case_name': cluster.get('case_name', ''),
                    'date_filed': cluster.get('date_filed', ''),
                    'court': cluster.get('court', '')
                }
        return {'found': False}
    except Exception as e:
        return {'found': False, 'error': str(e)}

def test_search_api(api_key, citation):
    """Test single citation with search API"""
    url = "https://www.courtlistener.com/api/rest/v4/search/"
    headers = {'Authorization': f'Token {api_key}'}
    params = {
        "type": "o",
        "q": f'citation:"{citation}"',
        "format": "json",
        "order_by": "score desc",
        "stat_Precedential": "on"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            if results:
                best = results[0]
                return {
                    'found': True,
                    'case_name': best.get('caseName', ''),
                    'date_filed': best.get('dateFiled', ''),
                    'court': best.get('court', ''),
                    'score': best.get('score', 0)
                }
        return {'found': False}
    except Exception as e:
        return {'found': False, 'error': str(e)}

def main():
    print("Simple API Comparison Test")
    print("=" * 40)
    
    api_key = load_api_key()
    if not api_key:
        print("Error: No API key found")
        return
    
    # Test key citations
    test_citations = [
        "384 U.S. 436",  # Miranda
        "347 U.S. 483",  # Brown
        "410 U.S. 113",  # Roe
        "86 S. Ct. 1602" # Miranda parallel
    ]
    
    print(f"Testing {len(test_citations)} citations...\n")
    
    lookup_found = 0
    search_found = 0
    both_found = 0
    
    for citation in test_citations:
        print(f"Testing: {citation}")
        
        # Test citation-lookup
        lookup_result = test_citation_lookup(api_key, citation)
        time.sleep(0.5)
        
        # Test search API  
        search_result = test_search_api(api_key, citation)
        time.sleep(0.5)
        
        lookup_success = lookup_result.get('found', False)
        search_success = search_result.get('found', False)
        
        if lookup_success:
            lookup_found += 1
        if search_success:
            search_found += 1
        if lookup_success and search_success:
            both_found += 1
            
        print(f"  Citation-Lookup: {'✓' if lookup_success else '✗'}")
        if lookup_success:
            print(f"    Case: {lookup_result.get('case_name', 'Unknown')}")
            
        print(f"  Search API: {'✓' if search_success else '✗'}")
        if search_success:
            print(f"    Case: {search_result.get('case_name', 'Unknown')}")
            print(f"    Score: {search_result.get('score', 'N/A')}")
        
        # Compare if both found
        if lookup_success and search_success:
            lookup_name = lookup_result.get('case_name', '').strip()
            search_name = search_result.get('case_name', '').strip()
            if lookup_name == search_name:
                print(f"  ✓ Names match")
            else:
                print(f"  ⚠ Names differ:")
                print(f"    Lookup: {lookup_name}")
                print(f"    Search: {search_name}")
        
        print()
    
    print("SUMMARY:")
    print(f"Citation-Lookup found: {lookup_found}/{len(test_citations)}")
    print(f"Search API found: {search_found}/{len(test_citations)}")
    print(f"Both found: {both_found}/{len(test_citations)}")
    
    if lookup_found >= search_found:
        print("\n✅ RECOMMENDATION: Citation-Lookup API is sufficient")
        print("   - Equal or better coverage than Search API")
        print("   - Batch processing capability")
        print("   - Better rate limits")
    else:
        print("\n⚠️ RECOMMENDATION: Use both APIs")
        print("   - Search API finds additional cases")

if __name__ == "__main__":
    main()
