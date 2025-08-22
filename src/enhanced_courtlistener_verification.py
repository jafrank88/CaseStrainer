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
        """Verify using search API with fuzzy case name matching - focus on PRIMARY cases"""
        
        result = {
            "canonical_name": None,
            "canonical_date": None,
            "url": None,
            "verified": False,
            "raw": None
        }
        
        try:
            # Strategy: Search for the PRIMARY case, not cases that cite it
            # Use extracted case name as primary search term, citation as secondary
            
            if extracted_case_name:
                # Search by case name first (more likely to find the primary case)
                search_query = extracted_case_name
                # Add citation as a filter to narrow down results
                citation_filter = citation
                
                # Try multiple search strategies to find the primary case
                best_result = self._search_for_primary_case_multiple_strategies(
                    extracted_case_name, citation, citation_filter
                )
                
                if best_result:
                    result.update({
                        "canonical_name": best_result.get('caseName', ''),
                        "canonical_date": best_result.get('dateFiled', ''),
                        "url": self._normalize_url(best_result.get('absolute_url', '')),
                        "verified": True,
                        "source": "CourtListener Search API"
                    })
                    
                    # Adjust confidence based on case name match quality
                    similarity = enhanced_matcher.calculate_similarity(
                        extracted_case_name, 
                        best_result.get('caseName', '')
                    )
                    result['confidence'] = min(0.9, 0.6 + similarity * 0.3)
            else:
                # No case name - search by citation but be more restrictive
                search_query = citation
                citation_filter = None
                
                url = f"https://www.courtlistener.com/api/rest/v4/search/"
                params = {
                    'q': search_query,
                    'format': 'json',
                    'stat_Precedential': 'on',  # Only published opinions
                    'type': 'o',  # Opinions only
                    'order_by': 'dateFiled desc'  # Most recent first
                }
                
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    api_results = response.json()
                    result['raw'] = response.text
                    
                    # Find valid results
                    found_results = [r for r in api_results.get('results', []) if r.get('status') != 404]
                    
                    if found_results:
                        # Use enhanced matching to find the PRIMARY case
                        best_result = self._find_primary_case_with_enhanced_matching(
                            found_results, extracted_case_name, citation, citation_filter
                        )
                        
                        if best_result:
                            result.update({
                                "canonical_name": best_result.get('caseName', ''),
                                "canonical_date": best_result.get('dateFiled', ''),
                                "url": best_result.get('absolute_url', ''),
                                "verified": True,
                                "source": "CourtListener Search API"
                            })
                            
                            result['confidence'] = 0.7
                
        except Exception as e:
            print(f"[ENHANCED] Search API error: {e}")
            logger.error(f"Search API error: {e}")
        
        return result
    
    def _verify_with_citation_lookup(self, citation: str, extracted_case_name: Optional[str] = None) -> Dict:
        """Verify using citation-lookup API with citation-first search strategy"""
        
        result = {
            "canonical_name": None,
            "canonical_date": None,
            "url": None,
            "verified": False,
            "raw": None
        }
        
        try:
            # Citation-lookup API is designed to find cases by citation
            # This should be more reliable for finding the primary case
            url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
            data = {"text": citation}
            
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            
            if response.status_code == 200:
                api_results = response.json()
                result['raw'] = response.text
                
                # Find valid results
                found_results = [r for r in api_results if r.get('status') != 404 and r.get('clusters')]
                
                if found_results:
                    # Use enhanced matching to find the PRIMARY case
                    # Citation-lookup should find the case that IS the citation
                    best_result = self._find_primary_case_with_enhanced_matching(
                        found_results, extracted_case_name, citation, citation
                    )
                    
                    if best_result:
                        result.update({
                            "canonical_name": best_result.get('caseName', ''),
                            "canonical_date": best_result.get('dateFiled', ''),
                            "url": self._normalize_url(best_result.get('absolute_url', '')),
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
    
    def _search_for_primary_case_multiple_strategies(self, extracted_case_name: str, citation: str, citation_filter: str) -> Optional[Dict]:
        """
        Use multiple search strategies to find the primary case.
        
        Strategy 1: Search by citation (highest priority) - FIND THE ACTUAL CASE
        Strategy 2: Search by citation + case name (medium priority)
        Strategy 3: Search by case name only (lower priority) - FALLBACK
        
        Args:
            extracted_case_name: Case name extracted from document
            citation: Citation text
            citation_filter: Citation to use as filter
            
        Returns:
            Best matching primary case result or None
        """
        url = f"https://www.courtlistener.com/api/rest/v4/search/"
        
        # Strategy 1: Search by citation (highest priority) - FIND THE ACTUAL CASE
        print(f"[ENHANCED] Strategy 1: Searching by citation: '{citation}'")
        params = {
            'q': citation,
            'format': 'json',
            'stat_Precedential': 'on',
            'type': 'o',
            'order_by': 'dateFiled desc'
        }
        
        response = requests.get(url, headers=self.headers, params=params, timeout=30)
        if response.status_code == 200:
            api_results = response.json()
            found_results = [r for r in api_results.get('results', []) if r.get('status') != 404]
            
            if found_results:
                best_result = self._find_primary_case_with_enhanced_matching(
                    found_results, extracted_case_name, citation, citation_filter
                )
                if best_result:
                    print(f"[ENHANCED] Strategy 1 successful: Found primary case by citation")
                    return best_result
        
        # Strategy 2: Search by citation + case name (medium priority)
        print(f"[ENHANCED] Strategy 2: Searching by citation + case name")
        params = {
            'q': f'{citation} {extracted_case_name}',
            'format': 'json',
            'stat_Precedential': 'on',
            'type': 'o',
            'order_by': 'dateFiled desc'
        }
        
        response = requests.get(url, headers=self.headers, params=params, timeout=30)
        if response.status_code == 200:
            api_results = response.json()
            found_results = [r for r in api_results.get('results', []) if r.get('status') != 404]
            
            if found_results:
                best_result = self._find_primary_case_with_enhanced_matching(
                    found_results, extracted_case_name, citation, citation_filter
                )
                if best_result:
                    print(f"[ENHANCED] Strategy 2 successful: Found primary case by citation + name")
                    return best_result
        
        # Strategy 3: Search by exact case name (lower priority) - FALLBACK
        print(f"[ENHANCED] Strategy 3: Searching by exact case name (fallback)")
        params = {
            'q': f'"{extracted_case_name}"',  # Exact phrase match
            'format': 'json',
            'stat_Precedential': 'on',
            'type': 'o',
            'order_by': 'dateFiled desc'
        }
        
        response = requests.get(url, headers=self.headers, params=params, timeout=30)
        if response.status_code == 200:
            api_results = response.json()
            found_results = [r for r in api_results.get('results', []) if r.get('status') != 404]
            
            if found_results:
                best_result = self._find_primary_case_with_enhanced_matching(
                    found_results, extracted_case_name, citation, citation_filter
                )
                if best_result:
                    print(f"[ENHANCED] Strategy 3 successful: Found primary case by name (fallback)")
                    return best_result
        
        print(f"[ENHANCED] All search strategies failed to find primary case")
        return None
    
    def _find_primary_case_with_enhanced_matching(self, api_results: List[Dict], 
                                                extracted_case_name: Optional[str], 
                                                citation: str,
                                                citation_filter: Optional[str] = None) -> Optional[Dict]:
        """
        Find the PRIMARY case (the one in header/metadata) rather than cases that just cite it.
        
        Strategy:
        1. Prioritize exact case name matches
        2. Use citation as a filter to eliminate cases that just cite the target
        3. Focus on finding the case that IS the citation, not cases that CONTAIN the citation
        
        Args:
            api_results: List of results from CourtListener API
            extracted_case_name: Case name extracted from document
            citation: Citation text
            citation_filter: Citation to use as a filter
            
        Returns:
            Primary case result or None
        """
        if not api_results:
            return None
        
        # If we have an extracted case name, use enhanced matching
        if extracted_case_name:
            best_match = None
            best_score = 0.0
            
            for result in api_results:
                api_case_name = result.get('caseName', '')
                if not api_case_name:
                    continue
                
                # Calculate similarity using enhanced matcher
                similarity = enhanced_matcher.calculate_similarity(
                    extracted_case_name, api_case_name
                )
                
                # Log similarity for debugging
                print(f"[ENHANCED] Primary case similarity: '{extracted_case_name}' vs '{api_case_name}' = {similarity:.3f}")
                
                # Use citation filter to eliminate cases that just cite the target
                if citation_filter:
                    # Check if this result's text contains the citation (indicating it's NOT the primary case)
                    result_text = result.get('plain_text', '') or result.get('html', '') or ''
                    if citation_filter in result_text and similarity < 0.8:
                        # This case cites the target - likely NOT the primary case
                        print(f"[ENHANCED] Skipping case that cites target: {api_case_name}")
                        continue
                
                # Additional check: Look for citation patterns in the case text
                # If the case text contains the exact citation pattern, it might be citing the target
                citation_penalty = 0.0
                if self._case_appears_to_cite_target(result, citation, extracted_case_name):
                    print(f"[ENHANCED] Case appears to cite target, reducing score: {api_case_name}")
                    citation_penalty = 0.2
                
                # Score based on similarity and other factors
                score = similarity - citation_penalty
                
                # Bonus for exact case name match
                if extracted_case_name.lower() == api_case_name.lower():
                    score += 0.3
                
                # Bonus for high similarity
                if similarity >= 0.8:
                    score += 0.2
                elif similarity >= 0.6:
                    score += 0.1
                
                # Penalty for very low similarity
                if similarity < 0.4:
                    score -= 0.3
                
                # Additional bonus for citation-based matches
                # If we found this case by searching the citation, it's more likely to be the primary case
                if citation_filter and citation_filter in api_case_name:
                    score += 0.2
                    print(f"[ENHANCED] Citation found in case name - bonus applied: {api_case_name}")
                
                # Penalty for cases that appear to be citing the target
                # This helps eliminate cases that just mention the target case
                if extracted_case_name and extracted_case_name.lower() in api_case_name.lower() and similarity < 0.7:
                    # This case name contains the extracted case name but similarity is low
                    # It might be a different case that just mentions the target
                    score -= 0.3
                    print(f"[ENHANCED] Case name contains target but low similarity - penalty applied: {api_case_name}")
                
                print(f"[ENHANCED] Case '{api_case_name}' scored: {score:.3f}")
                
                if score > best_score:
                    best_score = score
                    best_match = result
            
            if best_match and best_score >= 0.5:  # Require minimum score for primary case
                print(f"[ENHANCED] Primary case found with score {best_score:.3f}: {best_match.get('caseName')}")
                return best_match
        
        # Fallback: return first valid result if no enhanced match found
        for result in api_results:
            if result.get('caseName') and result.get('absolute_url'):
                return result
        
        return None
    
    def _case_appears_to_cite_target(self, result: Dict, citation: str, extracted_case_name: Optional[str] = None) -> bool:
        """
        Check if a case result appears to be citing the target case rather than being the target.
        
        Args:
            result: Case result from CourtListener API
            citation: Citation text we're looking for
            extracted_case_name: Extracted case name
            
        Returns:
            True if the case appears to cite the target, False otherwise
        """
        # Get case text content
        case_text = result.get('plain_text', '') or result.get('html', '') or ''
        if not case_text:
            return False
        
        # Look for citation patterns that suggest this case is citing the target
        citation_patterns = [
            # Pattern: "See" or "citing" followed by citation
            rf'(?:see|citing|cited)\s+{re.escape(citation)}',
            # Pattern: Citation in parentheses (common citation format)
            rf'\({re.escape(citation)}\)',
            # Pattern: Citation after "In" or "See"
            rf'(?:in|see)\s+{re.escape(citation)}',
        ]
        
        for pattern in citation_patterns:
            if re.search(pattern, case_text, re.IGNORECASE):
                print(f"[ENHANCED] Found citation pattern '{pattern}' in case text")
                return True
        
        # Look for case name patterns that suggest this case is citing the target
        if extracted_case_name:
            # If the case text contains the extracted case name in a citation context
            # but the case name doesn't match the result's case name, it's likely citing
            case_name_patterns = [
                rf'(?:see|citing|cited)\s+{re.escape(extracted_case_name)}',
                rf'\({re.escape(extracted_case_name)}\)',
                rf'(?:in|see)\s+{re.escape(extracted_case_name)}',
            ]
            
            for pattern in case_name_patterns:
                if re.search(pattern, case_text, re.IGNORECASE):
                    print(f"[ENHANCED] Found case name citation pattern '{pattern}' in case text")
                    return True
        
        return False
    
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

    def _normalize_url(self, url: str) -> str:
        """
        Normalize a CourtListener URL to ensure it's absolute.
        CourtListener URLs are often relative, but the API expects absolute.
        """
        if url and not url.startswith('http://') and not url.startswith('https://'):
            # Attempt to prepend https:// if it's a relative path
            if url.startswith('/'):
                return f"https://www.courtlistener.com{url}"
            # If it's a subdomain path, prepend https://
            if url.startswith('api/'):
                return f"https://www.courtlistener.com{url}"
            # If it's a direct path, prepend https://
            return f"https://www.courtlistener.com{url}"
        return url

# Backward compatibility function
def verify_with_courtlistener_enhanced(courtlistener_api_key: str, citation: str, extracted_case_name: Optional[str] = None) -> Dict:
    """Enhanced verification function with cross-validation"""
    
    verifier = EnhancedCourtListenerVerifier(courtlistener_api_key)
    return verifier.verify_citation_enhanced(citation, extracted_case_name)
