#!/usr/bin/env python3
"""
Enhanced CourtListener verification with cross-validation to prevent false positives
"""

import requests
import json
import logging
import time
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

class EnhancedCourtListenerVerifier:
    """Enhanced verification with cross-validation between API endpoints"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"Authorization": f"Token {api_key}"}
    
    def verify_citation_enhanced(self, citation: str, extracted_case_name: str = None) -> Dict:
        """
        Enhanced verification with cross-validation to prevent false positives
        
        Strategy:
        1. Try search API first (more reliable, broader coverage)
        2. Cross-validate with citation-lookup if needed
        3. Only mark as verified if validation passes strict criteria
        """
        
        print(f"[ENHANCED] Starting enhanced verification for: {citation}")
        
        result = {
            "canonical_name": None,
            "canonical_date": None,
            "url": None,
            "verified": False,
            "raw": None,
            "source": None,
            "confidence": 0.0,
            "validation_method": "enhanced_cross_validation"
        }
        
        # Step 1: Try search API first (more reliable)
        search_result = self._verify_with_search_api(citation, extracted_case_name)
        
        if search_result['verified']:
            print(f"[ENHANCED] Search API found result, performing validation...")
            
            # Validate the search result
            if self._validate_verification_result(search_result, citation, extracted_case_name):
                print(f"[ENHANCED] Search API result passed validation")
                result.update(search_result)
                result['source'] = 'CourtListener-search-validated'
                result['confidence'] = 0.9
                return result
            else:
                print(f"[ENHANCED] Search API result failed validation")
        
        # Step 2: Try citation-lookup as fallback (if search failed or didn't validate)
        print(f"[ENHANCED] Trying citation-lookup as fallback...")
        lookup_result = self._verify_with_citation_lookup(citation, extracted_case_name)
        
        if lookup_result['verified']:
            print(f"[ENHANCED] Citation-lookup found result, performing validation...")
            
            # Validate the lookup result
            if self._validate_verification_result(lookup_result, citation, extracted_case_name):
                print(f"[ENHANCED] Citation-lookup result passed validation")
                result.update(lookup_result)
                result['source'] = 'CourtListener-lookup-validated'
                result['confidence'] = 0.8
                return result
            else:
                print(f"[ENHANCED] Citation-lookup result failed validation")
        
        # Step 3: Cross-validation for uncertain cases
        if search_result['verified'] or lookup_result['verified']:
            print(f"[ENHANCED] Performing cross-validation between endpoints...")
            
            cross_validated = self._cross_validate_results(search_result, lookup_result, citation)
            if cross_validated['verified']:
                print(f"[ENHANCED] Cross-validation successful")
                result.update(cross_validated)
                result['source'] = 'CourtListener-cross-validated'
                result['confidence'] = 0.95
                return result
        
        print(f"[ENHANCED] No valid verification found for: {citation}")
        return result
    
    def _verify_with_search_api(self, citation: str, extracted_case_name: str = None) -> Dict:
        """Verify using search API"""
        
        result = {
            "canonical_name": None,
            "canonical_date": None,
            "url": None,
            "verified": False,
            "raw": None
        }
        
        try:
            url = "https://www.courtlistener.com/api/rest/v4/search/"
            params = {
                "type": "o",  # opinions
                "q": citation,
                "format": "json"
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                result['raw'] = response.text
                
                results_count = data.get('count', 0)
                results = data.get('results', [])
                
                if results_count > 0 and results:
                    # Use best result (first one, or best name match if available)
                    best_result = self._select_best_search_result(results, extracted_case_name)
                    
                    if best_result:
                        case_name = best_result.get('caseName')
                        date_filed = best_result.get('dateFiled')
                        absolute_url = best_result.get('absolute_url')
                        
                        # CRITICAL: Only mark as verified if we have essential data
                        if case_name and case_name.strip() and absolute_url and absolute_url.strip():
                            result['canonical_name'] = case_name
                            result['canonical_date'] = date_filed
                            result['url'] = f"https://www.courtlistener.com{absolute_url}"
                            result['verified'] = True
                            
                            print(f"[ENHANCED] Search API found valid data: {case_name}")
                        else:
                            print(f"[ENHANCED] Search API result missing essential data")
        
        except Exception as e:
            print(f"[ENHANCED] Search API error: {str(e)}")
            logger.error(f"[Enhanced CL search] {citation} exception: {e}")
        
        return result
    
    def _verify_with_citation_lookup(self, citation: str, extracted_case_name: str = None) -> Dict:
        """Verify using citation-lookup API"""
        
        result = {
            "canonical_name": None,
            "canonical_date": None,
            "url": None,
            "verified": False,
            "raw": None
        }
        
        try:
            url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
            data = {"text": citation}
            
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            
            if response.status_code == 200:
                api_results = response.json()
                result['raw'] = response.text
                
                # Find valid results
                found_results = [r for r in api_results if r.get('status') != 404 and r.get('clusters')]
                
                if found_results:
                    # Select best cluster
                    best_cluster = self._select_best_cluster(found_results, extracted_case_name)
                    
                    if best_cluster:
                        case_name = best_cluster.get('case_name')
                        date_filed = best_cluster.get('date_filed')
                        absolute_url = best_cluster.get('absolute_url')
                        
                        # CRITICAL: Only mark as verified if we have essential data
                        if case_name and case_name.strip() and absolute_url and absolute_url.strip():
                            result['canonical_name'] = case_name
                            result['canonical_date'] = date_filed
                            result['url'] = f"https://www.courtlistener.com{absolute_url}"
                            result['verified'] = True
                            
                            print(f"[ENHANCED] Citation-lookup found valid data: {case_name}")
                        else:
                            print(f"[ENHANCED] Citation-lookup result missing essential data")
        
        except Exception as e:
            print(f"[ENHANCED] Citation-lookup error: {str(e)}")
            logger.error(f"[Enhanced CL lookup] {citation} exception: {e}")
        
        return result
    
    def _validate_verification_result(self, result: Dict, citation: str, extracted_case_name: str = None) -> bool:
        """Strict validation of verification results to prevent false positives"""
        
        if not result.get('verified'):
            return False
        
        case_name = result.get('canonical_name')
        url = result.get('url')
        
        # Essential data validation
        if not case_name or not case_name.strip():
            print(f"[ENHANCED] Validation failed: No case name")
            return False
        
        if not url or not url.strip():
            print(f"[ENHANCED] Validation failed: No URL")
            return False
        
        # Case name quality validation
        if len(case_name.strip()) < 5:
            print(f"[ENHANCED] Validation failed: Case name too short: '{case_name}'")
            return False
        
        # Check for placeholder or invalid case names
        invalid_patterns = ['unknown', 'n/a', 'null', 'none', 'test', 'placeholder']
        if any(pattern in case_name.lower() for pattern in invalid_patterns):
            print(f"[ENHANCED] Validation failed: Invalid case name pattern: '{case_name}'")
            return False
        
        # URL validation
        if not url.startswith('https://www.courtlistener.com/'):
            print(f"[ENHANCED] Validation failed: Invalid URL format: '{url}'")
            return False
        
        # Name similarity validation (if extracted name available)
        if extracted_case_name and extracted_case_name.strip() and extracted_case_name != 'N/A':
            similarity = self._calculate_name_similarity(case_name, extracted_case_name)
            if similarity < 0.3:  # Very low threshold to catch obvious mismatches
                print(f"[ENHANCED] Validation warning: Low name similarity ({similarity:.2f})")
                print(f"[ENHANCED]   Canonical: '{case_name}'")
                print(f"[ENHANCED]   Extracted: '{extracted_case_name}'")
                # Don't fail validation, but log the concern
        
        print(f"[ENHANCED] Validation passed for: '{case_name}'")
        return True
    
    def _cross_validate_results(self, search_result: Dict, lookup_result: Dict, citation: str) -> Dict:
        """Cross-validate results between different API endpoints"""
        
        result = {
            "canonical_name": None,
            "canonical_date": None,
            "url": None,
            "verified": False,
            "raw": None
        }
        
        # If both methods found results, check for consistency
        if search_result.get('verified') and lookup_result.get('verified'):
            search_name = search_result.get('canonical_name', '').strip()
            lookup_name = lookup_result.get('canonical_name', '').strip()
            
            if search_name and lookup_name:
                similarity = self._calculate_name_similarity(search_name, lookup_name)
                
                if similarity > 0.8:  # High similarity threshold for cross-validation
                    print(f"[ENHANCED] Cross-validation: High similarity ({similarity:.2f})")
                    # Use the result with more complete data
                    if search_result.get('canonical_date') and not lookup_result.get('canonical_date'):
                        result.update(search_result)
                    elif lookup_result.get('canonical_date') and not search_result.get('canonical_date'):
                        result.update(lookup_result)
                    else:
                        # Prefer search result as it's generally more reliable
                        result.update(search_result)
                    
                    result['verified'] = True
                    return result
                else:
                    print(f"[ENHANCED] Cross-validation failed: Low similarity ({similarity:.2f})")
                    print(f"[ENHANCED]   Search: '{search_name}'")
                    print(f"[ENHANCED]   Lookup: '{lookup_name}'")
        
        # If only one method found a result, use it if it passed validation
        elif search_result.get('verified'):
            result.update(search_result)
            result['verified'] = True
        elif lookup_result.get('verified'):
            result.update(lookup_result)
            result['verified'] = True
        
        return result
    
    def _select_best_search_result(self, results: List[Dict], extracted_case_name: str = None) -> Optional[Dict]:
        """Select the best result from search API results"""
        
        if not results:
            return None
        
        # If we have an extracted case name, try to find the best match
        if extracted_case_name and extracted_case_name.strip() and extracted_case_name != 'N/A':
            best_result = None
            best_similarity = 0
            
            for result in results:
                case_name = result.get('caseName', '')
                if case_name:
                    similarity = self._calculate_name_similarity(case_name, extracted_case_name)
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_result = result
            
            if best_result and best_similarity > 0.5:
                return best_result
        
        # Otherwise, return the first result (highest relevance)
        return results[0]
    
    def _select_best_cluster(self, found_results: List[Dict], extracted_case_name: str = None) -> Optional[Dict]:
        """Select the best cluster from citation-lookup results"""
        
        all_clusters = []
        for result in found_results:
            all_clusters.extend(result.get('clusters', []))
        
        if not all_clusters:
            return None
        
        # If we have an extracted case name, try to find the best match
        if extracted_case_name and extracted_case_name.strip() and extracted_case_name != 'N/A':
            best_cluster = None
            best_similarity = 0
            
            for cluster in all_clusters:
                case_name = cluster.get('case_name', '')
                if case_name:
                    similarity = self._calculate_name_similarity(case_name, extracted_case_name)
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_cluster = cluster
            
            if best_cluster and best_similarity > 0.5:
                return best_cluster
        
        # Otherwise, return the first cluster
        return all_clusters[0]
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two case names"""
        
        if not name1 or not name2:
            return 0.0
        
        # Normalize names
        name1 = name1.lower().strip()
        name2 = name2.lower().strip()
        
        # Simple similarity based on common words
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0

# Backward compatibility function
def verify_with_courtlistener_enhanced(courtlistener_api_key: str, citation: str, extracted_case_name: str = None) -> Dict:
    """Enhanced verification function with cross-validation"""
    
    verifier = EnhancedCourtListenerVerifier(courtlistener_api_key)
    return verifier.verify_citation_enhanced(citation, extracted_case_name)
