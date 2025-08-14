#!/usr/bin/env python3
"""
Compare CourtListener citation-lookup API vs search API results.
This will help determine if we need both APIs or if citation-lookup is sufficient.
"""

import sys
import os
import json
import requests
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def load_api_key():
    """Load API key from config.json"""
    try:
        with open('config/config.json', 'r') as f:
            config = json.load(f)
            return config.get('COURTLISTENER_API_KEY') or config.get('courtlistener_api_key')
    except FileNotFoundError:
        print("Error: config/config.json not found")
        return None
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

def test_citation_lookup_api(api_key, citations):
    """Test citation-lookup API (batch)"""
    print("Testing Citation-Lookup API (Batch)")
    print("-" * 40)
    
    url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    headers = {
        'Authorization': f'Token {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Test with all citations in one batch
    citations_text = ' '.join(citations)
    data = {'text': citations_text}
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            print(f"Results found: {len(results)}")
            
            lookup_results = {}
            for result in results:
                citation = result.get('citation', '')
                if citation and result.get('clusters'):
                    cluster = result['clusters'][0]
                    lookup_results[citation] = {
                        'found': True,
                        'case_name': cluster.get('case_name', ''),
                        'date_filed': cluster.get('date_filed', ''),
                        'absolute_url': cluster.get('absolute_url', ''),
                        'court': cluster.get('court', ''),
                        'docket_id': cluster.get('docket_id', ''),
                        'api': 'citation-lookup'
                    }
                else:
                    lookup_results[citation] = {
                        'found': False,
                        'api': 'citation-lookup'
                    }
            
            return lookup_results
        else:
            print(f"Error: {response.text}")
            return {}
            
    except Exception as e:
        print(f"Error: {e}")
        return {}

def test_search_api(api_key, citations):
    """Test search API (individual)"""
    print("\nTesting Search API (Individual)")
    print("-" * 40)
    
    search_results = {}
    
    for citation in citations:
        print(f"Searching for: {citation}")
        
        url = "https://www.courtlistener.com/api/rest/v4/search/"
        headers = {'Authorization': f'Token {api_key}'}
        params = {
            "type": "o",  # opinions
            "q": f'citation:"{citation}"',
            "format": "json",
            "order_by": "score desc",
            "stat_Precedential": "on"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if results:
                    best_result = results[0]  # Highest score
                    search_results[citation] = {
                        'found': True,
                        'case_name': best_result.get('caseName', ''),
                        'date_filed': best_result.get('dateFiled', ''),
                        'absolute_url': best_result.get('absolute_url', ''),
                        'court': best_result.get('court', ''),
                        'docket_id': best_result.get('docket', ''),
                        'score': best_result.get('score', 0),
                        'api': 'search'
                    }
                    print(f"  ✓ Found: {best_result.get('caseName', 'Unknown')}")
                else:
                    search_results[citation] = {
                        'found': False,
                        'api': 'search'
                    }
                    print(f"  ✗ Not found")
            else:
                print(f"  Error: {response.status_code}")
                search_results[citation] = {
                    'found': False,
                    'error': f"HTTP {response.status_code}",
                    'api': 'search'
                }
            
            # Rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  Error: {e}")
            search_results[citation] = {
                'found': False,
                'error': str(e),
                'api': 'search'
            }
    
    return search_results

def compare_results(lookup_results, search_results, citations):
    """Compare results from both APIs"""
    print("\n" + "=" * 70)
    print("COMPARISON RESULTS")
    print("=" * 70)
    
    # Summary statistics
    lookup_found = sum(1 for r in lookup_results.values() if r.get('found', False))
    search_found = sum(1 for r in search_results.values() if r.get('found', False))
    
    print(f"\nSummary:")
    print(f"  Citation-Lookup API: {lookup_found}/{len(citations)} found ({lookup_found/len(citations)*100:.1f}%)")
    print(f"  Search API: {search_found}/{len(citations)} found ({search_found/len(citations)*100:.1f}%)")
    
    # Detailed comparison
    print(f"\nDetailed Comparison:")
    print("-" * 50)
    
    both_found = 0
    only_lookup = 0
    only_search = 0
    neither_found = 0
    
    for citation in citations:
        lookup_result = lookup_results.get(citation, {})
        search_result = search_results.get(citation, {})
        
        lookup_found = lookup_result.get('found', False)
        search_found = search_result.get('found', False)
        
        print(f"\n{citation}:")
        
        if lookup_found and search_found:
            both_found += 1
            print(f"  ✓ Both APIs found results")
            
            # Compare case names
            lookup_name = lookup_result.get('case_name', '')
            search_name = search_result.get('case_name', '')
            
            print(f"  Citation-Lookup: {lookup_name}")
            print(f"  Search API: {search_name}")
            
            if lookup_name.strip() == search_name.strip():
                print(f"  📝 Case names MATCH")
            else:
                print(f"  ⚠️  Case names DIFFER")
            
            # Compare dates
            lookup_date = lookup_result.get('date_filed', '')
            search_date = search_result.get('date_filed', '')
            
            if lookup_date == search_date:
                print(f"  📅 Dates match: {lookup_date}")
            else:
                print(f"  ⚠️  Dates differ: {lookup_date} vs {search_date}")
                
        elif lookup_found and not search_found:
            only_lookup += 1
            print(f"  ✓ Only Citation-Lookup found: {lookup_result.get('case_name', 'Unknown')}")
            
        elif not lookup_found and search_found:
            only_search += 1
            print(f"  ✓ Only Search API found: {search_result.get('case_name', 'Unknown')}")
            
        else:
            neither_found += 1
            print(f"  ✗ Neither API found results")
    
    print(f"\nResult Categories:")
    print(f"  Both found: {both_found}")
    print(f"  Only Citation-Lookup: {only_lookup}")
    print(f"  Only Search API: {only_search}")
    print(f"  Neither found: {neither_found}")
    
    # Recommendations
    print(f"\nRecommendations:")
    print("-" * 20)
    
    if only_search == 0:
        print("✅ Citation-Lookup API finds all cases that Search API finds")
        print("✅ RECOMMENDATION: Use only Citation-Lookup API (batch, efficient)")
    elif only_search > 0:
        print(f"⚠️  Search API finds {only_search} additional cases")
        print("⚠️  RECOMMENDATION: Use Citation-Lookup first, then Search API for failures")
    
    if only_lookup > 0:
        print(f"✅ Citation-Lookup finds {only_lookup} cases that Search API misses")
        print("✅ Citation-Lookup API has better coverage")

def main():
    print("CourtListener API Comparison Test")
    print("=" * 50)
    
    # Load API key
    api_key = load_api_key()
    if not api_key:
        print("Error: Could not load API key from config/config.json")
        return
    
    print(f"API Key loaded: {api_key[:10]}...")
    
    # Test citations - mix of well-known and potentially obscure
    test_citations = [
        "384 U.S. 436",      # Miranda v. Arizona (well-known)
        "347 U.S. 483",      # Brown v. Board (well-known)
        "372 U.S. 335",      # Gideon v. Wainwright (well-known)
        "410 U.S. 113",      # Roe v. Wade (well-known)
        "163 U.S. 537",      # Plessy v. Ferguson (historical)
        "86 S. Ct. 1602",    # Miranda parallel citation
        "74 S. Ct. 686",     # Brown parallel citation
        "123 F.3d 456",      # Potentially less common federal
        "789 P.2d 123",      # State court citation
    ]
    
    print(f"\nTesting {len(test_citations)} citations:")
    for citation in test_citations:
        print(f"  - {citation}")
    print()
    
    # Test both APIs
    lookup_results = test_citation_lookup_api(api_key, test_citations)
    search_results = test_search_api(api_key, test_citations)
    
    # Compare results
    compare_results(lookup_results, search_results, test_citations)

if __name__ == "__main__":
    main()
