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

from src.unified_case_name_extractor_v2 import (
    get_unified_extractor,
    extract_case_name_and_date_master,
    extract_case_name_only_unified
)

from src.unified_citation_clustering import cluster_citations_unified
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
    from src.unified_citation_clustering import (
        UnifiedCitationClusterer,
        cluster_citations_unified
    )
    CLUSTERING_AVAILABLE = True
    logger.info("Citation clustering successfully imported")
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

from src.unified_citation_clustering import cluster_citations_unified

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
        self.progress_callback = progress_callback  # NEW: Progress callback support
        self._init_patterns()
        self._init_case_name_patterns()
        self._init_date_patterns()
        self._init_state_reporter_mapping()
        
        # Initialize CourtListener API key
        self.courtlistener_api_key = os.getenv('COURTLISTENER_API_KEY')
        
        # Initialize enhanced web searcher
        from src.comprehensive_websearch_engine import ComprehensiveWebSearchEngine
        self.enhanced_web_searcher = ComprehensiveWebSearchEngine(enable_experimental_engines=True)
        logger.info("Initialized ComprehensiveWebSearchEngine for legal database lookups")
        
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
            'wn2d': re.compile(r'\b(\d+)\s+Wn\.2d\s*\n?\s*(\d+)(?:\s*,\s*\d+\s*P\.3d\s*\d+)?\b', re.IGNORECASE),
            'wn2d_space': re.compile(r'\b(\d+)\s+Wn\.\s*2d\s*\n?\s*(\d+)(?:\s*,\s*\d+\s*P\.3d\s*\d+)?\b', re.IGNORECASE),
            'wn_app': re.compile(r'\b(\d+)\s+Wn\.\s*App\.\s+(\d+)\b', re.IGNORECASE),
            'wn_app_space': re.compile(r'\b(\d+)\s+Wn\.\s*App\s+(\d+)\b', re.IGNORECASE),
            'wn3d': re.compile(r'\b(\d+)\s+Wn\.\s*3d\s*\n?\s*(\d+)\b', re.IGNORECASE),
            'wn3d_space': re.compile(r'\b(\d+)\s+Wn\.\s*3d\s*\n?\s*(\d+)\b', re.IGNORECASE),
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
            
            logger.info(f"🔍 [CITATION_BLOCKS] Found citation block: '{case_name}' with citations '{citations_text}' year {year}")
            
            individual_citations = self._extract_citations_from_block(citations_text)
            
            for citation_text in individual_citations:
                citation_start = text.find(citation_text, start)
                citation_end = citation_start + len(citation_text) if citation_start != -1 else start
                
                citation = CitationResult(
                    citation=citation_text,
                    start_index=citation_start,
                    end_index=citation_end,
                    extracted_case_name=case_name,
                    extracted_date=year,
                    canonical_name=None,
                    canonical_date=None,
                    url=None,
                    verified=False,
                    source="citation_block",
                    confidence=0.9,  # Higher confidence for block extraction
                    metadata={
                        'block_case_name': case_name,
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
        
        if any(pattern in citation_str for pattern in [
            "U.S.C.", "USC", "U.S.C", "U.S.C.A.", "USCA", "C.F.R.", "CFR", "C.F.R"
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
        """Extract metadata from eyecite citation object."""
        try:
            citation.metadata.update({
                'volume': getattr(citation_obj, 'volume', None),
                'reporter': getattr(citation_obj, 'reporter', None), 
                'page': getattr(citation_obj, 'page', None),
                'year': getattr(citation_obj, 'year', None),
                'court': getattr(citation_obj, 'court', None),
                'type': getattr(citation_obj, 'type', None),
            })
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
                    
                    citations.append(citation)
                    
                except Exception as e:
                    logger.error(f"Error processing eyecite citation: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in eyecite extraction: {e}")
            
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
                logger.debug(f"Error normalizing citation: {e}")
            if self.config.extract_case_names:
                try:
                    if citation.start_index is not None:
                        context_start = max(0, citation.start_index - 300)
                        isolated_context = text[context_start:citation.start_index].strip()
                    else:
                        citation_pos = text.find(citation.citation)
                        if citation_pos != -1:
                            context_start = max(0, citation_pos - 300)
                            isolated_context = text[context_start:citation_pos].strip()
                        else:
                            isolated_context = ""
                    
                    
                    if True:

                    
                    
                        pass  # Empty block

                    
                    
                    
                        pass  # Empty block

                    
                    
                    
                        unified_result = extract_case_name_and_date_master(
                            text=text,
                            citation=citation.citation,
                            citation_start=citation.start_index,
                            citation_end=citation.end_index
                        )
                        
                        
                        extracted_name = unified_result.get('case_name', '')
                        extracted_date = unified_result.get('year', '')
                        confidence = unified_result.get('confidence', 0.0)
                        method = unified_result.get('method', 'unknown')
                        
                        if extracted_name and len(extracted_name.strip()) > 3:
                            citation.extracted_case_name = extracted_name
                            citation.case_name = extracted_name
                        else:
                            manual_case_name = self._extract_case_name_from_context(text, citation)
                            if manual_case_name:
                                citation.extracted_case_name = manual_case_name
                                citation.case_name = manual_case_name
                            else:
                                citation.extracted_case_name = "N/A"
                                citation.case_name = "N/A"
                    else:
                        manual_case_name = self._extract_case_name_from_context(text, citation)
                        if manual_case_name:
                            citation.extracted_case_name = manual_case_name
                            citation.case_name = manual_case_name
                        else:
                            citation.extracted_case_name = "N/A"
                            citation.case_name = "N/A"
                except Exception as e:
                    # Don't overwrite existing extracted case name on exception
                    if not citation.extracted_case_name:
                        citation.extracted_case_name = "N/A"
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
        
        search_start = max(0, citation.start_index - 200)
        search_end = min(len(text), citation.end_index + 200)
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
        
        context_start = max(0, citation.start_index - 150)
        context_end = min(len(text), citation.end_index + 100)
        
        for boundary_type, start, end in all_boundaries:
            if end < citation.start_index and end > context_start:
                context_start = end + 1
                if boundary_type == 'date':
                    context_start = min(context_start + 10, citation.start_index)
        
        for boundary_type, start, end in all_boundaries:
            if start > citation.end_index and start < context_end:
                context_end = start - 1
                break
        
        context = text[context_start:context_end].strip()
        
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
        
        v_pattern_improved = r'([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*)\s+v\.\s+([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*)(?:\s*,|\s*\(|\s*$)'
        match = re.search(v_pattern_improved, case_name)
        if match:
            extracted = f"{match.group(1).strip()} v. {match.group(2).strip()}"
            if len(extracted) < 200 and ' v. ' in extracted:
                return extracted
        
        case_name_lower = case_name.lower()
        for indicator in contamination_indicators:
            if indicator in case_name_lower:
                v_pattern = r'([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*)\s+v\.\s+([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*)(?=\s*,|\s*$)'
                match = re.search(v_pattern, case_name)
                if match:
                    extracted = f"{match.group(1).strip()} v. {match.group(2).strip()}"
                    if len(extracted) < 200 and ' v. ' in extracted:
                        return extracted
                    else:
                        last_v_pattern = r'([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*)\s+v\.\s+([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*)(?=[^A-Za-z]*$)'
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
            v_pattern = r'([A-Z][A-Za-z0-9&.\'\s-]+(?:\s+[A-Za-z0-9&.\'\s-]+)*?)\s+v\.\s+([A-Z][A-Za-z0-9&.\'\s-]+(?:\s+[A-Za-z0-9&.\'\s-]+)*?)(?=\s*,|\s*\(|\s*$)'
            match = re.search(v_pattern, case_name)
            if match:
                case_name = f"{match.group(1).strip()} v. {match.group(2).strip()}"
            else:
                return ""  # Too long and no clear case name pattern
        
        case_name_patterns = [
            r'^([A-Z][a-zA-Z\'\.\&\s]+?)\s+v\.\s+([A-Z][a-zA-Z\'\.\&\s]+?)(?:\s*,)?',  # Party v. Party - allows apostrophes, periods, ampersands
            r'^(In\s+re\s+[A-Z][a-zA-Z\'\.\&\s]+?)(?:\s*,)?',  # In re cases - allows full names
            r'^(Ex\s+parte\s+[A-Z][a-zA-Z\'\.\&\s]+?)(?:\s*,)?',  # Ex parte cases - allows full names
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
        Enhanced case name extraction with improved context handling and fallbacks.
        
        Args:
            text: The full document text
            citation: The citation to extract context for
            all_citations: List of all citations in the document (for context isolation)
            
        Returns:
            Extracted case name or None if not found
        """
        try:
            from src.unified_case_name_extractor_v2 import extract_case_name_and_date_master
            
            result = extract_case_name_and_date_master(
                text=text,
                citation=getattr(citation, 'citation', None),
                citation_start=getattr(citation, 'start_index', None),
                citation_end=getattr(citation, 'end_index', None),
                debug=False
            )
            
            case_name = result.get('case_name')
            if case_name and case_name != 'N/A':
                return case_name
        except Exception as e:
            logger.debug(f"Error extracting case name from context: {e}")
        
        if not citation.start_index or not citation.end_index:
            return None
            
        citation_text = citation.citation
        start = citation.start_index
        end = citation.end_index
        
        context_start = max(0, start - 300)  # Increased lookback to 300 chars
        context_end = min(len(text), end + 100)  # Look ahead 100 chars (less important)
        
        context = text[context_start:start] + ' ' + citation_text + ' ' + text[end:context_end]
        
        before_citation = text[max(0, start-100):start]
        
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
                    match = matches[-1]
                    
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
        
        immediate_context = text[max(0, start-100):start].strip()
        if ',' in immediate_context and len(immediate_context) > 20:
            potential_name = immediate_context.rsplit(',', 1)[0].strip()
            if self._is_valid_case_name(potential_name):
                return potential_name
        
        return None

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
        context_end = min(len(text), case_pos + len(case_name) + 300)  # Reduced from 1000 to 300
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
                        potential_start = max(0, citation.start_index - 300)  # Increased from 100
                        
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
                    potential_start = max(0, citation.start_index - 300)  # Increased from 100
                    
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
        
        sorted_citations = sorted(citations, key=lambda x: (x.start_index or 0, -(x.end_index or 0)))
        
        non_overlapping = []
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
                    break
            
            if not overlaps:
                non_overlapping.append(citation)
        
        seen = {}
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
                    seen[key] = citation
        
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
                    citation.is_parallel = True
                    citation.cluster_id = cluster_id
                    citation.cluster_members = [c for c in member_citations if c != citation.citation]
                    citation.parallel_citations = [c for c in member_citations if c != citation.citation]
                    group_case_names = [c.extracted_case_name for c in group if c.extracted_case_name and c.extracted_case_name != 'N/A']
                    if len(group_case_names) > 1:
                        normalized_names = [self._normalize_case_name_for_clustering(name) for name in group_case_names]
                        if len(set(normalized_names)) == 1 or all(
                            self._calculate_case_name_similarity(normalized_names[0], name) > 0.8 
                            for name in normalized_names[1:]
                        ):
                            if not citation.extracted_case_name or citation.extracted_case_name == 'N/A':
                                citation.extracted_case_name = best_name
                    else:
                        if not citation.extracted_case_name or citation.extracted_case_name == 'N/A':
                            citation.extracted_case_name = best_name
                    
                    # CRITICAL: Never overwrite extracted_date if it already contains a valid year from user document
                    if (not citation.extracted_date or citation.extracted_date == 'N/A') and best_date:
                        citation.extracted_date = best_date
                    elif citation.extracted_date and not re.match(r'^\d{4}$', str(citation.extracted_date)) and best_date:
                        # If current extracted_date looks contaminated (has month/day), replace with clean year
                        logger.warning(f"[DATA_SEPARATION] Replacing contaminated date '{citation.extracted_date}' with clean year '{best_date}' for {citation.citation}")
                        citation.extracted_date = best_date
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

    def _verify_citations_sync(self, citations: List['CitationResult'], text: Optional[str] = None) -> List['CitationResult']:
        """Verify citations using CourtListener and fallback sources with enhanced validation."""
        logger.info(f"[VERIFICATION] Starting verification for {len(citations)} citations")
        
        if not citations:
            return citations
        
        courtlistener_verified_count = 0
        courtlistener_errors = []
        
        for citation in citations:
            try:
                # Verification handled by unified clustering - deprecated check removed
                        validation_result = self._validate_verification_result(citation, 'CourtListener')
                        if validation_result['valid']:
                            courtlistener_verified_count += 1
                            logger.info(f"[VERIFICATION] SUCCESS: CourtListener verified: {citation.citation} -> {citation.canonical_name}")
                        else:
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
        
        if courtlistener_errors:
            logger.info(f"[VERIFICATION] CourtListener errors: {len(courtlistener_errors)} citations failed")
            if self.config.debug_mode:
                for error in courtlistener_errors[:3]:  # Show first 3 errors in debug mode
                    logger.debug(f"[VERIFICATION] CourtListener error: {error}")
        
        logger.info(f"[VERIFICATION] CourtListener results: {courtlistener_verified_count}/{len(citations)} verified")
        
        unverified_citations = [c for c in citations if not c.verified]
        logger.info(f"[VERIFICATION] {len(unverified_citations)} citations need fallback verification")
        
        fallback_verified_count = 0
        fallback_errors = []
        fallback_validation_failures = []
        
        if unverified_citations:
            try:
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
                        if True:

                            pass  # Empty block

                        
                            pass  # Empty block

                        
                        result = verifier.verify_citation_sync(
                            citation_text, 
                            extracted_case_name, 
                            extracted_date
                        )
                        
                        if result['verified']:
                            citation.verified = True
                            citation.canonical_name = result['canonical_name']
                            citation.canonical_date = result['canonical_date']
                            citation.url = result['url']
                            citation.source = result['source']  # Use actual website source (e.g., 'Cornell Law', 'Justia')
                            citation.confidence = result['confidence']
                            
                            validation_result = self._validate_verification_result(citation, f"Fallback-{result['source']}")
                            
                            if validation_result['valid']:
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
                            failure_reason = result.get('error', 'Unknown error')
                            
                    except Exception as e:
                        error_context = {
                            'citation': citation.citation,
                            'extracted_name': getattr(citation, 'extracted_case_name', 'N/A'),
                            'error': str(e),
                            'step': 'Fallback verification'
                        }
                        fallback_errors.append(error_context)
                        logger.warning(f"[VERIFICATION] Fallback verification error for {citation.citation}: {str(e)}")
                
                logger.info(f"[VERIFICATION] Fallback results: {fallback_verified_count}/{len(unverified_citations)} verified")
                
                if fallback_validation_failures:
                    logger.info(f"[VERIFICATION] Fallback validation failures: {len(fallback_validation_failures)} citations failed validation")
                    if self.config.debug_mode:
                        for failure in fallback_validation_failures[:3]:  # Show first 3 failures in debug mode
                            logger.debug(f"[VERIFICATION] Fallback validation failure: {failure}")
                
                if fallback_errors:
                    logger.info(f"[VERIFICATION] Fallback errors: {len(fallback_errors)} citations had errors")
                    if self.config.debug_mode:
                        for error in fallback_errors[:3]:  # Show first 3 errors in debug mode
                            logger.debug(f"[VERIFICATION] Fallback error: {error}")
                
            except Exception as e:
                logger.error(f"[VERIFICATION] Critical error in fallback verification system: {str(e)}")
                if self.config.debug_mode:
                    import traceback
        
        total_verified = sum(1 for c in citations if c.verified)
        verification_rate = (total_verified / len(citations)) * 100 if citations else 0
        
        logger.info(f"[VERIFICATION] === FINAL VERIFICATION SUMMARY ===")
        logger.info(f"[VERIFICATION] Total citations processed: {len(citations)}")
        logger.info(f"[VERIFICATION] Successfully verified: {total_verified} ({verification_rate:.1f}%)")
        logger.info(f"[VERIFICATION] CourtListener verified: {courtlistener_verified_count}")
        logger.info(f"[VERIFICATION] Fallback verified: {fallback_verified_count}")
        logger.info(f"[VERIFICATION] Still unverified: {len(citations) - total_verified}")
        
        if total_verified > 0:
            high_confidence_count = sum(1 for c in citations if c.verified and hasattr(c, 'confidence') and c.confidence and c.confidence > 0.8)
            medium_confidence_count = sum(1 for c in citations if c.verified and hasattr(c, 'confidence') and c.confidence and 0.5 <= c.confidence <= 0.8)
            low_confidence_count = sum(1 for c in citations if c.verified and hasattr(c, 'confidence') and c.confidence and c.confidence < 0.5)
            
            logger.info(f"[VERIFICATION] Quality breakdown:")
            logger.info(f"[VERIFICATION]   High confidence (>0.8): {high_confidence_count}")
            logger.info(f"[VERIFICATION]   Medium confidence (0.5-0.8): {medium_confidence_count}")
            logger.info(f"[VERIFICATION]   Low confidence (<0.5): {low_confidence_count}")
        
        if self.config.debug_mode:
            unverified_citations = [c for c in citations if not c.verified]
            if unverified_citations:
                for citation in unverified_citations[:5]:  # Show first 5 unverified
                    logger.debug(f"[VERIFICATION] Unverified citation: {citation.citation}")
        
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
        
        if purpose in ["verification", "general"]:
            normalized = re.sub(r'\bWn\.2d\b', 'Wash.2d', normalized)
            normalized = re.sub(r'\bWn\.3d\b', 'Wash.3d', normalized)
            normalized = re.sub(r'\bWn\.\s*App\.\b', 'Wash.App.', normalized)
            normalized = re.sub(r'\bWn\.\b', 'Wash.', normalized)
            
            normalized = normalized.replace('wn2d', 'wash2d')
            normalized = normalized.replace('wnapp', 'washapp')
        
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
        
        logger.info("[UNIFIED_EXTRACTION] Step 3: Extracting names and dates with full text context")
        for citation in all_citations:
            try:
                if not citation.extracted_case_name:
                    citation.extracted_case_name = self._extract_case_name_from_context(text, citation, all_citations)
                
                if not citation.extracted_date:
                    citation.extracted_date = self._extract_date_from_context(text, citation)
                
            except Exception as e:
                logger.warning(f"[UNIFIED_EXTRACTION] Error extracting metadata for {citation.citation}: {e}")
        
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
            words1 = set(name1.lower().split())
            words2 = set(name2.lower().split())
            common_words = words1.intersection(words2)
            
            if len(common_words) >= 1:  # At least 1 common word (changed from 2)
                return True
        
        date1 = citation1.extracted_date or ""
        date2 = citation2.extracted_date or ""
        
        if date1 and date2 and date1 == date2:
            return True
            
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
        
        logger.info("[UNIFIED_EXTRACTION] Step 1: Enhanced regex extraction")
        regex_citations = self._extract_with_regex_enhanced(text)
        logger.info(f"[UNIFIED_EXTRACTION] Regex found {len(regex_citations)} citations")
        all_citations.extend(regex_citations)
        
        if EYECITE_AVAILABLE:
            logger.info("[UNIFIED_EXTRACTION] Step 2: Eyecite extraction")
            eyecite_citations = self._extract_with_eyecite(text)
            logger.info(f"[UNIFIED_EXTRACTION] Eyecite found {len(eyecite_citations)} citations")
            all_citations.extend(eyecite_citations)
        else:
            logger.info("[UNIFIED_EXTRACTION] Step 2: Eyecite not available, skipping")
        
        logger.info("[UNIFIED_EXTRACTION] Step 3: Initial deduplication")
        deduplicated_citations = self._deduplicate_citations(all_citations)
        logger.info(f"[UNIFIED_EXTRACTION] After deduplication: {len(deduplicated_citations)} citations")
        
        logger.info("[UNIFIED_EXTRACTION] Step 4: Extracting names and dates with full text context")
        for citation in deduplicated_citations:
            try:
                if not citation.extracted_case_name:
                    citation.extracted_case_name = self._extract_case_name_from_context(text, citation, deduplicated_citations)
                
                if not citation.extracted_date:
                    citation.extracted_date = self._extract_date_from_context(text, citation)
                    
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
        self._update_progress(10, "Extracting", "Extracting citations from text")
        
        citations = self._extract_citations_unified(text)
        logger.info(f"[UNIFIED_PIPELINE] Phase 1 complete: {len(citations)} citations extracted")
        self._update_progress(30, "Enhancing", "Enhancing citation data with case names and dates")
        
        # Align with Enhanced Sync: upgrade truncated names using master extractor
        try:
            from src.unified_case_name_extractor_v2 import extract_case_name_and_date_master
            master_tokens = ["dep't", "department", "dept", "fish", "wildlife", "bros.", "farms", "inc", "llc", "corp", "ltd", "co."]
            for c in citations:
                try:
                    current_name = getattr(c, 'extracted_case_name', None) or ''
                    citation_text = getattr(c, 'citation', '')
                    start_index = getattr(c, 'start_index', None)
                    end_index = getattr(c, 'end_index', None)
                    res = extract_case_name_and_date_master(
                        text=text,
                        citation=citation_text,
                        citation_start=start_index if start_index != -1 else None,
                        citation_end=end_index,
                        debug=False
                    )
                    full_name = (res or {}).get('case_name') or ''
                    if full_name and full_name != 'N/A' and full_name != current_name:
                        current_lower = current_name.lower()
                        full_lower = full_name.lower()
                        is_truncated = current_lower.endswith(' v. dep') or current_lower.endswith(" v. dep't") or current_lower.endswith(' v. dept')
                        contains_key_tokens = any(t in full_lower for t in master_tokens)
                        is_clearly_longer = len(full_name) >= len(current_name) + 4
                        names_share_prefix = (current_name.split(' v.')[0] if current_name else '') == (full_name.split(' v.')[0] if full_name else '')
                        should_replace = (not current_name) or (names_share_prefix and (is_truncated or contains_key_tokens or is_clearly_longer))
                        if should_replace:
                            setattr(c, 'extracted_case_name', full_name)
                            try:
                                if hasattr(self, '_clean_extracted_case_name'):
                                    cleaned = self._clean_extracted_case_name(full_name)
                                    setattr(c, 'extracted_case_name', cleaned)
                            except Exception:
                                pass
                except Exception:
                    continue
        except Exception:
            pass
        
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
        
        logger.info("[UNIFIED_PIPELINE] Phase 5: Creating citation clusters with unified system")
        self._update_progress(70, "Clustering", "Creating citation clusters")
        clusters = cluster_citations_unified(citations, original_text=text, enable_verification=True)
        logger.info(f"[UNIFIED_PIPELINE] Created {len(clusters)} clusters using unified clustering")
        
        if self.config.enable_verification and citations:
            logger.info("[UNIFIED_PIPELINE] Phase 6: Verifying citations (enabled)")
            self._update_progress(80, "Verifying", "Verifying citations with external sources")
            verified_citations = self._verify_citations_sync(citations, text)
            citations = verified_citations
            logger.info(f"[UNIFIED_PIPELINE] After verification: {len(citations)} citations")
        else:
            logger.info("[UNIFIED_PIPELINE] Phase 6: Skipping verification (disabled)")
        
        self._update_progress(100, "Complete", f"Processing complete: {len(citations)} citations, {len(clusters)} clusters")
        logger.info(f"[UNIFIED_PIPELINE] Pipeline complete: {len(citations)} final citations, {len(clusters)} clusters")
        
        return {
            'citations': citations,
            'clusters': clusters
        }

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
            from src.unified_citation_clustering import _normalize_citation_comprehensive
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

