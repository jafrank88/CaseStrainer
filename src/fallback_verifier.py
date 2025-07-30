#!/usr/bin/env python3
"""
Fallback Citation Verification System

This module provides fallback verification for citations that are not found in CourtListener.
It checks multiple legal databases and sources including Cornell Law, Justia, and others.
"""

import requests
import re
import time
import logging
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, quote
import json

logger = logging.getLogger(__name__)

class FallbackVerifier:
    """
    Verifies citations using multiple fallback sources when CourtListener fails.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CaseStrainer Citation Verifier (Educational Research)'
        })
        
        # Rate limiting
        self.last_request_time = {}
        self.min_delay = 1.0  # Minimum delay between requests to same domain
        
    def verify_citation(self, citation_text: str, extracted_case_name: str = None, extracted_date: str = None) -> Dict:
        """
        Verify a citation using fallback sources.
        
        Args:
            citation_text: The citation to verify (e.g., "385 U.S. 493")
            extracted_case_name: Optional case name (e.g., "Davis v. Alaska")
            extracted_date: Optional date (e.g., "1967")
            
        Returns:
            Dict with verification results
        """
        logger.info(f"Starting fallback verification for: {citation_text}")
        
        # Parse citation to determine type and court
        citation_info = self._parse_citation(citation_text)
        
        # Try different verification sources based on citation type
        verification_result = {
            'verified': False,
            'source': None,
            'canonical_name': None,
            'canonical_date': None,
            'url': None,
            'confidence': 0.0,
            'verification_details': {}
        }
        
        # Try sources in order of reliability
        sources = [
            ('cornell_law', self._verify_with_cornell_law),
            ('justia', self._verify_with_justia),
            ('google_scholar', self._verify_with_google_scholar),
            ('caselaw_access', self._verify_with_caselaw_access)
        ]
        
        for source_name, verify_func in sources:
            try:
                logger.debug(f"Trying {source_name} for {citation_text}")
                result = verify_func(citation_text, citation_info, extracted_case_name, extracted_date)
                
                if result and result.get('verified', False):
                    verification_result.update(result)
                    verification_result['source'] = source_name
                    logger.info(f"Successfully verified {citation_text} via {source_name}")
                    break
                    
            except Exception as e:
                logger.warning(f"Error verifying {citation_text} with {source_name}: {str(e)}")
                continue
        
        return verification_result
    
    def _parse_citation(self, citation_text: str) -> Dict:
        """Parse citation to extract volume, reporter, page, and court type."""
        citation_info = {
            'volume': None,
            'reporter': None,
            'page': None,
            'year': None,
            'court_type': 'unknown'
        }
        
        # Common citation patterns
        patterns = [
            # U.S. Supreme Court: "385 U.S. 493"
            r'(\d+)\s+U\.S\.\s+(\d+)',
            # Federal: "123 F.2d 456", "456 F.3d 789"
            r'(\d+)\s+F\.(?:2d|3d)\s+(\d+)',
            # State: "123 Wash. 2d 456", "789 P.2d 123"
            r'(\d+)\s+(?:Wash\.|P\.)(?:\s*2d)?\s+(\d+)',
            # Law Review: "123 Harv. L. Rev. 456"
            r'(\d+)\s+\w+\.?\s+L\.?\s+Rev\.?\s+(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, citation_text, re.IGNORECASE)
            if match:
                citation_info['volume'] = match.group(1)
                citation_info['page'] = match.group(2)
                
                # Determine court type
                if 'U.S.' in citation_text:
                    citation_info['court_type'] = 'supreme_court'
                    citation_info['reporter'] = 'U.S.'
                elif 'F.' in citation_text:
                    citation_info['court_type'] = 'federal'
                    if 'F.2d' in citation_text:
                        citation_info['reporter'] = 'F.2d'
                    elif 'F.3d' in citation_text:
                        citation_info['reporter'] = 'F.3d'
                elif 'Wash.' in citation_text or 'P.' in citation_text:
                    citation_info['court_type'] = 'state'
                break
        
        return citation_info
    
    def _rate_limit(self, domain: str):
        """Apply rate limiting for requests to the same domain."""
        now = time.time()
        if domain in self.last_request_time:
            elapsed = now - self.last_request_time[domain]
            if elapsed < self.min_delay:
                time.sleep(self.min_delay - elapsed)
        self.last_request_time[domain] = time.time()
    
    def _verify_with_cornell_law(self, citation_text: str, citation_info: Dict, 
                                extracted_case_name: str = None, extracted_date: str = None) -> Optional[Dict]:
        """Verify citation with Cornell Law School's Legal Information Institute."""
        
        # Cornell Law has different URL patterns for different courts
        if citation_info['court_type'] == 'supreme_court' and citation_info['volume'] and citation_info['page']:
            # Supreme Court: https://www.law.cornell.edu/supremecourt/text/385/493
            url = f"https://www.law.cornell.edu/supremecourt/text/{citation_info['volume']}/{citation_info['page']}"
            
            self._rate_limit('law.cornell.edu')
            
            try:
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    content = response.text
                    
                    # Extract case name from Cornell Law page
                    case_name = None
                    
                    # Try multiple patterns for case name extraction from Cornell Law
                    case_name_patterns = [
                        r'<title>([^<]+?)\s*\|\s*(?:Supreme Court|US Law)',
                        r'<h1[^>]*>([^<]+?)</h1>',
                        r'<h2[^>]*>([^<]+?)</h2>'
                    ]
                    
                    for pattern in case_name_patterns:
                        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                        if match:
                            raw_name = match.group(1).strip()
                            
                            # Clean up the case name from Cornell Law format
                            case_name = raw_name
                            
                            # Remove common prefixes and suffixes
                            case_name = re.sub(r'^[^A-Z]*', '', case_name)  # Remove leading non-caps
                            case_name = re.sub(r'\s*,\s*Appellant[s]?.*', '', case_name)  # Remove appellant info
                            case_name = re.sub(r'\s*,\s*Petitioner[s]?.*', '', case_name)  # Remove petitioner info
                            case_name = re.sub(r'\s+', ' ', case_name).strip()
                            
                            # Check if this looks like a valid case name
                            if len(case_name) > 5 and re.search(r'\bv\.?\b|\bvs\.?\b', case_name, re.IGNORECASE):
                                break
                    
                    # If we still don't have a good case name, try a simpler extraction
                    if not case_name or len(case_name) < 5:
                        # Look for pattern like "NAME v. NAME" in the content
                        simple_match = re.search(r'([A-Z][a-zA-Z]+\s+v\.?\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)', content)
                        if simple_match:
                            case_name = simple_match.group(1).strip()
                    
                    if case_name:
                        
                        # Extract date/year
                        date_match = re.search(r'(\d{4})', content)
                        year = date_match.group(1) if date_match else None
                        
                        # Verify this matches our extracted case name if provided
                        confidence = 0.9
                        if extracted_case_name:
                            # Simple name matching - could be enhanced
                            if self._names_match(extracted_case_name, case_name):
                                confidence = 0.95
                            else:
                                confidence = 0.7
                        
                        return {
                            'verified': True,
                            'canonical_name': case_name,
                            'canonical_date': year,
                            'url': url,
                            'source': 'Cornell Law',  # Actual website source
                            'confidence': confidence,
                            'verification_details': {
                                'method': 'cornell_law_direct_url',
                                'status_code': response.status_code
                            }
                        }
                        
            except requests.RequestException as e:
                logger.debug(f"Cornell Law request failed for {citation_text}: {str(e)}")
                
        return None
    
    def _verify_with_justia(self, citation_text: str, citation_info: Dict,
                           extracted_case_name: str = None, extracted_date: str = None) -> Optional[Dict]:
        """Verify citation with Justia legal database."""
        
        if citation_info['court_type'] == 'supreme_court' and citation_info['volume'] and citation_info['page']:
            # Justia Supreme Court: https://supreme.justia.com/cases/federal/us/385/493/
            url = f"https://supreme.justia.com/cases/federal/us/{citation_info['volume']}/{citation_info['page']}/"
            
            self._rate_limit('justia.com')
            
            try:
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    content = response.text
                    
                    # Extract case name from Justia page
                    case_name_patterns = [
                        r'<h1[^>]*>([^<]+)</h1>',
                        r'<title>([^<]+?)\s*\|\s*Justia',
                        r'case-title[^>]*>([^<]+)</div>'
                    ]
                    
                    case_name = None
                    for pattern in case_name_patterns:
                        match = re.search(pattern, content, re.IGNORECASE)
                        if match:
                            case_name = match.group(1).strip()
                            break
                    
                    if case_name:
                        # Extract year
                        year_match = re.search(r'(\d{4})', content)
                        year = year_match.group(1) if year_match else None
                        
                        confidence = 0.85
                        if extracted_case_name and self._names_match(extracted_case_name, case_name):
                            confidence = 0.9
                        
                        return {
                            'verified': True,
                            'canonical_name': case_name,
                            'canonical_date': year,
                            'url': url,
                            'source': 'Justia',  # Actual website source
                            'confidence': confidence,
                            'verification_details': {
                                'method': 'justia_direct_url',
                                'status_code': response.status_code
                            }
                        }
                        
            except requests.RequestException as e:
                logger.debug(f"Justia request failed for {citation_text}: {str(e)}")
                
        return None
    
    def _verify_with_google_scholar(self, citation_text: str, citation_info: Dict,
                                   extracted_case_name: str = None, extracted_date: str = None) -> Optional[Dict]:
        """Verify citation with Google Scholar (simplified approach)."""
        
        # Google Scholar search is more complex and may require handling CAPTCHAs
        # For now, implement a basic approach
        search_query = citation_text
        if extracted_case_name:
            search_query += f" \"{extracted_case_name}\""
        
        # Note: This is a simplified implementation
        # A full implementation would need to handle Google Scholar's anti-bot measures
        return None
    
    def _verify_with_caselaw_access(self, citation_text: str, citation_info: Dict,
                                   extracted_case_name: str = None, extracted_date: str = None) -> Optional[Dict]:
        """Verify citation with Caselaw Access Project or similar free databases."""
        
        # This would integrate with Harvard's Caselaw Access Project API
        # For now, return None (not implemented)
        return None
    
    def _names_match(self, name1: str, name2: str) -> bool:
        """Check if two case names likely refer to the same case."""
        if not name1 or not name2:
            return False
        
        # Normalize names for comparison
        def normalize_name(name):
            # Remove common legal terms and normalize spacing
            name = re.sub(r'\b(v\.?|vs\.?|versus)\b', 'v', name, flags=re.IGNORECASE)
            name = re.sub(r'[^\w\s]', ' ', name)
            name = re.sub(r'\s+', ' ', name)
            return name.lower().strip()
        
        norm1 = normalize_name(name1)
        norm2 = normalize_name(name2)
        
        # Simple substring matching
        return norm1 in norm2 or norm2 in norm1 or norm1 == norm2


def verify_citations_with_fallback(citations: List, progress_callback=None) -> None:
    """
    Verify a list of citations using fallback sources.
    
    Args:
        citations: List of citation objects to verify
        progress_callback: Optional callback function for progress updates
    """
    verifier = FallbackVerifier()
    
    for i, citation in enumerate(citations):
        if hasattr(citation, 'verified') and citation.verified:
            # Already verified, skip
            continue
            
        citation_text = getattr(citation, 'citation', str(citation))
        extracted_case_name = getattr(citation, 'extracted_case_name', None)
        extracted_date = getattr(citation, 'extracted_date', None)
        
        result = verifier.verify_citation(citation_text, extracted_case_name, extracted_date)
        
        if result['verified']:
            # Update citation object with verification results
            citation.verified = True
            citation.canonical_name = result['canonical_name']
            citation.canonical_date = result['canonical_date']
            citation.url = result['url']
            citation.source = f"fallback_{result['source']}"
            citation.confidence = result['confidence']
            
            if hasattr(citation, 'verification_details'):
                citation.verification_details = result['verification_details']
        
        if progress_callback:
            progress_callback(i + 1, len(citations))
        
        # Small delay to be respectful to servers
        time.sleep(0.5)


if __name__ == "__main__":
    # Test the fallback verifier
    verifier = FallbackVerifier()
    
    # Test with the citation from the user's question
    test_citation = "385 U.S. 493"
    test_case_name = "Davis v. Alaska"
    test_date = "1967"
    
    print(f"Testing fallback verification for: {test_citation}")
    result = verifier.verify_citation(test_citation, test_case_name, test_date)
    
    print(f"Result: {json.dumps(result, indent=2)}")
