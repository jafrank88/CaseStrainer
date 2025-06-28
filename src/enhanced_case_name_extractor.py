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
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import nltk
from nltk.tokenize import sent_tokenize
from src.case_name_extraction_core import extract_case_name_triple, extract_case_name_from_text, extract_case_name_hinted

class EnhancedCaseNameExtractor:
    def __init__(self, api_key: Optional[str] = None, cache_results: bool = True):
        """
        Initialize the enhanced case name extractor.
        
        Args:
            api_key: API key for CourtListener API. If None, will try to get from config.
            cache_results: Whether to cache API results
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        
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
        
        # Browser-like headers for web scraping
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def get_canonical_case_name(self, citation: str) -> Optional[dict]:
        print(f"[PRINT] get_canonical_case_name called for: {citation}")
        """Get canonical case name and date from CourtListener API or Google Scholar as fallback.
        Returns a dictionary with 'case_name' and 'date' keys.
        """
        import re
        tried_citations = set()
        forms_to_try = [citation]
        
        # Add normalized forms for Washington
        from src.citation_format_utils import normalize_washington_synonyms
        from src.citation_patterns import normalize_washington_citation
        norm1 = normalize_washington_synonyms(citation)
        norm2 = normalize_washington_citation(citation)
        for form in (norm1, norm2):
            if form and form not in forms_to_try:
                forms_to_try.append(form)
        
        # Enhanced Washington citation normalization
        washington_variants = self._generate_washington_variants(citation)
        forms_to_try.extend(washington_variants)
        
        # Add generic normalization for other states/reporters
        generic_variants = set()
        # Remove/replace common spaces and periods in reporter abbreviations
        generic_variants.add(re.sub(r"\bApp\.\b", "App", citation))
        generic_variants.add(re.sub(r"\bApp\b", "App.", citation))
        generic_variants.add(re.sub(r"\bDiv\.\b", "Div", citation))
        generic_variants.add(re.sub(r"\bDiv\b", "Div.", citation))
        generic_variants.add(re.sub(r"\bCal\.\b", "Cal", citation))
        generic_variants.add(re.sub(r"\bCal\b", "Cal.", citation))
        generic_variants.add(re.sub(r"\bN\.Y\.\b", "NY", citation))
        generic_variants.add(re.sub(r"\bNY\b", "N.Y.", citation))
        generic_variants.add(re.sub(r"\bIll\.\b", "Ill", citation))
        generic_variants.add(re.sub(r"\bIll\b", "Ill.", citation))
        generic_variants.add(re.sub(r"\bTex\.\b", "Tex", citation))
        generic_variants.add(re.sub(r"\bTex\b", "Tex.", citation))
        generic_variants.add(re.sub(r"\bPa\.\b", "Pa", citation))
        generic_variants.add(re.sub(r"\bPa\b", "Pa.", citation))
        
        # Add more comprehensive normalization patterns
        # Handle common citation format variations
        base_citation = re.sub(r'\s+', ' ', citation).strip()
        
        # Try different spacing patterns
        spacing_variants = [
            base_citation,
            re.sub(r'(\d+)\s+([A-Z])', r'\1 \2', base_citation),  # Add space between number and letter
            re.sub(r'([A-Z])\s+(\d+)', r'\1 \2', base_citation),  # Add space between letter and number
            re.sub(r'(\d+)\s*([A-Z]{2,})\s*(\d+)', r'\1 \2 \3', base_citation),  # Standardize reporter spacing
        ]
        forms_to_try.extend(spacing_variants)
        
        # Try different reporter abbreviation formats
        reporter_variants = []
        # Washington specific
        if 'Wn.' in citation or 'Wn' in citation:
            reporter_variants.extend([
                re.sub(r'Wn\.?\s*', 'Wash. ', citation),
                re.sub(r'Wn\.?\s*', 'Washington ', citation),
                re.sub(r'Wn\.?\s*', 'Wn. ', citation),
            ])
        # Federal specific
        if 'F.' in citation or 'F.3d' in citation or 'F.2d' in citation:
            reporter_variants.extend([
                re.sub(r'F\.?\s*(\d+)d', r'F.\1d', citation),
                re.sub(r'F\.?\s*(\d+)d', r'F \1d', citation),
            ])
        # Supreme Court specific
        if 'U.S.' in citation or 'US' in citation:
            reporter_variants.extend([
                re.sub(r'U\.?\s*S\.?', 'U.S.', citation),
                re.sub(r'U\.?\s*S\.?', 'US', citation),
            ])
        
        forms_to_try.extend(reporter_variants)
        
        # Add parallel citation attempts
        parallel_variants = self._generate_parallel_citations(citation)
        forms_to_try.extend(parallel_variants)
        
        # Remove duplicates and empty strings
        forms_to_try = [form for form in forms_to_try if form and form.strip()]
        forms_to_try = list(dict.fromkeys(forms_to_try))  # Remove duplicates while preserving order
        
        # Try all forms in order
        for form in forms_to_try:
            if not form or form in tried_citations:
                continue
            tried_citations.add(form)
            
            # Check cache first
            if self.cache_results and self.cache_manager:
                cached_result = self.cache_manager.get_citation(form)
                if cached_result and cached_result.get('canonical_name'):
                    return {
                        'case_name': cached_result.get('canonical_name'),
                        'date': cached_result.get('canonical_date')
                    }
            
            # Make API request to CourtListener
            if self.api_key:
                try:
                    # Try citation-lookup endpoint first (most precise) - use POST with JSON
                    url = f"{self.api_base_url}/citation-lookup/"
                    headers = {
                        "Authorization": f"Token {self.api_key}",
                        "Content-Type": "application/json",
                        "User-Agent": "CaseStrainer Enhanced Extractor"
                    }
                    response = requests.post(url, json={"text": form}, headers=headers, timeout=10)

                    if response.status_code == 200:
                        data = response.json()
                        if data.get('results'):
                            result = data['results'][0]
                            return {
                                'case_name': result['case_name'],
                                'date': result['date']
                            }
                        else:
                            self.logger.warning("No results found for citation: " + form)
                    else:
                        self.logger.warning("API request failed with status code: " + str(response.status_code))
                except Exception as e:
                    self.logger.warning("Exception occurred while making API request: " + str(e))
        
        self.logger.warning("No canonical case name found for citation: " + citation)
        return None 

    def get_citation_url(self, citation: str) -> Optional[str]:
        """Get direct URL to citation in legal databases."""
        try:
            # Try CourtListener first (most reliable)
            if self.api_key:
                try:
                    # Try citation-lookup endpoint first - use POST with JSON
                    url = f"{self.api_base_url}/citation-lookup/"
                    headers = {
                        "Authorization": f"Token {self.api_key}",
                        "Content-Type": "application/json",
                        "User-Agent": "CaseStrainer Enhanced Extractor"
                    }
                    response = requests.post(url, json={"text": citation}, headers=headers, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Parse citation-lookup response (returns a list)
                    if isinstance(data, list) and len(data) > 0:
                        citation_data = data[0]
                        if citation_data.get('clusters') and len(citation_data['clusters']) > 0:
                            cluster = citation_data['clusters'][0]
                            if cluster.get('absolute_url'):
                                return f"https://www.courtlistener.com{cluster['absolute_url']}"
                    
                    # If citation-lookup fails, try search endpoint
                    search_url = f"{self.api_base_url}/search/"
                    search_params = {
                        "q": citation,
                        "type": "o",  # opinions only
                        "stat_Precedential": "on"
                    }
                    search_response = requests.get(search_url, params=search_params, headers=headers, timeout=10)
                    search_response.raise_for_status()
                    search_data = search_response.json()
                    
                    if search_data.get('results'):
                        for result in search_data['results']:
                            if result.get('absolute_url'):
                                return f"https://www.courtlistener.com{result['absolute_url']}"
                                
                except Exception as e:
                    self.logger.warning(f"Error getting CourtListener URL for '{citation}': {e}")
            
            # Fallback to other legal databases with search functionality
            # Justia - has good search
            justia_url = f"https://law.justia.com/search?query={quote_plus(citation)}"
            
            # FindLaw - has search
            findlaw_url = f"https://caselaw.findlaw.com/search?query={quote_plus(citation)}"
            
            # Casetext - has search
            casetext_url = f"https://casetext.com/search?q={quote_plus(citation)}"
            
            # Return Justia as primary fallback (most reliable)
            return justia_url
            
        except Exception as e:
            self.logger.warning(f"Error generating citation URL for '{citation}': {e}")
            return None 

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
        
        # Group citations by sentence or comma separation for parallel handling
        nltk.download('punkt', quiet=True)
        sentences = sent_tokenize(text)
        # Map citation string to sentence index
        citation_to_sentence = {}
        for idx, sentence in enumerate(sentences):
            for citation_info in all_citations:
                if citation_info['citation'] in sentence:
                    citation_to_sentence[citation_info['citation']] = idx
        # Group citations by sentence
        sentence_to_citations = {}
        for citation, idx in citation_to_sentence.items():
            sentence_to_citations.setdefault(idx, []).append(citation)
        # Extract case names for each sentence group
        sentence_case_names = {}
        for idx, citation_list in sentence_to_citations.items():
            sentence = sentences[idx]
            # Try to extract a case name from the sentence context
            extracted_name = self.extract_case_name_from_context(sentence, citation_list[0])
            if extracted_name:
                for citation in citation_list:
                    sentence_case_names[citation] = extracted_name
        
        # Process each citation
        for citation_info in all_citations:
            citation = citation_info['citation']
            
            # Get canonical case name from API
            canonical_result = self.get_canonical_case_name(citation)
            canonical_name = canonical_result.get('case_name') if canonical_result else None
            
            # Use group-extracted name if available
            extracted_name = sentence_case_names.get(citation)
            if not extracted_name:
                extracted_name = self.extract_case_name_from_context(text, citation)

            # If we have a canonical name, try hinted extraction if needed
            hinted_name = None
            hinted_score = 0.0
            if canonical_name:
                # Only use hinted extraction if extracted_name is missing or not similar
                similarity_score = 0.0
                if extracted_name:
                    similarity_score = self.calculate_similarity(canonical_name, extracted_name)
                if not extracted_name or similarity_score < 0.7:
                    hinted_name = extract_case_name_hinted(text, citation, canonical_name)
                    if hinted_name:
                        extracted_name = hinted_name
                        similarity_score = 1.0  # Perfect match since we used the canonical name

            # Determine best case name and source
            final_case_name = None
            confidence = 0.0
            method = "none"
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
            
            # Add detailed debug logging
            self.logger.info(f"[DEBUG] Citation: {citation} | Extracted: {extracted_name} | Canonical: {canonical_name} | Final: {final_case_name} | Method: {method} | Confidence: {confidence}")
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
    
    def _get_canonical_source(self, citation: str) -> str:
        """Determine the source of the canonical case name."""
        if not self.api_key:
            return "none"
        
        # For now, assume CourtListener if we have an API key
        return "courtlistener"
    
    def calculate_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two case names."""
        if not name1 or not name2:
            return 0.0
        
        # Normalize names for comparison
        norm1 = re.sub(r'\s+', ' ', name1.lower().strip())
        norm2 = re.sub(r'\s+', ' ', name2.lower().strip())
        
        # Use SequenceMatcher for similarity
        return SequenceMatcher(None, norm1, norm2).ratio()

    def extract_case_name_from_context(self, text: str, citation: str, context_window: int = 500) -> Optional[str]:
        """
        Extract case name from text context around a citation using the unified API.
        """
        return extract_case_name_from_text(text, citation, context_window)