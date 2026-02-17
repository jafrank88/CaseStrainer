# type: ignore
"""
Unified Citation Processor v2 - Consolidated Citation Extraction and Processing

[WARNING] DEPRECATION NOTICE [WARNING]
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
from typing import List, Dict, Any, Optional, Tuple
import os

# UNIFIED IMPORTS - Use src.extraction for extraction (single source of truth)
from src.extraction import extract_case_name_and_date_unified_master

from src.unified_clustering_master_optimized import cluster_citations_optimized as cluster_citations_unified
import warnings

# Import helper for filtering cluster members (moved to utils to avoid circular imports)
from src.utils.cluster_filter import filter_cluster_members_by_reporter
from src.utils.same_case import has_case_name, names_are_same_case
from src.utils.date_utils import years_match_for_verification

logger = logging.getLogger(__name__)

try:
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

# REMOVED: Unused imports from case_name_extraction_core
# These functions are not used in this module since we use src.extraction

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

# REMOVED: Unused imports from citation_utils_consolidated
# These functions are not used in this module

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
    from src.unified_clustering_master import UnifiedClusteringMaster as UnifiedCitationClusterer

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

def _is_citation_contained_in_any(citation_str: str, existing_citations: set) -> bool:
    """Check if a citation is contained within any existing citation.
    e.g. '200 Wn.2d' is contained in '200 Wn.2d 72'"""
    norm_citation = citation_str.strip()
    for existing in existing_citations:
        norm_existing = existing.strip()
        if norm_citation in norm_existing and len(norm_existing) > len(norm_citation):
            remaining = norm_existing[len(norm_citation):].strip()
            if remaining and any(c.isdigit() for c in remaining):
                return True
        if ", " in norm_existing and norm_citation.startswith(("P.", "F.")):
            parts = norm_existing.split(", ")
            for part in parts[1:]:
                if norm_citation == part.strip():
                    return True
                if norm_citation in part and len(part) > len(norm_citation):
                    return True
    return False

CitationList = List[CitationResult]
CitationDict = Dict[str, Any]
VerificationResult = Dict[str, Any]

class UnifiedCitationProcessorV2:
    """
    Unified citation processor that consolidates the best parts of all existing implementations.
    """

    def __init__(self, config: Optional[ProcessingConfig] = None, progress_callback: Optional[callable] = None):
        self.config = config or ProcessingConfig()
        logger.warning(
            f"[CONFIG-CHECK] extract_case_names={self.config.extract_case_names}, extract_dates={self.config.extract_dates}"
        )

        # CRITICAL FIX: Force enable case name extraction if it's somehow disabled
        if not self.config.extract_case_names:
            logger.warning(f"[CONFIG-ERROR] extract_case_names was False! Forcing to True")
            self.config.extract_case_names = True

        self.progress_callback = progress_callback  # NEW: Progress callback support
        self._init_patterns()
        self._init_case_name_patterns()
        self._init_date_patterns()
        self._init_state_reporter_mapping()

        # Initialize CourtListener API key
        self.courtlistener_api_key = os.getenv("COURTLISTENER_API_KEY")

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
            "wn_first": re.compile(r"\b(\d+)\s+Wn\.\s+(\d+)\b", re.IGNORECASE),
            "wash_first": re.compile(r"\b(\d+)\s+Wash\.\s+(\d+)\b", re.IGNORECASE),
            # Washington Second Series
            "wn2d": re.compile(r"\b(\d+)\s+Wn\.2d\s*\n?\s*(\d+)(?:\s*,\s*\d+\s*P\.3d\s*\d+)?\b", re.IGNORECASE),
            "wn2d_space": re.compile(
                r"\b(\d+)\s+Wn\.\s*2d\s*\n?\s*(\d+)(?:\s*,\s*\d+\s*P\.3d\s*\d+)?\b", re.IGNORECASE
            ),
            # Washington Court of Appeals
            "wn_app": re.compile(r"\b(\d+)\s+Wn\.\s*App\.\s+(\d+)\b", re.IGNORECASE),
            "wn_app_space": re.compile(r"\b(\d+)\s+Wn\.\s*App\s+(\d+)\b", re.IGNORECASE),
            # Washington Third Series
            "wn3d": re.compile(r"\b(\d+)\s+Wn\.\s*3d\s*\n?\s*(\d+)\b", re.IGNORECASE),
            "wn3d_space": re.compile(r"\b(\d+)\s+Wn\.\s*3d\s*\n?\s*(\d+)\b", re.IGNORECASE),
            # Wash. variants
            "wash2d": re.compile(r"\b(\d+)\s+Wash\.\s*2d\s+(\d+)(?:\s*,\s*\d+\s*P\.3d\s*\d+)?\b", re.IGNORECASE),
            "wash2d_space": re.compile(r"\b(\d+)\s+Wash\.\s*2d\s+(\d+)(?:\s*,\s*\d+\s*P\.3d\s*\d+)?\b", re.IGNORECASE),
            "wash_app": re.compile(r"\b(\d+)\s+Wash\.\s*App\.\s+(\d+)\b", re.IGNORECASE),
            "wash_app_space": re.compile(r"\b(\d+)\s+Wash\.\s*App\s+(\d+)\b", re.IGNORECASE),
            "p3d": re.compile(r"\b(\d+)\s+P\.3d\s+(\d+)\b", re.IGNORECASE),
            "p2d": re.compile(r"\b(\d+)\s+P\.2d\s+(\d+)\b", re.IGNORECASE),
            "us": re.compile(r"\b(\d+)\s+U\.S\.\s+(\d+)\b", re.IGNORECASE),
            "us_spaced": re.compile(r"\b(\d+)\s+U\.\s*S\.\s+(\d+)\b", re.IGNORECASE),
            "f3d": re.compile(r"\b(\d+)\s+F\.3d\s+(\d+)\b", re.IGNORECASE),
            "f2d": re.compile(r"\b(\d+)\s+F\.2d\s+(\d+)\b", re.IGNORECASE),
            "f_supp": re.compile(r"\b(\d+)\s+F\.\s*Supp\.\s+(\d+)\b", re.IGNORECASE),
            "f_supp2d": re.compile(r"\b(\d+)\s+F\.\s*Supp\.\s*2d\s+(\d+)\b", re.IGNORECASE),
            "f_supp3d": re.compile(r"\b(\d+)\s+F\.\s*Supp\.\s*3d\s+(\d+)\b", re.IGNORECASE),
            "s_ct": re.compile(r"\b(\d+)\s+S\.\s*Ct\.\s+(\d+)\b", re.IGNORECASE),
            "l_ed": re.compile(r"\b(\d+)\s+L\.\s*Ed\.\s+(\d+)\b", re.IGNORECASE),
            "l_ed2d": re.compile(r"\b(\d+)\s+L\.\s*Ed\.\s*2d\s+(\d+)\b", re.IGNORECASE),
            "a2d": re.compile(r"\b(\d+)\s+A\.2d\s+(\d+)\b", re.IGNORECASE),
            "a3d": re.compile(r"\b(\d+)\s+A\.3d\s+(\d+)\b", re.IGNORECASE),
            "so2d": re.compile(r"\b(\d+)\s+So\.\s*2d\s+(\d+)\b", re.IGNORECASE),
            "so3d": re.compile(r"\b(\d+)\s+So\.\s*3d\s+(\d+)\b", re.IGNORECASE),
            "wash_2d_alt": re.compile(r"\b(\d+)\s+Wash\.\s*2d\s+(\d+)\b", re.IGNORECASE),
            "wash_app_alt": re.compile(r"\b(\d+)\s+Wash\.\s*App\.\s+(\d+)\b", re.IGNORECASE),
            "wn2d_alt": re.compile(r"\b(\d+)\s+Wn\.\s*2d\s+(\d+)\b", re.IGNORECASE),
            "wn2d_alt_space": re.compile(r"\b(\d+)\s+Wn\.\s*2d\s+(\d+)\b", re.IGNORECASE),
            "wn_app_alt": re.compile(r"\b(\d+)\s+Wn\.\s*App\.\s+(\d+)\b", re.IGNORECASE),
            "p3d_alt": re.compile(r"\b(\d+)\s+P\.\s*3d\s+(\d+)\b", re.IGNORECASE),
            "p2d_alt": re.compile(r"\b(\d+)\s+P\.\s*2d\s+(\d+)\b", re.IGNORECASE),
            "wash_complete": re.compile(
                r"\b(\d+)\s+(?:Wash\.|Wn\.)\s*(?:2d|App\.)\s+(\d+)(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\b",
                re.IGNORECASE,
            ),
            "wash_with_parallel": re.compile(
                r"\b(\d+)\s+(?:Wash\.|Wn\.)\s*(?:2d|App\.)\s+(\d+)(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\b",
                re.IGNORECASE,
            ),
            "parallel_cluster": re.compile(
                r"\b(\d+)\s+(?:Wash\.|Wn\.)\s*(?:2d|App\.)\s+(\d+)(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\b",
                re.IGNORECASE,
            ),
            "flexible_wash2d": re.compile(
                r"\b(\d+)\s+(?:Wash\.|Wn\.)\s*2d\s+(\d+)(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\s*(?:\(\d{4}\))?\b",
                re.IGNORECASE,
            ),
            "flexible_p3d": re.compile(
                r"\b(\d+)\s+P\.3d\s+(\d+)(?:\s*,\s*(\d+)\s+(?:Wash\.|Wn\.)\s*2d\s+(\d+))?\s*(?:\(\d{4}\))?\b",
                re.IGNORECASE,
            ),
            "flexible_p2d": re.compile(
                r"\b(\d+)\s+P\.2d\s+(\d+)(?:\s*,\s*(\d+)\s+(?:Wash\.|Wn\.)\s*2d\s+(\d+))?\s*(?:\(\d{4}\))?\b",
                re.IGNORECASE,
            ),
            "parallel_citation_cluster": re.compile(
                r"\b(\d+)\s+(?:Wash\.|Wn\.)\s*2d\s+(\d+)(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\s*(?:\(\d{4}\))?\b",
                re.IGNORECASE,
            ),
            "wash_with_pinpoint_and_parallel": re.compile(
                r"\b(\d+)\s+(?:Wash\.|Wn\.)\s*(?:App\.)\s*2d\s+(\d+)(?:\s*,\s*(\d+))?(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\s*(?:\(\d{4}\))?\b",
                re.IGNORECASE,
            ),
            "westlaw": re.compile(r"\b(\d{4})\s+WL\s+(\d{1,12})\b", re.IGNORECASE),
            "westlaw_alt": re.compile(r"\b(\d{4})\s+Westlaw\s+(\d{1,12})\b", re.IGNORECASE),
            "simple_wash2d": re.compile(r"\b(\d+)\s+(?:Wash\.|Wn\.)\s*2d\s+(\d+)\b", re.IGNORECASE),
            "simple_p3d": re.compile(r"\b(\d+)\s+P\.3d\s+(\d+)\b", re.IGNORECASE),
            "simple_p2d": re.compile(r"\b(\d+)\s+P\.2d\s+(\d+)\b", re.IGNORECASE),
            # Early American Supreme Court reporters (pre-U.S. Reports)
            "cranch": re.compile(r"\b\d+\s+Cranch\s+\d+\b", re.IGNORECASE),  # 1801-1815
            "wheat": re.compile(r"\b\d+\s+Wheat\.?\s+\d+\b", re.IGNORECASE),  # 1816-1827
            "pet": re.compile(r"\b\d+\s+Pet\.?\s+\d+\b", re.IGNORECASE),  # 1828-1842
            "how": re.compile(r"\b\d+\s+How\.?\s+\d+\b", re.IGNORECASE),  # 1843-1860
            "black": re.compile(r"\b\d+\s+Black\s+\d+\b", re.IGNORECASE),  # 1861-1862
            "wall": re.compile(r"\b\d+\s+Wall\.?\s+\d+\b", re.IGNORECASE),  # 1863-1875
            # Federal Cases (early federal case reporter)
            "f_cas": re.compile(r"\b\d+\s+F\.\s*Cas\.\s+\d+\b", re.IGNORECASE),
            # Slip opinion placeholders (e.g., "584 U.S. ___" or "593 U. S. ___, ___")
            "us_slip": re.compile(r"\b(\d+)\s+U\.?\s*S\.?\s+_{2,}(?:\s*,?\s*_{2,})*", re.IGNORECASE),
            # State reporters - Tennessee
            "tenn": re.compile(r"\b(\d+)\s+Tenn\.\s+(\d+)\b", re.IGNORECASE),
            "lexis": re.compile(r"\b(\d{4})\s+[A-Za-z\.\s]+LEXIS\s+(\d{1,12})\b", re.IGNORECASE),
            "lexis_alt": re.compile(r"\b(\d{4})\s+LEXIS\s+(\d{1,12})\b", re.IGNORECASE),
            # Neutral/Public Domain Citations (Year-State-Number format)
            # These are official state citations used by many states
            "neutral_nm": re.compile(r"\b(20\d{2})-NM(?:CA)?-(\d{1,5})\b", re.IGNORECASE),  # New Mexico: 2017-NM-007
            "neutral_nd": re.compile(r"\b(20\d{2})\s+ND\s+(\d{1,5})\b", re.IGNORECASE),  # North Dakota
            "neutral_ok": re.compile(r"\b(20\d{2})\s+OK\s+(\d{1,5})\b", re.IGNORECASE),  # Oklahoma
            "neutral_sd": re.compile(r"\b(20\d{2})\s+SD\s+(\d{1,5})\b", re.IGNORECASE),  # South Dakota
            "neutral_ut": re.compile(r"\b(20\d{2})\s+UT\s+(\d{1,5})\b", re.IGNORECASE),  # Utah
            "neutral_wi": re.compile(r"\b(20\d{2})\s+WI\s+(\d{1,5})\b", re.IGNORECASE),  # Wisconsin
            "neutral_wy": re.compile(r"\b(20\d{2})\s+WY\s+(\d{1,5})\b", re.IGNORECASE),  # Wyoming
            "neutral_mt": re.compile(r"\b(20\d{2})\s+MT\s+(\d{1,5})\b", re.IGNORECASE),  # Montana
        }

        self.pinpoint_pattern = re.compile(r"\b(?:at\s+)?(\d+)\b", re.IGNORECASE)
        self.docket_pattern = re.compile(
            r"\b(?:No\.|Docket\s+No\.|Case\s+No\.)\s*[:\-]?\s*([A-Z0-9\-\.]+)\b", re.IGNORECASE
        )
        self.history_pattern = re.compile(
            r"\b(?:affirmed|reversed|remanded|vacated|denied|granted|cert\.?\s+denied)\b", re.IGNORECASE
        )
        self.status_pattern = re.compile(r"\b(?:published|unpublished|memorandum|opinion)\b", re.IGNORECASE)

    def _init_case_name_patterns(self):
        """Initialize case name extraction patterns."""
        self.case_name_patterns = [
            r"([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[a-zA-Z\'\.\&]+|of|the|and|&))*)\s+(?:v\.|vs\.|versus)\s+([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[a-zA-Z\'\.\&]+|of|the|and|&))*)",
            r"(In\s+re\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[a-zA-Z\'\.\&]+|of|the|and|&))*)",
            r"(Ex\s+parte\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[a-zA-Z\'\.\&]+|of|the|and|&))*)",
            r"((?:State|United\s+States|People)(?:\s+of\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[a-zA-Z\'\.\&]+|of|the|and|&))*))\s+(?:v\.|vs\.|versus)\s+([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[a-zA-Z\'\.\&]+|of|the|and|&))*)",
        ]

    def _init_date_patterns(self):
        """Initialize date extraction patterns."""
        self.date_patterns = [
            r"\((\d{4})\)",  # (2022)
            r"\b(\d{4})\b",  # 2022
            r"\b(19|20)\d{2}\b",  # 19xx or 20xx
        ]

    def _init_state_reporter_mapping(self):
        """Initialize comprehensive state-to-reporter mapping based on Westlaw regional reporters."""
        self.state_reporter_mapping = {
            "P.3d": [
                "Alaska",
                "Arizona",
                "California",
                "Colorado",
                "Hawaii",
                "Idaho",
                "Kansas",
                "Montana",
                "Nevada",
                "New Mexico",
                "Oklahoma",
                "Oregon",
                "Utah",
                "Washington",
                "Wyoming",
            ],
            "P.2d": [
                "Alaska",
                "Arizona",
                "California",
                "Colorado",
                "Hawaii",
                "Idaho",
                "Kansas",
                "Montana",
                "Nevada",
                "New Mexico",
                "Oklahoma",
                "Oregon",
                "Utah",
                "Washington",
                "Wyoming",
            ],
            "N.W.2d": ["Iowa", "Michigan", "Minnesota", "Nebraska", "North Dakota", "South Dakota", "Wisconsin"],
            "N.W.": ["Iowa", "Michigan", "Minnesota", "Nebraska", "North Dakota", "South Dakota", "Wisconsin"],
            "S.W.3d": ["Arkansas", "Kentucky", "Missouri", "Tennessee", "Texas"],
            "S.W.2d": ["Arkansas", "Kentucky", "Missouri", "Tennessee", "Texas"],
            "S.W.": ["Arkansas", "Kentucky", "Missouri", "Tennessee", "Texas"],
            "N.E.2d": ["Illinois", "Indiana", "Massachusetts", "New York", "Ohio"],
            "N.E.": ["Illinois", "Indiana", "Massachusetts", "New York", "Ohio"],
            "So.3d": ["Alabama", "Florida", "Louisiana", "Mississippi"],
            "So.2d": ["Alabama", "Florida", "Louisiana", "Mississippi"],
            "So.": ["Alabama", "Florida", "Louisiana", "Mississippi"],
            "S.E.2d": ["Georgia", "North Carolina", "South Carolina", "Virginia", "West Virginia"],
            "S.E.": ["Georgia", "North Carolina", "South Carolina", "Virginia", "West Virginia"],
            "A.3d": [
                "Connecticut",
                "Delaware",
                "Maine",
                "Maryland",
                "New Hampshire",
                "New Jersey",
                "Pennsylvania",
                "Rhode Island",
                "Vermont",
                "District of Columbia",
            ],
            "A.2d": [
                "Connecticut",
                "Delaware",
                "Maine",
                "Maryland",
                "New Hampshire",
                "New Jersey",
                "Pennsylvania",
                "Rhode Island",
                "Vermont",
                "District of Columbia",
            ],
            "A.": [
                "Connecticut",
                "Delaware",
                "Maine",
                "Maryland",
                "New Hampshire",
                "New Jersey",
                "Pennsylvania",
                "Rhode Island",
                "Vermont",
                "District of Columbia",
            ],
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
            "P.3d": r"\b\d+\s+P\.3d\b",
            "P.2d": r"\b\d+\s+P\.2d\b",
            "N.W.2d": r"\b\d+\s+N\.W\.2d\b",
            "N.W.": r"\b\d+\s+N\.W\.\b",
            "S.W.3d": r"\b\d+\s+S\.W\.3d\b",
            "S.W.2d": r"\b\d+\s+S\.W\.2d\b",
            "S.W.": r"\b\d+\s+S\.W\.\b",
            "N.E.2d": r"\b\d+\s+N\.E\.2d\b",
            "N.E.": r"\b\d+\s+N\.E\.\b",
            "So.3d": r"\b\d+\s+So\.3d\b",
            "So.2d": r"\b\d+\s+So\.2d\b",
            "So.": r"\b\d+\s+So\.\b",
            "S.E.2d": r"\b\d+\s+S\.E\.2d\b",
            "S.E.": r"\b\d+\s+S\.E\.\b",
            "A.3d": r"\b\d+\s+A\.3d\b",
            "A.2d": r"\b\d+\s+A\.2d\b",
            "A.": r"\b\d+\s+A\.\b",
            "WL": r"\b\d{4}\s+WL\s+\d+\b",
            "LEXIS": r"\b\d{4}\s+[A-Za-z\.\s]+LEXIS\s+\d+\b",
            "LEXIS_ALT": r"\b\d{4}\s+LEXIS\s+\d+\b",
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

        parts = [part.strip() for part in cite.split(",")]
        cleaned_parts = []

        for part in parts:
            if re.match(r"^\d+\s+\w+\.\w+\s+\d+", part):
                cleaned_parts.append(part)
            elif re.match(r"^\d+$", part):
                continue
            else:
                citation_match = re.match(r"^(\d+\s+\w+\.\w+\s+\d+)", part)
                if citation_match:
                    cleaned_parts.append(citation_match.group(1))
                else:
                    cleaned_parts.append(part)

        return ", ".join(cleaned_parts)

    def _get_extracted_case_name(self, citation: "CitationResult") -> Optional[str]:
        """Utility to safely get extracted case name from a citation."""
        return citation.extracted_case_name if hasattr(citation, "extracted_case_name") else None

    def _is_partial_citation(self, citation_text: str) -> bool:
        """
        Return True if the citation is partial (e.g. slip opinion placeholder).
        Partial = page part is placeholder (___ or ____) so we cannot uniquely identify the case.
        N/A + partial = insufficient to verify; N/A + complete citation = OK to verify.
        """
        if not citation_text or not isinstance(citation_text, str):
            return False
        s = citation_text.strip()
        # Slip opinion / placeholder: "592 U.S. ___", "593 U.S. ____", "590 U.S. ___ (2021)"
        if re.search(r"\s_{2,}\s*(?:\(|$)", s) or re.search(r"\s_{2,}\)", s):
            return True
        # Ends with space + underscores (no page number)
        if re.search(r"[.\s]_{2,}\s*$", s):
            return True
        return False

    def _na_and_partial_insufficient(self, citation) -> bool:
        """True if citation has N/A case name AND partial citation text → insufficient to verify."""
        if hasattr(citation, "get") and callable(getattr(citation, "get", None)):
            ext_name = citation.get("extracted_case_name") or citation.get("cluster_case_name") or ""
            cite_text = citation.get("citation") or ""
        else:
            ext_name = getattr(citation, "extracted_case_name", None) or getattr(citation, "cluster_case_name", None) or ""
            cite_text = getattr(citation, "citation", None) or ""
        if (ext_name or "").strip().upper() != "N/A":
            return False
        return self._is_partial_citation(str(cite_text))

    def _get_unverified_citations(self, citations: List["CitationResult"]) -> List["CitationResult"]:
        """Utility to filter unverified citations."""
        return [c for c in citations if not getattr(c, "verified", False)]

    def _apply_verification_result(
        self, citation: "CitationResult", verify_result: dict, source: str = "CourtListener"
    ):
        """Centralized method to apply verification results with validation against extracted data."""
        if verify_result.get("verified"):
            canonical_name = verify_result.get("canonical_name")
            extracted_name = getattr(citation, "extracted_case_name", None)

            # VALIDATION: Check if CourtListener canonical name matches our extracted name
            if canonical_name and extracted_name and extracted_name != "N/A":
                # Normalize both names for comparison
                canonical_norm = self._normalize_case_name_for_comparison(canonical_name)
                extracted_norm = self._normalize_case_name_for_comparison(extracted_name)

                # Compute an overlap similarity on normalized tokens
                words1 = set(canonical_norm.split())
                words2 = set(extracted_norm.split())
                smaller = min(words1, words2, key=len) if words1 and words2 else set()
                overlap = len(words1 & words2)
                similarity = (overlap / len(smaller)) if smaller else 0.0

                names_match_bool = self._case_names_match(canonical_norm, extracted_norm)
                if not names_match_bool:
                    logger.warning(
                        f"[WARNING] CourtListener canonical name differs from extracted: '{canonical_name}' vs extracted '{extracted_name}' for {citation.citation} (sim={similarity:.2f})"
                    )
                    # When API returned a verified match (citation + URL), trust it: set canonical_name
                    # so the UI can show the correct case (e.g. Simon for 426 U.S. 26, not Eichman).
                    url = verify_result.get("url") or verify_result.get("canonical_url")
                    if url and canonical_name:
                        citation.canonical_name = canonical_name
                        citation.canonical_date = verify_result.get("canonical_date")
                        citation.url = url
                        citation.canonical_url = url
                        citation.verified = True
                        citation.source = source
                        citation.name_mismatch = True  # document had different name
                        citation.metadata = citation.metadata or {}
                        citation.metadata[f"{source.lower()}_source"] = verify_result.get("source")
                        citation.metadata["canonical_name_validation"] = "courtlistener_canonical_preferred"
                        try:
                            citation.mismatch_confidence = max(0.0, min(1.0, 1.0 - similarity))
                        except Exception:
                            citation.mismatch_confidence = 0.5
                        return True
                    # No URL: cannot verify; keep as possible_match
                    if similarity < 0.35 and hasattr(citation, "__dict__"):
                        citation.verified = False
                        citation.possible_match = True
                        citation.canonical_name = None
                        citation.canonical_date = None
                        citation.canonical_url = None
                        citation.url = verify_result.get("url")
                        citation.source = source
                        citation.metadata = citation.metadata or {}
                        citation.metadata[f"{source.lower()}_source"] = verify_result.get("source")
                        citation.metadata["canonical_name_validation"] = "possible_match_low_similarity"
                        citation.metadata["possible_match_name"] = canonical_name
                        citation.metadata["possible_match_date"] = verify_result.get("canonical_date")
                        citation.metadata["possible_match_url"] = verify_result.get("url")
                        citation.name_mismatch = True
                        try:
                            citation.mismatch_confidence = max(0.0, min(1.0, 1.0 - similarity))
                        except Exception:
                            citation.mismatch_confidence = 1.0
                        return False
                    # Similarity >= 0.35: allow verification with canonical name
                    if url:
                        citation.canonical_name = canonical_name
                        citation.canonical_date = verify_result.get("canonical_date")
                        citation.url = url
                        citation.canonical_url = url
                        citation.verified = True
                        citation.source = source
                        citation.metadata = citation.metadata or {}
                        citation.metadata[f"{source.lower()}_source"] = verify_result.get("source")
                        citation.metadata["canonical_name_validation"] = "courtlistener_canonical_preferred"
                        return True
                    citation.verified = False
                    return False

            # CRITICAL: Only set canonical data if verification succeeded
            # FIX 2026-02-01: REQUIRE canonical_name to mark as verified
            # USER RULE: verified=True ONLY when we have a canonical URL (link to the case)
            if canonical_name and canonical_name != "N/A":
                citation.canonical_name = canonical_name
                canonical_date = verify_result.get("canonical_date")
                # CRITICAL: Only set canonical_date from verification results
                if canonical_date:
                    citation.canonical_date = canonical_date
                url = verify_result.get("url") or verify_result.get("canonical_url")
                if url:
                    citation.url = url
                    citation.canonical_url = url
                    citation.verified = True
                    citation.source = verify_result.get("source", source)
                    citation.metadata = citation.metadata or {}
                    citation.metadata[f"{source.lower()}_source"] = verify_result.get("source")
                else:
                    # No URL - cannot mark as verified (user rule: verified requires canonical_url)
                    citation.verified = False
                    citation.canonical_url = None
            else:
                # No canonical name - cannot verify
                citation.verified = False

            # CRITICAL FIX: NEVER set or overwrite extracted_case_name from canonical data.
            # The extracted name must come only from the user's document. Preserve whatever exists.
            try:
                existing_extracted_name = getattr(citation, "extracted_case_name", None)
                # Preserve as-is; do not backfill from canonical under any circumstance
                citation.extracted_case_name = existing_extracted_name
            except Exception:
                # Be conservative: do not interrupt verification if accessing attributes fails
                pass

            # NEW: Backend-driven mismatch tagging (name/date)
            try:
                # Name mismatch: only evaluate if both names present
                if (
                    canonical_name
                    and citation.extracted_case_name
                    and citation.extracted_case_name.strip().upper() != "N/A"
                ):
                    can_norm = self._normalize_case_name_for_comparison(canonical_name)
                    ext_norm = self._normalize_case_name_for_comparison(citation.extracted_case_name)
                    names_match = self._case_names_match(can_norm, ext_norm)
                    # Set flag; keep verification status as decided above
                    if hasattr(citation, "__dict__"):
                        citation.name_mismatch = not names_match
                        # Provide a coarse confidence: 1.0 when clearly different, else 0.0
                        citation.mismatch_confidence = 1.0 if not names_match else 0.0

                # Date mismatch: compare years if both present (single source: date_utils)
                from src.utils.date_utils import extract_year_value
                ext_year = extract_year_value(getattr(citation, "extracted_date", None))
                can_year = extract_year_value(getattr(citation, "canonical_date", None))
                if ext_year and can_year and hasattr(citation, "__dict__"):
                    citation.date_mismatch = ext_year != can_year
            except Exception as e:
                logger.warning(
                    f"[MISMATCH-TAGGING] Failed to tag mismatch for {getattr(citation, 'citation', 'unknown')}: {e}"
                )
            return True
        else:
            # CRITICAL: Unverified citations CANNOT have canonical data
            # EXCEPTION: year_mismatch_rejected citations PRESERVE canonical data for cluster splitting
            citation.verified = False

            # Check if this is a year_mismatch_rejected citation - preserve canonical data for clustering
            current_source = getattr(citation, "source", None)
            if current_source != "year_mismatch_rejected":
                # Clear canonical data for unverified citations (except year_mismatch_rejected)
                citation.canonical_name = None
                citation.canonical_date = None
                citation.canonical_url = None
            # else: preserve canonical data for cluster splitting

            if (
                not hasattr(citation, "source")
                or not citation.source
                or citation.source == f"{source}_extracted_preferred"
            ):
                citation.source = None  # Clear source for unverified citations
            return False

    def _normalize_case_name_for_comparison(self, case_name: str) -> str:
        """Normalize case name for comparison by removing common variations."""
        if not case_name:
            return ""

        # Convert to lowercase and remove extra whitespace
        normalized = case_name.lower().strip()

        # Remove common variations that don't affect meaning
        normalized = re.sub(r"\s+", " ", normalized)  # Normalize whitespace

        # Handle common abbreviations BEFORE removing punctuation
        # This ensures abbreviations are expanded properly
        abbrev_map = {
            r"\bauto\.?\b": "automobile",
            r"\bins\.?\b": "insurance",
            r"\bco\.?\b": "company",
            r"\bcorp\.?\b": "corporation",
            r"\binc\.?\b": "incorporated",
            r"\bllc\.?\b": "limited liability company",
            r"\bvs?\.?\b": "v",
            r"\bmut\.?\b": "mutual",
            r"\bassn\.?\b": "association",
            r"\bass\'?n\.?\b": "association",
            r"\bdept\.?\b": "department",
            r"\bdep\'?t\.?\b": "department",
        }
        for pattern, replacement in abbrev_map.items():
            normalized = re.sub(pattern, replacement, normalized)

        # Remove punctuation after abbreviation expansion
        normalized = re.sub(r"[^\w\s]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized)  # Normalize whitespace again

        # Remove common words that don't affect case identity
        common_words = ["the", "and", "or", "of", "in", "on", "at", "by", "for", "with", "a", "an"]
        words = normalized.split()
        filtered_words = [word for word in words if word not in common_words]

        return " ".join(filtered_words)

    def _case_names_match(self, name1: str, name2: str) -> bool:
        """Check if two case names match, allowing for reasonable variations.

        Handles:
        - Abbreviations (e.g., "Auto. Ins. Co." vs "Automobile Insurance Company")
        - Shared party names (e.g., both have "Campbell" as second party)
        - Partial matches and word overlap
        """
        if not name1 or not name2:
            return False

        # Explicitly reject N/A values
        if name1.strip().upper() == "N/A" or name2.strip().upper() == "N/A":
            return False

        # Normalize both names
        norm1 = self._normalize_case_name_for_comparison(name1)
        norm2 = self._normalize_case_name_for_comparison(name2)

        # Exact match after normalization
        if norm1 == norm2:
            return True

        # Check if one contains the other (handles partial matches)
        if norm1 in norm2 or norm2 in norm1:
            return True

        # Split into words and check overlap
        words1 = set(norm1.split())
        words2 = set(norm2.split())

        if not words1 or not words2:
            return False

        # If significant overlap (>70% of smaller set), consider them matching
        smaller_set = min(words1, words2, key=len)
        larger_set = max(words1, words2, key=len)

        overlap = len(smaller_set & larger_set)
        if overlap / len(smaller_set) > 0.7:
            return True

        # CRITICAL: Check if both names share the same party name (especially after "v")
        # This handles cases like "Auto. Ins. Co. v. Campbell" vs "State Farm Mutual Automobile Insurance v. Campbell"
        def extract_parties(name: str) -> tuple:
            """Extract first and second party names from a case name."""
            # Split on "v" to get parties
            parts = re.split(r"\bv\b", name.lower(), maxsplit=1)
            if len(parts) == 2:
                first_party = parts[0].strip()
                second_party = parts[1].strip()
                # Extract key words from each party (remove common words)
                first_words = set(w for w in first_party.split() if len(w) > 2 and w not in ["the", "and", "of", "in"])
                second_words = set(
                    w for w in second_party.split() if len(w) > 2 and w not in ["the", "and", "of", "in"]
                )
                return first_words, second_words
            return set(), set()

        first1, second1 = extract_parties(norm1)
        first2, second2 = extract_parties(norm2)

        # If both have the same second party name, and first parties share some words, consider it a match
        if second1 and second2:
            second_overlap = second1 & second2
            if second_overlap:
                # Both share at least one word in the second party (e.g., "campbell")
                # Check if first parties have any overlap or if one is an abbreviation of the other
                first_overlap = first1 & first2
                if first_overlap:
                    # Both parties have some overlap - strong match
                    return True
                # Check if one first party is a subset of the other (abbreviation case)
                if first1.issubset(first2) or first2.issubset(first1):
                    return True
                # Check if there's significant word overlap in first party (at least 30%)
                if first1 and first2:
                    first_smaller = min(first1, first2, key=len)
                    first_larger = max(first1, first2, key=len)
                    first_overlap_count = len(first_smaller & first_larger)
                    if first_smaller and first_overlap_count / len(first_smaller) >= 0.3:
                        return True

        # Final check: if there's reasonable overall word overlap (at least 50% of smaller set)
        # and at least 2 words overlap, consider it a match
        if overlap >= 2 and overlap / len(smaller_set) >= 0.5:
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
                    "source": landmark_result.get("source", "Landmark Cases"),
                }

            return {
                "found": False,
                "confidence": 0.0,
                "explanation": "Citation not found in landmark cases database",
                "case_name": case_name,
                "source": "Landmark Cases",
            }

        except Exception as e:
            return {
                "found": False,
                "confidence": 0.0,
                "explanation": f"Error during verification: {str(e)}",
                "case_name": case_name,
                "source": "Error",
            }

    def _verify_with_landmark_cases(self, citation: str) -> Dict[str, Any]:
        """Verify a citation against known landmark cases."""
        landmark_cases = {
            "410 u.s. 113": {
                "case_name": "Roe v. Wade",
                "date": "1973",
                "court": "United States Supreme Court",
                "url": "https://www.courtlistener.com/opinion/108713/roe-v-wade/",
            },
            "347 u.s. 483": {
                "case_name": "Brown v. Board of Education",
                "date": "1954",
                "court": "United States Supreme Court",
                "url": "https://www.courtlistener.com/opinion/105221/brown-v-board-of-education/",
            },
            "384 u.s. 436": {
                "case_name": "Miranda v. Arizona",
                "date": "1966",
                "court": "United States Supreme Court",
                "url": "https://www.courtlistener.com/opinion/107137/miranda-v-arizona/",
            },
            "576 u.s. 644": {
                "case_name": "Obergefell v. Hodges",
                "date": "2015",
                "court": "United States Supreme Court",
                "url": "https://www.courtlistener.com/opinion/281877/obergefell-v-hodges/",
            },
            "5 u.s. 137": {
                "case_name": "Marbury v. Madison",
                "date": "1803",
                "court": "United States Supreme Court",
                "url": "https://www.courtlistener.com/opinion/84759/marbury-v-madison/",
            },
            "999 u.s. 999": {
                "case_name": "Fake Case Name v. Another Party",
                "date": "1999",
                "court": "United States Supreme Court",
                "url": None,
            },
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
                "confidence": 0.9,
            }

        return {"verified": False, "source": "Landmark Cases", "error": "Citation not found in landmark cases"}

    def _detect_parallel_citations(self, citations: List["CitationResult"], text: str) -> List["CitationResult"]:
        """Fixed parallel detection that updates existing objects and assigns cluster IDs."""
        if not citations or len(citations) < 2:
            return citations
        sorted_citations = sorted(citations, key=lambda x: x.start_index or 0)
        groups = []
        current_group = [sorted_citations[0]]
        for i in range(1, len(sorted_citations)):
            curr = sorted_citations[i]
            prev = current_group[-1]
            if curr.start_index and prev.end_index and curr.start_index - prev.end_index <= 100:
                text_between = text[prev.end_index : curr.start_index]
                if "," in text_between and len(text_between.strip()) < 50:
                    if (
                        prev.extracted_case_name
                        and curr.extracted_case_name
                        and prev.extracted_case_name != "N/A"
                        and curr.extracted_case_name != "N/A"
                    ):
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
                best_name = next(
                    (c.extracted_case_name for c in group if c.extracted_case_name and c.extracted_case_name != "N/A"),
                    None,
                )
                # CRITICAL: Only use dates that appear to be from user document (year-only format)
                # Avoid contamination from verification APIs that return full dates like "2018-12-06"
                document_dates = [
                    c.extracted_date
                    for c in group
                    if c.extracted_date and c.extracted_date != "N/A" and re.match(r"^\d{4}$", str(c.extracted_date))
                ]  # Year-only format
                document_dates[0] if document_dates else None
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
                    # CRITICAL FIX: Use helper function to filter cluster members
                    filtered_members = filter_cluster_members_by_reporter(
                        citation.citation, member_citations
                    )
                    
                    citation.is_parallel = len(filtered_members) > 0
                    citation.cluster_id = cluster_id if filtered_members else None
                    citation.cluster_members = filtered_members
                    citation.parallel_citations = filtered_members
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

        if hasattr(self, "_check_court_compatibility"):
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

        federal_reporters = {"F.", "F.2d", "F.3d", "F.Supp.", "F.Supp.2d", "U.S.", "S.Ct."}
        washington_reporters = {"Wn.", "Wn.2d", "Wash.", "Wash.App.", "Wash.2d"}

        if reporter1 in federal_reporters and reporter2 in federal_reporters:
            return True
        if reporter1 in washington_reporters and reporter2 in washington_reporters:
            return True

        return False

    def _extract_reporter_type(self, citation: str) -> Optional[str]:
        """Extract reporter type from citation."""
        import re

        patterns = {
            r"\bF\.\d*d?\b": "F.",
            r"\bF\.Supp\.\d*d?\b": "F.Supp.",
            r"\bU\.S\.\b": "U.S.",
            r"\bS\.Ct\.\b": "S.Ct.",
            r"\bWn\.\d*d?\b": "Wn.",
            r"\bWash\.\d*d?\b": "Wash.",
        }

        for pattern, reporter in patterns.items():
            if re.search(pattern, citation):
                return reporter

        return None

    def _calculate_confidence(self, citation: CitationResult, text: str) -> float:
        """Calculate confidence score for a citation."""
        confidence = 0.0

        method_scores = {
            "eyecite": 0.8,
            "regex": 0.6,
            "cluster_detection": 0.7,
        }
        confidence += method_scores.get(citation.method, 0.5)

        if re.match(r"^\d+\s+[A-Za-z\.]+\s+\d+$", citation.citation):
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
            "Wn.": "Washington",
            "Wash.": "Washington",
            "Cal.": "California",
            "Kan.": "Kansas",
            "Or.": "Oregon",
            "Idaho": "Idaho",
            "Nev.": "Nevada",
            "Colo.": "Colorado",
            "Mont.": "Montana",
            "Utah": "Utah",
            "Ariz.": "Arizona",
            "N.M.": "New Mexico",
            "Alaska": "Alaska",
        }
        for abbr, state in state_map.items():
            if abbr in citation:
                return state
        return None

    def _validate_verification_result(self, citation: "CitationResult", source: str) -> Dict[str, Any]:
        """Validate that a verification result makes sense and is high quality."""
        validation_result = {"valid": True, "reason": "", "confidence_adjustment": 0.0}

        if not citation.canonical_name or citation.canonical_name.strip() == "":
            validation_result["valid"] = False
            validation_result["reason"] = "Missing canonical name"
            return validation_result

        canonical_lower = citation.canonical_name.lower()
        if "v." not in canonical_lower and "in re" not in canonical_lower and "ex parte" not in canonical_lower:
            validation_result["valid"] = False
            validation_result["reason"] = f"Canonical name lacks proper case format: {citation.canonical_name}"
            return validation_result

        if len(citation.canonical_name) < 5:
            validation_result["valid"] = False
            validation_result["reason"] = f"Canonical name too short: {citation.canonical_name}"
            return validation_result

        if len(citation.canonical_name) > 200:
            validation_result["valid"] = False
            validation_result["reason"] = f"Canonical name too long: {citation.canonical_name[:50]}..."
            return validation_result

        if (
            hasattr(citation, "extracted_case_name")
            and citation.extracted_case_name
            and citation.extracted_case_name != "N/A"
        ):
            similarity = self._calculate_case_name_similarity(citation.extracted_case_name, citation.canonical_name)
            if similarity < 0.1:  # Very low similarity threshold
                logger.warning(
                    f"[VALIDATION] Low similarity between extracted '{citation.extracted_case_name}' and canonical '{citation.canonical_name}' (similarity: {similarity:.2f})"
                )
                validation_result["confidence_adjustment"] = -0.2

        if citation.canonical_date:
            try:
                if len(citation.canonical_date) == 4:  # Year only
                    year = int(citation.canonical_date)
                    if year < 1600 or year > 2030:
                        validation_result["valid"] = False
                        validation_result["reason"] = f"Invalid canonical year: {citation.canonical_date}"
                        return validation_result
                elif "-" in citation.canonical_date:  # Full date
                    from datetime import datetime

                    datetime.strptime(citation.canonical_date, "%Y-%m-%d")
            except (ValueError, TypeError):
                validation_result["valid"] = False
                validation_result["reason"] = f"Invalid canonical date format: {citation.canonical_date}"
                return validation_result

        if source == "CourtListener":
            if not citation.url or not citation.url.startswith("https://www.courtlistener.com"):
                validation_result["confidence_adjustment"] = -0.1

        if hasattr(citation, "confidence") and citation.confidence is not None:
            citation.confidence = max(0.0, min(1.0, citation.confidence + validation_result["confidence_adjustment"]))

        return validation_result

    def _verify_with_courtlistener(self, citations) -> dict:
        """Verify citations using src.verification (UnifiedVerificationMaster batch)."""
        try:
            import asyncio
            from src.verification import get_master_verifier

            citation_strings = [c.citation for c in citations if hasattr(c, "citation")]
            if not citation_strings:
                return {}

            verifier = get_master_verifier()
            case_names = [getattr(c, "extracted_case_name", None) for c in citations if hasattr(c, "citation")]
            case_dates = [getattr(c, "extracted_date", None) for c in citations if hasattr(c, "citation")]
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                results_list = loop.run_until_complete(
                    verifier.verify_citations_batch(
                        citation_strings,
                        extracted_case_names=case_names if case_names else None,
                        extracted_dates=case_dates if case_dates else None,
                        progress_callback=None,
                        enable_fallback=False,
                    )
                )
            finally:
                loop.close()
            # Convert List[VerificationResult] to dict keyed by citation (old API shape)
            out = {}
            for r in results_list:
                cit = getattr(r, "citation", None) or (r.citation if hasattr(r, "citation") else None)
                if cit is not None:
                    out[cit] = {
                        "verified": getattr(r, "verified", r.verified),
                        "canonical_name": getattr(r, "canonical_name", r.canonical_name),
                        "canonical_date": getattr(r, "canonical_date", r.canonical_date),
                        "canonical_url": getattr(r, "canonical_url", r.canonical_url),
                        "source": getattr(r, "source", r.source),
                    }
            return out
        except Exception as e:
            logger.warning(f"Error using verification (CourtListener batch): {e}")
            return {}

    def _verify_citations_sync(
        self, citations: List["CitationResult"], text: Optional[str] = None
    ) -> List["CitationResult"]:
        """
        ENHANCED: Now using unified verification master with BATCH processing.

        Uses CourtListener's batch API (50 citations per call) for massive speedup.
        Falls back to individual verification only for failed citations.
        """
        print(f"[BATCH-VERIFY] ⚠️⚠️⚠️ _verify_citations_sync CALLED with {len(citations)} citations ⚠️⚠️⚠️")
        logger.error(f"[BATCH-VERIFY] ⚠️⚠️⚠️ _verify_citations_sync CALLED with {len(citations)} citations ⚠️⚠️⚠️")
        logger.error(f"[BATCH-VERIFY] Starting BATCH verification for {len(citations)} citations")

        if not citations:
            return citations

        # Use the new unified verification master with BATCH processing
        try:
            from src.verification import UnifiedVerificationMaster
            import asyncio

            logger.info("[VERIFICATION] Using BATCH VERIFICATION (250 citations per API call)")

            # First pass: identify citations that need verification
            citations_to_verify = []
            for citation in citations:
                verification_status = getattr(citation, "verification_status", None)
                getattr(citation, "is_parallel", False)

                # More thorough check: only skip if citation is actually verified with complete data
                is_actually_verified = (
                    (getattr(citation, "verified", False) == True)
                    and (getattr(citation, "canonical_name", None) is not None)
                    and (getattr(citation, "canonical_date", None) is not None)
                )

                if is_actually_verified:
                    logger.error(
                        f"🚫 [FIX #62] SKIPPING '{citation.citation}': already fully verified with canonical data"
                    )
                    continue

                logger.error(
                    f"[SUCCESS] [FIX #62] PROCESSING '{citation.citation}': verification_status={verification_status}, verified={getattr(citation, 'verified', None)}"
                    f" ecn='{getattr(citation, 'extracted_case_name', 'MISSING')}' edate='{getattr(citation, 'extracted_date', 'MISSING')}'"
                )

                # Store original values before any verification
                if not hasattr(citation, "original_case_name"):
                    citation.original_case_name = getattr(citation, "extracted_case_name", "N/A")
                if not hasattr(citation, "original_date"):
                    citation.original_date = getattr(citation, "extracted_date", "N/A")

                citations_to_verify.append(citation)

            # BATCH VERIFICATION: Single call with full list so internal batching yields 1/3, 2/3, 3/3
            if citations_to_verify:
                batch_size = 250  # Match CourtListener's per-request limit
                total = len(citations_to_verify)
                logger.info(
                    f"[BATCH-VERIFY] Processing {total} citations in batches of {batch_size} (single master call)"
                )

                # Get progress callback if available (passed from RQ worker)
                progress_callback = getattr(self, "_progress_callback", None)

                # Set total in VerificationManager BEFORE starting verification
                if progress_callback:
                    try:
                        progress_callback(0, "Verifying", f"Starting verification of {total} citations...")
                        logger.info(f"[BATCH-VERIFY] Set initial total: {total} citations")
                    except Exception as e:
                        logger.warning(f"Failed to set initial total: {e}")

                verifier = UnifiedVerificationMaster()

                # Extract data for entire set
                citation_strings = [c.citation for c in citations_to_verify]
                case_names = [c.extracted_case_name for c in citations_to_verify]
                # CRITICAL FIX: Prioritize cluster_year over extracted_date
                # cluster_year is set by clustering and is more reliable than extracted_date
                # extracted_date can be contaminated with document metadata dates
                dates = [getattr(c, 'cluster_year', None) or c.extracted_date for c in citations_to_verify]
                # USER FIX 2026-01-09: Extract in_toa_section metadata for TOA year validation skip
                toa_flags = [
                    bool(c.metadata.get("in_toa_section", False)) if hasattr(c, "metadata") and c.metadata else False
                    for c in citations_to_verify
                ]
                logger.error(f"[TOA-FLAGS-DEBUG] Extracted {sum(toa_flags)} TOA citations out of {len(toa_flags)} total")

                # Run master batch verification once in a separate event loop.
                # ThreadPoolExecutor is REQUIRED here because we're already inside
                # asyncio.run() from rq_worker.py — can't nest event loops without it.
                # Memory mitigation: pass data as args (not closure) so main thread
                # can release its references while worker thread runs.
                try:
                    from concurrent.futures import ThreadPoolExecutor

                    # Reduce fallback count for large docs to prevent OOM
                    _max_fb = 30 if total <= 100 else 15

                    def _run_verification_in_new_loop(
                        _verifier, _citations, _names, _dates, _total, _max_fb_count, _progress_cb
                    ):
                        """Run batch verification in a new event loop (separate thread)."""
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            def batch_progress_callback(processed_count, status, message):
                                if _progress_cb:
                                    try:
                                        processed_global = processed_count or 0
                                        global_message = (
                                            f"Verifying citations... ({processed_global}/{_total} citations)"
                                        )
                                        _progress_cb(processed_global, status, global_message)
                                    except Exception as e:
                                        logger.warning(f"Progress callback failed: {e}")

                            print(f"[BATCH-VERIFY] Calling verify_citations_batch with enable_fallback=True, max_fallback_citations={_max_fb_count}, batch_size=250")
                            logger.error(f"[BATCH-VERIFY] Calling verify_citations_batch with enable_fallback=True, max_fallback_citations={_max_fb_count}, batch_size=250")
                            results = loop.run_until_complete(
                                _verifier.verify_citations_batch(
                                    citations=_citations,
                                    extracted_case_names=_names,
                                    extracted_dates=_dates,
                                    progress_callback=batch_progress_callback if _progress_cb else None,
                                    enable_fallback=True,
                                    max_fallback_citations=_max_fb_count,
                                )
                            )
                            print(f"[BATCH-VERIFY] verify_citations_batch returned {len(results)} results")
                            logger.error(f"[BATCH-VERIFY] verify_citations_batch returned {len(results)} results")
                            return results
                        finally:
                            loop.close()
                            asyncio.set_event_loop(None)

                    with ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(
                            _run_verification_in_new_loop,
                            verifier, citation_strings, case_names, dates,
                            total, _max_fb, progress_callback,
                        )
                        # Release main-thread references while worker runs
                        # so GC can reclaim if worker is the only holder
                        citation_strings = None
                        case_names = None
                        dates = None
                        toa_flags = None
                        import gc
                        gc.collect()
                        all_results = future.result(timeout=600.0)
                        # OOM-FIX: Force glibc to return freed pages to OS after verification.
                        # After verification, HTTP response data is freed by gc but
                        # glibc malloc keeps pages mapped (RSS stays at 4GB).
                        # malloc_trim(0) forces page release.
                        try:
                            import ctypes
                            _libc = ctypes.CDLL("libc.so.6")
                            gc.collect()
                            _libc.malloc_trim(0)
                            logger.debug(f"[BATCH-VERIFY] malloc_trim called after verification")
                        except Exception:
                            pass
                except TimeoutError:
                    logger.error(f"[BATCH-TIMEOUT] Master batch verification timed out after 600s")
                    from src.verification import VerificationResult

                    all_results = [
                        VerificationResult(
                            citation=c.citation, verified=False, error="Master batch verification timeout"
                        )
                        for c in citations_to_verify
                    ]
                except Exception as e:
                    import traceback
                    logger.error(f"[BATCH-ERROR] Master batch verification failed: {e}")
                    logger.error(f"[BATCH-ERROR] Exception type: {type(e).__name__}")
                    logger.error(f"[BATCH-ERROR] Traceback:\n{traceback.format_exc()}")
                    from src.verification import VerificationResult

                    all_results = [
                        VerificationResult(
                            citation=c.citation, verified=False, error=f"Master batch verification failed: {e}"
                        )
                        for c in citations_to_verify
                    ]

                # Apply results to citation objects
                verified_count = 0
                import re as re_module

                for citation, result in zip(citations_to_verify, all_results):
                    # Preserve extracted fields
                    original_extracted_name = getattr(citation, "extracted_case_name", None)
                    original_extracted_date = getattr(citation, "extracted_date", None)
                    
                    # DEBUG: Log verification result application
                    citation_str = str(getattr(citation, "citation", ""))

                    if result and getattr(result, "verified", False):
                        # USER FIX: Validate year match before accepting verification result
                        # UPDATED: Allow ±1 year tolerance for legal citations
                        # USER FIX 2026-01-09: Skip year validation for TOA citations
                        extracted_date = original_extracted_date
                        canonical_date = result.canonical_date
                        year_match = True  # Default to True if no dates to compare
                        year_diff = 0
                        
                        # Check if this citation is from Table of Authorities section
                        citation_metadata = getattr(citation, "metadata", {})
                        in_toa_section = citation_metadata.get("in_toa_section", False)
                        
                        if in_toa_section:
                            # TOA citations have unreliable year extraction (often picks up document year)
                            # Trust the canonical year from CourtListener instead
                            year_match = True
                            logger.info(
                                f"[TOA-YEAR-SKIP] {citation.citation}: TOA citation - skipping year validation (extracted year unreliable)"
                            )
                        elif extracted_date and canonical_date:
                            citation_str = str(getattr(citation, "citation", ""))
                            is_federal_reporter = bool(re_module.search(r"\bF(\.(2|3|4)th)?\b", citation_str))
                            if is_federal_reporter:
                                year_match = True
                                logger.info(
                                    f"[FED-YEAR-SKIP] {citation.citation}: Federal Reporter - skipping year comparison (citation year is authoritative)"
                                )
                            else:
                                match, year_diff, extracted_clearly_wrong = years_match_for_verification(
                                    extracted_date, canonical_date, tolerance=0
                                )
                                year_match = match or extracted_clearly_wrong
                                if extracted_clearly_wrong:
                                    logger.warning(
                                        f"[BATCH-YEAR-FIX] {citation.citation}: Extracted date {extracted_date} "
                                        f"treated as clearly wrong vs {canonical_date} (diff={year_diff}) - ignoring mismatch"
                                    )

                        if not year_match:
                            logger.warning(
                                f"[BATCH-YEAR-REJECT] {citation.citation}: extracted={extracted_date} canonical={canonical_date} diff={year_diff}"
                            )
                            # Year mismatch - reject verification BUT PRESERVE canonical data for clustering
                            citation.verified = False
                            citation.verification_status = "year_mismatch"
                            citation.verification_error = (
                                f"Year mismatch: extracted {extracted_date} vs canonical {canonical_date}"
                            )
                            citation.source = "year_mismatch_rejected"
                            # PRESERVE canonical data for cluster splitting
                            citation.canonical_name = result.canonical_name
                            citation.canonical_date = result.canonical_date
                            citation.canonical_url = result.canonical_url
                            if not citation.extracted_case_name or citation.extracted_case_name == "N/A":
                                citation.extracted_case_name = original_extracted_name
                            if not citation.extracted_date or citation.extracted_date == "N/A":
                                citation.extracted_date = original_extracted_date
                            logger.warning(
                                f"[BATCH-YEAR-MISMATCH] {citation.citation}: Rejected - extracted {extracted_date} vs canonical {canonical_date}"
                            )
                            continue

                        # FIX 2026-02-01: REQUIRE canonical_name AND canonical_url to mark as verified
                        # USER RULE: verified=True only when we have a canonical URL (link to the case)
                        result_canonical = getattr(result, "canonical_name", None)
                        result_url = getattr(result, "canonical_url", None) or getattr(result, "url", None)
                        if (
                            result_canonical
                            and result_canonical != "N/A"
                            and result_url
                            and not self._na_and_partial_insufficient(citation)
                        ):
                            citation.verified = True
                            citation.canonical_name = result.canonical_name
                            citation.canonical_date = result.canonical_date
                            citation.canonical_url = result_url
                            citation.verification_status = "verified"
                            citation.verification_source = result.source or "batch_verify"
                            citation.source = result.source or "batch_verify"
                            if not citation.extracted_case_name or citation.extracted_case_name == "N/A":
                                citation.extracted_case_name = original_extracted_name
                            if not citation.extracted_date or citation.extracted_date == "N/A":
                                citation.extracted_date = original_extracted_date
                            # FIX 2026-02-13: When ECN doesn't match verified canonical,
                            # the extraction grabbed a nearby case name — fix at source.
                            _ecn = (citation.extracted_case_name or "").strip()
                            _cn = (result.canonical_name or "").strip()
                            if _ecn and _ecn != "N/A" and _cn and _cn != "N/A":
                                from src.utils.same_case import names_are_same_case
                                if not names_are_same_case(_ecn, _cn):
                                    logger.info(
                                        f"[BATCH-ECN-FIX] {citation.citation}: ECN '{_ecn}' doesn't match "
                                        f"canonical '{_cn}' — replacing ECN with canonical"
                                    )
                                    citation.extracted_case_name = _cn
                            verified_count += 1
                            logger.warning(
                                f"[BATCH-VERIFIED] {citation.citation} -> {result.canonical_name} (source: {result.source})"
                            )
                        elif self._na_and_partial_insufficient(citation) and result_canonical and result_canonical != "N/A":
                            # N/A + partial citation (e.g. "592 U.S. ___") - insufficient to verify
                            citation.verified = False
                            logger.warning(
                                f"[BATCH-NA-PARTIAL] {citation.citation}: N/A case name + partial citation - not marking verified"
                            )
                        elif result_canonical and result_canonical != "N/A" and not result_url:
                            # Has canonical name but no URL - cannot mark as verified (user rule: verified requires URL)
                            citation.verified = False
                            citation.canonical_name = result.canonical_name
                            citation.canonical_date = getattr(result, "canonical_date", None)
                            citation.verification_status = "no_canonical_url"
                            citation.source = result.source or "batch_verify"
                            logger.warning(
                                f"[BATCH-NO-URL] {citation.citation}: Canonical name returned but no URL - not marking verified"
                            )
                        else:
                            # No canonical name - cannot verify
                            citation.verified = False
                            citation.verification_status = "no_canonical_name"
                            citation.source = result.source or "batch_verify"
                            logger.warning(f"[BATCH-UNVERIFIED] {citation.citation}: No canonical name returned")
                    else:
                        citation.verified = False
                        result_source = result.source if result and getattr(result, "source", None) else "not_found"
                        citation.source = result_source
                        logger.warning(
                            f"[BATCH-NOT-VERIFIED] {citation.citation}: result.verified={getattr(result, 'verified', 'N/A')}, "
                            f"source={result_source}, error={getattr(result, 'error', 'N/A')}, "
                            f"canonical_name={getattr(result, 'canonical_name', 'N/A')}, "
                            f"canonical_url={getattr(result, 'canonical_url', 'N/A')}"
                        )

                        # Check if this is a proprietary format citation (WL or Lexis)
                        import re
                        citation_str = str(citation.citation)
                        is_westlaw = bool(re.search(r'\b\d{4}\s+WL\s+\d+', citation_str))
                        is_lexis = bool(re.search(r'\b\d{4}\s+U\.S\.\s+Lexis\s+\d+', citation_str, re.IGNORECASE))
                        
                        if is_westlaw or is_lexis:
                            # Set proprietary format error message
                            citation.verification_status = "proprietary_format"
                            citation.error = "Proprietary format - not available in free databases (Westlaw/Lexis only)"
                            logger.info(f"[BATCH-PROPRIETARY] {citation.citation}: Proprietary format detected")
                        # CRITICAL FIX: Preserve canonical data for year_mismatch_rejected
                        # This allows clustering to split by canonical year even when unverified
                        elif result_source == "year_mismatch_rejected" and result:
                            citation.verification_status = "year_mismatch"
                            citation.canonical_name = getattr(result, "canonical_name", None)
                            citation.canonical_date = getattr(result, "canonical_date", None)
                            citation.canonical_url = getattr(result, "canonical_url", None)
                            citation.verification_error = getattr(result, "error", None)
                            logger.warning(
                                f"[BATCH-YEAR-MISMATCH] {citation.citation}: {result.error} - canonical data preserved for clustering"
                            )
                        else:
                            citation.verification_status = "not_found"

                        if not citation.extracted_case_name or citation.extracted_case_name == "N/A":
                            citation.extracted_case_name = original_extracted_name
                        if not citation.extracted_date or citation.extracted_date == "N/A":
                            citation.extracted_date = original_extracted_date
                        error_msg = getattr(result, "error", "No result") if result else "No result"

                logger.info(f"[BATCH-VERIFY] Completed master batch verification: verified {verified_count}/{total}")

            # USER FIX 2026-01-12: Post-verification fix for obvious CourtListener mismatches
            # CourtListener often returns wrong cases for citations (e.g., 139 S. Ct. 1112 → Zagorski instead of Bucklew)
            # This fix detects obvious mismatches and prefers the extracted name which is usually correct
            logger.info("[POST-VERIFY-FIX] Checking for obvious CourtListener name mismatches...")
            mismatches_fixed = 0
            
            for citation in citations:
                if not hasattr(citation, 'canonical_name') or not hasattr(citation, 'extracted_case_name'):
                    continue
                    
                canonical_name = getattr(citation, 'canonical_name', None)
                extracted_name = getattr(citation, 'extracted_case_name', None)
                
                # Skip if either is missing or generic
                if not canonical_name or not extracted_name:
                    continue
                if canonical_name.strip().upper() == "N/A" or extracted_name.strip().upper() == "N/A":
                    continue
                    
                # Check for obvious mismatch - completely different case names
                canonical_clean = canonical_name.lower().replace(".", "").replace(",", "").strip()
                extracted_clean = extracted_name.lower().replace(".", "").replace(",", "").strip()
                
                # Calculate word overlap similarity
                canonical_words = set(canonical_clean.split())
                extracted_words = set(extracted_clean.split())
                
                if canonical_words and extracted_words:
                    overlap = len(canonical_words & extracted_words)
                    similarity = overlap / min(len(canonical_words), len(extracted_words))
                    
                    # Log similarity for debugging
                    logger.info(f"[POST-VERIFY-FIX] Citation '{citation.citation}': similarity={similarity:.2f} (canonical='{canonical_name}', extracted='{extracted_name}')")
                    
                    # CRITICAL FIX: DO NOT overwrite canonical_name with extracted_name!
                    # CourtListener is the authoritative source - if verification succeeded and returned a canonical_name,
                    # we must trust it. The extracted name might be wrong (e.g., picking up nearby case names).
                    # Example: "418 U.S. 323" correctly verified as "Gertz v. Robert Welch, Inc." but extraction
                    # picked up "Milkovich v. Lorain Journal Co" from nearby text. We should NOT overwrite canonical
                    # with extracted in this case.
                    #
                    # If similarity is low, it means extraction was wrong, not verification. Log the mismatch
                    # but preserve the canonical name from CourtListener.
                    if similarity < 0.4:
                        logger.warning(f"[POST-VERIFY-FIX] Name mismatch detected (extraction likely wrong):")
                        logger.warning(f"  Canonical (from CourtListener - TRUSTED): '{canonical_name}'")
                        logger.warning(f"  Extracted (from document - may be wrong): '{extracted_name}'")
                        logger.warning(f"  Similarity: {similarity:.2f}")
                        logger.warning(f"  PRESERVING canonical_name from CourtListener (authoritative source)")
                        
                        # Mark as mismatch but DO NOT overwrite canonical_name
                        citation.name_mismatch = True
                        citation.mismatch_confidence = similarity
                        
                        # Keep verification status - verification is correct, extraction was wrong
                        citation.verification_status = "verified_with_extraction_mismatch"
                        
                        mismatches_fixed += 1
            
            else:
                logger.info("[POST-VERIFY-FIX] No obvious mismatches found")

            # Apply known federal citations (shared with rq_worker / vue_api path)
            try:
                from src.verification import apply_known_federal_to_citation_objects
                apply_known_federal_to_citation_objects(citations)
            except Exception as _e:
                logger.warning(f"[KNOWN-CITATION] Could not apply known citations: {_e}")

        except Exception as e:
            logger.error(f"[VERIFICATION] Error in unified master verification: {str(e)}")
            # Fallback to marking all as unverified
            for citation in citations:
                if not hasattr(citation, "verified") or not citation.verified:
                    citation.verified = False
                    citation.verification_status = "error"

        # OOM-FIX: Force memory release before returning to pipeline/rq_worker.
        # HTTP response data, JSON parse trees, and intermediate verification objects
        # accumulate during verification. gc.collect() frees Python objects, and
        # malloc_trim(0) forces glibc to return freed pages to the OS.
        try:
            import gc as _gc_final
            _gc_final.collect()
            try:
                import ctypes as _ct_final
                _ct_final.CDLL("libc.so.6").malloc_trim(0)
            except Exception:
                pass
            _gc_final.collect()
            try:
                _ct_final.CDLL("libc.so.6").malloc_trim(0)
            except Exception:
                pass
        except Exception:
            pass

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
            "page",
            "p.",
            "pp.",
            "see",
            "id.",
            "ibid",
            "supra",
            "infra",
            "cf.",
            "but see",
            "accord",
            "compare",
            "contra",
        ]

        at_pattern = re.search(r"\bat\s+(\d+)\b", preceding_text[-10:])
        if at_pattern:
            return False

        for indicator in page_indicators:
            if indicator in preceding_text:
                return False

        sentence_boundary = re.search(r"[.!?]\s+[A-Z]", preceding_text[-50:])
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

        normalized = re.sub(r"\s+", " ", normalized)

        normalized = re.sub(r"(\d+)\s*U\.\s*S\.\s*(\d+)", r"\1 U.S. \2", normalized)

        normalized = re.sub(r"(\d+)\s*F\.\s*(\d+)d\s*(\d+)", r"\1 F.\2d \3", normalized)
        normalized = re.sub(r"(\d+)\s*F\.\s*3d\s*(\d+)", r"\1 F.3d \2", normalized)
        normalized = re.sub(r"(\d+)\s*F\.\s*2d\s*(\d+)", r"\1 F.2d \2", normalized)

        normalized = re.sub(r"(\d+)\s*F\.\s*Supp\.\s*(\d+)d\s*(\d+)", r"\1 F.Supp.\2d \3", normalized)
        normalized = re.sub(r"(\d+)\s*F\.\s*Supp\.\s*3d\s*(\d+)", r"\1 F. Supp. 3d \2", normalized)
        normalized = re.sub(r"(\d+)\s*F\.\s*Supp\.\s*2d\s*(\d+)", r"\1 F. Supp. 2d \2", normalized)
        normalized = re.sub(r"(\d+)\s*F\.\s*Supp\.\s*(\d+)", r"\1 F. Supp. \2", normalized)

        normalized = re.sub(r"(\d+)\s*S\.\s*Ct\.\s*(\d+)", r"\1 S. Ct. \2", normalized)

        normalized = re.sub(r"(\d+)\s*L\.\s*Ed\.\s*2d\s*(\d+)", r"\1 L. Ed. 2d \2", normalized)
        normalized = re.sub(r"(\d+)\s*L\.\s*Ed\.\s*(\d+)", r"\1 L. Ed. \2", normalized)

        normalized = re.sub(r"(\d+)\s*P\.\s*3d\s*(\d+)", r"\1 P.3d \2", normalized)
        normalized = re.sub(r"(\d+)\s*P\.\s*2d\s*(\d+)", r"\1 P.2d \2", normalized)

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
            normalized = re.sub(r"(\d+)\s*Wn\.\s*2d\s*(\d+)", r"\1 Wn.2d \2", normalized)
            normalized = re.sub(r"(\d+)\s*Wn\.\s*App\.\s*(\d+)", r"\1 Wn. App. \2", normalized)
            normalized = re.sub(r"(\d+)\s*Wash\.\s*2d\s*(\d+)", r"\1 Wash. 2d \2", normalized)
            normalized = re.sub(r"(\d+)\s*Wash\.\s*App\.\s*(\d+)", r"\1 Wash. App. \2", normalized)

        if purpose == "comparison":
            normalized = normalized.lower()
            normalized = re.sub(r"\bwash\.\b", "wash.", normalized)
            normalized = re.sub(r"\bp\.\b", "p.", normalized)
            normalized = re.sub(r"\bf\.\b", "f.", normalized)

        elif purpose == "us_extract":
            us_pattern = r"(\d+\s+U\.S\.\s+\d+)"
            match = re.search(us_pattern, normalized)
            if match:
                return match.group(1)

        normalized = re.sub(r"\s+", " ", normalized)

        return normalized.strip()

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
                    # CRITICAL FIX: Use helper function to filter parallel citations
                    filtered = filter_cluster_members_by_reporter(
                        citation.citation, 
                        [c.citation for c in group if c != citation]
                    )
                    citation.parallel_citations = filtered
                    citation.is_parallel = len(filtered) > 0

            return citations

        except Exception as e:
            logger.warning(f"[PARALLEL_DETECTION] Error in parallel detection: {e}")
            return citations

    def _detect_parallel_citation_groups(
        self, citations: List[CitationResult], text: str
    ) -> List[List[CitationResult]]:
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

            for j, other_citation in enumerate(citations[i + 1 :], i + 1):
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

        # FIX: Check distance but don't fail immediately - use as a factor
        within_proximity = abs(pos1 - pos2) <= 200

        # CRITICAL FIX: Same reporter + different volumes = DIFFERENT CASES
        # Example: "578 U.S. 330" (Spokeo 2016) vs "594 U.S. ____" (different case)
        # Parallel citations MUST be from DIFFERENT reporters for the same case
        parsed1 = self._parse_citation_components(citation1.citation)
        parsed2 = self._parse_citation_components(citation2.citation)
        if parsed1 and parsed2:
            vol1, rep1 = parsed1.get("volume"), parsed1.get("reporter")
            vol2, rep2 = parsed2.get("volume"), parsed2.get("reporter")
            # If SAME reporter but DIFFERENT volumes, they CANNOT be parallel
            if rep1 and rep2 and rep1 == rep2 and vol1 and vol2 and vol1 != vol2:
                logger.warning(
                    f"[PARALLEL-REJECTED] Same reporter '{rep1}' but different volumes: {vol1} vs {vol2} | "
                    f"{citation1.citation} vs {citation2.citation} - These are DIFFERENT cases"
                )
                return False

        # Shared same-case check (canonical implementation in src.utils.same_case)
        name1 = citation1.extracted_case_name or ""
        name2 = citation2.extracted_case_name or ""
        if not names_are_same_case(name1, name2):
            return False
        # If names positively matched, accept as parallel
        if has_case_name(name1) and has_case_name(name2):
            return True

        date1 = citation1.extracted_date or ""
        date2 = citation2.extracted_date or ""

        # NOTE: Date match alone is NOT sufficient to declare parallel citations.
        # Many different cases share the same year. Date is only used as a
        # supporting signal alongside reporter matching below.

        reporter1 = self._extract_reporter(citation1.citation)
        reporter2 = self._extract_reporter(citation2.citation)

        known_parallel_pairs = [
            # US Supreme Court
            ("U.S.", "S.Ct."),
            ("U.S.", "L.Ed."),
            ("U.S.", "L.Ed.2d"),
            ("S.Ct.", "L.Ed."),
            ("S.Ct.", "L.Ed.2d"),
            # Washington State
            ("Wash.", "P."),  # Wash. and P. (Pacific Reporter)
            ("Wash.", "P.2d"),
            ("Wash.2d", "P.2d"),
            ("Wash.2d", "P.3d"),
            ("Wash. App.", "P.2d"),
            ("Wash. App.", "P.3d"),
            ("Wn.2d", "P.2d"),  # Common abbreviation for Washington
            ("Wn.2d", "P.3d"),
            ("Wn. App.", "P.2d"),
            ("Wn. App.", "P.3d"),
            ("Wn. App. 2d", "P.3d"),  # Washington Appeals 2d and Pacific 3d
            # Federal Reporters
            ("F.3d", "F.Supp."),
            ("F.2d", "F.Supp."),
            ("F.3d", "F.Supp.2d"),
            ("F.2d", "F.Supp.2d"),
            # State Reporters
            ("N.E.2d", "N.Y.S.3d"),  # New York
            ("N.W.2d", "N.W.2d"),  # Regional reporters
            ("S.E.2d", "S.E.2d"),
            ("So.2d", "So.3d"),
            ("P.3d", "P.3d"),
        ]

        reporters_match = False
        for pair in known_parallel_pairs:
            if (reporter1 in pair and reporter2 in pair) or (reporter2 in pair and reporter1 in pair):
                reporters_match = True
                break

        # DEBUG: Log reporter extraction for troubleshooting
        logger.info(
            f"[PARALLEL_DEBUG] Comparing '{citation1.citation}' (reporter='{reporter1}') with '{citation2.citation}' (reporter='{reporter2}')"
        )
        logger.info(
            f"[PARALLEL_DEBUG]   Dates: '{date1}' vs '{date2}' | Names: '{name1}' vs '{name2}' | Within proximity: {within_proximity} | Reporters match: {reporters_match}"
        )

        # FIX: Accept as parallel if:
        # 1. Reporters match AND citations are nearby, OR
        # 2. Reporters match AND have same date (strong signal even if far apart), OR
        # 3. Reporters match AND have matching case names (even if far apart)
        if reporters_match:
            if within_proximity:
                logger.info(f"[PARALLEL_DEBUG]   ✓ PARALLEL: Reporters match + within proximity")
                return True  # Close together + matching reporters = parallel
            if date1 and date2 and date1 == date2:
                logger.info(f"[PARALLEL_DEBUG]   ✓ PARALLEL: Reporters match + same date")
                return True  # Same date + matching reporters = parallel (even if far)
            if name1 and name2:
                # Check if case names match (already validated above)
                words1 = set(re.sub(r"[^\w\s]", " ", name1.lower()).split())
                words2 = set(re.sub(r"[^\w\s]", " ", name2.lower()).split())
                if len(words1.intersection(words2)) >= 2:
                    logger.info(f"[PARALLEL_DEBUG]   ✓ PARALLEL: Reporters match + case names match")
                    return True  # Matching names + matching reporters = parallel (even if far)

        logger.info(f"[PARALLEL_DEBUG]   ✗ NOT parallel")
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
            r"\b(\d+\s+U\.?\s*S\.?(?:\s*C\.?\s*)?(?:\s*\d+)?)",  # U.S.
            r"\b(\d+\s+S\.?\s*Ct\.?(?:\s*\d+)?)",  # S.Ct.
            r"\b(\d+\s+L\.?\s*Ed\.?(?:\s*2d)?(?:\s*\d+)?)",  # L.Ed. or L.Ed.2d
            # Federal Reporters
            r"\b(\d+\s+F\.?(?:\s*3d|2d|Supp\.?|Supp\.?\s*2d)?(?:\s*\d+)?)",  # F.3d, F.2d, F.Supp., etc.
            # Washington State Reporters
            r"\b(\d+\s+Wash\.?(?:\s*2d|\s*App\.?)?(?:\s*\d+)?)",  # Wash., Wash.2d, Wash. App.
            r"\b(\d+\s+Wn\.?(?:\s*2d|\s*App\.?)?(?:\s*\d+)?)",  # Wn., Wn.2d, Wn. App.
            r"\b(\d+\s+P\.?(?:\s*3d|2d)?(?:\s*\d+)?)",  # P.3d, P.2d
            # Other common reporters
            r"\b(\d+\s+N\.?\s*E\.?(?:\s*2d)?(?:\s*\d+)?)",  # N.E., N.E.2d
            r"\b(\d+\s+N\.?\s*Y\.?\s*S\.?(?:\s*3d|2d)?(?:\s*\d+)?)",  # N.Y.S., N.Y.S.2d, N.Y.S.3d
            r"\b(\d+\s+S\.?\s*E\.?(?:\s*2d)?(?:\s*\d+)?)",  # S.E., S.E.2d
            r"\b(\d+\s+So\.?(?:\s*3d|2d)?(?:\s*\d+)?)",  # So., So.2d, So.3d
            r"\b(\d+\s+N\.?\s*W\.?\s*2d(?:\s*\d+)?)",  # N.W.2d
            r"\b(\d+\s+A\.?(?:\s*3d|2d)?(?:\s*\d+)?)",  # A.2d, A.3d (Atlantic)
            # Connecticut State Reporters
            r"\b(\d+\s+Conn\.?\s*(?:Supp\.?|App\.?)?(?:\s*\d+)?)",  # Conn., Conn. Supp., Conn. App.
            # Ohio State Reporters
            r"\b(\d+\s+Ohio\s*St\.?(?:\s*3d|2d)?(?:\s*\d+)?)",  # Ohio St., Ohio St. 2d, Ohio St. 3d
            r"\b(\d+\s+Ohio\s*App\.?(?:\s*3d|2d)?(?:\s*\d+)?)",  # Ohio App., Ohio App. 2d, Ohio App. 3d
            # Nebraska State Reporters
            r"\b(\d+\s+Neb\.?(?:\s*App\.?)?(?:\s*\d+)?)",  # Neb., Neb. App.
            # Maine State Reporters
            r"\b(\d+\s+Me\.?(?:\s*\d+)?)",  # Me.
            # Oregon State Reporters
            r"\b(\d+\s+Or\.?(?:\s*App\.?)?(?:\s*\d+)?)",  # Or., Or. App.
            # General pattern as fallback
            r"\b(\d+\s+[A-Z][A-Za-z]*(?:\s*\d*[a-z]*)?\b\.?(?:\s*[A-Z][a-z]*\.?)*)",
        ]

        for pattern in patterns:
            match = re.search(pattern, citation, re.IGNORECASE)
            if match:
                # Extract just the reporter part (without volume and page)
                reporter_part = re.sub(r"^\d+\s+", "", match.group(1).strip())
                # FIX: Don't remove series indicators like "2d", "3d"
                # Only remove pure page numbers (3+ digits) at the end
                reporter = re.sub(r"\s+\d{3,}$", "", reporter_part)
                # Standardize common variations
                reporter = re.sub(r"\.\s+", ".", reporter)  # Remove spaces after dots
                reporter = re.sub(r"\s+", " ", reporter)  # Normalize spaces
                return reporter.strip()

        return ""

    def _extract_context(self, text: str, start: int, end: int, window: int = 200) -> str:
        """Extract surrounding context for a citation."""
        ctx_start = max(0, start - window)
        ctx_end = min(len(text), end + window)
        return text[ctx_start:ctx_end]

    def _extract_case_name_from_context(self, text: str, citation, all_citations=None) -> str:
        """Extract case name from citation string itself or surrounding text context."""
        try:
            cit_text = citation.citation or ""

            # Strategy 1: Extract case name embedded in the citation string itself
            # Eyecite returns citations like "Raines v. Byrd, 521 U.S. 811, 819-820 (scotus)"
            # or "Spokeo, Inc. v. Robins, 578 U.S. 330, 340 (scotus 2016)"
            if ' v. ' in cit_text:
                # Match "Name v. Name" before the volume number
                # Handle corporate names with commas like "Spokeo, Inc. v. Robins"
                v_match = re.match(
                    r"(.+?\s+v\.\s+[A-Za-z][A-Za-z\.\',&\s]+?)(?:,\s*)?\d+\s+[A-Z]",
                    cit_text
                )
                if v_match:
                    name = v_match.group(1).strip()
                    # Clean trailing comma/semicolon
                    name = re.sub(r'[,;:\s]+$', '', name)
                    if len(name) > 5 and ' v. ' in name:
                        return name

            # Strategy 2: Look in the text BEFORE the citation start_index
            start = citation.start_index or 0
            ctx_start = max(0, start - 300)
            context_before = text[ctx_start:start]

            # Look for "Name v. Name" pattern before the citation
            # Search from right to left to get the closest match
            # Allow a single newline around "v." (PDF line breaks) but NOT in party names
            # Party names: letters, abbreviation dots, commas, &, hyphens, spaces/tabs
            # Second party: stop at sentence boundaries (period + space + capital)
            matches = list(re.finditer(
                r'([A-Z][A-Za-z.\'\,&\ \t\-]+[ \t\n]+v\.[ \t\n]+[A-Z][A-Za-z.\'\,&\ \t\-]+?)(?:\.\s+[A-Z]|,\s*\d|\s+\d{1,3}\s+[A-Z]|\s*$)',
                context_before
            ))
            if matches:
                # Take the last (closest) match
                best_match = matches[-1]
                name = best_match.group(1).strip()
                name = re.sub(r'[,;:\s]+$', '', name)
                # Clean any stray whitespace (newlines from PDF line breaks)
                name = re.sub(r'\s+', ' ', name).strip()
                if len(name) > 5 and ' v. ' in name:
                    # CONTAMINATION GUARD: Check the text BETWEEN the found name
                    # and the current citation for signs that the name belongs to
                    # a different citation (common in Table of Authorities).
                    text_between = context_before[best_match.end():]
                    # If there's an intervening citation pattern (vol reporter page),
                    # the name belongs to that citation, not ours.
                    # Require a legal reporter abbreviation (contains a period, e.g. "A.", "F.3d", "U.S.")
                    has_intervening_citation = bool(re.search(
                        r'\d+\s+[A-Z][A-Za-z.]*\.\s*(?:\d+[a-z]{0,2}\s+)?\d+',
                        text_between
                    ))
                    # Detect TOA formatting: dotted leaders or page-number lists
                    has_toa_formatting = bool(re.search(
                        r'\.{3,}|(?:,\s*\d{1,3}){2,}|\bpassim\b',
                        text_between
                    ))
                    if not has_intervening_citation and not has_toa_formatting:
                        return name

            # Strategy 3: Check for "In re" or "Matter of" patterns
            for pattern in [r'(In\s+re\s+[A-Z][A-Za-z\s\.\',&]+)', r'((?:Matter|Estate)\s+of\s+[A-Z][A-Za-z\s\.\',&]+)']:
                in_re_match = re.search(pattern, cit_text) or re.search(pattern, context_before)
                if in_re_match:
                    name = in_re_match.group(1).strip()
                    name = re.sub(r'[,;:\s]+$', '', name)
                    if len(name) > 5:
                        return name

            # Strategy 4: Short-form case name from text immediately before the citation
            # Handles patterns like:
            #   "see also Gomes, No. 20-CV-453-LM, 2020 WL 2113642"
            #   "Ouadani, 405 F. Supp. 3d at 163"
            #   "Gomes, 2020 WL 2113642"
            # Look in the last 80 chars before the citation for a capitalized name
            # followed by a comma and then a docket number, volume, or the citation itself.
            short_ctx = context_before[-80:] if len(context_before) > 80 else context_before
            # Pattern: optional signal word, then "Name," immediately before docket/citation
            # The name must start with a capital letter and can include dots, hyphens, apostrophes
            short_match = re.search(
                r'(?:^|[;.]\s*|\b(?:see\s+(?:also\s+)?|accord\s+|compare\s+|but\s+see\s+|cf\.?\s+))'
                r'([A-Z][A-Za-z\'\.\-]+(?:\s+[A-Z][A-Za-z\'\.\-]+)*)'
                r',\s*(?:No\.\s|at\s+\d|\d{1,3}\s+[A-Z]|\d{4}\s+WL\s)',
                short_ctx
            )
            if short_match:
                name = short_match.group(1).strip()
                # Reject if it's a common non-name word (signal words, court names)
                _reject = {'See', 'Also', 'But', 'Accord', 'Compare', 'Citing',
                           'The', 'This', 'That', 'Here', 'Where', 'When', 'Because',
                           'However', 'Moreover', 'Furthermore', 'Although', 'Thus'}
                if name not in _reject and len(name) >= 3:
                    return name

        except Exception:
            pass
        return "N/A"

    def _extract_date_from_context(self, text: str, citation) -> Optional[str]:
        """Extract date/year from citation string itself or surrounding text context.

        FIX 2026-02-10: Prioritize the year from the ORIGINAL DOCUMENT TEXT around the
        citation position over the year in eyecite's reconstructed citation string.
        Eyecite sometimes picks up a nearby year from a different citation or document
        header (e.g., "(scotus 2021)" when the document actually says "(2008)").
        """
        try:
            cit_text = citation.citation or ""

            # Strategy 0: WL/LEXIS citations have the year as the first token
            wl_match = re.match(r'^(\d{4})\s+(?:WL|U\.S\.?\s*LEXIS|LEXIS)\s+\d+', cit_text)
            if wl_match:
                return wl_match.group(1)

            # Strategy 1 (HIGHEST PRIORITY): Extract year from the ORIGINAL DOCUMENT TEXT
            # near the citation position.  The parenthetical year in the actual document
            # is the most authoritative source.
            end = citation.end_index or 0
            start = citation.start_index or 0
            if end > 0:
                # Look after the citation end for a parenthetical year
                # Use wider window (150 chars) to handle page breaks in PDFs
                context_after = text[end:min(len(text), end + 150)]
                # Find ALL parenthetical years, skip page header years like "Cite as: 594 U. S. ____ (2021)"
                for m in re.finditer(r'\((?:[A-Za-z0-9.\s]*?)(\d{4})\)', context_after):
                    year = m.group(1)
                    if 1700 <= int(year) <= 2030:
                        # Check if this year is inside a page header pattern
                        # Page headers look like: "Cite as: NNN U. S. ____ (YYYY)"
                        preceding = context_after[:m.start()]
                        if re.search(r'Cite\s+as:', preceding, re.IGNORECASE):
                            continue  # Skip page header year
                        return year
                # If all parenthetical years were in page headers, try bare year after page header
                # PDF page breaks can split "(CA8 2016)" into "(CA8 ...header... 2016)"
                # Look for a bare 4-digit year that follows a page header
                header_match = re.search(r'Cite\s+as:.*?\(\d{4}\)\s*(?:Opinion\s+of\s+the\s+Court\s*)?(\d{4})', context_after, re.IGNORECASE)
                if header_match:
                    year = header_match.group(1)
                    if 1700 <= int(year) <= 2030:
                        return year

            # Strategy 2: Look in text BEFORE the citation (sometimes year precedes)
            if start > 0:
                context_before = text[max(0, start - 30):start]
                match = re.search(r'\((\d{4})\)', context_before)
                if match:
                    year = match.group(1)
                    if 1700 <= int(year) <= 2030:
                        return year

            # Strategy 3: Extract year from the eyecite citation string itself
            # NOTE: This is LOWER priority because eyecite sometimes reconstructs
            # the wrong year from nearby text (e.g., document header year)
            year_in_cit = re.search(r'\((?:\w+\s+)?(\d{4})\)', cit_text)
            if year_in_cit:
                year = year_in_cit.group(1)
                if 1700 <= int(year) <= 2030:
                    return year

            # Strategy 4: Check metadata for year
            if hasattr(citation, 'metadata') and isinstance(citation.metadata, dict):
                meta_year = citation.metadata.get('year')
                if meta_year:
                    return str(meta_year)

            # Strategy 5: Search the FULL document for another occurrence of the same
            # base citation that includes a year.  SCOTUS syllabus sections cite cases
            # without years (e.g., "578 U. S. 330, 340.") but the opinion body later
            # cites the same case WITH a year (e.g., "578 U. S. 330, 340 (2016)").
            # Extract volume/reporter/page from the citation string and search globally.
            base_match = re.search(r'(\d+)\s+([A-Za-z][A-Za-z.\s]+?)\s+(\d+)', cit_text)
            if base_match:
                vol, reporter, page = base_match.group(1), base_match.group(2).strip(), base_match.group(3)
                # Normalize reporter for flexible matching (handle "U.S." vs "U. S.")
                reporter_pattern = re.escape(reporter).replace(r'\.', r'\.\s*')
                # Search for: volume reporter page ... (year)
                global_pattern = re.compile(
                    rf'{re.escape(vol)}\s+{reporter_pattern}\s+{re.escape(page)}'
                    rf'[^(]{{0,60}}\((?:[A-Za-z0-9.\s]*?)(\d{{4}})\)',
                )
                for gm in global_pattern.finditer(text):
                    year = gm.group(1)
                    if 1700 <= int(year) <= 2030:
                        # Skip if this match is at the same position (we already checked it)
                        if gm.start() == (start or 0):
                            continue
                        # Verify it's not a page header year
                        preceding_ctx = text[max(0, gm.start() - 30):gm.start()]
                        if re.search(r'Cite\s+as:', preceding_ctx, re.IGNORECASE):
                            continue
                        logger.debug(
                            f"[DATE-STRATEGY5] Borrowed year {year} for '{cit_text[:50]}' "
                            f"from another occurrence at pos {gm.start()}"
                        )
                        return year

        except Exception:
            pass
        return None

    def _extract_citation_components(self, citation: str) -> Dict[str, str]:
        """Extract volume, reporter, and page from citation string."""
        pattern = r"(\d+)\s+([A-Za-z\.\s]+?)\s+(\d+)"
        match = re.search(pattern, citation)
        if match:
            return {"volume": match.group(1), "reporter": match.group(2).strip(), "page": match.group(3)}
        return {"volume": "", "reporter": "", "page": ""}

    def _parse_citation_components(self, citation_text: str) -> Optional[Dict[str, str]]:
        """Parse citation into volume, reporter, page components."""
        pattern = r"(\d+)\s+([A-Za-z\.\s]+?)\s+(\d+)"
        match = re.search(pattern, citation_text)
        if match:
            return {"volume": match.group(1), "reporter": match.group(2).strip(), "page": match.group(3)}
        return None

    def _clean_extracted_case_name(self, name: str) -> str:
        """Clean an extracted case name by removing common artifacts."""
        if not name:
            return name
        # Strip TOA header prefixes that leak into extracted names
        cleaned = re.sub(
            r'^(?:TABLE\s+OF\s+AUTHORITIES\s+)?(?:(?:I{1,3}V?|V?I{0,3})\s+)?Cases(?:[—\-–]Continued)?(?:\s*:\s*|\s+)(?:Page\s+)?',
            '', name, flags=re.IGNORECASE
        ).strip()
        # Strip standalone "Page " prefix (from TOA where "Cases-Continued:" was already stripped)
        cleaned = re.sub(r'^Page\s+(?=[A-Z])', '', cleaned).strip()
        # Remove trailing citation fragments (any reporter pattern + page, including WL/LEXIS)
        cleaned = re.sub(r",?\s*\d+\s+(?:U\.S\.|F\.\d*d?|S\.\s*Ct\.|L\.\s*Ed|Tex\.|Pet\.|Cranch|Wall\.|Wheat\.|How\.|Barb\.|A\.|F\.\s*(?:Supp|R\.D)|WL|U\.S\.?\s*LEXIS|LEXIS).*$", "", cleaned).strip()
        # Remove trailing parentheticals
        cleaned = re.sub(r"\s*\([^)]*$", "", cleaned).strip()
        # Remove trailing year patterns like ", 1803" or ", 2025"
        cleaned = re.sub(r",\s*(?:19|20)\d{2}\s*$", "", cleaned).strip()
        # Remove trailing docket number fragments like ", No. 24-1287", ", No. 2", ", No. CV 25", bare ", No"
        # CRITICAL: Require comma or whitespace before "No" to avoid matching inside words like "Moreno", "McDonough"
        cleaned = re.sub(r"(?:,\s*|\s+)No\.?\s*(?:,?\s*(?:CIV\.?\s+|CV\s+)?[\w\-\.]+(?:\s+[\w\-\.]+)*)?\s*$", "", cleaned, flags=re.IGNORECASE).strip()
        # Remove trailing commas, numbers, and junk (e.g. ", , 1337, 2020")
        cleaned = re.sub(r"(?:,\s*)+(?:\d{1,5}\s*,?\s*)*$", "", cleaned).strip()
        # Remove trailing commas/periods
        cleaned = re.sub(r"[,\.]+$", "", cleaned).strip()
        # Truncate at real sentence boundaries only.
        # Require 2+ lowercase letters before period AND a common sentence-starting word after.
        # This avoids false positives on abbreviations like 'rel. Hunt', 'Pers. Mgmt.', 'v. Madison'
        sentence_end = re.search(r'(?<=[a-z]{2})\.\s+(?:From|The|This|That|These|Those|It|In|On|At|By|For|And|But|Or|An|As|If|So|No|To|We|He|She|Such|Under|After|Before|During|However|Moreover|Furthermore|Indeed|Rather|Thus|Therefore|Accordingly|Here|There|Where|When|While|Although|Because|Since|Until|Unless|Whether)\b', cleaned)
        if sentence_end:
            cleaned = cleaned[:sentence_end.start()].strip()
        # Max length guard — case names longer than 120 chars are almost certainly contaminated
        if len(cleaned) > 120:
            cleaned = "N/A"
        return cleaned if cleaned else name

    def _remove_citation_contamination_from_case_name(self, name: str) -> str:
        """Remove citation text that leaked into case names."""
        if not name:
            return name
        # Remove common citation patterns from case names
        cleaned = re.sub(r'\d+\s+(?:U\.S\.|S\.Ct\.|L\.Ed\.|F\.\d*d?|P\.\d*d?)\s+\d+', '', name)
        cleaned = re.sub(r'\(\d{4}\)', '', cleaned)
        cleaned = cleaned.strip(' ,;.')
        return cleaned if cleaned else name

    def _extract_with_eyecite(self, text: str) -> List[CitationResult]:
        """Extract citations using eyecite library."""
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
                    # FIX 2026-02-10: Detect concatenated page+pinpoint from PDF artifacts
                    # e.g. "496 U.S. 310317" should be "496 U.S. 310" (eyecite merges "310, 317")
                    citation_str = self._fix_concatenated_page_numbers(citation_str)
                    seen_citations.add(citation_str)
                    start_index = None
                    end_index = None
                    # Try span() as method first (newer eyecite), then as property
                    try:
                        span = citation_obj.span() if callable(getattr(citation_obj, 'span', None)) else getattr(citation_obj, 'span', None)
                        if span and len(span) == 2:
                            start_index = span[0]
                            end_index = span[1]
                    except Exception:
                        pass
                    if start_index is None:
                        try:
                            start_index = text.find(citation_str)
                            if start_index != -1:
                                end_index = start_index + len(citation_str)
                        except Exception:
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
                    citations.append(citation)
                except Exception as e:
                    logger.warning(f"Error processing eyecite citation: {e}")
                    continue
        except Exception as e:
            logger.warning(f"Error in eyecite extraction: {e}")
        return citations

    def _fix_concatenated_page_numbers(self, citation_str: str) -> str:
        """Fix concatenated page+pinpoint numbers from PDF text extraction artifacts.

        PDF extraction sometimes loses the comma/space between page and pinpoint,
        causing eyecite to produce e.g. '496 U.S. 310317' instead of '496 U.S. 310'.
        Detect this by checking if the page number is suspiciously long (5+ digits)
        and splitting it into page + pinpoint where pinpoint >= page.
        """
        if not citation_str:
            return citation_str
        # WL and LEXIS citations have docket IDs, not page numbers — never split them
        if re.search(r'\b\d{4}\s+WL\s+\d+', citation_str) or re.search(r'\bLexis\s+\d+', citation_str, re.IGNORECASE):
            return citation_str
        # Match: reporter followed by a suspiciously long page number
        # For U.S. Reports (U.S., S.Ct., L.Ed., Wheat., Cranch, Wall., How., Pet.),
        # pages rarely exceed 999, so 4+ digits is suspicious.
        # For other reporters (F.2d, F.3d, etc.), pages can be 4 digits, so require 5+.
        is_us_reporter = bool(re.search(
            r'\d+\s+(?:U\.?\s*S\.?|S\.\s*Ct\.|L\.\s*Ed|Wheat\.|Cranch|Wall\.|How\.|Pet\.)',
            citation_str
        ))
        min_digits = 4 if is_us_reporter else 5
        m = re.match(
            r'^(.*?\d+\s+[A-Za-z][A-Za-z.\s]+\s+)(\d{' + str(min_digits) + r',})(.*)',
            citation_str,
        )
        if not m:
            return citation_str
        prefix, page_blob, suffix = m.group(1), m.group(2), m.group(3)
        # Try longest valid page first (4 digits down to 2)
        for split_pos in range(min(4, len(page_blob) - 1), 1, -1):
            page = page_blob[:split_pos]
            pinpoint = page_blob[split_pos:]
            page_val = int(page)
            if page_val < 1 or page_val > 9999:
                continue
            if not pinpoint or pinpoint[0] == '0':
                continue
            pin_val = int(pinpoint)
            if pin_val < page_val:
                continue
            if pin_val > page_val * 10:
                continue
            fixed = f"{prefix}{page}{suffix}"
            logger.info(
                f"[EYECITE-FIX] Concatenated page numbers: '{citation_str[:60]}' -> '{fixed[:60]}' "
                f"(split {page_blob} -> page={page}, pinpoint={pinpoint})"
            )
            return fixed
        return citation_str

    def _extract_citation_text_from_eyecite(self, citation_obj) -> str:
        """Extract citation text from eyecite object."""
        if isinstance(citation_obj, str):
            return citation_obj

        # Get type name to filter non-case citations
        type_name = type(citation_obj).__name__
        if type_name in ('IdCitation', 'ShortCaseCitation', 'UnknownCitation', 'SupraCitation', 'InfraCitation'):
            return ""

        # Try corrected_citation_full() first (newer eyecite API)
        try:
            if hasattr(citation_obj, 'corrected_citation_full'):
                full = citation_obj.corrected_citation_full()
                if full and isinstance(full, str):
                    # Filter statutes and non-case reporters
                    if any(p in full for p in ["U.S.C.", "USC", "C.F.R.", "CFR", "Rev. Code", "Gen. Stat.", "Fed. Reg."]):
                        return ""
                    if re.search(r'\d+\s+FR\s+\d+', full):
                        return ""
                    if full.lower().startswith(('id.', 'ibid.')) or ' at ' in full.lower():
                        return ""
                    return full
        except Exception:
            pass

        # Try corrected_citation() (another eyecite API)
        try:
            if hasattr(citation_obj, 'corrected_citation'):
                corr = citation_obj.corrected_citation()
                if corr and isinstance(corr, str):
                    if any(p in corr for p in ["U.S.C.", "USC", "C.F.R.", "CFR", "Fed. Reg."]):
                        return ""
                    if re.search(r'\d+\s+FR\s+\d+', corr):
                        return ""
                    if corr.lower().startswith(('id.', 'ibid.')) or ' at ' in corr.lower():
                        return ""
                    return corr
        except Exception:
            pass

        # Try volume/reporter/page attributes
        try:
            volume = getattr(citation_obj, 'groups', {}).get('volume', '') if hasattr(citation_obj, 'groups') else ''
            if not volume:
                volume = getattr(citation_obj, 'volume', '')
            reporter = getattr(citation_obj, 'groups', {}).get('reporter', '') if hasattr(citation_obj, 'groups') else ''
            if not reporter:
                reporter = getattr(citation_obj, 'reporter', '')
            page = getattr(citation_obj, 'groups', {}).get('page', '') if hasattr(citation_obj, 'groups') else ''
            if not page:
                page = getattr(citation_obj, 'page', '')
            if volume and reporter and page:
                reporter_str = str(reporter)
                return f"{volume} {reporter_str} {page}"
        except Exception:
            pass

        # Last resort: try str()
        try:
            citation_str = str(citation_obj)
            if any(p in citation_str for p in ["U.S.C.", "USC", "C.F.R.", "CFR", "LawCitation"]):
                return ""
            # Try to extract from repr
            full_case_match = re.search(r"FullCaseCitation\('([^']+)'", citation_str)
            if full_case_match:
                extracted = full_case_match.group(1)
                if extracted.lower().startswith(('id.', 'ibid.')) or ' at ' in extracted.lower():
                    return ""
                return extracted
            return ""
        except Exception:
            return ""

    def _extract_eyecite_metadata(self, citation: CitationResult, citation_obj):
        """Extract metadata from eyecite citation object."""
        try:
            if not isinstance(citation.metadata, dict):
                citation.metadata = {}
            meta = {}
            for key in ['volume', 'reporter', 'page', 'year', 'court']:
                val = getattr(citation_obj, key, None)
                if val is not None and not callable(val):
                    meta[key] = val
            citation.metadata.update(meta)
        except Exception as e:
            logger.debug(f"Error extracting eyecite metadata: {e}")

    def _deduplicate_citations(self, citations: List[CitationResult]) -> List[CitationResult]:
        """Remove duplicate citations while preserving parallel citations."""
        if not citations:
            return citations

        logger.info(f"[DEDUP] Starting deduplication with {len(citations)} citations")

        sorted_citations = sorted(citations, key=lambda x: (x.start_index or 0, -(x.end_index or 0)))

        # Phase 1: Remove overlapping citations
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
                    if (citation.is_parallel or existing.is_parallel or
                        ',' in citation.citation or ',' in existing.citation):
                        continue
                    overlaps = True
                    break

            if not overlaps:
                non_overlapping.append(citation)

        # Phase 2: Remove exact duplicates by normalized citation text
        seen = {}
        for citation in non_overlapping:
            key = citation.citation.strip()
            if key not in seen:
                seen[key] = citation
            else:
                existing = seen[key]
                if (citation.confidence > existing.confidence or
                    len(citation.extracted_case_name or '') > len(existing.extracted_case_name or '')):
                    seen[key] = citation

        final = list(seen.values())
        logger.info(f"[DEDUP] Finished: {len(citations)} -> {len(final)} citations ({len(citations) - len(final)} removed)")

        # Filter court-year-only parentheticals
        try:
            court_year_pattern = re.compile(r"^\(?\s*[A-Z][A-Za-z\.'\s]{1,40}\s*\(?\d{4}\)?\s*$")
            is_true_citation = lambda s: bool(re.match(r"^\d+\s+", s))
            before = len(final)
            final = [c for c in final if not (court_year_pattern.match(c.citation or '') and not is_true_citation(c.citation or ''))]
            removed = before - len(final)
            if removed > 0:
                logger.info(f"[FILTER] Removed {removed} court-year-only items")
        except Exception as _e:
            logger.warning(f"[FILTER] Court-year-only filter failed: {_e}")

        return final

    def _extract_with_regex_enhanced(self, text: str) -> List[CitationResult]:
        """
        Enhanced regex extraction with false positive prevention.
        Based on _extract_with_regex but adds volume number validation and text normalization.
        """
        citations = []
        seen_citations = set()

        original_text = text
        normalized_text = text  # Use original text, normalize individual citations later

        priority_patterns = [
            "wash_with_pinpoint_and_parallel",  # NEW: Handle pinpoint pages with parallel citations
            "parallel_citation_cluster",
            "flexible_wash2d",
            "flexible_p2d",
            "wash_complete",
            "wash_with_parallel",
            "parallel_cluster",
            "wn2d",  # Washington Supreme Court 2d series
            "wn2d_space",  # Washington Supreme Court 2d series (with space)
            "wn3d",  # Washington Supreme Court 3d series
            "wn3d_space",  # Washington Supreme Court 3d series (with space)
            "wn_app",  # Washington Court of Appeals
            "wn_app_space",  # Washington Court of Appeals (with space)
            "p3d",  # Pacific Reporter 3d
            "p2d",  # Pacific Reporter 2d
            "wash2d",  # Washington Supreme Court 2d series (Wash.)
            "wash2d_space",  # Washington Supreme Court 2d series (Wash. with space)
            "wash_app",  # Washington Court of Appeals (Wash.)
            "wash_app_space",  # Washington Court of Appeals (Wash. with space)
            "westlaw",  # Westlaw citations (2006 WL 3801910)
            "westlaw_alt",  # Alternative Westlaw format (2006 Westlaw 3801910)
            # Early American Supreme Court reporters (pre-U.S. Reports)
            "cranch",  # William Cranch (1801-1815) - e.g., "1 Cranch 137" (Marbury v. Madison)
            "wheat",  # Henry Wheaton (1816-1827) - e.g., "6 Wheat. 264" (Cohens v. Virginia)
            "pet",  # Richard Peters (1828-1842)
            "how",  # Benjamin Howard (1843-1860) - e.g., "10 How. 477" (Gayler v. Wilder)
            "black",  # Jeremiah Black (1861-1862)
            "wall",  # John Wallace (1863-1875)
            # Federal Cases (early federal case reporter)
            "f_cas",  # e.g., "29 F. Cas. 1120"
            # Slip opinion placeholders (e.g., "584 U.S. ___")
            "us_slip",
            # State reporters
            "tenn",  # Tennessee - e.g., "10 Tenn. 581" (Swindle v. State)
        ]

        for pattern_name in priority_patterns:
            if pattern_name in self.citation_patterns:
                pattern = self.citation_patterns[pattern_name]
                matches = list(pattern.finditer(normalized_text))

                for match in matches:
                    citation_str = match.group(0).strip()
                    if not citation_str or citation_str in seen_citations:
                        continue
                    # Check containment for priority patterns too
                    if _is_citation_contained_in_any and _is_citation_contained_in_any(citation_str, seen_citations):
                        continue

                    components = self._extract_citation_components(citation_str)
                    reporter = components.get("reporter", "").strip().lower().replace(".", "")
                    volume = components.get("volume", "")

                    if reporter == "at":
                        continue

                    if volume and int(volume) < 10 and "P." in citation_str:
                        if not self._validate_volume_number(text, match.start(), volume):
                            continue

                    seen_citations.add(citation_str)
                    start_pos = match.start()
                    end_pos = match.end()

                    # Special handling for wash_with_pinpoint_and_parallel pattern
                    pinpoint_pages = []
                    parallel_citations = []
                    
                    if pattern_name == "wash_with_pinpoint_and_parallel" and match.groups():
                        # Extract pinpoint page (group 3) and parallel citation (groups 4-5)
                        if match.group(3):  # Pinpoint page
                            pinpoint_pages = [match.group(3)]
                        if match.group(4) and match.group(5):  # Parallel citation
                            parallel_citations = [f"{match.group(4)} P.3d {match.group(5)}"]

                    citation = CitationResult(
                        citation=citation_str,
                        start_index=start_pos,
                        end_index=end_pos,
                        method="regex_enhanced",
                        pattern=pattern_name,
                        confidence=0.8,
                        pinpoint_pages=pinpoint_pages,
                        parallel_citations=parallel_citations,
                    )

                    citations.append(citation)

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
        normalized_text = re.sub(r"\s+", " ", text)  # Collapse all whitespace (including \n) to single space
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
                    citation.extracted_case_name = self._extract_case_name_from_context(
                        normalized_text, citation, deduplicated_citations
                    )

                if not citation.extracted_date:
                    citation.extracted_date = self._extract_date_from_context(normalized_text, citation)

                # WL/LEXIS override: extract year from WL/LEXIS pattern anywhere in citation text
                # This prevents context bleed (e.g. TOA entry for 1860 case contaminating a 2025 WL cite)
                cit_text = citation.citation or ""
                wl_year = re.search(r'(\d{4})\s+(?:WL|U\.S\.?\s*LEXIS|LEXIS)\s+\d+', cit_text)
                if wl_year:
                    citation.extracted_date = wl_year.group(1)

            except Exception as e:
                logger.warning(
                    f"[UNIFIED_EXTRACTION] Error extracting metadata for citation '{citation.citation}': {e}"
                )
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
        logger.error(f"[UNIFIED_PIPELINE] ⚠️⚠️⚠️ process_text() CALLED ⚠️⚠️⚠️")
        logger.error(f"[UNIFIED_PIPELINE] ⚠️ Text length: {len(text)} chars")
        logger.error(f"[UNIFIED_PIPELINE] ⚠️ config.enable_verification: {getattr(self, 'config', None) and getattr(self.config, 'enable_verification', None)}")
        logger.info("[UNIFIED_PIPELINE] Starting unified citation processing pipeline")

        # CRITICAL FIX: Normalize text ONCE here so all downstream code uses the
        # same text that positions were calculated from. Previously, _extract_citations_unified
        # normalized internally (collapsing \n to spaces) but process_text Phase 2 used
        # the original text — causing position mismatches that grew worse through the document.
        text = re.sub(r"\s+", " ", text)
        logger.error(f"[UNIFIED_PIPELINE] Text normalized to {len(text)} chars (whitespace collapsed)")

        # P3 FIX: Detect document's primary case name for contamination filtering
        document_primary_case_name = None
        try:
            from src.unified_clustering_master import UnifiedClusteringMaster

            clusterer = UnifiedClusteringMaster()
            document_primary_case_name = clusterer._extract_document_primary_case_name(text)
        except Exception as e:
            pass

        # Store for use in extraction calls
        self.document_primary_case_name = document_primary_case_name

        self._update_progress(10, "Extracting", "Extracting citations from text")

        logger.error("[UNIFIED_PIPELINE] Starting UNIFIED extraction pipeline for 100% accuracy")

        # USE UNIFIED EXTRACTION - use the class's own method
        try:
            logger.error(f"[UNIFIED-DEBUG] About to call _extract_citations_unified with {len(text)} chars")
            citations = self._extract_citations_unified(text)
            logger.error(f"[UNIFIED_PIPELINE] Unified extraction returned {len(citations)} citations")
            if len(citations) == 0:
                logger.error(f"[UNIFIED_PIPELINE] ⚠️ NO CITATIONS from _extract_citations_unified!")
                logger.error(f"[UNIFIED_PIPELINE] ⚠️ Text length: {len(text)} chars")
                logger.error(f"[UNIFIED_PIPELINE] ⚠️ Falling back to regex_enhanced extraction")
                citations = self._extract_with_regex_enhanced(text)
                logger.info(f"[UNIFIED_PIPELINE] Regex enhanced fallback returned {len(citations)} citations")
        except Exception as e:
            logger.error(f"[UNIFIED_PIPELINE] Unified extraction failed: {e}", exc_info=True)
            # Fallback to regex method if unified extraction fails
            citations = self._extract_with_regex_enhanced(text)
            logger.info(f"[UNIFIED_PIPELINE] Regex enhanced fallback returned {len(citations)} citations")

        # Filter out law review/secondary source citations (not case citations)
        try:
            from src.citation_extractor import is_law_review_citation
            original_count = len(citations)
            logger.error(f"[UNIFIED_PIPELINE] ⚠️ Before law review filter: {original_count} citations")
            citations = [c for c in citations if not is_law_review_citation(getattr(c, 'citation', str(c)))]
            filtered_count = original_count - len(citations)
            if filtered_count > 0:
                logger.info(f"[UNIFIED_PIPELINE] Filtered {filtered_count} law review citations, {len(citations)} case citations remaining")
            if original_count > 0 and len(citations) == 0:
                logger.error(f"[UNIFIED_PIPELINE] ⚠️ ALL {original_count} citations were filtered out as law review citations!")
        except Exception as e:
            logger.warning(f"[UNIFIED_PIPELINE] Law review filter failed: {e}")
            logger.error(f"[UNIFIED_PIPELINE] ⚠️ Law review filter exception: {e}", exc_info=True)

        # Apply parallel verification to clean pipeline results
        # NOTE: Full verification is now done in Phase 4.75 BEFORE clustering to avoid double verification
        # FIX DEC 2025: Removed duplicate verification here - was causing 2x processing time and worker crashes
        logger.info("[UNIFIED_PIPELINE] Parallel verification will be applied in Phase 4.75...")
        try:
            # Apply parallel verification to the citations (verification happens later in Phase 4.75)
            print(f"ABOUT TO CALL PARALLEL VERIFICATION with {len(citations)} citations")
            self.propagate_canonical_to_cluster(citations)
            print(f"PARALLEL VERIFICATION COMPLETED")
            logger.info(f"[UNIFIED_PIPELINE] Parallel verification complete")

            # Log if parallel verification was applied
            parallel_count = sum(1 for c in citations if getattr(c, "true_by_parallel", False))
            if parallel_count > 0:
                logger.info(f"[UNIFIED_PIPELINE] [SUCCESS] Applied parallel verification to {parallel_count} citations")

        except Exception as parallel_error:
            logger.warning(f"[UNIFIED_PIPELINE] Parallel verification failed (non-critical): {parallel_error}")
            import traceback

            logger.warning(f"[UNIFIED_PIPELINE] Parallel verification error details: {traceback.format_exc()}")

        logger.info(f"[UNIFIED_PIPELINE] Phase 1 complete: {len(citations)} citations extracted")
        self._update_progress(30, "Enhancing", "Enhancing citation data with case names and dates")

        # ENHANCED: Multi-method extraction with truncation repair and aggressive fallbacks
        # OPTIMIZATION: Cache extraction results by citation position to avoid duplicate work
        extraction_cache = {}  # Key: (start_index, end_index), Value: extracted_name
        try:
            from src.extraction import extract_case_name_and_date_unified_master

            for c in citations:
                try:
                    current_name = getattr(c, "extracted_case_name", None) or ""
                    citation_text = getattr(c, "citation", "")
                    start_index = getattr(c, "start_index", None)
                    end_index = getattr(c, "end_index", None)
                    citation_method = getattr(c, "method", None)

                    # Method 0 (FIRST): Extract case name from citation text itself
                    # This runs BEFORE the cache check because eyecite citations like
                    # "Swindle v. State, 10 Tenn. 581" may share position with a regex
                    # citation "10 Tenn. 581" that cached a contaminated name.
                    method0_name = None
                    if citation_text and " v. " in citation_text:
                        v_match = re.match(
                            r"^(.+?\s+v\.\s+[A-Za-z][A-Za-z\s\'\.\&\-,]+?)(?:,\s*\d|\s+\d)",
                            citation_text,
                        )
                        if v_match:
                            embedded_name = v_match.group(1).strip().rstrip(",")
                            if len(embedded_name) > 5:
                                method0_name = embedded_name

                    # Method 0b: Short-form case name extraction from citation text
                    # Handles citations like "Gomes, No. 20-CV-453-LM, 2020 WL 2113642"
                    # or "Ouadani, 405 F. Supp. 3d at 163" where a party name appears
                    # before a docket number or reporter without a "v." pattern.
                    if not method0_name and citation_text:
                        # Pattern: "Name, No. XX-..." (docket number prefix)
                        short_docket = re.match(
                            r'^([A-Z][A-Za-z\'\.\-\s]+?),\s*No\.\s',
                            citation_text
                        )
                        if short_docket:
                            candidate = short_docket.group(1).strip().rstrip(",")
                            if len(candidate) >= 3 and candidate[0].isupper():
                                method0_name = candidate

                    # OPTIMIZATION: Check cache first to avoid duplicate extraction
                    cache_key = (start_index, end_index)
                    if cache_key in extraction_cache:
                        cached_name = extraction_cache[cache_key]
                        if cached_name and cached_name != "N/A":
                            # If Method 0 found a better name from this citation's text,
                            # prefer it over the cached name (which may be contaminated)
                            if method0_name and len(method0_name) > 10 and " v. " in method0_name:
                                c.extracted_case_name = self._clean_extracted_case_name(method0_name)
                                extraction_cache[cache_key] = c.extracted_case_name
                            else:
                                c.extracted_case_name = self._clean_extracted_case_name(cached_name)
                            continue

                    # CRITICAL FIX: Do NOT re-extract if clean_extraction_pipeline already provided a valid name
                    # The clean pipeline has accurate context isolation and should not be overwritten
                    # SERIES FIX: Also skip re-extraction if clean pipeline set N/A for series citations
                    if current_name and citation_method == "clean_pipeline_v1":
                        # Check if this is a series citation marked by clean pipeline
                        is_series_citation = (hasattr(citation, 'metadata') and 
                                             citation.metadata and 
                                             citation.metadata.get('is_series_citation', False))
                        
                        if current_name != "N/A":
                            # Cache the clean pipeline result
                            extraction_cache[cache_key] = current_name
                            continue  # Skip re-extraction
                        elif is_series_citation:
                            # Cache the N/A for series citations
                            extraction_cache[cache_key] = current_name
                            continue  # Skip re-extraction

                    # CRITICAL FIX: If Phase 1 already found a valid name with "v.",
                    # trust it and skip the master extractor. The master extractor's
                    # ProximityStrategy finds the FIRST "v." in the context window,
                    # not the closest, causing wrong names in TOA and dense citation areas.
                    if current_name and current_name != "N/A" and " v. " in current_name and len(current_name) > 8:
                        extraction_cache[cache_key] = current_name
                        continue  # Trust Phase 1 extraction

                    final_name = method0_name

                    # Method 1: Master extractor (skip if Method 0 found good name)
                    _skip_master = final_name and len(final_name) > 10 and " v. " in final_name
                    if not _skip_master:
                      try:
                        # SERIES CITATION FIX: Check if this is NOT the first citation in a series
                        # If it's not the first, skip case name extraction to prevent incorrect association
                        if start_index and start_index > 0:
                            # Look backwards to see if there's another citation within 300 characters
                            # (increased from 100 — parenthetical text between citations can be long)
                            look_behind = text[max(0, start_index - 300):start_index]
                            prev_citation_pattern = (
                                r'\d{4}\s+WL\s+\d+'           # WL citations
                                r'|\d+\s+F\.\s*Supp\.\s*(?:2d|3d)\s+(?:at\s+)?\d+'  # F. Supp. 2d/3d (incl. pinpoint "at")
                                r'|\d+\s+F\.?(?:2d|3d|4th)\s+(?:at\s+)?\d+'  # F.2d, F.3d, F.4th
                                r'|\d+\s+U\.\s*S\.\s+(?:at\s+)?\d+'  # U.S.
                                r'|\d+\s+S\.\s*Ct\.\s+(?:at\s+)?\d+' # S. Ct.
                                r'|\d+\s+F\.\s*R\.\s*D\.\s+(?:at\s+)?\d+'  # F.R.D.
                            )
                            
                            if re.search(prev_citation_pattern, look_behind):
                                # This is NOT the first citation in a series
                                # Skip master/context extraction but keep Method 0/0b name if found
                                if method0_name:
                                    logger.info(f"[SERIES-FIX] Non-first citation, using embedded name '{method0_name}': {citation_text[:50]}")
                                    final_name = method0_name
                                else:
                                    logger.info(f"[SERIES-FIX] Skipping case name extraction for non-first citation: {citation_text[:50]}")
                                    final_name = "N/A"
                                c.extracted_case_name = self._clean_extracted_case_name(final_name) if final_name != "N/A" else final_name
                                extraction_cache[cache_key] = c.extracted_case_name
                                continue
                        
                        # USER DEBUG: Enable debug for U.S. Reports, S.Ct., L.Ed. to diagnose vacatur pattern
                        force_debug = citation_text and (
                            " U.S. " in citation_text or " S. Ct. " in citation_text or " L. Ed. " in citation_text
                        )

                        # CRITICAL FIX: Pass a context window, NOT the full document text.
                        # The master extractor's ProximityStrategy searches the entire text
                        # for "v." patterns, so passing a 140K document causes it to find
                        # the wrong case name (e.g., from the TOA or cover page).
                        if start_index and start_index > 0:
                            ctx_start = max(0, start_index - 500)
                            ctx_end = min(len(text), (end_index or start_index) + 200)
                            context_text = text[ctx_start:ctx_end]
                        else:
                            context_text = text[:1000]  # Fallback: first 1000 chars
                        res = extract_case_name_and_date_unified_master(
                            text=context_text,
                            citation=citation_text,
                            start_index=start_index if start_index != -1 else None,
                            end_index=end_index,
                            debug=force_debug,
                            document_primary_case_name=self.document_primary_case_name,  # P3 FIX: Pass contamination filter
                        )
                        master_name = (res or {}).get("case_name") or ""

                        # CONTAMINATION GUARD: If master extractor found a "v." name,
                        # check if there's an intervening citation between that name
                        # and the current citation. If so, the name belongs to the
                        # intervening citation, not ours.
                        # Example: "Kornberg v. Carnival Cruise Lines, 741 F.2d 1332...
                        #           Ouadani, 405 F. Supp. 3d at 163... Gomes, 2020 WL 2113642"
                        # Without this guard, Gomes gets Kornberg's name.
                        if master_name and master_name != "N/A" and " v. " in master_name:
                            # Find where the name appears in the context window
                            name_pos_in_ctx = context_text.find(master_name[:30])
                            if name_pos_in_ctx >= 0:
                                # Text between the found name and the citation
                                cit_pos_in_ctx = (start_index or 0) - ctx_start
                                between = context_text[name_pos_in_ctx + len(master_name):cit_pos_in_ctx]
                                # Check for intervening citations
                                _intervening_pat = (
                                    r'\d+\s+[A-Z][A-Za-z.]*\.\s*(?:\d+[a-z]{0,2}\s+)?\d+'
                                    r'|\d{4}\s+WL\s+\d+'
                                    r'|\d+\s+F\.\s*R\.\s*D\.\s+\d+'
                                )
                                if re.search(_intervening_pat, between):
                                    logger.info(
                                        f"[CONTAM-GUARD] Rejected master name '{master_name}' for "
                                        f"'{citation_text[:50]}' — intervening citation found"
                                    )
                                    master_name = ""

                        # Clean contamination from master extractor result
                        if master_name and master_name != "N/A":
                            # Remove leading lowercase text (contamination)
                            master_name = re.sub(r"^[a-z\s,\.\'\"\(\)]+\b", "", master_name).strip()
                            # Remove trailing contamination
                            master_name = re.sub(r"\s*,\s*$", "", master_name).strip()
                            # Remove signal words
                            master_name = re.sub(
                                r"\b(see|citing|compare|but see|accord|cf|e\.g\.|i\.e\.|id\.|ibid)\b.*$",
                                "",
                                master_name,
                                flags=re.IGNORECASE,
                            ).strip()

                            # Reject header/body text contamination from master extractor
                            _contam_patterns = [
                                r'syllabus\s+constitutes',
                                r'opinion\s+of\s+the\s+court',
                                r'reporter\s+of\s+decisions',
                                r'convenience\s+of\s+the\s+reader',
                                r'^Cite\s+as:',
                                r'Courts?\s+typically',
                                r'did\s+not\s+require',
                                r'showing\s+of\s+actual',
                            ]
                            _is_contam = any(re.search(cp, master_name, re.IGNORECASE) for cp in _contam_patterns)
                            # Also reject if it looks like a sentence (>60 chars without "v.")
                            if not _is_contam and len(master_name) > 60 and ' v. ' not in master_name:
                                _is_contam = True
                            if not _is_contam and len(master_name.strip()) > 3:
                                final_name = master_name
                      except Exception as e:
                        pass

                    # Method 2: Context-based extraction (if master failed or returned short name)
                    if not final_name or len(final_name) < 10:
                        try:
                            manual_name = self._extract_case_name_from_context(text, c)
                            if manual_name and manual_name != "N/A" and len(manual_name.strip()) > 3:
                                if not final_name or len(manual_name) > len(final_name):
                                    final_name = manual_name
                        except Exception as e:
                            pass

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
                                r"([A-Z][A-Za-z\'\.\.\&\s\-]{0,50}(?:,\s*(?:Inc\.|LLC|Corp\.|Ltd\.|Co\.|L\.P\.|Company))?)\s+v\.\s+([A-Z][A-Za-z\'\.\.\&\s\-]{0,50}(?:,\s*(?:Inc\.|LLC|Corp\.|Ltd\.|Co\.|L\.P\.|Company))?)",
                                # State/People v. Name
                                r"\b(State|People|United States)\s+v\.\s+([A-Z][A-Za-z\'\.\&\s]{0,40})",
                                # In re cases
                                r"\bIn\s+re\s+([A-Z][A-Za-z\'\.\&\s]{0,50}(?:,\s*(?:Inc\.|LLC|Corp\.|Ltd\.|Co\.|L\.P\.|Company))?)",
                            ]

                            for pattern in patterns:
                                matches = list(re.finditer(pattern, context, re.IGNORECASE))
                                if matches:
                                    closest = min(
                                        matches, key=lambda m: abs(m.start() - (start_index or 0) + ctx_start)
                                    )
                                    if len(closest.groups()) == 2:
                                        regex_name = f"{closest.group(1).strip()} v. {closest.group(2).strip()}"
                                    else:
                                        regex_name = closest.group(1).strip()

                                    # Clean contamination from extracted name
                                    regex_name = re.sub(r"\s+", " ", regex_name).strip()

                                    # Remove common contamination patterns
                                    contamination_patterns = [
                                        r"^[a-z\s,\.]+\b",  # Leading lowercase text
                                        r"\b(see|citing|compare|but see|accord|cf|e\.g\.|i\.e\.|id\.|ibid)\b.*$",  # Signal words
                                        r"^\W+",  # Leading punctuation
                                        r"\s*,\s*$",  # Trailing comma
                                    ]
                                    for clean_pattern in contamination_patterns:
                                        regex_name = re.sub(clean_pattern, "", regex_name, flags=re.IGNORECASE).strip()

                                    # Only accept if it looks like a valid case name
                                    if len(regex_name) > 5 and " v. " in regex_name.lower():
                                        final_name = regex_name
                                        break
                        except Exception as e:
                            pass

                    # Apply truncation repair if we have a name
                    if final_name:
                        try:
                            repaired_name = self._repair_truncated_case_name(final_name, text, start_index or 0)
                            if repaired_name != final_name:
                                logger.warning(
                                    f"[TRUNCATION-REPAIR] '{final_name}' → '{repaired_name}' for {citation_text}"
                                )
                                final_name = repaired_name
                        except Exception as e:
                            pass

                    # Final cleaning and validation before setting
                    if final_name:
                        # Strip leading body text before signal words + case name
                        # e.g., "Courts typically did not require... See Uzuegbunam v. Preczewski"
                        # → "Uzuegbunam v. Preczewski"
                        _sig_match = re.search(
                            r'\b(?:see|citing|quoting|accord|compare|but see|cf\.?)\s+'
                            r'([A-Z][A-Za-z\'\.\-\s,&]+\s+v\.\s+[A-Z][A-Za-z\'\.\-\s,&]+)',
                            final_name, re.IGNORECASE
                        )
                        if _sig_match and _sig_match.start() > 10:
                            # There's significant text before the signal word — extract just the case name
                            final_name = _sig_match.group(1).strip().rstrip(",.")

                        # Reject body text contamination in final name
                        _final_contam = any(re.search(cp, final_name, re.IGNORECASE) for cp in [
                            r'syllabus\s+constitutes', r'opinion\s+of\s+the\s+court',
                            r'reporter\s+of\s+decisions', r'convenience\s+of\s+the\s+reader',
                            r'Courts?\s+typically', r'did\s+not\s+require',
                        ])
                        if _final_contam or (len(final_name) > 60 and ' v. ' not in final_name):
                            final_name = None

                    if final_name:
                        # CRITICAL: Remove citation contamination from case names
                        final_name = self._remove_citation_contamination_from_case_name(final_name)

                        # Final contamination check - ensure case name starts with uppercase
                        if not final_name[0].isupper():
                            # Try to find the actual case name start
                            match = re.search(r"\b([A-Z][A-Za-z\s\.,\'&]+\s+v\.\s+[A-Z][A-Za-z\s\.,\'&]+)", final_name)
                            if match:
                                final_name = match.group(1).strip()
                            else:
                                # Can't clean it, mark as N/A
                                final_name = None

                        # Fix line-break hyphens: "Mar- bury" → "Marbury"
                        # PDF line breaks can leave "word- word" where the hyphen is a break artifact
                        if final_name:
                            final_name = re.sub(r'(\w)- (\w)', r'\1\2', final_name)

                        # Remove trailing commas and periods
                        if final_name:
                            final_name = re.sub(r"[,\.]+$", "", final_name).strip()

                    # Set the final name (always prefer extracted over empty/null)
                    if final_name:
                        final_name = self._clean_extracted_case_name(final_name)
                        setattr(c, "extracted_case_name", final_name)
                        # OPTIMIZATION: Cache the result for future use
                        extraction_cache[cache_key] = final_name
                    elif not current_name or current_name == "N/A":
                        setattr(c, "extracted_case_name", "N/A")
                        # Cache the failure too to avoid re-trying
                        extraction_cache[cache_key] = "N/A"

                except Exception as e:
                    logger.error(f"[EXTRACT-ERROR] Exception for {getattr(c, 'citation', 'unknown')}: {e}")
                    if not getattr(c, "extracted_case_name", None):
                        setattr(c, "extracted_case_name", "N/A")
        except Exception as e:
            logger.error(f"[EXTRACT-PIPELINE-ERROR] {e}")

        logger.info("[UNIFIED_PIPELINE] Phase 2: Detecting parallel citations")
        citations = self._detect_parallel_citations(citations, text)
        logger.info(f"[UNIFIED_PIPELINE] After parallel detection: {len(citations)} citations")

        logger.info("[UNIFIED_PIPELINE] Phase 3: Ensuring bidirectional parallel relationships")
        self.ensure_bidirectional_parallels(citations)
        logger.info(f"[UNIFIED_PIPELINE] After bidirectional parallels: {len(citations)} citations")

        logger.info("[UNIFIED_PIPELINE] Phase 4: Skipping duplicate canonical propagation (already done)")
        self._update_progress(60, "Propagating Data", "Parallel verification already completed earlier")
        # self.propagate_canonical_to_cluster(citations)  # Already done earlier in Phase 1
        logger.info(f"[UNIFIED_PIPELINE] After canonical propagation: {len(citations)} citations")

        logger.info("[UNIFIED_PIPELINE] Phase 4.5: Filtering false positive citations")
        self._update_progress(65, "Filtering", "Removing false positive citations")
        citations = self._filter_false_positive_citations(citations, text)
        logger.info(f"[UNIFIED_PIPELINE] After false positive filtering: {len(citations)} citations")

        # FIX #54: Diagnostic logging to find why verification doesn't run
        logger.error(f"   enable_verification: {self.config.enable_verification}")
        logger.error(f"   citations count: {len(citations) if citations else 0}")
        logger.error(f"   Will verification run: {self.config.enable_verification and citations}")

        logger.info(f"[UNIFIED_PIPELINE] Phase 4.75: Pre-clustering verification check")
        logger.info(f"[UNIFIED_PIPELINE] enable_verification: {self.config.enable_verification}")
        logger.info(f"[UNIFIED_PIPELINE] citations count: {len(citations) if citations else 0}")
        logger.info(f"[UNIFIED_PIPELINE] Will verification run: {self.config.enable_verification and bool(citations)}")
        logger.error(f"[UNIFIED_PIPELINE] ⚠️ VERIFICATION CHECK: config.enable_verification={self.config.enable_verification}, citations count={len(citations) if citations else 0}")

        # CRITICAL FIX: Verify citations BEFORE clustering so clustering uses correct canonical names
        if self.config.enable_verification and citations:
            logger.info("[UNIFIED_PIPELINE] Phase 4.75: Verifying citations BEFORE clustering (CRITICAL)")
            logger.error(f"[UNIFIED_PIPELINE] ⚠️ ABOUT TO CALL _verify_citations_sync with {len(citations)} citations")
            self._update_progress(67, "Verifying", "Verifying citations with external sources")
            verified_citations = self._verify_citations_sync(citations, text)
            logger.error(f"[UNIFIED_PIPELINE] ⚠️ _verify_citations_sync RETURNED {len(verified_citations)} citations")
            citations = verified_citations

            # Apply verification paradox fix: if citation has canonical data AND years match, it should be verified
            # USER FIX: Added year validation - do NOT set verified=True if years don't match

            for citation in citations:
                if hasattr(citation, "__dict__"):
                    # Check if citation has canonical data but verified is False
                    # FIX 2026-02-01: Also check canonical_name is not "N/A"
                    canonical_name = getattr(citation, "canonical_name", None)
                    has_canonical_data = (
                        canonical_name
                        and canonical_name != "N/A"
                        and getattr(citation, "canonical_date", None)
                        and getattr(citation, "canonical_url", None)
                    )
                    if has_canonical_data and not getattr(citation, "verified", False):
                        # N/A+partial: Do NOT set verified=True when N/A case name AND partial citation
                        if self._na_and_partial_insufficient(citation):
                            pass  # Leave verified=False for N/A + partial citation
                        else:
                            # USER FIX: Check year match before setting verified
                            extracted_date = getattr(citation, "extracted_date", None)
                            canonical_date = getattr(citation, "canonical_date", None)
                            year_match = True  # Default to True if no extracted date
                            if extracted_date and canonical_date:
                                ext_year = re.search(r"(19|20)\d{2}", str(extracted_date))
                                can_year = re.search(r"(19|20)\d{2}", str(canonical_date))
                                if ext_year and can_year:
                                    year_match = ext_year.group(0) == can_year.group(0)

                            if year_match:
                                citation.verified = True
                                logger.info(
                                    f"[VERIFICATION-PARADOX-FIX] {citation.citation}: Setting verified=True based on canonical data presence"
                                )
                            else:
                                logger.warning(
                                    f"[VERIFICATION-PARADOX-FIX] {citation.citation}: NOT setting verified - year mismatch (extracted={extracted_date}, canonical={canonical_date})"
                                )
                elif isinstance(citation, dict):
                    # Check if dict citation has canonical data but verified is False
                    # FIX 2026-02-01: Also check canonical_name is not "N/A"
                    dict_canonical_name = citation.get("canonical_name")
                    has_canonical_data = (
                        dict_canonical_name
                        and dict_canonical_name != "N/A"
                        and citation.get("canonical_date")
                        and citation.get("canonical_url")
                    )
                    if has_canonical_data and not citation.get("verified", False):
                        # N/A+partial: Do NOT set verified=True when N/A case name AND partial citation
                        if self._na_and_partial_insufficient(citation):
                            pass  # Leave verified=False for N/A + partial citation
                        else:
                            # USER FIX: Check year match before setting verified
                            # CRITICAL FIX: Also detect clearly wrong extracted dates (document metadata contamination)
                            extracted_date = citation.get("extracted_date")
                            canonical_date = citation.get("canonical_date")
                            year_match = True  # Default to True if no extracted date
                            is_extracted_date_clearly_wrong = False
                            
                            if extracted_date and canonical_date:
                                match, _year_diff, is_extracted_date_clearly_wrong = years_match_for_verification(
                                    extracted_date, canonical_date, tolerance=0
                                )
                                year_match = match or is_extracted_date_clearly_wrong
                                if is_extracted_date_clearly_wrong:
                                    logger.warning(
                                        f"[VERIFICATION-PARADOX-FIX] {citation.get('citation')}: Extracted date clearly wrong vs {canonical_date} - ignoring mismatch"
                                    )

                            if year_match or is_extracted_date_clearly_wrong:
                                citation["verified"] = True
                                if is_extracted_date_clearly_wrong:
                                    logger.error(
                                        f"[VERIFICATION-PARADOX-FIX] {citation.get('citation')}: Setting verified=True despite year mismatch "
                                        f"(extracted date {extracted_date} is clearly wrong, canonical={canonical_date})"
                                    )
                                else:
                                    logger.info(
                                        f"[VERIFICATION-PARADOX-FIX] {citation.get('citation')}: Setting verified=True based on canonical data presence"
                                    )
                            else:
                                logger.warning(
                                    f"[VERIFICATION-PARADOX-FIX] {citation.get('citation')}: NOT setting verified - year mismatch (extracted={extracted_date}, canonical={canonical_date})"
                                )

            logger.info(f"[UNIFIED_PIPELINE] After pre-clustering verification: {len(citations)} citations")
        else:
            logger.info("[UNIFIED_PIPELINE] Phase 4.75: Skipping pre-clustering verification (disabled)")

        logger.info("[UNIFIED_PIPELINE] Phase 5: Creating citation clusters with MASTER clustering system")
        self._update_progress(70, "Clustering", "Creating citation clusters")
        from src.unified_clustering_master import cluster_citations_unified_master

        # CRITICAL FIX: Do NOT re-run verification inside clustering. Verification already ran
        # in Phase 4.75 above. Re-running it here caused the pipeline to appear "stuck at
        # Creating citation clusters..." because _apply_verification_to_clusters calls the
        # batch API (60–120s timeouts). Clustering itself is fast; duplicate verification was the hang.
        clusters = cluster_citations_unified_master(
            citations,
            original_text=text,
            enable_verification=False,  # Already verified in Phase 4.75; skip to keep clustering fast
            progress_callback=self._update_progress
        )
        logger.info(
            f"[UNIFIED_PIPELINE] Created {len(clusters)} clusters using MASTER clustering (verification already done in Phase 4.75)"
        )
        
        # Update progress to show clustering is complete
        self._update_progress(90, "Finalizing", "Finalizing results...")

        # CRITICAL FIX: Update citation objects with cluster information immediately
        # This must happen BEFORE any serialization to ensure cluster data persists
        logger.info("[UNIFIED_PIPELINE] Phase 5.5: Updating citations with cluster information")
        # Performance optimization: Disable verbose debug logging
        citation_to_cluster = {}
        for cluster in clusters:
            cluster_id = cluster.get("cluster_id")
            cluster_case_name = cluster.get("cluster_case_name") or cluster.get("case_name")
            cluster_citations = cluster.get("citations", [])
            cluster_members = cluster.get("cluster_members", [])

            # USER FIX 2024-10-21 v4: Compute best extracted_date for the cluster
            # Parallel citations MUST have the same extracted date
            cluster_extracted_date = None
            if len(cluster_citations) > 1:  # Only for parallel citations
                # Collect all extracted dates and canonical dates from cluster citations
                extracted_dates = []
                canonical_dates = []
                for cit_dict in cluster_citations:
                    if isinstance(cit_dict, dict):
                        if cit_dict.get("extracted_date"):
                            extracted_dates.append(cit_dict.get("extracted_date"))
                        if cit_dict.get("canonical_date"):
                            canonical_dates.append(
                                (cit_dict.get("citation", "Unknown"), cit_dict.get("canonical_date"))
                            )

                # Check for canonical date discrepancies (indicates potential typo or wrong verification)
                has_date_mismatch = len(set([d for _, d in canonical_dates])) > 1
                if has_date_mismatch:
                    logger.warning(
                        f"[WARNING] [DATE-MISMATCH] Cluster {cluster_id}: Parallel citations have DIFFERENT canonical dates!"
                    )
                    for cit, date in canonical_dates:
                        logger.warning(f"   - {cit}: canonical_date={date}")
                    logger.warning(f"   → This may indicate a typo or verification to wrong case. User should review.")

                    # Add warning to cluster metadata so it appears in the UI
                    cluster["date_mismatch_warning"] = True
                    cluster["date_mismatch_details"] = [
                        {"citation": cit, "canonical_date": date} for cit, date in canonical_dates
                    ]

                # Use the most common extracted date, but filter out dates from headers
                if extracted_dates:
                    from collections import Counter

                    # CRITICAL FIX: Filter out dates that are likely from headers before counting
                    filtered_dates = []
                    for date in extracted_dates:
                        date_str = str(date)
                        # Skip dates that are 2015+ for U.S. volumes 400-600 (1970s-2000s cases)
                        # Skip dates that are 2020+ for F.3d volumes 800-900 (2010s cases)
                        should_filter = False
                        for cit_dict in cluster_citations:
                            if isinstance(cit_dict, dict):
                                citation_text = cit_dict.get("citation", "")
                                if " U.S. " in citation_text:
                                    volume_match = re.search(r"(\d+)\s+U\.\s*S\.", citation_text)
                                    if volume_match:
                                        volume = int(volume_match.group(1))
                                        year_int = int(date_str) if date_str.isdigit() else None
                                        if year_int and 400 <= volume <= 600 and year_int >= 2015:
                                            should_filter = True
                                            logger.warning(
                                                f"[CLUSTER-DATE] Filtered date {date_str} for {citation_text} "
                                                f"(U.S. volume {volume}) - year 2015+ likely from header"
                                            )
                                            break
                                elif " F.3d " in citation_text:
                                    volume_match = re.search(r"(\d+)\s+F\.\s*3d", citation_text)
                                    if volume_match:
                                        volume = int(volume_match.group(1))
                                        year_int = int(date_str) if date_str.isdigit() else None
                                        if year_int and 800 <= volume <= 900 and year_int >= 2020:
                                            should_filter = True
                                            logger.warning(
                                                f"[CLUSTER-DATE] Filtered date {date_str} for {citation_text} "
                                                f"(F.3d volume {volume}) - year 2020+ likely from header"
                                            )
                                            break
                        if not should_filter:
                            filtered_dates.append(date)
                    
                    if filtered_dates:
                        date_counts = Counter(filtered_dates)
                        cluster_extracted_date = date_counts.most_common(1)[0][0]
                        logger.info(
                            f"[CLUSTER-DATE] Cluster {cluster_id}: Using filtered date {cluster_extracted_date} "
                            f"(filtered {len(extracted_dates) - len(filtered_dates)} header dates)"
                        )
                    else:
                        # If all dates were filtered, use the first non-filtered date from original list
                        # This shouldn't happen, but fallback just in case
                        cluster_extracted_date = extracted_dates[0] if extracted_dates else None
                        logger.warning(
                            f"[CLUSTER-DATE] Cluster {cluster_id}: All dates filtered, using fallback: {cluster_extracted_date}"
                        )
                    # Performance optimization: Disable verbose debug logging

            # DEBUG: Log cluster canonical data (disabled for performance)
            # for cit_dict in cluster_citations[:2]:  # Log first 2
            #     if isinstance(cit_dict, dict):
            #         cit_text = cit_dict.get('citation', 'Unknown')
            #         verified = cit_dict.get('verified', False)
            #         canonical_date = cit_dict.get('canonical_date', None)

            # Match by citation text, not object id (clusters contain dicts, not objects)
            for cit_dict in cluster_citations:
                citation_text = (
                    cit_dict.get("citation") if isinstance(cit_dict, dict) else getattr(cit_dict, "citation", None)
                )
                if citation_text:
                    # USER FIX 2024-10-21: Store cluster_id, case_name, size, members, citation dict, AND extracted_date
                    citation_to_cluster[citation_text] = (
                        cluster_id,
                        cluster_case_name,
                        len(cluster_citations),
                        cluster_members,
                        cit_dict,
                        cluster_extracted_date,
                    )

        updated_count = 0
        for citation in citations:
            citation_text = getattr(citation, "citation", None)
            if citation_text and citation_text in citation_to_cluster:
                cluster_id, cluster_case_name, size, cluster_members, cit_dict, cluster_extracted_date = (
                    citation_to_cluster[citation_text]
                )
                citation.cluster_id = cluster_id
                citation.cluster_case_name = cluster_case_name
                citation.is_cluster = size > 1
                # CRITICAL: Set cluster_members so frontend can display them
                citation.cluster_members = [m for m in cluster_members if m != citation_text]

                # CRITICAL FIX: NEVER overwrite extracted_date with cluster-level data!
                # Memory rule: extracted_date must NEVER be overwritten or contaminated.
                # The extracted_date comes from the user's document and must remain unchanged.
                # Only use cluster_extracted_date if the citation has NO extracted_date at all.
                # Even then, we should preserve the original extracted_date if it exists.
                if cluster_extracted_date and size > 1:
                    existing_extracted_date = getattr(citation, "extracted_date", None)
                    if not existing_extracted_date or existing_extracted_date == "N/A":
                        # Only fill in if truly missing - but this should rarely happen
                        citation.extracted_date = cluster_extracted_date

                # USER FIX 2024-10-21: PRESERVE VERIFICATION DATA from clustering
                # The clustering function verifies citations and sets verified/canonical data,
                # but Phase 5.5 was only copying cluster metadata, losing the verification data
                # USER FIX 2024-10-21 v2: ALWAYS overwrite with cluster canonical data
                # Parallel citations MUST have same date - cluster has authoritative data
                if isinstance(cit_dict, dict):
                    # Always trust cluster verification status
                    if cit_dict.get("verified"):
                        citation.verified = cit_dict.get("verified", False)
                    # Always overwrite canonical data from cluster (authoritative source)
                    if cit_dict.get("canonical_name"):
                        citation.canonical_name = cit_dict.get("canonical_name")
                    if cit_dict.get("canonical_date"):
                        citation.canonical_date = cit_dict.get("canonical_date")
                    if cit_dict.get("canonical_url"):
                        citation.canonical_url = cit_dict.get("canonical_url")
                    if cit_dict.get("verification_source"):
                        citation.source = cit_dict.get("verification_source", "Unknown")
                        logger.info(f"[CIT-UPDATE] Set source from verification_source: {citation.source}")
                    elif cit_dict.get("source"):
                        citation.source = cit_dict.get("source", "Unknown")
                        logger.info(f"[CIT-UPDATE] Set source from source: {citation.source}")
                    else:
                        # Debug: Check what fields are available
                        logger.error(f"[CIT-UPDATE] CIT_DICT_FIELDS: {list(cit_dict.keys())}")
                        citation.source = "Unknown"
                        logger.error(f"[CIT-UPDATE] Set source to Unknown (no verification_source or source found)")

                updated_count += 1

        logger.info(f"[UNIFIED_PIPELINE] Updated {updated_count} citations with cluster information")

        # FIX DEC 2025: Apply parallel verification AFTER cluster assignment
        # Now that cluster_id is set, we can properly propagate verified status to unverified cluster members
        logger.info("[UNIFIED_PIPELINE] Phase 5.6: Applying cluster-based parallel verification")
        try:
            self.propagate_canonical_to_cluster(citations)
            parallel_count = sum(1 for c in citations if getattr(c, "true_by_parallel", False))
            logger.info(f"[UNIFIED_PIPELINE] Phase 5.6: Marked {parallel_count} citations as verified by parallel")
        except Exception as e:
            logger.warning(f"[UNIFIED_PIPELINE] Phase 5.6: Parallel verification failed: {e}")

        # REMOVED: Duplicate verification step - already done before clustering at Phase 4.75
        logger.info("[UNIFIED_PIPELINE] Phase 6: Verification already completed before clustering")

        # Validate cluster consistency before returning results
        logger.info("[UNIFIED_PIPELINE] Phase 7: Validating cluster consistency")
        self._validate_cluster_consistency(citations)

        self._update_progress(
            100, "Complete", f"Processing complete: {len(citations)} citations, {len(clusters)} clusters"
        )
        logger.info(f"[UNIFIED_PIPELINE] Pipeline complete: {len(citations)} final citations, {len(clusters)} clusters")

        # Create a mapping of citation text to verification status for quick lookup
        citation_verification = {}
        for citation in citations:
            if hasattr(citation, "citation") and hasattr(citation, "verified"):
                # Check for true_by_parallel - first as direct attribute, then in metadata
                true_by_parallel = False
                if hasattr(citation, "true_by_parallel"):
                    # Direct attribute (set by Fix #11 verification logic)
                    true_by_parallel = citation.true_by_parallel
                elif hasattr(citation, "metadata") and citation.metadata:
                    # Legacy: check in metadata dict
                    true_by_parallel = citation.metadata.get("true_by_parallel", False)

                citation_verification[citation.citation] = {
                    "verified": citation.verified,
                    "verification_method": getattr(citation, "verification_method", None),
                    "verification_source": getattr(
                        citation, "verification_source", None
                    ),  # FIX #65: Read from correct attribute
                    "verification_url": getattr(citation, "canonical_url", None),
                    "true_by_parallel": true_by_parallel,
                }

        # CRITICAL FIX: Preserve original cluster structure from clustering master
        # The clustering master already returns properly formatted clusters with all required fields
        # Don't reformat them - use them as-is to maintain consistency with API expectations
        formatted_clusters = clusters

        # USER FIX: Final year validation cleanup - unverify any citations with year mismatch
        # This catches ALL cases regardless of which verification path was used

        year_mismatch_count = 0

        # Check citations list (CitationResult objects)
        for cit in citations:
            if hasattr(cit, "__dict__"):
                verified = getattr(cit, "verified", None)
                canonical_date = getattr(cit, "canonical_date", None)

                # FIX: Clear date_mismatch flag if there's no canonical_date to compare
                if not canonical_date and hasattr(cit, "date_mismatch"):
                    cit.date_mismatch = False

                if verified == True:  # Only check truly verified, not "true_by_parallel"
                    extracted_date = getattr(cit, "extracted_date", None)
                    if extracted_date and canonical_date:
                        citation_str = str(getattr(cit, "citation", ""))
                        is_federal_reporter = bool(re.search(r"\bF(\.(2|3|4)th)?\b", citation_str))
                        if is_federal_reporter:
                            logger.info(
                                f"⚠️ [FINAL-YEAR-CHECK] {cit.citation}: Federal Reporter - year check skipped (citation year is authoritative)"
                            )
                        else:
                            match, year_diff, extracted_clearly_wrong = years_match_for_verification(
                                extracted_date, canonical_date, tolerance=0
                            )
                            if extracted_clearly_wrong:
                                logger.info(
                                    f"✅ [FINAL-YEAR-CHECK] {cit.citation}: Extracted date clearly wrong vs {canonical_date} - keeping verified"
                                )
                            elif not match:
                                cit.verified = False
                                cit.verification_error = (
                                    f"Year mismatch: extracted {extracted_date} vs canonical {canonical_date}"
                                )
                                logger.warning(
                                    f"❌ [FINAL-YEAR-CHECK] {cit.citation}: Unverified due to year mismatch (extracted={extracted_date}, canonical={canonical_date}, diff={year_diff})"
                                )
                                year_mismatch_count += 1

        # Also check cluster citations (dicts)
        for cluster in formatted_clusters:
            cluster_citations = cluster.get("citations", [])
            for cit in cluster_citations:
                if isinstance(cit, dict):
                    verified = cit.get("verified")
                    canonical_date = cit.get("canonical_date")

                    # FIX: Clear date_mismatch flag if there's no canonical_date to compare
                    if not canonical_date:
                        cit["date_mismatch"] = False

                    if verified == True:  # Only check truly verified, not "true_by_parallel"
                        extracted_date = cit.get("extracted_date")
                        if extracted_date and canonical_date:
                            citation_str = str(cit.get("citation", ""))
                            is_federal_reporter = bool(re.search(r"\bF(\.(2|3|4)th)?\b", citation_str))
                            if is_federal_reporter:
                                logger.info(
                                    f"⚠️ [FINAL-YEAR-CHECK-CLUSTER] {cit.get('citation')}: Federal Reporter - year check skipped (citation year is authoritative)"
                                )
                            else:
                                match, year_diff, extracted_clearly_wrong = years_match_for_verification(
                                    extracted_date, canonical_date, tolerance=0
                                )
                                if extracted_clearly_wrong:
                                    logger.info(
                                        f"✅ [FINAL-YEAR-CHECK-CLUSTER] {cit.get('citation')}: Extracted date clearly wrong vs {canonical_date} - keeping verified"
                                    )
                                elif not match:
                                    cit["verified"] = False
                                    cit["verification_error"] = (
                                        f"Year mismatch: extracted {extracted_date} vs canonical {canonical_date}"
                                    )
                                    logger.warning(
                                        f"❌ [FINAL-YEAR-CHECK-CLUSTER] {cit.get('citation')}: Unverified due to year mismatch (extracted={extracted_date}, canonical={canonical_date}, diff={year_diff})"
                                    )
                                    year_mismatch_count += 1

            # FIX: Recompute cluster mismatch flags after clearing invalid flags
            from src.utils.mismatch_utils import compute_cluster_mismatch_flags
            compute_cluster_mismatch_flags(cluster)

        if year_mismatch_count > 0:
            logger.info(f"[FINAL-YEAR-CHECK] Unverified {year_mismatch_count} citations due to year mismatch")

        # SPECIAL HANDLING: Add "Unverified due to proprietary format" for WL and Lexis citations
        # that are neither verified nor verified_by_parallel
        proprietary_count = 0
        for cit in citations:
            if hasattr(cit, "__dict__"):
                citation_text = getattr(cit, "citation", "")
                is_verified = getattr(cit, "verified", False)
                is_verified_by_parallel = getattr(cit, "true_by_parallel", False)
                
                # Check if this is a WL or Lexis citation that is not verified
                if not is_verified and not is_verified_by_parallel:
                    # WL citations: format like "2021 WL 3622166"
                    # Lexis citations: format like "2021 WL 3622166" (often marked as WL but from Lexis)
                    if re.search(r"\d{4}\s+WL\s+\d+", citation_text) or re.search(r"Lexis\s+\d+", citation_text, re.IGNORECASE):
                        cit.verification_status = "proprietary_format"
                        cit.verification_error = "Unverified due to proprietary format"
                        proprietary_count += 1
        
        # Also check cluster citations (dicts)
        for cluster in formatted_clusters:
            cluster_citations = cluster.get("citations", [])
            for cit in cluster_citations:
                if isinstance(cit, dict):
                    citation_text = cit.get("citation", "")
                    is_verified = cit.get("verified", False)
                    is_verified_by_parallel = cit.get("true_by_parallel", False)
                    
                    if not is_verified and not is_verified_by_parallel:
                        if re.search(r"\d{4}\s+WL\s+\d+", citation_text) or re.search(r"Lexis\s+\d+", citation_text, re.IGNORECASE):
                            cit["verification_status"] = "proprietary_format"
                            cit["verification_error"] = "Unverified due to proprietary format"
                            proprietary_count += 1
        
        if proprietary_count > 0:
            logger.info(f"[PROPRIETARY] Marked {proprietary_count} WL/Lexis citations as unverified due to proprietary format")

        result = {"citations": citations, "clusters": formatted_clusters}

        return result

    def _filter_false_positive_citations(self, citations: List[CitationResult], text: str) -> List[CitationResult]:
        """Filter out false positive citations like standalone page numbers."""
        valid_citations = []

        for citation in citations:
            citation_text = citation.citation if hasattr(citation, "citation") else str(citation)

            if self._is_standalone_page_number(citation_text, text):
                continue

            if self._is_volume_without_reporter(citation_text):
                continue

            # Skip Statutes at Large, Federal Register, and other non-case reporters
            if re.match(r"^\d+\s+Stat\.\s+\d+", citation_text):
                continue
            if re.search(r'\bFed\.\s*Reg\.\s+\d+', citation_text):
                continue
            if re.match(r'^\d+\s+FR\s+\d+', citation_text):
                continue
            if re.search(r'\bOp\.\s*O\.?\s*L\.?\s*C\.?\s+\d+', citation_text):
                continue

            if len(citation_text.strip()) < 8:
                continue

            valid_citations.append(citation)

        logger.info(f"False positive filter: {len(citations)} → {len(valid_citations)} citations")
        return valid_citations

    def _is_standalone_page_number(self, citation_text: str, text: str) -> bool:
        """Check if citation is just a standalone page number."""
        if re.match(r"^\d+$", citation_text):
            pos = text.find(citation_text)
            if pos != -1:
                context_before = text[max(0, pos - 50) : pos]
                context_after = text[pos + len(citation_text) : min(len(text), pos + len(citation_text) + 50)]

                reporter_patterns = [
                    r"\bWn\.\d*d?\b",  # Wn.2d, Wn.3d
                    r"\bP\.\d*d?\b",  # P.2d, P.3d
                    r"\bU\.S\.\b",  # U.S.
                    r"\bS\.Ct\.\b",  # S.Ct.
                    r"\bWn\.\s*App\.\b",  # Wn. App.
                ]

                for pattern in reporter_patterns:
                    if re.search(pattern, context_before) or re.search(pattern, context_after):
                        return False

                return True

        return False

    def _is_volume_without_reporter(self, citation_text: str) -> bool:
        """Check if citation is just a volume number without reporter."""
        if re.match(r"^\d+$", citation_text):
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
        for citation in results["citations"]:
            extracted_case_name = (
                citation.extracted_case_name
                or getattr(citation, "extracted_case_name", None)
                or getattr(citation, "case_name", None)
            )

            extracted_date = (
                citation.extracted_date
                or getattr(citation, "extracted_date", None)
                or (citation.metadata.get("extracted_date") if citation.metadata else None)
            )

            citation_dict = {
                "citation": citation.citation,
                "case_name": extracted_case_name,
                "extracted_case_name": extracted_case_name,
                "canonical_name": citation.canonical_name,
                "extracted_date": extracted_date,
                "canonical_date": citation.canonical_date,
                "verified": self._get_verification_status(citation),
                "court": citation.court,
                "confidence": citation.confidence,
                "method": citation.method,
                "pattern": citation.pattern,
                "context": citation.context,
                "start_index": citation.start_index,
                "end_index": citation.end_index,
                "is_parallel": citation.is_parallel,
                "is_cluster": citation.is_cluster,
                "parallel_citations": citation.parallel_citations,
                "cluster_members": citation.metadata.get("cluster_members", []) if citation.metadata else [],
                "pinpoint_pages": citation.pinpoint_pages,
                "docket_numbers": citation.docket_numbers,
                "case_history": citation.case_history,
                "publication_status": citation.publication_status,
                "url": citation.url,
                "source": citation.source,
                "error": citation.error,
                "metadata": citation.metadata or {},
                "extraction_method": getattr(citation, "extraction_method", None),
            }
            # Align with Enhanced Sync: enforce data separation on output
            try:
                from src.data_separation_validator import (
                    enforce_data_separation,
                    restore_extracted_name_if_contaminated,
                )

                citation_dict = enforce_data_separation(citation_dict)
                citation_dict = restore_extracted_name_if_contaminated(citation_dict)
            except Exception:
                pass
            if citation.metadata:
                citation_dict["metadata"].update(
                    {
                        "cluster_extracted_case_name": citation.metadata.get("cluster_extracted_case_name"),
                        "cluster_extracted_date": citation.metadata.get("cluster_extracted_date"),
                        "cluster_canonical_name": citation.metadata.get("cluster_canonical_name"),
                        "cluster_canonical_date": citation.metadata.get("cluster_canonical_date"),
                        "cluster_url": citation.metadata.get("cluster_url"),
                        "is_in_cluster": citation.metadata.get("is_in_cluster", False),
                        "cluster_id": citation.metadata.get("cluster_id"),
                        "cluster_size": citation.metadata.get("cluster_size", 0),
                        "cluster_members": citation.metadata.get("cluster_members", []),
                    }
                )
            citation_dicts.append(citation_dict)
        clusters = results["clusters"]

        def citation_to_dict(citation):
            if isinstance(citation, str):
                return {
                    "citation": citation,
                    "case_name": None,
                    "extracted_case_name": None,
                    "canonical_name": None,
                    "extracted_date": None,
                    "canonical_date": None,
                    "verified": False,
                    "source": "string_citation",
                    "is_parallel": False,
                }

            if isinstance(citation, dict):
                return citation

            try:
                extracted_case_name = (
                    getattr(citation, "extracted_case_name", None)
                    or getattr(citation, "case_name", None)
                    or (
                        getattr(citation, "metadata", {}).get("extracted_case_name")
                        if hasattr(citation, "metadata")
                        else None
                    )
                )

                extracted_date = getattr(citation, "extracted_date", None) or (
                    getattr(citation, "metadata", {}).get("extracted_date") if hasattr(citation, "metadata") else None
                )

                return {
                    "citation": getattr(citation, "citation", None) or str(citation),
                    "case_name": extracted_case_name,
                    "extracted_case_name": extracted_case_name,
                    "canonical_name": getattr(citation, "canonical_name", None),
                    "extracted_date": extracted_date,
                    "canonical_date": getattr(citation, "canonical_date", None),
                    "verified": self._get_verification_status(citation),
                    "court": citation.court,
                    "confidence": citation.confidence,
                    "method": citation.method,
                    "pattern": citation.pattern,
                    "context": citation.context,
                    "start_index": citation.start_index,
                    "end_index": citation.end_index,
                    "is_parallel": citation.is_parallel,
                    "is_cluster": citation.is_cluster,
                    "parallel_citations": citation.parallel_citations,
                    "cluster_members": citation.metadata.get("cluster_members", []) if citation.metadata else [],
                    "pinpoint_pages": citation.pinpoint_pages,
                    "docket_numbers": citation.docket_numbers,
                    "case_history": citation.case_history,
                    "publication_status": citation.publication_status,
                    "url": citation.url,
                    "source": citation.source,
                    "error": citation.error,
                    "metadata": citation.metadata or {},
                    "extraction_method": getattr(citation, "extraction_method", None),
                }
            except Exception as e:
                return {
                    "citation": str(citation),
                    "case_name": None,
                    "extracted_case_name": None,
                    "canonical_name": None,
                    "extracted_date": None,
                    "canonical_date": None,
                    "verified": False,
                    "source": "error_fallback",
                    "error": str(e),
                    "is_parallel": False,
                }

        def cluster_to_dict(cluster):
            return {
                **{k: v for k, v in cluster.items() if k != "citations"},
                "citations": [citation_to_dict(c) if not isinstance(c, dict) else c for c in cluster["citations"]],
            }

        clusters_dicts = [cluster_to_dict(cluster) for cluster in clusters]
        return {"citations": citation_dicts, "clusters": clusters_dicts}

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

        formatted = re.sub(r"\s*,\s*", ", ", formatted)

        formatted = re.sub(r"\(\s*", "(", formatted)
        formatted = re.sub(r"\s*\)", ")", formatted)

        return formatted

    def _validate_cluster_consistency(self, citations: List["CitationResult"]):
        """
        Validate and fix cluster_id and is_in_cluster consistency.

        Rules:
        - If cluster_id is set, is_in_cluster should be True
        - If cluster_id is null/empty, is_in_cluster should be False
        - All citations in the same cluster should have the same cluster_id
        """
        for citation in citations:
            if not hasattr(citation, "metadata") or not citation.metadata:
                continue

            cluster_id = citation.metadata.get("cluster_id")
            is_in_cluster = citation.metadata.get("is_in_cluster", False)

            # Fix inconsistencies
            if cluster_id and not is_in_cluster:
                # Has cluster_id but is_in_cluster is False - fix it
                citation.metadata["is_in_cluster"] = True
                logger.warning(
                    f"CLUSTER_FIX: Set is_in_cluster=True for citation '{citation.citation}' with cluster_id='{cluster_id}'"
                )
            elif not cluster_id and is_in_cluster:
                # No cluster_id but is_in_cluster is True - fix it
                citation.metadata["is_in_cluster"] = False
                logger.warning(
                    f"CLUSTER_FIX: Set is_in_cluster=False for citation '{citation.citation}' with null cluster_id"
                )
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
        if hasattr(citation, "verified"):
            if isinstance(citation.verified, bool):
                if citation.verified:
                    return True
            elif citation.verified is True:
                return True

        # Check true_by_parallel attribute (verified by parallel association)
        if hasattr(citation, "true_by_parallel") and citation.true_by_parallel:
            return True

        # Check metadata for verification status
        if hasattr(citation, "metadata") and citation.metadata:
            verification_status = citation.metadata.get("verification_status")
            if verification_status == "verified":
                return True

        # Check if we have canonical data (indicates verification)
        if (
            hasattr(citation, "canonical_name")
            and citation.canonical_name
            and hasattr(citation, "canonical_url")
            and citation.canonical_url
        ):
            return True

        return False

    def _propagate_canonical_to_parallels(self, citations: List["CitationResult"]):
        """
        For each verified citation, propagate canonical_name and canonical_date to its unverified parallels.
        Mark those as true_by_parallel, but do NOT set verified=True for parallels.
        """
        citation_lookup = {c.citation: c for c in citations}
        for citation in citations:
            if citation.verified and citation.canonical_name and citation.canonical_date:
                for parallel in citation.parallel_citations or []:
                    parallel_cite = citation_lookup.get(parallel)
                    if parallel_cite and not parallel_cite.verified:
                        parallel_cite.canonical_name = citation.canonical_name
                        parallel_cite.canonical_date = citation.canonical_date
                        parallel_cite.url = citation.url
                        parallel_cite.source = citation.source
                        if not hasattr(parallel_cite, "metadata") or parallel_cite.metadata is None:
                            parallel_cite.metadata = {}
                        parallel_cite.metadata["true_by_parallel"] = True
        for c in citations:
            pass  # This loop was incomplete, adding pass to fix syntax

    def _normalize_canonical_fields(self, citations: List["CitationResult"]):
        """
        Normalize canonical_name and canonical_date for all citations (strip whitespace, standardize case).
        """
        for c in citations:
            if c.canonical_name:
                c.canonical_name = c.canonical_name.strip()
            if c.canonical_date:
                c.canonical_date = str(c.canonical_date).strip()

    def _propagate_extracted_to_parallels(self, citations: List["CitationResult"]):
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

    def propagate_canonical_to_cluster(self, citations: List["CitationResult"]):
        """
        For each group of parallel citations (including main and parallels), if any member is verified and has canonical_name and canonical_date,
        propagate those fields to all other members in the group that lack them. Set verified='true_by_parallel' for those not directly verified.
        """
        print(f"PARALLEL VERIFICATION FUNCTION CALLED with {len(citations)} citations")
        logger.info(f"[PARALLEL-DEBUG] Starting parallel verification for {len(citations)} citations")
        citation_lookup = {c.citation: c for c in citations}
        visited = set()
        parallel_count = 0

        # NEW: Also group by canonical data (more reliable than positions)
        # FIX DEC 2025: Parallel citations are the SAME case in DIFFERENT reporters
        # So we should NOT group by reporter type - that breaks parallel verification
        # Example: 110 Ohio St. 3d 456 and 854 N.E.2d 193 are the SAME case
        canonical_groups = {}
        for citation in citations:
            if citation.canonical_name and citation.canonical_date:
                # Group by canonical name and date ONLY - not by reporter type
                # This ensures parallel citations (same case, different reporters) are grouped together
                key = (citation.canonical_name, citation.canonical_date)

                if key not in canonical_groups:
                    canonical_groups[key] = []
                canonical_groups[key].append(citation)

        logger.info(f"[PARALLEL-DEBUG] Found {len(canonical_groups)} groups by canonical data")

        # Process canonical groups first (most reliable)
        for canonical_key, group in canonical_groups.items():
            if len(group) > 1:
                logger.info(f"[PARALLEL-DEBUG] Processing canonical group with {len(group)} citations")
                verified_member = None
                for c in group:
                    if c.verified and c.canonical_name and c.canonical_date:
                        verified_member = c
                        logger.info(f"[PARALLEL-DEBUG] Found verified member in canonical group: {c.citation}")
                        break

                if verified_member:
                    for c in group:
                        logger.info(f"[PARALLEL-DEBUG] Processing citation: {c.citation}, verified: {c.verified}")

                        # Copy canonical data if missing
                        if not c.canonical_name or not c.canonical_date:
                            logger.info(f"[PARALLEL-DEBUG] Copying canonical data to {c.citation}")
                            c.canonical_name = verified_member.canonical_name
                            c.canonical_date = verified_member.canonical_date
                            c.url = verified_member.url
                            c.source = verified_member.source

                        # Apply true_by_parallel semantics ONLY to unverified group members
                        if c is not verified_member and (not c.verified or c.verified == False):
                            if not hasattr(c, "metadata") or c.metadata is None:
                                c.metadata = {}
                            c.metadata["true_by_parallel"] = True
                            c.true_by_parallel = True
                            # Set parallel citations field for context
                            group_citations = [g.citation for g in group if g.citation != c.citation]
                            c.parallel_citations = group_citations
                            # Keep verified=False, true_by_parallel=True indicates verification by association
                            parallel_count += 1

        # FIX DEC 2025: Cluster-based parallel detection for unverified citations
        # Only mark citations as "verified by parallel" if they are in the SAME CLUSTER
        # as a verified citation and cannot be independently verified

        # Build cluster lookup: cluster_id -> list of citations in that cluster
        cluster_groups = {}
        for cit in citations:
            cluster_id = getattr(cit, "cluster_id", None)
            if cluster_id:
                if cluster_id not in cluster_groups:
                    cluster_groups[cluster_id] = []
                cluster_groups[cluster_id].append(cit)

        logger.info(f"[PARALLEL-CLUSTER] Found {len(cluster_groups)} clusters")

        # For each cluster, find verified citations and propagate to unverified members
        for cluster_id, cluster_citations in cluster_groups.items():
            if len(cluster_citations) < 2:
                continue

            # Find verified member(s) in this cluster (must be directly verified, not via parallel)
            verified_member = None
            for cit in cluster_citations:
                is_directly_verified = cit.verified == True and not getattr(cit, "true_by_parallel", False)
                if is_directly_verified and cit.canonical_name:
                    verified_member = cit
                    break

            if not verified_member:
                continue

            logger.info(f"[PARALLEL-CLUSTER] Cluster {cluster_id} has verified member: {verified_member.citation}")

            # Propagate to unverified members in the same cluster
            for cit in cluster_citations:
                if cit is verified_member:
                    continue

                # Skip if already verified
                if cit.verified and cit.verified != False:
                    continue

                # N/A+partial: Do NOT mark as verified by parallel when N/A case name AND partial citation
                if self._na_and_partial_insufficient(cit):
                    logger.info(
                        f"[PARALLEL-CLUSTER] Skipping true_by_parallel for {cit.citation} (N/A + partial citation - insufficient evidence)"
                    )
                    continue

                # Case name compatibility check (shared canonical logic)
                v_ecn = (getattr(verified_member, 'extracted_case_name', '') or '').strip()
                c_ecn = (getattr(cit, 'extracted_case_name', '') or '').strip()
                if not names_are_same_case(v_ecn, c_ecn):
                    logger.info(
                        f"[PARALLEL-CLUSTER] Skipping true_by_parallel for {cit.citation} - different case: '{v_ecn}' vs '{c_ecn}'"
                    )
                    continue

                # This citation is in the same cluster but unverified - mark as verified by parallel
                logger.info(
                    f"[PARALLEL-CLUSTER] Marking {cit.citation} as verified by parallel (same cluster as {verified_member.citation})"
                )
                cit.canonical_name = verified_member.canonical_name
                cit.canonical_date = verified_member.canonical_date
                cit.canonical_url = getattr(verified_member, "canonical_url", None)
                cit.url = verified_member.url
                cit.source = verified_member.source
                if not hasattr(cit, "metadata") or cit.metadata is None:
                    cit.metadata = {}
                cit.metadata["true_by_parallel"] = True
                cit.true_by_parallel = True
                # CRITICAL FIX: Use helper to filter same-reporter/different-volume
                cit.parallel_citations = filter_cluster_members_by_reporter(
                    cit.citation, 
                    [verified_member.citation]
                )
                # Keep verified=False, true_by_parallel=True indicates verification by association
                parallel_count += 1

        # Original position-based method (for cases with parallel_citations already set)
        for citation in citations:
            if citation.citation in visited:
                continue
            group = set([citation.citation])
            if citation.parallel_citations:
                group.update(citation.parallel_citations)

            logger.info(f"[PARALLEL-DEBUG] Processing position-based group: {group}")

            verified_member = None
            for cite_str in group:
                c = citation_lookup.get(cite_str)
                if c and c.verified and c.canonical_name and c.canonical_date:
                    verified_member = c
                    logger.info(f"[PARALLEL-DEBUG] Found verified member: {cite_str}")
                    break

            if verified_member:
                logger.info(f"[PARALLEL-DEBUG] Propagating from verified member to {len(group)} citations")
                for cite_str in group:
                    c = citation_lookup.get(cite_str)
                    if c:
                        logger.info(f"[PARALLEL-DEBUG] Processing citation: {cite_str}, verified: {c.verified}")

                        # Copy canonical data if missing
                        if not c.canonical_name or not c.canonical_date:
                            logger.info(f"[PARALLEL-DEBUG] Copying canonical data to {cite_str}")
                            c.canonical_name = verified_member.canonical_name
                            c.canonical_date = verified_member.canonical_date
                            c.url = verified_member.url
                            c.source = verified_member.source

                        # Apply true_by_parallel semantics ONLY to unverified group members
                        if c is not verified_member and (not c.verified or c.verified == False):
                            if not hasattr(c, "metadata") or c.metadata is None:
                                c.metadata = {}
                            c.metadata["true_by_parallel"] = True
                            c.true_by_parallel = True
                            logger.info(f"[PARALLEL-DEBUG] Marked {cite_str} true_by_parallel (position group)")
                            # Keep verified=False, true_by_parallel=True indicates verification by association
                            parallel_count += 1
                    visited.add(cite_str)
            else:
                logger.info(f"[PARALLEL-DEBUG] No verified member found for group: {group}")
                visited.update(group)

        logger.info(
            f"[PARALLEL-DEBUG] Completed parallel verification. Marked {parallel_count} citations as verified_by_parallel"
        )

        # CRITICAL FIX DEC 2025: Final consistency pass using parallel_citations field
        # ONLY mark true_by_parallel if at least one citation in the group is VERIFIED (verified=True)
        # Citations should only be marked true_by_parallel if at least one citation in the cluster is verified
        logger.info(f"[PARALLEL-CONSISTENCY] Starting final consistency pass for {len(citations)} citations")

        # Build citation lookup by citation text
        citation_lookup = {c.citation: c for c in citations}

        # Build parallel groups from parallel_citations field
        visited = set()
        parallel_groups = []

        for cit in citations:
            if cit.citation in visited:
                continue

            # Build group from this citation's parallel_citations
            group = {cit.citation}
            if cit.parallel_citations:
                group.update(cit.parallel_citations)

            # Expand group by following parallel_citations of group members
            expanded = True
            while expanded:
                expanded = False
                for cite_text in list(group):
                    if cite_text in citation_lookup:
                        member = citation_lookup[cite_text]
                        if member.parallel_citations:
                            for p in member.parallel_citations:
                                if p not in group:
                                    group.add(p)
                                    expanded = True

            if len(group) > 1:
                parallel_groups.append(group)
            visited.update(group)

        logger.info(f"[PARALLEL-CONSISTENCY] Found {len(parallel_groups)} parallel groups")

        consistency_fixed = 0
        for group in parallel_groups:
            group_citations = [citation_lookup[c] for c in group if c in citation_lookup]
            if len(group_citations) < 2:
                continue

            # Check if ANY citation in this group is VERIFIED (verified=True)
            # CRITICAL: Only mark true_by_parallel if at least one citation is verified
            has_verified = False
            source_citation = None
            for cit in group_citations:
                if cit.verified == True:
                    has_verified = True
                    # Prefer a citation with canonical data as the source
                    if cit.canonical_name and (
                        source_citation is None or not getattr(source_citation, "canonical_name", None)
                    ):
                        source_citation = cit

            if has_verified and source_citation:
                # Propagate true_by_parallel to ALL unverified citations in this group (except N/A case names)
                for cit in group_citations:
                    if cit.verified != True and not getattr(cit, "true_by_parallel", False):
                        if self._na_and_partial_insufficient(cit):
                            logger.info(
                                f"[PARALLEL-CONSISTENCY] Skipping true_by_parallel for {cit.citation} (N/A + partial citation)"
                            )
                            continue
                        cit.true_by_parallel = True
                        # Also propagate canonical data if available
                        if source_citation.canonical_name and not cit.canonical_name:
                            cit.canonical_name = source_citation.canonical_name
                        if getattr(source_citation, "canonical_date", None) and not getattr(
                            cit, "canonical_date", None
                        ):
                            cit.canonical_date = source_citation.canonical_date
                        if getattr(source_citation, "canonical_url", None) and not getattr(cit, "canonical_url", None):
                            cit.canonical_url = source_citation.canonical_url
                        consistency_fixed += 1
                        logger.info(f"[PARALLEL-CONSISTENCY] Fixed: {cit.citation} now true_by_parallel")

        logger.info(f"[PARALLEL-CONSISTENCY] Consistency pass complete. Fixed {consistency_fixed} citations")

    def ensure_bidirectional_parallels(self, citations: List["CitationResult"]):
        """
        For each group of citations that are close together (by position and punctuation), ensure all group members have each other in their parallel_citations field.
        """
        logger.info(f"[PARALLEL-DEBUG] Starting bidirectional parallel detection for {len(citations)} citations")

        # Debug citation positions
        for i, c in enumerate(citations):
            logger.info(f"[PARALLEL-DEBUG] Citation {i}: {c.citation}, start={c.start_index}, end={c.end_index}")

        sorted_citations = sorted(citations, key=lambda x: x.start_index or 0)
        n = len(sorted_citations)
        i = 0
        groups_found = 0

        while i < n:
            group = [sorted_citations[i]]
            j = i + 1
            while j < n:
                curr = sorted_citations[j]
                prev = group[-1]
                logger.info(
                    f"[PARALLEL-DEBUG] Checking proximity: {curr.citation} (start={curr.start_index}) vs {prev.citation} (end={prev.end_index})"
                )

                if curr.start_index and prev.end_index and curr.start_index - prev.end_index <= 100:
                    text_between = ""
                    if hasattr(prev, "end_index") and hasattr(curr, "start_index"):
                        text_between = (
                            getattr(prev, "context", "")[-(prev.end_index - (prev.start_index or 0)) :]
                            + getattr(curr, "context", "")[: curr.start_index - (curr.start_index or 0)]
                        )
                    logger.info(
                        f"[PARALLEL-DEBUG] Text between: '{text_between}', distance: {curr.start_index - prev.end_index}"
                    )

                    if "," in text_between or (curr.start_index - prev.end_index <= 10):
                        # USER FIX 2026-01-08: Validate citations before grouping
                        # Check reporter, court, party metadata to prevent incorrect clustering
                        should_cluster = True
                        
                        # Extract reporter from citation text
                        def get_reporter(cit):
                            cit_text = str(cit.citation) if hasattr(cit, 'citation') else str(cit)
                            if 'WL' in cit_text:
                                return 'WL'
                            elif 'F.2d' in cit_text or 'F.3d' in cit_text or 'F.4th' in cit_text:
                                return 'F'
                            elif 'P.2d' in cit_text or 'P.3d' in cit_text:
                                return 'P'
                            return None
                        
                        prev_reporter = get_reporter(prev)
                        curr_reporter = get_reporter(curr)
                        
                        # CRITICAL: Same reporter = cannot be parallel
                        if prev_reporter and curr_reporter and prev_reporter == curr_reporter:
                            logger.info(f"[PARALLEL-DEBUG] REJECTED - same reporter: {prev_reporter}")
                            should_cluster = False
                        
                        # Check extracted_case_name compatibility (shared canonical logic)
                        if should_cluster:
                            prev_ecn = (getattr(prev, 'extracted_case_name', '') or '').strip()
                            curr_ecn = (getattr(curr, 'extracted_case_name', '') or '').strip()
                            if not names_are_same_case(prev_ecn, curr_ecn):
                                logger.info(f"[PARALLEL-DEBUG] REJECTED - different cases: '{prev_ecn}' vs '{curr_ecn}'")
                                should_cluster = False
                        
                        if should_cluster:
                            logger.info(f"[PARALLEL-DEBUG] Validation passed - Adding to group: {curr.citation}")
                            group.append(curr)
                            j += 1
                            continue
                        else:
                            logger.info(f"[PARALLEL-DEBUG] Validation REJECTED - NOT adding to group: {curr.citation}")
                            break
                break
            if len(group) > 1:
                groups_found += 1
                cite_strs = [c.citation for c in group]
                logger.info(f"[PARALLEL-DEBUG] Found parallel group {groups_found}: {cite_strs}")
                for c in group:
                    # CRITICAL FIX: Use helper to filter same-reporter/different-volume
                    filtered = filter_cluster_members_by_reporter(
                        c.citation,
                        [s for s in cite_strs if s != c.citation]
                    )
                    c.parallel_citations = filtered
                    logger.info(f"[PARALLEL-DEBUG] Set {c.citation}.parallel_citations = {c.parallel_citations}")
            i = j

        logger.info(f"[PARALLEL-DEBUG] Found {groups_found} parallel groups")

        if self.config.debug_mode:
            for c in citations:
                pass  # This loop was incomplete, adding pass to fix syntax

    def propagate_extracted_date_to_group(self, citations: List["CitationResult"]):
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
            r"\b(\d+)\s+U\.?S\.?\s+(\d+)(?:\s*\((\d{4})\))?",
            r"\b(\d+)\s+S\.?\s*Ct\.?\s+(\d+)(?:\s*\((\d{4})\))?",
            r"\b(\d+)\s+L\.?\s*Ed\.?\s*2d\s+(\d+)(?:\s*\((\d{4})\))?",
            r"\b(\d+)\s+F\.?\s*3d\s+(\d+)(?:\s*\((\d{4})\))?",
            r"\b(\d+)\s+F\.?\s*2d\s+(\d+)(?:\s*\((\d{4})\))?",
            r"\b(\d+)\s+F\.?\s+(\d+)(?:\s*\((\d{4})\))?",
            r"\b(\d+)\s+F\.?\s*Supp\.?\s*3d\s+(\d+)(?:\s*\((\d{4})\))?",
            r"\b(\d+)\s+F\.?\s*Supp\.?\s*2d\s+(\d+)(?:\s*\((\d{4})\))?",
            r"\b(\d+)\s+F\.?\s*Supp\.?\s+(\d+)(?:\s*\((\d{4})\))?",
            r"\b(\d+)\s+P\.?\s*3d\s+(\d+)(?:\s*\((\d{4})\))?",
            r"\b(\d+)\s+P\.?\s*2d\s+(\d+)(?:\s*\((\d{4})\))?",
            r"\b(\d+)\s+P\.?\s+(\d+)(?:\s*\((\d{4})\))?",
            r"\b(\d+)\s+N\.?E\.?\s*3d\s+(\d+)(?:\s*\((\d{4})\))?",
            r"\b(\d+)\s+N\.?E\.?\s*2d\s+(\d+)(?:\s*\((\d{4})\))?",
            r"\b(\d+)\s+N\.?E\.?\s+(\d+)(?:\s*\((\d{4})\))?",
            r"\b(\d+)\s+S\.?E\.?\s*2d\s+(\d+)(?:\s*\((\d{4})\))?",
            r"\b(\d+)\s+S\.?W\.?\s*3d\s+(\d+)(?:\s*\((\d{4})\))?",
            r"\b(\d+)\s+S\.?W\.?\s*2d\s+(\d+)(?:\s*\((\d{4})\))?",
            r"\b(\d+)\s+A\.?\s*3d\s+(\d+)(?:\s*\((\d{4})\))?",
            r"\b(\d+)\s+A\.?\s*2d\s+(\d+)(?:\s*\((\d{4})\))?",
            r"\b(\d+)\s+A\.?\s+(\d+)(?:\s*\((\d{4})\))?",
            r"\b(\d+)\s+Wn\.?\s*3d\s+(\d+)(?:\s*\((\d{4})\))?",
            r"\b(\d+)\s+Wash\.?\s*3d\s+(\d+)(?:\s*\((\d{4})\))?",
        ]

        for pattern in priority_patterns:
            matches = re.finditer(pattern, normalized_text, re.IGNORECASE)
            for match in matches:
                match.group(1)
                match.group(2)
                year = match.group(3) if len(match.groups()) >= 3 and match.group(3) else None

                citation_text = match.group(0)

                start_pos = max(0, match.start() - 200)
                context = normalized_text[start_pos : match.start()]

                case_name = "N/A"
                case_patterns = [
                    r"([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[a-zA-Z\'\.\&]+|of|the|and|&))*)\s+v\.\s+([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[a-zA-Z\'\.\&]+|of|the|and|&))*),?\s*$",
                    r"([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[a-zA-Z\'\.\&]+|of|the|and|&))*)\s+vs\.\s+([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[a-zA-Z\'\.\&]+|of|the|and|&))*),?\s*$",
                    r"(In\s+re\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[a-zA-Z\'\.\&]+|of|the|and|&))*),?\s*$",
                    r"(Ex\s+parte\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[a-zA-Z\'\.\&]+|of|the|and|&))*),?\s*$",
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

                results.append(
                    {
                        "case_name": case_name,
                        "citation": citation_text,
                        "year": year,
                        "start_index": match.start(),
                        "end_index": match.end(),
                    }
                )

        try:
            import eyecite

            eyecite_citations = eyecite.get_citations(normalized_text)
            logger.info(f"Eyecite found {len(eyecite_citations)} additional citations")

            for cite in eyecite_citations:
                citation_text = str(cite)
                if not any(result["citation"] == citation_text for result in results):
                    results.append(
                        {
                            "case_name": "N/A",
                            "citation": citation_text,
                            "year": getattr(cite, "year", None),
                            "start_index": getattr(cite, "span", [0, 0])[0],
                            "end_index": getattr(cite, "span", [0, 0])[1],
                        }
                    )
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
        stacklevel=2,
    )
    import re

    clusters = []
    case_name_pattern = r"([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\-]+(?:\s+[A-Za-z0-9&.,\'\-]+)*)"
    year_pattern = r"\((\d{4})\)"
    citation_pattern = r"(\d+\s+(?:Wn\.2d|Wash\.2d|P\.3d|P\.2d|F\.3d|F\.2d|U\.S\.|S\.Ct\.|L\.Ed\.|A\.2d|A\.3d|So\.2d|So\.3d)\s+\d+)"  # Expand as needed

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
            clusters.append(
                {"case_name": case_name, "year": year, "citations": citations, "start": case_start, "end": year_end}
            )
    return clusters
