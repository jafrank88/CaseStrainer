# DEPRECATED: Use ComprehensiveWebSearchEngine in src/comprehensive_websearch_engine.py instead of EnhancedWebSearcher.
# This file is retained for legacy reference only and should not be used in new code.
# 
# The ComprehensiveWebSearchEngine provides:
# - All features from EnhancedWebSearcher
# - Enhanced Washington citation variants
# - Advanced case name extraction
# - Specialized legal database extraction
# - Similarity scoring and validation
# - Better reliability scoring
#
# Migration guide: See docs/WEB_SEARCH_MIGRATION.md

import warnings
warnings.warn(
    "EnhancedWebSearcher is deprecated. Use ComprehensiveWebSearchEngine in src/comprehensive_websearch_engine.py instead.",
    DeprecationWarning,
    stacklevel=2
)

"""
Enhanced Web Search and Extraction for Legal Citations
Provides advanced web scraping with multiple extraction techniques
"""

import re
import logging
import time
import asyncio
import aiohttp
from typing import Dict, Optional, Any, List, Tuple
from urllib.parse import quote_plus, urljoin, urlparse
import json
from datetime import datetime
from src.extract_case_name import extract_case_name_from_text  # Use canonical extraction if needed

logger = logging.getLogger(__name__)

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

class EnhancedWebExtractor:
    """
    Advanced web extraction using multiple techniques for canonical information.
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
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Method 1: Structured data extraction (JSON-LD, microdata)
            structured_data = self._extract_structured_data(soup)
            if structured_data:
                result.update(structured_data)
                result['extraction_methods'].append('structured_data')
                result['confidence'] += 0.4
            
            # Method 2: HTML metadata extraction
            metadata = self._extract_html_metadata(soup)
            if metadata:
                for key, value in metadata.items():
                    if not result.get(key) and value:
                        result[key] = value
                        result['extraction_methods'].append(f'metadata_{key}')
                        result['confidence'] += 0.2
            
            # Method 3: Semantic HTML extraction
            semantic_data = self._extract_semantic_html(soup, citation)
            if semantic_data:
                for key, value in semantic_data.items():
                    if not result.get(key) and value:
                        result[key] = value
                        result['extraction_methods'].append(f'semantic_{key}')
                        result['confidence'] += 0.3
            
            # Method 4: Pattern-based extraction from cleaned text
            text_data = self._extract_from_text_patterns(soup.get_text(), citation)
            if text_data:
                for key, value in text_data.items():
                    if not result.get(key) and value:
                        result[key] = value
                        result['extraction_methods'].append(f'pattern_{key}')
                        result['confidence'] += 0.2
            
            # Method 5: URL-based extraction
            url_data = self._extract_from_url(url, citation)
            if url_data:
                for key, value in url_data.items():
                    if not result.get(key) and value:
                        result[key] = value
                        result['extraction_methods'].append(f'url_{key}')
                        result['confidence'] += 0.1
            
            return result
            
        except ImportError:
            # Fallback to text-only extraction if BeautifulSoup not available
            self.logger.warning("BeautifulSoup not available, using text-only extraction")
            return self._extract_from_text_patterns(html_content, citation)
        except Exception as e:
            self.logger.error(f"Error in advanced extraction: {e}")
            result['error'] = str(e)
            return result

    def extract_from_search_results(self, html_content: str, search_engine: str) -> List[SearchEngineMetadata]:
        """
        Extract search results metadata from search engine pages.
        This is useful when the actual pages are unavailable (linkrot).
        """
        results = []
        
        try:
            from bs4 import BeautifulSoup
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

    def _extract_structured_data(self, soup) -> Dict[str, Any]:
        """Extract data from JSON-LD, microdata, and RDFa."""
        result = {}
        
        try:
            # JSON-LD extraction
            json_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_scripts:
                try:
                    if script.string is None:
                        continue
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        # Look for legal case data
                        if data.get('@type') in ['LegalCase', 'Case', 'CourtCase']:
                            result['case_name'] = data.get('name') or data.get('caseName')
                            result['date'] = self._extract_date_from_value(data.get('datePublished') or data.get('dateDecided'))
                            result['court'] = data.get('court') or data.get('courtName')
                            result['docket_number'] = data.get('docketNumber')
                            break
                except (json.JSONDecodeError, TypeError):
                    continue
            
            # Microdata extraction
            if not result.get('case_name'):
                case_name_elem = soup.find(attrs={'itemprop': 'name'}) or soup.find(attrs={'itemprop': 'caseName'})
                if case_name_elem:
                    result['case_name'] = case_name_elem.get_text(strip=True)
            
            if not result.get('date'):
                date_elem = soup.find(attrs={'itemprop': 'datePublished'}) or soup.find(attrs={'itemprop': 'dateDecided'})
                if date_elem:
                    result['date'] = self._extract_date_from_value(date_elem.get_text(strip=True))
            
            if not result.get('court'):
                court_elem = soup.find(attrs={'itemprop': 'court'}) or soup.find(attrs={'itemprop': 'courtName'})
                if court_elem:
                    result['court'] = court_elem.get_text(strip=True)
        
        except Exception as e:
            self.logger.debug(f"Structured data extraction failed: {e}")
        
        return result

    def _extract_html_metadata(self, soup) -> Dict[str, Any]:
        """Extract case information from HTML metadata."""
        result = {}
        
        try:
            # Meta tags
            meta_mappings = {
                'case_name': ['og:title', 'twitter:title', 'citation', 'case-name', 'title'],
                'date': ['og:published_time', 'article:published_time', 'date', 'publication-date'],
                'court': ['court', 'jurisdiction', 'og:site_name']
            }
            
            for field, meta_names in meta_mappings.items():
                for meta_name in meta_names:
                    meta_tag = (soup.find('meta', {'name': meta_name}) or 
                               soup.find('meta', {'property': meta_name}) or
                               soup.find('meta', {'itemprop': meta_name}))
                    if meta_tag and meta_tag.get('content'):
                        content = meta_tag.get('content', '').strip()
                        if content:
                            if field == 'date':
                                result[field] = self._extract_date_from_value(content)
                            else:
                                result[field] = content
                            break
            
            # Title tag fallback
            if not result.get('case_name'):
                title_tag = soup.find('title')
                if title_tag:
                    title_text = title_tag.get_text(strip=True)
                    # Clean common title suffixes
                    title_text = re.sub(r'\s*[\|\-–—]\s*.*', '', title_text)
                    if len(title_text) > 10 and ('v.' in title_text or 'vs.' in title_text):
                        result['case_name'] = title_text
        
        except Exception as e:
            self.logger.debug(f"HTML metadata extraction failed: {e}")
        
        return result

    def _extract_semantic_html(self, soup, citation: str) -> Dict[str, Any]:
        """Extract case information from semantic HTML structure."""
        result = {}
        
        try:
            # Look for common semantic patterns
            semantic_selectors = {
                'case_name': [
                    'h1.case-title', 'h1.title', 'h1.case-name', '.case-title h1',
                    'h2.case-title', 'h2.title', '.case-header h1', '.case-header h2',
                    '.opinion-title', '.case-caption', '.document-title',
                    '[class*="case"][class*="name"]', '[class*="case"][class*="title"]'
                ],
                'date': [
                    '.date', '.publication-date', '.filed-date', '.decided-date',
                    '.case-date', '.opinion-date', '[class*="date"]',
                    'time', '.dateline', '.case-info .date'
                ],
                'court': [
                    '.court', '.jurisdiction', '.court-name', '.tribunal',
                    '.case-court', '.opinion-court', '[class*="court"]'
                ],
                'docket_number': [
                    '.docket', '.docket-number', '.case-number', '.file-number',
                    '[class*="docket"]', '[class*="case-num"]'
                ]
            }
            
            for field, selectors in semantic_selectors.items():
                for selector in selectors:
                    try:
                        elements = soup.select(selector)
                        for elem in elements:
                            text = elem.get_text(strip=True)
                            if text and len(text) > 3:
                                if field == 'case_name':
                                    # Validate case name
                                    if any(pattern in text.lower() for pattern in ['v.', 'vs.', 'versus', 'in re', 'ex parte']):
                                        result[field] = text
                                        break
                                elif field == 'date':
                                    extracted_date = self._extract_date_from_value(text)
                                    if extracted_date:
                                        result[field] = extracted_date
                                        break
                                else:
                                    result[field] = text
                                    break
                        if result.get(field):
                            break
                    except Exception:
                        continue
            
            # Context-based extraction near citation
            if citation and not result.get('case_name'):
                # Find citation in text and look for case name nearby
                text_content = soup.get_text()
                citation_index = text_content.find(citation)
                if citation_index > 0:
                    # Look in the 500 characters before the citation
                    context = text_content[max(0, citation_index - 500):citation_index]
                    for pattern in self.case_name_patterns:
                        match = re.search(pattern, context, re.IGNORECASE)
                        if match:
                            potential_name = match.group(1).strip()
                            if len(potential_name) > 10:
                                result['case_name'] = potential_name
                                break
        
        except Exception as e:
            self.logger.debug(f"Semantic HTML extraction failed: {e}")
        
        return result

    def _extract_from_text_patterns(self, text: str, citation: str) -> Dict[str, Any]:
        """Extract information using advanced text patterns."""
        result = {}
        
        try:
            # Enhanced case name extraction
            if not result.get('case_name'):
                for pattern in self.case_name_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        # Take the longest, most complete match
                        best_match = max(matches, key=len)
                        if len(best_match) > 10:
                            result['case_name'] = re.sub(r'\s+', ' ', best_match.strip())
                            break
            
            # Enhanced date extraction with context
            if not result.get('date'):
                date_patterns = [
                    r'(?:decided|filed|issued|released|argued|submitted|entered).*?(\w+\s+\d{1,2},\s+\d{4})',
                    r'(?:decided|filed|issued|released|argued|submitted|entered).*?(\d{4})',
                    r'(\w+\s+\d{1,2},\s+\d{4})',
                    r'\((\d{4})\)',
                    r'\b(19|20)\d{2}\b'
                ]
                
                for pattern in date_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    for match in matches:
                        date_value = self._extract_date_from_value(match)
                        if date_value:
                            result['date'] = date_value
                            break
                    if result.get('date'):
                        break
            
            # Court extraction
            if not result.get('court'):
                court_patterns = [
                    r'(?:Supreme Court|Court of Appeals|District Court|Circuit Court|Superior Court|Municipal Court|Appellate Court|Trial Court|Family Court|Probate Court)\s+(?:of\s+)?(?:the\s+)?([A-Za-z\s]+)',
                    r'([A-Za-z\s]+)\s+(?:Supreme Court|Court of Appeals|District Court|Circuit Court|Superior Court)',
                    r'United States\s+(Supreme Court|Court of Appeals|District Court)',
                    r'(Washington|California|New York|Texas|Florida|Illinois)\s+(?:State\s+)?(?:Supreme\s+)?Court'
                ]
                
                for pattern in court_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        result['court'] = match.group(0).strip()
                        break
        
        except Exception as e:
            self.logger.debug(f"Text pattern extraction failed: {e}")
        
        return result

    def _extract_from_url(self, url: str, citation: str) -> Dict[str, Any]:
        """Extract information from URL structure."""
        result = {}
        
        try:
            from urllib.parse import urlparse, unquote
            parsed = urlparse(url)
            path = unquote(parsed.path)
            
            # Extract year from URL path
            year_match = re.search(r'/(\d{4})/', path)
            if year_match:
                result['date'] = year_match.group(1)
            
            # Extract court from domain or path
            domain = parsed.netloc.lower()
            if 'supreme' in domain:
                result['court'] = 'Supreme Court'
            elif 'appeals' in domain or 'appellate' in domain:
                result['court'] = 'Court of Appeals'
            elif 'district' in domain:
                result['court'] = 'District Court'
            
            # State-specific courts from domain
            state_domains = {
                'courts.wa.gov': 'Washington State Court',
                'courts.ca.gov': 'California State Court',
                'nycourts.gov': 'New York State Court',
                'txcourts.gov': 'Texas State Court'
            }
            
            for state_domain, court_name in state_domains.items():
                if state_domain in domain:
                    result['court'] = court_name
                    break
        
        except Exception as e:
            self.logger.debug(f"URL extraction failed: {e}")
        
        return result

    def _extract_date_from_value(self, value: str) -> Optional[str]:
        """Enhanced date extraction with multiple format support."""
        if not value:
            return None
        
        try:
            # Clean the value
            value = re.sub(r'[^\w\s\-\/\.,:]', '', value).strip()
            
            # Try various date formats
            date_formats = [
                '%Y-%m-%d',           # 2023-01-15
                '%m/%d/%Y',           # 01/15/2023
                '%d/%m/%Y',           # 15/01/2023
                '%B %d, %Y',          # January 15, 2023
                '%b %d, %Y',          # Jan 15, 2023
                '%B %d %Y',           # January 15 2023
                '%b %d %Y',           # Jan 15 2023
                '%Y',                 # 2023
            ]
            
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(value, fmt)
                    return str(parsed_date.year)  # Return just the year
                except ValueError:
                    continue
            
            # Extract year with regex as fallback
            year_match = re.search(r'\b(19|20)\d{2}\b', value)
            if year_match:
                return year_match.group(0)
        
        except Exception as e:
            self.logger.debug(f"Date extraction failed for '{value}': {e}")
        
        return None

class EnhancedWebSearcher:
    """
    Enhanced web searcher for legal citations with intelligent method prioritization.
    """
    
    def __init__(self):
        self.session = None
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour
        self.extractor = EnhancedWebExtractor()
        self.logger = logging.getLogger(__name__)
        
        # Method statistics for optimization
        self.method_stats = {
            'justia': {'success': 0, 'total': 0, 'avg_time': 0},
            'findlaw': {'success': 0, 'total': 0, 'avg_time': 0},
            'courtlistener_web': {'success': 0, 'total': 0, 'avg_time': 0},
            'leagle': {'success': 0, 'total': 0, 'avg_time': 0},
            'openjurist': {'success': 0, 'total': 0, 'avg_time': 0},
            'casemine': {'success': 0, 'total': 0, 'avg_time': 0},
            'casetext': {'success': 0, 'total': 0, 'avg_time': 0},
            'vlex': {'success': 0, 'total': 0, 'avg_time': 0},
            'google_scholar': {'success': 0, 'total': 0, 'avg_time': 0},
            'bing': {'success': 0, 'total': 0, 'avg_time': 0},
            'duckduckgo': {'success': 0, 'total': 0, 'avg_time': 0}
        }
        
        # Rate limiting
        self.rate_limits = {
            'justia': {'requests': 0, 'last_request': 0, 'max_per_minute': 30},
            'findlaw': {'requests': 0, 'last_request': 0, 'max_per_minute': 20},
            'courtlistener_web': {'requests': 0, 'last_request': 0, 'max_per_minute': 30},
            'leagle': {'requests': 0, 'last_request': 0, 'max_per_minute': 20},
            'openjurist': {'requests': 0, 'last_request': 0, 'max_per_minute': 20},
            'casemine': {'requests': 0, 'last_request': 0, 'max_per_minute': 15},
            'casetext': {'requests': 0, 'last_request': 0, 'max_per_minute': 15},
            'vlex': {'requests': 0, 'last_request': 0, 'max_per_minute': 15},
            'google_scholar': {'requests': 0, 'last_request': 0, 'max_per_minute': 10},
            'bing': {'requests': 0, 'last_request': 0, 'max_per_minute': 20},
            'duckduckgo': {'requests': 0, 'last_request': 0, 'max_per_minute': 20}
        }
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=15),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _respect_rate_limit(self, method: str) -> bool:
        """Check and update rate limits."""
        now = time.time()
        limit_info = self.rate_limits.get(method, {'requests': 0, 'last_request': 0, 'max_per_minute': 10})
        if now - limit_info['last_request'] < 60 / limit_info['max_per_minute']:
            return False
        limit_info['last_request'] = now
        return True
    
    def _update_stats(self, method: str, success: bool, duration: float):
        """Update method statistics."""
        if method not in self.method_stats:
            self.method_stats[method] = {'success': 0, 'total': 0, 'avg_time': 0}
        
        stats = self.method_stats[method]
        stats['total'] += 1
        if success:
            stats['success'] += 1
        stats['avg_time'] = (stats['avg_time'] * (stats['total'] - 1) + duration) / stats['total']

    async def search_justia(self, citation: str, case_name: str = None) -> Dict:
        """Enhanced Justia search with multiple strategies."""
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
            
            # Strategy 2: Citation search
            search_urls.append(f"https://law.justia.com/search?query={quote_plus(citation)}")
            
            # Strategy 3: Citation + case name
            if case_name:
                search_urls.append(f"https://law.justia.com/search?query={quote_plus(f'{citation} {case_name}')}")
            
            # Strategy 4: Cases section search
            search_urls.append(f"https://law.justia.com/cases/search?query={quote_plus(citation)}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive'
            }
            
            for url in search_urls:
                try:
                    async with self.session.get(url, headers=headers, timeout=10) as response:
                        if response.status == 200:
                            content = await response.text()
                            
                            # Use extractor for comprehensive analysis
                            result = self.extractor.extract_from_page_content(content, url, citation)
                            if result.get('case_name'):
                                duration = time.time() - start_time
                                self._update_stats('justia', True, duration)
                                result['confidence'] = 0.9  # High confidence for Justia
                                result['verified'] = True
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
                    
                    async with self.session.get(url, headers=headers, timeout=15) as response:
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
                                            async with self.session.get(case_url, headers=headers, timeout=10) as case_response:
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
                    async with self.session.get(url, headers=headers, timeout=15) as response:
                        if response.status == 200:
                            content = await response.text()
                            
                            # Check if citation is present
                            if re.search(re.escape(citation), content, re.IGNORECASE):
                                # Try to extract from current page first
                                extracted_data = self.extractor.extract_from_page_content(content, str(response.url), citation)
                                
                                if extracted_data.get('case_name'):
                                    duration = time.time() - start_time
                                    self._update_stats('findlaw', True, duration)
                                    
                                    return {
                                        'case_name': extracted_data['case_name'],
                                        'date': extracted_data.get('date'),
                                        'court': extracted_data.get('court'),
                                        'docket_number': extracted_data.get('docket_number'),
                                        'url': extracted_data['canonical_url'],
                                        'source': 'FindLaw (Enhanced)',
                                        'confidence': min(0.85, 0.4 + extracted_data.get('confidence', 0)),
                                        'verified': True
                                    }
                
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
            from urllib.parse import quote_plus
            search_url = f"https://www.leagle.com/leaglesearch?cite={quote_plus(citation)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive',
                'Referer': 'https://www.leagle.com/'
            }
            async with self.session.get(search_url, headers=headers, timeout=15) as response:
                if response.status == 200:
                    content = await response.text()
                    extracted = self.extractor.extract_from_page_content(content, str(response.url), citation)
                    if extracted.get('case_name'):
                        duration = time.time() - start_time
                        self._update_stats('leagle', True, duration)
                        return {
                            'case_name': extracted['case_name'],
                            'date': extracted.get('date'),
                            'court': extracted.get('court'),
                            'url': extracted['canonical_url'],
                            'source': 'Leagle (Enhanced)',
                            'confidence': min(0.8, 0.4 + extracted.get('confidence', 0)),
                            'verified': True
                        }
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
            from urllib.parse import quote_plus
            query = f'"{citation}"'
            if case_name:
                query += f' "{case_name}"'
            search_url = f"https://openjurist.org/search?q={quote_plus(query)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive'
            }
            async with self.session.get(search_url, headers=headers, timeout=15) as response:
                if response.status == 200:
                    content = await response.text()
                    extracted = self.extractor.extract_from_page_content(content, str(response.url), citation)
                    if extracted.get('case_name'):
                        duration = time.time() - start_time
                        self._update_stats('openjurist', True, duration)
                        return {
                            'case_name': extracted['case_name'],
                            'date': extracted.get('date'),
                            'court': extracted.get('court'),
                            'url': extracted['canonical_url'],
                            'source': 'OpenJurist (Enhanced)',
                            'confidence': min(0.7, 0.4 + extracted.get('confidence', 0)),
                            'verified': True
                        }
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
            from urllib.parse import quote_plus
            query = f'"{citation}"'
            if case_name:
                query += f' "{case_name}"'
            search_url = f"https://www.casemine.com/search?q={quote_plus(query)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive'
            }
            async with self.session.get(search_url, headers=headers, timeout=15) as response:
                if response.status == 200:
                    content = await response.text()
                    extracted = self.extractor.extract_from_page_content(content, str(response.url), citation)
                    if extracted.get('case_name'):
                        duration = time.time() - start_time
                        self._update_stats('casemine', True, duration)
                        return {
                            'case_name': extracted['case_name'],
                            'date': extracted.get('date'),
                            'court': extracted.get('court'),
                            'url': extracted['canonical_url'],
                            'source': 'CaseMine (Enhanced)',
                            'confidence': min(0.7, 0.4 + extracted.get('confidence', 0)),
                            'verified': True
                        }
            duration = time.time() - start_time
            self._update_stats('casemine', False, duration)
            return {'verified': False, 'error': 'Citation not found'}
        except Exception as e:
            duration = time.time() - start_time
            self._update_stats('casemine', False, duration)
            logger.debug(f"CaseMine search failed: {e}")
            return {'verified': False, 'error': str(e)}

    async def search_casetext(self, citation: str, case_name: str = None) -> Dict:
        """Enhanced Casetext search with advanced extraction."""
        if not self._respect_rate_limit('casetext'):
            return {'verified': False, 'error': 'Rate limited'}
        start_time = time.time()
        try:
            from urllib.parse import quote_plus
            query = f'"{citation}"'
            if case_name:
                query += f' "{case_name}"'
            search_url = f"https://casetext.com/search?q={quote_plus(query)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive'
            }
            async with self.session.get(search_url, headers=headers, timeout=15) as response:
                if response.status == 200:
                    content = await response.text()
                    extracted = self.extractor.extract_from_page_content(content, str(response.url), citation)
                    if extracted.get('case_name'):
                        duration = time.time() - start_time
                        self._update_stats('casetext', True, duration)
                        return {
                            'case_name': extracted['case_name'],
                            'date': extracted.get('date'),
                            'court': extracted.get('court'),
                            'url': extracted['canonical_url'],
                            'source': 'Casetext (Enhanced)',
                            'confidence': min(0.7, 0.4 + extracted.get('confidence', 0)),
                            'verified': True
                        }
            duration = time.time() - start_time
            self._update_stats('casetext', False, duration)
            return {'verified': False, 'error': 'Citation not found'}
        except Exception as e:
            duration = time.time() - start_time
            self._update_stats('casetext', False, duration)
            logger.debug(f"Casetext search failed: {e}")
            return {'verified': False, 'error': str(e)}

    async def search_vlex(self, citation: str, case_name: str = None) -> Dict:
        """Enhanced vLex search with advanced extraction."""
        if not self._respect_rate_limit('vlex'):
            return {'verified': False, 'error': 'Rate limited'}
        start_time = time.time()
        try:
            from urllib.parse import quote_plus
            query = f'"{citation}"'
            if case_name:
                query += f' "{case_name}"'
            search_url = f"https://vlex.com/search?q={quote_plus(query)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive'
            }
            async with self.session.get(search_url, headers=headers, timeout=15) as response:
                if response.status == 200:
                    content = await response.text()
                    extracted = self.extractor.extract_from_page_content(content, str(response.url), citation)
                    if extracted.get('case_name'):
                        duration = time.time() - start_time
                        self._update_stats('vlex', True, duration)
                        return {
                            'case_name': extracted['case_name'],
                            'date': extracted.get('date'),
                            'court': extracted.get('court'),
                            'url': extracted['canonical_url'],
                            'source': 'vLex (Enhanced)',
                            'confidence': min(0.7, 0.4 + extracted.get('confidence', 0)),
                            'verified': True
                        }
            duration = time.time() - start_time
            self._update_stats('vlex', False, duration)
            return {'verified': False, 'error': 'Citation not found'}
        except Exception as e:
            duration = time.time() - start_time
            self._update_stats('vlex', False, duration)
            logger.debug(f"vLex search failed: {e}")
            return {'verified': False, 'error': str(e)}

    async def search_google_scholar(self, citation: str, case_name: str = None) -> Dict:
        """Enhanced Google Scholar search with advanced extraction and defensive checks."""
        if not self._respect_rate_limit('google_scholar'):
            return {'verified': False, 'error': 'Rate limited'}
        
        start_time = time.time()
        try:
            from urllib.parse import quote_plus
            query = f'"{citation}"'
            if case_name:
                query += f' "{case_name}"'
            search_url = f"https://scholar.google.com/scholar?q={quote_plus(query)}&hl=en&as_sdt=0%2C48&as_vis=1"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive'
            }
            
            await asyncio.sleep(2)  # Avoid rate limiting
            
            async with self.session.get(search_url, headers=headers, timeout=15) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # First, try to extract search results metadata (for linkrot scenarios)
                    search_results = self.extractor.extract_from_search_results(content, 'google')
                    
                    # Try to extract from the search page itself
                    extracted = self.extractor.extract_from_page_content(content, str(response.url), citation)
                    
                    if extracted.get('case_name'):
                        duration = time.time() - start_time
                        self._update_stats('google_scholar', True, duration)
                        return {
                            'case_name': extracted['case_name'],
                            'date': extracted.get('date'),
                            'court': extracted.get('court'),
                            'url': extracted['canonical_url'],
                            'source': 'Google Scholar (Enhanced)',
                            'confidence': min(0.8, 0.4 + extracted.get('confidence', 0)),
                            'verified': True,
                            'search_metadata': [result.to_dict() for result in search_results[:3]]
                        }
                    
                    # If no direct extraction, try search results metadata
                    if search_results:
                        best_result = self._find_best_search_result(search_results, citation, case_name)
                        if best_result:
                            case_info = best_result.extract_case_info()
                            if case_info.get('case_name'):
                                # Check if the URL is still accessible
                                url_status = await self._check_url_accessibility(best_result.url)
                                
                                duration = time.time() - start_time
                                self._update_stats('google_scholar', True, duration)
                                
                                result = {
                                    'case_name': case_info['case_name'],
                                    'date': case_info.get('date'),
                                    'court': case_info.get('court'),
                                    'url': best_result.url,
                                    'source': f'Google Scholar (Search Metadata)',
                                    'confidence': min(0.7, case_info.get('confidence', 0)),
                                    'verified': True,
                                    'search_metadata': [result.to_dict() for result in search_results[:3]],
                                    'extraction_method': 'search_engine_metadata'
                                }
                                
                                # Add URL accessibility information
                                if url_status['accessible']:
                                    result['url_status'] = 'accessible'
                                    result['confidence'] += 0.1
                                else:
                                    result['url_status'] = 'potentially_unavailable'
                                    result['source'] += ' (URL may be unavailable)'
                                    result['confidence'] -= 0.1
                                    result['url_warning'] = 'This URL was found in search results but may no longer be accessible'
                                
                                return result
                
                # Log the failure for debugging
                self.logger.debug(f"Google Scholar search failed for citation: {citation}, status: {response.status}")
                
            duration = time.time() - start_time
            self._update_stats('google_scholar', False, duration)
            return {'verified': False, 'error': 'Citation not found'}
            
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            self._update_stats('google_scholar', False, duration)
            self.logger.warning(f"Google Scholar search timeout for citation: {citation}")
            return {'verified': False, 'error': 'Timeout'}
        except Exception as e:
            duration = time.time() - start_time
            self._update_stats('google_scholar', False, duration)
            self.logger.error(f"Google Scholar search failed for citation {citation}: {e}")
            return {'verified': False, 'error': str(e)}

    async def search_bing(self, citation: str, case_name: str = None) -> Dict:
        """Enhanced Bing search with advanced extraction and defensive checks."""
        if not self._respect_rate_limit('bing'):
            return {'verified': False, 'error': 'Rate limited'}
        
        start_time = time.time()
        try:
            from urllib.parse import quote_plus
            query = f'"{citation}"'
            if case_name:
                query += f' "{case_name}"'
            search_url = f"https://www.bing.com/search?q={quote_plus(query)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive'
            }
            
            async with self.session.get(search_url, headers=headers, timeout=15) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # First, try to extract search results metadata (for linkrot scenarios)
                    search_results = self.extractor.extract_from_search_results(content, 'bing')
                    
                    # Try to extract from the search page itself
                    extracted = self.extractor.extract_from_page_content(content, str(response.url), citation)
                    
                    if extracted.get('case_name'):
                        duration = time.time() - start_time
                        self._update_stats('bing', True, duration)
                        return {
                            'case_name': extracted['case_name'],
                            'date': extracted.get('date'),
                            'court': extracted.get('court'),
                            'url': extracted['canonical_url'],
                            'source': 'Bing (Enhanced)',
                            'confidence': min(0.7, 0.4 + extracted.get('confidence', 0)),
                            'verified': True,
                            'search_metadata': [result.to_dict() for result in search_results[:3]]
                        }
                    
                    # If no direct extraction, try search results metadata
                    if search_results:
                        best_result = self._find_best_search_result(search_results, citation, case_name)
                        if best_result:
                            case_info = best_result.extract_case_info()
                            if case_info.get('case_name'):
                                # Check if the URL is still accessible
                                url_status = await self._check_url_accessibility(best_result.url)
                                
                                duration = time.time() - start_time
                                self._update_stats('bing', True, duration)
                                
                                result = {
                                    'case_name': case_info['case_name'],
                                    'date': case_info.get('date'),
                                    'court': case_info.get('court'),
                                    'url': best_result.url,
                                    'source': f'Bing (Search Metadata)',
                                    'confidence': min(0.6, case_info.get('confidence', 0)),
                                    'verified': True,
                                    'search_metadata': [result.to_dict() for result in search_results[:3]],
                                    'extraction_method': 'search_engine_metadata'
                                }
                                
                                # Add URL accessibility information
                                if url_status['accessible']:
                                    result['url_status'] = 'accessible'
                                    result['confidence'] += 0.1
                                else:
                                    result['url_status'] = 'potentially_unavailable'
                                    result['source'] += ' (URL may be unavailable)'
                                    result['confidence'] -= 0.1
                                    result['url_warning'] = 'This URL was found in search results but may no longer be accessible'
                                
                                return result
                
                # Log the failure for debugging
                self.logger.debug(f"Bing search failed for citation: {citation}, status: {response.status}")
                
            duration = time.time() - start_time
            self._update_stats('bing', False, duration)
            return {'verified': False, 'error': 'Citation not found'}
            
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            self._update_stats('bing', False, duration)
            self.logger.warning(f"Bing search timeout for citation: {citation}")
            return {'verified': False, 'error': 'Timeout'}
        except Exception as e:
            duration = time.time() - start_time
            self._update_stats('bing', False, duration)
            self.logger.error(f"Bing search failed for citation {citation}: {e}")
            return {'verified': False, 'error': str(e)}

    async def search_duckduckgo(self, citation: str, case_name: str = None) -> Dict:
        """Enhanced DuckDuckGo search with advanced extraction and defensive checks."""
        if not self._respect_rate_limit('duckduckgo'):
            return {'verified': False, 'error': 'Rate limited'}
        
        start_time = time.time()
        try:
            from urllib.parse import quote_plus
            query = f'"{citation}"'
            if case_name:
                query += f' "{case_name}"'
            search_url = f"https://duckduckgo.com/?q={quote_plus(query)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive'
            }
            
            async with self.session.get(search_url, headers=headers, timeout=15) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # First, try to extract search results metadata (for linkrot scenarios)
                    search_results = self.extractor.extract_from_search_results(content, 'duckduckgo')
                    
                    # Try to extract from the search page itself
                    extracted = self.extractor.extract_from_page_content(content, str(response.url), citation)
                    
                    if extracted.get('case_name'):
                        duration = time.time() - start_time
                        self._update_stats('duckduckgo', True, duration)
                        return {
                            'case_name': extracted['case_name'],
                            'date': extracted.get('date'),
                            'court': extracted.get('court'),
                            'url': extracted['canonical_url'],
                            'source': 'DuckDuckGo (Enhanced)',
                            'confidence': min(0.7, 0.4 + extracted.get('confidence', 0)),
                            'verified': True,
                            'search_metadata': [result.to_dict() for result in search_results[:3]]
                        }
                    
                    # If no direct extraction, try search results metadata
                    if search_results:
                        best_result = self._find_best_search_result(search_results, citation, case_name)
                        if best_result:
                            case_info = best_result.extract_case_info()
                            if case_info.get('case_name'):
                                # Check if the URL is still accessible
                                url_status = await self._check_url_accessibility(best_result.url)
                                
                                duration = time.time() - start_time
                                self._update_stats('duckduckgo', True, duration)
                                
                                result = {
                                    'case_name': case_info['case_name'],
                                    'date': case_info.get('date'),
                                    'court': case_info.get('court'),
                                    'url': best_result.url,
                                    'source': f'DuckDuckGo (Search Metadata)',
                                    'confidence': min(0.6, case_info.get('confidence', 0)),
                                    'verified': True,
                                    'search_metadata': [result.to_dict() for result in search_results[:3]],
                                    'extraction_method': 'search_engine_metadata'
                                }
                                
                                # Add URL accessibility information
                                if url_status['accessible']:
                                    result['url_status'] = 'accessible'
                                    result['confidence'] += 0.1
                                else:
                                    result['url_status'] = 'potentially_unavailable'
                                    result['source'] += ' (URL may be unavailable)'
                                    result['confidence'] -= 0.1
                                    result['url_warning'] = 'This URL was found in search results but may no longer be accessible'
                                
                                return result
                
                # Log the failure for debugging
                self.logger.debug(f"DuckDuckGo search failed for citation: {citation}, status: {response.status}")
                
            duration = time.time() - start_time
            self._update_stats('duckduckgo', False, duration)
            return {'verified': False, 'error': 'Citation not found'}
            
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            self._update_stats('duckduckgo', False, duration)
            self.logger.warning(f"DuckDuckGo search timeout for citation: {citation}")
            return {'verified': False, 'error': 'Timeout'}
        except Exception as e:
            duration = time.time() - start_time
            self._update_stats('duckduckgo', False, duration)
            self.logger.error(f"DuckDuckGo search failed for citation {citation}: {e}")
            return {'verified': False, 'error': str(e)}

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

    async def search_multiple_sources(self, citation: str, case_name: str = None, max_concurrent: int = 3) -> Dict:
        """Search multiple sources concurrently with intelligent prioritization and graceful fallbacks."""
        
        # Get prioritized methods based on historical success
        priority_methods = self.get_search_priority()
        
        # Limit concurrent searches
        methods_to_try = priority_methods[:max_concurrent]
        
        # Create search tasks
        tasks = []
        method_map = {
            'justia': self.search_justia,
            'findlaw': self.search_findlaw,
            'courtlistener_web': self.search_courtlistener_web,
            'leagle': self.search_leagle,
            'openjurist': self.search_openjurist,
            'casemine': self.search_casemine,
            'casetext': self.search_casetext,
            'vlex': self.search_vlex,
            'google_scholar': self.search_google_scholar,
            'bing': self.search_bing,
            'duckduckgo': self.search_duckduckgo,
        }
        
        for method in methods_to_try:
            if method in method_map:
                task = method_map[method](citation, case_name)
                tasks.append((method, task))
        
        # Execute tasks and return first successful result
        if tasks:
            try:
                # Use asyncio.gather to run all tasks concurrently
                results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
                
                # Check results in order of priority
                for i, (method, _) in enumerate(tasks):
                    if i < len(results):
                        result = results[i]
                        
                        # Handle exceptions gracefully
                        if isinstance(result, Exception):
                            self.logger.warning(f"Search method {method} failed with exception: {result}")
                            continue
                        
                        # Check if result is valid
                        if isinstance(result, dict) and result.get('verified'):
                            self.logger.info(f"Found citation via {method}: {result.get('case_name', 'N/A')}")
                            return result
                        
                        # Log non-successful results for debugging
                        elif isinstance(result, dict):
                            self.logger.debug(f"Search method {method} returned: {result.get('error', 'Unknown error')}")
                            
            except Exception as e:
                self.logger.error(f"Error in concurrent search: {e}")
        
        # If all methods fail, try a fallback approach
        return await self._fallback_search(citation, case_name)

    async def _fallback_search(self, citation: str, case_name: str = None) -> Dict:
        """Fallback search using simpler methods when all primary methods fail."""
        self.logger.info(f"Attempting fallback search for citation: {citation}")
        
        try:
            # Try a simple web search as last resort
            fallback_result = await self.search_bing(citation, case_name)
            if fallback_result.get('verified'):
                fallback_result['source'] = f"{fallback_result['source']} (Fallback)"
                return fallback_result
            
            # If still no success, return a structured failure response
            return {
                'verified': False,
                'error': 'All search methods failed',
                'citation': citation,
                'case_name': case_name,
                'attempted_methods': self.get_search_priority()[:5],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Fallback search failed: {e}")
            return {
                'verified': False,
                'error': f'Fallback search failed: {str(e)}',
                'citation': citation,
                'case_name': case_name
            }
    
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
            async with self.session.head(url, headers=headers, timeout=5, allow_redirects=True) as response:
                return {
                    'accessible': response.status < 400,
                    'status_code': response.status,
                    'error': None
                }
                
        except asyncio.TimeoutError:
            return {'accessible': False, 'status_code': None, 'error': 'Timeout'}
        except Exception as e:
            return {'accessible': False, 'status_code': None, 'error': str(e)} 