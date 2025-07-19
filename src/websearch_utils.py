# DEPRECATED: Use ComprehensiveWebSearchEngine in src/comprehensive_websearch_engine.py instead of LegalWebSearchEngine.
# This file is retained for legacy reference only and should not be used in new code.
# 
# The ComprehensiveWebSearchEngine provides:
# - All features from LegalWebSearchEngine
# - Enhanced Washington citation variants
# - Advanced case name extraction
# - Specialized legal database extraction
# - Similarity scoring and validation
# - Better reliability scoring
#
# Migration guide: See docs/WEB_SEARCH_MIGRATION.md

import warnings
warnings.warn(
    "LegalWebSearchEngine is deprecated. Use ComprehensiveWebSearchEngine in src/comprehensive_websearch_engine.py instead.",
    DeprecationWarning,
    stacklevel=2
)

"""
Enhanced Legal Web Search Engine
Focused, reliable web searching for legal citations with better error handling and maintainability
"""

import re
import requests
from bs4 import BeautifulSoup
import random
import time
from urllib.parse import quote, urljoin, urlparse
from typing import List, Dict, Set, Optional, Tuple
import json
from datetime import datetime
import hashlib
import logging
from src.citation_normalizer import normalize_citation, generate_citation_variants

logger = logging.getLogger(__name__)

class LegalWebSearchEngine:
    """
    Enhanced legal citation web search with reliability scoring and canonical source prioritization.
    
    Focuses on finding authoritative legal sources through strategic search queries.
    """
    
    def __init__(self, enable_experimental_engines=False):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        
        # Set reasonable timeouts
        self.session.timeout = 5
        
        # Canonical legal databases ranked by reliability
        self.canonical_sources = {
            # Primary official sources (highest reliability)
            'courtlistener.com': {'weight': 100, 'type': 'primary', 'official': True},
            'justia.com': {'weight': 95, 'type': 'primary', 'official': True},
            'leagle.com': {'weight': 90, 'type': 'primary', 'official': True},
            'caselaw.findlaw.com': {'weight': 85, 'type': 'primary', 'official': True},
            'scholar.google.com': {'weight': 80, 'type': 'primary', 'official': True},
            'cetient.com': {'weight': 85, 'type': 'primary', 'official': True},
            'casetext.com': {'weight': 75, 'type': 'primary', 'official': False},
            'openjurist.org': {'weight': 65, 'type': 'secondary', 'official': False},
            
            # Government sources (very high reliability)
            'supremecourt.gov': {'weight': 100, 'type': 'government', 'official': True},
            'uscourts.gov': {'weight': 100, 'type': 'government', 'official': True},
            
            # Academic sources
            'law.cornell.edu': {'weight': 70, 'type': 'academic', 'official': False},
            'law.duke.edu': {'weight': 60, 'type': 'academic', 'official': False},
            
            # Commercial but reliable (lower priority)
            'westlaw.com': {'weight': 85, 'type': 'commercial', 'official': False},
            'lexis.com': {'weight': 85, 'type': 'commercial', 'official': False},
        }
        
        # Rate limiting configuration
        self.rate_limits = {
            'google': {'delay': 2.0, 'last_request': 0},
            'bing': {'delay': 1.5, 'last_request': 0},
            'ddg': {'delay': 1.0, 'last_request': 0}
        }
        
        # Search engines to use
        self.enabled_engines = ['google', 'bing']
        if enable_experimental_engines:
            self.enabled_engines.append('ddg')
        
        # Cache for parsed domains to avoid repeated parsing
        self._domain_cache = {}
        
    def normalize_citation(self, citation: str) -> Dict[str, str]:
        """Extract and normalize citation components with better pattern matching."""
        if not citation:
            return {'original': '', 'normalized': ''}
            
        citation = citation.strip()
        
        # Enhanced citation patterns with more specificity
        patterns = {
            'us_supreme': r'(\d+)\s+(U\.?S\.?)\s+(\d+)(?:\s+\((\d{4})\))?',
            'federal_circuit': r'(\d+)\s+(F\.?\d*d?)\s+(\d+)(?:\s+\(([^)]+)\))?',
            'federal_supp': r'(\d+)\s+(F\.?\s*Supp\.?\s*\d*d?)\s+(\d+)(?:\s+\(([^)]+)\))?',
            'state_pacific': r'(\d+)\s+(P\.?\d*d?)\s+(\d+)(?:\s+\(([^)]+)\))?',
            'washington': r'(\d+)\s+(Wn\.?\s*(?:2d|App\.?))\s+(\d+)(?:\s+\((\d{4})\))?',
            'new_york': r'(\d+)\s+(N\.?Y\.?\s*\d*d?)\s+(\d+)(?:\s+\((\d{4})\))?',
            'california': r'(\d+)\s+(Cal\.?\s*\d*d?)\s+(\d+)(?:\s+\(([^)]+)\))?',
        }
        
        for pattern_name, pattern in patterns.items():
            match = re.search(pattern, citation, re.IGNORECASE)
            if match:
                groups = match.groups()
                reporter = groups[1]
                
                # Normalize Washington citations: Wn.2d -> Wash.2d, Wn.App -> Wash.App
                if pattern_name == 'washington':
                    if 'Wn.2d' in reporter or 'Wn. 2d' in reporter:
                        reporter = reporter.replace('Wn.', 'Wash.').replace('Wn ', 'Wash. ')
                    elif 'Wn.App' in reporter or 'Wn. App' in reporter:
                        reporter = reporter.replace('Wn.', 'Wash.').replace('Wn ', 'Wash. ')
                
                normalized_citation = f"{groups[0]} {reporter} {groups[2]}"
                
                return {
                    'volume': groups[0],
                    'reporter': reporter,
                    'page': groups[2],
                    'year': groups[3] if len(groups) > 3 and groups[3] else None,
                    'type': pattern_name,
                    'normalized': normalized_citation,
                    'original': citation
                }
        
        return {'original': citation, 'normalized': citation}
    
    def extract_case_name_variants(self, case_name: str) -> Set[str]:
        """Generate search variants of a case name with improved cleaning."""
        if not case_name or case_name in ('N/A', 'Unknown', ''):
            return set()
            
        variants = set()
        case_name = case_name.strip()
        
        if len(case_name) < 3:  # Skip very short names
            return set()
            
        variants.add(case_name)
        
        # Clean corporate suffixes more aggressively
        corporate_suffixes = [
            r'\b(?:LLC|Inc\.?|Corp\.?|Co\.?|Ltd\.?|L\.P\.?|LLP|LP)\b',
            r'\b(?:Corporation|Company|Limited|Partnership)\b'
        ]
        
        cleaned = case_name
        for suffix_pattern in corporate_suffixes:
            cleaned = re.sub(suffix_pattern, '', cleaned, flags=re.I)
        
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        if cleaned and cleaned != case_name and len(cleaned) > 3:
            variants.add(cleaned)
        
        # Extract party names from "X v. Y" format
        adversarial_match = re.search(r'^([^v]+)\s+v\.?\s+([^,\(]+)', case_name, re.I)
        if adversarial_match:
            plaintiff = adversarial_match.group(1).strip()
            defendant = adversarial_match.group(2).strip()
            
            if len(plaintiff) > 2 and len(defendant) > 2:
                variants.add(f"{plaintiff} v. {defendant}")
                variants.add(f"{plaintiff} v {defendant}")
                
                # Add individual parties only if they're substantial
                if len(plaintiff) > 4:
                    variants.add(plaintiff)
                if len(defendant) > 4:
                    variants.add(defendant)
        
        # Handle "In re" and "Ex parte" cases
        special_case_match = re.search(r'^(?:In re|Ex parte)\s+(.+)', case_name, re.I)
        if special_case_match:
            subject = special_case_match.group(1).strip()
            if len(subject) > 3:
                variants.add(subject)
        
        return {v for v in variants if len(v.strip()) > 2}
    
    def generate_strategic_queries(self, cluster: Dict) -> List[Dict[str, str]]:
        """Generate focused, strategic search queries with better prioritization."""
        queries = []
        
        # Extract citations with validation and normalization
        citations = set()
        normalized_citations = set()
        for citation_obj in cluster.get('citations', []):
            citation = citation_obj.get('citation', '').strip()
            if citation and len(citation) > 5:  # Basic validation
                citations.add(citation)
                # Normalize citation for better websearch results
                normalized = normalize_citation(citation)
                if normalized.get('normalized') and normalized['normalized'] != citation:
                    normalized_citations.add(normalized['normalized'])
        
        # Extract case names with validation
        case_names = set()
        for name_field in ['canonical_name', 'extracted_case_name', 'case_name']:
            if cluster.get(name_field):
                case_names.update(self.extract_case_name_variants(cluster[name_field]))
        
        # Extract years
        years = set()
        for date_field in ['canonical_date', 'extracted_date', 'date']:
            if cluster.get(date_field):
                year_match = re.search(r'\b(19|20)\d{2}\b', str(cluster[date_field]))
                if year_match:
                    years.add(year_match.group(0))
        
        # Priority 1: Exact citation on top canonical sources (original and normalized)
        top_domains = ['courtlistener.com', 'justia.com', 'leagle.com']
        all_citations = list(citations) + list(normalized_citations)
        for citation in all_citations:
            for domain in top_domains:
                queries.append({
                    'query': f'site:{domain} "{citation}"',
                    'priority': 1,
                    'strategy': 'exact_citation_canonical',
                    'target_domain': domain,
                    'expected_reliability': 90
                })
        
        # Priority 2: Citation with legal context indicators (original and normalized)
        for citation in all_citations:
            queries.append({
                'query': f'"{citation}" (opinion OR court OR case OR decision)',
                'priority': 2,
                'strategy': 'citation_with_context',
                'target_domain': None,
                'expected_reliability': 75
            })
        
        # Priority 3: Case name + citation on canonical sources (original and normalized)
        for case_name in list(case_names)[:3]:  # Limit to best case names
            for citation in list(all_citations)[:2]:  # Limit citations
                for domain in ['courtlistener.com', 'justia.com']:
                    queries.append({
                        'query': f'site:{domain} "{case_name}" "{citation}"',
                        'priority': 3,
                        'strategy': 'name_citation_canonical',
                        'target_domain': domain,
                        'expected_reliability': 85
                    })
        
        # Priority 4: Case name + year (for harder to find cases)
        for case_name in list(case_names)[:2]:
            for year in years:
                queries.append({
                    'query': f'"{case_name}" {year} (court OR opinion)',
                    'priority': 4,
                    'strategy': 'name_year_broad',
                    'target_domain': None,
                    'expected_reliability': 60
                })
        
        # Priority 5: Broader citation search (last resort) - original and normalized
        for citation in list(all_citations)[:2]:
            queries.append({
                'query': f'"{citation}"',
                'priority': 5,
                'strategy': 'citation_broad',
                'target_domain': None,
                'expected_reliability': 50
            })
        
        # Sort by priority and limit to reasonable number
        queries.sort(key=lambda x: (x['priority'], -x['expected_reliability']))
        return queries[:15]  # Reasonable limit
    
    def score_result_reliability(self, result: Dict, query_info: Dict) -> float:
        """Enhanced reliability scoring with better domain recognition."""
        score = 0.0
        url = result.get('url', '')
        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()
        
        if not url:
            return 0.0
        
        # Extract domain efficiently
        domain = self._get_domain_from_url(url)
        if not domain:
            return 0.0
        
        # Domain reliability score (primary factor)
        domain_score = 0
        for canonical_domain, info in self.canonical_sources.items():
            if canonical_domain in domain:
                domain_score = info['weight']
                break
        
        # Unknown domains get a base score
        if domain_score == 0:
            domain_score = 30  # Base score for unknown but legitimate domains
        
        score += domain_score * 0.5  # 50% weight to domain
        
        # Content quality indicators (30% weight)
        content = f"{title} {snippet}"
        
        # Strong legal indicators
        strong_indicators = ['opinion', 'court decision', 'case law', 'judicial', 'ruling']
        strong_score = sum(5 for indicator in strong_indicators if indicator in content)
        
        # General legal indicators
        legal_indicators = ['court', 'judge', 'plaintiff', 'defendant', 'circuit', 'district']
        legal_score = sum(2 for indicator in legal_indicators if indicator in content)
        
        content_score = min(strong_score + legal_score, 30)
        score += content_score * 0.3
        
        # Citation presence bonus (15% weight)
        query_text = query_info.get('query', '')
        citations_in_query = re.findall(r'"\d+\s+[A-Z][a-z]*\.?\d*d?\s+\d+"', query_text)
        
        citation_score = 0
        for citation in citations_in_query:
            clean_citation = citation.strip('"')
            if clean_citation.lower() in content:
                citation_score += 15
        
        score += min(citation_score, 15) * 0.15
        
        # URL structure quality (5% weight)
        url_indicators = ['/opinion/', '/case/', '/court/', '/decision/', '/legal/']
        url_score = sum(2 for indicator in url_indicators if indicator in url.lower())
        score += min(url_score, 5) * 0.05
        
        # Penalties for low-quality sources
        penalties = ['blog', 'forum', 'wiki', 'comment', 'discussion']
        penalty = sum(5 for pen in penalties if pen in url.lower() or pen in content)
        score -= penalty
        
        return max(0, min(100, score))
    
    def _get_domain_from_url(self, url: str) -> str:
        """Extract domain from URL with caching."""
        if url in self._domain_cache:
            return self._domain_cache[url]
        
        try:
            domain = urlparse(url).netloc.lower()
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            self._domain_cache[url] = domain
            return domain
        except Exception:
            self._domain_cache[url] = ''
            return ''
    
    def _rate_limit_check(self, engine: str):
        """Improved rate limiting with per-engine tracking."""
        if engine not in self.rate_limits:
            return
        
        config = self.rate_limits[engine]
        now = time.time()
        elapsed = now - config['last_request']
        
        if elapsed < config['delay']:
            sleep_time = config['delay'] - elapsed
            logger.debug(f"Rate limiting {engine}: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.rate_limits[engine]['last_request'] = time.time()
    
    def search_with_engine(self, query: str, engine: str, num_results: int = 5) -> List[Dict]:
        """Execute search with improved error handling and validation."""
        if engine not in self.enabled_engines:
            logger.warning(f"Engine {engine} not enabled")
            return []
        
        # Input validation
        if not query or len(query.strip()) < 3:
            logger.warning(f"Query too short for {engine}: '{query}'")
            return []
        
        self._rate_limit_check(engine)
        
        try:
            if engine == 'google':
                return self._google_search(query, num_results)
            elif engine == 'bing':
                return self._bing_search(query, num_results)
            elif engine == 'ddg':
                return self._ddg_search(query, num_results)
            else:
                logger.error(f"Unknown search engine: {engine}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"{engine} network error for '{query}': {e}")
            return []
        except Exception as e:
            logger.error(f"{engine} search failed for '{query}': {e}")
            return []
    
    def _google_search(self, query: str, num_results: int) -> List[Dict]:
        """Enhanced Google search with better result extraction."""
        params = {
            "q": query, 
            "num": min(num_results, 10),  # Google limits
            "hl": "en",
            "lr": "lang_en"  # English results
        }
        
        try:
            response = self.session.get(
                "https://www.google.com/search", 
                params=params, 
                timeout=5
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Google request failed: {e}")
            return []
        
        if "unusual traffic" in response.text.lower():
            logger.warning("Google detected unusual traffic - may be rate limited")
            return []
        
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        
        # Multiple selectors for robustness
        result_selectors = [
            'div.g',           # Standard result
            'div[data-ved]',   # Alternative
            '.rc',             # Classic
            'div.yuRUbf'       # Newer format
        ]
        
        elements = []
        for selector in result_selectors:
            elements = soup.select(selector)
            if elements:
                break
        
        for elem in elements[:num_results]:
            try:
                # Find link
                link_elem = elem.find('a', href=True)
                if not link_elem:
                    continue
                
                # Find title
                title_elem = elem.find('h3') or link_elem.find('h3')
                if not title_elem:
                    continue
                
                # Find snippet
                snippet_selectors = [
                    'span.aCOpRe', 'div.VwiC3b', 'div.s', '.st', 
                    'span[data-ved]', '.IsZvec'
                ]
                snippet_elem = None
                for sel in snippet_selectors:
                    snippet_elem = elem.select_one(sel)
                    if snippet_elem:
                        break
                
                url = link_elem['href']
                
                # Clean Google redirect URLs
                if url.startswith('/url?q='):
                    url = url.split('&')[0].replace('/url?q=', '')
                
                # Validate URL
                if not url.startswith(('http://', 'https://')):
                    continue
                
                results.append({
                    'url': url,
                    'title': title_elem.get_text(strip=True),
                    'snippet': snippet_elem.get_text(strip=True) if snippet_elem else '',
                    'source': 'google'
                })
                
            except Exception as e:
                logger.debug(f"Error parsing Google result element: {e}")
                continue
        
        return results
    
    def _bing_search(self, query: str, num_results: int) -> List[Dict]:
        """Enhanced Bing search with better parsing."""
        params = {
            "q": query, 
            "count": min(num_results, 20),  # Bing's limit
            "mkt": "en-US"
        }
        
        try:
            response = self.session.get(
                "https://www.bing.com/search", 
                params=params, 
                timeout=5
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Bing request failed: {e}")
            return []
        
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        
        # Bing result selectors
        for li in soup.select('li.b_algo, .b_algo')[:num_results]:
            try:
                # Link and title
                link_elem = li.find('a', href=True)
                if not link_elem:
                    continue
                
                # Snippet
                snippet_selectors = ['p', '.b_caption p', '.b_caption', 'div.b_caption p']
                snippet_elem = None
                for sel in snippet_selectors:
                    snippet_elem = li.select_one(sel)
                    if snippet_elem:
                        break
                
                url = link_elem['href']
                title = link_elem.get_text(strip=True)
                
                if url.startswith('http') and title:
                    results.append({
                        'url': url,
                        'title': title,
                        'snippet': snippet_elem.get_text(strip=True) if snippet_elem else '',
                        'source': 'bing'
                    })
                    
            except Exception as e:
                logger.debug(f"Error parsing Bing result: {e}")
                continue
        
        return results
    
    def _ddg_search(self, query: str, num_results: int) -> List[Dict]:
        """DuckDuckGo search (experimental - less reliable)."""
        try:
            data = {"q": query, "kl": "us-en"}
            response = self.session.post(
                "https://html.duckduckgo.com/html/", 
                data=data, 
                timeout=5
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"DuckDuckGo request failed: {e}")
            return []
        
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        
        for result_div in soup.select('div.result')[:num_results]:
            try:
                link_elem = result_div.find('a', class_='result__a', href=True)
                snippet_elem = result_div.find('a', class_='result__snippet')
                
                if link_elem:
                    results.append({
                        'url': link_elem['href'],
                        'title': link_elem.get_text(strip=True),
                        'snippet': snippet_elem.get_text(strip=True) if snippet_elem else '',
                        'source': 'duckduckgo'
                    })
            except Exception as e:
                logger.debug(f"Error parsing DDG result: {e}")
                continue
        
        return results
    
    def search_cluster_canonical(self, cluster: Dict, max_results: int = 10) -> List[Dict]:
        """
        Main search function: find canonical legal sources for a citation cluster.
        Returns ranked results with reliability scores.
        """
        if not cluster:
            logger.warning("Empty cluster provided to search")
            return []
        
        queries = self.generate_strategic_queries(cluster)
        if not queries:
            logger.warning("No valid queries generated from cluster")
            return []
        
        all_results = []
        seen_urls = set()
        
        logger.info(f"Executing {len(queries)} strategic queries with {len(self.enabled_engines)} engines")
        
        # Execute searches in priority order
        for i, query_info in enumerate(queries):
            if len(all_results) >= max_results:
                break
            
            query = query_info['query']
            logger.debug(f"Query {i+1}: {query} (strategy: {query_info['strategy']})")
            
            # Randomize engine order to distribute load
            engines = self.enabled_engines.copy()
            random.shuffle(engines)
            
            for engine in engines:
                try:
                    results = self.search_with_engine(query, engine, num_results=3)
                    
                    for result in results:
                        url = result['url']
                        if url not in seen_urls and self._is_valid_result(result):
                            # Score result reliability
                            score = self.score_result_reliability(result, query_info)
                            
                            result.update({
                                'reliability_score': score,
                                'query_strategy': query_info['strategy'],
                                'query_priority': query_info['priority'],
                                'search_engine': engine,
                                'expected_reliability': query_info.get('expected_reliability', 50)
                            })
                            
                            all_results.append(result)
                            seen_urls.add(url)
                            
                            if len(all_results) >= max_results:
                                break
                    
                    if len(all_results) >= max_results:
                        break
                        
                except Exception as e:
                    logger.error(f"Search failed for {engine} with query '{query}': {e}")
                    continue
            
            # Brief pause between query batches
            if i < len(queries) - 1:
                time.sleep(0.3)
        
        # Sort by reliability score (highest first)
        all_results.sort(key=lambda x: x['reliability_score'], reverse=True)
        
        logger.info(f"Found {len(all_results)} total results, returning top {min(len(all_results), max_results)}")
        
        return all_results[:max_results]
    
    def _is_valid_result(self, result: Dict) -> bool:
        """Validate search result quality."""
        url = result.get('url', '')
        title = result.get('title', '')
        
        # Basic validation
        if not url or not title:
            return False
        
        # URL validation
        if not url.startswith(('http://', 'https://')):
            return False
        
        # Skip obvious junk
        junk_indicators = ['javascript:', 'mailto:', '#', 'data:']
        if any(indicator in url.lower() for indicator in junk_indicators):
            return False
        
        # Title validation
        if len(title.strip()) < 3:
            return False
        
        return True


# Convenience functions for backward compatibility
def search_cluster_for_canonical_sources(cluster: Dict, max_results: int = 10) -> List[Dict]:
    """Main function to search for canonical legal sources."""
    try:
        from src.comprehensive_websearch_engine import ComprehensiveWebSearchEngine
        engine = ComprehensiveWebSearchEngine(enable_experimental_engines=True)
        return engine.search_cluster_canonical(cluster, max_results)
    except ImportError:
        # Fallback to old engine if comprehensive engine not available
        engine = LegalWebSearchEngine()
        return engine.search_cluster_canonical(cluster, max_results)


def search_all_engines(query: str, num_results: int = 5, engines: List[str] = None) -> List[Dict]:
    """Search multiple engines (backward compatibility)."""
    try:
        from src.comprehensive_websearch_engine import ComprehensiveWebSearchEngine
        engine = ComprehensiveWebSearchEngine(enable_experimental_engines=True)
        return engine.search_all_engines(query, num_results, engines)
    except ImportError:
        # Fallback to old engine if comprehensive engine not available
        engine = LegalWebSearchEngine()
        
        if engines is None:
            engines = engine.enabled_engines
        
        all_results = []
        seen_urls = set()
        
        for search_engine in engines:
            if search_engine in engine.enabled_engines:
                results = engine.search_with_engine(query, search_engine, num_results)
                for result in results:
                    if result['url'] not in seen_urls:
                        all_results.append(result)
                        seen_urls.add(result['url'])
                    if len(all_results) >= num_results:
                        break
            if len(all_results) >= num_results:
                break
        
        return all_results


def test_web_search():
    """Test function for web search functionality."""
    # Test citation
    test_cluster = {
        'citations': [{'citation': '347 U.S. 483'}],
        'canonical_name': 'Brown v. Board of Education',
        'canonical_date': '1954'
    }
    
    logger.info("=== Legal Web Search Test ===")
    engine = LegalWebSearchEngine()
    
    logger.info(f"Enabled engines: {engine.enabled_engines}")
    logger.info(f"Canonical sources: {len(engine.canonical_sources)}")
    
    results = engine.search_cluster_canonical(test_cluster, max_results=5)
    
    logger.info(f"\nFound {len(results)} results:")
    for i, result in enumerate(results, 1):
        logger.info(f"{i}. {result['title']}")
        logger.info(f"   URL: {result['url']}")
        logger.info(f"   Score: {result['reliability_score']:.1f}")
        logger.info(f"   Strategy: {result['query_strategy']}")
        logger.info(f"   Engine: {result['search_engine']}")
        logger.info()


if __name__ == "__main__":
    test_web_search() 