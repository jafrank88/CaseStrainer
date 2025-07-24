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

# Import canonical case name extraction functions
from src.case_name_extraction_core import extract_case_name_from_text, extract_case_name_triple_from_text, extract_case_name_hinted
from src.extract_case_name import clean_case_name, is_valid_case_name
from src.citation_utils_consolidated import normalize_washington_synonyms

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
                    response = requests.post(url, data={"text": form}, headers=headers, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    print(f"[PRINT] Citation-lookup response for '{form}': {json.dumps(data, default=str)[:500]}")
                    # Debug: log the actual response structure
                    self.logger.info(f"[DEBUG] Citation-lookup response for '{form}': {json.dumps(data, default=str)[:500]}")
                    
                    # Parse citation-lookup response (returns a list)
                    if isinstance(data, list) and len(data) > 0:
                        citation_data = data[0]
                        self.logger.info(f"[DEBUG] Citation data keys: {list(citation_data.keys()) if isinstance(citation_data, dict) else 'Not a dict'}")
                        
                        if citation_data.get('clusters') and len(citation_data['clusters']) > 0:
                            cluster = citation_data['clusters'][0]
                            self.logger.info(f"[DEBUG] First cluster keys: {list(cluster.keys()) if isinstance(cluster, dict) else 'Not a dict'}")
                            
                            # Try to get case name from cluster
                            case_name = self._extract_case_name_from_cluster(cluster)
                            self.logger.info(f"[DEBUG] Extracted case name from cluster: {case_name}")
                            
                            # Try to get canonical date from cluster
                            canonical_date = self._extract_canonical_date_from_cluster(cluster)
                            self.logger.info(f"[DEBUG] Extracted canonical date from cluster: {canonical_date}")
                            
                            if case_name and case_name != 'Unknown Case':
                                # Cache the result
                                if self.cache_results and self.cache_manager:
                                    cache_data = {
                                        'canonical_name': case_name,
                                        'canonical_date': canonical_date,
                                        'source': 'courtlistener_citation_lookup',
                                        'citation': form,
                                        'timestamp': time.time()
                                    }
                                    self.cache_manager.set_citation(form, cache_data)
                                self.logger.info(f"[PATCH] Found canonical name in CourtListener citation-lookup for form '{form}': {case_name}")
                                return {
                                    'case_name': case_name,
                                    'date': canonical_date
                                }
                        else:
                            self.logger.info(f"[DEBUG] No clusters found in citation data")
                    else:
                        self.logger.info(f"[DEBUG] Response is not a list or is empty")
                    
                    # If citation-lookup fails, try search endpoint as fallback
                    self.logger.info(f"[PATCH] Citation-lookup failed for '{form}', trying search endpoint...")
                    search_url = f"{self.api_base_url}/search/"
                    search_params = {
                        "q": form,
                        "type": "o",  # opinions only
                        "stat_Precedential": "on"
                    }
                    search_response = requests.get(search_url, params=search_params, headers=headers, timeout=10)
                    search_response.raise_for_status()
                    search_data = search_response.json()
                    
                    # Parse search response
                    if search_data.get('results'):
                        for result in search_data['results']:
                            if result.get('caseName') and result['caseName'] != 'Unknown Case':
                                canonical_name = result['caseName']
                                canonical_date = result.get('dateFiled') or result.get('date_created')
                                # Cache the result
                                if self.cache_results and self.cache_manager:
                                    cache_data = {
                                        'canonical_name': canonical_name,
                                        'canonical_date': canonical_date,
                                        'source': 'courtlistener_search',
                                        'citation': form,
                                        'timestamp': time.time()
                                    }
                                    self.cache_manager.set_citation(form, cache_data)
                                self.logger.info(f"[PATCH] Found canonical name in CourtListener search for form '{form}': {canonical_name}")
                                return {
                                    'case_name': canonical_name,
                                    'date': canonical_date
                                }
                                
                except Exception as e:
                    self.logger.warning(f"[PATCH] Error with CourtListener API for '{form}': {e}")
        
        # If all forms fail, try Google Scholar
        google_result = self.get_canonical_case_name_from_google_scholar(citation)
        if google_result:
            return {
                'case_name': google_result,
                'date': None  # Google Scholar doesn't provide dates
            }
        
        return None
    
    def _generate_washington_variants(self, citation: str) -> List[str]:
        """Generate Washington-specific citation variants with proper normalization."""
        variants = []
        
        # First, normalize Wn. to Wash. for better search results
        normalized_citation = citation.replace('Wn.', 'Wash.').replace('Wn ', 'Wash. ')
        
        # Washington citation patterns with proper normalization
        washington_patterns = [
            # Standard Washington patterns (Wn. -> Wash.)
            (r'(\d+)\s+Wn\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wash. \2 \3'),
            (r'(\d+)\s+Wn\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Washington \2 \3'),
            (r'(\d+)\s+Wn\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wn. \2 \3'),
            (r'(\d+)\s+Wn\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wn \2 \3'),
            
            # Washington App patterns (Wn. App. -> Wash. App.)
            (r'(\d+)\s+Wn\.?\s*App\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wash. App. \2 \3'),
            (r'(\d+)\s+Wn\.?\s*App\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Washington App. \2 \3'),
            (r'(\d+)\s+Wn\.?\s*App\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wn. App. \2 \3'),
            
            # Washington 2d patterns (Wn. 2d -> Wash. 2d)
            (r'(\d+)\s+Wn\.?\s*2d\s+(\d+[a-z]?)\s+(\d+)', r'\1 Wash. 2d \2 \3'),
            (r'(\d+)\s+Wn\.?\s*2d\s+(\d+[a-z]?)\s+(\d+)', r'\1 Washington 2d \2 \3'),
            
            # Handle cases where Wn. is already in the citation
            (r'(\d+)\s+Wash\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wn. \2 \3'),
            (r'(\d+)\s+Washington\s+(\d+[a-z]?)\s+(\d+)', r'\1 Wn. \2 \3'),
        ]
        
        # Apply patterns to both original and normalized citations
        for original, replacement in washington_patterns:
            # Apply to original citation
            variant = re.sub(original, replacement, citation, flags=re.IGNORECASE)
            if variant != citation:
                variants.append(variant)
            
            # Apply to normalized citation (Wn. -> Wash.)
            variant = re.sub(original, replacement, normalized_citation, flags=re.IGNORECASE)
            if variant != normalized_citation and variant not in variants:
                variants.append(variant)
        
        # Add the normalized citation itself
        if normalized_citation != citation:
            variants.append(normalized_citation)
        
        # Add specific Washington variants for better search
        if 'Wn.' in citation or 'Wn ' in citation:
            # Convert Wn. to Wash. for better API compatibility
            wash_variant = citation.replace('Wn.', 'Wash.').replace('Wn ', 'Wash. ')
            if wash_variant not in variants:
                variants.append(wash_variant)
            
            # Also try Washington (full word)
            wash_full_variant = citation.replace('Wn.', 'Washington ').replace('Wn ', 'Washington ')
            if wash_full_variant not in variants:
                variants.append(wash_full_variant)
        
        return variants
    
    def _generate_parallel_citations(self, citation: str) -> List[str]:
        """Generate parallel citation attempts for common legal databases."""
        variants = []
        
        # Common parallel citation patterns
        # If it's a Washington citation, try federal equivalents
        if 'Wn.' in citation or 'Wash.' in citation:
            # Try to find federal parallel citations
            # This would require a lookup table or API call
            pass
        
        # If it's a federal citation, try state equivalents
        if 'F.' in citation or 'U.S.' in citation:
            # Try to find state parallel citations
            pass
        
        return variants
    
    def _extract_case_name_from_cluster(self, cluster_data: dict) -> str:
        """Extract case name from CourtListener cluster data.
        NOTE: Uses 'case_name' as the canonical name if available, with 'case_name_short' and 'case_name_full' as fallbacks.
        """
        try:
            # Use 'case_name' as the canonical name if available
            case_name = (
                cluster_data.get("case_name")
                or cluster_data.get("case_name_short")
                or cluster_data.get("case_name_full")
                or cluster_data.get("name")
                or cluster_data.get("title")
            )
            if case_name and case_name != "Unknown Case":
                return case_name
            # If still no case name, try to extract from absolute_url
            if cluster_data.get("absolute_url"):
                url_path = cluster_data["absolute_url"]
                if "/opinion/" in url_path:
                    parts = url_path.split("/")
                    if len(parts) >= 4:
                        case_slug = parts[-2]
                        case_name = case_slug.replace("-", " ").title()
                        return case_name
            return "Unknown Case"
        except Exception as e:
            self.logger.warning(f"Error extracting case name from cluster: {e}")
            return "Unknown Case"
    
    def _extract_canonical_date_from_cluster(self, cluster_data: dict) -> str:
        """Extract canonical date from CourtListener cluster data.
        NOTE: Uses 'date_filed' as the canonical date if available, with other date fields as fallbacks.
        Returns just the year (e.g., '1954' from '1954-05-17').
        """
        try:
            # Use 'date_filed' as the canonical date if available
            canonical_date = cluster_data.get("date_filed")
            if canonical_date:
                # Extract year from ISO date string (e.g., '1954-05-17' -> '1954')
                if isinstance(canonical_date, str) and '-' in canonical_date:
                    year = canonical_date.split('-')[0]
                    if year.isdigit():
                        return year
            
            # Fallback to other date fields
            fallback_dates = [
                cluster_data.get("date_created"),
                cluster_data.get("date_modified"),
            ]
            
            # Check if there are other_dates available
            other_dates = cluster_data.get("other_dates", [])
            if isinstance(other_dates, list) and other_dates:
                fallback_dates.extend(other_dates)
            
            # Return the first available date's year
            for date in fallback_dates:
                if date and isinstance(date, str) and '-' in date:
                    year = date.split('-')[0]
                    if year.isdigit():
                        return year
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error extracting canonical date from cluster: {e}")
            return None
    
    def extract_case_name_from_context(self, text: str, citation: str, context_window: int = 500) -> Optional[str]:
        """
        Extract case name from text context around a citation using the unified API.
        """
        return extract_case_name_from_text(text, citation, context_window)
    
    def _is_valid_case_name(self, case_name: str) -> bool:
        """
        Check if a potential case name is valid using canonical function.
        
        Args:
            case_name: The potential case name
            
        Returns:
            True if valid, False otherwise
        """
        return is_valid_case_name(case_name)
    
    def _clean_case_name(self, case_name: str) -> str:
        """
        Clean up a case name using canonical function.
        
        Args:
            case_name: The case name to clean
            
        Returns:
            Cleaned case name
        """
        return clean_case_name(case_name)
    
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
            canonical_name = self.get_canonical_case_name(citation)
            
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
                    response = requests.post(url, data={"text": citation}, headers=headers, timeout=10)
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
        """Get canonical case name from Google Scholar using direct web scraping.
        
        Args:
            citation: The citation text to search for
            
        Returns:
            Canonical case name if found, None otherwise
        """
        try:
            # Check cache first
            cache_key = f"scholar_{citation}"
            if self.cache_results and self.cache_manager:
                cached_result = self.cache_manager.get_citation(cache_key)
                if cached_result:
                    return cached_result.get('canonical_name')
            
            # Add delay to prevent rate limiting
            time.sleep(2)  # 2 second delay between requests
            
            # Build Google Scholar search URL
            search_query = quote_plus(citation)
            scholar_url = f"https://scholar.google.com/scholar?q={search_query}&hl=en&as_sdt=0,5"
            
            self.logger.info(f"Searching Google Scholar for citation: {citation}")
            
            # Fetch the search results page with longer timeout
            response = requests.get(scholar_url, headers=self.headers, timeout=30)
            
            # Check for rate limiting
            if response.status_code == 429:
                self.logger.warning(f"Google Scholar rate limited for citation: {citation}")
                # Cache negative result to avoid repeated attempts
                if self.cache_results and self.cache_manager:
                    cache_data = {
                        'canonical_name': None,
                        'source': 'google_scholar_rate_limited',
                        'citation': citation,
                        'timestamp': time.time()
                    }
                    self.cache_manager.set_citation(cache_key, cache_data)
                return None
            
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for search result titles (Google Scholar result titles are in h3 tags)
            result_titles = soup.find_all('h3', class_='gs_rt')
            
            if result_titles:
                # Get the first result title
                first_title = result_titles[0].get_text(strip=True)
                
                # Also look for snippets which might contain case names
                result_snippets = soup.find_all('div', class_='gs_rs')
                first_snippet = result_snippets[0].get_text(strip=True) if result_snippets else ""
                
                # Extract case name from title and snippet
                case_name = self._extract_case_name_from_scholar_result(first_title, first_snippet)
                
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
            
            self.logger.info(f"No case name found in Google Scholar for: {citation}")
            return None
            
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Network error searching Google Scholar for '{citation}': {e}")
            # Cache negative result to avoid repeated attempts
            if self.cache_results and self.cache_manager:
                cache_data = {
                    'canonical_name': None,
                    'source': 'google_scholar_error',
                    'citation': citation,
                    'timestamp': time.time()
                }
                self.cache_manager.set_citation(cache_key, cache_data)
            return None
        except Exception as e:
            self.logger.warning(f"Error searching Google Scholar for '{citation}': {e}")
            # Cache negative result to avoid repeated attempts
            if self.cache_results and self.cache_manager:
                cache_data = {
                    'canonical_name': None,
                    'source': 'google_scholar_error',
                    'citation': citation,
                    'timestamp': time.time()
                }
                self.cache_manager.set_citation(cache_key, cache_data)
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