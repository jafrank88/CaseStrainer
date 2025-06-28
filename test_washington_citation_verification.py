#!/usr/bin/env python3
"""
Test Washington citation verification with CourtListener API
"""

import requests
import json
import re
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WashingtonCitationTester:
    def __init__(self):
        self.base_url = "https://www.courtlistener.com/api/rest/v4"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
    def test_citation_lookup(self, citation: str) -> Dict[str, Any]:
        """Test citation lookup with CourtListener API."""
        try:
            url = f"{self.base_url}/citation-lookup/"
            params = {'citation': citation}
            
            logger.info(f"Testing citation lookup: {citation}")
            logger.info(f"URL: {url}")
            logger.info(f"Params: {params}")
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data: {json.dumps(data, indent=2)}")
                
                if data and len(data) > 0:
                    return {
                        'citation': citation,
                        'found': True,
                        'data': data[0],
                        'status_code': response.status_code
                    }
                else:
                    return {
                        'citation': citation,
                        'found': False,
                        'data': None,
                        'status_code': response.status_code,
                        'error': 'No results returned'
                    }
            else:
                logger.error(f"API error: {response.status_code}")
                logger.error(f"Response text: {response.text}")
                return {
                    'citation': citation,
                    'found': False,
                    'data': None,
                    'status_code': response.status_code,
                    'error': f'API error: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Exception during citation lookup: {e}")
            return {
                'citation': citation,
                'found': False,
                'data': None,
                'error': str(e)
            }
    
    def test_search_api(self, citation: str) -> Dict[str, Any]:
        """Test search API with CourtListener."""
        try:
            url = f"{self.base_url}/search/"
            params = {
                'q': f'citation:"{citation}"',
                'type': 'o',  # opinions
                'stat_Precedential': 'on'
            }
            
            logger.info(f"Testing search API: {citation}")
            logger.info(f"URL: {url}")
            logger.info(f"Params: {params}")
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Search results count: {data.get('count', 0)}")
                
                if data.get('results') and len(data['results']) > 0:
                    return {
                        'citation': citation,
                        'found': True,
                        'data': data['results'][0],
                        'count': data.get('count', 0),
                        'status_code': response.status_code
                    }
                else:
                    return {
                        'citation': citation,
                        'found': False,
                        'data': None,
                        'count': data.get('count', 0),
                        'status_code': response.status_code,
                        'error': 'No search results'
                    }
            else:
                logger.error(f"Search API error: {response.status_code}")
                logger.error(f"Response text: {response.text}")
                return {
                    'citation': citation,
                    'found': False,
                    'data': None,
                    'status_code': response.status_code,
                    'error': f'Search API error: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Exception during search: {e}")
            return {
                'citation': citation,
                'found': False,
                'data': None,
                'error': str(e)
            }
    
    def test_case_name_search(self, case_name: str) -> Dict[str, Any]:
        """Test searching by case name."""
        try:
            url = f"{self.base_url}/search/"
            params = {
                'q': f'case_name:"{case_name}"',
                'type': 'o',  # opinions
                'stat_Precedential': 'on'
            }
            
            logger.info(f"Testing case name search: {case_name}")
            logger.info(f"URL: {url}")
            logger.info(f"Params: {params}")
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Case name search results count: {data.get('count', 0)}")
                
                if data.get('results') and len(data['results']) > 0:
                    return {
                        'case_name': case_name,
                        'found': True,
                        'data': data['results'][0],
                        'count': data.get('count', 0),
                        'status_code': response.status_code
                    }
                else:
                    return {
                        'case_name': case_name,
                        'found': False,
                        'data': None,
                        'count': data.get('count', 0),
                        'status_code': response.status_code,
                        'error': 'No case name results'
                    }
            else:
                logger.error(f"Case name search error: {response.status_code}")
                return {
                    'case_name': case_name,
                    'found': False,
                    'data': None,
                    'status_code': response.status_code,
                    'error': f'Case name search error: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Exception during case name search: {e}")
            return {
                'case_name': case_name,
                'found': False,
                'data': None,
                'error': str(e)
            }

def main():
    """Test Washington citation verification."""
    tester = WashingtonCitationTester()
    
    # Test the specific citation from the URL
    target_citation = "199 Wash. App. 280"
    case_name = "Doe P v. Thurston County"
    
    print("=" * 80)
    print("TESTING WASHINGTON CITATION VERIFICATION")
    print("=" * 80)
    print(f"Target citation: {target_citation}")
    print(f"Case name: {case_name}")
    print(f"CourtListener URL: https://www.courtlistener.com/opinion/4402021/doe-p-v-thurston-county/")
    print()
    
    # Test 1: Citation lookup
    print("1. Testing Citation Lookup API")
    print("-" * 40)
    lookup_result = tester.test_citation_lookup(target_citation)
    print(f"Lookup result: {json.dumps(lookup_result, indent=2)}")
    print()
    
    # Test 2: Search API with citation
    print("2. Testing Search API with citation")
    print("-" * 40)
    search_result = tester.test_search_api(target_citation)
    print(f"Search result: {json.dumps(search_result, indent=2)}")
    print()
    
    # Test 3: Search by case name
    print("3. Testing Search API with case name")
    print("-" * 40)
    case_result = tester.test_case_name_search(case_name)
    print(f"Case name search result: {json.dumps(case_result, indent=2)}")
    print()
    
    # Test 4: Try different citation formats
    print("4. Testing different citation formats")
    print("-" * 40)
    citation_variants = [
        "199 Wn. App. 280",
        "199 Wash. App. 280",
        "199 Washington App. 280",
        "199 Wn App 280",
        "199 Wash App 280"
    ]
    
    for variant in citation_variants:
        print(f"\nTesting variant: {variant}")
        variant_result = tester.test_citation_lookup(variant)
        print(f"Result: {'FOUND' if variant_result['found'] else 'NOT FOUND'}")
        if variant_result.get('error'):
            print(f"Error: {variant_result['error']}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Original citation '{target_citation}' lookup: {'SUCCESS' if lookup_result['found'] else 'FAILED'}")
    print(f"Search API with citation: {'SUCCESS' if search_result['found'] else 'FAILED'}")
    print(f"Case name search: {'SUCCESS' if case_result['found'] else 'FAILED'}")
    
    if lookup_result['found']:
        print(f"Lookup data: {json.dumps(lookup_result['data'], indent=2)}")
    elif search_result['found']:
        print(f"Search data: {json.dumps(search_result['data'], indent=2)}")
    elif case_result['found']:
        print(f"Case data: {json.dumps(case_result['data'], indent=2)}")

if __name__ == "__main__":
    main() 