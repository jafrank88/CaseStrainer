#!/usr/bin/env python3
"""
Analyze the efficiency and necessity of citation-lookup API vs direct search/opinion APIs
"""

import os
import sys
import requests
import json
import time

def get_api_key():
    """Get CourtListener API key"""
    try:
        with open('.env', 'r') as f:
            for line in f:
                if 'COURTLISTENER_API_KEY=' in line:
                    return line.split('=')[1].strip().strip('"\'')
    except:
        pass
    return os.getenv('COURTLISTENER_API_KEY')

def test_citation_lookup_api(api_key, citation):
    """Test citation-lookup API"""
    
    print(f"TESTING CITATION-LOOKUP API")
    print("-" * 30)
    
    url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    headers = {"Authorization": f"Token {api_key}"}
    data = {"text": citation}
    
    start_time = time.time()
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response_time = time.time() - start_time
        
        print(f"Response time: {response_time:.2f}s")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            print(f"Results: {len(results)}")
            
            valid_clusters = 0
            for result in results:
                if result.get('status') != 404 and result.get('clusters'):
                    for cluster in result.get('clusters', []):
                        case_name = cluster.get('case_name')
                        absolute_url = cluster.get('absolute_url')
                        if case_name and case_name.strip() and absolute_url and absolute_url.strip():
                            valid_clusters += 1
                            print(f"  Valid cluster: {case_name}")
                        else:
                            print(f"  Invalid cluster: case_name='{case_name}', url='{absolute_url}'")
            
            return {
                'success': True,
                'response_time': response_time,
                'valid_clusters': valid_clusters,
                'total_results': len(results)
            }
        else:
            print(f"Error: {response.status_code}")
            return {'success': False, 'response_time': response_time}
            
    except Exception as e:
        response_time = time.time() - start_time
        print(f"Exception: {str(e)}")
        return {'success': False, 'response_time': response_time, 'error': str(e)}

def test_search_api(api_key, citation):
    """Test search API"""
    
    print(f"\nTESTING SEARCH API")
    print("-" * 20)
    
    url = "https://www.courtlistener.com/api/rest/v4/search/"
    headers = {"Authorization": f"Token {api_key}"}
    params = {
        "type": "o",  # opinions
        "q": citation,
        "format": "json"
    }
    
    start_time = time.time()
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response_time = time.time() - start_time
        
        print(f"Response time: {response_time:.2f}s")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results_count = data.get('count', 0)
            results = data.get('results', [])
            
            print(f"Results count: {results_count}")
            print(f"Results returned: {len(results)}")
            
            valid_results = 0
            for result in results:
                case_name = result.get('caseName')
                absolute_url = result.get('absolute_url')
                if case_name and case_name.strip() and absolute_url and absolute_url.strip():
                    valid_results += 1
                    print(f"  Valid result: {case_name}")
                else:
                    print(f"  Invalid result: caseName='{case_name}', url='{absolute_url}'")
            
            return {
                'success': True,
                'response_time': response_time,
                'valid_results': valid_results,
                'total_count': results_count,
                'returned_results': len(results)
            }
        else:
            print(f"Error: {response.status_code}")
            return {'success': False, 'response_time': response_time}
            
    except Exception as e:
        response_time = time.time() - start_time
        print(f"Exception: {str(e)}")
        return {'success': False, 'response_time': response_time, 'error': str(e)}

def analyze_api_efficiency():
    """Analyze which API approach is most efficient and accurate"""
    
    api_key = get_api_key()
    if not api_key:
        print("No API key found")
        return
    
    # Test citations - mix of valid and potentially problematic ones
    test_citations = [
        "654 F. Supp. 2d 321",  # The problematic one
        "147 Wn. App. 891",     # Another from our test
        "456 F.3d 789",         # Federal appeals
        "123 Wn.2d 456",        # State supreme court
        "999 F.3d 999"          # Likely non-existent
    ]
    
    print("API EFFICIENCY AND ACCURACY ANALYSIS")
    print("=" * 45)
    
    results = {}
    
    for citation in test_citations:
        print(f"\n{'='*60}")
        print(f"TESTING CITATION: {citation}")
        print(f"{'='*60}")
        
        # Test citation-lookup API
        lookup_result = test_citation_lookup_api(api_key, citation)
        
        # Test search API
        search_result = test_search_api(api_key, citation)
        
        results[citation] = {
            'lookup': lookup_result,
            'search': search_result
        }
        
        # Brief pause between citations
        time.sleep(1)
    
    # Analysis
    print(f"\n{'='*60}")
    print("EFFICIENCY ANALYSIS")
    print(f"{'='*60}")
    
    lookup_times = []
    search_times = []
    lookup_accuracy = []
    search_accuracy = []
    
    for citation, data in results.items():
        print(f"\nCitation: {citation}")
        
        if data['lookup']['success']:
            lookup_time = data['lookup']['response_time']
            lookup_valid = data['lookup']['valid_clusters']
            lookup_times.append(lookup_time)
            lookup_accuracy.append(lookup_valid > 0)
            print(f"  Citation-lookup: {lookup_time:.2f}s, {lookup_valid} valid clusters")
        else:
            print(f"  Citation-lookup: FAILED")
        
        if data['search']['success']:
            search_time = data['search']['response_time']
            search_valid = data['search']['valid_results']
            search_times.append(search_time)
            search_accuracy.append(search_valid > 0)
            print(f"  Search API: {search_time:.2f}s, {search_valid} valid results")
        else:
            print(f"  Search API: FAILED")
    
    # Summary
    print(f"\nSUMMARY:")
    print("-" * 20)
    
    if lookup_times:
        avg_lookup_time = sum(lookup_times) / len(lookup_times)
        lookup_success_rate = sum(lookup_accuracy) / len(lookup_accuracy) * 100
        print(f"Citation-lookup API:")
        print(f"  Average response time: {avg_lookup_time:.2f}s")
        print(f"  Success rate: {lookup_success_rate:.1f}%")
    
    if search_times:
        avg_search_time = sum(search_times) / len(search_times)
        search_success_rate = sum(search_accuracy) / len(search_accuracy) * 100
        print(f"Search API:")
        print(f"  Average response time: {avg_search_time:.2f}s")
        print(f"  Success rate: {search_success_rate:.1f}%")
    
    # Recommendation
    print(f"\nRECOMMENDATION:")
    print("-" * 20)
    
    if lookup_times and search_times:
        if avg_lookup_time < avg_search_time and lookup_success_rate >= search_success_rate:
            print("✅ KEEP citation-lookup API - faster and equally accurate")
        elif avg_search_time < avg_lookup_time and search_success_rate >= lookup_success_rate:
            print("❌ REPLACE citation-lookup with search API - faster and equally/more accurate")
        elif lookup_success_rate > search_success_rate:
            print("⚖️  KEEP citation-lookup API - more accurate despite speed difference")
        elif search_success_rate > lookup_success_rate:
            print("⚖️  REPLACE citation-lookup with search API - more accurate despite speed difference")
        else:
            print("🤔 MIXED RESULTS - further analysis needed")
    
    print(f"\nNEXT STEPS:")
    print("-" * 15)
    print("1. If citation-lookup is inefficient, replace with search API")
    print("2. Implement cross-validation for critical citations")
    print("3. Add stricter validation regardless of API choice")
    print("4. Consider hybrid approach: fast API first, cross-validate on uncertain results")

if __name__ == "__main__":
    analyze_api_efficiency()
