#!/usr/bin/env python3
"""
Enhanced API Integration for Complex Citations

This module provides enhanced integration with CourtListener API
to properly handle complex citation strings with parallel citations,
case history, and docket numbers.
"""

import requests
import logging
import json
import re
from typing import Dict, List, Optional, Any
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

class EnhancedCourtListenerAPI:
    """Enhanced CourtListener API integration for complex citations."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.courtlistener.com/api/rest/v3"
        self.headers = {
            'Authorization': f'Token {api_key}',
            'Content-Type': 'application/json'
        }
    
    def verify_complex_citation(self, citation_data: Dict) -> Dict[str, Any]:
        """Verify a complex citation using multiple strategies."""
        results = {
            'citation': citation_data.get('full_text', ''),
            'is_complex': citation_data.get('is_complex', False),
            'verification_strategies': [],
            'best_result': None,
            'all_results': []
        }
        
        # Strategy 1: Try primary citation
        if citation_data.get('primary_citation'):
            result = self._verify_single_citation(citation_data['primary_citation'])
            results['verification_strategies'].append({
                'strategy': 'primary_citation',
                'citation': citation_data['primary_citation'],
                'result': result
            })
            results['all_results'].append(result)
        
        # Strategy 2: Try parallel citations
        for parallel in citation_data.get('parallel_citations', []):
            result = self._verify_single_citation(parallel)
            results['verification_strategies'].append({
                'strategy': 'parallel_citation',
                'citation': parallel,
                'result': result
            })
            results['all_results'].append(result)
        
        # Strategy 3: Try with case name
        if citation_data.get('case_name'):
            for citation_text in [citation_data.get('primary_citation')] + citation_data.get('parallel_citations', []):
                if citation_text:
                    result = self._verify_with_case_name(citation_data['case_name'], citation_text)
                    results['verification_strategies'].append({
                        'strategy': 'with_case_name',
                        'case_name': citation_data['case_name'],
                        'citation': citation_text,
                        'result': result
                    })
                    results['all_results'].append(result)
        
        # Strategy 4: Try docket number if available
        for docket in citation_data.get('docket_numbers', []):
            result = self._verify_docket_number(docket)
            results['verification_strategies'].append({
                'strategy': 'docket_number',
                'docket': docket,
                'result': result
            })
            results['all_results'].append(result)
        
        # Strategy 5: Try flexible search with full citation text
        result = self._flexible_search(citation_data['full_text'])
        results['verification_strategies'].append({
            'strategy': 'flexible_search',
            'full_text': citation_data['full_text'],
            'result': result
        })
        results['all_results'].append(result)
        
        # Find best result
        best_result = self._find_best_result(results['all_results'])
        results['best_result'] = best_result
        
        return results
    
    def _verify_single_citation(self, citation: str) -> Dict[str, Any]:
        """Verify a single citation using CourtListener citation lookup."""
        try:
            # Clean the citation
            clean_citation = self._clean_citation(citation)
            
            # Make API request
            url = f"{self.base_url}/citation-lookup/"
            params = {
                'citation': clean_citation
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    # Found citation
                    citation_info = data[0]
                    return {
                        'citation': citation,
                        'verified': True,
                        'source': 'CourtListener API',
                        'confidence': 0.9,
                        'details': citation_info,
                        'error': None
                    }
                else:
                    return {
                        'citation': citation,
                        'verified': False,
                        'source': 'CourtListener API',
                        'confidence': 0.0,
                        'error': 'Citation not found in database'
                    }
            else:
                return {
                    'citation': citation,
                    'verified': False,
                    'source': 'CourtListener API',
                    'confidence': 0.0,
                    'error': f'API error: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Error verifying citation '{citation}': {e}")
            return {
                'citation': citation,
                'verified': False,
                'source': 'CourtListener API',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _verify_with_case_name(self, case_name: str, citation: str) -> Dict[str, Any]:
        """Verify citation with case name using CourtListener search."""
        try:
            # Clean inputs
            clean_case_name = self._clean_case_name(case_name)
            clean_citation = self._clean_citation(citation)
            
            # Search for cases with the case name
            url = f"{self.base_url}/search/"
            params = {
                'q': f'case_name:"{clean_case_name}" AND citation:"{clean_citation}"',
                'type': 'o',  # opinions
                'stat_Precedential': 'on'
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results') and len(data['results']) > 0:
                    # Found matching case
                    case_info = data['results'][0]
                    return {
                        'citation': citation,
                        'case_name': case_name,
                        'verified': True,
                        'source': 'CourtListener Search',
                        'confidence': 0.95,
                        'details': case_info,
                        'error': None
                    }
                else:
                    return {
                        'citation': citation,
                        'case_name': case_name,
                        'verified': False,
                        'source': 'CourtListener Search',
                        'confidence': 0.0,
                        'error': 'No matching case found'
                    }
            else:
                return {
                    'citation': citation,
                    'case_name': case_name,
                    'verified': False,
                    'source': 'CourtListener Search',
                    'confidence': 0.0,
                    'error': f'API error: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Error verifying citation with case name: {e}")
            return {
                'citation': citation,
                'case_name': case_name,
                'verified': False,
                'source': 'CourtListener Search',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _verify_docket_number(self, docket: str) -> Dict[str, Any]:
        """Verify using docket number."""
        try:
            # Clean docket number
            clean_docket = self._clean_docket_number(docket)
            
            # Search for cases with the docket number
            url = f"{self.base_url}/search/"
            params = {
                'q': f'docket_number:"{clean_docket}"',
                'type': 'o',  # opinions
                'stat_Precedential': 'on'
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results') and len(data['results']) > 0:
                    # Found matching case
                    case_info = data['results'][0]
                    return {
                        'docket': docket,
                        'verified': True,
                        'source': 'CourtListener Docket Search',
                        'confidence': 0.9,
                        'details': case_info,
                        'error': None
                    }
                else:
                    return {
                        'docket': docket,
                        'verified': False,
                        'source': 'CourtListener Docket Search',
                        'confidence': 0.0,
                        'error': 'No matching docket found'
                    }
            else:
                return {
                    'docket': docket,
                    'verified': False,
                    'source': 'CourtListener Docket Search',
                    'confidence': 0.0,
                    'error': f'API error: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Error verifying docket number: {e}")
            return {
                'docket': docket,
                'verified': False,
                'source': 'CourtListener Docket Search',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _flexible_search(self, full_text: str) -> Dict[str, Any]:
        """Perform flexible search with the full citation text."""
        try:
            # Extract key components for search
            search_terms = self._extract_search_terms(full_text)
            
            # Build search query
            query_parts = []
            if search_terms.get('case_name'):
                query_parts.append(f'case_name:"{search_terms["case_name"]}"')
            if search_terms.get('citations'):
                for citation in search_terms['citations']:
                    query_parts.append(f'citation:"{citation}"')
            if search_terms.get('year'):
                query_parts.append(f'dateFiled:{search_terms["year"]}')
            
            query = ' AND '.join(query_parts) if query_parts else f'"{full_text[:100]}"'
            
            # Search
            url = f"{self.base_url}/search/"
            params = {
                'q': query,
                'type': 'o',  # opinions
                'stat_Precedential': 'on'
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results') and len(data['results']) > 0:
                    # Found potential matches
                    case_info = data['results'][0]
                    return {
                        'full_text': full_text,
                        'verified': True,
                        'source': 'CourtListener Flexible Search',
                        'confidence': 0.8,
                        'details': case_info,
                        'error': None
                    }
                else:
                    return {
                        'full_text': full_text,
                        'verified': False,
                        'source': 'CourtListener Flexible Search',
                        'confidence': 0.0,
                        'error': 'No matches found'
                    }
            else:
                return {
                    'full_text': full_text,
                    'verified': False,
                    'source': 'CourtListener Flexible Search',
                    'confidence': 0.0,
                    'error': f'API error: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Error in flexible search: {e}")
            return {
                'full_text': full_text,
                'verified': False,
                'source': 'CourtListener Flexible Search',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _clean_citation(self, citation: str) -> str:
        """Clean citation for API search."""
        # Remove extra spaces and normalize
        citation = re.sub(r'\s+', ' ', citation.strip())
        return citation
    
    def _clean_case_name(self, case_name: str) -> str:
        """Clean case name for API search."""
        # Remove extra spaces and normalize
        case_name = re.sub(r'\s+', ' ', case_name.strip())
        return case_name
    
    def _clean_docket_number(self, docket: str) -> str:
        """Clean docket number for API search."""
        # Remove extra spaces and normalize
        docket = re.sub(r'\s+', '', docket.strip())
        return docket
    
    def _extract_search_terms(self, text: str) -> Dict[str, Any]:
        """Extract search terms from full citation text."""
        terms = {
            'case_name': None,
            'citations': [],
            'year': None
        }
        
        # Extract case name (simplified)
        case_match = re.search(r'([A-Z][A-Za-z\s\.,&\'\"\(\)]+v\.\s+[A-Z][A-Za-z\s\.,&\'\"\(\)]+?)(?=\s*[,;]|\s*\d+\s+[A-Z])', text)
        if case_match:
            terms['case_name'] = case_match.group(1).strip()
        
        # Extract citations
        citation_patterns = [
            r'\b(\d+)\s+Wn\.\s*App\.\s+(\d+)\b',
            r'\b(\d+)\s+P\.3d\s+(\d+)\b',
            r'\b(\d+)\s+P\.2d\s+(\d+)\b',
        ]
        
        for pattern in citation_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                volume, page = match.groups()
                citation = f"{volume} {pattern.replace(r'\b(\d+)\s+', '').replace(r'\s+(\d+)\b', '').replace('\\', '')} {page}"
                terms['citations'].append(citation)
        
        # Extract year
        year_match = re.search(r'\((\d{4})\)', text)
        if year_match:
            terms['year'] = year_match.group(1)
        
        return terms
    
    def _find_best_result(self, results: List[Dict]) -> Optional[Dict]:
        """Find the best verification result."""
        if not results:
            return None
        
        # Sort by confidence and verification status
        sorted_results = sorted(results, key=lambda x: (x.get('verified', False), x.get('confidence', 0)), reverse=True)
        return sorted_results[0]

# Example usage and testing
if __name__ == "__main__":
    # Load API key from config
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        api_key = config.get('COURTLISTENER_API_KEY')
    except Exception as e:
        print(f"Warning: Could not load API key from config: {e}")
        api_key = None
    
    if not api_key:
        print("No API key available. Please set COURTLISTENER_API_KEY in config.json")
        exit(1)
    
    # Initialize the enhanced API
    api = EnhancedCourtListenerAPI(api_key)
    
    # Test with your complex citation
    test_citation = {
        'full_text': 'John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017) (Doe I), modified on other grounds on remand, No. 48000-0-II (Wash. Ct. App. Oct. 2, 2018) (Doe II) (unpublished)',
        'case_name': 'John Doe P v. Thurston County',
        'primary_citation': '199 Wn. App. 280',
        'parallel_citations': ['399 P.3d 1195'],
        'pinpoint_pages': ['283'],
        'docket_numbers': ['48000-0-II'],
        'case_history': ['Doe I'],
        'publication_status': 'unpublished',
        'year': '2017',
        'is_complex': True
    }
    
    print("=== Enhanced CourtListener API Testing ===")
    print(f"Testing citation: {test_citation['full_text']}")
    print()
    
    # Verify the citation
    results = api.verify_complex_citation(test_citation)
    
    print("=== Verification Results ===")
    print(f"Best Result: {results['best_result']}")
    print()
    
    print("=== All Strategies ===")
    for strategy in results['verification_strategies']:
        print(f"Strategy: {strategy['strategy']}")
        if 'citation' in strategy:
            print(f"  Citation: {strategy['citation']}")
        if 'case_name' in strategy:
            print(f"  Case Name: {strategy['case_name']}")
        if 'docket' in strategy:
            print(f"  Docket: {strategy['docket']}")
        if 'full_text' in strategy:
            print(f"  Full Text: {strategy['full_text'][:50]}...")
        print(f"  Result: {strategy['result']}")
        print() 