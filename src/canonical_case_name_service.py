"""
Canonical Case Name and Date Retrieval Implementation
Provides authoritative case information from multiple legal databases
"""

import re
import logging
import requests
import time
from typing import Dict, Optional, Any, List
from urllib.parse import quote_plus
import json
from functools import lru_cache
from dataclasses import dataclass
try:
    from .config import get_config_value
except ImportError:
    from config import get_config_value
import os
from src.comprehensive_websearch_engine import search_cluster_for_canonical_sources
import concurrent.futures
import sys

logger = logging.getLogger(__name__)

# Dedicated fallback logger
fallback_logger = logging.getLogger('fallback_usage')
fallback_logger.setLevel(logging.INFO)

# Create fallback log file handler
try:
    # Ensure logs directory exists
    logs_dir = 'logs'
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir, exist_ok=True)
    fallback_log_path = os.path.join(logs_dir, 'fallback_usage.log')
    fallback_handler = logging.FileHandler(fallback_log_path)
    fallback_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    fallback_logger.addHandler(fallback_handler)
except Exception as e:
    logger.warning(f"Could not create fallback log file: {e}")
    logger.error(f"FALLBACK LOGGING ERROR: Could not create fallback log file: {e}")

def log_fallback_usage(citation: str, fallback_type: str, reason: str, context: Dict = None):
    """Log fallback usage to dedicated log file"""
    try:
        log_entry = {
            'timestamp': time.time(),
            'citation': citation,
            'fallback_type': fallback_type,
            'reason': reason,
            'context': context or {}
        }
        fallback_logger.info(f"FALLBACK_USED: {json.dumps(log_entry)}")
    except Exception as e:
        logger.error(f"Failed to log fallback usage: {e}")

@dataclass
class CanonicalResult:
    """Structured result for canonical case information"""
    case_name: Optional[str] = None
    date: Optional[str] = None
    court: Optional[str] = None
    docket_number: Optional[str] = None
    url: Optional[str] = None
    source: str = "unknown"
    confidence: float = 0.0
    verified: bool = False
    parallel_citations: List[str] = None
    
    def __post_init__(self):
        if self.parallel_citations is None:
            self.parallel_citations = []

class CanonicalCaseNameService:
    """
    Service for retrieving canonical case names and dates from legal databases
    """
    
    def __init__(self):
        # API configuration - get from environment or config
        self.courtlistener_api_key = self._get_config_value("COURTLISTENER_API_KEY")
        self.caselaw_api_key = self._get_config_value("CASELAW_API_KEY")
        self.westlaw_api_key = self._get_config_value("WESTLAW_API_KEY")
        
        # Rate limiting
        self.last_request_time = {}
        self.min_request_interval = 1.0  # seconds between requests
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CaseStrainer/2.0 Legal Citation Processor'
        })
        
        # Citation normalization patterns
        self.citation_patterns = {
            'wn2d': r'(\d+)\s+Wn\.2d\s+(\d+)',
            'wn_app': r'(\d+)\s+Wn\.\s*App\.\s+(\d+)', 
            'p3d': r'(\d+)\s+P\.3d\s+(\d+)',
            'p2d': r'(\d+)\s+P\.2d\s+(\d+)',
            'us': r'(\d+)\s+U\.S\.\s+(\d+)',
            'f3d': r'(\d+)\s+F\.3d\s+(\d+)',
            'f2d': r'(\d+)\s+F\.2d\s+(\d+)',
        }
        
        # Clear cache to ensure fresh lookups with new service order
        self._cached_lookup.cache_clear()
    
    def _get_config_value(self, key: str) -> Optional[str]:
        """Get configuration value from environment or config file"""
        import os
        try:
            # Try environment variable first
            value = os.environ.get(key)
            if value:
                return value
            
            # Try config file
            return get_config_value(key)
        except ImportError:
            # Fallback to environment only
            return os.environ.get(key)
    
    def _normalize_citation(self, citation: str) -> str:
        """Normalize citation format for better API matching"""
        if not citation:
            return ""
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', citation.strip())
        
        # Standardize Washington citations
        normalized = re.sub(r'Wash\.\s*2d', 'Wn.2d', normalized)
        normalized = re.sub(r'Wash\.\s*App\.', 'Wn. App.', normalized)
        
        # Standardize Pacific Reporter
        normalized = re.sub(r'P\.\s*3d', 'P.3d', normalized)
        normalized = re.sub(r'P\.\s*2d', 'P.2d', normalized)
        
        return normalized
    
    def _extract_citation_components(self, citation: str) -> Dict[str, str]:
        """Extract volume, reporter, and page from citation"""
        components = {'volume': '', 'reporter': '', 'page': ''}
        
        # Try each pattern
        for pattern_name, pattern in self.citation_patterns.items():
            match = re.search(pattern, citation)
            if match:
                components['volume'] = match.group(1)
                components['page'] = match.group(2)
                
                # Map pattern to reporter
                reporter_map = {
                    'wn2d': 'Wn.2d',
                    'wn_app': 'Wn. App.',
                    'p3d': 'P.3d',
                    'p2d': 'P.2d',
                    'us': 'U.S.',
                    'f3d': 'F.3d',
                    'f2d': 'F.2d'
                }
                components['reporter'] = reporter_map.get(pattern_name, '')
                break
        
        return components
    
    def _rate_limit(self, service: str):
        """Implement rate limiting for API requests"""
        now = time.time()
        last_time = self.last_request_time.get(service, 0)
        
        time_since_last = now - last_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time[service] = time.time()
    
    @lru_cache(maxsize=1000)
    def _cached_lookup(self, normalized_citation: str) -> Optional[CanonicalResult]:
        """Cached lookup to avoid repeated API calls"""
        return self._perform_lookup(normalized_citation)
    
    def _perform_lookup(self, citation: str) -> Optional[CanonicalResult]:
        """Perform the actual lookup across multiple services"""
        
        # Try services in order of preference
        services = [
            ('courtlistener', self._lookup_courtlistener),
            ('web_sources', self._lookup_web_sources)   # Web search (can target CAP, Westlaw, etc.)
        ]
        
        failed_services = []
        for service_name, lookup_func in services:
            try:
                self._rate_limit(service_name)
                result = lookup_func(citation)
                # HARDFILTER: Only return if case_name is valid
                from src.canonical_case_name_service import is_valid_case_name
                if result and result.case_name:
                    if not is_valid_case_name(result.case_name):
                        logger.warning(f"[HARDFILTER] Rejected result from {service_name} for '{citation}': '{result.case_name}' is not a valid case name (hard filter)")
                        continue
                    else:
                        logger.info(f"[HARDFILTER] Accepted result from {service_name} for '{citation}': '{result.case_name}' is a valid case name (hard filter)")
                if result and result.case_name:
                    logger.info(f"Found canonical result via {service_name}: {result.case_name}")
                    # Log if fallback was used (web_sources only)
                    if service_name == 'web_sources':
                        log_fallback_usage(
                            citation=citation,
                            fallback_type='canonical_lookup',
                            reason=f"Primary service (courtlistener) failed, using {service_name}",
                            context={'result_case_name': result.case_name, 'result_source': result.source}
                        )
                        # Ensure source field includes 'fallback' for test detection
                        result.source = f"fallback: {result.source}"
                    return result
                else:
                    failed_services.append(f"{service_name}(no_result)")
            except Exception as e:
                failed_services.append(f"{service_name}(error:{str(e)})")
                logger.warning(f"Lookup failed for {service_name}: {e}")
                continue
        
        # If we get here, all services failed
        log_fallback_usage(
            citation=citation,
            fallback_type='canonical_lookup',
            reason=f"All services failed: {', '.join(failed_services)}",
            context={'failed_services': failed_services}
        )
        return None
    
    def _lookup_courtlistener(self, citation: str) -> Optional[CanonicalResult]:
        """Lookup using CourtListener API"""
        if not self.courtlistener_api_key:
            return None
        
        try:
            components = self._extract_citation_components(citation)
            if not all(components.values()):
                return None
            
            # Build search query - use exact citation format
            query = f'"{components["volume"]} {components["reporter"]} {components["page"]}"'
            
            url = "https://www.courtlistener.com/api/rest/v4/search/"
            headers = {"Authorization": f"Token {self.courtlistener_api_key}"}
            params = {
                "q": query,
                "type": "o",  # Opinions
                "format": "json",
                "page_size": 10
            }
            
            response = self.session.get(url, headers=headers, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            for result in results:
                # Look for exact citation match
                citation_string = result.get('citation', [])
                if isinstance(citation_string, list):
                    citation_string = ' '.join(citation_string)
                
                # Check for exact match of the full citation
                if citation.lower() in str(citation_string).lower():
                    return CanonicalResult(
                        case_name=result.get('caseName', ''),
                        date=result.get('dateFiled', ''),
                        court=result.get('court', ''),
                        docket_number=result.get('docketNumber', ''),
                        url=result.get('absolute_url', ''),
                        source='CourtListener',
                        confidence=0.9,
                        verified=True,
                        parallel_citations=result.get('citation', [])
                    )
                
                # Also check for exact component match as fallback
                if (components['volume'] in str(citation_string) and 
                    components['page'] in str(citation_string) and
                    components['reporter'] in str(citation_string)):
                    
                    return CanonicalResult(
                        case_name=result.get('caseName', ''),
                        date=result.get('dateFiled', ''),
                        court=result.get('court', ''),
                        docket_number=result.get('docketNumber', ''),
                        url=result.get('absolute_url', ''),
                        source='CourtListener',
                        confidence=0.9,
                        verified=True,
                        parallel_citations=result.get('citation', [])
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"CourtListener lookup failed: {e}")
            return None
    
    def _lookup_caselaw_access(self, citation: str) -> Optional[CanonicalResult]:
        """Lookup using Caselaw Access Project API"""
        try:
            # CAP API endpoint
            url = "https://api.case.law/v1/cases/"
            params = {
                "cite": citation,
                "format": "json",
                "full_case": "false"
            }
            
            if self.caselaw_api_key:
                headers = {"Authorization": f"Token {self.caselaw_api_key}"}
            else:
                headers = {}
            
            response = self.session.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            if results:
                result = results[0]  # Take first result
                
                # Extract date from decision_date
                date = result.get('decision_date', '')
                if date:
                    # Convert YYYY-MM-DD to just year if needed
                    year_match = re.search(r'(\d{4})', date)
                    if year_match:
                        date = year_match.group(1)
                
                return CanonicalResult(
                    case_name=result.get('name_abbreviation', ''),
                    date=date,
                    court=result.get('court', {}).get('name', ''),
                    docket_number=result.get('docket_number', ''),
                    url=result.get('frontend_url', ''),
                    source='Caselaw Access Project',
                    confidence=0.85,
                    verified=True,
                    parallel_citations=result.get('citations', [])
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Caselaw Access lookup failed: {e}")
            return None
    
    def _lookup_westlaw(self, citation: str) -> Optional[CanonicalResult]:
        """Lookup using Westlaw API or fallback to canonical verification."""
        try:
            # First try the canonical verification workflow as primary method
            try:
                from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
                PROCESSOR_AVAILABLE = True
            except ImportError:
                PROCESSOR_AVAILABLE = False
                logger.warning("UnifiedCitationProcessorV2 not available")
                
            if PROCESSOR_AVAILABLE:
                processor = UnifiedCitationProcessorV2()
                result = processor.verify_citation_unified_workflow(citation)
                
                if result.get("verified"):
                    return CanonicalResult(
                        case_name=result.get("case_name") or result.get("canonical_name"),
                        date=result.get("canonical_date"),
                        url=result.get("url"),
                        source="Westlaw (via UnifiedProcessor)",
                        confidence=result.get("confidence", 0.8)
                    )
            
            # If no Westlaw API key, return None
            if not self.westlaw_api_key:
                return None
            
            # Try actual Westlaw API if available (placeholder for future implementation)
            url = "https://api.westlaw.com/v1/cases"
            headers = {
                "Authorization": f"Bearer {self.westlaw_api_key}",
                "Content-Type": "application/json"
            }
            params = {"q": citation}
            
            response = self.session.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            # Process Westlaw response format
            # This would need to be implemented based on actual Westlaw API
            
            return None
            
        except Exception as e:
            logger.error(f"Westlaw lookup failed: {e}")
            return None
    
    def _lookup_web_sources(self, citation: str) -> Optional[CanonicalResult]:
        """Lookup using intelligent web scraping with EnhancedLegalSearchEngine and multiple engines, with cluster batching and a global timeout. Site-specific legal DBs are tried before general search engines."""
        try:
            import logging
            import asyncio
            import time
            from src.enhanced_legal_search_engine import EnhancedLegalSearchEngine
            from src.comprehensive_websearch_engine import ComprehensiveWebSearchEngine
            logger = logging.getLogger(__name__)
            print(f"[DEBUG] [WEBSEARCH] Attempting enhanced websearch for citation: {citation} and variants")

            # --- Playwright Justia search (before other site-specific engines) ---
            import subprocess
            import sys
            try:
                print(f"[DEBUG] [PLAYWRIGHT][JUSTIA] Attempting Playwright Justia search for: {citation}")
                result = subprocess.run([
                    sys.executable, "playwright_search_justia.py", citation
                ], capture_output=True, text=True, timeout=12)
                output = result.stdout.strip()
                print(f"[DEBUG] [PLAYWRIGHT][JUSTIA] Output: {output}")
                # Parse output for case name
                if "Case name:" in output:
                    case_name = output.split("Case name:")[-1].strip()
                    if case_name and case_name.lower() != 'none':
                        print(f"[DEBUG] [PLAYWRIGHT][JUSTIA] Found case name: {case_name}")
                        return CanonicalResult(
                            case_name=case_name,
                            date=None,
                            url=None,
                            source="justia (playwright)",
                            confidence=0.85,
                            verified=True
                        )
            except Exception as e:
                print(f"[DEBUG] [PLAYWRIGHT][JUSTIA] Exception: {e}")
            # --- End Playwright Justia search ---

            enhanced_engine = EnhancedLegalSearchEngine()
            web_engine = ComprehensiveWebSearchEngine()
            queries = enhanced_engine.generate_enhanced_legal_queries(citation)
            all_results = []
            seen_urls = set()
            max_results = 40
            error_threshold = 2
            query_limit = 3
            global_timeout = 15  # seconds

            # --- Clustered search: batch queries for parallel citations ---
            cluster_citations = [citation]
            all_variants = set()
            for cit in cluster_citations:
                all_variants.add(cit.strip())
                all_variants.add(enhanced_engine.normalize_citation(cit))
                if enhanced_engine.is_washington_citation(cit):
                    all_variants.update(enhanced_engine.generate_washington_variants(cit))
            or_query = ' OR '.join([f'"{v}"' for v in all_variants if v])
            batched_queries = [{'query': or_query, 'priority': 0, 'type': 'batched_cluster', 'citation': citation}]
            queries = batched_queries + queries

            # Phase 1: Site-specific legal database searches
            site_specific_engines = ['casetext', 'leagle', 'casemine', 'justia', 'findlaw', 'openjurist', 'vlex']
            error_counts = {engine: 0 for engine in site_specific_engines}
            found_valid_result = None
            def run_site_query(engine_name, query):
                if error_counts[engine_name] >= error_threshold:
                    print(f"[DEBUG] [WEBSEARCH] Skipping {engine_name} due to repeated errors.")
                    return []
                try:
                    # Use the async search_* methods for site-specific engines
                    search_method = getattr(web_engine, f'search_{engine_name}', None)
                    if search_method is None:
                        print(f"[DEBUG] [WEBSEARCH] No search method for {engine_name}")
                        return []
                    # Run the async method using asyncio.run()
                    import asyncio
                    results = asyncio.run(search_method(query, None))
                    time.sleep(1.5)
                    # If the result is a dict, wrap in a list for uniformity
                    if isinstance(results, dict):
                        results = [results]
                    return results
                except Exception as e:
                    print(f"[DEBUG] [WEBSEARCH] {engine_name} search error: {e}")
                    error_counts[engine_name] += 1
                    return []
            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                future_to_info = {}
                for query_info in queries[:query_limit]:
                    query = query_info['query']
                    for engine_name in site_specific_engines:
                        if error_counts[engine_name] < error_threshold:
                            future = executor.submit(run_site_query, engine_name, query)
                            future_to_info[future] = (engine_name, query)
                start_time = time.time()
                try:
                    for future in concurrent.futures.as_completed(future_to_info, timeout=global_timeout):
                        engine_name, query = future_to_info[future]
                        results = future.result()
                        if not results:
                            print(f"[DEBUG] [WEBSEARCH] No results from {engine_name} for query: {query}")
                            continue
                        for result in results:
                            url = result.get('url')
                            if url and url not in seen_urls:
                                seen_urls.add(url)
                                all_results.append(result)
                                legal_results = enhanced_engine.filter_legal_results([result])
                                if legal_results:
                                    best = legal_results[0]
                                    candidate_name = best.get('title')
                                    is_valid = is_valid_case_name(candidate_name)
                                    if is_valid:
                                        print(f"[DEBUG] [WEBSEARCH] Found valid canonical result (site-specific): {candidate_name} | URL: {best.get('url')}")
                                        found_valid_result = best
                                        break
                            if len(all_results) >= max_results or found_valid_result:
                                break
                        if len(all_results) >= max_results or found_valid_result:
                            break
                        if time.time() - start_time > global_timeout:
                            print(f"[DEBUG] [WEBSEARCH] Timeout reached, stopping websearch early (site-specific phase).")
                    if found_valid_result:
                        pass
                except concurrent.futures.TimeoutError:
                    print(f"[DEBUG] [WEBSEARCH] Global websearch timeout ({global_timeout}s) reached (site-specific phase).")
                finally:
                    pass
            if found_valid_result:
                candidate_name = found_valid_result.get('title')
                url = found_valid_result.get('url')
                domain = None
                if url:
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc.lower()
                if not domain:
                    domain = found_valid_result.get('source', 'Web Search')
                return CanonicalResult(
                    case_name=candidate_name,
                    date=None,  # Date extraction can be added if available
                    court=None,
                    docket_number=None,
                    url=url,
                    source=domain,
                    confidence=found_valid_result.get('legal_relevance_score', 0) / 100.0,
                    verified=found_valid_result.get('legal_relevance_score', 0) >= 70
                )

            # Phase 2: General search engines (Google, Bing, DDG)
            engines = ['google', 'bing', 'ddg']
            error_counts = {engine: 0 for engine in engines}
            found_valid_result = None
            def run_query(engine_name, query):
                if error_counts[engine_name] >= error_threshold:
                    print(f"[DEBUG] [WEBSEARCH] Skipping {engine_name} due to repeated errors.")
                    return []
                try:
                    results = web_engine.search_with_engine(query, engine_name, num_results=20)
                    time.sleep(1.5)
                    return results
                except Exception as e:
                    print(f"[DEBUG] [WEBSEARCH] {engine_name} search error: {e}")
                    error_counts[engine_name] += 1
                    return []
            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                future_to_info = {}
                for query_info in queries[:query_limit]:
                    query = query_info['query']
                    for engine_name in engines:
                        if error_counts[engine_name] < error_threshold:
                            future = executor.submit(run_query, engine_name, query)
                            future_to_info[future] = (engine_name, query)
                start_time = time.time()
                try:
                    for future in concurrent.futures.as_completed(future_to_info, timeout=global_timeout):
                        engine_name, query = future_to_info[future]
                        results = future.result()
                        if not results:
                            print(f"[DEBUG] [WEBSEARCH] No results from {engine_name} for query: {query}")
                            continue
                        for result in results:
                            url = result.get('url')
                            if url and url not in seen_urls:
                                seen_urls.add(url)
                                all_results.append(result)
                                legal_results = enhanced_engine.filter_legal_results([result])
                                if legal_results:
                                    best = legal_results[0]
                                    candidate_name = best.get('title')
                                    is_valid = is_valid_case_name(candidate_name)
                                    if is_valid:
                                        print(f"[DEBUG] [WEBSEARCH] Found valid canonical result: {candidate_name} | URL: {best.get('url')}")
                                        found_valid_result = best
                                        break
                            if len(all_results) >= max_results or found_valid_result:
                                break
                        if len(all_results) >= max_results or found_valid_result:
                            break
                        if time.time() - start_time > global_timeout:
                            print(f"[DEBUG] [WEBSEARCH] Timeout reached, stopping websearch early.")
                    if found_valid_result:
                        pass
                except concurrent.futures.TimeoutError:
                    print(f"[DEBUG] [WEBSEARCH] Global websearch timeout ({global_timeout}s) reached.")
                finally:
                    pass
            if found_valid_result:
                candidate_name = found_valid_result.get('title')
                url = found_valid_result.get('url')
                domain = None
                if url:
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc.lower()
                if not domain:
                    domain = found_valid_result.get('source', 'Web Search')
                return CanonicalResult(
                    case_name=candidate_name,
                    date=None,  # Date extraction can be added if available
                    court=None,
                    docket_number=None,
                    url=url,
                    source=domain,
                    confidence=found_valid_result.get('legal_relevance_score', 0) / 100.0,
                    verified=found_valid_result.get('legal_relevance_score', 0) >= 70
                )

            # TODO: Integrate Google Custom Search API here if/when available

            # Filter and score results
            legal_results = enhanced_engine.filter_legal_results(all_results)
            print(f"[DEBUG] [WEBSEARCH] Top filtered legal results:")
            for res in legal_results[:5]:
                print(f"  Score: {res.get('legal_relevance_score', 0)} | Title: {res.get('title')} | URL: {res.get('url')}")

            # Use the best result for canonical extraction
            if legal_results:
                best = legal_results[0]
                candidate_name = best.get('title')
                is_valid = is_valid_case_name(candidate_name)
                print(f"[DEBUG] [WEBSEARCH] Candidate name: {candidate_name}, is_valid: {is_valid}")
                if not is_valid:
                    print(f"[DEBUG] [WEBSEARCH] Rejected candidate name: {candidate_name}")
                    return None
                print(f"[DEBUG] [WEBSEARCH] Accepted candidate name: {candidate_name}")
                url = best.get('url')
                domain = None
                if url:
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc.lower()
                if not domain:
                    domain = best.get('source', 'Web Search')
                return CanonicalResult(
                    case_name=candidate_name,
                    date=None,  # Date extraction can be added if available
                    court=None,
                    docket_number=None,
                    url=url,
                    source=domain,
                    confidence=best.get('legal_relevance_score', 0) / 100.0,
                    verified=best.get('legal_relevance_score', 0) >= 70
                )
            else:
                print(f"[DEBUG] [WEBSEARCH] No legal results returned for citation: {citation}")
        except Exception as e:
            logger.error(f"Web search lookup failed: {e}")
            import traceback
            logger.error(f"Exception traceback: {traceback.format_exc()}")
            print(f"[DEBUG] [WEBSEARCH] Exception occurred: {e}")
        return None

def is_valid_case_name(name: str) -> bool:
    """Return True if the name looks like a real legal case name (e.g., contains ' v. ' or ' vs. ')."""
    if not name or not isinstance(name, str):
        return False
    import re
    # Require ' v. ' or ' vs. ' with spaces (case-insensitive)
    if not re.search(r"\s(v\.|vs\.|v|vs)\s", name, re.IGNORECASE):
        return False
    # Exclude domains, URLs, or generic titles
    if re.search(r"(\.com|\.net|\.org|https?://|store|watch|eventify|app|allareacodes|youtube|steampowered|outlook)", name, re.IGNORECASE):
        return False
    # Exclude names that are too short or generic
    if len(name.strip()) < 7:
        return False
    return True

# Global service instance
_canonical_service = None

def get_canonical_case_name_with_date(citation: str, api_key: str = None) -> Optional[Dict[str, Any]]:
    """
    Main function to get canonical case name and date information.
    
    Args:
        citation: The citation string to look up
        api_key: Optional API key (for backward compatibility)
        
    Returns:
        Dictionary with case_name, date, court, etc. or None if not found
    """
    global _canonical_service
    
    if _canonical_service is None:
        _canonical_service = CanonicalCaseNameService()
    
    try:
        # Normalize citation for lookup
        normalized_citation = _canonical_service._normalize_citation(citation)
        logger.info(f"get_canonical_case_name_with_date called for: {citation} (normalized: {normalized_citation})")
        
        # Perform cached lookup
        result = _canonical_service._cached_lookup(normalized_citation)
        logger.info(f"get_canonical_case_name_with_date result: {result}")
        
        # TOP-LEVEL HARDFILTER: Only return if case_name is valid (applies to all results, even from cache)
        from src.canonical_case_name_service import is_valid_case_name
        if result and result.case_name:
            if not is_valid_case_name(result.case_name):
                logger.warning(f"[TOP-HARDFILTER] Rejected result for '{citation}': '{result.case_name}' is not a valid case name (top-level hard filter)")
                return None
            else:
                logger.info(f"[TOP-HARDFILTER] Accepted result for '{citation}': '{result.case_name}' is a valid case name (top-level hard filter)")
        
        if result:
            # Convert to dictionary for backward compatibility
            return {
                'case_name': result.case_name,
                'date': result.date,
                'court': result.court,
                'docket_number': result.docket_number,
                'url': result.url,
                'source': result.source,
                'confidence': result.confidence,
                'verified': result.verified,
                'parallel_citations': result.parallel_citations
            }
        
        logger.info(f"No canonical result found for: {citation}")
        return None
        
    except Exception as e:
        logger.error(f"Error in get_canonical_case_name_with_date: {e}")
        return None

def get_canonical_case_name(citation: str, api_key: str = None) -> Optional[str]:
    """
    Simplified function to get just the case name.
    
    Args:
        citation: The citation string to look up
        api_key: Optional API key (for backward compatibility)
        
    Returns:
        Case name string or None if not found
    """
    result = get_canonical_case_name_with_date(citation, api_key)
    return result.get('case_name') if result else None

def test_canonical_lookup():
    """Test function for canonical lookup"""
    import logging
    logger = logging.getLogger(__name__)
    
    test_citations = [
        "171 Wn.2d 486",
        "200 Wn.2d 72", 
        "514 P.3d 643",
        "410 U.S. 113",  # Roe v. Wade
        "347 U.S. 483"   # Brown v. Board
    ]
    
    logger.info("=== Testing Canonical Case Name Lookup ===")
    
    for citation in test_citations:
        logger.info(f"Testing: {citation}")
        result = get_canonical_case_name_with_date(citation)
        
        if result:
            logger.info(f"  ✅ Found: {result['case_name']}")
            logger.info(f"     Date: {result['date']}")
            logger.info(f"     Court: {result['court']}")
            logger.info(f"     Source: {result['source']}")
            logger.info(f"     Confidence: {result['confidence']}")
        else:
            logger.info(f"  ❌ Not found")

if __name__ == "__main__":
    test_canonical_lookup() 