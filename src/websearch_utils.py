import re
import requests
from bs4 import BeautifulSoup
import random
import time
from urllib.parse import quote, urljoin, urlparse
from typing import List, Dict, Set, Optional, Tuple
import json
from datetime import datetime, timedelta
import hashlib

class LegalWebsearchEngine:
    """Enhanced legal citation websearch with reliability scoring and canonical source prioritization."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        
        # Canonical legal databases ranked by reliability
        self.canonical_sources = {
            # Primary official sources (highest reliability)
            'courtlistener.com': {'weight': 100, 'type': 'primary', 'official': True},
            'justia.com': {'weight': 95, 'type': 'primary', 'official': True},
            'leagle.com': {'weight': 90, 'type': 'primary', 'official': True},
            'caselaw.findlaw.com': {'weight': 85, 'type': 'primary', 'official': True},
            'scholar.google.com': {'weight': 80, 'type': 'primary', 'official': True},
            
            # Government sources (very high reliability)
            'supremecourt.gov': {'weight': 100, 'type': 'government', 'official': True},
            'ca1.uscourts.gov': {'weight': 100, 'type': 'government', 'official': True},
            'ca2.uscourts.gov': {'weight': 100, 'type': 'government', 'official': True},
            'ca3.uscourts.gov': {'weight': 100, 'type': 'government', 'official': True},
            'ca4.uscourts.gov': {'weight': 100, 'type': 'government', 'official': True},
            'ca5.uscourts.gov': {'weight': 100, 'type': 'government', 'official': True},
            'ca6.uscourts.gov': {'weight': 100, 'type': 'government', 'official': True},
            'ca7.uscourts.gov': {'weight': 100, 'type': 'government', 'official': True},
            'ca8.uscourts.gov': {'weight': 100, 'type': 'government', 'official': True},
            'ca9.uscourts.gov': {'weight': 100, 'type': 'government', 'official': True},
            'ca10.uscourts.gov': {'weight': 100, 'type': 'government', 'official': True},
            'ca11.uscourts.gov': {'weight': 100, 'type': 'government', 'official': True},
            'cadc.uscourts.gov': {'weight': 100, 'type': 'government', 'official': True},
            'cafc.uscourts.gov': {'weight': 100, 'type': 'government', 'official': True},
            
            # State courts (high reliability)
            'courts.state.ny.us': {'weight': 95, 'type': 'government', 'official': True},
            'courts.ca.gov': {'weight': 95, 'type': 'government', 'official': True},
            'txcourts.gov': {'weight': 95, 'type': 'government', 'official': True},
            
            # Secondary reliable sources
            'casetext.com': {'weight': 75, 'type': 'secondary', 'official': False},
            'law.cornell.edu': {'weight': 70, 'type': 'academic', 'official': False},
            'openjurist.org': {'weight': 65, 'type': 'secondary', 'official': False},
            'law.duke.edu': {'weight': 60, 'type': 'academic', 'official': False},
            
            # Commercial but reliable
            'westlaw.com': {'weight': 85, 'type': 'commercial', 'official': False},
            'lexis.com': {'weight': 85, 'type': 'commercial', 'official': False},
            'bloomberg.com': {'weight': 75, 'type': 'commercial', 'official': False},
        }
        
        # Rate limiting
        self.last_request = {}
        self.min_delay = 1.0  # Minimum delay between requests per engine
        
    def normalize_citation(self, citation: str) -> Dict[str, str]:
        """Extract and normalize citation components."""
        citation = citation.strip()
        
        # Common citation patterns
        patterns = {
            'us_reporter': r'(\d+)\s+(U\.?S\.?)\s+(\d+)',
            'fed_reporter': r'(\d+)\s+(F\.?\d*d?)\s+(\d+)',
            'state_reporter': r'(\d+)\s+([A-Z][a-z]*\.?\d*d?)\s+(\d+)',
            'wash_reporter': r'(\d+)\s+(Wn\.?\d*d?)\s+(\d+)',
            'pacific': r'(\d+)\s+(P\.?\d*d?)\s+(\d+)',
        }
        
        for pattern_name, pattern in patterns.items():
            match = re.search(pattern, citation, re.IGNORECASE)
            if match:
                return {
                    'volume': match.group(1),
                    'reporter': match.group(2),
                    'page': match.group(3),
                    'type': pattern_name,
                    'normalized': f"{match.group(1)} {match.group(2)} {match.group(3)}"
                }
        
        return {'original': citation, 'normalized': citation}
    
    def extract_case_name_variants(self, case_name: str) -> Set[str]:
        """Generate multiple variants of a case name for better search coverage."""
        if not case_name or case_name == 'N/A':
            return set()
            
        variants = set()
        case_name = case_name.strip()
        variants.add(case_name)
        
        # Remove common corporate suffixes
        cleaned = re.sub(r'\b(LLC|Inc\.?|Corp\.?|Co\.?|Ltd\.?|L\.P\.?|LLP)\b', '', case_name, flags=re.I)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        if cleaned and cleaned != case_name:
            variants.add(cleaned)
        
        # Extract just the party names (before "v.")
        v_match = re.search(r'^([^v]+)\s+v\.?\s+([^,]+)', case_name, re.I)
        if v_match:
            plaintiff = v_match.group(1).strip()
            defendant = v_match.group(2).strip()
            variants.add(f"{plaintiff} v. {defendant}")
            variants.add(f"{plaintiff} v {defendant}")
            
            # Individual party names
            variants.add(plaintiff)
            variants.add(defendant)
        
        # Remove punctuation for broader matching
        no_punct = re.sub(r'[^\w\s]', ' ', case_name)
        no_punct = re.sub(r'\s+', ' ', no_punct).strip()
        if no_punct:
            variants.add(no_punct)
        
        return {v for v in variants if len(v.strip()) > 2}
    
    def generate_strategic_queries(self, cluster: Dict) -> List[Dict[str, str]]:
        """Generate strategic search queries prioritizing canonical sources."""
        queries = []
        
        # Extract all citation variants
        citations = set()
        for citation_obj in cluster.get('citations', []):
            if citation_obj.get('citation'):
                citations.add(citation_obj['citation'].strip())
        
        # Extract case name variants
        case_names = set()
        if cluster.get('canonical_name'):
            case_names.update(self.extract_case_name_variants(cluster['canonical_name']))
        if cluster.get('extracted_case_name'):
            case_names.update(self.extract_case_name_variants(cluster['extracted_case_name']))
        
        # Extract years
        years = set()
        for date_field in ['canonical_date', 'extracted_date']:
            if cluster.get(date_field):
                year_match = re.search(r'\b(19|20)\d{2}\b', str(cluster[date_field]))
                if year_match:
                    years.add(year_match.group(0))
        
        # Strategy 1: Direct citation searches on canonical sources
        for citation in citations:
            normalized = self.normalize_citation(citation)
            
            # Primary canonical sources first
            for domain in ['courtlistener.com', 'justia.com', 'leagle.com']:
                queries.append({
                    'query': f'site:{domain} "{citation}"',
                    'priority': 1,
                    'strategy': 'canonical_citation',
                    'target_domain': domain
                })
            
            # Scholar.google.com with citation
            queries.append({
                'query': f'site:scholar.google.com "{citation}" case',
                'priority': 1,
                'strategy': 'scholar_citation',
                'target_domain': 'scholar.google.com'
            })
        
        # Strategy 2: Case name + citation combinations
        for case_name in case_names:
            for citation in citations:
                for domain in ['courtlistener.com', 'justia.com']:
                    queries.append({
                        'query': f'site:{domain} "{case_name}" "{citation}"',
                        'priority': 2,
                        'strategy': 'name_citation_combo',
                        'target_domain': domain
                    })
        
        # Strategy 3: Case name + year on canonical sources
        for case_name in case_names:
            for year in years:
                for domain in ['courtlistener.com', 'justia.com', 'leagle.com']:
                    queries.append({
                        'query': f'site:{domain} "{case_name}" {year}',
                        'priority': 3,
                        'strategy': 'name_year_combo',
                        'target_domain': domain
                    })
        
        # Strategy 4: Broader searches for hard-to-find cases
        for citation in citations:
            queries.append({
                'query': f'"{citation}" "opinion" OR "court" OR "case"',
                'priority': 4,
                'strategy': 'broad_citation',
                'target_domain': None
            })
        
        # Strategy 5: Case name only on canonical sources (last resort)
        for case_name in case_names:
            if len(case_name) > 10:  # Only for substantial case names
                for domain in ['courtlistener.com', 'justia.com']:
                    queries.append({
                        'query': f'site:{domain} "{case_name}"',
                        'priority': 5,
                        'strategy': 'name_only',
                        'target_domain': domain
                    })
        
        # Sort by priority and limit
        queries.sort(key=lambda x: x['priority'])
        return queries[:20]  # Limit to top 20 queries
    
    def score_result_reliability(self, result: Dict, query_info: Dict) -> float:
        """Score search result reliability based on source, content, and query match."""
        score = 0.0
        url = result.get('url', '')
        title = result.get('title', '')
        snippet = result.get('snippet', '')
        
        # Domain reliability score (0-100)
        domain = urlparse(url).netloc.lower()
        domain_score = 0
        
        for canonical_domain, info in self.canonical_sources.items():
            if canonical_domain in domain:
                domain_score = info['weight']
                break
        
        # Base score from domain reliability
        score += domain_score * 0.4
        
        # Content quality indicators
        content = f"{title} {snippet}".lower()
        
        # Legal content indicators
        legal_indicators = [
            'opinion', 'court', 'judge', 'ruling', 'decision', 'case',
            'plaintiff', 'defendant', 'appellant', 'appellee', 'petitioner',
            'respondent', 'circuit', 'district', 'supreme', 'federal'
        ]
        legal_score = sum(1 for indicator in legal_indicators if indicator in content)
        score += min(legal_score * 2, 20)  # Max 20 points for legal content
        
        # Citation presence in content
        query_citations = re.findall(r'\d+\s+[A-Z][a-z]*\.?\d*d?\s+\d+', query_info.get('query', ''))
        for citation in query_citations:
            if citation in content:
                score += 15  # Strong indicator of relevant content
        
        # Title relevance
        if any(word in title.lower() for word in ['case', 'opinion', 'court']):
            score += 10
        
        # URL structure quality
        if any(indicator in url.lower() for indicator in ['/opinion/', '/case/', '/court/', '/decision/']):
            score += 5
        
        # Penalty for low-quality indicators
        if any(indicator in url.lower() for indicator in ['blog', 'forum', 'wiki', 'comment']):
            score -= 10
        
        return max(0, min(100, score))
    
    def search_with_engine(self, query: str, engine: str, num_results: int = 5) -> List[Dict]:
        """Execute search with rate limiting and error handling."""
        # Rate limiting
        now = time.time()
        if engine in self.last_request:
            elapsed = now - self.last_request[engine]
            if elapsed < self.min_delay:
                time.sleep(self.min_delay - elapsed)
        
        self.last_request[engine] = time.time()
        
        try:
            if engine == 'google':
                return self._google_search(query, num_results)
            elif engine == 'bing':
                return self._bing_search(query, num_results)
            elif engine == 'ddg':
                return self._ddg_search(query, num_results)
            else:
                return []
        except Exception as e:
            print(f"[websearch] {engine} search failed for '{query}': {e}")
            return []
    
    def _google_search(self, query: str, num_results: int) -> List[Dict]:
        """Enhanced Google search with better parsing."""
        params = {"q": query, "num": num_results, "hl": "en"}
        
        try:
            resp = self.session.get("https://www.google.com/search", params=params, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"[websearch] Google request failed: {e}")
            return []
        
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        
        # Try multiple selectors for robustness
        selectors = ['div.g', 'div[data-ved]', '.rc']
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                break
        
        for elem in elements[:num_results]:
            link_elem = elem.find('a', href=True)
            title_elem = elem.find('h3')
            
            # Look for snippet in multiple places
            snippet_elem = (elem.find('span', class_='aCOpRe') or 
                          elem.find('div', class_='VwiC3b') or
                          elem.find('div', class_='s') or
                          elem.find('.st'))
            
            if link_elem and title_elem:
                url = link_elem['href']
                if url.startswith('/url?q='):
                    # Extract actual URL from Google redirect
                    url = url.split('&')[0].replace('/url?q=', '')
                
                results.append({
                    'url': url,
                    'title': title_elem.get_text(strip=True),
                    'snippet': snippet_elem.get_text(strip=True) if snippet_elem else '',
                    'source': 'google'
                })
        
        return results
    
    def _bing_search(self, query: str, num_results: int) -> List[Dict]:
        """Enhanced Bing search."""
        params = {"q": query, "count": num_results}
        
        try:
            resp = self.session.get("https://www.bing.com/search", params=params, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            return []
        
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        
        for li in soup.select('li.b_algo')[:num_results]:
            a = li.find('a', href=True)
            if a:
                title = a.get_text(strip=True)
                url = a['href']
                
                # Better snippet extraction
                snippet = ''
                desc_elem = li.find('p') or li.find('.b_caption p')
                if desc_elem:
                    snippet = desc_elem.get_text(strip=True)
                
                results.append({
                    'url': url,
                    'title': title,
                    'snippet': snippet,
                    'source': 'bing'
                })
        
        return results
    
    def _ddg_search(self, query: str, num_results: int) -> List[Dict]:
        """Enhanced DuckDuckGo search."""
        data = {"q": query, "kl": "us-en"}
        
        try:
            resp = self.session.post("https://html.duckduckgo.com/html/", data=data, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            return []
        
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        
        for res in soup.select('div.result')[:num_results]:
            a = res.find('a', class_='result__a', href=True)
            snippet_elem = res.find('a', class_='result__snippet')
            
            if a:
                results.append({
                    'url': a['href'],
                    'title': a.get_text(strip=True),
                    'snippet': snippet_elem.get_text(strip=True) if snippet_elem else '',
                    'source': 'duckduckgo'
                })
        
        return results
    
    def search_cluster_canonical(self, cluster: Dict, max_results: int = 10) -> List[Dict]:
        """
        Main search function: find canonical legal sources for a citation cluster.
        Returns ranked results with reliability scores.
        """
        queries = self.generate_strategic_queries(cluster)
        all_results = []
        seen_urls = set()
        
        # Execute searches in priority order
        engines = ['google', 'bing', 'ddg']
        
        for query_info in queries:
            if len(all_results) >= max_results:
                break
            
            query = query_info['query']
            
            # Try engines in random order to distribute load
            random.shuffle(engines)
            
            for engine in engines:
                try:
                    results = self.search_with_engine(query, engine, num_results=5)
                    
                    for result in results:
                        url = result['url']
                        if url not in seen_urls and url.startswith('http'):
                            # Score result reliability
                            score = self.score_result_reliability(result, query_info)
                            
                            result.update({
                                'reliability_score': score,
                                'query_strategy': query_info['strategy'],
                                'query_priority': query_info['priority'],
                                'search_engine': engine
                            })
                            
                            all_results.append(result)
                            seen_urls.add(url)
                            
                            if len(all_results) >= max_results:
                                break
                    
                    if len(all_results) >= max_results:
                        break
                        
                except Exception as e:
                    print(f"[websearch] Error in {engine} search: {e}")
                    continue
            
            # Small delay between query batches
            time.sleep(0.5)
        
        # Sort by reliability score (highest first)
        all_results.sort(key=lambda x: x['reliability_score'], reverse=True)
        
        # Return top results with canonical sources prioritized
        canonical_results = [r for r in all_results if r['reliability_score'] >= 70]
        other_results = [r for r in all_results if r['reliability_score'] < 70]
        
        return (canonical_results + other_results)[:max_results]


# Convenience functions for backward compatibility
def generate_legal_websearch_queries(cluster):
    """Generate search queries for a cluster (backward compatibility)."""
    engine = LegalWebsearchEngine()
    queries = engine.generate_strategic_queries(cluster)
    return [q['query'] for q in queries]

def search_all_engines(query, num_results=5, engines=None):
    """Search all engines (backward compatibility)."""
    engine = LegalWebsearchEngine()
    if engines is None:
        engines = ['google', 'bing', 'ddg']
    
    all_results = []
    seen_urls = set()
    
    for search_engine in engines:
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

def search_cluster_for_canonical_sources(cluster, max_results=10):
    """Main function to search for canonical legal sources."""
    engine = LegalWebsearchEngine()
    return engine.search_cluster_canonical(cluster, max_results) 