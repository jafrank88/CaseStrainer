#!/usr/bin/env python3
"""
Legal Database Scraper for extracting canonical case information
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
        Extract canonical case information from a legal database URL.
        
        Args:
            url: The URL of the case page
            
        Returns:
            Dictionary containing:
            - canonical_name: The official case name
            - url: The main page URL
            - parallel_citations: List of parallel citations
            - year: The year of the case
            - court: The court name (if available)
            - docket: The docket number (if available)
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
            elif 'descrybe.ai' in domain:
                return self._extract_descrybe_info(url)
            elif 'midpage.ai' in domain:
                return self._extract_midpage_info(url)
            else:
                self.logger.warning(f"Unknown legal database domain: {domain}")
                return self._extract_generic_info(url)
                
        except Exception as e:
            self.logger.error(f"Error extracting case info from {url}: {e}")
            return {
                'canonical_name': '',
                'url': url,
                'parallel_citations': [],
                'year': '',
                'court': '',
                'docket': ''
            }
    
    def _extract_casemine_info(self, url: str) -> Dict[str, str]:
        """Extract case information from CaseMine."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract canonical name - look for case names in search results
            canonical_name = ''
            
            # First try to find case names in search results
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
            
            # If no canonical name found in search results, try the main page
            if not canonical_name:
                name_elements = soup.find_all(['h1', 'h2', 'h3'], class_=re.compile(r'title|name|heading'))
                if not name_elements:
                    # Look for the case name in the main content area
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
                    if re.match(r'\d+\s+[A-Z]\.\d+', text):  # Pattern like "534 F.3d 1290"
                        parallel_citations.append(text)
            
            # If no citations found in search results, try main page
            if not parallel_citations:
                citation_section = soup.find('div', string=re.compile(r'Equivalent Citations', re.I))
                if citation_section:
                    citation_parent = citation_section.find_parent()
                    if citation_parent:
                        citation_elements = citation_parent.find_all(['div', 'span', 'p'])
                        for element in citation_elements:
                            text = element.get_text(strip=True)
                            if re.match(r'\d+\s+[A-Z]\.\d+', text):  # Pattern like "534 F.3d 1290"
                                parallel_citations.append(text)
            
            # Extract year from the page
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
            self.logger.error(f"Error extracting CaseMine info: {e}")
            return {'canonical_name': '', 'url': url, 'parallel_citations': [], 'year': '', 'court': '', 'docket': ''}
    
    def _extract_vlex_info(self, url: str) -> Dict[str, str]:
        """Extract case information from vLex."""
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
            self.logger.error(f"Error extracting vLex info: {e}")
            return {'canonical_name': '', 'url': url, 'parallel_citations': [], 'year': '', 'court': '', 'docket': ''}
    
    def _extract_casetext_info(self, url: str) -> Dict[str, str]:
        """Extract case information from Casetext."""
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
            return {'canonical_name': '', 'url': url, 'parallel_citations': [], 'year': '', 'court': '', 'docket': ''}
    
    def _extract_leagle_info(self, url: str) -> Dict[str, str]:
        """Extract case information from Leagle."""
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
            self.logger.error(f"Error extracting Leagle info: {e}")
            return {'canonical_name': '', 'url': url, 'parallel_citations': [], 'year': '', 'court': '', 'docket': ''}
    
    def _extract_justia_info(self, url: str) -> Dict[str, str]:
        """Extract case information from Justia."""
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
            self.logger.error(f"Error extracting Justia info: {e}")
            return {'canonical_name': '', 'url': url, 'parallel_citations': [], 'year': '', 'court': '', 'docket': ''}
    
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