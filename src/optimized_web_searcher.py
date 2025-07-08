"""
Optimized Web Searcher for Legal Citations

This module implements efficient web search strategies for verifying legal citations
that are not found in CourtListener. It uses intelligent prioritization, caching,
and parallel processing to maximize success rates while minimizing API calls.
"""

import asyncio
import aiohttp
import logging
import re
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os

logger = logging.getLogger(__name__)

class OptimizedWebSearcher:
    """
    Optimized web searcher for legal citations with intelligent method prioritization.
    """
    
    def __init__(self):
        self.session = None
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour
        self.method_stats = {
            'google': {'success': 0, 'total': 0, 'avg_time': 0},
            'justia': {'success': 0, 'total': 0, 'avg_time': 0},
            'findlaw': {'success': 0, 'total': 0, 'avg_time': 0},
            'courtlistener': {'success': 0, 'total': 0, 'avg_time': 0},
            'leagle': {'success': 0, 'total': 0, 'avg_time': 0},
            'openjurist': {'success': 0, 'total': 0, 'avg_time': 0},
            'bing': {'success': 0, 'total': 0, 'avg_time': 0},
            'duckduckgo': {'success': 0, 'total': 0, 'avg_time': 0}
        }
        self.rate_limits = {
            'google': {'requests': 0, 'last_request': 0, 'max_per_minute': 10},
            'bing': {'requests': 0, 'last_request': 0, 'max_per_minute': 20},
            'duckduckgo': {'requests': 0, 'last_request': 0, 'max_per_minute': 20},
            'justia': {'requests': 0, 'last_request': 0, 'max_per_minute': 30},
            'findlaw': {'requests': 0, 'last_request': 0, 'max_per_minute': 20},
            'courtlistener': {'requests': 0, 'last_request': 0, 'max_per_minute': 30},
            'leagle': {'requests': 0, 'last_request': 0, 'max_per_minute': 20},
            'openjurist': {'requests': 0, 'last_request': 0, 'max_per_minute': 20},
        }
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
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
        limit_info = self.rate_limits[method]
        if now - limit_info['last_request'] < 60 / limit_info['max_per_minute']:
            return False
        limit_info['last_request'] = now
        return True
    
    def _update_stats(self, method: str, success: bool, duration: float):
        """Update method statistics."""
        stats = self.method_stats[method]
        stats['total'] += 1
        if success:
            stats['success'] += 1
        stats['avg_time'] = (stats['avg_time'] * (stats['total'] - 1) + duration) / stats['total']
    
    def get_search_priority(self) -> List[str]:
        """Get search methods in priority order."""
        return [
            'justia',
            'findlaw',
            'courtlistener',
            'leagle',
            'openjurist',
            'bing',
            'duckduckgo',
            'google',
        ]
    
    async def search_google(self, citation: str, case_name: str = None) -> Dict:
        """Search Google for legal citations."""
        if not self._respect_rate_limit('google'):
            return {'verified': False, 'error': 'Rate limited'}
        
        start_time = time.time()
        try:
            # Construct search query - try multiple variations
            queries = []
            
            # Primary query: citation + case name
            if case_name:
                queries.append(f'"{citation}" "{case_name}" legal case')
            
            # Secondary query: just citation
            queries.append(f'"{citation}" legal case')
            
            # Tertiary query: citation without quotes
            queries.append(f'{citation} legal case')
            
            # Quaternary query: search on legal sites
            queries.append(f'"{citation}" site:justia.com OR site:findlaw.com OR site:law.cornell.edu')
            
            for query in queries:
                try:
                    encoded_query = quote_plus(query)
                    url = f"https://www.google.com/search?q={encoded_query}"
                    
                    # Add better headers to avoid blocking
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Cache-Control': 'max-age=0'
                    }
                    
                    async with self.session.get(url, headers=headers, timeout=15) as response:
                        if response.status == 429:
                            return {'verified': False, 'error': 'Rate limited by Google'}
                        elif response.status != 200:
                            continue  # Try next query
                        
                        content = await response.text()
                        
                        # Look for citation patterns in the results - more flexible matching
                        citation_clean = re.sub(r'[^\w\s\.]', '', citation)  # Remove punctuation
                        patterns = [
                            rf'\b{re.escape(citation)}\b',
                            rf'\b{re.escape(citation_clean)}\b',
                            rf'\b{re.escape(citation.lower())}\b',
                            rf'\b{re.escape(citation.upper())}\b',
                            rf'\b{re.escape(citation.replace(" ", ""))}\b',
                            rf'\b{re.escape(citation.replace(" ", " "))}\b',  # Handle extra spaces
                        ]
                        
                        for pattern in patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                duration = time.time() - start_time
                                self._update_stats('google', True, duration)
                                return {
                                    'verified': True,
                                    'source': 'google',
                                    'url': url,
                                    'confidence': 0.8,
                                    'method': 'google'
                                }
                        
                        # If we get here, try the next query
                        continue
                        
                except Exception as e:
                    continue  # Try next query
            
            # If all queries failed
            duration = time.time() - start_time
            self._update_stats('google', False, duration)
            return {'verified': False, 'error': 'Citation not found in any query variation'}
                
        except Exception as e:
            duration = time.time() - start_time
            self._update_stats('google', False, duration)
            logger.debug(f"Google search failed: {e}")
            return {'verified': False, 'error': str(e)}
    
    async def search_justia(self, citation: str, case_name: str = None) -> Dict:
        """Search Justia for legal citations."""
        if not self._respect_rate_limit('justia'):
            return {'verified': False, 'error': 'Rate limited'}
        
        start_time = time.time()
        try:
            # Try multiple search approaches
            search_urls = []
            
            # Primary: Direct case URL construction for US Supreme Court
            if 'U.S.' in citation:
                # Extract volume and page from "410 U.S. 113"
                match = re.search(r'(\d+)\s+U\.S\.\s+(\d+)', citation)
                if match:
                    volume, page = match.groups()
                    search_urls.append(f"https://supreme.justia.com/cases/federal/us/{volume}/{page}/")
            
            # Secondary: Search by citation
            search_urls.append(f"https://law.justia.com/search?query={quote_plus(citation)}")
            
            # Tertiary: Search by citation + case name
            if case_name:
                search_urls.append(f"https://law.justia.com/search?query={quote_plus(f'{citation} {case_name}')}")
            
            # Quaternary: Search in cases section
            search_urls.append(f"https://law.justia.com/cases/search?query={quote_plus(citation)}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            for url in search_urls:
                try:
                    async with self.session.get(url, headers=headers, timeout=10) as response:
                        if response.status == 200:
                            content = await response.text()
                            
                            # Check if citation appears in content
                            if re.search(re.escape(citation), content, re.IGNORECASE):
                                duration = time.time() - start_time
                                self._update_stats('justia', True, duration)
                                return {
                                    'verified': True,
                                    'source': 'justia',
                                    'url': url,
                                    'confidence': 0.9,
                                    'method': 'justia'
                                }
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
    
    async def search_oscn(self, citation: str, case_name: str = None) -> Dict:
        """Search Oklahoma State Courts Network for OK citations."""
        if not self._respect_rate_limit('oscn'):
            return {'verified': False, 'error': 'Rate limited'}
        
        start_time = time.time()
        try:
            # Check if it's an Oklahoma citation
            if not re.search(r'\d+\s+ok\s+\d+', citation, re.IGNORECASE):
                return {'verified': False, 'error': 'Not an Oklahoma citation'}
            
            # Extract volume and page
            match = re.search(r'(\d+)\s+ok\s+(\d+)', citation, re.IGNORECASE)
            if not match:
                return {'verified': False, 'error': 'Invalid Oklahoma citation format'}
            
            volume, page = match.groups()
            
            # Try direct URL construction
            url = f"https://www.oscn.net/applications/oscn/DeliverDocument.asp?CiteID={volume}OK{page}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Check if it's a valid case page
                    if 'Case Details' in content or 'Opinion' in content:
                        duration = time.time() - start_time
                        self._update_stats('oscn', True, duration)
                        return {
                            'verified': True,
                            'source': 'oscn',
                            'url': url,
                            'confidence': 0.95,
                            'method': 'oscn'
                        }
                
                duration = time.time() - start_time
                self._update_stats('oscn', False, duration)
                return {'verified': False, 'error': 'Citation not found'}
                
        except Exception as e:
            duration = time.time() - start_time
            self._update_stats('oscn', False, duration)
            logger.debug(f"OSCN search failed: {e}")
            return {'verified': False, 'error': str(e)}
    
    def _extract_citation_components(self, citation: str) -> Dict:
        """Extract components from citation string."""
        components = {}
        
        # Federal reporter patterns
        fed_patterns = [
            r'(\d+)\s+(F\.\d+[a-z]?)\s+(\d+)',
            r'(\d+)\s+(F\.Supp\.\d*)\s+(\d+)',
            r'(\d+)\s+(U\.S\.)\s+(\d+)',
            r'(\d+)\s+(S\.Ct\.)\s+(\d+)'
        ]
        
        for pattern in fed_patterns:
            match = re.search(pattern, citation, re.IGNORECASE)
            if match:
                components['volume'] = match.group(1)
                components['reporter'] = match.group(2)
                components['page'] = match.group(3)
                break
        
        return components
    
    async def search_parallel(self, citation: str, case_name: str = None, max_workers: int = 3) -> Dict:
        """Search multiple sources in parallel with intelligent prioritization."""
        priority_methods = self.get_search_priority()
        
        # Limit to max_workers methods
        methods_to_try = priority_methods[:max_workers]
        
        # Create tasks for parallel execution
        tasks = []
        for method in methods_to_try:
            if method == 'google':
                task = self.search_google(citation, case_name)
            elif method == 'justia':
                task = self.search_justia(citation, case_name)
            elif method == 'oscn':
                task = self.search_oscn(citation, case_name)
            elif method == 'bing':
                task = self.search_bing(citation, case_name)
            elif method == 'duckduckgo':
                task = self.search_duckduckgo(citation, case_name)
            elif method == 'findlaw':
                task = self.search_findlaw(citation, case_name)
            elif method == 'courtlistener':
                task = self.search_courtlistener(citation, case_name)
            elif method == 'leagle':
                task = self.search_leagle(citation, case_name)
            elif method == 'openjurist':
                task = self.search_openjurist(citation, case_name)
            elif method == 'descrybe':
                task = self.search_descrybe(citation, case_name)
            elif method == 'midpage':
                task = self.search_midpage(citation, case_name)
            else:
                continue
            tasks.append((method, task))
        
        # Execute tasks and return first successful result
        for method, task in tasks:
            try:
                result = await task
                if result.get('verified'):
                    return result
            except Exception as e:
                logger.debug(f"Method {method} failed: {e}")
                continue
        
        return {'verified': False, 'error': 'All methods failed'}
    
    def get_method_stats(self) -> Dict:
        """Get current method statistics."""
        stats = {}
        for method, data in self.method_stats.items():
            success_rate = data['success'] / data['total'] if data['total'] > 0 else 0
            stats[method] = {
                'success_rate': success_rate,
                'total_calls': data['total'],
                'successful_calls': data['success'],
                'avg_response_time': data['avg_time']
            }
        return stats
    
    def optimize_search_strategy(self) -> List[str]:
        """Optimize search strategy based on current statistics."""
        stats = self.get_method_stats()
        
        # Sort methods by success rate and speed
        method_scores = []
        for method, data in stats.items():
            if data['total_calls'] > 0:
                # Score based on success rate and inverse of response time
                score = data['success_rate'] * (1 / (data['avg_response_time'] + 0.1))
                method_scores.append((method, score))
        
        # Sort by score (highest first)
        method_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [method for method, score in method_scores]
    
    async def search_bing(self, citation: str, case_name: str = None) -> Dict:
        """Search Bing for legal citations."""
        if not self._respect_rate_limit('bing'):
            return {'verified': False, 'error': 'Rate limited'}
        
        start_time = time.time()
        try:
            # Construct search query
            queries = []
            
            # Primary query: citation + case name
            if case_name:
                queries.append(f'"{citation}" "{case_name}" legal case')
            
            # Secondary query: just citation
            queries.append(f'"{citation}" legal case')
            
            # Tertiary query: citation without quotes
            queries.append(f'{citation} legal case')
            
            for query in queries:
                try:
                    encoded_query = quote_plus(query)
                    url = f"https://www.bing.com/search?q={encoded_query}"
                    
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate',
                        'Connection': 'keep-alive',
                    }
                    
                    async with self.session.get(url, headers=headers) as response:
                        if response.status != 200:
                            continue
                        
                        content = await response.text()
                        
                        # Look for citation patterns in the results
                        citation_clean = re.sub(r'[^\w\s\.]', '', citation)
                        patterns = [
                            rf'\b{re.escape(citation)}\b',
                            rf'\b{re.escape(citation_clean)}\b',
                            rf'\b{re.escape(citation.lower())}\b',
                            rf'\b{re.escape(citation.upper())}\b',
                        ]
                        
                        for pattern in patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                duration = time.time() - start_time
                                self._update_stats('bing', True, duration)
                                return {
                                    'verified': True,
                                    'source': 'bing',
                                    'url': url,
                                    'confidence': 0.7,
                                    'method': 'bing'
                                }
                        
                        continue
                        
                except Exception as e:
                    continue
            
            duration = time.time() - start_time
            self._update_stats('bing', False, duration)
            return {'verified': False, 'error': 'Citation not found'}
                
        except Exception as e:
            duration = time.time() - start_time
            self._update_stats('bing', False, duration)
            logger.debug(f"Bing search failed: {e}")
            return {'verified': False, 'error': str(e)}

    async def search_duckduckgo(self, citation: str, case_name: str = None) -> Dict:
        """Search DuckDuckGo for legal citations using the official API."""
        if not self._respect_rate_limit('duckduckgo'):
            return {'verified': False, 'error': 'Rate limited'}
        
        start_time = time.time()
        try:
            from duckduckgo_search import DDGS
            
            # Construct search queries
            queries = []
            
            # Primary query: citation + case name
            if case_name:
                queries.append(f'"{citation}" "{case_name}" legal case')
            
            # Secondary query: just citation
            queries.append(f'"{citation}" legal case')
            
            # Tertiary query: citation without quotes
            queries.append(f'{citation} legal case')
            
            # Quaternary query: search on legal sites
            queries.append(f'"{citation}" site:justia.com OR site:findlaw.com OR site:law.cornell.edu')
            
            with DDGS() as ddgs:
                for query in queries:
                    try:
                        # Get search results
                        results = list(ddgs.text(query, max_results=10))
                        
                        # Check if any result contains the citation
                        for result in results:
                            # Check title and snippet for citation
                            content = f"{result.get('title', '')} {result.get('body', '')}"
                            
                            if re.search(re.escape(citation), content, re.IGNORECASE):
                                duration = time.time() - start_time
                                self._update_stats('duckduckgo', True, duration)
                                return {
                                    'verified': True,
                                    'source': 'duckduckgo',
                                    'url': result.get('link', ''),
                                    'confidence': 0.8,
                                    'method': 'duckduckgo',
                                    'title': result.get('title', ''),
                                    'snippet': result.get('body', '')
                                }
                        
                    except Exception as e:
                        logger.debug(f"DuckDuckGo query '{query}' failed: {e}")
                        continue
            
            duration = time.time() - start_time
            self._update_stats('duckduckgo', False, duration)
            return {'verified': False, 'error': 'Citation not found'}
            
        except Exception as e:
            duration = time.time() - start_time
            self._update_stats('duckduckgo', False, duration)
            logger.debug(f"DuckDuckGo search failed: {e}")
            return {'verified': False, 'error': str(e)}

    async def search_findlaw(self, citation: str, case_name: str = None) -> dict:
        """Search FindLaw for a legal citation."""
        from urllib.parse import quote_plus
        import re
        
        # Try multiple search approaches
        search_urls = []
        
        # Primary: Search by citation
        search_urls.append(f"https://caselaw.findlaw.com/search?query={quote_plus(citation)}")
        
        # Secondary: Search by citation + case name
        if case_name:
            search_urls.append(f"https://caselaw.findlaw.com/search?query={quote_plus(f'{citation} {case_name}')}")
        
        # Tertiary: Try direct case URL for US Supreme Court
        if 'U.S.' in citation:
            match = re.search(r'(\d+)\s+U\.S\.\s+(\d+)', citation)
            if match:
                volume, page = match.groups()
                search_urls.append(f"https://caselaw.findlaw.com/us-supreme-court/{volume}/{page}.html")
        
        # Quaternary: Try different search endpoint
        search_urls.append(f"https://caselaw.findlaw.com/search?q={quote_plus(citation)}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
            "Referer": "https://www.google.com/"
        }
        
        for url in search_urls:
            try:
                async with self.session.get(url, headers=headers, timeout=10) as resp:
                    if resp.status != 200:
                        continue
                    html = await resp.text()
                    # Look for citation in the page content
                    if re.search(re.escape(citation), html, re.IGNORECASE):
                        return {
                            "verified": True,
                            "source": "findlaw",
                            "url": str(resp.url),
                            "confidence": 0.8,
                            "method": "findlaw"
                        }
            except Exception as e:
                logger.debug(f"FindLaw URL {url} failed: {e}")
                continue
        
        return {"verified": False, "error": "Citation not found"}

    async def search_courtlistener(self, citation: str, case_name: str = None) -> dict:
        from urllib.parse import quote_plus
        import re
        query = f'"{citation}"'
        if case_name:
            query += f' "{case_name}"'
        url = f"https://www.courtlistener.com/?q={quote_plus(query)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept-Language": "en-US,en;q=0.9",
        }
        async with self.session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return {"verified": False, "error": f"HTTP {resp.status}"}
            html = await resp.text()
            if re.search(re.escape(citation), html, re.IGNORECASE):
                return {
                    "verified": True,
                    "source": "courtlistener",
                    "url": str(resp.url),
                    "confidence": 0.7,
                    "method": "courtlistener"
                }
            return {"verified": False, "error": "Citation not found"}

    async def search_leagle(self, citation: str, case_name: str = None) -> dict:
        """Search Leagle for a legal citation using session and cookies."""
        from urllib.parse import quote_plus
        import re
        
        url = f"https://www.leagle.com/leaglesearch?cite={quote_plus(citation)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Referer": "https://www.leagle.com/"
        }
        try:
            # Step 1: Load the search form to get cookies
            async with self.session.get("https://www.leagle.com/leaglesearch", headers=headers, timeout=10) as resp:
                _ = await resp.text()
            # Step 2: Perform the citation search with cookies and headers
            async with self.session.get(url, headers=headers, timeout=10) as resp:
                if resp.status != 200:
                    return {"verified": False, "error": f"HTTP {resp.status}"}
                html = await resp.text()
                # Look for citation in the page content
                if re.search(re.escape(citation), html, re.IGNORECASE):
                    return {
                        "verified": True,
                        "source": "leagle",
                        "url": str(resp.url),
                        "confidence": 0.8,
                        "method": "leagle"
                    }
        except Exception as e:
            logger.debug(f"Leagle URL {url} failed: {e}")
        return {"verified": False, "error": "Citation not found"}

    async def search_openjurist(self, citation: str, case_name: str = None) -> dict:
        """Search OpenJurist for a legal citation."""
        from urllib.parse import quote_plus
        import re
        query = f'"{citation}"'
        if case_name:
            query += f' "{case_name}"'
        url = f"https://openjurist.org/search?q={quote_plus(query)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        try:
            async with self.session.get(url, headers=headers, timeout=5) as resp:
                if resp.status != 200:
                    return {"verified": False, "error": f"HTTP {resp.status}"}
                html = await resp.text()
                # Look for citation in the page content
                if re.search(re.escape(citation), html, re.IGNORECASE):
                    return {
                        "verified": True,
                        "source": "openjurist",
                        "url": str(resp.url),
                        "confidence": 0.7,
                        "method": "openjurist"
                    }
                return {"verified": False, "error": "Citation not found"}
        except asyncio.TimeoutError:
            return {"verified": False, "error": "Timeout"}
        except Exception as e:
            return {"verified": False, "error": str(e)}

    async def search_descrybe(self, citation: str, case_name: str = None) -> dict:
        """Search Descrybe.ai for a legal citation."""
        from urllib.parse import quote_plus
        import re
        
        start_time = time.time()
        
        try:
            # Clean citation for search
            clean_citation = citation.replace(' ', '+').replace('.', '')
            url = f"https://descrybe.ai/search?q={clean_citation}"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
            
            async with self.session.get(url, headers=headers, timeout=10) as resp:
                if resp.status != 200:
                    duration = time.time() - start_time
                    self._update_stats('descrybe', False, duration)
                    return {"verified": "false", "error": f"HTTP {resp.status}"}
                
                html = await resp.text()
                # Look for citation in the page content
                if re.search(re.escape(citation), html, re.IGNORECASE):
                    duration = time.time() - start_time
                    self._update_stats('descrybe', True, duration)
                    return {
                        "verified": "true",
                        "source": "descrybe",
                        "url": str(resp.url),
                        "confidence": 0.8,
                        "method": "descrybe"
                    }
                
                duration = time.time() - start_time
                self._update_stats('descrybe', False, duration)
                return {"verified": "false", "error": "Citation not found"}
                
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            self._update_stats('descrybe', False, duration)
            return {"verified": "false", "error": "Timeout"}
        except Exception as e:
            duration = time.time() - start_time
            self._update_stats('descrybe', False, duration)
            logger.debug(f"Descrybe search failed: {e}")
            return {"verified": "false", "error": str(e)}

    async def search_midpage(self, citation: str, case_name: str = None) -> dict:
        """Search Midpage.ai for a legal citation."""
        from urllib.parse import quote_plus
        import re
        
        start_time = time.time()
        
        try:
            # Clean citation for search
            clean_citation = citation.replace(' ', '+').replace('.', '')
            url = f"https://midpage.ai/search?q={clean_citation}"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
            
            async with self.session.get(url, headers=headers, timeout=10) as resp:
                if resp.status != 200:
                    duration = time.time() - start_time
                    self._update_stats('midpage', False, duration)
                    return {"verified": "false", "error": f"HTTP {resp.status}"}
                
                html = await resp.text()
                # Look for citation in the page content
                if re.search(re.escape(citation), html, re.IGNORECASE):
                    duration = time.time() - start_time
                    self._update_stats('midpage', True, duration)
                    return {
                        "verified": "true",
                        "source": "midpage",
                        "url": str(resp.url),
                        "confidence": 0.8,
                        "method": "midpage"
                    }
                
                duration = time.time() - start_time
                self._update_stats('midpage', False, duration)
                return {"verified": "false", "error": "Citation not found"}
                
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            self._update_stats('midpage', False, duration)
            return {"verified": "false", "error": "Timeout"}
        except Exception as e:
            duration = time.time() - start_time
            self._update_stats('midpage', False, duration)
            logger.debug(f"Midpage search failed: {e}")
            return {"verified": "false", "error": str(e)} 