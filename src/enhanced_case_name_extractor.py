#!/usr/bin/env python3
"""
Enhanced Case Name Extractor

This module uses CourtListener API v4 to get canonical case names
and improve extraction accuracy from documents.
"""

import re
import json
import requests
import time
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher
import logging

class EnhancedCaseNameExtractor:
    def __init__(self, api_key: Optional[str] = None, cache_results: bool = True):
        """
        Initialize the enhanced case name extractor.
        
        Args:
            api_key: API key for CourtListener API. If None, will try to get from config.
            cache_results: Whether to cache API results
        """
        self.logger = logging.getLogger(__name__)
        
        # Get API key from config if not provided
        if api_key is None:
            try:
                from src.config import get_config_value
                api_key = get_config_value("COURTLISTENER_API_KEY")
            except ImportError:
                api_key = None
        
        self.api_key = api_key
        self.cache_results = cache_results
        
        # Initialize cache manager
        try:
            from src.cache_manager import get_cache_manager
            self.cache_manager = get_cache_manager()
        except ImportError:
            self.cache_manager = None
        
        # API base URL
        try:
            from src.config import get_config_value
            self.api_base_url = get_config_value(
                "COURTLISTENER_API_URL", "https://www.courtlistener.com/api/rest/v4/"
            ).rstrip("/")
        except ImportError:
            self.api_base_url = "https://www.courtlistener.com/api/rest/v4/"
        
        # Google Scholar API configuration
        self.serpapi_key = "c7dafc0c5d9a040b5fa2b9b1d70b26b4ac6858720005c54adc910c581e1da534"
        self.serpapi_base_url = "https://serpapi.com/search.json"
        
        # Citation patterns for extraction
        self.citation_patterns = [
            # Washington citations
            r'\d+\s+Wn\.?\s*\d+[a-z]*\s+\d+',
            # Federal citations
            r'\d+\s+F\.?\s*\d+[a-z]*\s+\d+',
            # Supreme Court citations
            r'\d+\s+U\.?\s*S\.?\s+\d+',
            # State citations
            r'\d+\s+[A-Z]{2}\.?\s*\d+[a-z]*\s+\d+',
            # General reporter pattern
            r'\d+\s+[A-Z]+\s*\d+[a-z]*\s+\d+'
        ]
        
        if not self.api_key:
            self.logger.warning("No CourtListener API key provided. Canonical name lookup will be limited.")
        
        self.citation_cache = {}
        self.base_url = "https://www.courtlistener.com/api/rest/v4"
        
        # Headers for API requests
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "CaseStrainer Enhanced Extractor"
        }
    
    def get_canonical_case_name(self, citation: str) -> Optional[str]:
        """Get canonical case name from CourtListener API or Google Scholar as fallback.
        
        Args:
            citation: The citation text to look up
            
        Returns:
            Canonical case name if found, None otherwise
        """
        # First try CourtListener API
        if self.api_key:
            try:
                # Check cache first
                if self.cache_results and self.cache_manager:
                    cached_result = self.cache_manager.get_citation(citation)
                    if cached_result:
                        return cached_result.get('canonical_name')
                
                # Make API request to CourtListener
                url = f"{self.api_base_url}/citation-lookup/"
                params = {"citation": citation}
                headers = {
                    "Authorization": f"Token {self.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "CaseStrainer Enhanced Extractor"
                }
                
                response = requests.get(url, params=params, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                # Extract canonical name from response
                if data.get('results'):
                    for result in data['results']:
                        if result.get('case_name') and result['case_name'] != 'Unknown Case':
                            canonical_name = result['case_name']
                            
                            # Cache the result
                            if self.cache_results and self.cache_manager:
                                cache_data = {
                                    'canonical_name': canonical_name,
                                    'source': 'courtlistener',
                                    'citation': citation,
                                    'timestamp': time.time()
                                }
                                self.cache_manager.set_citation(citation, cache_data)
                            
                            self.logger.info(f"Found canonical name in CourtListener: {canonical_name}")
                            return canonical_name
                
                # If CourtListener didn't find it, try Google Scholar
                self.logger.info(f"Citation not found in CourtListener, trying Google Scholar: {citation}")
                google_scholar_name = self.get_canonical_case_name_from_google_scholar(citation)
                if google_scholar_name:
                    return google_scholar_name
                
                # Cache negative result
                if self.cache_results and self.cache_manager:
                    cache_data = {
                        'canonical_name': None,
                        'source': 'none',
                        'citation': citation,
                        'timestamp': time.time()
                    }
                    self.cache_manager.set_citation(citation, cache_data)
                
                return None
                
            except Exception as e:
                self.logger.warning(f"Error with CourtListener API for '{citation}': {e}")
                # Fall back to Google Scholar
                return self.get_canonical_case_name_from_google_scholar(citation)
        
        # If no CourtListener API key, try Google Scholar directly
        return self.get_canonical_case_name_from_google_scholar(citation)
    
    def extract_case_name_from_context(self, text: str, citation: str, context_window: int = 500) -> Optional[str]:
        """
        Extract case name from text context around a citation.
        
        Args:
            text: The full text
            citation: The citation string
            context_window: Number of characters to look before/after citation
            
        Returns:
            Extracted case name or None
        """
        # Find citation position
        citation_pos = text.find(citation)
        if citation_pos == -1:
            return None
        
        # Get context before citation
        start_pos = max(0, citation_pos - context_window)
        context_before = text[start_pos:citation_pos]
        
        # Case name patterns (in order of preference)
        case_patterns = [
            # "Case Name v. Defendant" (most common)
            r'([A-Z][A-Za-z0-9\s&\'\.\-]{3,50}\s+v\.?\s+[A-Z][A-Za-z0-9\s&\'\.\-]{3,50})',
            # "Case Name, Defendant" (comma separated)
            r'([A-Z][A-Za-z0-9\s&\'\.\-]{3,50},\s+[A-Z][A-Za-z0-9\s&\'\.\-]{3,50})',
            # "In re Case Name" (bankruptcy/probate)
            r'(In\s+re\s+[A-Z][A-Za-z0-9\s&\'\.\-]{3,50})',
            # "State v. Defendant" or "United States v. Defendant"
            r'((?:State|United\s+States)\s+v\.?\s+[A-Z][A-Za-z0-9\s&\'\.\-]{3,50})',
            # Single party with more flexibility
            r'([A-Z][A-Za-z0-9\s&\'\.\-]{3,50})',
        ]
        
        # Look for case names in context before citation
        for pattern in case_patterns:
            matches = re.findall(pattern, context_before)
            if matches:
                # Get the last match (closest to citation)
                potential_case = matches[-1].strip()
                if self._is_valid_case_name(potential_case):
                    return potential_case
        
        return None
    
    def _is_valid_case_name(self, case_name: str) -> bool:
        """
        Check if a potential case name is valid.
        
        Args:
            case_name: The potential case name
            
        Returns:
            True if valid, False otherwise
        """
        if not case_name or len(case_name) < 3:
            return False
        
        # Remove common prefixes/suffixes
        cleaned = self._clean_case_name(case_name)
        
        # Check for common invalid patterns
        invalid_patterns = [
            r'^\d+$',  # Just numbers
            r'^[A-Z]\s*$',  # Single letter
            r'^[A-Z]\s+[A-Z]\s*$',  # Two letters
            r'^[A-Z]\s+[A-Z]\s+[A-Z]\s*$',  # Three letters
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, cleaned):
                return False
        
        return True
    
    def _clean_case_name(self, case_name: str) -> str:
        """
        Clean up a case name by removing common prefixes/suffixes.
        
        Args:
            case_name: The case name to clean
            
        Returns:
            Cleaned case name
        """
        # Remove common prefixes
        prefixes_to_remove = [
            'See, e.g.,',
            'See',
            'citing',
            'quoted in',
            'as cited in',
            'accord',
            'cf.',
            'but see',
            'contra',
        ]
        
        cleaned = case_name.strip()
        for prefix in prefixes_to_remove:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()
        
        # Remove common suffixes
        suffixes_to_remove = [
            ', supra',
            ', infra',
            ';',
            ',',
            '.',
        ]
        
        for suffix in suffixes_to_remove:
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)].strip()
        
        return cleaned
    
    def calculate_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two case names.
        
        Args:
            name1: First case name
            name2: Second case name
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not name1 or not name2:
            return 0.0
        
        # Normalize names for comparison
        norm1 = re.sub(r'[^\w\s]', '', name1.lower())
        norm2 = re.sub(r'[^\w\s]', '', name2.lower())
        
        # Use SequenceMatcher for similarity
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def extract_enhanced_case_names(self, text: str) -> List[Dict]:
        """
        Extract case names from text using enhanced method with API lookup.
        
        Args:
            text: The text to extract from
            
        Returns:
            List of dictionaries with citation and case name information
        """
        results = []
        
        # Extract all citations
        all_citations = []
        for pattern in self.citation_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                citation = match.group(0)
                all_citations.append({
                    'citation': citation,
                    'start': match.start(),
                    'end': match.end(),
                    'pattern': pattern
                })
        
        # Sort by position in text
        all_citations.sort(key=lambda x: x['start'])
        
        # Process each citation
        for citation_info in all_citations:
            citation = citation_info['citation']
            
            # Get canonical case name from API
            canonical_name = self.get_canonical_case_name(citation)
            
            # Extract case name from context
            extracted_name = self.extract_case_name_from_context(text, citation)
            
            # Determine best case name and source
            final_case_name = None
            confidence = 0.0
            method = "none"
            similarity_score = 0.0
            source = "none"
            
            if extracted_name and self._verify_in_text(extracted_name, text):
                # We have a valid extracted name from the document
                if canonical_name:
                    similarity_score = self.calculate_similarity(canonical_name, extracted_name)
                    if similarity_score > 0.7:
                        confidence = 0.95
                        method = "extracted_api_confirmed"
                        # Determine source based on where canonical name came from
                        source = self._get_canonical_source(citation)
                    else:
                        confidence = 0.8
                        method = "extracted_api_mismatch"
                        source = self._get_canonical_source(citation)
                else:
                    confidence = 0.7
                    method = "extracted_only"
                
                final_case_name = extracted_name
            elif canonical_name:
                # Only API result available, but we can't use it directly
                confidence = 0.0
                method = "api_only_no_text_match"
                source = self._get_canonical_source(citation)
            
            # Add to results
            result = {
                'citation': citation,
                'case_name': final_case_name,
                'confidence': confidence,
                'method': method,
                'canonical_name': canonical_name,
                'extracted_name': extracted_name,
                'position': citation_info['start'],
                'similarity_score': similarity_score,
                'source': source
            }
            
            results.append(result)
            
            # Rate limiting - be nice to the API
            if canonical_name:
                time.sleep(0.1)
        
        return results
    
    def _verify_in_text(self, extracted_name: str, text: str) -> bool:
        """Verify that the extracted name is actually a substring of the original text"""
        if not extracted_name:
            return False
        
        # Check if the exact extracted name exists in the text
        return extracted_name in text
    
    def get_extraction_stats(self, results: List[Dict]) -> Dict:
        """
        Get statistics about the extraction results.
        
        Args:
            results: List of extraction results
            
        Returns:
            Dictionary with statistics
        """
        total = len(results)
        if total == 0:
            return {'total': 0}
        
        stats = {
            'total': total,
            'with_case_names': len([r for r in results if r['case_name']]),
            'api_success': len([r for r in results if r['canonical_name']]),
            'extracted_success': len([r for r in results if r['extracted_name']]),
            'high_confidence': len([r for r in results if r['confidence'] >= 0.8]),
            'method_breakdown': {}
        }
        
        # Method breakdown
        for result in results:
            method = result['method']
            stats['method_breakdown'][method] = stats['method_breakdown'].get(method, 0) + 1
        
        return stats
    
    def get_citation_url(self, citation: str) -> Optional[str]:
        """Get the URL for a citation from CourtListener, legal databases, or Google Scholar fallback.
        
        Args:
            citation: The citation text
            
        Returns:
            URL to the case on CourtListener, legal databases, or Google Scholar, or None if not found
        """
        # First try CourtListener
        if self.api_key:
            try:
                # Check cache first
                if self.cache_results and self.cache_manager:
                    cached_result = self.cache_manager.get_citation(citation)
                    if cached_result:
                        verification_result = json.loads(cached_result.get('verification_result', '{}'))
                        if verification_result.get('results'):
                            # Return the first result's URL
                            for result in verification_result['results']:
                                if result.get('absolute_url'):
                                    return f"https://www.courtlistener.com{result['absolute_url']}"
                
                # Make API request to CourtListener
                url = f"{self.api_base_url}/citation-lookup/"
                params = {"citation": citation}
                headers = {
                    "Authorization": f"Token {self.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "CaseStrainer Enhanced Extractor"
                }
                
                response = requests.get(url, params=params, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                # Extract URL from response
                if data.get('results'):
                    for result in data['results']:
                        if result.get('absolute_url'):
                            courtlistener_url = f"https://www.courtlistener.com{result['absolute_url']}"
                            
                            # Cache the result
                            if self.cache_results and self.cache_manager:
                                cache_data = {
                                    'citation_url': courtlistener_url,
                                    'source': 'courtlistener',
                                    'citation': citation,
                                    'timestamp': time.time()
                                }
                                self.cache_manager.set_citation(f"url_{citation}", cache_data)
                            
                            return courtlistener_url
                
            except Exception as e:
                self.logger.warning(f"Error getting CourtListener URL for '{citation}': {e}")
        
        # Fallback to legal database URLs (prioritize legal databases over Google Scholar)
        legal_db_url = self.get_legal_database_url(citation)
        if legal_db_url:
            return legal_db_url
        
        # Fallback to Google Scholar URL (for academic/research citations)
        google_scholar_url = self.get_google_scholar_url(citation)
        if google_scholar_url:
            return google_scholar_url
        
        # Final fallback to general legal search
        return self.get_general_legal_search_url(citation)
    
    def get_legal_database_url(self, citation: str) -> Optional[str]:
        """Get a URL for a citation from legal databases like vLex, CaseMine, Leagle, etc.
        
        Args:
            citation: The citation text
            
        Returns:
            Legal database URL for the citation, or None if not found
        """
        try:
            # Check cache first
            cache_key = f"legal_db_url_{citation}"
            if self.cache_results and self.cache_manager:
                cached_result = self.cache_manager.get_citation(cache_key)
                if cached_result:
                    return cached_result.get('url')
            
            # Try different legal databases based on citation type
            citation_lower = citation.lower()
            
            # vLex for international and some US cases
            if any(term in citation_lower for term in ['u.s.', 'f.', 's.ct.', 'l.ed.']):
                search_query = citation.replace(' ', '+')
                vlex_url = f"https://vlex.com/sites/search?q={search_query}"
                
                # Cache the result
                if self.cache_results and self.cache_manager:
                    cache_data = {
                        'url': vlex_url,
                        'source': 'vlex',
                        'citation': citation,
                        'timestamp': time.time()
                    }
                    self.cache_manager.set_citation(cache_key, cache_data)
                
                self.logger.info(f"Generated vLex URL for citation: {citation}")
                return vlex_url
            
            # CaseMine for Indian and some international cases
            elif any(term in citation_lower for term in ['indian', 'india', 'supreme court', 'high court']):
                search_query = citation.replace(' ', '+')
                casemine_url = f"https://www.casemine.com/search?q={search_query}"
                
                # Cache the result
                if self.cache_results and self.cache_manager:
                    cache_data = {
                        'url': casemine_url,
                        'source': 'casemine',
                        'citation': citation,
                        'timestamp': time.time()
                    }
                    self.cache_manager.set_citation(cache_key, cache_data)
                
                self.logger.info(f"Generated CaseMine URL for citation: {citation}")
                return casemine_url
            
            # Leagle for US cases
            elif any(term in citation_lower for term in ['u.s.', 'f.', 's.ct.', 'l.ed.', 'f.2d', 'f.3d']):
                # Check specifically for F.2d and F.3d patterns for Leagle
                if any(pattern in citation_lower for pattern in ['f.2d', 'f.3d']):
                    search_query = citation.replace(' ', '+')
                    leagle_url = f"https://www.leagle.com/search?q={search_query}"
                    
                    # Cache the result
                    if self.cache_results and self.cache_manager:
                        cache_data = {
                            'url': leagle_url,
                            'source': 'leagle',
                            'citation': citation,
                            'timestamp': time.time()
                        }
                        self.cache_manager.set_citation(cache_key, cache_data)
                    
                    self.logger.info(f"Generated Leagle URL for citation: {citation}")
                    return leagle_url
                else:
                    # For other US cases, use vLex
                    search_query = citation.replace(' ', '+')
                    vlex_url = f"https://vlex.com/sites/search?q={search_query}"
                    
                    # Cache the result
                    if self.cache_results and self.cache_manager:
                        cache_data = {
                            'url': vlex_url,
                            'source': 'vlex',
                            'citation': citation,
                            'timestamp': time.time()
                        }
                        self.cache_manager.set_citation(cache_key, cache_data)
                    
                    self.logger.info(f"Generated vLex URL for citation: {citation}")
                    return vlex_url
            
            # Default to vLex for other cases
            else:
                search_query = citation.replace(' ', '+')
                vlex_url = f"https://vlex.com/sites/search?q={search_query}"
                
                # Cache the result
                if self.cache_results and self.cache_manager:
                    cache_data = {
                        'url': vlex_url,
                        'source': 'vlex',
                        'citation': citation,
                        'timestamp': time.time()
                    }
                    self.cache_manager.set_citation(cache_key, cache_data)
                
                self.logger.info(f"Generated vLex URL for citation: {citation}")
                return vlex_url
            
        except Exception as e:
            self.logger.warning(f"Error generating legal database URL for '{citation}': {e}")
            return None
    
    def get_general_legal_search_url(self, citation: str) -> Optional[str]:
        """Get a general legal search URL for a citation using legal-specific search engines.
        
        Args:
            citation: The citation text
            
        Returns:
            General legal search URL for the citation, or None if not found
        """
        try:
            # Check cache first
            cache_key = f"legal_search_url_{citation}"
            if self.cache_results and self.cache_manager:
                cached_result = self.cache_manager.get_citation(cache_key)
                if cached_result:
                    return cached_result.get('url')
            
            # Use Justia for general legal search
            search_query = citation.replace(' ', '+')
            justia_url = f"https://law.justia.com/search?query={search_query}"
            
            # Cache the result
            if self.cache_results and self.cache_manager:
                cache_data = {
                    'url': justia_url,
                    'source': 'justia',
                    'citation': citation,
                    'timestamp': time.time()
                }
                self.cache_manager.set_citation(cache_key, cache_data)
            
            self.logger.info(f"Generated Justia URL for citation: {citation}")
            return justia_url
            
        except Exception as e:
            self.logger.warning(f"Error generating general legal search URL for '{citation}': {e}")
            return None
    
    def get_google_scholar_url(self, citation: str) -> Optional[str]:
        """Get the Google Scholar URL for a citation.
        
        Args:
            citation: The citation text
            
        Returns:
            Google Scholar search URL for the citation, or None if not found
        """
        try:
            # Check cache first
            cache_key = f"scholar_url_{citation}"
            if self.cache_results and self.cache_manager:
                cached_result = self.cache_manager.get_citation(cache_key)
                if cached_result:
                    return cached_result.get('url')
            
            # Create Google Scholar search URL
            # Use the citation as the search query
            search_query = citation.replace(' ', '+')
            google_scholar_url = f"https://scholar.google.com/scholar?q={search_query}&hl=en&as_sdt=0,5"
            
            # Cache the result
            if self.cache_results and self.cache_manager:
                cache_data = {
                    'url': google_scholar_url,
                    'source': 'google_scholar',
                    'citation': citation,
                    'timestamp': time.time()
                }
                self.cache_manager.set_citation(cache_key, cache_data)
            
            self.logger.info(f"Generated Google Scholar URL for citation: {citation}")
            return google_scholar_url
            
        except Exception as e:
            self.logger.warning(f"Error generating Google Scholar URL for '{citation}': {e}")
            return None
    
    def get_canonical_case_name_from_google_scholar(self, citation: str) -> Optional[str]:
        """Get canonical case name from Google Scholar using SerpApi.
        
        Args:
            citation: The citation text to search for
            
        Returns:
            Canonical case name if found, None otherwise
        """
        if not self.serpapi_key:
            return None
            
        try:
            # Check cache first
            cache_key = f"scholar_{citation}"
            if self.cache_results and self.cache_manager:
                cached_result = self.cache_manager.get_citation(cache_key)
                if cached_result:
                    return cached_result.get('canonical_name')
            
            # Prepare search query - use the citation as the search term
            params = {
                'engine': 'google_scholar',
                'q': citation,
                'api_key': self.serpapi_key,
                'hl': 'en',
                'as_sdt': '0,5'  # Include patents and legal documents
            }
            
            self.logger.info(f"Searching Google Scholar for citation: {citation}")
            response = requests.get(self.serpapi_base_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            # Extract case name from search results
            if data.get('organic_results'):
                for result in data['organic_results']:
                    title = result.get('title', '')
                    snippet = result.get('snippet', '')
                    
                    # Look for case name patterns in title and snippet
                    case_name = self._extract_case_name_from_scholar_result(title, snippet)
                    if case_name:
                        # Cache the result
                        if self.cache_results and self.cache_manager:
                            cache_data = {
                                'canonical_name': case_name,
                                'source': 'google_scholar',
                                'citation': citation,
                                'timestamp': time.time()
                            }
                            self.cache_manager.set_citation(cache_key, cache_data)
                        
                        self.logger.info(f"Found case name in Google Scholar: {case_name}")
                        return case_name
            
            # If no results found, cache the negative result
            if self.cache_results and self.cache_manager:
                cache_data = {
                    'canonical_name': None,
                    'source': 'google_scholar',
                    'citation': citation,
                    'timestamp': time.time()
                }
                self.cache_manager.set_citation(cache_key, cache_data)
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error searching Google Scholar for '{citation}': {e}")
            return None
    
    def _get_canonical_source(self, citation: str) -> str:
        """Determine the source of the canonical case name."""
        # Check cache to see where the canonical name came from
        if self.cache_results and self.cache_manager:
            cached_result = self.cache_manager.get_citation(citation)
            if cached_result:
                return cached_result.get('source', 'unknown')
        
        # If not in cache, we can't determine the source
        return "unknown"
    
    def _extract_case_name_from_scholar_result(self, title: str, snippet: str) -> Optional[str]:
        """Extract case name from Google Scholar search result.
        
        Args:
            title: The title of the search result
            snippet: The snippet/description of the search result
            
        Returns:
            Extracted case name if found, None otherwise
        """
        # Combine title and snippet for analysis
        text = f"{title} {snippet}"
        
        # Look for common case name patterns
        patterns = [
            # Pattern: "Case Name v. Another Party"
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+v\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            # Pattern: "Case Name v. Another Party,"
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+v\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),',
            # Pattern: "Case Name v. Another Party."
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+v\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\.',
            # Pattern: "Case Name v. Another Party,"
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+v\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+',
            # Pattern: "Case Name v. Another Party"
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+v\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Clean up the match
                case_name = match.strip()
                if len(case_name) > 10 and 'v.' in case_name:  # Basic validation
                    return case_name
        
        return None 