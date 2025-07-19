#!/usr/bin/env python3
# DEPRECATED: Use ComprehensiveWebSearchEngine in src/comprehensive_websearch_engine.py instead of LegalDatabaseScraper.
# This file is retained for legacy reference only and should not be used in new code.
# 
# The ComprehensiveWebSearchEngine provides:
# - All features from LegalDatabaseScraper
# - Enhanced Washington citation variants
# - Advanced case name extraction
# - Specialized legal database extraction (CaseMine, vLex, Casetext, Leagle, Justia, FindLaw)
# - Similarity scoring and validation
# - Better reliability scoring
#
# Migration guide: See docs/WEB_SEARCH_MIGRATION.md

import warnings
warnings.warn(
    "LegalDatabaseScraper is deprecated. Use ComprehensiveWebSearchEngine in src/comprehensive_websearch_engine.py instead.",
    DeprecationWarning,
    stacklevel=2
)

"""
Legal Database Scraper
Specialized scraping for legal databases with enhanced extraction capabilities
"""

import requests
import re
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import logging
from bs4 import BeautifulSoup

class LegalDatabaseScraper:
    """Scraper for extracting canonical case information from legal databases."""
    
    def __init__(self, cache_results: bool = True):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.cache_results = cache_results
        self.logger = logging.getLogger(__name__)
        
    def extract_case_info(self, url: str) -> Dict[str, str]:
        """
        Extract case information from a legal database URL.
        
        Args:
            url: The URL to extract information from
            
        Returns:
            Dictionary containing extracted case information
        """
        try:
            domain = urlparse(url).netloc.lower()
            
            if 'casemine.com' in domain:
                return self._extract_casemine_info(url)
            elif 'vlex.com' in domain:
                return self._extract_vlex_info(url)
            elif 'casetext.com' in domain or 'cetient.com' in domain:
                return self._extract_casetext_info(url)
            elif 'leagle.com' in domain:
                return self._extract_leagle_info(url)
            elif 'justia.com' in domain:
                return self._extract_justia_info(url)
            elif 'findlaw.com' in domain or 'caselaw.findlaw.com' in domain:
                return self._extract_findlaw_info(url)
            elif 'descrybe.ai' in domain:
                return self._extract_descrybe_info(url)
            elif 'midpage.ai' in domain:
                return self._extract_midpage_info(url)
            else:
                self.logger.warning(f"Unknown legal database domain: {domain}")
                return self._extract_generic_info(url)
                
        except Exception as e:
            self.logger.error(f"Error extracting case info from {url}: {e}")
            return self._extract_from_google_snippet_fallback(url)
    
    def _extract_casemine_info(self, url: str) -> Dict[str, str]:
        """Extract case information from CaseMine."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            if response.status_code != 200 or 'Sign on now to see your case' in response.text:
                self.logger.warning("CaseMine service unavailable or restricted, using Google snippet fallback")
                return self._extract_from_google_snippet_fallback(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text(separator='\n')
            # Extract canonical name
            canonical_name = ''
            h1 = soup.find('h1')
            if h1:
                canonical_name = h1.get_text(strip=True)
            else:
                for line in page_text.split('\n'):
                    if 'v.' in line:
                        canonical_name = line.strip()
                        break
            # Extract citation
            citation_pattern = r'(\d+\s+[A-Z]\.\d+\s+\d+\s*\(\d{4}\))'
            citation_match = re.search(citation_pattern, page_text)
            parallel_citations = [citation_match.group(1)] if citation_match else []
            # Extract year
            year = ''
            year_pattern = r'Filed\s+(\w+\s+\d{1,2},\s+(19|20)\d{2})'
            year_match = re.search(year_pattern, page_text)
            if year_match:
                year = re.search(r'(19|20)\d{2}', year_match.group(1)).group()
            elif citation_match:
                year = re.search(r'(19|20)\d{2}', citation_match.group(1)).group()
            # Extract court
            court = ''
            court_pattern = r'Supreme Court of [A-Za-z\s,]+'
            court_match = re.search(court_pattern, page_text)
            if court_match:
                court = court_match.group(0).strip()
            else:
                for line in page_text.split('\n')[:10]:
                    if 'Court' in line:
                        court = line.strip()
                        break
            # Extract docket
            docket = ''
            docket_pattern = r'No\.\s*([0-9-]+)'
            docket_match = re.search(docket_pattern, page_text)
            if docket_match:
                docket = docket_match.group(0)
            if not canonical_name:
                self.logger.warning("CaseMine: No case name found, using Google snippet fallback")
                return self._extract_from_google_snippet_fallback(url)
            return {
                'canonical_name': canonical_name,
                'url': url,
                'parallel_citations': parallel_citations,
                'year': year,
                'court': court,
                'docket': docket,
                'source': 'casemine'
            }
        except Exception as e:
            self.logger.error(f"Error extracting CaseMine info: {e}")
            return self._extract_from_google_snippet_fallback(url)
    
    def _extract_vlex_info(self, url: str) -> Dict[str, str]:
        """Extract case information from vLex."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            if response.status_code != 200 or 'Sign on now to see your case' in response.text:
                self.logger.warning("vLex service unavailable or restricted, using Google snippet fallback")
                return self._extract_from_google_snippet_fallback(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text(separator='\n')
            canonical_name = ''
            h1 = soup.find('h1')
            if h1:
                canonical_name = h1.get_text(strip=True)
            else:
                for line in page_text.split('\n'):
                    if 'v.' in line:
                        canonical_name = line.strip()
                        break
            # Extract citation - look for patterns like "3 Wn.3d 80 (Wash. 2024)"
            citation_patterns = [
                r'(\d+\s+Wn\.3d\s+\d+\s*\([^)]+\))',  # e.g., "3 Wn.3d 80 (Wash. 2024)"
                r'(\d+\s+[A-Z][a-z]+\.\d+\s+\d+\s*\([A-Za-z]+\.\s*\d{4}\))',  # e.g., "3 Wn.3d 80 (Wash. 2024)"
                r'(\d+\s+[A-Z][a-z]+\.\d+\s+\d+\s*\([A-Za-z]+\s+\d{4}\))',  # e.g., "3 Wn.3d 80 (Wash 2024)"
                r'(\d+\s+[A-Z]\.\d+\s+\d+\s*\(\d{4}\))',  # e.g., "546 P.3d 385 (2024)"
                r'(\d+\s+[A-Z]\.\s*\d+\s*[a-z]+\s+\d+\s*\(\d{4}\))',  # e.g., "546 P. 3d 385 (2024)"
            ]
            parallel_citations = []
            for pattern in citation_patterns:
                citation_match = re.search(pattern, page_text)
                if citation_match:
                    parallel_citations.append(citation_match.group(1))
                    break
            # Extract year from citation or decision date
            year = ''
            if parallel_citations:
                year_match = re.search(r'(19|20)\d{2}', parallel_citations[0])
                if year_match:
                    year = year_match.group()
            else:
                # Look for decision date
                year_pattern = r'Decided\s+\w+\s+\d{1,2},\s+(19|20)\d{2}'
                year_match = re.search(year_pattern, page_text)
                if year_match:
                    year = re.search(r'(19|20)\d{2}', year_match.group()).group()
            # Extract court - look for "Washington Supreme Court"
            court = ''
            court_patterns = [
                r'Washington Supreme Court',
                r'Supreme Court of Washington',
                r'Court of Appeals',
                r'District Court'
            ]
            for pattern in court_patterns:
                court_match = re.search(pattern, page_text)
                if court_match:
                    court = court_match.group(0).strip()
                    break
            # Extract docket number
            docket = ''
            docket_pattern = r'No\.\s*([0-9-]+)'
            docket_match = re.search(docket_pattern, page_text)
            if docket_match:
                docket = docket_match.group(0)
            if not canonical_name:
                self.logger.warning("vLex: No case name found, using Google snippet fallback")
                return self._extract_from_google_snippet_fallback(url)
            return {
                'canonical_name': canonical_name,
                'url': url,
                'parallel_citations': parallel_citations,
                'year': year,
                'court': court,
                'docket': docket,
                'source': 'vlex'
            }
        except Exception as e:
            self.logger.error(f"Error extracting vLex info: {e}")
            return self._extract_from_google_snippet_fallback(url)
    
    def _extract_casetext_info(self, url: str) -> Dict[str, str]:
        """Extract case information from Casetext."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Check if Casetext is shut down (returns 410)
            if response.status_code == 410:
                self.logger.warning("Casetext service is no longer available (410 status)")
                return self._extract_from_google_snippet_fallback(url)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract canonical name from search results or main page
            canonical_name = ''
            
            # Look for case names in search results
            search_results = soup.find_all(['div', 'article'], class_=re.compile(r'result|case|item'))
            for result in search_results:
                name_elements = result.find_all(['h1', 'h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|name|heading'))
                for element in name_elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 10 and 'v.' in text:
                        canonical_name = text
                        break
                if canonical_name:
                    break
            
            # If no canonical name found in search results, try main page
            if not canonical_name:
                name_elements = soup.find_all(['h1', 'h2'], class_=re.compile(r'title|name|heading'))
                if not name_elements:
                    name_elements = soup.find_all(['h1', 'h2'])
                
                for element in name_elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 10 and 'v.' in text:
                        canonical_name = text
                        break
            
            # Extract parallel citations
            parallel_citations = []
            
            # Look for citations in search results first
            for result in search_results:
                citation_elements = result.find_all(['div', 'span'], class_=re.compile(r'citation|cite'))
                for element in citation_elements:
                    text = element.get_text(strip=True)
                    if re.match(r'\d+\s+[A-Z]\.\d+', text):
                        parallel_citations.append(text)
            
            # If no citations found in search results, try main page
            if not parallel_citations:
                citation_elements = soup.find_all(['div', 'span'], class_=re.compile(r'citation'))
                for element in citation_elements:
                    text = element.get_text(strip=True)
                    if re.match(r'\d+\s+[A-Z]\.\d+', text):
                        parallel_citations.append(text)
            
            # Extract year
            year = ''
            year_pattern = r'\b(19|20)\d{2}\b'
            page_text = soup.get_text()
            year_match = re.search(year_pattern, page_text)
            if year_match:
                year = year_match.group()
            
            # Extract court information
            court = ''
            court_patterns = [
                r'Court:\s*([^\n;]+)',
                r'([A-Z][a-z]+ Court)',
                r'(Supreme Court|Court of Appeals|District Court)'
            ]
            for pattern in court_patterns:
                court_match = re.search(pattern, page_text, re.I)
                if court_match:
                    court = court_match.group(1).strip()
                    break
            
            # Extract docket number
            docket = ''
            docket_patterns = [
                r'Docket:\s*([^\n;]+)',
                r'Docket No\.:\s*([^\n;]+)',
                r'No\.\s*([0-9-]+)'
            ]
            for pattern in docket_patterns:
                docket_match = re.search(pattern, page_text, re.I)
                if docket_match:
                    docket = docket_match.group(1).strip()
                    break
            
            return {
                'canonical_name': canonical_name,
                'url': url,
                'parallel_citations': parallel_citations,
                'year': year,
                'court': court,
                'docket': docket
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting Casetext info: {e}")
            return self._extract_from_google_snippet_fallback(url)
    
    def _extract_from_google_snippet_fallback(self, url: str) -> Dict[str, str]:
        """
        Extract metadata from Google search result snippets when the actual page is unavailable.
        This is a fallback method for cases where pages return 410, require authentication, etc.
        """
        try:
            # For Casetext URLs, we can extract some info from the URL itself
            if 'casetext.com/case/' in url:
                # Extract case name from URL path
                case_path = url.split('/case/')[-1]
                if case_path:
                    # Convert URL slug to readable case name
                    case_name = case_path.replace('-', ' ').replace('_', ' ')
                    # Capitalize properly
                    case_name = ' '.join(word.capitalize() for word in case_name.split())
                    # Handle common abbreviations
                    case_name = case_name.replace('Llc', 'LLC').replace('Inc', 'Inc.').replace('Corp', 'Corp.')
                    
                    # Try to extract citation from the URL or use a placeholder
                    # For now, we'll return what we can extract
                    return {
                        'canonical_name': case_name,
                        'url': url,
                        'parallel_citations': [],
                        'year': '',  # Would need to be extracted from search snippet
                        'court': '',
                        'docket': '',
                        'source': 'url_extraction'
                    }
            
            # For Leagle URLs, extract from URL pattern
            elif 'leagle.com/decision/' in url:
                # Extract case identifier from URL
                case_id = url.split('/decision/')[-1]
                if case_id:
                    # Convert to readable format
                    case_name = case_id.replace('_', ' ').replace('-', ' ')
                    case_name = ' '.join(word.capitalize() for word in case_name.split())
                    case_name = case_name.replace('Llc', 'LLC').replace('Inc', 'Inc.').replace('Corp', 'Corp.')
                    
                    return {
                        'canonical_name': case_name,
                        'url': url,
                        'parallel_citations': [],
                        'year': '',
                        'court': '',
                        'docket': '',
                        'source': 'url_extraction'
                    }
            
            # For FindLaw URLs, extract from URL pattern
            elif 'findlaw.com/court/' in url:
                # Extract court and case info from URL
                url_parts = url.split('/')
                if len(url_parts) >= 6:
                    court = url_parts[-3].replace('-', ' ').title()
                    case_id = url_parts[-1].replace('.html', '')
                    
                    return {
                        'canonical_name': f"Case {case_id}",
                        'url': url,
                        'parallel_citations': [],
                        'year': '',
                        'court': court,
                        'docket': case_id,
                        'source': 'url_extraction'
                    }
            
            return {
                'canonical_name': '',
                'url': url,
                'parallel_citations': [],
                'year': '',
                'court': '',
                'docket': '',
                'source': 'fallback_failed'
            }
            
        except Exception as e:
            self.logger.error(f"Error in Google snippet fallback: {e}")
            return {
                'canonical_name': '',
                'url': url,
                'parallel_citations': [],
                'year': '',
                'court': '',
                'docket': '',
                'source': 'fallback_error'
            }
    
    def _extract_leagle_info(self, url: str) -> Dict[str, str]:
        """Extract case information from Leagle."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # If Leagle is down or returns an error page, fallback to Google snippet
            if response.status_code != 200 or 'Sign on now to see your case' in response.text:
                self.logger.warning("Leagle service unavailable or restricted, using Google snippet fallback")
                return self._extract_from_google_snippet_fallback(url)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text(separator='\n')
            
            # Extract case name from <h1> or main heading
            canonical_name = ''
            h1 = soup.find('h1')
            if h1:
                canonical_name = h1.get_text(strip=True)
            else:
                # Fallback: first line with 'v.'
                for line in page_text.split('\n'):
                    if 'v.' in line:
                        canonical_name = line.strip()
                        break
            
            # Extract citation (e.g., 546 P.3d 385 (2024))
            citation_pattern = r'(\d+\s+[A-Z]\.\d+\s+\d+\s*\(\d{4}\))'
            citation_match = re.search(citation_pattern, page_text)
            parallel_citations = [citation_match.group(1)] if citation_match else []
            
            # Extract year
            year = ''
            year_pattern = r'Filed\s+(\w+\s+\d{1,2},\s+(19|20)\d{2})'
            year_match = re.search(year_pattern, page_text)
            if year_match:
                # Extract just the year
                year = re.search(r'(19|20)\d{2}', year_match.group(1)).group()
            elif citation_match:
                # Try to extract year from citation
                year = re.search(r'(19|20)\d{2}', citation_match.group(1)).group()
            
            # Extract court
            court = ''
            court_pattern = r'Supreme Court of [A-Za-z\s,]+'
            court_match = re.search(court_pattern, page_text)
            if court_match:
                court = court_match.group(0).strip()
            else:
                # Try to extract from the first 10 lines
                for line in page_text.split('\n')[:10]:
                    if 'Court' in line:
                        court = line.strip()
                        break
            
            # Extract docket number (e.g., No. 101872-0)
            docket = ''
            docket_pattern = r'No\.\s*([0-9-]+)'
            docket_match = re.search(docket_pattern, page_text)
            if docket_match:
                docket = docket_match.group(0)
            
            # If we failed to extract a case name, fallback to Google snippet
            if not canonical_name:
                self.logger.warning("Leagle: No case name found, using Google snippet fallback")
                return self._extract_from_google_snippet_fallback(url)
            
            return {
                'canonical_name': canonical_name,
                'url': url,
                'parallel_citations': parallel_citations,
                'year': year,
                'court': court,
                'docket': docket,
                'source': 'leagle'
            }
        except Exception as e:
            self.logger.error(f"Error extracting Leagle info: {e}")
            return self._extract_from_google_snippet_fallback(url)
    
    def _extract_justia_info(self, url: str) -> Dict[str, str]:
        """Extract case information from Justia."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            if response.status_code != 200 or 'Sign on now to see your case' in response.text:
                self.logger.warning("Justia service unavailable or restricted, using Google snippet fallback")
                return self._extract_from_google_snippet_fallback(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text(separator='\n')
            canonical_name = ''
            h1 = soup.find('h1')
            if h1:
                canonical_name = h1.get_text(strip=True)
                # Clean up the case name (remove "(Majority)" suffix)
                canonical_name = re.sub(r'\s*\(Majority\)\s*$', '', canonical_name)
            else:
                for line in page_text.split('\n'):
                    if 'v.' in line:
                        canonical_name = line.strip()
                        break
            # Extract citation - look for patterns like "546 P.3d 385 (2024)"
            citation_patterns = [
                r'(\d+\s+[A-Z]\.\d+\s+\d+\s*\(\d{4}\))',  # e.g., "546 P.3d 385 (2024)"
                r'(\d+\s+[A-Z]\.\s*\d+\s*[a-z]+\s+\d+\s*\(\d{4}\))',  # e.g., "546 P. 3d 385 (2024)"
                r'(\d+\s+[A-Z][A-Za-z]+\s+\d+\s*\(\d{4}\))',  # e.g., "546 Pacific 3d 385 (2024)"
            ]
            parallel_citations = []
            for pattern in citation_patterns:
                citation_match = re.search(pattern, page_text)
                if citation_match:
                    parallel_citations.append(citation_match.group(1))
                    break
            # Extract year from citation or filed date
            year = ''
            if parallel_citations:
                year_match = re.search(r'(19|20)\d{2}', parallel_citations[0])
                if year_match:
                    year = year_match.group()
            else:
                # Look for filed date
                year_pattern = r'Filed:\s*(\w+\s+\d{1,2},\s+(19|20)\d{2})'
                year_match = re.search(year_pattern, page_text)
                if year_match:
                    year = re.search(r'(19|20)\d{2}', year_match.group(1)).group()
            # Extract court - look for "Supreme Court of the State of Washington"
            court = ''
            court_patterns = [
                r'Supreme Court of the State of Washington',
                r'Supreme Court of Washington',
                r'Court of Appeals',
                r'District Court'
            ]
            for pattern in court_patterns:
                court_match = re.search(pattern, page_text)
                if court_match:
                    court = court_match.group(0).strip()
                    break
            # Extract docket number
            docket = ''
            docket_pattern = r'No\.\s*([0-9-]+)'
            docket_match = re.search(docket_pattern, page_text)
            if docket_match:
                docket = docket_match.group(0)
            if not canonical_name:
                self.logger.warning("Justia: No case name found, using Google snippet fallback")
                return self._extract_from_google_snippet_fallback(url)
            return {
                'canonical_name': canonical_name,
                'url': url,
                'parallel_citations': parallel_citations,
                'year': year,
                'court': court,
                'docket': docket,
                'source': 'justia'
            }
        except Exception as e:
            self.logger.error(f"Error extracting Justia info: {e}")
            return self._extract_from_google_snippet_fallback(url)
    
    def _extract_generic_info(self, url: str) -> Dict[str, str]:
        """Extract case information using generic methods."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract canonical name from search results or main page
            canonical_name = ''
            
            # Look for case names in search results
            search_results = soup.find_all(['div', 'article'], class_=re.compile(r'result|case|item'))
            for result in search_results:
                name_elements = result.find_all(['h1', 'h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|name|heading'))
                for element in name_elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 10 and 'v.' in text:
                        canonical_name = text
                        break
                if canonical_name:
                    break
            
            # If no canonical name found in search results, try main page
            if not canonical_name:
                name_elements = soup.find_all(['h1', 'h2', 'h3'])
                for element in name_elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 10 and 'v.' in text:
                        canonical_name = text
                        break
            
            # Extract parallel citations from search results or main page
            parallel_citations = []
            
            # Look for citations in search results first
            for result in search_results:
                citation_elements = result.find_all(['div', 'span', 'p'], class_=re.compile(r'citation|cite'))
                for element in citation_elements:
                    text = element.get_text(strip=True)
                    if re.match(r'\d+\s+[A-Z]\.\d+', text):
                        parallel_citations.append(text)
            
            # If no citations found in search results, try main page
            if not parallel_citations:
                page_text = soup.get_text()
                citation_pattern = r'\d+\s+[A-Z]\.\d+'
                citations = re.findall(citation_pattern, page_text)
                parallel_citations = list(set(citations))  # Remove duplicates
            
            # Extract year
            year = ''
            year_pattern = r'\b(19|20)\d{2}\b'
            page_text = soup.get_text()
            year_match = re.search(year_pattern, page_text)
            if year_match:
                year = year_match.group()
            
            # Extract court information
            court = ''
            court_patterns = [
                r'Court:\s*([^\n;]+)',
                r'([A-Z][a-z]+ Court)',
                r'(Supreme Court|Court of Appeals|District Court)'
            ]
            for pattern in court_patterns:
                court_match = re.search(pattern, page_text, re.I)
                if court_match:
                    court = court_match.group(1).strip()
                    break
            
            # Extract docket number
            docket = ''
            docket_patterns = [
                r'Docket:\s*([^\n;]+)',
                r'Docket No\.:\s*([^\n;]+)',
                r'No\.\s*([0-9-]+)'
            ]
            for pattern in docket_patterns:
                docket_match = re.search(pattern, page_text, re.I)
                if docket_match:
                    docket = docket_match.group(1).strip()
                    break
            
            return {
                'canonical_name': canonical_name,
                'url': url,
                'parallel_citations': parallel_citations,
                'year': year,
                'court': court,
                'docket': docket
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting generic info: {e}")
            return {'canonical_name': '', 'url': url, 'parallel_citations': [], 'year': '', 'court': '', 'docket': ''}
    
    def _extract_descrybe_info(self, url: str) -> Dict[str, str]:
        """Extract case information from Descrybe.ai."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text(separator='\n')

            # Canonical name
            canonical_name = ''
            for tag in soup.find_all(['h1', 'h2']):
                text = tag.get_text(strip=True)
                if 'v.' in text:
                    canonical_name = text
                    break
            if not canonical_name:
                # Try fallback: first line with 'v.'
                for line in page_text.split('\n'):
                    if 'v.' in line:
                        canonical_name = line.strip()
                        break

            # Citations
            parallel_citations = []
            citation_match = re.search(r'Citations:\s*([^\n]+)', page_text)
            if citation_match:
                citations = citation_match.group(1)
                # Split on semicolon or comma
                for c in re.split(r'[;,]', citations):
                    c = c.strip()
                    if c:
                        parallel_citations.append(c)

            # Year
            year = ''
            court_line = ''
            for line in page_text.split('\n'):
                if line.lower().startswith('court:'):
                    court_line = line
                    break
            year_match = re.search(r'\b(19|20)\d{2}\b', court_line)
            if year_match:
                year = year_match.group()

            # Court
            court = ''
            if court_line:
                court = court_line.replace('Court:', '').split(';')[0].strip()

            # Docket
            docket = ''
            docket_match = re.search(r'Docket:\s*([^\n;]+)', page_text)
            if docket_match:
                docket = docket_match.group(1).strip()

            return {
                'canonical_name': canonical_name,
                'url': url,
                'parallel_citations': parallel_citations,
                'year': year,
                'court': court,
                'docket': docket
            }
        except Exception as e:
            self.logger.error(f"Error extracting Descrybe info: {e}")
            return {'canonical_name': '', 'url': url, 'parallel_citations': [], 'year': '', 'court': '', 'docket': ''}

    def _extract_midpage_info(self, url: str) -> Dict[str, str]:
        """Extract case information from Midpage.ai."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text(separator='\n')

            # Canonical name
            canonical_name = ''
            for tag in soup.find_all(['h1', 'h2']):
                text = tag.get_text(strip=True)
                if 'v.' in text:
                    canonical_name = text
                    break
            if not canonical_name:
                for line in page_text.split('\n'):
                    if 'v.' in line:
                        canonical_name = line.strip()
                        break

            # Citations
            parallel_citations = []
            citation_match = re.search(r'Citations?:\s*([^\n]+)', page_text)
            if citation_match:
                citations = citation_match.group(1)
                for c in re.split(r'[;,]', citations):
                    c = c.strip()
                    if c:
                        parallel_citations.append(c)

            # Year
            year = ''
            year_match = re.search(r'\b(19|20)\d{2}\b', page_text)
            if year_match:
                year = year_match.group()

            # Court
            court = ''
            court_match = re.search(r'Court:\s*([^\n;]+)', page_text)
            if court_match:
                court = court_match.group(1).strip()

            # Docket
            docket = ''
            docket_match = re.search(r'Docket:\s*([^\n;]+)', page_text)
            if docket_match:
                docket = docket_match.group(1).strip()

            return {
                'canonical_name': canonical_name,
                'url': url,
                'parallel_citations': parallel_citations,
                'year': year,
                'court': court,
                'docket': docket
            }
        except Exception as e:
            self.logger.error(f"Error extracting Midpage info: {e}")
            return {'canonical_name': '', 'url': url, 'parallel_citations': [], 'year': '', 'court': '', 'docket': ''}
    
    def _extract_findlaw_info(self, url: str) -> Dict[str, str]:
        """Extract case information from FindLaw."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            if response.status_code != 200 or 'Sign on now to see your case' in response.text:
                self.logger.warning("FindLaw service unavailable or restricted, using Google snippet fallback")
                return self._extract_from_google_snippet_fallback(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text(separator='\n')
            canonical_name = ''
            h1 = soup.find('h1')
            if h1:
                canonical_name = h1.get_text(strip=True)
            else:
                for line in page_text.split('\n'):
                    if 'v.' in line:
                        canonical_name = line.strip()
                        break
            citation_pattern = r'(\d+\s+[A-Z]\.\d+\s+\d+\s*\(\d{4}\))'
            citation_match = re.search(citation_pattern, page_text)
            parallel_citations = [citation_match.group(1)] if citation_match else []
            year = ''
            year_pattern = r'Filed\s+(\w+\s+\d{1,2},\s+(19|20)\d{2})'
            year_match = re.search(year_pattern, page_text)
            if year_match:
                year = re.search(r'(19|20)\d{2}', year_match.group(1)).group()
            elif citation_match:
                year = re.search(r'(19|20)\d{2}', citation_match.group(1)).group()
            court = ''
            court_pattern = r'Supreme Court of [A-Za-z\s,]+'
            court_match = re.search(court_pattern, page_text)
            if court_match:
                court = court_match.group(0).strip()
            else:
                for line in page_text.split('\n')[:10]:
                    if 'Court' in line:
                        court = line.strip()
                        break
            docket = ''
            docket_pattern = r'No\.\s*([0-9-]+)'
            docket_match = re.search(docket_pattern, page_text)
            if docket_match:
                docket = docket_match.group(0)
            if not canonical_name:
                self.logger.warning("FindLaw: No case name found, using Google snippet fallback")
                return self._extract_from_google_snippet_fallback(url)
            return {
                'canonical_name': canonical_name,
                'url': url,
                'parallel_citations': parallel_citations,
                'year': year,
                'court': court,
                'docket': docket,
                'source': 'findlaw'
            }
        except Exception as e:
            self.logger.error(f"Error extracting FindLaw info: {e}")
            return self._extract_from_google_snippet_fallback(url)
    
    def extract_from_multiple_sources(self, citation: str) -> List[Dict[str, str]]:
        """
        Extract case information from multiple legal database sources.
        
        Args:
            citation: The citation to search for
            
        Returns:
            List of dictionaries containing case information from different sources
        """
        results = []
        
        # Generate URLs for different legal databases
        urls = self._generate_search_urls(citation)
        
        for url in urls:
            try:
                case_info = self.extract_case_info(url)
                if case_info['canonical_name']:  # Only add if we found a canonical name
                    results.append(case_info)
                time.sleep(1)  # Be respectful to the servers
            except Exception as e:
                self.logger.error(f"Error processing {url}: {e}")
                continue
        
        return results
    
    def _generate_search_urls(self, citation: str) -> List[str]:
        """Generate search URLs for different legal databases."""
        # Clean the citation for URL generation
        clean_citation = citation.replace(' ', '+').replace('.', '')
        
        urls = [
            # Use more reliable search patterns
            f"https://www.casemine.com/search?q={clean_citation}",
            f"https://vlex.com/sites/search?q={clean_citation}",
            f"https://casetext.com/search?q={clean_citation}",
            f"https://www.leagle.com/search?q={clean_citation}",
            f"https://law.justia.com/search?query={clean_citation}",
            # For Descrybe and Midpage, try different URL patterns
            f"https://descrybe.ai/search?q={clean_citation}",
            f"https://midpage.ai/search?q={clean_citation}"
        ]
        
        return urls 

def extract_canonical_metadata_from_justia_supreme(url, html):
    soup = BeautifulSoup(html, "html.parser")
    # Case name from <h1>
    case_name = ""
    h1 = soup.find("h1")
    if h1:
        case_name = h1.get_text(strip=True)
    # Date from 'Filed for record at ... on <DATE>'
    date = ""
    date_match = re.search(r"Filed for record at [^\n]+ on ([A-Za-z]+ \d{1,2}, \d{4})", html)
    if date_match:
        date = date_match.group(1)
    return {
        "canonical_case_name": case_name,
        "canonical_date": date,
        "canonical_url": url
    }

def extract_canonical_metadata_from_findlaw_wa_supreme(url, html):
    soup = BeautifulSoup(html, "html.parser")
    # Case name from <h1> or page title
    case_name = ""
    h1 = soup.find("h1")
    if h1:
        case_name = h1.get_text(strip=True)
    if not case_name:
        case_name = soup.title.get_text(strip=True) if soup.title else ""
    # Date: look for 'Decided: <DATE>' or similar
    date = ""
    date_match = re.search(r"Decided:\s*([A-Za-z]+ \d{1,2}, \d{4})", html)
    if not date_match:
        # Try to find any date pattern in the text
        date_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}', html)
    if date_match:
        date = date_match.group(1)
    return {
        "canonical_case_name": case_name,
        "canonical_date": date,
        "canonical_url": url
    }

# In your main extraction function:
def extract_case_metadata(url):
    resp = requests.get(url, timeout=10)
    html = resp.text
    if "law.justia.com/cases/washington/supreme-court/" in url:
        return extract_canonical_metadata_from_justia_supreme(url, html)
    if "caselaw.findlaw.com/court/wa-supreme-court/" in url:
        return extract_canonical_metadata_from_findlaw_wa_supreme(url, html)
    # ... fallback to previous logic for other domains ... 