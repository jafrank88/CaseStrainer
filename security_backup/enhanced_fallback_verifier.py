#!/usr/bin/env python3
"""
Enhanced Fallback Citation Verification System

This module integrates the best components from:
1. FallbackVerifier's verification logic
2. EnhancedLegalSearchEngine's query strategies
3. ComprehensiveWebSearchEngine's search capabilities

It provides robust fallback verification for citations not found in CourtListener,
ensuring canonical name, year, and URL are extracted from approved sites.
"""

import asyncio
import logging
import re
import time
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin, quote, urlparse
import requests
import json

logger = logging.getLogger(__name__)

class EnhancedFallbackVerifier:
    """
    Enhanced fallback verification system that integrates multiple approaches
    to provide reliable citation verification with canonical data extraction.
    """
    
    def __init__(self, enable_experimental_engines=True):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CaseStrainer Citation Verifier (Educational Research)'
        })
        
        # Rate limiting
        self.last_request_time = {}
        self.min_delay = 1.0
        
        # Legal-specific domains with priority scores
        self.legal_domains = {
            'justia.com': 95,
            'caselaw.findlaw.com': 90, 
            'findlaw.com': 85,
            'courtlistener.com': 100,
            'leagle.com': 85,
            'casetext.com': 80,
            'law.cornell.edu': 80,
            'google.com/scholar': 75,
            'casemine.com': 80,
            'vlex.com': 85,
            'openjurist.org': 70
        }
        
        # Washington state specific patterns
        self.washington_patterns = [
            r'(\d+)\s+Wn\.?\s*2d\s+(\d+)',
            r'(\d+)\s+Wn\.?\s*3d\s+(\d+)', 
            r'(\d+)\s+Wn\.?\s*App\.?\s*2d\s+(\d+)',
            r'(\d+)\s+Wash\.?\s*2d\s+(\d+)',
            r'(\d+)\s+Washington\s+2d\s+(\d+)'
        ]
        
        # Pacific Reporter patterns
        self.pacific_patterns = [
            r'(\d+)\s+P\.\s*3d\s+(\d+)',
            r'(\d+)\s+P\.\s*2d\s+(\d+)',
        ]
        
        # Enable experimental engines for broader coverage
        self.enable_experimental_engines = enable_experimental_engines
        
    def _rate_limit(self, domain: str):
        """Apply rate limiting for requests to the same domain."""
        now = time.time()
        if domain in self.last_request_time:
            time_since_last = now - self.last_request_time[domain]
            if time_since_last < self.min_delay:
                sleep_time = self.min_delay - time_since_last
                time.sleep(sleep_time)
        self.last_request_time[domain] = now
    
    def normalize_citation(self, citation: str) -> str:
        """Normalize citation format (e.g., WN. -> Wash.)."""
        if not citation:
            return citation
        
        # Washington reporter normalization
        normalized = re.sub(r'\bWN\.?\b', 'Wash.', citation, flags=re.IGNORECASE)
        normalized = re.sub(r'\bWn\.?\b', 'Wash.', normalized, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def is_washington_citation(self, citation: str) -> bool:
        """Check if citation is from Washington state."""
        washington_indicators = [
            r'\bWn\.?\s*\d+d\b',
            r'\bWash\.?\s*\d+d\b', 
            r'\bWashington\s*\d+d\b'
        ]
        
        for pattern in washington_indicators:
            if re.search(pattern, citation, re.IGNORECASE):
                return True
        return False
    
    def generate_washington_variants(self, citation: str) -> List[str]:
        """Generate Washington citation variants."""
        variants = []
        
        # Replace Wn. with Wash.
        if 'Wn.' in citation:
            variants.append(citation.replace('Wn.', 'Wash.'))
        
        # Replace Wash. with Wn.
        if 'Wash.' in citation:
            variants.append(citation.replace('Wash.', 'Wn.'))
        
        # Replace Washington with Wn.
        if 'Washington' in citation:
            variants.append(citation.replace('Washington', 'Wn.'))
        
        return variants
    
    def generate_enhanced_legal_queries(self, citation: str, case_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Generate legal-specific search queries with context."""
        queries = []
        
        # Clean and normalize the citation first
        normalized_citation = self.normalize_citation(citation)
        
        # Generate all major variants (including the original citation)
        variants = set([citation.strip(), normalized_citation])
        if self.is_washington_citation(citation):
            variants.update(self.generate_washington_variants(citation))
        
        # For each variant, generate all query strategies
        for variant in variants:
            # Strategy 1: Exact citation with legal context keywords
            legal_contexts = [
                f'"{variant}" case law',
                f'"{variant}" court decision', 
                f'"{variant}" legal opinion',
                f'"{variant}" judgment',
                f'"{variant}" Washington Supreme Court',
                f'"{variant}" Washington Court of Appeals'
            ]
            for context_query in legal_contexts:
                queries.append({
                    'query': context_query,
                    'priority': 1,
                    'type': 'legal_context',
                    'citation': variant
                })
            
            # Strategy 2: Site-specific searches on legal databases
            legal_sites = [
                'site:justia.com',
                'site:caselaw.findlaw.com', 
                'site:courtlistener.com',
                'site:leagle.com',
                'site:casetext.com',
                'site:law.cornell.edu',
                'site:vlex.com'
            ]
            for site in legal_sites:
                queries.append({
                    'query': f'{site} "{variant}"',
                    'priority': 2,
                    'type': 'site_specific',
                    'citation': variant,
                    'site': site
                })
            
            # Strategy 3: Washington-specific context (if applicable)
            if self.is_washington_citation(variant):
                queries.append({
                    'query': f'"{variant}" Washington state court',
                    'priority': 3,
                    'type': 'washington_variant',
                    'citation': variant
                })
            
            # Strategy 4: Broader legal database searches
            broad_queries = [
                f'"{variant}" filetype:pdf',
                f'"{variant}" "Wn.2d" OR "Wash.2d"',
                f'legal citation "{variant}"'
            ]
            for broad_query in broad_queries:
                queries.append({
                    'query': broad_query,
                    'priority': 4, 
                    'type': 'broad_legal',
                    'citation': variant
                })
        
        # Strategy 5: Case name + citation combinations (if case name available)
        if case_name:
            for variant in list(variants)[:3]:  # Limit to top 3 variants
                queries.append({
                    'query': f'"{case_name}" "{variant}"',
                    'priority': 5,
                    'type': 'case_and_citation',
                    'citation': variant,
                    'case_name': case_name
                })
        
        # Sort by priority (citation-based first)
        queries.sort(key=lambda x: x.get('priority', 999))
        
        return queries
    
    def _parse_citation(self, citation_text: str) -> Dict:
        """Parse citation to extract volume, reporter, page, and court type."""
        citation_info = {
            'volume': None,
            'reporter': None,
            'page': None,
            'year': None,
            'court_type': 'unknown'
        }
        
        # Washington-specific patterns
        washington_patterns = [
            r'(\d+)\s+Wn\.\s*2d\s+(\d+)',  # 188 Wn.2d 114
            r'(\d+)\s+Wn\.\s*App\.\s+(\d+)',  # 178 Wn. App. 929
            r'(\d+)\s+Wash\.\s*2d\s+(\d+)',  # 188 Wash. 2d 114
            r'(\d+)\s+Wash\.\s*App\.\s+(\d+)',  # 178 Wash. App. 929
        ]
        
        for pattern in washington_patterns:
            match = re.search(pattern, citation_text, re.IGNORECASE)
            if match:
                citation_info['volume'] = match.group(1)
                citation_info['page'] = match.group(2)
                citation_info['court_type'] = 'washington'
                citation_info['reporter'] = 'Wn.' if 'Wn.' in citation_text else 'Wash.'
                break
        
        # Pacific Reporter patterns
        pacific_patterns = [
            r'(\d+)\s+P\.\s*3d\s+(\d+)',  # 392 P.3d 1041
            r'(\d+)\s+P\.\s*2d\s+(\d+)',  # 317 P.2d 1068
        ]
        
        for pattern in pacific_patterns:
            match = re.search(pattern, citation_text, re.IGNORECASE)
            if match:
                citation_info['volume'] = match.group(1)
                citation_info['page'] = match.group(2)
                citation_info['court_type'] = 'pacific'
                citation_info['reporter'] = 'P.3d' if '3d' in citation_text else 'P.2d'
                break
        
        # Extract year if present in citation
        year_match = re.search(r'\((\d{4})\)', citation_text)
        if year_match:
            citation_info['year'] = year_match.group(1)
        
        return citation_info
    
    async def verify_citation(self, citation_text: str, extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None) -> Dict:
        """
        Verify a citation using enhanced fallback sources.
        
        Args:
            citation_text: The citation to verify (e.g., "188 Wn.2d 114")
            extracted_case_name: Optional case name (e.g., "In re Marriage of Black")
            extracted_date: Optional date (e.g., "2017")
            
        Returns:
            Dict with verification results including canonical_name, canonical_date, and url
        """
        logger.info(f"Starting enhanced fallback verification for: {citation_text}")
        
        # Parse citation to determine type and court
        citation_info = self._parse_citation(citation_text)
        
        # Generate enhanced search queries
        queries = self.generate_enhanced_legal_queries(citation_text, extracted_case_name)
        
        # Try sources in order of reliability
        sources = [
            ('justia', self._verify_with_justia),
            ('findlaw', self._verify_with_findlaw),
            ('leagle', self._verify_with_leagle),
            ('casemine', self._verify_with_casemine),
            ('vlex', self._verify_with_vlex),
            ('google_scholar', self._verify_with_google_scholar),
            ('bing', self._verify_with_bing),
            ('duckduckgo', self._verify_with_duckduckgo)
        ]
        
        # Try each source with the generated queries
        for source_name, verify_func in sources:
            try:
                logger.debug(f"Trying {source_name} for {citation_text}")
                
                # Try the top priority queries first
                for query_info in queries[:5]:  # Top 5 queries
                    query = query_info['query']
                    query_type = query_info.get('type', '')
                    
                    # Prioritize citation-based searches
                    if query_type.startswith('legal_context') or query_type == 'site_specific':
                        result = await verify_func(citation_text, citation_info, extracted_case_name, extracted_date, query)
                        
                        if result and result.get('verified', False):
                            logger.info(f"Successfully verified {citation_text} via {source_name}")
                            return result
                
            except Exception as e:
                logger.warning(f"Error verifying {citation_text} with {source_name}: {str(e)}")
                continue
        
        # If no sources worked, return unverified
        return {
            'verified': False,
            'source': None,
            'canonical_name': None,
            'canonical_date': None,
            'url': None,
            'confidence': 0.0
        }
    
    def verify_citation_sync(self, citation_text: str, extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None) -> Dict:
        """
        Synchronous version of verify_citation for use in non-async contexts.
        
        Args:
            citation_text: The citation to verify (e.g., "188 Wn.2d 114")
            extracted_case_name: Optional case name (e.g., "In re Marriage of Black")
            extracted_date: Optional date (e.g., "2017")
            
        Returns:
            Dict with verification results including canonical_name, canonical_date, and url
        """
        try:
            # Create a new event loop for this thread
            import asyncio
            import threading
            
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an event loop, can't run sync version
                    logger.warning(f"Sync verification called from within event loop for {citation_text}")
                    return {
                        'verified': False,
                        'source': 'sync_limitation',
                        'canonical_name': None,
                        'canonical_date': None,
                        'url': None,
                        'confidence': 0.0,
                        'error': 'Cannot run sync verification from within event loop'
                    }
            except RuntimeError:
                # No event loop, we can create one
                pass
            
            # Create a new event loop and run the async verification
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Run the async verification
                result = loop.run_until_complete(
                    self.verify_citation(citation_text, extracted_case_name, extracted_date)
                )
                return result
            finally:
                loop.close()
                asyncio.set_event_loop(None)
            
        except Exception as e:
            logger.error(f"Error in sync verification: {e}")
            return {
                'verified': False,
                'source': None,
                'canonical_name': None,
                'canonical_date': None,
                'url': None,
                'confidence': 0.0,
                'error': str(e)
            }
    
    async def _verify_with_justia(self, citation_text: str, citation_info: Dict, 
                                 extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None,
                                 search_query: Optional[str] = None) -> Optional[Dict]:
        """Verify citation with Justia legal database."""
        try:
            # Use provided search query or generate one
            if not search_query:
                search_query = citation_text
                if extracted_case_name:
                    search_query += f" {extracted_case_name}"
            
            # Justia search URL
            search_url = f"https://law.justia.com/search?query={quote(search_query)}"
            
            self._rate_limit('justia.com')
            response = self.session.get(search_url, timeout=15)
            
            if response.status_code == 200:
                content = response.text
                
                # Look for case links that contain our citation
                case_link_pattern = r'<a[^>]*href="([^"]*cases[^"]+)"[^>]*>([^<]*)</a>'
                matches = re.findall(case_link_pattern, content, re.IGNORECASE)
                
                for link_url, link_text in matches:
                    # Check if this link contains our citation
                    if citation_text.replace(' ', '').lower() in link_text.replace(' ', '').lower():
                        # Found a matching case link
                        full_url = link_url if link_url.startswith('http') else f"https://law.justia.com{link_url}"
                        
                        # Extract case name from link text
                        case_name = self._extract_case_name_from_link(link_text)
                        if not case_name and extracted_case_name:
                            case_name = extracted_case_name
                        
                        # Extract year
                        year = extracted_date or (citation_info.get('year') if citation_info else None)
                        if not year:
                            year_match = re.search(r'(\d{4})', link_text)
                            if year_match:
                                year = year_match.group(1)
                        
                        if case_name:
                            return {
                                'verified': True,
                                'source': 'justia',
                                'canonical_name': case_name,
                                'canonical_date': year,
                                'url': full_url,
                                'confidence': 0.85
                            }
            
            return None
            
        except Exception as e:
            logger.warning(f"Justia verification failed for {citation_text}: {e}")
            return None
    
    async def _verify_with_findlaw(self, citation_text: str, citation_info: Dict,
                                  extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None,
                                  search_query: Optional[str] = None) -> Optional[Dict]:
        """Verify citation with FindLaw legal database."""
        try:
            # Use provided search query or generate one
            if not search_query:
                search_query = citation_text
                if extracted_case_name:
                    search_query += f" {extracted_case_name}"
            
            # FindLaw search URL
            search_url = f"https://caselaw.findlaw.com/search?query={quote(search_query)}"
            
            self._rate_limit('findlaw.com')
            response = self.session.get(search_url, timeout=15)
            
            if response.status_code == 200:
                content = response.text
                
                # Look for case links that contain our citation
                case_link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
                matches = re.findall(case_link_pattern, content, re.IGNORECASE)
                
                for link_url, link_text in matches:
                    # Check if this link contains our citation
                    if citation_text.replace(' ', '').lower() in link_text.replace(' ', '').lower():
                        # Found a matching case link
                        full_url = link_url if link_url.startswith('http') else f"https://caselaw.findlaw.com{link_url}"
                        
                        # Extract case name from link text
                        case_name = self._extract_case_name_from_link(link_text)
                        if not case_name and extracted_case_name:
                            case_name = extracted_case_name
                        
                        # Extract year
                        year = extracted_date or (citation_info.get('year') if citation_info else None)
                        if not year:
                            year_match = re.search(r'(\d{4})', link_text)
                            if year_match:
                                year = year_match.group(1)
                        
                        if case_name:
                            return {
                                'verified': True,
                                'source': 'findlaw',
                                'canonical_name': case_name,
                                'canonical_date': year,
                                'url': full_url,
                                'confidence': 0.8
                            }
            
            return None
            
        except Exception as e:
            logger.warning(f"FindLaw verification failed for {citation_text}: {e}")
            return None
    
    async def _verify_with_leagle(self, citation_text: str, citation_info: Dict,
                                 extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None,
                                 search_query: Optional[str] = None) -> Optional[Dict]:
        """Verify citation with Leagle legal database."""
        try:
            # Use provided search query or generate one
            if not search_query:
                search_query = citation_text
                if extracted_case_name:
                    search_query += f" {extracted_case_name}"
            
            # Leagle search URL
            search_url = f"https://www.leagle.com/search?query={quote(search_query)}"
            
            self._rate_limit('leagle.com')
            response = self.session.get(search_url, timeout=15)
            
            if response.status_code == 200:
                content = response.text
                
                # Look for case links that contain our citation
                case_link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
                matches = re.findall(case_link_pattern, content, re.IGNORECASE)
                
                for link_url, link_text in matches:
                    # Check if this link contains our citation
                    if citation_text.replace(' ', '').lower() in link_text.replace(' ', '').lower():
                        # Found a matching case link
                        full_url = link_url if link_url.startswith('http') else f"https://www.leagle.com{link_url}"
                        
                        # Extract case name from link text
                        case_name = self._extract_case_name_from_link(link_text)
                        if not case_name and extracted_case_name:
                            case_name = extracted_case_name
                        
                        # Extract year
                        year = extracted_date or (citation_info.get('year') if citation_info else None)
                        if not year:
                            year_match = re.search(r'(\d{4})', link_text)
                            if year_match:
                                year = year_match.group(1)
                        
                        if case_name:
                            return {
                                'verified': True,
                                'source': 'leagle',
                                'canonical_name': case_name,
                                'canonical_date': year,
                                'url': full_url,
                                'confidence': 0.8
                            }
            
            return None
            
        except Exception as e:
            logger.warning(f"Leagle verification failed for {citation_text}: {e}")
            return None
    
    async def _verify_with_casemine(self, citation_text: str, citation_info: Dict,
                                   extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None,
                                   search_query: Optional[str] = None) -> Optional[Dict]:
        """Verify citation with CaseMine legal database."""
        try:
            # Use provided search query or generate one
            if not search_query:
                search_query = citation_text
                if extracted_case_name:
                    search_query += f" {extracted_case_name}"
            
            # CaseMine search URL
            search_url = f"https://www.casemine.com/search?q={quote(search_query)}"
            
            self._rate_limit('casemine.com')
            response = self.session.get(search_url, timeout=15)
            
            if response.status_code == 200:
                content = response.text
                
                # Look for case links that contain our citation
                case_link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
                matches = re.findall(case_link_pattern, content, re.IGNORECASE)
                
                for link_url, link_text in matches:
                    # Check if this link contains our citation
                    if citation_text.replace(' ', '').lower() in link_text.replace(' ', '').lower():
                        # Found a matching case link
                        full_url = link_url if link_url.startswith('http') else f"https://www.casemine.com{link_url}"
                        
                        # Extract case name from link text
                        case_name = self._extract_case_name_from_link(link_text)
                        if not case_name and extracted_case_name:
                            case_name = extracted_case_name
                        
                        # Extract year
                        year = extracted_date or (citation_info.get('year') if citation_info else None)
                        if not year:
                            year_match = re.search(r'(\d{4})', link_text)
                            if year_match:
                                year = year_match.group(1)
                        
                        if case_name:
                            return {
                                'verified': True,
                                'source': 'casemine',
                                'canonical_name': case_name,
                                'canonical_date': year,
                                'url': full_url,
                                'confidence': 0.8
                            }
            
            return None
            
        except Exception as e:
            logger.warning(f"CaseMine verification failed for {citation_text}: {e}")
            return None
    
    async def _verify_with_google_scholar(self, citation_text: str, citation_info: Dict,
                                        extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None,
                                        search_query: Optional[str] = None) -> Optional[Dict]:
        """Verify citation with Google Scholar."""
        try:
            # Use provided search query or generate one
            if not search_query:
                search_query = citation_text
                if extracted_case_name:
                    search_query += f" {extracted_case_name}"
            
            # Google Scholar search URL
            search_url = f"https://scholar.google.com/scholar?q={quote(search_query)}"
            
            self._rate_limit('scholar.google.com')
            response = self.session.get(search_url, timeout=15)
            
            if response.status_code == 200:
                content = response.text
                
                # Look for case links that contain our citation
                case_link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
                matches = re.findall(case_link_pattern, content, re.IGNORECASE)
                
                for link_url, link_text in matches:
                    # Check if this link contains our citation
                    if citation_text.replace(' ', '').lower() in link_text.replace(' ', '').lower():
                        # Found a matching case link
                        full_url = link_url if link_url.startswith('http') else f"https://scholar.google.com{link_url}"
                        
                        # Extract case name from link text
                        case_name = self._extract_case_name_from_link(link_text)
                        if not case_name and extracted_case_name:
                            case_name = extracted_case_name
                        
                        # Extract year
                        year = extracted_date or (citation_info.get('year') if citation_info else None)
                        if not year:
                            year_match = re.search(r'(\d{4})', link_text)
                            if year_match:
                                year = year_match.group(1)
                        
                        if case_name:
                            return {
                                'verified': True,
                                'source': 'google_scholar',
                                'canonical_name': case_name,
                                'canonical_date': year,
                                'url': full_url,
                                'confidence': 0.75
                            }
            
            return None
            
        except Exception as e:
            logger.warning(f"Google Scholar verification failed for {citation_text}: {e}")
            return None
    
    async def _verify_with_bing(self, citation_text: str, citation_info: Dict,
                               extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None,
                               search_query: Optional[str] = None) -> Optional[Dict]:
        """Verify citation with Bing search."""
        try:
            # Use provided search query or generate one
            if not search_query:
                search_query = citation_text
                if extracted_case_name:
                    search_query += f" {extracted_case_name}"
            
            # Bing search URL
            search_url = f"https://www.bing.com/search?q={quote(search_query)}"
            
            self._rate_limit('bing.com')
            response = self.session.get(search_url, timeout=15)
            
            if response.status_code == 200:
                content = response.text
                
                # Look for case links that contain our citation
                case_link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
                matches = re.findall(case_link_pattern, content, re.IGNORECASE)
                
                for link_url, link_text in matches:
                    # Check if this link contains our citation
                    if citation_text.replace(' ', '').lower() in link_text.replace(' ', '').lower():
                        # Found a matching case link
                        full_url = link_url if link_url.startswith('http') else f"https://www.bing.com{link_url}"
                        
                        # Extract case name from link text
                        case_name = self._extract_case_name_from_link(link_text)
                        if not case_name and extracted_case_name:
                            case_name = extracted_case_name
                        
                        # Extract year
                        year = extracted_date or (citation_info.get('year') if citation_info else None)
                        if not year:
                            year_match = re.search(r'(\d{4})', link_text)
                            if year_match:
                                year = year_match.group(1)
                        
                        if case_name:
                            return {
                                'verified': True,
                                'source': 'bing',
                                'canonical_name': case_name,
                                'canonical_date': year,
                                'url': full_url,
                                'confidence': 0.7
                            }
            
            return None
            
        except Exception as e:
            logger.warning(f"Bing verification failed for {citation_text}: {e}")
            return None
    
    async def _verify_with_duckduckgo(self, citation_text: str, citation_info: Dict,
                                     extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None,
                                     search_query: Optional[str] = None) -> Optional[Dict]:
        """Verify citation with DuckDuckGo search."""
        try:
            # Use provided search query or generate one
            if not search_query:
                search_query = citation_text
                if extracted_case_name:
                    search_query += f" {extracted_case_name}"
            
            # DuckDuckGo search URL
            search_url = f"https://duckduckgo.com/html?q={quote(search_query)}"
            
            self._rate_limit('duckduckgo.com')
            response = self.session.get(search_url, timeout=15)
            
            if response.status_code == 200:
                content = response.text
                
                # Look for case links that contain our citation
                case_link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
                matches = re.findall(case_link_pattern, content, re.IGNORECASE)
                
                for link_url, link_text in matches:
                    # Check if this link contains our citation
                    if citation_text.replace(' ', '').lower() in link_text.replace(' ', '').lower():
                        # Found a matching case link
                        full_url = link_url if link_url.startswith('http') else f"https://duckduckgo.com{link_url}"
                        
                        # Extract case name from link text
                        case_name = self._extract_case_name_from_link(link_text)
                        if not case_name and extracted_case_name:
                            case_name = extracted_case_name
                        
                        # Extract year
                        year = extracted_date or (citation_info.get('year') if citation_info else None)
                        if not year:
                            year_match = re.search(r'(\d{4})', link_text)
                            if year_match:
                                year = year_match.group(1)
                        
                        if case_name:
                            return {
                                'verified': True,
                                'source': 'duckduckgo',
                                'canonical_date': year,
                                'url': full_url,
                                'confidence': 0.7
                            }
            
            return None
            
        except Exception as e:
            logger.warning(f"DuckDuckGo verification failed for {citation_text}: {e}")
            return None

    async def _verify_with_vlex(self, citation_text: str, citation_info: Dict,
                               extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None,
                               search_query: Optional[str] = None) -> Optional[Dict]:
        """Verify citation with vLex legal database."""
        try:
            # Use provided search query or generate one
            if not search_query:
                search_query = citation_text
                if extracted_case_name:
                    search_query += f" {extracted_case_name}"
            
            # vLex search URL - try multiple search endpoints
            search_urls = [
                f"https://vlex.com/search?q={quote(search_query)}",
                f"https://vlex.com/search?query={quote(search_query)}",
                f"https://vlex.com/search?search={quote(search_query)}"
            ]
            
            for search_url in search_urls:
                try:
                    self._rate_limit('vlex.com')
                    response = self.session.get(search_url, timeout=15)
                    
                    if response.status_code == 200:
                        content = response.text
                        
                        # Look for case links that contain our citation
                        case_link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
                        matches = re.findall(case_link_pattern, content, re.IGNORECASE)
                        
                        for link_url, link_text in matches:
                            # Check if this link contains our citation
                            if citation_text.replace(' ', '').lower() in link_text.replace(' ', '').lower():
                                # Found a matching case link
                                full_url = link_url if link_url.startswith('http') else f"https://vlex.com{link_url}"
                                
                                # Extract case name from link text
                                case_name = self._extract_case_name_from_link(link_text)
                                if not case_name and extracted_case_name:
                                    case_name = extracted_case_name
                                
                                # Extract year
                                year = extracted_date or (citation_info.get('year') if citation_info else None)
                                if not year:
                                    year_match = re.search(r'(\d{4})', link_text)
                                    if year_match:
                                        year = year_match.group(1)
                                
                                if case_name:
                                    return {
                                        'verified': True,
                                        'source': 'vlex',
                                        'canonical_name': case_name,
                                        'canonical_date': year,
                                        'url': full_url,
                                        'confidence': 0.8
                                    }
                        
                        # If we get here, no matches found in this URL
                        continue
                        
                except Exception as e:
                    logger.debug(f"vLex search URL {search_url} failed: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.warning(f"vLex verification failed for {citation_text}: {e}")
            return None
    
    def _extract_case_name_from_link(self, link_text: str) -> Optional[str]:
        """Extract case name from link text."""
        # Clean up the link text
        clean_text = re.sub(r'<[^>]+>', '', link_text)  # Remove HTML tags
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        # Look for case name patterns
        case_patterns = [
            r'([A-Z][a-zA-Z\s&.]+\s+v\.?\s+[A-Z][a-zA-Z\s&.]+)',  # X v. Y
            r'(In re [A-Z][a-zA-Z\s&.]+)',  # In re X
            r'(Ex parte [A-Z][a-zA-Z\s&.]+)',  # Ex parte X
        ]
        
        for pattern in case_patterns:
            match = re.search(pattern, clean_text)
            if match:
                case_name = match.group(1).strip()
                if len(case_name) > 5:  # Ensure it's a reasonable length
                    return case_name
        
        return None

# Convenience function for easy integration
async def verify_citation_with_enhanced_fallback(citation_text: str, extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None) -> Dict:
    """
    Convenience function to verify a citation using the enhanced fallback verifier.
    
    Args:
        citation_text: The citation to verify
        extracted_case_name: Optional extracted case name
        extracted_date: Optional extracted date
        
    Returns:
        Dict with verification results
    """
    verifier = EnhancedFallbackVerifier()
    return await verifier.verify_citation(citation_text, extracted_case_name, extracted_date)

# Convenience function specifically for vlex verification
async def verify_citation_with_vlex(citation_text: str, extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None) -> Optional[Dict]:
    """
    Convenience function to verify a citation specifically using vLex.
    
    Args:
        citation_text: The citation to verify
        extracted_case_name: Optional extracted case name
        extracted_date: Optional extracted date
        
    Returns:
        Dict with verification results
    """
    verifier = EnhancedFallbackVerifier()
    return await verifier._verify_with_vlex(citation_text, {}, extracted_case_name, extracted_date)
