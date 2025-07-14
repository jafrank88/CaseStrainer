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
from .legal_database_scraper import LegalDatabaseScraper
from .websearch_utils import (
    create_legal_search_queries,
    search_google_py,
    search_bing_html,
    search_duckduckgo_api
)

class EnhancedLegalScraper:
    """Enhanced scraper that uses search engines to find case detail pages."""
    
    def __init__(self, use_duckduckgo: bool = True, use_google: bool = True, use_bing: bool = True, cache_results: bool = True):
        """
        Initialize the enhanced legal scraper.
        
        Args:
            use_duckduckgo: Whether to use DuckDuckGo search
            use_google: Whether to use Google search
            use_bing: Whether to use Bing search
            cache_results: Whether to cache search results
        """
        self.logger = logging.getLogger(__name__)
        self.use_duckduckgo = use_duckduckgo
        self.use_google = use_google
        self.use_bing = use_bing
        self.cache_results = cache_results
        
        # Initialize DuckDuckGo
        try:
            from duckduckgo_search import DDGS
            self.ddgs = DDGS
            self.duckduckgo_available = True
        except ImportError:
            self.ddgs = None
            self.duckduckgo_available = False
            self.logger.warning("DuckDuckGo search not available - install duckduckgo-search package")
        
        # Initialize session for HTTP requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Initialize detail scraper
        self.detail_scraper = LegalDatabaseScraper()
        
        # Legal databases configuration
        self.legal_databases = {
            'courtlistener': {
                'domain': 'courtlistener.com',
                'detail_patterns': ['/opinion/', '/cluster/'],
                'name': 'CourtListener'
            },
            'justia': {
                'domain': 'justia.com',
                'detail_patterns': ['/cases/', '/opinions/'],
                'name': 'Justia'
            },
            'findlaw': {
                'domain': 'findlaw.com',
                'detail_patterns': ['/caselaw/', '/opinions/'],
                'name': 'FindLaw'
            },
            'casetext': {
                'domain': 'casetext.com',
                'detail_patterns': ['/case/', '/opinion/'],
                'name': 'CaseText'
            },
            'leagle': {
                'domain': 'leagle.com',
                'detail_patterns': ['/case/', '/opinion/'],
                'name': 'Leagle'
            },
            'supreme_court': {
                'domain': 'supreme.justia.com',
                'detail_patterns': ['/cases/', '/opinions/'],
                'name': 'Supreme Court'
            },
            'cornell': {
                'domain': 'law.cornell.edu',
                'detail_patterns': ['/supremecourt/', '/opinions/'],
                'name': 'Cornell Law'
            }
        }
    
    def search_for_case(self, citation: str, database_name: str) -> List[Dict[str, Any]]:
        """
        Search for a case on a specific legal database using search engines.
        First, try the two-step CourtListener process. Only if not verified, proceed to DuckDuckGo -> Bing -> Google.
        """
        if database_name not in self.legal_databases:
            self.logger.warning(f"Unknown database: {database_name}")
            return []
        # --- Two-step CourtListener process first ---
        try:
            from .enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
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
        # Use canonical query generator
        search_queries = create_legal_search_queries(citation, database_info)
        # 1. Try DuckDuckGo first
        if self.use_duckduckgo:
            for query in search_queries:
                results.extend(search_duckduckgo_api(query, num_results=5))
        # 2. Try Bing second
        if self.use_bing:
            for query in search_queries:
                results.extend(search_bing_html(query, num_results=5))
        # 3. Try Google as fallback
        if self.use_google:
            for query in search_queries:
                results.extend(search_google_py(query, num_results=5))
        # Filter and rank results
        filtered_results = self._filter_and_rank_results(results, database_info)
        return filtered_results
    
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
            from .enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
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