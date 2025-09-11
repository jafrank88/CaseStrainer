"""
Verification Services for CaseStrainer

Implements actual verification calls to:
- CourtListener citation lookup API
- CourtListener search API  
- Web search fallback
"""

import logging
from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

import time
import requests
from typing import Dict, List, Any, Optional
from urllib.parse import quote_plus
import re

logger = logging.getLogger(__name__)

class CourtListenerService:
    """Service for CourtListener API interactions"""
    
    def __init__(self):
        self.base_url = "https://www.courtlistener.com/api/rest/v4"
        self.citation_lookup_url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
        self.search_url = "https://www.courtlistener.com/api/rest/v4/search/"
        
        self.requests_per_minute = 60
        self.last_request_time = 0
        self.request_interval = 60.0 / self.requests_per_minute
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CaseStrainer/1.0 (Legal Citation Verification Tool)',
            'Accept': 'application/json'
        })
    
    def _rate_limit(self):
        """Implement rate limiting for API calls"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_interval:
            sleep_time = self.request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def verify_citations_batch(self, citations: List[str]) -> Dict[str, Any]:
        """
        Verify multiple citations using CourtListener citation lookup API
        
        Args:
            citations: List of citation strings to verify
            
        Returns:
            Dictionary mapping citations to verification results
        """
        if not citations:
            return {}
        
        self._rate_limit()
        
        try:
            batch_data = {
                'citations': citations
            }
            
            logger.info(f"Verifying {len(citations)} citations with CourtListener citation lookup")
            
            response = self.session.post(
                self.citation_lookup_url,
                json=batch_data,
                timeout=DEFAULT_REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                results = response.json()
                return self._parse_citation_lookup_results(citations, results)
            else:
                logger.warning(f"CourtListener citation lookup failed: {response.status_code} - {response.text}")
                return self._create_fallback_results(citations, 'citation_lookup_v4')
                
        except Exception as e:
            logger.error(f"Error calling CourtListener citation lookup: {e}")
            return self._create_fallback_results(citations, 'citation_lookup_v4')
    
    def verify_citations_search(self, citations: List[str]) -> Dict[str, Any]:
        """
        Verify citations using CourtListener search API as fallback
        
        Args:
            citations: List of citation strings to verify
            
        Returns:
            Dictionary mapping citations to verification results
        """
        if not citations:
            return {}
        
        results = {}
        
        for citation in citations:
            self._rate_limit()
            
            try:
                search_query = self._build_search_query(citation)
                
                search_params = {
                    'q': search_query,
                    'type': 'o',  # Opinions
                    'stat_Precedential': 'on',  # Precedential opinions only
                    'order_by': 'score desc',
                    'stat_OnTheMerits': 'on'
                }
                
                
                response = self.session.get(
                    self.search_url,
                    params=search_params,
                    timeout=DEFAULT_REQUEST_TIMEOUT
                )
                
                if response.status_code == 200:
                    search_results = response.json()
                    results[citation] = self._parse_search_result(citation, search_results)
                else:
                    logger.warning(f"CourtListener search failed for {citation}: {response.status_code}")
                    results[citation] = self._create_fallback_result(citation, 'courtlistener_search')
                    
            except Exception as e:
                logger.error(f"Error searching CourtListener for {citation}: {e}")
                results[citation] = self._create_fallback_result(citation, 'courtlistener_search')
        
        return results
    
    def _build_search_query(self, citation: str) -> str:
        """Build search query for a citation"""
        clean_citation = re.sub(r'[^\w\s\.]', ' ', citation).strip()
        
        parts = clean_citation.split()
        if len(parts) >= 2:
            return f'"{clean_citation}"'
        else:
            return clean_citation
    
    def _parse_citation_lookup_results(self, citations: List[str], api_results: Dict[str, Any]) -> Dict[str, Any]:
        """Parse results from CourtListener citation lookup API"""
        results = {}
        
        for citation in citations:
            results[citation] = self._create_fallback_result(citation, 'citation_lookup_v4')
        
        if 'results' in api_results:
            for result in api_results['results']:
                citation = result.get('citation')
                if citation and citation in results:
                    verification_data = self._parse_verification_result(result)
                    results[citation].update(verification_data)
                    results[citation]['verified'] = True
                    results[citation]['source'] = 'citation_lookup_v4'
        
        return results
    
    def _parse_search_result(self, citation: str, search_results: Dict[str, Any]) -> Dict[str, Any]:
        """Parse results from CourtListener search API"""
        result = self._create_fallback_result(citation, 'courtlistener_search')
        
        if 'results' in search_results and search_results['results']:
            top_result = search_results['results'][0]
            
            verification_data = self._parse_verification_result(top_result)
            result.update(verification_data)
            result['verified'] = True
            result['source'] = 'courtlistener_search'
        
        return result
    
    def _parse_verification_result(self, api_result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse verification data from CourtListener API result"""
        verification_data = {}
        
        if 'case_name' in api_result:
            verification_data['canonical_name'] = api_result['case_name']
        elif 'caseName' in api_result:
            verification_data['canonical_name'] = api_result['caseName']
        
        if 'date_filed' in api_result:
            date_str = api_result['date_filed']
            if date_str:
                year_match = re.search(r'(\d{4})', date_str)
                if year_match:
                    verification_data['canonical_date'] = year_match.group(1)
        
        if 'absolute_url' in api_result:
            verification_data['canonical_url'] = f"https://www.courtlistener.com{api_result['absolute_url']}"
        elif 'url' in api_result:
            verification_data['canonical_url'] = api_result['url']
        
        verification_data['confidence'] = 0.8  # High confidence for CourtListener results
        
        return verification_data
    
    def _create_fallback_result(self, citation: str, source: str) -> Dict[str, Any]:
        """Create a fallback result for unverified citations"""
        return {
            'verified': False,
            'source': source,
            'canonical_name': None,
            'canonical_date': None,
            'canonical_url': None,
            'confidence': 0.0,
            'validation_method': f'{source}_only'
        }
    
    def _create_fallback_results(self, citations: List[str], source: str) -> Dict[str, Any]:
        """Create fallback results for multiple citations"""
        return {citation: self._create_fallback_result(citation, source) for citation in citations}

class WebSearchService:
    """Service for web search verification fallback"""
    
    def __init__(self):
        # you would integrate with a web search API like Google Custom Search,
        self.enabled = False
        logger.warning("Web search verification is not yet implemented")
    
    def verify_citations(self, citations: List[str]) -> Dict[str, Any]:
        """Verify citations using web search (placeholder)"""
        if not self.enabled:
            return {citation: self._create_fallback_result(citation, 'web_search') for citation in citations}
        
        # TODO: Implement web search verification
        
        return {citation: self._create_fallback_result(citation, 'web_search') for citation in citations}
    
    def _create_fallback_result(self, citation: str, source: str) -> Dict[str, Any]:
        """Create a fallback result for web search"""
        return {
            'verified': False,
            'source': source,
            'canonical_name': None,
            'canonical_date': None,
            'canonical_url': None,
            'confidence': 0.0,
            'validation_method': f'{source}_only'
        }

class VerificationServiceFactory:
    """Factory for creating verification services"""
    
    @staticmethod
    def create_service(service_type: str):
        """Create a verification service of the specified type"""
        if service_type == 'citation_lookup_v4':
            return CourtListenerService()
        elif service_type == 'courtlistener_search':
            return CourtListenerService()
        elif service_type == 'web_search':
            return WebSearchService()
        else:
            raise ValueError(f"Unknown verification service type: {service_type}")
    
    @staticmethod
    def get_all_services():
        """Get all available verification services"""
        return {
            'citation_lookup_v4': CourtListenerService(),
            'courtlistener_search': CourtListenerService(),
            'web_search': WebSearchService()
        }
