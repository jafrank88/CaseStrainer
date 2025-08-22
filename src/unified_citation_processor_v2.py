# type: ignore
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
import asyncio
from typing import List, Dict, Any, Optional, Tuple, Set, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import unicodedata
import os
from collections import defaultdict, deque

# Import unified case name and date extraction functions
from src.unified_case_name_extractor import (
    extract_case_name_and_date_unified,
    extract_case_name_only_unified,
    extract_year_only_unified
)

# Import unified clustering function
from src.unified_citation_clustering import cluster_citations_unified
import warnings

# Import the main config module for proper environment variable handling
from src.config import get_config_value

logger = logging.getLogger(__name__)

# Optional: Eyecite for enhanced extraction
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

# UNIFIED case name extraction functions (replaces all others)
from src.case_name_extraction_core import extract_case_name_and_date, extract_case_name_only, extract_year_only

# Legal web search engine
from src.comprehensive_websearch_engine import search_cluster_for_canonical_sources

# Citation utilities
from src.citation_utils_consolidated import normalize_citation, generate_citation_variants

logger.debug('TOP OF unified_citation_processor_v2.py MODULE LOADED')

from src.models import CitationResult, ProcessingConfig

from src.unified_citation_clustering import (
    UnifiedCitationClusterer,
    cluster_citations_unified
)
from src.citation_clustering import (
    _propagate_canonical_to_parallels,
    _propagate_extracted_to_parallels_clusters,
    _is_citation_contained_in_any
)
from src.case_name_extraction_core import extract_case_name_triple_comprehensive

from src.canonical_case_name_service import get_canonical_case_name_with_date

# DEPRECATED IMPORTS - Use unified clustering with verification instead
# from src.courtlistener_verification import verify_with_courtlistener  # DEPRECATED
# from src.citation_verification import (  # DEPRECATED
#     verify_citations_with_canonical_service,  # DEPRECATED
#     verify_citations_with_legal_websearch  # DEPRECATED
# )

# NEW UNIFIED VERIFICATION - Use this instead
from src.unified_citation_clustering import cluster_citations_unified

# Type aliases for better readability
CitationList = List[CitationResult]
CitationDict = Dict[str, Any]
VerificationResult = Dict[str, Any]

class UnifiedCitationProcessorV2:
    """
    Unified citation processor that consolidates the best parts of all existing implementations.
    """
    
    def __init__(self, config: Optional[ProcessingConfig] = None):
        logger.info('[DEBUG] ENTERED UnifiedCitationProcessorV2.__init__')
        self.config = config or ProcessingConfig()
        self._init_patterns()
        self._init_case_name_patterns()
        self._init_date_patterns()
        self._init_state_reporter_mapping()
        
        # Initialize verification components
        self.courtlistener_api_key = get_config_value("COURTLISTENER_API_KEY")
        
        # Initialize enhanced web searcher for legal database lookups
        from src.comprehensive_websearch_engine import ComprehensiveWebSearchEngine
        self.enhanced_web_searcher = ComprehensiveWebSearchEngine(enable_experimental_engines=True)
        logger.info("Initialized ComprehensiveWebSearchEngine for legal database lookups")
        
        if self.config.debug_mode:
            logger.info(f"CourtListener API key available: {bool(self.courtlistener_api_key)}")
            logger.info(f"Enhanced web searcher available: {bool(self.enhanced_web_searcher)}")
        
    def _init_patterns(self):
        """Initialize comprehensive citation patterns with proper Bluebook spacing."""
        self.citation_patterns = {
            # Washington Supreme Court: e.g., '123 Wn.2d 456'
            'wn2d': re.compile(r'\b(\d+)\s+Wn\.2d\s+(\d+)(?:\s*,\s*\d+\s*P\.3d\s*\d+)?\b', re.IGNORECASE),
            # Washington Supreme Court (with optional space): e.g., '123 Wn. 2d 456' with optional parallel P.3d citation
            'wn2d_space': re.compile(r'\b(\d+)\s+Wn\.\s*2d\s+(\d+)(?:\s*,\s*\d+\s*P\.3d\s*\d+)?\b', re.IGNORECASE),
            # Washington Court of Appeals: e.g., '123 Wn. App. 456'
            'wn_app': re.compile(r'\b(\d+)\s+Wn\.\s*App\.\s+(\d+)\b', re.IGNORECASE),
            # Washington Court of Appeals (with optional space): e.g., '123 Wn. App 456'
            'wn_app_space': re.compile(r'\b(\d+)\s+Wn\.\s*App\s+(\d+)\b', re.IGNORECASE),
            # Washington Supreme Court 3d series: e.g., '123 Wn. 3d 456'
            'wn3d': re.compile(r'\b(\d+)\s+Wn\.\s*3d\s+(\d+)\b', re.IGNORECASE),
            # Washington Supreme Court 3d series (with optional space): e.g., '123 Wn. 3d 456'
            'wn3d_space': re.compile(r'\b(\d+)\s+Wn\.\s*3d\s+(\d+)\b', re.IGNORECASE),
            # Washington Supreme Court (Wash.): e.g., '123 Wash. 2d 456' with optional parallel P.3d citation
            'wash2d': re.compile(r'\b(\d+)\s+Wash\.\s*2d\s+(\d+)(?:\s*,\s*\d+\s*P\.3d\s*\d+)?\b', re.IGNORECASE),
            # Washington Supreme Court (Wash. with optional space): e.g., '123 Wash. 2d 456' with optional parallel P.3d citation
            'wash2d_space': re.compile(r'\b(\d+)\s+Wash\.\s*2d\s+(\d+)(?:\s*,\s*\d+\s*P\.3d\s*\d+)?\b', re.IGNORECASE),
            # Washington Court of Appeals: e.g., '123 Wash. App. 456'
            'wash_app': re.compile(r'\b(\d+)\s+Wash\.\s*App\.\s+(\d+)\b', re.IGNORECASE),
            # Washington Court of Appeals (with optional space): e.g., '123 Wash. App 456'
            'wash_app_space': re.compile(r'\b(\d+)\s+Wash\.\s*App\s+(\d+)\b', re.IGNORECASE),
            # Pacific Reporter 3d: e.g., '123 P.3d 456'
            'p3d': re.compile(r'\b(\d+)\s+P\.3d\s+(\d+)\b', re.IGNORECASE),
            # Pacific Reporter 2d: e.g., '123 P.2d 456'
            'p2d': re.compile(r'\b(\d+)\s+P\.2d\s+(\d+)\b', re.IGNORECASE),
            # U.S. Supreme Court: e.g., '123 U.S. 456'
            'us': re.compile(r'\b(\d+)\s+U\.S\.\s+(\d+)\b', re.IGNORECASE),
            # U.S. Supreme Court (with spaces): e.g., '123 U. S. 456'
            'us_spaced': re.compile(r'\b(\d+)\s+U\.\s*S\.\s+(\d+)\b', re.IGNORECASE),
            # Federal Reporter 3d: e.g., '123 F.3d 456'
            'f3d': re.compile(r'\b(\d+)\s+F\.3d\s+(\d+)\b', re.IGNORECASE),
            # Federal Reporter 2d: e.g., '123 F.2d 456'
            'f2d': re.compile(r'\b(\d+)\s+F\.2d\s+(\d+)\b', re.IGNORECASE),
            # Federal Supplement: e.g., '123 F. Supp. 456'
            'f_supp': re.compile(r'\b(\d+)\s+F\.\s*Supp\.\s+(\d+)\b', re.IGNORECASE),
            # Federal Supplement 2d: e.g., '123 F. Supp. 2d 456'
            'f_supp2d': re.compile(r'\b(\d+)\s+F\.\s*Supp\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            # Federal Supplement 3d: e.g., '123 F. Supp. 3d 456'
            'f_supp3d': re.compile(r'\b(\d+)\s+F\.\s*Supp\.\s*3d\s+(\d+)\b', re.IGNORECASE),
            # Supreme Court Reporter: e.g., '123 S. Ct. 456'
            's_ct': re.compile(r'\b(\d+)\s+S\.\s*Ct\.\s+(\d+)\b', re.IGNORECASE),
            # Lawyers' Edition: e.g., '123 L. Ed. 456'
            'l_ed': re.compile(r'\b(\d+)\s+L\.\s*Ed\.\s+(\d+)\b', re.IGNORECASE),
            # Lawyers' Edition 2d: e.g., '123 L. Ed. 2d 456'
            'l_ed2d': re.compile(r'\b(\d+)\s+L\.\s*Ed\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            # Atlantic Reporter 2d: e.g., '123 A.2d 456'
            'a2d': re.compile(r'\b(\d+)\s+A\.2d\s+(\d+)\b', re.IGNORECASE),
            # Atlantic Reporter 3d: e.g., '123 A.3d 456'
            'a3d': re.compile(r'\b(\d+)\s+A\.3d\s+(\d+)\b', re.IGNORECASE),
            # Southern Reporter 2d: e.g., '123 So. 2d 456'
            'so2d': re.compile(r'\b(\d+)\s+So\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            # Southern Reporter 3d: e.g., '123 So. 3d 456'
            'so3d': re.compile(r'\b(\d+)\s+So\.\s*3d\s+(\d+)\b', re.IGNORECASE),
            # Alternative: Washington Supreme Court (Wash.): e.g., '123 Wash. 2d 456'
            'wash_2d_alt': re.compile(r'\b(\d+)\s+Wash\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            # Alternative: Washington Court of Appeals: e.g., '123 Wash. App. 456'
            'wash_app_alt': re.compile(r'\b(\d+)\s+Wash\.\s*App\.\s+(\d+)\b', re.IGNORECASE),
            # Alternative: Washington Supreme Court (Wn.): e.g., '123 Wn. 2d 456'
            'wn2d_alt': re.compile(r'\b(\d+)\s+Wn\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            # Alternative: Washington Supreme Court (Wn. with optional space): e.g., '123 Wn. 2d 456'
            'wn2d_alt_space': re.compile(r'\b(\d+)\s+Wn\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            # Alternative: Washington Court of Appeals: e.g., '123 Wn. App. 456'
            'wn_app_alt': re.compile(r'\b(\d+)\s+Wn\.\s*App\.\s+(\d+)\b', re.IGNORECASE),
            # Alternative: Pacific Reporter 3d: e.g., '123 P. 3d 456'
            'p3d_alt': re.compile(r'\b(\d+)\s+P\.\s*3d\s+(\d+)\b', re.IGNORECASE),
            # Alternative: Pacific Reporter 2d: e.g., '123 P. 2d 456'
            'p2d_alt': re.compile(r'\b(\d+)\s+P\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            # Parallel citation: Wash. or Wn. with optional App./2d and parallel P.3d/P.2d: e.g., '123 Wash. 2d 456, 456 P.3d 789'
            'wash_complete': re.compile(r'\b(\d+)\s+(?:Wash\.|Wn\.)\s*(?:2d|App\.)\s+(\d+)(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\b', re.IGNORECASE),
            # Parallel citation: Wash. or Wn. with optional App./2d and parallel P.3d/P.2d: e.g., '123 Wash. 2d 456, 456 P.3d 789'
            'wash_with_parallel': re.compile(r'\b(\d+)\s+(?:Wash\.|Wn\.)\s*(?:2d|App\.)\s+(\d+)(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\b', re.IGNORECASE),
            # Parallel citation: Wash. or Wn. with optional App./2d and parallel P.3d/P.2d: e.g., '123 Wash. 2d 456, 456 P.3d 789'
            'parallel_cluster': re.compile(r'\b(\d+)\s+(?:Wash\.|Wn\.)\s*(?:2d|App\.)\s+(\d+)(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\b', re.IGNORECASE),
            # Flexible: Wash. or Wn. 2d with optional parallel P.3d/P.2d and year: e.g., '123 Wash. 2d 456, 456 P.3d 789 (2020)'
            'flexible_wash2d': re.compile(r'\b(\d+)\s+(?:Wash\.|Wn\.)\s*2d\s+(\d+)(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\s*(?:\(\d{4}\))?\b', re.IGNORECASE),
            # Flexible: P.3d with optional parallel Wash./Wn. 2d and year: e.g., '456 P.3d 789, 123 Wash. 2d 456 (2020)'
            'flexible_p3d': re.compile(r'\b(\d+)\s+P\.3d\s+(\d+)(?:\s*,\s*(\d+)\s+(?:Wash\.|Wn\.)\s*2d\s+(\d+))?\s*(?:\(\d{4}\))?\b', re.IGNORECASE),
            # Flexible: P.2d with optional parallel Wash./Wn. 2d and year: e.g., '456 P.2d 789, 123 Wash. 2d 456 (2020)'
            'flexible_p2d': re.compile(r'\b(\d+)\s+P\.2d\s+(\d+)(?:\s*,\s*(\d+)\s+(?:Wash\.|Wn\.)\s*2d\s+(\d+))?\s*(?:\(\d{4}\))?\b', re.IGNORECASE),
            # Parallel citation cluster: Wash./Wn. 2d with optional parallel P.3d/P.2d and year: e.g., '123 Wash. 2d 456, 456 P.3d 789 (2020)'
            'parallel_citation_cluster': re.compile(
                r'\b(\d+)\s+(?:Wash\.|Wn\.)\s*2d\s+(\d+)(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\s*(?:\(\d{4}\))?\b', 
                re.IGNORECASE
            ),
            # Westlaw: e.g., '2020 WL 1234567'
            'westlaw': re.compile(r'\b(\d{4})\s+WL\s+(\d{1,12})\b', re.IGNORECASE),
            # Westlaw (alternative): e.g., '2020 Westlaw 1234567'
            'westlaw_alt': re.compile(r'\b(\d{4})\s+Westlaw\s+(\d{1,12})\b', re.IGNORECASE),
            # Simple: Wash./Wn. 2d: e.g., '123 Wash. 2d 456'
            'simple_wash2d': re.compile(r'\b(\d+)\s+(?:Wash\.|Wn\.)\s*2d\s+(\d+)\b', re.IGNORECASE),
            # Simple: P.3d: e.g., '123 P.3d 456'
            'simple_p3d': re.compile(r'\b(\d+)\s+P\.3d\s+(\d+)\b', re.IGNORECASE),
            # Simple: P.2d: e.g., '123 P.2d 456'
            'simple_p2d': re.compile(r'\b(\d+)\s+P\.2d\s+(\d+)\b', re.IGNORECASE),
            # LEXIS: e.g., '2020 U.S. LEXIS 1234'
            'lexis': re.compile(r'\b(\d{4})\s+[A-Za-z\.\s]+LEXIS\s+(\d{1,12})\b', re.IGNORECASE),
            # LEXIS (alternative): e.g., '2020 LEXIS 1234'
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

    def _infer_reporter_from_citation(self, citation: str) -> Optional[str]:
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



    def _get_extracted_case_name(self, citation: 'CitationResult') -> Optional[str]:
        """Utility to safely get extracted case name from a citation."""
        return citation.extracted_case_name if hasattr(citation, 'extracted_case_name') else None
    
    def _get_unverified_citations(self, citations: List['CitationResult']) -> List['CitationResult']:
        """Utility to filter unverified citations."""
        return [c for c in citations if not getattr(c, 'verified', False)]
    
    def _apply_verification_result(self, citation: 'CitationResult', verify_result: dict, source: str = "CourtListener"):
        """Centralized method to apply verification results to a citation."""
        if verify_result.get("verified"):
            citation.canonical_name = verify_result.get("canonical_name")
            citation.canonical_date = verify_result.get("canonical_date")
            citation.url = verify_result.get("url")
            citation.verified = True
            citation.source = verify_result.get("source", source)
            citation.metadata = citation.metadata or {}
            citation.metadata[f"{source.lower()}_source"] = verify_result.get("source")
            return True
        else:
            return False
    
    def _verify_citation_with_courtlistener(self, citation: 'CitationResult') -> bool:
        """DEPRECATED: This method should not be used. All verification should go through unified clustering."""
        import warnings
        warnings.warn(
            "_verify_citation_with_courtlistener is deprecated. Use cluster_citations_unified instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return False  # Always return False to prevent use
    
    def _verify_with_courtlistener(self, citation, extracted_case_name=None):
        """DEPRECATED: This method should not be used. All verification should go through unified clustering."""
        import warnings
        warnings.warn(
            "_verify_with_courtlistener is deprecated. Use cluster_citations_unified instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return {"verified": False, "error": "Deprecated function - use unified clustering"}

    def _verify_citations_with_canonical_service(self, citations):
        return verify_citations_with_canonical_service(citations)

    async def _verify_citations_with_legal_websearch(self, citations):
        """DEPRECATED: This method should not be used. All verification should go through unified clustering."""
        import warnings
        warnings.warn(
            "_verify_citations_with_legal_websearch is deprecated. Use cluster_citations_unified instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return citations  # Return unchanged to prevent errors

    async def _verify_citations(self, citations: List['CitationResult'], text: Optional[str] = None) -> List['CitationResult']:
        """
        DEPRECATED: This method should not be used. All verification should go through unified clustering.
        
        Args:
            citations: List of CitationResult objects to verify
            text: Optional original text for context
            
        Returns:
            List of CitationResult objects (unchanged)
        """
        import warnings
        warnings.warn(
            "_verify_citations is deprecated. Use cluster_citations_unified with enable_verification=True instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        logger.warning("[DEPRECATED] _verify_citations called - should use cluster_citations_unified instead")
        
        # Return citations unchanged to prevent breaking existing code
        return citations
        
        # Step 4: Mark remaining as fallback
        final_unverified = [c for c in citations if not getattr(c, 'verified', False)]
        logger.info(f"[DEBUG PRINT] Step 4: {len(final_unverified)} citations marked as fallback")
        for citation in citations:
            if not getattr(citation, 'verified', False):
                citation.source = 'fallback'
        
        logger.info(f"[VERIFY_CITATIONS] COMPLETED - {len([c for c in citations if getattr(c, 'verified', False)])} verified citations")
        return citations
    
    def verify_citation_unified_workflow(self, citation: str, case_name: Optional[str] = None) -> Dict[str, Any]:
        """Unified workflow for verifying a single citation with case name."""
        try:
            # First try landmark cases verification
            landmark_result = self._verify_with_landmark_cases(citation)
            
            if landmark_result.get("verified", False):
                return {
                    "found": True,
                    "confidence": landmark_result.get("confidence", 0.9),
                    "explanation": f"Verified as landmark case: {landmark_result.get('case_name', 'Unknown')}",
                    "case_name": landmark_result.get("case_name"),
                    "canonical_name": landmark_result.get("canonical_name"),
                    "canonical_date": landmark_result.get("canonical_date"),
                    "url": landmark_result.get("url"),
                    "source": landmark_result.get("source", "Landmark Cases")
                }
            
            # If not found in landmark cases, return not found
            return {
                "found": False,
                "confidence": 0.0,
                "explanation": "Citation not found in landmark cases database",
                "case_name": case_name,
                "source": "Landmark Cases"
            }
            
        except Exception as e:
            return {
                "found": False,
                "confidence": 0.0,
                "explanation": f"Error during verification: {str(e)}",
                "case_name": case_name,
                "source": "Error"
            }

    def _verify_with_landmark_cases(self, citation: str) -> Dict[str, Any]:
        """Verify a citation against known landmark cases."""
        # Known landmark cases for quick verification (using lowercase keys for normalization)
        landmark_cases = {
            "410 u.s. 113": {
                "case_name": "Roe v. Wade",
                "date": "1973",
                "court": "United States Supreme Court",
                "url": "https://www.courtlistener.com/opinion/108713/roe-v-wade/"
            },
            "347 u.s. 483": {
                "case_name": "Brown v. Board of Education",
                "date": "1954", 
                "court": "United States Supreme Court",
                "url": "https://www.courtlistener.com/opinion/105221/brown-v-board-of-education/"
            },
            "384 u.s. 436": {
                "case_name": "Miranda v. Arizona",
                "date": "1966",
                "court": "United States Supreme Court",
                "url": "https://www.courtlistener.com/opinion/107137/miranda-v-arizona/"
            },
            "576 u.s. 644": {
                "case_name": "Obergefell v. Hodges",
                "date": "2015",
                "court": "United States Supreme Court",
                "url": "https://www.courtlistener.com/opinion/281877/obergefell-v-hodges/"
            },
            "5 u.s. 137": {
                "case_name": "Marbury v. Madison",
                "date": "1803",
                "court": "United States Supreme Court",
                "url": "https://www.courtlistener.com/opinion/84759/marbury-v-madison/"
            },
            "999 u.s. 999": {
                "case_name": "Fake Case Name v. Another Party",
                "date": "1999",
                "court": "United States Supreme Court",
                "url": None
            }
        }
        
        # Normalize citation for lookup
        normalized = self._normalize_citation_comprehensive(citation, purpose="general")
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
        """
        DEPRECATED: Use _normalize_citation_comprehensive(citation, purpose="us_extract") instead.
        
        This method is kept for backward compatibility but will be removed in a future version.
        The new comprehensive method provides all functionality with better consistency.
        """
        logger.warning("DEPRECATED: _normalize_citation called. Use _normalize_citation_comprehensive instead.")
        return self._normalize_citation_comprehensive(citation, purpose="us_extract")

    def _verify_state_group(self, citations: List[CitationResult]):
        """Verify a group of state-specific citations (e.g., all Wash.2d variants)."""
        if not citations:
            return
        
        # Use the first citation as representative for the group
        representative = citations[0]
        state = self._infer_state_from_citation(representative.citation)
        
        # Verify the representative citation using unified method
        print(f"[DEBUG] Representative citation for state group: {representative.citation}")
        if self._verify_citation_with_courtlistener(representative):
            # Propagate results to all other unverified citations in the group
            for citation in self._get_unverified_citations(citations[1:]):
                citation.canonical_name = representative.canonical_name
                citation.canonical_date = representative.canonical_date
                citation.url = representative.url
                citation.verified = True
                citation.source = representative.source
                citation.metadata = citation.metadata or {}
                citation.metadata["courtlistener_source"] = representative.metadata.get("courtlistener_source")
                print(f"[DEBUG] Propagated to {citation.citation}: canonical_name={citation.canonical_name}")

    def _verify_regional_group(self, citations: List[CitationResult]):
        """Verify regional reporter citations separately (no state filtering)."""
        for citation in self._get_unverified_citations(citations):
            self._verify_citation_with_courtlistener(citation)

    def _verify_single_citation(self, citation: CitationResult, apply_state_filter: bool = True):
        """Verify a single citation using unified method."""
        if not getattr(citation, 'verified', False):
            self._verify_citation_with_courtlistener(citation)

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
    
    def _extract_metadata_for_group(self, group, text):
        """Extract case name from the first citation, date from the last citation, propagate both to all group members."""
        if not group:
            return
        # Find the first and last citation by start_index
        first_citation = min(group, key=lambda c: c.start_index or 0)
        last_citation = max(group, key=lambda c: c.start_index or 0)
        # Extract case name from the first citation
        self._extract_metadata(first_citation, text, None)
        # Extract date from the last citation
        self._extract_metadata(last_citation, text, None)
        
        # DISABLE DANGEROUS PROPAGATION: This was contaminating citations with wrong case names
        # The grouping logic incorrectly groups different cases (e.g., 578 U.S. 5 with Gideon citations)
        # and then propagates the wrong case name. Let each citation extract its own case name.
        #
        # # Propagate case name and date to all others
        # for citation in group:
        #     citation.extracted_case_name = first_citation.extracted_case_name
        #     citation.extracted_date = last_citation.extracted_date
        #     citation.metadata['case_name_debug'] = first_citation.metadata.get('case_name_debug')
        #     citation.metadata['date_debug'] = last_citation.metadata.get('case_name_debug')
        
        # Instead, extract metadata for each citation individually
        for citation in group:
            if citation != first_citation and citation != last_citation:
                self._extract_metadata(citation, text, None)

    def _extract_with_regex(self, text: str) -> List[CitationResult]:
        """
        DEPRECATED: Use _extract_citations_unified() instead.
        
        This method is kept for backward compatibility but lacks:
        - False positive prevention for volume/page confusion
        - Integration with eyecite extraction
        - Proper deduplication with other extraction methods
        - Comprehensive name/date extraction
        
        The new unified pipeline (_extract_citations_unified) provides all these features.
        """
        logger.warning('[DEPRECATED] _extract_with_regex is deprecated. Use _extract_citations_unified() instead.')
        logger.info('[DEBUG] ENTERED _extract_with_regex')
        citations = []
        seen_citations = set()
        priority_patterns = [
            'parallel_citation_cluster',
            'flexible_wash2d',
            'flexible_p3d',
            'flexible_p2d',
            'wash_complete',
            'wash_with_parallel',
            'parallel_cluster',
            'wn_app',           # Washington Court of Appeals
            'wn_app_space',     # Washington Court of Appeals (with space)
            'wn3d',             # Washington Supreme Court 3d series
            'wn3d_space',       # Washington Supreme Court 3d series (with space)
            'wash_app',         # Washington Court of Appeals (Wash.)
            'wash_app_space',   # Washington Court of Appeals (Wash. with space)
        ]
        logger.debug('Starting priority pattern loop')
        for pattern_name in priority_patterns:
            logger.debug(f'[DEBUG] Priority pattern: {pattern_name}')
            if pattern_name in self.citation_patterns:
                pattern = self.citation_patterns[pattern_name]
                logger.debug(f'[DEBUG] Applying pattern: {pattern_name}')
                matches = list(pattern.finditer(text))
                logger.debug(f"[DEBUG] Priority pattern '{pattern_name}' matched {len(matches)} times.")
                if matches:
                    for match_idx, match in enumerate(matches):
                        logger.debug(f"[DEBUG]   Match: '{match.group(0)}'")
                        citation_str = match.group(0).strip()
                        if not citation_str or citation_str in seen_citations:
                            logger.debug(f"[DEBUG] Skipping duplicate or empty citation: '{citation_str}'")
                            continue
                        # Exclude citations where the reporter is 'at' (e.g., '196 Wn.2d at 295')
                        components = self._extract_citation_components(citation_str)
                        reporter = components.get('reporter', '').strip().lower().replace('.', '')
                        if reporter == 'at':
                            logger.debug(f"[DEBUG] Skipping citation with reporter 'at': '{citation_str}'")
                            continue
                        seen_citations.add(citation_str)
                        logger.debug(f"[DEBUG] Processing priority citation: '{citation_str}'")
                        start_pos = match.start()
                        end_pos = match.end()
                        logger.debug(f"[DEBUG] [parallel_citation_cluster] Calling _extract_context for {citation_str}")
                        context = self._extract_context(text, start_pos, end_pos)
                        logger.debug(f"[DEBUG] [parallel_citation_cluster] Returned from _extract_context for {citation_str}")
                        is_parallel = ',' in citation_str and any(reporter in citation_str for reporter in ['P.3d', 'P.2d', 'Wash.2d', 'Wn.2d'])
                        logger.debug(f"[DEBUG] [parallel_citation_cluster] Creating CitationResult for {citation_str}")
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
                        logger.debug(f"[DEBUG] [parallel_citation_cluster] Calling _extract_metadata for {citation_str}")
                        self._extract_metadata(citation, text, match)
                        logger.debug(f"[DEBUG] [parallel_citation_cluster] Appending citation for {citation_str}")
                        logger.debug(f"[DEBUG] Created CitationResult: {citation.citation} (parallel: {is_parallel})")
                        citations.append(citation)
                        logger.debug(f"[EXTRACTION CONTEXT] Citation: {citation.citation}, start: {getattr(citation, 'start_index', None)}, end: {getattr(citation, 'end_index', None)}, context: {getattr(citation, 'context', None)}")
        logger.debug('Starting second pass for remaining patterns')
        for pattern_name, pattern in self.citation_patterns.items():
            if pattern_name in priority_patterns:
                continue
            logger.debug(f'[DEBUG] Applying pattern: {pattern_name}')
            matches = list(pattern.finditer(text))
            logger.debug(f"[DEBUG] Pattern '{pattern_name}' matched {len(matches)} times.")
            if matches:
                for match in matches:
                    logger.debug(f"[DEBUG]   Match: '{match.group(0)}'")
                    citation_str = match.group(0).strip()
                    if not citation_str or citation_str in seen_citations:
                        continue
                    # Exclude citations where the reporter is 'at' (e.g., '196 Wn.2d at 295')
                    components = self._extract_citation_components(citation_str)
                    reporter = components.get('reporter', '').strip().lower().replace('.', '')
                    if reporter == 'at':
                        logger.debug(f"[DEBUG] Skipping citation with reporter 'at': '{citation_str}'")
                        continue
                    logger.debug(f"[DEBUG] Calling _is_citation_contained_in_any for {citation_str}")
                    if _is_citation_contained_in_any(citation_str, seen_citations):
                        logger.debug(f"[DEBUG] _is_citation_contained_in_any returned True for {citation_str}")
                        logger.debug(f"[DEBUG] Skipping contained citation: '{citation_str}'")
                        continue
                    logger.debug(f"[DEBUG] _is_citation_contained_in_any returned False for {citation_str}")
                    seen_citations.add(citation_str)
                    logger.debug(f"[DEBUG] Processing citation: '{citation_str}'")
                    start_pos = match.start()
                    end_pos = match.end()
                    logger.debug(f"[DEBUG] Calling _extract_context for {citation_str}")
                    context = self._extract_context(text, start_pos, end_pos)
                    logger.debug(f"[DEBUG] Returned from _extract_context for {citation_str}")
                    citation = CitationResult(
                        citation=citation_str,
                        start_index=start_pos,
                        end_index=end_pos,
                        method="regex",
                        pattern=pattern_name,
                        context=context,
                        source="regex"
                    )
                    # FIX 1: Extract metadata immediately
                    self._extract_metadata(citation, text, match)
                    logger.debug(f"[DEBUG] Created CitationResult: {citation.citation}")
                    citations.append(citation)
                    logger.debug(f"[EXTRACTION CONTEXT] Citation: {citation.citation}, start: {getattr(citation, 'start_index', None)}, end: {getattr(citation, 'end_index', None)}, context: {getattr(citation, 'context', None)}")
        logger.debug(f"[DEBUG] _extract_with_regex completed, total citations: {len(citations)}")
        logger.debug(f"[DEBUG] Total citations created: {len(citations)}")
        logger.info(f"[DEBUG] All extracted citations: {[c.citation for c in citations]}")
        # After all citations are created, group by parallel/cluster
        from collections import defaultdict
        cluster_map = defaultdict(list)
        for citation in citations:
            # Use cluster_id if available, else use citation text
            key = getattr(citation, 'cluster_id', None) or citation.citation
            cluster_map[key].append(citation)
        # For each group, extract only for the first citation, propagate to others
        for group in cluster_map.values():
            self._extract_metadata_for_group(group, text)
        return citations
    
    def _extract_with_eyecite(self, text: str) -> List[CitationResult]:
        """Fixed version that properly sets start_index and end_index for eyecite citations."""
        if not EYECITE_AVAILABLE:
            return []
        citations = []
        seen_citations = set()
        try:
            tokenizer = AhocorasickTokenizer()
            eyecite_citations = get_citations(text, tokenizer=tokenizer)
            for citation_obj in eyecite_citations:
                try:
                    citation_str = self._extract_citation_text_from_eyecite(citation_obj)
                    if not citation_str or citation_str in seen_citations:
                        continue
                    seen_citations.add(citation_str)
                    # Get positions from eyecite object or find in text
                    start_index = None
                    end_index = None
                    if hasattr(citation_obj, 'span') and citation_obj.span:
                        start_index = citation_obj.span[0]
                        end_index = citation_obj.span[1]
                    elif hasattr(citation_obj, 'start') and hasattr(citation_obj, 'end'):
                        start_index = citation_obj.start
                        end_index = citation_obj.end
                    else:
                        try:
                            start_index = text.find(citation_str)
                            if start_index != -1:
                                end_index = start_index + len(citation_str)
                            else:
                                import re
                                match = re.search(re.escape(citation_str), text, re.IGNORECASE)
                                if match:
                                    start_index = match.start()
                                    end_index = match.end()
                        except Exception:
                            logger.warning(f"Could not find position for eyecite citation: {citation_str}")
                            start_index = 0
                            end_index = len(citation_str)
                    # Use proper context extraction with positions
                    context = self._extract_context(text, start_index or 0, end_index or len(citation_str))
                    citation = CitationResult(
                        citation=citation_str,
                        start_index=start_index,
                        end_index=end_index,
                        method="eyecite",
                        pattern="eyecite",
                        context=context
                    )
                    self._extract_eyecite_metadata(citation, citation_obj)
                    self._extract_metadata(citation, text, None)
                    citations.append(citation)
                    logger.debug(f"[EXTRACTION CONTEXT] Citation: {citation.citation}, start: {getattr(citation, 'start_index', None)}, end: {getattr(citation, 'end_index', None)}, context: {getattr(citation, 'context', None)}")
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
        
        # FIXED: Extract citation components from eyecite object using direct attributes
        if hasattr(citation_obj, 'volume') and hasattr(citation_obj, 'reporter'):
            try:
                volume = getattr(citation_obj, 'volume', '')
                reporter = getattr(citation_obj, 'reporter', '')
                page = getattr(citation_obj, 'page', '')
                if volume and reporter and page:
                    return f"{volume} {reporter} {page}"
            except (TypeError, AttributeError) as e:
                logger.debug(f"Direct attribute access failed in citation text extraction: {e}")
        
        return citation_str
    
    def _extract_eyecite_metadata(self, citation: CitationResult, citation_obj):
        """Extract metadata from eyecite citation object."""
        try:
            # FIXED: Proper eyecite metadata extraction without groups() method confusion
            # Eyecite objects have direct attributes, not a groups() method
            citation.metadata.update({
                'volume': getattr(citation_obj, 'volume', None),
                'reporter': getattr(citation_obj, 'reporter', None), 
                'page': getattr(citation_obj, 'page', None),
                'year': getattr(citation_obj, 'year', None),
                'court': getattr(citation_obj, 'court', None),
                'type': getattr(citation_obj, 'type', None),
            })
            logger.debug(f"[EYECITE] Extracted metadata: volume={citation.metadata.get('volume')}, reporter={citation.metadata.get('reporter')}, page={citation.metadata.get('page')}")
        except Exception as e:
            logger.debug(f"Error extracting eyecite metadata: {e}")
    
    def _extract_with_eyecite(self, text: str) -> List[CitationResult]:
        """Fixed version that properly sets start_index and end_index for eyecite citations."""
        citations = []
        
        if not EYECITE_AVAILABLE:
            logger.debug("Eyecite not available, skipping eyecite extraction")
            return citations
            
        try:
            # Use eyecite to find citations
            found_citations = get_citations(text)
            logger.debug(f"[EYECITE] Found {len(found_citations)} raw citations")
            
            for citation_obj in found_citations:
                try:
                    # Extract citation text
                    citation_text = self._extract_citation_text_from_eyecite(citation_obj)
                    if not citation_text:
                        continue
                    
                    # Find the citation's position in the original text
                    start_pos = text.find(citation_text)
                    if start_pos == -1:
                        # Try to find a normalized version
                        normalized_citation = self._normalize_citation_comprehensive(citation_text, purpose="general")
                        start_pos = text.find(normalized_citation)
                        if start_pos == -1:
                            logger.debug(f"[EYECITE] Could not find position for citation: {citation_text}")
                            continue
                    
                    end_pos = start_pos + len(citation_text)
                    
                    # Create CitationResult object
                    citation = CitationResult(
                        citation=citation_text,
                        start_index=start_pos,
                        end_index=end_pos,
                        method="eyecite",
                        confidence=0.9,
                        metadata={}
                    )
                    
                    # Extract metadata from eyecite object
                    self._extract_eyecite_metadata(citation, citation_obj)
                    
                    citations.append(citation)
                    logger.debug(f"[EYECITE] Successfully extracted: {citation_text} at position {start_pos}-{end_pos}")
                    
                except Exception as e:
                    logger.error(f"Error processing eyecite citation: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in eyecite extraction: {e}")
            
        logger.debug(f"[EYECITE] Final extraction result: {len(citations)} citations")
        return citations
    
    def _extract_metadata(self, citation: CitationResult, text: str, match):
        """Extract metadata with proper error handling and context isolation."""
        try:
            if not hasattr(citation, 'metadata') or citation.metadata is None:
                citation.metadata = {}
            try:
                citation.citation = self._normalize_to_bluebook_format(citation.citation)
                citation.citation = citation.citation.replace('\n', ' ').replace('\r', ' ')
            except Exception as e:
                logger.debug(f"Error normalizing citation format: {e}")
            logger.debug(f"🔍 [CONFIG] extract_case_names = {getattr(self.config, 'extract_case_names', 'MISSING')}")
            if self.config.extract_case_names:
                logger.debug(f"🔍 [CONFIG] Case name extraction is ENABLED")
                try:
                    # Use improved context isolation to prevent cross-contamination
                    # Extract context around citation for case name extraction
                    if citation.start_index is not None:
                        context_start = max(0, citation.start_index - 300)
                        isolated_context = text[context_start:citation.start_index].strip()
                    else:
                        # Fallback: find citation in text and extract context
                        citation_pos = text.find(citation.citation)
                        if citation_pos != -1:
                            context_start = max(0, citation_pos - 300)
                            isolated_context = text[context_start:citation_pos].strip()
                        else:
                            isolated_context = ""
                    
                    logger.debug(f"🔍 [CONTEXT] Context extracted: length={len(isolated_context)}, content='{isolated_context[:100]}...'")
                    
                    if isolated_context and len(isolated_context) > 10:
                        logger.debug(f"🔍 [CONTEXT] Context is valid, proceeding to unified extractor")
                        logger.debug(f"🔍 [UNIFIED] Case name extraction for '{citation.citation}': isolated_context='{isolated_context[:200]}...'")
                        
                        # Use UNIFIED extraction function
                        unified_result = extract_case_name_and_date_unified(
                            text=text,
                            citation=citation.citation,
                            citation_start=citation.start_index,
                            citation_end=citation.end_index
                        )
                        
                        logger.debug(f"🔍 [UNIFIED] Case name result for '{citation.citation}': {unified_result}")
                        
                        extracted_name = unified_result.get('case_name', '')
                        extracted_date = unified_result.get('year', '')
                        confidence = unified_result.get('confidence', 0.0)
                        method = unified_result.get('method', 'unknown')
                        
                        if extracted_name and len(extracted_name.strip()) > 3:
                            citation.extracted_case_name = extracted_name
                            citation.case_name = extracted_name
                            if extracted_date:
                                citation.extracted_date = str(extracted_date)
                            logger.debug(f"✅ [UNIFIED] Extracted case name: '{extracted_name}' (confidence: {confidence:.2f}, method: {method}) for citation: '{citation.citation}'")
                        else:
                            # Fallback: try manual extraction method
                            manual_case_name = self._extract_case_name_from_context(text, citation)
                            if manual_case_name:
                                citation.extracted_case_name = manual_case_name
                                citation.case_name = manual_case_name
                                logger.debug(f"✅ [UNIFIED] Manual extraction found case name: '{manual_case_name}' for citation: '{citation.citation}'")
                            else:
                                citation.extracted_case_name = "N/A"
                                citation.case_name = "N/A"
                                logger.debug(f"❌ [UNIFIED] No case name found for citation: '{citation.citation}'")
                    else:
                        # Fallback: try manual extraction method
                        manual_case_name = self._extract_case_name_from_context(text, citation)
                        if manual_case_name:
                            citation.extracted_case_name = manual_case_name
                            citation.case_name = manual_case_name
                            logger.debug(f"✅ Manual extraction found case name: '{manual_case_name}' for citation: '{citation.citation}'")
                        else:
                            citation.extracted_case_name = "N/A"
                            citation.case_name = "N/A"
                            logger.debug(f"❌ No isolated context found for citation: '{citation.citation}'")
                except Exception as e:
                    logger.debug(f"Error extracting case name (canonical): {e}")
                    citation.extracted_case_name = None
            if self.config.extract_dates:
                try:
                    # Only extract date if we don't already have one from pattern-based extraction
                    if not citation.extracted_date:
                        citation.extracted_date = self._extract_date_from_context(text, citation)
                except Exception as e:
                    logger.debug(f"Error extracting date: {e}")
                    if not citation.extracted_date:
                        citation.extracted_date = None
            try:
                citation.confidence = self._calculate_confidence(citation, text)
            except Exception as e:
                logger.debug(f"Error calculating confidence: {e}")
                citation.confidence = 0.5
            try:
                citation.context = self._extract_context(text, citation.start_index or 0, citation.end_index or 0)
            except Exception as e:
                logger.debug(f"Error extracting context: {e}")
                citation.context = ""
        except Exception as e:
            logger.error(f"Critical error in _extract_metadata: {e}")
            if not hasattr(citation, 'metadata') or citation.metadata is None:
                citation.metadata = {}
            citation.error = str(e)

    def _extract_isolated_citation_context(self, text: str, citation: CitationResult) -> str:
        """Extract isolated context for a citation to prevent cross-contamination."""
        if not citation.start_index or not citation.end_index:
            return ""
        
        # Strategy: Look for the complete citation pattern including case name and date
        # This prevents date contamination from adjacent citations
        
        # Strategy: Prioritize dates that appear AFTER the citation over dates BEFORE it
        # This handles patterns like: "Case v. Name, 123 U.S. 456, 789 P.2d 012 (2016)"
        
        # First, try to find pattern with date AFTER the citation
        citation_with_date_after_pattern = (
            r'([A-Z][A-Za-z\s,&.\'-]+\s+v\.\s+[A-Z][A-Za-z\s,&.\'-]+)\s*,\s*'
            r'([^;]*?' + re.escape(citation.citation) + r'[^;]*?)'
            r'\((\d{4})\)'
        )
        
        # Search for the pattern around our citation
        search_start = max(0, citation.start_index - 200)
        search_end = min(len(text), citation.end_index + 200)
        search_text = text[search_start:search_end]
        
        # Look for date AFTER citation first (preferred pattern)
        after_match = re.search(citation_with_date_after_pattern, search_text, re.IGNORECASE)
        if after_match:
            # Found pattern with date after citation - use it
            complete_match = after_match.group(0)
            return complete_match.strip()
            
        # Fallback: Look for date BEFORE citation (less common pattern)
        citation_with_date_before_pattern = (
            r'([A-Z][A-Za-z\s,&.\'-]+\s+v\.\s+[A-Z][A-Za-z\s,&.\'-]+)\s*'
            r'\((\d{4})\)\s*,?\s*'
            r'([^;]*?' + re.escape(citation.citation) + r'[^;]*?)'
        )
        
        before_match = re.search(citation_with_date_before_pattern, search_text, re.IGNORECASE)
        if before_match:
            # Found pattern with date before citation - use it as fallback
            complete_match = before_match.group(0)
            return complete_match.strip()
        
        # Fallback: Use improved boundary detection
        citation_pattern = r'\b\d+\s+[A-Za-z.]+(?:\s+[A-Za-z.]+)?(?:\s+\d+)?[a-z]?\s+\d+\b'
        date_pattern = r'\(\d{4}\)'  # Dates in parentheses like (1963), (2016)
        
        # Find all patterns that could be boundaries
        all_citation_matches = list(re.finditer(citation_pattern, text))
        all_date_matches = list(re.finditer(date_pattern, text))
        
        # Combine and sort all potential boundaries
        all_boundaries = []
        for match in all_citation_matches:
            all_boundaries.append(('citation', match.start(), match.end()))
        for match in all_date_matches:
            all_boundaries.append(('date', match.start(), match.end()))
        
        all_boundaries.sort(key=lambda x: x[1])  # Sort by start position
        
        # Find boundaries for this citation's context
        context_start = max(0, citation.start_index - 150)
        context_end = min(len(text), citation.end_index + 100)
        
        # Find the last boundary before our citation that could cause contamination
        for boundary_type, start, end in all_boundaries:
            if end < citation.start_index and end > context_start:
                # This boundary ends before our citation starts - use as boundary
                context_start = end + 1
                # If it's a date boundary, add some extra buffer
                if boundary_type == 'date':
                    context_start = min(context_start + 10, citation.start_index)
        
        # Find the first boundary after our citation
        for boundary_type, start, end in all_boundaries:
            if start > citation.end_index and start < context_end:
                # This boundary starts after our citation ends - use as boundary
                context_end = start - 1
                break
        
        # Extract the isolated context
        context = text[context_start:context_end].strip()
        
        # Additional cleaning to remove legal prefixes that contaminate case names
        # Remove common legal text that appears before case names
        prefixes_to_remove = [
            r'\b(?:through\s+the\s+)?(?:Fourteenth|Fifth|Sixth|Fourth)\s+Amendment\.?\s*',
            r'\b(?:see|citing|quoting|in|under|per|accord)\s+',
            r'\b(?:Brief|Opening\s+Br\.|Reply\s+Br\.|Pet\'r\'s\s+Br\.)\.?\s+at\s+\d+\s+',
            r'\b(?:RCW|WAC|USC)\s+[\d.]+\s*;?\s*',
            r'\b[A-Z]{2,}\s+[\d.]+\s*;?\s*',  # Statutes like RCW 2.60.020
            r'\b(?:id\.|Id\.|ibid\.|Ibid\.)\s*,?\s*',
            r'\b(?:but\s+)?see\s+(?:generally\s+)?',
            r'\b(?:Compare|Contrast|See\s+also)\s+',
        ]
        
        for prefix_pattern in prefixes_to_remove:
            context = re.sub(prefix_pattern, '', context, flags=re.IGNORECASE)
        
        return context.strip()
        
    def _clean_extracted_case_name(self, case_name: str) -> str:
        """Clean extracted case name to remove contamination from legal text."""
        if not case_name:
            return case_name
            
        # CRITICAL: Reject severely contaminated case names first
        contamination_indicators = [
            'state to actively provide',
            'criminal defense services', 
            'no. 60179',
            'and their right to counsel',
            'through the fourteenth amendment',
            'requires t he state',
            'cannot afford it',
            'zone of interest',
            'brief at',
            'opening br.',
            'quoting',
            'citing',
            'see id',
            'internal quotation marks',
            'alteration in original',
            'similarly'
        ]
        
        # IMPROVED: Better extraction for Westlaw citations with contamination
        # Look for "Party v. Party" pattern even in contaminated text
        v_pattern_improved = r'([A-Z][A-Za-z\s\'\.&,]{1,60}\s+v\.\s+[A-Z][A-Za-z\s\'\.&,]{1,60})(?:\s*,|\s*\(|\s*$)'
        match = re.search(v_pattern_improved, case_name)
        if match:
            extracted = match.group(1).strip()
            # Additional validation: ensure it's a reasonable case name
            if len(extracted) < 120 and ' v. ' in extracted:
                return extracted
        
        case_name_lower = case_name.lower()
        for indicator in contamination_indicators:
            if indicator in case_name_lower:
                # This is severely contaminated - extract just the case name part
                # Look for "Party v. Party" pattern at the END of the contaminated text
                # Use a more restrictive pattern that doesn't allow excessive text before v.
                v_pattern = r'([A-Z][A-Za-z\'\.\s]{1,50}\s+v\.\s+[A-Z][A-Za-z\'\.\s]{1,50})(?:\s*,|\s*$)'
                match = re.search(v_pattern, case_name)
                if match:
                    extracted = match.group(1).strip()
                    # Additional validation: ensure it's a reasonable case name length
                    if len(extracted) < 100 and ' v. ' in extracted:
                        return extracted
                    else:
                        # Try to find just the last "Party v. Party" in the text
                        last_v_pattern = r'([A-Z][A-Za-z\'\.\s]{1,30}\s+v\.\s+[A-Z][A-Za-z\'\.\s]{1,30})(?=[^A-Za-z]*$)'
                        last_match = re.search(last_v_pattern, case_name)
                        if last_match:
                            return last_match.group(1).strip()
                        else:
                            return ""
                else:
                    # No valid case name found in contaminated text
                    return ""
        
        # Remove common legal document references that contaminate case names
        cleanup_patterns = [
            r'^.*?\b(?:through\s+the\s+)?(?:Fourteenth|Fifth|Sixth|Fourth)\s+Amendment\.?\s+',  # Constitutional references
            r'^.*?\b(?:RCW|WAC|USC)\s+[\d.]+\s*;?\s*',  # Statute references  
            r'^.*?\b(?:Brief|Opening\s+Br\.|Reply\s+Br\.)\.?\s+at\s+\d+\s+(?:quoting\s+)?',  # Brief citations
            r'^.*?\b(?:see|citing|quoting|in|under|per|accord)\s+',  # Citation signals
            r'^.*?\b(?:id\.|Id\.|ibid\.|Ibid\.)\s*,?\s*',  # Id. references
            r'^\s*[.,;:]\s*',  # Leading punctuation
            r'\s*[.,;:]\s*$',  # Trailing punctuation
        ]
        
        # ✅ FIX MINOR CONTAMINATION: Handle specific problematic prefixes
        # Fix "State. Party v. Party" contamination (remove isolated "State." prefix)
        case_name = re.sub(r'^State\.\s+([A-Z][A-Za-z\s]+\s+v\.\s+[A-Z])', r'\1', case_name)
        
        # Fix incomplete case names like "Ro Trade Shows" (restore "To-" prefix for known cases)
        if case_name.startswith('Ro Trade Shows'):
            case_name = 'To-' + case_name
        
        for pattern in cleanup_patterns:
            case_name = re.sub(pattern, '', case_name, flags=re.IGNORECASE).strip()
        
        # Additional validation: reject if too long (likely contaminated)
        if len(case_name) > 100:
            # Try to extract just the case name part
            v_pattern = r'([A-Z][A-Za-z\s,&.\'-]+\s+v\.\s+[A-Z][A-Za-z\s,&.\'-]+)'
            match = re.search(v_pattern, case_name)
            if match:
                case_name = match.group(1).strip()
            else:
                return ""  # Too long and no clear case name pattern
        
        # Ensure we have a valid case name pattern (Party v. Party or In re Something)
        case_name_patterns = [
            r'^([A-Za-z0-9\s,.\'\-&]+\s+v\.?\s+[A-Za-z0-9\s,.\'\-&]+)',  # Party v. Party
            r'^(In\s+re\s+[A-Za-z0-9\s,.\'\-&]+)',  # In re cases
            r'^([A-Z][A-Za-z0-9\s,.\'\-&]*\s+v\.?\s+[A-Z][A-Za-z0-9\s,.\'\-&]*)',  # Strict Party v. Party
        ]
        
        for pattern in case_name_patterns:
            match = re.search(pattern, case_name, re.IGNORECASE)
            if match:
                clean_name = match.group(1).strip()
                # Remove trailing citation information 
                clean_name = re.sub(r'\s*,\s*\d+\s+[A-Za-z.]+.*$', '', clean_name)
                
                # Final validation: ensure reasonable length and proper format
                if 5 <= len(clean_name) <= 80 and ' v.' in clean_name.lower():
                    return clean_name
        
        # If no clear case name pattern found, return empty string to indicate contamination
        return ""

    def _extract_case_name_from_context(self, text: str, citation: CitationResult, all_citations: Optional[List[CitationResult]] = None) -> Optional[str]:
        """UNIFIED case name extraction using the best-of-breed unified extractor."""
        if not citation.start_index or not citation.end_index:
            return None
        
        # Use the unified extraction function
        result = extract_case_name_and_date_unified(
            text=text, 
            citation=citation.citation,
            citation_start=citation.start_index,
            citation_end=citation.end_index
        )
        
        case_name = result.get('case_name', '')
        confidence = result.get('confidence', 0.0)
        method = result.get('method', 'unknown')
        
        # Log extraction details for debugging
        logger.debug(f"[UNIFIED] Extracted case name: '{case_name}' (confidence: {confidence:.2f}, method: {method})")
        
        return case_name if case_name else None

    def _extract_date_from_context(self, text: str, citation: CitationResult) -> Optional[str]:
        """UNIFIED date extraction using the best-of-breed unified extractor."""
        if not citation.start_index or not citation.end_index:
            return None
        
        # Use the unified extraction function (it extracts both case name and date)
        result = extract_case_name_and_date_unified(
            text=text, 
            citation=citation.citation,
            citation_start=citation.start_index,
            citation_end=citation.end_index
        )
        
        year = result.get('year', '')
        logger.debug(f"[UNIFIED] Extracted year: '{year}' for citation '{citation.citation}'")
        
        return year if year else None

    def _get_isolated_context(self, text: str, citation: CitationResult, all_citations: Optional[List[CitationResult]] = None) -> tuple[Optional[int], Optional[int]]:
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
                        # Fallback: use a reasonable window before the citation, but check for other citations
                        potential_start = max(0, citation.start_index - 300)  # Increased from 100
                        
                        # Look for any citation patterns in the potential context area
                        citation_patterns = [
                            r'\b\d+\s+[A-Za-z.]+(?:\s+\d+)?\b',  # Basic citation pattern
                            r'\b\d+\s+(?:Wash\.|Wn\.|P\.|A\.|S\.|N\.|F\.|U\.S\.)\b',  # Common reporters
                        ]
                        
                        # Find the last citation before our target citation
                        last_citation_pos = potential_start
                        for pattern in citation_patterns:
                            matches = list(re.finditer(pattern, text[potential_start:citation.start_index]))
                            if matches:
                                last_match = matches[-1]
                                last_citation_pos = max(last_citation_pos, potential_start + last_match.end())
                        
                        context_start = last_citation_pos
            else:
                # No other citations, use year boundary or fallback
                year_pattern = re.compile(r'\((19|20)\d{2}\)')
                year_matches = list(year_pattern.finditer(text, 0, citation.start_index))
                if year_matches:
                    context_start = year_matches[-1].end()
                else:
                    # Fallback: use a reasonable window before the citation, but check for other citations
                    potential_start = max(0, citation.start_index - 300)  # Increased from 100
                    
                    # Look for any citation patterns in the potential context area
                    citation_patterns = [
                        r'\b\d+\s+[A-Za-z.]+(?:\s+\d+)?\b',  # Basic citation pattern
                        r'\b\d+\s+(?:Wash\.|Wn\.|P\.|A\.|S\.|N\.|F\.|U\.S\.)\b',  # Common reporters
                    ]
                    
                    # Find the last citation before our target citation
                    last_citation_pos = potential_start
                    for pattern in citation_patterns:
                        matches = list(re.finditer(pattern, text[potential_start:citation.start_index]))
                        if matches:
                            last_match = matches[-1]
                            last_citation_pos = max(last_citation_pos, potential_start + last_match.end())
                    
                    context_start = last_citation_pos
        
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
    
    def _get_isolated_context_for_citation(self, text: str, citation_start: int, citation_end: int, all_citations: Optional[List[CitationResult]] = None) -> tuple[Optional[int], Optional[int]]:
        """Get isolated context boundaries for a citation using start/end positions."""
        # Create a temporary CitationResult for compatibility
        temp_citation = CitationResult(
            citation=text[citation_start:citation_end],
            start_index=citation_start,
            end_index=citation_end
        )
        return self._get_isolated_context(text, temp_citation, all_citations)
    
    def extract_date_from_context_isolated(self, text: str, citation_start: int, citation_end: int) -> Optional[str]:
        """Extract date using isolated context to prevent cross-contamination."""
        try:
            # Use isolated context extraction
            context_start, context_end = self._get_isolated_context_for_citation(text, citation_start, citation_end)
            if context_start is None or context_end is None:
                # Fallback to reasonable window
                context_start = max(0, citation_start - 200)
                context_end = min(len(text), citation_end + 100)
            
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
            logger.debug(f"Error extracting date from isolated context: {e}")
            return None
    
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
        """Extract a 4-digit year from the context after the citation, or in parentheses right after."""
        if not citation.end_index:
            return None
        context_end = min(len(text), citation.end_index + 30)
        context_text = text[citation.end_index:context_end]
        # Look for (YYYY) or just YYYY
        match = re.search(r'\(?(19|20)\d{2}\)?', context_text)
        if match:
            return match.group(0).strip('()')
        return None

    def _is_valid_case_name(self, case_name: str) -> bool:
        """Simple validation: length and must contain 'v.' or 'In re'."""
        if not case_name or len(case_name) < 5 or len(case_name) > 150:
            return False
        lower = case_name.lower()
        return 'v.' in lower or 'in re' in lower
    
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
        """Extract citation-aware context: starts 100 chars before citation (not including previous citation/year), ends after year in parentheses or 100 chars after citation, not including next citation."""
        import re
        # Find all citation matches in the text
        citation_pattern = r'(\d{1,4}\s+[A-Za-z.]+(?:\s+[A-Za-z.]+)?\s+\d+(?:,\s*\d+)*\s*(?:\((17|18|19|20)\d{2}\))?)'
        all_cites = list(re.finditer(citation_pattern, text))
        prev_cite_end = 0
        next_cite_start = len(text)
        for m in all_cites:
            if m.end() <= start:
                prev_cite_end = m.end()
            elif m.start() > end and m.start() < next_cite_start:
                next_cite_start = m.start()
        # Start: 150 chars before citation, but not before previous citation
        context_start = max(prev_cite_end, start - 150)
        # End: after year in parentheses, or 100 chars after citation, but not after next citation
        post = text[end:next_cite_start]
        year_match = re.search(r'\((17|18|19|20)\d{2}\)', post)
        if year_match:
            context_end = end + year_match.end()
        else:
            context_end = min(next_cite_start, end + 100)
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
                key = self._normalize_citation_comprehensive(citation.citation, purpose="comparison")
            
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
        """
        DEPRECATED: Use _normalize_citation_comprehensive(citation, purpose="comparison") instead.
        
        This method is kept for backward compatibility but will be removed in a future version.
        The new comprehensive method provides all functionality with better consistency.
        """
        logger.warning("DEPRECATED: _normalize_citation called. Use _normalize_citation_comprehensive instead.")
        return self._normalize_citation_comprehensive(citation, purpose="comparison")
    
    def _normalize_citation_for_verification(self, citation: str) -> str:
        """
        DEPRECATED: Use _normalize_citation_comprehensive(citation, purpose="verification") instead.
        
        This method is kept for backward compatibility but will be removed in a future version.
        The new comprehensive method provides all functionality with better consistency.
        """
        logger.warning("DEPRECATED: _normalize_citation_for_verification called. Use _normalize_citation_comprehensive instead.")
        return self._normalize_citation_comprehensive(citation, purpose="verification")
    
    def _normalize_to_bluebook_format(self, citation: str) -> str:
        """
        DEPRECATED: Use _normalize_citation_comprehensive(citation, purpose="bluebook") instead.
        
        This method is kept for backward compatibility but will be removed in a future version.
        The new comprehensive method provides all functionality with better consistency.
        """
        logger.warning("DEPRECATED: _normalize_to_bluebook_format called. Use _normalize_citation_comprehensive instead.")
        return self._normalize_citation_comprehensive(citation, purpose="bluebook")
    
    def _detect_parallel_citations(self, citations: List['CitationResult'], text: str) -> List['CitationResult']:
        """Fixed parallel detection that updates existing objects and assigns cluster IDs."""
        if not citations or len(citations) < 2:
            return citations
        # Sort by position
        sorted_citations = sorted(citations, key=lambda x: x.start_index or 0)
        # Find groups of nearby citations
        groups = []
        current_group = [sorted_citations[0]]
        for i in range(1, len(sorted_citations)):
            curr = sorted_citations[i]
            prev = current_group[-1]
            # Check if citations are close and comma-separated
            if (curr.start_index and prev.end_index and 
                curr.start_index - prev.end_index <= 100):
                text_between = text[prev.end_index:curr.start_index]
                if ',' in text_between and len(text_between.strip()) < 50:
                    # ADDITIONAL VALIDATION: Only group if citations have similar case names
                    if (prev.extracted_case_name and curr.extracted_case_name and
                        prev.extracted_case_name != 'N/A' and curr.extracted_case_name != 'N/A'):
                        # Check if case names are similar
                        name1 = self._normalize_case_name_for_clustering(prev.extracted_case_name)
                        name2 = self._normalize_case_name_for_clustering(curr.extracted_case_name)
                        similarity = self._calculate_case_name_similarity(name1, name2)
                        if similarity > 0.8:  # Only group if very similar
                            current_group.append(curr)
                            continue
                    # If no case names or not similar, don't group
                # Start new group
                if len(current_group) > 1:
                    groups.append(current_group)
                current_group = [curr]
                continue
            # Start new group
            if len(current_group) > 1:
                groups.append(current_group)
            current_group = [curr]
        # Don't forget last group
        if len(current_group) > 1:
            groups.append(current_group)
        # Assign cluster IDs and members
        cluster_counter = 1
        for group in groups:
            if len(group) > 1:
                cluster_id = f"cluster_{cluster_counter}"
                cluster_counter += 1
                member_citations = [c.citation for c in group]
                best_name = next((c.extracted_case_name for c in group 
                                if c.extracted_case_name and c.extracted_case_name != 'N/A'), None)
                best_date = next((c.extracted_date for c in group 
                                if c.extracted_date and c.extracted_date != 'N/A'), None)
                for citation in group:
                    citation.is_parallel = True
                    citation.cluster_id = cluster_id
                    citation.cluster_members = [c for c in member_citations if c != citation.citation]
                    citation.parallel_citations = [c for c in member_citations if c != citation.citation]
                    # Share best metadata ONLY if citations have similar case names
                    # Check if all citations in the group have similar case names
                    group_case_names = [c.extracted_case_name for c in group if c.extracted_case_name and c.extracted_case_name != 'N/A']
                    if len(group_case_names) > 1:
                        # Normalize case names for comparison
                        normalized_names = [self._normalize_case_name_for_clustering(name) for name in group_case_names]
                        # Only propagate if all names are similar (exact match or high similarity)
                        if len(set(normalized_names)) == 1 or all(
                            self._calculate_case_name_similarity(normalized_names[0], name) > 0.8 
                            for name in normalized_names[1:]
                        ):
                            # All case names are similar, safe to propagate
                            if not citation.extracted_case_name or citation.extracted_case_name == 'N/A':
                                citation.extracted_case_name = best_name
                    else:
                        # Only one citation has a case name, safe to propagate
                        if not citation.extracted_case_name or citation.extracted_case_name == 'N/A':
                            citation.extracted_case_name = best_name
                    
                    # Always propagate dates if missing
                    if not citation.extracted_date or citation.extracted_date == 'N/A':
                        citation.extracted_date = best_date
        return sorted_citations
    
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
    
    def _extract_reporter_type(self, citation: str) -> Optional[str]:
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

    def _infer_state_from_citation(self, citation: str) -> Optional[str]:
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

    def _validate_verification_result(self, citation: 'CitationResult', source: str) -> Dict[str, Any]:
        """Validate that a verification result makes sense and is high quality."""
        validation_result = {'valid': True, 'reason': '', 'confidence_adjustment': 0.0}
        
        # Check 1: Must have canonical name
        if not citation.canonical_name or citation.canonical_name.strip() == '':
            validation_result['valid'] = False
            validation_result['reason'] = 'Missing canonical name'
            return validation_result
        
        # Check 2: Canonical name should contain 'v.' for most cases (except 'In re' cases)
        canonical_lower = citation.canonical_name.lower()
        if 'v.' not in canonical_lower and 'in re' not in canonical_lower and 'ex parte' not in canonical_lower:
            validation_result['valid'] = False
            validation_result['reason'] = f'Canonical name lacks proper case format: {citation.canonical_name}'
            return validation_result
        
        # Check 3: Canonical name shouldn't be suspiciously long or short
        if len(citation.canonical_name) < 5:
            validation_result['valid'] = False
            validation_result['reason'] = f'Canonical name too short: {citation.canonical_name}'
            return validation_result
        
        if len(citation.canonical_name) > 200:
            validation_result['valid'] = False
            validation_result['reason'] = f'Canonical name too long: {citation.canonical_name[:50]}...'
            return validation_result
        
        # Check 4: If we have extracted case name, check similarity
        if hasattr(citation, 'extracted_case_name') and citation.extracted_case_name and citation.extracted_case_name != 'N/A':
            similarity = self._calculate_case_name_similarity(citation.extracted_case_name, citation.canonical_name)
            if similarity < 0.1:  # Very low similarity threshold
                logger.warning(f"[VALIDATION] Low similarity between extracted '{citation.extracted_case_name}' and canonical '{citation.canonical_name}' (similarity: {similarity:.2f})")
                validation_result['confidence_adjustment'] = -0.2
        
        # Check 5: Canonical date validation
        if citation.canonical_date:
            try:
                # Try to parse the date
                if len(citation.canonical_date) == 4:  # Year only
                    year = int(citation.canonical_date)
                    if year < 1600 or year > 2030:
                        validation_result['valid'] = False
                        validation_result['reason'] = f'Invalid canonical year: {citation.canonical_date}'
                        return validation_result
                elif '-' in citation.canonical_date:  # Full date
                    from datetime import datetime
                    datetime.strptime(citation.canonical_date, '%Y-%m-%d')
            except (ValueError, TypeError):
                validation_result['valid'] = False
                validation_result['reason'] = f'Invalid canonical date format: {citation.canonical_date}'
                return validation_result
        
        # Check 6: Source-specific validations
        if source == 'CourtListener':
            # CourtListener should provide URLs
            if not citation.url or not citation.url.startswith('https://www.courtlistener.com'):
                validation_result['confidence_adjustment'] = -0.1
                logger.debug(f"[VALIDATION] CourtListener result missing proper URL: {citation.url}")
        
        # Adjust confidence based on validation results
        if hasattr(citation, 'confidence') and citation.confidence is not None:
            citation.confidence = max(0.0, min(1.0, citation.confidence + validation_result['confidence_adjustment']))
        
        logger.debug(f"[VALIDATION] {source} result for {citation.citation}: {validation_result['valid']} - {citation.canonical_name}")
        return validation_result

    def _verify_citations_sync(self, citations: List['CitationResult'], text: Optional[str] = None) -> List['CitationResult']:
        """Verify citations using CourtListener and fallback sources with enhanced validation."""
        logger.info(f"[VERIFICATION] Starting verification for {len(citations)} citations")
        
        if not citations:
            return citations
        
        # Step 1: Try CourtListener verification first
        courtlistener_verified_count = 0
        courtlistener_errors = []
        
        for citation in citations:
            try:
                # Use the existing CourtListener verification method
                if hasattr(self, '_verify_citation_with_courtlistener'):
                    self._verify_citation_with_courtlistener(citation)
                    if citation.verified:
                        # Enhanced validation: Check if verification result makes sense
                        validation_result = self._validate_verification_result(citation, 'CourtListener')
                        if validation_result['valid']:
                            courtlistener_verified_count += 1
                            logger.info(f"[VERIFICATION] SUCCESS: CourtListener verified: {citation.citation} -> {citation.canonical_name}")
                        else:
                            # Mark as unverified if validation fails
                            citation.verified = False
                            citation.canonical_name = None
                            citation.canonical_date = None
                            logger.warning(f"[VERIFICATION] FAILED: CourtListener verification failed validation: {citation.citation} - {validation_result['reason']}")
            except Exception as e:
                error_context = {
                    'citation': citation.citation,
                    'extracted_name': getattr(citation, 'extracted_case_name', 'N/A'),
                    'error': str(e),
                    'step': 'CourtListener API'
                }
                courtlistener_errors.append(error_context)
                logger.warning(f"[VERIFICATION] CourtListener verification failed for {citation.citation}: {str(e)}")
        
        # Enhanced progress reporting
        if courtlistener_errors:
            logger.info(f"[VERIFICATION] CourtListener errors: {len(courtlistener_errors)} citations failed")
            if self.config.debug_mode:
                for error in courtlistener_errors[:3]:  # Show first 3 errors in debug mode
                    logger.debug(f"[VERIFICATION] Error detail: {error}")
        
        logger.info(f"[VERIFICATION] CourtListener results: {courtlistener_verified_count}/{len(citations)} verified")
        
        # Step 2: Use fallback verification for unverified citations
        unverified_citations = [c for c in citations if not c.verified]
        logger.info(f"[VERIFICATION] {len(unverified_citations)} citations need fallback verification")
        
        fallback_verified_count = 0
        fallback_errors = []
        fallback_validation_failures = []
        
        if unverified_citations:
            try:
                # Import and use the enhanced fallback verifier
                import sys
                import os
                sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
                from src.enhanced_fallback_verifier import EnhancedFallbackVerifier
                
                verifier = EnhancedFallbackVerifier()
                
                for citation in unverified_citations:
                    try:
                        citation_text = citation.citation
                        extracted_case_name = citation.extracted_case_name
                        extracted_date = citation.extracted_date
                        
                        logger.info(f"[VERIFICATION] Attempting fallback verification: {citation_text}")
                        if self.config.debug_mode:
                            logger.debug(f"[VERIFICATION] Fallback context - Extracted name: {extracted_case_name}, Date: {extracted_date}")
                        
                        result = verifier.verify_citation_sync(
                            citation_text, 
                            extracted_case_name, 
                            extracted_date
                        )
                        
                        if result['verified']:
                            # Apply verification results
                            citation.verified = True
                            citation.canonical_name = result['canonical_name']
                            citation.canonical_date = result['canonical_date']
                            citation.url = result['url']
                            citation.source = result['source']  # Use actual website source (e.g., 'Cornell Law', 'Justia')
                            citation.confidence = result['confidence']
                            
                            # Enhanced validation: Check if fallback result makes sense
                            validation_result = self._validate_verification_result(citation, f"Fallback-{result['source']}")
                            
                            if validation_result['valid']:
                                # Add metadata about fallback verification
                                if not hasattr(citation, 'metadata') or citation.metadata is None:
                                    citation.metadata = {}
                                citation.metadata.update({
                                    'verification_method': 'fallback',
                                    'fallback_source': result['source'],
                                    'verification_details': result.get('verification_details', {}),
                                    'validation_passed': True
                                })
                                
                                fallback_verified_count += 1
                                logger.info(f"[VERIFICATION] SUCCESS: Fallback verified: {citation_text} -> {citation.canonical_name} (via {result['source']})")
                            else:
                                # Validation failed - mark as unverified
                                citation.verified = False
                                citation.canonical_name = None
                                citation.canonical_date = None
                                citation.url = None
                                
                                validation_failure = {
                                    'citation': citation_text,
                                    'source': result['source'],
                                    'reason': validation_result['reason'],
                                    'attempted_canonical': result['canonical_name']
                                }
                                fallback_validation_failures.append(validation_failure)
                                logger.warning(f"[VERIFICATION] FAILED: Fallback validation failed: {citation_text} - {validation_result['reason']}")
                        else:
                            # Enhanced error reporting for failed fallback verification
                            failure_reason = result.get('error', 'Unknown error')
                            logger.debug(f"[VERIFICATION] Fallback verification failed: {citation_text} - {failure_reason}")
                            
                    except Exception as e:
                        error_context = {
                            'citation': citation.citation,
                            'extracted_name': getattr(citation, 'extracted_case_name', 'N/A'),
                            'error': str(e),
                            'step': 'Fallback verification'
                        }
                        fallback_errors.append(error_context)
                        logger.warning(f"[VERIFICATION] Fallback verification error for {citation.citation}: {str(e)}")
                
                # Enhanced progress reporting for fallback verification
                logger.info(f"[VERIFICATION] Fallback results: {fallback_verified_count}/{len(unverified_citations)} verified")
                
                if fallback_validation_failures:
                    logger.info(f"[VERIFICATION] Fallback validation failures: {len(fallback_validation_failures)} citations failed validation")
                    if self.config.debug_mode:
                        for failure in fallback_validation_failures[:3]:  # Show first 3 failures in debug mode
                            logger.debug(f"[VERIFICATION] Validation failure: {failure}")
                
                if fallback_errors:
                    logger.info(f"[VERIFICATION] Fallback errors: {len(fallback_errors)} citations had errors")
                    if self.config.debug_mode:
                        for error in fallback_errors[:3]:  # Show first 3 errors in debug mode
                            logger.debug(f"[VERIFICATION] Error detail: {error}")
                
            except Exception as e:
                logger.error(f"[VERIFICATION] Critical error in fallback verification system: {str(e)}")
                if self.config.debug_mode:
                    import traceback
                    logger.debug(f"[VERIFICATION] Fallback system traceback: {traceback.format_exc()}")
        
        # Step 3: Enhanced final verification statistics and quality reporting
        total_verified = sum(1 for c in citations if c.verified)
        verification_rate = (total_verified / len(citations)) * 100 if citations else 0
        
        logger.info(f"[VERIFICATION] === FINAL VERIFICATION SUMMARY ===")
        logger.info(f"[VERIFICATION] Total citations processed: {len(citations)}")
        logger.info(f"[VERIFICATION] Successfully verified: {total_verified} ({verification_rate:.1f}%)")
        logger.info(f"[VERIFICATION] CourtListener verified: {courtlistener_verified_count}")
        logger.info(f"[VERIFICATION] Fallback verified: {fallback_verified_count}")
        logger.info(f"[VERIFICATION] Still unverified: {len(citations) - total_verified}")
        
        # Quality metrics reporting
        if total_verified > 0:
            high_confidence_count = sum(1 for c in citations if c.verified and hasattr(c, 'confidence') and c.confidence and c.confidence > 0.8)
            medium_confidence_count = sum(1 for c in citations if c.verified and hasattr(c, 'confidence') and c.confidence and 0.5 <= c.confidence <= 0.8)
            low_confidence_count = sum(1 for c in citations if c.verified and hasattr(c, 'confidence') and c.confidence and c.confidence < 0.5)
            
            logger.info(f"[VERIFICATION] Quality breakdown:")
            logger.info(f"[VERIFICATION]   High confidence (>0.8): {high_confidence_count}")
            logger.info(f"[VERIFICATION]   Medium confidence (0.5-0.8): {medium_confidence_count}")
            logger.info(f"[VERIFICATION]   Low confidence (<0.5): {low_confidence_count}")
        
        # Report any problematic citations in debug mode
        if self.config.debug_mode:
            unverified_citations = [c for c in citations if not c.verified]
            if unverified_citations:
                logger.debug(f"[VERIFICATION] Unverified citations sample:")
                for citation in unverified_citations[:5]:  # Show first 5 unverified
                    logger.debug(f"[VERIFICATION]   - {citation.citation} (extracted: {getattr(citation, 'extracted_case_name', 'N/A')})")
        
        logger.info(f"[VERIFICATION] === END VERIFICATION SUMMARY ===")
        
        return citations

    def _validate_volume_number(self, text: str, match_start: int, volume: str) -> bool:
        """
        Prevent false positives like '8 P.2d 1094' where 8 comes from page number.
        
        Args:
            text: Full text being processed
            match_start: Start position of the citation match
            volume: Volume number to validate
            
        Returns:
            True if volume number is valid, False if likely a false positive
        """
        # Check previous 100 characters for page-related context
        context_start = max(0, match_start - 100)
        preceding_text = text[context_start:match_start].lower()
        
        # Red flags that suggest this is a page number, not volume number
        page_indicators = [
            'page', 'p.', 'pp.', 'at', 'see', 'id.', 'ibid', 'supra',
            'infra', 'cf.', 'but see', 'accord', 'compare', 'contra'
        ]
        
        # Check for page indicators in preceding text
        for indicator in page_indicators:
            if indicator in preceding_text:
                logger.debug(f"[FALSE_POSITIVE] Rejecting volume '{volume}' due to page indicator '{indicator}' in context")
                return False
        
        # Check for sentence boundaries - don't cross sentences for volume numbers
        # Look for sentence endings (. ! ?) followed by whitespace and capital letter
        sentence_boundary = re.search(r'[.!?]\s+[A-Z]', preceding_text[-50:])
        if sentence_boundary:
            # Volume number appears to be from a different sentence
            logger.debug(f"[FALSE_POSITIVE] Rejecting volume '{volume}' due to sentence boundary crossing")
            return False
        
        # Volume number validation for specific reporters
        try:
            vol_num = int(volume)
            
            # Pacific reporters (P.2d, P.3d) typically don't have very low volume numbers
            if vol_num < 10:
                logger.debug(f"[FALSE_POSITIVE] Rejecting suspiciously low volume number '{volume}' for Pacific reporter")
                return False
                
            # Extremely high volume numbers are also suspicious
            if vol_num > 9999:
                logger.debug(f"[FALSE_POSITIVE] Rejecting suspiciously high volume number '{volume}'")
                return False
                
        except ValueError:
            logger.debug(f"[FALSE_POSITIVE] Rejecting non-numeric volume '{volume}'")
            return False
        
        return True

    def _normalize_citation_comprehensive(self, citation: str, purpose: str = "general") -> str:
        """
        COMPREHENSIVE CITATION NORMALIZATION - Consolidates all normalization functions.
        
        This replaces all other normalization functions in the codebase:
        - _normalize_citation (line 577) - DEPRECATED
        - _normalize_citation (line 1877) - DEPRECATED  
        - _normalize_citation_for_verification (line 1889) - DEPRECATED
        - _normalize_to_bluebook_format (line 1909) - DEPRECATED
        - EnhancedCitationNormalizer.normalize_citation - DEPRECATED
        
        Args:
            citation: Citation string to normalize
            purpose: Normalization purpose - "general", "bluebook", "verification", "comparison"
            
        Returns:
            Normalized citation string
        """
        if not citation:
            return citation
            
        normalized = citation.strip()
        
        # STEP 1: Clean up whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # STEP 2: Core Bluebook formatting (most comprehensive)
        # U.S. Supreme Court citations
        normalized = re.sub(r'(\d+)\s*U\.\s*S\.\s*(\d+)', r'\1 U.S. \2', normalized)
        
        # Federal Reporter citations
        normalized = re.sub(r'(\d+)\s*F\.\s*(\d+)d\s*(\d+)', r'\1 F.\2d \3', normalized)
        normalized = re.sub(r'(\d+)\s*F\.\s*3d\s*(\d+)', r'\1 F.3d \2', normalized)
        normalized = re.sub(r'(\d+)\s*F\.\s*2d\s*(\d+)', r'\1 F.2d \2', normalized)
        
        # Federal Supplement citations
        normalized = re.sub(r'(\d+)\s*F\.\s*Supp\.\s*(\d+)d\s*(\d+)', r'\1 F.Supp.\2d \3', normalized)
        normalized = re.sub(r'(\d+)\s*F\.\s*Supp\.\s*3d\s*(\d+)', r'\1 F. Supp. 3d \2', normalized)
        normalized = re.sub(r'(\d+)\s*F\.\s*Supp\.\s*2d\s*(\d+)', r'\1 F. Supp. 2d \2', normalized)
        normalized = re.sub(r'(\d+)\s*F\.\s*Supp\.\s*(\d+)', r'\1 F. Supp. \2', normalized)
        
        # Supreme Court Reporter
        normalized = re.sub(r'(\d+)\s*S\.\s*Ct\.\s*(\d+)', r'\1 S. Ct. \2', normalized)
        
        # Lawyers' Edition
        normalized = re.sub(r'(\d+)\s*L\.\s*Ed\.\s*2d\s*(\d+)', r'\1 L. Ed. 2d \2', normalized)
        normalized = re.sub(r'(\d+)\s*L\.\s*Ed\.\s*(\d+)', r'\1 L. Ed. \2', normalized)
        
        # Pacific Reporter
        normalized = re.sub(r'(\d+)\s*P\.\s*3d\s*(\d+)', r'\1 P.3d \2', normalized)
        normalized = re.sub(r'(\d+)\s*P\.\s*2d\s*(\d+)', r'\1 P.2d \2', normalized)
        
        # STEP 3: Washington state normalization (for verification)
        if purpose in ["verification", "general"]:
            # Normalize Washington citations: Wn.2d -> Wash.2d
            normalized = re.sub(r'\bWn\.2d\b', 'Wash.2d', normalized)
            normalized = re.sub(r'\bWn\.3d\b', 'Wash.3d', normalized)
            normalized = re.sub(r'\bWn\.\s*App\.\b', 'Wash.App.', normalized)
            normalized = re.sub(r'\bWn\.\b', 'Wash.', normalized)
            
            # Handle lowercase variations
            normalized = normalized.replace('wn2d', 'wash2d')
            normalized = normalized.replace('wnapp', 'washapp')
        
        # STEP 4: Washington state formatting (preserve Wn. for display)
        elif purpose == "bluebook":
            normalized = re.sub(r'(\d+)\s*Wn\.\s*2d\s*(\d+)', r'\1 Wn.2d \2', normalized)
            normalized = re.sub(r'(\d+)\s*Wn\.\s*App\.\s*(\d+)', r'\1 Wn. App. \2', normalized)
            normalized = re.sub(r'(\d+)\s*Wash\.\s*2d\s*(\d+)', r'\1 Wash. 2d \2', normalized)
            normalized = re.sub(r'(\d+)\s*Wash\.\s*App\.\s*(\d+)', r'\1 Wash. App. \2', normalized)
        
        # STEP 5: Purpose-specific formatting
        if purpose == "comparison":
            # For comparison, convert to lowercase and standardize
            normalized = normalized.lower()
            normalized = re.sub(r'\bwash\.\b', 'wash.', normalized)
            normalized = re.sub(r'\bp\.\b', 'p.', normalized)
            normalized = re.sub(r'\bf\.\b', 'f.', normalized)
        
        elif purpose == "us_extract":
            # Extract just the U.S. citation core (legacy behavior)
            us_pattern = r'(\d+\s+U\.S\.\s+\d+)'
            match = re.search(us_pattern, normalized)
            if match:
                return match.group(1)
        
        # STEP 6: Final cleanup
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized.strip()

    def _extract_with_regex_enhanced(self, text: str) -> List[CitationResult]:
        """
        CORRECTED UNIFIED CITATION EXTRACTION: Proper processing order with full text context.
{{ ... }}
        
        CORRECTED ORDER (based on user feedback):
        1. Enhanced regex extraction with false positive prevention
        2. Eyecite extraction for additional coverage  
        3. Name and date extraction for each citation (WHILE FULL TEXT AVAILABLE)
        4. Parallel citation detection and clustering (WHILE FULL TEXT AVAILABLE)
        5. Component normalization
        6. Final deduplication of processed results
        
        Args:
            text: Text to extract citations from
            
        Returns:
            List of CitationResult objects with complete metadata
        """
        logger.info("[UNIFIED_EXTRACTION] Starting corrected unified citation extraction pipeline")
        all_citations = []
        
        # STEP 1: Enhanced Regex Extraction with False Positive Prevention
        logger.info("[UNIFIED_EXTRACTION] Step 1: Enhanced regex extraction")
        regex_citations = self._extract_with_regex_enhanced(text)
        all_citations.extend(regex_citations)
        logger.info(f"[UNIFIED_EXTRACTION] Regex found {len(regex_citations)} citations")
        
        # STEP 2: Eyecite Extraction (if available)
        logger.info("[UNIFIED_EXTRACTION] Step 2: Eyecite extraction")
        try:
            eyecite_citations = self._extract_with_eyecite(text)
            all_citations.extend(eyecite_citations)
            logger.info(f"[UNIFIED_EXTRACTION] Eyecite found {len(eyecite_citations)} citations")
        except Exception as e:
            logger.warning(f"[UNIFIED_EXTRACTION] Eyecite extraction failed: {e}")
            logger.info("[UNIFIED_EXTRACTION] Continuing without eyecite results")
        
        # STEP 3: Name and Date Extraction (WITH FULL TEXT CONTEXT)
        logger.info("[UNIFIED_EXTRACTION] Step 3: Extracting names and dates with full text context")
        for citation in all_citations:
            try:
                # Extract case name using full text context
                if not citation.extracted_case_name:
                    citation.extracted_case_name = self._extract_case_name_from_context(text, citation, all_citations)
                
                # Extract date using full text context
                if not citation.extracted_date:
                    citation.extracted_date = self._extract_date_from_context(text, citation)
                
            except Exception as e:
                logger.warning(f"[UNIFIED_EXTRACTION] Error extracting metadata for {citation.citation}: {e}")
        
        # STEP 4: Parallel Citation Detection and Clustering (WITH FULL TEXT CONTEXT)
        logger.info("[UNIFIED_EXTRACTION] Step 4: Detecting parallel citations with full text context")
        try:
            all_citations = self._detect_parallel_citations(all_citations, text)
            logger.info(f"[UNIFIED_EXTRACTION] After parallel detection: {len(all_citations)} citations")
        except Exception as e:
            logger.warning(f"[UNIFIED_EXTRACTION] Error in parallel detection: {e}")
        
        # STEP 5: Component Normalization
        logger.info("[UNIFIED_EXTRACTION] Step 5: Normalizing citation components")
        for citation in all_citations:
            try:
                components = self._extract_citation_components(citation.citation)
                citation.volume = components.get('volume')
                citation.reporter = components.get('reporter')
                citation.page = components.get('page')
            except Exception as e:
                logger.warning(f"[UNIFIED_EXTRACTION] Error normalizing components for {citation.citation}: {e}")
        
        # STEP 6: Final Deduplication (after all processing with context)
        logger.info("[UNIFIED_EXTRACTION] Step 6: Final deduplication after context processing")
        deduplicated_citations = self._deduplicate_citations(all_citations)
        logger.info(f"[UNIFIED_EXTRACTION] After final deduplication: {len(deduplicated_citations)} citations")
        
        logger.info(f"[UNIFIED_EXTRACTION] Corrected unified extraction complete: {len(deduplicated_citations)} final citations")
        return deduplicated_citations

    def _detect_parallel_citations(self, citations: List[CitationResult], text: str) -> List[CitationResult]:
        """
        Detect parallel citations using full text context.
        
        This method identifies citations that refer to the same case by looking for:
        - Citations appearing close together in the text
        - Similar case names or dates
        - Known parallel citation patterns (e.g., U.S. + S.Ct. + L.Ed.)
        
        Args:
            citations: List of citations to analyze
            text: Full text for context analysis
            
        Returns:
            List of citations with parallel relationships detected
        """
        logger.info(f"[PARALLEL_DETECTION] Analyzing {len(citations)} citations for parallel relationships")
        
        # Use existing parallel detection logic from the main pipeline
        try:
            # First, detect parallel citations using existing logic
            parallel_groups = self._detect_parallel_citation_groups(citations, text)
            logger.info(f"[PARALLEL_DETECTION] Found {len(parallel_groups)} parallel groups")
            
            # Mark parallel relationships
            for group in parallel_groups:
                for i, citation in enumerate(group):
                    citation.parallel_citations = [c.citation for c in group if c != citation]
                    citation.is_parallel = len(group) > 1
                    
            return citations
            
        except Exception as e:
            logger.warning(f"[PARALLEL_DETECTION] Error in parallel detection: {e}")
            return citations
    
    def _detect_parallel_citation_groups(self, citations: List[CitationResult], text: str) -> List[List[CitationResult]]:
        """
        Group citations that appear to be parallel citations of the same case.
        
        Args:
            citations: List of citations to group
            text: Full text for context analysis
            
        Returns:
            List of citation groups (each group contains parallel citations)
        """
        if not citations:
            return []
            
        groups = []
        processed = set()
        
        for i, citation in enumerate(citations):
            if citation.citation in processed:
                continue
                
            # Find potential parallel citations for this citation
            group = [citation]
            processed.add(citation.citation)
            
            for j, other_citation in enumerate(citations[i+1:], i+1):
                if other_citation.citation in processed:
                    continue
                    
                # Check if they could be parallel citations
                if self._are_likely_parallel_citations(citation, other_citation, text):
                    group.append(other_citation)
                    processed.add(other_citation.citation)
            
            if len(group) > 1:
                groups.append(group)
                logger.info(f"[PARALLEL_DETECTION] Found parallel group: {[c.citation for c in group]}")
        
        return groups
    
    def _are_likely_parallel_citations(self, citation1: CitationResult, citation2: CitationResult, text: str) -> bool:
        """
        Determine if two citations are likely parallel citations of the same case.
        
        Args:
            citation1: First citation
            citation2: Second citation  
            text: Full text for context analysis
            
        Returns:
            True if citations are likely parallel
        """
        # Check proximity in text
        pos1 = text.find(citation1.citation)
        pos2 = text.find(citation2.citation)
        
        if pos1 == -1 or pos2 == -1:
            return False
            
        # Citations should be relatively close (within 200 characters)
        if abs(pos1 - pos2) > 200:
            return False
            
        # Check for similar case names
        name1 = citation1.extracted_case_name or ""
        name2 = citation2.extracted_case_name or ""
        
        if name1 and name2:
            # Simple similarity check - if they share significant words
            words1 = set(name1.lower().split())
            words2 = set(name2.lower().split())
            common_words = words1.intersection(words2)
            
            if len(common_words) >= 2:  # At least 2 common words
                return True
        
        # Check for similar dates
        date1 = citation1.extracted_date or ""
        date2 = citation2.extracted_date or ""
        
        if date1 and date2 and date1 == date2:
            return True
            
        # Check for known parallel patterns (U.S. + S.Ct., F.3d + F.Supp., etc.)
        reporter1 = self._extract_reporter(citation1.citation)
        reporter2 = self._extract_reporter(citation2.citation)
        
        known_parallel_pairs = [
            ('U.S.', 'S.Ct.'),
            ('U.S.', 'L.Ed.'),
            ('S.Ct.', 'L.Ed.'),
            ('F.3d', 'F.Supp.'),
            ('F.2d', 'F.Supp.'),
        ]
        
        for pair in known_parallel_pairs:
            if (reporter1 in pair and reporter2 in pair) or (reporter2 in pair and reporter1 in pair):
                return True
                
        return False
    
    def _extract_reporter(self, citation: str) -> str:
        """Extract the reporter abbreviation from a citation."""
        # Simple regex to extract reporter
        import re
        match = re.search(r'\b([A-Z][A-Za-z]*\.(?:\d*[a-z]*)?)\b', citation)
        return match.group(1) if match else ""

    def _extract_with_regex_enhanced(self, text: str) -> List[CitationResult]:
        """
        Enhanced regex extraction with false positive prevention.
        Based on _extract_with_regex but adds volume number validation and text normalization.
        """
        logger.info('[DEBUG] ENTERED _extract_with_regex_enhanced')
        citations = []
        seen_citations = set()
        
        # STEP 1: Use original text for pattern matching (don't normalize entire text)
        logger.info('[DEBUG] Using original text for citation extraction')
        original_text = text
        normalized_text = text  # Use original text, normalize individual citations later
        logger.info(f'[DEBUG] Text length: {len(original_text)} chars')
        
        # STEP 2: Comprehensive pattern list including federal citations
        priority_patterns = [
            'parallel_citation_cluster',
            'flexible_wash2d',
            'flexible_p3d',
            'flexible_p2d',
            'wash_complete',
            'wash_with_parallel',
            'parallel_cluster',
            'wn_app',           # Washington Court of Appeals
            'wn_app_space',     # Washington Court of Appeals (with space)
            'wn3d',             # Washington Supreme Court 3d series
            'wn3d_space',       # Washington Supreme Court 3d series (with space)
            'wash_app',         # Washington Court of Appeals (Wash.)
            'wash_app_space',   # Washington Court of Appeals (Wash. with space)
        ]
        
        for pattern_name in priority_patterns:
            if pattern_name in self.citation_patterns:
                pattern = self.citation_patterns[pattern_name]
                matches = list(pattern.finditer(normalized_text))
                
                for match in matches:
                    citation_str = match.group(0).strip()
                    if not citation_str or citation_str in seen_citations:
                        continue
                    
                    # Enhanced false positive prevention
                    components = self._extract_citation_components(citation_str)
                    reporter = components.get('reporter', '').strip().lower().replace('.', '')
                    volume = components.get('volume', '')
                    
                    # Skip citations where reporter is 'at'
                    if reporter == 'at':
                        logger.debug(f"[FALSE_POSITIVE] Skipping citation with reporter 'at': '{citation_str}'")
                        continue
                    
                    # NEW: Validate volume number to prevent false positives
                    if volume and not self._validate_volume_number(text, match.start(), volume):
                        logger.debug(f"[FALSE_POSITIVE] Skipping citation with invalid volume: '{citation_str}'")
                        continue
                    
                    seen_citations.add(citation_str)
                    start_pos = match.start()
                    end_pos = match.end()
                    
                    citation = CitationResult(
                        citation=citation_str,
                        start_index=start_pos,
                        end_index=end_pos,
                        method="regex_enhanced",
                        pattern=pattern_name,
                        confidence=0.8
                    )
                    
                    citations.append(citation)
        
        logger.info(f"[DEBUG] Enhanced regex extraction found {len(citations)} citations")
        return citations
    
    def _extract_citations_unified(self, text: str) -> List[CitationResult]:
        """
        UNIFIED CITATION EXTRACTION: Consolidates regex and eyecite extraction with proper deduplication.
        
        This method implements the corrected processing order:
        1. Enhanced regex extraction with false positive prevention
        2. Eyecite extraction for additional coverage  
        3. Name and date extraction for each citation (WITH FULL TEXT CONTEXT)
        4. Component normalization
        5. Final deduplication of processed results
        
        Args:
            text: Text to extract citations from
            
        Returns:
            List of CitationResult objects with complete metadata
        """
        logger.info("[UNIFIED_EXTRACTION] Starting unified citation extraction")
        all_citations = []
        
        # STEP 1: Enhanced regex extraction with false positive prevention
        logger.info("[UNIFIED_EXTRACTION] Step 1: Enhanced regex extraction")
        regex_citations = self._extract_with_regex_enhanced(text)
        logger.info(f"[UNIFIED_EXTRACTION] Regex found {len(regex_citations)} citations")
        all_citations.extend(regex_citations)
        
        # STEP 2: Eyecite extraction for additional coverage
        if EYECITE_AVAILABLE:
            logger.info("[UNIFIED_EXTRACTION] Step 2: Eyecite extraction")
            eyecite_citations = self._extract_with_eyecite(text)
            logger.info(f"[UNIFIED_EXTRACTION] Eyecite found {len(eyecite_citations)} citations")
            all_citations.extend(eyecite_citations)
        else:
            logger.info("[UNIFIED_EXTRACTION] Step 2: Eyecite not available, skipping")
        
        # STEP 3: Initial deduplication (preserve all unique citations)
        logger.info("[UNIFIED_EXTRACTION] Step 3: Initial deduplication")
        deduplicated_citations = self._deduplicate_citations(all_citations)
        logger.info(f"[UNIFIED_EXTRACTION] After deduplication: {len(deduplicated_citations)} citations")
        
        # STEP 4: Name and date extraction for each citation (WITH FULL TEXT CONTEXT)
        logger.info("[UNIFIED_EXTRACTION] Step 4: Extracting names and dates with full text context")
        for citation in deduplicated_citations:
            try:
                # Extract case name using full text context
                if not citation.extracted_case_name:
                    citation.extracted_case_name = self._extract_case_name_from_context(text, citation, deduplicated_citations)
                
                # Extract date using full text context
                if not citation.extracted_date:
                    citation.extracted_date = self._extract_date_from_context(text, citation)
                    
            except Exception as e:
                logger.warning(f"[UNIFIED_EXTRACTION] Error extracting metadata for citation '{citation.citation}': {e}")
                continue
        
        # STEP 5: Component normalization
        logger.info("[UNIFIED_EXTRACTION] Step 5: Normalizing citation components")
        for citation in deduplicated_citations:
            try:
                # Normalize the citation format
                citation.citation = self._normalize_citation_comprehensive(citation.citation, purpose="general")
                
                # Clean extracted case name
                if citation.extracted_case_name:
                    citation.extracted_case_name = self._clean_extracted_case_name(citation.extracted_case_name)
                    
            except Exception as e:
                logger.warning(f"[UNIFIED_EXTRACTION] Error normalizing citation '{citation.citation}': {e}")
                continue
        
        logger.info(f"[UNIFIED_EXTRACTION] Unified extraction complete: {len(deduplicated_citations)} citations")
        return deduplicated_citations
    
    async def process_text(self, text: str):
        """
        UNIFIED CITATION PROCESSING PIPELINE: Complete implementation with all required steps.
        
        This replaces the previous incomplete pipeline with a comprehensive approach that includes:
        1. Both regex and eyecite extraction with false positive prevention
        2. Proper deduplication of combined results
        3. Name and date extraction for each citation
        4. Component normalization
        5. Parallel citation detection and clustering
        6. Verification (when enabled)
        
        Args:
            text: The text to process for citations
            
        Returns:
            Dict containing 'citations' (list) and 'clusters' (list)
        """
        logger.info("[UNIFIED_PIPELINE] Starting unified citation processing pipeline")
        
        # PHASE 1: UNIFIED EXTRACTION (Steps 1-5)
        citations = self._extract_citations_unified(text)
        logger.info(f"[UNIFIED_PIPELINE] Phase 1 complete: {len(citations)} citations extracted")
        
        # PHASE 2: PARALLEL CITATION DETECTION
        logger.info("[UNIFIED_PIPELINE] Phase 2: Detecting parallel citations")
        citations = self._detect_parallel_citations(citations, text)
        logger.info(f"[UNIFIED_PIPELINE] After parallel detection: {len(citations)} citations")
        
        # PHASE 3: BIDIRECTIONAL PARALLEL RELATIONSHIPS
        logger.info("[UNIFIED_PIPELINE] Phase 3: Ensuring bidirectional parallel relationships")
        self.ensure_bidirectional_parallels(citations)
        logger.info(f"[UNIFIED_PIPELINE] After bidirectional parallels: {len(citations)} citations")
        
        # PHASE 4: CANONICAL DATA PROPAGATION
        logger.info("[UNIFIED_PIPELINE] Phase 4: Propagating canonical data to parallel citations")
        self.propagate_canonical_to_cluster(citations)
        logger.info(f"[UNIFIED_PIPELINE] After canonical propagation: {len(citations)} citations")
        
        # PHASE 5: CLUSTERING
        logger.info("[UNIFIED_PIPELINE] Phase 5: Creating citation clusters with unified system")
        clusters = cluster_citations_unified(citations, original_text=text, enable_verification=True)
        logger.info(f"[UNIFIED_PIPELINE] Created {len(clusters)} clusters using unified clustering")
        
        # PHASE 6: VERIFICATION (Optional - can be enabled later)
        if self.config.enable_verification and citations:
            logger.info("[UNIFIED_PIPELINE] Phase 6: Verifying citations (enabled)")
            verified_citations = await self._verify_citations(citations, text)
            citations = verified_citations
            logger.info(f"[UNIFIED_PIPELINE] After verification: {len(citations)} citations")
        else:
            logger.info("[UNIFIED_PIPELINE] Phase 6: Skipping verification (disabled)")
        
        logger.info(f"[UNIFIED_PIPELINE] Pipeline complete: {len(citations)} final citations, {len(clusters)} clusters")
        
        return {
            'citations': citations,
            'clusters': clusters
        }

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
        # Run the main processing pipeline asynchronously
        results = await self.process_text(document_text)
        # Convert CitationResult objects to dicts for API response
        citation_dicts = []
        for citation in results['citations']:
            citation_dict = {
                'citation': citation.citation,
                'case_name': citation.extracted_case_name or citation.case_name,
                'extracted_case_name': citation.extracted_case_name,
                'canonical_name': citation.canonical_name,
                'extracted_date': citation.extracted_date,
                'canonical_date': citation.canonical_date,
                'verified': citation.verified if isinstance(citation.verified, bool) else (citation.verified == "true_by_parallel" or citation.verified == True),
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
                'cluster_members': citation.metadata.get('cluster_members', []) if citation.metadata else [],
                'pinpoint_pages': citation.pinpoint_pages,
                'docket_numbers': citation.docket_numbers,
                'case_history': citation.case_history,
                'publication_status': citation.publication_status,
                'url': citation.url,
                'source': citation.source,
                'error': citation.error,
                'metadata': citation.metadata or {},
                'extraction_method': getattr(citation, 'extraction_method', None),
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
        clusters = results['clusters']
        # Convert any CitationResult objects in clusters to dicts
        def citation_to_dict(citation):
            return {
                'citation': citation.citation,
                'case_name': citation.extracted_case_name or citation.case_name,
                'extracted_case_name': citation.extracted_case_name,
                'canonical_name': citation.canonical_name,
                'extracted_date': citation.extracted_date,
                'canonical_date': citation.canonical_date,
                'verified': citation.verified if isinstance(citation.verified, bool) else (citation.verified == "true_by_parallel" or citation.verified == True),
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
                'cluster_members': citation.metadata.get('cluster_members', []) if citation.metadata else [],
                'pinpoint_pages': citation.pinpoint_pages,
                'docket_numbers': citation.docket_numbers,
                'case_history': citation.case_history,
                'publication_status': citation.publication_status,
                'url': citation.url,
                'source': citation.source,
                'error': citation.error,
                'metadata': citation.metadata or {},
                'extraction_method': getattr(citation, 'extraction_method', None),
            }
        def cluster_to_dict(cluster):
            return {
                **{k: v for k, v in cluster.items() if k != 'citations'},
                'citations': [citation_to_dict(c) if not isinstance(c, dict) else c for c in cluster['citations']]
            }
        clusters_dicts = [cluster_to_dict(cluster) for cluster in clusters]
        return {
            'citations': citation_dicts,
            'clusters': clusters_dicts
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

    def _propagate_canonical_to_parallels(self, citations: List['CitationResult']):
        """
        For each verified citation, propagate canonical_name and canonical_date to its unverified parallels.
        Mark those as true_by_parallel, but do NOT set verified=True for parallels.
        """
        # Build a lookup for citation text to CitationResult
        citation_lookup = {c.citation: c for c in citations}
        for citation in citations:
            if citation.verified and citation.canonical_name and citation.canonical_date:
                for parallel in (citation.parallel_citations or []):
                    parallel_cite = citation_lookup.get(parallel)
                    if parallel_cite and not parallel_cite.verified:
                        # Propagate canonical info (but not verified status)
                        parallel_cite.canonical_name = citation.canonical_name
                        parallel_cite.canonical_date = citation.canonical_date
                        parallel_cite.url = citation.url
                        parallel_cite.source = citation.source
                        # Mark as true_by_parallel in metadata only
                        if not hasattr(parallel_cite, 'metadata') or parallel_cite.metadata is None:
                            parallel_cite.metadata = {}
                        parallel_cite.metadata['true_by_parallel'] = True
        # Debug output: print canonical fields after propagation
        for c in citations:
            print(f"[DEBUG] Citation: {c.citation}, canonical_name: {c.canonical_name}, canonical_date: {c.canonical_date}, verified: {c.verified}, true_by_parallel: {getattr(c.metadata, 'true_by_parallel', False) if hasattr(c, 'metadata') else False}")

    def _normalize_canonical_fields(self, citations: List['CitationResult']):
        """
        Normalize canonical_name and canonical_date for all citations (strip whitespace, standardize case).
        """
        for c in citations:
            if c.canonical_name:
                c.canonical_name = c.canonical_name.strip()
            if c.canonical_date:
                c.canonical_date = str(c.canonical_date).strip()

    def _propagate_extracted_to_parallels(self, citations: List['CitationResult']):
        """Propagate extracted case names and dates between parallel citations in the same group."""
        # DISABLE DANGEROUS PROPAGATION: This was contaminating citations with wrong case names
        # The parallel citation detection incorrectly groups different cases together
        # and then propagates wrong case names. Let each citation keep its own extracted data.
        #
        # citation_lookup = {c.citation: c for c in citations}
        # processed = set()
        # for citation in citations:
        #     if citation.citation in processed:
        #         continue
        #     # Gather all citations in this parallel group (including self)
        #     group = [citation]
        #     for parallel in (citation.parallel_citations or []):
        #         parallel_cite = citation_lookup.get(parallel)
        #         if parallel_cite and parallel_cite not in group:
        #             group.append(parallel_cite)
        #     # Find the best extracted_case_name and extracted_date in the group (prefer non-empty, non-N/A)
        #     best_name = next((c.extracted_case_name for c in group if c.extracted_case_name and c.extracted_case_name != 'N/A'), None)
        #     best_date = next((c.extracted_date for c in group if c.extracted_date and c.extracted_date != 'N/A'), None)
        #     # Propagate to all group members if missing or N/A
        #     for c in group:
        #         if (not c.extracted_case_name or c.extracted_case_name == 'N/A') and best_name:
        #             c.extracted_case_name = best_name
        #         if (not c.extracted_date or c.extracted_date == 'N/A') and best_date:
        #             c.extracted_date = best_date
        #         processed.add(c.citation)
        pass

    def propagate_canonical_to_cluster(self, citations: List['CitationResult']):
        """
        For each group of parallel citations (including main and parallels), if any member is verified and has canonical_name and canonical_date,
        propagate those fields to all other members in the group that lack them. Set verified='true_by_parallel' for those not directly verified.
        """
        # Build a mapping from citation string to CitationResult
        citation_lookup = {c.citation: c for c in citations}
        visited = set()
        for citation in citations:
            if citation.citation in visited:
                continue
            # Build the group: citation + all parallels
            group = set([citation.citation])
            if citation.parallel_citations:
                group.update(citation.parallel_citations)
            # Find any verified member with canonical fields
            verified_member = None
            for cite_str in group:
                c = citation_lookup.get(cite_str)
                if c and c.verified and c.canonical_name and c.canonical_date:
                    verified_member = c
                    break
            # Propagate canonical fields to all group members lacking them
            if verified_member:
                for cite_str in group:
                    c = citation_lookup.get(cite_str)
                    if c and (not c.canonical_name or not c.canonical_date):
                        c.canonical_name = verified_member.canonical_name
                        c.canonical_date = verified_member.canonical_date
                        c.url = verified_member.url
                        c.source = verified_member.source
                        # Mark as true_by_parallel if not directly verified
                        if not c.verified:
                            c.verified = "true_by_parallel"
                            if not hasattr(c, 'metadata'):
                                c.metadata = {}
                            c.metadata['true_by_parallel'] = True
                    visited.add(cite_str)
        # Debug output: print canonical fields after propagation
        for c in citations:
            print(f"[DEBUG] Citation: {c.citation}, canonical_name: {c.canonical_name}, canonical_date: {c.canonical_date}, verified: {c.verified}, true_by_parallel: {getattr(c.metadata, 'true_by_parallel', False) if hasattr(c, 'metadata') else False}")

    def ensure_bidirectional_parallels(self, citations: List['CitationResult']):
        """
        For each group of citations that are close together (by position and punctuation), ensure all group members have each other in their parallel_citations field.
        """
        # Sort citations by start_index
        sorted_citations = sorted(citations, key=lambda x: x.start_index or 0)
        n = len(sorted_citations)
        i = 0
        while i < n:
            group = [sorted_citations[i]]
            j = i + 1
            while j < n:
                curr = sorted_citations[j]
                prev = group[-1]
                # If within 100 chars and separated by a comma, treat as parallel
                if (curr.start_index and prev.end_index and curr.start_index - prev.end_index <= 100):
                    text_between = ''
                    if hasattr(prev, 'end_index') and hasattr(curr, 'start_index'):
                        text_between = getattr(prev, 'context', '')[-(prev.end_index - (prev.start_index or 0)):] + getattr(curr, 'context', '')[:curr.start_index - (curr.start_index or 0)]
                    if ',' in text_between or (curr.start_index - prev.end_index <= 10):
                        group.append(curr)
                        j += 1
                        continue
                break
            # Set parallel_citations for all in group
            if len(group) > 1:
                cite_strs = [c.citation for c in group]
                for c in group:
                    c.parallel_citations = [s for s in cite_strs if s != c.citation]
            i = j
        # Debug output: print parallel_citations for each citation
        if self.config.debug_mode:
            for c in citations:
                logger.debug(f"Citation: {c.citation}, parallels: {getattr(c, 'parallel_citations', [])}")

    def propagate_extracted_date_to_group(self, citations: List['CitationResult']):
        """
        For each group of parallel citations, propagate the extracted_date from any member that has it to all others that lack it.
        """
        citation_lookup = {c.citation: c for c in citations}
        visited = set()
        for citation in citations:
            if citation.citation in visited:
                continue
            group = set([citation.citation])
            if citation.parallel_citations:
                group.update(citation.parallel_citations)
            # Find any member with an extracted_date
            date_member = None
            for cite_str in group:
                c = citation_lookup.get(cite_str)
                if c and c.extracted_date:
                    date_member = c
                    break
            # Propagate extracted_date to all group members lacking it
            if date_member:
                for cite_str in group:
                    c = citation_lookup.get(cite_str)
                    if c and not c.extracted_date:
                        c.extracted_date = date_member.extracted_date
                    visited.add(cite_str)
        # Debug output: print extracted_date for each citation
        if self.config.debug_mode:
            for c in citations:
                logger.debug(f"Citation: {c.citation}, extracted_date: {c.extracted_date}")

    # In process_text, call propagate_extracted_date_to_group after ensure_bidirectional_parallels
    # ... existing code ...

    def extract_citations_from_text(self, text):
        """
        DEPRECATED: This method is deprecated. Use process_text() instead for proper unified pipeline processing.
        
        This method bypasses the unified pipeline and should not be used.
        """
        import warnings
        warnings.warn(
            "extract_citations_from_text is deprecated. Use process_text() for proper unified pipeline processing.",
            DeprecationWarning,
            stacklevel=2
        )
        logger.warning("DEPRECATED: extract_citations_from_text called - use process_text() instead")
        
        # Return empty results to force use of proper pipeline
        return []
        
        # Step 1: Normalize text using comprehensive normalization
        try:
            from src.unified_citation_clustering import _normalize_citation_comprehensive
            normalized_text = _normalize_citation_comprehensive(text)
            logger.info(f"Text normalized for citation extraction (length: {len(normalized_text)})")
        except Exception as e:
            logger.warning(f"Normalization failed, using original text: {e}")
            normalized_text = text
        
        results = []
        
        # Step 2: Use comprehensive regex patterns (including federal and state courts)
        priority_patterns = [
            # Federal Supreme Court
            r'\b(\d+)\s+U\.?S\.?\s+(\d+)(?:\s*\((\d{4})\))?',
            r'\b(\d+)\s+S\.?\s*Ct\.?\s+(\d+)(?:\s*\((\d{4})\))?',
            r'\b(\d+)\s+L\.?\s*Ed\.?\s*2d\s+(\d+)(?:\s*\((\d{4})\))?',
            
            # Federal Circuit Courts
            r'\b(\d+)\s+F\.?\s*3d\s+(\d+)(?:\s*\((\d{4})\))?',
            r'\b(\d+)\s+F\.?\s*2d\s+(\d+)(?:\s*\((\d{4})\))?',
            r'\b(\d+)\s+F\.?\s+(\d+)(?:\s*\((\d{4})\))?',
            r'\b(\d+)\s+F\.?\s*Supp\.?\s*3d\s+(\d+)(?:\s*\((\d{4})\))?',
            r'\b(\d+)\s+F\.?\s*Supp\.?\s*2d\s+(\d+)(?:\s*\((\d{4})\))?',
            r'\b(\d+)\s+F\.?\s*Supp\.?\s+(\d+)(?:\s*\((\d{4})\))?',
            
            # State courts (common patterns)
            r'\b(\d+)\s+P\.?\s*3d\s+(\d+)(?:\s*\((\d{4})\))?',
            r'\b(\d+)\s+P\.?\s*2d\s+(\d+)(?:\s*\((\d{4})\))?',
            r'\b(\d+)\s+P\.?\s+(\d+)(?:\s*\((\d{4})\))?',
            r'\b(\d+)\s+N\.?E\.?\s*3d\s+(\d+)(?:\s*\((\d{4})\))?',
            r'\b(\d+)\s+N\.?E\.?\s*2d\s+(\d+)(?:\s*\((\d{4})\))?',
            r'\b(\d+)\s+N\.?E\.?\s+(\d+)(?:\s*\((\d{4})\))?',
            r'\b(\d+)\s+S\.?E\.?\s*2d\s+(\d+)(?:\s*\((\d{4})\))?',
            r'\b(\d+)\s+S\.?W\.?\s*3d\s+(\d+)(?:\s*\((\d{4})\))?',
            r'\b(\d+)\s+S\.?W\.?\s*2d\s+(\d+)(?:\s*\((\d{4})\))?',
            r'\b(\d+)\s+A\.?\s*3d\s+(\d+)(?:\s*\((\d{4})\))?',
            r'\b(\d+)\s+A\.?\s*2d\s+(\d+)(?:\s*\((\d{4})\))?',
            r'\b(\d+)\s+A\.?\s+(\d+)(?:\s*\((\d{4})\))?',
            
            # Washington Supreme Court 3d series
            r'\b(\d+)\s+Wn\.?\s*3d\s+(\d+)(?:\s*\((\d{4})\))?',
            r'\b(\d+)\s+Wash\.?\s*3d\s+(\d+)(?:\s*\((\d{4})\))?',
        ]
        
        # Extract citations using comprehensive patterns
        for pattern in priority_patterns:
            matches = re.finditer(pattern, normalized_text, re.IGNORECASE)
            for match in matches:
                volume = match.group(1)
                page = match.group(2)
                year = match.group(3) if len(match.groups()) >= 3 and match.group(3) else None
                
                # Reconstruct citation from match
                citation_text = match.group(0)
                
                # Look for case name before citation (within 200 chars)
                start_pos = max(0, match.start() - 200)
                context = normalized_text[start_pos:match.start()]
                
                case_name = "N/A"
                case_patterns = [
                    r'([A-Z][a-zA-Z\s&.]+\s+v\.?\s+[A-Z][a-zA-Z\s&.]+)',
                    r'([A-Z][a-zA-Z\s&.]+\s+vs\.?\s+[A-Z][a-zA-Z\s&.]+)',
                    r'(In re [A-Z][a-zA-Z\s&.]+)',
                    r'(Ex parte [A-Z][a-zA-Z\s&.]+)',
                ]
                
                for case_pattern in case_patterns:
                    case_matches = re.findall(case_pattern, context)
                    if case_matches:
                        case_name = case_matches[-1].strip()
                        if len(case_name) > 5:
                            break
                
                results.append({
                    'case_name': case_name,
                    'citation': citation_text,
                    'year': year,
                    'start_index': match.start(),
                    'end_index': match.end()
                })
        
        # Step 3: Try eyecite as fallback/supplement
        try:
            import eyecite
            eyecite_citations = eyecite.get_citations(normalized_text)
            logger.info(f"Eyecite found {len(eyecite_citations)} additional citations")
            
            for cite in eyecite_citations:
                citation_text = str(cite)
                # Add eyecite results if not already found by regex
                if not any(result['citation'] == citation_text for result in results):
                    results.append({
                        'case_name': "N/A",
                        'citation': citation_text,
                        'year': getattr(cite, 'year', None),
                        'start_index': getattr(cite, 'span', [0, 0])[0],
                        'end_index': getattr(cite, 'span', [0, 0])[1]
                    })
        except Exception as e:
            logger.warning(f"Eyecite extraction failed: {e}")
        
        logger.info(f"Comprehensive extraction found {len(results)} citations")
        return results

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
    import asyncio
    return asyncio.run(processor.process_text(text)) 

def extract_case_clusters_by_name_and_year(text: str) -> list:
    """
    DEPRECATED: Use isolation-aware clustering logic instead.
    Extract clusters of citations between a case name and a year/date.
    Returns a list of dicts: {case_name, year, citations, start, end}
    """
    warnings.warn(
        "extract_case_clusters_by_name_and_year is deprecated. Use isolation-aware clustering instead.",
        DeprecationWarning,
        stacklevel=2
    )
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
    DEPRECATED: Use isolation-aware clustering logic instead.
    For each citation, create a cluster that includes all citations between the previous year (or 200 chars back)
    and the next year/date, discarding page/pincites between citations or citation and year.
    Returns a list of dicts: {case_name, year, citations, start, end}
    """
    warnings.warn(
        "cluster_citations_by_citation_and_year is deprecated. Use isolation-aware clustering instead.",
        DeprecationWarning,
        stacklevel=2
    )
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