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
import logging

# Import existing modules (copy them from old files if needed)
# These imports will be handled by moving the files later

# API endpoints
COURTLISTENER_CITATION_API = 'https://www.courtlistener.com/api/rest/v4/citation-lookup/'
COURTLISTENER_SEARCH_API = 'https://www.courtlistener.com/api/rest/v4/search/'
COURTLISTENER_OPINION_API = 'https://www.courtlistener.com/api/rest/v4/opinions/'
COURTLISTENER_CLUSTER_API = 'https://www.courtlistener.com/api/rest/v4/clusters/'

# Note: CourtListener API v4 requires specific parameters
# For citation-lookup, we need to use 'citation' parameter
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
        
        # Add more detailed logging for API key
        if self.api_key:
            print(f"DEBUG: Using CourtListener API key: {self.api_key[:6]}... (length: {len(self.api_key)})")
            logging.info(f"DEBUG: Using CourtListener API key: {self.api_key[:6]}... (length: {len(self.api_key)})")
        else:
            print("WARNING: No CourtListener API key provided!")
            logging.warning("WARNING: No CourtListener API key provided!")
        
        self.headers = {
            'Authorization': f'Token {self.api_key}' if self.api_key else '',
            'Content-Type': 'application/json'
        }
        
        # Log the full headers (without the full token)
        headers_log = self.headers.copy()
        if 'Authorization' in headers_log and headers_log['Authorization']:
            auth_parts = headers_log['Authorization'].split(' ')
            if len(auth_parts) > 1:
                headers_log['Authorization'] = f"{auth_parts[0]} {auth_parts[1][:6]}..."
        
        print(f"DEBUG: Request headers: {headers_log}")
        logging.info(f"DEBUG: Request headers: {headers_log}")
        
        logger.info(f"Initialized CitationVerifier with API key: {self.api_key[:6]}... (length: {len(self.api_key) if self.api_key else 0})")
        print(f"Initialized CitationVerifier with API key: {self.api_key[:6]}... (length: {len(self.api_key) if self.api_key else 0})")
    
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
            - explanation: Explanation of verification result
        """
        print(f"DEBUG: Starting verification for citation: {citation}")
        logging.info(f"[DEBUG] Starting verification for citation: {citation}")
        
        # Check if this is a Westlaw citation
        is_westlaw = bool(re.search(r'\d+\s+WL\s+\d+', citation, re.IGNORECASE))
        
        result = {
            'citation': citation,
            'found': False,
            'source': None,
            'case_name': None,
            'url': None,
            'details': {},
            'explanation': None,
            'is_westlaw': is_westlaw
        }
        
        # Special handling for Westlaw citations
        if is_westlaw:
            logging.info(f"[DEBUG] Detected Westlaw citation: {citation}")
            print(f"DEBUG: Detected Westlaw citation: {citation}")
            # Try to extract year from Westlaw citation
            year_match = re.search(r'(\d{4})\s+WL', citation)
            if year_match:
                result['details']['year'] = year_match.group(1)
                logging.info(f"[DEBUG] Extracted year from Westlaw citation: {result['details']['year']}")
            
            # Add explanation for Westlaw citations
            result['explanation'] = "Westlaw citations require subscription access and may not be verifiable through public APIs."
            
            # We'll still try to verify with CourtListener, but with lower expectations
        try:
            logging.info("[DEBUG] Trying CourtListener Citation Lookup API...")
            print("DEBUG: Trying CourtListener Citation Lookup API...")
            cl_result = self.verify_with_courtlistener_citation_api(citation)
            logging.info(f"[DEBUG] CourtListener Citation Lookup API result: {cl_result}")
            print(f"DEBUG: CourtListener Citation Lookup API result: {cl_result}")
            if cl_result.get('found'):
                result.update(cl_result)
                logging.info("[DEBUG] Citation verified by CourtListener Citation Lookup API.")
                print("DEBUG: Citation verified by CourtListener Citation Lookup API.")
                return result
            logging.info("[DEBUG] Trying CourtListener Search API...")
            print("DEBUG: Trying CourtListener Search API...")
            search_result = self.verify_with_courtlistener_search_api(citation)
            logging.info(f"[DEBUG] CourtListener Search API result: {search_result}")
            print(f"DEBUG: CourtListener Search API result: {search_result}")
            if search_result.get('found'):
                result.update(search_result)
                logging.info("[DEBUG] Citation verified by CourtListener Search API.")
                print("DEBUG: Citation verified by CourtListener Search API.")
                return result
            
            # If we get here, neither method found the citation
            if not result.get('explanation'):
                # Check for common citation patterns to provide better explanations
                if re.search(r'\d+\s+F\.\s*Supp', citation):
                    result['explanation'] = "Federal District Court opinions may have limited availability in free databases."
                elif re.search(r'\d+\s+F\.\d+d', citation):
                    result['explanation'] = "This appears to be a Federal Circuit Court citation. Verification failed, possibly due to database limitations."
                elif re.search(r'\d+\s+S\.\s*Ct', citation):
                    result['explanation'] = "This appears to be a Supreme Court citation. Verification failed, possibly due to database limitations."
                elif re.search(r'\d+\s+U\.\s*S', citation):
                    result['explanation'] = "This appears to be a U.S. Reports citation. Verification failed, possibly due to database limitations."
                elif re.search(r'Id\.', citation, re.IGNORECASE):
                    result['explanation'] = "'Id.' citations refer to the immediately preceding citation and cannot be verified independently."
                elif re.search(r'supra', citation, re.IGNORECASE):
                    result['explanation'] = "'Supra' citations refer to earlier citations in the document and cannot be verified independently."
                elif re.search(r'\d+\s+P\.\d+d', citation):
                    result['explanation'] = "This appears to be a Pacific Reporter citation. Verification failed, possibly due to database limitations."
                else:
                    result['explanation'] = "Citation could not be verified through available APIs. This may be due to database limitations or an uncommon citation format."
            logging.info("[DEBUG] Trying CourtListener Cluster/Docket APIs...")
            print("DEBUG: Trying CourtListener Cluster/Docket APIs...")
            cluster_result = self.verify_with_courtlistener_cluster_api(citation)
            logging.info(f"[DEBUG] CourtListener Cluster/Docket APIs result: {cluster_result}")
            print(f"DEBUG: CourtListener Cluster/Docket APIs result: {cluster_result}")
            if cluster_result.get('found'):
                result.update(cluster_result)
                logging.info("[DEBUG] Citation verified by CourtListener Cluster/Docket APIs.")
                print("DEBUG: Citation verified by CourtListener Cluster/Docket APIs.")
                return result
            if LANGSEARCH_AVAILABLE and self.langsearch_api_key:
                logging.info("[DEBUG] Trying LangSearch API...")
                print("DEBUG: Trying LangSearch API...")
                lang_result = self.verify_with_langsearch_api(citation)
                logging.info(f"[DEBUG] LangSearch API result: {lang_result}")
                print(f"DEBUG: LangSearch API result: {lang_result}")
                if lang_result.get('found'):
                    result.update(lang_result)
                    logging.info("[DEBUG] Citation verified by LangSearch API.")
                    print("DEBUG: Citation verified by LangSearch API.")
                    return result
            if GOOGLE_SCHOLAR_AVAILABLE:
                logging.info("[DEBUG] Trying Google Scholar...")
                print("DEBUG: Trying Google Scholar...")
                scholar_result = self.verify_with_google_scholar(citation)
                logging.info(f"[DEBUG] Google Scholar result: {scholar_result}")
                print(f"DEBUG: Google Scholar result: {scholar_result}")
                if scholar_result.get('found'):
                    result.update(scholar_result)
                    logging.info("[DEBUG] Citation verified by Google Scholar.")
                    print("DEBUG: Citation verified by Google Scholar.")
                    return result
        except Exception as e:
            logging.error(f"[ERROR] Exception in verify_citation: {e}")
            print(f"DEBUG: Exception in verify_citation: {e}")
            traceback.print_exc()
        logging.info(f"[DEBUG] Citation not verified by any method: {citation}")
        print(f"DEBUG: Citation not verified by any method: {citation}")
        return result
    
    def verify_with_courtlistener_citation_api(self, citation: str) -> Dict[str, Any]:
        """Verify a citation using the CourtListener Citation Lookup API."""
        result = {
            'citation': citation,
            'found': False,
            'source': 'CourtListener Citation Lookup API',
            'case_name': None,
            'details': {}
        }
        
        if not COURTLISTENER_AVAILABLE or not self.api_key:
            print("CourtListener API not available or no API key provided")
            print(f"API key available: {bool(self.api_key)}")
            return result
        
        try:
            # Format citation for CourtListener
            formatted_citation = self._format_citation_for_courtlistener(citation)
            logging.info(f"[CourtListener] Formatted citation: {formatted_citation}")
            print(f"DEBUG: Formatted citation for CourtListener: {formatted_citation}")
            
            # Use the correct format for the API request
            # The API v4 citation-lookup endpoint expects a 'citation' parameter
            data = {'citation': formatted_citation}
            logging.info(f"[CourtListener] POST data: {data}")
            print(f"DEBUG: CourtListener API request data: {data}")
            logging.info(f"[CourtListener] API URL: {COURTLISTENER_CITATION_API}")
            logging.info(f"[CourtListener] Headers: {self.headers}")
            logging.info(f"[CourtListener] API key being used: {self.api_key[:5]}... (truncated)")
            # First try the citation lookup API
            print(f"\n==== MAKING API REQUEST TO {COURTLISTENER_CITATION_API} ====\n")
            print(f"Headers: {self.headers}")
            print(f"Data: {data}\n")
            
            logging.info(f"==== MAKING API REQUEST TO {COURTLISTENER_CITATION_API} ====")
            logging.info(f"Headers: {self.headers}")
            logging.info(f"Data: {data}")
            
            try:
                response = requests.post(
                    COURTLISTENER_CITATION_API, 
                    headers=self.headers, 
                    json=data,
                    timeout=TIMEOUT_SECONDS
                )
                
                print(f"\n==== API RESPONSE ====\n")
                print(f"Status code: {response.status_code}")
                print(f"Response headers: {dict(response.headers)}")
                print(f"Response text: {response.text}\n")
                
                logging.info(f"==== API RESPONSE ====")
                logging.info(f"Status code: {response.status_code}")
                logging.info(f"Response headers: {dict(response.headers)}")
                logging.info(f"Response text: {response.text}")
            except Exception as req_error:
                print(f"\n==== API REQUEST ERROR ====\n")
                print(f"Error: {str(req_error)}\n")
                traceback.print_exc()
                
                logging.error(f"==== API REQUEST ERROR ====")
                logging.error(f"Error: {str(req_error)}")
                logging.error(traceback.format_exc())
                
                # Re-raise to be caught by the outer try-except
                raise
            
            if response.status_code == 200:
                api_result = response.json()
                print(f"DEBUG: CourtListener API response JSON: {api_result}")
                logging.info(f"DEBUG: CourtListener API response JSON: {api_result}")
                
                # API v4 citation-lookup returns a different format than v3
                print(f"DEBUG: Full API v4 response: {api_result}")
                logging.info(f"DEBUG: Full API v4 response: {api_result}")
                
                # Check if we have results
                if api_result and isinstance(api_result, list) and len(api_result) > 0:
                    # Get the first result
                    citation_result = api_result[0]
                    print(f"DEBUG: First citation result: {citation_result}")
                    logging.info(f"DEBUG: First citation result: {citation_result}")
                    
                    # API v4 citation-lookup returns a list of matched citations with 'clusters'
                    clusters = citation_result.get('clusters', [])
                    if clusters and len(clusters) > 0:
                        # Get the first cluster
                        cluster = clusters[0]
                        print(f"DEBUG: First cluster: {cluster}")
                        logging.info(f"DEBUG: First cluster: {cluster}")
                        
                        # Mark as found and update result with case information
                        result['found'] = True
                        result['source'] = 'CourtListener'
                        result['case_name'] = cluster.get('case_name', 'Unknown Case')
                        
                        # Build URL from cluster ID if available
                        if cluster.get('id'):
                            result['url'] = f"https://www.courtlistener.com/opinion/{cluster.get('id')}/"
                        elif cluster.get('absolute_url'):
                            result['url'] = f"https://www.courtlistener.com{cluster.get('absolute_url')}"
                        
                        # Add detailed information
                        result['details'] = {
                            'court': cluster.get('court', 'Unknown Court'),
                            'date_filed': cluster.get('date_filed', 'Unknown Date'),
                            'docket_number': cluster.get('docket_number', 'Unknown')
                        }
                        
                        # Add citation information if available
                        if cluster.get('citations') and len(cluster['citations']) > 0:
                            citations_list = []
                            for cite in cluster['citations']:
                                if cite.get('volume') and cite.get('reporter') and cite.get('page'):
                                    citations_list.append(f"{cite['volume']} {cite['reporter']} {cite['page']}")
                            if citations_list:
                                result['details']['citations'] = citations_list
                        
                        print(f"DEBUG: Found case in CourtListener API v4: {result['case_name']}")
                        logging.info(f"DEBUG: Found case in CourtListener API v4: {result['case_name']}")
                        return result
                else:
                    print("No results found in citation lookup API response")
                
                # If no results found, try the search API as fallback
                # API v4 search endpoint uses different parameters
                search_url = f"{COURTLISTENER_SEARCH_API}?type=o&q={urllib.parse.quote(formatted_citation)}&format=json"
                print(f"Trying search API: {search_url}")
                
                response = requests.get(search_url, headers=self.headers, timeout=TIMEOUT_SECONDS)
                print(f"Search API response status: {response.status_code}")
                print(f"Search API response headers: {response.headers}")
                print(f"Search API response text: {response.text}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"Search API response JSON: {data}")
                    
                    if data.get('count', 0) > 0:
                        # Look for exact match in results
                        exact_match = None
                        for item in data['results']:
                            citations = item.get('citation', [])
                            print(f"Checking citations: {citations}")
                            if any(formatted_citation in cite for cite in citations):
                                exact_match = item
                                break
                        
                        if exact_match:
                            result_item = exact_match
                        else:
                            # If no exact match, use the first result
                            result_item = data['results'][0]
                            
                        result['found'] = True
                        result['case_name'] = result_item.get('caseName', result_item.get('case_name', 'Unknown Case'))
                        result['url'] = f"https://www.courtlistener.com{result_item.get('absolute_url', '')}"
                        result['details'] = {
                            'court': result_item.get('court', 'Unknown Court'),
                            'date_filed': result_item.get('dateFiled', result_item.get('date_filed', 'Unknown Date')),
                            'docket_number': result_item.get('docketNumber', result_item.get('docket_number', 'Unknown Docket')),
                            'citations': result_item.get('citation', [])
                        }
                        print(f"Found case in search API: {result['case_name']}")
                        return result
                    else:
                        print("No results found in search API response")
            else:
                print(f"Error response from citation lookup API: {response.status_code}")
                print(f"Error response text: {response.text}")
        
        except Exception as e:
            print(f"Error in verify_with_courtlistener_citation_api: {e}")
            traceback.print_exc()
        
        print("Citation not found in any API endpoint")
        return result
    
    def _format_citation_for_courtlistener(self, citation: str) -> str:
        """
        Format a citation for the CourtListener API.
        
        Args:
            citation: The original citation
            
        Returns:
            Properly formatted citation
        """
        # For U.S. Supreme Court citations, ensure proper spacing and format
        if 'U.S.' in citation:
            # Split the citation into parts
            parts = citation.split()
            if len(parts) >= 3:
                # Ensure proper spacing between volume, reporter, and page
                # Also ensure the reporter is properly formatted
                volume = parts[0]
                reporter = parts[1]
                page = parts[2]
                
                # Format the reporter if needed
                if reporter == 'U.S.':
                    reporter = 'U.S.'
                elif reporter == 'U.S':
                    reporter = 'U.S.'
                
                return f"{volume} {reporter} {page}"
        
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
            
            # Build search query
            search_params = {
                'q': formatted_citation,
                'type': 'o',  # opinions only
                'order_by': 'score desc',
                'format': 'json',
                'cite': formatted_citation,  # Add exact citation match
                'highlight': 'false',  # Disable highlighting for better performance
                'page_size': 1  # We only need the top result
            }
            
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
                    
                    # Handle rate limiting
                    if response.status_code == 429:
                        retry_after = int(response.headers.get('Retry-After', 60))
                        print(f"Rate limited. Waiting {retry_after} seconds...")
                        time.sleep(retry_after)
                        continue
                    
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
            
            # Build more specific search query
            search_params = {
                'q': formatted_citation,
                'type': 'o',  # opinions only
                'order_by': 'score desc',
                'format': 'json'
            }
            
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
