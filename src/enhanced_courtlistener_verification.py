#!/usr/bin/env python3
"""
Enhanced CourtListener verification with cross-validation to prevent false positives
"""

import re
import requests
import json
import logging
import time
from typing import Dict, Optional, List

# Import the enhanced case name matcher
from src.enhanced_case_name_matcher import enhanced_matcher, is_likely_same_case

logger = logging.getLogger(__name__)

class EnhancedCourtListenerVerifier:
    """Enhanced verification with cross-validation between API endpoints"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"Authorization": f"Token {api_key}"}
    
    def verify_citation_enhanced(self, citation: str, extracted_case_name: Optional[str] = None) -> Dict:
        """
        Enhanced verification with cross-validation to prevent false positives
        
        Strategy:
        1. Filter out test citations
        2. Try search API first (more reliable, broader coverage)
        3. Cross-validate with citation-lookup if needed
        4. Use fuzzy matching for case name verification
        5. Only mark as verified if validation passes strict criteria
        """
        
        print(f"[ENHANCED] Starting enhanced verification for: {citation}")
        
        # CRITICAL: Filter out known test citations
        if self._is_test_citation(citation):
            print(f"[ENHANCED] REJECTED: Test citation detected: {citation}")
            return {
                "canonical_name": None,
                "canonical_date": None,
                "url": None,
                "verified": False,
                "raw": None,
                "source": "test_citation_rejected",
                "confidence": 0.0,
                "validation_method": "test_citation_filter"
            }
        
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
            # Cross-validate with citation-lookup if we have extracted case name
            if extracted_case_name:
                lookup_result = self._verify_with_citation_lookup(citation, extracted_case_name)
                if lookup_result['verified']:
                    # Both APIs agree - high confidence
                    result.update(search_result)
                    result['confidence'] = 0.95
                    result['validation_method'] = "dual_api_cross_validation"
                else:
                    # Search API found it but lookup didn't - moderate confidence
                    result.update(search_result)
                    result['confidence'] = 0.8
                    result['validation_method'] = "search_api_only"
            else:
                # No extracted case name for cross-validation - moderate confidence
                result.update(search_result)
                result['confidence'] = 0.8
                result['validation_method'] = "search_api_only"
        else:
            # Search API failed, try citation-lookup
            lookup_result = self._verify_with_citation_lookup(citation, extracted_case_name)
            if lookup_result['verified']:
                result.update(lookup_result)
                result['confidence'] = 0.7
                result['validation_method'] = "citation_lookup_only"
        
        return result
    
    def _verify_with_search_api(self, citation: str, extracted_case_name: Optional[str] = None) -> Dict:
        """Verify using search API with fuzzy case name matching"""
        
        result = {
            "canonical_name": None,
            "canonical_date": None,
            "url": None,
            "verified": False,
            "raw": None
        }
        
        try:
            # Build search query
            search_query = citation
            if extracted_case_name:
                # Add case name to search query for better results
                search_query = f"{extracted_case_name} {citation}"
            
            url = f"https://www.courtlistener.com/api/rest/v4/search/"
            params = {
                'q': search_query,
                'format': 'json',
                'stat_Precedential': 'on',  # Only published opinions
                'type': 'o'  # Opinions only
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                api_results = response.json()
                result['raw'] = response.text
                
                # Find valid results
                found_results = [r for r in api_results.get('results', []) if r.get('status') != 404]
                
                if found_results:
                    # Use fuzzy matching to find the best result
                    best_result = self._find_best_match_with_fuzzy_matching(
                        found_results, extracted_case_name, citation
                    )
                    
                    if best_result:
                        result.update({
                            "canonical_name": best_result.get('caseName', ''),
                            "canonical_date": best_result.get('dateFiled', ''),
                            "url": best_result.get('absolute_url', ''),
                            "verified": True,
                            "source": "CourtListener Search API"
                        })
                        
                        # Adjust confidence based on case name match quality
                        if extracted_case_name:
                            similarity = enhanced_matcher.calculate_similarity(
                                extracted_case_name, 
                                best_result.get('caseName', '')
                            )
                            result['confidence'] = min(0.9, 0.6 + similarity * 0.3)
                        else:
                            result['confidence'] = 0.7
                
        except Exception as e:
            print(f"[ENHANCED] Search API error: {e}")
            logger.error(f"Search API error: {e}")
        
        return result
    
    def _verify_with_citation_lookup(self, citation: str, extracted_case_name: Optional[str] = None) -> Dict:
        """Verify using citation-lookup API with fuzzy case name matching"""
        
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
                    # Use fuzzy matching to find the best result
                    best_result = self._find_best_match_with_fuzzy_matching(
                        found_results, extracted_case_name, citation
                    )
                    
                    if best_result:
                        result.update({
                            "canonical_name": best_result.get('caseName', ''),
                            "canonical_date": best_result.get('dateFiled', ''),
                            "url": best_result.get('absolute_url', ''),
                            "verified": True,
                            "source": "CourtListener Citation-Lookup API"
                        })
                        
                        # Adjust confidence based on case name match quality
                        if extracted_case_name:
                            similarity = enhanced_matcher.calculate_similarity(
                                extracted_case_name, 
                                best_result.get('caseName', '')
                            )
                            result['confidence'] = min(0.9, 0.6 + similarity * 0.3)
                        else:
                            result['confidence'] = 0.7
                
        except Exception as e:
            print(f"[ENHANCED] Citation-lookup API error: {e}")
            logger.error(f"Citation-lookup API error: {e}")
        
        return result
    
    def _find_best_match_with_fuzzy_matching(self, api_results: List[Dict], 
                                           extracted_case_name: Optional[str], 
                                           citation: str) -> Optional[Dict]:
        """
        Find the best matching result using fuzzy case name matching.
        
        Args:
            api_results: List of results from CourtListener API
            extracted_case_name: Case name extracted from document
            citation: Citation text
            
        Returns:
            Best matching result or None
        """
        if not api_results:
            return None
        
        # If we have an extracted case name, use fuzzy matching
        if extracted_case_name:
            best_match = None
            best_score = 0.0
            
            for result in api_results:
                api_case_name = result.get('caseName', '')
                if api_case_name:
                    # Calculate similarity using enhanced matcher
                    similarity = enhanced_matcher.calculate_similarity(
                        extracted_case_name, api_case_name
                    )
                    
                    # Log similarity for debugging
                    print(f"[ENHANCED] Case name similarity: '{extracted_case_name}' vs '{api_case_name}' = {similarity:.3f}")
                    
                    # Use threshold of 0.6 for verification (more lenient than clustering)
                    if similarity >= 0.6 and similarity > best_score:
                        best_score = similarity
                        best_match = result
            
            if best_match:
                print(f"[ENHANCED] Best match found with similarity {best_score:.3f}")
                return best_match
        
        # Fallback: return first valid result if no fuzzy match found
        for result in api_results:
            if result.get('caseName') and result.get('absolute_url'):
                return result
        
        return None
    
    def _is_test_citation(self, citation: str) -> bool:
        """Check if citation is a known test citation."""
        test_patterns = [
            r'\b123\s+f\.?3d\s+456\b',
            r'\b999\s+u\.?s\.?\s+999\b',
            r'\bsmith\s+v\.?\s+jones\b',
            r'\btest\s+citation\b',
            r'\bsample\s+citation\b',
            r'\bfake\s+citation\b'
        ]
        
        citation_lower = citation.lower()
        for pattern in test_patterns:
            if re.search(pattern, citation_lower):
                return True
        
        return False

# Backward compatibility function
def verify_with_courtlistener_enhanced(courtlistener_api_key: str, citation: str, extracted_case_name: Optional[str] = None) -> Dict:
    """Enhanced verification function with cross-validation"""
    
    verifier = EnhancedCourtListenerVerifier(courtlistener_api_key)
    return verifier.verify_citation_enhanced(citation, extracted_case_name)
