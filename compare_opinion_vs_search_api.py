#!/usr/bin/env python3
"""
Comprehensive comparison between CourtListener Opinion API and Search API
"""

import os
import sys
import requests
import json
import time
from typing import Dict, List, Optional

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

class APIComparator:
    """Compare Opinion API vs Search API performance and capabilities"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"Authorization": f"Token {api_key}"}
    
    def test_opinion_api(self, opinion_id: str) -> Dict:
        """Test Opinion API with specific opinion ID"""
        
        print(f"TESTING OPINION API")
        print("-" * 25)
        print(f"Opinion ID: {opinion_id}")
        
        result = {
            'api_type': 'opinion',
            'success': False,
            'response_time': 0,
            'data_quality': {},
            'error': None
        }
        
        start_time = time.time()
        
        try:
            url = f"https://www.courtlistener.com/api/rest/v4/opinions/{opinion_id}/"
            
            response = requests.get(url, headers=self.headers, timeout=30)
            result['response_time'] = time.time() - start_time
            
            print(f"Response time: {result['response_time']:.2f}s")
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                result['success'] = True
                result['raw_data'] = data
                
                # Analyze data quality
                cluster = data.get('cluster')
                if cluster:
                    case_name = cluster.get('case_name')
                    date_filed = cluster.get('date_filed')
                    absolute_url = cluster.get('absolute_url')
                    
                    result['data_quality'] = {
                        'has_cluster': True,
                        'has_case_name': bool(case_name and case_name.strip()),
                        'has_date': bool(date_filed),
                        'has_url': bool(absolute_url and absolute_url.strip()),
                        'case_name': case_name,
                        'date_filed': date_filed,
                        'url': f"https://www.courtlistener.com{absolute_url}" if absolute_url else None
                    }
                    
                    print(f"Cluster found: YES")
                    print(f"Case name: '{case_name}'")
                    print(f"Date filed: '{date_filed}'")
                    print(f"URL: '{absolute_url}'")
                    
                    # Data completeness score
                    completeness = sum([
                        result['data_quality']['has_case_name'],
                        result['data_quality']['has_date'],
                        result['data_quality']['has_url']
                    ]) / 3.0
                    result['data_quality']['completeness_score'] = completeness
                    print(f"Data completeness: {completeness:.1%}")
                    
                else:
                    result['data_quality'] = {
                        'has_cluster': False,
                        'has_case_name': False,
                        'has_date': False,
                        'has_url': False,
                        'completeness_score': 0.0
                    }
                    print(f"Cluster found: NO")
            
            elif response.status_code == 404:
                print(f"Opinion not found (404)")
                result['error'] = 'Opinion not found'
            else:
                print(f"Error: {response.status_code}")
                result['error'] = f"HTTP {response.status_code}"
        
        except Exception as e:
            result['response_time'] = time.time() - start_time
            result['error'] = str(e)
            print(f"Exception: {str(e)}")
        
        return result
    
    def test_search_api(self, citation: str) -> Dict:
        """Test Search API with citation query"""
        
        print(f"\nTESTING SEARCH API")
        print("-" * 20)
        print(f"Citation: {citation}")
        
        result = {
            'api_type': 'search',
            'success': False,
            'response_time': 0,
            'data_quality': {},
            'error': None
        }
        
        start_time = time.time()
        
        try:
            url = "https://www.courtlistener.com/api/rest/v4/search/"
            params = {
                "type": "o",  # opinions
                "q": citation,
                "format": "json"
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            result['response_time'] = time.time() - start_time
            
            print(f"Response time: {result['response_time']:.2f}s")
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                result['success'] = True
                result['raw_data'] = data
                
                results_count = data.get('count', 0)
                results = data.get('results', [])
                
                print(f"Total results: {results_count}")
                print(f"Returned results: {len(results)}")
                
                if results:
                    # Analyze first (best) result
                    best_result = results[0]
                    
                    case_name = best_result.get('caseName')
                    date_filed = best_result.get('dateFiled')
                    absolute_url = best_result.get('absolute_url')
                    
                    result['data_quality'] = {
                        'total_results': results_count,
                        'returned_results': len(results),
                        'has_case_name': bool(case_name and case_name.strip()),
                        'has_date': bool(date_filed),
                        'has_url': bool(absolute_url and absolute_url.strip()),
                        'case_name': case_name,
                        'date_filed': date_filed,
                        'url': f"https://www.courtlistener.com{absolute_url}" if absolute_url else None
                    }
                    
                    print(f"Best result:")
                    print(f"  Case name: '{case_name}'")
                    print(f"  Date filed: '{date_filed}'")
                    print(f"  URL: '{absolute_url}'")
                    
                    # Data completeness score
                    completeness = sum([
                        result['data_quality']['has_case_name'],
                        result['data_quality']['has_date'],
                        result['data_quality']['has_url']
                    ]) / 3.0
                    result['data_quality']['completeness_score'] = completeness
                    print(f"  Data completeness: {completeness:.1%}")
                    
                else:
                    result['data_quality'] = {
                        'total_results': results_count,
                        'returned_results': 0,
                        'has_case_name': False,
                        'has_date': False,
                        'has_url': False,
                        'completeness_score': 0.0
                    }
                    print(f"No results returned")
            
            else:
                print(f"Error: {response.status_code}")
                result['error'] = f"HTTP {response.status_code}"
        
        except Exception as e:
            result['response_time'] = time.time() - start_time
            result['error'] = str(e)
            print(f"Exception: {str(e)}")
        
        return result
    
    def compare_apis(self, test_cases: List[Dict]) -> Dict:
        """Compare both APIs across multiple test cases"""
        
        print(f"\n{'='*70}")
        print("COMPREHENSIVE API COMPARISON")
        print(f"{'='*70}")
        
        comparison_results = {
            'opinion_api': {
                'successes': 0,
                'failures': 0,
                'avg_response_time': 0,
                'avg_completeness': 0,
                'response_times': [],
                'completeness_scores': []
            },
            'search_api': {
                'successes': 0,
                'failures': 0,
                'avg_response_time': 0,
                'avg_completeness': 0,
                'response_times': [],
                'completeness_scores': []
            },
            'detailed_results': []
        }
        
        for i, test_case in enumerate(test_cases):
            print(f"\n{'-'*60}")
            print(f"TEST CASE {i+1}: {test_case['name']}")
            print(f"{'-'*60}")
            
            case_result = {
                'name': test_case['name'],
                'opinion_id': test_case.get('opinion_id'),
                'citation': test_case.get('citation'),
                'opinion_result': None,
                'search_result': None
            }
            
            # Test Opinion API (if opinion_id provided)
            if test_case.get('opinion_id'):
                opinion_result = self.test_opinion_api(test_case['opinion_id'])
                case_result['opinion_result'] = opinion_result
                
                if opinion_result['success']:
                    comparison_results['opinion_api']['successes'] += 1
                    comparison_results['opinion_api']['response_times'].append(opinion_result['response_time'])
                    comparison_results['opinion_api']['completeness_scores'].append(
                        opinion_result['data_quality'].get('completeness_score', 0)
                    )
                else:
                    comparison_results['opinion_api']['failures'] += 1
            
            # Test Search API (if citation provided)
            if test_case.get('citation'):
                search_result = self.test_search_api(test_case['citation'])
                case_result['search_result'] = search_result
                
                if search_result['success']:
                    comparison_results['search_api']['successes'] += 1
                    comparison_results['search_api']['response_times'].append(search_result['response_time'])
                    comparison_results['search_api']['completeness_scores'].append(
                        search_result['data_quality'].get('completeness_score', 0)
                    )
                else:
                    comparison_results['search_api']['failures'] += 1
            
            comparison_results['detailed_results'].append(case_result)
            
            # Brief pause between tests
            time.sleep(0.5)
        
        # Calculate averages
        if comparison_results['opinion_api']['response_times']:
            comparison_results['opinion_api']['avg_response_time'] = sum(
                comparison_results['opinion_api']['response_times']
            ) / len(comparison_results['opinion_api']['response_times'])
            
            comparison_results['opinion_api']['avg_completeness'] = sum(
                comparison_results['opinion_api']['completeness_scores']
            ) / len(comparison_results['opinion_api']['completeness_scores'])
        
        if comparison_results['search_api']['response_times']:
            comparison_results['search_api']['avg_response_time'] = sum(
                comparison_results['search_api']['response_times']
            ) / len(comparison_results['search_api']['response_times'])
            
            comparison_results['search_api']['avg_completeness'] = sum(
                comparison_results['search_api']['completeness_scores']
            ) / len(comparison_results['search_api']['completeness_scores'])
        
        return comparison_results
    
    def print_comparison_summary(self, results: Dict):
        """Print comprehensive comparison summary"""
        
        print(f"\n{'='*70}")
        print("API COMPARISON SUMMARY")
        print(f"{'='*70}")
        
        opinion_stats = results['opinion_api']
        search_stats = results['search_api']
        
        print(f"\nOPINION API PERFORMANCE:")
        print(f"  Success rate: {opinion_stats['successes']}/{opinion_stats['successes'] + opinion_stats['failures']} "
              f"({opinion_stats['successes']/(opinion_stats['successes'] + opinion_stats['failures'])*100:.1f}%)")
        print(f"  Avg response time: {opinion_stats['avg_response_time']:.2f}s")
        print(f"  Avg data completeness: {opinion_stats['avg_completeness']:.1%}")
        
        print(f"\nSEARCH API PERFORMANCE:")
        print(f"  Success rate: {search_stats['successes']}/{search_stats['successes'] + search_stats['failures']} "
              f"({search_stats['successes']/(search_stats['successes'] + search_stats['failures'])*100:.1f}%)")
        print(f"  Avg response time: {search_stats['avg_response_time']:.2f}s")
        print(f"  Avg data completeness: {search_stats['avg_completeness']:.1%}")
        
        # Recommendations
        print(f"\nRECOMMENDATIONS:")
        print("-" * 20)
        
        if search_stats['avg_response_time'] < opinion_stats['avg_response_time']:
            print("✅ SPEED: Search API is faster")
        else:
            print("✅ SPEED: Opinion API is faster")
        
        if search_stats['avg_completeness'] > opinion_stats['avg_completeness']:
            print("✅ DATA QUALITY: Search API has more complete data")
        else:
            print("✅ DATA QUALITY: Opinion API has more complete data")
        
        search_success_rate = search_stats['successes']/(search_stats['successes'] + search_stats['failures']) if (search_stats['successes'] + search_stats['failures']) > 0 else 0
        opinion_success_rate = opinion_stats['successes']/(opinion_stats['successes'] + opinion_stats['failures']) if (opinion_stats['successes'] + opinion_stats['failures']) > 0 else 0
        
        if search_success_rate > opinion_success_rate:
            print("✅ RELIABILITY: Search API has higher success rate")
        else:
            print("✅ RELIABILITY: Opinion API has higher success rate")
        
        print(f"\nOVERALL RECOMMENDATION:")
        print("-" * 30)
        
        # Calculate overall scores
        search_score = (search_success_rate * 0.4 + 
                       (1 - search_stats['avg_response_time']/10) * 0.3 + 
                       search_stats['avg_completeness'] * 0.3)
        
        opinion_score = (opinion_success_rate * 0.4 + 
                        (1 - opinion_stats['avg_response_time']/10) * 0.3 + 
                        opinion_stats['avg_completeness'] * 0.3)
        
        if search_score > opinion_score:
            print("🎯 USE SEARCH API as primary verification method")
            print("   - Better overall performance and reliability")
            print("   - Use Opinion API for cross-validation when needed")
        else:
            print("🎯 USE OPINION API as primary verification method")
            print("   - Better overall performance and reliability")
            print("   - Use Search API for cross-validation when needed")

def main():
    """Main comparison function"""
    
    api_key = get_api_key()
    if not api_key:
        print("No API key found")
        return
    
    comparator = APIComparator(api_key)
    
    # Test cases with both opinion IDs and citations
    test_cases = [
        {
            'name': 'Problematic Citation (False Positive)',
            'opinion_id': '1689955',  # From our earlier investigation
            'citation': '654 F. Supp. 2d 321'
        },
        {
            'name': 'Washington State Citation',
            'citation': '147 Wn. App. 891'
        },
        {
            'name': 'Federal Appeals Citation',
            'citation': '456 F.3d 789'
        },
        {
            'name': 'Supreme Court Citation',
            'citation': '123 S. Ct. 456'
        },
        {
            'name': 'Non-existent Citation',
            'citation': '999 F.3d 999'
        }
    ]
    
    # Run comprehensive comparison
    results = comparator.compare_apis(test_cases)
    
    # Print detailed summary
    comparator.print_comparison_summary(results)
    
    print(f"\n{'='*70}")
    print("DETAILED ANALYSIS FOR CITATION VERIFICATION")
    print(f"{'='*70}")
    
    print("\nKEY FINDINGS:")
    print("1. Data Accuracy: Which API provides more accurate case information?")
    print("2. Coverage: Which API finds more legitimate citations?")
    print("3. False Positives: Which API is less likely to return invalid data?")
    print("4. Performance: Which API responds faster and more reliably?")
    print("5. Use Case: Which API is better for automated citation verification?")

if __name__ == "__main__":
    main()
