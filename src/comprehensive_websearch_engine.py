"""
Comprehensive Legal Web Search Engine
Combines the best features from enhanced_web_searcher.py and websearch_utils.py
"""

import re
import asyncio
import aiohttp
import logging
import time
import json
import random
from typing import Dict, List, Any, Optional, Tuple, Set
from urllib.parse import urlparse, quote_plus
from dataclasses import dataclass, asdict
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import os
from datetime import datetime, timedelta

# Import citation utilities from consolidated module
try:
    from src.citation_utils_consolidated import normalize_citation, generate_citation_variants
except ImportError:
    from citation_utils_consolidated import normalize_citation, generate_citation_variants

logger = logging.getLogger(__name__)

class EnhancedCitationNormalizer:
    """Advanced citation normalization with ML-enhanced variant generation."""
    
    def __init__(self):
        self.citation_patterns = {
            'washington': [
                r'(\d+)\s+Wn\.?\s*(\d+[a-z]?)\s+(\d+)',
                r'(\d+)\s+Wn\.?\s*App\.?\s*(\d+[a-z]?)\s+(\d+)',
                r'(\d+)\s+Wash\.?\s*(\d+[a-z]?)\s+(\d+)',
                r'(\d+)\s+Washington\s+(\d+[a-z]?)\s+(\d+)',
            ],
            'federal': [
                r'(\d+)\s+U\.?S\.?\s+(\d+)',
                r'(\d+)\s+F\.?\s*(\d+[a-z]?)\s+(\d+)',
                r'(\d+)\s+F\.?\s*Supp\.?\s*(\d+[a-z]?)\s+(\d+)',
                r'(\d+)\s+Fed\.?\s*(\d+[a-z]?)\s+(\d+)',
            ],
            'pacific': [
                r'(\d+)\s+P\.?\s*(\d+[a-z]?)\s+(\d+)',
                r'(\d+)\s+Pac\.?\s*(\d+[a-z]?)\s+(\d+)',
                r'(\d+)\s+Pacific\s+(\d+[a-z]?)\s+(\d+)',
            ]
        }
        
        # Common abbreviation mappings
        self.abbreviation_map = {
            'Wn.': ['Wash.', 'Washington'],
            'Wash.': ['Wn.', 'Washington'],
            'Washington': ['Wn.', 'Wash.'],
            'P.': ['Pac.', 'Pacific'],
            'Pac.': ['P.', 'Pacific'],
            'Pacific': ['P.', 'Pac.'],
            'F.': ['Fed.', 'Federal'],
            'Fed.': ['F.', 'Federal'],
            'U.S.': ['US', 'United States'],
            'App.': ['Ct. App.', 'Court of Appeals'],
        }
    
    def normalize_citation(self, citation: str) -> str:
        """Normalize a citation to standard format."""
        if not citation:
            return ""
        
        # Clean up whitespace
        citation = re.sub(r'\s+', ' ', citation.strip())
        
        # Standardize common patterns
        citation = re.sub(r'(\d+)\s*Wn\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wn. \2 \3', citation)
        citation = re.sub(r'(\d+)\s*P\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 P. \2 \3', citation)
        citation = re.sub(r'(\d+)\s*U\.?\s*S\.?\s+(\d+)', r'\1 U.S. \2', citation)
        citation = re.sub(r'(\d+)\s*F\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 F. \2 \3', citation)
        
        return citation.strip()
    
    def generate_variants(self, citation: str) -> List[str]:
        """Generate comprehensive citation variants using enhanced algorithms."""
        if not citation:
            return []
        
        variants = set([citation])
        normalized = self.normalize_citation(citation)
        if normalized != citation:
            variants.add(normalized)
        
        # Generate variants based on abbreviation mappings
        for abbrev, replacements in self.abbreviation_map.items():
            if abbrev in citation:
                for replacement in replacements:
                    variant = citation.replace(abbrev, replacement)
                    variants.add(variant)
                    # Also try with the normalized version
                    variant_norm = self.normalize_citation(variant)
                    variants.add(variant_norm)
        
        # Generate spacing variants
        for variant in list(variants):
            # Try with different spacing
            spaced = re.sub(r'(\d+)([A-Za-z])', r'\1 \2', variant)
            variants.add(spaced)
            
            # Try without spaces
            nospaces = re.sub(r'(\d+)\s+([A-Za-z])', r'\1\2', variant)
            variants.add(nospaces)
        
        # Generate ordinal variants (2d vs 2nd, 3d vs 3rd)
        for variant in list(variants):
            ordinal_variant = re.sub(r'(\d+)(d)\b', r'\1\2', variant)
            variants.add(ordinal_variant)
            
            full_ordinal = re.sub(r'(\d+)d\b', lambda m: f"{m.group(1)}{'nd' if m.group(1).endswith('2') else 'rd' if m.group(1).endswith('3') else 'th'}", variant)
            variants.add(full_ordinal)
        
        return list(variants)
    
    def extract_citation_components(self, citation: str) -> Dict[str, Any]:
        """Extract structured components from a citation."""
        components = {
            'volume': None,
            'reporter': None,
            'page': None,
            'year': None,
            'court': None,
            'series': None
        }
        
        # Try different patterns
        patterns = [
            r'(\d+)\s+([A-Za-z\.]+)\s*(\d+[a-z]?)\s+(\d+)\s*\(([^)]+)\s*(\d{4})\)',
            r'(\d+)\s+([A-Za-z\.]+)\s*(\d+[a-z]?)\s+(\d+)\s*\((\d{4})\)',
            r'(\d+)\s+([A-Za-z\.]+)\s*(\d+[a-z]?)\s+(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, citation)
            if match:
                components['volume'] = match.group(1)
                components['reporter'] = match.group(2)
                components['series'] = match.group(3) if len(match.groups()) >= 3 else None
                components['page'] = match.group(4) if len(match.groups()) >= 4 else match.group(3)
                
                if len(match.groups()) >= 6:
                    components['court'] = match.group(5)
                    components['year'] = match.group(6)
                elif len(match.groups()) >= 5:
                    components['year'] = match.group(5)
                
                break
        
        return components

class SearchEngineMetadata:
    """Container for search engine metadata when page content is unavailable."""
    
    def __init__(self, title: str = None, snippet: str = None, url: str = None, 
                 source: str = None, timestamp: str = None):
        self.title = title
        self.snippet = snippet
        self.url = url
        self.source = source
        self.timestamp = timestamp or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'snippet': self.snippet,
            'url': self.url,
            'source': self.source,
            'timestamp': self.timestamp,
            'type': 'search_engine_metadata'
        }
    
    def extract_case_info(self) -> Dict[str, Any]:
        """Extract case information from search engine metadata."""
        result = {
            'case_name': None,
            'date': None,
            'court': None,
            'confidence': 0.0,
            'extraction_method': 'search_engine_metadata'
        }
        
        # Combine title and snippet for analysis
        text = f"{self.title or ''} {self.snippet or ''}"
        
        # Extract case name from title/snippet
        case_name = self._extract_case_name_from_text(text)
        if case_name:
            result['case_name'] = case_name
            result['confidence'] += 0.3
        
        # Extract date from text
        date = self._extract_date_from_text(text)
        if date:
            result['date'] = date
            result['confidence'] += 0.2
        
        # Extract court from text
        court = self._extract_court_from_text(text)
        if court:
            result['court'] = court
            result['confidence'] += 0.1
        
        return result
    
    def _extract_case_name_from_text(self, text: str) -> Optional[str]:
        """Extract case name from search engine text."""
        # Common case name patterns
        patterns = [
            r'([A-Z][A-Za-z\s,&\.]+v\.?\s+[A-Z][A-Za-z\s,&\.]+)',
            r'(State\s+v\.?\s+[A-Z][A-Za-z\s,&\.]+)',
            r'(United\s+States\s+v\.?\s+[A-Z][A-Za-z\s,&\.]+)',
            r'(In\s+re\s+[A-Z][A-Za-z\s,&\.]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                case_name = match.group(1).strip()
                if len(case_name) > 10:  # Filter out very short matches
                    return case_name
        return None
    
    def _extract_date_from_text(self, text: str) -> Optional[str]:
        """Extract date from search engine text."""
        # Look for years
        year_match = re.search(r'\b(19|20)\d{2}\b', text)
        if year_match:
            return year_match.group(0)
        return None
    
    def _extract_court_from_text(self, text: str) -> Optional[str]:
        """Extract court information from search engine text."""
        court_patterns = [
            r'(Supreme\s+Court)',
            r'(Court\s+of\s+Appeals)',
            r'(District\s+Court)',
            r'(Circuit\s+Court)',
        ]
        
        for pattern in court_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

class ComprehensiveWebExtractor:
    """
    Advanced web extraction using multiple techniques for canonical information.
    Incorporates specialized extraction methods from legal_database_scraper.py
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Enhanced case name patterns with more precision
        self.case_name_patterns = [
            # Department cases with apostrophe (most specific first)
            r"(Dep't\s+of\s+[A-Za-z\s,&\.]+\s+v\.?\s+[A-Za-z\s,&\.]+)",
            # Department spelled out
            r"(Department\s+of\s+[A-Za-z\s,&\.]+\s+v\.?\s+[A-Za-z\s,&\.]+)",
            # Government cases
            r"(United\s+States\s+v\.?\s+[A-Za-z\s,&\.]+)",
            r"(State\s+(?:of\s+)?[A-Za-z\s,&\.]*\s+v\.?\s+[A-Za-z\s,&\.]+)",
            r"(People\s+(?:of\s+)?[A-Za-z\s,&\.]*\s+v\.?\s+[A-Za-z\s,&\.]+)",
            r"(Commonwealth\s+(?:of\s+)?[A-Za-z\s,&\.]*\s+v\.?\s+[A-Za-z\s,&\.]+)",
            # In re and Ex parte cases
            r"(In\s+re\s+[A-Za-z\s,&\.]+)",
            r"(Ex\s+parte\s+[A-Za-z\s,&\.]+)",
            r"(Matter\s+of\s+[A-Za-z\s,&\.]+)",
            # Estate and guardianship
            r"(Estate\s+of\s+[A-Za-z\s,&\.]+)",
            r"(Guardianship\s+of\s+[A-Za-z\s,&\.]+)",
            # Standard case format with enhanced matching
            r"([A-Z][A-Za-z'\.\s,&-]+\s+v\.?\s+[A-Z][A-Za-z'\.\s,&-]+)",
            # Corporate cases with Inc., LLC, Corp., etc.
            r"([A-Z][A-Za-z\s,&\.]*(?:Inc\.|LLC|Corp\.|Co\.|Ltd\.)\s+v\.?\s+[A-Za-z\s,&\.]+)",
            r"([A-Za-z\s,&\.]+\s+v\.?\s+[A-Z][A-Za-z\s,&\.]*(?:Inc\.|LLC|Corp\.|Co\.|Ltd\.))",
        ]
        
        # Citation patterns for different legal databases
        self.citation_patterns = [
            r'(\d+\s+Wn\.3d\s+\d+\s*\([^)]+\))',  # e.g., "3 Wn.3d 80 (Wash. 2024)"
            r'(\d+\s+[A-Z][a-z]+\.\d+\s+\d+\s*\([A-Za-z]+\.\s*\d{4}\))',  # e.g., "3 Wn.3d 80 (Wash. 2024)"
            r'(\d+\s+[A-Z][a-z]+\.\d+\s+\d+\s*\([A-Za-z]+\s+\d{4}\))',  # e.g., "3 Wn.3d 80 (Wash 2024)"
            r'(\d+\s+[A-Z]\.\d+\s+\d+\s*\(\d{4}\))',  # e.g., "546 P.3d 385 (2024)"
            r'(\d+\s+[A-Z]\.\s*\d+\s*[a-z]+\s+\d+\s*\(\d{4}\))',  # e.g., "546 P. 3d 385 (2024)"
            r'(\d+\s+[A-Z][A-Za-z]+\s+\d+\s*\(\d{4}\))',  # e.g., "546 Pacific 3d 385 (2024)"
        ]
        
        # Court patterns
        self.court_patterns = [
            r'Supreme Court of the State of Washington',
            r'Supreme Court of Washington',
            r'Washington Supreme Court',
            r'Court of Appeals',
            r'District Court',
            r'Circuit Court'
        ]
        
        # Docket patterns
        self.docket_patterns = [
            r'Docket:\s*([^\n;]+)',
            r'Docket No\.:\s*([^\n;]+)',
            r'No\.\s*([0-9-]+)'
        ]
        
        # Enhanced citation patterns for better extraction
        self.enhanced_citation_patterns = [
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

    def generate_washington_variants(self, citation: str) -> List[str]:
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

    def extract_case_name_from_context(self, text: str, citation: str, context_window: int = 500) -> Optional[str]:
        """
        Extract case name from text context around a citation.
        """
        try:
            # Find the citation in the text
            citation_pos = text.find(citation)
            if citation_pos == -1:
                return None
            
            # Extract context around the citation
            start = max(0, citation_pos - context_window)
            end = min(len(text), citation_pos + len(citation) + context_window)
            context = text[start:end]
            
            # Look for case name patterns in the context
            for pattern in self.case_name_patterns:
                matches = re.finditer(pattern, context, re.IGNORECASE)
                for match in matches:
                    case_name = match.group(1).strip()
                    if len(case_name) > 10 and self._is_valid_case_name(case_name):
                        return case_name
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting case name from context: {e}")
            return None

    def _is_valid_case_name(self, case_name: str) -> bool:
        """
        Check if a potential case name is valid.
        
        Args:
            case_name: The potential case name
            
        Returns:
            True if valid, False otherwise
        """
        if not case_name or len(case_name) < 5:
            return False
        
        # Must contain 'v.' or 'v ' for adversarial cases
        if 'v.' in case_name.lower() or 'v ' in case_name.lower():
            return True
        
        # Or must be a special case type
        special_patterns = [
            r'^In\s+re\s+',
            r'^Ex\s+parte\s+',
            r'^Matter\s+of\s+',
            r'^Estate\s+of\s+',
            r'^Guardianship\s+of\s+',
            r'^State\s+v\.?\s+',
            r'^United\s+States\s+v\.?\s+',
            r'^People\s+v\.?\s+',
            r'^Commonwealth\s+v\.?\s+',
        ]
        
        for pattern in special_patterns:
            if re.search(pattern, case_name, re.IGNORECASE):
                return True
        
        return False

    def _clean_case_name(self, case_name: str) -> str:
        """
        Clean up a case name.
        
        Args:
            case_name: The case name to clean
            
        Returns:
            Cleaned case name
        """
        if not case_name:
            return ""
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', case_name.strip())
        
        # Remove common suffixes
        cleaned = re.sub(r'\s*\(Majority\)\s*$', '', cleaned)
        cleaned = re.sub(r'\s*\(Dissenting\)\s*$', '', cleaned)
        cleaned = re.sub(r'\s*\(Concurring\)\s*$', '', cleaned)
        
        return cleaned

    def extract_enhanced_case_names(self, text: str) -> List[Dict]:
        """
        Extract case names from text using enhanced method.
        
        Args:
            text: The text to extract from
            
        Returns:
            List of dictionaries with citation and case name information
        """
        results = []
        
        # Extract all citations
        all_citations = []
        for pattern in self.enhanced_citation_patterns:
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
            
            # Extract case name from context
            extracted_name = self.extract_case_name_from_context(text, citation)
            
            # Clean the extracted name
            if extracted_name:
                extracted_name = self._clean_case_name(extracted_name)
            
            # Generate citation variants for better search
            citation_variants = []
            if 'Wn.' in citation or 'Wn ' in citation:
                citation_variants = self.generate_washington_variants(citation)
            else:
                citation_variants = generate_citation_variants(citation)
            
            # Add to results
            result = {
                'citation': citation,
                'case_name': extracted_name,
                'citation_variants': citation_variants,
                'position': citation_info['start'],
                'confidence': 0.7 if extracted_name else 0.0,
                'method': 'enhanced_extraction'
            }
            
            results.append(result)
        
        return results

    def extract_from_page_content(self, html_content: str, url: str, citation: str) -> Dict[str, Any]:
        """
        Advanced extraction from full page content using multiple techniques.
        """
        result = {
            'case_name': None,
            'date': None,
            'court': None,
            'docket_number': None,
            'canonical_url': url,
            'confidence': 0.0,
            'extraction_methods': [],
            'error': None
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Method 1: Specialized legal database extraction (highest priority)
            legal_db_result = self.extract_from_legal_database(url, html_content)
            if legal_db_result and legal_db_result.get('case_name'):
                result.update(legal_db_result)
                result['extraction_methods'].extend(legal_db_result.get('extraction_methods', []))
                result['confidence'] = max(result['confidence'], legal_db_result.get('confidence', 0))
                # If we got good results from specialized extraction, return early
                if result['confidence'] > 0.5:
                    return result
            
            # Method 2: Structured data extraction (JSON-LD, microdata)
            structured_data = self._extract_structured_data(soup)
            if structured_data:
                for key, value in structured_data.items():
                    if not result.get(key) and value:
                        result[key] = value
                        result['extraction_methods'].append('structured_data')
                        result['confidence'] += 0.4
            
            # Method 3: HTML metadata extraction
            metadata = self._extract_html_metadata(soup)
            if metadata:
                for key, value in metadata.items():
                    if not result.get(key) and value:
                        result[key] = value
                        result['extraction_methods'].append(f'metadata_{key}')
                        result['confidence'] += 0.2
            
            # Method 4: Semantic HTML extraction
            semantic_data = self._extract_semantic_html(soup, citation)
            if semantic_data:
                for key, value in semantic_data.items():
                    if not result.get(key) and value:
                        result[key] = value
                        result['extraction_methods'].append(f'semantic_{key}')
                        result['confidence'] += 0.3
            
            # Method 5: Pattern-based extraction from cleaned text
            text_data = self._extract_from_text_patterns(soup.get_text(), citation)
            if text_data:
                for key, value in text_data.items():
                    if not result.get(key) and value:
                        result[key] = value
                        result['extraction_methods'].append(f'text_pattern_{key}')
                        result['confidence'] += 0.2
            
            # Method 6: URL-based extraction
            url_data = self._extract_from_url(url, citation)
            if url_data:
                for key, value in url_data.items():
                    if not result.get(key) and value:
                        result[key] = value
                        result['extraction_methods'].append(f'url_{key}')
                        result['confidence'] += 0.1
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Error extracting from page content: {e}")
        
        return result

    def extract_from_legal_database(self, url: str, html_content: str) -> Dict[str, Any]:
        """
        Extract case information using specialized methods for legal databases.
        Based on legal_database_scraper.py techniques.
        """
        try:
            domain = urlparse(url).netloc.lower()
            
            if 'casemine.com' in domain:
                return self._extract_casemine_info(html_content, url)
            elif 'vlex.com' in domain:
                return self._extract_vlex_info(html_content, url)
            elif 'casetext.com' in domain or 'cetient.com' in domain:
                return self._extract_casetext_info(html_content, url)
            elif 'leagle.com' in domain:
                return self._extract_leagle_info(html_content, url)
            elif 'justia.com' in domain:
                return self._extract_justia_info(html_content, url)
            elif 'findlaw.com' in domain or 'caselaw.findlaw.com' in domain:
                return self._extract_findlaw_info(html_content, url)
            else:
                return self._extract_generic_legal_info(html_content, url)
                
        except Exception as e:
            self.logger.error(f"Error extracting from legal database {url}: {e}")
            return {}

    def _extract_casemine_info(self, html_content: str, url: str) -> Dict[str, Any]:
        """Extract case information from CaseMine."""
        result = {
            'case_name': None,
            'date': None,
            'court': None,
            'docket_number': None,
            'parallel_citations': [],
            'confidence': 0.0,
            'extraction_methods': ['casemine_specialized'],
            'source': 'casemine'
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            page_text = soup.get_text(separator='\n')
            
            # Extract canonical name
            h1 = soup.find('h1')
            if h1:
                result['case_name'] = h1.get_text(strip=True)
                result['confidence'] += 0.4
            else:
                # Fallback: first line with 'v.'
                for line in page_text.split('\n'):
                    if 'v.' in line:
                        result['case_name'] = line.strip()
                        result['confidence'] += 0.3
                        break
            
            # Extract citations
            for pattern in self.citation_patterns:
                citation_match = re.search(pattern, page_text)
                if citation_match:
                    result['parallel_citations'].append(citation_match.group(1))
                    result['confidence'] += 0.2
                    break
            
            # Extract year
            year_pattern = r'Filed\s+(\w+\s+\d{1,2},\s+(19|20)\d{2})'
            year_match = re.search(year_pattern, page_text)
            if year_match:
                result['date'] = re.search(r'(19|20)\d{2}', year_match.group(1)).group()
                result['confidence'] += 0.2
            elif result['parallel_citations']:
                year_match = re.search(r'(19|20)\d{2}', result['parallel_citations'][0])
                if year_match:
                    result['date'] = year_match.group()
                    result['confidence'] += 0.1
            
            # Extract court
            for pattern in self.court_patterns:
                court_match = re.search(pattern, page_text)
                if court_match:
                    result['court'] = court_match.group(0).strip()
                    result['confidence'] += 0.1
                    break
            
            # Extract docket
            for pattern in self.docket_patterns:
                docket_match = re.search(pattern, page_text)
                if docket_match:
                    result['docket_number'] = docket_match.group(0)
                    result['confidence'] += 0.1
                    break
            
        except Exception as e:
            self.logger.error(f"Error extracting CaseMine info: {e}")
        
        return result

    def _extract_vlex_info(self, html_content: str, url: str) -> Dict[str, Any]:
        """Extract case information from vLex."""
        result = {
            'case_name': None,
            'date': None,
            'court': None,
            'docket_number': None,
            'parallel_citations': [],
            'confidence': 0.0,
            'extraction_methods': ['vlex_specialized'],
            'source': 'vlex'
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            page_text = soup.get_text(separator='\n')
            
            # Enhanced vLex case name extraction patterns
            vlex_patterns = [
                # vLex specific patterns from extract_case_name.py
                r'<h1[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]+)</h1>',
                r'<h1[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</h1>',
                r'<h2[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]+)</h2>',
                r'<h1[^>]*>([^<]*' + re.escape(result.get('citation', '')) + r'[^<]*)</h1>',
                r'<title[^>]*>([^<]*' + re.escape(result.get('citation', '')) + r'[^<]*)</title>',
                r'class="case-title"[^>]*>([^<]*)</',
                r'<span[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]*)</span>',
                r'<div[^>]*class="[^"]*case-title[^"]*"[^>]*>([^<]*)</div>',
                # Additional vLex patterns
                r'<h1[^>]*>([^<]+)</h1>',
                r'<h2[^>]*>([^<]+)</h2>',
                r'<title[^>]*>([^<]+)</title>'
            ]
            
            # Extract case name from <h1> or main heading
            for pattern in vlex_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
                if match:
                    case_name = match.group(1).strip()
                    if self._is_valid_case_name(case_name):
                        result['case_name'] = self._clean_case_name(case_name)
                        result['confidence'] += 0.4
                        break
            
            # Fallback: first line with 'v.' if no case name found
            if not result['case_name']:
                for line in page_text.split('\n'):
                    if 'v.' in line:
                        case_name = line.strip()
                        if self._is_valid_case_name(case_name):
                            result['case_name'] = self._clean_case_name(case_name)
                            result['confidence'] += 0.3
                            break
            
            # Extract citations with enhanced patterns
            for pattern in self.citation_patterns:
                citation_match = re.search(pattern, page_text)
                if citation_match:
                    result['parallel_citations'].append(citation_match.group(1))
                    result['confidence'] += 0.2
                    break
            
            # Extract year
            year_pattern = r'Filed\s+(\w+\s+\d{1,2},\s+(19|20)\d{2})'
            year_match = re.search(year_pattern, page_text)
            if year_match:
                result['date'] = re.search(r'(19|20)\d{2}', year_match.group(1)).group()
                result['confidence'] += 0.2
            elif result['parallel_citations']:
                year_match = re.search(r'(19|20)\d{2}', result['parallel_citations'][0])
                if year_match:
                    result['date'] = year_match.group()
                    result['confidence'] += 0.1
            
            # Extract court
            for pattern in self.court_patterns:
                court_match = re.search(pattern, page_text)
                if court_match:
                    result['court'] = court_match.group(0).strip()
                    result['confidence'] += 0.1
                    break
            
            # Extract docket
            for pattern in self.docket_patterns:
                docket_match = re.search(pattern, page_text)
                if docket_match:
                    result['docket_number'] = docket_match.group(0)
                    result['confidence'] += 0.1
                    break
            
        except Exception as e:
            self.logger.error(f"Error extracting vLex info: {e}")
        
        return result

    def _extract_casetext_info(self, html_content: str, url: str) -> Dict[str, Any]:
        """Extract case information from Casetext."""
        result = {
            'case_name': None,
            'date': None,
            'court': None,
            'docket_number': None,
            'parallel_citations': [],
            'confidence': 0.0,
            'extraction_methods': ['casetext_specialized'],
            'source': 'casetext'
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract canonical name from search results or main page
            search_results = soup.find_all(['div', 'article'], class_=re.compile(r'result|case|item'))
            for result_item in search_results:
                name_elements = result_item.find_all(['h1', 'h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|name|heading'))
                for element in name_elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 10 and 'v.' in text:
                        result['case_name'] = text
                        result['confidence'] += 0.4
                        break
                if result['case_name']:
                    break
            
            # If no canonical name found in search results, try main page
            if not result['case_name']:
                name_elements = soup.find_all(['h1', 'h2'], class_=re.compile(r'title|name|heading'))
                if not name_elements:
                    name_elements = soup.find_all(['h1', 'h2'])
                
                for element in name_elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 10 and 'v.' in text:
                        result['case_name'] = text
                        result['confidence'] += 0.3
                        break
            
            # Extract parallel citations
            for result_item in search_results:
                citation_elements = result_item.find_all(['div', 'span'], class_=re.compile(r'citation|cite'))
                for element in citation_elements:
                    text = element.get_text(strip=True)
                    if re.match(r'\d+\s+[A-Z]\.\d+', text):
                        result['parallel_citations'].append(text)
                        result['confidence'] += 0.2
                        break
            
            # If no citations found in search results, try main page
            if not result['parallel_citations']:
                citation_elements = soup.find_all(['div', 'span'], class_=re.compile(r'citation'))
                for element in citation_elements:
                    text = element.get_text(strip=True)
                    if re.match(r'\d+\s+[A-Z]\.\d+', text):
                        result['parallel_citations'].append(text)
                        result['confidence'] += 0.2
                        break
            
            # Extract year
            page_text = soup.get_text()
            year_match = re.search(r'\b(19|20)\d{2}\b', page_text)
            if year_match:
                result['date'] = year_match.group()
                result['confidence'] += 0.1
            
            # Extract court information
            for pattern in self.court_patterns:
                court_match = re.search(pattern, page_text, re.I)
                if court_match:
                    result['court'] = court_match.group(0).strip()
                    result['confidence'] += 0.1
                    break
            
            # Extract docket number
            for pattern in self.docket_patterns:
                docket_match = re.search(pattern, page_text, re.I)
                if docket_match:
                    result['docket_number'] = docket_match.group(1).strip()
                    result['confidence'] += 0.1
                    break
            
        except Exception as e:
            self.logger.error(f"Error extracting Casetext info: {e}")
        
        return result

    def _extract_leagle_info(self, html_content: str, url: str) -> Dict[str, Any]:
        """Extract case information from Leagle."""
        result = {
            'case_name': None,
            'date': None,
            'court': None,
            'docket_number': None,
            'parallel_citations': [],
            'confidence': 0.0,
            'extraction_methods': ['leagle_specialized'],
            'source': 'leagle'
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            page_text = soup.get_text(separator='\n')
            
            # Extract case name from <h1> or main heading
            h1 = soup.find('h1')
            if h1:
                result['case_name'] = h1.get_text(strip=True)
                result['confidence'] += 0.4
            else:
                # Fallback: first line with 'v.'
                for line in page_text.split('\n'):
                    if 'v.' in line:
                        result['case_name'] = line.strip()
                        result['confidence'] += 0.3
                        break
            
            # Extract citations
            for pattern in self.citation_patterns:
                citation_match = re.search(pattern, page_text)
                if citation_match:
                    result['parallel_citations'].append(citation_match.group(1))
                    result['confidence'] += 0.2
                    break
            
            # Extract year
            year_pattern = r'Filed\s+(\w+\s+\d{1,2},\s+(19|20)\d{2})'
            year_match = re.search(year_pattern, page_text)
            if year_match:
                result['date'] = re.search(r'(19|20)\d{2}', year_match.group(1)).group()
                result['confidence'] += 0.2
            elif result['parallel_citations']:
                year_match = re.search(r'(19|20)\d{2}', result['parallel_citations'][0])
                if year_match:
                    result['date'] = year_match.group()
                    result['confidence'] += 0.1
            
            # Extract court
            for pattern in self.court_patterns:
                court_match = re.search(pattern, page_text)
                if court_match:
                    result['court'] = court_match.group(0).strip()
                    result['confidence'] += 0.1
                    break
            
            # Extract docket
            for pattern in self.docket_patterns:
                docket_match = re.search(pattern, page_text)
                if docket_match:
                    result['docket_number'] = docket_match.group(0)
                    result['confidence'] += 0.1
                    break
            
        except Exception as e:
            self.logger.error(f"Error extracting Leagle info: {e}")
        
        return result

    def _extract_justia_info(self, html_content: str, url: str) -> Dict[str, Any]:
        """Extract case information from Justia."""
        result = {
            'case_name': None,
            'date': None,
            'court': None,
            'docket_number': None,
            'parallel_citations': [],
            'confidence': 0.0,
            'extraction_methods': ['justia_specialized'],
            'source': 'justia'
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            page_text = soup.get_text(separator='\n')
            
            # Extract canonical name
            h1 = soup.find('h1')
            if h1:
                result['case_name'] = h1.get_text(strip=True)
                # Clean up the case name (remove "(Majority)" suffix)
                result['case_name'] = re.sub(r'\s*\(Majority\)\s*$', '', result['case_name'])
                result['confidence'] += 0.4
            else:
                for line in page_text.split('\n'):
                    if 'v.' in line:
                        result['case_name'] = line.strip()
                        result['confidence'] += 0.3
                        break
            
            # Extract citations
            for pattern in self.citation_patterns:
                citation_match = re.search(pattern, page_text)
                if citation_match:
                    result['parallel_citations'].append(citation_match.group(1))
                    result['confidence'] += 0.2
                    break
            
            # Extract year
            if result['parallel_citations']:
                year_match = re.search(r'(19|20)\d{2}', result['parallel_citations'][0])
                if year_match:
                    result['date'] = year_match.group()
                    result['confidence'] += 0.1
            else:
                # Look for filed date
                year_pattern = r'Filed:\s*(\w+\s+\d{1,2},\s+(19|20)\d{2})'
                year_match = re.search(year_pattern, page_text)
                if year_match:
                    result['date'] = re.search(r'(19|20)\d{2}', year_match.group(1)).group()
                    result['confidence'] += 0.2
            
            # Extract court
            for pattern in self.court_patterns:
                court_match = re.search(pattern, page_text)
                if court_match:
                    result['court'] = court_match.group(0).strip()
                    result['confidence'] += 0.1
                    break
            
            # Extract docket number
            for pattern in self.docket_patterns:
                docket_match = re.search(pattern, page_text)
                if docket_match:
                    result['docket_number'] = docket_match.group(0)
                    result['confidence'] += 0.1
                    break
            
        except Exception as e:
            self.logger.error(f"Error extracting Justia info: {e}")
        
        return result

    def _extract_findlaw_info(self, html_content: str, url: str) -> Dict[str, Any]:
        """Extract case information from FindLaw."""
        result = {
            'case_name': None,
            'date': None,
            'court': None,
            'docket_number': None,
            'parallel_citations': [],
            'confidence': 0.0,
            'extraction_methods': ['findlaw_specialized'],
            'source': 'findlaw'
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            page_text = soup.get_text(separator='\n')
            
            # Extract case name
            h1 = soup.find('h1')
            if h1:
                result['case_name'] = h1.get_text(strip=True)
                result['confidence'] += 0.4
            else:
                for line in page_text.split('\n'):
                    if 'v.' in line:
                        result['case_name'] = line.strip()
                        result['confidence'] += 0.3
                        break
            
            # Extract citations
            for pattern in self.citation_patterns:
                citation_match = re.search(pattern, page_text)
                if citation_match:
                    result['parallel_citations'].append(citation_match.group(1))
                    result['confidence'] += 0.2
                    break
            
            # Extract year
            if result['parallel_citations']:
                year_match = re.search(r'(19|20)\d{2}', result['parallel_citations'][0])
                if year_match:
                    result['date'] = year_match.group()
                    result['confidence'] += 0.1
            
            # Extract court
            for pattern in self.court_patterns:
                court_match = re.search(pattern, page_text)
                if court_match:
                    result['court'] = court_match.group(0).strip()
                    result['confidence'] += 0.1
                    break
            
            # Extract docket
            for pattern in self.docket_patterns:
                docket_match = re.search(pattern, page_text)
                if docket_match:
                    result['docket_number'] = docket_match.group(0)
                    result['confidence'] += 0.1
                    break
            
        except Exception as e:
            self.logger.error(f"Error extracting FindLaw info: {e}")
        
        return result

    def _extract_generic_legal_info(self, html_content: str, url: str) -> Dict[str, Any]:
        """Extract case information using generic methods."""
        result = {
            'case_name': None,
            'date': None,
            'court': None,
            'docket_number': None,
            'parallel_citations': [],
            'confidence': 0.0,
            'extraction_methods': ['generic_legal'],
            'source': 'generic'
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract canonical name from search results or main page
            search_results = soup.find_all(['div', 'article'], class_=re.compile(r'result|case|item'))
            for result_item in search_results:
                name_elements = result_item.find_all(['h1', 'h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|name|heading'))
                for element in name_elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 10 and 'v.' in text:
                        result['case_name'] = text
                        result['confidence'] += 0.3
                        break
                if result['case_name']:
                    break
            
            # If no canonical name found in search results, try main page
            if not result['case_name']:
                name_elements = soup.find_all(['h1', 'h2', 'h3'])
                for element in name_elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 10 and 'v.' in text:
                        result['case_name'] = text
                        result['confidence'] += 0.2
                        break
            
            # Extract parallel citations
            for result_item in search_results:
                citation_elements = result_item.find_all(['div', 'span', 'p'], class_=re.compile(r'citation|cite'))
                for element in citation_elements:
                    text = element.get_text(strip=True)
                    if re.match(r'\d+\s+[A-Z]\.\d+', text):
                        result['parallel_citations'].append(text)
                        result['confidence'] += 0.2
                        break
            
            # Extract year
            page_text = soup.get_text()
            year_match = re.search(r'\b(19|20)\d{2}\b', page_text)
            if year_match:
                result['date'] = year_match.group()
                result['confidence'] += 0.1
            
            # Extract court
            for pattern in self.court_patterns:
                court_match = re.search(pattern, page_text, re.I)
                if court_match:
                    result['court'] = court_match.group(0).strip()
                    result['confidence'] += 0.1
                    break
            
            # Extract docket
            for pattern in self.docket_patterns:
                docket_match = re.search(pattern, page_text, re.I)
                if docket_match:
                    result['docket_number'] = docket_match.group(1).strip()
                    result['confidence'] += 0.1
                    break
            
        except Exception as e:
            self.logger.error(f"Error extracting generic legal info: {e}")
        
        return result

    def _extract_structured_data(self, soup) -> Dict[str, Any]:
        """Extract structured data from JSON-LD and microdata."""
        result = {}
        
        # JSON-LD extraction
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    # Look for case information in structured data
                    if data.get('@type') in ['LegalCase', 'Article', 'WebPage']:
                        if data.get('name'):
                            result['case_name'] = data['name']
                        if data.get('datePublished'):
                            result['date'] = data['datePublished']
                        if data.get('author', {}).get('name'):
                            result['court'] = data['author']['name']
            except (json.JSONDecodeError, AttributeError):
                continue
        
        return result

    def _extract_html_metadata(self, soup) -> Dict[str, Any]:
        """Extract metadata from HTML meta tags."""
        result = {}
        
        # Meta tags
        meta_mappings = {
            'og:title': 'case_name',
            'twitter:title': 'case_name',
            'title': 'case_name',
            'og:description': 'description',
            'description': 'description',
            'date': 'date',
            'pubdate': 'date',
            'article:published_time': 'date',
        }
        
        for meta_name, result_key in meta_mappings.items():
            meta_tag = soup.find('meta', attrs={'name': meta_name}) or soup.find('meta', attrs={'property': meta_name})
            if meta_tag and meta_tag.get('content'):
                result[result_key] = meta_tag['content']
        
        # Title tag
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            result['case_name'] = result.get('case_name') or title_tag.string.strip()
        
        return result

    def _extract_semantic_html(self, soup, citation: str) -> Dict[str, Any]:
        """Extract information from semantic HTML elements."""
        result = {}
        
        # Look for case name in headings
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4']):
            if heading.string:
                text = heading.string.strip()
                # Check if this looks like a case name
                for pattern in self.case_name_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        result['case_name'] = match.group(1).strip()
                        break
                if result.get('case_name'):
                    break
        
        # Look for dates in semantic elements
        date_patterns = [
            r'\b(19|20)\d{2}\b',
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+(?:19|20)\d{2}\b',
        ]
        
        for element in soup.find_all(['time', 'span', 'div'], class_=re.compile(r'date|published|time')):
            if element.string:
                for pattern in date_patterns:
                    match = re.search(pattern, element.string, re.IGNORECASE)
                    if match:
                        result['date'] = match.group(0)
                        break
                if result.get('date'):
                    break
        
        return result

    def _extract_from_text_patterns(self, text: str, citation: str) -> Dict[str, Any]:
        """Extract information using pattern matching on text."""
        result = {}
        
        # Extract case name using patterns
        for pattern in self.case_name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['case_name'] = match.group(1).strip()
                break
        
        # Extract date
        date_match = re.search(r'\b(19|20)\d{2}\b', text)
        if date_match:
            result['date'] = date_match.group(0)
        
        return result

    def _extract_from_url(self, url: str, citation: str) -> Dict[str, Any]:
        """Extract information from URL patterns."""
        result = {}
        
        # Extract case name from URL if it contains case-like patterns
        url_lower = url.lower()
        if 'case' in url_lower or 'opinion' in url_lower:
            # Try to extract case name from URL path
            path = urlparse(url).path
            path_parts = [p for p in path.split('/') if p and len(p) > 3]
            
            for part in path_parts:
                # Check if this part looks like a case name
                for pattern in self.case_name_patterns:
                    match = re.search(pattern, part, re.IGNORECASE)
                    if match:
                        result['case_name'] = match.group(1).strip()
                        break
                if result.get('case_name'):
                    break
        
        return result

    def extract_from_search_results(self, html_content: str, search_engine: str) -> List[SearchEngineMetadata]:
        """
        Extract search results metadata from search engine pages.
        This is useful when the actual pages are unavailable (linkrot).
        """
        results = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            if search_engine == 'bing':
                results = self._extract_bing_results(soup)
            elif search_engine == 'google':
                results = self._extract_google_results(soup)
            elif search_engine == 'duckduckgo':
                results = self._extract_duckduckgo_results(soup)
            else:
                # Generic extraction
                results = self._extract_generic_search_results(soup, search_engine)
                
        except Exception as e:
            self.logger.error(f"Error extracting search results from {search_engine}: {e}")
        
        return results

    def _extract_bing_results(self, soup) -> List[SearchEngineMetadata]:
        """Extract search results from Bing."""
        results = []
        
        try:
            # Bing search result selectors
            result_elements = soup.find_all('li', class_='b_algo') or soup.find_all('div', class_='b_algo')
            
            for element in result_elements[:5]:  # Limit to top 5 results
                try:
                    # Extract title
                    title_elem = element.find('h2') or element.find('a')
                    title = title_elem.get_text(strip=True) if title_elem else None
                    
                    # Extract URL
                    link_elem = element.find('a')
                    url = link_elem.get('href') if link_elem else None
                    
                    # Extract snippet
                    snippet_elem = element.find('p') or element.find('div', class_='b_caption')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else None
                    
                    if title and url:
                        metadata = SearchEngineMetadata(
                            title=title,
                            snippet=snippet,
                            url=url,
                            source='Bing'
                        )
                        results.append(metadata)
                        
                except Exception as e:
                    self.logger.debug(f"Error extracting Bing result: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error parsing Bing results: {e}")
        
        return results

    def _extract_google_results(self, soup) -> List[SearchEngineMetadata]:
        """Extract search results from Google."""
        results = []
        
        try:
            # Google search result selectors
            result_elements = soup.find_all('div', class_='g') or soup.find_all('div', {'data-sokoban-container': True})
            
            for element in result_elements[:5]:  # Limit to top 5 results
                try:
                    # Extract title
                    title_elem = element.find('h3') or element.find('a')
                    title = title_elem.get_text(strip=True) if title_elem else None
                    
                    # Extract URL
                    link_elem = element.find('a')
                    url = link_elem.get('href') if link_elem else None
                    
                    # Extract snippet
                    snippet_elem = element.find('div', class_='VwiC3b') or element.find('span', class_='aCOpRe')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else None
                    
                    if title and url:
                        metadata = SearchEngineMetadata(
                            title=title,
                            snippet=snippet,
                            url=url,
                            source='Google'
                        )
                        results.append(metadata)
                        
                except Exception as e:
                    self.logger.debug(f"Error extracting Google result: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error parsing Google results: {e}")
        
        return results

    def _extract_duckduckgo_results(self, soup) -> List[SearchEngineMetadata]:
        """Extract search results from DuckDuckGo."""
        results = []
        
        try:
            # DuckDuckGo search result selectors
            result_elements = soup.find_all('div', class_='result') or soup.find_all('article')
            
            for element in result_elements[:5]:  # Limit to top 5 results
                try:
                    # Extract title
                    title_elem = element.find('h2') or element.find('a')
                    title = title_elem.get_text(strip=True) if title_elem else None
                    
                    # Extract URL
                    link_elem = element.find('a')
                    url = link_elem.get('href') if link_elem else None
                    
                    # Extract snippet
                    snippet_elem = element.find('div', class_='snippet') or element.find('p')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else None
                    
                    if title and url:
                        metadata = SearchEngineMetadata(
                            title=title,
                            snippet=snippet,
                            url=url,
                            source='DuckDuckGo'
                        )
                        results.append(metadata)
                        
                except Exception as e:
                    self.logger.debug(f"Error extracting DuckDuckGo result: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error parsing DuckDuckGo results: {e}")
        
        return results

    def _extract_generic_search_results(self, soup, search_engine: str) -> List[SearchEngineMetadata]:
        """Generic extraction for unknown search engines."""
        results = []
        
        try:
            # Look for common patterns
            links = soup.find_all('a', href=True)
            
            for link in links[:10]:  # Limit to top 10 links
                try:
                    title = link.get_text(strip=True)
                    url = link.get('href')
                    
                    if title and url and len(title) > 10:
                        # Try to find nearby snippet
                        snippet = None
                        parent = link.parent
                        if parent:
                            text_elements = parent.find_all(['p', 'div', 'span'])
                            for elem in text_elements:
                                if elem != link and elem.get_text(strip=True):
                                    snippet = elem.get_text(strip=True)[:200]  # Limit length
                                    break
                        
                        metadata = SearchEngineMetadata(
                            title=title,
                            snippet=snippet,
                            url=url,
                            source=search_engine
                        )
                        results.append(metadata)
                        
                except Exception as e:
                    self.logger.debug(f"Error extracting generic result: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error parsing generic search results: {e}")
        
        return results

    def _find_best_search_result(self, search_results: List[SearchEngineMetadata], 
                                citation: str, case_name: str = None) -> Optional[SearchEngineMetadata]:
        """Find the best search result based on relevance to citation and case name."""
        if not search_results:
            return None
        
        best_result = None
        best_score = 0
        
        for result in search_results:
            score = 0
            
            # Score based on citation presence in title/snippet
            combined_text = f"{result.title or ''} {result.snippet or ''}"
            if citation.lower() in combined_text.lower():
                score += 3
            
            # Score based on case name presence
            if case_name and case_name.lower() in combined_text.lower():
                score += 2
            
            # Score based on legal domain indicators
            legal_indicators = ['court', 'case', 'opinion', 'decision', 'judgment', 'legal']
            for indicator in legal_indicators:
                if indicator in combined_text.lower():
                    score += 0.5
            
            # Score based on URL quality
            if result.url:
                legal_domains = ['justia.com', 'findlaw.com', 'courtlistener.com', 'law.cornell.edu', 
                               'supreme.justia.com', 'casetext.com', 'leagle.com']
                for domain in legal_domains:
                    if domain in result.url.lower():
                        score += 2
                        break
            
            if score > best_score:
                best_score = score
                best_result = result
        
        return best_result if best_score >= 1 else None

class ComprehensiveWebSearchEngine:
    """
    Comprehensive legal citation web search combining the best of both engines.
    """
    
    def __init__(self, enable_experimental_engines=False):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        
        # Set reasonable timeouts
        self.session.timeout = 10
        
        # Initialize enhancement components
        self.citation_normalizer = EnhancedCitationNormalizer()
        self.cache_manager = CacheManager()
        self.source_predictor = SourcePredictor()
        self.semantic_matcher = SemanticMatcher()
        self.linkrot_detector = EnhancedLinkrotDetector(self.cache_manager)
        self.fusion_engine = ResultFusionEngine(self.semantic_matcher)
        self.ml_predictor = AdvancedMLPredictor(self.cache_manager)
        self.error_recovery = AdvancedErrorRecovery(self.cache_manager, self.ml_predictor)
        self.analytics = AdvancedAnalytics(self.cache_manager)
        
        # Canonical legal databases ranked by reliability
        self.canonical_sources = {
            # Primary official sources (highest reliability)
            'courtlistener.com': {'weight': 100, 'type': 'primary', 'official': True},
            'justia.com': {'weight': 95, 'type': 'primary', 'official': True},
            'leagle.com': {'weight': 90, 'type': 'primary', 'official': True},
            'caselaw.findlaw.com': {'weight': 85, 'type': 'primary', 'official': True},
            'scholar.google.com': {'weight': 80, 'type': 'primary', 'official': True},
            'cetient.com': {'weight': 85, 'type': 'primary', 'official': True},
            'casetext.com': {'weight': 75, 'type': 'primary', 'official': False},
            'openjurist.org': {'weight': 65, 'type': 'secondary', 'official': False},
            'vlex.com': {'weight': 80, 'type': 'primary', 'official': False},
            
            # Government sources (very high reliability)
            'supremecourt.gov': {'weight': 100, 'type': 'government', 'official': True},
            'uscourts.gov': {'weight': 100, 'type': 'government', 'official': True},
            
            # Academic sources
            'law.cornell.edu': {'weight': 70, 'type': 'academic', 'official': False},
            'law.duke.edu': {'weight': 60, 'type': 'academic', 'official': False},
            
            # Commercial but reliable (lower priority)
            'westlaw.com': {'weight': 85, 'type': 'commercial', 'official': False},
            'lexis.com': {'weight': 85, 'type': 'commercial', 'official': False},
        }
        
        # Rate limiting configuration
        self.rate_limits = {
            'google': {'delay': 2.0, 'last_request': 0},
            'bing': {'delay': 1.5, 'last_request': 0},
            'ddg': {'delay': 1.0, 'last_request': 0},
            'justia': {'delay': 1.0, 'last_request': 0},
            'findlaw': {'delay': 1.0, 'last_request': 0},
            'leagle': {'delay': 1.0, 'last_request': 0},
            'casetext': {'delay': 1.0, 'last_request': 0},
            'vlex': {'delay': 1.0, 'last_request': 0},
            'casemine': {'delay': 1.0, 'last_request': 0},
            'openjurist': {'delay': 1.0, 'last_request': 0},
            'google_scholar': {'delay': 2.0, 'last_request': 0},
        }
        
        # Method statistics for optimization
        self.method_stats = {
            'justia': {'success': 0, 'total': 0, 'avg_time': 0},
            'findlaw': {'success': 0, 'total': 0, 'avg_time': 0},
            'leagle': {'success': 0, 'total': 0, 'avg_time': 0},
            'casetext': {'success': 0, 'total': 0, 'avg_time': 0},
            'vlex': {'success': 0, 'total': 0, 'avg_time': 0},
            'casemine': {'success': 0, 'total': 0, 'avg_time': 0},
            'openjurist': {'success': 0, 'total': 0, 'avg_time': 0},
            'google_scholar': {'success': 0, 'total': 0, 'avg_time': 0},
            'bing': {'success': 0, 'total': 0, 'avg_time': 0},
            'duckduckgo': {'success': 0, 'total': 0, 'avg_time': 0},
        }
        
        # Rate limiting for individual methods
        self.method_rate_limits = {
            'justia': {'requests': 0, 'last_request': 0, 'max_per_minute': 30},
            'findlaw': {'requests': 0, 'last_request': 0, 'max_per_minute': 30},
            'leagle': {'requests': 0, 'last_request': 0, 'max_per_minute': 20},
            'casetext': {'requests': 0, 'last_request': 0, 'max_per_minute': 15},
            'vlex': {'requests': 0, 'last_request': 0, 'max_per_minute': 15},
            'casemine': {'requests': 0, 'last_request': 0, 'max_per_minute': 15},
            'openjurist': {'requests': 0, 'last_request': 0, 'max_per_minute': 20},
            'google_scholar': {'requests': 0, 'last_request': 0, 'max_per_minute': 10},
            'bing': {'requests': 0, 'last_request': 0, 'max_per_minute': 30},
            'duckduckgo': {'requests': 0, 'last_request': 0, 'max_per_minute': 30},
        }
        
        # Search engines to use
        self.enabled_engines = ['google', 'bing']
        if enable_experimental_engines:
            self.enabled_engines.append('ddg')
        
        # Cache for parsed domains to avoid repeated parsing
        self._domain_cache = {}
        
        # Initialize the web extractor
        self.extractor = ComprehensiveWebExtractor()
        
        # Statistics tracking
        self.stats = {
            'requests': 0,
            'successful': 0,
            'failed': 0,
            'rate_limited': 0
        }

    def generate_strategic_queries(self, cluster: Dict) -> List[Dict[str, str]]:
        """Generate focused, strategic search queries with enhanced citation variants."""
        queries = []
        
        # Extract citations with validation and enhanced normalization
        citations = set()
        normalized_citations = set()
        for citation_obj in cluster.get('citations', []):
            citation = citation_obj.get('citation', '').strip()
            if citation and len(citation) > 5:  # Basic validation
                citations.add(citation)
                
                # Use enhanced citation normalizer for comprehensive variants
                enhanced_variants = self.citation_normalizer.generate_variants(citation)
                normalized_citations.update(enhanced_variants)
        
        # Extract case names with enhanced validation
        case_names = set()
        for name_field in ['canonical_name', 'extracted_case_name', 'case_name']:
            if cluster.get(name_field):
                case_name = cluster[name_field]
                # Clean the case name
                cleaned_name = self.extractor._clean_case_name(case_name)
                if cleaned_name:
                    case_names.update(self.extract_case_name_variants(cleaned_name))
        
        # Extract years
        years = set()
        for date_field in ['canonical_date', 'extracted_date', 'date']:
            if cluster.get(date_field):
                year_match = re.search(r'\b(19|20)\d{2}\b', str(cluster[date_field]))
                if year_match:
                    years.add(year_match.group(0))
        
        # Priority 1: Exact citations on canonical sources (including enhanced variants)
        for citation in citations:
            queries.append({
                'query': f'"{citation}"',
                'priority': 1,
                'type': 'exact_citation',
                'citation': citation
            })
        
        # Add enhanced citation variants
        for citation in normalized_citations:
            if citation not in citations:  # Avoid duplicates
                queries.append({
                    'query': f'"{citation}"',
                    'priority': 1,
                    'type': 'exact_citation_enhanced',
                    'citation': citation
                })
        
        # Priority 2: Citations with legal context
        for citation in citations:
            queries.append({
                'query': f'"{citation}" case opinion',
                'priority': 2,
                'type': 'citation_with_context',
                'citation': citation
            })
        
        # Priority 3: Case name + citation combinations
        for case_name in case_names:
            for citation in citations:
                queries.append({
                    'query': f'"{case_name}" "{citation}"',
                    'priority': 3,
                    'type': 'case_name_citation',
                    'case_name': case_name,
                    'citation': citation
                })
            
            # Also try with enhanced variants
            for citation in normalized_citations:
                if citation not in citations:
                    queries.append({
                        'query': f'"{case_name}" "{citation}"',
                        'priority': 3,
                        'type': 'case_name_citation_enhanced',
                        'case_name': case_name,
                        'citation': citation
                    })
        
        # Priority 4: Broader searches with year
        for citation in citations:
            for year in years:
                queries.append({
                    'query': f'"{citation}" {year}',
                    'priority': 4,
                    'type': 'citation_year',
                    'citation': citation,
                    'year': year
                })
        
        # Priority 5: Use source prediction for optimized search order
        if citations:
            # Get predicted sources for the first citation
            first_citation = list(citations)[0]
            case_name = cluster.get('canonical_name') or cluster.get('case_name')
            predicted_sources = self.source_predictor.predict_best_sources(first_citation, case_name)
            
            # Add source-specific queries
            for source in predicted_sources[:3]:  # Top 3 predicted sources
                for citation in citations:
                    queries.append({
                        'query': f'site:{source} "{citation}"',
                        'priority': 5,
                        'type': 'source_specific',
                        'citation': citation,
                        'predicted_source': source
                    })
        
        # Sort by priority and remove duplicates
        seen_queries = set()
        unique_queries = []
        for query in sorted(queries, key=lambda x: x['priority']):
            query_str = query['query']
            if query_str not in seen_queries:
                seen_queries.add(query_str)
                unique_queries.append(query)
        
        return unique_queries

    def extract_case_name_variants(self, case_name: str) -> Set[str]:
        """Generate search variants of a case name with improved cleaning."""
        if not case_name or case_name in ('N/A', 'Unknown', ''):
            return set()
            
        variants = set()
        case_name = case_name.strip()
        
        if len(case_name) < 3:  # Skip very short names
            return set()
            
        variants.add(case_name)
        
        # Clean corporate suffixes more aggressively
        corporate_suffixes = [
            r'\b(?:LLC|Inc\.?|Corp\.?|Co\.?|Ltd\.?|L\.P\.?|LLP|LP)\b',
            r'\b(?:Corporation|Company|Limited|Partnership)\b'
        ]
        
        cleaned = case_name
        for suffix_pattern in corporate_suffixes:
            cleaned = re.sub(suffix_pattern, '', cleaned, flags=re.I)
        
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        if cleaned and cleaned != case_name and len(cleaned) > 3:
            variants.add(cleaned)
        
        # Extract party names from "X v. Y" format
        adversarial_match = re.search(r'^([^v]+)\s+v\.?\s+([^,\(]+)', case_name, re.I)
        if adversarial_match:
            plaintiff = adversarial_match.group(1).strip()
            defendant = adversarial_match.group(2).strip()
            
            if len(plaintiff) > 2 and len(defendant) > 2:
                variants.add(f"{plaintiff} v. {defendant}")
                variants.add(f"{plaintiff} v {defendant}")
                
                # Add individual parties only if they're substantial
                if len(plaintiff) > 4:
                    variants.add(plaintiff)
                if len(defendant) > 4:
                    variants.add(defendant)
        
        # Handle "In re" and "Ex parte" cases
        special_case_match = re.search(r'^(?:In re|Ex parte)\s+(.+)', case_name, re.I)
        if special_case_match:
            subject = special_case_match.group(1).strip()
            if len(subject) > 3:
                variants.add(subject)
        
        return {v for v in variants if len(v.strip()) > 2}

    def score_result_reliability(self, result: Dict, query_info: Dict) -> float:
        """Score result reliability based on source and content quality."""
        score = 0.0
        
        # Base score from canonical source ranking
        domain = self._get_domain_from_url(result.get('url', ''))
        if domain in self.canonical_sources:
            score += self.canonical_sources[domain]['weight'] / 100.0
        
        # Boost for exact citation matches
        if query_info.get('type') == 'exact_citation':
            citation = query_info.get('citation', '')
            if citation and citation.lower() in result.get('title', '').lower():
                score += 0.3
            if citation and citation.lower() in result.get('snippet', '').lower():
                score += 0.2
        
        # Boost for case name matches
        if query_info.get('case_name'):
            case_name = query_info['case_name'].lower()
            if case_name in result.get('title', '').lower():
                score += 0.2
            if case_name in result.get('snippet', '').lower():
                score += 0.1
        
        # Penalty for generic results
        generic_terms = ['search', 'find', 'directory', 'index', 'list']
        title_lower = result.get('title', '').lower()
        if any(term in title_lower for term in generic_terms):
            score -= 0.2
        
        # Boost for recent results (if year is available)
        if query_info.get('year'):
            year = query_info['year']
            if year in result.get('title', '') or year in result.get('snippet', ''):
                score += 0.1
        
        return min(1.0, max(0.0, score))

    def _get_domain_from_url(self, url: str) -> str:
        """Extract domain from URL with caching."""
        if not url:
            return ''
        
        if url in self._domain_cache:
            return self._domain_cache[url]
        
        try:
            domain = urlparse(url).netloc.lower()
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            self._domain_cache[url] = domain
            return domain
        except Exception:
            return ''

    def _rate_limit_check(self, engine: str):
        """Check and enforce rate limits."""
        if engine in self.rate_limits:
            last_request = self.rate_limits[engine]['last_request']
            delay = self.rate_limits[engine]['delay']
            
            time_since_last = time.time() - last_request
            if time_since_last < delay:
                sleep_time = delay - time_since_last
                time.sleep(sleep_time)
            
            self.rate_limits[engine]['last_request'] = time.time()

    def search_with_engine(self, query: str, engine: str, num_results: int = 5) -> List[Dict]:
        """Search with a specific engine."""
        self._rate_limit_check(engine)
        
        try:
            if engine == 'google':
                return self._google_search(query, num_results)
            elif engine == 'bing':
                return self._bing_search(query, num_results)
            elif engine == 'ddg':
                return self._ddg_search(query, num_results)
            else:
                logger.warning(f"Unknown search engine: {engine}")
                return []
        except Exception as e:
            logger.error(f"Error searching with {engine}: {e}")
            return []

    def _google_search(self, query: str, num_results: int) -> List[Dict]:
        """Google search implementation."""
        try:
            # Use a simple Google search approach
            search_url = "https://www.google.com/search"
            params = {
                'q': query,
                'num': min(num_results, 10),  # Google limit
                'hl': 'en'
            }
            
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Extract search results
            for result in soup.find_all('div', class_='g'):
                title_elem = result.find('h3')
                link_elem = result.find('a')
                snippet_elem = result.find('div', class_='VwiC3b')
                
                if title_elem and link_elem:
                    title = title_elem.get_text().strip()
                    url = link_elem.get('href', '')
                    snippet = snippet_elem.get_text().strip() if snippet_elem else ''
                    
                    if url.startswith('/url?q='):
                        url = url.split('/url?q=')[1].split('&')[0]
                    
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'source': 'google'
                    })
            
            return results[:num_results]
            
        except Exception as e:
            logger.error(f"Google search error: {e}")
            return []

    def _bing_search(self, query: str, num_results: int) -> List[Dict]:
        """Bing search implementation."""
        try:
            search_url = "https://www.bing.com/search"
            params = {
                'q': query,
                'count': num_results
            }
            
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Extract search results
            for result in soup.find_all('li', class_='b_algo'):
                title_elem = result.find('h2')
                link_elem = title_elem.find('a') if title_elem else None
                snippet_elem = result.find('p')
                
                if title_elem and link_elem:
                    title = title_elem.get_text().strip()
                    url = link_elem.get('href', '')
                    snippet = snippet_elem.get_text().strip() if snippet_elem else ''
                    
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'source': 'bing'
                    })
            
            return results[:num_results]
            
        except Exception as e:
            logger.error(f"Bing search error: {e}")
            return []

    def _ddg_search(self, query: str, num_results: int) -> List[Dict]:
        """DuckDuckGo search implementation."""
        try:
            search_url = "https://html.duckduckgo.com/html/"
            params = {
                'q': query
            }
            
            response = self.session.post(search_url, data=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Extract search results
            for result in soup.find_all('div', class_='result'):
                title_elem = result.find('a', class_='result__a')
                snippet_elem = result.find('a', class_='result__snippet')
                
                if title_elem:
                    title = title_elem.get_text().strip()
                    url = title_elem.get('href', '')
                    snippet = snippet_elem.get_text().strip() if snippet_elem else ''
                    
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet,
                        'source': 'duckduckgo'
                    })
            
            return results[:num_results]
            
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []

    async def search_vlex(self, citation: str, case_name: str = None) -> Dict:
        """Search Vlex for legal cases with enhanced URL patterns."""
        try:
            # Try multiple vlex search URL patterns for better coverage
            vlex_urls = [
                f"https://vlex.com/search?q={quote_plus(citation)}",
                f"https://vlex.com/sites/search?q={quote_plus(citation)}"
            ]
            
            if case_name:
                # Also try with case name
                combined_query = f'"{citation}" "{case_name}"'
                vlex_urls.extend([
                    f"https://vlex.com/search?q={quote_plus(combined_query)}",
                    f"https://vlex.com/sites/search?q={quote_plus(combined_query)}"
                ])
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive'
            }
            
            # Try each URL pattern
            for search_url in vlex_urls:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(search_url, headers=headers, timeout=15) as response:
                            if response.status == 200:
                                content = await response.text()
                                
                                # Extract case information using our enhanced extractor
                                extracted = self.extractor.extract_from_page_content(content, str(response.url), citation)
                                
                                if extracted.get('case_name'):
                                    return {
                                        'case_name': extracted['case_name'],
                                        'date': extracted.get('date'),
                                        'court': extracted.get('court'),
                                        'url': extracted.get('canonical_url', search_url),
                                        'source': 'vLex (Enhanced)',
                                        'confidence': min(0.8, 0.4 + extracted.get('confidence', 0)),
                                        'verified': True,
                                        'search_url_used': search_url
                                    }
                                
                                # If no direct extraction, try specialized vlex extraction
                                vlex_result = self.extractor.extract_from_legal_database(str(response.url), content)
                                if vlex_result.get('case_name'):
                                    return {
                                        'case_name': vlex_result['case_name'],
                                        'date': vlex_result.get('date'),
                                        'court': vlex_result.get('court'),
                                        'url': search_url,
                                        'source': 'vLex (Specialized)',
                                        'confidence': min(0.7, 0.3 + vlex_result.get('confidence', 0)),
                                        'verified': True,
                                        'search_url_used': search_url
                                    }
                                
                except Exception as e:
                    logger.debug(f"vLex search failed for {search_url}: {e}")
                    continue
            
            return {'verified': False, 'error': 'Citation not found in vLex'}
            
        except Exception as e:
            logger.error(f"Vlex search error: {e}")
            return {'verified': False, 'error': str(e)}

    async def search_casetext(self, citation: str, case_name: str = None) -> Dict:
        """Enhanced Casetext search with advanced extraction."""
        if not self._respect_rate_limit('casetext'):
            return {'verified': False, 'error': 'Rate limited'}
        
        start_time = time.time()
        try:
            search_queries = [
                citation,
                f'"{citation}"',
                citation.replace(' ', '+')
            ]
            
            if case_name:
                search_queries.insert(0, f'"{citation}" "{case_name}"')
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://casetext.com/'
            }
            
            for query in search_queries:
                try:
                    url = f"https://casetext.com/search?q={quote_plus(query)}"
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=headers, timeout=15) as response:
                            if response.status == 200:
                                content = await response.text()
                                
                                # Look for citation in results
                                if re.search(re.escape(citation), content, re.IGNORECASE):
                                    # Extract case links and follow them
                                    from bs4 import BeautifulSoup
                                    soup = BeautifulSoup(content, 'html.parser')
                                    
                                    # Find case result links
                                    case_links = soup.find_all('a', href=True)
                                    for link in case_links:
                                        href = link.get('href', '')
                                        if '/case/' in href and citation.replace(' ', '') in link.get_text().replace(' ', ''):
                                            # Follow the case link
                                            case_url = urljoin('https://casetext.com', href)
                                            
                                            try:
                                                async with session.get(case_url, headers=headers, timeout=10) as case_response:
                                                    if case_response.status == 200:
                                                        case_content = await case_response.text()
                                                        
                                                        # Extract detailed information from case page
                                                        extracted_data = self.extractor.extract_from_page_content(
                                                            case_content, str(case_response.url), citation
                                                        )
                                                        
                                                        if extracted_data.get('case_name'):
                                                            duration = time.time() - start_time
                                                            self._update_stats('casetext', True, duration)
                                                            
                                                            return {
                                                                'case_name': extracted_data['case_name'],
                                                                'date': extracted_data.get('date'),
                                                                'court': extracted_data.get('court'),
                                                                'docket_number': extracted_data.get('docket_number'),
                                                                'url': extracted_data['canonical_url'],
                                                                'source': 'Casetext (Enhanced)',
                                                                'confidence': min(0.85, 0.4 + extracted_data.get('confidence', 0)),
                                                                'verified': True
                                                            }
                            
                                            except Exception as e:
                                                logger.debug(f"Casetext case page failed: {e}")
                                                continue
                
                except Exception as e:
                    logger.debug(f"Casetext query '{query}' failed: {e}")
                    continue
            
            duration = time.time() - start_time
            self._update_stats('casetext', False, duration)
            return {'verified': False, 'error': 'Citation not found'}
                
        except Exception as e:
            duration = time.time() - start_time
            self._update_stats('casetext', False, duration)
            logger.debug(f"Casetext search failed: {e}")
            return {'verified': False, 'error': str(e)}

    async def search_justia(self, citation: str, case_name: str = None) -> Dict:
        """Enhanced Justia search with multiple strategies and best content extraction."""
        if not self._respect_rate_limit('justia'):
            return {'verified': False, 'error': 'Rate limited'}
        
        start_time = time.time()
        try:
            search_urls = []
            
            # Strategy 1: Direct URL construction for US Supreme Court
            if 'U.S.' in citation:
                match = re.search(r'(\d+)\s+U\.S\.\s+(\d+)', citation)
                if match:
                    volume, page = match.groups()
                    search_urls.append(f"https://supreme.justia.com/cases/federal/us/{volume}/{page}/")
            
            # Strategy 2: Citation search with multiple endpoints
            search_queries = [
                citation,
                f'"{citation}"',
                citation.replace(' ', '+')
            ]
            
            if case_name:
                search_queries.insert(0, f'"{citation}" "{case_name}"')
            
            for query in search_queries:
                search_urls.extend([
                    f"https://law.justia.com/search?query={quote_plus(query)}",
                    f"https://law.justia.com/cases/search?query={quote_plus(query)}",
                    f"https://supreme.justia.com/search?query={quote_plus(query)}"
                ])
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive'
            }
            
            for url in search_urls:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=headers, timeout=10) as response:
                            if response.status == 200:
                                content = await response.text()
                                
                                # Use extractor for comprehensive analysis
                                result = self.extractor.extract_from_page_content(content, url, citation)
                                if result.get('case_name'):
                                    duration = time.time() - start_time
                                    self._update_stats('justia', True, duration)
                                    result['confidence'] = 0.9  # High confidence for Justia
                                    result['verified'] = True
                                    result['source'] = 'Justia (Enhanced)'
                                    return result
                                    
                except Exception as e:
                    logger.debug(f"Justia URL {url} failed: {e}")
                    continue
            
            duration = time.time() - start_time
            self._update_stats('justia', False, duration)
            return {'verified': False, 'error': 'Citation not found'}
                
        except Exception as e:
            duration = time.time() - start_time
            self._update_stats('justia', False, duration)
            logger.debug(f"Justia search failed: {e}")
            return {'verified': False, 'error': str(e)}

    async def search_courtlistener_web(self, citation: str, case_name: str = None) -> Dict:
        """Enhanced CourtListener web search with advanced extraction."""
        if not self._respect_rate_limit('courtlistener_web'):
            return {'verified': False, 'error': 'Rate limited'}
        
        start_time = time.time()
        try:
            # Build comprehensive search queries
            queries = [
                f'"{citation}"',
                citation,
                f'cite:"{citation}"'
            ]
            
            if case_name:
                queries.insert(0, f'"{citation}" "{case_name}"')
            
            for query in queries:
                try:
                    url = f"https://www.courtlistener.com/?q={quote_plus(query)}"
                    
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Referer': 'https://www.courtlistener.com/',
                        'DNT': '1'
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=headers, timeout=15) as response:
                            if response.status == 200:
                                content = await response.text()
                                
                                # Look for citation in results
                                if re.search(re.escape(citation), content, re.IGNORECASE):
                                    # Extract case links and follow them
                                    from bs4 import BeautifulSoup
                                    soup = BeautifulSoup(content, 'html.parser')
                                    
                                    # Find case result links
                                    case_links = soup.find_all('a', href=True)
                                    for link in case_links:
                                        href = link.get('href', '')
                                        if '/opinion/' in href and citation.replace(' ', '') in link.get_text().replace(' ', ''):
                                            # Follow the case link
                                            case_url = urljoin('https://www.courtlistener.com', href)
                                            
                                            try:
                                                async with session.get(case_url, headers=headers, timeout=10) as case_response:
                                                    if case_response.status == 200:
                                                        case_content = await case_response.text()
                                                        
                                                        # Extract detailed information from case page
                                                        extracted_data = self.extractor.extract_from_page_content(
                                                            case_content, str(case_response.url), citation
                                                        )
                                                        
                                                        if extracted_data.get('case_name'):
                                                            duration = time.time() - start_time
                                                            self._update_stats('courtlistener_web', True, duration)
                                                            
                                                            return {
                                                                'case_name': extracted_data['case_name'],
                                                                'date': extracted_data.get('date'),
                                                                'court': extracted_data.get('court'),
                                                                'docket_number': extracted_data.get('docket_number'),
                                                                'url': extracted_data['canonical_url'],
                                                                'source': 'CourtListener Web (Enhanced)',
                                                                'confidence': min(0.9, 0.4 + extracted_data.get('confidence', 0)),
                                                                'verified': True
                                                            }
                            
                                            except Exception as e:
                                                logger.debug(f"CourtListener case page failed: {e}")
                                                continue
                
                except Exception as e:
                    logger.debug(f"CourtListener query '{query}' failed: {e}")
                    continue
            
            duration = time.time() - start_time
            self._update_stats('courtlistener_web', False, duration)
            return {'verified': False, 'error': 'Citation not found'}
                
        except Exception as e:
            duration = time.time() - start_time
            self._update_stats('courtlistener_web', False, duration)
            logger.debug(f"CourtListener web search failed: {e}")
            return {'verified': False, 'error': str(e)}

    async def search_findlaw(self, citation: str, case_name: str = None) -> Dict:
        """Enhanced FindLaw search with advanced extraction."""
        if not self._respect_rate_limit('findlaw'):
            return {'verified': False, 'error': 'Rate limited'}
        
        start_time = time.time()
        try:
            search_urls = []
            
            # Strategy 1: Direct URL construction for major courts
            if 'U.S.' in citation:
                match = re.search(r'(\d+)\s+U\.S\.\s+(\d+)', citation)
                if match:
                    volume, page = match.groups()
                    search_urls.append(f"https://caselaw.findlaw.com/us-supreme-court/{volume}/{page}.html")
            
            # Strategy 2: Search endpoints with multiple approaches
            search_queries = [
                citation,
                f'"{citation}"',
                citation.replace(' ', '+')
            ]
            
            if case_name:
                search_queries.insert(0, f'"{citation}" "{case_name}"')
            
            for query in search_queries:
                search_urls.extend([
                    f"https://caselaw.findlaw.com/search?query={quote_plus(query)}",
                    f"https://caselaw.findlaw.com/search?q={quote_plus(query)}",
                    f"https://www.findlaw.com/casecode/search.html?q={quote_plus(query)}"
                ])
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Referer": "https://www.findlaw.com/"
            }
            
            for url in search_urls:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=headers, timeout=15) as response:
                            if response.status == 200:
                                content = await response.text()
                                
                                # Use extractor for comprehensive analysis
                                result = self.extractor.extract_from_page_content(content, url, citation)
                                if result.get('case_name'):
                                    duration = time.time() - start_time
                                    self._update_stats('findlaw', True, duration)
                                    result['confidence'] = 0.85  # High confidence for FindLaw
                                    result['verified'] = True
                                    result['source'] = 'FindLaw (Enhanced)'
                                    return result
                                    
                except Exception as e:
                    logger.debug(f"FindLaw URL {url} failed: {e}")
                    continue
            
            duration = time.time() - start_time
            self._update_stats('findlaw', False, duration)
            return {'verified': False, 'error': 'Citation not found'}
                
        except Exception as e:
            duration = time.time() - start_time
            self._update_stats('findlaw', False, duration)
            logger.debug(f"FindLaw search failed: {e}")
            return {'verified': False, 'error': str(e)}

    async def search_leagle(self, citation: str, case_name: str = None) -> Dict:
        """Enhanced Leagle search with advanced extraction."""
        if not self._respect_rate_limit('leagle'):
            return {'verified': False, 'error': 'Rate limited'}
        
        start_time = time.time()
        try:
            search_queries = [
                citation,
                f'"{citation}"',
                citation.replace(' ', '+')
            ]
            
            if case_name:
                search_queries.insert(0, f'"{citation}" "{case_name}"')
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.leagle.com/'
            }
            
            for query in search_queries:
                try:
                    url = f"https://www.leagle.com/search?query={quote_plus(query)}"
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=headers, timeout=15) as response:
                            if response.status == 200:
                                content = await response.text()
                                
                                # Look for citation in results
                                if re.search(re.escape(citation), content, re.IGNORECASE):
                                    # Extract case links and follow them
                                    from bs4 import BeautifulSoup
                                    soup = BeautifulSoup(content, 'html.parser')
                                    
                                    # Find case result links
                                    case_links = soup.find_all('a', href=True)
                                    for link in case_links:
                                        href = link.get('href', '')
                                        if '/case/' in href and citation.replace(' ', '') in link.get_text().replace(' ', ''):
                                            # Follow the case link
                                            case_url = urljoin('https://www.leagle.com', href)
                                            
                                            try:
                                                async with session.get(case_url, headers=headers, timeout=10) as case_response:
                                                    if case_response.status == 200:
                                                        case_content = await case_response.text()
                                                        
                                                        # Extract detailed information from case page
                                                        extracted_data = self.extractor.extract_from_page_content(
                                                            case_content, str(case_response.url), citation
                                                        )
                                                        
                                                        if extracted_data.get('case_name'):
                                                            duration = time.time() - start_time
                                                            self._update_stats('leagle', True, duration)
                                                            
                                                            return {
                                                                'case_name': extracted_data['case_name'],
                                                                'date': extracted_data.get('date'),
                                                                'court': extracted_data.get('court'),
                                                                'docket_number': extracted_data.get('docket_number'),
                                                                'url': extracted_data['canonical_url'],
                                                                'source': 'Leagle (Enhanced)',
                                                                'confidence': min(0.85, 0.4 + extracted_data.get('confidence', 0)),
                                                                'verified': True
                                                            }
                            
                                            except Exception as e:
                                                logger.debug(f"Leagle case page failed: {e}")
                                                continue
                
                except Exception as e:
                    logger.debug(f"Leagle query '{query}' failed: {e}")
                    continue
            
            duration = time.time() - start_time
            self._update_stats('leagle', False, duration)
            return {'verified': False, 'error': 'Citation not found'}
                
        except Exception as e:
            duration = time.time() - start_time
            self._update_stats('leagle', False, duration)
            logger.debug(f"Leagle search failed: {e}")
            return {'verified': False, 'error': str(e)}

    async def search_openjurist(self, citation: str, case_name: str = None) -> Dict:
        """Enhanced OpenJurist search with advanced extraction."""
        if not self._respect_rate_limit('openjurist'):
            return {'verified': False, 'error': 'Rate limited'}
        
        start_time = time.time()
        try:
            search_queries = [
                citation,
                f'"{citation}"',
                citation.replace(' ', '+')
            ]
            
            if case_name:
                search_queries.insert(0, f'"{citation}" "{case_name}"')
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://openjurist.org/'
            }
            
            for query in search_queries:
                try:
                    url = f"https://openjurist.org/search?q={quote_plus(query)}"
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=headers, timeout=15) as response:
                            if response.status == 200:
                                content = await response.text()
                                
                                # Use extractor for comprehensive analysis
                                result = self.extractor.extract_from_page_content(content, url, citation)
                                if result.get('case_name'):
                                    duration = time.time() - start_time
                                    self._update_stats('openjurist', True, duration)
                                    result['confidence'] = 0.8  # Good confidence for OpenJurist
                                    result['verified'] = True
                                    result['source'] = 'OpenJurist (Enhanced)'
                                    return result
                                    
                except Exception as e:
                    logger.debug(f"OpenJurist query '{query}' failed: {e}")
                    continue
            
            duration = time.time() - start_time
            self._update_stats('openjurist', False, duration)
            return {'verified': False, 'error': 'Citation not found'}
                
        except Exception as e:
            duration = time.time() - start_time
            self._update_stats('openjurist', False, duration)
            logger.debug(f"OpenJurist search failed: {e}")
            return {'verified': False, 'error': str(e)}

    async def search_casemine(self, citation: str, case_name: str = None) -> Dict:
        """Enhanced CaseMine search with advanced extraction."""
        if not self._respect_rate_limit('casemine'):
            return {'verified': False, 'error': 'Rate limited'}
        
        start_time = time.time()
        try:
            search_queries = [
                citation,
                f'"{citation}"',
                citation.replace(' ', '+')
            ]
            
            if case_name:
                search_queries.insert(0, f'"{citation}" "{case_name}"')
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.casemine.com/'
            }
            
            for query in search_queries:
                try:
                    url = f"https://www.casemine.com/search?q={quote_plus(query)}"
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=headers, timeout=15) as response:
                            if response.status == 200:
                                content = await response.text()
                                
                                # Look for citation in results
                                if re.search(re.escape(citation), content, re.IGNORECASE):
                                    # Extract case links and follow them
                                    from bs4 import BeautifulSoup
                                    soup = BeautifulSoup(content, 'html.parser')
                                    
                                    # Find case result links
                                    case_links = soup.find_all('a', href=True)
                                    for link in case_links:
                                        href = link.get('href', '')
                                        if '/judgment/' in href and citation.replace(' ', '') in link.get_text().replace(' ', ''):
                                            # Follow the case link
                                            case_url = urljoin('https://www.casemine.com', href)
                                            
                                            try:
                                                async with session.get(case_url, headers=headers, timeout=10) as case_response:
                                                    if case_response.status == 200:
                                                        case_content = await case_response.text()
                                                        
                                                        # Extract detailed information from case page
                                                        extracted_data = self.extractor.extract_from_page_content(
                                                            case_content, str(case_response.url), citation
                                                        )
                                                        
                                                        if extracted_data.get('case_name'):
                                                            duration = time.time() - start_time
                                                            self._update_stats('casemine', True, duration)
                                                            
                                                            return {
                                                                'case_name': extracted_data['case_name'],
                                                                'date': extracted_data.get('date'),
                                                                'court': extracted_data.get('court'),
                                                                'docket_number': extracted_data.get('docket_number'),
                                                                'url': extracted_data['canonical_url'],
                                                                'source': 'CaseMine (Enhanced)',
                                                                'confidence': min(0.85, 0.4 + extracted_data.get('confidence', 0)),
                                                                'verified': True
                                                            }
                            
                                            except Exception as e:
                                                logger.debug(f"CaseMine case page failed: {e}")
                                                continue
                
                except Exception as e:
                    logger.debug(f"CaseMine query '{query}' failed: {e}")
                    continue
            
            duration = time.time() - start_time
            self._update_stats('casemine', False, duration)
            return {'verified': False, 'error': 'Citation not found'}
                
        except Exception as e:
            duration = time.time() - start_time
            self._update_stats('casemine', False, duration)
            logger.debug(f"CaseMine search failed: {e}")
            return {'verified': False, 'error': str(e)}

    async def search_google_scholar(self, citation: str, case_name: str = None) -> Dict:
        """Enhanced Google Scholar search with advanced extraction."""
        if not self._respect_rate_limit('google_scholar'):
            return {'verified': False, 'error': 'Rate limited'}
        
        start_time = time.time()
        try:
            search_queries = [
                f'"{citation}"',
                citation,
                f'cite:"{citation}"'
            ]
            
            if case_name:
                search_queries.insert(0, f'"{citation}" "{case_name}"')
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://scholar.google.com/'
            }
            
            for query in search_queries:
                try:
                    url = f"https://scholar.google.com/scholar?q={quote_plus(query)}"
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=headers, timeout=15) as response:
                            if response.status == 200:
                                content = await response.text()
                                
                                # Extract search results
                                search_results = self.extractor.extract_from_search_results(content, 'google_scholar')
                                
                                # Find best result
                                best_result = self.extractor._find_best_search_result(search_results, citation, case_name)
                                
                                if best_result:
                                    # Follow the best result link
                                    try:
                                        async with session.get(best_result.url, headers=headers, timeout=10) as result_response:
                                            if result_response.status == 200:
                                                result_content = await result_response.text()
                                                
                                                # Extract detailed information from result page
                                                extracted_data = self.extractor.extract_from_page_content(
                                                    result_content, str(result_response.url), citation
                                                )
                                                
                                                if extracted_data.get('case_name'):
                                                    duration = time.time() - start_time
                                                    self._update_stats('google_scholar', True, duration)
                                                    
                                                    return {
                                                        'case_name': extracted_data['case_name'],
                                                        'date': extracted_data.get('date'),
                                                        'court': extracted_data.get('court'),
                                                        'docket_number': extracted_data.get('docket_number'),
                                                        'url': extracted_data['canonical_url'],
                                                        'source': 'Google Scholar (Enhanced)',
                                                        'confidence': min(0.8, 0.4 + extracted_data.get('confidence', 0)),
                                                        'verified': True
                                                    }
                                    
                                    except Exception as e:
                                        logger.debug(f"Google Scholar result page failed: {e}")
                                        continue
                
                except Exception as e:
                    logger.debug(f"Google Scholar query '{query}' failed: {e}")
                    continue
            
            duration = time.time() - start_time
            self._update_stats('google_scholar', False, duration)
            return {'verified': False, 'error': 'Citation not found'}
                
        except Exception as e:
            duration = time.time() - start_time
            self._update_stats('google_scholar', False, duration)
            logger.debug(f"Google Scholar search failed: {e}")
            return {'verified': False, 'error': str(e)}

    async def search_bing(self, citation: str, case_name: str = None) -> Dict:
        """Enhanced Bing search with advanced extraction."""
        if not self._respect_rate_limit('bing'):
            return {'verified': False, 'error': 'Rate limited'}
        
        start_time = time.time()
        try:
            search_queries = [
                f'"{citation}"',
                citation,
                f'cite:"{citation}"'
            ]
            
            if case_name:
                search_queries.insert(0, f'"{citation}" "{case_name}"')
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.bing.com/'
            }
            
            for query in search_queries:
                try:
                    url = f"https://www.bing.com/search?q={quote_plus(query)}"
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=headers, timeout=15) as response:
                            if response.status == 200:
                                content = await response.text()
                                
                                # Extract search results
                                search_results = self.extractor.extract_from_search_results(content, 'bing')
                                
                                # Find best result
                                best_result = self.extractor._find_best_search_result(search_results, citation, case_name)
                                
                                if best_result:
                                    # Follow the best result link
                                    try:
                                        async with session.get(best_result.url, headers=headers, timeout=10) as result_response:
                                            if result_response.status == 200:
                                                result_content = await result_response.text()
                                                
                                                # Extract detailed information from result page
                                                extracted_data = self.extractor.extract_from_page_content(
                                                    result_content, str(result_response.url), citation
                                                )
                                                
                                                if extracted_data.get('case_name'):
                                                    duration = time.time() - start_time
                                                    self._update_stats('bing', True, duration)
                                                    
                                                    return {
                                                        'case_name': extracted_data['case_name'],
                                                        'date': extracted_data.get('date'),
                                                        'court': extracted_data.get('court'),
                                                        'docket_number': extracted_data.get('docket_number'),
                                                        'url': extracted_data['canonical_url'],
                                                        'source': 'Bing (Enhanced)',
                                                        'confidence': min(0.75, 0.4 + extracted_data.get('confidence', 0)),
                                                        'verified': True
                                                    }
                                    
                                    except Exception as e:
                                        logger.debug(f"Bing result page failed: {e}")
                                        continue
                
                except Exception as e:
                    logger.debug(f"Bing query '{query}' failed: {e}")
                    continue
            
            duration = time.time() - start_time
            self._update_stats('bing', False, duration)
            return {'verified': False, 'error': 'Citation not found'}
                
        except Exception as e:
            duration = time.time() - start_time
            self._update_stats('bing', False, duration)
            logger.debug(f"Bing search failed: {e}")
            return {'verified': False, 'error': str(e)}

    async def search_duckduckgo(self, citation: str, case_name: str = None) -> Dict:
        """Enhanced DuckDuckGo search with advanced extraction."""
        if not self._respect_rate_limit('duckduckgo'):
            return {'verified': False, 'error': 'Rate limited'}
        
        start_time = time.time()
        try:
            search_queries = [
                f'"{citation}"',
                citation,
                f'cite:"{citation}"'
            ]
            
            if case_name:
                search_queries.insert(0, f'"{citation}" "{case_name}"')
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://duckduckgo.com/'
            }
            
            for query in search_queries:
                try:
                    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=headers, timeout=15) as response:
                            if response.status == 200:
                                content = await response.text()
                                
                                # Extract search results
                                search_results = self.extractor.extract_from_search_results(content, 'duckduckgo')
                                
                                # Find best result
                                best_result = self.extractor._find_best_search_result(search_results, citation, case_name)
                                
                                if best_result:
                                    # Follow the best result link
                                    try:
                                        async with session.get(best_result.url, headers=headers, timeout=10) as result_response:
                                            if result_response.status == 200:
                                                result_content = await result_response.text()
                                                
                                                # Extract detailed information from result page
                                                extracted_data = self.extractor.extract_from_page_content(
                                                    result_content, str(result_response.url), citation
                                                )
                                                
                                                if extracted_data.get('case_name'):
                                                    duration = time.time() - start_time
                                                    self._update_stats('duckduckgo', True, duration)
                                                    
                                                    return {
                                                        'case_name': extracted_data['case_name'],
                                                        'date': extracted_data.get('date'),
                                                        'court': extracted_data.get('court'),
                                                        'docket_number': extracted_data.get('docket_number'),
                                                        'url': extracted_data['canonical_url'],
                                                        'source': 'DuckDuckGo (Enhanced)',
                                                        'confidence': min(0.75, 0.4 + extracted_data.get('confidence', 0)),
                                                        'verified': True
                                                    }
                                    
                                    except Exception as e:
                                        logger.debug(f"DuckDuckGo result page failed: {e}")
                                        continue
                
                except Exception as e:
                    logger.debug(f"DuckDuckGo query '{query}' failed: {e}")
                    continue
            
            duration = time.time() - start_time
            self._update_stats('duckduckgo', False, duration)
            return {'verified': False, 'error': 'Citation not found'}
                
        except Exception as e:
            duration = time.time() - start_time
            self._update_stats('duckduckgo', False, duration)
            logger.debug(f"DuckDuckGo search failed: {e}")
            return {'verified': False, 'error': str(e)}

    async def search_multiple_sources(self, citation: str, case_name: str = None, max_concurrent: int = 3) -> Dict:
        """Search multiple sources concurrently with intelligent prioritization and graceful fallbacks."""
        start_time = time.time()
        
        # Get prioritized search methods
        search_methods = self.get_search_priority()
        
        # Create tasks for concurrent execution
        tasks = []
        for method in search_methods[:max_concurrent]:
            if hasattr(self, f'search_{method}'):
                task = asyncio.create_task(getattr(self, f'search_{method}')(citation, case_name))
                tasks.append((method, task))
        
        try:
            # Execute all tasks concurrently
            results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                method = tasks[i][0]
                
                # Handle exceptions gracefully
                if isinstance(result, Exception):
                    logger.warning(f"Search method {method} failed with exception: {result}")
                    continue
                
                # Check if we got a successful result
                if result.get('verified') and result.get('case_name'):
                    duration = time.time() - start_time
                    logger.info(f"Found result using {method} in {duration:.2f}s")
                    return result
            
            # If no successful results, try fallback
            logger.info("No successful results from primary methods, trying fallback")
            return await self._fallback_search(citation, case_name)
            
        except Exception as e:
            logger.error(f"Multiple sources search failed: {e}")
            # If all methods fail, try a fallback approach
            return await self._fallback_search(citation, case_name)

    async def _fallback_search(self, citation: str, case_name: str = None) -> Dict:
        """
        DEPRECATED: Use isolation-aware search logic instead.
        Fallback search using simpler methods when all primary methods fail.
        """
        warnings.warn(
            "_fallback_search is deprecated. Use isolation-aware search logic instead.",
            DeprecationWarning,
            stacklevel=2
        )
        logger.info(f"Attempting fallback search for citation: {citation}")
        
        try:
            # Try simple web search as fallback
            fallback_result = await self.search_bing(citation, case_name)
            if fallback_result.get('verified'):
                fallback_result['source'] = f"{fallback_result['source']} (Fallback)"
                return fallback_result
            
            # Try DuckDuckGo as second fallback
            fallback_result = await self.search_duckduckgo(citation, case_name)
            if fallback_result.get('verified'):
                fallback_result['source'] = f"{fallback_result['source']} (Fallback)"
                return fallback_result
            
            return {
                'verified': False,
                'error': 'All search methods failed'
            }
            
        except Exception as e:
            logger.error(f"Fallback search failed: {e}")
            return {
                'verified': False,
                'error': f'Fallback search failed: {str(e)}'
            }

    async def search_cluster_canonical(self, cluster: Dict, max_results: int = 10) -> List[Dict]:
        """Search for canonical legal sources with enhanced caching and optimization."""
        
        # Check cache first
        cache_key = f"cluster_search_{hash(str(cluster))}_{max_results}"
        cached_results = self.cache_manager.get(cache_key)
        if cached_results:
            logger.info(f"Cache hit for cluster search: {len(cached_results)} results")
            return cached_results
        
        # Generate strategic queries with enhanced normalizer
        queries = self.generate_strategic_queries(cluster)
        if not queries:
            logger.warning("No valid queries generated from cluster")
            return []
        
        all_results = []
        seen_urls = set()
        
        logger.info(f"Executing {len(queries)} strategic queries with enhanced optimization")
        
        # Execute searches in priority order with source prediction
        for i, query_info in enumerate(queries):
            if len(all_results) >= max_results:
                break
            
            query = query_info['query']
            logger.debug(f"Query {i+1}: {query} (strategy: {query_info['type']})")
            
            # Use source prediction for optimized search order
            if 'predicted_source' in query_info:
                # Use predicted source first
                predicted_source = query_info['predicted_source']
                engines = [predicted_source] + [e for e in self.enabled_engines if e != predicted_source]
            else:
                # Use default engine order
                engines = self.enabled_engines.copy()
                random.shuffle(engines)
            
            for engine in engines:
                try:
                    results = self.search_with_engine(query, engine, num_results=3)
                    
                    for result in results:
                        url = result['url']
                        if url not in seen_urls and self._is_valid_result(result):
                            # Score result reliability with enhanced scoring
                            score = self.score_result_reliability(result, query_info)
                            
                            result.update({
                                'reliability_score': score,
                                'query_strategy': query_info['type'],
                                'query_priority': query_info['priority'],
                                'search_engine': engine,
                                'expected_reliability': query_info.get('expected_reliability', 50)
                            })
                            
                            all_results.append(result)
                            seen_urls.add(url)
                            
                            if len(all_results) >= max_results:
                                break
                    
                    if len(all_results) >= max_results:
                        break
                        
                except Exception as e:
                    logger.error(f"Search failed for {engine} with query '{query}': {e}")
                    continue
            
            # Brief pause between query batches
            if i < len(queries) - 1:
                time.sleep(0.3)
        
        # Use result fusion for intelligent grouping and scoring
        if all_results:
            # Extract citation and case name for fusion
            citation = ""
            case_name = ""
            if cluster.get('citations'):
                citation = cluster['citations'][0].get('citation', '')
            case_name = cluster.get('canonical_name') or cluster.get('case_name', '')
            
            # Fuse results using semantic matching
            fused_results = self.fusion_engine.fuse_results(all_results, citation, case_name)
            
            # Check URL accessibility for fused results
            await self._check_accessibility_batch(fused_results)
            
            final_results = fused_results[:max_results]
        else:
            final_results = []
        
        # Cache the results
        self.cache_manager.set(cache_key, final_results, ttl_hours=24)
        
        logger.info(f"Found {len(all_results)} total results, fused to {len(final_results)} results")
        
        return final_results

    def _is_valid_result(self, result: Dict) -> bool:
        """Check if a search result is valid and useful."""
        if not result.get('url'):
            return False
        
        # Skip certain types of results
        skip_domains = ['youtube.com', 'facebook.com', 'twitter.com', 'instagram.com']
        domain = self._get_domain_from_url(result['url'])
        if any(skip_domain in domain for skip_domain in skip_domains):
            return False
        
        # Skip very short titles
        if len(result.get('title', '')) < 10:
            return False
        
        return True

    def _respect_rate_limit(self, method: str) -> bool:
        """Check if we can make a request to the given method based on rate limits."""
        if method not in self.method_rate_limits:
            return True
        
        now = time.time()
        rate_limit = self.method_rate_limits[method]
        
        # Reset counter if a minute has passed
        if now - rate_limit['last_request'] >= 60:
            rate_limit['requests'] = 0
            rate_limit['last_request'] = now
        
        # Check if we're under the limit
        if rate_limit['requests'] < rate_limit['max_per_minute']:
            rate_limit['requests'] += 1
            rate_limit['last_request'] = now
            return True
        
        return False

    def _update_stats(self, method: str, success: bool, duration: float):
        """Update statistics for a method call."""
        if method not in self.method_stats:
            return
        
        stats = self.method_stats[method]
        stats['total'] += 1
        
        if success:
            stats['success'] += 1
        
        # Update average time (exponential moving average)
        if stats['total'] == 1:
            stats['avg_time'] = duration
        else:
            stats['avg_time'] = 0.9 * stats['avg_time'] + 0.1 * duration

    def get_search_priority(self) -> List[str]:
        """Get search methods prioritized by success rate and speed."""
        method_scores = []
        for method, stats in self.method_stats.items():
            if stats['total'] > 0:
                success_rate = stats['success'] / stats['total']
                # Score = success_rate * speed_factor (inverse of avg_time)
                speed_factor = 1 / (stats['avg_time'] + 0.1)
                score = success_rate * speed_factor
                method_scores.append((method, score))
            else:
                # Default priority for untested methods
                default_priorities = {
                    'justia': 1.0,
                    'findlaw': 0.9,
                    'courtlistener_web': 0.8,
                    'google_scholar': 0.6,
                    'vlex': 0.7,
                    'casetext': 0.7,
                    'leagle': 0.6,
                    'casemine': 0.6,
                    'openjurist': 0.5,
                    'bing': 0.5,
                    'duckduckgo': 0.4,
                }
                score = default_priorities.get(method, 0.05)
                method_scores.append((method, score))
        
        # Sort by score (highest first)
        method_scores.sort(key=lambda x: x[1], reverse=True)
        return [method for method, _ in method_scores]

    async def _check_url_accessibility(self, url: str) -> Dict[str, Any]:
        """Check if a URL is still accessible."""
        if not url:
            return {'accessible': False, 'status_code': None, 'error': 'No URL provided'}
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive'
            }
            
            # Use a shorter timeout for accessibility check
            async with aiohttp.ClientSession() as session:
                async with session.head(url, headers=headers, timeout=5, allow_redirects=True) as response:
                    return {
                        'accessible': response.status < 400,
                        'status_code': response.status,
                        'error': None
                    }
                    
        except asyncio.TimeoutError:
            return {'accessible': False, 'status_code': None, 'error': 'Timeout'}
        except Exception as e:
            return {'accessible': False, 'status_code': None, 'error': str(e)}

    async def _check_accessibility_batch(self, results: List[Dict]):
        """Check URL accessibility for a batch of results."""
        accessibility_tasks = []
        
        for result in results:
            if result.get('url'):
                task = asyncio.create_task(self.linkrot_detector.check_url_status(result['url']))
                accessibility_tasks.append((result, task))
        
        if accessibility_tasks:
            completed_checks = await asyncio.gather(
                *[task for _, task in accessibility_tasks], 
                return_exceptions=True
            )
            
            for i, status_result in enumerate(completed_checks):
                result, _ = accessibility_tasks[i]
                
                if isinstance(status_result, dict):
                    result['accessibility_status'] = status_result.get('status', 'unknown')
                    result['last_checked'] = status_result.get('last_checked')
                    
                    if status_result.get('status') == 'linkrot':
                        # Try to recover dead links
                        recovery_urls = await self.linkrot_detector.recover_dead_link(
                            result['url'], {
                                'case_name': result.get('title', ''),
                                'citation': result.get('citation', '')
                            }
                        )
                        
                        if recovery_urls:
                            result['recovery_urls'] = recovery_urls
                            result['accessibility_status'] = 'recovered'

# Convenience functions
def search_cluster_for_canonical_sources(cluster: Dict, max_results: int = 10) -> List[Dict]:
    """Convenience function to search for canonical sources."""
    engine = ComprehensiveWebSearchEngine()
    return engine.search_cluster_canonical(cluster, max_results)

def search_all_engines(query: str, num_results: int = 5, engines: List[str] = None) -> List[Dict]:
    """Convenience function to search all engines."""
    if engines is None:
        engines = ['google', 'bing']
    
    engine = ComprehensiveWebSearchEngine()
    all_results = []
    
    for search_engine in engines:
        results = engine.search_with_engine(query, search_engine, num_results)
        all_results.extend(results)
    
    return all_results

def test_comprehensive_web_search():
    """Test the comprehensive web search engine."""
    print("=== Testing Comprehensive Web Search Engine ===\n")
    
    # Test cluster
    test_cluster = {
        'citations': [
            {'citation': '200 Wn.2d 72'},
            {'citation': '514 P.3d 643'}
        ],
        'canonical_name': 'Convoyant, LLC v. DeepThink, LLC',
        'canonical_date': '2022'
    }
    
    engine = ComprehensiveWebSearchEngine()
    
    print("Testing query generation:")
    queries = engine.generate_strategic_queries(test_cluster)
    for i, query in enumerate(queries[:5]):  # Show first 5 queries
        print(f"  {i+1}. {query['query']} (Priority: {query['priority']}, Type: {query['type']})")
    
    print("\nTesting search (limited to 3 results):")
    results = engine.search_cluster_canonical(test_cluster, max_results=3)
    
    for i, result in enumerate(results):
        print(f"\nResult {i+1}:")
        print(f"  Title: {result.get('title', 'N/A')}")
        print(f"  URL: {result.get('url', 'N/A')}")
        print(f"  Reliability Score: {result.get('reliability_score', 0):.2f}")
        print(f"  Source: {result.get('source', 'N/A')}")
        if result.get('extracted_info'):
            extracted = result['extracted_info']
            print(f"  Extracted Case Name: {extracted.get('case_name', 'N/A')}")
            print(f"  Extracted Date: {extracted.get('date', 'N/A')}")
            print(f"  Confidence: {extracted.get('confidence', 0):.2f}")

class CacheManager:
    """Advanced caching system with SQLite backend and TTL support."""
    
    def __init__(self, cache_file: str = "legal_search_cache.db", ttl_hours: int = 24):
        self.cache_file = cache_file
        self.ttl = timedelta(hours=ttl_hours)
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database for caching."""
        import sqlite3
        from datetime import timedelta
        import pickle
        
        conn = sqlite3.connect(self.cache_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_cache (
                key TEXT PRIMARY KEY,
                value TEXT,
                timestamp DATETIME,
                ttl_hours INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS url_status (
                url TEXT PRIMARY KEY,
                status TEXT,
                status_code INTEGER,
                last_checked DATETIME,
                content_hash TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _generate_key(self, *args) -> str:
        """Generate cache key from arguments."""
        key_string = "|".join(str(arg) for arg in args)
        return hashlib.md5(key_string.encode('utf-8'), usedforsecurity=False).hexdigest()
    
    def get(self, *args) -> Optional[Any]:
        """Get cached value."""
        import sqlite3
        import pickle
        from datetime import datetime, timedelta
        
        key = self._generate_key(*args)
        
        conn = sqlite3.connect(self.cache_file)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT value, timestamp, ttl_hours FROM search_cache WHERE key = ?',
            (key,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            value_str, timestamp_str, ttl_hours = result
            timestamp = datetime.fromisoformat(timestamp_str)
            ttl = timedelta(hours=ttl_hours)
            
            if datetime.now() - timestamp < ttl:
                try:
                    return pickle.loads(value_str.encode('latin1'))
                except Exception:
                    return None
            else:
                # Expired, remove it
                self.delete(*args)
        
        return None
    
    def set(self, *args, value: Any, ttl_hours: Optional[int] = None):
        """Set cached value."""
        import sqlite3
        import pickle
        from datetime import datetime
        
        key = self._generate_key(*args[:-1])  # Exclude value from key
        ttl_hours = ttl_hours or (self.ttl.total_seconds() / 3600)
        
        conn = sqlite3.connect(self.cache_file)
        cursor = conn.cursor()
        
        try:
            value_str = pickle.dumps(value).decode('latin1')
            cursor.execute(
                'INSERT OR REPLACE INTO search_cache (key, value, timestamp, ttl_hours) VALUES (?, ?, ?, ?)',
                (key, value_str, datetime.now().isoformat(), ttl_hours)
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to cache value: {e}")
        finally:
            conn.close()
    
    def delete(self, *args):
        """Delete cached value."""
        import sqlite3
        
        key = self._generate_key(*args)
        
        conn = sqlite3.connect(self.cache_file)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM search_cache WHERE key = ?', (key,))
        conn.commit()
        conn.close()
    
    def cleanup_expired(self):
        """Remove expired cache entries."""
        import sqlite3
        
        conn = sqlite3.connect(self.cache_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM search_cache 
            WHERE datetime(timestamp, '+' || ttl_hours || ' hours') < datetime('now')
        ''')
        
        conn.commit()
        conn.close()
    
    def get_url_status(self, url: str) -> Optional[Dict[str, Any]]:
        """Get cached URL accessibility status."""
        import sqlite3
        from datetime import datetime, timedelta
        
        conn = sqlite3.connect(self.cache_file)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT status, status_code, last_checked, content_hash FROM url_status WHERE url = ?',
            (url,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            status, status_code, last_checked_str, content_hash = result
            last_checked = datetime.fromisoformat(last_checked_str)
            
            # Return cached status if checked within last hour
            if datetime.now() - last_checked < timedelta(hours=1):
                return {
                    'status': status,
                    'status_code': status_code,
                    'last_checked': last_checked,
                    'content_hash': content_hash
                }
        
        return None
    
    def set_url_status(self, url: str, status: str, status_code: int = None, content_hash: str = None):
        """Cache URL accessibility status."""
        import sqlite3
        from datetime import datetime
        
        conn = sqlite3.connect(self.cache_file)
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT OR REPLACE INTO url_status (url, status, status_code, last_checked, content_hash) VALUES (?, ?, ?, ?, ?)',
            (url, status, status_code, datetime.now().isoformat(), content_hash)
        )
        
        conn.commit()
        conn.close()

class SourcePredictor:
    """ML-based source prediction for optimal search strategy."""
    
    def __init__(self):
        self.citation_patterns = {
            'washington_state': [r'Wn\.?\s*\d+', r'Wash\.?\s*\d+', r'Washington\s+\d+'],
            'federal_supreme': [r'U\.S\.?\s+\d+', r'US\s+\d+'],
            'federal_circuit': [r'F\.?\s*\d+', r'Fed\.?\s*\d+'],
            'pacific_reporter': [r'P\.?\s*\d+', r'Pac\.?\s*\d+', r'Pacific\s+\d+'],
        }
        
        self.source_affinity = {
            'washington_state': ['justia', 'findlaw', 'courtlistener_web', 'leagle'],
            'federal_supreme': ['justia', 'findlaw', 'google_scholar', 'courtlistener_web'],
            'federal_circuit': ['justia', 'findlaw', 'leagle', 'casetext'],
            'pacific_reporter': ['justia', 'findlaw', 'leagle', 'vlex'],
        }
    
    def predict_best_sources(self, citation: str, case_name: str = None) -> List[str]:
        """Predict the best sources for a given citation."""
        predicted_sources = set()
        
        # Pattern-based prediction
        for pattern_type, patterns in self.citation_patterns.items():
            for pattern in patterns:
                if re.search(pattern, citation, re.IGNORECASE):
                    predicted_sources.update(self.source_affinity.get(pattern_type, []))
                    break
        
        # Date-based prediction (newer cases more likely in certain sources)
        year_match = re.search(r'\b(19|20)\d{2}\b', citation)
        if year_match:
            year = int(year_match.group(0))
            if year >= 2010:
                predicted_sources.update(['casetext', 'vlex', 'google_scholar'])
            if year >= 2000:
                predicted_sources.update(['justia', 'findlaw'])
        
        # Case name based prediction
        if case_name:
            if re.search(r'\bUnited States\b', case_name, re.IGNORECASE):
                predicted_sources.update(['justia', 'findlaw', 'google_scholar'])
            if re.search(r'\bState\b.*\bv\b', case_name, re.IGNORECASE):
                predicted_sources.update(['justia', 'findlaw', 'leagle'])
        
        # Return sorted by priority
        all_sources = ['justia', 'findlaw', 'courtlistener_web', 'leagle', 'casetext', 
                      'vlex', 'google_scholar', 'bing', 'duckduckgo']
        
        # Prioritize predicted sources, then add others
        result = [s for s in all_sources if s in predicted_sources]
        result.extend([s for s in all_sources if s not in predicted_sources])
        
        return result

class SemanticMatcher:
    """Enhanced semantic matching for legal text using TF-IDF and cosine similarity."""
    
    def __init__(self):
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
            import threading
            
            self.vectorizer = TfidfVectorizer(
                stop_words='english',
                ngram_range=(1, 3),
                max_features=5000,
                min_df=1,
                max_df=0.95
            )
            self.is_fitted = False
            self._lock = threading.Lock()
            self.np = np
            self.cosine_similarity = cosine_similarity
        except ImportError:
            logger.warning("scikit-learn not available, using fallback similarity")
            self.vectorizer = None
            self.is_fitted = False
    
    def preprocess_legal_text(self, text: str) -> str:
        """Preprocess legal text for better matching."""
        if not text:
            return ""
        
        # Normalize case names
        text = re.sub(r'\bv\.?\s+', ' v. ', text, flags=re.IGNORECASE)
        
        # Normalize common legal terms
        text = re.sub(r'\bDep\'t\b', 'Department', text)
        text = re.sub(r'\bCorp\.?\b', 'Corporation', text)
        text = re.sub(r'\bInc\.?\b', 'Incorporated', text)
        text = re.sub(r'\bLLC\b', 'Limited Liability Company', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        return text.lower()
    
    def fit_documents(self, documents: List[str]):
        """Fit the vectorizer on a collection of documents."""
        if not self.vectorizer:
            return
            
        with self._lock:
            if documents:
                processed_docs = [self.preprocess_legal_text(doc) for doc in documents]
                self.vectorizer.fit(processed_docs)
                self.is_fitted = True
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts."""
        if not text1 or not text2:
            return 0.0
        
        processed1 = self.preprocess_legal_text(text1)
        processed2 = self.preprocess_legal_text(text2)
        
        # Simple character-based similarity as fallback
        if not self.vectorizer or not self.is_fitted:
            return SequenceMatcher(None, processed1, processed2).ratio()
        
        try:
            with self._lock:
                vectors = self.vectorizer.transform([processed1, processed2])
                similarity = self.cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
                return float(similarity)
        except Exception:
            # Fallback to character-based similarity
            return SequenceMatcher(None, processed1, processed2).ratio()
    
    def find_best_match(self, query: str, candidates: List[str], threshold: float = 0.3) -> Tuple[Optional[str], float]:
        """Find the best matching candidate for a query."""
        if not candidates:
            return None, 0.0
        
        best_match = None
        best_score = 0.0
        
        for candidate in candidates:
            score = self.calculate_similarity(query, candidate)
            if score > best_score and score >= threshold:
                best_score = score
                best_match = candidate
        
        return best_match, best_score

class EnhancedLinkrotDetector:
    """Advanced linkrot detection with recovery strategies."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.recovery_strategies = [
            self._try_wayback_machine,
            self._try_alternative_domains,
            self._try_similar_urls,
        ]
    
    async def check_url_status(self, url: str) -> Dict[str, Any]:
        """Check URL accessibility with caching."""
        if not url:
            return {'status': 'invalid', 'accessible': False}
        
        # Check cache first
        cached_status = self.cache.get_url_status(url)
        if cached_status:
            return {
                'status': cached_status['status'],
                'accessible': cached_status['status'] == 'accessible',
                'status_code': cached_status['status_code'],
                'last_checked': cached_status['last_checked']
            }
        
        # Check URL accessibility
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.head(url, headers=headers, timeout=10, allow_redirects=True) as response:
                    if response.status < 400:
                        status = 'accessible'
                        accessible = True
                    elif response.status == 403:
                        status = 'paywall'
                        accessible = False
                    else:
                        status = 'linkrot'
                        accessible = False
                    
                    self.cache.set_url_status(url, status, response.status)
                    
                    return {
                        'status': status,
                        'accessible': accessible,
                        'status_code': response.status,
                        'last_checked': datetime.now()
                    }
        
        except Exception as e:
            status = 'linkrot'
            self.cache.set_url_status(url, status, None)
            
            return {
                'status': status,
                'accessible': False,
                'error': str(e),
                'last_checked': datetime.now()
            }
    
    async def recover_dead_link(self, url: str, metadata: Dict[str, Any] = None) -> List[str]:
        """Attempt to recover a dead link using various strategies."""
        recovery_urls = []
        
        for strategy in self.recovery_strategies:
            try:
                recovered = await strategy(url, metadata)
                recovery_urls.extend(recovered)
            except Exception as e:
                logger.debug(f"Recovery strategy failed: {e}")
        
        return recovery_urls
    
    async def _try_wayback_machine(self, url: str, metadata: Dict[str, Any] = None) -> List[str]:
        """Try to find the URL in Wayback Machine."""
        wayback_urls = []
        
        try:
            # Query Wayback Machine API
            api_url = f"http://archive.org/wayback/available?url={quote(url)}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('archived_snapshots', {}).get('closest', {}).get('available'):
                            wayback_url = data['archived_snapshots']['closest']['url']
                            wayback_urls.append(wayback_url)
        
        except Exception as e:
            logger.debug(f"Wayback Machine lookup failed: {e}")
        
        return wayback_urls
    
    async def _try_alternative_domains(self, url: str, metadata: Dict[str, Any] = None) -> List[str]:
        """Try alternative domains for the same content."""
        alternative_urls = []
        
        try:
            parsed = urlparse(url)
            path = parsed.path
            
            # Common domain alternatives
            domain_alternatives = {
                'caselaw.findlaw.com': ['findlaw.com', 'laws.findlaw.com'],
                'law.justia.com': ['justia.com', 'supreme.justia.com'],
                'www.leagle.com': ['leagle.com'],
                'casetext.com': ['www.casetext.com'],
            }
            
            original_domain = parsed.netloc
            if original_domain in domain_alternatives:
                for alt_domain in domain_alternatives[original_domain]:
                    alt_url = f"{parsed.scheme}://{alt_domain}{path}"
                    alternative_urls.append(alt_url)
        
        except Exception as e:
            logger.debug(f"Alternative domain generation failed: {e}")
        
        return alternative_urls
    
    async def _try_similar_urls(self, url: str, metadata: Dict[str, Any] = None) -> List[str]:
        """Try to construct similar URLs based on metadata."""
        similar_urls = []
        
        if not metadata:
            return similar_urls
        
        try:
            # If we have case name and citation, try to construct URLs
            case_name = metadata.get('case_name', '')
            citation = metadata.get('citation', '')
            
            if case_name and citation:
                # Try different URL patterns
                case_slug = re.sub(r'[^a-z0-9]+', '-', case_name.lower()).strip('-')
                citation_slug = re.sub(r'[^a-z0-9]+', '-', citation.lower()).strip('-')
                
                url_patterns = [
                    f"https://law.justia.com/cases/{case_slug}",
                    f"https://caselaw.findlaw.com/case/{case_slug}",
                    f"https://www.leagle.com/decision/{citation_slug}",
                    f"https://casetext.com/case/{case_slug}",
                ]
                
                similar_urls.extend(url_patterns)
        
        except Exception as e:
            logger.debug(f"Similar URL generation failed: {e}")
        
        return similar_urls

class ResultFusionEngine:
    """Advanced result fusion with cross-validation and confidence scoring."""
    
    def __init__(self, semantic_matcher: SemanticMatcher):
        self.semantic_matcher = semantic_matcher
    
    def fuse_results(self, results: List[Dict], query_citation: str, query_case_name: str = None) -> List[Dict]:
        """Fuse and rank results from multiple sources."""
        if not results:
            return []
        
        # Group results by URL similarity
        url_groups = self._group_by_url_similarity(results)
        
        # Fuse each group
        fused_results = []
        for group in url_groups:
            fused_result = self._fuse_result_group(group, query_citation, query_case_name)
            if fused_result:
                fused_results.append(fused_result)
        
        # Calculate final scores and rank
        for result in fused_results:
            result['reliability_score'] = self._calculate_reliability_score(result, query_citation, query_case_name)
            if query_case_name:
                result['semantic_score'] = self.semantic_matcher.calculate_similarity(
                    result.get('title', ''), query_case_name
                )
        
        # Sort by combined score
        fused_results.sort(key=lambda r: (r.get('reliability_score', 0) + r.get('semantic_score', 0)) / 2, reverse=True)
        
        return fused_results
    
    def _group_by_url_similarity(self, results: List[Dict]) -> List[List[Dict]]:
        """Group results by URL similarity."""
        groups = []
        used_indices = set()
        
        for i, result1 in enumerate(results):
            if i in used_indices:
                continue
            
            group = [result1]
            used_indices.add(i)
            
            for j, result2 in enumerate(results[i+1:], i+1):
                if j in used_indices:
                    continue
                
                # Check if URLs are similar (same domain, similar path)
                if self._are_urls_similar(result1.get('url', ''), result2.get('url', '')):
                    group.append(result2)
                    used_indices.add(j)
            
            groups.append(group)
        
        return groups
    
    def _are_urls_similar(self, url1: str, url2: str, threshold: float = 0.8) -> bool:
        """Check if two URLs are similar enough to be considered the same resource."""
        if not url1 or not url2:
            return False
        
        try:
            parsed1 = urlparse(url1)
            parsed2 = urlparse(url2)
            
            # Same domain
            if parsed1.netloc != parsed2.netloc:
                return False
            
            # Similar paths
            path_similarity = SequenceMatcher(None, parsed1.path, parsed2.path).ratio()
            return path_similarity >= threshold
        
        except Exception:
            return False
    
    def _fuse_result_group(self, group: List[Dict], query_citation: str, query_case_name: str = None) -> Optional[Dict]:
        """Fuse a group of similar results into a single result."""
        if not group:
            return None
        
        if len(group) == 1:
            return group[0]
        
        # Use the result with highest confidence as base
        base_result = max(group, key=lambda r: r.get('reliability_score', 0))
        
        # Merge information from all results
        fused = base_result.copy()
        
        # Collect all titles and pick the best one
        titles = [r.get('title', '') for r in group if r.get('title')]
        if titles:
            if query_case_name:
                best_title, score = self.semantic_matcher.find_best_match(query_case_name, titles)
                fused['title'] = best_title or max(titles, key=len)
            else:
                fused['title'] = max(titles, key=len)
        
        # Merge other fields
        snippets = [r.get('snippet', '') for r in group if r.get('snippet')]
        fused['snippet'] = max(snippets, key=len) if snippets else ''
        
        # Combine sources
        sources = list(set(r.get('source', '') for r in group if r.get('source')))
        fused['source'] = " + ".join(sources[:3])  # Limit to 3 sources
        
        # Average reliability score
        scores = [r.get('reliability_score', 0) for r in group]
        fused['reliability_score'] = sum(scores) / len(scores)
        
        # Add fusion metadata
        fused['fusion_metadata'] = {
            'group_size': len(group),
            'original_sources': sources,
            'fusion_method': 'semantic_grouping'
        }
        
        return fused
    
    def _calculate_reliability_score(self, result: Dict, query_citation: str, query_case_name: str = None) -> float:
        """Calculate reliability score for a result."""
        score = 0.0
        
        # Base confidence
        score += result.get('reliability_score', 0) * 0.3
        
        # Source reliability
        source_scores = {
            'justia': 0.9,
            'findlaw': 0.85,
            'courtlistener': 0.9,
            'leagle': 0.8,
            'casetext': 0.75,
            'vlex': 0.7,
            'google scholar': 0.6,
            'bing': 0.4,
            'duckduckgo': 0.4,
        }
        
        source_score = 0.0
        source = result.get('source', '').lower()
        for source_name, weight in source_scores.items():
            if source_name in source:
                source_score = max(source_score, weight)
        score += source_score * 0.3
        
        # Citation match
        if query_citation:
            citation_text = f"{result.get('title', '')} {result.get('snippet', '')}"
            if query_citation.lower() in citation_text.lower():
                score += 0.2
        
        # Case name match
        if query_case_name and result.get('title'):
            name_similarity = self.semantic_matcher.calculate_similarity(result['title'], query_case_name)
            score += name_similarity * 0.2
        
        return min(1.0, score)

class AdvancedMLPredictor:
    """Advanced ML-based prediction for search optimization and error recovery."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.feature_weights = {
            'citation_pattern': 0.25,
            'case_name_complexity': 0.20,
            'year_recency': 0.15,
            'court_type': 0.20,
            'historical_success': 0.20
        }
        
        # Historical success rates by source and citation type
        self.success_rates = {
            'washington_state': {
                'justia': 0.85,
                'findlaw': 0.80,
                'courtlistener_web': 0.90,
                'leagle': 0.75,
                'casetext': 0.70
            },
            'federal_supreme': {
                'justia': 0.90,
                'findlaw': 0.85,
                'google_scholar': 0.80,
                'courtlistener_web': 0.95
            },
            'federal_circuit': {
                'justia': 0.80,
                'findlaw': 0.75,
                'leagle': 0.85,
                'casetext': 0.80
            }
        }
    
    def extract_features(self, citation: str, case_name: str = None) -> Dict[str, Any]:
        """Extract comprehensive features for ML prediction."""
        features = {}
        
        # Citation pattern features
        features['citation_pattern'] = self._extract_citation_pattern(citation)
        features['volume_number'] = self._extract_volume_number(citation)
        features['reporter_type'] = self._extract_reporter_type(citation)
        features['year'] = self._extract_year(citation)
        
        # Case name features
        if case_name:
            features['case_name_complexity'] = self._calculate_name_complexity(case_name)
            features['party_count'] = self._count_parties(case_name)
            features['has_abbreviations'] = self._has_abbreviations(case_name)
        
        # Court type features
        features['court_type'] = self._determine_court_type(citation, case_name)
        
        # Year recency features
        if features.get('year'):
            features['year_recency'] = self._calculate_year_recency(features['year'])
        
        return features
    
    def _extract_citation_pattern(self, citation: str) -> str:
        """Extract the citation pattern type."""
        patterns = {
            'washington_state': [r'Wn\.?\s*\d+', r'Wash\.?\s*\d+'],
            'federal_supreme': [r'U\.S\.?\s+\d+'],
            'federal_circuit': [r'F\.?\s*\d+', r'Fed\.?\s*\d+'],
            'pacific_reporter': [r'P\.?\s*\d+', r'Pac\.?\s*\d+']
        }
        
        for pattern_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, citation, re.IGNORECASE):
                    return pattern_type
        
        return 'unknown'
    
    def _extract_volume_number(self, citation: str) -> Optional[int]:
        """Extract volume number from citation."""
        match = re.search(r'(\d+)\s+[A-Za-z]', citation)
        return int(match.group(1)) if match else None
    
    def _extract_reporter_type(self, citation: str) -> str:
        """Extract reporter type from citation."""
        reporters = {
            'Wn.': 'washington',
            'Wash.': 'washington',
            'U.S.': 'supreme',
            'F.': 'federal',
            'P.': 'pacific'
        }
        
        for abbrev, reporter_type in reporters.items():
            if abbrev in citation:
                return reporter_type
        
        return 'unknown'
    
    def _extract_year(self, citation: str) -> Optional[int]:
        """Extract year from citation."""
        match = re.search(r'\b(19|20)\d{2}\b', citation)
        return int(match.group(0)) if match else None
    
    def _calculate_name_complexity(self, case_name: str) -> float:
        """Calculate case name complexity score."""
        if not case_name:
            return 0.0
        
        # Factors: length, special characters, abbreviations
        length_factor = min(len(case_name) / 100, 1.0)
        special_char_factor = len(re.findall(r'[&,\.]', case_name)) / 10
        abbrev_factor = len(re.findall(r'\b[A-Z]{2,}\b', case_name)) / 5
        
        return min(length_factor + special_char_factor + abbrev_factor, 1.0)
    
    def _count_parties(self, case_name: str) -> int:
        """Count number of parties in case name."""
        if not case_name:
            return 0
        
        # Count "v." occurrences
        return len(re.findall(r'\bv\.?\b', case_name, re.IGNORECASE))
    
    def _has_abbreviations(self, case_name: str) -> bool:
        """Check if case name has abbreviations."""
        if not case_name:
            return False
        
        return bool(re.search(r'\b(LLC|Inc|Corp|Co|Ltd|Dep\'t|Dept)\b', case_name, re.IGNORECASE))
    
    def _determine_court_type(self, citation: str, case_name: str = None) -> str:
        """Determine court type from citation and case name."""
        # Check citation patterns first
        if re.search(r'Wn\.?\s*\d+', citation, re.IGNORECASE):
            return 'washington_state'
        elif re.search(r'U\.S\.?\s+\d+', citation, re.IGNORECASE):
            return 'federal_supreme'
        elif re.search(r'F\.?\s*\d+', citation, re.IGNORECASE):
            return 'federal_circuit'
        
        # Check case name patterns
        if case_name:
            if re.search(r'\bState\b.*\bv\.?\b', case_name, re.IGNORECASE):
                return 'state_court'
            elif re.search(r'\bUnited States\b', case_name, re.IGNORECASE):
                return 'federal_court'
        
        return 'unknown'
    
    def _calculate_year_recency(self, year: int) -> float:
        """Calculate year recency score (0-1, newer = higher)."""
        current_year = datetime.now().year
        age = current_year - year
        
        if age <= 5:
            return 1.0
        elif age <= 10:
            return 0.8
        elif age <= 20:
            return 0.6
        elif age <= 50:
            return 0.4
        else:
            return 0.2
    
    def predict_optimal_sources(self, citation: str, case_name: str = None) -> List[Tuple[str, float]]:
        """Predict optimal sources with confidence scores."""
        features = self.extract_features(citation, case_name)
        court_type = features.get('court_type', 'unknown')
        
        # Get base success rates for this court type
        base_rates = self.success_rates.get(court_type, {})
        
        # Calculate adjusted scores based on features
        source_scores = []
        for source, base_rate in base_rates.items():
            score = base_rate
            
            # Adjust based on year recency
            if features.get('year_recency'):
                if features['year_recency'] > 0.8:  # Recent case
                    if source in ['casetext', 'vlex']:
                        score *= 1.2
                else:  # Older case
                    if source in ['justia', 'findlaw']:
                        score *= 1.1
            
            # Adjust based on case name complexity
            if features.get('case_name_complexity', 0) > 0.7:
                if source in ['justia', 'findlaw']:
                    score *= 1.1
            
            # Adjust based on citation pattern
            if features.get('citation_pattern') == 'washington_state':
                if source in ['justia', 'findlaw', 'courtlistener_web']:
                    score *= 1.15
            
            source_scores.append((source, min(score, 1.0)))
        
        # Sort by score (highest first)
        source_scores.sort(key=lambda x: x[1], reverse=True)
        
        return source_scores
    
    def update_success_rate(self, source: str, court_type: str, success: bool):
        """Update historical success rates based on actual results."""
        cache_key = f"success_rate_{source}_{court_type}"
        
        # Get current rates
        current_data = self.cache.get(cache_key) or {'successes': 0, 'total': 0}
        
        current_data['total'] += 1
        if success:
            current_data['successes'] += 1
        
        # Update cache
        self.cache.set(cache_key, current_data, ttl_hours=168)  # 1 week
        
        # Update in-memory rates
        if court_type in self.success_rates and source in self.success_rates[court_type]:
            new_rate = current_data['successes'] / current_data['total']
            self.success_rates[court_type][source] = new_rate

class AdvancedErrorRecovery:
    """Advanced error recovery with intelligent fallback strategies."""
    
    def __init__(self, cache_manager: CacheManager, ml_predictor: AdvancedMLPredictor):
        self.cache = cache_manager
        self.ml_predictor = ml_predictor
        self.error_patterns = {
            'rate_limit': [r'rate.?limit', r'too.?many.?requests', r'429'],
            'timeout': [r'timeout', r'timed.?out', r'connection.?timeout'],
            'not_found': [r'404', r'not.?found', r'page.?not.?found'],
            'server_error': [r'500', r'server.?error', r'internal.?error'],
            'access_denied': [r'403', r'access.?denied', r'forbidden'],
            'network_error': [r'connection.?refused', r'network.?unreachable']
        }
        
        self.recovery_strategies = {
            'rate_limit': self._handle_rate_limit,
            'timeout': self._handle_timeout,
            'not_found': self._handle_not_found,
            'server_error': self._handle_server_error,
            'access_denied': self._handle_access_denied,
            'network_error': self._handle_network_error
        }
    
    def classify_error(self, error: Exception) -> str:
        """Classify error type for appropriate recovery strategy."""
        error_str = str(error).lower()
        
        for error_type, patterns in self.error_patterns.items():
            for pattern in patterns:
                if re.search(pattern, error_str):
                    return error_type
        
        return 'unknown'
    
    async def handle_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle error with appropriate recovery strategy."""
        error_type = self.classify_error(error)
        logger.warning(f"Handling {error_type} error: {error}")
        
        # Get recovery strategy
        strategy = self.recovery_strategies.get(error_type, self._handle_unknown_error)
        
        try:
            recovery_result = await strategy(error, context)
            recovery_result['error_type'] = error_type
            recovery_result['original_error'] = str(error)
            return recovery_result
        except Exception as recovery_error:
            logger.error(f"Recovery strategy failed: {recovery_error}")
            return {
                'success': False,
                'error_type': error_type,
                'recovery_failed': True,
                'fallback_used': True
            }
    
    async def _handle_rate_limit(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle rate limiting with exponential backoff."""
        source = context.get('source', 'unknown')
        cache_key = f"rate_limit_{source}"
        
        # Get current backoff time
        backoff_data = self.cache.get(cache_key) or {'attempts': 0, 'last_backoff': 0}
        backoff_data['attempts'] += 1
        
        # Exponential backoff: 2^attempts seconds, max 300 seconds
        backoff_time = min(2 ** backoff_data['attempts'], 300)
        backoff_data['last_backoff'] = backoff_time
        
        # Cache backoff data
        self.cache.set(cache_key, backoff_data, ttl_hours=1)
        
        # Try alternative sources
        alternative_sources = self._get_alternative_sources(source)
        
        return {
            'success': False,
            'recovery_strategy': 'exponential_backoff',
            'backoff_time': backoff_time,
            'alternative_sources': alternative_sources,
            'retry_after': backoff_time
        }
    
    async def _handle_timeout(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle timeout with reduced timeout and retry."""
        source = context.get('source', 'unknown')
        
        # Try with reduced timeout
        return {
            'success': False,
            'recovery_strategy': 'reduced_timeout',
            'suggested_timeout': 5,  # Reduce from 10 to 5 seconds
            'alternative_sources': self._get_alternative_sources(source)
        }
    
    async def _handle_not_found(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle 404 with alternative search strategies."""
        citation = context.get('citation', '')
        case_name = context.get('case_name', '')
        
        # Try alternative citation variants
        try:
            from src.citation_utils_consolidated import generate_citation_variants
        except ImportError:
            from citation_utils_consolidated import generate_citation_variants
        variants = generate_citation_variants(citation)
        
        # Try broader search terms
        broader_queries = [
            f'"{case_name}"' if case_name else citation,
            f'"{citation}" case opinion',
            f'"{citation}" decision'
        ]
        
        return {
            'success': False,
            'recovery_strategy': 'alternative_variants',
            'citation_variants': variants,
            'broader_queries': broader_queries
        }
    
    async def _handle_server_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle server errors with source switching."""
        source = context.get('source', 'unknown')
        
        # Switch to alternative sources
        alternative_sources = self._get_alternative_sources(source)
        
        return {
            'success': False,
            'recovery_strategy': 'source_switching',
            'alternative_sources': alternative_sources,
            'retry_delay': 30  # Wait 30 seconds before retry
        }
    
    async def _handle_access_denied(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle access denied with alternative sources."""
        source = context.get('source', 'unknown')
        
        # Some sources may have paywalls, try free alternatives
        free_alternatives = ['google_scholar', 'bing', 'duckduckgo', 'courtlistener_web']
        
        return {
            'success': False,
            'recovery_strategy': 'free_alternatives',
            'alternative_sources': free_alternatives,
            'reason': 'paywall_or_access_restriction'
        }
    
    async def _handle_network_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle network errors with connection retry."""
        return {
            'success': False,
            'recovery_strategy': 'connection_retry',
            'retry_delay': 10,
            'max_retries': 3
        }
    
    async def _handle_unknown_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle unknown errors with generic fallback."""
        source = context.get('source', 'unknown')
        
        return {
            'success': False,
            'recovery_strategy': 'generic_fallback',
            'alternative_sources': self._get_alternative_sources(source),
            'error_message': str(error)
        }
    
    def _get_alternative_sources(self, current_source: str) -> List[str]:
        """Get alternative sources for a given source."""
        source_groups = {
            'justia': ['findlaw', 'courtlistener_web', 'leagle'],
            'findlaw': ['justia', 'courtlistener_web', 'leagle'],
            'courtlistener_web': ['justia', 'findlaw', 'leagle'],
            'leagle': ['justia', 'findlaw', 'courtlistener_web'],
            'casetext': ['vlex', 'justia', 'findlaw'],
            'vlex': ['casetext', 'justia', 'findlaw'],
            'google_scholar': ['bing', 'duckduckgo', 'justia'],
            'bing': ['google_scholar', 'duckduckgo', 'justia'],
            'duckduckgo': ['google_scholar', 'bing', 'justia']
        }
        
        return source_groups.get(current_source, ['justia', 'findlaw', 'google_scholar'])

class AdvancedAnalytics:
    """Advanced analytics and performance monitoring system."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.metrics = {
            'search_attempts': 0,
            'successful_searches': 0,
            'failed_searches': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'average_response_time': 0.0,
            'error_counts': {},
            'source_performance': {},
            'citation_patterns': {},
            'recovery_attempts': 0,
            'recovery_successes': 0
        }
        
        self.performance_history = []
        self.error_history = []
    
    def record_search_attempt(self, source: str, success: bool, response_time: float, 
                            citation: str = None, error: Exception = None):
        """Record search attempt metrics."""
        self.metrics['search_attempts'] += 1
        
        if success:
            self.metrics['successful_searches'] += 1
        else:
            self.metrics['failed_searches'] += 1
        
        # Update average response time
        current_avg = self.metrics['average_response_time']
        total_searches = self.metrics['search_attempts']
        self.metrics['average_response_time'] = (
            (current_avg * (total_searches - 1) + response_time) / total_searches
        )
        
        # Record source performance
        if source not in self.metrics['source_performance']:
            self.metrics['source_performance'][source] = {
                'attempts': 0,
                'successes': 0,
                'avg_response_time': 0.0
            }
        
        source_metrics = self.metrics['source_performance'][source]
        source_metrics['attempts'] += 1
        if success:
            source_metrics['successes'] += 1
        
        # Update source average response time
        current_source_avg = source_metrics['avg_response_time']
        source_attempts = source_metrics['attempts']
        source_metrics['avg_response_time'] = (
            (current_source_avg * (source_attempts - 1) + response_time) / source_attempts
        )
        
        # Record citation pattern
        if citation:
            pattern = self._extract_citation_pattern(citation)
            if pattern not in self.metrics['citation_patterns']:
                self.metrics['citation_patterns'][pattern] = 0
            self.metrics['citation_patterns'][pattern] += 1
        
        # Record error if any
        if error:
            error_type = type(error).__name__
            if error_type not in self.metrics['error_counts']:
                self.metrics['error_counts'][error_type] = 0
            self.metrics['error_counts'][error_type] += 1
            
            self.error_history.append({
                'timestamp': datetime.now(),
                'source': source,
                'error_type': error_type,
                'error_message': str(error),
                'citation': citation
            })
        
        # Store performance history
        self.performance_history.append({
            'timestamp': datetime.now(),
            'source': source,
            'success': success,
            'response_time': response_time,
            'citation': citation
        })
        
        # Keep only last 1000 entries
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]
        if len(self.error_history) > 500:
            self.error_history = self.error_history[-500:]
    
    def record_cache_operation(self, hit: bool):
        """Record cache operation metrics."""
        if hit:
            self.metrics['cache_hits'] += 1
        else:
            self.metrics['cache_misses'] += 1
    
    def record_recovery_attempt(self, success: bool):
        """Record error recovery attempt metrics."""
        self.metrics['recovery_attempts'] += 1
        if success:
            self.metrics['recovery_successes'] += 1
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        total_searches = self.metrics['search_attempts']
        success_rate = (self.metrics['successful_searches'] / total_searches * 100) if total_searches > 0 else 0
        cache_hit_rate = (
            self.metrics['cache_hits'] / (self.metrics['cache_hits'] + self.metrics['cache_misses']) * 100
        ) if (self.metrics['cache_hits'] + self.metrics['cache_misses']) > 0 else 0
        recovery_success_rate = (
            self.metrics['recovery_successes'] / self.metrics['recovery_attempts'] * 100
        ) if self.metrics['recovery_attempts'] > 0 else 0
        
        # Top performing sources
        source_performance = []
        for source, metrics in self.metrics['source_performance'].items():
            if metrics['attempts'] > 0:
                success_rate = (metrics['successes'] / metrics['attempts']) * 100
                source_performance.append({
                    'source': source,
                    'attempts': metrics['attempts'],
                    'success_rate': success_rate,
                    'avg_response_time': metrics['avg_response_time']
                })
        
        source_performance.sort(key=lambda x: x['success_rate'], reverse=True)
        
        # Most common citation patterns
        citation_patterns = [
            {'pattern': pattern, 'count': count}
            for pattern, count in self.metrics['citation_patterns'].items()
        ]
        citation_patterns.sort(key=lambda x: x['count'], reverse=True)
        
        # Most common errors
        error_counts = [
            {'error_type': error_type, 'count': count}
            for error_type, count in self.metrics['error_counts'].items()
        ]
        error_counts.sort(key=lambda x: x['count'], reverse=True)
        
        return {
            'overall_metrics': {
                'total_searches': total_searches,
                'success_rate': success_rate,
                'cache_hit_rate': cache_hit_rate,
                'recovery_success_rate': recovery_success_rate,
                'average_response_time': self.metrics['average_response_time']
            },
            'top_sources': source_performance[:5],
            'citation_patterns': citation_patterns[:5],
            'common_errors': error_counts[:5],
            'recent_performance': self.performance_history[-10:] if self.performance_history else [],
            'recent_errors': self.error_history[-5:] if self.error_history else []
        }
    
    def get_source_recommendations(self, citation: str, case_name: str = None) -> List[Dict[str, Any]]:
        """Get source recommendations based on historical performance."""
        pattern = self._extract_citation_pattern(citation)
        
        recommendations = []
        for source, metrics in self.metrics['source_performance'].items():
            if metrics['attempts'] >= 5:  # Only consider sources with sufficient data
                success_rate = (metrics['successes'] / metrics['attempts']) * 100
                recommendations.append({
                    'source': source,
                    'confidence': success_rate / 100,
                    'avg_response_time': metrics['avg_response_time'],
                    'attempts': metrics['attempts']
                })
        
        # Sort by confidence (success rate)
        recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        
        return recommendations[:5]
    
    def _extract_citation_pattern(self, citation: str) -> str:
        """Extract citation pattern for analytics."""
        patterns = {
            'washington_state': [r'Wn\.?\s*\d+', r'Wash\.?\s*\d+'],
            'federal_supreme': [r'U\.S\.?\s+\d+'],
            'federal_circuit': [r'F\.?\s*\d+', r'Fed\.?\s*\d+'],
            'pacific_reporter': [r'P\.?\s*\d+', r'Pac\.?\s*\d+']
        }
        
        for pattern_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, citation, re.IGNORECASE):
                    return pattern_type
        
        return 'unknown'
    
    def export_analytics(self, filename: str = None) -> str:
        """Export analytics data to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analytics_export_{timestamp}.json"
        
        data = {
            'export_timestamp': datetime.now().isoformat(),
            'metrics': self.metrics,
            'performance_history': self.performance_history,
            'error_history': self.error_history
        }
        
        import json
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        return filename

if __name__ == "__main__":
    test_comprehensive_web_search() 