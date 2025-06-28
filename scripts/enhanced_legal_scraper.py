#!/usr/bin/env python3
"""
Enhanced Legal Database Scraper

This module provides an enhanced scraping system that uses search engines
(Google and Bing) to find deep links to case detail pages on legal databases,
then extracts comprehensive metadata from those pages.
"""

import requests
import re
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse, quote
from bs4 import BeautifulSoup
import json
import os
# Add googlesearch import
from googlesearch import search as google_search

# Import the existing scraper for detail page extraction
from src.legal_database_scraper import LegalDatabaseScraper

class EnhancedLegalScraper:
    """Enhanced scraper that uses search engines to find case detail pages."""
    
    def __init__(self, use_google: bool = True, use_bing: bool = True, cache_results: bool = True):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.use_google = use_google
        self.use_bing = use_bing
        self.cache_results = cache_results
        self.logger = logging.getLogger(__name__)
        
        # Initialize the detail page scraper
        self.detail_scraper = LegalDatabaseScraper()
        
        # Legal database domains and their search patterns
        self.legal_databases = {
            'vLex': {
                'domain': 'vlex.com',
                'search_patterns': ['vlex.com', 'vlex.com/sites'],
                'detail_patterns': ['vlex.com/sites', 'vlex.com/case']
            },
            'CaseMine': {
                'domain': 'casemine.com',
                'search_patterns': ['casemine.com'],
                'detail_patterns': ['casemine.com/judgement', 'casemine.com/case']
            },
            'Casetext': {
                'domain': 'casetext.com',
                'search_patterns': ['casetext.com'],
                'detail_patterns': ['casetext.com/case', 'casetext.com/decision']
            },
            'Leagle': {
                'domain': 'leagle.com',
                'search_patterns': ['leagle.com'],
                'detail_patterns': ['leagle.com/decision', 'leagle.com/case']
            },
            'Justia': {
                'domain': 'justia.com',
                'search_patterns': ['justia.com', 'law.justia.com'],
                'detail_patterns': ['justia.com/cases', 'law.justia.com/cases']
            },
            'FindLaw': {
                'domain': 'findlaw.com',
                'search_patterns': ['findlaw.com'],
                'detail_patterns': ['findlaw.com/caselaw', 'findlaw.com/case']
            },
            'OpenJurist': {
                'domain': 'openjurist.org',
                'search_patterns': ['openjurist.org'],
                'detail_patterns': ['openjurist.org']
            },
            'Harvard Caselaw': {
                'domain': 'case.law',
                'search_patterns': ['case.law'],
                'detail_patterns': ['case.law']
            },
            'Google Books': {
                'domain': 'books.google.com',
                'search_patterns': ['books.google.com'],
                'detail_patterns': ['books.google.com/books']
            }
        }
    
    def search_for_case(self, citation: str, database_name: str) -> List[Dict[str, Any]]:
        """
        Search for a case on a specific legal database using search engines.
        First, try the two-step CourtListener process. Only if not verified, proceed to Google/Bing.
        """
        if database_name not in self.legal_databases:
            self.logger.warning(f"Unknown database: {database_name}")
            return []
        
        # --- Two-step CourtListener process first ---
        try:
            from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
            verifier = EnhancedMultiSourceVerifier()
            cl_result = verifier.verify_citation_unified_workflow(citation)
            if cl_result.get("verified") and cl_result.get("url"):
                # Return as a search result format for downstream compatibility
                return [{
                    'title': cl_result.get('canonical_name', cl_result.get('case_name', '')),
                    'url': cl_result.get('url', ''),
                    'snippet': '',
                    'source': 'courtlistener',
                    'score': 100,
                    'is_detail_page': True
                }]
        except Exception as e:
            self.logger.error(f"CourtListener verification error: {e}")
        
        database_info = self.legal_databases[database_name]
        results = []
        # Create search queries for both Google and Bing
        search_queries = self._create_search_queries(citation, database_info)
        # Search using Google
        if self.use_google:
            google_results = self._search_google(search_queries)
            results.extend(google_results)
        # Search using Bing
        if self.use_bing:
            bing_results = self._search_bing(search_queries)
            results.extend(bing_results)
        # Filter and rank results
        filtered_results = self._filter_and_rank_results(results, database_info)
        return filtered_results
    
    def _create_search_queries(self, citation: str, database_info: Dict) -> List[str]:
        """Create search queries for the given citation and database."""
        queries = []
        
        # Basic citation search
        queries.append(f'"{citation}" site:{database_info["domain"]}')
        
        # Search with database name
        queries.append(f'"{citation}" {database_info["domain"]}')
        
        # Search with common legal terms
        queries.append(f'"{citation}" case law site:{database_info["domain"]}')
        
        # Search with "v." pattern (for case names)
        if 'v.' in citation or 'v ' in citation:
            # Extract potential case name
            case_name_match = re.search(r'([^0-9]+)\s+v\.?\s+([^0-9]+)', citation)
            if case_name_match:
                case_name = f"{case_name_match.group(1).strip()} v. {case_name_match.group(2).strip()}"
                queries.append(f'"{case_name}" site:{database_info["domain"]}')
        
        return queries
    
    def _search_google(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Search using googlesearch-python."""
        results = []
        for query in queries:
            try:
                for url in google_search(query, num_results=5):
                    results.append({
                        'title': '',  # googlesearch-python does not provide title
                        'url': url,
                        'snippet': '',
                        'source': 'google'
                    })
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Error searching Google: {e}")
        return results
    
    def _search_bing(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Search Bing by scraping HTML results (unofficial, fallback only)."""
        results = []
        for query in queries:
            try:
                url = f'https://www.bing.com/search?q={quote(query)}'
                resp = self.session.get(url, timeout=10)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, 'html.parser')
                for li in soup.select('li.b_algo'):
                    a = li.find('a', href=True)
                    if a:
                        title = a.get_text(strip=True)
                        link = a['href']
                        snippet = ''
                        desc = li.find('p')
                        if desc:
                            snippet = desc.get_text(strip=True)
                        results.append({
                            'title': title,
                            'url': link,
                            'snippet': snippet,
                            'source': 'bing'
                        })
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Error scraping Bing: {e}")
        return results
    
    def _filter_and_rank_results(self, results: List[Dict], database_info: Dict) -> List[Dict[str, Any]]:
        """Filter and rank search results to find the best case detail pages."""
        filtered_results = []
        
        for result in results:
            url = result.get('url', '')
            if not url:
                continue
            
            # Check if URL matches the database domain
            if database_info['domain'] not in url:
                continue
            
            # Check if URL looks like a detail page
            is_detail_page = any(pattern in url for pattern in database_info['detail_patterns'])
            
            # Score the result
            score = 0
            if is_detail_page:
                score += 10
            
            # Check if citation appears in title or snippet
            title = result.get('title', '').lower()
            snippet = result.get('snippet', '').lower()
            if 'case' in title or 'decision' in title:
                score += 5
            if 'law' in title or 'court' in title:
                score += 3
            
            result['score'] = score
            result['is_detail_page'] = is_detail_page
            
            if score > 0:  # Only include relevant results
                filtered_results.append(result)
        
        # Sort by score (highest first)
        filtered_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return filtered_results
    
    def extract_case_metadata(self, citation: str, database_name: str) -> Dict[str, Any]:
        """
        Extract comprehensive case metadata using search engines to find detail pages.
        First, try the two-step CourtListener process. Only if not verified, proceed to Google/Bing.
        """
        try:
            # --- Two-step CourtListener process first ---
            from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
            verifier = EnhancedMultiSourceVerifier()
            cl_result = verifier.verify_citation_unified_workflow(citation)
            if cl_result.get("verified") and cl_result.get("url"):
                return {
                    'canonical_name': cl_result.get('canonical_name', cl_result.get('case_name', '')),
                    'url': cl_result.get('url', ''),
                    'parallel_citations': cl_result.get('parallel_citations', []),
                    'year': cl_result.get('date_filed', ''),
                    'court': cl_result.get('court', ''),
                    'docket': cl_result.get('docket', ''),
                    'search_source': 'courtlistener',
                    'search_score': 100,
                    'search_results_count': 1,
                    'citation': citation,
                    'database': database_name
                }
        except Exception as e:
            self.logger.error(f"CourtListener verification error: {e}")
        # Fallback to search engines
        search_results = self.search_for_case(citation, database_name)
        if not search_results:
            self.logger.warning(f"No search results found for {citation} on {database_name}")
            return self._empty_result(citation, database_name)
        # Try the best result first
        best_result = search_results[0]
        detail_url = best_result['url']
        # Extract metadata from the detail page
        metadata = self.detail_scraper.extract_case_info(detail_url)
        # Add search result info
        metadata['search_source'] = best_result.get('source', 'unknown')
        metadata['search_score'] = best_result.get('score', 0)
        metadata['search_results_count'] = len(search_results)
        return metadata
    
    def extract_from_all_databases(self, citation: str) -> Dict[str, Dict[str, Any]]:
        """
        Extract case metadata from all supported legal databases.
        
        Args:
            citation: The citation to search for
            
        Returns:
            Dictionary mapping database names to their extracted metadata
        """
        results = {}
        
        for database_name in self.legal_databases.keys():
            self.logger.info(f"Searching {database_name} for citation: {citation}")
            
            try:
                metadata = self.extract_case_metadata(citation, database_name)
                if metadata.get('canonical_name'):  # Only include if we found something useful
                    results[database_name] = metadata
                
                time.sleep(2)  # Be respectful to search engines
                
            except Exception as e:
                self.logger.error(f"Error processing {database_name}: {e}")
                continue
        
        return results
    
    def _empty_result(self, citation: str, database_name: str) -> Dict[str, Any]:
        """Return an empty result structure."""
        return {
            'canonical_name': '',
            'url': '',
            'parallel_citations': [],
            'year': '',
            'court': '',
            'docket': '',
            'search_source': '',
            'search_score': 0,
            'search_results_count': 0,
            'citation': citation,
            'database': database_name
        }
    
    def get_supported_databases(self) -> List[str]:
        """Get list of supported legal databases."""
        return list(self.legal_databases.keys())
    
    def get_database_info(self, database_name: str) -> List[str]:
        """Get information about a specific database."""
        return self.legal_databases.get(database_name, {}) 