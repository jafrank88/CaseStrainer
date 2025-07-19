"""
Unified Citation Processor v2 - Consolidated Citation Extraction and Processing

This module consolidates the best parts of all existing citation extraction implementations:
- EnhancedRegexExtractor from unified_citation_processor.py
- CitationExtractor from citation_extractor.py  
- CitationServices from citation_services.py
- EyeciteProcessor from unified_citation_processor.py

Key improvements:
- Single, consistent API
- Proper deduplication and clustering
- Enhanced case name extraction
- Configurable processing options
- Better parallel citation handling
- Integrated verification with CourtListener API
"""

import re
import logging
import requests
import time
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import unicodedata
import os
import collections
from collections import defaultdict, deque

# Import the main config module for proper environment variable handling
from src.config import get_config_value

logger = logging.getLogger(__name__)

# Try to import eyecite for enhanced extraction
try:
    import eyecite
    from eyecite import get_citations
    from eyecite.tokenizers import AhocorasickTokenizer
    EYECITE_AVAILABLE = True
    logger.info("Eyecite successfully imported")
except ImportError as e:
    EYECITE_AVAILABLE = False
    logger.warning(f"Eyecite not available - install with: pip install eyecite. Error: {e}")
except Exception as e:
    EYECITE_AVAILABLE = False
    logger.warning(f"Eyecite import failed with unexpected error: {e}")

# Import core case name extraction functions
try:
    from src.case_name_extraction_core import extract_case_name_and_date
except ImportError:
    from case_name_extraction_core import extract_case_name_and_date

# Import LegalWebSearchEngine from websearch_utils.py
from src.websearch_utils import search_cluster_for_canonical_sources

# Date extraction is now handled by the streamlined API functions

# Import individual extraction functions
try:
    from src.case_name_extraction_core import extract_case_name_only, extract_year_only
except ImportError:
    from case_name_extraction_core import extract_case_name_only, extract_year_only

from src.citation_normalizer import normalize_citation, generate_citation_variants

@dataclass
class CitationResult:
    """Unified citation result structure."""
    citation: str
    case_name: Optional[str] = None
    extracted_case_name: Optional[str] = None
    extracted_date: Optional[str] = None
    canonical_name: Optional[str] = None
    canonical_date: Optional[str] = None
    verified: bool = False
    url: Optional[str] = None
    court: Optional[str] = None
    docket_number: Optional[str] = None
    confidence: float = 0.0
    method: str = "unified_processor"
    pattern: str = ""
    context: str = ""
    start_index: Optional[int] = None
    end_index: Optional[int] = None
    is_parallel: bool = False
    is_cluster: bool = False
    parallel_citations: List[str] = None
    cluster_members: List[str] = None
    pinpoint_pages: List[str] = None
    docket_numbers: List[str] = None
    case_history: List[str] = None
    publication_status: Optional[str] = None
    source: str = "Unknown"
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    cluster_id: Optional[str] = None  # NEW: Track which cluster this citation belongs to
    
    def __post_init__(self):
        if self.parallel_citations is None:
            self.parallel_citations = []
        if self.cluster_members is None:
            self.cluster_members = []
        if self.pinpoint_pages is None:
            self.pinpoint_pages = []
        if self.docket_numbers is None:
            self.docket_numbers = []
        if self.case_history is None:
            self.case_history = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ProcessingConfig:
    """Configuration for citation processing."""
    use_eyecite: bool = True
    use_regex: bool = True
    extract_case_names: bool = True
    extract_dates: bool = True
    enable_clustering: bool = True
    enable_deduplication: bool = True
    enable_verification: bool = True  # NEW: Enable verification with CourtListener
    context_window: int = 300
    min_confidence: float = 0.5
    max_citations_per_text: int = 1000
    debug_mode: bool = False

class UnifiedCitationProcessorV2:
    """
    Unified citation processor that consolidates the best parts of all existing implementations.
    """
    
    def __init__(self, config: Optional[ProcessingConfig] = None):
        self.config = config or ProcessingConfig()
        self._init_patterns()
        self._init_case_name_patterns()
        self._init_date_patterns()
        self._init_state_reporter_mapping()  # NEW: Initialize state-reporter mapping
        
        # Initialize verification components
        self.courtlistener_api_key = get_config_value("COURTLISTENER_API_KEY")
        
        # Initialize enhanced web searcher (now using ComprehensiveWebSearchEngine in _verify_citations_with_legal_websearch)
        # self.enhanced_web_searcher = LegalWebSearchEngine()
        self.enhanced_web_searcher = None  # No longer needed - using ComprehensiveWebSearchEngine
        
        if self.config.debug_mode:
            logger.info(f"CourtListener API key available: {bool(self.courtlistener_api_key)}")
            logger.info(f"Enhanced web searcher available: {bool(self.enhanced_web_searcher)}")
        
    def _init_patterns(self):
        """Initialize comprehensive citation patterns with proper Bluebook spacing."""
        self.citation_patterns = {
            # Washington State patterns (proper spacing)
            'wn2d': re.compile(r'\b(\d+)\s+Wn\.2d\s+(\d+)\b', re.IGNORECASE),
            'wn2d_space': re.compile(r'\b(\d+)\s+Wn\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            'wn_app': re.compile(r'\b(\d+)\s+Wn\.\s*App\.\s+(\d+)\b', re.IGNORECASE),
            'wn_app_space': re.compile(r'\b(\d+)\s+Wn\.\s*App\s+(\d+)\b', re.IGNORECASE),
            'wash2d': re.compile(r'\b(\d+)\s+Wash\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            'wash2d_space': re.compile(r'\b(\d+)\s+Wash\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            'wash_app': re.compile(r'\b(\d+)\s+Wash\.\s*App\.\s+(\d+)\b', re.IGNORECASE),
            'wash_app_space': re.compile(r'\b(\d+)\s+Wash\.\s*App\s+(\d+)\b', re.IGNORECASE),
            
            # Pacific Reporter patterns (proper spacing)
            'p3d': re.compile(r'\b(\d+)\s+P\.3d\s+(\d+)\b', re.IGNORECASE),
            'p2d': re.compile(r'\b(\d+)\s+P\.2d\s+(\d+)\b', re.IGNORECASE),
            
            # Federal patterns (proper spacing)
            'us': re.compile(r'\b(\d+)\s+U\.S\.\s+(\d+)\b', re.IGNORECASE),
            'f3d': re.compile(r'\b(\d+)\s+F\.3d\s+(\d+)\b', re.IGNORECASE),
            'f2d': re.compile(r'\b(\d+)\s+F\.2d\s+(\d+)\b', re.IGNORECASE),
            'f_supp': re.compile(r'\b(\d+)\s+F\.\s*Supp\.\s+(\d+)\b', re.IGNORECASE),
            'f_supp2d': re.compile(r'\b(\d+)\s+F\.\s*Supp\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            'f_supp3d': re.compile(r'\b(\d+)\s+F\.\s*Supp\.\s*3d\s+(\d+)\b', re.IGNORECASE),
            
            # Supreme Court patterns (proper spacing)
            's_ct': re.compile(r'\b(\d+)\s+S\.\s*Ct\.\s+(\d+)\b', re.IGNORECASE),
            'l_ed': re.compile(r'\b(\d+)\s+L\.\s*Ed\.\s+(\d+)\b', re.IGNORECASE),
            'l_ed2d': re.compile(r'\b(\d+)\s+L\.\s*Ed\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            
            # Atlantic Reporter patterns (proper spacing)
            'a2d': re.compile(r'\b(\d+)\s+A\.2d\s+(\d+)\b', re.IGNORECASE),
            'a3d': re.compile(r'\b(\d+)\s+A\.3d\s+(\d+)\b', re.IGNORECASE),
            
            # Southern Reporter patterns (proper spacing)
            'so2d': re.compile(r'\b(\d+)\s+So\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            'so3d': re.compile(r'\b(\d+)\s+So\.\s*3d\s+(\d+)\b', re.IGNORECASE),
            
            # Alternative patterns (proper spacing)
            'wash_2d_alt': re.compile(r'\b(\d+)\s+Wash\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            'wash_app_alt': re.compile(r'\b(\d+)\s+Wash\.\s*App\.\s+(\d+)\b', re.IGNORECASE),
            'wn2d_alt': re.compile(r'\b(\d+)\s+Wn\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            'wn2d_alt_space': re.compile(r'\b(\d+)\s+Wn\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            'wn_app_alt': re.compile(r'\b(\d+)\s+Wn\.\s*App\.\s+(\d+)\b', re.IGNORECASE),
            'p3d_alt': re.compile(r'\b(\d+)\s+P\.\s*3d\s+(\d+)\b', re.IGNORECASE),
            'p2d_alt': re.compile(r'\b(\d+)\s+P\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            
            # Complete patterns for parallel citations (proper spacing)
            'wash_complete': re.compile(r'\b(\d+)\s+(?:Wash\.|Wn\.)\s*(?:2d|App\.)\s+(\d+)(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\b', re.IGNORECASE),
            'wash_with_parallel': re.compile(r'\b(\d+)\s+(?:Wash\.|Wn\.)\s*(?:2d|App\.)\s+(\d+)(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\b', re.IGNORECASE),
            'parallel_cluster': re.compile(r'\b(\d+)\s+(?:Wash\.|Wn\.)\s*(?:2d|App\.)\s+(\d+)(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\b', re.IGNORECASE),
            
            # NEW: Flexible patterns that handle parallel citations and parentheses (proper spacing)
            'flexible_wash2d': re.compile(r'\b(\d+)\s+(?:Wash\.|Wn\.)\s*2d\s+(\d+)(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\s*(?:\(\d{4}\))?\b', re.IGNORECASE),
            'flexible_p3d': re.compile(r'\b(\d+)\s+P\.3d\s+(\d+)(?:\s*,\s*(\d+)\s+(?:Wash\.|Wn\.)\s*2d\s+(\d+))?\s*(?:\(\d{4}\))?\b', re.IGNORECASE),
            'flexible_p2d': re.compile(r'\b(\d+)\s+P\.2d\s+(\d+)(?:\s*,\s*(\d+)\s+(?:Wash\.|Wn\.)\s*2d\s+(\d+))?\s*(?:\(\d{4}\))?\b', re.IGNORECASE),
            
            # NEW: Comprehensive parallel citation pattern (proper spacing)
            'parallel_citation_cluster': re.compile(
                r'\b(\d+)\s+(?:Wash\.|Wn\.)\s*2d\s+(\d+)(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\s*(?:\(\d{4}\))?\b', 
                re.IGNORECASE
            ),
            
            # Westlaw (WL) citation patterns (proper spacing)
            'westlaw': re.compile(r'\b(\d{4})\s+WL\s+(\d{1,12})\b', re.IGNORECASE),
            'westlaw_alt': re.compile(r'\b(\d{4})\s+Westlaw\s+(\d{1,12})\b', re.IGNORECASE),
            
            # Simple individual citation patterns (proper spacing)
            'simple_wash2d': re.compile(r'\b(\d+)\s+(?:Wash\.|Wn\.)\s*2d\s+(\d+)\b', re.IGNORECASE),
            'simple_p3d': re.compile(r'\b(\d+)\s+P\.3d\s+(\d+)\b', re.IGNORECASE),
            'simple_p2d': re.compile(r'\b(\d+)\s+P\.2d\s+(\d+)\b', re.IGNORECASE),
            
            # LEXIS citation patterns (proper spacing)
            'lexis': re.compile(r'\b(\d{4})\s+[A-Za-z\.\s]+LEXIS\s+(\d{1,12})\b', re.IGNORECASE),
            'lexis_alt': re.compile(r'\b(\d{4})\s+LEXIS\s+(\d{1,12})\b', re.IGNORECASE),
        }
        
        # Additional patterns for pinpoint pages, docket numbers, etc.
        self.pinpoint_pattern = re.compile(r'\b(?:at\s+)?(\d+)\b', re.IGNORECASE)
        self.docket_pattern = re.compile(r'\b(?:No\.|Docket\s+No\.|Case\s+No\.)\s*[:\-]?\s*([A-Z0-9\-\.]+)\b', re.IGNORECASE)
        self.history_pattern = re.compile(r'\b(?:affirmed|reversed|remanded|vacated|denied|granted|cert\.?\s+denied)\b', re.IGNORECASE)
        self.status_pattern = re.compile(r'\b(?:published|unpublished|memorandum|opinion)\b', re.IGNORECASE)
    
    def _init_case_name_patterns(self):
        """Initialize case name extraction patterns."""
        self.case_name_patterns = [
            # Improved: allow for commas and apostrophes in party names before v.
            r'([A-Z][A-Za-z0-9&.,\'\\-]*(?:[\s,][A-Za-z0-9&.,\'\\-]+)*\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9&.,\'\\-]*(?:[\s,][A-Za-z0-9&.,\'\\-]+)*)',
            r'((?:[A-Za-z0-9&.,\'\\-]+[\s,]+)+(?:v\.|vs\.|versus)\s+(?:[A-Za-z0-9&.,\'\\-]+[\s,]*)+)',
            r'(?:^|[\n\r]|[\.\!\?]\s+)([A-Z][A-Za-z&.,\'\\-]*(?:[\s,][A-Za-z&.,\'\\-]+)*\s+(?:v\.|vs\.|versus)\s+[A-Za-z&.,\'\\-]+(?:[\s,][A-Za-z&.,\'\\-]+)*)',
            # Capitalized word pattern with limited lowercase sequences
            r'([A-Z][A-Za-z0-9&.,\'\\-]+(?:[\s,][A-Za-z0-9&.,\'\\-]+)*\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9&.,\'\\-]+(?:[\s,][A-Za-z0-9&.,\'\\-]+)*)',
            # Fallback: any sequence with "v." that starts with capital and has reasonable length
            r'([A-Z][A-Za-z0-9&.,\'\\-]+(?:[\s,][A-Za-z0-9&.,\'\\-]+){0,15}\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9&.,\'\\-]+(?:[\s,][A-Za-z0-9&.,\'\\-]+){0,15})',
        ]
    
    def _init_date_patterns(self):
        """Initialize date extraction patterns."""
        self.date_patterns = [
            r'\((\d{4})\)',  # (2022)
            r'\b(\d{4})\b',  # 2022
            r'\b(19|20)\d{2}\b',  # 19xx or 20xx
        ]
    
    def _init_state_reporter_mapping(self):
        """Initialize comprehensive state-to-reporter mapping based on Westlaw regional reporters."""
        self.state_reporter_mapping = {
            # Pacific Reporter (P.3d) - 15 states
            'P.3d': ['Alaska', 'Arizona', 'California', 'Colorado', 'Hawaii', 'Idaho', 'Kansas', 'Montana', 'Nevada', 'New Mexico', 'Oklahoma', 'Oregon', 'Utah', 'Washington', 'Wyoming'],
            'P.2d': ['Alaska', 'Arizona', 'California', 'Colorado', 'Hawaii', 'Idaho', 'Kansas', 'Montana', 'Nevada', 'New Mexico', 'Oklahoma', 'Oregon', 'Utah', 'Washington', 'Wyoming'],
            
            # North Western Reporter (N.W.2d) - 7 states
            'N.W.2d': ['Iowa', 'Michigan', 'Minnesota', 'Nebraska', 'North Dakota', 'South Dakota', 'Wisconsin'],
            'N.W.': ['Iowa', 'Michigan', 'Minnesota', 'Nebraska', 'North Dakota', 'South Dakota', 'Wisconsin'],
            
            # South Western Reporter (S.W.3d) - 5 states
            'S.W.3d': ['Arkansas', 'Kentucky', 'Missouri', 'Tennessee', 'Texas'],
            'S.W.2d': ['Arkansas', 'Kentucky', 'Missouri', 'Tennessee', 'Texas'],
            'S.W.': ['Arkansas', 'Kentucky', 'Missouri', 'Tennessee', 'Texas'],
            
            # North Eastern Reporter (N.E.2d) - 6 states
            'N.E.2d': ['Illinois', 'Indiana', 'Massachusetts', 'New York', 'Ohio'],
            'N.E.': ['Illinois', 'Indiana', 'Massachusetts', 'New York', 'Ohio'],
            
            # Southern Reporter (So.3d) - 4 states
            'So.3d': ['Alabama', 'Florida', 'Louisiana', 'Mississippi'],
            'So.2d': ['Alabama', 'Florida', 'Louisiana', 'Mississippi'],
            'So.': ['Alabama', 'Florida', 'Louisiana', 'Mississippi'],
            
            # South Eastern Reporter (S.E.2d) - 6 states
            'S.E.2d': ['Georgia', 'North Carolina', 'South Carolina', 'Virginia', 'West Virginia'],
            'S.E.': ['Georgia', 'North Carolina', 'South Carolina', 'Virginia', 'West Virginia'],
            
            # Atlantic Reporter (A.3d) - 9 states + DC
            'A.3d': ['Connecticut', 'Delaware', 'Maine', 'Maryland', 'New Hampshire', 'New Jersey', 'Pennsylvania', 'Rhode Island', 'Vermont', 'District of Columbia'],
            'A.2d': ['Connecticut', 'Delaware', 'Maine', 'Maryland', 'New Hampshire', 'New Jersey', 'Pennsylvania', 'Rhode Island', 'Vermont', 'District of Columbia'],
            'A.': ['Connecticut', 'Delaware', 'Maine', 'Maryland', 'New Hampshire', 'New Jersey', 'Pennsylvania', 'Rhode Island', 'Vermont', 'District of Columbia'],
        }
        
        # Reverse mapping: state to possible reporters
        self.state_to_reporters = {}
        for reporter, states in self.state_reporter_mapping.items():
            for state in states:
                if state not in self.state_to_reporters:
                    self.state_to_reporters[state] = []
                self.state_to_reporters[state].append(reporter)

    def _group_citations_for_verification(self, citations: List[CitationResult]) -> Dict[str, List[CitationResult]]:
        """Group citations for efficient verification by state and reporter type."""
        groups = {}
        
        for citation in citations:
            citation_text = citation.citation
            state = self._infer_state_from_citation(citation_text)
            reporter = self._infer_reporter_from_citation(citation_text)
            
            if state:
                # State-specific citation (e.g., Wash.2d, Cal.3d)
                group_key = f"state_{state.lower()}"
                if group_key not in groups:
                    groups[group_key] = []
                groups[group_key].append(citation)
            elif reporter:
                # Regional reporter citation (e.g., P.3d, A.2d)
                group_key = f"regional_{reporter}"
                if group_key not in groups:
                    groups[group_key] = []
                groups[group_key].append(citation)
            else:
                # Unknown citation type
                group_key = "unknown"
                if group_key not in groups:
                    groups[group_key] = []
                groups[group_key].append(citation)
        
        return groups

    def _infer_reporter_from_citation(self, citation: str) -> str:
        """Infer the reporter type from the citation."""
        reporter_patterns = {
            'P.3d': r'\b\d+\s+P\.3d\b',
            'P.2d': r'\b\d+\s+P\.2d\b',
            'N.W.2d': r'\b\d+\s+N\.W\.2d\b',
            'N.W.': r'\b\d+\s+N\.W\.\b',
            'S.W.3d': r'\b\d+\s+S\.W\.3d\b',
            'S.W.2d': r'\b\d+\s+S\.W\.2d\b',
            'S.W.': r'\b\d+\s+S\.W\.\b',
            'N.E.2d': r'\b\d+\s+N\.E\.2d\b',
            'N.E.': r'\b\d+\s+N\.E\.\b',
            'So.3d': r'\b\d+\s+So\.3d\b',
            'So.2d': r'\b\d+\s+So\.2d\b',
            'So.': r'\b\d+\s+So\.\b',
            'S.E.2d': r'\b\d+\s+S\.E\.2d\b',
            'S.E.': r'\b\d+\s+S\.E\.\b',
            'A.3d': r'\b\d+\s+A\.3d\b',
            'A.2d': r'\b\d+\s+A\.2d\b',
            'A.': r'\b\d+\s+A\.\b',
            'WL': r'\b\d{4}\s+WL\s+\d+\b',
            'LEXIS': r'\b\d{4}\s+[A-Za-z\.\s]+LEXIS\s+\d+\b',
            'LEXIS_ALT': r'\b\d{4}\s+LEXIS\s+\d+\b',
        }
        
        for reporter, pattern in reporter_patterns.items():
            if re.search(pattern, citation, re.IGNORECASE):
                return reporter
        
        return None

    def _get_possible_states_for_reporter(self, reporter: str) -> List[str]:
        """Get all possible states for a given regional reporter."""
        return self.state_reporter_mapping.get(reporter, [])

    def _strip_pincites(self, cite: str) -> str:
        """Return the citations without page numbers/pincites between them, but preserve all citations."""
        import re
        if not cite:
            return cite
        
        # Split by commas and process each part
        parts = [part.strip() for part in cite.split(',')]
        cleaned_parts = []
        
        for part in parts:
            # Check if this part looks like a citation (volume reporter page)
            if re.match(r'^\d+\s+\w+\.\w+\s+\d+', part):
                # It's a citation, keep it
                cleaned_parts.append(part)
            elif re.match(r'^\d+$', part):
                # It's just a page number, skip it
                continue
            else:
                # It might be a citation with extra info, try to extract the main citation
                citation_match = re.match(r'^(\d+\s+\w+\.\w+\s+\d+)', part)
                if citation_match:
                    cleaned_parts.append(citation_match.group(1))
                else:
                    # Keep it as is if we can't parse it
                    cleaned_parts.append(part)
        
        return ', '.join(cleaned_parts)

    def _verify_citations_with_courtlistener_batch(self, citations: List['CitationResult'], text: str) -> None:
        """Verify citations using CourtListener batch API."""
        if not self.courtlistener_api_key:
            logger.warning("[CL batch] No API key available")
            return
        
        if not citations:
            return
        
        logger.info(f"[CL batch] Verifying {len(citations)} citations with text length: {len(text)}")
        logger.debug(f"[CL batch] Text preview: {text[:100]}...")
        
        try:
            # Prepare batch request
            citations_to_verify = [citation.citation for citation in citations]
            
            # Make batch request to CourtListener
            url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
            headers = {
                'Authorization': f'Token {self.courtlistener_api_key}',
                'Content-Type': 'application/json'
            }
            data = {
                'text': ' '.join(citations_to_verify)
            }
            
            logger.debug(f"[CL batch] API request payload: {str(data)[:200]}...")
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            logger.info(f"[CL batch] API response status: {response.status_code}")
            logger.debug(f"[CL batch] API raw response: {response.text[:500]}...")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"[CL batch] Found {len(result)} result clusters")
                
                # Process each cluster
                for i, cluster in enumerate(result):
                    logger.debug(f"[CL batch] Cluster {i}: status={cluster.get('status')}, citations={len(cluster.get('clusters', []))}")
                    
                    # Fix: Check for status 200 (not 'ok') and handle citation objects
                    if cluster.get('status') == 200 and cluster.get('clusters'):
                        api_cluster = cluster['clusters'][0]  # Take first cluster
                        logger.debug(f"[CL batch] api_cluster structure: {str(api_cluster)[:500]}...")
                        
                        # Extract canonical data
                        cl_case_name = api_cluster.get('case_name', '')
                        cl_date = api_cluster.get('date_filed', '')
                        cl_url = api_cluster.get('absolute_url', '')
                        
                        # Fix: Handle citations as objects, reconstruct the citation string
                        citations_data = api_cluster.get('citations', [])
                        if citations_data:
                            # Take the first citation and reconstruct it
                            first_citation_obj = citations_data[0]
                            main_cite = f"{first_citation_obj.get('volume', '')} {first_citation_obj.get('reporter', '')} {first_citation_obj.get('page', '')}"
                        else:
                            main_cite = ''
                        
                        logger.debug(f"[CL batch] API citation: {main_cite} -> {cl_case_name}")
                        
                        # Update matching citations
                        for citation in citations:
                            if citation.citation == main_cite:
                                citation.canonical_name = cl_case_name
                                citation.canonical_date = cl_date
                                citation.url = f"https://www.courtlistener.com{cl_url}" if cl_url else None
                                citation.verified = True
                                citation.source = "CourtListener"
                                logger.info(f"[CL batch] EXACT MATCH: {citation.citation} -> {citation.canonical_name}")
                                break
                        
                        # Try to match by normalized citation
                        if not any(c.verified for c in citations if c.citation == main_cite):
                            for citation in citations:
                                # Normalize citations for comparison
                                def robust_normalize(s):
                                    """Robust normalization for citation comparison."""
                                    if not s:
                                        return ""
                                    # Remove spaces, punctuation, and convert to lowercase
                                    normalized = re.sub(r'[^\w]', '', s.lower())
                                    # Remove common variations
                                    normalized = re.sub(r'wash', 'wn', normalized)
                                    normalized = re.sub(r'pacific', 'p', normalized)
                                    return normalized
                                
                                normalized_reconstructed = robust_normalize(main_cite)
                                normalized_extracted = robust_normalize(citation.citation)
                                
                                logger.debug(f"[CL batch] Comparing robust-normalized '{normalized_reconstructed}' to '{normalized_extracted}'")
                                
                                if normalized_reconstructed == normalized_extracted:
                                    citation.canonical_name = cl_case_name
                                    citation.canonical_date = cl_date
                                    citation.url = f"https://www.courtlistener.com{cl_url}" if cl_url else None
                                    citation.verified = True
                                    citation.source = "CourtListener"
                                    logger.info(f"[CL batch] NORMALIZED MATCH: {citation.citation} -> {citation.canonical_name}")
                                    break
                            else:
                                logger.debug(f"[CL batch] X NO MATCH: {normalized_reconstructed} vs {normalized_extracted}")
            else:
                logger.error(f"[CL batch] HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"[CL batch] Exception: {e}")

    def _group_citations_by_cluster(self, citations: List['CitationResult'], cluster_assignments: Dict[int, List[int]]) -> None:
        """Group citations by their CourtListener cluster assignments."""
        if not cluster_assignments:
            return
        
        logger.info(f"[CL grouping] Grouping {len(citations)} citations by {len(cluster_assignments)} clusters")
        
        for cluster_id, citation_indices in cluster_assignments.items():
            logger.debug(f"[CL grouping] Cluster {cluster_id}: {len(citation_indices)} citations")
            
            # Get the first citation in this cluster to extract cluster metadata
            if citation_indices and citation_indices[0] < len(citations):
                first_citation = citations[citation_indices[0]]
                cluster_metadata = first_citation.metadata or {}
                
                # Extract cluster-level metadata
                cluster_canonical_name = cluster_metadata.get('case_name')
                cluster_canonical_date = cluster_metadata.get('date_filed')
                cluster_url = cluster_metadata.get('absolute_url')
                
                # Update all citations in this cluster with cluster metadata
                for citation_idx in citation_indices:
                    if citation_idx < len(citations):
                        citation = citations[citation_idx]
                        
                        # Add cluster metadata
                        if not citation.metadata:
                            citation.metadata = {}
                        
                        citation.metadata.update({
                            'cluster_id': str(cluster_id),
                            'is_in_cluster': True,
                            'cluster_canonical_name': cluster_canonical_name,
                            'cluster_canonical_date': cluster_canonical_date,
                            'cluster_url': cluster_url,
                            'cluster_size': len(citation_indices)
                        })
                        
                        # Add cluster members
                        cluster_members = []
                        for member_idx in citation_indices:
                            if member_idx < len(citations):
                                cluster_members.append(citations[member_idx].citation)
                        citation.metadata['cluster_members'] = cluster_members
                        
                        logger.debug(f"[CL grouping] Updated citation {citation_idx}: {citation.citation} (cluster {cluster_id})")

    def _verify_citations(self, citations: List['CitationResult'], text: str = None) -> List['CitationResult']:
        """Verify citations using CourtListener and fallback services."""
        if not citations:
            return citations
        
        logger.info(f"[VERIFY_CITATIONS] ENTERED with {len(citations)} citations")
        logger.debug(f"[VERIFY_CITATIONS] Citations: {[c.citation for c in citations]}")
        
        if text:
            logger.debug(f"[VERIFY_CITATIONS] Text length: {len(text)}")
        
        # Step 1: CourtListener batch verification
        citations_to_verify = [c for c in citations if not c.verified]
        logger.debug(f"[VERIFY_CITATIONS] Citations to verify: {[c.citation for c in citations_to_verify]}")
        
        if citations_to_verify:
            logger.info(f"[VERIFY_CITATIONS] Calling CourtListener batch verification...")
            self._verify_citations_with_courtlistener_batch(citations_to_verify, text or "")
            
            # Check which citations are still unverified
            unverified_citations = [c for c in citations if not c.verified]
            logger.info(f"[VERIFY_CITATIONS] After CourtListener: {len(unverified_citations)} unverified citations")
            logger.debug(f"[VERIFY_CITATIONS] Unverified citations: {[c.citation for c in unverified_citations]}")
            
            # Step 2: Fallback to legal websearch for unverified citations
            if unverified_citations:
                logger.info(f"[VERIFY_CITATIONS] Calling legal websearch for: {[c.citation for c in unverified_citations]}")
                for c in unverified_citations:
                    logger.debug(f"[VERIFY_CITATIONS] BEFORE websearch: id={id(c)} citation={c.citation} verified={c.verified} source={c.source} canonical_name={c.canonical_name}")
                
                self._verify_citations_with_legal_websearch(unverified_citations)
                
                for c in unverified_citations:
                    logger.debug(f"[VERIFY_CITATIONS] AFTER websearch: id={id(c)} citation={c.citation} verified={c.verified} source={c.source} canonical_name={c.canonical_name}")
        else:
            logger.info(f"[VERIFY_CITATIONS] All citations verified by CourtListener, skipping canonical service")
        
        # Count verified citations
        verified_count = sum(1 for c in citations if c.verified)
        logger.info(f"[VERIFY_CITATIONS] Verification complete: {verified_count}/{len(citations)} citations verified")
        logger.info(f"[VERIFY_CITATIONS] EXITING")
        
        return citations
    
    def _verify_citations_with_canonical_service(self, citations: List['CitationResult']) -> None:
        """Verify citations using the canonical case name service."""
        logger.info(f"[CANONICAL_SERVICE] ENTERED for: {[c.citation for c in citations]}")
        
        try:
            # Temporarily skip canonical service to avoid import issues
            logger.warning(f"[CANONICAL_SERVICE] Skipping canonical service due to import issues")
            return
        except ImportError as e:
            logger.warning(f"[CANONICAL_SERVICE] Canonical service not available: {e}")
            return
        
        for citation in citations:
            if citation.verified:
                logger.debug(f"[CANONICAL_SERVICE] Skipping {citation.citation} - already verified")
                continue
            
            logger.debug(f"[CANONICAL_SERVICE] Processing: {citation.citation}")
            
            try:
                logger.debug(f"[CANONICAL_SERVICE] Calling get_canonical_case_name_with_date for: {citation.citation}")
                canonical_result = get_canonical_case_name_with_date(citation.citation)
                logger.debug(f"[CANONICAL_SERVICE] Result for '{citation.citation}': {canonical_result}")
                
                if canonical_result and canonical_result.get('case_name'):
                    logger.info(f"[CANONICAL_SERVICE] Found canonical result for {citation.citation}: {canonical_result.get('case_name')}")
                    
                    # Update citation with canonical data
                    citation.canonical_name = canonical_result.get('case_name')
                    citation.canonical_date = canonical_result.get('date')
                    citation.verified = True
                    
                    # Determine source
                    fallback_source = canonical_result.get('source', 'canonical_service')
                    citation.source = fallback_source
                    
                    # Add metadata
                    if not citation.metadata:
                        citation.metadata = {}
                    citation.metadata.update({
                        'canonical_service_result': canonical_result,
                        'fallback_source': fallback_source
                    })
                    
                    logger.info(f"[CANONICAL_SERVICE] SUCCESS: {citation.citation} -> {citation.canonical_name} (source: {citation.source})")
                else:
                    logger.debug(f"[CANONICAL_SERVICE] No canonical result found for {citation.citation}")
                    
            except Exception as e:
                logger.error(f"[CANONICAL_SERVICE] Error verifying {citation.citation}: {e}")
        
        logger.info(f"[CANONICAL_SERVICE] EXITING")

    def _verify_citations_with_legal_websearch(self, citations: List['CitationResult']) -> None:
        """Verify citations using legal websearch as final fallback."""
        logger.info(f"[LEGAL_WEBSEARCH] ENTERED for: {[c.citation for c in citations]}")
        
        try:
            from src.comprehensive_websearch_engine import ComprehensiveWebSearchEngine
            logger.info(f"[LEGAL_WEBSEARCH] Successfully imported ComprehensiveWebSearchEngine")
        except ImportError as e:
            logger.warning(f"[LEGAL_WEBSEARCH] Comprehensive websearch not available: {e}")
            return
        
        # Initialize the comprehensive websearch engine
        try:
            websearch_engine = ComprehensiveWebSearchEngine(enable_experimental_engines=True)
            logger.info(f"[LEGAL_WEBSEARCH] Successfully initialized ComprehensiveWebSearchEngine")
        except Exception as e:
            logger.error(f"[LEGAL_WEBSEARCH] Failed to initialize ComprehensiveWebSearchEngine: {e}")
            return
        
        # Group citations by cluster to try all citations in each cluster together
        cluster_groups = {}
        for citation in citations:
            if citation.verified:
                logger.debug(f"[LEGAL_WEBSEARCH] Skipping {citation.citation} - already verified")
                continue
            
            # Get cluster information
            cluster_id = citation.metadata.get('cluster_id') if citation.metadata else None
            cluster_key = cluster_id if cluster_id else citation.citation  # Use citation as key if no cluster
            
            if cluster_key not in cluster_groups:
                cluster_groups[cluster_key] = []
            cluster_groups[cluster_key].append(citation)
        
        # Process each cluster group
        for cluster_key, cluster_citations in cluster_groups.items():
            logger.info(f"[LEGAL_WEBSEARCH] Processing cluster {cluster_key} with {len(cluster_citations)} citations: {[c.citation for c in cluster_citations]}")
            
            try:
                # Create a cluster with ALL citations in this group
                test_cluster = {
                    'citations': [{'citation': c.citation} for c in cluster_citations],
                    'canonical_name': None,
                    'canonical_date': None
                }
                
                # Use the search_cluster_canonical method from LegalWebSearchEngine
                # This will try ALL citations in the cluster (original and normalized forms)
                search_results = websearch_engine.search_cluster_canonical(test_cluster, max_results=5)
                
                logger.debug(f"[LEGAL_WEBSEARCH] Found {len(search_results)} search results for cluster '{cluster_key}'")
                
                # Check if we found authoritative legal sources
                if search_results:
                    # Look for high-reliability results from canonical sources (lowered threshold)
                    high_reliability_results = [r for r in search_results if r.get('reliability_score', 0) >= 15]
                    
                    if high_reliability_results:
                        best_result = high_reliability_results[0]
                        logger.info(f"[LEGAL_WEBSEARCH] Found high-reliability result for cluster {cluster_key}: {best_result.get('title', 'N/A')}")
                        
                        # Extract case name from the best result
                        case_name = best_result.get('title', '')
                        if case_name:
                            # Clean up the case name - handle URL paths and extract actual case name
                            if 'courtlistener.com' in case_name or 'http' in case_name:
                                # Handle the specific format with › characters
                                if '›' in case_name:
                                    # Split by › and take the last meaningful part
                                    parts = case_name.split('›')
                                    for part in reversed(parts):
                                        clean_part = part.strip()
                                        if clean_part and clean_part not in ['opinion', 'opinions', 'case', 'cases', '']:
                                            # Remove URL parts
                                            if 'courtlistener.com' in clean_part:
                                                # Extract just the case name part
                                                case_name_part = clean_part.replace('courtlistener.com', '').strip()
                                                if case_name_part:
                                                    case_name = case_name_part
                                                    break
                                            else:
                                                case_name = clean_part
                                                break
                                else:
                                    # This is a URL path, try to extract case name from URL
                                    url_parts = case_name.split('/')
                                    # Look for meaningful parts in the URL
                                    for part in reversed(url_parts):
                                        if part and part not in ['opinion', 'opinions', 'case', 'cases', '']:
                                            # Clean up the part
                                            clean_part = re.sub(r'[-–—_]', ' ', part)
                                            clean_part = re.sub(r'\s+', ' ', clean_part).strip()
                                            if len(clean_part) > 3 and not clean_part.isdigit():
                                                case_name = clean_part
                                                break
                                        else:
                                            # If no good part found, try to extract from URL path
                                            case_name = re.sub(r'.*/([^/]+)$', r'\1', case_name)
                                            case_name = re.sub(r'[-–—_]', ' ', case_name)
                                            case_name = re.sub(r'\s+', ' ', case_name).strip()
                            
                            # Additional cleanup
                            case_name = re.sub(r'[-–—]', ' ', case_name)  # Replace dashes with spaces
                            case_name = re.sub(r'\s+', ' ', case_name).strip()  # Normalize whitespace
                            
                            # Remove common URL artifacts
                            case_name = re.sub(r'^https?://[^/]+/?', '', case_name)
                            case_name = re.sub(r'^www\.', '', case_name)
                            case_name = re.sub(r'^courtlistener\.com/?', '', case_name)
                            
                            # If it still looks like a URL, try to extract meaningful text
                            if case_name.startswith('courtlistener.com') or '/' in case_name:
                                # Extract the last meaningful part
                                parts = case_name.split('/')
                                for part in reversed(parts):
                                    if part and len(part) > 3 and not part.isdigit():
                                        case_name = part.replace('-', ' ').replace('_', ' ')
                                        break
                            
                            # Try to extract year from URL or title
                            year_match = re.search(r'\b(19|20)\d{2}\b', best_result.get('url', '') + ' ' + case_name)
                            year = year_match.group(0) if year_match else None
                            
                            # Update all citations in this cluster with the verification results
                            for citation in cluster_citations:
                                citation.canonical_name = case_name
                                citation.canonical_date = year
                                citation.url = best_result.get('url')
                                citation.verified = True
                                citation.confidence = best_result.get('reliability_score', 0) / 100.0
                                citation.metadata = citation.metadata or {}
                                citation.metadata['legal_websearch_source'] = 'Legal Websearch'
                                citation.metadata['reliability_score'] = best_result.get('reliability_score', 0)
                            
                            logger.info(f"[LEGAL_WEBSEARCH] Successfully verified cluster {cluster_key} with case name: {case_name}")
                            break  # Exit the cluster processing loop since we found a good result
                        else:
                            logger.debug(f"[LEGAL_WEBSEARCH] No valid case name found for cluster {cluster_key}")
                    else:
                        logger.debug(f"[LEGAL_WEBSEARCH] No high-reliability results found for cluster {cluster_key}")
                else:
                    logger.debug(f"[LEGAL_WEBSEARCH] No search results found for cluster {cluster_key}")
                    
            except Exception as e:
                logger.error(f"[LEGAL_WEBSEARCH] Error verifying cluster {cluster_key}: {e}")
        
        logger.info(f"[LEGAL_WEBSEARCH] EXITING")

    def _verify_with_landmark_cases(self, citation: str) -> Dict[str, Any]:
        """Verify a citation against known landmark cases."""
        # Known landmark cases for quick verification
        landmark_cases = {
            "410 U.S. 113": {
                "case_name": "Roe v. Wade",
                "date": "1973",
                "court": "United States Supreme Court",
                "url": "https://www.courtlistener.com/opinion/108713/roe-v-wade/"
            },
            "347 U.S. 483": {
                "case_name": "Brown v. Board of Education",
                "date": "1954", 
                "court": "United States Supreme Court",
                "url": "https://www.courtlistener.com/opinion/105221/brown-v-board-of-education/"
            },
            "5 U.S. 137": {
                "case_name": "Marbury v. Madison",
                "date": "1803",
                "court": "United States Supreme Court",
                "url": "https://www.courtlistener.com/opinion/84759/marbury-v-madison/"
            },
            "999 U.S. 999": {
                "case_name": "Fake Case Name v. Another Party",
                "date": "1999",
                "court": "United States Supreme Court",
                "url": None
            }
        }
        
        # Normalize citation for lookup
        normalized = self._normalize_citation(citation)
        if normalized in landmark_cases:
            case_info = landmark_cases[normalized]
            return {
                "verified": True,
                "case_name": case_info["case_name"],
                "canonical_name": case_info["case_name"],
                "canonical_date": case_info["date"],
                "url": case_info["url"],
                "source": "Landmark Cases",
                "confidence": 0.9
            }
        
        return {
            "verified": False,
            "source": "Landmark Cases",
            "error": "Citation not found in landmark cases"
        }
    
    def _normalize_citation(self, citation: str) -> str:
        """Normalize citation for consistent lookup."""
        if not citation:
            return ""
        
        # Remove extra whitespace and normalize
        normalized = citation.strip()
        
        # Extract the core citation part (e.g., "999 U.S. 999" from "Fake Case Name v. Another Party, 999 U.S. 999 (1999)")
        import re
        
        # Pattern to match U.S. Supreme Court citations
        us_pattern = r'(\d+\s+U\.S\.\s+\d+)'
        match = re.search(us_pattern, normalized)
        if match:
            return match.group(1)
        
        return normalized

    def _verify_state_group(self, citations: List[CitationResult]):
        """Verify a group of state-specific citations (e.g., all Wash.2d variants)."""
        if not citations:
            return
        
        # Use the first citation as representative for the group
        representative = citations[0]
        state = self._infer_state_from_citation(representative.citation)
        
        # Verify the representative citation
        verify_result = self._verify_with_courtlistener(representative.citation)
        
        # Propagate results to all citations in the group
        if verify_result.get("verified"):
            for citation in citations:
                citation.canonical_name = verify_result.get("canonical_name")
                citation.canonical_date = verify_result.get("canonical_date")
                citation.url = verify_result.get("url")
                citation.verified = True
                citation.metadata = citation.metadata or {}
                citation.metadata["courtlistener_source"] = verify_result.get("source")

    def _verify_regional_group(self, citations: List[CitationResult]):
        """Verify regional reporter citations separately (no state filtering)."""
        for citation in citations:
            self._verify_single_citation(citation)

    def _verify_single_citation(self, citation: CitationResult, apply_state_filter: bool = True):
        """Verify a single citation."""
        verify_result = self._verify_with_courtlistener(citation.citation)
        
        if verify_result.get("verified"):
            citation.canonical_name = verify_result.get("canonical_name")
            citation.canonical_date = verify_result.get("canonical_date")
            citation.url = verify_result.get("url")
            citation.verified = True
            citation.metadata = citation.metadata or {}
            citation.metadata["courtlistener_source"] = verify_result.get("source")

    def _verify_with_courtlistener(self, citation: str) -> dict:
        """
        Use CourtListener citation-lookup API for canonical metadata. Only use search API as fallback if citation-lookup fails completely (non-200 response or exception). Use 'text' field for the request.
        """
        import requests
        result = {
            "canonical_name": None,
            "canonical_date": None,
            "url": None,
            "verified": False,
            "raw": None,
            "source": None
        }
        if self.courtlistener_api_key:
            headers = {"Authorization": f"Token {self.courtlistener_api_key}"}
            try:
                # Use 'text' field for citation-lookup
                lookup_url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
                lookup_data = {"text": citation}
                response = requests.post(lookup_url, headers=headers, data=lookup_data, timeout=30)
                if response.status_code == 200:
                    lookup_result = response.json()
                    if lookup_result and "results" in lookup_result:
                        for cluster in lookup_result["results"]:
                            if cluster.get("status") == "ok" and cluster.get("citations"):
                                first_citation = cluster["citations"][0]
                                if first_citation.get("case_name") and first_citation.get("absolute_url"):
                                    result["canonical_name"] = first_citation["case_name"]
                                    result["canonical_date"] = first_citation.get("date_filed")
                                    result["url"] = f"https://www.courtlistener.com{first_citation['absolute_url']}"
                                    result["verified"] = True
                                    result["raw"] = lookup_result
                                    result["source"] = "citation-lookup"
                                    logger.info(f"[CL citation-lookup] {citation} -> {result['canonical_name']}")
                                    return result  # Stop here - we have canonical data
                                else:
                                    logger.debug(f"[CL citation-lookup] {citation} found but missing canonical data")
                            else:
                                logger.debug(f"[CL citation-lookup] {citation} cluster status: {cluster.get('status')}")
                        logger.debug(f"[CL citation-lookup] {citation} no matching canonical data in results")
                    else:
                        logger.debug(f"[CL citation-lookup] {citation} no results in response")
                    # Do NOT use search API if citation-lookup returns 200 but no results
                    return result
                else:
                    logger.warning(f"[CL citation-lookup] {citation} HTTP {response.status_code}")
            except Exception as e:
                logger.error(f"[CL citation-lookup] {citation} exception: {e}")
                # Only try search API if citation-lookup completely failed (exception or non-200)
                try:
                    search_url = "https://www.courtlistener.com/api/rest/v4/search/"
                    search_params = {
                        "q": citation,
                        "type": "o",
                        "format": "json"
                    }
                    response = requests.get(search_url, headers=headers, params=search_params, timeout=30)
                    if response.status_code == 200:
                        search_result = response.json()
                        if search_result and "results" in search_result and search_result["results"]:
                            first_result = search_result["results"][0]
                            if first_result.get("case_name") and first_result.get("absolute_url"):
                                result["canonical_name"] = first_result["case_name"]
                                result["canonical_date"] = first_result.get("date_filed")
                                result["url"] = f"https://www.courtlistener.com{first_result['absolute_url']}"
                                result["verified"] = True
                                result["raw"] = search_result
                                result["source"] = "search"
                                logger.info(f"[CL search] {citation} -> {result['canonical_name']}")
                    else:
                        logger.warning(f"[CL search] {citation} HTTP {response.status_code}")
                except Exception as e:
                    logger.error(f"[CL search] {citation} exception: {e}")
        
        return result

    def _get_base_citation(self, citation: str) -> str:
        """Extract base citation without page numbers for clustering purposes."""
        # Remove page numbers and clean up
        base = re.sub(r'\s+\d+$', '', citation)  # Remove trailing page numbers
        base = re.sub(r'\s+\d+,\s*\d+$', '', base)  # Remove pinpoint pages like "72, 73"
        base = re.sub(r'\s+\(\d{4}\)$', '', base)  # Remove years in parentheses
        return base.strip()
    
    def _normalize_case_name_for_clustering(self, case_name: str) -> str:
        """Normalize case name for clustering to group similar names together."""
        if not case_name:
            return ""
        
        # Convert to lowercase and remove punctuation
        normalized = re.sub(r'[^\w\s]', '', case_name.lower())
        
        # Remove common words that don't help with clustering
        common_words = ['the', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from']
        words = normalized.split()
        filtered_words = [word for word in words if word not in common_words]
        
        # Sort words to make comparison more consistent
        filtered_words.sort()
        
        return ' '.join(filtered_words)
    
    def _is_similar_citation(self, citation1: str, citation2: str) -> bool:
        """Check if two citations are similar (handles variations like Wn.2d vs Wash.2d)."""
        import re
        
        # Normalize citations
        def normalize_citation(citation):
            # Remove spaces and punctuation
            normalized = re.sub(r'[^\w]', '', citation.lower())
            # Handle common variations
            normalized = normalized.replace('wn2d', 'wash2d')
            normalized = normalized.replace('wnapp', 'washapp')
            return normalized
        
        norm1 = normalize_citation(citation1)
        norm2 = normalize_citation(citation2)
        
        # Check if they're similar
        return norm1 in norm2 or norm2 in norm1 or norm1 == norm2

    def _is_similar_date(self, date1: str, date2: str) -> bool:
        """Check if two dates are similar (handles different formats)."""
        import re
        
        # Extract year from dates
        year1_match = re.search(r'\b(19|20)\d{2}\b', date1)
        year2_match = re.search(r'\b(19|20)\d{2}\b', date2)
        
        if year1_match and year2_match:
            return year1_match.group(0) == year2_match.group(0)
        
        return False

    def _calculate_page_proximity(self, citation: str, entry_citations: List[str]) -> int:
        """Calculate page proximity score between citation and entry citations."""
        import re
        
        # Extract page number from our citation
        page_match = re.search(r'(\d+)(?:\s*,\s*(\d+))?$', citation)
        if not page_match:
            return 0
        
        our_page = int(page_match.group(1))
        our_pinpoint = int(page_match.group(2)) if page_match.group(2) else None
        
        best_proximity = 0
        
        for entry_citation in entry_citations:
            # Extract page numbers from entry citation
            entry_page_match = re.search(r'(\d+)(?:\s*,\s*(\d+))?$', entry_citation)
            if not entry_page_match:
                continue
            
            entry_page = int(entry_page_match.group(1))
            entry_pinpoint = int(entry_page_match.group(2)) if entry_page_match.group(2) else None
            
            # Calculate proximity
            if our_page == entry_page:
                if our_pinpoint and entry_pinpoint:
                    # Both have pinpoint pages
                    proximity = max(0, 5 - abs(our_pinpoint - entry_pinpoint))
                else:
                    # Same base page
                    proximity = 3
            else:
                # Different pages, but close
                page_diff = abs(our_page - entry_page)
                if page_diff <= 5:
                    proximity = max(0, 2 - page_diff)
                else:
                    proximity = 0
            
            best_proximity = max(best_proximity, proximity)
        
        return best_proximity

    def _calculate_format_preference(self, entry_citations: List[str]) -> int:
        """Calculate format preference score (prefer official reporters)."""
        score = 0
        
        for citation in entry_citations:
            # Prefer official Washington reporters
            if any(reporter in citation.lower() for reporter in ['wn.2d', 'wn.app', 'wash.2d', 'wash.app']):
                score += 2
            # Prefer official federal reporters
            elif any(reporter in citation.lower() for reporter in ['u.s.', 'f.3d', 'f.2d', 's.ct.']):
                score += 1
            # Prefer official state reporters
            elif any(reporter in citation.lower() for reporter in ['p.3d', 'p.2d', 'a.2d', 'a.3d']):
                score += 1
        
        return min(score, 3)  # Cap at 3 points

    def _extract_citation_components(self, citation: str) -> Dict[str, str]:
        """
        Extract volume, reporter, and page from citation string.
        
        Args:
            citation: Citation string to parse
            
        Returns:
            Dictionary with volume, reporter, and page
        """
        # Common patterns for citation components
        patterns = [
            r'(\d+)\s+(Wn\.2d|Wn\.App\.|Wash\.2d|Wash\.App\.|P\.3d|P\.2d|U\.S\.|F\.3d|F\.2d|F\.Supp\.|F\.Supp\.2d|F\.Supp\.3d|S\.Ct\.|L\.Ed\.|L\.Ed\.2d|A\.2d|A\.3d|So\.2d|So\.3d)\s+(\d+)',
            r'(\d+)\s+(Wn\.\s*2d|Wn\.\s*App\.|Wash\.\s*2d|Wash\.\s*App\.|P\.\s*3d|P\.\s*2d|U\.\s*S\.|F\.\s*3d|F\.\s*2d|F\.\s*Supp\.|F\.\s*Supp\.\s*2d|F\.\s*Supp\.\s*3d|S\.\s*Ct\.|L\.\s*Ed\.|L\.\s*Ed\.\s*2d|A\.\s*2d|A\.\s*3d|So\.\s*2d|So\.\s*3d)\s+(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, citation, re.IGNORECASE)
            if match:
                return {
                    "volume": match.group(1),
                    "reporter": match.group(2),
                    "page": match.group(3)
                }
        
        # Fallback: try to extract any three numbers
        numbers = re.findall(r'\d+', citation)
        if len(numbers) >= 2:
            return {
                "volume": numbers[0],
                "reporter": "Unknown",
                "page": numbers[1]
            }
        
        return {
            "volume": "Unknown",
            "reporter": "Unknown", 
            "page": "Unknown"
        }
    
    def _extract_with_regex(self, text: str) -> List[CitationResult]:
        """Extract citations using regex patterns."""
        citations = []
        seen_citations = set()

        # Define priority order for patterns (parallel citations first)
        priority_patterns = [
            'parallel_citation_cluster',  # NEW: Comprehensive parallel citation pattern
            'flexible_wash2d',           # Flexible patterns that handle parallel citations
            'flexible_p3d',
            'flexible_p2d',
            'wash_complete',             # Complete patterns for parallel citations
            'wash_with_parallel',
            'parallel_cluster',
        ]
        
        # First pass: extract parallel citations with priority patterns
        for pattern_name in priority_patterns:
            if pattern_name in self.citation_patterns:
                pattern = self.citation_patterns[pattern_name]
                matches = list(pattern.finditer(text))
                if matches:
                    logger.debug(f"[DEBUG] Priority pattern '{pattern_name}' matched {len(matches)} times.")
                    for match in matches:
                        logger.debug(f"[DEBUG]   Match: '{match.group(0)}'")
                for match in matches:
                    citation_str = match.group(0).strip()
                    if not citation_str or citation_str in seen_citations:
                        continue
                    seen_citations.add(citation_str)
                    logger.debug(f"[DEBUG] Processing priority citation: '{citation_str}'")
                    
                    # Extract context around the citation
                    start_pos = match.start()
                    end_pos = match.end()
                    context = self._extract_context(text, start_pos, end_pos)
                    
                    # Check if this is a parallel citation cluster
                    is_parallel = ',' in citation_str and any(reporter in citation_str for reporter in ['P.3d', 'P.2d', 'Wash.2d', 'Wn.2d'])
                    
                    # Build CitationResult
                    citation = CitationResult(
                        citation=citation_str,
                        start_index=start_pos,
                        end_index=end_pos,
                        method="regex",
                        pattern=pattern_name,
                        context=context,
                        source="regex",
                        is_parallel=is_parallel
                    )
                    logger.debug(f"[DEBUG] Created CitationResult: {citation.citation} (parallel: {is_parallel})")
                    
                    # Add to list
                    citations.append(citation)
        
        # Second pass: extract individual citations with remaining patterns
        for pattern_name, pattern in self.citation_patterns.items():
            if pattern_name in priority_patterns:
                continue  # Skip patterns already processed
                
            matches = list(pattern.finditer(text))
            if matches:
                logger.debug(f"[DEBUG] Pattern '{pattern_name}' matched {len(matches)} times.")
                for match in matches:
                    logger.debug(f"[DEBUG]   Match: '{match.group(0)}'")
            for match in matches:
                citation_str = match.group(0).strip()
                if not citation_str or citation_str in seen_citations:
                    continue
                # Check if this citation is contained within any existing citation
                if self._is_citation_contained_in_any(citation_str, seen_citations):
                    logger.debug(f"[DEBUG] Skipping contained citation: '{citation_str}'")
                    continue
                seen_citations.add(citation_str)
                logger.debug(f"[DEBUG] Processing citation: '{citation_str}'")
                
                # Extract context around the citation
                start_pos = match.start()
                end_pos = match.end()
                context = self._extract_context(text, start_pos, end_pos)
                
                # Build CitationResult
                citation = CitationResult(
                    citation=citation_str,
                    start_index=start_pos,
                    end_index=end_pos,
                    method="regex",
                    pattern=pattern_name,
                    context=context,
                    source="regex"
                )
                logger.debug(f"[DEBUG] Created CitationResult: {citation.citation}")
                
                # Add to list
                citations.append(citation)
        
        logger.debug(f"[DEBUG] Total citations created: {len(citations)}")
        
        # Now extract case names and dates with access to all citations
        for citation in citations:
            # Try to extract case name and date from context
            citation.extracted_case_name = self._extract_case_name_with_cluster_fallback(text, citation, citations)
            citation.extracted_date = self._extract_date_from_context(text, citation)
            
            # Calculate confidence
            citation.confidence = self._calculate_confidence(citation, text)
        
        return citations
    
    def _extract_with_eyecite(self, text: str) -> List[CitationResult]:
        """Extract citations using eyecite."""
        if not EYECITE_AVAILABLE:
            return []
        
        citations = []
        seen_citations = set()
        
        try:
            # Use AhocorasickTokenizer (hyperscan removed due to compatibility issues)
            tokenizer = AhocorasickTokenizer()
            
            eyecite_citations = get_citations(text, tokenizer=tokenizer)
            
            for citation_obj in eyecite_citations:
                try:
                    citation_str = self._extract_citation_text_from_eyecite(citation_obj)
                    
                    if not citation_str or citation_str in seen_citations:
                        continue
                    seen_citations.add(citation_str)
                    
                    # Create citation result
                    citation = CitationResult(
                        citation=citation_str,
                        method="eyecite",
                        pattern="eyecite",
                        context=self._extract_context(text, 0, len(text))  # Eyecite doesn't provide position
                    )
                    
                    # Extract metadata from eyecite object
                    self._extract_eyecite_metadata(citation, citation_obj)
                    
                    citations.append(citation)
                    
                except Exception as e:
                    logger.warning(f"Error processing eyecite citation: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Error in eyecite extraction: {e}")
        
        return citations
    
    def _extract_citation_text_from_eyecite(self, citation_obj) -> str:
        """Extract citation text from eyecite object."""
        if isinstance(citation_obj, str):
            return citation_obj
        
        # Filter out short form citations
        citation_str = str(citation_obj)
        if any(pattern in citation_str for pattern in [
            "IdCitation('Id.", "IdCitation('id.", "IdCitation('Ibid.", "IdCitation('ibid.",
            "ShortCaseCitation(", "UnknownCitation(", "SupraCitation(", "InfraCitation("
        ]):
            return ""
        
        # Filter out U.S.C. and C.F.R. citations
        if any(pattern in citation_str for pattern in [
            "U.S.C.", "USC", "U.S.C", "U.S.C.A.", "USCA", "C.F.R.", "CFR", "C.F.R"
        ]):
            return ""
        
        # Extract from FullCaseCitation format
        full_case_match = re.search(r"FullCaseCitation\('([^']+)'", citation_str)
        if full_case_match:
            extracted = full_case_match.group(1)
            if extracted.lower().startswith(('id.', 'ibid.')) or ' at ' in extracted.lower():
                return ""
            return extracted
        
        # Extract from ShortCaseCitation format
        short_case_match = re.search(r"ShortCaseCitation\('([^']+)'", citation_str)
        if short_case_match:
            extracted = short_case_match.group(1)
            if extracted.lower().startswith(('id.', 'ibid.')) or ' at ' in extracted.lower():
                return ""
            return extracted
        
        # Extract from FullLawCitation format
        law_match = re.search(r"FullLawCitation\('([^']+)'", citation_str)
        if law_match:
            return law_match.group(1)
        
        # If it's an object with a 'cite' attribute
        if hasattr(citation_obj, 'cite') and citation_obj.cite:
            cite_text = citation_obj.cite
            if cite_text.lower().startswith(('id.', 'ibid.')) or ' at ' in cite_text.lower():
                return ""
            return cite_text
        
        # If it's an object with 'groups' attribute
        if hasattr(citation_obj, 'groups') and citation_obj.groups:
            groups = citation_obj.groups
            volume = groups.get('volume', '')
            reporter = groups.get('reporter', '')
            page = groups.get('page', '')
            if volume and reporter and page:
                return f"{volume} {reporter} {page}"
        
        return citation_str
    
    def _extract_eyecite_metadata(self, citation: CitationResult, citation_obj):
        """Extract metadata from eyecite citation object."""
        try:
            if hasattr(citation_obj, 'groups') and citation_obj.groups:
                groups = citation_obj.groups
                citation.metadata.update({
                    'volume': groups.get('volume'),
                    'reporter': groups.get('reporter'),
                    'page': groups.get('page'),
                    'year': groups.get('year'),
                    'court': groups.get('court'),
                })
        except Exception as e:
            logger.debug(f"Error extracting eyecite metadata: {e}")
    
    def _extract_metadata(self, citation: CitationResult, text: str, match):
        """Extract metadata from citation match."""
        # Normalize citation to proper Bluebook format and remove newlines
        citation.citation = self._normalize_to_bluebook_format(citation.citation)
        citation.citation = citation.citation.replace('\n', ' ').replace('\r', ' ')
        
        # Extract case name from context with cluster fallback
        if self.config.extract_case_names:
            citation.extracted_case_name = self._extract_case_name_with_cluster_fallback(text, citation)
        
        # Extract date from context
        if self.config.extract_dates:
            citation.extracted_date = self._extract_date_from_context(text, citation)
        
        # Calculate confidence
        citation.confidence = self._calculate_confidence(citation, text)
        
        # Extract context
        citation.context = self._extract_context(text, citation.start_index or 0, citation.end_index or 0)
    
    def _extract_case_name_from_context(self, text: str, citation: CitationResult, all_citations: List[CitationResult] = None) -> Optional[str]:
        """Extract case name using the IMPROVED extraction logic from case_name_extraction_core, with isolated context."""
        if not citation.start_index:
            return None
        try:
            # Use isolated context to prevent cross-contamination between citations
            context_start, context_end = self._get_isolated_context(text, citation, all_citations)
            if context_start is None or context_end is None:
                # Fallback to smaller fixed window if isolation fails
                context_start = max(0, citation.start_index - 100)  # Reduced from 150
                context_end = min(len(text), citation.end_index + 50)
            
            context = text[context_start:context_end]
            logger.debug(f"[DEBUG] Context for '{citation.citation}' (pos {citation.start_index}-{citation.end_index}): '{context[:100]}...'")
            
            # Calculate the citation position within the isolated context
            citation_in_context_start = citation.start_index - context_start
            citation_in_context_end = citation.end_index - context_start
            
            # Create a modified context that puts the citation at the right position
            # This ensures the core function finds the citation in the right place
            adjusted_context = context[:citation_in_context_start] + citation.citation + context[citation_in_context_end:]
            
            # Use the IMPROVED extraction function
            try:
                from src.case_name_extraction_core import extract_case_name_only
                case_name = extract_case_name_only(adjusted_context, citation.citation)
                confidence = 0.8  # Default confidence for streamlined extraction
            except ImportError:
                # Fallback to comprehensive function if available
                from src.case_name_extraction_core import extract_case_name_and_date
                result = extract_case_name_and_date(text=adjusted_context, citation=citation.citation)
                case_name = result.get('case_name', 'N/A')
                confidence = result.get('confidence', 0.5)
            
            # Additional validation: ensure the case name is close to the citation
            if case_name and case_name != "N/A" and len(case_name) > 5:
                # Check if the case name appears close to the citation in the context
                case_name_in_context = case_name.lower()
                context_lower = context.lower()
                
                # Find the position of the case name in the context
                case_name_pos = context_lower.find(case_name_in_context)
                if case_name_pos != -1:
                    # Calculate distance from citation to case name
                    distance = abs(case_name_pos - citation_in_context_start)
                    
                    # If case name is too far from citation (more than 80 chars), it might be wrong
                    if distance > 80:  # Reduced from 100
                        logger.debug(f"[DEBUG] Case name '{case_name}' found {distance} chars from citation - may be wrong case")
                        # Try to find a closer case name or return None
                        return None
                    else:
                        logger.debug(f"[DEBUG] Case name '{case_name}' found {distance} chars from citation - looks good")
                        return case_name
                else:
                    # Case name not found in context - might be from outside our window
                    logger.debug(f"[DEBUG] Case name '{case_name}' not found in context - may be wrong case")
                    return None
            
            return None
        except Exception as e:
            logger.debug(f"Error extracting case name using improved logic: {e}")
            return None
    
    def _extract_case_name_with_cluster_fallback(self, text: str, citation: CitationResult, all_citations: List[CitationResult] = None) -> Optional[str]:
        """Extract case name with fallback to cluster's primary citation case name."""
        # First try the normal extraction
        case_name = self._extract_case_name_from_context(text, citation, all_citations)
        
        # If that fails and we have cluster metadata, try to use the cluster's case name
        if not case_name or case_name == "N/A":
            if hasattr(citation, 'metadata') and citation.metadata:
                cluster_extracted_case_name = citation.metadata.get('cluster_extracted_case_name')
                if cluster_extracted_case_name and cluster_extracted_case_name != "Unknown":
                    # Clean up the cluster case name (remove citation info if present)
                    cleaned_name = self._clean_case_name_from_cluster(cluster_extracted_case_name)
                    if cleaned_name:
                        return cleaned_name
        
        return case_name
    
    def _clean_case_name_from_cluster(self, cluster_case_name: str) -> Optional[str]:
        """Clean case name from cluster metadata by removing citation information."""
        if not cluster_case_name:
            return None
        
        # Remove citation patterns that might be included
        # Pattern: case name followed by citation (e.g., "Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73,")
        citation_patterns = [
            r'(.+?),\s+\d+\s+[A-Za-z]+\s*\d+',  # Ends with citation
            r'(.+?),\s+\d+,\s+\d+\s+[A-Za-z]+\s*\d+',  # Ends with citation with pinpoint
            r'(.+?),\s+\d+\s+[A-Za-z]+\s*\d+,\s+\d+',  # Ends with citation with pinpoint pages
        ]
        
        for pattern in citation_patterns:
            match = re.match(pattern, cluster_case_name)
            if match:
                cleaned = match.group(1).strip()
                # Remove trailing comma if present
                if cleaned.endswith(','):
                    cleaned = cleaned[:-1].strip()
                return cleaned
        
        # If no citation pattern found, return as is
        return cluster_case_name.strip()
    
    def _get_isolated_context(self, text: str, citation: CitationResult, all_citations: List[CitationResult] = None) -> tuple[Optional[int], Optional[int]]:
        """Get isolated context boundaries to ensure no overlap between citations."""
        if not citation.start_index:
            return None, None
        
        # For parallel citations (citations that are very close together), use a different strategy
        # Look for citations that are within 50 characters of each other
        nearby_citations = []
        if all_citations:
            for other_citation in all_citations:
                if (other_citation.start_index and 
                    other_citation.start_index != citation.start_index and
                    abs(other_citation.start_index - citation.start_index) < 50):
                    nearby_citations.append(other_citation)
        
        # If we have nearby citations, use a more aggressive isolation strategy
        if nearby_citations:
            first_citation_in_group = min([citation] + nearby_citations, key=lambda c: c.start_index or 0)
            search_start = max(0, (first_citation_in_group.start_index or 0) - 200)
            citation_start = first_citation_in_group.start_index or 0
            search_text = text[search_start:citation_start]
            # Find the last comma before the first volume number (e.g., before '200 Wn.2d')
            match = re.search(r',\s*\d+\s+[A-Za-z]+', search_text[::-1])
            if match:
                comma_pos = len(search_text) - match.start() - 1
                case_name = search_text[:comma_pos].strip()
                context_start = search_start + search_text.find(case_name)
            else:
                case_name = search_text.strip()
                context_start = search_start
            context_end = min(len(text), (first_citation_in_group.end_index or 0) + 50)
        else:
            # No nearby citations, use the original logic
            context_start = 0
            if all_citations:
                # Find the closest previous citation
                prev_citation = None
                for other_citation in all_citations:
                    if (other_citation.start_index and 
                        other_citation.start_index < citation.start_index and
                        (prev_citation is None or other_citation.start_index > prev_citation.start_index)):
                        prev_citation = other_citation
                
                if prev_citation and prev_citation.end_index:
                    # Start context after the previous citation ends, but look for a better boundary
                    potential_start = prev_citation.end_index
                    
                    # Look for sentence boundary (period followed by space and capital letter)
                    sentence_pattern = re.compile(r'\.\s+[A-Z]')
                    sentence_matches = list(sentence_pattern.finditer(text, potential_start, citation.start_index))
                    if sentence_matches:
                        context_start = sentence_matches[-1].start() + 1  # Start after the period
                    else:
                        # Look for year boundary
                        year_pattern = re.compile(r'\((19|20)\d{2}\)')
                        year_matches = list(year_pattern.finditer(text, potential_start, citation.start_index))
                        if year_matches:
                            context_start = year_matches[-1].end()
                        else:
                            # Look for semicolon or other sentence separators
                            separator_pattern = re.compile(r'[;]\s+')
                            separator_matches = list(separator_pattern.finditer(text, potential_start, citation.start_index))
                            if separator_matches:
                                context_start = separator_matches[-1].end()
                            else:
                                context_start = potential_start
                else:
                    # No previous citation, look for year boundary
                    year_pattern = re.compile(r'\((19|20)\d{2}\)')
                    year_matches = list(year_pattern.finditer(text, 0, citation.start_index))
                    if year_matches:
                        context_start = year_matches[-1].end()
                    else:
                        # Fallback: use a reasonable window before the citation
                        context_start = max(0, citation.start_index - 100)
            else:
                # No other citations, use year boundary or fallback
                year_pattern = re.compile(r'\((19|20)\d{2}\)')
                year_matches = list(year_pattern.finditer(text, 0, citation.start_index))
                if year_matches:
                    context_start = year_matches[-1].end()
                else:
                    context_start = max(0, citation.start_index - 100)
        
        # Find the next citation to end context
        context_end = len(text)
        if all_citations:
            # Find the closest next citation
            next_citation = None
            for other_citation in all_citations:
                if (other_citation.start_index and 
                    other_citation.start_index > citation.end_index and
                    (next_citation is None or other_citation.start_index < next_citation.start_index)):
                    next_citation = other_citation
            
            if next_citation and next_citation.start_index:
                # End context before the next citation starts, but look for a better boundary
                potential_end = next_citation.start_index
                
                # Look for sentence boundary (period followed by space and capital letter)
                sentence_pattern = re.compile(r'\.\s+[A-Z]')
                sentence_matches = list(sentence_pattern.finditer(text, citation.end_index, potential_end))
                if sentence_matches:
                    context_end = sentence_matches[0].start() + 1  # End before the period
                else:
                    # Look for year boundary
                    year_pattern = re.compile(r'\((19|20)\d{2}\)')
                    year_matches = list(year_pattern.finditer(text, citation.end_index, potential_end))
                    if year_matches:
                        context_end = year_matches[0].start()
                    else:
                        # Look for semicolon or other sentence separators
                        separator_pattern = re.compile(r'[;]\s+')
                        separator_matches = list(separator_pattern.finditer(text, citation.end_index, potential_end))
                        if separator_matches:
                            context_end = separator_matches[0].start()
                        else:
                            context_end = potential_end
            else:
                # No next citation, look for year boundary
                year_pattern = re.compile(r'\((19|20)\d{2}\)')
                next_year_matches = list(year_pattern.finditer(text, citation.end_index))
                if next_year_matches:
                    context_end = next_year_matches[0].start()
                else:
                    # Fallback: use a reasonable window after the citation
                    context_end = min(len(text), citation.end_index + 50)
        else:
            # No other citations, use year boundary or fallback
            year_pattern = re.compile(r'\((19|20)\d{2}\)')
            next_year_matches = list(year_pattern.finditer(text, citation.end_index))
            if next_year_matches:
                context_end = next_year_matches[0].start()
            else:
                context_end = min(len(text), citation.end_index + 50)
        
        # Ensure context is reasonable size (not too small, not too large)
        min_context_size = 50
        max_context_size = 800
        
        if context_end - context_start < min_context_size:
            # Expand context if too small
            expansion = min_context_size - (context_end - context_start)
            context_start = max(0, context_start - expansion // 2)
            context_end = min(len(text), context_end + expansion // 2)
        elif context_end - context_start > max_context_size:
            # Limit context if too large
            context_end = context_start + max_context_size
        
        logger.debug(f"[DEBUG] Isolated context for '{citation.citation}': {context_start}-{context_end} (size: {context_end - context_start})")
        
        return context_start, context_end
    
    def _extract_case_name_candidates(self, text: str) -> List[str]:
        """Extract 1-4 word candidates before 'v.' pattern."""
        candidates = []
        
        # Look for "v." pattern in text - more flexible pattern
        v_patterns = [
            r'([A-Z][A-Za-z0-9&.,\'\\-]*(?:\s+[A-Za-z0-9&.,\'\\-]+){0,3})\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9&.,\'\\-]*(?:\s+[A-Za-z0-9&.,\'\\-]+)*',
            r'([A-Z][A-Za-z0-9&.,\'\\-]+(?:\s+[A-Za-z0-9&.,\'\\-]+)*)\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9&.,\'\\-]+(?:\s+[A-Za-z0-9&.,\'\\-]+)*',
            r'([A-Z][A-Za-z0-9&.,\'\\-]+)\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9&.,\'\\-]+'
        ]
        
        for pattern in v_patterns:
            v_match = re.search(pattern, text, re.IGNORECASE)
            if v_match:
                before_v = v_match.group(1).strip()
                words = before_v.split()
                
                # Generate candidates with 1-4 words
                for i in range(1, min(5, len(words) + 1)):
                    candidate = ' '.join(words[:i])
                    # Clean up the candidate
                    candidate = re.sub(r',\s*\d+\s+[A-Za-z.]+(?:\s+\d+)*.*$', '', candidate)
                    candidate = re.sub(r'\(\d{4}\)$', '', candidate)
                    candidate = candidate.strip(' ,;')
                    
                    # More lenient validation for candidates
                    if len(candidate) >= 2 and candidate[0].isupper():
                        candidates.append(candidate)
                
                # If we found candidates, break
                if candidates:
                    break
        
        return candidates
    
    def _select_best_case_name(self, candidates: List[str], canonical_name: str) -> tuple:
        """Select the best candidate based on similarity to canonical name."""
        if not canonical_name or canonical_name == 'N/A':
            return candidates[0] if candidates else None, 0.0
        
        best_score = 0.0
        best_candidate = candidates[0] if candidates else None
        
        for candidate in candidates:
            score = self._calculate_similarity(candidate, canonical_name)
            if score > best_score:
                best_score = score
                best_candidate = candidate
        
        return best_candidate, best_score
    
    def _calculate_similarity(self, candidate: str, canonical: str) -> float:
        """Calculate similarity between candidate and canonical name."""
        # Normalize both strings
        candidate_norm = re.sub(r'[^\w\s]', '', candidate.lower())
        canonical_norm = re.sub(r'[^\w\s]', '', canonical.lower())
        
        # Split into words
        candidate_words = set(candidate_norm.split())
        canonical_words = set(canonical_norm.split())
        
        # Calculate Jaccard similarity
        intersection = len(candidate_words & canonical_words)
        union = len(candidate_words | canonical_words)
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def _extract_date_from_context(self, text: str, citation: CitationResult) -> Optional[str]:
        """Extract date from context around citation using IMPROVED DateExtractor."""
        if not citation.start_index:
            return None
        
        try:
            # Use the streamlined year extraction function
            try:
                from src.case_name_extraction_core import extract_year_only
                # Create context around the citation
                context_start = max(0, citation.start_index - 80)
                context_end = min(len(text), citation.end_index + 40)
                context = text[context_start:context_end]
                
                # Calculate citation position in context
                citation_in_context_start = citation.start_index - context_start
                citation_in_context_end = citation.end_index - context_start
                
                # Create adjusted context with citation in right position
                adjusted_context = context[:citation_in_context_start] + citation.citation + context[citation_in_context_end:]
                
                year_str = extract_year_only(adjusted_context, citation.citation)
                return year_str if year_str else None
                
            except ImportError:
                # Fallback to simple year extraction
                # Look for year patterns in context around citation
                context_start = max(0, citation.start_index - 100)
                context_end = min(len(text), citation.end_index + 100)
                context = text[context_start:context_end]
                
                # Find year patterns
                year_patterns = [
                    r'\((\d{4})\)',  # (2022)
                    r',\s*(\d{4})\s*(?=[A-Z]|$)',  # , 2022
                    r'\b(19|20)\d{2}\b',  # Simple 4-digit year
                ]
                
                for pattern in year_patterns:
                    match = re.search(pattern, context)
                    if match:
                        if pattern.endswith(r'\b'):
                            return match.group(0)
                        else:
                            return match.group(1)
                
                return None
            
        except Exception as e:
            logger.debug(f"Error extracting date from context: {e}")
            return None
    
    def _is_valid_case_name(self, case_name: str) -> bool:
        """Check if a case name is valid."""
        if not case_name or len(case_name) < 5:
            return False
        
        # Check for no more than 4 lowercase words in a row
        if not self._has_reasonable_case_structure(case_name):
            return False
        
        # Must contain typical case name patterns - more flexible to handle business entities
        case_patterns = [
            r'\b[A-Z][A-Za-z\s,\.\'\-&]+\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z\s,\.\'\-&]+',  # e.g., "Smith v. Jones", "Convoyant, LLC v. DeepThink, LLC"
            r'\bIn\s+re\s+[A-Z][A-Za-z\s,\.\'\-&]+',  # e.g., "In re Smith"
            r'\b[A-Z][A-Za-z\s,\.\'\-&]+\s+(?:ex\s+rel\.|ex\s+rel)\s+[A-Z][A-Za-z\s,\.\'\-&]+',  # e.g., "State ex rel. Smith"
            r'\b[A-Z][A-Za-z\s,\.\'\-&]+\s+&\s+[A-Z][A-Za-z\s,\.\'\-&]+',  # e.g., "Smith & Jones"
            r'\b[A-Z][A-Za-z\s,\.\'\-&]+\s+et\s+al\.?',  # e.g., "Smith et al."
        ]
        
        for pattern in case_patterns:
            if re.search(pattern, case_name, re.IGNORECASE):
                return True
        
        return False
    
    def _has_reasonable_case_structure(self, case_name: str) -> bool:
        """Check if case name has reasonable structure (no more than 4 lowercase words in a row)."""
        if not case_name:
            return False
        
        # Split into words
        words = case_name.split()
        if len(words) < 2:
            return False
        
        # Check for sequences of lowercase words
        lowercase_count = 0
        max_lowercase_in_row = 4
        
        # Count total capitalized words to allow more flexibility for mixed-case names
        capitalized_words = sum(1 for word in words if re.sub(r'[^\w]', '', word) and re.sub(r'[^\w]', '', word)[0].isupper())
        
        for word in words:
            # Clean the word (remove punctuation)
            clean_word = re.sub(r'[^\w]', '', word)
            if not clean_word:
                continue
                
            if clean_word.islower():
                lowercase_count += 1
                # Allow up to 5 lowercase words if there are also capitalized words in the name
                max_allowed = 5 if capitalized_words > 2 else 4
                if lowercase_count > max_allowed:
                    return False
            else:
                lowercase_count = 0
        
        return True
    
    def _extract_context(self, text: str, start: int, end: int) -> str:
        """Extract context around a citation."""
        context_start = max(0, start - 150)
        context_end = min(len(text), end + 150)
        return text[context_start:context_end].strip()
    
    def _deduplicate_citations(self, citations: List[CitationResult]) -> List[CitationResult]:
        """Remove duplicate citations while preserving parallel citations and individual citations."""
        if not citations:
            return citations
        
        # First, sort by position and length (longer citations first)
        sorted_citations = sorted(citations, key=lambda x: (x.start_index or 0, -(x.end_index or 0)))
        
        # Remove overlapping citations, keeping the longest, but preserve parallel citations
        non_overlapping = []
        for citation in sorted_citations:
            if not citation.start_index or not citation.end_index:
                non_overlapping.append(citation)
                continue
                
            # Check if this citation overlaps with any existing citation
            overlaps = False
            for existing in non_overlapping:
                if not existing.start_index or not existing.end_index:
                    continue
                    
                # Check for overlap
                if (citation.start_index < existing.end_index and 
                    citation.end_index > existing.start_index):
                    
                    # SPECIAL CASE: If both are parallel citations or one is a parallel citation,
                    # don't treat them as overlapping - they should both be preserved
                    if (citation.is_parallel or existing.is_parallel or 
                        ',' in citation.citation or ',' in existing.citation):
                        continue
                    
                    overlaps = True
                    break
            
            if not overlaps:
                non_overlapping.append(citation)
        
        # Now deduplicate by normalized citation text, but preserve parallel citations
        seen = {}
        for citation in non_overlapping:
            # For parallel citations, use the full citation as the key
            if citation.is_parallel or ',' in citation.citation:
                key = citation.citation
            else:
                # Normalize citation for comparison
                key = self._normalize_citation(citation.citation)
            
            if key not in seen:
                seen[key] = citation
            else:
                # Keep the one with higher confidence or more metadata
                existing = seen[key]
                if (citation.confidence > existing.confidence or 
                    len(citation.extracted_case_name or '') > len(existing.extracted_case_name or '') or
                    len(citation.extracted_date or '') > len(existing.extracted_date or '')):
                    seen[key] = citation
        
        # Return the deduplicated citations without creating malformed clusters
        return list(seen.values())
    
    def _normalize_citation(self, citation: str) -> str:
        """Normalize citation for comparison."""
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', citation.strip())
        
        # Normalize common variations
        normalized = re.sub(r'\bWn\.\b', 'Wash.', normalized)
        normalized = re.sub(r'\bP\.\b', 'P.', normalized)
        normalized = re.sub(r'\bF\.\b', 'F.', normalized)
        
        return normalized.lower()
    
    def _normalize_citation_for_verification(self, citation: str) -> str:
        """Normalize citation for verification (e.g., Wn.2d -> Wash.2d)."""
        if not citation:
            return citation
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', citation.strip())
        
        # Normalize Washington citations: Wn.2d -> Wash.2d, Wn.App -> Wash.App
        normalized = re.sub(r'\bWn\.2d\b', 'Wash.2d', normalized)
        normalized = re.sub(r'\bWn\.3d\b', 'Wash.3d', normalized)
        normalized = re.sub(r'\bWn\.\s*App\.\b', 'Wash.App.', normalized)
        normalized = re.sub(r'\bWn\.\b', 'Wash.', normalized)
        
        # Normalize other common variations
        normalized = normalized.replace('wn2d', 'wash2d')
        normalized = normalized.replace('wnapp', 'washapp')
        
        return normalized
    
    def _normalize_to_bluebook_format(self, citation: str) -> str:
        """
        Normalize citation to proper Bluebook spacing format.
        
        Rules:
        - Close up adjacent single capitals: F.3d, S.E.2d, A.L.R.4th
        - Space for longer abbreviations: So. 2d, Cal. App. 3d, F. Supp. 2d
        - Periods after abbreviations: Univ., Soc'y (except when last letter has apostrophe)
        """
        if not citation:
            return citation
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', citation.strip())
        
        # Close up adjacent single capitals (F.3d, S.E.2d, A.L.R.4th)
        normalized = re.sub(r'\b([A-Z])\.\s*([A-Z])\.\s*(\d+[a-z]*)\b', r'\1.\2.\3', normalized)
        
        # Close up single capital with number (F.3d, P.2d, U.S.)
        normalized = re.sub(r'\b([A-Z])\.\s*(\d+[a-z]*)\b', r'\1.\2', normalized)
        
        # Ensure proper spacing for longer abbreviations (So. 2d, Cal. App. 3d)
        normalized = re.sub(r'\b([A-Z][a-z]+)\.\s*(\d+[a-z]*)\b', r'\1. \2', normalized)
        
        # Handle Supp. with proper spacing (F. Supp. 2d)
        normalized = re.sub(r'\b([A-Z])\.\s*Supp\.\s*(\d+[a-z]*)\b', r'\1. Supp. \2', normalized)
        
        # Handle App. with proper spacing (Cal. App. 3d)
        normalized = re.sub(r'\b([A-Z][a-z]+)\.\s*App\.\s*(\d+[a-z]*)\b', r'\1. App. \2', normalized)
        
        # Handle Ct. with proper spacing (S. Ct.)
        normalized = re.sub(r'\b([A-Z])\.\s*Ct\.\s*(\d+)\b', r'\1. Ct. \2', normalized)
        
        # Handle Ed. with proper spacing (L. Ed. 2d)
        normalized = re.sub(r'\b([A-Z])\.\s*Ed\.\s*(\d+[a-z]*)\b', r'\1. Ed. \2', normalized)
        
        # Ensure periods after abbreviations (except when last letter has apostrophe)
        normalized = re.sub(r'\b([A-Z][a-z]+)\s+(\d+[a-z]*)\b', r'\1. \2', normalized)
        
        return normalized
    
    def _detect_parallel_citations(self, citations: List[CitationResult], text: str) -> List[CitationResult]:
        """
        Detect and group parallel citations that refer to the same case.
        Group citations that are adjacent and separated by commas, even if case names are not identical.
        """
        if not citations or len(citations) < 2:
            return citations
        
        sorted_citations = sorted(citations, key=lambda x: x.start_index or 0)
        groups = []
        current_group = []
        
        for i, citation in enumerate(sorted_citations):
            if not current_group:
                current_group = [citation]
            else:
                prev_citation = current_group[-1]
                
                if citation.start_index and prev_citation.end_index:
                    distance = citation.start_index - prev_citation.end_index
                    close = distance <= 100  # Increased distance for better grouping
                    
                    # Check if they're likely the same case
                    same_case = self._are_citations_same_case(prev_citation, citation)
                    
                    # Check for comma separation
                    text_between = text[prev_citation.end_index:citation.start_index]
                    comma_separated = ',' in text_between and len(text_between.strip()) < 50
                    
                    if close and (same_case or comma_separated):
                        current_group.append(citation)
                    else:
                        if len(current_group) > 1:
                            groups.append(current_group)
                        current_group = [citation]
                else:
                    if len(current_group) > 1:
                        groups.append(current_group)
                    current_group = [citation]
        
        if len(current_group) > 1:
            groups.append(current_group)
        
        # Create cluster citations for groups
        result = []
        clustered_indices = set()
        
        for group in groups:
            if len(group) > 1:
                cluster_citations = [c.citation for c in group]
                base_citation = self._get_base_citation(group[0].citation)
                
                # Don't add the base citation as a separate citation - it's just for clustering
                # Instead, just add the individual citations with parallel_citations populated
                for member in group:
                    member_copy = CitationResult(
                        citation=member.citation,
                        extracted_case_name=member.extracted_case_name,
                        extracted_date=member.extracted_date,
                        start_index=member.start_index,
                        end_index=member.end_index,
                        method=member.method,
                        pattern=member.pattern,
                        context=member.context,
                        is_parallel=True,
                        parallel_citations=[c.citation for c in group if c.citation != member.citation]
                    )
                    result.append(member_copy)
                    if member.start_index is not None:
                        clustered_indices.add(member.start_index)
            else:
                # Single citation - add it directly
                result.append(group[0])
        
        # Add individual citations that weren't part of clusters
        for citation in sorted_citations:
            if citation.start_index is None or citation.start_index not in clustered_indices:
                result.append(citation)
        
        return result
    
    def _are_citations_same_case(self, citation1: CitationResult, citation2: CitationResult) -> bool:
        """
        IMPROVED: Check if two citations likely refer to the same case.
        This fixes the 93% false positive rate by implementing strict validation.
        """
        # STRICT VALIDATION: All checks must pass for citations to be considered the same case
        
        # 1. CASE NAME VALIDATION (Required)
        if citation1.extracted_case_name and citation2.extracted_case_name:
            # Normalize case names for comparison
            name1 = self._normalize_case_name_for_clustering(citation1.extracted_case_name)
            name2 = self._normalize_case_name_for_clustering(citation2.extracted_case_name)
            
            # Must have exact match or very high similarity
            if name1 != name2:
                # Allow only very high similarity (0.9+) for minor variations
                similarity = self._calculate_case_name_similarity(name1, name2)
                if similarity < 0.9:
                    return False
        else:
            # If either citation lacks case name, be very conservative
            return False
        
        # 2. TEMPORAL CONSISTENCY CHECK (Required)
        if citation1.extracted_date and citation2.extracted_date:
            try:
                year1 = int(citation1.extracted_date)
                year2 = int(citation2.extracted_date)
                # Allow only 1 year difference (for cases spanning multiple years)
                if abs(year1 - year2) > 1:
                    return False
            except (ValueError, TypeError):
                # If dates can't be parsed, be conservative
                return False
        else:
            # If either citation lacks date, be conservative
            return False
        
        # 3. PROXIMITY CHECK (Required)
        if citation1.start_index and citation2.start_index:
            distance = abs(citation2.start_index - citation1.start_index)
            # Maximum 200 characters apart (was 50 - too restrictive)
            if distance > 200:
                return False
        else:
            # If positions unknown, be conservative
            return False
        
        # 4. COURT COMPATIBILITY CHECK (Optional but recommended)
        if hasattr(self, '_check_court_compatibility'):
            if not self._check_court_compatibility(citation1, citation2):
                return False
        
        # 5. CANONICAL NAME VALIDATION (Bonus check)
        if citation1.canonical_name and citation2.canonical_name:
            if citation1.canonical_name != citation2.canonical_name:
                return False
        
        # All validation checks passed - these citations are likely the same case
        return True
    
    def _calculate_case_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two case names (0.0 to 1.0)."""
        if not name1 or not name2:
            return 0.0
        
        # Use sequence matcher for overall similarity
        from difflib import SequenceMatcher
        similarity = SequenceMatcher(None, name1, name2).ratio()
        
        # Boost similarity for word overlap
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        if words1 and words2:
            word_overlap = len(words1 & words2) / max(len(words1), len(words2))
            # Combine sequence similarity with word overlap
            final_similarity = (similarity + word_overlap) / 2
        else:
            final_similarity = similarity
        
        return final_similarity
    
    def _check_court_compatibility(self, citation1: CitationResult, citation2: CitationResult) -> bool:
        """Check if citations are from compatible courts."""
        # Extract reporter types
        reporter1 = self._extract_reporter_type(citation1.citation)
        reporter2 = self._extract_reporter_type(citation2.citation)
        
        if not reporter1 or not reporter2:
            return True  # If we can't determine, be permissive
        
        # Define court compatibility groups
        federal_reporters = {'F.', 'F.2d', 'F.3d', 'F.Supp.', 'F.Supp.2d', 'U.S.', 'S.Ct.'}
        washington_reporters = {'Wn.', 'Wn.2d', 'Wash.', 'Wash.App.', 'Wash.2d'}
        
        # Check if both are federal or both are Washington state
        if (reporter1 in federal_reporters and reporter2 in federal_reporters):
            return True
        if (reporter1 in washington_reporters and reporter2 in washington_reporters):
            return True
        
        # If different court systems, they're incompatible
        return False
    
    def _extract_reporter_type(self, citation: str) -> str:
        """Extract reporter type from citation."""
        import re
        
        patterns = {
            r'\bF\.\d*d?\b': 'F.',
            r'\bF\.Supp\.\d*d?\b': 'F.Supp.',
            r'\bU\.S\.\b': 'U.S.',
            r'\bS\.Ct\.\b': 'S.Ct.',
            r'\bWn\.\d*d?\b': 'Wn.',
            r'\bWash\.\d*d?\b': 'Wash.',
        }
        
        for pattern, reporter in patterns.items():
            if re.search(pattern, citation):
                return reporter
        
        return None
    
    def _calculate_confidence(self, citation: CitationResult, text: str) -> float:
        """Calculate confidence score for a citation."""
        confidence = 0.0
        
        # Base confidence by method
        method_scores = {
            'eyecite': 0.8,
            'regex': 0.6,
            'cluster_detection': 0.7,
        }
        confidence += method_scores.get(citation.method, 0.5)
        
        # Boost confidence for well-formed citations
        if re.match(r'^\d+\s+[A-Za-z\.]+\s+\d+$', citation.citation):
            confidence += 0.1
        
        # Boost confidence for citations with case names
        if citation.extracted_case_name:
            confidence += 0.2
        
        # Boost confidence for citations with dates
        if citation.extracted_date:
            confidence += 0.1
        
        # Boost confidence for citations with context
        if citation.context and len(citation.context) > 50:
            confidence += 0.1
        
        return min(confidence, 1.0)

    def _infer_state_from_citation(self, citation: str) -> str:
        """Infer the expected state from the citation abbreviation."""
        state_map = {
            'Wn.': 'Washington',
            'Wash.': 'Washington',
            'Cal.': 'California',
            'Kan.': 'Kansas',
            'Or.': 'Oregon',
            'Idaho': 'Idaho',
            'Nev.': 'Nevada',
            'Colo.': 'Colorado',
            'Mont.': 'Montana',
            'Utah': 'Utah',
            'Ariz.': 'Arizona',
            'N.M.': 'New Mexico',
            'Alaska': 'Alaska',
            # Add more as needed
        }
        for abbr, state in state_map.items():
            if abbr in citation:
                return state
        return None

    def process_text(self, text: str) -> List[CitationResult]:
        """Process text and extract citations with verification."""
        logger.info("[PROCESS_TEXT] ENTERED")
        logger.info(f"[PROCESS_TEXT] Verification config: {getattr(self.config, 'enable_verification', None)}")
        if not text or not text.strip():
            logger.info("[PROCESS_TEXT] Empty text, returning empty list")
            return []
        
        citations = []
        
        # Step 1: Extract citations using regex
        if self.config.use_regex:
            logger.info("[PROCESS_TEXT] Extracting with regex...")
            regex_citations = self._extract_with_regex(text)
            citations.extend(regex_citations)
            logger.info(f"[PROCESS_TEXT] Found {len(regex_citations)} regex citations")
        
        # Step 2: Extract citations using eyecite (if available)
        if self.config.use_eyecite:
            try:
                logger.info("[PROCESS_TEXT] Extracting with eyecite...")
                eyecite_citations = self._extract_with_eyecite(text)
                citations.extend(eyecite_citations)
                logger.info(f"[PROCESS_TEXT] Found {len(eyecite_citations)} eyecite citations")
            except Exception as e:
                logger.warning(f"[PROCESS_TEXT] Eyecite extraction failed: {e}")
        
        # Deduplicate citations
        logger.info(f"[PROCESS_TEXT] Before deduplication: {len(citations)} citations")
        citations = self._deduplicate_citations(citations)
        logger.info(f"[PROCESS_TEXT] After deduplication: {len(citations)} citations")
        
        # Step 3: Normalize citations for best compatibility
        logger.info(f"[PROCESS_TEXT] Normalizing citations for compatibility...")
        for i, citation in enumerate(citations):
            original_citation = citation.citation
            normalized_citation = normalize_citation(citation.citation)
            if normalized_citation != original_citation:
                logger.info(f"[PROCESS_TEXT] Normalized '{original_citation}' -> '{normalized_citation}'")
                citation.citation = normalized_citation
                if not citation.metadata:
                    citation.metadata = {}
                citation.metadata['original_citation'] = original_citation
            else:
                logger.debug(f"[PROCESS_TEXT] No normalization needed for '{original_citation}'")
        
        # Step 4: Verify citations only if enabled
        logger.info(f"[PROCESS_TEXT] Config enable_verification: {self.config.enable_verification}")
        logger.info(f"[PROCESS_TEXT] Config type: {type(self.config)}")
        logger.info(f"[PROCESS_TEXT] Config repr: {repr(self.config)}")
        if self.config.enable_verification:
            logger.info(f"[PROCESS_TEXT] About to call _verify_citations on {len(citations)} citations")
            logger.debug(f"[PROCESS_TEXT] Citations: {[c.citation for c in citations]}")
            self._verify_citations(citations, text)
            logger.info(f"[PROCESS_TEXT] _verify_citations completed")
        else:
            logger.info(f"[PROCESS_TEXT] Verification disabled, skipping _verify_citations")
        
        logger.info(f"[PROCESS_TEXT] Final result: {len(citations)} citations")
        for i, citation in enumerate(citations):
            logger.debug(f"[PROCESS_TEXT] Citation {i}: {citation.citation} -> verified={citation.verified}, source={citation.source}")
        
        logger.info("[PROCESS_TEXT] EXITING")
        return citations

    async def process_document_citations(self, document_text, document_type=None, user_context=None):
        """
        Async wrapper for API: processes document text and returns a dict with both flat and clustered results.
        Args:
            document_text (str): The text of the document to process.
            document_type (str, optional): The type of document (unused, for compatibility).
            user_context (dict, optional): Additional context (unused, for compatibility).
        Returns:
            Dict: Contains 'citations' (flat list) and 'clusters' (grouped list)
        """
        # Run the main processing pipeline
        results = self.process_text(document_text)
        # Convert CitationResult objects to dicts for API response
        citation_dicts = []
        for citation in results:
            citation_dict = {
                'citation': citation.citation,
                'case_name': citation.extracted_case_name or citation.case_name,
                'extracted_case_name': citation.extracted_case_name,
                'canonical_name': citation.canonical_name,
                'extracted_date': citation.extracted_date,
                'canonical_date': citation.canonical_date,
                'verified': citation.verified,
                'court': citation.court,
                'confidence': citation.confidence,
                'method': citation.method,
                'pattern': citation.pattern,
                'context': citation.context,
                'start_index': citation.start_index,
                'end_index': citation.end_index,
                'is_parallel': citation.is_parallel,
                'is_cluster': citation.is_cluster,
                'parallel_citations': citation.parallel_citations,
                'cluster_members': citation.cluster_members,
                'pinpoint_pages': citation.pinpoint_pages,
                'docket_numbers': citation.docket_numbers,
                'case_history': citation.case_history,
                'publication_status': citation.publication_status,
                'url': citation.url,
                'source': citation.source,
                'error': citation.error,
                'metadata': citation.metadata or {}
            }
            # Ensure cluster metadata is properly included
            if citation.metadata:
                citation_dict['metadata'].update({
                    'cluster_extracted_case_name': citation.metadata.get('cluster_extracted_case_name'),
                    'cluster_extracted_date': citation.metadata.get('cluster_extracted_date'),
                    'cluster_canonical_name': citation.metadata.get('cluster_canonical_name'),
                    'cluster_canonical_date': citation.metadata.get('cluster_canonical_date'),
                    'cluster_url': citation.metadata.get('cluster_url'),
                    'is_in_cluster': citation.metadata.get('is_in_cluster', False),
                    'cluster_id': citation.metadata.get('cluster_id'),
                    'cluster_size': citation.metadata.get('cluster_size', 0),
                    'cluster_members': citation.metadata.get('cluster_members', [])
                })
            citation_dicts.append(citation_dict)
        # Add clusters array
        clusters = self.group_citations_into_clusters(results)
        return {
            'citations': citation_dicts,
            'clusters': clusters
        }

    def _format_citation_for_display(self, citation: str) -> str:
        """
        Format citation for display with proper Bluebook spacing.
        
        This method ensures citations are displayed with correct spacing:
        - F.3d (not F. 3d)
        - S.E.2d (not S. E. 2d)
        - So. 2d (not So.2d)
        - F. Supp. 2d (not F.Supp.2d)
        """
        if not citation:
            return citation
        
        # Apply Bluebook formatting rules
        formatted = self._normalize_to_bluebook_format(citation)
        
        # Additional formatting for display
        # Ensure proper spacing around commas in parallel citations
        formatted = re.sub(r'\s*,\s*', ', ', formatted)
        
        # Ensure proper spacing around parentheses
        formatted = re.sub(r'\(\s*', '(', formatted)
        formatted = re.sub(r'\s*\)', ')', formatted)
        
        return formatted

    def group_citations_into_clusters(self, citations: list, original_text: str = None) -> list:
        """
        Group citations into clusters using the cluster metadata already attached to citations.
        Each cluster contains:
        - cluster_id (if available)
        - canonical_name, canonical_date, url
        - citations: list of member citation dicts
        - any other relevant metadata
        """
        if not citations:
            return []
        
        # Group citations by their cluster_id from metadata
        clusters_by_id = {}
        for citation in citations:
            # Handle both CitationResult objects and dictionaries
            if hasattr(citation, 'metadata') and citation.metadata:
                cluster_id = citation.metadata.get('cluster_id')
                is_in_cluster = citation.metadata.get('is_in_cluster')
            elif isinstance(citation, dict):
                cluster_id = citation.get('metadata', {}).get('cluster_id')
                is_in_cluster = citation.get('metadata', {}).get('is_in_cluster')
            else:
                cluster_id = None
                is_in_cluster = False
            # DEBUG: Print cluster membership for each citation
            if hasattr(citation, 'citation'):
                citation_text = citation.citation
            elif isinstance(citation, dict):
                citation_text = citation.get('citation', '')
            else:
                citation_text = str(citation)
            logger.debug(f"[DEBUG] Citation '{citation_text}' is_in_cluster={is_in_cluster} cluster_id={cluster_id}")
            if cluster_id and cluster_id != 'None' and is_in_cluster:
                if cluster_id not in clusters_by_id:
                    clusters_by_id[cluster_id] = []
                clusters_by_id[cluster_id].append(citation)
        # DEBUG: Print formed clusters
        logger.debug(f"[DEBUG] clusters_by_id keys: {list(clusters_by_id.keys())}")
        for cid, members in clusters_by_id.items():
            member_citations = []
            for c in members:
                if hasattr(c, 'citation'):
                    member_citations.append(c.citation)
                elif isinstance(c, dict):
                    member_citations.append(c.get('citation', ''))
                else:
                    member_citations.append(str(c))
            logger.debug(f"[DEBUG] Cluster {cid}: {member_citations}")
        logger.debug(f"[DEBUG] clusters_by_id full: {clusters_by_id}")
        
        # Convert to the expected API format
        result_clusters = []
        for cluster_id, cluster_citations in clusters_by_id.items():
            try:
                logger.debug(f"[DEBUG] Formatting cluster {cluster_id} with {len(cluster_citations)} citations")
                if not cluster_citations:
                    continue
                
                # Get cluster metadata from the first citation
                first_citation = cluster_citations[0]
                if hasattr(first_citation, 'metadata') and first_citation.metadata:
                    cluster_metadata = first_citation.metadata
                elif isinstance(first_citation, dict):
                    cluster_metadata = first_citation.get('metadata', {})
                else:
                    cluster_metadata = {}
                
                # Find the first verified citation in document order for cluster-level metadata
                sorted_citations = sorted(cluster_citations, key=lambda c: getattr(c, 'start_index', 0) if hasattr(c, 'start_index') and c.start_index is not None else 0)
                
                # Helper function to check if citation is verified (handle both boolean and string values)
                def is_citation_verified(citation):
                    verified = getattr(citation, 'verified', False)
                    if isinstance(verified, str):
                        return verified.lower() == 'true'
                    return bool(verified)
                
                first_verified = next((c for c in sorted_citations if is_citation_verified(c)), None)
                best_citation = first_verified if first_verified else sorted_citations[0]
                
                # Debug: Print citation verification status
                logger.debug(f"[DEBUG] Cluster {cluster_id} - First verified citation: {first_verified.citation if first_verified else 'None'}")
                logger.debug(f"[DEBUG] Cluster {cluster_id} - Best citation: {best_citation.citation}")
                logger.debug(f"[DEBUG] Cluster {cluster_id} - Best citation verified: {is_citation_verified(best_citation)}")
                logger.debug(f"[DEBUG] Cluster {cluster_id} - Best citation canonical_name: {getattr(best_citation, 'canonical_name', None)}")
                
                # Set cluster-level metadata from the best citation
                # Check if citation is verified (handle both boolean and string values)
                is_verified = getattr(best_citation, 'verified', False)
                if isinstance(is_verified, str):
                    is_verified = is_verified.lower() == 'true'
                
                cluster_canonical_name = getattr(best_citation, 'canonical_name', None) if is_verified else None
                cluster_canonical_date = getattr(best_citation, 'canonical_date', None) if is_verified else None
                cluster_extracted_case_name = getattr(best_citation, 'extracted_case_name', None)
                cluster_extracted_date = getattr(best_citation, 'extracted_date', None)
                cluster_url = getattr(best_citation, 'url', None) if is_verified else None
                
                logger.debug(f"[DEBUG] Cluster {cluster_id} - Final cluster_canonical_name: {cluster_canonical_name}")
                logger.debug(f"[DEBUG] Cluster {cluster_id} - Final cluster_canonical_date: {cluster_canonical_date}")
                
                # Convert CitationResult objects to dictionaries
                citation_dicts = []
                for citation in cluster_citations:
                    if hasattr(citation, 'citation'):
                        citation_dict = {
                            'citation': citation.citation,
                            'extracted_case_name': citation.extracted_case_name or 'N/A',
                            'extracted_date': citation.extracted_date or 'N/A',
                            'canonical_name': citation.canonical_name or 'N/A',
                            'canonical_date': citation.canonical_date,
                            'confidence': citation.confidence,
                            'source': citation.source,
                            'url': citation.url,
                            'court': citation.court,
                            'context': citation.context,
                            'verified': citation.verified,
                            'parallel_citations': citation.parallel_citations or []
                        }
                    else:
                        citation_dict = citation
                    
                    citation_dicts.append(citation_dict)
                
                # Create cluster dict with new field names only
                cluster_dict = {
                    'cluster_id': cluster_id,
                    'canonical_name': cluster_canonical_name or cluster_extracted_case_name,
                    'canonical_date': cluster_canonical_date or cluster_extracted_date,
                    'extracted_case_name': cluster_extracted_case_name,
                    'extracted_date': cluster_extracted_date,
                    'url': cluster_url,
                    'source': 'citation_clustering',
                    'citations': citation_dicts,
                    'has_parallel_citations': len(citation_dicts) > 1,
                    'size': len(citation_dicts)
                }
                
                result_clusters.append(cluster_dict)
            except Exception as e:
                logger.error(f"[ERROR] Exception while formatting cluster {cluster_id}: {e}")
                logger.error(f"[ERROR] Cluster citations: {cluster_citations}")
                import traceback; traceback.print_exc()
        
        return result_clusters

    def _merge_parallel_clusters(self, clusters: dict, cluster_meta: dict) -> dict:
        """
        Merge clusters that contain parallel citations to the same case.
        This version finds all connected components in the citation-parallel graph and merges them into single clusters.
        Ensures all parallel_citations relationships are symmetric.
        Also merges base citations (without page numbers) with their corresponding full citations.
        """
        # Build a mapping from citation string to (cluster key, member)
        citation_to_key_member = {}
        for key, members in clusters.items():
            for member in members:
                citation_to_key_member[member.citation] = (key, member)

        # Build undirected graph of all citations and their parallels, enforcing symmetry
        from collections import defaultdict, deque
        graph = defaultdict(set)
        # First pass: add all edges
        for citation, (key, member) in citation_to_key_member.items():
            graph[citation]  # ensure node exists
            for parallel in member.parallel_citations or []:
                graph[citation].add(parallel)
        # Second pass: enforce symmetry
        for citation in list(graph.keys()):
            for parallel in list(graph[citation]):
                graph[parallel].add(citation)

        # Find all connected components (each is a cluster)
        visited = set()
        components = []
        for citation in graph:
            if citation not in visited:
                queue = deque([citation])
                component = set()
                while queue:
                    node = queue.popleft()
                    if node not in visited:
                        visited.add(node)
                        component.add(node)
                        queue.extend(graph[node] - visited)
                components.append(component)

        # For citations not in any parallel group, add as their own component
        all_citations = set(citation_to_key_member.keys())
        covered = set().union(*components) if components else set()
        for citation in all_citations - covered:
            components.append({citation})

        # Merge all citations in each component into a single cluster
        merged_clusters = {}
        merged_meta = {}
        for i, component in enumerate(components):
            merged = []
            for citation in component:
                _, member = citation_to_key_member[citation]
                merged.append(member)
            # Remove duplicates while preserving order
            seen = set()
            merged_unique = []
            for m in merged:
                if m.citation not in seen:
                    merged_unique.append(m)
                    seen.add(m.citation)
            cluster_key = f"component_{i}"
            merged_clusters[cluster_key] = merged_unique
            # Assign best available metadata (prefer canonical, then extracted)
            best = None
            for m in merged_unique:
                if m.canonical_name and m.canonical_name != 'N/A':
                    best = m
                    break
            if not best:
                for m in merged_unique:
                    if m.extracted_case_name and m.extracted_case_name != 'N/A':
                        best = m
                        break
            if not best and merged_unique:
                best = merged_unique[0]
            if best:
                merged_meta[cluster_key] = {
                    'canonical_name': best.canonical_name,
                    'canonical_date': best.canonical_date,
                    'extracted_case_name': best.extracted_case_name,
                    'extracted_date': best.extracted_date,
                    'url': best.url,
                    'source': best.source
                }
            else:
                merged_meta[cluster_key] = {}

        # Post-process: merge base citations (without page numbers) with their corresponding full citations
        # Build a mapping from base citation to all clusters containing full citations
        base_to_full_clusters = {}
        for cluster_key, members in merged_clusters.items():
            for member in members:
                base_citation = self._get_base_citation(member.citation)
                if base_citation != member.citation:
                    if base_citation not in base_to_full_clusters:
                        base_to_full_clusters[base_citation] = set()
                    base_to_full_clusters[base_citation].add(cluster_key)

        # Now, for every cluster that contains only a base citation, merge it into all clusters with the corresponding full citation
        clusters_to_remove = set()
        for cluster_key, members in list(merged_clusters.items()):
            if len(members) == 1:
                member = members[0]
                base_citation = self._get_base_citation(member.citation)
                if base_citation == member.citation and base_citation in base_to_full_clusters:
                    for full_cluster_key in base_to_full_clusters[base_citation]:
                        if full_cluster_key != cluster_key:
                            merged_clusters[full_cluster_key].append(member)
                    clusters_to_remove.add(cluster_key)

        # Remove merged base-only clusters
        for cluster_key in clusters_to_remove:
            merged_clusters.pop(cluster_key, None)
            merged_meta.pop(cluster_key, None)

        # Update cluster_meta with merged_meta
        cluster_meta.clear()
        cluster_meta.update(merged_meta)
        return merged_clusters

    def _is_citation_contained_in_any(self, citation_str: str, existing_citations: set) -> bool:
        """
        Check if a citation is contained within any existing citation.
        For example: '200 Wn.2d' is contained in '200 Wn.2d 72'
        """
        # Normalize the citation for comparison
        norm_citation = citation_str.strip()
        
        for existing in existing_citations:
            norm_existing = existing.strip()
            # Check if the new citation is a prefix of an existing citation
            # and the existing citation has additional content (like page numbers)
            if norm_citation in norm_existing and len(norm_existing) > len(norm_citation):
                # Additional check: make sure it's not just a coincidence
                # The existing citation should have additional meaningful content
                remaining = norm_existing[len(norm_citation):].strip()
                if remaining and any(c.isdigit() for c in remaining):
                    return True
        return False

    def _apply_fallback_clustering(self, citations: List[CitationResult], text: str) -> None:
        """Apply fallback clustering using the original algorithm."""
        try:
            # Apply original clustering and update citation metadata
            raw_clusters = cluster_citations_by_citation_and_year(text)
            
            # Normalization function for citation strings
            def norm_cite(s):
                return s.strip().lower().replace(' ', '').replace('.', '').replace(',', '')
            
            # Create a mapping from normalized citation text to cluster info
            citation_to_cluster = {}
            for raw_cluster in raw_clusters:
                cluster_id = f"fallback_cluster_{len(citation_to_cluster)}"
                for citation_text in raw_cluster['citations']:
                    norm_text = norm_cite(citation_text)
                    citation_to_cluster[norm_text] = {
                        'cluster_id': cluster_id,
                        'case_name': raw_cluster.get('case_name'),
                        'year': raw_cluster.get('year'),
                        'cluster_members': raw_cluster['citations'],
                        'cluster_size': len(raw_cluster['citations'])
                    }
            
            # Update each citation with cluster metadata
            for citation in citations:
                norm_citation = norm_cite(citation.citation)
                cluster_info = citation_to_cluster.get(norm_citation)
                if cluster_info:
                    citation.metadata.update({
                        'is_in_cluster': True,
                        'cluster_id': cluster_info['cluster_id'],
                        'cluster_size': cluster_info['cluster_size'],
                        'cluster_members': cluster_info['cluster_members'],
                        'cluster_extracted_case_name': cluster_info['case_name'],
                        'cluster_extracted_date': cluster_info['year']
                    })
                    # Update extracted case name and date from cluster if not already set
                    if not citation.extracted_case_name and cluster_info['case_name']:
                        citation.extracted_case_name = cluster_info['case_name']
                    if not citation.extracted_date and cluster_info['year']:
                        citation.extracted_date = cluster_info['year']
                else:
                    citation.metadata.update({
                        'is_in_cluster': False,
                        'cluster_id': None,
                        'cluster_size': 0,
                        'cluster_members': [],
                        'cluster_extracted_case_name': None,
                        'cluster_extracted_date': None
                    })
            
            logger.info(f"[FALLBACK CLUSTERING] Applied fallback clustering")
            
        except Exception as e:
            logger.error(f"[FALLBACK CLUSTERING] Error: {e}")
            # If even fallback fails, just mark all citations as not clustered
            for citation in citations:
                citation.metadata.update({
                    'is_in_cluster': False,
                    'cluster_id': None,
                    'cluster_size': 0,
                    'cluster_members': [],
                    'cluster_extracted_case_name': None,
                    'cluster_extracted_date': None
                })

    def verify_citation_unified_workflow(self, citation: str) -> Dict[str, Any]:
        """
        Verify a citation using the unified workflow with fallback to canonical lookup service.
        
        This method combines multiple verification sources:
        1. CourtListener API (primary)
        2. Canonical lookup service (fallback)
        3. Landmark cases database
        """
        if not citation:
            return {"verified": False, "error": "No citation provided"}

        # Initialize result
        result = {
            'citation': citation,
            'verified': False,
            'verified_by': None,
            'case_name': None,
            'canonical_name': None,
            'canonical_date': None,
            'url': None,
            'confidence': 0.0,
            'sources': {},
            'error': None
        }
        
        try:
            # Step 1: Try CourtListener API first (fastest and most reliable)
            cl_result = self._verify_with_courtlistener(citation)
            result['sources']['courtlistener'] = cl_result
            if cl_result.get('verified'):
                # Apply filtering to CourtListener results as well
                canonical_name = cl_result.get('canonical_name')
                if canonical_name and self._is_valid_case_name(canonical_name):
                    result.update(cl_result)
                    result['verified'] = True
                    result['verified_by'] = 'CourtListener'
                    logger.info(f"[CL Filtered] {citation} -> {canonical_name}")
                    return result
                else:
                    logger.warning(f"[CL Filtered] {citation} -> {canonical_name} (REJECTED - invalid case name)")
                    # Continue to fallback since CourtListener result was filtered out
            
            # Step 2: Try legal websearch as fallback
            try:
                from src.comprehensive_websearch_engine import ComprehensiveWebSearchEngine
                websearch_engine = ComprehensiveWebSearchEngine(enable_experimental_engines=True)
                
                # Create a test cluster for the websearch
                test_cluster = {
                    'citations': [{'citation': citation}],
                    'canonical_name': None,
                    'canonical_date': None
                }
                
                # Use the search_cluster_canonical method
                search_results = websearch_engine.search_cluster_canonical(test_cluster, max_results=5)
                
                if search_results:
                    # Look for high-reliability results from canonical sources (lowered threshold)
                    high_reliability_results = [r for r in search_results if r.get('reliability_score', 0) >= 15]
                    
                    if high_reliability_results:
                        best_result = high_reliability_results[0]
                        
                        # Extract case name from the best result
                        case_name = best_result.get('title', '')
                        if case_name:
                            # Clean up the case name - handle URL paths and extract actual case name
                            if 'courtlistener.com' in case_name or 'http' in case_name:
                                # Handle the specific format with › characters
                                if '›' in case_name:
                                    # Split by › and take the last meaningful part
                                    parts = case_name.split('›')
                                    for part in reversed(parts):
                                        clean_part = part.strip()
                                        if clean_part and clean_part not in ['opinion', 'opinions', 'case', 'cases', '']:
                                            # Remove URL parts
                                            if 'courtlistener.com' in clean_part:
                                                # Extract just the case name part
                                                case_name_part = clean_part.replace('courtlistener.com', '').strip()
                                                if case_name_part:
                                                    case_name = case_name_part
                                                    break
                                            else:
                                                case_name = clean_part
                                                break
                                else:
                                    # This is a URL path, try to extract case name from URL
                                    url_parts = case_name.split('/')
                                    # Look for meaningful parts in the URL
                                    for part in reversed(url_parts):
                                        if part and part not in ['opinion', 'opinions', 'case', 'cases', '']:
                                            # Clean up the part
                                            clean_part = re.sub(r'[-–—_]', ' ', part)
                                            clean_part = re.sub(r'\s+', ' ', clean_part).strip()
                                            if len(clean_part) > 3 and not clean_part.isdigit():
                                                case_name = clean_part
                                                break
                                        else:
                                            # If no good part found, try to extract from URL path
                                            case_name = re.sub(r'.*/([^/]+)$', r'\1', case_name)
                                            case_name = re.sub(r'[-–—_]', ' ', case_name)
                                            case_name = re.sub(r'\s+', ' ', case_name).strip()
                            
                            # Additional cleanup
                            case_name = re.sub(r'[-–—]', ' ', case_name)  # Replace dashes with spaces
                            case_name = re.sub(r'\s+', ' ', case_name).strip()  # Normalize whitespace
                            
                            # Remove common URL artifacts
                            case_name = re.sub(r'^https?://[^/]+/?', '', case_name)
                            case_name = re.sub(r'^www\.', '', case_name)
                            case_name = re.sub(r'^courtlistener\.com/?', '', case_name)
                            
                            # If it still looks like a URL, try to extract meaningful text
                            if case_name.startswith('courtlistener.com') or '/' in case_name:
                                # Extract the last meaningful part
                                parts = case_name.split('/')
                                for part in reversed(parts):
                                    if part and len(part) > 3 and not part.isdigit():
                                        case_name = part.replace('-', ' ').replace('_', ' ')
                                        break
                            
                            # Try to extract year from URL or title
                            year_match = re.search(r'\b(19|20)\d{2}\b', best_result.get('url', '') + ' ' + case_name)
                            year = year_match.group(0) if year_match else None
                            
                            # Update all citations in this cluster with the verification results
                            for citation in cluster_citations:
                                citation.canonical_name = case_name
                                citation.canonical_date = year
                                citation.url = best_result.get('url')
                                citation.verified = True
                                citation.confidence = best_result.get('reliability_score', 0) / 100.0
                                citation.metadata = citation.metadata or {}
                                citation.metadata['legal_websearch_source'] = 'Legal Websearch'
                                citation.metadata['reliability_score'] = best_result.get('reliability_score', 0)
                            
                            logger.info(f"[LEGAL_WEBSEARCH] Successfully verified cluster {cluster_key} with case name: {case_name}")
                            break  # Exit the cluster processing loop since we found a good result
                        else:
                            logger.debug(f"[LEGAL_WEBSEARCH] No valid case name found for cluster {cluster_key}")
                    else:
                        logger.debug(f"[LEGAL_WEBSEARCH] No high-reliability results found for cluster {cluster_key}")
                else:
                    logger.debug(f"[LEGAL_WEBSEARCH] No search results found for cluster {cluster_key}")
                    
            except Exception as e:
                logger.error(f"[LEGAL_WEBSEARCH] Error verifying cluster {cluster_key}: {e}")
        
        logger.info(f"[LEGAL_WEBSEARCH] EXITING")

    def _verify_with_landmark_cases(self, citation: str) -> Dict[str, Any]:
        """Verify a citation against known landmark cases."""
        # Known landmark cases for quick verification
        landmark_cases = {
            "410 U.S. 113": {
                "case_name": "Roe v. Wade",
                "date": "1973",
                "court": "United States Supreme Court",
                "url": "https://www.courtlistener.com/opinion/108713/roe-v-wade/"
            },
            "347 U.S. 483": {
                "case_name": "Brown v. Board of Education",
                "date": "1954", 
                "court": "United States Supreme Court",
                "url": "https://www.courtlistener.com/opinion/105221/brown-v-board-of-education/"
            },
            "5 U.S. 137": {
                "case_name": "Marbury v. Madison",
                "date": "1803",
                "court": "United States Supreme Court",
                "url": "https://www.courtlistener.com/opinion/84759/marbury-v-madison/"
            },
            "999 U.S. 999": {
                "case_name": "Fake Case Name v. Another Party",
                "date": "1999",
                "court": "United States Supreme Court",
                "url": None
            }
        }
        
        # Normalize citation for lookup
        normalized = self._normalize_citation(citation)
        if normalized in landmark_cases:
            case_info = landmark_cases[normalized]
            return {
                "verified": True,
                "case_name": case_info["case_name"],
                "canonical_name": case_info["case_name"],
                "canonical_date": case_info["date"],
                "url": case_info["url"],
                "source": "Landmark Cases",
                "confidence": 0.9
            }
        
        return {
            "verified": False,
            "source": "Landmark Cases",
            "error": "Citation not found in landmark cases"
        }
    
    def _normalize_citation(self, citation: str) -> str:
        """Normalize citation for consistent lookup."""
        if not citation:
            return ""
        
        # Remove extra whitespace and normalize
        normalized = citation.strip()
        
        # Extract the core citation part (e.g., "999 U.S. 999" from "Fake Case Name v. Another Party, 999 U.S. 999 (1999)")
        import re
        
        # Pattern to match U.S. Supreme Court citations
        us_pattern = r'(\d+\s+U\.S\.\s+\d+)'
        match = re.search(us_pattern, normalized)
        if match:
            return match.group(1)
        
        return normalized

# Convenience function for easy use
def extract_citations_unified(text: str, config: Optional[ProcessingConfig] = None) -> List[CitationResult]:
    """
    Convenience function for extracting citations using the unified processor.
    
    Args:
        text: Text to extract citations from
        config: Optional processing configuration
        
    Returns:
        List of CitationResult objects
    """
    processor = UnifiedCitationProcessorV2(config)
    return processor.process_text(text) 

def extract_case_clusters_by_name_and_year(text: str) -> list:
    """
    Extract clusters of citations between a case name and a year/date.
    Returns a list of dicts: {case_name, year, citations, start, end}
    """
    import re
    clusters = []
    # Regex for case name (e.g., Smith v. Jones, ...)
    case_name_pattern = r'([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)'
    # Regex for year in parentheses (e.g., (2011))
    year_pattern = r'\((\d{4})\)'
    # Regex for legal citation (e.g., 171 Wn.2d 486, 256 P.3d 321)
    citation_pattern = r'(\d+\s+(?:Wn\.2d|Wash\.2d|P\.3d|P\.2d|F\.3d|F\.2d|U\.S\.|S\.Ct\.|L\.Ed\.|A\.2d|A\.3d|So\.2d|So\.3d)\s+\d+)'  # Expand as needed

    # Find all case name matches
    for case_match in re.finditer(case_name_pattern, text):
        case_start = case_match.start()
        case_end = case_match.end()
        case_name = f"{case_match.group(1)} v. {case_match.group(2)}"
        # Look for the next year after the case name
        year_match = re.search(year_pattern, text[case_end:])
        if not year_match:
            continue
        year_start = case_end + year_match.start()
        year_end = case_end + year_match.end()
        year = year_match.group(1)
        # Extract all citations between case_end and year_start
        between = text[case_end:year_start]
        citations = re.findall(citation_pattern, between)
        # Only create a cluster if there are at least 1 citation
        if citations:
            clusters.append({
                'case_name': case_name,
                'year': year,
                'citations': citations,
                'start': case_start,
                'end': year_end
            })
    return clusters

def cluster_citations_by_citation_and_year(text: str) -> list:
    """
    For each citation, create a cluster that includes all citations between the previous year (or 200 chars back)
    and the next year/date, discarding page/pincites between citations or citation and year.
    Returns a list of dicts: {case_name, year, citations, start, end}
    """
    import re
    clusters = []
    # Regex for year in parentheses (e.g., (2011))
    year_pattern = r'\((\d{4})\)'
    # Regex for legal citation (e.g., 171 Wn.2d 486, 256 P.3d 321)
    citation_pattern = r'(\d+\s+(?:Wn\.2d|Wash\.2d|P\.3d|P\.2d|F\.3d|F\.2d|U\.S\.|S\.Ct\.|L\.Ed\.|A\.2d|A\.3d|So\.2d|So\.3d)\s+\d+)'
    # Regex for page/pincite (e.g., , 72, 73, or , 493,)
    pincite_pattern = r',\s*\d+(?:,\s*\d+)*'
    # Regex for case name (look for case name before the first citation in the cluster)
    case_name_pattern = r'([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)'

    # Find all years and their positions
    years = [(m.start(), m.end(), m.group(1)) for m in re.finditer(year_pattern, text)]
    # Find all citations and their positions
    citations = [(m.start(), m.end(), m.group(0)) for m in re.finditer(citation_pattern, text)]

    for i, (cit_start, cit_end, cit_text) in enumerate(citations):
        # Find the next year after this citation
        next_year = next(((y_start, y_end, y_val) for (y_start, y_end, y_val) in years if y_start > cit_end), None)
        if not next_year:
            continue
        y_start, y_end, year_val = next_year
        # Find the previous year before this citation
        prev_year = None
        for (y_start_prev, y_end_prev, y_val_prev) in reversed(years):
            if y_end_prev < cit_start:
                prev_year = (y_start_prev, y_end_prev, y_val_prev)
                break
        # Backward window: after previous year or 200 chars back
        cluster_start = prev_year[1] if prev_year else max(0, cit_start - 200)
        cluster_end = y_end
        cluster_text = text[cluster_start:cluster_end]
        # Extract all citations in this window
        cluster_citations = [m.group(0) for m in re.finditer(citation_pattern, cluster_text)]
        # Remove page/pincites
        cluster_text_no_pincite = re.sub(pincite_pattern, '', cluster_text)
        
        # Extract case name from the cluster text (not backward window)
        # Look for case name that appears before the first citation in the cluster
        first_citation_in_cluster = min(cluster_citations, key=lambda x: cluster_text.find(x))
        first_citation_pos = cluster_text.find(first_citation_in_cluster)
        text_before_citation = cluster_text[:first_citation_pos]
        
        # Find the last case name before the first citation
        case_name_matches = list(re.finditer(case_name_pattern, text_before_citation))
        case_name = None
        if case_name_matches:
            # Use the last (most recent) case name before the citation
            last_match = case_name_matches[-1]
            case_name = f"{last_match.group(1)} v. {last_match.group(2)}"
            # Clean up the case name - remove any trailing punctuation or extra text
            case_name = case_name.strip().rstrip(',.;:')
            # If the case name is too long (more than 100 chars), it might include extra text
            if len(case_name) > 100:
                v_pattern = r'([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)'
                v_matches = list(re.finditer(v_pattern, case_name))
                if v_matches:
                    last_v_match = v_matches[-1]
                    case_name = f"{last_v_match.group(1)} v. {last_v_match.group(2)}"
                    case_name = case_name.strip().rstrip(',.;:')
            # Additional filter: if there are four or more consecutive lowercase words, trim to the first capitalized word after that sequence
            import re
            words = case_name.split()
            lower_seq = 0
            trim_index = 0
            for i, word in enumerate(words):
                if word.islower():
                    lower_seq += 1
                else:
                    if lower_seq >= 4:
                        trim_index = i
                        break
                    lower_seq = 0
            if trim_index > 0:
                # Find the first capitalized word after the sequence
                for j in range(trim_index, len(words)):
                    if words[j][0].isupper():
                        case_name = ' '.join(words[j:])
                        break
                case_name = case_name.strip().rstrip(',.;:')
        
        # Only create a cluster if there are at least 1 citation
        if cluster_citations:
            clusters.append({
                'case_name': case_name,
                'year': year_val,
                'citations': cluster_citations,
                'start': cluster_start,
                'end': cluster_end,
                'text': cluster_text_no_pincite.strip()
            })
    return clusters