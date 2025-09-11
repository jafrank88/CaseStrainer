"""
Enhanced Fallback Citation Verification System

This module integrates the best components from:
1. FallbackVerifier's verification logic
2. EnhancedLegalSearchEngine's query strategies
3. ComprehensiveWebSearchEngine's search capabilities

It provides robust fallback verification for citations not found in CourtListener,
ensuring canonical name, year, and URL are extracted from approved sites.
"""

import asyncio
from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

import logging
import re
import time
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin, quote, urlparse
import requests
import json
from src.url_decoder import URLDecoder
import os

logger = logging.getLogger(__name__)

class EnhancedFallbackVerifier:
    """
    Enhanced fallback verification system that integrates multiple approaches
    to provide reliable citation verification with canonical data extraction.
    """
    
    def __init__(self, enable_experimental_engines=True):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CaseStrainer Citation Verifier (Educational Research)'
        })
        
        self.last_request_time = {}
        self.min_delay = 0.2  # Reduced from 1.0 to 0.2 seconds for faster processing
        
        self.legal_domains = {
            'justia.com': 95,
            'caselaw.findlaw.com': 90, 
            'findlaw.com': 85,
            'courtlistener.com': 100,
            'leagle.com': 85,
            'casetext.com': 80,
            'law.cornell.edu': 80,
            'google.com/scholar': 75,
            'casemine.com': 80,
            'vlex.com': 85,
            'openjurist.org': 70
        }
        
        self.state_patterns = {
            'WA': [  # Washington
                r'(\d+)\s+Wn\.?\s*2d\s+(\d+)',
                r'(\d+)\s+Wn\.?\s*3d\s+(\d+)', 
                r'(\d+)\s+Wn\.?\s*App\.?\s*2d\s+(\d+)',
                r'(\d+)\s+Wash\.?\s*2d\s+(\d+)',
                r'(\d+)\s+Washington\s+2d\s+(\d+)'
            ],
            'CA': [  # California
                r'(\d+)\s+Cal\.?\s*2d\s+(\d+)',
                r'(\d+)\s+Cal\.?\s*3d\s+(\d+)',
                r'(\d+)\s+Cal\.?\s*App\.?\s*2d\s+(\d+)',
                r'(\d+)\s+Cal\.?\s*App\.?\s*3d\s+(\d+)'
            ],
            'NY': [  # New York
                r'(\d+)\s+N\.?Y\.?\s*2d\s+(\d+)',
                r'(\d+)\s+N\.?Y\.?\s*3d\s+(\d+)',
                r'(\d+)\s+N\.?Y\.?\s*Supp\.?\s*2d\s+(\d+)'
            ],
            'TX': [  # Texas
                r'(\d+)\s+S\.?W\.?\s*2d\s+(\d+)',
                r'(\d+)\s+S\.?W\.?\s*3d\s+(\d+)',
                r'(\d+)\s+Tex\.?\s*App\.?\s*(\d+)'
            ],
            'FL': [  # Florida
                r'(\d+)\s+So\.?\s*2d\s+(\d+)',
                r'(\d+)\s+So\.?\s*3d\s+(\d+)',
                r'(\d+)\s+Fla\.?\s*App\.?\s*(\d+)'
            ]
        }
        
        self.regional_reporters = {
            'P.': [  # Pacific (Western states)
                r'(\d+)\s+P\.\s*3d\s+(\d+)',
                r'(\d+)\s+P\.\s*2d\s+(\d+)'
            ],
            'S.E.': [  # Southeast (GA, NC, SC, VA, WV)
                r'(\d+)\s+S\.?E\.?\s*2d\s+(\d+)',
                r'(\d+)\s+S\.?E\.?\s*3d\s+(\d+)'
            ],
            'S.W.': [  # Southwest (TX, AR, KY, TN)
                r'(\d+)\s+S\.?W\.?\s*2d\s+(\d+)',
                r'(\d+)\s+S\.?W\.?\s*3d\s+(\d+)'
            ],
            'N.E.': [  # Northeast (NY, MA, OH, IL, IN)
                r'(\d+)\s+N\.?E\.?\s*2d\s+(\d+)',
                r'(\d+)\s+N\.?E\.?\s*3d\s+(\d+)'
            ],
            'N.W.': [  # Northwest (MN, IA, NE, ND, SD)
                r'(\d+)\s+N\.?W\.?\s*2d\s+(\d+)',
                r'(\d+)\s+N\.?W\.?\s*3d\s+(\d+)'
            ],
            'A.': [  # Atlantic (PA, NJ, DE, MD)
                r'(\d+)\s+A\.\s*2d\s+(\d+)',
                r'(\d+)\s+A\.\s*3d\s+(\d+)'
            ]
        }
        
        self.enable_experimental_engines = enable_experimental_engines
        
        self._verification_cache = {}
        self._cache_ttl = 60 * 60  # Cache results for 1 hour
    
    def _rate_limit(self, domain: str):
        """Apply rate limiting for requests to the same domain."""
        now = time.time()
        if domain in self.last_request_time:
            time_since_last = now - self.last_request_time[domain]
            if time_since_last < self.min_delay:
                sleep_time = self.min_delay - time_since_last
                time.sleep(sleep_time)
        self.last_request_time[domain] = now
    
    def normalize_citation(self, citation: str) -> str:
        """Normalize citation format (e.g., WN. -> Wash.)."""
        if not citation:
            return citation
        
        normalized = re.sub(r'\bWN\.?\b', 'Wash.', citation, flags=re.IGNORECASE)
        normalized = re.sub(r'\bWn\.?\b', 'Wash.', normalized, flags=re.IGNORECASE)
        
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def detect_state_from_citation(self, citation: str) -> Optional[str]:
        """Detect which state a citation is from based on citation patterns."""
        for state_code, patterns in self.state_patterns.items():
            for pattern in patterns:
                if re.search(pattern, citation, re.IGNORECASE):
                    return state_code
        
        for reporter_code, patterns in self.regional_reporters.items():
            for pattern in patterns:
                if re.search(pattern, citation, re.IGNORECASE):
                    if reporter_code == 'P.':  # Pacific
                        return 'WA'  # Default to Washington for Pacific reporter
                    elif reporter_code == 'S.E.':  # Southeast
                        return 'GA'  # Default to Georgia for Southeast reporter
                    elif reporter_code == 'S.W.':  # Southwest
                        return 'TX'  # Default to Texas for Southwest reporter
                    elif reporter_code == 'N.E.':  # Northeast
                        return 'NY'  # Default to New York for Northeast reporter
                    elif reporter_code == 'N.W.':  # Northwest
                        return 'MN'  # Default to Minnesota for Northwest reporter
                    elif reporter_code == 'A.':  # Atlantic
                        return 'PA'  # Default to Pennsylvania for Atlantic reporter
        
        return None
    
    def is_washington_citation(self, citation: str) -> bool:
        """Check if citation is from Washington state (maintained for backward compatibility)."""
        return self.detect_state_from_citation(citation) == 'WA'
    
    def generate_citation_variants(self, citation: str) -> List[str]:
        """Generate citation variants for any state."""
        variants = []
        state = self.detect_state_from_citation(citation)
        
        if state == 'WA':  # Washington
            if 'Wn.' in citation:
                variants.append(citation.replace('Wn.', 'Wash.'))
            
            if 'Wash.' in citation:
                variants.append(citation.replace('Wash.', 'Wn.'))
            
            if 'Washington' in citation:
                variants.append(citation.replace('Washington', 'Wn.'))
            
            if 'Wn. App.' in citation:
                variants.append(citation.replace('Wn. App.', 'Wash. App.'))
            
            if 'Wash. App.' in citation:
                variants.append(citation.replace('Wash. App.', 'Wn. App.'))
            
            if 'Wn.2d' in citation:
                variants.append(citation.replace('Wn.2d', 'Wash.2d'))
            
            if 'Wash.2d' in citation:
                variants.append(citation.replace('Wash.2d', 'Wn.2d'))
        
        elif state == 'CA':  # California
            if 'Cal.' in citation:
                variants.append(citation.replace('Cal.', 'California'))
            
            if 'California' in citation:
                variants.append(citation.replace('California', 'Cal.'))
        
        elif state == 'NY':  # New York
            if 'N.Y.' in citation:
                variants.append(citation.replace('N.Y.', 'New York'))
            
            if 'New York' in citation:
                variants.append(citation.replace('New York', 'N.Y.'))
        
        elif state == 'TX':  # Texas
            if 'Tex.' in citation:
                variants.append(citation.replace('Tex.', 'Texas'))
            
            if 'Texas' in citation:
                variants.append(citation.replace('Texas', 'Tex.'))
        
        return variants
    
    def generate_washington_variants(self, citation: str) -> List[str]:
        """Generate Washington citation variants (maintained for backward compatibility)."""
        return self.generate_citation_variants(citation)
    
    def _get_state_name(self, state_code: str) -> str:
        """Get full state name from state code."""
        state_names = {
            'WA': 'Washington',
            'CA': 'California',
            'NY': 'New York',
            'TX': 'Texas',
            'FL': 'Florida',
            'GA': 'Georgia',
            'PA': 'Pennsylvania',
            'MN': 'Minnesota'
        }
        return state_names.get(state_code, state_code)
    
    def _get_state_legal_sites(self, state_code: str) -> List[str]:
        """Get state-specific legal database sites."""
        state_sites = {
            'WA': [  # Washington
                'site:caselaw.findlaw.com/court/wa-supreme-court',
                'site:caselaw.findlaw.com/court/wa-court-of-appeals',
                'site:justia.com/courts/wa',
                'site:leagle.com/courts/wa',
                'site:law.justia.com/courts/wa',
                'site:supreme.findlaw.com/court/wa',
                'site:courts.wa.gov',
                'site:leg.wa.gov',
                'site:app.leg.wa.gov'
            ],
            'CA': [  # California
                'site:caselaw.findlaw.com/court/ca-supreme-court',
                'site:caselaw.findlaw.com/court/ca-court-of-appeal',
                'site:justia.com/courts/ca',
                'site:leagle.com/courts/ca',
                'site:law.justia.com/courts/ca',
                'site:courts.ca.gov'
            ],
            'NY': [  # New York
                'site:caselaw.findlaw.com/court/ny-court-of-appeals',
                'site:caselaw.findlaw.com/court/ny-supreme-court',
                'site:justia.com/courts/ny',
                'site:leagle.com/courts/ny',
                'site:law.justia.com/courts/ny',
                'site:courts.ny.gov'
            ],
            'TX': [  # Texas
                'site:caselaw.findlaw.com/court/tx-supreme-court',
                'site:caselaw.findlaw.com/court/tx-court-of-appeals',
                'site:justia.com/courts/tx',
                'site:leagle.com/courts/tx',
                'site:law.justia.com/courts/tx',
                'site:courts.texas.gov'
            ]
        }
        return state_sites.get(state_code, [])
    
    def _get_court_type(self, citation_text: str, state_code: str) -> str:
        """Determine court type from citation."""
        if 'App.' in citation_text:
            return 'appellate court'
        elif '2d' in citation_text and 'App.' not in citation_text:
            return 'supreme court'
        else:
            return 'court'
    
    def generate_enhanced_legal_queries(self, citation_text: str, case_name: Optional[str] = None) -> List[Dict]:
        """
        Generate optimized search queries for enhanced fallback verification.
        Prioritizes simple, effective queries that work well with Google/Bing.
        """
        queries = []
        
        citation_text = citation_text.strip()
        
        queries.append({
            'query': f'"{citation_text}"',
            'priority': 1,
            'type': 'simple_citation',
            'citation': citation_text
        })
        
        state = self.detect_state_from_citation(citation_text)
        if state:
            citation_variants = self.generate_citation_variants(citation_text)
            for variant in citation_variants:
                queries.append({
                    'query': f'"{variant}"',
                    'priority': 1,  # Same priority as original
                    'type': 'citation_variant',
                    'citation': variant,
                    'original': citation_text
                })
        
        queries.append({
            'query': f'"{citation_text}" court decision',
            'priority': 2,
            'type': 'citation_court',
            'citation': citation_text
        })
        
        state = self.detect_state_from_citation(citation_text)
        if state:
            state_name = self._get_state_name(state)
            queries.append({
                'query': f'"{citation_text}" {state_name}',
                'priority': 2,  # Increased priority for state-specific cases
                'type': f'citation_{state.lower()}',
                'citation': citation_text
            })
            
            state_legal_sites = self._get_state_legal_sites(state)
            for site in state_legal_sites:
                queries.append({
                    'query': f'{site} "{citation_text}"',
                    'priority': 2,  # High priority for state-specific searches
                    'type': f'{state.lower()}_site_specific',
                    'citation': citation_text,
                    'site': site
                })
            
            if case_name:
                court_type = self._get_court_type(citation_text, state)
                queries.append({
                    'query': f'"{case_name}" "{citation_text}" {state_name} {court_type}',
                    'priority': 1,  # Highest priority for state cases with names
                    'type': f'{state.lower()}_case_citation',
                    'citation': citation_text,
                    'case_name': case_name
                })
        
        if case_name:
            queries.append({
                'query': f'"{case_name}" "{citation_text}"',
                'priority': 4,
                'type': 'case_and_citation',
                'citation': citation_text,
                'case_name': case_name
            })
            
            if ' vs. ' in case_name:
                alt_case_name = case_name.replace(' vs. ', ' v. ')
                queries.append({
                    'query': f'"{alt_case_name}" "{citation_text}"',
                    'priority': 4,
                    'type': 'case_and_citation_alt',
                    'citation': citation_text,
                    'case_name': alt_case_name
                })
        
        legal_sites = [
            'site:caselaw.findlaw.com',  # FindLaw - very reliable for legal cases
            'site:justia.com',           # Justia - excellent legal database
            'site:courtlistener.com',    # CourtListener - official court data
            'site:case-law.vlex.com',    # Vlex - international legal database
            'site:leagle.com',           # Leagle - legal case database
            'site:supreme.findlaw.com',  # FindLaw Supreme Court cases
            'site:law.justia.com',      # Justia law database
            'site:scholar.google.com',   # Google Scholar (legal cases)
        ]
        for site in legal_sites:
            queries.append({
                'query': f'{site} "{citation_text}"',
                'priority': 2,  # Increased from 5 to 2 - these are very effective!
                'type': 'site_specific',
                'citation': citation_text,
                'site': site
            })
        
        state = self.detect_state_from_citation(citation_text)
        if state:
            state_queries = self._generate_state_specific_queries(citation_text, case_name, state)
            queries.extend(state_queries)
        
        if state:
            parallel_queries = self._generate_parallel_citation_queries(citation_text, case_name)
            queries.extend(parallel_queries)
        
        return queries
    
    def _generate_state_specific_queries(self, citation_text: str, case_name: Optional[str] = None, state_code: str = 'WA') -> List[Dict]:
        """Generate state-specific search queries for better case discovery."""
        state_queries = []
        state_name = self._get_state_name(state_code)
        
        if 'App.' in citation_text:
            state_queries.append({
                'query': f'"{citation_text}" "{state_name} Court of Appeals"',
                'priority': 1,  # Highest priority
                'type': f'{state_code.lower()}_appeals_specific',
                'citation': citation_text
            })
            
            if case_name:
                state_queries.append({
                    'query': f'"{case_name}" "{citation_text}" "{state_name} Court of Appeals"',
                    'priority': 1,  # Highest priority
                    'type': f'{state_code.lower()}_appeals_case',
                    'citation': citation_text,
                    'case_name': case_name
                })
        
        if '2d' in citation_text and 'App.' not in citation_text:
            state_queries.append({
                'query': f'"{citation_text}" "{state_name} Supreme Court"',
                'priority': 1,  # Highest priority
                'type': f'{state_code.lower()}_supreme_specific',
                'citation': citation_text
            })
            
            if case_name:
                state_queries.append({
                    'query': f'"{case_name}" "{citation_text}" "{state_name} Supreme Court"',
                    'priority': 1,  # Highest priority
                    'type': f'{state_code.lower()}_supreme_case',
                    'citation': citation_text,
                    'case_name': case_name
                })
        
        if 'P.3d' in citation_text or 'P.2d' in citation_text:
            state_queries.append({
                'query': f'"{citation_text}" "{state_name}" "Pacific Reporter"',
                'priority': 2,  # High priority
                'type': f'{state_code.lower()}_pacific_parallel',
                'citation': citation_text
            })
        elif 'S.E.' in citation_text:
            state_queries.append({
                'query': f'"{citation_text}" "{state_name}" "Southeast Reporter"',
                'priority': 2,  # High priority
                'type': f'{state_code.lower()}_southeast_parallel',
                'citation': citation_text
            })
        elif 'S.W.' in citation_text:
            state_queries.append({
                'query': f'"{citation_text}" "{state_name}" "Southwest Reporter"',
                'priority': 2,  # High priority
                'type': f'{state_code.lower()}_southwest_parallel',
                'citation': citation_text
            })
        elif 'N.E.' in citation_text:
            state_queries.append({
                'query': f'"{citation_text}" "{state_name}" "Northeast Reporter"',
                'priority': 2,  # High priority
                'type': f'{state_code.lower()}_northeast_parallel',
                'citation': citation_text
            })
        elif 'N.W.' in citation_text:
            state_queries.append({
                'query': f'"{citation_text}" "{state_name}" "Northwest Reporter"',
                'priority': 2,  # High priority
                'type': f'{state_code.lower()}_northwest_parallel',
                'citation': citation_text
            })
        elif 'A.' in citation_text:
            state_queries.append({
                'query': f'"{citation_text}" "{state_name}" "Atlantic Reporter"',
                'priority': 2,  # High priority
                'type': f'{state_code.lower()}_atlantic_parallel',
                'citation': citation_text
            })
        
        return state_queries
    
    def _generate_parallel_citation_queries(self, citation_text: str, case_name: Optional[str] = None) -> List[Dict]:
        """Generate queries for parallel citations to improve case discovery."""
        parallel_queries = []
        
        if 'Wn.' in citation_text or 'Wash.' in citation_text:
            volume_page_match = re.search(r'(\d+)\s+(?:Wn\.|Wash\.)\s*(?:App\.|2d|3d)\s+(\d+)', citation_text)
            if volume_page_match:
                volume, page = volume_page_match.groups()
                
                if 'App.' in citation_text:
                    parallel_queries.append({
                        'query': f'"{volume} P.3d {page}" Washington',
                        'priority': 1,  # High priority
                        'type': 'parallel_pacific_appeals',
                        'citation': citation_text
                    })
                elif '2d' in citation_text:
                    parallel_queries.append({
                        'query': f'"{volume} P.2d {page}" Washington',
                        'priority': 1,  # High priority
                        'type': 'parallel_pacific_supreme',
                        'citation': citation_text
                    })
        
        elif 'P.3d' in citation_text or 'P.2d' in citation_text:
            volume_page_match = re.search(r'(\d+)\s+P\.(?:3d|2d)\s+(\d+)', citation_text)
            if volume_page_match:
                volume, page = volume_page_match.groups()
                
                if 'P.3d' in citation_text:
                    parallel_queries.append({
                        'query': f'"{volume} Wn. App. {page}" Washington',
                        'priority': 1,  # High priority
                        'type': 'parallel_washington_appeals',
                        'citation': citation_text
                    })
                    parallel_queries.append({
                        'query': f'"{volume} Wash. App. {page}" Washington',
                        'priority': 1,  # High priority
                        'type': 'parallel_washington_appeals_full',
                        'citation': citation_text
                    })
                elif 'P.2d' in citation_text:
                    parallel_queries.append({
                        'query': f'"{volume} Wn.2d {page}" Washington',
                        'priority': 1,  # High priority
                        'type': 'parallel_washington_supreme',
                        'citation': citation_text
                    })
                    parallel_queries.append({
                        'query': f'"{volume} Wash.2d {page}" Washington',
                        'priority': 1,  # High priority
                        'type': 'parallel_washington_supreme_full',
                        'citation': citation_text
                    })
        
        return parallel_queries
    
    def _parse_citation(self, citation_text: str) -> Dict:
        """Parse citation to extract volume, reporter, page, and court type."""
        citation_info = {
            'volume': None,
            'reporter': None,
            'page': None,
            'year': None,
            'court_type': 'unknown'
        }
        
        washington_patterns = [
            r'(\d+)\s+Wn\.\s*2d\s+(\d+)',  # 188 Wn.2d 114
            r'(\d+)\s+Wn\.\s*App\.\s+(\d+)',  # 178 Wn. App. 929
            r'(\d+)\s+Wash\.\s*2d\s+(\d+)',  # 188 Wash. 2d 114
            r'(\d+)\s+Wash\.\s*App\.\s+(\d+)',  # 178 Wash. App. 929
        ]
        
        for pattern in washington_patterns:
            match = re.search(pattern, citation_text, re.IGNORECASE)
            if match:
                citation_info['volume'] = match.group(1)
                citation_info['page'] = match.group(2)
                citation_info['court_type'] = 'washington'
                citation_info['reporter'] = 'Wn.' if 'Wn.' in citation_text else 'Wash.'
                break
        
        pacific_patterns = [
            r'(\d+)\s+P\.\s*3d\s+(\d+)',  # 392 P.3d 1041
            r'(\d+)\s+P\.\s*2d\s+(\d+)',  # 317 P.2d 1068
        ]
        
        for pattern in pacific_patterns:
            match = re.search(pattern, citation_text, re.IGNORECASE)
            if match:
                citation_info['volume'] = match.group(1)
                citation_info['page'] = match.group(2)
                citation_info['court_type'] = 'pacific'
                citation_info['reporter'] = 'P.3d' if '3d' in citation_text else 'P.2d'
                break
        
        year_match = re.search(r'\((\d{4})\)', citation_text)
        if year_match:
            citation_info['year'] = year_match.group(1)
        
        return citation_info
    
    async def verify_citation(self, citation_text: str, extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None, has_courtlistener_data: bool = False) -> Dict[str, Any]:
        """
        Verify a citation using hybrid verification: CourtListener first, then enhanced fallback with 10 sources.
        
        Args:
            citation_text: The citation text to verify
            extracted_case_name: Optional extracted case name
            extracted_date: Optional extracted date
            has_courtlistener_data: If True, skip fallback verification (already verified)
            
        Returns:
            Dictionary with verification results
        """
        logger.info(f"🚀 HYBRID VERIFICATION CALLED for {citation_text}")
        
        if has_courtlistener_data:
            logger.info(f"Skipping fallback verification for {citation_text} - already has CourtListener data")
            return self._create_fallback_result(citation_text, "already_verified", extracted_case_name)
        
        start_time = time.time()
        max_total_time = 30.0  # Increased to 30 seconds total per citation for better reliability
        
        
        try:
            courtlistener_result = await self._try_courtlistener_first(citation_text, extracted_case_name)
            if courtlistener_result and courtlistener_result.get('verified', False):
                elapsed = time.time() - start_time
                logger.info(f"✅ CourtListener verified: {citation_text} -> {courtlistener_result.get('canonical_name', 'N/A')} in {elapsed:.1f}s")
                return courtlistener_result
            
            logger.info(f"CourtListener failed for {citation_text}, proceeding with enhanced fallback verification")
            
            citation_info = self._parse_citation(citation_text)
            
            queries = self.generate_enhanced_legal_queries(citation_text, extracted_case_name)
            
            state = self.detect_state_from_citation(citation_text)
            if state:
                logger.info(f"Generated {len(queries)} queries for {state} citation {citation_text}")
                for i, q in enumerate(queries[:6]):  # Show first 6 queries
                    logger.debug(f"  Query {i+1}: {q[:100]}{'...' if len(q) > 100 else ''}")
            
            sources = [
                ('casemine', self._verify_with_casemine, 8.0),        # Legal database, international - FREE, HAS WASHINGTON CASES!
                ('descrybe', self._verify_with_descrybe, 8.0),        # Legal database, 3.6M U.S. cases - FREE!
                ('findlaw', self._verify_with_findlaw, 8.0),          # Legal database, good coverage - FREE!
                ('leagle', self._verify_with_leagle, 8.0),            # Legal database, comprehensive - FREE!
                ('vlex', self._verify_with_vlex, 8.0),                # Legal database, extensive - FREE!
                ('justia', self._verify_with_justia, 8.0),            # Legal-specific but reliable - FREE!
                
                ('google', self._verify_with_google_scholar, 6.0),    # Fast, reliable, broad coverage (rate-limited)
                ('bing', self._verify_with_bing, 6.0),                # Fast, reliable, good legal indexing (rate-limited)
                ('duckduckgo', self._verify_with_duckduckgo, 6.0),    # Fast, no rate limiting (rate-limited)
                
                ('scrapingbee', self._verify_with_scrapingbee, 4.0),  # Premium: handles JS, anti-bot bypass - LAST RESORT
            ]
            
            logger.info(f"Configured {len(sources)} verification sources: {[s[0] for s in sources]}")
            
            tasks = []
            logger.info(f"🔍 Processing {len(sources)} verification sources: {[s[0] for s in sources]}")
            
            for source_name, verify_func, source_timeout in sources:
                state = self.detect_state_from_citation(citation_text)
                max_queries = 4 if state else 2
                logger.info(f"📋 Processing source {source_name} with max_queries={max_queries} and timeout={source_timeout}s")
                
                for query_info in queries[:max_queries]:
                    query = query_info['query']
                    query_type = query_info.get('type', '')
                    
                    
                    task = self._create_verification_task(
                        source_name, verify_func, citation_text, citation_info, extracted_case_name, extracted_date, query, source_timeout
                    )
                    tasks.append(task)
                    logger.info(f"✅ Created task for {source_name} with query: {query[:50]}... and timeout: {source_timeout}s")
            
            logger.info(f"Created {len(tasks)} verification tasks for {len(sources)} sources")
            results = []
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=max_total_time
                )
            except asyncio.TimeoutError:
                logger.warning(f"Enhanced fallback verification timed out after {max_total_time}s for {citation_text}")
                return self._create_fallback_result(citation_text, "timeout", extracted_case_name)
            
            best_result = None
            best_score = 0
            free_source_results = []  # Track results from free sources
            
            for result in results:
                if isinstance(result, Exception):
                    continue
                    
                if isinstance(result, dict) and result.get('verified'):
                    expected_name = extracted_case_name
                    expected_year = extracted_date or (citation_info.get('year') if citation_info else None)
                    score = self._calculate_verification_score(result, expected_name, expected_year)
                    
                    source_name = result.get('source', 'unknown')
                    if source_name != 'scrapingbee':
                        free_source_results.append((result, score))
                    
                    if score > best_score:
                        best_score = score
                        best_result = result
            
            if best_result and best_score >= 1.5:  # Require minimum score for verification
                if best_result.get('source') == 'CourtListener':
                    logger.info(f"Preserving CourtListener source for {citation_text}")
                else:
                    source_url = best_result.get('canonical_url') or best_result.get('url')
                    if source_url:
                        best_result['source'] = self._extract_source_from_url(source_url)
                
                if not best_result.get('canonical_url') and best_result.get('url'):
                    best_result['canonical_url'] = best_result['url']
                
                elapsed = time.time() - start_time
                logger.info(f"✅ Enhanced fallback verified: {citation_text} -> {best_result.get('canonical_name', 'N/A')} (via {best_result.get('source', 'unknown')}) in {elapsed:.1f}s")
                return best_result
            elif best_result:
                elapsed = time.time() - start_time
                logger.warning(f"❌ Verification score too low ({best_score:.2f}) for {citation_text} -> {best_result.get('canonical_name', 'N/A')} in {elapsed:.1f}s")
                return self._create_fallback_result(citation_text, "low_confidence", extracted_case_name)
            
            if not free_source_results:
                logger.info(f"🔄 No results from free sources for {citation_text}, ScrapingBee was used as last resort")
            else:
                logger.info(f"🔄 Free sources found {len(free_source_results)} results but none met verification threshold for {citation_text}")
            
            elapsed = time.time() - start_time
            return self._create_fallback_result(citation_text, "not_found", extracted_case_name)
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Enhanced fallback verification error for {citation_text} after {elapsed:.1f}s: {str(e)}")
            return self._create_fallback_result(citation_text, "error", extracted_case_name)
    
    async def _try_courtlistener_first(self, citation_text: str, extracted_case_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Try CourtListener verification first for fast, reliable results.
        
        Args:
            citation_text: The citation to verify
            extracted_case_name: Optional extracted case name
            
        Returns:
            CourtListener verification result or None if failed
        """
        try:
            courtlistener_api_key = os.getenv('COURTLISTENER_API_KEY')
            if not courtlistener_api_key:
                return None
            
            try:
                from src.enhanced_courtlistener_verification import EnhancedCourtListenerVerifier
            except ImportError:
                return None
            
            courtlistener_verifier = EnhancedCourtListenerVerifier(courtlistener_api_key)
            
            result = courtlistener_verifier.verify_citation_enhanced(citation_text, extracted_case_name)
            
            if result and result.get('verified', False):
                logger.info(f"✓ CourtListener verification successful for: {citation_text}")
                
                url = result.get('url', '')
                canonical_url = result.get('canonical_url') or result.get('url', '')
                
                if url and url.startswith('/'):
                    url = f"https://www.courtlistener.com{url}"
                if canonical_url and canonical_url.startswith('/'):
                    canonical_url = f"https://www.courtlistener.com{canonical_url}"
                
                return {
                    'verified': True,
                    'canonical_name': result.get('canonical_name'),
                    'canonical_date': result.get('canonical_date'),
                    'url': url,
                    'canonical_url': canonical_url,
                    'source': 'CourtListener',
                    'validation_method': result.get('validation_method', 'enhanced_cross_validation'),
                    'confidence': result.get('confidence', 0.0),
                    'verification_strategy': 'courtlistener_only'
                }
            else:
                return None
                
        except Exception as e:
            logger.warning(f"CourtListener verification error for {citation_text}: {str(e)}")
            return None
    
    def _extract_source_from_url(self, url: Optional[str]) -> str:
        """Extract a user-friendly source name from a URL."""
        if not url:
            return "unknown"
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            source_map = {
                'courtlistener.com': 'CourtListener',
                'caselaw.findlaw.com': 'FindLaw',
                'findlaw.com': 'FindLaw',
                'justia.com': 'Justia',
                'leagle.com': 'Leagle',
                'casetext.com': 'Casetext',
                'law.cornell.edu': 'Cornell Law',
                'scholar.google.com': 'Google Scholar',
                'casemine.com': 'CaseMine',
                'vlex.com': 'vLex',
                'openjurist.org': 'OpenJurist',
                'descrybe.ai': 'Descrybe.ai',
                'scrapingbee.com': 'Web Search'
            }
            
            for domain_pattern, source_name in source_map.items():
                if domain_pattern in domain:
                    return source_name
            
            for domain_pattern, source_name in source_map.items():
                if domain_pattern.split('.')[0] in domain:
                    return source_name
            
            return domain.replace('www.', '')
            
        except Exception:
            return "unknown"

    def _create_fallback_result(self, citation_text: str, status: str, case_name: Optional[str] = None) -> Dict[str, Any]:
        """Create a standardized fallback result."""
        return {
            'verified': False,
            'source': f"fallback_{status}",
            'canonical_name': None,
            'canonical_date': None,
            'url': None,
            'canonical_url': None,
            'confidence': 0.0,
            'error': f"Verification {status}"
        }
    
    def _normalize_case_name(self, name: Optional[str]) -> str:
        """Normalize a case name for fuzzy comparison."""
        if not name:
            return ""
        name_norm = name.lower()
        name_norm = name_norm.replace('.', ' ').replace(',', ' ').replace('\n', ' ').replace('\r', ' ')
        name_norm = name_norm.replace(' v ', ' v. ').replace(' vs ', ' v. ').replace(' vs. ', ' v. ')
        name_norm = name_norm.replace('in re', 'in re').replace('ex parte', 'ex parte')
        name_norm = re.sub(r'\s+', ' ', name_norm).strip()
        return name_norm

    def _token_jaccard(self, a: str, b: str) -> float:
        """Simple token Jaccard similarity for fuzzy matching."""
        if not a or not b:
            return 0.0
        ta = set(a.split())
        tb = set(b.split())
        if not ta or not tb:
            return 0.0
        inter = ta.intersection(tb)
        union = ta.union(tb)
        return len(inter) / len(union) if union else 0.0

    def _year_from_any(self, value: Optional[str]) -> Optional[str]:
        """Extract a 4-digit year from various date formats."""
        if not value:
            return None
        m = re.search(r'(19|20)\d{2}', str(value))
        return m.group(0) if m else None

    def _calculate_verification_score(self, result: Dict[str, Any], expected_name: Optional[str] = None, expected_year: Optional[str] = None) -> float:
        """Calculate a score for verification result quality with fuzzy name/year alignment."""
        score = 0.0
        
        if result.get('verified'):
            score += 1.0
        
        canonical_name = result.get('canonical_name')
        if canonical_name:
            score += 0.5
        
        canonical_date = result.get('canonical_date')
        if canonical_date:
            score += 0.3
        
        if result.get('url'):
            score += 0.2
        
        if result.get('confidence'):
            score += min(result['confidence'], 1.0)
        
        if expected_name and canonical_name:
            sim = self._token_jaccard(self._normalize_case_name(expected_name), self._normalize_case_name(canonical_name))
            
            if ('in re' in expected_name.lower() or 'in re' in canonical_name.lower()):
                if sim >= 0.2:  # Very low threshold for Washington "In re" cases
                    score += sim * 2.0  # High bonus for any similarity in "In re" cases
                elif sim < 0.1:  # Still require minimal similarity
                    score -= 0.5  # Very light penalty for very low similarity
                else:
                    score += sim * 1.0  # Partial credit
            elif 'marriage' in expected_name.lower() and 'marriage' in canonical_name.lower():
                if sim >= 0.3:  # Lower threshold for marriage cases
                    score += sim * 1.5  # Bonus for marriage case similarity
                elif sim < 0.2:  # Still require some similarity
                    score -= 1.0  # Reduced penalty for marriage cases
                else:
                    score += sim * 0.5  # Partial credit
            else:
                if sim < 0.5:  # Reduced from 0.6 to 0.5 for Washington cases
                    score -= 1.5  # Reduced penalty from 2.0 to 1.5
                else:
                    score += sim  # Bonus for high similarity
        else:
            score -= 1.0
        
        exp_year = self._year_from_any(expected_year)
        can_year = self._year_from_any(canonical_date)
        if exp_year and can_year:
            try:
                exp_year_int = int(exp_year) if isinstance(exp_year, (int, str)) else None
                can_year_int = int(can_year) if isinstance(can_year, (int, str)) else None
                
                if exp_year_int and can_year_int:
                    year_diff = abs(exp_year_int - can_year_int)
                    if year_diff == 0:
                        score += 1.5  # Strong bonus for exact year match
                    elif year_diff <= 2:  # Allow 2 year difference for Washington cases
                        score += 0.5  # Small bonus for close years
                    elif year_diff <= 5:  # Allow 5 year difference with penalty
                        score -= 0.5  # Small penalty for moderate year difference
                    else:
                        score -= 1.5  # Heavy penalty for large year difference
            except (ValueError, TypeError):
                score -= 1.0
        
        return score
    
    def _create_verification_task(self, source_name: str, verify_func, citation_text: str, 
                                 citation_info: Dict, extracted_case_name: Optional[str], 
                                 extracted_date: Optional[str], query: str, source_timeout: float = 5.0):
        """Create a verification task with proper error handling and tiered timeouts."""
        async def task_wrapper():
            try:
                if not isinstance(query, str):
                    logger.error(f"ERROR: query is not a string! Type: {type(query)}, Value: {query}")
                    safe_query = str(query) if query is not None else ""
                else:
                    safe_query = query
                
                result = await asyncio.wait_for(
                    verify_func(citation_text, citation_info, extracted_case_name, extracted_date, safe_query),
                    timeout=source_timeout  # Use tiered timeout per source
                )
                if result and result.get('verified', False):
                    return result
            except asyncio.TimeoutError:
                return None
            except Exception as e:
                return None
        
        return task_wrapper()
    
    def verify_citation_sync(self, citation_text: str, extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None) -> Dict:
        """
        Synchronous version of verify_citation for use in non-async contexts.
        
        Args:
            citation_text: The citation to verify (e.g., "188 Wn.2d 114")
            extracted_case_name: Optional case name (e.g., "In re Marriage of Black")
            extracted_date: Optional date (e.g., "2017")
            
        Returns:
            Dict with verification results including canonical_name, canonical_date, and url
        """
        try:
            import asyncio
            import threading
            
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    logger.warning(f"Sync verification called from within event loop for {citation_text}")
                    return {
                        'verified': False,
                        'source': 'sync_limitation',
                        'canonical_name': None,
                        'canonical_date': None,
                        'url': None,
                        'confidence': 0.0,
                        'error': 'Cannot run sync verification from within event loop'
                    }
            except RuntimeError:
                pass
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    self.verify_citation(citation_text, extracted_case_name, extracted_date, has_courtlistener_data=False)
                )
                return result
            finally:
                loop.close()
                asyncio.set_event_loop(None)
            
        except Exception as e:
            logger.error(f"Error in sync verification: {e}")
            return {
                'verified': False,
                'source': None,
                'canonical_name': None,
                'canonical_date': None,
                'url': None,
                'confidence': 0.0,
                'error': str(e)
            }
    
    async def _verify_with_justia(self, citation_text: str, citation_info: Dict, 
                                 extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None,
                                 search_query: Optional[str] = None) -> Optional[Dict]:
        """Verify citation with Justia legal database."""
        try:
            if not search_query:
                search_query = citation_text
                if extracted_case_name:
                    search_query += f" {extracted_case_name}"
            
            search_url = f"https://law.justia.com/search?query={quote(search_query)}"
            
            self._rate_limit('justia.com')
            response = self.session.get(search_url, timeout=WEBSEARCH_TIMEOUT)  # Reduced from 15 to 5 seconds
            
            if response.status_code == 200:
                content = response.text
                
                case_link_pattern = r'<a[^>]*href="([^"]*cases[^"]+)"[^>]*>([^<]*)</a>'
                matches = re.findall(case_link_pattern, content, re.IGNORECASE)
                
                for link_url, link_text in matches:
                    if citation_text.replace(' ', '').lower() in link_text.replace(' ', '').lower():
                        full_url = link_url if link_url.startswith('http') else f"https://law.justia.com{link_url}"
                        
                        case_name = self._extract_case_name_from_link(link_text)
                        if not case_name and extracted_case_name:
                            case_name = extracted_case_name
                        
                        year = extracted_date or (citation_info.get('year') if citation_info else None)
                        if not year:
                            year_match = re.search(r'(\d{4})', link_text)
                            if year_match:
                                year = year_match.group(1)
                        
                        if case_name:
                            return {
                                'verified': True,
                                'source': 'justia',
                                'canonical_name': case_name,
                                'canonical_date': year,
                                'url': full_url,
                                'confidence': 0.85
                            }
            
            return None
            
        except Exception as e:
            logger.warning(f"Justia verification failed for {citation_text}: {e}")
            return None
    
    async def _verify_with_findlaw(self, citation_text: str, citation_info: Dict,
                                  extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None,
                                  search_query: Optional[str] = None) -> Optional[Dict]:
        """Verify citation with FindLaw legal database."""
        try:
            if not search_query:
                search_query = citation_text
                if extracted_case_name:
                    search_query += f" {extracted_case_name}"
            
            search_url = f"https://caselaw.findlaw.com/search?query={quote(search_query)}"
            
            self._rate_limit('findlaw.com')
            response = self.session.get(search_url, timeout=WEBSEARCH_TIMEOUT)  # Reduced from 15 to 5 seconds
            
            if response.status_code == 200:
                content = response.text
                
                case_link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
                matches = re.findall(case_link_pattern, content, re.IGNORECASE)
                
                for link_url, link_text in matches:
                    if citation_text.replace(' ', '').lower() in link_text.replace(' ', '').lower():
                        full_url = link_url if link_url.startswith('http') else f"https://caselaw.findlaw.com{link_url}"
                        
                        case_name = self._extract_case_name_from_link(link_text)
                        if not case_name and extracted_case_name:
                            case_name = extracted_case_name
                        
                        year = extracted_date or (citation_info.get('year') if citation_info else None)
                        if not year:
                            year_match = re.search(r'(\d{4})', link_text)
                            if year_match:
                                year = year_match.group(1)
                        
                        if case_name:
                            return {
                                'verified': True,
                                'source': 'findlaw',
                                'canonical_name': case_name,
                                'canonical_date': year,
                                'url': full_url,
                                'confidence': 0.8
                            }
            
            return None
            
        except Exception as e:
            logger.warning(f"FindLaw verification failed for {citation_text}: {e}")
            return None
    
    async def _verify_with_leagle(self, citation_text: str, citation_info: Dict,
                                 extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None,
                                 search_query: Optional[str] = None) -> Optional[Dict]:
        """Verify citation with Leagle legal database."""
        try:
            if not search_query:
                search_query = citation_text
                if extracted_case_name:
                    search_query += f" {extracted_case_name}"
            
            search_url = f"https://www.leagle.com/search?query={quote(search_query)}"
            
            self._rate_limit('leagle.com')
            response = self.session.get(search_url, timeout=WEBSEARCH_TIMEOUT)  # Reduced from 15 to 5 seconds
            
            if response.status_code == 200:
                content = response.text
                
                case_link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
                matches = re.findall(case_link_pattern, content, re.IGNORECASE)
                
                for link_url, link_text in matches:
                    if citation_text.replace(' ', '').lower() in link_text.replace(' ', '').lower():
                        full_url = link_url if link_url.startswith('http') else f"https://www.leagle.com{link_url}"
                        
                        case_name = self._extract_case_name_from_link(link_text)
                        if not case_name and extracted_case_name:
                            case_name = extracted_case_name
                        
                        year = extracted_date or (citation_info.get('year') if citation_info else None)
                        if not year:
                            year_match = re.search(r'(\d{4})', link_text)
                            if year_match:
                                year = year_match.group(1)
                        
                        if case_name:
                            return {
                                'verified': True,
                                'source': 'leagle',
                                'canonical_name': case_name,
                                'canonical_date': year,
                                'url': full_url,
                                'confidence': 0.8
                            }
            
            return None
            
        except Exception as e:
            logger.warning(f"Leagle verification failed for {citation_text}: {e}")
            return None
    
    async def _verify_with_casemine(self, citation_text: str, citation_info: Dict,
                                   extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None,
                                   search_query: Optional[str] = None) -> Optional[Dict]:
        """Verify citation with CaseMine legal database."""
        try:
            if not search_query:
                search_query = citation_text
                if extracted_case_name:
                    search_query += f" {extracted_case_name}"
            
            search_url = f"https://www.casemine.com/search/us?q={quote(search_query)}"
            
            self._rate_limit('casemine.com')
            response = self.session.get(search_url, timeout=CASEMINE_TIMEOUT)  # Increased to 8 seconds for reliability
            
            if response.status_code == 200:
                content = response.text
                
                if 'judgement' in content.lower() or 'case-card' in content.lower():
                    # Found relevant legal content
                    pass

                    pass  # Empty block

                
                    pass  # Empty block

                
                case_title_patterns = [
                    r'<a[^>]*href="([^"]*judgement/us/[^"]*)"[^>]*>([^<]*In re[^<]*)</a>',  # In re case links
                    r'<a[^>]*href="([^"]*judgement/us/[^"]*)"[^>]*>([^<]*v\.[^<]*)</a>',  # v. case links
                    r'<a[^>]*href="([^"]*judgement/us/[^"]*)"[^>]*>([^<]*[A-Z][a-z]+[^<]*)</a>',  # General case links
                ]
                
                case_card_patterns = [
                    r'<div[^>]*class="[^"]*case-card[^"]*"[^>]*>.*?<a[^>]*href="([^"]*judgement/us/[^"]*)"[^>]*>([^<]*)</a>.*?</div>',
                    r'<div[^>]*class="[^"]*search-result[^"]*"[^>]*>.*?<a[^>]*href="([^"]*judgement/us/[^"]*)"[^>]*>([^<]*)</a>.*?</div>',
                ]
                
                matches = []
                
                for pattern in case_title_patterns:
                    pattern_matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                    if pattern_matches:
                        matches.extend(pattern_matches)
                
                if not matches:
                    for pattern in case_card_patterns:
                        pattern_matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                        if pattern_matches:
                            matches.extend(pattern_matches)
                
                if not matches:
                    judgement_pattern = r'<a[^>]*href="([^"]*judgement/us/[^"]*)"[^>]*>([^<]*)</a>'
                    judgement_matches = re.findall(judgement_pattern, content, re.IGNORECASE)
                    matches.extend(judgement_matches)
                
                for link_url, link_text in matches:
                    if (citation_text.replace(' ', '').lower() in link_text.replace(' ', '').lower() or
                        (extracted_case_name and extracted_case_name.lower() in link_text.lower())):
                        
                        full_url = link_url if link_url.startswith('http') else f"https://www.casemine.com{link_url}"
                        
                        case_name = self._extract_case_name_from_link(link_text)
                        
                        year = extracted_date or (citation_info.get('year') if citation_info else None)
                        if not year:
                            year_match = re.search(r'(\d{4})', link_text)
                            if year_match:
                                year = year_match.group(1)
                        
                        if case_name:
                            logger.info(f"Found CaseMine case: {case_name} at {full_url}")
                            return {
                                'verified': True,
                                'source': 'casemine',
                                'canonical_name': case_name,
                                'canonical_date': year,
                                'url': full_url,
                                'confidence': 0.85
                            }
            
            return None
            
        except Exception as e:
            logger.warning(f"CaseMine verification failed for {citation_text}: {e}")
            return None
    
    async def _verify_with_google_scholar(self, citation_text: str, citation_info: Dict, 
                                         extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None,
                                         search_query: Optional[str] = None) -> Optional[Dict]:
        """Verify citation with Google Scholar using the courts endpoint for better legal results."""
        try:
            if not search_query:
                search_query = citation_text
                if extracted_case_name:
                    search_query += f" {extracted_case_name}"
            
            search_url = f"https://scholar.google.com/scholar_courts?hl=en&as_sdt=0,33&q={quote(search_query)}"
            
            self._rate_limit('scholar.google.com')
            response = self.session.get(search_url, timeout=WEBSEARCH_TIMEOUT)  # Reduced from 15 to 5 seconds
            
            if response.status_code == 200:
                content = response.text
                
                case_link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
                matches = re.findall(case_link_pattern, content, re.IGNORECASE)
                
                case_name_patterns = [
                    r'<h3[^>]*class="gs_rt"[^>]*>([^<]*)</h3>',  # Google Scholar result titles
                    r'<div[^>]*class="gs_a"[^>]*>([^<]*)</div>',  # Google Scholar author/date info
                    r'<span[^>]*class="gs_ct"[^>]*>([^<]*)</span>',  # Google Scholar citation info
                ]
                
                potential_case_names = []
                for pattern in case_name_patterns:
                    name_matches = re.findall(pattern, content, re.IGNORECASE)
                    potential_case_names.extend(name_matches)
                
                citation_patterns = [
                    r'(\d+\s+Wn\.?\s*2d\s+\d+)',  # Washington citations
                    r'(\d+\s+Wn\.?\s*3d\s+\d+)',  # Washington citations
                    r'(\d+\s+Wn\.?\s*App\.?\s*\d+)',  # Washington App citations
                    r'(\d+\s+P\.\s*3d\s+\d+)',  # Pacific Reporter citations
                    r'(\d+\s+P\.\s*2d\s+\d+)',  # Pacific Reporter citations
                ]
                
                for pattern in citation_patterns:
                    citation_matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in citation_matches:
                        if citation_text.replace(' ', '').lower() in match.replace(' ', '').lower():
                            logger.info(f"Found citation {match} in Google Scholar results for {citation_text}")
                            
                            for link_url, link_text in matches:
                                if link_text and len(link_text.strip()) > 10:  # Valid link text
                                    case_name = self._extract_case_name_from_link(link_text)
                                    if not case_name and extracted_case_name:
                                        case_name = extracted_case_name
                                    
                                    year = extracted_date or (citation_info.get('year') if citation_info else None)
                                    if not year:
                                        year_match = re.search(r'(\d{4})', match)
                                        if year_match:
                                            year = year_match.group(1)
                                    
                                    underlying_url = URLDecoder.decode_google_redirect_url(link_url)
                                    if underlying_url:
                                        full_url = underlying_url
                                        logger.info(f"Extracted underlying URL from Google Scholar: {underlying_url}")
                                    else:
                                        full_url = link_url if link_url.startswith('http') else f"https://scholar.google.com{link_url}"
                                    
                                    if case_name:
                                        return {
                                            'verified': True,
                                            'source': 'google_scholar',
                                            'canonical_name': case_name,
                                            'canonical_date': year,
                                            'url': full_url,
                                            'confidence': 0.8
                                        }
                
                for link_url, link_text in matches:
                    if citation_text.replace(' ', '').lower() in link_text.replace(' ', '').lower():
                        underlying_url = URLDecoder.decode_google_redirect_url(link_url)
                        if underlying_url:
                            full_url = underlying_url
                            logger.info(f"Extracted underlying URL from Google Scholar: {underlying_url}")
                        else:
                            full_url = link_url if link_url.startswith('http') else f"https://scholar.google.com{link_url}"
                        
                        case_name = self._extract_case_name_from_link(link_text)
                        if not case_name and extracted_case_name:
                            case_name = extracted_case_name
                        
                        year = extracted_date or (citation_info.get('year') if citation_info else None)
                        if not year:
                            year_match = re.search(r'(\d{4})', link_text)
                            if year_match:
                                year = year_match.group(1)
                        
                        if case_name:
                            return {
                                'verified': True,
                                'source': 'google_scholar',
                                'canonical_name': case_name,
                                'canonical_date': year,
                                'url': full_url,
                                'confidence': 0.75
                            }
                
                # that might be related to our citation
                if extracted_case_name and potential_case_names:
                    for potential_name in potential_case_names:
                        if self._are_case_names_similar(potential_name, extracted_case_name):
                            year = extracted_date or (citation_info.get('year') if citation_info else None)
                            
                            for link_url, link_text in matches:
                                if potential_name.lower() in link_url.lower():
                                    underlying_url = URLDecoder.decode_google_redirect_url(link_url)
                                    if underlying_url:
                                        full_url = underlying_url
                                        logger.info(f"Extracted underlying URL from Google Scholar (fallback): {underlying_url}")
                                    else:
                                        full_url = link_url if link_url.startswith('http') else f"https://scholar.google.com{link_url}"
                                    return {
                                        'verified': True,
                                        'source': 'google_scholar',
                                        'canonical_name': potential_name,
                                        'canonical_date': year,
                                        'url': full_url,
                                        'confidence': 0.7
                                    }
            
            return None
            
        except Exception as e:
            logger.warning(f"Google Scholar verification failed for {citation_text}: {e}")
            return None
    
    def _verify_with_bing(self, citation_text, citation_info, extracted_case_name, extracted_date, search_query):
        """Verify citation using Bing search"""
        try:
            if not search_query:
                search_query = citation_text
                if extracted_case_name:
                    search_query += f" {extracted_case_name}"
            
            if not isinstance(search_query, str):
                logger.error(f"BING ERROR: search_query is not a string! Type: {type(search_query)}, Value: {search_query}")
                search_query = str(search_query) if search_query is not None else ""
            
            search_url = f"https://www.bing.com/search?q={quote(search_query)}"
            
            self._rate_limit('bing.com')
            response = self.session.get(search_url, timeout=WEBSEARCH_TIMEOUT)  # Reduced from 15 to 5 seconds
            
            if response.status_code == 200:
                content = response.text
                
                matches = []
                
                import re
                
                result_pattern = r'<li[^>]*class="[^"]*b_algo[^"]*"[^>]*>(.*?)</li>'
                results = re.findall(result_pattern, content, re.DOTALL | re.IGNORECASE)
                
                
                for i, result in enumerate(results[:5]):  # Check first 5 results
                    
                    title_match = re.search(r'<h2[^>]*>(.*?)</h2>', result, re.DOTALL | re.IGNORECASE)
                    if title_match:
                        title_content = title_match.group(1)
                        link_match = re.search(r'href="([^"]+)"', title_content)
                        if link_match:
                            link_url = link_match.group(1)
                            link_text_match = re.search(r'<a[^>]*>(.*?)</a>', title_content, re.DOTALL | re.IGNORECASE)
                            if link_text_match:
                                link_text = re.sub(r'<[^>]+>', '', link_text_match.group(1)).strip()
                                matches.append((link_url, link_text))
                    
                    caption_match = re.search(r'<div[^>]*class="[^"]*b_caption[^"]*"[^>]*>(.*?)</div>', result, re.DOTALL | re.IGNORECASE)
                    if caption_match:
                        caption_content = caption_match.group(1)
                        caption_text = re.sub(r'<[^>]+>', '', caption_content).strip()
                        
                        if citation_text.replace(' ', '').lower() in caption_text.replace(' ', '').lower():
                            logger.info(f"Found citation {citation_text} in Bing caption: {caption_text}")
                            
                            case_name = self._extract_case_name_from_text(caption_text)
                            if not case_name and extracted_case_name:
                                case_name = extracted_case_name
                            
                            year = extracted_date or (citation_info.get('year') if citation_info else None)
                            if not year:
                                year_match = re.search(r'(\d{4})', caption_text)
                                if year_match:
                                    year = year_match.group(1)
                            
                            if matches:
                                full_url = matches[0][0]
                                underlying_url = URLDecoder.decode_bing_url(full_url)
                                if underlying_url:
                                    full_url = underlying_url
                                    logger.info(f"Extracted underlying URL from Bing: {underlying_url}")
                                
                                if case_name:
                                    return {
                                        'verified': True,
                                        'source': 'bing',
                                        'canonical_name': case_name,
                                        'canonical_date': year,
                                        'url': full_url,
                                        'confidence': 0.75
                                    }
                
                for link_url, link_text in matches:
                    if citation_text.replace(' ', '').lower() in link_text.replace(' ', '').lower():
                        underlying_url = URLDecoder.decode_bing_url(link_url)
                        if underlying_url:
                            full_url = underlying_url
                            logger.info(f"Extracted underlying URL from Bing: {underlying_url}")
                        else:
                            full_url = link_url if link_url.startswith('http') else f"https://www.bing.com{link_url}"
                        
                        case_name = self._extract_case_name_from_link(link_text)
                        if not case_name and extracted_case_name:
                            case_name = extracted_case_name
                        
                        year = extracted_date or (citation_info.get('year') if citation_info else None)
                        if not year:
                            year_match = re.search(r'(\d{4})', link_text)
                            if year_match:
                                year = year_match.group(1)
                        
                        if case_name:
                            return {
                                'verified': True,
                                'source': 'bing',
                                'canonical_name': case_name,
                                'canonical_date': year,
                                'url': full_url,
                                'confidence': 0.75
                            }
                
                return None
            else:
                logger.warning(f"Bing search failed with status code: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error during Bing verification: {str(e)}")
            return None
    
    async def _verify_with_duckduckgo(self, citation_text: str, citation_info: Dict,
                                     extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None,
                                     search_query: Optional[str] = None) -> Optional[Dict]:
        """Verify citation with DuckDuckGo search."""
        try:
            if not search_query:
                search_query = citation_text
                if extracted_case_name:
                    search_query += f" {extracted_case_name}"
            
            search_url = f"https://duckduckgo.com/html/?q={quote(search_query)}"
            
            self._rate_limit('duckduckgo.com')
            response = self.session.get(search_url, timeout=WEBSEARCH_TIMEOUT)  # Reduced from 15 to 5 seconds
            
            if response.status_code == 200:
                content = response.text
                
                case_link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
                matches = re.findall(case_link_pattern, content, re.IGNORECASE)
                
                case_name_patterns = [
                    r'<h2[^>]*>([^<]*)</h2>',  # DuckDuckGo result titles
                    r'<a[^>]*class="result__title"[^>]*>([^<]*)</a>',  # DuckDuckGo result titles
                    r'<a[^>]*class="result__snippet"[^>]*>([^<]*)</a>',  # DuckDuckGo result snippets
                ]
                
                potential_case_names = []
                for pattern in case_name_patterns:
                    name_matches = re.findall(pattern, content, re.IGNORECASE)
                    potential_case_names.extend(name_matches)
                
                citation_patterns = [
                    r'(\d+\s+Wn\.?\s*2d\s+\d+)',  # Washington citations
                    r'(\d+\s+Wn\.?\s*3d\s+\d+)',  # Washington citations
                    r'(\d+\s+Wn\.?\s*App\.?\s*\d+)',  # Washington App citations
                    r'(\d+\s+P\.\s*3d\s+\d+)',  # Pacific Reporter citations
                    r'(\d+\s+P\.\s*2d\s+\d+)',  # Pacific Reporter citations
                ]
                
                for pattern in citation_patterns:
                    citation_matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in citation_matches:
                        if citation_text.replace(' ', '').lower() in match.replace(' ', '').lower():
                            logger.info(f"Found citation {match} in DuckDuckGo results for {citation_text}")
                            
                            for link_url, link_text in matches:
                                if link_text and len(link_text.strip()) > 10:  # Valid link text
                                    case_name = self._extract_case_name_from_link(link_text)
                                    if not case_name and extracted_case_name:
                                        case_name = extracted_case_name
                                    
                                    year = extracted_date or (citation_info.get('year') if citation_info else None)
                                    if not year:
                                        year_match = re.search(r'(\d{4})', match)
                                        if year_match:
                                            year = year_match.group(1)
                                    
                                    underlying_url = URLDecoder.decode_duckduckgo_url(link_url)
                                    if underlying_url:
                                        full_url = underlying_url
                                        logger.info(f"Extracted underlying URL from DuckDuckGo: {underlying_url}")
                                    else:
                                        full_url = link_url if link_url.startswith('http') else f"https://duckduckgo.com{link_url}"
                                    
                                    if case_name:
                                        return {
                                            'verified': True,
                                            'source': 'duckduckgo',
                                            'canonical_name': case_name,
                                            'canonical_date': year,
                                            'url': full_url,
                                            'confidence': 0.8
                                        }
                
                for link_url, link_text in matches:
                    if citation_text.replace(' ', '').lower() in link_text.replace(' ', '').lower():
                        underlying_url = URLDecoder.decode_duckduckgo_url(link_url)
                        if underlying_url:
                            full_url = underlying_url
                            logger.info(f"Extracted underlying URL from DuckDuckGo: {underlying_url}")
                        else:
                            full_url = link_url if link_url.startswith('http') else f"https://duckduckgo.com{link_url}"
                        
                        case_name = self._extract_case_name_from_link(link_text)
                        if not case_name and extracted_case_name:
                            case_name = extracted_case_name
                        
                        year = extracted_date or (citation_info.get('year') if citation_info else None)
                        if not year:
                            year_match = re.search(r'(\d{4})', link_text)
                            if year_match:
                                year = year_match.group(1)
                        
                        if case_name:
                            return {
                                'verified': True,
                                'source': 'duckduckgo',
                                'canonical_name': case_name,
                                'canonical_date': year,
                                'url': full_url,
                                'confidence': 0.75
                            }
                
                # that might be related to our citation
                if extracted_case_name and potential_case_names:
                    for potential_name in potential_case_names:
                        if self._are_case_names_similar(potential_name, extracted_case_name):
                            year = extracted_date or (citation_info.get('year') if citation_info else None)
                            
                            for link_url, link_text in matches:
                                if potential_name.lower() in link_text.lower():
                                    underlying_url = URLDecoder.decode_duckduckgo_url(link_url)
                                    if underlying_url:
                                        full_url = underlying_url
                                        logger.info(f"Extracted underlying URL from DuckDuckGo (fallback): {underlying_url}")
                                    else:
                                        full_url = link_url if link_url.startswith('http') else f"https://duckduckgo.com{link_url}"
                                    return {
                                        'verified': True,
                                        'source': 'duckduckgo',
                                        'canonical_name': potential_name,
                                        'canonical_date': year,
                                        'url': full_url,
                                        'confidence': 0.7
                                    }
            
            return None
            
        except Exception as e:
            logger.warning(f"DuckDuckGo verification failed for {citation_text}: {e}")
            return None

    async def _verify_with_vlex(self, citation_text: str, citation_info: Dict,
                               extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None,
                               search_query: Optional[str] = None) -> Optional[Dict]:
        """Verify citation with vLex legal database."""
        try:
            if not search_query:
                search_query = citation_text
                if extracted_case_name:
                    search_query += f" {extracted_case_name}"
            
            # vLex search URL - try multiple search endpoints
            search_urls = [
                f"https://vlex.com/search?q={quote(search_query)}",
                f"https://vlex.com/search?query={quote(search_query)}",
                f"https://vlex.com/search?search={quote(search_query)}"
            ]
            
            for search_url in search_urls:
                try:
                    self._rate_limit('vlex.com')
                    response = self.session.get(search_url, timeout=WEBSEARCH_TIMEOUT)  # Reduced from 15 to 5 seconds
                    
                    if response.status_code == 200:
                        content = response.text
                        
                        case_link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
                        matches = re.findall(case_link_pattern, content, re.IGNORECASE)
                        
                        for link_url, link_text in matches:
                            if citation_text.replace(' ', '').lower() in link_text.replace(' ', '').lower():
                                full_url = link_url if link_url.startswith('http') else f"https://vlex.com{link_url}"
                                
                                case_name = self._extract_case_name_from_link(link_text)
                                if not case_name and extracted_case_name:
                                    case_name = extracted_case_name
                                
                                year = extracted_date or (citation_info.get('year') if citation_info else None)
                                if not year:
                                    year_match = re.search(r'(\d{4})', link_text)
                                    if year_match:
                                        year = year_match.group(1)
                                
                                if case_name:
                                    return {
                                        'verified': True,
                                        'source': 'vlex',
                                        'canonical_name': case_name,
                                        'canonical_date': year,
                                        'url': full_url,
                                        'confidence': 0.8
                                    }
                        
                        continue
                        
                except Exception as e:
                    continue
            
            return None
            
        except Exception as e:
            logger.warning(f"vLex verification failed for {citation_text}: {e}")
            return None
    
    def _extract_case_name_from_link(self, link_text: str) -> Optional[str]:
        """Extract case name from link text."""
        clean_text = re.sub(r'<[^>]+>', '', link_text).strip()
        
        case_patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+v\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # Smith v. Jones
            r'(In\s+re\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # In re Smith
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Petition\s+for\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # Smith Petition for Jones
        ]
        
        for pattern in case_patterns:
            match = re.search(pattern, clean_text)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_case_name_from_text(self, text: str) -> Optional[str]:
        """Extract case name from text content."""
        if not text:
            return None
        
        clean_text = re.sub(r'<[^>]+>', '', text).strip()
        
        case_patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+v\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # Smith v. Jones
            r'(In\s+re\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # In re Smith
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Petition\s+for\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # Smith Petition for Jones
        ]
        
        for pattern in case_patterns:
            match = re.search(pattern, clean_text)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _are_case_names_too_similar(self, canonical_name: str, extracted_name: str) -> bool:
        """Check if canonical name is too similar to extracted name (indicating contamination)."""
        if not canonical_name or not extracted_name:
            return False
        
        canonical_clean = re.sub(r'[^\w\s]', '', canonical_name.lower()).strip()
        extracted_clean = re.sub(r'[^\w\s]', '', extracted_name.lower()).strip()
        
        if canonical_clean == extracted_clean:
            return True
        
        if canonical_clean in extracted_clean or extracted_clean in canonical_clean:
            return True
        
        from difflib import SequenceMatcher
        similarity = SequenceMatcher(None, canonical_clean, extracted_clean).ratio()
        if similarity > 0.8:
            return True
        
        return False
    
    def _are_case_names_similar(self, name1: str, name2: str) -> bool:
        """Check if two case names are similar."""
        if not name1 or not name2:
            return False
        
        clean1 = re.sub(r'[^\w\s]', '', name1.lower()).strip()
        clean2 = re.sub(r'[^\w\s]', '', name2.lower()).strip()
        
        if clean1 == clean2:
            return True
        
        if clean1 in clean2 or clean2 in clean1:
            return True
        
        words1 = set(clean1.split())
        words2 = set(clean2.split())
        common_words = words1.intersection(words2)
        
        common_words = {w for w in common_words if len(w) > 2 and w not in {'the', 'and', 'for', 'petition', 'in', 're'}}
        
        return len(common_words) >= 1  # Changed from 2 to 1 - one non-stopword in common is enough

    async def _verify_with_descrybe(self, citation_text: str, citation_info: Dict[str, Any], 
                                   extracted_case_name: Optional[str], extracted_date: Optional[str], 
                                   search_query: str) -> Optional[Dict[str, Any]]:
        """Verify citation using Descrybe.ai legal database."""
        try:
            search_url = "https://descrybe.ai/search"
            
            params = {
                'q': search_query,
                'type': 'cases'  # Focus on case law
            }
            
            response = self.session.get(search_url, params=params, timeout=COURTLISTENER_TIMEOUT)
            
            if response.status_code == 200:
                content = response.text
                
                case_patterns = [
                    r'<a[^>]*href="([^"]*)"[^>]*>([^<]*In re[^<]*)</a>',  # In re case links
                    r'<a[^>]*href="([^"]*)"[^>]*>([^<]*v\.[^<]*)</a>',  # v. case links
                    r'<a[^>]*href="([^"]*)"[^>]*>([^<]*[A-Z][a-z]+[^<]*)</a>',  # General case links
                ]
                
                matches = []
                for pattern in case_patterns:
                    pattern_matches = re.findall(pattern, content, re.IGNORECASE)
                    if pattern_matches:
                        matches.extend(pattern_matches)
                
                for link_url, link_text in matches:
                    if (citation_text.replace(' ', '').lower() in link_text.replace(' ', '').lower() or
                        (extracted_case_name and extracted_case_name.lower() in link_text.lower())):
                        
                        full_url = link_url if link_url.startswith('http') else f"https://descrybe.ai{link_url}"
                        
                        case_name = self._extract_case_name_from_link(link_text)
                        if not case_name and extracted_case_name:
                            case_name = extracted_case_name
                        
                        year = extracted_date or (citation_info.get('year') if citation_info else None)
                        if not year:
                            year_match = re.search(r'(\d{4})', link_text)
                            if year_match:
                                year = year_match.group(1)
                        
                        if case_name:
                            logger.info(f"Found Descrybe.ai case: {case_name} at {full_url}")
                            return {
                                'verified': True,
                                'source': 'descrybe',
                                'canonical_name': case_name,
                                'canonical_date': year,
                                'url': full_url,
                                'confidence': 0.85
                            }
            
            return None
            
        except Exception as e:
            logger.error(f"Descrybe.ai verification error for {citation_text}: {str(e)}")
            return None

    async def _verify_with_scrapingbee(self, citation_text: str, citation_info: Dict,
                                      extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None,
                                      search_query: Optional[str] = None) -> Optional[Dict]:
        """
        Verify citation using ScrapingBee API for reliable web scraping.
        
        NOTE: This is a LAST RESORT method that should only be used when:
        1. All free legal databases fail to find results
        2. All free search engines fail to find results
        3. The citation cannot be verified through any other means
        
        ScrapingBee is a premium service and should be used sparingly.
        """
        try:
            logger.info(f"🔄 LAST RESORT: Using ScrapingBee for {citation_text} (free sources failed)")
            if not search_query:
                search_query = citation_text
                if extracted_case_name:
                    search_query += f" {extracted_case_name}"
            
            api_key = os.getenv('SCRAPINGBEE_API_KEY')
            
            if not api_key:
                logger.warning("ScrapingBee API key not configured. Set SCRAPINGBEE_API_KEY in config/scrapingbee_config.py or environment variable")
                return None
            
            search_urls = [
                f"https://www.google.com/search?q={quote(search_query)}",
                f"https://www.bing.com/search?q={quote(search_query)}",
                f"https://duckduckgo.com/?q={quote(search_query)}",
                f"https://law.justia.com/search?query={quote(search_query)}",
                f"https://caselaw.findlaw.com/search?query={quote(search_query)}",
                f"https://www.casemine.com/search/us?q={quote(search_query)}"
            ]
            
            for search_url in search_urls:
                try:
                    scrapingbee_url = "https://app.scrapingbee.com/api/v1/"
                    params = {
                        'api_key': api_key,
                        'url': search_url,
                        'render_js': 'true',
                        'premium_proxy': 'true',
                        'country_code': 'us',
                        'wait': '3000'  # Wait 3 seconds for JavaScript to load
                    }
                    
                    self._rate_limit('scrapingbee.com')
                    response = self.session.get(scrapingbee_url, params=params, timeout=SCRAPINGBEE_TIMEOUT)
                    
                    if response.status_code == 200:
                        content = response.text
                        
                        citation_patterns = [
                            r'(\d+\s+Wn\.?\s*2d\s+\d+)',  # Washington citations
                            r'(\d+\s+Wn\.?\s*3d\s+\d+)',  # Washington citations
                            r'(\d+\s+Wn\.?\s*App\.?\s*\d+)',  # Washington App citations
                            r'(\d+\s+P\.\s*3d\s+\d+)',  # Pacific Reporter citations
                            r'(\d+\s+P\.\s*2d\s+\d+)',  # Pacific Reporter citations
                        ]
                        
                        for pattern in citation_patterns:
                            citation_matches = re.findall(pattern, content, re.IGNORECASE)
                            for match in citation_matches:
                                if citation_text.replace(' ', '').lower() in match.replace(' ', '').lower():
                                    logger.info(f"Found citation {match} in ScrapingBee results for {citation_text}")
                                    
                                    case_name_patterns = [
                                        r'<h[1-6][^>]*>([^<]*In re[^<]*)</h[1-6]>',  # In re case titles
                                        r'<h[1-6][^>]*>([^<]*v\.[^<]*)</h[1-6]>',  # v. case titles
                                        r'<a[^>]*href="[^"]*"[^>]*>([^<]*In re[^<]*)</a>',  # In re case links
                                        r'<a[^>]*href="[^"]*"[^>]*>([^<]*v\.[^<]*)</a>',  # v. case links
                                    ]
                                    
                                    case_name = None
                                    for case_pattern in case_name_patterns:
                                        case_matches = re.findall(case_pattern, content, re.IGNORECASE)
                                        if case_matches:
                                            case_name = case_matches[0].strip()
                                            break
                                    
                                    if not case_name and extracted_case_name:
                                        case_name = extracted_case_name
                                    
                                    year = extracted_date or (citation_info.get('year') if citation_info else None)
                                    if not year:
                                        year_match = re.search(r'(\d{4})', content)
                                        if year_match:
                                            year = year_match.group(1)
                                    
                                    source = 'scrapingbee'
                                    if 'google.com' in search_url:
                                        source = 'google'
                                    elif 'bing.com' in search_url:
                                        source = 'bing'
                                    elif 'duckduckgo.com' in search_url:
                                        source = 'duckduckgo'
                                    elif 'justia.com' in search_url:
                                        source = 'justia'
                                    elif 'findlaw.com' in search_url:
                                        source = 'findlaw'
                                    elif 'casemine.com' in search_url:
                                        source = 'casemine'
                                    
                                    return {
                                        'verified': True,
                                        'source': source,
                                        'canonical_name': case_name,
                                        'canonical_date': year,
                                        'url': search_url,
                                        'confidence': 0.85
                                    }
                    
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    continue
            
            return None
            
        except Exception as e:
            logger.warning(f"ScrapingBee verification failed for {citation_text}: {e}")
            return None

    async def verify_citations_batch(self, citations: List[str], extracted_case_names: Optional[List[str]] = None, extracted_dates: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Verify multiple citations using CourtListener batch API first, then enhanced fallback.
        
        Args:
            citations: List of citation texts to verify
            extracted_case_names: Optional list of extracted case names
            extracted_dates: Optional list of extracted dates
            
        Returns:
            List of verification results for each citation
        """
        if not citations:
            return []
        
        logger.info(f"🚀 BATCH VERIFICATION CALLED for {len(citations)} citations")
        
        if extracted_case_names and len(extracted_case_names) != len(citations):
            logger.warning("extracted_case_names length doesn't match citations length")
            extracted_case_names = None
        
        if extracted_dates and len(extracted_dates) != len(citations):
            logger.warning("extracted_dates length doesn't match citations length")
            extracted_dates = None
        
        results = []
        
        try:
            courtlistener_results = await self._try_courtlistener_batch_first(citations, extracted_case_names)
            
            citations_needing_fallback = []
            fallback_indices = []
            
            for i, (citation, courtlistener_result) in enumerate(zip(citations, courtlistener_results)):
                if courtlistener_result and courtlistener_result.get('verified', False):
                    results.append(courtlistener_result)
                    logger.info(f"✅ CourtListener batch verified: {citation} -> {courtlistener_result.get('canonical_name', 'N/A')}")
                else:
                    citations_needing_fallback.append(citation)
                    fallback_indices.append(i)
                    results.append({
                        'verified': False,
                        'source': 'pending_fallback',
                        'canonical_name': None,
                        'canonical_date': None,
                        'url': None,
                        'canonical_url': None,
                        'confidence': 0.0,
                        'error': 'CourtListener failed, pending fallback'
                    })
            
            if citations_needing_fallback:
                logger.info(f"Processing {len(citations_needing_fallback)} citations with enhanced fallback verification")
                
                for i, citation in enumerate(citations_needing_fallback):
                    original_index = fallback_indices[i]
                    extracted_case_name = extracted_case_names[original_index] if extracted_case_names and original_index < len(extracted_case_names) else None
                    extracted_date = extracted_dates[original_index] if extracted_dates and original_index < len(extracted_dates) else None
                    
                    fallback_result = await self.verify_citation(citation, extracted_case_name, extracted_date, has_courtlistener_data=False)
                    
                    results[original_index] = fallback_result
                    
                    if fallback_result.get('verified', False):
                        logger.info(f"✅ Fallback verified: {citation} -> {fallback_result.get('canonical_name', 'N/A')} (via {fallback_result.get('source', 'unknown')})")
                    else:
            
            logger.info(f"Batch verification completed: {len([r for r in results if r.get('verified', False)])}/{len(citations)} verified")
            return results
            
        except Exception as e:
            logger.error(f"Batch verification error: {e}")
            return [self._create_fallback_result(citation, "batch_error") for citation in citations]
    
    async def _try_courtlistener_batch_first(self, citations: List[str], extracted_case_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Try CourtListener batch verification first for fast, reliable results.
        
        Args:
            citations: List of citations to verify
            extracted_case_names: Optional list of extracted case names
            
        Returns:
            List of CourtListener verification results
        """
        try:
            courtlistener_api_key = os.getenv('COURTLISTENER_API_KEY')
            if not courtlistener_api_key:
                return [self._create_fallback_result(citation, "no_api_key") for citation in citations]
            
            try:
                from src.enhanced_courtlistener_verification import EnhancedCourtListenerVerifier
            except ImportError:
                return [self._create_fallback_result(citation, "verifier_unavailable") for citation in citations]
            
            courtlistener_verifier = EnhancedCourtListenerVerifier(courtlistener_api_key)
            
            logger.info(f"Attempting CourtListener batch verification for {len(citations)} citations")
            batch_results = courtlistener_verifier.verify_citations_batch(citations, extracted_case_names)
            
            if batch_results and len(batch_results) == len(citations):
                logger.info(f"✓ CourtListener batch verification successful for {len(citations)} citations")
                
                processed_results = []
                for result in batch_results:
                    if result and result.get('verified', False):
                        url = result.get('url', '')
                        canonical_url = result.get('canonical_url') or result.get('url', '')
                        
                        if url and url.startswith('/'):
                            url = f"https://www.courtlistener.com{url}"
                        if canonical_url and canonical_url.startswith('/'):
                            canonical_url = f"https://www.courtlistener.com{canonical_url}"
                        
                        processed_result = {
                            'verified': True,
                            'canonical_name': result.get('canonical_name'),
                            'canonical_date': result.get('canonical_date'),
                            'url': url,
                            'canonical_url': canonical_url,
                            'source': 'CourtListener',
                            'validation_method': result.get('validation_method', 'batch_citation_lookup'),
                            'confidence': result.get('confidence', 0.9),
                            'verification_strategy': 'courtlistener_batch'
                        }
                        processed_results.append(processed_result)
                    else:
                        processed_results.append(self._create_fallback_result(citations[len(processed_results)], "batch_failed"))
                
                return processed_results
            else:
                return [self._create_fallback_result(citation, "batch_failed") for citation in citations]
                
        except Exception as e:
            logger.warning(f"CourtListener batch verification error: {str(e)}")
            return [self._create_fallback_result(citation, "batch_error") for citation in citations]

    def verify_citation_sync_optimized(self, citation_text: str, extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None) -> Dict:
        """
        Optimized synchronous version of verify_citation with early termination, caching, and efficient search ordering.
        """
        start_time = time.time()
        
        cache_key = f"{citation_text}_{extracted_case_name}_{extracted_date}"
        if cache_key in self._verification_cache:
            cached_result = self._verification_cache[cache_key]
            if time.time() - cached_result.get('cache_time', 0) < self._cache_ttl:
                logger.info(f"Cache hit for {citation_text}")
                return cached_result['result']
        
        logger.info(f"Starting optimized sync verification for {citation_text}")
        
        queries = self.generate_enhanced_legal_queries(citation_text, extracted_case_name)
        
        search_sources = [
            ('courtlistener_lookup', self._verify_with_courtlistener_lookup_sync, 4.0),
            ('courtlistener_search', self._verify_with_courtlistener_search_sync, 4.0),
            ('casemine', self._verify_with_casemine_sync, 3.0),
            ('bing', self._verify_with_bing_sync, 4.0),
            ('justia', self._verify_with_justia_sync, 4.0),
            ('google', self._verify_with_google_scholar_sync, 3.0),
            ('duckduckgo', self._verify_with_duckduckgo_sync, 3.0),
        ]
        
        for source_name, verify_func, timeout in search_sources:
            
            try:
                for query_info in queries[:2]:  # Limit to 2 queries per source
                    query = query_info['query']
                    result = verify_func(citation_text, {}, extracted_case_name, extracted_date, query)
                    
                    if result and result.get('verified', False):
                        elapsed = time.time() - start_time
                        logger.info(f"✅ Optimized sync verification successful: {citation_text} -> {result.get('canonical_name', 'N/A')} (via {source_name}) in {elapsed:.1f}s")
                        
                        self._verification_cache[cache_key] = {
                            'result': result,
                            'cache_time': time.time()
                        }
                        
                        return result
                        
            except Exception as e:
                continue
        
        elapsed = time.time() - start_time
        logger.info(f"❌ Optimized sync verification failed for {citation_text} after {elapsed:.1f}s")
        
        failed_result = {
            'verified': False,
            'source': 'optimized_sync_failed',
            'canonical_name': None,
            'canonical_date': None,
            'url': None,
            'confidence': 0.0,
            'error': 'No verification sources succeeded'
        }
        
        self._verification_cache[cache_key] = {
            'result': failed_result,
            'cache_time': time.time()
        }
        
        return failed_result

    def _verify_with_casemine_sync(self, citation_text: str, citation_info: Dict, 
                                  extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None,
                                  search_query: Optional[str] = None) -> Optional[Dict]:
        """Synchronous version of CaseMine verification."""
        try:
            if not search_query:
                search_query = citation_text
                if extracted_case_name:
                    search_query += f" {extracted_case_name}"
            
            search_url = f"https://www.casemine.com/search?q={quote(search_query)}"
            self._rate_limit('casemine.com')
            response = self.session.get(search_url, timeout=WEBSEARCH_TIMEOUT)
            
            if response.status_code == 200 and 'judgement' in response.text:
                judgement_pattern = r'href="([^"]*judgement[^"]*)"'
                matches = re.findall(judgement_pattern, response.text)
                
                if matches:
                    case_url = matches[0] if matches[0].startswith('http') else f"https://www.casemine.com{matches[0]}"
                    case_name = None
                    canonical_date = None
                    
                    try:
                        self._rate_limit('casemine.com')
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                            'Accept-Language': 'en-US,en;q=0.5',
                            'Accept-Encoding': 'gzip, deflate',
                            'Connection': 'keep-alive',
                            'Upgrade-Insecure-Requests': '1',
                        }
                        page_resp = self.session.get(case_url, headers=headers, timeout=CASEMINE_TIMEOUT)
                        if page_resp.status_code == 200:
                            html = page_resp.text
                            
                            if 'capcha' in html.lower() or 'captcha' in html.lower() or 'recaptcha' in html.lower():
                                case_name = "Unknown Case"
                                logger.info(f"CaseMine CAPTCHA detected - using 'Unknown Case' to prevent contamination")
                            else:
                                title_patterns = [
                                    r'<title[^>]*>([^<]*v\.[^<]*)</title>',
                                    r'<h1[^>]*>([^<]*v\.[^<]*)</h1>',
                                    r'<h2[^>]*>([^<]*v\.[^<]*)</h2>',
                                    r'"caseName"\s*:\s*"([^"]*v\.[^"]*)"',
                                    r'"title"\s*:\s*"([^"]*v\.[^"]*)"'
                                ]
                                
                                for pattern in title_patterns:
                                    m = re.search(pattern, html, re.IGNORECASE)
                                    if m:
                                        case_name = m.group(1).strip()
                                        case_name = re.sub(r'\s+', ' ', case_name)  # Normalize whitespace
                                        case_name = re.sub(r'^[^A-Za-z]*', '', case_name)  # Remove leading non-letters
                                        if len(case_name) > 10:  # Ensure it's a reasonable case name
                                            break
                                
                                date_patterns = [
                                    r'(Judgment Date|Decision Date)\s*[:\-]?\s*([A-Za-z]+\s+\d{1,2},\s+\d{4}|\d{4}-\d{2}-\d{2}|\d{4})',
                                    r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})"',
                                    r'"decisionDate"\s*:\s*"(\d{4}-\d{2}-\d{2})"'
                                ]
                                
                                for pattern in date_patterns:
                                    m = re.search(pattern, html, re.IGNORECASE)
                                    if m:
                                        canonical_date = m.group(2) if len(m.groups()) > 1 else m.group(1)
                                        break
                                
                                if not canonical_date:
                                    # time tag
                                    m = re.search(r'<time[^>]*>([^<]*\d{4}[^<]*)</time>', html, re.IGNORECASE)
                                    if m:
                                        # extract year or ISO
                                        y = re.search(r'(\d{4}(?:-\d{2}-\d{2})?)', m.group(1))
                                        if y:
                                            canonical_date = y.group(1)
                                            
                                if not canonical_date:
                                    m = re.search(r'(\d{4})', citation_text)
                                    if m:
                                        canonical_date = m.group(1)
                                    
                    except Exception as ex:
                    
                    if case_name and case_name != "Unknown Case":
                        if self._are_case_names_too_similar(case_name, extracted_case_name):
                            return None
                        logger.info(f"Found CaseMine case: {case_name} at {case_url}")
                        is_verified = True
                    else:
                        logger.info(f"CaseMine found case at {case_url} but couldn't extract canonical name")
                        case_name = "Unknown Case"
                        is_verified = False
                    
                    return {
                        'verified': is_verified,
                        'source': 'CaseMine',
                        'canonical_name': case_name,
                        'canonical_date': canonical_date,
                        'url': case_url,
                        'confidence': 0.85
                    }
            
            return None
            
        except Exception as e:
            return None

    def _verify_with_bing_sync(self, citation_text: str, citation_info: Dict, 
                              extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None,
                              search_query: Optional[str] = None) -> Optional[Dict]:
        """Synchronous version of Bing verification."""
        try:
            if not search_query:
                search_query = citation_text
                if extracted_case_name:
                    search_query += f" {extracted_case_name}"
            
            search_url = f"https://www.bing.com/search?q={quote(search_query)}"
            self._rate_limit('bing.com')
            response = self.session.get(search_url, timeout=WEBSEARCH_TIMEOUT)
            
            if response.status_code == 200:
                result_pattern = r'<li[^>]*class="[^"]*b_algo[^"]*"[^>]*>(.*?)</li>'
                results = re.findall(result_pattern, response.text, re.DOTALL | re.IGNORECASE)
                
                for result in results[:3]:
                    caption_match = re.search(r'<div[^>]*class="[^"]*b_caption[^"]*"[^>]*>(.*?)</div>', result, re.DOTALL | re.IGNORECASE)
                    if caption_match:
                        caption_text = re.sub(r'<[^>]+>', '', caption_match.group(1)).strip()
                        
                        if citation_text.replace(' ', '').lower() in caption_text.replace(' ', '').lower():
                            case_name = self._extract_case_name_from_text(caption_text)
                            if not case_name or case_name == extracted_case_name:
                                continue
                            
                            if self._are_case_names_too_similar(case_name, extracted_case_name):
                                continue
                            
                            if 'r.bing.com' in case_url or 'bing.com/rs/' in case_url:
                                continue
                                
                            year_match = re.search(r'(\d{4})', caption_text)
                            year = year_match.group(1) if year_match else None
                            
                            link_match = re.search(r'href="([^"]+)"', result)
                            if link_match:
                                return {
                                    'verified': True,
                                    'source': 'Bing',
                                    'canonical_name': case_name,
                                    'canonical_date': year,
                                    'url': link_match.group(1),
                                    'confidence': 0.75
                                }
            
            return None
            
        except Exception as e:
            return None

    def _verify_with_courtlistener_lookup_sync(self, citation_text: str, citation_info: Dict,
                                               extracted_case_name: Optional[str] = None,
                                               extracted_date: Optional[str] = None,
                                               search_query: Optional[str] = None) -> Optional[Dict]:
        """Enhanced CourtListener citation-lookup with strict matching criteria.
        Docs: https://www.courtlistener.com/help/api/rest/citation-lookup/
        """
        try:
            import os
            api_key = os.environ.get('COURTLISTENER_API_KEY') or os.environ.get('CL_API_KEY')
            if not api_key:
                try:
                    api_key = getattr(self, 'api_keys', {}).get('courtlistener')
                except Exception:
                    api_key = None
            if not api_key:
                return None
            headers = {'Authorization': f'Token {api_key}'}
            try:
                masked = f"{api_key[:6]}...{api_key[-4:]}"
            except Exception:
                pass
            url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
            
            def normalize_reporter(cit: str) -> str:
                c = cit
                c = c.replace('\u2019', "'")  # Fix smart quotes
                c = re.sub(r'\bWn\.?\s*2d\b', 'Wash. 2d', c, flags=re.IGNORECASE)
                c = re.sub(r'\bWash\.?\s*2d\b', 'Wash. 2d', c, flags=re.IGNORECASE)
                c = re.sub(r'\bWn\.?\s*App\.?\b', 'Wash. App.', c, flags=re.IGNORECASE)
                c = re.sub(r'\bWash\.?\s*App\.?\b', 'Wash. App.', c, flags=re.IGNORECASE)
                return c

            norm_citation = normalize_reporter(citation_text)
            payload = {'text': norm_citation}
            self._rate_limit('courtlistener.com')
            resp = self.session.post(url, json=payload, headers=headers, timeout=COURTLISTENER_TIMEOUT)
            
            if resp.status_code != 200:
                return None
                
            data = resp.json() or {}
            
            if isinstance(data, list) and len(data) > 0:
                citation_data = data[0]
                
                if citation_data.get("status") == 200 and citation_data.get("clusters"):
                    clusters = citation_data["clusters"]
                    
                    if clusters:
                        best_case = self._find_best_case_with_strict_criteria(clusters, citation_text, extracted_case_name)
                        
                        if best_case:
                            case_name = best_case.get('case_name')
                            abs_url = best_case.get('absolute_url')
                            if abs_url and abs_url.startswith('/'):
                                abs_url = f"https://www.courtlistener.com{abs_url}"
                            date_filed = best_case.get('date_filed')
                            canonical_date = None
                            if isinstance(date_filed, str):
                                m = re.search(r'(\d{4})', date_filed)
                                if m:
                                    canonical_date = m.group(1)
                            
                            return {
                                'case_name': case_name,
                                'canonical_name': case_name,
                                'canonical_date': canonical_date,
                                'canonical_url': abs_url,
                                'verified': True,
                                'source': 'CourtListener Citation Lookup',
                                'confidence': 0.95,
                                'raw': citation_data
                            }
                        else:
                            return None
                    else:
                        return None
                else:
                    return None
            else:
                return None
                
        except Exception as e:
            return None

    def _find_best_case_with_strict_criteria(self, clusters: List[Dict], citation: str, extracted_case_name: Optional[str]) -> Optional[Dict]:
        """
        Find the best case using strict matching criteria:
        1. Citation must match exactly
        2. Year should be close (within 5 years)
        3. Case names should have meaningful words in common
        
        Args:
            clusters: List of case clusters from CourtListener API
            citation: Citation text to match
            extracted_case_name: Extracted case name from document
            
        Returns:
            Best matching case or None
        """
        if not clusters:
            return None
        
        best_match = None
        best_score = 0.0
        
        for cluster in clusters:
            score = self._calculate_strict_match_score(cluster, citation, extracted_case_name)
            if score > best_score:
                best_score = score
                best_match = cluster
        
        if best_match and best_score >= 1.0:
            return best_match
        
        return None

    def _calculate_strict_match_score(self, case: Dict, citation: str, extracted_case_name: Optional[str]) -> float:
        """
        Calculate match score using strict criteria.
        
        Returns:
            float: Score >= 1.0 for a match, 0.0 for no match
        """
        score = 0.0
        
        case_citations = case.get('citations', [])
        citation_found = False
        
        for case_citation in case_citations:
            if case_citation.get('volume') and case_citation.get('reporter') and case_citation.get('page'):
                case_citation_str = f"{case_citation['volume']} {case_citation['reporter']} {case_citation['page']}"
                
                if self._citations_match(citation, case_citation_str):
                    citation_found = True
                    break
        
        if not citation_found:
            return 0.0
        
        score += 1.0
        
        exp_year = self._extract_year_from_citation(citation)
        can_year = self._extract_year_from_date(case.get('date_filed') or '')
        
        if exp_year and can_year:
            try:
                year_diff = abs(int(exp_year) - int(can_year))
                if year_diff == 0:
                    score += 1.0  # Exact match
                elif year_diff <= 5:
                    score += 0.5  # Close match
                elif year_diff <= 10:
                    score += 0.2  # Distant match
            except (ValueError, TypeError):
                score += 0.3  # Benefit of doubt
        else:
            score += 0.3  # No year info
        
        if extracted_case_name:
            if self._has_meaningful_words_in_common(extracted_case_name, case.get('case_name', '')):
                score += 1.0
            else:
                score += 0.5  # Partial credit
        else:
            score += 0.5  # No extracted name
        
        return score

    def _extract_year_from_citation(self, citation: str) -> Optional[str]:
        """Extract year from citation text."""
        year_match = re.search(r'(19|20)\d{2}', citation)
        return year_match.group(0) if year_match else None

    def _extract_year_from_date(self, date_str: str) -> Optional[str]:
        """Extract year from date string."""
        if not date_str:
            return None
        year_match = re.search(r'(19|20)\d{2}', str(date_str))
        return year_match.group(0) if year_match else None

    def _citations_match(self, citation1: str, citation2: str) -> bool:
        """Check if two citations match (allowing for reporter variations)."""
        if not citation1 or not citation2:
            return False
        
        norm1 = self._normalize_citation(citation1)
        norm2 = self._normalize_citation(citation2)
        
        return norm1 == norm2

    def _normalize_citation(self, citation: str) -> str:
        """Normalize citation for comparison."""
        citation = re.sub(r'\s+', '', citation.lower())
        
        citation = re.sub(r'wn\.?2d', 'wash.2d', citation)
        citation = re.sub(r'wash\.?2d', 'wash.2d', citation)
        citation = re.sub(r'wn\.?app\.?', 'wash.app.', citation)
        citation = re.sub(r'wash\.?app\.?', 'wash.app.', citation)
        
        return citation

    def _has_meaningful_words_in_common(self, name1: str, name2: str) -> bool:
        """Check if two case names have meaningful words in common."""
        if not name1 or not name2:
            return False
        
        stopwords = {'v', 'vs', 'and', 'of', 'the', 'in', 'for', 'on', 'at', 'to', 'a', 'an'}
        
        words1 = set(re.findall(r'\b[a-z]+\b', name1.lower()))
        words2 = set(re.findall(r'\b[a-z]+\b', name2.lower()))
        
        words1 = words1 - stopwords
        words2 = words2 - stopwords
        
        common_words = words1.intersection(words2)
        return len(common_words) > 0

    def _verify_with_courtlistener_search_sync(self, citation_text: str, citation_info: Dict,
                                               extracted_case_name: Optional[str] = None,
                                               extracted_date: Optional[str] = None,
                                               search_query: Optional[str] = None) -> Optional[Dict]:
        """Synchronous CourtListener Search API verification.
        Prefers CL canonical data and URLs. Docs: https://www.courtlistener.com/help/api/rest/search/
        """
        try:
            if not search_query:
                parts = [citation_text]
                clean_name = None
                if extracted_case_name and isinstance(extracted_case_name, str):
                    tokens = extracted_case_name.split()
                    for idx, tk in enumerate(tokens):
                        if tk[:1].isupper():
                            clean_name = " ".join(tokens[idx:])
                            break
                    if not clean_name:
                        clean_name = extracted_case_name
                if clean_name:
                    parts.append(clean_name)
                if extracted_date:
                    parts.append(str(extracted_date))
                def normalize_reporter_q(cit: str) -> str:
                    c = cit.replace('\u2019', "'")
                    c = re.sub(r'\bWn\.?\s*2d\b', 'Wash. 2d', c, flags=re.IGNORECASE)
                    c = re.sub(r'\bWash\.?\s*2d\b', 'Wash. 2d', c, flags=re.IGNORECASE)
                    c = re.sub(r'\bWn\.?\s*App\.?\b', 'Wash. App.', c, flags=re.IGNORECASE)
                    c = re.sub(r'\bWash\.?\s*App\.?\b', 'Wash. App.', c, flags=re.IGNORECASE)
                    return c
                parts = [normalize_reporter_q(p) for p in parts]
                search_query = " ".join([p for p in parts if p])

            base_url = "https://www.courtlistener.com/api/rest/v4/search/"
            params = {
                'q': search_query,
                'type': 'opinion',
                'order_by': 'relevance'
            }

            headers = {}
            import os
            api_key = os.environ.get('COURTLISTENER_API_KEY') or os.environ.get('CL_API_KEY')
            if not api_key:
                try:
                    api_key = getattr(self, 'api_keys', {}).get('courtlistener')
                except Exception:
                    api_key = None
            if api_key:
                headers['Authorization'] = f'Token {api_key}'
                try:
                    masked = f"{api_key[:6]}...{api_key[-4:]}"
                except Exception:
                    pass

            self._rate_limit('courtlistener.com')
            resp = self.session.get(base_url, params=params, headers=headers, timeout=WEBSEARCH_TIMEOUT)
            if resp.status_code != 200:
                return None

            data = resp.json()
            results = data.get('results') or data.get('results', [])
            if not results:
                return None

            best = results[0]
            case_name = best.get('case_name') or best.get('caseName')
            date_filed = best.get('date_filed') or best.get('dateFiled')
            abs_url = best.get('absolute_url') or best.get('absoluteUrl')
            if abs_url and abs_url.startswith('/'):
                abs_url = f"https://www.courtlistener.com{abs_url}"

            if not case_name:
                return None

            canonical_date = None
            if isinstance(date_filed, str):
                m = re.search(r'(\d{4})', date_filed)
                if m:
                    canonical_date = m.group(1)

            return {
                'verified': True,
                'source': 'CourtListener Search API',
                'canonical_name': case_name,
                'canonical_date': canonical_date,
                'canonical_url': abs_url,
                'url': abs_url,
                'confidence': 0.9,
                'validation_method': 'courtlistener_search'
            }

        except Exception as e:
            return None

    def _verify_with_justia_sync(self, citation_text: str, citation_info: Dict, 
                                extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None,
                                search_query: Optional[str] = None) -> Optional[Dict]:
        """Synchronous version of Justia verification."""
        try:
            if not search_query:
                search_query = citation_text
                if extracted_case_name:
                    search_query += f" {extracted_case_name}"
            
            search_url = f"https://law.justia.com/search?query={quote(search_query)}"
            self._rate_limit('justia.com')
            response = self.session.get(search_url, timeout=WEBSEARCH_TIMEOUT)
            
            if response.status_code == 200:
                case_link_pattern = r'<a[^>]*href="([^"]*cases[^"]+)"[^>]*>([^<]*)</a>'
                matches = re.findall(case_link_pattern, response.text, re.IGNORECASE)
                
                for link_url, link_text in matches:
                    if citation_text.replace(' ', '').lower() in link_text.replace(' ', '').lower():
                        full_url = link_url if link_url.startswith('http') else f"https://law.justia.com{link_url}"
                        case_name = self._extract_case_name_from_link(link_text)
                        if not case_name or case_name == extracted_case_name:
                            continue
                        year = None
                        
                        try:
                            self._rate_limit('justia.com')
                            page_resp = self.session.get(full_url, timeout=WEBSEARCH_TIMEOUT)
                            if page_resp.status_code == 200:
                                html = page_resp.text
                                m = re.search(r'(Date\s*:?|Decided\s*:?|Filed\s*:?)[^\n\r:]*[:\-]?\s*(?:<[^>]+>\s*)*([A-Za-z]+\s+\d{1,2},\s+\d{4}|\d{4}-\d{2}-\d{2}|\d{4})', html, re.IGNORECASE)
                                if m:
                                    year = m.group(2)
                                if not year:
                                    m = re.search(r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})"', html)
                                    if m:
                                        year = m.group(1)
                                if not year:
                                    m = re.search(r'<time[^>]*datetime="(\d{4}-\d{2}-\d{2})"', html, re.IGNORECASE)
                                    if m:
                                        year = m.group(1)
                                if not year:
                                    m = re.search(r'<time[^>]*>([^<]*\d{4}[^<]*)</time>', html, re.IGNORECASE)
                                    if m:
                                        y = re.search(r'(\d{4}(?:-\d{2}-\d{2})?)', m.group(1))
                                        if y:
                                            year = y.group(1)
                        except Exception:
                            pass
                        
                        return {
                            'verified': True,
                            'source': 'Justia',
                            'canonical_name': case_name,
                            'canonical_date': year,
                            'url': full_url,
                            'confidence': 0.8
                        }
            
            return None
            
        except Exception as e:
            return None

    def _verify_with_google_scholar_sync(self, citation_text: str, citation_info: Dict, 
                                        extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None,
                                        search_query: Optional[str] = None) -> Optional[Dict]:
        """Synchronous version of Google Scholar verification."""
        try:
            if not search_query:
                search_query = citation_text
                if extracted_case_name:
                    search_query += f" {extracted_case_name}"
            
            search_url = f"https://scholar.google.com/scholar?q={quote(search_query)}"
            self._rate_limit('google.com')
            response = self.session.get(search_url, timeout=WEBSEARCH_TIMEOUT)
            
            if response.status_code == 200 and citation_text.replace(' ', '').lower() in response.text.replace(' ', '').lower():
                case_name = self._extract_case_name_from_text(response.text)
                if not case_name or case_name == extracted_case_name:
                    return None
                
                if self._are_case_names_too_similar(case_name, extracted_case_name):
                    return None
                    
                year_match = re.search(r'(\d{4})', response.text)
                year = year_match.group(1) if year_match else None
                
                return {
                    'verified': True,
                    'source': 'Google Scholar',
                    'canonical_name': case_name,
                    'canonical_date': year,
                    'url': search_url,
                    'confidence': 0.7
                }
            
            return None
            
        except Exception as e:
            return None

    def _verify_with_duckduckgo_sync(self, citation_text: str, citation_info: Dict, 
                                    extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None,
                                    search_query: Optional[str] = None) -> Optional[Dict]:
        """Synchronous version of DuckDuckGo verification."""
        try:
            if not search_query:
                search_query = citation_text
                if extracted_case_name:
                    search_query += f" {extracted_case_name}"
            
            search_url = f"https://duckduckgo.com/html/?q={quote(search_query)}"
            self._rate_limit('duckduckgo.com')
            response = self.session.get(search_url, timeout=WEBSEARCH_TIMEOUT)
            
            if response.status_code == 200 and citation_text.replace(' ', '').lower() in response.text.replace(' ', '').lower():
                case_name = self._extract_case_name_from_text(response.text)
                if not case_name or case_name == extracted_case_name:
                    return None
                
                if self._are_case_names_too_similar(case_name, extracted_case_name):
                    return None
                
                if 'duckduckgo.com/html/' in url or 'Any Time' in case_name or 'Past Day' in case_name:
                    return None
                    
                year_match = re.search(r'(\d{4})', response.text)
                year = year_match.group(1) if year_match else None
                
                return {
                    'verified': True,
                    'source': 'DuckDuckGo',
                    'canonical_name': case_name,
                    'canonical_date': year,
                    'url': search_url,
                    'confidence': 0.65
                }
            
            return None
            
        except Exception as e:
            return None

async def verify_citation_with_enhanced_fallback(citation_text: str, extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None) -> Dict:
    """
    Convenience function to verify a citation using the enhanced fallback verifier.
    
    Args:
        citation_text: The citation to verify
        extracted_case_name: Optional extracted case name
        extracted_date: Optional extracted date
        
    Returns:
        Dict with verification results
    """
    verifier = EnhancedFallbackVerifier()
    return await verifier.verify_citation(citation_text, extracted_case_name)

async def verify_citation_with_vlex(citation_text: str, extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None) -> Optional[Dict]:
    """
    Convenience function to verify a citation specifically using vLex.
    
    Args:
        citation_text: The citation to verify
        extracted_case_name: Optional extracted case name
        extracted_date: Optional extracted date
        
    Returns:
        Dict with verification results
    """
    verifier = EnhancedFallbackVerifier()
    return await verifier._verify_with_vlex(citation_text, {}, extracted_case_name, extracted_date, None)
