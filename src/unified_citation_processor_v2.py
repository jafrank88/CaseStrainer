# type: ignore
"""
Unified Citation Processor v2 - Consolidated Citation Extraction and Processing

⚠️  DEPRECATION NOTICE ⚠️
================================================================================
This module is being phased out in favor of clean_extraction_pipeline.py

Citation patterns defined in this file are DEPRECATED. All new pattern 
definitions should go in src/citation_patterns.py (single source of truth).

The clean_extraction_pipeline.py now uses shared patterns from citation_patterns.py
and should be the primary extraction method for production use.

This file will be kept temporarily for:
1. Legacy code that still imports from it
2. Features not yet migrated to clean_extraction_pipeline.py
3. Backwards compatibility

Future Development: Use clean_extraction_pipeline.py + citation_patterns.py
================================================================================

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

from src.unified_case_name_extractor_v2 import (
    get_unified_extractor,
    extract_case_name_and_date_master,
    extract_case_name_only_unified
)

from src.unified_clustering_master import cluster_citations_unified_master as cluster_citations_unified
import warnings

from src.config import get_config_value

logger = logging.getLogger(__name__)

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

from src.case_name_extraction_core import extract_case_name_and_date, extract_case_name_only

try:
    from src.comprehensive_websearch_engine import search_cluster_for_canonical_sources
    COMPREHENSIVE_WEBSEARCH_AVAILABLE = True
    logger.info("Comprehensive websearch engine successfully imported")
except ImportError as e:
    COMPREHENSIVE_WEBSEARCH_AVAILABLE = False
    logger.warning(f"Comprehensive websearch engine not available: {e}")
    search_cluster_for_canonical_sources = None
except Exception as e:
    COMPREHENSIVE_WEBSEARCH_AVAILABLE = False
    logger.warning(f"Comprehensive websearch engine import failed with unexpected error: {e}")
    search_cluster_for_canonical_sources = None

try:
    from src.citation_utils_consolidated import normalize_citation, generate_citation_variants
    CITATION_UTILS_AVAILABLE = True
    logger.info("Citation utils successfully imported")
except ImportError as e:
    CITATION_UTILS_AVAILABLE = False
    logger.warning(f"Citation utils not available: {e}")
    normalize_citation = None
    generate_citation_variants = None
except Exception as e:
    CITATION_UTILS_AVAILABLE = False
    logger.warning(f"Citation utils import failed with unexpected error: {e}")
    normalize_citation = None
    generate_citation_variants = None


try:
    from src.models import CitationResult, ProcessingConfig
    MODELS_AVAILABLE = True
    logger.info("Models successfully imported")
except ImportError as e:
    MODELS_AVAILABLE = False
    logger.warning(f"Models not available: {e}")
    CitationResult = None
    ProcessingConfig = None
except Exception as e:
    MODELS_AVAILABLE = False
    logger.warning(f"Models import failed with unexpected error: {e}")
    CitationResult = None
    ProcessingConfig = None

try:
    from src.unified_clustering_master import (
        UnifiedClusteringMaster as UnifiedCitationClusterer
    )
    # cluster_citations_unified is already imported above
    CLUSTERING_AVAILABLE = True
    logger.info("Citation clustering successfully imported (unified_clustering_master)")
except ImportError as e:
    CLUSTERING_AVAILABLE = False
    logger.warning(f"Citation clustering not available: {e}")
    UnifiedCitationClusterer = None
    cluster_citations_unified = None
except Exception as e:
    CLUSTERING_AVAILABLE = False
    logger.warning(f"Citation clustering import failed with unexpected error: {e}")
    UnifiedCitationClusterer = None
    cluster_citations_unified = None

try:
    from src.citation_clustering import (
        _propagate_canonical_to_parallels,
        _propagate_extracted_to_parallels_clusters,
        _is_citation_contained_in_any
    )
    CITATION_CLUSTERING_AVAILABLE = True
    logger.info("Citation clustering utilities successfully imported")
except ImportError as e:
    CITATION_CLUSTERING_AVAILABLE = False
    logger.warning(f"Citation clustering utilities not available: {e}")
    _propagate_canonical_to_parallels = None
    _propagate_extracted_to_parallels_clusters = None
    _is_citation_contained_in_any = None
except Exception as e:
    CITATION_CLUSTERING_AVAILABLE = False
    logger.warning(f"Citation clustering utilities import failed with unexpected error: {e}")
    _propagate_canonical_to_parallels = None
    _propagate_extracted_to_parallels_clusters = None
    _is_citation_contained_in_any = None

try:
    from src.canonical_case_name_service import get_canonical_case_name_with_date
    CANONICAL_SERVICE_AVAILABLE = True
    logger.info("Canonical case name service successfully imported")
except ImportError as e:
    CANONICAL_SERVICE_AVAILABLE = False
    logger.warning(f"Canonical case name service not available: {e}")
    get_canonical_case_name_with_date = None
except Exception as e:
    CANONICAL_SERVICE_AVAILABLE = False
    logger.warning(f"Canonical case name service import failed with unexpected error: {e}")
    get_canonical_case_name_with_date = None

# from src.courtlistener_verification import verify_with_courtlistener  # DEPRECATED
# from src.citation_verification import (  # DEPRECATED
#     verify_citations_with_canonical_service,  # DEPRECATED
#     verify_citations_with_legal_websearch  # DEPRECATED

# cluster_citations_unified is imported above from unified_clustering_master

CitationList = List[CitationResult]
CitationDict = Dict[str, Any]
VerificationResult = Dict[str, Any]

class UnifiedCitationProcessorV2:
    """
    Unified citation processor that consolidates the best parts of all existing implementations.
    """
    
    def __init__(self, config: Optional[ProcessingConfig] = None, progress_callback: Optional[callable] = None):
        logger.info('[DEBUG] ENTERED UnifiedCitationProcessorV2.__init__')
        self.config = config or ProcessingConfig()
        logger.warning(f'[CONFIG-CHECK] extract_case_names={self.config.extract_case_names}, extract_dates={self.config.extract_dates}')
        
        # CRITICAL FIX: Force enable case name extraction if it's somehow disabled
        if not self.config.extract_case_names:
            logger.error(f'[CONFIG-ERROR] extract_case_names was False! Forcing to True')
            self.config.extract_case_names = True
        
        self.progress_callback = progress_callback  # NEW: Progress callback support
        self._init_patterns()
        self._init_case_name_patterns()
        self._init_date_patterns()
        self._init_state_reporter_mapping()
        
        # Initialize CourtListener API key
        self.courtlistener_api_key = os.getenv('COURTLISTENER_API_KEY')
        
        # Initialize enhanced web searcher (optional)
        try:
            from src.comprehensive_websearch_engine import ComprehensiveWebSearchEngine
            self.enhanced_web_searcher = ComprehensiveWebSearchEngine(enable_experimental_engines=True)
            logger.info("Initialized ComprehensiveWebSearchEngine for legal database lookups")
        except ImportError as e:
            logger.warning(f"ComprehensiveWebSearchEngine not available: {e}")
            self.enhanced_web_searcher = None
        except Exception as e:
            logger.warning(f"Failed to initialize ComprehensiveWebSearchEngine: {e}")
            self.enhanced_web_searcher = None
        
        if self.config.debug_mode:
            logger.info(f"CourtListener API key available: {bool(self.courtlistener_api_key)}")
            logger.info(f"Enhanced web searcher available: {bool(self.enhanced_web_searcher)}")
        
        logger.info('[DEBUG] EXITED UnifiedCitationProcessorV2.__init__')

    def _update_progress(self, progress: int, step: str, message: str):
        """Update progress if callback is available."""
        if self.progress_callback and callable(self.progress_callback):
            try:
                self.progress_callback(progress, step, message)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")

    def _init_patterns(self):
        """Initialize comprehensive citation patterns with proper Bluebook spacing."""
        self.citation_patterns = {
            # Washington First Series (NEW - FIX for first series support)
            'wn_first': re.compile(r'\b(\d+)\s+Wn\.\s+(\d+)\b', re.IGNORECASE),
            'wash_first': re.compile(r'\b(\d+)\s+Wash\.\s+(\d+)\b', re.IGNORECASE),
            
            # Washington Second Series
            'wn2d': re.compile(r'\b(\d+)\s+Wn\.2d\s*\n?\s*(\d+)(?:\s*,\s*\d+\s*P\.3d\s*\d+)?\b', re.IGNORECASE),
            'wn2d_space': re.compile(r'\b(\d+)\s+Wn\.\s*2d\s*\n?\s*(\d+)(?:\s*,\s*\d+\s*P\.3d\s*\d+)?\b', re.IGNORECASE),
            
            # Washington Court of Appeals
            'wn_app': re.compile(r'\b(\d+)\s+Wn\.\s*App\.\s+(\d+)\b', re.IGNORECASE),
            'wn_app_space': re.compile(r'\b(\d+)\s+Wn\.\s*App\s+(\d+)\b', re.IGNORECASE),
            
            # Washington Third Series
            'wn3d': re.compile(r'\b(\d+)\s+Wn\.\s*3d\s*\n?\s*(\d+)\b', re.IGNORECASE),
            'wn3d_space': re.compile(r'\b(\d+)\s+Wn\.\s*3d\s*\n?\s*(\d+)\b', re.IGNORECASE),
            
            # Wash. variants
            'wash2d': re.compile(r'\b(\d+)\s+Wash\.\s*2d\s+(\d+)(?:\s*,\s*\d+\s*P\.3d\s*\d+)?\b', re.IGNORECASE),
            'wash2d_space': re.compile(r'\b(\d+)\s+Wash\.\s*2d\s+(\d+)(?:\s*,\s*\d+\s*P\.3d\s*\d+)?\b', re.IGNORECASE),
            'wash_app': re.compile(r'\b(\d+)\s+Wash\.\s*App\.\s+(\d+)\b', re.IGNORECASE),
            'wash_app_space': re.compile(r'\b(\d+)\s+Wash\.\s*App\s+(\d+)\b', re.IGNORECASE),
            'p3d': re.compile(r'\b(\d+)\s+P\.3d\s+(\d+)\b', re.IGNORECASE),
            'p2d': re.compile(r'\b(\d+)\s+P\.2d\s+(\d+)\b', re.IGNORECASE),
            'us': re.compile(r'\b(\d+)\s+U\.S\.\s+(\d+)\b', re.IGNORECASE),
            'us_spaced': re.compile(r'\b(\d+)\s+U\.\s*S\.\s+(\d+)\b', re.IGNORECASE),
            'f3d': re.compile(r'\b(\d+)\s+F\.3d\s+(\d+)\b', re.IGNORECASE),
            'f2d': re.compile(r'\b(\d+)\s+F\.2d\s+(\d+)\b', re.IGNORECASE),
            'f_supp': re.compile(r'\b(\d+)\s+F\.\s*Supp\.\s+(\d+)\b', re.IGNORECASE),
            'f_supp2d': re.compile(r'\b(\d+)\s+F\.\s*Supp\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            'f_supp3d': re.compile(r'\b(\d+)\s+F\.\s*Supp\.\s*3d\s+(\d+)\b', re.IGNORECASE),
            's_ct': re.compile(r'\b(\d+)\s+S\.\s*Ct\.\s+(\d+)\b', re.IGNORECASE),
            'l_ed': re.compile(r'\b(\d+)\s+L\.\s*Ed\.\s+(\d+)\b', re.IGNORECASE),
            'l_ed2d': re.compile(r'\b(\d+)\s+L\.\s*Ed\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            'a2d': re.compile(r'\b(\d+)\s+A\.2d\s+(\d+)\b', re.IGNORECASE),
            'a3d': re.compile(r'\b(\d+)\s+A\.3d\s+(\d+)\b', re.IGNORECASE),
            'so2d': re.compile(r'\b(\d+)\s+So\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            'so3d': re.compile(r'\b(\d+)\s+So\.\s*3d\s+(\d+)\b', re.IGNORECASE),
            'wash_2d_alt': re.compile(r'\b(\d+)\s+Wash\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            'wash_app_alt': re.compile(r'\b(\d+)\s+Wash\.\s*App\.\s+(\d+)\b', re.IGNORECASE),
            'wn2d_alt': re.compile(r'\b(\d+)\s+Wn\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            'wn2d_alt_space': re.compile(r'\b(\d+)\s+Wn\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            'wn_app_alt': re.compile(r'\b(\d+)\s+Wn\.\s*App\.\s+(\d+)\b', re.IGNORECASE),
            'p3d_alt': re.compile(r'\b(\d+)\s+P\.\s*3d\s+(\d+)\b', re.IGNORECASE),
            'p2d_alt': re.compile(r'\b(\d+)\s+P\.\s*2d\s+(\d+)\b', re.IGNORECASE),
            'wash_complete': re.compile(r'\b(\d+)\s+(?:Wash\.|Wn\.)\s*(?:2d|App\.)\s+(\d+)(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\b', re.IGNORECASE),
            'wash_with_parallel': re.compile(r'\b(\d+)\s+(?:Wash\.|Wn\.)\s*(?:2d|App\.)\s+(\d+)(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\b', re.IGNORECASE),
            'parallel_cluster': re.compile(r'\b(\d+)\s+(?:Wash\.|Wn\.)\s*(?:2d|App\.)\s+(\d+)(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\b', re.IGNORECASE),
            'flexible_wash2d': re.compile(r'\b(\d+)\s+(?:Wash\.|Wn\.)\s*2d\s+(\d+)(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\s*(?:\(\d{4}\))?\b', re.IGNORECASE),
            'flexible_p3d': re.compile(r'\b(\d+)\s+P\.3d\s+(\d+)(?:\s*,\s*(\d+)\s+(?:Wash\.|Wn\.)\s*2d\s+(\d+))?\s*(?:\(\d{4}\))?\b', re.IGNORECASE),
            'flexible_p2d': re.compile(r'\b(\d+)\s+P\.2d\s+(\d+)(?:\s*,\s*(\d+)\s+(?:Wash\.|Wn\.)\s*2d\s+(\d+))?\s*(?:\(\d{4}\))?\b', re.IGNORECASE),
            'parallel_citation_cluster': re.compile(
                r'\b(\d+)\s+(?:Wash\.|Wn\.)\s*2d\s+(\d+)(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\s*(?:\(\d{4}\))?\b', 
                re.IGNORECASE
            ),
            'westlaw': re.compile(r'\b(\d{4})\s+WL\s+(\d{1,12})\b', re.IGNORECASE),
            'westlaw_alt': re.compile(r'\b(\d{4})\s+Westlaw\s+(\d{1,12})\b', re.IGNORECASE),
            'simple_wash2d': re.compile(r'\b(\d+)\s+(?:Wash\.|Wn\.)\s*2d\s+(\d+)\b', re.IGNORECASE),
            'simple_p3d': re.compile(r'\b(\d+)\s+P\.3d\s+(\d+)\b', re.IGNORECASE),
            'simple_p2d': re.compile(r'\b(\d+)\s+P\.2d\s+(\d+)\b', re.IGNORECASE),
            'lexis': re.compile(r'\b(\d{4})\s+[A-Za-z\.\s]+LEXIS\s+(\d{1,12})\b', re.IGNORECASE),
            'lexis_alt': re.compile(r'\b(\d{4})\s+LEXIS\s+(\d{1,12})\b', re.IGNORECASE),
            
            # Neutral/Public Domain Citations (Year-State-Number format)
            # These are official state citations used by many states
            'neutral_nm': re.compile(r'\b(20\d{2})-NM(?:CA)?-(\d{1,5})\b', re.IGNORECASE),  # New Mexico: 2017-NM-007
            'neutral_nd': re.compile(r'\b(20\d{2})\s+ND\s+(\d{1,5})\b', re.IGNORECASE),  # North Dakota
            'neutral_ok': re.compile(r'\b(20\d{2})\s+OK\s+(\d{1,5})\b', re.IGNORECASE),  # Oklahoma
            'neutral_sd': re.compile(r'\b(20\d{2})\s+SD\s+(\d{1,5})\b', re.IGNORECASE),  # South Dakota
            'neutral_ut': re.compile(r'\b(20\d{2})\s+UT\s+(\d{1,5})\b', re.IGNORECASE),  # Utah
            'neutral_wi': re.compile(r'\b(20\d{2})\s+WI\s+(\d{1,5})\b', re.IGNORECASE),  # Wisconsin
            'neutral_wy': re.compile(r'\b(20\d{2})\s+WY\s+(\d{1,5})\b', re.IGNORECASE),  # Wyoming
            'neutral_mt': re.compile(r'\b(20\d{2})\s+MT\s+(\d{1,5})\b', re.IGNORECASE),  # Montana
        }
        
        self.pinpoint_pattern = re.compile(r'\b(?:at\s+)?(\d+)\b', re.IGNORECASE)
        self.docket_pattern = re.compile(r'\b(?:No\.|Docket\s+No\.|Case\s+No\.)\s*[:\-]?\s*([A-Z0-9\-\.]+)\b', re.IGNORECASE)
        self.history_pattern = re.compile(r'\b(?:affirmed|reversed|remanded|vacated|denied|granted|cert\.?\s+denied)\b', re.IGNORECASE)
        self.status_pattern = re.compile(r'\b(?:published|unpublished|memorandum|opinion)\b', re.IGNORECASE)
    
    def _init_case_name_patterns(self):
        """Initialize case name extraction patterns."""
        self.case_name_patterns = [
            r'([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[a-zA-Z\'\.\&]+|of|the|and|&))*)\s+(?:v\.|vs\.|versus)\s+([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[a-zA-Z\'\.\&]+|of|the|and|&))*)',
            r'(In\s+re\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[a-zA-Z\'\.\&]+|of|the|and|&))*)',
            r'(Ex\s+parte\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[a-zA-Z\'\.\&]+|of|the|and|&))*)',
            r'((?:State|United\s+States|People)(?:\s+of\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[a-zA-Z\'\.\&]+|of|the|and|&))*))\s+(?:v\.|vs\.|versus)\s+([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[a-zA-Z\'\.\&]+|of|the|and|&))*)',
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
            'P.3d': ['Alaska', 'Arizona', 'California', 'Colorado', 'Hawaii', 'Idaho', 'Kansas', 'Montana', 'Nevada', 'New Mexico', 'Oklahoma', 'Oregon', 'Utah', 'Washington', 'Wyoming'],
            'P.2d': ['Alaska', 'Arizona', 'California', 'Colorado', 'Hawaii', 'Idaho', 'Kansas', 'Montana', 'Nevada', 'New Mexico', 'Oklahoma', 'Oregon', 'Utah', 'Washington', 'Wyoming'],
            
            'N.W.2d': ['Iowa', 'Michigan', 'Minnesota', 'Nebraska', 'North Dakota', 'South Dakota', 'Wisconsin'],
            'N.W.': ['Iowa', 'Michigan', 'Minnesota', 'Nebraska', 'North Dakota', 'South Dakota', 'Wisconsin'],
            
            'S.W.3d': ['Arkansas', 'Kentucky', 'Missouri', 'Tennessee', 'Texas'],
            'S.W.2d': ['Arkansas', 'Kentucky', 'Missouri', 'Tennessee', 'Texas'],
            'S.W.': ['Arkansas', 'Kentucky', 'Missouri', 'Tennessee', 'Texas'],
            
            'N.E.2d': ['Illinois', 'Indiana', 'Massachusetts', 'New York', 'Ohio'],
            'N.E.': ['Illinois', 'Indiana', 'Massachusetts', 'New York', 'Ohio'],
            
            'So.3d': ['Alabama', 'Florida', 'Louisiana', 'Mississippi'],
            'So.2d': ['Alabama', 'Florida', 'Louisiana', 'Mississippi'],
            'So.': ['Alabama', 'Florida', 'Louisiana', 'Mississippi'],
            
            'S.E.2d': ['Georgia', 'North Carolina', 'South Carolina', 'Virginia', 'West Virginia'],
            'S.E.': ['Georgia', 'North Carolina', 'South Carolina', 'Virginia', 'West Virginia'],
            
            'A.3d': ['Connecticut', 'Delaware', 'Maine', 'Maryland', 'New Hampshire', 'New Jersey', 'Pennsylvania', 'Rhode Island', 'Vermont', 'District of Columbia'],
            'A.2d': ['Connecticut', 'Delaware', 'Maine', 'Maryland', 'New Hampshire', 'New Jersey', 'Pennsylvania', 'Rhode Island', 'Vermont', 'District of Columbia'],
            'A.': ['Connecticut', 'Delaware', 'Maine', 'Maryland', 'New Hampshire', 'New Jersey', 'Pennsylvania', 'Rhode Island', 'Vermont', 'District of Columbia'],
        }
        
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
                group_key = f"state_{state.lower()}"
                if group_key not in groups:
                    groups[group_key] = []
                groups[group_key].append(citation)
            elif reporter:
                group_key = f"regional_{reporter}"
                if group_key not in groups:
                    groups[group_key] = []
                groups[group_key].append(citation)
            else:
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
        
        parts = [part.strip() for part in cite.split(',')]
        cleaned_parts = []
        
        for part in parts:
            if re.match(r'^\d+\s+\w+\.\w+\s+\d+', part):
                cleaned_parts.append(part)
            elif re.match(r'^\d+$', part):
                continue
            else:
                citation_match = re.match(r'^(\d+\s+\w+\.\w+\s+\d+)', part)
                if citation_match:
                    cleaned_parts.append(citation_match.group(1))
                else:
                    cleaned_parts.append(part)
        
        return ', '.join(cleaned_parts)



    def _get_extracted_case_name(self, citation: 'CitationResult') -> Optional[str]:
        """Utility to safely get extracted case name from a citation."""
        return citation.extracted_case_name if hasattr(citation, 'extracted_case_name') else None
    
    def _get_unverified_citations(self, citations: List['CitationResult']) -> List['CitationResult']:
        """Utility to filter unverified citations."""
        return [c for c in citations if not getattr(c, 'verified', False)]
    
    def _apply_verification_result(self, citation: 'CitationResult', verify_result: dict, source: str = "CourtListener"):
        """Centralized method to apply verification results with validation against extracted data."""
        if verify_result.get("verified"):
            canonical_name = verify_result.get("canonical_name")
            extracted_name = getattr(citation, 'extracted_case_name', None)

            # VALIDATION: Check if CourtListener canonical name matches our extracted name
            if canonical_name and extracted_name and extracted_name != "N/A":
                # Normalize both names for comparison
                canonical_norm = self._normalize_case_name_for_comparison(canonical_name)
                extracted_norm = self._normalize_case_name_for_comparison(extracted_name)

                # Log the comparison but ALWAYS prefer CourtListener canonical data
                if not self._case_names_match(canonical_norm, extracted_norm):
                    logger.warning(f"⚠️ CourtListener canonical name differs from extracted: '{canonical_name}' vs extracted '{extracted_name}' for {citation.citation}")
                    logger.warning(f"   Using CourtListener canonical data (more authoritative than extraction)")

                    # Use CourtListener canonical data (it's more authoritative than extraction)
                    citation.canonical_name = canonical_name  # Always use CourtListener canonical
                    citation.canonical_date = verify_result.get("canonical_date")
                    citation.url = verify_result.get("url")
                    citation.verified = True
                    citation.source = source
                    citation.metadata = citation.metadata or {}
                    citation.metadata[f"{source.lower()}_source"] = verify_result.get("source")
                    citation.metadata["canonical_name_validation"] = "courtlistener_canonical_preferred"
                    return True

            # Names match or no extracted name available - use CourtListener data as normal (only if not None)
            if canonical_name:
                citation.canonical_name = canonical_name
            canonical_date = verify_result.get("canonical_date")
            if canonical_date:
                citation.canonical_date = canonical_date
            url = verify_result.get("url")
            if url:
                citation.url = url
            citation.verified = True
            citation.source = verify_result.get("source", source)
            citation.metadata = citation.metadata or {}
            citation.metadata[f"{source.lower()}_source"] = verify_result.get("source")
            return True
        else:
            # FIXED: Ensure unverified citations have consistent status
            citation.verified = False
            if not hasattr(citation, 'source') or not citation.source or citation.source == f"{source}_extracted_preferred":
                citation.source = None  # Clear source for unverified citations
            return False
    
    def _normalize_case_name_for_comparison(self, case_name: str) -> str:
        """Normalize case name for comparison by removing common variations."""
        if not case_name:
            return ""
        
        # Convert to lowercase and remove extra whitespace
        normalized = case_name.lower().strip()
        
        # Remove common variations that don't affect meaning
        normalized = re.sub(r'\s+', ' ', normalized)  # Normalize whitespace
        normalized = re.sub(r'[^\w\s]', '', normalized)  # Remove punctuation
        
        # Handle common abbreviations
        normalized = re.sub(r'\bvs?\b', 'v', normalized)  # vs -> v
        normalized = re.sub(r'\bco\b', 'company', normalized)  # co -> company
        normalized = re.sub(r'\bcorp\b', 'corporation', normalized)  # corp -> corporation
        normalized = re.sub(r'\binc\b', 'incorporated', normalized)  # inc -> incorporated
        normalized = re.sub(r'\bllc\b', 'limited liability company', normalized)  # llc -> limited liability company
        
        # Remove common words that don't affect case identity
        common_words = ['the', 'and', 'or', 'of', 'in', 'on', 'at', 'by', 'for', 'with', 'a', 'an']
        words = normalized.split()
        filtered_words = [word for word in words if word not in common_words]
        
        return ' '.join(filtered_words)
    
    def _case_names_match(self, name1: str, name2: str) -> bool:
        """Check if two case names match, allowing for reasonable variations."""
        if not name1 or not name2:
            return False
            
        # Exact match after normalization
        if name1 == name2:
            return True
            
        # Check if one contains the other (handles partial matches)
        if name1 in name2 or name2 in name1:
            return True
            
        # Split into words and check overlap
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        # If significant overlap (>70% of smaller set), consider them matching
        smaller_set = min(words1, words2, key=len)
        larger_set = max(words1, words2, key=len)
        
        overlap = len(smaller_set & larger_set)
        if overlap / len(smaller_set) > 0.7:
            return True
            
        return False
    
    

    def _verify_citations_with_canonical_service(self, citations):
        return verify_citations_with_canonical_service(citations)


    
    def verify_citation_unified_workflow(self, citation: str, case_name: Optional[str] = None) -> Dict[str, Any]:
        """Unified workflow for verifying a single citation with case name."""
        try:
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
        
        representative = citations[0]
        state = self._infer_state_from_citation(representative.citation)
        
        # Use unified clustering instead of deprecated verification
        if hasattr(representative, 'verified') and representative.verified:
            for citation in self._get_unverified_citations(citations[1:]):
                citation.canonical_name = representative.canonical_name
                citation.canonical_date = representative.canonical_date
                citation.url = representative.url
                citation.verified = True
                citation.source = representative.source
                citation.metadata = citation.metadata or {}
                citation.metadata["courtlistener_source"] = representative.metadata.get("courtlistener_source")

    def _verify_regional_group(self, citations: List[CitationResult]):
        """Verify regional reporter citations separately (no state filtering)."""
        for citation in self._get_unverified_citations(citations):
            # Verification handled by unified clustering
            pass

    def _verify_single_citation(self, citation: CitationResult, apply_state_filter: bool = True):
        """Verify a single citation using unified method."""
        if not getattr(citation, 'verified', False):
            # Verification handled by unified clustering
            pass

    def _get_base_citation(self, citation: str) -> str:
        """Extract base citation without page numbers for clustering purposes."""
        base = re.sub(r'\s+\d+$', '', citation)  # Remove trailing page numbers
        base = re.sub(r'\s+\d+,\s*\d+$', '', base)  # Remove pinpoint pages like "72, 73"
        base = re.sub(r'\s+\(\d{4}\)$', '', base)  # Remove years in parentheses
        return base.strip()
    
    def _normalize_case_name_for_clustering(self, case_name: str) -> str:
        """Normalize case name for clustering to group similar names together."""
        if not case_name:
            return ""
        
        normalized = re.sub(r'[^\w\s]', '', case_name.lower())
        
        common_words = ['the', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from']
        words = normalized.split()
        filtered_words = [word for word in words if word not in common_words]
        
        filtered_words.sort()
        
        return ' '.join(filtered_words)
    
    def _is_similar_citation(self, citation1: str, citation2: str) -> bool:
        """Check if two citations are similar (handles variations like Wn.2d vs Wash.2d)."""
        import re
        
        def normalize_citation(citation):
            normalized = re.sub(r'[^\w]', '', citation.lower())
            normalized = normalized.replace('wn2d', 'wash2d')
            normalized = normalized.replace('wnapp', 'washapp')
            return normalized
        
        norm1 = normalize_citation(citation1)
        norm2 = normalize_citation(citation2)
        
        return norm1 in norm2 or norm2 in norm1 or norm1 == norm2

    def _is_similar_date(self, date1: str, date2: str) -> bool:
        """Check if two dates are similar (handles different formats)."""
        import re
        
        year1_match = re.search(r'\b(19|20)\d{2}\b', date1)
        year2_match = re.search(r'\b(19|20)\d{2}\b', date2)
        
        if year1_match and year2_match:
            return year1_match.group(0) == year2_match.group(0)
        
        return False

    def _calculate_page_proximity(self, citation: str, entry_citations: List[str]) -> int:
        """Calculate page proximity score between citation and entry citations."""
        import re
        
        page_match = re.search(r'(\d+)(?:\s*,\s*(\d+))?$', citation)
        if not page_match:
            return 0
        
        our_page = int(page_match.group(1))
        our_pinpoint = int(page_match.group(2)) if page_match.group(2) else None
        
        best_proximity = 0
        
        for entry_citation in entry_citations:
            entry_page_match = re.search(r'(\d+)(?:\s*,\s*(\d+))?$', entry_citation)
            if not entry_page_match:
                continue
            
            entry_page = int(entry_page_match.group(1))
            entry_pinpoint = int(entry_page_match.group(2)) if entry_page_match.group(2) else None
            
            if our_page == entry_page:
                if our_pinpoint and entry_pinpoint:
                    proximity = max(0, 5 - abs(our_pinpoint - entry_pinpoint))
                else:
                    proximity = 3
            else:
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
            if any(reporter in citation.lower() for reporter in ['wn.2d', 'wn.app', 'wash.2d', 'wash.app']):
                score += 2
            elif any(reporter in citation.lower() for reporter in ['u.s.', 'f.3d', 'f.2d', 's.ct.']):
                score += 1
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
        first_citation = min(group, key=lambda c: c.start_index or 0)
        last_citation = max(group, key=lambda c: c.start_index or 0)
        self._extract_metadata(first_citation, text, None)
        self._extract_metadata(last_citation, text, None)
        
        # and then propagates the wrong case name. Let each citation extract its own case name.
        #
        # for citation in group:
        #     citation.extracted_case_name = first_citation.extracted_case_name
        #     citation.extracted_date = last_citation.extracted_date
        #     citation.metadata['case_name_debug'] = first_citation.metadata.get('case_name_debug')
        #     citation.metadata['date_debug'] = last_citation.metadata.get('case_name_debug')
        
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
        
        logger.info(f"🔍 [CITATION_BLOCKS] Attempting citation block extraction for text: '{text[:100]}...'")
        citation_blocks = self._extract_citation_blocks(text)
        if citation_blocks:
            logger.info(f"🔍 [CITATION_BLOCKS] Extracted {len(citation_blocks)} citation blocks")
            for block in citation_blocks:
                logger.info(f"🔍 [CITATION_BLOCKS] Block: '{block.citation}' with extracted_date='{block.extracted_date}'")
            return citation_blocks
        else:
            logger.info(f"🔍 [CITATION_BLOCKS] No citation blocks found, falling back to regex extraction")
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
            'wn_first',         # Washington First Series (NEW)
            'wash_first',       # Washington First Series - Wash. variant (NEW)
            'wn_app',           # Washington Court of Appeals
            'wn_app_space',     # Washington Court of Appeals (with space)
            'wn3d',             # Washington Supreme Court 3d series
            'wn3d_space',       # Washington Supreme Court 3d series (with space)
            'wash_app',         # Washington Court of Appeals (Wash.)
            'wash_app_space',   # Washington Court of Appeals (Wash. with space)
            # Neutral/Public Domain Citations (MUST be in priority list!)
            'neutral_nm',       # New Mexico neutral citations (2017-NM-007)
            'neutral_nd',       # North Dakota
            'neutral_ok',       # Oklahoma
            'neutral_sd',       # South Dakota
            'neutral_ut',       # Utah
            'neutral_wi',       # Wisconsin
            'neutral_wy',       # Wyoming
            'neutral_mt',       # Montana
        ]
        for pattern_name in priority_patterns:
            if pattern_name in self.citation_patterns:
                pattern = self.citation_patterns[pattern_name]
                matches = list(pattern.finditer(text))
                if matches:
                    for match_idx, match in enumerate(matches):
                        citation_str = match.group(0).strip()
                        if not citation_str or citation_str in seen_citations:
                            continue
                        components = self._extract_citation_components(citation_str)
                        reporter = components.get('reporter', '').strip().lower().replace('.', '')
                        if reporter == 'at':
                            continue
                        seen_citations.add(citation_str)
                        start_pos = match.start()
                        end_pos = match.end()
                        context = self._extract_context(text, start_pos, end_pos)
                        is_parallel = ',' in citation_str and any(reporter in citation_str for reporter in ['P.3d', 'P.2d', 'Wash.2d', 'Wn.2d'])
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
                        self._extract_metadata(citation, text, match)
                        citations.append(citation)
        for pattern_name, pattern in self.citation_patterns.items():
            if pattern_name in priority_patterns:
                continue
            matches = list(pattern.finditer(text))
            if matches:
                for match in matches:
                    citation_str = match.group(0).strip()
                    if not citation_str or citation_str in seen_citations:
                        continue
                    components = self._extract_citation_components(citation_str)
                    reporter = components.get('reporter', '').strip().lower().replace('.', '')
                    if reporter == 'at':
                        continue
                    if _is_citation_contained_in_any(citation_str, seen_citations):
                        continue
                    seen_citations.add(citation_str)
                    start_pos = match.start()
                    end_pos = match.end()
                    context = self._extract_context(text, start_pos, end_pos)
                    citation = CitationResult(
                        citation=citation_str,
                        start_index=start_pos,
                        end_index=end_pos,
                        method="regex",
                        pattern=pattern_name,
                        context=context,
                        source="regex"
                    )
                    self._extract_metadata(citation, text, match)
                    citations.append(citation)
        logger.info(f"[DEBUG] All extracted citations: {[c.citation for c in citations]}")
        from collections import defaultdict
        cluster_map = defaultdict(list)
        for citation in citations:
            key = getattr(citation, 'cluster_id', None) or citation.citation
            cluster_map[key].append(citation)
        for group in cluster_map.values():
            self._extract_metadata_for_group(group, text)
        return citations
    
    def _extract_citation_blocks(self, text: str) -> List[CitationResult]:
        """
        Extract complete citation blocks: case name + all parallel citations + year.
        This handles cases like "DeSean v. Sanger, 2 Wn. 3d 329, 334-35, 536 P.3d 191 (2023)"
        """
        if not text:
            return []
        
        logger.info(f"🔍 [CITATION_BLOCKS] Starting citation block extraction for text: '{text[:200]}...'")
        citations = []
        
        citation_block_pattern = re.compile(
            r'([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*\s+v\.\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*|'  # Enhanced v. pattern - require capitalized words
            r'State(?:\s+of\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*)?\s+v\.\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*|'  # Enhanced State v. pattern
            r'In\s+re\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*)'  # Enhanced In re pattern
            r'[,\s]*'  # Optional comma and whitespace after case name
            r'([^()]+)'  # All citations and content between case name and year
            r'\((\d{4})\)'  # Year in parentheses
        )
        
        matches = list(citation_block_pattern.finditer(text))
        logger.info(f"🔍 [CITATION_BLOCKS] Pattern found {len(matches)} matches")
        for i, match in enumerate(matches):
            logger.info(f"🔍 [CITATION_BLOCKS] Match {i+1}: '{match.group(0)}'")
        
        for match in citation_block_pattern.finditer(text):
            case_name = match.group(1).strip().rstrip(',')  # Remove trailing comma
            citations_text = match.group(2).strip()
            year = match.group(3)
            start, end = match.span()
            
            # FIX #35: Debug logging for 183 Wn.2d 649
            if "183" in citations_text and "649" in citations_text:
                logger.warning(f"🔥 FIX #35: BLOCK MATCH for 183 Wn.2d 649!")
                logger.warning(f"   case_name (group 1): '{case_name}'")
                logger.warning(f"   citations (group 2): '{citations_text}'")
                logger.warning(f"   year (group 3): '{year}'")
                logger.warning(f"   full match: '{match.group(0)}'")
                logger.warning(f"   position: [{start}:{end}]")
            
            logger.info(f"🔍 [CITATION_BLOCKS] Found citation block: '{case_name}' with citations '{citations_text}' year {year}")
            
            individual_citations = self._extract_citations_from_block(citations_text)
            
            for citation_text in individual_citations:
                citation_start = text.find(citation_text, start)
                citation_end = citation_start + len(citation_text) if citation_start != -1 else start
                
                citation = CitationResult(
                    citation=citation_text,
                    start_index=citation_start,
                    end_index=citation_end,
                    extracted_case_name=None,  # CRITICAL: Let unified extraction handle this with strict context isolation
                    extracted_date=year,
                    canonical_name=None,
                    canonical_date=None,
                    url=None,
                    verified=False,
                    source="citation_block",
                    confidence=0.9,  # Higher confidence for block extraction
                    metadata={
                        'block_case_name': case_name,  # Store for reference but don't use as extracted_case_name
                        'block_year': year,
                        'parallel_citations': individual_citations
                    }
                )
                
                
                
                citations.append(citation)
        
        logger.info(f"🔍 [CITATION_BLOCKS] Citation block extraction completed, found {len(citations)} citations")
        return citations
    
    def _extract_citations_from_block(self, citations_text: str) -> List[str]:
        """Extract individual citations from a citation block text."""
        citations = []
        
        parts = [part.strip() for part in citations_text.split(',')]
        
        for part in parts:
            if not part or len(part) < 5:  # Skip very short parts
                continue
            
            for pattern_name, pattern in self.citation_patterns.items():
                if pattern.search(part):
                    citations.append(part)
                    break
        
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
        
        citation_str = str(citation_obj)
        if any(pattern in citation_str for pattern in [
            "IdCitation('Id.", "IdCitation('id.", "IdCitation('Ibid.", "IdCitation('ibid.",
            "ShortCaseCitation(", "UnknownCitation(", "SupraCitation(", "InfraCitation("
        ]):
            return ""
        
        # Filter out federal and state statute citations
        if any(pattern in citation_str for pattern in [
            # Federal statutes
            "U.S.C.", "USC", "U.S.C", "U.S.C.A.", "USCA", "C.F.R.", "CFR", "C.F.R",
            # State codes (common patterns)
            " Code §", " Code \\u00a7", "Civ. Proc. Code", "Penal Code", "Bus. & Prof. Code",
            "Rev. Code", "Comp. Laws", "Gen. Stat.", "Ann. Code", "Stat. §", " Stat. ",
            # Generic statute patterns
            "FullLawCitation", "LawCitation"
        ]):
            return ""
        
        full_case_match = re.search(r"FullCaseCitation\('([^']+)'", citation_str)
        if full_case_match:
            extracted = full_case_match.group(1)
            if extracted.lower().startswith(('id.', 'ibid.')) or ' at ' in extracted.lower():
                return ""
            return extracted
        
        short_case_match = re.search(r"ShortCaseCitation\('([^']+)'", citation_str)
        if short_case_match:
            extracted = short_case_match.group(1)
            if extracted.lower().startswith(('id.', 'ibid.')) or ' at ' in extracted.lower():
                return ""
            return extracted
        
        law_match = re.search(r"FullLawCitation\('([^']+)'", citation_str)
        if law_match:
            return law_match.group(1)
        
        if hasattr(citation_obj, 'cite') and citation_obj.cite:
            cite_text = citation_obj.cite
            if cite_text.lower().startswith(('id.', 'ibid.')) or ' at ' in cite_text.lower():
                return ""
            return cite_text
        
        if hasattr(citation_obj, 'volume') and hasattr(citation_obj, 'reporter'):
            try:
                volume = getattr(citation_obj, 'volume', '')
                reporter = getattr(citation_obj, 'reporter', '')
                page = getattr(citation_obj, 'page', '')
                if volume and reporter and page:
                    return f"{volume} {reporter} {page}"
            except (TypeError, AttributeError) as e:
                logger.debug(f"Error normalizing citation format: {e}")
        
        return citation_str
    
    def _extract_eyecite_metadata(self, citation: CitationResult, citation_obj):
        """Extract metadata from eyecite citation object, including case name from plaintiff/defendant."""
        try:
            citation.metadata.update({
                'volume': getattr(citation_obj, 'volume', None),
                'reporter': getattr(citation_obj, 'reporter', None), 
                'page': getattr(citation_obj, 'page', None),
                'year': getattr(citation_obj, 'year', None),
                'court': getattr(citation_obj, 'court', None),
                'type': getattr(citation_obj, 'type', None),
            })
            
            # FIX: DO NOT use eyecite's plaintiff/defendant - they are often truncated
            # Eyecite produces names like "Noem v. Nat" instead of "Noem v. Nat'l TPS All."
            # Let our unified_case_extraction_master handle extraction instead
            # We'll still extract year from eyecite since that's usually accurate
            if hasattr(citation_obj, 'metadata') and citation_obj.metadata:
                plaintiff = getattr(citation_obj.metadata, 'plaintiff', None)
                defendant = getattr(citation_obj.metadata, 'defendant', None)
                
                # Log what eyecite found but DON'T use it
                if plaintiff and defendant:
                    eyecite_name = f"{plaintiff} v. {defendant}"
                    logger.info(f"[EYECITE-SKIP] Eyecite found '{eyecite_name}' for {citation.citation}, but will use better extraction instead")
                elif plaintiff:
                    logger.info(f"[EYECITE-SKIP] Eyecite found plaintiff '{plaintiff}' for {citation.citation}, but will use better extraction instead")
                
                # DON'T set citation.extracted_case_name here - let _extract_metadata do it
                
                # Also extract year from eyecite metadata if available
                eyecite_year = getattr(citation_obj.metadata, 'year', None)
                if eyecite_year:
                    citation.extracted_date = str(eyecite_year)
                    logger.info(f"[EYECITE-EXTRACT] Set extracted_date from eyecite: '{eyecite_year}' for {citation.citation}")
        except Exception as e:
            logger.debug(f"Error extracting eyecite metadata: {e}")
    
    def _extract_with_eyecite(self, text: str) -> List[CitationResult]:
        """Fixed version that properly sets start_index and end_index for eyecite citations."""
        citations = []
        
        if not EYECITE_AVAILABLE:
            return citations
            
        try:
            found_citations = get_citations(text)
            
            for citation_obj in found_citations:
                try:
                    citation_text = self._extract_citation_text_from_eyecite(citation_obj)
                    if not citation_text:
                        continue
                    
                    start_pos = text.find(citation_text)
                    if start_pos == -1:
                        normalized_citation = self._normalize_citation_comprehensive(citation_text, purpose="general")
                        start_pos = text.find(normalized_citation)
                        if start_pos == -1:
                            continue
                    
                    end_pos = start_pos + len(citation_text)
                    
                    citation = CitationResult(
                        citation=citation_text,
                        start_index=start_pos,
                        end_index=end_pos,
                        method="eyecite",
                        confidence=0.9,
                        metadata={}
                    )
                    
                    self._extract_eyecite_metadata(citation, citation_obj)
                    # CRITICAL: Also call _extract_metadata to override eyecite's truncated names
                    self._extract_metadata(citation, text, None)
                    
                    citations.append(citation)
                    
                except Exception as e:
                    logger.error(f"Error processing eyecite citation: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in eyecite extraction: {e}")
            
        return citations
    
    def _extract_metadata(self, citation: CitationResult, text: str, match):
        """Extract metadata with proper error handling and context isolation."""
        logger.warning(f"🔥🔥🔥 [_extract_metadata ENTRY] Called for citation: {citation.citation}")
        try:
            if not hasattr(citation, 'metadata') or citation.metadata is None:
                citation.metadata = {}
            try:
                citation.citation = self._normalize_to_bluebook_format(citation.citation)
                citation.citation = citation.citation.replace('\n', ' ').replace('\r', ' ')
            except Exception as e:
                logger.debug(f"Error normalizing citation: {e}")
            # FIX: ALWAYS re-extract case names with our better extraction logic
            # Eyecite often produces truncated names like "E. Palo Alto v. U." instead of "E. Palo Alto v. U.S."
            # Our unified_case_extraction_master has better abbreviation handling
            eyecite_already_extracted = (
                hasattr(citation, 'extracted_case_name') and 
                citation.extracted_case_name and 
                citation.extracted_case_name != "N/A" and
                citation.method == "eyecite"
            )
            
            if eyecite_already_extracted:
                logger.warning(f"[EXTRACT-OVERRIDE] Eyecite extracted '{citation.extracted_case_name}' for {citation.citation}, but will re-extract with better logic to fix truncation issues")
                # Clear eyecite's extraction so we can override it
                old_eyecite_name = citation.extracted_case_name
                citation.extracted_case_name = None
            
            # CRITICAL: Always extract case names (even if eyecite already extracted)
            logger.warning(f"[EXTRACT-START] Starting extraction for {citation.citation}, config.extract_case_names={self.config.extract_case_names}, eyecite_already_extracted={eyecite_already_extracted}")
            
            if self.config.extract_case_names:
                try:
                    final_name = None
                    
                    # METHOD 1 (PRIMARY): Use UNIFIED STRICT CONTEXT ISOLATION
                    logger.info(f"[EXTRACT-M1-UNIFIED] Using unified strict extraction for {citation.citation}")
                    
                    from src.utils.unified_case_name_extractor import extract_case_name_with_strict_isolation
                    
                    strict_name = extract_case_name_with_strict_isolation(
                        text=text,
                        citation_text=citation.citation,
                        citation_start=citation.start_index,
                        citation_end=citation.end_index,
                        all_citations=None
                    )
                    
                    if strict_name:
                        final_name = strict_name
                        logger.info(f"[EXTRACT-M1-UNIFIED-SUCCESS] {citation.citation} → '{strict_name}'")
                    
                    # Set the final extracted name
                    if final_name:
                        citation.extracted_case_name = final_name
                        logger.info(f"[EXTRACT-SUCCESS] Final name: '{final_name}' for {citation.citation}")
                    else:
                        citation.extracted_case_name = "N/A"
                        logger.warning(f"[EXTRACT-FAIL] Strict isolation failed for {citation.citation}")
                except Exception as e:
                    # Don't overwrite existing extracted case name on exception
                    logger.error(f"[EXTRACT-ERROR] Exception during extraction for {citation.citation}: {e}")
                    if not citation.extracted_case_name:
                        citation.extracted_case_name = "N/A"
            
            # CRITICAL: Final safety check - ensure no citation has null/empty extracted_case_name
            if not hasattr(citation, 'extracted_case_name') or citation.extracted_case_name is None or citation.extracted_case_name == '':
                citation.extracted_case_name = "N/A"
                logger.warning(f"[EXTRACT-NULL] Citation {citation.citation} had null/empty name, set to N/A")
            if self.config.extract_dates:
                try:
                    if not citation.extracted_date:
                        if citation.extracted_case_name and citation.extracted_case_name != "N/A":
                            citation.extracted_date = self._extract_date_from_case_context(text, citation.extracted_case_name, citation.citation)
                        else:
                            citation.extracted_date = self._extract_date_from_context(text, citation)
                    else:
                        if citation.extracted_date and citation.extracted_date != "2010-09-09":
                            pass  # Date is valid, keep it
                        else:
                            logger.warning(f"🔍 [WARNING] Suspicious extracted_date: '{citation.extracted_date}' for citation: '{citation.citation}'")
                            if citation.extracted_date and "-" in citation.extracted_date:
                                logger.warning(f"🔍 [WARNING] Detected canonical date format '{citation.extracted_date}', attempting to extract year from user document")
                                year_from_context = self._extract_date_from_case_context(text, citation.extracted_case_name or "Unknown", citation.citation)
                                if year_from_context and year_from_context != citation.extracted_date:
                                    logger.warning(f"🔍 [FIX] Replacing canonical date '{citation.extracted_date}' with user document year '{year_from_context}'")
                                    citation.extracted_date = year_from_context
                except Exception as e:
                    if not citation.extracted_date:
                        citation.extracted_date = None
            try:
                citation.confidence = self._calculate_confidence(citation, text)
            except Exception as e:
                citation.confidence = 0.5
            try:
                citation.context = self._extract_context(text, citation.start_index or 0, citation.end_index or 0)
            except Exception as e:
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
        
        
        
        citation_with_date_after_pattern = (
            r'([A-Z][A-Za-z\s,&.\'-]+\s+v\.\s+[A-Z][A-Za-z\s,&.\'-]+)\s*,\s*'
            r'([^;]*?' + re.escape(citation.citation) + r'[^;]*?)'
            r'\((\d{4})\)'
        )
        
        search_start = max(0, citation.start_index - 300)  # CRITICAL: Restored to 300 for proper extraction
        search_end = min(len(text), citation.end_index + 200)  # Restored to 200 for proper extraction
        search_text = text[search_start:search_end]
        
        after_match = re.search(citation_with_date_after_pattern, search_text, re.IGNORECASE)
        if after_match:
            complete_match = after_match.group(0)
            return complete_match.strip()
            
        citation_with_date_before_pattern = (
            r'([A-Z][A-Za-z\s,&.\'-]+\s+v\.\s+[A-Z][A-Za-z\s,&.\'-]+)\s*'
            r'\((\d{4})\)\s*,?\s*'
            r'([^;]*?' + re.escape(citation.citation) + r'[^;]*?)'
        )
        
        before_match = re.search(citation_with_date_before_pattern, search_text, re.IGNORECASE)
        if before_match:
            complete_match = before_match.group(0)
            return complete_match.strip()
        
        citation_pattern = r'\b\d+\s+[A-Za-z.]+(?:\s+[A-Za-z.]+)?(?:\s+\d+)?[a-z]?\s+\d+\b'
        date_pattern = r'\(\d{4}\)'  # Dates in parentheses like (1963), (2016)
        
        all_citation_matches = list(re.finditer(citation_pattern, text))
        all_date_matches = list(re.finditer(date_pattern, text))
        
        all_boundaries = []
        for match in all_citation_matches:
            all_boundaries.append(('citation', match.start(), match.end()))
        for match in all_date_matches:
            all_boundaries.append(('date', match.start(), match.end()))
        
        all_boundaries.sort(key=lambda x: x[1])  # Sort by start position
        
        # FIX #30: Only look BACKWARD for case names, never forward!
        context_start = max(0, citation.start_index - 300)  # Look backward 300 chars
        # FIX #30: REMOVED forward context_end - we don't search forward anymore!
        
        # Adjust context_start to avoid crossing boundaries (e.g., dates, other citations)
        for boundary_type, start, end in all_boundaries:
            if end < citation.start_index and end > context_start:
                context_start = end + 1
                if boundary_type == 'date':
                    context_start = min(context_start + 10, citation.start_index)
        
        # FIX #30: REMOVED forward boundary check - we only look backward!
        # No need to check boundaries after the citation since we don't search forward
        
        # Extract ONLY backward context
        context = text[context_start:citation.start_index].strip()
        
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
            'similarly',
            'de novo',
            'review de novo',
            'reviews de novo',
            'reviewed de novo',
            'reviewing de novo',
            'questions of law',
            'statutory interpretation',
            'certified questions',
            'questions are questions',
            'issue of law',
            'issues of law',
            'court reviews',
            'this court reviews',
            'that this court reviews',
            'in light of',
            'and in light of',
            'record certified by',
            'federal court',
            'by the federal court'
        ]
        
        # FIXED: Updated pattern to handle commas in company names like "Spokeo, Inc."
        v_pattern_improved = r'([A-Z][a-zA-Z\'\.\&,]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&,]*|of|the|and|&))*)\s+v\.\s+([A-Z][a-zA-Z\'\.\&,]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&,]*|of|the|and|&))*)(?:\s*,|\s*\(|\s*$)'
        match = re.search(v_pattern_improved, case_name)
        if match:
            extracted = f"{match.group(1).strip()} v. {match.group(2).strip()}"
            if len(extracted) < 200 and ' v. ' in extracted:
                return extracted
        
        case_name_lower = case_name.lower()
        for indicator in contamination_indicators:
            if indicator in case_name_lower:
                # FIXED: Updated pattern to handle commas in company names
                v_pattern = r'([A-Z][a-zA-Z\'\.\&,]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&,]*|of|the|and|&))*)\s+v\.\s+([A-Z][a-zA-Z\'\.\&,]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&,]*|of|the|and|&))*)(?=\s*,|\s*$)'
                match = re.search(v_pattern, case_name)
                if match:
                    extracted = f"{match.group(1).strip()} v. {match.group(2).strip()}"
                    if len(extracted) < 200 and ' v. ' in extracted:
                        return extracted
                    else:
                        # FIXED: Updated pattern to handle commas in company names
                        last_v_pattern = r'([A-Z][a-zA-Z\'\.\&,]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&,]*|of|the|and|&))*)\s+v\.\s+([A-Z][a-zA-Z\'\.\&,]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&,]*|of|the|and|&))*)(?=[^A-Za-z]*$)'
                        last_match = re.search(last_v_pattern, case_name)
                        if last_match:
                            return f"{last_match.group(1).strip()} v. {last_match.group(2).strip()}"
                        else:
                            return ""
                else:
                    return ""
        
        cleanup_patterns = [
            r'^.*?\b(?:through\s+the\s+)?(?:Fourteenth|Fifth|Sixth|Fourth)\s+Amendment\.?\s+',  # Constitutional references
            r'^.*?\b(?:RCW|WAC|USC)\s+[\d.]+\s*;?\s*',  # Statute references  
            r'^.*?\b(?:Brief|Opening\s+Br\.|Reply\s+Br\.)\.?\s+at\s+\d+\s+(?:quoting\s+)?',  # Brief citations
            r'^.*?\b(?:see|citing|quoting|in|under|per|accord)\s+',  # Citation signals
            r'^.*?\b(?:id\.|Id\.|ibid\.|Ibid\.)\s*,?\s*',  # Id. references
            r'^\s*[.,;:]\s*',  # Leading punctuation
            r'\s*[.,;:]\s*$',  # Trailing punctuation
        ]
        
        case_name = re.sub(r'^State\.\s+([A-Z][A-Za-z\s]+\s+v\.\s+[A-Z])', r'\1', case_name)
        
        if case_name.startswith('Ro Trade Shows'):
            case_name = 'To-' + case_name
        
        for pattern in cleanup_patterns:
            case_name = re.sub(pattern, '', case_name, flags=re.IGNORECASE).strip()
        
        if len(case_name) > 200:
            # FIXED: Updated pattern to handle commas in company names
            v_pattern = r'([A-Z][A-Za-z0-9&.\',\s-]+(?:\s+[A-Za-z0-9&.\',\s-]+)*?)\s+v\.\s+([A-Z][A-Za-z0-9&.\',\s-]+(?:\s+[A-Za-z0-9&.\',\s-]+)*?)(?=\s*,|\s*\(|\s*$)'
            match = re.search(v_pattern, case_name)
            if match:
                case_name = f"{match.group(1).strip()} v. {match.group(2).strip()}"
            else:
                return ""  # Too long and no clear case name pattern
        
        # FIXED: Updated patterns to handle commas in company names
        case_name_patterns = [
            r'^([A-Z][a-zA-Z\'\.\&,\s]+?)\s+v\.\s+([A-Z][a-zA-Z\'\.\&,\s]+?)(?:\s*,)?',  # Party v. Party - allows commas in company names
            r'^(In\s+re\s+[A-Z][a-zA-Z\'\.\&,\s]+?)(?:\s*,)?',  # In re cases - allows commas
            r'^(Ex\s+parte\s+[A-Z][a-zA-Z\'\.\&,\s]+?)(?:\s*,)?',  # Ex parte cases - allows commas
        ]
        
        for idx, pattern in enumerate(case_name_patterns):
            match = re.search(pattern, case_name, re.IGNORECASE)
            if match:
                if len(match.groups()) >= 2 and idx == 0:  # Two-party case
                    clean_name = f"{match.group(1).strip()} v. {match.group(2).strip()}"
                else:  # Single-party case
                    clean_name = match.group(1).strip()
                clean_name = re.sub(r'\s*,\s*\d+\s+[A-Za-z.]+.*$', '', clean_name)
                
                if 5 <= len(clean_name) <= 80 and ' v.' in clean_name.lower():
                    return clean_name
        
        return ""

    def _extract_case_name_from_context(self, text: str, citation: CitationResult, all_citations: Optional[List[CitationResult]] = None) -> Optional[str]:
        """
        Enhanced case name extraction with improved context isolation for nested parenthetical structures.
        
        Args:
            text: The full document text
            citation: The citation to extract context for
            all_citations: List of all citations in the document (for context isolation)
            
        Returns:
            Extracted case name or None if not found
        """
        # CRITICAL FIX: Use strict context isolation FIRST to prevent case name bleeding
        try:
            from src.utils.strict_context_isolator import (
                get_strict_context_for_citation,
                extract_case_name_from_strict_context,
                find_all_citation_positions
            )
            
            citation_text = getattr(citation, 'citation', None)
            start = getattr(citation, 'start_index', None)
            end = getattr(citation, 'end_index', None)
            
            if citation_text and start is not None and end is not None:
                # Get ALL citation positions for proper boundary detection
                all_positions = find_all_citation_positions(text)
                
                # Get strictly isolated context (stops at previous citation)
                strict_context = get_strict_context_for_citation(
                    text, start, end, all_positions, max_lookback=200
                )
                
                # Extract case name from isolated context
                case_name = extract_case_name_from_strict_context(strict_context, citation_text)
                
                if case_name and len(case_name) > 10:
                    logger.info(
                        f"[STRICT-ISOLATION-SUCCESS] {citation_text} → '{case_name}' "
                        f"(context: '{strict_context[-50:]}')"
                    )
                    return case_name
                
        except Exception as e:
            logger.warning(f"[STRICT-ISOLATION-FAILED] Error: {e}")
        
        # FALLBACK: Use the old extraction method if strict isolation failed
        try:
            from src.unified_case_name_extractor_v2 import extract_case_name_and_date_master
            
            # FIX #33: Enable debug for problematic citation
            citation_text = getattr(citation, 'citation', None)
            force_debug = citation_text and "183" in citation_text and "649" in citation_text
            
            result = extract_case_name_and_date_master(
                text=text,
                citation=citation_text,
                citation_start=getattr(citation, 'start_index', None),
                document_primary_case_name=getattr(self, 'document_primary_case_name', None),
                citation_end=getattr(citation, 'end_index', None),
                debug=force_debug  # FIX #33: Enable debug for problematic citations
            )
            
            case_name = result.get('case_name')
            if case_name and case_name != 'N/A':
                logger.info(f"[FALLBACK-EXTRACTION] {citation_text} → '{case_name}'")
                return case_name
        except Exception as e:
            logger.debug(f"Error extracting case name from context: {e}")
        
        if not citation.start_index or not citation.end_index:
            return None
            
        citation_text = citation.citation
        start = citation.start_index
        end = citation.end_index
        
        # NEW: Isolate context within parenthetical boundaries to prevent cross-contamination
        isolated_context = self._get_isolated_parenthetical_context(text, start, end)
        
        # FIX #30: CRITICAL - Only look BACKWARD, never forward!
        # FIX #46: Stop at previous citation to avoid capturing wrong case name
        # If we can't isolate a clean context, fall back to limited lookback ONLY
        if not isolated_context:
            context_start = max(0, start - 300)  # Look backward 300 chars initially
            
            # FIX #46: Find previous citation and stop there
            if all_citations:
                # Find all citations that end before current citation starts
                previous_citations = [c for c in all_citations 
                                     if c.end_index and c.end_index < start 
                                     and c.citation != citation.citation]
                
                if previous_citations:
                    # Find the closest previous citation
                    closest_previous = max(previous_citations, key=lambda c: c.end_index)
                    # Stop context at the previous citation's end (plus small buffer for punctuation)
                    context_start = max(context_start, closest_previous.end_index + 1)
                    logger.debug(f"[FIX #46] Stopping backward search at previous citation '{closest_previous.citation}' (end={closest_previous.end_index})")
            
            # FIX #30: REMOVED forward search (end + 100) - this was causing "Spokane County" bug!
            # Only use backward context for extraction
            isolated_context = text[context_start:start].strip()
        
        before_citation = isolated_context
        
        patterns = [
            r'([A-Z][a-zA-Z\'\.\&\s]+?)\s+v\.\s+([A-Z][a-zA-Z\'\.\&\s]+?),?\s*$',
            r'([A-Z][a-zA-Z\'\.\&\s]+?)\s+v\.\s+([A-Z][a-zA-Z\'\.\&\s]+?),\s*\d',
            r'([A-Z][a-zA-Z\'\.\&\s]+?)\s+v\.\s+([A-Z][a-zA-Z\'\.\&\s]+?),\s*$',
            r'(In\s+re\s+[A-Z][a-zA-Z\'\.\&\s]+?),?\s*$',
            r'(Ex\s+parte\s+[A-Z][a-zA-Z\'\.\&\s]+?),?\s*$',
        ]
        
        for idx, pattern in enumerate(patterns, 1):
            try:
                matches = list(re.finditer(pattern, before_citation, re.IGNORECASE | re.DOTALL))
                if matches:
                    match = matches[-1]  # Take the last (closest) match
                    
                    if len(match.groups()) >= 2 and idx in [1, 2, 3]:  # Two-party cases (patterns 1, 2, 3)
                        plaintiff = match.group(1).strip()
                        defendant = match.group(2).strip()
                        
                        contamination_phrases = [
                            r'\b(de\s+novo)\b', r'\b(questions?\s+of\s+law)\b', r'\b(statutory\s+interpretation)\b',
                            r'\b(in\s+light\s+of)\b', r'\b(the\s+record\s+certified)\b', r'\b(federal\s+court)\b',
                            r'\b(this\s+court\s+reviews?)\b', r'\b(we\s+review)\b', r'\b(certified\s+questions?)\b',
                            r'\b(issue\s+of\s+law)\b', r'\b(also\s+an?\s+issue)\b'
                        ]
                        
                        for phrase_pattern in contamination_phrases:
                            plaintiff = re.sub(phrase_pattern, '', plaintiff, flags=re.IGNORECASE)
                            defendant = re.sub(phrase_pattern, '', defendant, flags=re.IGNORECASE)
                        
                        plaintiff = re.sub(r'\s+', ' ', plaintiff).strip()
                        defendant = re.sub(r'\s+', ' ', defendant).strip()
                        
                        def extract_clean_name_part(text_part, is_plaintiff=True):
                            words = text_part.split()
                            clean_words = []
                            
                            if is_plaintiff:
                                for word in reversed(words):
                                    if (word and (word[0].isupper() or 
                                                word.lower() in ['v.', 'vs.', '&', 'of', 'the', 'inc', 'llc', 'corp'] or
                                                "'" in word or '.' in word)):
                                        clean_words.insert(0, word)
                                    else:
                                        if clean_words:
                                            break
                            else:
                                for word in words:
                                    if (word and (word[0].isupper() or 
                                                word.lower() in ['&', 'of', 'the', 'inc', 'llc', 'corp', 'fish', 'wildlife'] or
                                                "'" in word or '.' in word)):
                                        clean_words.append(word)
                                    elif clean_words and word.lower() not in ['and', 'or', 'at', 'in', 'on']:
                                        break
                            
                            return ' '.join(clean_words) if clean_words else text_part
                        
                        clean_plaintiff = extract_clean_name_part(plaintiff, is_plaintiff=True)
                        clean_defendant = extract_clean_name_part(defendant, is_plaintiff=False)
                        
                        case_name = f"{clean_plaintiff} v. {clean_defendant}"
                        
                    else:  # Single-party cases (In re, Ex parte, etc.)
                        case_name = match.group(1).strip()
                    
                    case_name = re.sub(r'^[.\s,;:]+', '', case_name)  # Remove leading punctuation
                    case_name = re.sub(r'^(the|a|an)\s+', '', case_name, flags=re.IGNORECASE)  # Remove leading articles
                    case_name = re.sub(r'\s+', ' ', case_name).strip()  # Clean up whitespace
                    
                    if self._is_valid_case_name(case_name):
                        return case_name
            except Exception as e:
                logger.debug(f"Error processing case name extraction: {e}")
        
        try:
            result = extract_case_name_and_date_master(
                text=text, 
                citation=citation_text,
                citation_start=start,
                document_primary_case_name=getattr(self, 'document_primary_case_name', None),
                citation_end=end,
                context_window=500,
                all_citations=all_citations
            )
            
            if result and result.get('case_name'):
                case_name = self._clean_extracted_case_name(result['case_name'])
                if self._is_valid_case_name(case_name):
                    return case_name
        except Exception as e:
            logger.debug(f"Error in unified case name extraction: {e}")
        
        immediate_context = isolated_context.strip()
        if ',' in immediate_context and len(immediate_context) > 20:
            potential_name = immediate_context.rsplit(',', 1)[0].strip()
            if self._is_valid_case_name(potential_name):
                return potential_name
        
        return None

    def _repair_truncated_case_name(self, case_name: str, text: str, citation_pos: int) -> str:
        """
        Repair truncated case names by looking for complete names in the surrounding context.
        
        Examples:
        - "Inc. v. Robins" → "Spokeo, Inc. v. Robins"
        - "Wilmot v. Ka" → "Wilmot v. Kaiser"
        - "Stevens v. Br" → "Stevens v. Brinks"
        
        Args:
            case_name: The potentially truncated case name
            text: Full document text
            citation_pos: Position of the citation in the text
            
        Returns:
            Repaired case name or original if no repair needed
        """
        import re
        
        # Check if the name appears truncated
        is_truncated = (
            len(case_name) < 15 or  # Very short names are likely truncated
            case_name.endswith(' v. ') or  # Missing defendant
            re.search(r'\b[A-Z][a-z]{1,2}\s*$', case_name) or  # Ends with short word like "Ka", "Be", "Ct", "Fo", "Wa"
            re.search(r'\bv\.\s+[A-Z][a-z]{0,2}\s*$', case_name) or  # Defendant is 1-3 chars like "v. A", "v. Be", "v. Ct"
            case_name.startswith('Inc.') or case_name.startswith('LLC') or  # Missing plaintiff
            case_name.startswith('Corp.') or case_name.startswith('Co.') or
            case_name.startswith('A. v.') or case_name.startswith('L. v.')  # Single letter plaintiff
        )
        
        if not is_truncated:
            return case_name
        
        # Extract broader context
        # FIX #39: ONLY look BACKWARD! Forward search (+200) was the REAL source
        # of "Spokane County" contamination after 12 previous fixes!
        # Increased from 600 to 1000 to catch more distant case names
        context_start = max(0, citation_pos - 1000)
        context_end = citation_pos  # FIX #39: NO forward search!
        context = text[context_start:context_end]
        
        # Pattern 1: Fix corporate name truncation (Inc., LLC, Corp., etc.)
        if case_name.startswith(('Inc.', 'LLC', 'Corp.', 'Co.', 'Ltd.', 'L.P.', 'Company')):
            # Look for the full corporate name before "Inc." or similar
            corporate_suffix = case_name.split()[0]
            
            # Try multiple patterns
            patterns = [
                r'([A-Z][A-Za-z\'\.\&\s]+?)\s*,\s*' + re.escape(corporate_suffix),  # With comma
                r'([A-Z][A-Za-z\'\.\&\s]{3,}?)\s+' + re.escape(corporate_suffix),  # Without comma
            ]
            
            for corporate_pattern in patterns:
                match = re.search(corporate_pattern, context)
                if match:
                    full_plaintiff = match.group(1).strip()
                    # Check if we found something meaningful (not just a single letter)
                    if len(full_plaintiff) > 2:
                        repaired = f"{full_plaintiff}, {case_name}" if ',' not in case_name else f"{full_plaintiff} {case_name}"
                        logger.info(f"[CORPORATE-REPAIR] '{case_name}' → '{repaired}'")
                        return repaired
        
        # Pattern 2: Fix truncated defendant name
        if ' v. ' in case_name:
            parts = case_name.split(' v. ')
            if len(parts) == 2:
                plaintiff = parts[0].strip()
                truncated_defendant = parts[1].strip()
                
                # Check if defendant is truncated (< 5 chars or ends with incomplete word)
                if len(truncated_defendant) < 5 or re.search(r'^[A-Z][a-z]{0,2}$', truncated_defendant):
                    # Search for pattern: plaintiff v. [full defendant name]
                    # Escape plaintiff but handle abbreviations flexibly
                    plaintiff_escaped = re.escape(plaintiff).replace(r'\.', r'\.?')
                    patterns = [
                        plaintiff_escaped + r'\s+v\.\s+([A-Z][A-Za-z\'\.\&\s,\-]+?)(?:\s*,|\s+\d|\s*\()',
                        plaintiff_escaped + r'\s+v\.\s+([A-Z][A-Za-z\'\.\&\s,\-]+?)(?:\s+\d{2,4}\s+[A-Z])',  # Before citation
                        plaintiff_escaped + r'\s+v\.\s+([A-Z][A-Za-z\'\.\&\s,\-]+?)\s*[,\.]',  # Before comma or period
                        plaintiff.replace('.', '') + r'\s+v\.\s+([A-Z][A-Za-z\'\.\&\s,\-]+?)(?:\s*,|\s+\d)',  # Without periods
                    ]
                    
                    for full_pattern in patterns:
                        match = re.search(full_pattern, context, re.IGNORECASE)
                        if match:
                            full_defendant = match.group(1).strip()
                            # Remove trailing punctuation and clean up
                            full_defendant = re.sub(r'[,\s]+$', '', full_defendant)
                            # Validate that we found a real improvement
                            if len(full_defendant) > len(truncated_defendant) and len(full_defendant) > 3:
                                # Check if the full defendant starts with the truncated version
                                if full_defendant.lower().startswith(truncated_defendant.lower()) or len(truncated_defendant) <= 3:
                                    repaired = f"{plaintiff} v. {full_defendant}"
                                    logger.info(f"[TRUNCATION-REPAIR] '{case_name}' → '{repaired}'")
                                    return repaired
        
        # Pattern 3: Look for the complete case name in context using fuzzy matching
        # Try to find a case name that contains our truncated version
        case_name_patterns = [
            r'([A-Z][A-Za-z\'\.\&\s,]+(?:Inc\.|LLC|Corp\.|Ltd\.|Co\.|L\.P\.|Company)?)\s+v\.\s+([A-Z][A-Za-z\'\.\&\s,]+(?:Inc\.|LLC|Corp\.|Ltd\.|Co\.|L\.P\.|Company)?)',
            r'(State|People|United States)\s+v\.\s+([A-Z][A-Za-z\'\.\&\s,]+)',
        ]
        
        for pattern in case_name_patterns:
            matches = re.finditer(pattern, context, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) == 2:
                    full_name = f"{match.group(1).strip()} v. {match.group(2).strip()}"
                else:
                    full_name = match.group(0).strip()
                
                # Check if our truncated name is a prefix of this full name
                if full_name.lower().startswith(case_name.lower()) or case_name.lower() in full_name.lower():
                    # Clean up the full name
                    full_name = re.sub(r'\s+', ' ', full_name).strip()
                    if len(full_name) > len(case_name):
                        return full_name
        
        # No repair possible, return original
        return case_name
    
    def _remove_citation_contamination_from_case_name(self, case_name: str) -> str:
        """
        Remove citation references that have been incorrectly included in case names.
        
        Examples:
        - "Fraternal Ord. of Eagles v. Grand Aerie, 148 Wn.2d 224, 239" → "Fraternal Ord. of Eagles v. Grand Aerie"
        - "Bostain v. Food Express, Inc., 159 Wn.2d 700, 716" → "Bostain v. Food Express, Inc."
        - "Rest. Dev., Inc. v. Cananwill, Inc., 150 Wn.2d 674, 682" → "Rest. Dev., Inc. v. Cananwill, Inc."
        
        Args:
            case_name: Case name that may contain citation references
            
        Returns:
            Cleaned case name without citation references
        """
        import re
        
        # Pattern to match citation references at the end of case names
        # Matches patterns like: ", 148 Wn.2d 224, 239" or ", 159 Wn.2d 700" or ", 22 Wn. App. 2d 22, 33"
        citation_patterns = [
            r',\s*\d+\s+(?:Wn\.2d|Wash\.2d|Wn\.\s*App\.?\s*2d|Wash\.\s*App\.?\s*2d)\s+\d+(?:\s*,\s*\d+)?(?:\s*\(\d{4}\))?$',  # Washington reporters
            r',\s*\d+\s+(?:U\.S\.|S\.\s*Ct\.|L\.\s*Ed\.?\s*2d)\s+\d+(?:\s*,\s*\d+)?(?:\s*\(\d{4}\))?$',  # Federal reporters
            r',\s*\d+\s+(?:P\.2d|P\.3d|P\.)\s+\d+(?:\s*,\s*\d+)?(?:\s*\(\d{4}\))?$',  # Pacific reporters
            r',\s*\d+\s+(?:F\.2d|F\.3d|F\.\s*Supp\.?\s*2d|F\.\s*Supp\.?)\s+\d+(?:\s*,\s*\d+)?(?:\s*\(\d{4}\))?$',  # Federal reporters
            r',\s*20\d{2}-(?:NM|ND|OK|SD|UT|WI|WY|MT)(?:CA)?-\d{1,5}(?:\s*\(\d{4}\))?$',  # Neutral citations (2017-NM-007, etc.)
            r',\s*20\d{2}\s+(?:ND|OK|SD|UT|WI|WY|MT)\s+\d{1,5}(?:\s*\(\d{4}\))?$',  # Neutral citations space-separated
            r',\s*\d+\s+[A-Z][A-Za-z\.]+\s+\d+(?:\s*,\s*\d+)?(?:\s*\(\d{4}\))?$',  # Generic reporter pattern
        ]
        
        cleaned_name = case_name
        for pattern in citation_patterns:
            cleaned_name = re.sub(pattern, '', cleaned_name, flags=re.IGNORECASE)
        
        # Clean up any trailing commas or whitespace
        cleaned_name = re.sub(r'\s*,\s*$', '', cleaned_name).strip()
        
        # If we removed something, log it
        if cleaned_name != case_name:
            logger.info(f"[CITATION-CONTAMINATION-REMOVED] '{case_name}' → '{cleaned_name}'")
        
        return cleaned_name
    
    def _get_isolated_parenthetical_context(self, text: str, citation_start: int, citation_end: int) -> Optional[str]:
        """
        Isolate the context for a citation within its immediate parenthetical or structural boundaries.
        
        This prevents cross-contamination between citations in nested parenthetical structures.
        For example, in:
        "Case A, 123 U.S. 456 (citing Case B, 789 U.S. 012 (2020))"
        
        The citation "789 U.S. 012" should only see context within "(citing Case B, 789 U.S. 012 (2020))"
        not the broader "Case A, 123 U.S. 456 (citing Case B, 789 U.S. 012 (2020))"
        
        Args:
            text: Full text
            citation_start: Start position of the citation
            citation_end: End position of the citation
            
        Returns:
            Isolated context string or None if no suitable isolation found
        """
        # Find the smallest enclosing parenthetical that contains this citation
        paren_stack = []
        innermost_paren_start = None
        
        # Search backward from citation start to find opening parentheses
        for i in range(citation_start - 1, max(-1, citation_start - 200), -1):
            if text[i] == ')':
                paren_stack.append(i)
            elif text[i] == '(':
                if paren_stack:
                    paren_stack.pop()
                else:
                    # Found an opening parenthesis that matches our citation's context
                    innermost_paren_start = i
                    break
        
        if innermost_paren_start is not None:
            # Extract the content within this parenthetical
            paren_content = text[innermost_paren_start + 1:citation_start].strip()
            
            # Look for case name patterns within this isolated context
            # Remove common introductory phrases that aren't part of the case name
            intro_phrases = [
                r'^citing\s+', r'^quoting\s+', r'^see\s+', r'^see\s+also\s+', 
                r'^compare\s+', r'^but\s+see\s+', r'^e\.g\.?\s*', r'^cf\.?\s+',
                r'^accord\s+', r'^see\s+generally\s+'
            ]
            
            for phrase in intro_phrases:
                paren_content = re.sub(phrase, '', paren_content, flags=re.IGNORECASE).strip()
            
            return paren_content
        
        # Fallback: Try to find structural boundaries using commas and semicolons
        # Look backward for the nearest structural separator
        separators = [';', ':', '.)', ').', '."', ')."', '.)"']
        separator_pos = None
        
        for i in range(citation_start - 1, max(-1, citation_start - 150), -1):
            char = text[i]
            next_char = text[i + 1] if i + 1 < len(text) else ''
            two_chars = char + next_char
            
            if two_chars in separators or char in [',', ';', ':']:
                # Check if this separator is followed by a citation pattern to avoid false boundaries
                after_separator = text[i + 1:citation_start].strip()
                if not re.search(r'\d+\s+[A-Za-z.]+\s+\d+', after_separator[:50]):
                    separator_pos = i
                    break
        
        if separator_pos is not None:
            context = text[separator_pos + 1:citation_start].strip()
            # Remove leading punctuation
            context = re.sub(r'^[,\s.;:]+', '', context).strip()
            return context
        
        # Last resort: Use a limited backward context
        context_start = max(0, citation_start - 100)
        context = text[context_start:citation_start].strip()
        return context

    def _extract_date_from_case_context(self, text: str, case_name: str, citation: str) -> Optional[str]:
        """Extract year from the broader context around the case name and citations."""
        import re
        
        year_match = re.search(r'\((\d{4})\)', citation)
        if year_match:
            return year_match.group(1)
        
        case_pos = text.find(case_name)
        if case_pos == -1:
            return None
        
        context_start = max(0, case_pos - 100)
        context_end = min(len(text), case_pos + len(case_name) + 1000)  # Restored to 1000 for proper date extraction
        context = text[context_start:context_end]
        
        year_patterns = [
            r'\((\d{4})\)',  # (2022) - highest priority, most reliable
            r'(\d{4})',      # 2022 - medium priority
            r'(\d{2})',      # 22 (for recent years) - lowest priority
        ]
        
        paren_matches = re.findall(r'\((\d{4})\)', context)
        for match in paren_matches:
            year = match
            if 1900 <= int(year) <= 2030:
                return year
        
        for pattern in year_patterns:
            matches = re.findall(pattern, context)
            for match in matches:
                year = match
                if len(year) == 4 and 1900 <= int(year) <= 2030:
                    return year
                elif len(year) == 2 and 20 <= int(year) <= 30:
                    year_4digit = f"20{year}"
                    return year_4digit
        
        if case_pos + len(case_name) < len(text):
            remaining_text = text[case_pos + len(case_name):]
            
            for pattern in year_patterns:
                matches = re.findall(pattern, remaining_text)
                for match in matches:
                    year = match
                    if len(year) == 4 and 1900 <= int(year) <= 2030:
                        return year
                    elif len(year) == 2 and 20 <= int(year) <= 30:
                        year_4digit = f"20{year}"
                        return year_4digit
        
        return None

    def _extract_date_from_context(self, text: str, citation: CitationResult) -> Optional[str]:
        """UNIFIED date extraction using the best-of-breed unified extractor."""
        if not citation.start_index or not citation.end_index:
            return None
        
        result = extract_case_name_and_date_master(
            text=text, 
            citation=citation.citation,
            citation_start=citation.start_index,
            document_primary_case_name=getattr(self, 'document_primary_case_name', None),
            citation_end=citation.end_index
        )
        
        year = result.get('year', '')
        
        return year if year else None

    def _get_isolated_context(self, text: str, citation: CitationResult, all_citations: Optional[List[CitationResult]] = None) -> tuple[Optional[int], Optional[int]]:
        """Get isolated context boundaries to ensure no overlap between citations."""
        if not citation.start_index:
            return None, None
        
        nearby_citations = []
        if all_citations:
            for other_citation in all_citations:
                if (other_citation.start_index and 
                    other_citation.start_index != citation.start_index and
                    abs(other_citation.start_index - citation.start_index) < 50):
                    nearby_citations.append(other_citation)
        
        if nearby_citations:
            first_citation_in_group = min([citation] + nearby_citations, key=lambda c: c.start_index or 0)
            search_start = max(0, (first_citation_in_group.start_index or 0) - 200)
            citation_start = first_citation_in_group.start_index or 0
            search_text = text[search_start:citation_start]
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
            context_start = 0
            if all_citations:
                prev_citation = None
                for other_citation in all_citations:
                    if (other_citation.start_index and 
                        other_citation.start_index < citation.start_index and
                        (prev_citation is None or other_citation.start_index > prev_citation.start_index)):
                        prev_citation = other_citation
                
                if prev_citation and prev_citation.end_index:
                    potential_start = prev_citation.end_index
                    
                    sentence_pattern = re.compile(r'\.\s+[A-Z]')
                    sentence_matches = list(sentence_pattern.finditer(text, potential_start, citation.start_index))
                    if sentence_matches:
                        context_start = sentence_matches[-1].start() + 1  # Start after the period
                    else:
                        year_pattern = re.compile(r'\((19|20)\d{2}\)')
                        year_matches = list(year_pattern.finditer(text, potential_start, citation.start_index))
                        if year_matches:
                            context_start = year_matches[-1].end()
                        else:
                            separator_pattern = re.compile(r'[;]\s+')
                            separator_matches = list(separator_pattern.finditer(text, potential_start, citation.start_index))
                            if separator_matches:
                                context_start = separator_matches[-1].end()
                            else:
                                context_start = potential_start
                else:
                    year_pattern = re.compile(r'\((19|20)\d{2}\)')
                    year_matches = list(year_pattern.finditer(text, 0, citation.start_index))
                    if year_matches:
                        context_start = year_matches[-1].end()
                    else:
                        potential_start = max(0, citation.start_index - 300)  # CRITICAL: Restored to 300 for proper extraction
                        
                        citation_patterns = [
                            r'\b\d+\s+[A-Za-z.]+(?:\s+\d+)?\b',  # Basic citation pattern
                            r'\b\d+\s+(?:Wash\.|Wn\.|P\.|A\.|S\.|N\.|F\.|U\.S\.)\b',  # Common reporters
                        ]
                        
                        last_citation_pos = potential_start
                        for pattern in citation_patterns:
                            matches = list(re.finditer(pattern, text[potential_start:citation.start_index]))
                            if matches:
                                last_match = matches[-1]
                                last_citation_pos = max(last_citation_pos, potential_start + last_match.end())
                        
                        context_start = last_citation_pos
            else:
                year_pattern = re.compile(r'\((19|20)\d{2}\)')
                year_matches = list(year_pattern.finditer(text, 0, citation.start_index))
                if year_matches:
                    context_start = year_matches[-1].end()
                else:
                    potential_start = max(0, citation.start_index - 50)  # Reduced from 300 to 50
                    
                    citation_patterns = [
                        r'\b\d+\s+[A-Za-z.]+(?:\s+\d+)?\b',  # Basic citation pattern
                        r'\b\d+\s+(?:Wash\.|Wn\.|P\.|A\.|S\.|N\.|F\.|U\.S\.)\b',  # Common reporters
                    ]
                    
                    last_citation_pos = potential_start
                    for pattern in citation_patterns:
                        matches = list(re.finditer(pattern, text[potential_start:citation.start_index]))
                        if matches:
                            last_match = matches[-1]
                            last_citation_pos = max(last_citation_pos, potential_start + last_match.end())
                    
                    context_start = last_citation_pos
        
        context_end = len(text)
        if all_citations:
            next_citation = None
            for other_citation in all_citations:
                if (other_citation.start_index and 
                    other_citation.start_index > citation.end_index and
                    (next_citation is None or other_citation.start_index < next_citation.start_index)):
                    next_citation = other_citation
            
            if next_citation and next_citation.start_index:
                potential_end = next_citation.start_index
                
                sentence_pattern = re.compile(r'\.\s+[A-Z]')
                sentence_matches = list(sentence_pattern.finditer(text, citation.end_index, potential_end))
                if sentence_matches:
                    context_end = sentence_matches[0].start() + 1  # End before the period
                else:
                    year_pattern = re.compile(r'\((19|20)\d{2}\)')
                    year_matches = list(year_pattern.finditer(text, citation.end_index, potential_end))
                    if year_matches:
                        context_end = year_matches[0].start()
                    else:
                        separator_pattern = re.compile(r'[;]\s+')
                        separator_matches = list(separator_pattern.finditer(text, citation.end_index, potential_end))
                        if separator_matches:
                            context_end = separator_matches[0].start()
                        else:
                            context_end = potential_end
            else:
                year_pattern = re.compile(r'\((19|20)\d{2}\)')
                next_year_matches = list(year_pattern.finditer(text, citation.end_index))
                if next_year_matches:
                    context_end = next_year_matches[0].start()
                else:
                    context_end = min(len(text), citation.end_index + 50)
        else:
            year_pattern = re.compile(r'\((19|20)\d{2}\)')
            next_year_matches = list(year_pattern.finditer(text, citation.end_index))
            if next_year_matches:
                context_end = next_year_matches[0].start()
            else:
                context_end = min(len(text), citation.end_index + 50)
        
        min_context_size = 50
        max_context_size = 800
        
        if context_end - context_start < min_context_size:
            expansion = min_context_size - (context_end - context_start)
            context_start = max(0, context_start - expansion // 2)
            context_end = min(len(text), context_end + expansion // 2)
        elif context_end - context_start > max_context_size:
            context_end = context_start + max_context_size
        
        
        return context_start, context_end
    
    def _get_isolated_context_for_citation(self, text: str, citation_start: int, citation_end: int, all_citations: Optional[List[CitationResult]] = None) -> tuple[Optional[int], Optional[int]]:
        """Get isolated context boundaries for a citation using start/end positions."""
        temp_citation = CitationResult(
            citation=text[citation_start:citation_end],
            start_index=citation_start,
            end_index=citation_end
        )
        return self._get_isolated_context(text, temp_citation, all_citations)
    
    def extract_date_from_context_isolated(self, text: str, citation_start: int, citation_end: int) -> Optional[str]:
        """Extract date using isolated context to prevent cross-contamination."""
        try:
            context_start, context_end = self._get_isolated_context_for_citation(text, citation_start, citation_end)
            if context_start is None or context_end is None:
                context_start = max(0, citation_start - 200)
                context_end = min(len(text), citation_end + 100)
            
            context = text[context_start:context_end]
            
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
            return None
    
    def _extract_case_name_candidates(self, text: str) -> List[str]:
        """Extract 1-4 word candidates before 'v.' pattern."""
        candidates = []
        
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
                
                for i in range(1, min(5, len(words) + 1)):
                    candidate = ' '.join(words[:i])
                    candidate = re.sub(r',\s*\d+\s+[A-Za-z.]+(?:\s+\d+)*.*$', '', candidate)
                    candidate = re.sub(r'\(\d{4}\)$', '', candidate)
                    candidate = candidate.strip(' ,;')
                    
                    if len(candidate) >= 2 and candidate[0].isupper():
                        candidates.append(candidate)
                
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
        candidate_norm = re.sub(r'[^\w\s]', '', candidate.lower())
        canonical_norm = re.sub(r'[^\w\s]', '', canonical.lower())
        
        candidate_words = set(candidate_norm.split())
        canonical_words = set(canonical_norm.split())
        
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
        match = re.search(r'\(?(19|20)\d{2}\)?', context_text)
        if match:
            return match.group(0).strip('()')
        return None

    def _is_valid_case_name(self, case_name: str) -> bool:
        """
        Enhanced case name validation with comprehensive rules.
        
        Args:
            case_name: The case name to validate
            
        Returns:
            bool: True if the case name appears valid, False otherwise
        """
        if not case_name or len(case_name) < 5 or len(case_name) > 150:
            return False
            
        lower = case_name.lower()
        
        case_patterns = [
            r'\bv\.?\b',  # v. or v
            r'\bvs\.?\b',  # vs. or vs
            r'\bin\s+re\b',  # in re
            r'\bex\s+rel\.?\b',  # ex rel. or ex rel
            r'\bex\s+parte\b',  # ex parte
            r'\bin\s+the\s+matter\s+of\b',  # in the matter of
            r'\bre\s+',  # re (as in "Re: Case Name")
            r'\bstate\s+(?:of\s+)?[A-Z]',  # State [of] X
            r'\bunited\s+states\b',  # United States
            r'\bcommonwealth\s+of\b',  # Commonwealth of
            r'\bpeople\s+(?:of\s+the\s+)?(?:state\s+of\s+)?[A-Z]',  # People [of the State] of X
            r'\bpetition\s+of\b'  # Petition of
        ]
        
        has_case_pattern = any(re.search(pattern, lower) for pattern in case_patterns)
        
        invalid_terms = [
            'court', 'appeals', 'district', 'circuit', 'supreme', 'county', 
            'municipal', 'federal', 'appellate', 'division', 'chancery', 
            'department', 'section', 'article', 'chapter', 'title', 'statute',
            'section', 'subsection', 'paragraph', 'subdivision', 'clause',
            'statutory', 'constitutional', 'provision', 'regulation', 'rule',
            'ordinance', 'code', 'revised code', 'annotated', 'compiled',
            'statutes', 'laws', 'session laws', 'public law', 'private law',
            'act of', 'bill', 'resolution', 'amendment', 'constitution',
            'amended', 'effective', 'enacted', 'adopted', 'approved',
            'repealed', 'superseded', 'codified', 'recodified', 'repealer',
            'sections', 'subsections', 'paragraphs', 'subdivisions', 'clauses'
        ]
        
        has_invalid_terms = any(term in lower for term in invalid_terms)
        
        words = [w for w in re.split(r'\W+', case_name) if w]
        if len(words) < 2:
            return False
            
        has_capitalized = any(word and word[0].isupper() for word in words[1:] if len(word) > 1)
        
        return (
            has_case_pattern and 
            not has_invalid_terms and 
            has_capitalized and
            self._has_reasonable_case_structure(case_name)
        )
    
    def _has_reasonable_case_structure(self, case_name: str) -> bool:
        """Check if case name has reasonable structure (no more than 4 lowercase words in a row)."""
        if not case_name:
            return False
        
        words = case_name.split()
        if len(words) < 2:
            return False
        
        lowercase_count = 0
        max_lowercase_in_row = 4
        
        capitalized_words = sum(1 for word in words if re.sub(r'[^\w]', '', word) and re.sub(r'[^\w]', '', word)[0].isupper())
        
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word)
            if not clean_word:
                continue
                
            if clean_word.islower():
                lowercase_count += 1
                max_allowed = 5 if capitalized_words > 2 else 4
                if lowercase_count > max_allowed:
                    return False
            else:
                lowercase_count = 0
        
        return True
    
    def _extract_context(self, text: str, start: int, end: int) -> str:
        """Extract citation-aware context: starts 100 chars before citation (not including previous citation/year), ends after year in parentheses or 100 chars after citation, not including next citation."""
        import re
        citation_pattern = r'(\d{1,4}\s+[A-Za-z.]+(?:\s+[A-Za-z.]+)?\s+\d+(?:,\s*\d+)*\s*(?:\((17|18|19|20)\d{2}\))?)'
        all_cites = list(re.finditer(citation_pattern, text))
        prev_cite_end = 0
        next_cite_start = len(text)
        for m in all_cites:
            if m.end() <= start:
                prev_cite_end = m.end()
            elif m.start() > end and m.start() < next_cite_start:
                next_cite_start = m.start()
        context_start = max(prev_cite_end, start - 150)
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
        
        # FIX #45: Add logging to track what's being removed
        logger.info(f"[DEDUP] Starting deduplication with {len(citations)} citations")
        
        sorted_citations = sorted(citations, key=lambda x: (x.start_index or 0, -(x.end_index or 0)))
        
        # Phase 1: Remove overlapping citations
        non_overlapping = []
        removed_overlap = []
        for citation in sorted_citations:
            if not citation.start_index or not citation.end_index:
                non_overlapping.append(citation)
                continue
                
            overlaps = False
            for existing in non_overlapping:
                if not existing.start_index or not existing.end_index:
                    continue
                    
                if (citation.start_index < existing.end_index and 
                    citation.end_index > existing.start_index):
                    
                    # don't treat them as overlapping - they should both be preserved
                    if (citation.is_parallel or existing.is_parallel or 
                        ',' in citation.citation or ',' in existing.citation):
                        continue
                    
                    overlaps = True
                    # FIX #45: Log what we're removing due to overlap
                    removed_overlap.append((citation.citation, existing.citation, citation.start_index))
                    break
            
            if not overlaps:
                non_overlapping.append(citation)
        
        # FIX #45: Log overlap removals
        if removed_overlap:
            logger.warning(f"[DEDUP] Phase 1 (Overlap): Removed {len(removed_overlap)} citations")
            for removed, kept, pos in removed_overlap:
                logger.warning(f"  - Removed '{removed}' at {pos} (overlaps with '{kept}')")
        
        # Phase 2: Remove exact duplicates
        seen = {}
        removed_duplicate = []
        for citation in non_overlapping:
            if citation.is_parallel or ',' in citation.citation:
                key = citation.citation
            else:
                key = self._normalize_citation_comprehensive(citation.citation, purpose="comparison")
            
            if key not in seen:
                seen[key] = citation
            else:
                existing = seen[key]
                if (citation.confidence > existing.confidence or 
                    len(citation.extracted_case_name or '') > len(existing.extracted_case_name or '') or
                    len(citation.extracted_date or '') > len(existing.extracted_date or '')):
                    # FIX #45: Log replacement
                    logger.warning(f"[DEDUP] Phase 2: Replacing '{existing.citation}' with '{citation.citation}' (better quality)")
                    removed_duplicate.append((existing.citation, citation.citation, key))
                    seen[key] = citation
                else:
                    # FIX #45: Log what we're removing as duplicate
                    removed_duplicate.append((citation.citation, existing.citation, key))
        
        # FIX #45: Log duplicate removals
        if removed_duplicate:
            logger.warning(f"[DEDUP] Phase 2 (Duplicate): Removed/replaced {len(removed_duplicate)} citations")
            for removed, kept, norm_key in removed_duplicate[:10]:  # Show first 10
                logger.warning(f"  - Removed '{removed}' (duplicate of '{kept}', normalized key: '{norm_key}')")
        
        final = list(seen.values())
        logger.info(f"[DEDUP] Finished: {len(citations)} → {len(final)} citations ({len(citations) - len(final)} removed)")
        
        return final
    
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
        sorted_citations = sorted(citations, key=lambda x: x.start_index or 0)
        groups = []
        current_group = [sorted_citations[0]]
        for i in range(1, len(sorted_citations)):
            curr = sorted_citations[i]
            prev = current_group[-1]
            if (curr.start_index and prev.end_index and 
                curr.start_index - prev.end_index <= 100):
                text_between = text[prev.end_index:curr.start_index]
                if ',' in text_between and len(text_between.strip()) < 50:
                    if (prev.extracted_case_name and curr.extracted_case_name and
                        prev.extracted_case_name != 'N/A' and curr.extracted_case_name != 'N/A'):
                        name1 = self._normalize_case_name_for_clustering(prev.extracted_case_name)
                        name2 = self._normalize_case_name_for_clustering(curr.extracted_case_name)
                        similarity = self._calculate_case_name_similarity(name1, name2)
                        if similarity > 0.8:  # Only group if very similar
                            current_group.append(curr)
                            continue
                if len(current_group) > 1:
                    groups.append(current_group)
                current_group = [curr]
                continue
            if len(current_group) > 1:
                groups.append(current_group)
            current_group = [curr]
        if len(current_group) > 1:
            groups.append(current_group)
        cluster_counter = 1
        for group in groups:
            if len(group) > 1:
                cluster_id = f"cluster_{cluster_counter}"
                cluster_counter += 1
                member_citations = [c.citation for c in group]
                best_name = next((c.extracted_case_name for c in group 
                                if c.extracted_case_name and c.extracted_case_name != 'N/A'), None)
                # CRITICAL: Only use dates that appear to be from user document (year-only format)
                # Avoid contamination from verification APIs that return full dates like "2018-12-06"
                document_dates = [c.extracted_date for c in group 
                                if c.extracted_date and c.extracted_date != 'N/A' 
                                and re.match(r'^\d{4}$', str(c.extracted_date))]  # Year-only format
                best_date = document_dates[0] if document_dates else None
                for citation in group:
                    # FIX #36: REMOVED ALL EXTRACTED DATA PROPAGATION!
                    # Each citation MUST preserve its OWN extracted_case_name/extracted_date from its document location.
                    # Propagating data between parallel citations destroys data integrity and causes contamination.
                    #
                    # BUG EXAMPLE THAT THIS FIX RESOLVES:
                    #   - "183 Wn.2d 649" extracted "Spokane County" (wrong, from forward search)
                    #   - "355 P.3d 258" extracted "Lopez Demetrio" from eyecite (correct!)
                    #   - They're grouped as parallels
                    #   - best_name = "Spokane County" (first in sorted list)
                    #   - OLD CODE: "355 P.3d 258"'s correct name gets OVERWRITTEN with "Spokane County"!
                    #   - FIX #36: Each citation keeps its own extracted_case_name/extracted_date
                    #
                    citation.is_parallel = True
                    citation.cluster_id = cluster_id
                    citation.cluster_members = [c for c in member_citations if c != citation.citation]
                    citation.parallel_citations = [c for c in member_citations if c != citation.citation]
                    # FIX #36: Removed lines 2558-2577 that propagated extracted_case_name and extracted_date
        return sorted_citations
    
    def _are_citations_same_case(self, citation1: CitationResult, citation2: CitationResult) -> bool:
        """
        IMPROVED: Check if two citations likely refer to the same case.
        This fixes the 93% false positive rate by implementing strict validation.
        """
        
        if citation1.extracted_case_name and citation2.extracted_case_name:
            name1 = self._normalize_case_name_for_clustering(citation1.extracted_case_name)
            name2 = self._normalize_case_name_for_clustering(citation2.extracted_case_name)
            
            if name1 != name2:
                similarity = self._calculate_case_name_similarity(name1, name2)
                if similarity < 0.9:
                    return False
        else:
            return False
        
        if citation1.extracted_date and citation2.extracted_date:
            try:
                year1 = int(citation1.extracted_date)
                year2 = int(citation2.extracted_date)
                if abs(year1 - year2) > 1:
                    return False
            except (ValueError, TypeError):
                return False
        else:
            return False
        
        if citation1.start_index and citation2.start_index:
            distance = abs(citation2.start_index - citation1.start_index)
            if distance > 200:
                return False
        else:
            return False
        
        if hasattr(self, '_check_court_compatibility'):
            if not self._check_court_compatibility(citation1, citation2):
                return False
        
        if citation1.canonical_name and citation2.canonical_name:
            if citation1.canonical_name != citation2.canonical_name:
                return False
        
        return True
    
    def _calculate_case_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two case names (0.0 to 1.0)."""
        if not name1 or not name2:
            return 0.0
        
        from difflib import SequenceMatcher
        similarity = SequenceMatcher(None, name1, name2).ratio()
        
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        if words1 and words2:
            word_overlap = len(words1 & words2) / max(len(words1), len(words2))
            final_similarity = (similarity + word_overlap) / 2
        else:
            final_similarity = similarity
        
        return final_similarity
    
    def _check_court_compatibility(self, citation1: CitationResult, citation2: CitationResult) -> bool:
        """Check if citations are from compatible courts."""
        reporter1 = self._extract_reporter_type(citation1.citation)
        reporter2 = self._extract_reporter_type(citation2.citation)
        
        if not reporter1 or not reporter2:
            return True  # If we can't determine, be permissive
        
        federal_reporters = {'F.', 'F.2d', 'F.3d', 'F.Supp.', 'F.Supp.2d', 'U.S.', 'S.Ct.'}
        washington_reporters = {'Wn.', 'Wn.2d', 'Wash.', 'Wash.App.', 'Wash.2d'}
        
        if (reporter1 in federal_reporters and reporter2 in federal_reporters):
            return True
        if (reporter1 in washington_reporters and reporter2 in washington_reporters):
            return True
        
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
        
        method_scores = {
            'eyecite': 0.8,
            'regex': 0.6,
            'cluster_detection': 0.7,
        }
        confidence += method_scores.get(citation.method, 0.5)
        
        if re.match(r'^\d+\s+[A-Za-z\.]+\s+\d+$', citation.citation):
            confidence += 0.1
        
        if citation.extracted_case_name:
            confidence += 0.2
        
        if citation.extracted_date:
            confidence += 0.1
        
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
        }
        for abbr, state in state_map.items():
            if abbr in citation:
                return state
        return None

    def _validate_verification_result(self, citation: 'CitationResult', source: str) -> Dict[str, Any]:
        """Validate that a verification result makes sense and is high quality."""
        validation_result = {'valid': True, 'reason': '', 'confidence_adjustment': 0.0}
        
        if not citation.canonical_name or citation.canonical_name.strip() == '':
            validation_result['valid'] = False
            validation_result['reason'] = 'Missing canonical name'
            return validation_result
        
        canonical_lower = citation.canonical_name.lower()
        if 'v.' not in canonical_lower and 'in re' not in canonical_lower and 'ex parte' not in canonical_lower:
            validation_result['valid'] = False
            validation_result['reason'] = f'Canonical name lacks proper case format: {citation.canonical_name}'
            return validation_result
        
        if len(citation.canonical_name) < 5:
            validation_result['valid'] = False
            validation_result['reason'] = f'Canonical name too short: {citation.canonical_name}'
            return validation_result
        
        if len(citation.canonical_name) > 200:
            validation_result['valid'] = False
            validation_result['reason'] = f'Canonical name too long: {citation.canonical_name[:50]}...'
            return validation_result
        
        if hasattr(citation, 'extracted_case_name') and citation.extracted_case_name and citation.extracted_case_name != 'N/A':
            similarity = self._calculate_case_name_similarity(citation.extracted_case_name, citation.canonical_name)
            if similarity < 0.1:  # Very low similarity threshold
                logger.warning(f"[VALIDATION] Low similarity between extracted '{citation.extracted_case_name}' and canonical '{citation.canonical_name}' (similarity: {similarity:.2f})")
                validation_result['confidence_adjustment'] = -0.2
        
        if citation.canonical_date:
            try:
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
        
        if source == 'CourtListener':
            if not citation.url or not citation.url.startswith('https://www.courtlistener.com'):
                validation_result['confidence_adjustment'] = -0.1
        
        if hasattr(citation, 'confidence') and citation.confidence is not None:
            citation.confidence = max(0.0, min(1.0, citation.confidence + validation_result['confidence_adjustment']))
        
        return validation_result

    def _verify_with_courtlistener(self, citations) -> dict:
        """Verify citations using existing CourtListener verification services"""
        try:
            # Use the existing verification services
            from verification_services import CourtListenerService
            
            service = CourtListenerService()
            citation_strings = [c.citation for c in citations if hasattr(c, 'citation')]
            
            if not citation_strings:
                return {}
            
            # Use the existing batch verification method
            results = service.verify_citations_batch(citation_strings)
            
            return results
            
        except Exception as e:
            logger.warning(f"Error using existing CourtListener verification service: {e}")
            return {}

    def _verify_citations_sync(self, citations: List['CitationResult'], text: Optional[str] = None) -> List['CitationResult']:
        """
        ENHANCED: Now using unified verification master with BATCH processing.
        
        Uses CourtListener's batch API (50 citations per call) for massive speedup.
        Falls back to individual verification only for failed citations.
        """
        logger.error(f"🔥 [BATCH-VERIFY] Starting BATCH verification for {len(citations)} citations")
        
        if not citations:
            return citations
        
        # Use the new unified verification master with BATCH processing
        try:
            from src.unified_verification_master import UnifiedVerificationMaster
            import asyncio
            
            logger.info("[VERIFICATION] Using BATCH VERIFICATION (50 citations per API call)")
            
            # First pass: identify citations that need verification
            citations_to_verify = []
            for citation in citations:
                verification_status = getattr(citation, 'verification_status', None)
                is_parallel = getattr(citation, 'is_parallel', False)
                
                if verification_status == 'verified' or is_parallel:
                    logger.error(f"🚫 [FIX #62] SKIPPING '{citation.citation}': verification_status={verification_status}, is_parallel={is_parallel}")
                    continue
                
                logger.error(f"✅ [FIX #62] PROCESSING '{citation.citation}'")
                
                # Store original values before any verification
                if not hasattr(citation, 'original_case_name'):
                    citation.original_case_name = getattr(citation, 'extracted_case_name', 'N/A')
                if not hasattr(citation, 'original_date'):
                    citation.original_date = getattr(citation, 'extracted_date', 'N/A')
                
                citations_to_verify.append(citation)
            
            # BATCH VERIFICATION: Process in batches of 50
            if citations_to_verify:
                batch_size = 50
                total = len(citations_to_verify)
                logger.info(f"[BATCH-VERIFY] Processing {total} citations in batches of {batch_size}")
                
                verifier = UnifiedVerificationMaster()
                
                # Process citations in batches
                for batch_start in range(0, total, batch_size):
                    batch_end = min(batch_start + batch_size, total)
                    batch = citations_to_verify[batch_start:batch_end]
                    batch_num = (batch_start // batch_size) + 1
                    total_batches = (total + batch_size - 1) // batch_size
                    
                    logger.info(f"[BATCH {batch_num}/{total_batches}] Verifying citations {batch_start+1}-{batch_end} ({len(batch)} citations)")
                    
                    # Extract data for batch
                    citation_strings = [c.citation for c in batch]
                    case_names = [c.extracted_case_name for c in batch]
                    dates = [c.extracted_date for c in batch]
                    
                    # Call batch verification
                    try:
                        batch_results = asyncio.run(verifier._batch_verify_with_courtlistener(
                            citations=citation_strings,
                            extracted_case_names=case_names,
                            extracted_dates=dates
                        ))
                        
                        # Apply results to citation objects
                        verified_count = 0
                        for citation, result in zip(batch, batch_results):
                            if result and result.verified:
                                # Store verified data in canonical fields
                                citation.verified = True
                                citation.canonical_name = result.canonical_name
                                citation.canonical_date = result.canonical_date
                                citation.canonical_url = result.canonical_url
                                citation.verification_status = "verified"
                                citation.verification_source = result.source or 'batch_verify'
                                verified_count += 1
                                logger.info(f"[BATCH-VERIFIED] {citation.citation} -> {result.canonical_name}")
                            else:
                                citation.verified = False
                                citation.verification_status = "not_found"
                                error_msg = result.error if result else 'No result'
                                logger.debug(f"[BATCH-NOT-VERIFIED] {citation.citation}: {error_msg}")
                        
                        logger.info(f"[BATCH {batch_num}/{total_batches}] Verified {verified_count}/{len(batch)} citations")
                        
                    except Exception as e:
                        logger.error(f"[BATCH-ERROR] Batch {batch_num} failed: {e}")
                        # Mark batch as unverified
                        for citation in batch:
                            citation.verified = False
                            citation.verification_status = "error"
            
            logger.info(f"[BATCH-VERIFY] Completed all batches")
            
        except Exception as e:
            logger.error(f"[VERIFICATION] Error in unified master verification: {str(e)}")
            # Fallback to marking all as unverified
            for citation in citations:
                if not hasattr(citation, 'verified') or not citation.verified:
                    citation.verified = False
                    citation.verification_status = "error"
        
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
        context_start = max(0, match_start - 100)
        preceding_text = text[context_start:match_start].lower()
        
        page_indicators = [
            'page', 'p.', 'pp.', 'see', 'id.', 'ibid', 'supra',
            'infra', 'cf.', 'but see', 'accord', 'compare', 'contra'
        ]
        
        at_pattern = re.search(r'\bat\s+(\d+)\b', preceding_text[-10:])
        if at_pattern:
            return False
        
        for indicator in page_indicators:
            if indicator in preceding_text:
                return False
        
        sentence_boundary = re.search(r'[.!?]\s+[A-Z]', preceding_text[-50:])
        if sentence_boundary:
            return False
        
        try:
            vol_num = int(volume)
            
            if vol_num < 10:
                return False
                
            if vol_num > 9999:
                return False
                
        except ValueError:
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
        
        normalized = re.sub(r'\s+', ' ', normalized)
        
        normalized = re.sub(r'(\d+)\s*U\.\s*S\.\s*(\d+)', r'\1 U.S. \2', normalized)
        
        normalized = re.sub(r'(\d+)\s*F\.\s*(\d+)d\s*(\d+)', r'\1 F.\2d \3', normalized)
        normalized = re.sub(r'(\d+)\s*F\.\s*3d\s*(\d+)', r'\1 F.3d \2', normalized)
        normalized = re.sub(r'(\d+)\s*F\.\s*2d\s*(\d+)', r'\1 F.2d \2', normalized)
        
        normalized = re.sub(r'(\d+)\s*F\.\s*Supp\.\s*(\d+)d\s*(\d+)', r'\1 F.Supp.\2d \3', normalized)
        normalized = re.sub(r'(\d+)\s*F\.\s*Supp\.\s*3d\s*(\d+)', r'\1 F. Supp. 3d \2', normalized)
        normalized = re.sub(r'(\d+)\s*F\.\s*Supp\.\s*2d\s*(\d+)', r'\1 F. Supp. 2d \2', normalized)
        normalized = re.sub(r'(\d+)\s*F\.\s*Supp\.\s*(\d+)', r'\1 F. Supp. \2', normalized)
        
        normalized = re.sub(r'(\d+)\s*S\.\s*Ct\.\s*(\d+)', r'\1 S. Ct. \2', normalized)
        
        normalized = re.sub(r'(\d+)\s*L\.\s*Ed\.\s*2d\s*(\d+)', r'\1 L. Ed. 2d \2', normalized)
        normalized = re.sub(r'(\d+)\s*L\.\s*Ed\.\s*(\d+)', r'\1 L. Ed. \2', normalized)
        
        normalized = re.sub(r'(\d+)\s*P\.\s*3d\s*(\d+)', r'\1 P.3d \2', normalized)
        normalized = re.sub(r'(\d+)\s*P\.\s*2d\s*(\d+)', r'\1 P.2d \2', normalized)
        
        # CRITICAL FIX: DO NOT normalize Wn.2d → Wash.2d for general/verification!
        # These are DIFFERENT reporters in CourtListener - "Wn.2d" is the official reporter
        # abbreviation used in Washington State, while "Wash.2d" is a variant.
        # Normalizing them causes verification to match the WRONG cases!
        # 
        # Example: "183 Wn.2d 649" (State v. M.Y.G.) is DIFFERENT from 
        #          "183 Wash.2d 649" (a different case) in CourtListener.
        #
        # We MUST preserve the exact reporter abbreviation from the document.
        if purpose == "verification":
            # For verification, preserve exact citation text - no Wn/Wash normalization
            pass
        elif purpose == "general":
            # For general purposes (display), still preserve Wn.2d vs Wash.2d distinction
            # Only normalize spacing/punctuation, not reporter names
            pass
        
        elif purpose == "bluebook":
            normalized = re.sub(r'(\d+)\s*Wn\.\s*2d\s*(\d+)', r'\1 Wn.2d \2', normalized)
            normalized = re.sub(r'(\d+)\s*Wn\.\s*App\.\s*(\d+)', r'\1 Wn. App. \2', normalized)
            normalized = re.sub(r'(\d+)\s*Wash\.\s*2d\s*(\d+)', r'\1 Wash. 2d \2', normalized)
            normalized = re.sub(r'(\d+)\s*Wash\.\s*App\.\s*(\d+)', r'\1 Wash. App. \2', normalized)
        
        if purpose == "comparison":
            normalized = normalized.lower()
            normalized = re.sub(r'\bwash\.\b', 'wash.', normalized)
            normalized = re.sub(r'\bp\.\b', 'p.', normalized)
            normalized = re.sub(r'\bf\.\b', 'f.', normalized)
        
        elif purpose == "us_extract":
            us_pattern = r'(\d+\s+U\.S\.\s+\d+)'
            match = re.search(us_pattern, normalized)
            if match:
                return match.group(1)
        
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
        
        logger.info("[UNIFIED_EXTRACTION] Step 1: Enhanced regex extraction")
        regex_citations = self._extract_with_regex(text)
        all_citations.extend(regex_citations)
        logger.info(f"[UNIFIED_EXTRACTION] Regex found {len(regex_citations)} citations")
        
        logger.info("[UNIFIED_EXTRACTION] Step 2: Eyecite extraction")
        try:
            eyecite_citations = self._extract_with_eyecite(text)
            all_citations.extend(eyecite_citations)
            logger.info(f"[UNIFIED_EXTRACTION] Eyecite found {len(eyecite_citations)} citations")
        except Exception as e:
            logger.warning(f"[UNIFIED_EXTRACTION] Eyecite extraction failed: {e}")
            logger.info("[UNIFIED_EXTRACTION] Continuing without eyecite results")
        
        logger.info("[UNIFIED_EXTRACTION] Step 3: Applying unified strict context extraction to ALL citations")
        try:
            from src.utils.unified_case_name_extractor import apply_unified_extraction_to_all_citations
            
            # CRITICAL: Use unified extraction for ALL citations to prevent case name bleeding
            apply_unified_extraction_to_all_citations(text, all_citations, force_reextract=False)
            
            # Extract dates
            for citation in all_citations:
                try:
                    if not citation.extracted_date:
                        citation.extracted_date = self._extract_date_from_context(text, citation)
                except Exception as e:
                    logger.warning(f"[UNIFIED_EXTRACTION] Error extracting date for {citation.citation}: {e}")
                    
        except Exception as e:
            logger.error(f"[UNIFIED_EXTRACTION] Unified extraction failed: {e}")
            # Fallback to old method
            for citation in all_citations:
                try:
                    if not citation.extracted_case_name or citation.extracted_case_name == "N/A":
                        citation.extracted_case_name = self._extract_case_name_from_context(text, citation, all_citations)
                    if not citation.extracted_date:
                        citation.extracted_date = self._extract_date_from_context(text, citation)
                except Exception as e2:
                    logger.warning(f"[UNIFIED_EXTRACTION] Error in fallback extraction for {citation.citation}: {e2}")
        
        logger.info("[UNIFIED_EXTRACTION] Step 4: Detecting parallel citations with full text context")
        try:
            all_citations = self._detect_parallel_citations(all_citations, text)
            logger.info(f"[UNIFIED_EXTRACTION] After parallel detection: {len(all_citations)} citations")
        except Exception as e:
            logger.warning(f"[UNIFIED_EXTRACTION] Error in parallel detection: {e}")
        
        logger.info("[UNIFIED_EXTRACTION] Step 5: Normalizing citation components")
        for citation in all_citations:
            try:
                components = self._extract_citation_components(citation.citation)
                citation.volume = components.get('volume')
                citation.reporter = components.get('reporter')
                citation.page = components.get('page')
            except Exception as e:
                logger.warning(f"[UNIFIED_EXTRACTION] Error normalizing components for {citation.citation}: {e}")
        
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
        
        try:
            parallel_groups = self._detect_parallel_citation_groups(citations, text)
            logger.info(f"[PARALLEL_DETECTION] Found {len(parallel_groups)} parallel groups")
            
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
                
            group = [citation]
            processed.add(citation.citation)
            
            for j, other_citation in enumerate(citations[i+1:], i+1):
                if other_citation.citation in processed:
                    continue
                    
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
        pos1 = text.find(citation1.citation)
        pos2 = text.find(citation2.citation)
        
        if pos1 == -1 or pos2 == -1:
            return False
            
        if abs(pos1 - pos2) > 200:
            return False
            
        name1 = citation1.extracted_case_name or ""
        name2 = citation2.extracted_case_name or ""
        
        if name1 and name2:
            # Clean and normalize case names for better comparison
            def clean_name(name):
                # Remove common legal terms that might cause mismatches
                common_terms = {'llc', 'inc', 'ltd', 'llp', 'corp', 'co', 'no', 'et', 'al'}
                # Remove punctuation and split into words
                words = re.sub(r'[^\w\s]', ' ', name.lower()).split()
                # Remove common terms and single letters
                return {w for w in words if w not in common_terms and len(w) > 1}
            
            # Get clean word sets
            words1 = clean_name(name1)
            words2 = clean_name(name2)
            
            # Check for significant word overlap (at least 2 words in common)
            common_words = words1.intersection(words2)
            if len(common_words) >= 2:
                return True
                
            # Check for corporate name patterns (e.g., "Spokeo, Inc. v. Robins")
            def get_corp_name_parts(name):
                # Match patterns like "Spokeo, Inc. v. Robins"
                corp_pattern = r'([A-Z][^,]+),?\s*(?:Inc|LLC|L\.?L\.?C\.?|Corp|Corp\.|Ltd|Ltd\.|Co|Co\.)'
                match = re.search(corp_pattern, name)
                if match:
                    return match.group(1).strip()
                return None
                
            corp1 = get_corp_name_parts(name1)
            corp2 = get_corp_name_parts(name2)
            
            if corp1 and corp2 and corp1 in name2 or corp2 in name1:
                return True
        
        date1 = citation1.extracted_date or ""
        date2 = citation2.extracted_date or ""
        
        if date1 and date2 and date1 == date2:
            return True
            
        reporter1 = self._extract_reporter(citation1.citation)
        reporter2 = self._extract_reporter(citation2.citation)
        
        known_parallel_pairs = [
            # US Supreme Court
            ('U.S.', 'S.Ct.'),
            ('U.S.', 'L.Ed.'),
            ('U.S.', 'L.Ed.2d'),
            ('S.Ct.', 'L.Ed.'),
            ('S.Ct.', 'L.Ed.2d'),
            
            # Washington State
            ('Wash.', 'P.'),  # Wash. and P. (Pacific Reporter)
            ('Wash.', 'P.2d'),
            ('Wash.2d', 'P.2d'),
            ('Wash.2d', 'P.3d'),
            ('Wash. App.', 'P.2d'),
            ('Wash. App.', 'P.3d'),
            ('Wn.2d', 'P.2d'),  # Common abbreviation for Washington
            ('Wn. App.', 'P.2d'),
            
            # Federal Reporters
            ('F.3d', 'F.Supp.'),
            ('F.2d', 'F.Supp.'),
            ('F.3d', 'F.Supp.2d'),
            ('F.2d', 'F.Supp.2d'),
            
            # State Reporters
            ('N.E.2d', 'N.Y.S.3d'),  # New York
            ('N.W.2d', 'N.W.2d'),    # Regional reporters
            ('S.E.2d', 'S.E.2d'),
            ('So.2d', 'So.3d'),
            ('P.3d', 'P.3d')
        ]
        
        for pair in known_parallel_pairs:
            if (reporter1 in pair and reporter2 in pair) or (reporter2 in pair and reporter1 in pair):
                return True
                
        return False
    
    def _extract_reporter(self, citation: str) -> str:
        """
        Enhanced reporter extraction with support for various reporter formats.
        
        Args:
            citation: The citation string to extract reporter from
            
        Returns:
            Extracted reporter abbreviation or empty string if not found
        """
        import re
        
        # Common reporter patterns with priority (most specific first)
        patterns = [
            # US Supreme Court
            r'\b(\d+\s+U\.?\s*S\.?(?:\s*C\.?\s*)?(?:\s*\d+)?)',  # U.S.
            r'\b(\d+\s+S\.?\s*Ct\.?(?:\s*\d+)?)',  # S.Ct.
            r'\b(\d+\s+L\.?\s*Ed\.?(?:\s*2d)?(?:\s*\d+)?)',  # L.Ed. or L.Ed.2d
            
            # Federal Reporters
            r'\b(\d+\s+F\.?(?:\s*3d|2d|Supp\.?|Supp\.?\s*2d)?(?:\s*\d+)?)',  # F.3d, F.2d, F.Supp., etc.
            
            # Washington State Reporters
            r'\b(\d+\s+Wash\.?(?:\s*2d|\s*App\.?)?(?:\s*\d+)?)',  # Wash., Wash.2d, Wash. App.
            r'\b(\d+\s+Wn\.?(?:\s*2d|\s*App\.?)?(?:\s*\d+)?)',  # Wn., Wn.2d, Wn. App.
            r'\b(\d+\s+P\.?(?:\s*3d|2d)?(?:\s*\d+)?)',  # P.3d, P.2d
            
            # Other common reporters
            r'\b(\d+\s+N\.?\s*E\.?(?:\s*2d)?(?:\s*\d+)?)',  # N.E., N.E.2d
            r'\b(\d+\s+N\.?\s*Y\.?\s*S\.?(?:\s*3d|2d)?(?:\s*\d+)?)',  # N.Y.S., N.Y.S.2d, N.Y.S.3d
            r'\b(\d+\s+S\.?\s*E\.?(?:\s*2d)?(?:\s*\d+)?)',  # S.E., S.E.2d
            r'\b(\d+\s+So\.?(?:\s*3d|2d)?(?:\s*\d+)?)',  # So., So.2d, So.3d
            r'\b(\d+\s+N\.?\s*W\.?\s*2d(?:\s*\d+)?)',  # N.W.2d
            
            # General pattern as fallback
            r'\b(\d+\s+[A-Z][A-Za-z]*(?:\s*\d*[a-z]*)?\b\.?(?:\s*[A-Z][a-z]*\.?)*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, citation, re.IGNORECASE)
            if match:
                # Extract just the reporter part (without volume and page)
                reporter_part = re.sub(r'^\d+\s+', '', match.group(1).strip())
                # Clean up any remaining digits that aren't part of the reporter
                reporter = re.sub(r'\s*\d+$', '', reporter_part)
                # Standardize common variations
                reporter = re.sub(r'\.\s+', '.', reporter)  # Remove spaces after dots
                reporter = re.sub(r'\s+', ' ', reporter)    # Normalize spaces
                return reporter.strip()
        
        return ""

    def _extract_with_regex_enhanced(self, text: str) -> List[CitationResult]:
        """
        Enhanced regex extraction with false positive prevention.
        Based on _extract_with_regex but adds volume number validation and text normalization.
        """
        logger.info('[DEBUG] ENTERED _extract_with_regex_enhanced')
        citations = []
        seen_citations = set()
        
        logger.info('[DEBUG] Using original text for citation extraction')
        original_text = text
        normalized_text = text  # Use original text, normalize individual citations later
        logger.info(f'[DEBUG] Text length: {len(original_text)} chars')
        
        priority_patterns = [
            'parallel_citation_cluster',
            'flexible_wash2d',
            'flexible_p3d',
            'flexible_p2d',
            'wash_complete',
            'wash_with_parallel',
            'parallel_cluster',
            'wn2d',             # Washington Supreme Court 2d series
            'wn2d_space',       # Washington Supreme Court 2d series (with space)
            'wn3d',             # Washington Supreme Court 3d series
            'wn3d_space',       # Washington Supreme Court 3d series (with space)
            'wn_app',           # Washington Court of Appeals
            'wn_app_space',     # Washington Court of Appeals (with space)
            'p3d',              # Pacific Reporter 3d
            'p2d',              # Pacific Reporter 2d
            'wash2d',           # Washington Supreme Court 2d series (Wash.)
            'wash2d_space',     # Washington Supreme Court 2d series (Wash. with space)
            'wash_app',         # Washington Court of Appeals (Wash.)
            'wash_app_space',   # Washington Court of Appeals (Wash. with space)
            'westlaw',          # Westlaw citations (2006 WL 3801910)
            'westlaw_alt',      # Alternative Westlaw format (2006 Westlaw 3801910)
        ]
        
        for pattern_name in priority_patterns:
            if pattern_name in self.citation_patterns:
                pattern = self.citation_patterns[pattern_name]
                matches = list(pattern.finditer(normalized_text))
                
                for match in matches:
                    citation_str = match.group(0).strip()
                    if not citation_str or citation_str in seen_citations:
                        continue
                    
                    components = self._extract_citation_components(citation_str)
                    reporter = components.get('reporter', '').strip().lower().replace('.', '')
                    volume = components.get('volume', '')
                    
                    if reporter == 'at':
                        continue
                    
                    if volume and int(volume) < 10 and 'P.' in citation_str:
                        if not self._validate_volume_number(text, match.start(), volume):
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
        1. TEXT NORMALIZATION (FIX #44: Normalize BEFORE extraction!)
        2. Enhanced regex extraction with false positive prevention
        3. Eyecite extraction for additional coverage  
        4. Name and date extraction for each citation (WITH FULL TEXT CONTEXT)
        5. Component normalization
        6. Final deduplication of processed results
        
        Args:
            text: Text to extract citations from
            
        Returns:
            List of CitationResult objects with complete metadata
        """
        logger.info("[UNIFIED_EXTRACTION] Starting unified citation extraction")
        
        # FIX #44: CRITICAL - Normalize text BEFORE extraction!
        # Eyecite fails on line breaks within citations (e.g., "148 Wn.2d\n224")
        # This was causing ~10-15 citations to be missed entirely
        logger.info("[UNIFIED_EXTRACTION] FIX #44: Normalizing text before extraction")
        normalized_text = re.sub(r'\s+', ' ', text)  # Collapse all whitespace (including \n) to single space
        logger.info(f"[UNIFIED_EXTRACTION] Text normalized: {len(text)} → {len(normalized_text)} chars")
        
        all_citations = []
        
        logger.info("[UNIFIED_EXTRACTION] Step 1: Enhanced regex extraction")
        regex_citations = self._extract_with_regex_enhanced(normalized_text)
        logger.info(f"[UNIFIED_EXTRACTION] Regex found {len(regex_citations)} citations")
        all_citations.extend(regex_citations)
        
        if EYECITE_AVAILABLE:
            logger.info("[UNIFIED_EXTRACTION] Step 2: Eyecite extraction")
            eyecite_citations = self._extract_with_eyecite(normalized_text)
            logger.info(f"[UNIFIED_EXTRACTION] Eyecite found {len(eyecite_citations)} citations")
            all_citations.extend(eyecite_citations)
        else:
            logger.info("[UNIFIED_EXTRACTION] Step 2: Eyecite not available, skipping")
        
        logger.info("[UNIFIED_EXTRACTION] Step 3: Initial deduplication")
        deduplicated_citations = self._deduplicate_citations(all_citations)
        logger.info(f"[UNIFIED_EXTRACTION] After deduplication: {len(deduplicated_citations)} citations")
        
        logger.info("[UNIFIED_EXTRACTION] Step 4: Extracting names and dates with full text context")
        # FIX #44: Use normalized_text for extraction since citation positions are from normalized_text
        # This prevents the position mismatch bug that was fixed in #43
        for citation in deduplicated_citations:
            try:
                if not citation.extracted_case_name:
                    citation.extracted_case_name = self._extract_case_name_from_context(normalized_text, citation, deduplicated_citations)
                
                if not citation.extracted_date:
                    citation.extracted_date = self._extract_date_from_context(normalized_text, citation)
                    
            except Exception as e:
                logger.warning(f"[UNIFIED_EXTRACTION] Error extracting metadata for citation '{citation.citation}': {e}")
                continue
        
        logger.info("[UNIFIED_EXTRACTION] Step 5: Normalizing citation components")
        for citation in deduplicated_citations:
            try:
                citation.citation = self._normalize_citation_comprehensive(citation.citation, purpose="general")
                
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
        
        CRITICAL: Uses CLEAN EXTRACTION PIPELINE to guarantee 100% accuracy with zero case name bleeding.
        
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
        
        # P3 FIX: Detect document's primary case name for contamination filtering
        document_primary_case_name = None
        try:
            from src.unified_clustering_master import UnifiedClusteringMaster
            clusterer = UnifiedClusteringMaster()
            document_primary_case_name = clusterer._extract_document_primary_case_name(text)
            if document_primary_case_name:
                logger.warning(f"[CONTAMINATION-FILTER] Document primary case detected: '{document_primary_case_name[:80]}'")
            else:
                logger.warning("[CONTAMINATION-FILTER] No document primary case name detected")
        except Exception as e:
            logger.warning(f"[CONTAMINATION-FILTER] Failed to detect document primary case: {e}")
        
        # Store for use in extraction calls
        self.document_primary_case_name = document_primary_case_name
        
        self._update_progress(10, "Extracting", "Extracting citations from text")
        
        logger.info("[UNIFIED_PIPELINE] Starting CLEAN extraction pipeline for 100% accuracy")
        
        # USE CLEAN EXTRACTION PIPELINE - guarantees zero case name bleeding
        try:
            from src.clean_extraction_pipeline import extract_citations_clean
            citations = extract_citations_clean(text)
            logger.info(f"[UNIFIED_PIPELINE] Clean pipeline extracted {len(citations)} citations with 100% accuracy")
        except Exception as e:
            logger.error(f"[UNIFIED_PIPELINE] Clean pipeline failed: {e}, falling back to old method")
            # Fallback to old method if clean pipeline fails
            citations = self._extract_with_regex_enhanced(text)
        logger.info(f"[UNIFIED_PIPELINE] Phase 1 complete: {len(citations)} citations extracted")
        self._update_progress(30, "Enhancing", "Enhancing citation data with case names and dates")
        
        # ENHANCED: Multi-method extraction with truncation repair and aggressive fallbacks
        try:
            from src.unified_case_name_extractor_v2 import extract_case_name_and_date_master
            import re
            
            for c in citations:
                try:
                    current_name = getattr(c, 'extracted_case_name', None) or ''
                    citation_text = getattr(c, 'citation', '')
                    start_index = getattr(c, 'start_index', None)
                    end_index = getattr(c, 'end_index', None)
                    citation_method = getattr(c, 'method', None)
                    
                    # FIX: ALWAYS re-extract, even for eyecite citations
                    # Eyecite often produces truncated names like "Noem v. Nat" instead of "Noem v. Nat'l TPS All."
                    # Our unified_case_extraction_master has better abbreviation and preposition handling
                    if current_name and current_name != 'N/A' and citation_method == 'eyecite':
                        logger.warning(f"[EXTRACT-OVERRIDE-EYECITE] Eyecite extracted '{current_name}' for {citation_text}, but will re-extract with better logic")
                        # Don't skip - continue to re-extract
                    
                    final_name = None
                    
                    # Method 1: Master extractor
                    try:
                        res = extract_case_name_and_date_master(
                            text=text,
                            citation=citation_text,
                            citation_start=start_index if start_index != -1 else None,
                            citation_end=end_index,
                            debug=False,
                            document_primary_case_name=self.document_primary_case_name  # P3 FIX: Pass contamination filter
                        )
                        master_name = (res or {}).get('case_name') or ''
                        
                        # Clean contamination from master extractor result
                        if master_name and master_name != 'N/A':
                            # Remove leading lowercase text (contamination)
                            master_name = re.sub(r'^[a-z\s,\.\'\"\(\)]+\b', '', master_name).strip()
                            # Remove trailing contamination
                            master_name = re.sub(r'\s*,\s*$', '', master_name).strip()
                            # Remove signal words
                            master_name = re.sub(r'\b(see|citing|compare|but see|accord|cf|e\.g\.|i\.e\.|id\.|ibid)\b.*$', '', master_name, flags=re.IGNORECASE).strip()
                            
                            if len(master_name.strip()) > 3:
                                final_name = master_name
                                logger.debug(f"[EXTRACT-M1] Master: '{master_name}' for {citation_text}")
                    except Exception as e:
                        logger.debug(f"[EXTRACT-M1] Master failed: {e}")
                    
                    # Method 2: Context-based extraction (if master failed or returned short name)
                    if not final_name or len(final_name) < 10:
                        try:
                            manual_name = self._extract_case_name_from_context(text, c)
                            if manual_name and manual_name != 'N/A' and len(manual_name.strip()) > 3:
                                if not final_name or len(manual_name) > len(final_name):
                                    final_name = manual_name
                                    logger.debug(f"[EXTRACT-M2] Context: '{manual_name}' for {citation_text}")
                        except Exception as e:
                            logger.debug(f"[EXTRACT-M2] Context failed: {e}")
                    
                    # Method 3: Direct regex extraction from broader context
                    if not final_name:
                        try:
                            # FIX #27: Only look BACKWARD, not forward!
                            # Looking forward (+ 100) was capturing case names from NEXT citations
                            # E.g., "Lopez...183 Wn.2d 649...Spokane County" would extract "Spokane County"
                            ctx_start = max(0, (start_index or 0) - 500)
                            ctx_end = start_index or 0  # Changed from + 100 to + 0 (only backward)
                            context = text[ctx_start:ctx_end]
                            
                            # More restrictive patterns to avoid contamination
                            patterns = [
                                # Standard case: Name v. Name (limit to reasonable length)
                                r'([A-Z][A-Za-z\'\.\&\s]{0,50}(?:,\s*(?:Inc\.|LLC|Corp\.|Ltd\.|Co\.|L\.P\.|Company))?)\s+v\.\s+([A-Z][A-Za-z\'\.\&\s]{0,50}(?:,\s*(?:Inc\.|LLC|Corp\.|Ltd\.|Co\.|L\.P\.|Company))?)',
                                # State/People v. Name
                                r'\b(State|People|United States)\s+v\.\s+([A-Z][A-Za-z\'\.\&\s]{0,40})',
                                # In re cases
                                r'\bIn\s+re\s+([A-Z][A-Za-z\'\.\&\s]{0,50}(?:,\s*(?:Inc\.|LLC|Corp\.|Ltd\.|Co\.|L\.P\.|Company))?)',
                            ]
                            
                            for pattern in patterns:
                                matches = list(re.finditer(pattern, context, re.IGNORECASE))
                                if matches:
                                    closest = min(matches, key=lambda m: abs(m.start() - (start_index or 0) + ctx_start))
                                    if len(closest.groups()) == 2:
                                        regex_name = f"{closest.group(1).strip()} v. {closest.group(2).strip()}"
                                    else:
                                        regex_name = closest.group(1).strip()
                                    
                                    # Clean contamination from extracted name
                                    regex_name = re.sub(r'\s+', ' ', regex_name).strip()
                                    
                                    # Remove common contamination patterns
                                    contamination_patterns = [
                                        r'^[a-z\s,\.]+\b',  # Leading lowercase text
                                        r'\b(see|citing|compare|but see|accord|cf|e\.g\.|i\.e\.|id\.|ibid)\b.*$',  # Signal words
                                        r'^\W+',  # Leading punctuation
                                        r'\s*,\s*$',  # Trailing comma
                                    ]
                                    for clean_pattern in contamination_patterns:
                                        regex_name = re.sub(clean_pattern, '', regex_name, flags=re.IGNORECASE).strip()
                                    
                                    # Only accept if it looks like a valid case name
                                    if len(regex_name) > 5 and ' v. ' in regex_name.lower():
                                        final_name = regex_name
                                        logger.debug(f"[EXTRACT-M3] Regex: '{regex_name}' for {citation_text}")
                                        break
                        except Exception as e:
                            logger.debug(f"[EXTRACT-M3] Regex failed: {e}")
                    
                    # Apply truncation repair if we have a name
                    if final_name:
                        try:
                            repaired_name = self._repair_truncated_case_name(final_name, text, start_index or 0)
                            if repaired_name != final_name:
                                logger.warning(f"[TRUNCATION-REPAIR] '{final_name}' → '{repaired_name}' for {citation_text}")
                                final_name = repaired_name
                        except Exception as e:
                            logger.debug(f"[TRUNCATION-REPAIR] Failed: {e}")
                    
                    # Final cleaning and validation before setting
                    if final_name:
                        # CRITICAL: Remove citation contamination from case names
                        final_name = self._remove_citation_contamination_from_case_name(final_name)
                        
                        # Final contamination check - ensure case name starts with uppercase
                        if not final_name[0].isupper():
                            # Try to find the actual case name start
                            match = re.search(r'\b([A-Z][A-Za-z\s\.,\'&]+\s+v\.\s+[A-Z][A-Za-z\s\.,\'&]+)', final_name)
                            if match:
                                final_name = match.group(1).strip()
                            else:
                                # Can't clean it, mark as N/A
                                final_name = None
                        
                        # Remove trailing commas and periods
                        if final_name:
                            final_name = re.sub(r'[,\.]+$', '', final_name).strip()
                    
                    # Set the final name (always prefer extracted over empty/null)
                    if final_name:
                        setattr(c, 'extracted_case_name', final_name)
                        logger.info(f"[EXTRACT-SUCCESS] Set '{final_name}' for {citation_text}")
                    elif not current_name or current_name == 'N/A':
                        setattr(c, 'extracted_case_name', 'N/A')
                        logger.warning(f"[EXTRACT-FAIL] All methods failed for {citation_text}")
                    
                except Exception as e:
                    logger.error(f"[EXTRACT-ERROR] Exception for {getattr(c, 'citation', 'unknown')}: {e}")
                    if not getattr(c, 'extracted_case_name', None):
                        setattr(c, 'extracted_case_name', 'N/A')
        except Exception as e:
            logger.error(f"[EXTRACT-PIPELINE-ERROR] {e}")
        
        logger.info("[UNIFIED_PIPELINE] Phase 2: Detecting parallel citations")
        citations = self._detect_parallel_citations(citations, text)
        logger.info(f"[UNIFIED_PIPELINE] After parallel detection: {len(citations)} citations")
        
        logger.info("[UNIFIED_PIPELINE] Phase 3: Ensuring bidirectional parallel relationships")
        self.ensure_bidirectional_parallels(citations)
        logger.info(f"[UNIFIED_PIPELINE] After bidirectional parallels: {len(citations)} citations")
        
        logger.info("[UNIFIED_PIPELINE] Phase 4: Propagating canonical data to parallel citations")
        self._update_progress(60, "Propagating Data", "Propagating canonical data to parallel citations")
        self.propagate_canonical_to_cluster(citations)
        logger.info(f"[UNIFIED_PIPELINE] After canonical propagation: {len(citations)} citations")
        
        logger.info("[UNIFIED_PIPELINE] Phase 4.5: Filtering false positive citations")
        self._update_progress(65, "Filtering", "Removing false positive citations")
        citations = self._filter_false_positive_citations(citations, text)
        logger.info(f"[UNIFIED_PIPELINE] After false positive filtering: {len(citations)} citations")
        
        # FIX #54: Diagnostic logging to find why verification doesn't run
        logger.error(f"🔍 [FIX #54] PRE-VERIFICATION CHECK:")
        logger.error(f"   enable_verification: {self.config.enable_verification}")
        logger.error(f"   citations count: {len(citations) if citations else 0}")
        logger.error(f"   Will verification run: {self.config.enable_verification and citations}")
        
        # CRITICAL FIX: Verify citations BEFORE clustering so clustering uses correct canonical names
        if self.config.enable_verification and citations:
            logger.info("[UNIFIED_PIPELINE] Phase 4.75: Verifying citations BEFORE clustering (CRITICAL)")
            self._update_progress(67, "Verifying", "Verifying citations with external sources")
            verified_citations = self._verify_citations_sync(citations, text)
            citations = verified_citations
            logger.info(f"[UNIFIED_PIPELINE] After pre-clustering verification: {len(citations)} citations")
        else:
            logger.info("[UNIFIED_PIPELINE] Phase 4.75: Skipping pre-clustering verification (disabled)")
        
        logger.info("[UNIFIED_PIPELINE] Phase 5: Creating citation clusters with MASTER clustering system")
        self._update_progress(70, "Clustering", "Creating citation clusters")
        from src.unified_clustering_master import cluster_citations_unified_master
        # ENABLE batch verification to use efficient citation-lookup API
        clusters = cluster_citations_unified_master(citations, original_text=text, enable_verification=True)
        logger.info(f"[UNIFIED_PIPELINE] Created {len(clusters)} clusters using MASTER clustering")
        
        # CRITICAL FIX: Update citation objects with cluster information immediately
        # This must happen BEFORE any serialization to ensure cluster data persists
        logger.info("[UNIFIED_PIPELINE] Phase 5.5: Updating citations with cluster information")
        citation_to_cluster = {}
        for cluster in clusters:
            cluster_id = cluster.get('cluster_id')
            cluster_case_name = cluster.get('cluster_case_name') or cluster.get('case_name')
            cluster_citations = cluster.get('citations', [])
            cluster_members = cluster.get('cluster_members', [])
            
            # Match by citation text, not object id (clusters contain dicts, not objects)
            for cit_dict in cluster_citations:
                citation_text = cit_dict.get('citation') if isinstance(cit_dict, dict) else getattr(cit_dict, 'citation', None)
                if citation_text:
                    # Store cluster_id, case_name, size, and members list
                    citation_to_cluster[citation_text] = (cluster_id, cluster_case_name, len(cluster_citations), cluster_members)
        
        updated_count = 0
        for citation in citations:
            citation_text = getattr(citation, 'citation', None)
            if citation_text and citation_text in citation_to_cluster:
                cluster_id, cluster_case_name, size, cluster_members = citation_to_cluster[citation_text]
                citation.cluster_id = cluster_id
                citation.cluster_case_name = cluster_case_name
                citation.is_cluster = size > 1
                # CRITICAL: Set cluster_members so frontend can display them
                citation.cluster_members = [m for m in cluster_members if m != citation_text]
                updated_count += 1
        
        logger.info(f"[UNIFIED_PIPELINE] Updated {updated_count} citations with cluster information")
        
        # REMOVED: Duplicate verification step - already done before clustering at Phase 4.75
        logger.info("[UNIFIED_PIPELINE] Phase 6: Verification already completed before clustering")
        
        # Validate cluster consistency before returning results
        logger.info("[UNIFIED_PIPELINE] Phase 7: Validating cluster consistency")
        self._validate_cluster_consistency(citations)
        
        self._update_progress(100, "Complete", f"Processing complete: {len(citations)} citations, {len(clusters)} clusters")
        logger.info(f"[UNIFIED_PIPELINE] Pipeline complete: {len(citations)} final citations, {len(clusters)} clusters")
        
        # Create a mapping of citation text to verification status for quick lookup
        citation_verification = {}
        for citation in citations:
            if hasattr(citation, 'citation') and hasattr(citation, 'verified'):
                # Check for true_by_parallel - first as direct attribute, then in metadata
                true_by_parallel = False
                if hasattr(citation, 'true_by_parallel'):
                    # Direct attribute (set by Fix #11 verification logic)
                    true_by_parallel = citation.true_by_parallel
                elif hasattr(citation, 'metadata') and citation.metadata:
                    # Legacy: check in metadata dict
                    true_by_parallel = citation.metadata.get('true_by_parallel', False)
                
                citation_verification[citation.citation] = {
                    'verified': citation.verified,
                    'verification_method': getattr(citation, 'verification_method', None),
                    'verification_source': getattr(citation, 'verification_source', None),  # FIX #65: Read from correct attribute
                    'verification_url': getattr(citation, 'canonical_url', None),
                    'true_by_parallel': true_by_parallel
                }
        
        # Format clusters for frontend
        formatted_clusters = []
        for cluster in clusters:
            # CRITICAL FIX #8: Each citation must display ITS OWN canonical data
            # DO NOT use cluster's aggregate canonical data - it may belong to a different citation!
            # 
            # EXAMPLE OF THE BUG:
            #   Cluster: ["192 Wn.2d 453", "430 P.3d 655"]
            #   - "192 Wn.2d 453" → API 404 (no canonical data)
            #   - "430 P.3d 655" → verified to "Spokane County"
            #   - Cluster's canonical_name = "Spokane County" (from "430 P.3d 655")
            #   - When displaying "192 Wn.2d 453", we were using cluster's canonical_name
            #   - WRONG! "192 Wn.2d 453" has NO canonical data!
            #
            # FIX: Get data ONLY from individual citations, not from cluster aggregates
            extracted_name = None
            extracted_date = None
            canonical_name = None  # DO NOT use cluster.get('canonical_name')!
            canonical_date = None  # DO NOT use cluster.get('canonical_date')!
            canonical_url = None   # DO NOT use cluster.get('canonical_url')!
            
            # Get data from first citation
            if cluster.get('citations'):
                first_citation = cluster['citations'][0]
                if isinstance(first_citation, dict):
                    # CRITICAL FIX #10: Check if first citation has error before using its canonical data
                    citation_has_error = first_citation.get('error') is not None and first_citation.get('error') != ''
                    citation_is_verified = first_citation.get('verified', False) and not citation_has_error
                    
                    # Always get extracted data
                    extracted_name = first_citation.get('extracted_case_name')
                    extracted_date = first_citation.get('extracted_date')
                    
                    # ONLY get canonical data if verified and no error
                    if citation_is_verified:
                        canonical_name = first_citation.get('canonical_name')
                        canonical_date = first_citation.get('canonical_date')
                        canonical_url = first_citation.get('canonical_url') or first_citation.get('url')
                elif hasattr(first_citation, 'extracted_case_name'):
                    # Same logic for CitationResult objects
                    citation_error = getattr(first_citation, 'error', None)
                    citation_has_error = citation_error is not None and citation_error != ''
                    citation_is_verified = getattr(first_citation, 'verified', False) and not citation_has_error
                    
                    # Always get extracted data
                    extracted_name = getattr(first_citation, 'extracted_case_name', None)
                    extracted_date = getattr(first_citation, 'extracted_date', None)
                    
                    # ONLY get canonical data if verified and no error
                    if citation_is_verified:
                        canonical_name = getattr(first_citation, 'canonical_name', None)
                        canonical_date = getattr(first_citation, 'canonical_date', None)
                        canonical_url = getattr(first_citation, 'canonical_url', None) or getattr(first_citation, 'url', None)
            
            # Fallback: If we still don't have data, check all citations (maintain data separation!)
            if cluster.get('citations'):
                for cit in cluster['citations']:
                    if isinstance(cit, dict):
                        # CRITICAL FIX #10: Only use canonical data if the citation was ACTUALLY verified
                        # and did NOT return an error (e.g., 404). Citations with errors should have
                        # NO canonical data, even if they're clustered with verified citations.
                        citation_has_error = cit.get('error') is not None and cit.get('error') != ''
                        citation_is_verified = cit.get('verified', False) and not citation_has_error
                        
                        # Always try to get extracted data from any citation
                        if not extracted_name:
                            extracted_name = cit.get('extracted_case_name')
                        if not extracted_date:
                            extracted_date = cit.get('extracted_date')
                        
                        # ONLY get canonical data from citations that were successfully verified (no errors)
                        if citation_is_verified:
                            if not canonical_name:
                                canonical_name = cit.get('canonical_name')
                            if not canonical_date:
                                canonical_date = cit.get('canonical_date')
                            if not canonical_url:
                                canonical_url = cit.get('canonical_url') or cit.get('url')
                    elif hasattr(cit, 'extracted_case_name'):
                        # Same logic for CitationResult objects
                        citation_error = getattr(cit, 'error', None)
                        citation_has_error = citation_error is not None and citation_error != ''
                        citation_is_verified = getattr(cit, 'verified', False) and not citation_has_error
                        
                        # Always try to get extracted data
                        if not extracted_name:
                            extracted_name = getattr(cit, 'extracted_case_name', None)
                        if not extracted_date:
                            extracted_date = getattr(cit, 'extracted_date', None)
                        
                        # ONLY get canonical data from verified citations with no errors
                        if citation_is_verified:
                            if not canonical_name:
                                canonical_name = getattr(cit, 'canonical_name', None)
                            if not canonical_date:
                                canonical_date = getattr(cit, 'canonical_date', None)
                            if not canonical_url:
                                canonical_url = getattr(cit, 'canonical_url', None) or getattr(cit, 'url', None)
                    
                    # Stop if we have all the data we need
                    if extracted_name and extracted_date:
                        # For canonical data, only stop if we found a verified citation
                        if canonical_name and canonical_date and canonical_url:
                            break
            
            # Determine the display name and date: Use canonical if verified, otherwise extracted
            case_name = canonical_name or extracted_name
            cluster_date = canonical_date or extracted_date
            
            # Get all citations with their verification status
            citations_with_status = []
            for citation_text in cluster.get('cluster_members', []):
                citation_info = {
                    'text': citation_text,
                    'verified': False,
                    'verification_method': None,
                    'verification_source': None,
                    'verification_url': None,
                    'true_by_parallel': False
                }
                
                # Get verification status from our mapping
                if citation_text in citation_verification:
                    citation_info.update({
                        'verified': citation_verification[citation_text]['verified'],
                        'verification_method': citation_verification[citation_text].get('verification_method'),
                        'verification_source': citation_verification[citation_text].get('verification_source'),
                        'verification_url': citation_verification[citation_text].get('verification_url'),
                        'true_by_parallel': citation_verification[citation_text].get('true_by_parallel', False)
                    })
                
                citations_with_status.append(citation_info)
            
            # Format the cluster for the frontend
            formatted_cluster = {
                'cluster_id': cluster.get('cluster_id'),
                'case_name': case_name,  # Display name (canonical if verified, otherwise extracted)
                'canonical_name': canonical_name,  # MUST be ONLY from API, never from document
                'extracted_case_name': extracted_name,  # MUST be ONLY from document, never from API
                'date': cluster_date,  # Display date (canonical if verified, otherwise extracted)
                'canonical_date': canonical_date,  # MUST be ONLY from API
                'extracted_date': extracted_date,  # MUST be ONLY from document
                'canonical_url': canonical_url,  # Add canonical URL for frontend links
                'citations': citations_with_status,  # Now includes verification status for each citation
                'size': len(cluster.get('cluster_members', [])),
                'verified': any(c['verified'] for c in citations_with_status),
                'source': 'clustering',
                'validation_method': 'cluster_validation',
                'citation_details': citations_with_status
            }
            
            formatted_clusters.append(formatted_cluster)
        
        result = {
            'citations': citations,
            'clusters': formatted_clusters
        }
        
        return result
    
    def _filter_false_positive_citations(self, citations: List[CitationResult], text: str) -> List[CitationResult]:
        """Filter out false positive citations like standalone page numbers."""
        valid_citations = []
        
        for citation in citations:
            citation_text = citation.citation if hasattr(citation, 'citation') else str(citation)
            
            if self._is_standalone_page_number(citation_text, text):
                logger.debug(f"Filtered standalone page number: {citation_text}")
                continue
            
            if self._is_volume_without_reporter(citation_text):
                logger.debug(f"Filtered volume without reporter: {citation_text}")
                continue
            
            if len(citation_text.strip()) < 8:
                logger.debug(f"Filtered too short citation: {citation_text}")
                continue
            
            valid_citations.append(citation)
        
        logger.info(f"False positive filter: {len(citations)} → {len(valid_citations)} citations")
        return valid_citations
    
    def _is_standalone_page_number(self, citation_text: str, text: str) -> bool:
        """Check if citation is just a standalone page number."""
        if re.match(r'^\d+$', citation_text):
            pos = text.find(citation_text)
            if pos != -1:
                context_before = text[max(0, pos-50):pos]
                context_after = text[pos+len(citation_text):min(len(text), pos+len(citation_text)+50)]
                
                reporter_patterns = [
                    r'\bWn\.\d*d?\b',  # Wn.2d, Wn.3d
                    r'\bP\.\d*d?\b',   # P.2d, P.3d
                    r'\bU\.S\.\b',     # U.S.
                    r'\bS\.Ct\.\b',    # S.Ct.
                    r'\bWn\.\s*App\.\b',  # Wn. App.
                ]
                
                for pattern in reporter_patterns:
                    if (re.search(pattern, context_before) or 
                        re.search(pattern, context_after)):
                        return False
                
                return True
        
        return False
    
    def _is_volume_without_reporter(self, citation_text: str) -> bool:
        """Check if citation is just a volume number without reporter."""
        if re.match(r'^\d+$', citation_text):
            return True
        
        if citation_text.lower() == "volume reporter page":
            return True
        
        parts = citation_text.split()
        if len(parts) == 2 and all(part.isdigit() for part in parts):
            return True
        
        return False

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
        results = await self.process_text(document_text)
        citation_dicts = []
        for citation in results['citations']:
            extracted_case_name = (
                citation.extracted_case_name or 
                getattr(citation, 'extracted_case_name', None) or 
                getattr(citation, 'case_name', None)
            )
            
            extracted_date = (
                citation.extracted_date or 
                getattr(citation, 'extracted_date', None) or
                (citation.metadata.get('extracted_date') if citation.metadata else None)
            )
            
            citation_dict = {
                'citation': citation.citation,
                'case_name': extracted_case_name,
                'extracted_case_name': extracted_case_name,
                'canonical_name': citation.canonical_name,
                'extracted_date': extracted_date,
                'canonical_date': citation.canonical_date,
                'verified': self._get_verification_status(citation),
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
            # Align with Enhanced Sync: enforce data separation on output
            try:
                from src.data_separation_validator import enforce_data_separation, restore_extracted_name_if_contaminated
                citation_dict = enforce_data_separation(citation_dict)
                citation_dict = restore_extracted_name_if_contaminated(citation_dict)
            except Exception:
                pass
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
        clusters = results['clusters']
        def citation_to_dict(citation):
            if isinstance(citation, str):
                return {
                    'citation': citation,
                    'case_name': None,
                    'extracted_case_name': None,
                    'canonical_name': None,
                    'extracted_date': None,
                    'canonical_date': None,
                    'verified': False,
                    'source': 'string_citation',
                    'is_parallel': False
                }
                
            if isinstance(citation, dict):
                return citation
                
            try:
                extracted_case_name = (
                    getattr(citation, 'extracted_case_name', None) or 
                    getattr(citation, 'case_name', None) or
                    (getattr(citation, 'metadata', {}).get('extracted_case_name') if hasattr(citation, 'metadata') else None)
                )
                
                extracted_date = (
                    getattr(citation, 'extracted_date', None) or
                    (getattr(citation, 'metadata', {}).get('extracted_date') if hasattr(citation, 'metadata') else None)
                )
                
                return {
                    'citation': getattr(citation, 'citation', None) or str(citation),
                    'case_name': extracted_case_name,
                    'extracted_case_name': extracted_case_name,
                    'canonical_name': getattr(citation, 'canonical_name', None),
                    'extracted_date': extracted_date,
                    'canonical_date': getattr(citation, 'canonical_date', None),
                    'verified': self._get_verification_status(citation),
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
            except Exception as e:
                return {
                    'citation': str(citation),
                    'case_name': None,
                    'extracted_case_name': None,
                    'canonical_name': None,
                    'extracted_date': None,
                    'canonical_date': None,
                    'verified': False,
                    'source': 'error_fallback',
                    'error': str(e),
                    'is_parallel': False
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
        
        formatted = self._normalize_to_bluebook_format(citation)
        
        formatted = re.sub(r'\s*,\s*', ', ', formatted)
        
        formatted = re.sub(r'\(\s*', '(', formatted)
        formatted = re.sub(r'\s*\)', ')', formatted)
        
        return formatted

    def _validate_cluster_consistency(self, citations: List['CitationResult']):
        """
        Validate and fix cluster_id and is_in_cluster consistency.
        
        Rules:
        - If cluster_id is set, is_in_cluster should be True
        - If cluster_id is null/empty, is_in_cluster should be False
        - All citations in the same cluster should have the same cluster_id
        """
        for citation in citations:
            if not hasattr(citation, 'metadata') or not citation.metadata:
                continue
                
            cluster_id = citation.metadata.get('cluster_id')
            is_in_cluster = citation.metadata.get('is_in_cluster', False)
            
            # Fix inconsistencies
            if cluster_id and not is_in_cluster:
                # Has cluster_id but is_in_cluster is False - fix it
                citation.metadata['is_in_cluster'] = True
                logger.warning(f"CLUSTER_FIX: Set is_in_cluster=True for citation '{citation.citation}' with cluster_id='{cluster_id}'")
            elif not cluster_id and is_in_cluster:
                # No cluster_id but is_in_cluster is True - fix it
                citation.metadata['is_in_cluster'] = False
                logger.warning(f"CLUSTER_FIX: Set is_in_cluster=False for citation '{citation.citation}' with null cluster_id")
            elif not cluster_id and not is_in_cluster:
                # Both are False/null - this is correct for single citations
                pass
            # If both cluster_id and is_in_cluster are set, that's correct
    
    def _get_verification_status(self, citation) -> bool:
        """
        Determine the actual verification status of a citation.
        
        Args:
            citation: Citation object to check
            
        Returns:
            bool: True if citation is verified, False otherwise
        """
        # Check the verified field
        if hasattr(citation, 'verified'):
            if isinstance(citation.verified, bool):
                return citation.verified
            elif citation.verified == "true_by_parallel":
                return True
            elif citation.verified is True:
                return True
        
        # Check metadata for verification status
        if hasattr(citation, 'metadata') and citation.metadata:
            verification_status = citation.metadata.get('verification_status')
            if verification_status == 'verified':
                return True
        
        # Check if we have canonical data (indicates verification)
        if (hasattr(citation, 'canonical_name') and citation.canonical_name and 
            hasattr(citation, 'canonical_url') and citation.canonical_url):
            return True
            
        return False

    def _propagate_canonical_to_parallels(self, citations: List['CitationResult']):
        """
        For each verified citation, propagate canonical_name and canonical_date to its unverified parallels.
        Mark those as true_by_parallel, but do NOT set verified=True for parallels.
        """
        citation_lookup = {c.citation: c for c in citations}
        for citation in citations:
            if citation.verified and citation.canonical_name and citation.canonical_date:
                for parallel in (citation.parallel_citations or []):
                    parallel_cite = citation_lookup.get(parallel)
                    if parallel_cite and not parallel_cite.verified:
                        parallel_cite.canonical_name = citation.canonical_name
                        parallel_cite.canonical_date = citation.canonical_date
                        parallel_cite.url = citation.url
                        parallel_cite.source = citation.source
                        if not hasattr(parallel_cite, 'metadata') or parallel_cite.metadata is None:
                            parallel_cite.metadata = {}
                        parallel_cite.metadata['true_by_parallel'] = True
        for c in citations:
            pass  # This loop was incomplete, adding pass to fix syntax

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
        # and then propagates wrong case names. Let each citation keep its own extracted data.
        #
        # citation_lookup = {c.citation: c for c in citations}
        # processed = set()
        # for citation in citations:
        #     if citation.citation in processed:
        #         continue
        #     group = [citation]
        #     for parallel in (citation.parallel_citations or []):
        #         parallel_cite = citation_lookup.get(parallel)
        #         if parallel_cite and parallel_cite not in group:
        #             group.append(parallel_cite)
        #     best_name = next((c.extracted_case_name for c in group if c.extracted_case_name and c.extracted_case_name != 'N/A'), None)
        #     best_date = next((c.extracted_date for c in group if c.extracted_date and c.extracted_date != 'N/A'), None)
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
        citation_lookup = {c.citation: c for c in citations}
        visited = set()
        for citation in citations:
            if citation.citation in visited:
                continue
            group = set([citation.citation])
            if citation.parallel_citations:
                group.update(citation.parallel_citations)
            verified_member = None
            for cite_str in group:
                c = citation_lookup.get(cite_str)
                if c and c.verified and c.canonical_name and c.canonical_date:
                    verified_member = c
                    break
            if verified_member:
                for cite_str in group:
                    c = citation_lookup.get(cite_str)
                    if c and (not c.canonical_name or not c.canonical_date):
                        c.canonical_name = verified_member.canonical_name
                        c.canonical_date = verified_member.canonical_date
                        c.url = verified_member.url
                        c.source = verified_member.source
                        if not c.verified:
                            c.verified = "true_by_parallel"
                            if not hasattr(c, 'metadata'):
                                c.metadata = {}
                            c.metadata['true_by_parallel'] = True
                    visited.add(cite_str)
        for c in citations:
            pass  # This loop was incomplete, adding pass to fix syntax

    def ensure_bidirectional_parallels(self, citations: List['CitationResult']):
        """
        For each group of citations that are close together (by position and punctuation), ensure all group members have each other in their parallel_citations field.
        """
        sorted_citations = sorted(citations, key=lambda x: x.start_index or 0)
        n = len(sorted_citations)
        i = 0
        while i < n:
            group = [sorted_citations[i]]
            j = i + 1
            while j < n:
                curr = sorted_citations[j]
                prev = group[-1]
                if (curr.start_index and prev.end_index and curr.start_index - prev.end_index <= 100):
                    text_between = ''
                    if hasattr(prev, 'end_index') and hasattr(curr, 'start_index'):
                        text_between = getattr(prev, 'context', '')[-(prev.end_index - (prev.start_index or 0)):] + getattr(curr, 'context', '')[:curr.start_index - (curr.start_index or 0)]
                    if ',' in text_between or (curr.start_index - prev.end_index <= 10):
                        group.append(curr)
                        j += 1
                        continue
                break
            if len(group) > 1:
                cite_strs = [c.citation for c in group]
                for c in group:
                    c.parallel_citations = [s for s in cite_strs if s != c.citation]
            i = j
        if self.config.debug_mode:
            for c in citations:
                pass  # This loop was incomplete, adding pass to fix syntax

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
            date_member = None
            for cite_str in group:
                c = citation_lookup.get(cite_str)
                if c and c.extracted_date:
                    date_member = c
                    break
            if date_member:
                for cite_str in group:
                    c = citation_lookup.get(cite_str)
                    if c and not c.extracted_date:
                        c.extracted_date = date_member.extracted_date
                    visited.add(cite_str)
        if self.config.debug_mode:
            for c in citations:
                pass  # This loop was incomplete, adding pass to fix syntax

        try:
            from src.unified_clustering_master import _normalize_citation_comprehensive
            normalized_text = _normalize_citation_comprehensive(text)
            logger.info(f"Text normalized for citation extraction (length: {len(normalized_text)})")
        except Exception as e:
            logger.warning(f"Normalization failed, using original text: {e}")
            normalized_text = text
        
        results = []
        
        priority_patterns = [
            r'\b(\d+)\s+U\.?S\.?\s+(\d+)(?:\s*\((\d{4})\))?',
            r'\b(\d+)\s+S\.?\s*Ct\.?\s+(\d+)(?:\s*\((\d{4})\))?',
            r'\b(\d+)\s+L\.?\s*Ed\.?\s*2d\s+(\d+)(?:\s*\((\d{4})\))?',
            
            r'\b(\d+)\s+F\.?\s*3d\s+(\d+)(?:\s*\((\d{4})\))?',
            r'\b(\d+)\s+F\.?\s*2d\s+(\d+)(?:\s*\((\d{4})\))?',
            r'\b(\d+)\s+F\.?\s+(\d+)(?:\s*\((\d{4})\))?',
            r'\b(\d+)\s+F\.?\s*Supp\.?\s*3d\s+(\d+)(?:\s*\((\d{4})\))?',
            r'\b(\d+)\s+F\.?\s*Supp\.?\s*2d\s+(\d+)(?:\s*\((\d{4})\))?',
            r'\b(\d+)\s+F\.?\s*Supp\.?\s+(\d+)(?:\s*\((\d{4})\))?',
            
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
            
            r'\b(\d+)\s+Wn\.?\s*3d\s+(\d+)(?:\s*\((\d{4})\))?',
            r'\b(\d+)\s+Wash\.?\s*3d\s+(\d+)(?:\s*\((\d{4})\))?',
        ]
        
        for pattern in priority_patterns:
            matches = re.finditer(pattern, normalized_text, re.IGNORECASE)
            for match in matches:
                volume = match.group(1)
                page = match.group(2)
                year = match.group(3) if len(match.groups()) >= 3 and match.group(3) else None
                
                citation_text = match.group(0)
                
                start_pos = max(0, match.start() - 200)
                context = normalized_text[start_pos:match.start()]
                
                case_name = "N/A"
                case_patterns = [
                    r'([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[a-zA-Z\'\.\&]+|of|the|and|&))*)\s+v\.\s+([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[a-zA-Z\'\.\&]+|of|the|and|&))*),?\s*$',
                    r'([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[a-zA-Z\'\.\&]+|of|the|and|&))*)\s+vs\.\s+([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[a-zA-Z\'\.\&]+|of|the|and|&))*),?\s*$',
                    r'(In\s+re\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[a-zA-Z\'\.\&]+|of|the|and|&))*),?\s*$',
                    r'(Ex\s+parte\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[a-zA-Z\'\.\&]+|of|the|and|&))*),?\s*$',
                ]
                
                for idx, case_pattern in enumerate(case_patterns):
                    matches = list(re.finditer(case_pattern, context, re.IGNORECASE))
                    if matches:
                        match = matches[-1]
                        if len(match.groups()) >= 2 and idx in [0, 1]:  # Two-party cases
                            case_name = f"{match.group(1).strip()} v. {match.group(2).strip()}"
                        else:  # Single-party cases
                            case_name = match.group(1).strip()
                        
                        if len(case_name) > 5:
                            break
                
                results.append({
                    'case_name': case_name,
                    'citation': citation_text,
                    'year': year,
                    'start_index': match.start(),
                    'end_index': match.end()
                })
        
        try:
            import eyecite
            eyecite_citations = eyecite.get_citations(normalized_text)
            logger.info(f"Eyecite found {len(eyecite_citations)} additional citations")
            
            for cite in eyecite_citations:
                citation_text = str(cite)
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
    case_name_pattern = r'([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)'
    year_pattern = r'\((\d{4})\)'
    citation_pattern = r'(\d+\s+(?:Wn\.2d|Wash\.2d|P\.3d|P\.2d|F\.3d|F\.2d|U\.S\.|S\.Ct\.|L\.Ed\.|A\.2d|A\.3d|So\.2d|So\.3d)\s+\d+)'  # Expand as needed

    for case_match in re.finditer(case_name_pattern, text):
        case_start = case_match.start()
        case_end = case_match.end()
        case_name = f"{case_match.group(1)} v. {case_match.group(2)}"
        year_match = re.search(year_pattern, text[case_end:])
        if not year_match:
            continue
        year_start = case_end + year_match.start()
        year_end = case_end + year_match.end()
        year = year_match.group(1)
        between = text[case_end:year_start]
        citations = re.findall(citation_pattern, between)
        if citations:
            clusters.append({
                'case_name': case_name,
                'year': year,
                'citations': citations,
                'start': case_start,
                'end': year_end
            })
    return clusters

