#!/usr/bin/env python3
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
import logging
import re
import time
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin, quote, urlparse
import requests
import json
from src.url_decoder import URLDecoder

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
        
        # Rate limiting
        self.last_request_time = {}
        self.min_delay = 0.2  # Reduced from 1.0 to 0.2 seconds for faster processing
        
        # Legal-specific domains with priority scores
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
        
        # State-specific citation patterns (extensible for all 50 states)
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
        
        # Regional reporter patterns (cover all states)
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
        
        # Enable experimental engines for broader coverage
        self.enable_experimental_engines = enable_experimental_engines
        
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
        
        # Washington reporter normalization
        normalized = re.sub(r'\bWN\.?\b', 'Wash.', citation, flags=re.IGNORECASE)
        normalized = re.sub(r'\bWn\.?\b', 'Wash.', normalized, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def detect_state_from_citation(self, citation: str) -> Optional[str]:
        """Detect which state a citation is from based on citation patterns."""
        for state_code, patterns in self.state_patterns.items():
            for pattern in patterns:
                if re.search(pattern, citation, re.IGNORECASE):
                    return state_code
        
        # Check regional reporters
        for reporter_code, patterns in self.regional_reporters.items():
            for pattern in patterns:
                if re.search(pattern, citation, re.IGNORECASE):
                    # Map regional reporters to likely states
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
            # Replace Wn. with Wash.
            if 'Wn.' in citation:
                variants.append(citation.replace('Wn.', 'Wash.'))
            
            # Replace Wash. with Wn.
            if 'Wash.' in citation:
                variants.append(citation.replace('Wash.', 'Wn.'))
            
            # Replace Washington with Wn.
            if 'Washington' in citation:
                variants.append(citation.replace('Washington', 'Wn.'))
            
            # Handle Wn. App. → Wash. App.
            if 'Wn. App.' in citation:
                variants.append(citation.replace('Wn. App.', 'Wash. App.'))
            
            # Handle Wash. App. → Wn. App.
            if 'Wash. App.' in citation:
                variants.append(citation.replace('Wash. App.', 'Wn. App.'))
            
            # Handle Wn.2d → Wash.2d
            if 'Wn.2d' in citation:
                variants.append(citation.replace('Wn.2d', 'Wash.2d'))
            
            # Handle Wash.2d → Wn.2d
            if 'Wash.2d' in citation:
                variants.append(citation.replace('Wash.2d', 'Wn.2d'))
        
        elif state == 'CA':  # California
            # Replace Cal. with California
            if 'Cal.' in citation:
                variants.append(citation.replace('Cal.', 'California'))
            
            # Replace California with Cal.
            if 'California' in citation:
                variants.append(citation.replace('California', 'Cal.'))
        
        elif state == 'NY':  # New York
            # Replace N.Y. with New York
            if 'N.Y.' in citation:
                variants.append(citation.replace('N.Y.', 'New York'))
            
            # Replace New York with N.Y.
            if 'New York' in citation:
                variants.append(citation.replace('New York', 'N.Y.'))
        
        elif state == 'TX':  # Texas
            # Replace Tex. with Texas
            if 'Tex.' in citation:
                variants.append(citation.replace('Tex.', 'Texas'))
            
            # Replace Texas with Tex.
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
        
        # Clean and normalize citation
        citation_text = citation_text.strip()
        
        # Strategy 1: Simple citation search (most likely to succeed)
        queries.append({
            'query': f'"{citation_text}"',
            'priority': 1,
            'type': 'simple_citation',
            'citation': citation_text
        })
        
        # Strategy 1b: Citation variants (for any state)
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
        
        # Strategy 2: Citation + "court decision" (very effective for Google/Bing)
        queries.append({
            'query': f'"{citation_text}" court decision',
            'priority': 2,
            'type': 'citation_court',
            'citation': citation_text
        })
        
        # Strategy 3: Citation + state name (if state is detected)
        state = self.detect_state_from_citation(citation_text)
        if state:
            state_name = self._get_state_name(state)
            queries.append({
                'query': f'"{citation_text}" {state_name}',
                'priority': 2,  # Increased priority for state-specific cases
                'type': f'citation_{state.lower()}',
                'citation': citation_text
            })
            
            # Strategy 3b: State-specific legal database searches
            state_legal_sites = self._get_state_legal_sites(state)
            for site in state_legal_sites:
                queries.append({
                    'query': f'{site} "{citation_text}"',
                    'priority': 2,  # High priority for state-specific searches
                    'type': f'{state.lower()}_site_specific',
                    'citation': citation_text,
                    'site': site
                })
            
            # Strategy 3c: State case name + citation (if case name available)
            if case_name:
                court_type = self._get_court_type(citation_text, state)
                queries.append({
                    'query': f'"{case_name}" "{citation_text}" {state_name} {court_type}',
                    'priority': 1,  # Highest priority for state cases with names
                    'type': f'{state.lower()}_case_citation',
                    'citation': citation_text,
                    'case_name': case_name
                })
        
        # Strategy 4: Case name + citation (if case name available)
        if case_name:
            queries.append({
                'query': f'"{case_name}" "{citation_text}"',
                'priority': 4,
                'type': 'case_and_citation',
                'citation': citation_text,
                'case_name': case_name
            })
            
            # Also try with "v." instead of "vs." for case names
            if ' vs. ' in case_name:
                alt_case_name = case_name.replace(' vs. ', ' v. ')
                queries.append({
                    'query': f'"{alt_case_name}" "{citation_text}"',
                    'priority': 4,
                    'type': 'case_and_citation_alt',
                    'citation': citation_text,
                    'case_name': alt_case_name
                })
        
        # Strategy 5: Legal database specific searches (HIGH priority - these are most effective!)
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
        
        # Strategy 6: Enhanced state-specific queries (if state is detected)
        state = self.detect_state_from_citation(citation_text)
        if state:
            # Add state-specific search strategies
            state_queries = self._generate_state_specific_queries(citation_text, case_name, state)
            queries.extend(state_queries)
        
        # Strategy 7: Parallel citation searches (if we know about parallel citations)
        if state:
            parallel_queries = self._generate_parallel_citation_queries(citation_text, case_name)
            queries.extend(parallel_queries)
        
        return queries
    
    def _generate_state_specific_queries(self, citation_text: str, case_name: Optional[str] = None, state_code: str = 'WA') -> List[Dict]:
        """Generate state-specific search queries for better case discovery."""
        state_queries = []
        state_name = self._get_state_name(state_code)
        
        # Court of Appeals specific searches
        if 'App.' in citation_text:
            state_queries.append({
                'query': f'"{citation_text}" "{state_name} Court of Appeals"',
                'priority': 1,  # Highest priority
                'type': f'{state_code.lower()}_appeals_specific',
                'citation': citation_text
            })
            
            # Try with case name if available
            if case_name:
                state_queries.append({
                    'query': f'"{case_name}" "{citation_text}" "{state_name} Court of Appeals"',
                    'priority': 1,  # Highest priority
                    'type': f'{state_code.lower()}_appeals_case',
                    'citation': citation_text,
                    'case_name': case_name
                })
        
        # Supreme Court specific searches
        if '2d' in citation_text and 'App.' not in citation_text:
            state_queries.append({
                'query': f'"{citation_text}" "{state_name} Supreme Court"',
                'priority': 1,  # Highest priority
                'type': f'{state_code.lower()}_supreme_specific',
                'citation': citation_text
            })
            
            # Try with case name if available
            if case_name:
                state_queries.append({
                    'query': f'"{case_name}" "{citation_text}" "{state_name} Supreme Court"',
                    'priority': 1,  # Highest priority
                    'type': f'{state_code.lower()}_supreme_case',
                    'citation': citation_text,
                    'case_name': case_name
                })
        
        # Regional reporter parallel citation searches
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
        
        # If this is a Washington Reporter citation, also search for Pacific Reporter
        if 'Wn.' in citation_text or 'Wash.' in citation_text:
            # Extract volume and page numbers
            volume_page_match = re.search(r'(\d+)\s+(?:Wn\.|Wash\.)\s*(?:App\.|2d|3d)\s+(\d+)', citation_text)
            if volume_page_match:
                volume, page = volume_page_match.groups()
                
                # Generate Pacific Reporter parallel citation queries
                if 'App.' in citation_text:
                    # Court of Appeals - try P.3d
                    parallel_queries.append({
                        'query': f'"{volume} P.3d {page}" Washington',
                        'priority': 1,  # High priority
                        'type': 'parallel_pacific_appeals',
                        'citation': citation_text
                    })
                elif '2d' in citation_text:
                    # Supreme Court - try P.2d
                    parallel_queries.append({
                        'query': f'"{volume} P.2d {page}" Washington',
                        'priority': 1,  # High priority
                        'type': 'parallel_pacific_supreme',
                        'citation': citation_text
                    })
        
        # If this is a Pacific Reporter citation, also search for Washington Reporter
        elif 'P.3d' in citation_text or 'P.2d' in citation_text:
            # Extract volume and page numbers
            volume_page_match = re.search(r'(\d+)\s+P\.(?:3d|2d)\s+(\d+)', citation_text)
            if volume_page_match:
                volume, page = volume_page_match.groups()
                
                # Generate Washington Reporter parallel citation queries
                if 'P.3d' in citation_text:
                    # Try Washington App. (Court of Appeals)
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
                    # Try Washington 2d (Supreme Court)
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
        
        # Washington-specific patterns
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
        
        # Pacific Reporter patterns
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
        
        # Extract year if present in citation
        year_match = re.search(r'\((\d{4})\)', citation_text)
        if year_match:
            citation_info['year'] = year_match.group(1)
        
        return citation_info
    
    async def verify_citation(self, citation_text: str, extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None, has_courtlistener_data: bool = False) -> Dict[str, Any]:
        """
        Verify a citation using enhanced fallback verification with strict timeout.
        
        Args:
            citation_text: The citation text to verify
            extracted_case_name: Optional extracted case name
            extracted_date: Optional extracted date
            has_courtlistener_data: If True, skip fallback verification (already verified)
            
        Returns:
            Dictionary with verification results
        """
        # Skip fallback verification if citation already has CourtListener data
        if has_courtlistener_data:
            logger.info(f"Skipping fallback verification for {citation_text} - already has CourtListener data")
            return self._create_fallback_result(citation_text, "already_verified", extracted_case_name)
        
        start_time = time.time()
        max_total_time = 15.0  # Increased to 15 seconds total per citation for better reliability
        
        try:
            # Parse citation to determine type and court
            citation_info = self._parse_citation(citation_text)
            
            # Generate optimized search queries
            queries = self.generate_enhanced_legal_queries(citation_text, extracted_case_name)
            
            # Debug logging for state citations
            state = self.detect_state_from_citation(citation_text)
            if state:
                logger.info(f"Generated {len(queries)} queries for {state} citation {citation_text}")
                for i, q in enumerate(queries[:6]):  # Show first 6 queries
                    logger.debug(f"  Query {i+1}: '{q['query']}' (type: {q['type']}, priority: {q['priority']})")
            
            # Define sources with their verification functions
            # Prioritize faster, more reliable sources first (reduced from 8 to 4 for better performance)
            sources = [
                ('google', self._verify_with_google_scholar),  # Fast, reliable, broad coverage
                ('bing', self._verify_with_bing),              # Fast, reliable, good legal indexing
                ('duckduckgo', self._verify_with_duckduckgo),  # Fast, no rate limiting
                ('justia', self._verify_with_justia),          # Legal-specific but reliable
            ]
            
            # Create tasks for all sources to run concurrently
            tasks = []
            for source_name, verify_func in sources:
                # For state citations, use more queries to ensure coverage
                state = self.detect_state_from_citation(citation_text)
                max_queries = 4 if state else 2
                
                for query_info in queries[:max_queries]:
                    query = query_info['query']
                    query_type = query_info.get('type', '')
                    
                    # Prioritize simple citation searches for faster sources
                    if source_name in ['google', 'bing', 'duckduckgo']:
                        # For fast sources, use all query types
                        task = self._create_verification_task(
                            source_name, verify_func, citation_text, citation_info, extracted_case_name, extracted_date, query
                        )
                        tasks.append(task)
                    else:
                        # For slower sources, use Washington-specific queries and simple citations
                        if (query_type in ['simple_citation', 'citation_court'] or 
                            'washington' in query_type.lower() or 
                            'appeals' in query_type.lower() or 
                            'supreme' in query_type.lower()):
                            task = self._create_verification_task(
                                source_name, verify_func, citation_text, citation_info, extracted_case_name, extracted_date, query
                            )
                            tasks.append(task)
            
            # Run all tasks concurrently with strict timeout
            results = []
            try:
                # Use asyncio.wait_for to enforce the 5-second total timeout
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=max_total_time
                )
            except asyncio.TimeoutError:
                logger.warning(f"Enhanced fallback verification timed out after {max_total_time}s for {citation_text}")
                # Return early with partial results if we have any
                return self._create_fallback_result(citation_text, "timeout", extracted_case_name)
            
            # Process results and find the best match
            best_result = None
            best_score = 0
            
            for result in results:
                if isinstance(result, Exception):
                    continue
                    
                if isinstance(result, dict) and result.get('verified'):
                    score = self._calculate_verification_score(result)
                    if score > best_score:
                        best_score = score
                        best_result = result
            
            if best_result:
                elapsed = time.time() - start_time
                logger.info(f"✅ Enhanced fallback verified: {citation_text} -> {best_result.get('canonical_name', 'N/A')} (via {best_result.get('source', 'unknown')}) in {elapsed:.1f}s")
                return best_result
            
            # No verification found
            elapsed = time.time() - start_time
            logger.debug(f"Enhanced fallback verification failed for {citation_text} after {elapsed:.1f}s")
            return self._create_fallback_result(citation_text, "not_found", extracted_case_name)
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Enhanced fallback verification error for {citation_text} after {elapsed:.1f}s: {str(e)}")
            return self._create_fallback_result(citation_text, "error", extracted_case_name)
    
    def _create_fallback_result(self, citation_text: str, status: str, case_name: Optional[str] = None) -> Dict[str, Any]:
        """Create a standardized fallback result."""
        return {
            'verified': False,
            'source': status,
            'canonical_name': None,
            'canonical_date': None,
            'url': None,
            'confidence': 0.0,
            'error': f"Verification {status}"
        }
    
    def _calculate_verification_score(self, result: Dict[str, Any]) -> float:
        """Calculate a score for verification result quality."""
        score = 0.0
        
        # Base score for verification
        if result.get('verified'):
            score += 1.0
        
        # Bonus for having canonical name
        if result.get('canonical_name'):
            score += 0.5
        
        # Bonus for having canonical date
        if result.get('canonical_date'):
            score += 0.3
        
        # Bonus for having URL
        if result.get('url'):
            score += 0.2
        
        # Bonus for high confidence
        if result.get('confidence'):
            score += min(result['confidence'], 1.0)
        
        return score
    
    def _create_verification_task(self, source_name: str, verify_func, citation_text: str, 
                                 citation_info: Dict, extracted_case_name: Optional[str], 
                                 extracted_date: Optional[str], query: str):
        """Create a verification task with proper error handling."""
        async def task_wrapper():
            try:
                logger.debug(f"Starting {source_name} verification for {citation_text}")
                result = await verify_func(citation_text, citation_info, extracted_case_name, extracted_date, query)
                if result and result.get('verified', False):
                    logger.debug(f"{source_name} verification successful for {citation_text}")
                return result
            except Exception as e:
                logger.debug(f"{source_name} verification failed for {citation_text}: {e}")
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
            # Create a new event loop for this thread
            import asyncio
            import threading
            
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an event loop, can't run sync version
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
                # No event loop, we can create one
                pass
            
            # Create a new event loop and run the async verification
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Run the async verification
                result = loop.run_until_complete(
                    self.verify_citation(citation_text, extracted_case_name)
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
            # Use provided search query or generate one
            if not search_query:
                search_query = citation_text
                if extracted_case_name:
                    search_query += f" {extracted_case_name}"
            
            # Justia search URL
            search_url = f"https://law.justia.com/search?query={quote(search_query)}"
            
            self._rate_limit('justia.com')
            response = self.session.get(search_url, timeout=5)  # Reduced from 15 to 5 seconds
            
            if response.status_code == 200:
                content = response.text
                
                # Look for case links that contain our citation
                case_link_pattern = r'<a[^>]*href="([^"]*cases[^"]+)"[^>]*>([^<]*)</a>'
                matches = re.findall(case_link_pattern, content, re.IGNORECASE)
                
                for link_url, link_text in matches:
                    # Check if this link contains our citation
                    if citation_text.replace(' ', '').lower() in link_text.replace(' ', '').lower():
                        # Found a matching case link
                        full_url = link_url if link_url.startswith('http') else f"https://law.justia.com{link_url}"
                        
                        # Extract case name from link text
                        case_name = self._extract_case_name_from_link(link_text)
                        if not case_name and extracted_case_name:
                            case_name = extracted_case_name
                        
                        # Extract year
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
            # Use provided search query or generate one
            if not search_query:
                search_query = citation_text
                if extracted_case_name:
                    search_query += f" {extracted_case_name}"
            
            # FindLaw search URL
            search_url = f"https://caselaw.findlaw.com/search?query={quote(search_query)}"
            
            self._rate_limit('findlaw.com')
            response = self.session.get(search_url, timeout=5)  # Reduced from 15 to 5 seconds
            
            if response.status_code == 200:
                content = response.text
                
                # Look for case links that contain our citation
                case_link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
                matches = re.findall(case_link_pattern, content, re.IGNORECASE)
                
                for link_url, link_text in matches:
                    # Check if this link contains our citation
                    if citation_text.replace(' ', '').lower() in link_text.replace(' ', '').lower():
                        # Found a matching case link
                        full_url = link_url if link_url.startswith('http') else f"https://caselaw.findlaw.com{link_url}"
                        
                        # Extract case name from link text
                        case_name = self._extract_case_name_from_link(link_text)
                        if not case_name and extracted_case_name:
                            case_name = extracted_case_name
                        
                        # Extract year
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
            # Use provided search query or generate one
            if not search_query:
                search_query = citation_text
                if extracted_case_name:
                    search_query += f" {extracted_case_name}"
            
            # Leagle search URL
            search_url = f"https://www.leagle.com/search?query={quote(search_query)}"
            
            self._rate_limit('leagle.com')
            response = self.session.get(search_url, timeout=5)  # Reduced from 15 to 5 seconds
            
            if response.status_code == 200:
                content = response.text
                
                # Look for case links that contain our citation
                case_link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
                matches = re.findall(case_link_pattern, content, re.IGNORECASE)
                
                for link_url, link_text in matches:
                    # Check if this link contains our citation
                    if citation_text.replace(' ', '').lower() in link_text.replace(' ', '').lower():
                        # Found a matching case link
                        full_url = link_url if link_url.startswith('http') else f"https://www.leagle.com{link_url}"
                        
                        # Extract case name from link text
                        case_name = self._extract_case_name_from_link(link_text)
                        if not case_name and extracted_case_name:
                            case_name = extracted_case_name
                        
                        # Extract year
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
            # Use provided search query or generate one
            if not search_query:
                search_query = citation_text
                if extracted_case_name:
                    search_query += f" {extracted_case_name}"
            
            # CaseMine search URL
            search_url = f"https://www.casemine.com/search?q={quote(search_query)}"
            
            self._rate_limit('casemine.com')
            response = self.session.get(search_url, timeout=5)  # Reduced from 15 to 5 seconds
            
            if response.status_code == 200:
                content = response.text
                
                # Look for case links that contain our citation
                case_link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
                matches = re.findall(case_link_pattern, content, re.IGNORECASE)
                
                for link_url, link_text in matches:
                    # Check if this link contains our citation
                    if citation_text.replace(' ', '').lower() in link_text.replace(' ', '').lower():
                        # Found a matching case link
                        full_url = link_url if link_url.startswith('http') else f"https://www.casemine.com{link_url}"
                        
                        # Extract case name from link text
                        case_name = self._extract_case_name_from_link(link_text)
                        if not case_name and extracted_case_name:
                            case_name = extracted_case_name
                        
                        # Extract year
                        year = extracted_date or (citation_info.get('year') if citation_info else None)
                        if not year:
                            year_match = re.search(r'(\d{4})', link_text)
                            if year_match:
                                year = year_match.group(1)
                        
                        if case_name:
                            return {
                                'verified': True,
                                'source': 'casemine',
                                'canonical_name': case_name,
                                'canonical_date': year,
                                'url': full_url,
                                'confidence': 0.8
                            }
            
            return None
            
        except Exception as e:
            logger.warning(f"CaseMine verification failed for {citation_text}: {e}")
            return None
    
    async def _verify_with_google_scholar(self, citation_text: str, citation_info: Dict,
                                        extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None,
                                        search_query: Optional[str] = None) -> Optional[Dict]:
        """Verify citation with Google Scholar."""
        try:
            # Use provided search query or generate one
            if not search_query:
                search_query = citation_text
                if extracted_case_name:
                    search_query += f" {extracted_case_name}"
            
            # Google Scholar search URL
            search_url = f"https://scholar.google.com/scholar?q={quote(search_query)}"
            
            self._rate_limit('scholar.google.com')
            response = self.session.get(search_url, timeout=5)  # Reduced from 15 to 5 seconds
            
            if response.status_code == 200:
                content = response.text
                
                # Look for case links and snippets that contain our citation
                case_link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
                matches = re.findall(case_link_pattern, content, re.IGNORECASE)
                
                # Also look for case name patterns in the content
                case_name_patterns = [
                    r'<h3[^>]*class="gs_rt"[^>]*>([^<]*)</h3>',  # Google Scholar result titles
                    r'<div[^>]*class="gs_a"[^>]*>([^<]*)</div>',  # Google Scholar author/date info
                    r'<span[^>]*class="gs_ct"[^>]*>([^<]*)</span>',  # Google Scholar citation info
                ]
                
                # Extract potential case names from various patterns
                potential_case_names = []
                for pattern in case_name_patterns:
                    name_matches = re.findall(pattern, content, re.IGNORECASE)
                    potential_case_names.extend(name_matches)
                
                # Look for case links that contain our citation
                for link_url, link_text in matches:
                    # Check if this link contains our citation
                    if citation_text.replace(' ', '').lower() in link_text.replace(' ', '').lower():
                        # Found a matching case link
                        # Try to extract the underlying URL from Google redirect
                        underlying_url = URLDecoder.decode_google_redirect_url(link_url)
                        if underlying_url:
                            full_url = underlying_url
                            logger.info(f"Extracted underlying URL from Google Scholar: {underlying_url}")
                        else:
                            full_url = link_url if link_url.startswith('http') else f"https://scholar.google.com{link_url}"
                        
                        # Extract case name from link text
                        case_name = self._extract_case_name_from_link(link_text)
                        if not case_name and extracted_case_name:
                            case_name = extracted_case_name
                        
                        # Extract year
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
                
                # If no direct citation match found, look for case names in the content
                # that might be related to our citation
                if extracted_case_name and potential_case_names:
                    for potential_name in potential_case_names:
                        # Check if this potential case name is similar to our extracted name
                        if self._are_case_names_similar(potential_name, extracted_case_name):
                            # Found a similar case name, check if we can extract more info
                            year = extracted_date or (citation_info.get('year') if citation_info else None)
                            
                            # Look for a URL that might contain this case
                            for link_url, link_text in matches:
                                if potential_name.lower() in link_url.lower():
                                    # Try to extract the underlying URL from Google redirect
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
    
    async def _verify_with_bing(self, citation_text: str, citation_info: Dict,
                               extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None,
                               search_query: Optional[str] = None) -> Optional[Dict]:
        """Verify citation with Bing search."""
        try:
            # Use provided search query or generate one
            if not search_query:
                search_query = citation_text
                if extracted_case_name:
                    search_query += f" {extracted_case_name}"
            
            # Bing search URL
            search_url = f"https://www.bing.com/search?q={quote(search_query)}"
            
            self._rate_limit('bing.com')
            response = self.session.get(search_url, timeout=5)  # Reduced from 15 to 5 seconds
            
            if response.status_code == 200:
                content = response.text
                
                # Look for case links and snippets that contain our citation
                case_link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
                matches = re.findall(case_link_pattern, content, re.IGNORECASE)
                
                # Also look for case name patterns in Bing search results
                case_name_patterns = [
                    r'<h2[^>]*>([^<]*)</h2>',  # Bing result titles
                    r'<cite[^>]*>([^<]*)</cite>',  # Bing result URLs
                    r'<p[^>]*>([^<]*)</p>',  # Bing result snippets
                ]
                
                # Extract potential case names from various patterns
                potential_case_names = []
                for pattern in case_name_patterns:
                    name_matches = re.findall(pattern, content, re.IGNORECASE)
                    potential_case_names.extend(name_matches)
                
                # Look for case links that contain our citation
                for link_url, link_text in matches:
                    # Check if this link contains our citation
                    if citation_text.replace(' ', '').lower() in link_text.replace(' ', '').lower():
                        # Found a matching case link
                        # Try to extract the underlying URL from Bing redirect
                        underlying_url = URLDecoder.decode_bing_url(link_url)
                        if underlying_url:
                            full_url = underlying_url
                            logger.info(f"Extracted underlying URL from Bing: {underlying_url}")
                        else:
                            full_url = link_url if link_url.startswith('http') else f"https://www.bing.com{link_url}"
                        
                        # Extract case name from link text
                        case_name = self._extract_case_name_from_link(link_text)
                        if not case_name and extracted_case_name:
                            case_name = extracted_case_name
                        
                        # Extract year
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
                
                # If no direct citation match found, look for case names in the content
                # that might be related to our citation
                if extracted_case_name and potential_case_names:
                    for potential_name in potential_case_names:
                        # Check if this potential case name is similar to our extracted name
                        if self._are_case_names_similar(potential_name, extracted_case_name):
                            # Found a similar case name, check if we can extract more info
                            year = extracted_date or (citation_info.get('year') if citation_info else None)
                            
                            # Look for a URL that might contain this case
                            for link_url, link_text in matches:
                                if potential_name.lower() in link_text.lower():
                                    # Try to extract the underlying URL from Bing redirect
                                    underlying_url = URLDecoder.decode_bing_url(link_url)
                                    if underlying_url:
                                        full_url = underlying_url
                                        logger.info(f"Extracted underlying URL from Bing (fallback): {underlying_url}")
                                    else:
                                        full_url = link_url if link_url.startswith('http') else f"https://www.bing.com{link_url}"
                                    return {
                                        'verified': True,
                                        'source': 'bing',
                                        'canonical_name': potential_name,
                                        'canonical_date': year,
                                        'url': full_url,
                                        'confidence': 0.7
                                    }
            
            return None
            
        except Exception as e:
            logger.warning(f"Bing verification failed for {citation_text}: {e}")
            return None
    
    async def _verify_with_duckduckgo(self, citation_text: str, citation_info: Dict,
                                     extracted_case_name: Optional[str] = None, extracted_date: Optional[str] = None,
                                     search_query: Optional[str] = None) -> Optional[Dict]:
        """Verify citation with DuckDuckGo search."""
        try:
            # Use provided search query or generate one
            if not search_query:
                search_query = citation_text
                if extracted_case_name:
                    search_query += f" {extracted_case_name}"
            
            # DuckDuckGo search URL
            search_url = f"https://duckduckgo.com/html/?q={quote(search_query)}"
            
            self._rate_limit('duckduckgo.com')
            response = self.session.get(search_url, timeout=5)  # Reduced from 15 to 5 seconds
            
            if response.status_code == 200:
                content = response.text
                
                # Look for case links and snippets that contain our citation
                case_link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
                matches = re.findall(case_link_pattern, content, re.IGNORECASE)
                
                # Also look for case name patterns in DuckDuckGo search results
                case_name_patterns = [
                    r'<h2[^>]*>([^<]*)</h2>',  # DuckDuckGo result titles
                    r'<a[^>]*class="result__title"[^>]*>([^<]*)</a>',  # DuckDuckGo result titles
                    r'<a[^>]*class="result__snippet"[^>]*>([^<]*)</a>',  # DuckDuckGo result snippets
                ]
                
                # Extract potential case names from various patterns
                potential_case_names = []
                for pattern in case_name_patterns:
                    name_matches = re.findall(pattern, content, re.IGNORECASE)
                    potential_case_names.extend(name_matches)
                
                # Look for case links that contain our citation
                for link_url, link_text in matches:
                    # Check if this link contains our citation
                    if citation_text.replace(' ', '').lower() in link_text.replace(' ', '').lower():
                        # Found a matching case link
                        # Try to extract the underlying URL from DuckDuckGo redirect
                        underlying_url = URLDecoder.decode_duckduckgo_url(link_url)
                        if underlying_url:
                            full_url = underlying_url
                            logger.info(f"Extracted underlying URL from DuckDuckGo: {underlying_url}")
                        else:
                            full_url = link_url if link_url.startswith('http') else f"https://duckduckgo.com{link_url}"
                        
                        # Extract case name from link text
                        case_name = self._extract_case_name_from_link(link_text)
                        if not case_name and extracted_case_name:
                            case_name = extracted_case_name
                        
                        # Extract year
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
                
                # If no direct citation match found, look for case names in the content
                # that might be related to our citation
                if extracted_case_name and potential_case_names:
                    for potential_name in potential_case_names:
                        # Check if this potential case name is similar to our extracted name
                        if self._are_case_names_similar(potential_name, extracted_case_name):
                            # Found a similar case name, check if we can extract more info
                            year = extracted_date or (citation_info.get('year') if citation_info else None)
                            
                            # Look for a URL that might contain this case
                            for link_url, link_text in matches:
                                if potential_name.lower() in link_text.lower():
                                    # Try to extract the underlying URL from DuckDuckGo redirect
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
            # Use provided search query or generate one
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
                    response = self.session.get(search_url, timeout=5)  # Reduced from 15 to 5 seconds
                    
                    if response.status_code == 200:
                        content = response.text
                        
                        # Look for case links that contain our citation
                        case_link_pattern = r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
                        matches = re.findall(case_link_pattern, content, re.IGNORECASE)
                        
                        for link_url, link_text in matches:
                            # Check if this link contains our citation
                            if citation_text.replace(' ', '').lower() in link_text.replace(' ', '').lower():
                                # Found a matching case link
                                full_url = link_url if link_url.startswith('http') else f"https://vlex.com{link_url}"
                                
                                # Extract case name from link text
                                case_name = self._extract_case_name_from_link(link_text)
                                if not case_name and extracted_case_name:
                                    case_name = extracted_case_name
                                
                                # Extract year
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
                        
                        # If we get here, no matches found in this URL
                        continue
                        
                except Exception as e:
                    logger.debug(f"vLex search URL {search_url} failed: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.warning(f"vLex verification failed for {citation_text}: {e}")
            return None
    
    def _extract_case_name_from_link(self, link_text: str) -> Optional[str]:
        """Extract case name from link text."""
        # Remove HTML tags and clean up
        clean_text = re.sub(r'<[^>]+>', '', link_text).strip()
        
        # Look for case name patterns
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
    
    def _are_case_names_similar(self, name1: str, name2: str) -> bool:
        """Check if two case names are similar."""
        if not name1 or not name2:
            return False
        
        # Clean and normalize names
        clean1 = re.sub(r'[^\w\s]', '', name1.lower()).strip()
        clean2 = re.sub(r'[^\w\s]', '', name2.lower()).strip()
        
        # Check exact match
        if clean1 == clean2:
            return True
        
        # Check if one name is contained in the other
        if clean1 in clean2 or clean2 in clean1:
            return True
        
        # Check word overlap (at least 2 words in common)
        words1 = set(clean1.split())
        words2 = set(clean2.split())
        common_words = words1.intersection(words2)
        
        # Filter out common words that don't indicate similarity
        common_words = {w for w in common_words if len(w) > 2 and w not in {'the', 'and', 'for', 'petition', 'in', 're'}}
        
        return len(common_words) >= 2

# Convenience function for easy integration
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

# Convenience function specifically for vlex verification
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
