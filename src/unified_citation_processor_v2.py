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

# Import the main config module for proper environment variable handling
try:
    from .config import get_config_value
except ImportError:
    try:
        from config import get_config_value
    except ImportError:
        def get_config_value(key: str, default: str = "") -> str:
            # Fallback: try environment variable directly
            return os.environ.get(key, default)

logger = logging.getLogger(__name__)

# Try to import eyecite for enhanced extraction
try:
    from eyecite import get_citations, AhocorasickTokenizer, HyperscanTokenizer
    EYECITE_AVAILABLE = True
except ImportError:
    EYECITE_AVAILABLE = False
    logger.warning("Eyecite not available - install with: pip install eyecite")

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
        
        # Initialize enhanced web searcher (optional)
        self.enhanced_web_searcher = None
        try:
            from src.enhanced_web_searcher import EnhancedWebSearcher
            self.enhanced_web_searcher = EnhancedWebSearcher()
        except ImportError:
            logger.warning("EnhancedWebSearcher not available - web search fallback disabled")
        
        if self.config.debug_mode:
            logger.info(f"CourtListener API key available: {bool(self.courtlistener_api_key)}")
            logger.info(f"Enhanced web searcher available: {bool(self.enhanced_web_searcher)}")
        
    def _init_patterns(self):
        """Initialize comprehensive citation patterns."""
        self.citation_patterns = {
            # Washington State patterns
            'wn2d': re.compile(r'\b(\d+)\s+Wn\.2d\s+(\d+)\b', re.IGNORECASE),
            'wn2d_space': re.compile(r'\b(\d+)\s+Wn\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            'wn_app': re.compile(r'\b(\d+)\s+Wn\.\s*App\.\s+(\d+)\b', re.IGNORECASE),
            'wn_app_space': re.compile(r'\b(\d+)\s+Wn\.\s*App\s+(\d+)\b', re.IGNORECASE),
            'wash2d': re.compile(r'\b(\d+)\s+Wash\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            'wash2d_space': re.compile(r'\b(\d+)\s+Wash\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            'wash_app': re.compile(r'\b(\d+)\s+Wash\.\s*App\.\s+(\d+)\b', re.IGNORECASE),
            'wash_app_space': re.compile(r'\b(\d+)\s+Wash\.\s*App\s+(\d+)\b', re.IGNORECASE),
            
            # Pacific Reporter patterns
            'p3d': re.compile(r'\b(\d+)\s+P\.3d\s+(\d+)\b', re.IGNORECASE),
            'p2d': re.compile(r'\b(\d+)\s+P\.2d\s+(\d+)\b', re.IGNORECASE),
            
            # Federal patterns
            'us': re.compile(r'\b(\d+)\s+U\.S\.\s+(\d+)\b', re.IGNORECASE),
            'f3d': re.compile(r'\b(\d+)\s+F\.3d\s+(\d+)\b', re.IGNORECASE),
            'f2d': re.compile(r'\b(\d+)\s+F\.2d\s+(\d+)\b', re.IGNORECASE),
            'f_supp': re.compile(r'\b(\d+)\s+F\.\s*Supp\.\s+(\d+)\b', re.IGNORECASE),
            'f_supp2d': re.compile(r'\b(\d+)\s+F\.\s*Supp\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            'f_supp3d': re.compile(r'\b(\d+)\s+F\.\s*Supp\.\s*3d\s+(\d+)\b', re.IGNORECASE),
            
            # Supreme Court patterns
            's_ct': re.compile(r'\b(\d+)\s+S\.\s*Ct\.\s+(\d+)\b', re.IGNORECASE),
            'l_ed': re.compile(r'\b(\d+)\s+L\.\s*Ed\.\s+(\d+)\b', re.IGNORECASE),
            'l_ed2d': re.compile(r'\b(\d+)\s+L\.\s*Ed\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            
            # Atlantic Reporter patterns
            'a2d': re.compile(r'\b(\d+)\s+A\.2d\s+(\d+)\b', re.IGNORECASE),
            'a3d': re.compile(r'\b(\d+)\s+A\.3d\s+(\d+)\b', re.IGNORECASE),
            
            # Southern Reporter patterns
            'so2d': re.compile(r'\b(\d+)\s+So\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            'so3d': re.compile(r'\b(\d+)\s+So\.\s*3d\s+(\d+)\b', re.IGNORECASE),
            
            # Alternative patterns
            'wash_2d_alt': re.compile(r'\b(\d+)\s+Wash\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            'wash_app_alt': re.compile(r'\b(\d+)\s+Wash\.\s*App\.\s+(\d+)\b', re.IGNORECASE),
            'wn2d_alt': re.compile(r'\b(\d+)\s+Wn\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            'wn2d_alt_space': re.compile(r'\b(\d+)\s+Wn\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            'wn_app_alt': re.compile(r'\b(\d+)\s+Wn\.\s*App\.\s+(\d+)\b', re.IGNORECASE),
            'p3d_alt': re.compile(r'\b(\d+)\s+P\.\s*3d\s+(\d+)\b', re.IGNORECASE),
            'p2d_alt': re.compile(r'\b(\d+)\s+P\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            
            # Complete patterns for parallel citations
            'wash_complete': re.compile(r'\b(\d+)\s+(?:Wash\.|Wn\.)\s*(?:2d|App\.)\s+(\d+)(?:\s*,\s*(\d+))?(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\b', re.IGNORECASE),
            'wash_with_parallel': re.compile(r'\b(\d+)\s+(?:Wash\.|Wn\.)\s*(?:2d|App\.)\s+(\d+)(?:\s*,\s*(\d+))?(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\b', re.IGNORECASE),
            'parallel_cluster': re.compile(r'\b(\d+)\s+(?:Wash\.|Wn\.)\s*(?:2d|App\.)\s+(\d+)(?:\s*,\s*(\d+))?(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\b', re.IGNORECASE),
            
            # NEW: Flexible patterns that handle parallel citations and parentheses
            'flexible_wash2d': re.compile(r'\b(\d+)\s+(?:Wash\.|Wn\.)\s*2d\s+(\d+)(?:\s*[,\s]\s*\d+\s+(?:P\.3d|P\.2d)\s+\d+)*\s*(?:\(\d{4}\))?\b', re.IGNORECASE),
            'flexible_p3d': re.compile(r'\b(\d+)\s+P\.3d\s+(\d+)(?:\s*[,\s]\s*\d+\s+(?:Wash\.|Wn\.)\s*2d\s+\d+)*\s*(?:\(\d{4}\))?\b', re.IGNORECASE),
            'flexible_p2d': re.compile(r'\b(\d+)\s+P\.2d\s+(\d+)(?:\s*[,\s]\s*\d+\s+(?:Wash\.|Wn\.)\s*2d\s+\d+)*\s*(?:\(\d{4}\))?\b', re.IGNORECASE),
            
            # Simple individual citation patterns (for fallback)
            'simple_wash2d': re.compile(r'\b(\d+)\s+(?:Wash\.|Wn\.)\s*2d\s+(\d+)\b', re.IGNORECASE),
            'simple_p3d': re.compile(r'\b(\d+)\s+P\.3d\s+(\d+)\b', re.IGNORECASE),
            'simple_p2d': re.compile(r'\b(\d+)\s+P\.2d\s+(\d+)\b', re.IGNORECASE),
        }
        
        # Additional patterns for pinpoint pages, docket numbers, etc.
        self.pinpoint_pattern = re.compile(r'\b(?:at\s+)?(\d+)\b', re.IGNORECASE)
        self.docket_pattern = re.compile(r'\b(?:No\.|Docket\s+No\.|Case\s+No\.)\s*[:\-]?\s*([A-Z0-9\-\.]+)\b', re.IGNORECASE)
        self.history_pattern = re.compile(r'\b(?:affirmed|reversed|remanded|vacated|denied|granted|cert\.?\s+denied)\b', re.IGNORECASE)
        self.status_pattern = re.compile(r'\b(?:published|unpublished|memorandum|opinion)\b', re.IGNORECASE)
    
    def _init_case_name_patterns(self):
        """Initialize case name extraction patterns."""
        self.case_name_patterns = [
            # Standard case name patterns
            r'([A-Z][A-Za-z0-9&.,\'\\-]*(?:\s+[A-Za-z0-9&.,\'\\-]+)*\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9&.,\'\\-]*(?:\s+[A-Za-z0-9&.,\'\\-]+)*)',
            r'((?:[A-Za-z0-9&.,\'\\-]+\s+)+(?:v\.|vs\.|versus)\s+(?:[A-Za-z0-9&.,\'\\-]+\s*)+)',
            r'(?:^|[\n\r]|[\.\!\?]\s+)([A-Z][A-Za-z&.,\'\\-]*(?:\s+[A-Za-z&.,\'\\-]+)*\s+(?:v\.|vs\.|versus)\s+[A-Za-z&.,\'\\-]+(?:\s+[A-Za-z&.,\'\\-]+)*)',
            
            # NEW: Capitalized word pattern with limited lowercase sequences
            # Matches: starts with capital, contains "v.", and no more than 4 lowercase words in a row
            r'([A-Z][A-Za-z0-9&.,\'\\-]+(?:\s+[A-Za-z0-9&.,\'\\-]+)*\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9&.,\'\\-]+(?:\s+[A-Za-z0-9&.,\'\\-]+)*)',
            
            # Fallback: any sequence with "v." that starts with capital and has reasonable length
            r'([A-Z][A-Za-z0-9&.,\'\\-]+(?:\s+[A-Za-z0-9&.,\'\\-]+){0,15}\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9&.,\'\\-]+(?:\s+[A-Za-z0-9&.,\'\\-]+){0,15})',
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
        }
        
        for reporter, pattern in reporter_patterns.items():
            if re.search(pattern, citation, re.IGNORECASE):
                return reporter
        
        return None

    def _get_possible_states_for_reporter(self, reporter: str) -> List[str]:
        """Get all possible states for a given regional reporter."""
        return self.state_reporter_mapping.get(reporter, [])

    def _verify_citations(self, citations: List[CitationResult]) -> List[CitationResult]:
        """Verify citations individually to ensure accurate results."""
        if not self.config.enable_verification:
            return citations
        
        # Verify each citation individually to ensure accurate results
        for citation in citations:
            self._verify_single_citation(citation)
        
        return citations

    def _verify_state_group(self, citations: List[CitationResult]):
        """Verify a group of state-specific citations (e.g., all Wash.2d variants)."""
        if not citations:
            return
        
        # Use the first citation as representative for the group
        representative = citations[0]
        state = self._infer_state_from_citation(representative.citation)
        
        # Verify the representative citation
        verify_result = self._verify_with_courtlistener_search(
            representative.citation,
            representative.extracted_case_name,
            representative.extracted_date
        )
        
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
        verify_result = self._verify_with_courtlistener_search(
            citation.citation,
            citation.extracted_case_name,
            citation.extracted_date
        )
        
        if verify_result.get("verified"):
            citation.canonical_name = verify_result.get("canonical_name")
            citation.canonical_date = verify_result.get("canonical_date")
            citation.url = verify_result.get("url")
            citation.verified = True
            citation.metadata = citation.metadata or {}
            citation.metadata["courtlistener_source"] = verify_result.get("source")

    def _verify_with_courtlistener_search(self, citation: str, extracted_case_name: str = None, extracted_date: str = None, apply_state_filter: bool = True) -> Dict:
        """
        Use CourtListener Search API for canonical metadata (used after batch lookup).
        Enhanced scoring to pick the closest match when multiple cases are on a single page.
        """
        import requests
        from difflib import SequenceMatcher
        
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
                base_citation = self._get_base_citation(citation)
                search_url = f"https://www.courtlistener.com/api/rest/v4/search/?q={base_citation}&format=json"
                resp2 = requests.get(search_url, headers=headers, timeout=10)
                if resp2.status_code == 200:
                    search_data = resp2.json()
                    results = search_data.get("results", [])
                    
                    # Apply state filtering only if requested
                    if apply_state_filter:
                        expected_state = self._infer_state_from_citation(citation)
                        if expected_state:
                            state_lower = expected_state.lower()
                            filtered = [
                                r for r in results
                                if state_lower in (r.get('court', '').lower() + r.get('jurisdiction', '').lower())
                            ]
                            if filtered:
                                results = filtered
                    
                    best = None
                    
                    for entry in results:
                        entry_citations = entry.get("citation", [])
                        entry_name = entry.get("caseName", "")
                        entry_date = entry.get("dateFiled", "")
                        entry_court = entry.get("court", "")
                        
                        # Enhanced scoring system
                        match_score = 0
                        citation_match_details = []
                        
                        # 1. Citation exact match (highest priority)
                        for c in entry_citations:
                            normalized_citation = c.replace(",", "").replace(" ", "").lower()
                            normalized_base = base_citation.replace(",", "").replace(" ", "").lower()
                            
                            if normalized_base in normalized_citation:
                                match_score += 10  # Exact citation match
                                citation_match_details.append(f"exact_citation_match: {c}")
                                break
                            elif self._is_similar_citation(base_citation, c):
                                match_score += 8  # Similar citation (handles variations)
                                citation_match_details.append(f"similar_citation_match: {c}")
                                break
                        
                        # 2. Case name similarity (using sequence matcher for fuzzy matching)
                        if extracted_case_name and entry_name:
                            # Exact case name match
                            if extracted_case_name.lower() in entry_name.lower():
                                match_score += 6
                                citation_match_details.append(f"exact_case_name_match: {extracted_case_name}")
                            # Partial case name match (word overlap)
                            elif any(word in entry_name.lower() for word in extracted_case_name.lower().split()):
                                match_score += 3
                                citation_match_details.append(f"partial_case_name_match: {extracted_case_name}")
                            # Fuzzy similarity for close matches
                            else:
                                similarity = SequenceMatcher(None, extracted_case_name.lower(), entry_name.lower()).ratio()
                                if similarity > 0.7:  # 70% similarity threshold
                                    match_score += int(similarity * 4)  # Up to 4 points for high similarity
                                    citation_match_details.append(f"fuzzy_case_name_match: {similarity:.2f}")
                        
                        # 3. Date matching
                        if extracted_date and entry_date:
                            if extracted_date in entry_date:
                                match_score += 2
                                citation_match_details.append(f"date_match: {extracted_date}")
                            elif self._is_similar_date(extracted_date, entry_date):
                                match_score += 1
                                citation_match_details.append(f"similar_date_match: {extracted_date}")
                        
                        # 4. Court preference (Washington courts get bonus)
                        if "washington" in entry_court.lower():
                            match_score += 2
                            citation_match_details.append("washington_court_bonus")
                        elif "supreme" in entry_court.lower() or "appellate" in entry_court.lower():
                            match_score += 1
                            citation_match_details.append("state_court_bonus")
                        
                        # 5. Page number proximity (if we can extract page numbers)
                        page_proximity_score = self._calculate_page_proximity(citation, entry_citations)
                        if page_proximity_score > 0:
                            match_score += page_proximity_score
                            citation_match_details.append(f"page_proximity: {page_proximity_score}")
                        
                        # 6. Citation format preference (prefer official reporters)
                        format_score = self._calculate_format_preference(entry_citations)
                        if format_score > 0:
                            match_score += format_score
                            citation_match_details.append(f"format_preference: {format_score}")
                        
                        # Update best match if this score is higher
                        if not best or match_score > best[0]:
                            best = (match_score, entry, citation_match_details)
                        elif match_score == best[0]:
                            # If scores are equal, prefer the one with more citation matches
                            current_citation_matches = sum(1 for detail in citation_match_details if "citation_match" in detail)
                            best_citation_matches = sum(1 for detail in best[2] if "citation_match" in detail)
                            if current_citation_matches > best_citation_matches:
                                best = (match_score, entry, citation_match_details)
                    
                    # Use a lower threshold since we have more sophisticated scoring
                    if best and best[0] >= 3:
                        entry = best[1]
                        match_details = best[2]
                        result["canonical_name"] = entry.get("caseName")
                        result["canonical_date"] = entry.get("dateFiled")
                        abs_url = entry.get("absolute_url")
                        if abs_url and abs_url.startswith("/"):
                            abs_url = "https://www.courtlistener.com" + abs_url
                        result["url"] = abs_url
                        result["verified"] = True
                        result["source"] = f"CourtListener (Search) - batch variant: {citation}"
                        result["raw"] = entry
                        logger.info(f"Found citation with search variant: {citation}, base: {base_citation}, score: {best[0]}, details: {match_details}")
                        return result
                    elif best:
                        logger.info(f"Citation {citation} found but score {best[0]} below threshold (3), details: {best[2]}")
                logger.warning(f"No results from CourtListener Search API for variant '{citation}' (base: {base_citation})")
            except Exception as e:
                logger.warning(f"Search endpoint failed for variant '{citation}': {e}")
        logger.warning(f"No verification found for citation: {citation}")
        return result

    def _get_base_citation(self, citation: str) -> str:
        """Return the base citation (volume reporter page) without pincites."""
        import re
        # Match patterns like "200 Wn.2d 72" or "146 Wn.2d 1"
        match = re.match(r'(\d+\s+\w+\.\w+\s+\d+)', citation)
        if match:
            return match.group(1)
        return citation

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

        # Use comprehensive citation patterns
        for pattern_name, pattern in self.citation_patterns.items():
            matches = list(pattern.finditer(text))
            if matches:
                print(f"[DEBUG] Pattern '{pattern_name}' matched {len(matches)} times.")
                for match in matches:
                    print(f"[DEBUG]   Match: '{match.group(0)}'")
            for match in matches:
                citation_str = match.group(0).strip()
                if not citation_str or citation_str in seen_citations:
                    continue
                seen_citations.add(citation_str)
                print(f"[DEBUG] Processing citation: '{citation_str}'")
                
                # Extract context around the citation
                start_pos = match.start()
                end_pos = match.end()
                context = self._extract_context(text, start_pos, end_pos)
                
                # Build CitationResult first
                citation = CitationResult(
                    citation=citation_str,
                    start_index=start_pos,
                    end_index=end_pos,
                    method="regex",
                    pattern=pattern_name,
                    context=context,
                    source="regex"
                )
                print(f"[DEBUG] Created CitationResult: {citation.citation}")
                
                # Add to list so we can pass it to case name extraction
                citations.append(citation)
        
        print(f"[DEBUG] Total citations created: {len(citations)}")
        
        # Now extract case names and dates with access to all citations
        for citation in citations:
            # Try to extract case name and date from context
            citation.extracted_case_name = self._extract_case_name_from_context(text, citation, citations)
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
            # Try HyperscanTokenizer first, fallback to AhocorasickTokenizer
            try:
                tokenizer = HyperscanTokenizer()
            except Exception:
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
        """Extract additional metadata from citation context."""
        try:
            # Extract pinpoint pages
            context = citation.context
            pinpoint_matches = self.pinpoint_pattern.findall(context)
            if pinpoint_matches:
                citation.pinpoint_pages = list(set(pinpoint_matches))
            
            # Extract docket numbers
            docket_matches = self.docket_pattern.findall(context)
            if docket_matches:
                citation.docket_numbers = list(set(docket_matches))
            
            # Extract case history
            history_matches = self.history_pattern.findall(context)
            if history_matches:
                citation.case_history = list(set(history_matches))
            
            # Extract publication status
            status_match = self.status_pattern.search(context)
            if status_match:
                citation.publication_status = status_match.group(0)
                
        except Exception as e:
            logger.debug(f"Error extracting metadata: {e}")
    
    def _extract_case_name_from_context(self, text: str, citation: CitationResult, all_citations: List[CitationResult] = None) -> Optional[str]:
        """Extract case name from context around citation using bracketed approach."""
        if not citation.start_index:
            return None
        
        # Find the end of the current citation's year (e.g., (2011)) or the end of the citation string
        context_end = citation.end_index
        year_match = re.search(r'\(\d{4}\)', text[citation.end_index: citation.end_index+8])
        if year_match:
            context_end = citation.end_index + year_match.end()
        
        # Find the start of context: end of previous citation's year, or a reasonable limit before current citation
        context_start = max(0, citation.start_index - 300)  # Default fallback: 300 chars before
        
        if all_citations:
            # Find the previous citation that ends before the current citation starts
            previous_citation_end = None
            for prev_citation in all_citations:
                if (prev_citation.end_index and 
                    prev_citation.end_index < citation.start_index and
                    (previous_citation_end is None or prev_citation.end_index > previous_citation_end)):
                    previous_citation_end = prev_citation.end_index
            
            if previous_citation_end is not None:
                # Find the end of the previous citation's year
                prev_year_match = re.search(r'\(\d{4}\)', text[previous_citation_end: previous_citation_end+8])
                if prev_year_match:
                    context_start = previous_citation_end + prev_year_match.end()
                else:
                    context_start = previous_citation_end
        
        # Limit context window to prevent capturing too much text between citations
        max_context_length = 500  # Maximum 500 characters for context window
        if context_end - context_start > max_context_length:
            context_start = context_end - max_context_length
        
        context = text[context_start:context_end]
        
        if self.config.debug_mode:
            logger.info(f"Extracting case name from context: '{context[:100]}...'")
        
        # Try each case name pattern on the full context
        best_case_name = None
        best_distance = float('inf')
        valid_case_names = []
        
        for pattern_str in self.case_name_patterns:
            try:
                pattern = re.compile(pattern_str, re.IGNORECASE)
                matches = pattern.finditer(context)
                
                for match in matches:
                    case_name = match.group(1).strip()
                    
                    # --- Enhanced post-processing: extract only the true case name ---
                    # Find the first capitalized word followed by v./vs./versus and extract up to a comma, parenthesis, or end, allowing business suffixes
                    m_case = re.search(r'([A-Z][A-Za-z0-9&.,\'\\-]+(?:\s+[A-Za-z0-9&.,\'\\-]+)*\s+(?:v\.|vs\.|versus).*?)(,\s*(?:LLC|Inc\.|Corp\.|Co\.|Ltd\.|L\.L\.C\.|P\.C\.|LLP|PLLC|PC|LP|PL|PLC|LLC\.|Inc|LLC,|Inc,|LLP,|Ltd,|Co,|Corp,|L\.L\.C\.|P\.C\.|LLP|PLLC|PC|LP|PL|PLC))?(?:,|\(|$)', case_name)
                    if m_case:
                        case_name = m_case.group(1).strip()
                        if m_case.group(2):
                            case_name += m_case.group(2)
                    else:
                        # fallback to previous logic
                        m_leading = re.search(r'([A-Z][A-Za-z0-9&.,\'\\-]*(?:\s+[A-Za-z0-9&.,\'\\-]+)*\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9&.,\'\\-]+(?:\s+[A-Za-z0-9&.,\'\\-]+)*)', case_name)
                        if m_leading:
                            case_name = m_leading.group(1)
                    # Trim any leading context before the actual case name
                    m_lead_trim = re.search(r'([A-Z][A-Za-z0-9&.,\'\\-]+\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9&.,\'\\-]+.*)', case_name)
                    if m_lead_trim:
                        case_name = m_lead_trim.group(1)
                    case_name = re.sub(r',?\s*\d+\s+[A-Za-z.]+(?:\s+\d+)*.*$', '', case_name)
                    case_name = re.sub(r'\(\d{4}\)$', '', case_name)
                    case_name = re.sub(r',\s*\d+\s*[A-Za-z.]+.*$', '', case_name)
                    case_name = case_name.strip(' ,;')
                    case_name = re.sub(r'\s+\d+\s*$', '', case_name)
                    case_name = re.sub(r'\s+\d+,\s*\d+\s*$', '', case_name)
                    
                    if self.config.debug_mode:
                        logger.info(f"Found potential case name: '{case_name}'")
                    
                    if self._is_valid_case_name(case_name):
                        valid_case_names.append(case_name)
                        if self.config.debug_mode:
                            logger.info(f"Case name '{case_name}' is valid")
                        
                        match_start_in_context = match.start()
                        match_start_in_text = context_start + match_start_in_context
                        match_end_in_text = context_start + match.end()
                        citation_start = citation.start_index
                        citation_end = citation.end_index
                        distances = [
                            abs(citation_start - match_start_in_text),
                            abs(citation_end - match_start_in_text),
                            abs(citation_start - match_end_in_text),
                            abs(citation_end - match_end_in_text)
                        ]
                        distance = min(distances)
                        if match_start_in_text > citation_start:
                            distance += 200
                        if distance > 150:
                            distance += 100
                        if self.config.debug_mode:
                            logger.info(f"Distance from citation to case name '{case_name}': {distance}")
                        if distance < best_distance:
                            best_distance = distance
                            best_case_name = case_name
                    else:
                        if self.config.debug_mode:
                            logger.info(f"Case name '{case_name}' is NOT valid")
            except Exception as e:
                logger.debug(f"Error with case name pattern {pattern_str}: {e}")
                continue
        if not best_case_name and valid_case_names:
            best_case_name = max(valid_case_names, key=len)
        if self.config.debug_mode and best_case_name:
            logger.info(f"Selected case name: '{best_case_name}' (distance: {best_distance})")
        return best_case_name
    
    def _extract_date_from_context(self, text: str, citation: CitationResult) -> Optional[str]:
        """Extract date from context around citation using core DateExtractor."""
        if not citation.start_index:
            return None
        
        try:
            # Use the core DateExtractor for consistent date extraction
            from src.case_name_extraction_core import date_extractor
            
            # Extract date using the core DateExtractor
            date_str = date_extractor.extract_date_from_context(
                text, 
                citation.start_index, 
                citation.end_index, 
                self.config.context_window
            )
            
            # Return just the year if a full date was found
            if date_str and '-' in date_str:
                return date_str.split('-')[0]
            
            return date_str
            
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
        """Remove duplicate citations while preserving the best version of each."""
        if not citations:
            return citations
        
        # First, sort by position and length (longer citations first)
        sorted_citations = sorted(citations, key=lambda x: (x.start_index or 0, -(x.end_index or 0)))
        
        # Remove overlapping citations, keeping the longest
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
                    overlaps = True
                    break
            
            if not overlaps:
                non_overlapping.append(citation)
        
        # Now deduplicate by normalized citation text
        seen = {}
        for citation in non_overlapping:
            # Normalize citation for comparison
            normalized = self._normalize_citation(citation.citation)
            
            if normalized not in seen:
                seen[normalized] = citation
            else:
                # Keep the one with higher confidence or more metadata
                existing = seen[normalized]
                if (citation.confidence > existing.confidence or 
                    len(citation.extracted_case_name or '') > len(existing.extracted_case_name or '') or
                    len(citation.extracted_date or '') > len(existing.extracted_date or '')):
                    seen[normalized] = citation
        
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
    
    def _detect_parallel_citations(self, citations: List[CitationResult], text: str) -> List[CitationResult]:
        """Detect and group parallel citations, but only if they are close together AND share the same case name and year."""
        if not citations:
            return citations
        
        # Sort citations by position in text
        sorted_citations = sorted(citations, key=lambda x: x.start_index or 0)
        
        # Group nearby citations that might be parallel and share the same case name and year
        groups = []
        current_group = []
        
        for i, citation in enumerate(sorted_citations):
            if not current_group:
                current_group = [citation]
            else:
                prev_citation = current_group[-1]
                
                # Check if citations are adjacent or very close
                if citation.start_index and prev_citation.end_index:
                    distance = citation.start_index - prev_citation.end_index
                    close = distance <= 50
                    
                    # Check same case name and year
                    same_case = (citation.extracted_case_name == current_group[0].extracted_case_name)
                    same_year = (citation.extracted_date == current_group[0].extracted_date)
                    
                    if close and same_case and same_year:
                        # Check for comma separation or adjacency
                        if distance <= 0:
                            # Overlapping or adjacent citations - definitely part of same group
                            current_group.append(citation)
                        else:
                            # Check for comma separation
                            text_between = text[prev_citation.end_index:citation.start_index]
                            comma_separated = ',' in text_between and len(text_between.strip()) < 30
                            if comma_separated:
                                current_group.append(citation)
                            else:
                                # Finalize current group and start new one
                                if len(current_group) > 1:
                                    groups.append(current_group)
                                current_group = [citation]
                    else:
                        # Finalize current group and start new one
                        if len(current_group) > 1:
                            groups.append(current_group)
                        current_group = [citation]
                else:
                    # No position info - start new group
                    if len(current_group) > 1:
                        groups.append(current_group)
                    current_group = [citation]
        
        # Add the last group if it has multiple citations
        if len(current_group) > 1:
            groups.append(current_group)
        
        # Create cluster citations for groups
        result = []
        clustered_indices = set()
        for group in groups:
            if len(group) > 1:
                # Create a cluster citation
                cluster_citations = [c.citation for c in group]
                # Use the base citation of the first group member for the cluster
                base_citation = self._get_base_citation(group[0].citation)
                cluster_str = base_citation
                
                cluster_citation = CitationResult(
                    citation=cluster_str,
                    extracted_case_name=group[0].extracted_case_name,
                    extracted_date=group[0].extracted_date,
                    start_index=group[0].start_index,
                    end_index=group[-1].end_index,
                    method="cluster_detection",
                    pattern="cluster",
                    is_cluster=True,
                    cluster_members=cluster_citations,
                    context=group[0].context
                )
                # Merge metadata from all group members
                all_pinpoints = []
                all_dockets = []
                all_history = []
                for member in group:
                    all_pinpoints.extend(member.pinpoint_pages or [])
                    all_dockets.extend(member.docket_numbers or [])
                    all_history.extend(member.case_history or [])
                    if member.start_index is not None:
                        clustered_indices.add(member.start_index)
                cluster_citation.pinpoint_pages = list(set(all_pinpoints))
                cluster_citation.docket_numbers = list(set(all_dockets))
                cluster_citation.case_history = list(set(all_history))
                result.append(cluster_citation)
        # Add individual citations that weren't part of clusters
        for citation in sorted_citations:
            if citation.start_index is None or citation.start_index not in clustered_indices:
                result.append(citation)
        return result
    
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
        """
        Main processing pipeline: extract citations, enhance with metadata, and verify.
        
        Args:
            text: Text to extract citations from
            
        Returns:
            List of CitationResult objects with extracted and verified data
        """
        if not text or not text.strip():
            return []
        
        citations = []
        
        # Step 1: Extract citations using regex
        if self.config.use_regex:
            regex_citations = self._extract_with_regex(text)
            citations.extend(regex_citations)
        
        # Step 2: Extract citations using eyecite (if available)
        if self.config.use_eyecite:
            try:
                eyecite_citations = self._extract_with_eyecite(text)
                citations.extend(eyecite_citations)
            except Exception as e:
                if self.config.debug_mode:
                    logger.warning(f"Eyecite extraction failed: {e}")
        
        # Step 3: Extract case names and dates for each citation
        if self.config.extract_case_names or self.config.extract_dates:
            for citation in citations:
                if self.config.extract_case_names and not citation.extracted_case_name:
                    citation.extracted_case_name = self._extract_case_name_from_context(text, citation, citations)
                
                if self.config.extract_dates and not citation.extracted_date:
                    citation.extracted_date = self._extract_date_from_context(text, citation)
                
                # Calculate confidence
                citation.confidence = self._calculate_confidence(citation, text)
        
        # Step 4: Detect parallel citations
        if self.config.enable_clustering:
            citations = self._detect_parallel_citations(citations, text)
        
        # Step 5: Deduplicate citations
        if self.config.enable_deduplication:
            citations = self._deduplicate_citations(citations)
        
        # Step 6: Filter by confidence
        citations = [c for c in citations if c.confidence >= self.config.min_confidence]
        
        # Step 7: Limit number of citations
        if len(citations) > self.config.max_citations_per_text:
            citations = citations[:self.config.max_citations_per_text]
        
        # Step 8: Verify citations (with grouping optimization)
        if self.config.enable_verification:
            citations = self._verify_citations(citations)
        
        return citations

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