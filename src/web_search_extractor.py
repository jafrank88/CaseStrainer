#!/usr/bin/env python3
"""
Web Search Extractor for Legal Citations

This module provides comprehensive extraction rules for case names, dates, and canonical URLs
from various legal websites and search engines.
"""

import re
import json
from typing import Dict, Optional, Tuple, List
from urllib.parse import urljoin, urlparse
from datetime import datetime
import logging

class WebSearchExtractor:
    """
    Extracts case names, dates, and canonical URLs from web search results.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Common case name patterns
        self.case_name_patterns = [
            # Standard case name format: "Plaintiff v. Defendant"
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+v\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            # Case name with "vs" instead of "v."
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+vs\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            # Case name with "versus"
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+versus\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            # Case name with "and" (for cases with multiple parties)
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+and\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            # Case name with "et al."
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+et\s+al\.)',
            # Case name with "In re"
            r'(In\s+re\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            # Case name with "Ex parte"
            r'(Ex\s+parte\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        # Date patterns
        self.date_patterns = [
            # Full date: "January 22, 1973"
            r'(\w+\s+\d{1,2},\s+\d{4})',
            # Abbreviated month: "Jan. 22, 1973"
            r'(\w+\.\s+\d{1,2},\s+\d{4})',
            # ISO format: "1973-01-22"
            r'(\d{4}-\d{2}-\d{2})',
            # MM/DD/YYYY: "01/22/1973"
            r'(\d{1,2}/\d{1,2}/\d{4})',
            # Year only: "(1973)"
            r'\((\d{4})\)',
            # Filed date: "Filed: January 22, 1973"
            r'Filed:\s*(\w+\s+\d{1,2},\s+\d{4})',
            # Decided date: "Decided: January 22, 1973"
            r'Decided:\s*(\w+\s+\d{1,2},\s+\d{4})',
        ]
        
        # Citation patterns for validation
        self.citation_patterns = [
            r'\d+\s+[A-Z]+\.[\d]*[A-Za-z]*\s+\d+',  # Standard reporter format
            r'\d+\s+[A-Z]{2}\s+\d+',       # State court format
            r'\d+\s+U\.S\.\s+\d+',         # Supreme Court
            r'\d+\s+S\.Ct\.\s+\d+',        # Supreme Court Reporter
            r'\d+\s+L\.Ed\.\d*\s+\d+',     # Lawyers' Edition
        ]

    def extract_case_name(self, text: str, citation: str = None) -> Optional[str]:
        """
        Extract case name from text using multiple strategies.
        
        Args:
            text: The text to search for case names
            citation: The citation being verified (for context)
            
        Returns:
            Extracted case name or None
        """
        if not text:
            return None
            
        # Clean the text
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Strategy 1: Look for case name patterns
        for pattern in self.case_name_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Return the longest match (most complete case name)
                return max(matches, key=len)
        
        # Strategy 2: Look for title-like text before the citation
        if citation:
            citation_index = text.find(citation)
            if citation_index > 0:
                # Look for text before the citation that might be a case name
                before_citation = text[:citation_index].strip()
                # Split by common separators and take the last meaningful part
                parts = re.split(r'[,\-–—]', before_citation)
                for part in reversed(parts):
                    part = part.strip()
                    if len(part) > 10 and not part.isdigit():
                        # Check if it looks like a case name
                        if re.search(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', part):
                            return part
        
        # Strategy 3: Look for text in quotes that might be a case name
        quoted_matches = re.findall(r'"([^"]+)"', text)
        for match in quoted_matches:
            if len(match) > 10 and re.search(r'\bv\.\b|\bvs\.\b|\bversus\b', match, re.IGNORECASE):
                return match
        
        return None

    def extract_date(self, text: str, citation: str = None) -> Optional[str]:
        """
        Extract date from text using multiple strategies.
        
        Args:
            text: The text to search for dates
            citation: The citation being verified (for context)
            
        Returns:
            Extracted date in ISO format (YYYY-MM-DD) or None
        """
        if not text:
            return None
            
        # Strategy 1: Look for date patterns
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                date_str = matches[0]
                try:
                    # Try to parse the date
                    if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                        # Already in ISO format
                        return date_str
                    elif re.match(r'\d{4}', date_str):
                        # Just a year
                        return f"{date_str}-01-01"
                    else:
                        # Try to parse various date formats
                        for fmt in ['%B %d, %Y', '%b. %d, %Y', '%m/%d/%Y']:
                            try:
                                parsed_date = datetime.strptime(date_str, fmt)
                                return parsed_date.strftime('%Y-%m-%d')
                            except ValueError:
                                continue
                except Exception as e:
                    self.logger.debug(f"Error parsing date '{date_str}': {e}")
                    continue
        
        # Strategy 2: Extract year from citation if present
        if citation:
            year_match = re.search(r'\((\d{4})\)', citation)
            if year_match:
                return f"{year_match.group(1)}-01-01"
        
        return None

    def extract_canonical_url(self, base_url: str, search_url: str, text: str) -> Optional[str]:
        """
        Extract canonical URL from search results.
        
        Args:
            base_url: The base URL of the search site
            search_url: The search URL that was used
            text: The HTML text of the search results
            
        Returns:
            Canonical URL or None
        """
        if not text:
            return None
            
        # Strategy 1: Look for canonical link tags
        canonical_match = re.search(r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', text)
        if canonical_match:
            return canonical_match.group(1)
        
        # Strategy 2: Look for case detail links
        case_link_patterns = [
            r'href=["\']([^"\']*cases[^"\']*)["\']',
            r'href=["\']([^"\']*case[^"\']*)["\']',
            r'href=["\']([^"\']*opinion[^"\']*)["\']',
        ]
        
        for pattern in case_link_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if match.startswith('http'):
                    return match
                elif match.startswith('/'):
                    return urljoin(base_url, match)
        
        return None

    def extract_from_justia(self, text: str, citation: str, search_url: str) -> Dict:
        """
        Extract case information from Justia search results.
        """
        result = {
            'verified': 'false',
            'source': 'Justia',
            'url': None,
            'case_name': None,
            'canonical_date': None,
            'confidence': 0.0
        }
        
        try:
            # Extract case name
            case_name = self.extract_case_name(text, citation)
            if case_name:
                result['case_name'] = case_name
                result['canonical_name'] = case_name
                result['confidence'] += 0.3
            
            # Extract date
            date = self.extract_date(text, citation)
            if date:
                result['canonical_date'] = date
                result['confidence'] += 0.2
            
            # Extract URL
            url = self.extract_canonical_url('https://law.justia.com', search_url, text)
            if url:
                result['url'] = url
                result['confidence'] += 0.4
            
            # Check if citation is found in text
            if citation.lower() in text.lower():
                result['verified'] = 'true'
                result['confidence'] += 0.1
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error extracting from Justia: {e}")
            return result

    def extract_from_findlaw(self, text: str, citation: str, search_url: str) -> Dict:
        """
        Extract case information from FindLaw search results.
        """
        result = {
            'verified': 'false',
            'source': 'FindLaw',
            'url': None,
            'case_name': None,
            'canonical_date': None,
            'confidence': 0.0
        }
        
        try:
            # Extract case name
            case_name = self.extract_case_name(text, citation)
            if case_name:
                result['case_name'] = case_name
                result['canonical_name'] = case_name
                result['confidence'] += 0.3
            
            # Extract date
            date = self.extract_date(text, citation)
            if date:
                result['canonical_date'] = date
                result['confidence'] += 0.2
            
            # Extract URL
            url = self.extract_canonical_url('https://caselaw.findlaw.com', search_url, text)
            if url:
                result['url'] = url
                result['confidence'] += 0.4
            
            # Check if citation is found in text
            if citation.lower() in text.lower():
                result['verified'] = 'true'
                result['confidence'] += 0.1
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error extracting from FindLaw: {e}")
            return result

    def extract_from_google_scholar(self, text: str, citation: str, search_url: str) -> Dict:
        """
        Extract case information from Google Scholar search results.
        """
        result = {
            'verified': 'false',
            'source': 'Google Scholar',
            'url': None,
            'case_name': None,
            'canonical_date': None,
            'confidence': 0.0
        }
        
        try:
            # Extract case name from title elements
            title_matches = re.findall(r'<h3[^>]*class="gs_rt"[^>]*>(.*?)</h3>', text, re.DOTALL)
            for title in title_matches:
                # Clean HTML tags
                clean_title = re.sub(r'<[^>]+>', '', title).strip()
                if citation.lower() in clean_title.lower():
                    result['case_name'] = clean_title
                    result['canonical_name'] = clean_title
                    result['confidence'] += 0.3
                    break
            
            # Extract date
            date = self.extract_date(text, citation)
            if date:
                result['canonical_date'] = date
                result['confidence'] += 0.2
            
            # Extract URL from title links
            url_match = re.search(r'<h3[^>]*class="gs_rt"[^>]*><a[^>]*href="([^"]+)"', text)
            if url_match:
                result['url'] = url_match.group(1)
                result['confidence'] += 0.4
            
            # Check if citation is found in text
            if citation.lower() in text.lower():
                result['verified'] = 'true'
                result['confidence'] += 0.1
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error extracting from Google Scholar: {e}")
            return result

    def extract_from_casemine(self, text: str, citation: str, search_url: str) -> Dict:
        """
        Extract case information from CaseMine search results.
        """
        result = {
            'verified': 'false',
            'source': 'CaseMine',
            'url': None,
            'case_name': None,
            'canonical_date': None,
            'confidence': 0.0
        }
        
        try:
            # Extract case name
            case_name = self.extract_case_name(text, citation)
            if case_name:
                result['case_name'] = case_name
                result['canonical_name'] = case_name
                result['confidence'] += 0.3
            
            # Extract date
            date = self.extract_date(text, citation)
            if date:
                result['canonical_date'] = date
                result['confidence'] += 0.2
            
            # Extract URL
            url = self.extract_canonical_url('https://www.casemine.com', search_url, text)
            if url:
                result['url'] = url
                result['confidence'] += 0.4
            
            # Check if citation is found in text
            if citation.lower() in text.lower():
                result['verified'] = 'true'
                result['confidence'] += 0.1
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error extracting from CaseMine: {e}")
            return result

    def extract_from_casetext(self, text: str, citation: str, search_url: str) -> Dict:
        """
        Extract case information from Casetext search results.
        """
        result = {
            'verified': 'false',
            'source': 'Casetext',
            'url': None,
            'case_name': None,
            'canonical_date': None,
            'confidence': 0.0
        }
        
        try:
            # Extract case name
            case_name = self.extract_case_name(text, citation)
            if case_name:
                result['case_name'] = case_name
                result['canonical_name'] = case_name
                result['confidence'] += 0.3
            
            # Extract date
            date = self.extract_date(text, citation)
            if date:
                result['canonical_date'] = date
                result['confidence'] += 0.2
            
            # Extract URL
            url = self.extract_canonical_url('https://casetext.com', search_url, text)
            if url:
                result['url'] = url
                result['confidence'] += 0.4
            
            # Check if citation is found in text
            if citation.lower() in text.lower():
                result['verified'] = 'true'
                result['confidence'] += 0.1
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error extracting from Casetext: {e}")
            return result

    def extract_from_vlex(self, text: str, citation: str, search_url: str) -> Dict:
        """
        Extract case information from vLex search results.
        """
        result = {
            'verified': 'false',
            'source': 'vLex',
            'url': None,
            'case_name': None,
            'canonical_date': None,
            'confidence': 0.0
        }
        
        try:
            # Extract case name
            case_name = self.extract_case_name(text, citation)
            if case_name:
                result['case_name'] = case_name
                result['canonical_name'] = case_name
                result['confidence'] += 0.3
            
            # Extract date
            date = self.extract_date(text, citation)
            if date:
                result['canonical_date'] = date
                result['confidence'] += 0.2
            
            # Extract URL
            url = self.extract_canonical_url('https://vlex.com', search_url, text)
            if url:
                result['url'] = url
                result['confidence'] += 0.4
            
            # Check if citation is found in text
            if citation.lower() in text.lower():
                result['verified'] = 'true'
                result['confidence'] += 0.1
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error extracting from vLex: {e}")
            return result

    def extract_from_leagle(self, text: str, citation: str, search_url: str) -> Dict:
        """
        Extract case information from Leagle search results.
        """
        result = {
            'verified': 'false',
            'source': 'Leagle',
            'url': None,
            'case_name': None,
            'canonical_date': None,
            'confidence': 0.0
        }
        
        try:
            # Extract case name
            case_name = self.extract_case_name(text, citation)
            if case_name:
                result['case_name'] = case_name
                result['canonical_name'] = case_name
                result['confidence'] += 0.3
            
            # Extract date
            date = self.extract_date(text, citation)
            if date:
                result['canonical_date'] = date
                result['confidence'] += 0.2
            
            # Extract URL
            url = self.extract_canonical_url('https://www.leagle.com', search_url, text)
            if url:
                result['url'] = url
                result['confidence'] += 0.4
            
            # Check if citation is found in text
            if citation.lower() in text.lower():
                result['verified'] = 'true'
                result['confidence'] += 0.1
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error extracting from Leagle: {e}")
            return result

    def extract_from_bing(self, text: str, citation: str, search_url: str) -> Dict:
        """
        Extract case information from Bing search results.
        """
        result = {
            'verified': 'false',
            'source': 'Bing',
            'url': None,
            'case_name': None,
            'canonical_date': None,
            'confidence': 0.0
        }
        
        try:
            # Extract case name
            case_name = self.extract_case_name(text, citation)
            if case_name:
                result['case_name'] = case_name
                result['canonical_name'] = case_name
                result['confidence'] += 0.3
            
            # Extract date
            date = self.extract_date(text, citation)
            if date:
                result['canonical_date'] = date
                result['confidence'] += 0.2
            
            # Extract URL from search results
            url_matches = re.findall(r'href="([^"]+)"', text)
            for url in url_matches:
                if any(domain in url.lower() for domain in ['justia.com', 'findlaw.com', 'caselaw.findlaw.com', 'supreme.justia.com']):
                    result['url'] = url
                    result['confidence'] += 0.4
                    break
            
            # Check if citation is found in text
            if citation.lower() in text.lower():
                result['verified'] = 'true'
                result['confidence'] += 0.1
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error extracting from Bing: {e}")
            return result

    def extract_from_duckduckgo(self, text: str, citation: str, search_url: str) -> Dict:
        """
        Extract case information from DuckDuckGo search results.
        """
        result = {
            'verified': 'false',
            'source': 'DuckDuckGo',
            'url': None,
            'case_name': None,
            'canonical_date': None,
            'confidence': 0.0
        }
        
        try:
            # Extract case name
            case_name = self.extract_case_name(text, citation)
            if case_name:
                result['case_name'] = case_name
                result['canonical_name'] = case_name
                result['confidence'] += 0.3
            
            # Extract date
            date = self.extract_date(text, citation)
            if date:
                result['canonical_date'] = date
                result['confidence'] += 0.2
            
            # Extract URL from search results
            url_matches = re.findall(r'href="([^"]+)"', text)
            for url in url_matches:
                if any(domain in url.lower() for domain in ['justia.com', 'findlaw.com', 'caselaw.findlaw.com', 'supreme.justia.com']):
                    result['url'] = url
                    result['confidence'] += 0.4
                    break
            
            # Check if citation is found in text
            if citation.lower() in text.lower():
                result['verified'] = 'true'
                result['confidence'] += 0.1
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error extracting from DuckDuckGo: {e}")
            return result

    def extract_generic(self, text: str, citation: str, search_url: str, source_name: str) -> Dict:
        """
        Generic extraction method for any source.
        """
        result = {
            'verified': 'false',
            'source': source_name,
            'url': None,
            'case_name': None,
            'canonical_date': None,
            'confidence': 0.0
        }
        
        try:
            # Extract case name
            case_name = self.extract_case_name(text, citation)
            if case_name:
                result['case_name'] = case_name
                result['canonical_name'] = case_name
                result['confidence'] += 0.3
            
            # Extract date
            date = self.extract_date(text, citation)
            if date:
                result['canonical_date'] = date
                result['confidence'] += 0.2
            
            # Extract URL
            parsed_url = urlparse(search_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            url = self.extract_canonical_url(base_url, search_url, text)
            if url:
                result['url'] = url
                result['confidence'] += 0.4
            
            # Check if citation is found in text
            if citation.lower() in text.lower():
                result['verified'] = 'true'
                result['confidence'] += 0.1
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in generic extraction for {source_name}: {e}")
            return result 