"""
Web Search Engine Module
Comprehensive web search engine for legal citations and case information.
"""

import asyncio
import aiohttp
import logging
import time
import random
from typing import Dict, List, Any, Optional, Tuple, Set
from urllib.parse import urlparse, quote_plus, urljoin
from datetime import datetime, timedelta
import warnings
import re

from .citation_normalizer import EnhancedCitationNormalizer
from .metadata import SearchEngineMetadata
from .cache import CacheManager
from .predictor import SourcePredictor
from .semantic import SemanticMatcher
from .linkrot import EnhancedLinkrotDetector
from .fusion import ResultFusionEngine
from .ml_predictor import AdvancedMLPredictor
from .error_recovery import AdvancedErrorRecovery
from .analytics import AdvancedAnalytics
from .extractor import ComprehensiveWebExtractor

logger = logging.getLogger(__name__)


class ComprehensiveWebSearchEngine:
    """Comprehensive web search engine for legal citations and case information."""
    
    def __init__(self, enable_experimental_engines=False):
        # Initialize components
        self.cache_manager = CacheManager()
        self.citation_normalizer = EnhancedCitationNormalizer()
        self.source_predictor = SourcePredictor()
        self.semantic_matcher = SemanticMatcher()
        self.linkrot_detector = EnhancedLinkrotDetector(self.cache_manager)
        self.result_fusion = ResultFusionEngine(self.semantic_matcher)
        self.ml_predictor = AdvancedMLPredictor(self.cache_manager)
        self.error_recovery = AdvancedErrorRecovery(self.cache_manager, self.ml_predictor)
        self.analytics = AdvancedAnalytics(self.cache_manager)
        self.extractor = ComprehensiveWebExtractor()
        
        # Search engines configuration
        self.search_engines = {
            'justia': {
                'base_url': 'https://law.justia.com',
                'search_url': 'https://law.justia.com/search',
                'rate_limit': 1.0,
                'enabled': True
            },
            'findlaw': {
                'base_url': 'https://caselaw.findlaw.com',
                'search_url': 'https://caselaw.findlaw.com/search',
                'rate_limit': 1.0,
                'enabled': True
            },
            'courtlistener_web': {
                'base_url': 'https://www.courtlistener.com',
                'search_url': 'https://www.courtlistener.com/search',
                'rate_limit': 2.0,
                'enabled': True
            },
            'leagle': {
                'base_url': 'https://www.leagle.com',
                'search_url': 'https://www.leagle.com/search',
                'rate_limit': 1.5,
                'enabled': True
            },
            'casetext': {
                'base_url': 'https://casetext.com',
                'search_url': 'https://casetext.com/search',
                'rate_limit': 2.0,
                'enabled': True
            },
            'vlex': {
                'base_url': 'https://vlex.com',
                'search_url': 'https://vlex.com/search',
                'rate_limit': 2.0,
                'enabled': True
            },
            'google_scholar': {
                'base_url': 'https://scholar.google.com',
                'search_url': 'https://scholar.google.com/scholar',
                'rate_limit': 3.0,
                'enabled': True
            },
            'bing': {
                'base_url': 'https://www.bing.com',
                'search_url': 'https://www.bing.com/search',
                'rate_limit': 1.0,
                'enabled': True
            },
            'duckduckgo': {
                'base_url': 'https://duckduckgo.com',
                'search_url': 'https://duckduckgo.com/html',
                'rate_limit': 1.0,
                'enabled': True
            }
        }
        
        # Experimental engines
        if enable_experimental_engines:
            self.search_engines.update({
                'openjurist': {
                    'base_url': 'https://openjurist.org',
                    'search_url': 'https://openjurist.org/search',
                    'rate_limit': 2.0,
                    'enabled': True
                },
                'casemine': {
                    'base_url': 'https://www.casemine.com',
                    'search_url': 'https://www.casemine.com/search',
                    'rate_limit': 2.0,
                    'enabled': True
                }
            })
        
        # Rate limiting
        self.last_request_time = {}
        self.request_counts = {}
        
        # Performance tracking
        self.stats = {
            'total_searches': 0,
            'successful_searches': 0,
            'failed_searches': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'average_response_time': 0.0
        }
    
    def generate_strategic_queries(self, cluster: Dict) -> List[Dict[str, str]]:
        """Generate strategic search queries for a citation cluster."""
        queries = []
        citation = cluster.get('citation', '')
        case_name = cluster.get('case_name', '')
        
        if not citation:
            return queries
        
        # Generate citation variants
        citation_variants = self.citation_normalizer.generate_variants(citation)
        
        # Extract individual citations from complex citations (e.g., "19 Wn. App. 2d 357, 362, 496 P.3d 305 (2021)")
        individual_citations = self._extract_individual_citations(citation)
        if individual_citations:
            # Generate variants for each individual citation
            for individual_citation in individual_citations:
                individual_variants = self.citation_normalizer.generate_variants(individual_citation)
                citation_variants.extend(individual_variants)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variants = []
        for variant in citation_variants:
            if variant not in seen:
                seen.add(variant)
                unique_variants.append(variant)
        
        citation_variants = unique_variants
        
        # Generate case name variants (only as fallback)
        case_name_variants = list(self.extract_case_name_variants(case_name)) if case_name else []
        
        # PRIORITY 1: Citation-based queries (most reliable)
        for citation_variant in citation_variants[:8]:  # Increased from 5 to 8 to get more variants
            # Exact citation match (highest priority)
            queries.append({
                'query': f'"{citation_variant}"',
                'type': 'citation_exact',
                'citation': citation_variant,
                'case_name': None,
                'priority': 1
            })
            
            # Citation with legal context terms
            queries.append({
                'query': f'"{citation_variant}" case opinion',
                'type': 'citation_with_context',
                'citation': citation_variant,
                'case_name': None,
                'priority': 2
            })
            
            # Citation with court/jurisdiction terms
            queries.append({
                'query': f'"{citation_variant}" court decision',
                'type': 'citation_with_court',
                'citation': citation_variant,
                'case_name': None,
                'priority': 3
            })
            
            # Citation with year (if available)
            if re.search(r'\(\d{4}\)', citation_variant):
                queries.append({
                    'query': f'"{citation_variant}"',
                    'type': 'citation_with_year',
                    'citation': citation_variant,
                    'case_name': None,
                    'priority': 1
                })
        
        # PRIORITY 2: Citation + Case Name combinations (medium reliability)
        if case_name_variants:
            for citation_variant in citation_variants[:4]:  # Increased from 3 to 4
                for case_variant in case_name_variants[:2]:
                    queries.append({
                        'query': f'"{case_variant}" "{citation_variant}"',
                        'type': 'case_and_citation',
                        'citation': citation_variant,
                        'case_name': case_variant,
                        'priority': 4
                    })
        
        # PRIORITY 3: Case name only queries (lowest priority - fallback)
        if not citation_variants and case_name_variants:
            for case_variant in case_name_variants[:2]:  # Reduced from 3 to 2
                queries.append({
                    'query': f'"{case_variant}"',
                    'type': 'case_name_only',
                    'citation': None,
                    'case_name': case_variant,
                    'priority': 5
                })
        
        # Sort by priority (citation-based first)
        queries.sort(key=lambda x: x.get('priority', 999))
        
        return queries
    
    def _extract_individual_citations(self, citation: str) -> List[str]:
        """Extract individual citations from a complex citation string."""
        if not citation:
            return []
        
        # Pattern to match individual citations (volume reporter series page)
        # This handles patterns like "19 Wn. App. 2d 357" and "496 P.3d 305"
        # Updated to handle more complex patterns with commas and page numbers
        pattern = r'\d+\s+[A-Za-z\.]+\s+\d+[a-z]?\s+\d+(?:\s*,\s*\d+)*'
        
        matches = re.findall(pattern, citation)
        
        # Clean up matches to get individual citations
        individual_citations = []
        for match in matches:
            # Split by comma to get individual citations
            parts = re.split(r'\s*,\s*', match)
            for part in parts:
                # Check if this part looks like a citation (volume reporter series page)
                if re.match(r'\d+\s+[A-Za-z\.]+\s+\d+[a-z]?\s+\d+', part):
                    individual_citations.append(part.strip())
        
        return individual_citations
    
    def extract_case_name_variants(self, case_name: str) -> Set[str]:
        """Extract case name variants for search."""
        if not case_name:
            return set()
        
        variants = {case_name}
        
        # Normalize case name
        normalized = self.extractor._normalize_case_name(case_name)
        if normalized != case_name:
            variants.add(normalized)
        
        # Generate variations
        # Remove "et al." and similar
        clean_name = re.sub(r'\s+et\s+al\.?\s*$', '', case_name, flags=re.IGNORECASE)
        if clean_name != case_name:
            variants.add(clean_name)
        
        # Try different "v." formats
        if ' v. ' in case_name:
            variants.add(case_name.replace(' v. ', ' v '))
            variants.add(case_name.replace(' v. ', ' vs. '))
            variants.add(case_name.replace(' v. ', ' versus '))
        elif ' v ' in case_name:
            variants.add(case_name.replace(' v ', ' v. '))
            variants.add(case_name.replace(' v ', ' vs. '))
            variants.add(case_name.replace(' v ', ' versus '))
        
        # Handle "In re" variations
        if case_name.startswith('In re '):
            # "In re Marriage of Niemi" -> "In the Matter of the Marriage of Niemi"
            rest_of_name = case_name[6:]  # Remove "In re "
            variants.add(f"In the Matter of the {rest_of_name}")
            variants.add(f"In the Matter of {rest_of_name}")
            # Also try without "the"
            if rest_of_name.startswith('the '):
                variants.add(f"In the Matter of {rest_of_name[4:]}")
        
        # Handle "In the Matter of" variations
        if case_name.startswith('In the Matter of '):
            # "In the Matter of the Marriage of Niemi" -> "In re Marriage of Niemi"
            rest_of_name = case_name[18:]  # Remove "In the Matter of "
            if rest_of_name.startswith('the '):
                rest_of_name = rest_of_name[4:]  # Remove "the "
            variants.add(f"In re {rest_of_name}")
        
        return variants
    
    def score_result_reliability(self, result: Dict, query_info: Dict) -> float:
        """Score the reliability of a search result."""
        score = 0.0
        
        # Base score from source
        source_scores = {
            'justia': 0.9,
            'findlaw': 0.85,
            'courtlistener_web': 0.9,
            'leagle': 0.8,
            'casetext': 0.75,
            'vlex': 0.7,
            'casemine': 0.8,  # Added Casemine
            'openjurist': 0.7,  # Added OpenJurist
            'google_scholar': 0.6,
            'bing': 0.4,
            'duckduckgo': 0.4
        }
        
        source = result.get('source', '').lower()
        score += source_scores.get(source, 0.3)
        
        # Query type bonus (citation-based searches get higher scores)
        query_type = query_info.get('type', '')
        if query_type.startswith('citation_'):
            score += 0.2  # Bonus for citation-based searches
        elif query_type == 'case_and_citation':
            score += 0.1  # Medium bonus for combined searches
        # No bonus for case_name_only searches
        
        # Citation match (highest priority)
        citation = query_info.get('citation', '')
        if citation and result.get('title'):
            title_text = result['title'].lower()
            citation_lower = citation.lower()
            if citation_lower in title_text:
                score += 0.4  # Increased from 0.3 to 0.4
            elif any(part in title_text for part in citation_lower.split()):
                score += 0.2  # Partial citation match
        
        # Case name match (lower priority)
        case_name = query_info.get('case_name', '')
        if case_name and result.get('title'):
            similarity = self.semantic_matcher.calculate_similarity(result['title'], case_name)
            score += similarity * 0.15  # Reduced from 0.2 to 0.15
        
        # URL quality
        url = result.get('url', '')
        if url:
            domain = urlparse(url).netloc.lower()
            if any(legal_domain in domain for legal_domain in ['justia.com', 'findlaw.com', 'courtlistener.com', 'casemine.com']):
                score += 0.1
        
        return min(1.0, score)
    
    def _get_domain_from_url(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            return urlparse(url).netloc.lower()
        except:
            return ""
    
    def _rate_limit_check(self, engine: str):
        """Check and enforce rate limiting for an engine."""
        if engine not in self.last_request_time:
            self.last_request_time[engine] = 0
            self.request_counts[engine] = 0
        
        current_time = time.time()
        last_time = self.last_request_time[engine]
        
        # Get rate limit for engine
        rate_limit = self.search_engines.get(engine, {}).get('rate_limit', 1.0)
        
        # Calculate time since last request
        time_since_last = current_time - last_time
        
        if time_since_last < rate_limit:
            sleep_time = rate_limit - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time[engine] = time.time()
        self.request_counts[engine] = self.request_counts.get(engine, 0) + 1
    
    def search_with_engine(self, query: str, engine: str, num_results: int = 5) -> List[Dict]:
        """Search with a specific engine."""
        if not self.search_engines.get(engine, {}).get('enabled', False):
            return []
        
        # Rate limiting
        self._rate_limit_check(engine)
        
        # Check cache first
        cache_key = f"search_{engine}_{hash(query)}"
        cached_result = self.cache_manager.get(cache_key)
        if cached_result:
            self.analytics.record_cache_operation(hit=True)
            return cached_result
        
        self.analytics.record_cache_operation(hit=False)
        
        # Perform search based on engine
        try:
            if engine == 'google_scholar':
                results = self._google_search(query, num_results)
            elif engine == 'bing':
                results = self._bing_search(query, num_results)
            elif engine == 'duckduckgo':
                results = self._ddg_search(query, num_results)
            else:
                results = []
            
            # Cache results
            if results:
                self.cache_manager.set(cache_key, value=results, ttl_hours=24)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching with {engine}: {e}")
            return []
    
    def _google_search(self, query: str, num_results: int) -> List[Dict]:
        """Perform Google Scholar search."""
        # This is a simplified implementation
        # In practice, you'd need to handle Google Scholar's anti-bot measures
        results = []
        
        # Simulate search results
        for i in range(min(num_results, 3)):
            results.append({
                'title': f'Search result {i+1} for {query}',
                'url': f'https://example.com/result{i+1}',
                'snippet': f'This is a snippet for result {i+1}',
                'source': 'google_scholar'
            })
        
        return results
    
    def _bing_search(self, query: str, num_results: int) -> List[Dict]:
        """Perform Bing search."""
        # This is a simplified implementation
        results = []
        
        # Simulate search results
        for i in range(min(num_results, 3)):
            results.append({
                'title': f'Bing result {i+1} for {query}',
                'url': f'https://example.com/bing-result{i+1}',
                'snippet': f'This is a Bing snippet for result {i+1}',
                'source': 'bing'
            })
        
        return results
    
    def _ddg_search(self, query: str, num_results: int) -> List[Dict]:
        """Perform DuckDuckGo search."""
        # This is a simplified implementation
        results = []
        
        # Simulate search results
        for i in range(min(num_results, 3)):
            results.append({
                'title': f'DDG result {i+1} for {query}',
                'url': f'https://example.com/ddg-result{i+1}',
                'snippet': f'This is a DuckDuckGo snippet for result {i+1}',
                'source': 'duckduckgo'
            })
        
        return results
    
    async def search_vlex(self, citation: str, case_name: Optional[str] = None) -> Dict:
        """Search Vlex for legal documents."""
        # Implementation would go here
        return {'source': 'vlex', 'results': []}
    
    async def search_casetext(self, citation: str, case_name: Optional[str] = None) -> Dict:
        """Search Casetext for legal documents."""
        # Implementation would go here
        return {'source': 'casetext', 'results': []}
    
    async def search_justia(self, citation: str, case_name: Optional[str] = None) -> Dict:
        """Search Justia for legal documents using citation-first approach."""
        try:
            cluster = {'citation': citation, 'case_name': case_name or ''}
            queries = self.generate_strategic_queries(cluster)
            
            for query_info in queries[:3]:
                query = query_info['query']
                query_type = query_info.get('type', '')
                
                if query_type.startswith('citation_'):
                    results = self.search_with_engine(query, 'justia', num_results=3)
                    
                    if results:
                        best_result = results[0]
                        return {
                            'source': 'justia',
                            'verified': True,
                            'url': best_result.get('url', ''),
                            'title': best_result.get('title', ''),
                            'canonical_name': case_name,
                            'canonical_date': None,
                            'results': results
                        }
            
            return {'source': 'justia', 'verified': False, 'results': []}
        except Exception as e:
            logger.warning(f"Justia search failed for {citation}: {e}")
            return {'source': 'justia', 'verified': False, 'results': []}
    
    async def search_courtlistener_web(self, citation: str, case_name: Optional[str] = None) -> Dict:
        """Search CourtListener web for legal documents using citation-first approach."""
        try:
            cluster = {'citation': citation, 'case_name': case_name or ''}
            queries = self.generate_strategic_queries(cluster)
            
            for query_info in queries[:3]:
                query = query_info['query']
                query_type = query_info.get('type', '')
                
                if query_type.startswith('citation_'):
                    results = self.search_with_engine(query, 'courtlistener_web', num_results=3)
                    
                    if results:
                        best_result = results[0]
                        return {
                            'source': 'courtlistener_web',
                            'verified': True,
                            'url': best_result.get('url', ''),
                            'title': best_result.get('title', ''),
                            'canonical_name': case_name,
                            'canonical_date': None,
                            'results': results
                        }
            
            return {'source': 'courtlistener_web', 'verified': False, 'results': []}
        except Exception as e:
            logger.warning(f"CourtListener web search failed for {citation}: {e}")
            return {'source': 'courtlistener_web', 'verified': False, 'results': []}
    
    async def search_findlaw(self, citation: str, case_name: Optional[str] = None) -> Dict:
        """Search FindLaw for legal documents using citation-first approach."""
        try:
            cluster = {'citation': citation, 'case_name': case_name or ''}
            queries = self.generate_strategic_queries(cluster)
            
            for query_info in queries[:3]:
                query = query_info['query']
                query_type = query_info.get('type', '')
                
                if query_type.startswith('citation_'):
                    results = self.search_with_engine(query, 'findlaw', num_results=3)
                    
                    if results:
                        best_result = results[0]
                        return {
                            'source': 'findlaw',
                            'verified': True,
                            'url': best_result.get('url', ''),
                            'title': best_result.get('title', ''),
                            'canonical_name': case_name,
                            'canonical_date': None,
                            'results': results
                        }
            
            return {'source': 'findlaw', 'verified': False, 'results': []}
        except Exception as e:
            logger.warning(f"FindLaw search failed for {citation}: {e}")
            return {'source': 'findlaw', 'verified': False, 'results': []}
    
    async def search_leagle(self, citation: str, case_name: Optional[str] = None) -> Dict:
        """Search Leagle for legal documents using citation-first approach."""
        try:
            cluster = {'citation': citation, 'case_name': case_name or ''}
            queries = self.generate_strategic_queries(cluster)
            
            for query_info in queries[:3]:
                query = query_info['query']
                query_type = query_info.get('type', '')
                
                if query_type.startswith('citation_'):
                    results = self.search_with_engine(query, 'leagle', num_results=3)
                    
                    if results:
                        best_result = results[0]
                        return {
                            'source': 'leagle',
                            'verified': True,
                            'url': best_result.get('url', ''),
                            'title': best_result.get('title', ''),
                            'canonical_name': case_name,
                            'canonical_date': None,
                            'results': results
                        }
            
            return {'source': 'leagle', 'verified': False, 'results': []}
        except Exception as e:
            logger.warning(f"Leagle search failed for {citation}: {e}")
            return {'source': 'leagle', 'verified': False, 'results': []}
    
    async def search_openjurist(self, citation: str, case_name: Optional[str] = None) -> Dict:
        """Search OpenJurist for legal documents using citation-first approach."""
        try:
            cluster = {'citation': citation, 'case_name': case_name or ''}
            queries = self.generate_strategic_queries(cluster)
            
            for query_info in queries[:3]:
                query = query_info['query']
                query_type = query_info.get('type', '')
                
                if query_type.startswith('citation_'):
                    results = self.search_with_engine(query, 'openjurist', num_results=3)
                    
                    if results:
                        best_result = results[0]
                        return {
                            'source': 'openjurist',
                            'verified': True,
                            'url': best_result.get('url', ''),
                            'title': best_result.get('title', ''),
                            'canonical_name': case_name,
                            'canonical_date': None,
                            'results': results
                        }
            
            return {'source': 'openjurist', 'verified': False, 'results': []}
        except Exception as e:
            logger.warning(f"OpenJurist search failed for {citation}: {e}")
            return {'source': 'openjurist', 'verified': False, 'results': []}
    
    async def search_casemine(self, citation: str, case_name: Optional[str] = None) -> Dict:
        """Search Casemine for legal documents using citation-first approach."""
        try:
            # Create a cluster for the citation
            cluster = {
                'citation': citation,
                'case_name': case_name or ''
            }
            
            # Generate strategic queries for this citation
            queries = self.generate_strategic_queries(cluster)
            
            # Try the first few citation-based queries
            for query_info in queries[:3]:  # Try top 3 queries
                query = query_info['query']
                query_type = query_info.get('type', '')
                
                # Only try citation-based queries for Casemine
                if query_type.startswith('citation_'):
                    # Use the search_with_engine method for actual search
                    results = self.search_with_engine(query, 'casemine', num_results=3)
                    
                    if results:
                        # Return the best result as verified
                        best_result = results[0]
                        return {
                            'source': 'casemine',
                            'verified': True,
                            'url': best_result.get('url', ''),
                            'title': best_result.get('title', ''),
                            'canonical_name': case_name,
                            'canonical_date': None,
                            'results': results
                        }
            
            # If no results found
            return {'source': 'casemine', 'verified': False, 'results': []}
                
        except Exception as e:
            logger.warning(f"Casemine search failed for {citation}: {e}")
            return {'source': 'casemine', 'verified': False, 'results': []}
    
    async def search_google_scholar(self, citation: str, case_name: Optional[str] = None) -> Dict:
        """Search Google Scholar for legal documents using citation-first approach."""
        try:
            cluster = {'citation': citation, 'case_name': case_name or ''}
            queries = self.generate_strategic_queries(cluster)
            
            for query_info in queries[:3]:
                query = query_info['query']
                query_type = query_info.get('type', '')
                
                if query_type.startswith('citation_'):
                    results = self.search_with_engine(query, 'google_scholar', num_results=3)
                    
                    if results:
                        best_result = results[0]
                        return {
                            'source': 'google_scholar',
                            'verified': True,
                            'url': best_result.get('url', ''),
                            'title': best_result.get('title', ''),
                            'canonical_name': case_name,
                            'canonical_date': None,
                            'results': results
                        }
            
            return {'source': 'google_scholar', 'verified': False, 'results': []}
        except Exception as e:
            logger.warning(f"Google Scholar search failed for {citation}: {e}")
            return {'source': 'google_scholar', 'verified': False, 'results': []}
    
    async def search_bing(self, citation: str, case_name: Optional[str] = None) -> Dict:
        """Search Bing for legal documents using citation-first approach."""
        try:
            cluster = {'citation': citation, 'case_name': case_name or ''}
            queries = self.generate_strategic_queries(cluster)
            
            for query_info in queries[:3]:
                query = query_info['query']
                query_type = query_info.get('type', '')
                
                if query_type.startswith('citation_'):
                    results = self.search_with_engine(query, 'bing', num_results=3)
                    
                    if results:
                        best_result = results[0]
                        return {
                            'source': 'bing',
                            'verified': True,
                            'url': best_result.get('url', ''),
                            'title': best_result.get('title', ''),
                            'canonical_name': case_name,
                            'canonical_date': None,
                            'results': results
                        }
            
            return {'source': 'bing', 'verified': False, 'results': []}
        except Exception as e:
            logger.warning(f"Bing search failed for {citation}: {e}")
            return {'source': 'bing', 'verified': False, 'results': []}
    
    async def search_duckduckgo(self, citation: str, case_name: Optional[str] = None) -> Dict:
        """Search DuckDuckGo for legal documents using citation-first approach."""
        try:
            cluster = {'citation': citation, 'case_name': case_name or ''}
            queries = self.generate_strategic_queries(cluster)
            
            for query_info in queries[:3]:
                query = query_info['query']
                query_type = query_info.get('type', '')
                
                if query_type.startswith('citation_'):
                    results = self.search_with_engine(query, 'duckduckgo', num_results=3)
                    
                    if results:
                        best_result = results[0]
                        return {
                            'source': 'duckduckgo',
                            'verified': True,
                            'url': best_result.get('url', ''),
                            'title': best_result.get('title', ''),
                            'canonical_name': case_name,
                            'canonical_date': None,
                            'results': results
                        }
            
            return {'source': 'duckduckgo', 'verified': False, 'results': []}
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed for {citation}: {e}")
            return {'source': 'duckduckgo', 'verified': False, 'results': []}
    
    async def search_multiple_sources(self, citation: str, case_name: Optional[str] = None, max_concurrent: int = 3) -> Dict:
        """Search multiple sources concurrently."""
        # Get recommended sources
        recommended_sources = self.source_predictor.predict_best_sources(citation, case_name)
        
        # Limit concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def search_source(source: str) -> Dict:
            async with semaphore:
                try:
                    if source == 'vlex':
                        return await self.search_vlex(citation, case_name)
                    elif source == 'casetext':
                        return await self.search_casetext(citation, case_name)
                    elif source == 'justia':
                        return await self.search_justia(citation, case_name)
                    elif source == 'courtlistener_web':
                        return await self.search_courtlistener_web(citation, case_name)
                    elif source == 'findlaw':
                        return await self.search_findlaw(citation, case_name)
                    elif source == 'leagle':
                        return await self.search_leagle(citation, case_name)
                    elif source == 'openjurist':
                        return await self.search_openjurist(citation, case_name)
                    elif source == 'casemine':
                        return await self.search_casemine(citation, case_name)
                    elif source == 'google_scholar':
                        return await self.search_google_scholar(citation, case_name)
                    elif source == 'bing':
                        return await self.search_bing(citation, case_name)
                    elif source == 'duckduckgo':
                        return await self.search_duckduckgo(citation, case_name)
                    else:
                        return {'source': source, 'results': [], 'error': 'Unknown source'}
                except Exception as e:
                    return {'source': source, 'results': [], 'error': str(e)}
        
        # Execute searches concurrently
        tasks = [search_source(source) for source in recommended_sources[:max_concurrent]]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        combined_results = []
        for result in results:
            if isinstance(result, dict) and 'results' in result:
                combined_results.extend(result['results'])
        
        return {
            'results': combined_results,
            'sources_used': recommended_sources[:max_concurrent],
            'total_results': len(combined_results)
        }
    
    async def _fallback_search(self, citation: str, case_name: Optional[str] = None) -> Dict:
        """Perform fallback search when primary sources fail."""
        # Try general search engines with citation-focused queries
        fallback_sources = ['google_scholar', 'bing', 'duckduckgo']
        
        results = []
        for source in fallback_sources:
            try:
                # Create citation-focused queries for fallback
                queries = []
                if citation:
                    # Exact citation match (highest priority)
                    queries.append(f'"{citation}"')
                    # Citation with legal terms
                    queries.append(f'"{citation}" case opinion')
                    # Citation with court terms
                    queries.append(f'"{citation}" court decision')
                
                # Only add case name queries if no citation available
                if not citation and case_name:
                    queries.append(f'"{case_name}"')
                
                # Try each query
                for query in queries[:2]:  # Limit to top 2 queries
                    if source == 'google_scholar':
                        result = await self.search_google_scholar(citation, case_name)
                    elif source == 'bing':
                        result = await self.search_bing(citation, case_name)
                    elif source == 'duckduckgo':
                        result = await self.search_duckduckgo(citation, case_name)
                    else:
                        continue
                    
                    if result.get('results'):
                        # Add query context
                        for res in result['results']:
                            res['query_used'] = query
                            res['query_type'] = 'fallback_citation' if citation else 'fallback_case_name'
                            res['source'] = source
                        results.extend(result['results'])
                        
            except Exception as e:
                logger.debug(f"Fallback search failed for {source}: {e}")
                continue
        
        return {
            'results': results,
            'sources_used': fallback_sources,
            'fallback_used': True
        }
    
    async def search_cluster_canonical(self, cluster: Dict, max_results: int = 10) -> List[Dict]:
        """Search for canonical sources for a citation cluster."""
        citation = cluster.get('citation', '')
        case_name = cluster.get('case_name', '')
        
        if not citation:
            return []
        
        # Generate strategic queries (prioritized by citation-based searches)
        queries = self.generate_strategic_queries(cluster)
        
        all_results = []
        
        # Search with each query in priority order
        for query_info in queries[:8]:  # Increased from 5 to 8 to get more citation-based queries
            query = query_info['query']
            query_type = query_info.get('type', 'unknown')
            priority = query_info.get('priority', 999)
            
            # Prioritize citation-based searches
            if query_type.startswith('citation_'):
                max_sources_per_query = 4  # More sources for citation-based searches
            else:
                max_sources_per_query = 2  # Fewer sources for case name searches
            
            # Get recommended sources for this query
            recommended_sources = self.source_predictor.predict_best_sources(
                query_info.get('citation', ''), 
                query_info.get('case_name', '')
            )
            
            # Search with each source
            for source in recommended_sources[:max_sources_per_query]:
                try:
                    if source == 'justia':
                        result = await self.search_justia(citation, case_name)
                    elif source == 'findlaw':
                        result = await self.search_findlaw(citation, case_name)
                    elif source == 'courtlistener_web':
                        result = await self.search_courtlistener_web(citation, case_name)
                    elif source == 'leagle':
                        result = await self.search_leagle(citation, case_name)
                    elif source == 'casetext':
                        result = await self.search_casetext(citation, case_name)
                    elif source == 'vlex':
                        result = await self.search_vlex(citation, case_name)
                    elif source == 'casemine':
                        result = await self.search_casemine(citation, case_name)
                    elif source == 'openjurist':
                        result = await self.search_openjurist(citation, case_name)
                    else:
                        continue
                    
                    if result.get('results'):
                        # Add query context to results
                        for res in result['results']:
                            res['query_used'] = query
                            res['query_type'] = query_type
                            res['query_priority'] = priority
                            res['reliability_score'] = self.score_result_reliability(res, query_info)
                        
                        all_results.extend(result['results'])
                        
                except Exception as e:
                    logger.debug(f"Search failed for {source}: {e}")
                    continue
        
        # Remove duplicates and sort by reliability and priority
        unique_results = {}
        for result in all_results:
            url = result.get('url', '')
            if url and url not in unique_results:
                unique_results[url] = result
            elif not url:
                # For results without URLs, use title as key
                title = result.get('title', '')
                if title and title not in unique_results:
                    unique_results[title] = result
        
        # Sort by priority first, then by reliability score
        sorted_results = sorted(
            unique_results.values(), 
            key=lambda x: (x.get('query_priority', 999), -x.get('reliability_score', 0)), 
            reverse=False  # Lower priority numbers first
        )
        
        return sorted_results[:max_results]
    
    def _is_valid_result(self, result: Dict) -> bool:
        """Check if a search result is valid."""
        if not result:
            return False
        
        # Must have at least a title or URL
        if not result.get('title') and not result.get('url'):
            return False
        
        # URL should be valid
        url = result.get('url', '')
        if url:
            try:
                parsed = urlparse(url)
                if not parsed.scheme or not parsed.netloc:
                    return False
            except:
                return False
        
        return True
    
    def _respect_rate_limit(self, method: str) -> bool:
        """Check if we should respect rate limits for a method."""
        # Some methods might be more lenient with rate limiting
        lenient_methods = ['fallback_search', 'cache_check']
        return method not in lenient_methods
    
    def _update_stats(self, method: str, success: bool, duration: float):
        """Update search statistics."""
        self.stats['total_searches'] += 1
        
        if success:
            self.stats['successful_searches'] += 1
        else:
            self.stats['failed_searches'] += 1
        
        # Update average response time
        current_avg = self.stats['average_response_time']
        total_searches = self.stats['total_searches']
        self.stats['average_response_time'] = (
            (current_avg * (total_searches - 1) + duration) / total_searches
        )
    
    def get_search_priority(self) -> List[str]:
        """Get prioritized list of search engines."""
        # This could be based on historical performance
        return [
            'justia',
            'findlaw', 
            'courtlistener_web',
            'leagle',
            'casetext',
            'vlex',
            'casemine',  # Added Casemine
            'openjurist',  # Added OpenJurist
            'google_scholar',
            'bing',
            'duckduckgo'
        ]
    
    async def _check_url_accessibility(self, url: str) -> Dict[str, Any]:
        """Check if a URL is accessible."""
        return await self.linkrot_detector.check_url_status(url)
    
    async def _check_accessibility_batch(self, results: List[Dict]):
        """Check accessibility of multiple URLs in batch."""
        tasks = []
        for result in results:
            url = result.get('url', '')
            if url:
                tasks.append(self._check_url_accessibility(url))
        
        if tasks:
            accessibility_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if i < len(accessibility_results):
                    accessibility = accessibility_results[i]
                    if isinstance(accessibility, dict):
                        result['accessibility'] = accessibility
                    else:
                        result['accessibility'] = {'status': 'unknown', 'accessible': False} 