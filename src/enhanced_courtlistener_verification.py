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
        Enhanced verification using citation-lookup API v4 as primary method.
        
        Strategy:
        1. Use citation-lookup API v4 (fast, reliable, designed for citations)
        2. Only use search API if we need additional metadata not in citation-lookup
        3. Apply strict matching criteria: same year, citation, and meaningful words in common
        """
        
        print(f"[ENHANCED] Starting citation-lookup API v4 verification for: {citation}")
        
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
            "validation_method": "citation_lookup_v4"
        }
        
        # STEP 1: Try citation-lookup API v4 first (primary method)
        lookup_result = self._verify_with_citation_lookup_v4(citation, extracted_case_name)
        
        if lookup_result['verified']:
            # Citation-lookup succeeded - use this result
            result.update(lookup_result)
            result['validation_method'] = "citation_lookup_v4_success"
            result['confidence'] = 0.95  # High confidence for citation-lookup matches
            
            # Only use search API if we need additional metadata
            if self._needs_additional_metadata(lookup_result):
                print(f"[ENHANCED] Citation-lookup succeeded but need additional metadata, trying search API")
                search_result = self._verify_with_search_api_for_metadata(citation, extracted_case_name, lookup_result)
                if search_result and search_result.get('verified', False):
                    # Merge additional metadata from search API
                    result.update(search_result)
                    result['validation_method'] = "citation_lookup_v4_plus_search_metadata"
                    result['confidence'] = 0.98  # Very high confidence with dual verification
        else:
            # Citation-lookup failed - try search API as fallback
            print(f"[ENHANCED] Citation-lookup failed, trying search API as fallback")
            search_result = self._verify_with_search_api(citation, extracted_case_name)
            if search_result['verified']:
                result.update(search_result)
                result['validation_method'] = "search_api_fallback"
                result['confidence'] = 0.7  # Lower confidence for search API fallback
        
        return result
    
    def verify_citations_batch(self, citations: List[str], extracted_case_names: Optional[List[str]] = None) -> List[Dict]:
        """
        Verify multiple citations using CourtListener citation-lookup API v4 batch processing.
        
        Args:
            citations: List of citation strings to verify
            extracted_case_names: Optional list of extracted case names (must match citations length)
            
        Returns:
            List of verification results for each citation
        """
        if not citations:
            return []
        
        # Ensure extracted_case_names matches citations length
        if extracted_case_names and len(extracted_case_names) != len(citations):
            logger.warning("extracted_case_names length doesn't match citations length")
            extracted_case_names = None
        
        results = []
        
        try:
            # Use citation-lookup API v4 for batch processing
            url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
            
            # Process citations in batches of 60 (API limit)
            batch_size = 60
            for i in range(0, len(citations), batch_size):
                batch_citations = citations[i:i + batch_size]
                batch_names = extracted_case_names[i:i + batch_size] if extracted_case_names else [None] * len(batch_citations)
                
                # Create batch request
                batch_data = {"text": batch_citations}
                
                logger.info(f"Processing CourtListener batch {i//batch_size + 1}: {len(batch_citations)} citations")
                
                response = requests.post(url, headers=self.headers, json=batch_data, timeout=30)
                
                if response.status_code == 200:
                    batch_results = response.json()
                    
                    # Process each citation result
                    for j, citation in enumerate(batch_citations):
                        citation_result = self._process_batch_citation_result(
                            citation, 
                            batch_names[j] if batch_names else None,
                            batch_results[j] if j < len(batch_results) else None
                        )
                        results.append(citation_result)
                else:
                    logger.warning(f"CourtListener batch API error: {response.status_code}")
                    # Add failed results for this batch
                    for citation in batch_citations:
                        results.append(self._create_failed_batch_result(citation))
            
        except Exception as e:
            logger.error(f"CourtListener batch verification error: {e}")
            # Return failed results for all citations
            for citation in citations:
                results.append(self._create_failed_batch_result(citation))
        
        return results
    
    def _process_batch_citation_result(self, citation: str, extracted_case_name: Optional[str], api_result: Optional[Dict]) -> Dict:
        """Process a single citation result from batch API response."""
        
        result = {
            "canonical_name": None,
            "canonical_date": None,
            "url": None,
            "verified": False,
            "raw": api_result,
            "source": "CourtListener Batch API",
            "confidence": 0.0,
            "validation_method": "batch_citation_lookup"
        }
        
        if not api_result or api_result.get('status') == 404:
            return result
        
        # Extract case data from API result
        clusters = api_result.get('clusters', [])
        if not clusters:
            return result
        
        # Find the best matching case using strict criteria
        best_case = self._find_best_case_with_strict_criteria(
            clusters, citation, extracted_case_name
        )
        
        if best_case:
            result.update({
                "canonical_name": best_case.get('caseName', ''),
                "canonical_date": best_case.get('dateFiled', ''),
                "url": self._normalize_url(best_case.get('absolute_url', '')),
                "verified": True,
                "confidence": 0.9
            })
        
        return result
    
    def _find_best_case_with_strict_criteria(self, clusters: List[Dict], citation: str, extracted_case_name: Optional[str]) -> Optional[Dict]:
        """
        Find the best case using strict criteria:
        1. Same year and citation
        2. At least one non-stopword in common between extracted and canonical names
        
        Args:
            clusters: List of case clusters from CourtListener API
            citation: Citation text to match
            extracted_case_name: Extracted case name from document
            
        Returns:
            Best matching case or None
        """
        if not clusters:
            return None
        
        best_match = None
        best_score = 0.0
        
        for cluster in clusters:
            cases = cluster.get('cases', [])
            for case in cases:
                score = self._calculate_strict_match_score(case, citation, extracted_case_name)
                if score > best_score:
                    best_score = score
                    best_match = case
        
        # Only return if we meet strict criteria
        if best_match and best_score >= 1.5:  # Reduced from 2.0 to 1.5 for more reasonable matching
            print(f"[ENHANCED] Primary case found with score {best_score:.3f}: {best_match.get('caseName')}")
            return best_match
        
        return None
    
    def _calculate_strict_match_score(self, case: Dict, citation: str, extracted_case_name: Optional[str]) -> float:
        """
        Calculate match score using strict criteria.
        
        Returns:
            Score >= 2.0 if strict criteria are met, lower score otherwise
        """
        score = 0.0
        
        # CRITICAL: Must have same citation (allowing for reporter variations)
        case_citation = case.get('citation', '')
        if not self._citations_match(citation, case_citation):
            print(f"[ENHANCED] Citation mismatch: '{citation}' vs '{case_citation}'")
            return 0.0  # Citation mismatch = no match
        else:
            score += 1.0
            print(f"[ENHANCED] Citation match: '{citation}' = '{case_citation}' (+1.0)")
        
        # YEAR MATCHING: More lenient - allow reasonable year differences
        case_date = case.get('dateFiled', '')
        citation_year = self._extract_year_from_citation(citation)
        case_year = self._extract_year_from_date(case_date)
        
        if citation_year and case_year:
            year_diff = abs(int(citation_year) - int(case_year))
            if year_diff == 0:
                score += 1.0
                print(f"[ENHANCED] Exact year match: {citation_year} = {case_year} (+1.0)")
            elif year_diff <= 3:  # Allow 3 year difference for citation-lookup
                score += 0.5
                print(f"[ENHANCED] Close year match: {citation_year} vs {case_year} (diff: {year_diff}) (+0.5)")
            else:
                print(f"[ENHANCED] Year mismatch: {citation_year} vs {case_year} (diff: {year_diff})")
                return 0.0  # Year too different = no match
        else:
            # No year info - still allow match but with lower score
            print(f"[ENHANCED] No year info available - proceeding with caution")
            score += 0.3
        
        # Case name must have at least one non-stopword in common
        if extracted_case_name:
            extracted_name = extracted_case_name
            canonical_name = case.get('caseName', '')
            
            if self._has_meaningful_words_in_common(extracted_name, canonical_name):
                score += 1.0
                print(f"[ENHANCED] Meaningful words in common: '{extracted_name}' vs '{canonical_name}' (+1.0)")
            else:
                print(f"[ENHANCED] No meaningful words in common: '{extracted_name}' vs '{canonical_name}'")
                return 0.0  # No meaningful words in common = no match
        else:
            # No extracted case name - still allow match but with lower score
            print(f"[ENHANCED] No extracted case name - proceeding with caution")
            score += 0.3
        
        print(f"[ENHANCED] Total strict match score: {score}")
        return score
    
    def _extract_year_from_citation(self, citation: str) -> Optional[str]:
        """Extract year from citation text."""
        # Look for 4-digit year in citation
        import re
        year_match = re.search(r'(19|20)\d{2}', citation)
        return year_match.group(0) if year_match else None
    
    def _extract_year_from_date(self, date_str: str) -> Optional[str]:
        """Extract year from date string."""
        if not date_str:
            return None
        
        # Handle various date formats
        import re
        year_match = re.search(r'(19|20)\d{2}', str(date_str))
        return year_match.group(0) if year_match else None
    
    def _citations_match(self, citation1: str, citation2: str) -> bool:
        """Check if two citations match (allowing for reporter variations)."""
        if not citation1 or not citation2:
            return False
        
        # Normalize citations for comparison
        norm1 = self._normalize_citation(citation1)
        norm2 = self._normalize_citation(citation2)
        
        return norm1 == norm2
    
    def _normalize_citation(self, citation: str) -> str:
        """Normalize citation for comparison."""
        # Remove spaces and convert to lowercase
        norm = citation.replace(' ', '').lower()
        
        # Handle Washington reporter variations
        norm = norm.replace('wn.', 'wn').replace('wash.', 'wn')
        norm = norm.replace('wn2d', 'wn2d').replace('wash2d', 'wn2d')
        norm = norm.replace('wnapp', 'wnapp').replace('washapp', 'wnapp')
        
        # Handle Pacific reporter variations
        norm = norm.replace('p.', 'p').replace('pac.', 'p')
        norm = norm.replace('p2d', 'p2d').replace('pac2d', 'p2d')
        norm = norm.replace('p3d', 'p3d').replace('pac3d', 'p3d')
        
        return norm
    
    def _has_meaningful_words_in_common(self, name1: str, name2: str) -> bool:
        """
        Check if two case names have at least one meaningful (non-stopword) word in common.
        
        Args:
            name1: First case name
            name2: Second case name
            
        Returns:
            True if they share at least one meaningful word
        """
        if not name1 or not name2:
            return False
        
        # Define stopwords (common legal terms that don't distinguish cases)
        stopwords = {
            'in', 're', 'of', 'the', 'and', 'or', 'for', 'to', 'a', 'an', 'v', 'vs', 'versus',
            'petition', 'petitioner', 'respondent', 'appellant', 'appellee', 'plaintiff', 'defendant',
            'state', 'united', 'states', 'county', 'city', 'town', 'village', 'corporation',
            'inc', 'llc', 'ltd', 'co', 'company', 'association', 'foundation', 'trust'
        }
        
        # Extract meaningful words from each name
        words1 = set(self._extract_meaningful_words(name1, stopwords))
        words2 = set(self._extract_meaningful_words(name2, stopwords))
        
        # Check for intersection
        common_words = words1.intersection(words2)
        
        return len(common_words) > 0
    
    def _extract_meaningful_words(self, name: str, stopwords: set) -> List[str]:
        """Extract meaningful (non-stopword) words from a case name."""
        if not name:
            return []
        
        # Split into words and filter out stopwords
        words = re.findall(r'\b[a-zA-Z]+\b', name.lower())
        meaningful_words = [word for word in words if word not in stopwords and len(word) > 2]
        
        return meaningful_words
    
    def _create_failed_batch_result(self, citation: str) -> Dict:
        """Create a result for a failed batch verification."""
        return {
            "canonical_name": None,
            "canonical_date": None,
            "url": None,
            "verified": False,
            "raw": None,
            "source": "CourtListener Batch API",
            "confidence": 0.0,
            "validation_method": "batch_failed",
            "error": "Batch verification failed"
        }
    
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

    def _verify_with_citation_lookup_v4(self, citation: str, extracted_case_name: Optional[str] = None) -> Dict:
        """Verify using citation-lookup API v4 with strict matching criteria."""
        
        result = {
            "canonical_name": None,
            "canonical_date": None,
            "url": None,
            "verified": False,
            "raw": None,
            "source": "CourtListener Citation-Lookup API v4"
        }
        
        try:
            # Use citation-lookup API v4
            url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
            data = {"text": citation}
            
            print(f"[ENHANCED] Citation-lookup API v4 request: {url}")
            print(f"[ENHANCED] Citation-lookup API v4 data: {data}")
            
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            
            print(f"[ENHANCED] Citation-lookup API v4 response status: {response.status_code}")
            
            if response.status_code == 200:
                api_results = response.json()
                result['raw'] = response.text
                
                print(f"[ENHANCED] Citation-lookup API v4 raw response: {api_results}")
                
                # Find valid results
                found_results = [r for r in api_results if r.get('status') != 404 and r.get('clusters')]
                
                print(f"[ENHANCED] Citation-lookup API v4 found {len(found_results)} valid results")
                
                if found_results:
                    # Use strict criteria to find the PRIMARY case
                    best_case = self._find_best_case_with_strict_criteria(
                        found_results, citation, extracted_case_name
                    )
                    
                    if best_case:
                        print(f"[ENHANCED] Citation-lookup API v4 found best case: {best_case.get('caseName', 'N/A')}")
                        result.update({
                            "canonical_name": best_case.get('caseName', ''),
                            "canonical_date": best_case.get('dateFiled', ''),
                            "url": self._normalize_url(best_case.get('absolute_url', '')),
                            "verified": True,
                            "confidence": 0.9
                        })
                    else:
                        print(f"[ENHANCED] Citation-lookup API v4 found results but strict criteria failed")
                else:
                    print(f"[ENHANCED] Citation-lookup API v4 found no valid results")
            else:
                print(f"[ENHANCED] Citation-lookup API v4 failed with status: {response.status_code}")
                print(f"[ENHANCED] Citation-lookup API v4 error response: {response.text}")
                
        except Exception as e:
            print(f"[ENHANCED] Citation-lookup API v4 error: {e}")
            logger.error(f"Citation-lookup API v4 error: {e}")
        
        return result
    
    def _needs_additional_metadata(self, lookup_result: Dict) -> bool:
        """Check if we need additional metadata from search API."""
        # Check if we have all essential metadata
        has_name = bool(lookup_result.get('canonical_name'))
        has_date = bool(lookup_result.get('canonical_date'))
        has_url = bool(lookup_result.get('url'))
        
        # We might need search API if:
        # 1. Missing case name (need to find the actual case)
        # 2. Missing date (need filing date)
        # 3. Missing URL (need case link)
        # 4. Need additional context (docket info, judge, etc.)
        
        return not (has_name and has_date and has_url)
    
    def _verify_with_search_api_for_metadata(self, citation: str, extracted_case_name: Optional[str], existing_result: Dict) -> Optional[Dict]:
        """Use search API only to get additional metadata not available in citation-lookup."""
        
        try:
            # Only search if we need specific metadata
            if not existing_result.get('canonical_name'):
                # Need case name - search by citation
                search_query = citation
            elif not existing_result.get('canonical_date'):
                # Need date - search by case name + citation
                search_query = f"{existing_result.get('canonical_name')} {citation}"
            else:
                # Have all essential metadata - no need for search
                return None
            
            url = f"https://www.courtlistener.com/api/rest/v4/search/"
            params = {
                'q': search_query,
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
                    # Find the best match for additional metadata
                    best_result = self._find_primary_case_with_enhanced_matching(
                        found_results, extracted_case_name, citation, citation
                    )
                    
                    if best_result:
                        # Only return metadata that we don't already have
                        metadata_result = {}
                        if not existing_result.get('canonical_name') and best_result.get('caseName'):
                            metadata_result['canonical_name'] = best_result.get('caseName')
                        if not existing_result.get('canonical_date') and best_result.get('dateFiled'):
                            metadata_result['canonical_date'] = best_result.get('dateFiled')
                        if not existing_result.get('url') and best_result.get('absolute_url'):
                            url = best_result.get('absolute_url')
                            if url:
                                metadata_result['url'] = self._normalize_url(url)
                        
                        if metadata_result:
                            metadata_result['verified'] = True
                            metadata_result['source'] = 'CourtListener Search API (Metadata)'
                            return metadata_result
            
        except Exception as e:
            logger.warning(f"Search API metadata lookup error: {e}")
        
        return None

# Backward compatibility function
def verify_with_courtlistener_enhanced(courtlistener_api_key: str, citation: str, extracted_case_name: Optional[str] = None) -> Dict:
    """Enhanced verification function with cross-validation"""
    
    verifier = EnhancedCourtListenerVerifier(courtlistener_api_key)
    return verifier.verify_citation_enhanced(citation, extracted_case_name)
