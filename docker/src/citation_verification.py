#!/usr/bin/env python3
"""
Citation Verification Module for CaseStrainer

This module provides comprehensive citation verification using multiple methods:
1. CourtListener Citation Lookup API
2. CourtListener Opinion Search API
3. CourtListener Cluster/Docket APIs
4. LangSearch API (backup)
5. Google Scholar (backup)

It implements a fallback mechanism to try different methods if one fails.
"""

import os
import re
import json
import time
import requests
import urllib.parse
from typing import Optional, Dict, Any, List, Tuple, Union
import traceback

# Import existing modules (copy them from old files if needed)
# These imports will be handled by moving the files later

# API endpoints
COURTLISTENER_CITATION_API = 'https://www.courtlistener.com/api/rest/v4/citation-lookup/'
COURTLISTENER_SEARCH_API = 'https://www.courtlistener.com/api/rest/v4/search/'
COURTLISTENER_OPINION_API = 'https://www.courtlistener.com/api/rest/v4/opinions/'
COURTLISTENER_CLUSTER_API = 'https://www.courtlistener.com/api/rest/v4/clusters/'
GOOGLE_SCHOLAR_URL = 'https://scholar.google.com/scholar'

# Flags to track API availability
COURTLISTENER_AVAILABLE = True
LANGSEARCH_AVAILABLE = True
GOOGLE_SCHOLAR_AVAILABLE = True

# Configuration
MAX_RETRIES = 5
TIMEOUT_SECONDS = 30

class CitationVerifier:
    """Class for verifying legal citations using multiple methods."""
    
    def __init__(self, api_key=None, langsearch_api_key=None):
        """Initialize the CitationVerifier with API keys."""
        self.api_key = api_key or os.environ.get('COURTLISTENER_API_KEY')
        self.langsearch_api_key = langsearch_api_key or os.environ.get('LANGSEARCH_API_KEY')
        self.headers = {
            'Authorization': f'Token {self.api_key}' if self.api_key else '',
            'Content-Type': 'application/json'
        }
    
    def verify_citation(self, citation: str) -> Dict[str, Any]:
        """
        Verify a citation using multiple methods with fallback.
        
        Args:
            citation: The legal citation to verify
            
        Returns:
            Dict with verification results including:
            - found: Whether the citation was found
            - source: Which source found the citation
            - case_name: Name of the case if found
            - details: Additional details about the case
            - url: Direct link to the case (if available)
        """
        result = {
            'citation': citation,
            'found': False,
            'source': None,
            'case_name': None,
            'url': None,
            'details': {}
        }
        
        # Try all methods in sequence until one succeeds
        try:
            # Method 1: CourtListener Citation Lookup API
            cl_result = self.verify_with_courtlistener_citation_api(citation)
            if cl_result.get('found'):
                result.update(cl_result)
                return result
                
            # Method 2: CourtListener Opinion Search API
            search_result = self.verify_with_courtlistener_search_api(citation)
            if search_result.get('found'):
                result.update(search_result)
                return result
                
            # Method 3: CourtListener Cluster/Docket APIs
            cluster_result = self.verify_with_courtlistener_cluster_api(citation)
            if cluster_result.get('found'):
                result.update(cluster_result)
                return result
                
            # Method 4: LangSearch API (backup)
            if LANGSEARCH_AVAILABLE and self.langsearch_api_key:
                lang_result = self.verify_with_langsearch_api(citation)
                if lang_result.get('found'):
                    result.update(lang_result)
                    return result
                    
            # Method 5: Google Scholar (backup)
            if GOOGLE_SCHOLAR_AVAILABLE:
                scholar_result = self.verify_with_google_scholar(citation)
                if scholar_result.get('found'):
                    result.update(scholar_result)
                    return result
        
        except Exception as e:
            print(f"Error verifying citation {citation}: {e}")
            traceback.print_exc()
        
        return result
    
    def verify_with_courtlistener_citation_api(self, citation: str) -> Dict[str, Any]:
        """
        Verify a citation using the CourtListener Citation Lookup API.
        
        Args:
            citation: The legal citation to verify
            
        Returns:
            Dict with verification results
        """
        result = {
            'citation': citation,
            'found': False,
            'source': 'CourtListener Citation API',
            'case_name': None,
            'details': {}
        }
        
        if not COURTLISTENER_AVAILABLE or not self.api_key:
            return result
        
        try:
            # Format citation for Washington state if needed
            formatted_citation = self._format_citation_for_courtlistener(citation)
            
            # Prepare the request
            data = {'text': formatted_citation}
            
            # Make the request with retries
            for attempt in range(MAX_RETRIES):
                try:
                    print(f"Sending request to {COURTLISTENER_CITATION_API}")
                    response = requests.post(
                        COURTLISTENER_CITATION_API, 
                        headers=self.headers, 
                        json=data,
                        timeout=TIMEOUT_SECONDS
                    )
                    
                    if response.status_code == 200:
                        api_result = response.json()
                        
                        # Check if the response is a list (newer API format)
                        if isinstance(api_result, list) and len(api_result) > 0:
                            item = api_result[0]
                            clusters = item.get('clusters', [])
                            
                            if clusters:
                                cluster = clusters[0]
                                result['found'] = True
                                result['case_name'] = cluster.get('case_name', 'Unknown Case')
                                result['url'] = f"https://www.courtlistener.com{cluster.get('absolute_url', '')}"
                                result['details'] = {
                                    'court': cluster.get('court', 'Unknown Court'),
                                    'date_filed': cluster.get('date_filed', 'Unknown Date'),
                                    'citations': [
                                        f"{cite.get('volume')} {cite.get('reporter')} {cite.get('page')}"
                                        for cite in cluster.get('citations', [])
                                    ]
                                }
                                return result
                        
                        # Check if the response has citations (older API format)
                        elif 'citations' in api_result:
                            for citation_result in api_result['citations']:
                                if citation_result.get('found', False):
                                    result['found'] = True
                                    result['case_name'] = citation_result.get('case_name', 'Unknown Case')
                                    result['url'] = citation_result.get('url', '')
                                    result['details'] = {
                                        'court': citation_result.get('court', 'Unknown Court'),
                                        'year': citation_result.get('year', 'Unknown Year'),
                                        'citation': citation_result.get('citation', citation)
                                    }
                                    return result
                    
                    # If we get here, the citation wasn't found
                    break
                    
                except requests.RequestException as e:
                    print(f"Request error (attempt {attempt+1}/{MAX_RETRIES}): {e}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        raise
        
        except Exception as e:
            print(f"Error in verify_with_courtlistener_citation_api: {e}")
            traceback.print_exc()
        
        return result
    
    def _format_citation_for_courtlistener(self, citation: str) -> str:
        """
        Format a citation for the CourtListener API, particularly for Washington state citations.
        
        Args:
            citation: The original citation
            
        Returns:
            Properly formatted citation
        """
        # Convert "Wash. 2d" format to "Wash. 2d" if needed
        wash_2d_pattern = r'(\d+)\s+Wash\.?\s*2d\s+(\d+)'
        wash_pattern = r'(\d+)\s+Wash\.?\s+(\d+)'
        wash_app_pattern = r'(\d+)\s+Wash\.?\s*App\.?\s+(\d+)'
        
        if re.search(wash_2d_pattern, citation, re.IGNORECASE):
            return re.sub(wash_2d_pattern, r'\1 Wash. 2d \2', citation, flags=re.IGNORECASE)
        elif re.search(wash_pattern, citation, re.IGNORECASE):
            return re.sub(wash_pattern, r'\1 Wash. \2', citation, flags=re.IGNORECASE)
        elif re.search(wash_app_pattern, citation, re.IGNORECASE):
            return re.sub(wash_app_pattern, r'\1 Wash. App. \2', citation, flags=re.IGNORECASE)
        
        return citation
    
    def verify_with_courtlistener_search_api(self, citation: str) -> Dict[str, Any]:
        """
        Verify a citation using the CourtListener Search API.
        This is a fallback when the Citation Lookup API doesn't find the case.
        
        Args:
            citation: The legal citation to verify
            
        Returns:
            Dict with verification results
        """
        result = {
            'citation': citation,
            'found': False,
            'source': 'CourtListener Search API',
            'case_name': None,
            'details': {}
        }
        
        if not COURTLISTENER_AVAILABLE or not self.api_key:
            return result
        
        try:
            # Format citation for search
            formatted_citation = self._format_citation_for_courtlistener(citation)
            
            # Extract components for better search
            citation_parts = self._extract_citation_parts(formatted_citation)
            
            # Build search query
            search_params = {
                'q': formatted_citation,
                'type': 'o',  # opinions only
                'order_by': 'score desc',
                'format': 'json'
            }
            
            # Add court filter for Washington state citations
            if citation_parts.get('reporter') in ['Wash.', 'Wash. 2d', 'Wash. App.']:
                search_params['court'] = 'wash washctapp washag washterr'
            
            # Make the request with retries
            for attempt in range(MAX_RETRIES):
                try:
                    print(f"Searching CourtListener for citation: {formatted_citation}")
                    response = requests.get(
                        COURTLISTENER_SEARCH_API, 
                        headers=self.headers, 
                        params=search_params,
                        timeout=TIMEOUT_SECONDS
                    )
                    
                    if response.status_code == 200:
                        search_results = response.json()
                        
                        if search_results.get('count', 0) > 0:
                            # Get the top result
                            top_result = search_results.get('results', [])[0]
                            
                            # Extract the opinion ID for further details
                            opinion_id = top_result.get('id')
                            if opinion_id:
                                opinion_details = self._get_opinion_details(opinion_id)
                                if opinion_details:
                                    result['found'] = True
                                    result['case_name'] = opinion_details.get('case_name', top_result.get('caseName', 'Unknown Case'))
                                    result['url'] = f"https://www.courtlistener.com{top_result.get('absolute_url', '')}"
                                    result['details'] = {
                                        'court': opinion_details.get('court_name', top_result.get('court', 'Unknown Court')),
                                        'date_filed': opinion_details.get('date_filed', top_result.get('dateFiled', 'Unknown Date')),
                                        'docket_number': opinion_details.get('docket_number', 'Unknown Docket')
                                    }
                                    return result
                    
                    # If we get here, the citation wasn't found
                    break
                    
                except requests.RequestException as e:
                    print(f"Request error (attempt {attempt+1}/{MAX_RETRIES}): {e}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        raise
        
        except Exception as e:
            print(f"Error in verify_with_courtlistener_search_api: {e}")
            traceback.print_exc()
        
        return result
    
    def _extract_citation_parts(self, citation: str) -> Dict[str, str]:
        """
        Extract the volume, reporter, and page from a citation.
        
        Args:
            citation: The citation to parse
            
        Returns:
            Dict with volume, reporter, and page
        """
        # Common patterns for citations
        patterns = [
            # Standard pattern: 123 U.S. 456
            r'(\d+)\s+([A-Za-z\.\s]+)\s+(\d+)',
            # Pattern with reporter in middle: 123 F. 2d 456
            r'(\d+)\s+([A-Za-z\.\s]+\d+[a-z]*\s+)\s*(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, citation)
            if match:
                return {
                    'volume': match.group(1),
                    'reporter': match.group(2).strip(),
                    'page': match.group(3)
                }
        
        # If no pattern matches, return empty dict
        return {}
    
    def _get_opinion_details(self, opinion_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about an opinion from the CourtListener API.
        
        Args:
            opinion_id: The ID of the opinion
            
        Returns:
            Dict with opinion details or None if not found
        """
        try:
            url = f"{COURTLISTENER_OPINION_API}{opinion_id}/"
            response = requests.get(url, headers=self.headers, timeout=TIMEOUT_SECONDS)
            
            if response.status_code == 200:
                opinion_data = response.json()
                
                # If the opinion has a cluster reference, get the cluster details
                cluster_ref = opinion_data.get('cluster')
                if isinstance(cluster_ref, str) and cluster_ref.startswith('http'):
                    # Extract cluster ID from URL
                    cluster_id = cluster_ref.rstrip('/').split('/')[-1]
                    cluster_data = self._get_cluster_details(cluster_id)
                    if cluster_data:
                        # Combine opinion and cluster data
                        return {**opinion_data, **cluster_data}
                
                return opinion_data
        
        except Exception as e:
            print(f"Error getting opinion details: {e}")
        
        return None
    
    def _get_cluster_details(self, cluster_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a cluster from the CourtListener API.
        
        Args:
            cluster_id: The ID of the cluster
            
        Returns:
            Dict with cluster details or None if not found
        """
        try:
            url = f"{COURTLISTENER_CLUSTER_API}{cluster_id}/"
            response = requests.get(url, headers=self.headers, timeout=TIMEOUT_SECONDS)
            
            if response.status_code == 200:
                return response.json()
        
        except Exception as e:
            print(f"Error getting cluster details: {e}")
        
        return None
    
    def verify_with_courtlistener_cluster_api(self, citation: str) -> Dict[str, Any]:
        """
        Verify a citation using the CourtListener Cluster API directly.
        This is a fallback when other CourtListener methods don't find the case.
        
        Args:
            citation: The legal citation to verify
            
        Returns:
            Dict with verification results
        """
        result = {
            'citation': citation,
            'found': False,
            'source': 'CourtListener Cluster API',
            'case_name': None,
            'details': {}
        }
        
        if not COURTLISTENER_AVAILABLE or not self.api_key:
            return result
        
        try:
            # For this method, we need to search for the cluster ID first
            # We'll use the search API but with different parameters
            formatted_citation = self._format_citation_for_courtlistener(citation)
            citation_parts = self._extract_citation_parts(formatted_citation)
            
            # Build more specific search query
            search_params = {
                'q': formatted_citation,
                'type': 'o',  # opinions only
                'order_by': 'score desc',
                'format': 'json'
            }
            
            # Add court filter for Washington state citations
            if citation_parts.get('reporter') in ['Wash.', 'Wash. 2d', 'Wash. App.']:
                search_params['court'] = 'wash washctapp washag washterr'
            
            # Add reporter filter if available
            if citation_parts.get('reporter'):
                search_params['reporter'] = citation_parts.get('reporter')
            
            # Make the request
            response = requests.get(
                COURTLISTENER_SEARCH_API, 
                headers=self.headers, 
                params=search_params,
                timeout=TIMEOUT_SECONDS
            )
            
            if response.status_code == 200:
                search_results = response.json()
                
                if search_results.get('count', 0) > 0:
                    # Get the top result
                    top_result = search_results.get('results', [])[0]
                    
                    # Extract the cluster ID
                    cluster_id = None
                    if 'cluster' in top_result:
                        cluster_url = top_result.get('cluster')
                        if isinstance(cluster_url, str) and cluster_url.startswith('http'):
                            cluster_id = cluster_url.rstrip('/').split('/')[-1]
                    
                    # If we found a cluster ID, get the details
                    if cluster_id:
                        cluster_data = self._get_cluster_details(cluster_id)
                        if cluster_data:
                            result['found'] = True
                            result['case_name'] = cluster_data.get('case_name', 'Unknown Case')
                            result['url'] = f"https://www.courtlistener.com{cluster_data.get('absolute_url', '')}"
                            result['details'] = {
                                'court': cluster_data.get('court_id', 'Unknown Court'),
                                'date_filed': cluster_data.get('date_filed', 'Unknown Date'),
                                'docket_number': cluster_data.get('docket_id', 'Unknown Docket'),
                                'precedential_status': cluster_data.get('precedential_status', 'Unknown')
                            }
                            
                            # Add citations if available
                            citations = cluster_data.get('citations', [])
                            if citations:
                                result['details']['citations'] = [
                                    f"{cite.get('volume')} {cite.get('reporter')} {cite.get('page')}"
                                    for cite in citations
                                ]
                            
                            return result
        
        except Exception as e:
            print(f"Error in verify_with_courtlistener_cluster_api: {e}")
            traceback.print_exc()
        
        return result
    
    def verify_with_langsearch_api(self, citation: str) -> Dict[str, Any]:
        """
        Verify a citation using the LangSearch API as a backup.
        
        Args:
            citation: The legal citation to verify
            
        Returns:
            Dict with verification results
        """
        result = {
            'citation': citation,
            'found': False,
            'source': 'LangSearch API',
            'case_name': None,
            'details': {}
        }
        
        if not LANGSEARCH_AVAILABLE or not self.langsearch_api_key:
            return result
        
        try:
            # LangSearch API endpoint
            api_url = 'https://api.langsearch.ai/v1/legal/case-summary'
            
            # Prepare the request
            headers = {
                'Authorization': f'Bearer {self.langsearch_api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'citation': citation,
                'include_full_text': False
            }
            
            # Make the request
            response = requests.post(api_url, headers=headers, json=data, timeout=TIMEOUT_SECONDS)
            
            if response.status_code == 200:
                api_result = response.json()
                
                # Check if the case was found
                if api_result.get('found', False):
                    result['found'] = True
                    result['case_name'] = api_result.get('case_name', 'Unknown Case')
                    result['url'] = api_result.get('url', '')  # LangSearch might provide a URL
                    result['details'] = {
                        'court': api_result.get('court', 'Unknown Court'),
                        'date': api_result.get('date', 'Unknown Date'),
                        'summary': api_result.get('summary', ''),
                        'source': 'LangSearch AI'
                    }
                    return result
        
        except Exception as e:
            print(f"Error in verify_with_langsearch_api: {e}")
            traceback.print_exc()
        
        return result
    
    def verify_with_google_scholar(self, citation: str) -> Dict[str, Any]:
        """
        Verify a citation using Google Scholar as a last resort.
        Note: This is a basic implementation and may be rate-limited by Google.
        
        Args:
            citation: The legal citation to verify
            
        Returns:
            Dict with verification results
        """
        result = {
            'citation': citation,
            'found': False,
            'source': 'Google Scholar',
            'case_name': None,
            'details': {}
        }
        
        if not GOOGLE_SCHOLAR_AVAILABLE:
            return result
        
        try:
            # Format the citation for search
            formatted_citation = self._format_citation_for_courtlistener(citation)  # Reuse this formatter
            
            # Prepare the search parameters
            params = {
                'q': f'"{formatted_citation}"',  # Exact match search
                'hl': 'en',
                'as_sdt': '0,5',  # Search only in case law
                'as_vis': '1'
            }
            
            # Set up headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5'
            }
            
            # Make the request
            response = requests.get(GOOGLE_SCHOLAR_URL, headers=headers, params=params, timeout=TIMEOUT_SECONDS)
            
            # Simple check if the citation appears in the results
            if response.status_code == 200 and formatted_citation in response.text:
                # Extract the first result title as case name (basic implementation)
                import re
                title_match = re.search(r'<h3 class="gs_rt">\s*<a[^>]*>([^<]+)</a>', response.text)
                case_name = title_match.group(1) if title_match else 'Unknown Case'
                
                result['found'] = True
                result['case_name'] = case_name
                result['url'] = f"{GOOGLE_SCHOLAR_URL}?{urllib.parse.urlencode(params)}"
                result['details'] = {
                    'source': 'Google Scholar',
                    'note': 'Limited information available from Google Scholar'
                }
                return result
        
        except Exception as e:
            print(f"Error in verify_with_google_scholar: {e}")
            traceback.print_exc()
        
        return result
