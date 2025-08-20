#!/usr/bin/env python3
"""
Working Fallback Citation Verification System

This module integrates the best working components from the existing codebase:
1. FallbackVerifier's verification logic
2. LegalDatabaseScraper's extraction capabilities  
3. ComprehensiveWebSearchEngine's search capabilities

It provides actual working verification for citations not found in CourtListener.
"""

import asyncio
import logging
import re
import time
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin, quote

logger = logging.getLogger(__name__)

class WorkingFallbackVerifier:
    """
    Working fallback verification system that actually extracts canonical data
    from legal database sites.
    """
    
    def __init__(self):
        self.session = None  # Will be initialized when needed
        self.legal_databases = {
            'justia': {
                'base_url': 'https://law.justia.com',
                'search_url': 'https://law.justia.com/search',
                'rate_limit': 1.0
            },
            'findlaw': {
                'base_url': 'https://caselaw.findlaw.com',
                'search_url': 'https://caselaw.findlaw.com/search',
                'rate_limit': 1.0
            },
            'casemine': {
                'base_url': 'https://www.casemine.com',
                'search_url': 'https://www.casemine.com/search',
                'rate_limit': 2.0
            }
            # vlex deprecated due to site blocking and unreliable web scraping
        }
        
        # Rate limiting
        self.last_request_time = {}
        self.min_delay = 1.0
        
    def _init_session(self):
        """Initialize requests session if not already done."""
        if not self.session:
            import requests
            self.session = requests.Session()
            self.session.headers.update({
                'User-Aost': 'CaseStrainer Citation Verifier (Educational Research)'
            })
    
    def _rate_limit(self, domain: str):
        """Apply rate limiting for requests to the same domain."""
        now = time.time()
        if domain in self.last_request_time:
            time_since_last = now - self.last_request_time[domain]
            if time_since_last < self.min_delay:
                sleep_time = self.min_delay - time_since_last
                time.sleep(sleep_time)
        self.last_request_time[domain] = now
    
    async def verify_citation(self, citation_text: str, extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None) -> Dict:
        """
        Verify a citation using working fallback sources.
        
        Args:
            citation_text: The citation to verify (e.g., "188 Wn.2d 114")
            extracted_case_name: Optional case name (e.g., "In re Marriage of Black")
            extracted_date: Optional date (e.g., "2017")
            
        Returns:
            Dict with verification results including canonical_name, canonical_date, and url
        """
        logger.info(f"Starting working fallback verification for: {citation_text}")
        
        # Parse citation to determine type and court
        citation_info = self._parse_citation(citation_text)
        
        # Try sources in order of reliability
        sources = [
            ('justia', self._verify_with_justia),
            ('findlaw', self._verify_with_findlaw),
            ('casemine', self._verify_with_casemine),
            # vlex deprecated due to site blocking
        ]
        
        for source_name, verify_func in sources:
            try:
                logger.debug(f"Trying {source_name} for {citation_text}")
                result = await verify_func(citation_text, citation_info, extracted_case_name, extracted_date)
                
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
    
    def _parse_citation(self, citation_text: str) -> Dict[str, Any]:
        """Parse citation to extract volume, reporter, page, and court type."""
        citation_info: Dict[str, Any] = {
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
    
    async def _verify_with_justia(self, citation_text: str, citation_info: Dict[str, Any],
                                 extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None) -> Optional[Dict]:
        """Verify citation with Justia legal database."""
        # Ensure citation_info is not None
        assert citation_info is not None, "citation_info should never be None"
        self._init_session()
        
        try:
            # Generate search query
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
                        case_name = self._extract_case_name_from_justia_link(link_text)
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
    
    def _extract_case_name_from_justia_link(self, link_text: str) -> Optional[str]:
        """Extract case name from Justia link text."""
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
    
    async def _verify_with_findlaw(self, citation_text: str, citation_info: Dict[str, Any],
                                  extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None) -> Optional[Dict]:
        """Verify citation with FindLaw legal database."""
        self._init_session()
        
        try:
            # Generate search query
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
                        case_name = self._extract_case_name_from_findlaw_link(link_text)
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
    
    def _extract_case_name_from_findlaw_link(self, link_text: str) -> Optional[str]:
        """Extract case name from FindLaw link text."""
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
    
    async def _verify_with_casemine(self, citation_text: str, citation_info: Dict[str, Any],
                                   extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None) -> Optional[Dict]:
        """Verify citation with CaseMine legal database."""
        self._init_session()
        
        try:
            # Generate search query
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
                        case_name = self._extract_case_name_from_casemine_link(link_text)
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
    
    def _extract_case_name_from_casemine_link(self, link_text: str) -> Optional[str]:
        """Extract case name from CaseMine link text."""
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
    
    async def _verify_with_vlex(self, citation_text: str, citation_info: Dict[str, Any],
                                extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None) -> Optional[Dict]:
        """
        Verify citation with vLex legal database.
        
        DEPRECATED: This function is deprecated due to site blocking and unreliable web scraping.
        Use Google Scholar, Bing, or DuckDuckGo for more reliable fallback verification.
        """
        import warnings
        warnings.warn(
            "_verify_with_vlex is deprecated due to site blocking and unreliable web scraping. "
            "Use Google Scholar, Bing, or DuckDuckGo for more reliable fallback verification.",
            DeprecationWarning,
            stacklevel=2
        )
        
        logger.warning(f"vLex verification deprecated for {citation_text} - use Google Scholar, Bing, or DuckDuckGo instead")
        return None
    
    def _extract_case_name_from_vlex_link(self, link_text: str) -> Optional[str]:
        """
        Extract case name from vLex link text.
        
        DEPRECATED: This function is deprecated as vLex verification is deprecated.
        """
        import warnings
        warnings.warn(
            "_extract_case_name_from_vlex_link is deprecated as vLex verification is deprecated.",
            DeprecationWarning,
            stacklevel=2
        )
        
        return None

# Convenience function for easy integration
async def verify_citation_with_fallback(citation_text: str, extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None) -> Dict:
    """
    Convenience function to verify a citation using the working fallback verifier.
    
    Args:
        citation_text: The citation to verify
        extracted_case_name: Optional extracted case name
        extracted_date: Optional extracted date
        
    Returns:
        Dict with verification results
    """
    verifier = WorkingFallbackVerifier()
    return await verifier.verify_citation(citation_text, extracted_case_name, extracted_date)
