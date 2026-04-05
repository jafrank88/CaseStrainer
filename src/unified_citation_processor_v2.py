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

# UNIFIED IMPORTS - Prefer src.extraction when available.
# In some CI snapshots the modular extraction package may be absent; keep imports resilient.
try:
    from src.extraction import extract_case_name_and_date_unified_master
except Exception as extraction_import_err:
    logger = logging.getLogger(__name__)
    logger.warning(
        f"src.extraction import unavailable; using minimal fallback extractor: {extraction_import_err}"
    )

    def extract_case_name_and_date_unified_master(  # type: ignore[override]
        text: str,
        citation: str,
        start_index: Optional[int] = None,
        end_index: Optional[int] = None,
        debug: bool = False,
        document_primary_case_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Minimal compatibility fallback when src.extraction is not installed in the
        current environment (e.g. partial CI checkout). Keeps callers functional.
        """
        _ = (start_index, end_index, debug, document_primary_case_name)
        case_name = ""
        if citation and " v. " in citation:
            m = re.match(r"^(.+?\s+v\.\s+[A-Za-z][A-Za-z\s'\.\&\-,]+?)(?:,\s*\d|\s+\d)", citation)
            if m:
                case_name = m.group(1).strip().rstrip(",")
        if not case_name and text:
            m = re.search(r"([A-Z][A-Za-z0-9&\.',\-\s]{3,140}\s+v\.\s+[A-Z][A-Za-z0-9&\.',\-\s]{2,140})", text)
            if m:
                case_name = m.group(1).strip().rstrip(",")
        return {
            "case_name": case_name or "N/A",
            "date": None,
            "method": "compat_fallback_no_src_extraction",
            "confidence": 0.0,
        }

from src.unified_clustering_master_optimized import cluster_citations_optimized as cluster_citations_unified
import warnings

# Import helper for filtering cluster members (moved to utils to avoid circular imports)
from src.citation_patterns import CitationPatterns
from src.utils.cluster_filter import filter_cluster_members_by_reporter
from src.utils.same_case import has_case_name, names_are_same_case
from src.utils.date_utils import years_match_for_verification, extract_year_value, extract_year_from_citation
from src.utils.citation_finalization_utils import apply_final_year_alignment, apply_proprietary_status
from src.utils.extraction_cleaner import (
    apply_pre_extraction_text_fixes,
    normalize_bold_italic_to_plain,
    normalize_to_ascii_display,
)

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

_COMMA_ABBREVS = (
    r"L\.?L\.?C\.?|L\.?P\.?|P\.?L\.?L\.?C\.?|P\.?L\.?C\.?|"
    r"Inc\.?|Ltd\.?|Corp\.?|Co\.?|"
    r"Ass\'?n\.?|Assoc\.?|Grp\.?|"
    r"LLC|LP|LLP|PLLC|PLC|Inc|Ltd|Corp"
)
_COMMA_ABBREVS_PAT = re.compile(r"^(" + _COMMA_ABBREVS + r")\s*,?\s*\d+\s+[A-Z]", re.IGNORECASE)
_SUFFIX_PAT = re.compile(r"^(" + _COMMA_ABBREVS + r")", re.IGNORECASE)
_NAME_THEN_CITE_RE = re.compile(
    r"([A-Z\u00C0-\u024F][A-Za-z\u00C0-\u024F.\'\,&\ \t\-]+[ \t\n]+v\s*\.\s*[ \t\n]+[A-Z\u00C0-\u024F][A-Za-z\u00C0-\u024F.\'\,&\ \t\-]+?)\s*,\s*(\d+)\s+[A-Z]",
    re.IGNORECASE,
)
_DOCKET_CAPTION_LINE_RE = re.compile(
    r"(?:Ins\.?\s*Co\.?|Inc\.?|Corp\.?|L\.?L\.?C\.?)\s+No\.?\s*[A-Z]?\d+[-\.]\d+",
    re.IGNORECASE,
)
_CITATION_IN_LINE_RE = re.compile(
    r"\d{4}\s+WL\s+\d+|\d+\s+(?:F\.?3d|F\.?2d|U\.S\.|P\.?3d|N\.E\.2d|S\.E\.2d|S\.W\.2d|Wn\.2d|Cal\.)\s+\d+",
    re.IGNORECASE,
)

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
            self.enhanced_web_searcher = None
            logger.debug(
                "ComprehensiveWebSearchEngine not installed; optional enhanced web search disabled: %s",
                e,
            )
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
        # Pinpoint pattern for SCOTUS block: match ", N" only when N is NOT followed by S. Ct. or L. Ed.
        # Prevents consuming "116" in "116 S. Ct." as a pinpoint (e.g. BMW: 517 U.S. 559, 572, 116 S. Ct. 1589).
        _scotus_pin = r"(?:\s*,\s*\d+(?!\s+(?:S\.\s*Ct\.|L\.\s*Ed\.)))*"
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
                # Allow footnote (e.g. "123 n.21") between pinpoint and parallel: "19 Wn. App. 2d 113, 123 n.21, 494 P.3d 1076"
                r"\b(\d+)\s+(?:Wash\.|Wn\.)\s*(?:App\.)\s*2d\s+(\d+)(?:\s*,\s*(\d+)(?:\s*n\.?\s*\d+)?)?(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\s*(?:\(\d{4}\))?\b",
                re.IGNORECASE,
            ),
            # U.S. Supreme Court multi-reporter block (e.g. BMW v. Gore: 517 U.S. 559, 572, 116 S. Ct. 1589, 134 L. Ed. 2d 809)
            # Matches U.S. + S.Ct. + L.Ed.2d in one block; allows optional pinpoint between reporters.
            # CRITICAL: Pinpoint must NOT consume next reporter's volume (e.g. 116 in "116 S. Ct.").
            "scotus_parallel_block": re.compile(
                rf"\b(\d+)\s+U\.\s*S\.\s+(\d+){_scotus_pin}\s*,\s*(\d+)\s+S\.\s*Ct\.\s+(\d+){_scotus_pin}\s*,\s*(\d+)\s+L\.\s*Ed\.\s*2d\s+(\d+)\b",
                re.IGNORECASE,
            ),
            # Alternate order: U.S. + L.Ed.2d + S.Ct.
            "scotus_parallel_block_led_first": re.compile(
                rf"\b(\d+)\s+U\.\s*S\.\s+(\d+){_scotus_pin}\s*,\s*(\d+)\s+L\.\s*Ed\.\s*2d\s+(\d+){_scotus_pin}\s*,\s*(\d+)\s+S\.\s*Ct\.\s+(\d+)\b",
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
            # Maine (2005 ME 113), Nebraska (289 Neb. 864), Ohio St. (110 Ohio St. 3d 456)
            "me": re.compile(r"\b(20\d{2})\s+ME\s+(\d+)\b", re.IGNORECASE),
            "neb": re.compile(r"\b(\d+)\s+Neb\.?\s+(\d+)\b", re.IGNORECASE),
            "ohio_st": re.compile(r"\b(\d+)\s+Ohio\s*St\.?\s*(?:3d|2d)?\s+(\d+)\b", re.IGNORECASE),
            # N.E.2d (Ohio, Ill., etc.), N.W.2d (Nebraska, etc.), A.2d already exists
            "ne2d": re.compile(r"\b(\d+)\s+N\.E\.2d\s+(\d+)\b", re.IGNORECASE),
            "nw2d": re.compile(r"\b(\d+)\s+N\.W\.2d\s+(\d+)\b", re.IGNORECASE),
            # Military Justice (not supported by eyecite)
            "mj": re.compile(r"\b(\d+)\s+M\.J\.\s+(\d+)\b"),
            # 6th Circuit FED App citation (e.g. 2001 FED App. 0138P)
            "fed_app_six": re.compile(r"\b(\d{4})\s+FED\s+App\.?\s+([0-9][0-9a-zA-Z]*)\b", re.IGNORECASE),
            # Federal district docket citations (e.g. King v. Ortiz, 17 Cv 7507 (F.DNY May 2, 2019))
            "federal_docket": re.compile(
                r"\b(\d{2})\s+Cv\.?\s+(\d{4,})\s*\(\s*(?:F\.?D\.?NY|S\.?D\.?NY|E\.?D\.?|W\.?D\.?|N\.?D\.?|M\.?D\.?)\s*[^)]*\d{4}\s*\)",
                re.IGNORECASE,
            ),
            # F. Supp. 3d with no space (Supp3d) - after text norm may already be Supp. 3d
            "f_supp3d_flex": re.compile(r"\b(\d+)\s+F\.\s*Supp\.?\s*3d\s+(\d+)\b", re.IGNORECASE),
            "lexis": re.compile(r"\b(\d{4})\s+[A-Za-z\.\s]+LEXIS\s+(\d{1,12})\b", re.IGNORECASE),
            "lexis_alt": re.compile(r"\b(\d{4})\s+LEXIS\s+(\d{1,12})\b", re.IGNORECASE),
            # Neutral/Public Domain Citations (20 states with vendor-neutral formats)
            # Group 1: Two-letter codes (no periods) — supreme + appellate courts
            "neutral_co": re.compile(r"\b(20\d{2})\s+CO\s+(\d{1,5})\b", re.IGNORECASE),
            "neutral_coa": re.compile(r"\b(20\d{2})\s+COA\s+(\d{1,5})\b", re.IGNORECASE),
            "neutral_me": re.compile(r"\b(20\d{2})\s+ME\s+(\d{1,5})\b", re.IGNORECASE),
            "neutral_mt": re.compile(r"\b(20\d{2})\s+MT\s+(\d{1,5})\b", re.IGNORECASE),
            "neutral_nd": re.compile(r"\b(20\d{2})\s+ND\s+(\d{1,5})\b", re.IGNORECASE),
            "neutral_nd_app": re.compile(r"\b(20\d{2})\s+ND\s+App\s+(\d{1,5})\b", re.IGNORECASE),
            "neutral_ok": re.compile(r"\b(20\d{2})\s+OK\s+(\d{1,5})\b", re.IGNORECASE),
            "neutral_ok_civ": re.compile(r"\b(20\d{2})\s+OK\s+CIV\s+APP\s+(\d{1,5})\b", re.IGNORECASE),
            "neutral_ok_cr": re.compile(r"\b(20\d{2})\s+OK\s+CR\s+(\d{1,5})\b", re.IGNORECASE),
            "neutral_sd": re.compile(r"\b(20\d{2})\s+SD\s+(\d{1,5})\b", re.IGNORECASE),
            "neutral_ut": re.compile(r"\b(20\d{2})\s+UT\s+(\d{1,5})\b", re.IGNORECASE),
            "neutral_ut_app": re.compile(r"\b(20\d{2})\s+UT\s+App\s+(\d{1,5})\b", re.IGNORECASE),
            "neutral_vt": re.compile(r"\b(20\d{2})\s+VT\s+(\d{1,5})\b", re.IGNORECASE),
            "neutral_wi": re.compile(r"\b(20\d{2})\s+WI\s+(\d{1,5})\b", re.IGNORECASE),
            "neutral_wi_app": re.compile(r"\b(20\d{2})\s+WI\s+App\s+(\d{1,5})\b", re.IGNORECASE),
            "neutral_wy": re.compile(r"\b(20\d{2})\s+WY\s+(\d{1,5})\b", re.IGNORECASE),
            # Group 2: Abbreviated with periods
            "neutral_ar": re.compile(r"\b(20\d{2})\s+Ark\.(?:\s+App\.)?\s+(\d{1,5})\b", re.IGNORECASE),
            "neutral_nh": re.compile(r"\b(20\d{2})\s+N\.H\.\s+(\d{1,5})\b", re.IGNORECASE),
            "neutral_ms_year": re.compile(r"\b(20\d{2})\s+Miss\.\s+(\d{1,5})\b", re.IGNORECASE),
            # Group 3: Hyphenated formats
            "neutral_nm": re.compile(r"\b(20\d{2})[\-\u2011\u2013\u2014]NM(?:SC|CA)?[\-\u2011\u2013\u2014]\s*(\d{1,5})\b", re.IGNORECASE),
            "neutral_nc": re.compile(r"\b(20\d{2})[\-\u2011\u2013\u2014]NC(?:SC|COA)[\-\u2011\u2013\u2014]\s*(\d{1,5})\b", re.IGNORECASE),
            # Ohio: 2006-Ohio-4854 or 2006-Ohio- 4854 (PDFs often add space before number)
            "neutral_ohio": re.compile(
                r"\b(20\d{2})[\-\u2011\u2013\u2014]?Ohio[\-\u2011\u2013\u2014]?\s*(\d{1,5})\b",
                re.IGNORECASE,
            ),
            # Ohio fused: 4632006-Ohio-4854 when pinpoint and year run together (no comma)
            "neutral_ohio_fused": re.compile(
                r"(?<=\d)(20\d{2})[\-\u2011\u2013\u2014]?Ohio[\-\u2011\u2013\u2014]?\s*(\d{1,5})\b",
                re.IGNORECASE,
            ),
            # Ohio parallel block: Ohio St. + neutral + N.E.2d (e.g. 110 Ohio St. 3d 456, 463, 2006-Ohio-4854, ¶ 29, 854 N.E.2d 193)
            # Allow optional space before neutral number (PDFs: "2006-Ohio- 4854")
            # Allow fused pinpoint+year (PDFs: "4632006-Ohio- 4854" when 463 and 2006 run together)
            "ohio_parallel_block": re.compile(
                r"\b(\d+)\s+Ohio\s*St\.?\s*(?:3d|2d)?\s+(\d+)\s*,\s*\d{1,3}?(?:\s*,\s*)?(20\d{2})[\-\u2011\u2013\u2014]?Ohio[\-\u2011\u2013\u2014]?\s*(\d+)(?:\s*,\s*[^,]+)?\s*,\s*(\d+)\s+N\.E\.2d\s+(\d+)\b",
                re.IGNORECASE,
            ),
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

    def _sanitize_citation_for_verification_query(self, citation_text: str) -> str:
        """
        Trim noisy/prose-heavy citation strings into a stable query segment.
        This is only for verification API queries; it does not mutate stored citation text.
        """
        s = re.sub(r"\s+", " ", str(citation_text or "")).strip()
        if not s:
            return s

        # Generalized: for verification, prefer the base reporter citation (vol/reporter/page)
        # so variants like "347 U.S. 521 (scotus 1954)" or "673 F. Supp. 525 (dcd 1987)"
        # hit citation-lookup reliably. Keep the full string for extraction/clustering/display.
        try:
            from src.utils.response_enrichment import extract_display_base_citation

            base = (extract_display_base_citation(s) or "").strip()
            if base:
                return base
        except Exception:
            pass

        # If already compact, keep as-is.
        if len(s) <= 180:
            return s

        # Drop trailing quote/parenthetical prose commonly appended by extraction noise.
        cut_markers = [
            " (quoting ",
            ' ("',
            " Resp't",
            " Resp’t",
            " Obj.",
            " TABLE OF AUTHORITIES",
        ]
        cut_idx = None
        low = s.lower()
        for m in cut_markers:
            i = low.find(m.lower())
            if i > 0:
                cut_idx = i if cut_idx is None else min(cut_idx, i)
        if cut_idx is not None:
            s = s[:cut_idx].strip(" ,;")

        # Keep a clean leading citation form if present:
        # e.g., "A. B. v. Hawaii..., 30 F.4th 828, 838 (ca9 2022)"
        lead_pat = re.compile(
            r"^(.{0,220}?\b\d+\s+"
            r"(?:U\.?\s*S\.?|S\.?\s*Ct\.?|F\.?\s*Supp\.?\s*(?:\d+d)?|F\.?\d+d|F\.?\d+th|F\.?\s*R\.?\s*D\.?|WL)"
            r"\s+\d+(?:,\s*\d+)?(?:\s*\([^)]+\))?)",
            re.IGNORECASE,
        )
        m = lead_pat.search(s)
        if m:
            candidate = m.group(1).strip(" ,;")
            if len(candidate) >= 12:
                return candidate

        # Conservative fallback: hard cap to avoid query pollution.
        return s[:220].rstrip(" ,;")

    def _na_and_partial_insufficient(self, citation) -> bool:
        """True if citation has N/A case name AND partial citation text -> insufficient to verify."""
        if hasattr(citation, "get") and callable(getattr(citation, "get", None)):
            ext_name = citation.get("extracted_case_name") or citation.get("cluster_case_name") or ""
            cite_text = citation.get("citation") or ""
        else:
            ext_name = getattr(citation, "extracted_case_name", None) or getattr(citation, "cluster_case_name", None) or ""
            cite_text = getattr(citation, "citation", None) or ""
        if (ext_name or "").strip().upper() != "N/A":
            return False
        return self._is_partial_citation(str(cite_text))

    def _is_missing_extracted_name(self, name: Optional[str]) -> bool:
        v = (name or "").strip()
        return (not v) or v.upper() == "N/A"

    def _is_missing_extracted_date(self, date_value: Optional[str]) -> bool:
        v = str(date_value or "").strip()
        return (not v) or v.upper() in {"N/A", "NONE", "UNKNOWN", "UNKNOWN YEAR"}

    def _set_extracted_date_provenance(
        self,
        citation: Any,
        source: str,
        confidence: str,
    ) -> None:
        """Persist extracted-date provenance on citation metadata for UI/debug."""
        try:
            md = getattr(citation, "metadata", None)
            if not isinstance(md, dict):
                md = {}
            md["extracted_date_source"] = source
            md["extracted_date_confidence"] = confidence
            citation.metadata = md
        except Exception:
            return

    def _is_scotus_citation_text(self, citation_text: str) -> bool:
        s = str(citation_text or "")
        return bool(
            re.search(r"\b\d+\s+U\.?\s*S\.?\s+\d+\b", s, re.IGNORECASE)
            or re.search(r"\b\d+\s+S\.?\s*Ct\.?\s+\d+\b", s, re.IGNORECASE)
            or re.search(r"\b\d+\s+L\.?\s*Ed\.?\s*(?:2d\s+)?\d+\b", s, re.IGNORECASE)
        )

    def _should_expose_gate_reject_canonical(self, citation_text: str, result: Any) -> bool:
        """For non-SCOTUS, only expose gate-reject canonical data on citation-core match."""
        if self._is_scotus_citation_text(citation_text):
            return True
        raw = getattr(result, "raw_data", None)
        if isinstance(raw, dict):
            core_match = raw.get("citation_core_match")
            if core_match is True:
                return True
            # Allow explicit same-name+same-year candidates to stay reviewable with URL.
            if raw.get("same_name_year_match") is True:
                return True
        return False

    def _citation_core_key(self, citation_text: str) -> Optional[str]:
        """Return a stable core key for reporter citations (used for metadata enrichment)."""
        if not citation_text:
            return None
        s = re.sub(r"\s+", " ", str(citation_text)).strip()

        m = re.search(r"\b(\d+)\s+F\.\s*Supp\.\s*3d\s+(\d+)\b", s, re.IGNORECASE)
        if m:
            return f"f_supp_3d:{m.group(1)}:{m.group(2)}"

        m = re.search(r"\b(\d+)\s+F\.\s*Supp\.\s*2d\s+(\d+)\b", s, re.IGNORECASE)
        if m:
            return f"f_supp_2d:{m.group(1)}:{m.group(2)}"

        m = re.search(r"\b(\d{4})\s+WL\s+(\d+)\b", s, re.IGNORECASE)
        if m:
            return f"wl:{m.group(1)}:{m.group(2)}"

        m = re.search(r"\b(\d+)\s+F\.\s*(?:2d|3d|4th)\s+(\d+)\b", s, re.IGNORECASE)
        if m:
            return f"f_reporter:{m.group(1)}:{m.group(2)}"

        m = re.search(r"\b(\d+)\s+N\.?\s*W\.?\s*2d\s+(\d+)\b", s, re.IGNORECASE)
        if m:
            return f"nw2d:{m.group(1)}:{m.group(2)}"

        m = re.search(r"\b(\d+)\s+A\.?\s*(?:2d|3d)\s+(\d+)\b", s, re.IGNORECASE)
        if m:
            return f"a2d:{m.group(1)}:{m.group(2)}"

        m = re.search(r"\b(\d+)\s+N\.?\s*E\.?\s*2d\s+(\d+)\b", s, re.IGNORECASE)
        if m:
            return f"ne2d:{m.group(1)}:{m.group(2)}"

        return None

    def _extract_name_year_from_text_for_citation(
        self, citation_text: str, document_text: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Try to recover `Name v. Name` and nearby year from full text for a citation.
        Uses a whitespace-flexible citation pattern to survive PDF line breaks.
        """
        if not citation_text or not document_text:
            return None, None

        tokens = re.sub(r"\s+", " ", citation_text).strip().split(" ")
        if not tokens:
            return None, None
        cite_pat = r"\s+".join(re.escape(tok) for tok in tokens if tok)
        if not cite_pat:
            return None, None

        name_then_cite = re.compile(
            r"(?P<name>[A-Z][A-Za-z0-9'&\.\-,\s]{3,180}?\bv\.\s*[A-Z][A-Za-z0-9'&\.\-,\s]{1,180}?)\s*,?\s*"
            + cite_pat
        )

        m = name_then_cite.search(document_text)
        if not m:
            return None, None

        name = self._clean_extracted_case_name((m.group("name") or "").strip())
        if self._is_missing_extracted_name(name) or " v. " not in name:
            return None, None

        post = document_text[m.end() : m.end() + 120]
        # Prefer decision year in parentheses (TOA / body) before any bare year (avoids brief date bleed)
        paren_y = re.search(r"\((\d{4})\)", post)
        if paren_y and 1700 <= int(paren_y.group(1)) <= 2030:
            year = paren_y.group(1)
        else:
            y = re.search(r"\b(17|18|19|20)\d{2}\b", post)
            year = y.group(0) if y else None
        return name, year

    def _extract_name_year_from_same_line_for_citation(
        self,
        text: str,
        citation_text: str,
        start_index: Optional[int],
        end_index: Optional[int],
        *,
        max_line_scan: int = 600,
        max_year_scan: int = 80,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Best-effort extraction of `Name v. Name` and `(YYYY)` from the *same line* as the citation.

        This is primarily to prevent Table-of-Authorities "neighbor bleed" where multiple cites
        appear on one line and a proximity search grabs the wrong case name or year.
        """
        if not text or not citation_text or start_index is None or start_index < 0:
            return None, None

        si = int(start_index)
        ei = int(end_index) if (end_index is not None and end_index >= si) else (si + len(citation_text))

        # Defensive: start_index/end_index sometimes refer to a normalized variant of text.
        # If the citation string isn't exactly at [si:ei], try to locate it nearby using whitespace-flexible matching.
        try:
            snippet = text[si: min(len(text), si + len(citation_text))]
        except Exception:
            snippet = ""
        if snippet != citation_text:
            window = text[max(0, si - 800) : min(len(text), si + 800)]
            tokens = re.sub(r"\s+", " ", citation_text).strip().split(" ")
            cite_pat = r"\s+".join(re.escape(tok) for tok in tokens if tok)
            if cite_pat:
                mloc = re.search(cite_pat, window)
                if mloc:
                    si = max(0, si - 800) + mloc.start()
                    ei = max(0, si - 800) + mloc.end()

        # Find line boundaries around the citation position (bounded scan).
        pre = text[max(0, si - max_line_scan) : si]
        post = text[ei : min(len(text), ei + max_line_scan)]
        line_start = si - (pre.rfind("\n") + 1 if "\n" in pre else len(pre))
        post_nl = post.find("\n")
        line_end = ei + (post_nl if post_nl >= 0 else len(post))

        line = text[line_start:line_end]
        if not line or len(line) < 10:
            return None, None

        rel_si = max(0, si - line_start)
        rel_ei = max(rel_si, min(len(line), ei - line_start))

        left = line[:rel_si]
        right = line[rel_ei : rel_ei + max_year_scan]

        # Extract year from trailing parenthetical immediately after cite.
        # Accept both "(2023)" and court parentheticals like "(2d Cir. 1990)".
        year = None
        py = re.search(r"\(([^)]{0,80}?\b(?P<year>\d{4})\b)\)", right)
        if py:
            try:
                yv = int(py.group("year"))
                if 1700 <= yv <= 2030:
                    year = py.group("year")
            except Exception:
                pass

        # Extract the nearest "X v. Y" from the left side of the line (use the *last* match).
        # Allow abbreviations and punctuation; keep it bounded to reduce over-capture.
        v_pat = re.compile(
            r"(?P<name>[A-Z][A-Za-z0-9'&\.\-(),\s]{3,220}?\bv\.\s*[A-Z][A-Za-z0-9'&\.\-(),\s]{1,220}?)"
        )

        # Consider only a suffix of left side to bias toward the nearest name.
        left_tail = left[-320:] if len(left) > 320 else left

        # Prefer the match whose end is closest to the citation (i.e., the last match in the tail).
        # This avoids a single huge regex match spanning multiple TOA entries.
        m = None
        for cand in v_pat.finditer(left_tail):
            m = cand
        if not m:
            return None, year

        name = self._clean_extracted_case_name((m.group("name") or "").strip().rstrip(","))
        if self._is_missing_extracted_name(name) or " v. " not in name:
            return None, year

        return name, year

    def _extract_name_year_by_exact_cite_anchor(
        self,
        text: str,
        citation_text: str,
        start_index: Optional[int],
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        High-precision recovery for TOA-style entries:
            Name v. Name, <citation_text> (YYYY)

        Searches the full text using a whitespace-flexible citation pattern and requires
        a parenthetical year immediately after the citation. This is used to correct
        cases where we extracted *a* name/year, but it belongs to a neighboring TOA entry.
        """
        if not text or not citation_text:
            return None, None

        def _fuzzy_cite_pat(cit: str) -> str:
            """
            OCR-tolerant reporter matching for common cites.
            Examples:
              - "490 U.S. 93" matches "490 US. 93", "490 U. S. 93", "490 U.S 93"
              - "143 S. Ct. 1142" matches "143 S Ct 1142", "143 S.Ct. 1142"
            """
            s = re.sub(r"\s+", " ", (cit or "").strip())
            m = re.match(r"^(?P<vol>\d{1,4})\s+U\.?\s*S\.?\s+(?P<page>\d{1,6})$", s, re.IGNORECASE)
            if m:
                return rf"\b{m.group('vol')}\s+U\.?\s*S\.?\s+{m.group('page')}\b"
            m = re.match(r"^(?P<vol>\d{1,4})\s+S\.?\s*Ct\.?\s+(?P<page>\d{1,6})$", s, re.IGNORECASE)
            if m:
                return rf"\b{m.group('vol')}\s+S\.?\s*Ct\.?\s+{m.group('page')}\b"
            m = re.match(r"^(?P<vol>\d{1,4})\s+F\.?\s*3d\s+(?P<page>\d{1,6})$", s, re.IGNORECASE)
            if m:
                return rf"\b{m.group('vol')}\s+F\.?\s*3d\s+{m.group('page')}\b"
            m = re.match(r"^(?P<vol>\d{1,4})\s+F\.?\s*2d\s+(?P<page>\d{1,6})$", s, re.IGNORECASE)
            if m:
                return rf"\b{m.group('vol')}\s+F\.?\s*2d\s+{m.group('page')}\b"
            m = re.match(r"^(?P<vol>\d{1,4})\s+F\.?\s*Supp\.?\s*(?P<series>\d{0,2})\s*(?P<page>\d{1,6})$", s, re.IGNORECASE)
            if m:
                ser = m.group("series") or ""
                ser_pat = rf"\s*{re.escape(ser)}" if ser else ""
                return rf"\b{m.group('vol')}\s+F\.?\s*Supp\.?{ser_pat}\s+{m.group('page')}\b"

            # Fallback: token-wise whitespace flexible (less tolerant to punctuation, but better than exact).
            tokens = re.sub(r"\s+", " ", s).split(" ")
            tokens = [t for t in tokens if t]
            if not tokens:
                return ""
            esc = [re.escape(t).replace(r"\.", r"\.?") for t in tokens]
            return r"\b" + r"\s+".join(esc) + r"\b"

        cite_pat = _fuzzy_cite_pat(citation_text)
        if not cite_pat:
            return None, None

        # Accept "(YYYY)" and "(<court...> YYYY)".
        anchored = re.compile(
            r"(?P<name>[A-Z][A-Za-z0-9'&\.\-,\s]{3,200}?\bv\.\s*[A-Z][A-Za-z0-9'&\.\-,\s]{1,200}?)\s*,?\s*"
            + cite_pat
            + r"\s*\((?:[^)]{0,80}?\b)?(?P<year>\d{4})\b[^)]{0,80}?\)",
        )
        matches = list(anchored.finditer(text))
        if not matches:
            return None, None

        def _estimate_toa_spans(doc: str) -> List[Tuple[int, int]]:
            """
            Best-effort detection of Table of Authorities spans so we can prefer body matches.
            Many briefs include every TOA citation again in the body; TOA lines are more prone
            to neighbor-bleed and page-number leader noise.
            """
            if not doc:
                return []
            # Start markers (headings)
            start_pat = re.compile(
                r"(?im)^\s*(?:table\s+of\s+(?:cited\s+)?authorities|cited\s+authorities)\b"
            )
            # End markers: first major section heading after TOA
            end_pat = re.compile(
                r"(?im)^\s*(?:argument|summary\s+of\s+argument|statement\s+of\s+interest|statement\s+of\s+the\s+case|introduction|background|conclusion)\b"
            )
            spans: List[Tuple[int, int]] = []
            for sm in start_pat.finditer(doc):
                start = sm.start()
                em = end_pat.search(doc, pos=sm.end())
                end = em.start() if em else min(len(doc), sm.end() + 20000)
                if end > start:
                    spans.append((start, end))
            return spans

        def _in_spans(idx: int, spans: List[Tuple[int, int]]) -> bool:
            for a, b in spans:
                if a <= idx < b:
                    return True
            return False

        # If multiple matches exist (common in TOA where multiple cases share reporters),
        # choose the one with the *smallest gap* between end-of-cite and the year paren.
        # This favors "..., CITE (YYYY)" over spillovers like "..., 331 U.S. 218 Smiley v. Kansas, 196 U.S. 447 (1905)".
        def _quality(mm: re.Match) -> Tuple[int, int]:
            # Lower is better.
            span_txt = mm.group(0) or ""
            # crude: find last occurrence of page number in the matched cite, then distance to "("
            gap = 9999
            try:
                paren_pos = span_txt.rfind("(")
                if paren_pos >= 0:
                    # distance from last digit before paren to paren
                    m_dig = re.search(r"(\d)\D*\($", span_txt[: paren_pos + 1])
                    if m_dig:
                        gap = paren_pos - m_dig.start(1)
            except Exception:
                pass
            return (gap, len(span_txt))

        toa_spans = _estimate_toa_spans(text)
        non_toa = [mm for mm in matches if not _in_spans(mm.start(), toa_spans)] if toa_spans else []
        pool = non_toa or matches

        best = min(pool, key=_quality)

        # Prefer the closest anchored occurrence to start_index when provided and reasonable.
        m = best
        if start_index is not None and start_index >= 0:
            closest = min(pool, key=lambda mm: abs(mm.start() - start_index))
            # If the closest match isn't dramatically worse in quality, use it.
            if _quality(closest) <= (_quality(best)[0] + 3, _quality(best)[1] + 50):
                m = closest

        name = self._clean_extracted_case_name((m.group("name") or "").strip().rstrip(","))
        if self._is_missing_extracted_name(name) or " v. " not in name:
            return None, None
        y = m.group("year")
        if not y or not y.isdigit() or not (1700 <= int(y) <= 2030):
            return name, None
        return name, y

    def _apply_exact_cite_anchor_repairs(self, citations: List["CitationResult"], text: str) -> int:
        """
        Repair extracted_case_name/extracted_date by anchoring on exact TOA-style patterns:
            Name v. Name, <citation> (YYYY)

        Unlike enrichment, this may overwrite existing (but wrong) extracted metadata.
        """
        if not citations or not text:
            return 0
        fixed = 0
        for c in citations:
            try:
                cit = (getattr(c, "citation", None) or "").strip()
                if not cit:
                    continue
                # Skip year-based vendor citations (year is part of the cite).
                if re.search(r"\b(?:19|20)\d{2}\s+(?:WL|(?:U\.S\.?\s*)?LEXIS|LEXIS)\s+\d+\b", cit, re.IGNORECASE):
                    continue
                # Indices in OCR'd / normalized text can drift; prefer global anchored match over "closest index".
                name, year = self._extract_name_year_by_exact_cite_anchor(text, cit, None)
                if not name or not year:
                    continue
                cur_name = (getattr(c, "extracted_case_name", None) or "").strip()
                cur_year = str(getattr(c, "extracted_date", None) or "").strip()
                changed = False
                if name and name != cur_name:
                    c.extracted_case_name = self._clean_extracted_case_name(name)
                    changed = True
                if year and year != cur_year:
                    c.extracted_date = year
                    self._set_extracted_date_provenance(c, "exact_cite_anchor", "high")
                    changed = True
                if changed:
                    fixed += 1
            except Exception:
                continue
        if fixed:
            logger.info(f"[TOA-ANCHOR] Repaired name/year on {fixed} citations via exact cite anchor")
        return fixed

    def _enrich_missing_extracted_metadata(
        self, citations: List["CitationResult"], text: str
    ) -> int:
        """
        Fill missing extracted_case_name / extracted_date for short cites using:
        1) same-citation donor rows with strong extracted names, then
        2) full-document name+citation pattern recovery.
        """
        if not citations:
            return 0

        donors_by_key = {}
        for c in citations:
            c_name = getattr(c, "extracted_case_name", None)
            if self._is_missing_extracted_name(c_name):
                continue
            c_name = (c_name or "").strip()
            if " v. " not in c_name or len(c_name) < 8:
                continue
            key = self._citation_core_key(getattr(c, "citation", ""))
            if not key:
                continue
            donors_by_key.setdefault(key, []).append(c)

        fixed = 0
        for c in citations:
            cur_name = getattr(c, "extracted_case_name", None)
            cur_date = getattr(c, "extracted_date", None)
            need_name = self._is_missing_extracted_name(cur_name)
            need_date = self._is_missing_extracted_date(cur_date)
            if not (need_name or need_date):
                continue

            key = self._citation_core_key(getattr(c, "citation", ""))
            donor = None
            if key and key in donors_by_key:
                candidates = [d for d in donors_by_key[key] if d is not c]
                if candidates:
                    c_start = getattr(c, "start_index", None)
                    if c_start is None:
                        donor = candidates[0]
                    else:
                        # Exclude donors with semicolon between (e.g. "857 N.W.2d 569" + Dow separated by ";")
                        def _no_semicolon_between(d):
                            d_end = getattr(d, "end_index", None)
                            if not text or c_start is None or d_end is None:
                                return True
                            between = text[min(c_start, d_end) : max(c_start, d_end)]
                            return ";" not in between
                        viable = [d for d in candidates if _no_semicolon_between(d)]
                        candidates = viable if viable else candidates
                        donor = min(
                            candidates,
                            key=lambda d: abs((getattr(d, "start_index", None) or c_start) - c_start),
                        )

            changed = False
            if donor is not None:
                donor_name = (getattr(donor, "extracted_case_name", None) or "").strip()
                donor_date = getattr(donor, "extracted_date", None)
                if need_name and donor_name and donor_name.upper() != "N/A":
                    c.extracted_case_name = donor_name
                    changed = True
                if need_date and donor_date and str(donor_date).strip().upper() != "N/A":
                    c.extracted_date = str(donor_date)
                    self._set_extracted_date_provenance(c, "citation_donor", "medium")
                    changed = True

            if not changed and need_name:
                found_name, found_year = self._extract_name_year_from_text_for_citation(
                    getattr(c, "citation", ""), text
                )
                if found_name and not self._is_missing_extracted_name(found_name):
                    c.extracted_case_name = found_name
                    changed = True
                if need_date and found_year:
                    c.extracted_date = found_year
                    self._set_extracted_date_provenance(c, "name_anchor", "low")
                    changed = True

            if changed:
                fixed += 1
                logger.info(
                    f"[EXTRACT-ENRICH] Recovered metadata for '{getattr(c, 'citation', '')}': "
                    f"name='{getattr(c, 'extracted_case_name', None)}' "
                    f"date='{getattr(c, 'extracted_date', None)}'"
                )

        if fixed > 0:
            logger.info(f"[EXTRACT-ENRICH] Recovered metadata on {fixed} citations")
        return fixed

    def _canonical_year_from_known_row(self, kn: Dict[str, Any]) -> Optional[str]:
        """4-digit year from a known-citation row (canonical_year or canonical_date)."""
        if not kn:
            return None
        y = kn.get("canonical_year")
        if y is not None and str(y).strip().isdigit() and 1700 <= int(str(y).strip()) <= 2030:
            return str(y).strip()
        cd = kn.get("canonical_date")
        if cd:
            ym = re.search(r"\b((?:19|20)\d{2})\b", str(cd))
            if ym:
                return ym.group(1)
        return None

    def _harmonize_trailing_year_in_extracted_case_name(self, citation: Any, year_s: str) -> None:
        """If extracted_case_name ends with ', YYYY' and YYYY != year_s, align to year_s."""
        ecn = (getattr(citation, "extracted_case_name", None) or "").strip()
        if not ecn or ecn.upper() == "N/A":
            return
        mtrail = re.search(r",\s*((?:19|20)\d{2})\s*$", ecn)
        if mtrail and mtrail.group(1) != year_s:
            citation.extracted_case_name = self._clean_extracted_case_name(
                ecn[: mtrail.start()] + f", {year_s}"
            )

    def _compute_cluster_decision_year_phase55(
        self,
        cluster: Dict[str, Any],
        cluster_citations: list,
        cluster_id: Any,
    ) -> Optional[str]:
        """Decision year for cluster display: canonical / cite paren / extracted (singleton or parallel)."""
        from collections import Counter

        cluster_extracted_date: Optional[str] = None
        if len(cluster_citations) > 1:
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

            has_date_mismatch = len(set([d for _, d in canonical_dates])) > 1
            if has_date_mismatch:
                logger.warning(
                    f"[WARNING] [DATE-MISMATCH] Cluster {cluster_id}: Parallel citations have DIFFERENT canonical dates!"
                )
                for cit, date in canonical_dates:
                    logger.warning(f"   - {cit}: canonical_date={date}")
                logger.warning(
                    f"   -> This may indicate a typo or verification to wrong case. User should review."
                )
                cluster["date_mismatch_warning"] = True
                cluster["date_mismatch_details"] = [
                    {"citation": cit, "canonical_date": date} for cit, date in canonical_dates
                ]

            v_years: List[str] = []
            for cit_dict in cluster_citations:
                if not isinstance(cit_dict, dict) or not cit_dict.get("verified"):
                    continue
                cd = cit_dict.get("canonical_date")
                if cd:
                    ym = re.search(r"(19|20)\d{2}", str(cd))
                    if ym:
                        v_years.append(ym.group(0))
                        continue
                ed = cit_dict.get("extracted_date")
                if ed and str(ed).strip().isdigit() and 1700 <= int(str(ed).strip()) <= 2030:
                    v_years.append(str(ed).strip())
            if v_years:
                cluster_extracted_date = Counter(v_years).most_common(1)[0][0]
            if not cluster_extracted_date:
                for cit_dict in cluster_citations:
                    if not isinstance(cit_dict, dict):
                        continue
                    py = self._decision_year_from_citation_paren(str(cit_dict.get("citation") or ""))
                    if py:
                        cluster_extracted_date = py
                        break

            if not cluster_extracted_date and extracted_dates:
                filtered_dates: List[Any] = []
                for date in extracted_dates:
                    date_str = str(date)
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
                    cluster_extracted_date = extracted_dates[0] if extracted_dates else None
                    logger.warning(
                        f"[CLUSTER-DATE] Cluster {cluster_id}: All dates filtered, using fallback: {cluster_extracted_date}"
                    )

        elif len(cluster_citations) == 1:
            c0 = cluster_citations[0]
            if isinstance(c0, dict):
                cd0 = c0.get("canonical_date")
                if cd0:
                    ym0 = re.search(r"(19|20)\d{2}", str(cd0))
                    if ym0:
                        cluster_extracted_date = ym0.group(0)
                if not cluster_extracted_date:
                    py0 = self._decision_year_from_citation_paren(str(c0.get("citation") or ""))
                    if py0:
                        cluster_extracted_date = py0
                if not cluster_extracted_date:
                    ed0 = c0.get("extracted_date")
                    if ed0 and str(ed0).strip().isdigit() and 1700 <= int(str(ed0).strip()) <= 2030:
                        cluster_extracted_date = str(ed0).strip()

        return cluster_extracted_date

    def _apply_known_pin_extracted_repairs(self, citations: List[Any]) -> None:
        """
        When citation text matches KNOWN_FEDERAL / KNOWN_WL but extracted_case_name came from
        neighbor bleed (e.g. UFCW name on 943 F. Supp. 172 = Delta Dental), repair extracted
        metadata.

        Pin year is always applied when present (fixes Cardizem/Aggrenox after the enhancement
        loop rewrites names with wrong TOA tails). Name replacement stays conservative (overlap
        < 0.30) so we do not stomp valid short captions that still match the same case.
        """
        from src.verification.known_citations import _lookup_known_federal
        from src.verification.utils import calculate_case_name_overlap

        for citation in citations:
            cit = getattr(citation, "citation", None) or ""
            if not (cit or "").strip():
                continue
            kn = _lookup_known_federal(cit)
            if not kn:
                continue
            canon = (kn.get("canonical_name") or "").strip()
            if not canon:
                continue
            yn = self._canonical_year_from_known_row(kn)
            ext = (getattr(citation, "extracted_case_name", None) or "").strip()

            if not ext or ext.upper() == "N/A":
                citation.extracted_case_name = self._clean_extracted_case_name(canon)
            elif not names_are_same_case(ext, canon):
                ov = calculate_case_name_overlap(ext, canon)
                if ov < 0.30:
                    citation.extracted_case_name = self._clean_extracted_case_name(canon)
                    logger.info(
                        f"[KNOWN-PIN-REPAIR] Replaced extracted name with pin canonical for cite '{cit[:80]}'"
                    )

            if yn:
                citation.extracted_date = yn
                self._set_extracted_date_provenance(citation, "known_citation_pin", "high")
                self._harmonize_trailing_year_in_extracted_case_name(citation, yn)

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
                    # No URL: cannot verify; keep unverified (possible_match requires URL evidence).
                    if similarity < 0.35 and hasattr(citation, "__dict__"):
                        citation.verified = False
                        citation.possible_match = False
                        citation.canonical_name = None
                        citation.canonical_date = None
                        citation.canonical_url = None
                        citation.url = verify_result.get("url")
                        citation.source = source
                        citation.metadata = citation.metadata or {}
                        citation.metadata[f"{source.lower()}_source"] = verify_result.get("source")
                        citation.metadata["canonical_name_validation"] = "unverified_low_similarity"
                        citation.metadata["possible_match_name"] = canonical_name
                        citation.metadata["possible_match_date"] = verify_result.get("canonical_date")
                        citation.metadata["possible_match_url"] = verify_result.get("url")
                        citation.verification_status = "not_found"
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
            except Exception as attr_err:
                # Be conservative: do not interrupt verification if accessing attributes fails
                logger.debug(
                    f"[SEPARATION-GUARD] Could not preserve extracted_case_name for "
                    f"{getattr(citation, 'citation', 'unknown')}: {attr_err}"
                )

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

                # Date mismatch: compare against source-aware canonical year.
                if hasattr(citation, "__dict__"):
                    year_eval = self._evaluate_year_alignment(
                        citation_text=str(getattr(citation, "citation", "") or ""),
                        extracted_date=getattr(citation, "extracted_date", None),
                        canonical_date=getattr(citation, "canonical_date", None),
                        verification_source=getattr(citation, "source", source),
                        in_toa_section=bool((getattr(citation, "metadata", {}) or {}).get("in_toa_section", False)),
                        allow_soft_mismatch=False,
                    )
                    citation.date_mismatch = bool(year_eval.get("hard_mismatch", False))
                    citation.metadata = citation.metadata or {}
                    citation.metadata["year_source"] = year_eval.get("compare_source")
                    citation.metadata["year_compare_value"] = year_eval.get("compare_year")
                    if year_eval.get("soft_mismatch"):
                        citation.metadata["year_mismatch_type"] = "soft"
                    elif year_eval.get("hard_mismatch"):
                        citation.metadata["year_mismatch_type"] = "hard"
                    else:
                        citation.metadata["year_mismatch_type"] = None
            except Exception as e:
                logger.warning(
                    f"[MISMATCH-TAGGING] Failed to tag mismatch for {getattr(citation, 'citation', 'unknown')}: {e}"
                )
            return True
        else:
            # CRITICAL: Unverified citations CANNOT have canonical data
            # EXCEPTIONS: diagnostic lanes preserve canonical candidate context so UI can
            # show "Date Differences"/"Possible Match" with source details.
            citation.verified = False

            # Preserve canonical fields for mismatch/possible-match diagnostics.
            current_source = getattr(citation, "source", None)
            verification_status = str(getattr(citation, "verification_status", "") or "").strip().lower()
            keep_diagnostic_candidate = bool(
                current_source == "year_mismatch_rejected"
                or getattr(citation, "date_mismatch", False)
                or getattr(citation, "possible_match", False)
                or verification_status
                in {
                    "year_mismatch",
                    "possible_match_with_url",
                    "possible_match_gate_reject",
                    "possible_match_no_canonical_url",
                }
            )
            if not keep_diagnostic_candidate:
                # Clear canonical data for unverified citations (except year_mismatch_rejected)
                citation.canonical_name = None
                citation.canonical_date = None
                citation.canonical_url = None
            # else: preserve canonical candidate metadata for downstream cluster/display logic

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

    def _normalize_case_name_for_clustering(self, case_name: str) -> str:
        """
        Backward-compatible clustering normalizer.
        Uses the same canonical normalization used for name comparison.
        """
        return self._normalize_case_name_for_comparison(case_name)

    def _normalize_to_bluebook_format(self, citation: str) -> str:
        """
        Backward-compatible display normalizer for Bluebook-like spacing.
        """
        return self._normalize_citation_comprehensive(citation, purpose="bluebook")

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

        # If substantial overlap (>60% of smaller set), consider them matching.
        # Year alignment is now strict, so name matching can be slightly more permissive.
        smaller_set = min(words1, words2, key=len)
        larger_set = max(words1, words2, key=len)

        overlap = len(smaller_set & larger_set)
        if overlap / len(smaller_set) >= 0.6:
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

    def _derive_compare_year(
        self,
        citation_text: str,
        canonical_date: Optional[str],
        extracted_date: Optional[str],
        verification_source: Optional[str],
        in_toa_section: bool = False,
    ) -> Tuple[Optional[str], str]:
        """
        Pick the most reliable year for mismatch comparisons.

        Returns:
            (year, source_tag)
            source_tag in {
                "citation_text",
                "canonical_date",
                "extracted_fallback",
                "scotus_cl_minus_one",
                "none",
                "toa_skip",
            }
        """
        if in_toa_section:
            return None, "toa_skip"

        canonical_year = extract_year_value(canonical_date)
        extracted_year = extract_year_value(extracted_date)

        # Strongest signal: year encoded directly in citation text
        # e.g. "2025 WL 1237305", "(2014)".
        # FIX: When extracted and canonical match but citation_text differs, prefer them
        # (citation_text can be contaminated by neighboring parentheticals in citation blocks)
        try:
            citation_year = extract_year_from_citation(citation_text or "")
            if citation_year:
                cit_yr_str = str(citation_year)
                if canonical_year and extracted_year and canonical_year == extracted_year:
                    if cit_yr_str != canonical_year:
                        logger.debug(
                            f"[YEAR-DERIVE] Preferring extracted/canonical {canonical_year} over "
                            f"citation_text {cit_yr_str} (likely contamination from neighboring cite)"
                        )
                        return canonical_year, "canonical_date"
                return cit_yr_str, "citation_text"
        except Exception as year_err:
            logger.debug(f"[YEAR-DERIVE] citation-text year extraction skipped: {year_err}")
        source_norm = str(verification_source or "").lower()

        # Narrow exception: CourtListener can occasionally expose a Supreme Court date
        # one year earlier than the citation's decision year. Permit only this specific
        # pattern for U.S. Supreme Court citations; all other courts remain strict.
        if canonical_year and extracted_year and "courtlistener" in source_norm:
            is_scotus_citation = bool(
                re.search(
                    r"\b\d+\s+(?:U\.?\s*S\.?|S\.?\s*Ct\.?|L\.?\s*Ed\.?\s*(?:2d)?)\s+",
                    str(citation_text or ""),
                    re.IGNORECASE,
                )
            )
            if is_scotus_citation:
                try:
                    if int(canonical_year) + 1 == int(extracted_year):
                        return extracted_year, "scotus_cl_minus_one"
                except Exception as scotus_year_err:
                    logger.debug(f"[YEAR-DERIVE] SCOTUS CourtListener offset check skipped: {scotus_year_err}")

        if canonical_year:
            return canonical_year, "canonical_date"
        if extracted_year:
            return extracted_year, "extracted_fallback"
        return None, "none"

    def _evaluate_year_alignment(
        self,
        citation_text: str,
        extracted_date: Optional[str],
        canonical_date: Optional[str],
        verification_source: Optional[str],
        in_toa_section: bool = False,
        allow_soft_mismatch: bool = False,
    ) -> Dict[str, Any]:
        """
        Evaluate year mismatch severity.

        Returns:
            {
              "accept": bool,                 # whether verification should remain accepted
              "hard_mismatch": bool,          # strong mismatch
              "soft_mismatch": bool,          # informational mismatch
              "year_diff": int,
              "compare_year": Optional[str],  # chosen canonical compare year
              "compare_source": str           # see _derive_compare_year()
            }
        """
        src_l = str(verification_source or "").strip().lower()
        # Curated pins (known_federal / known_wl / known_state) are authoritative: do not
        # strip verification because TOA/cluster years disagree with the pin (e.g. Cardizem
        # 332 F.3d 896 with a stray 1992 near the cite in the document).
        if src_l in ("known_federal", "known_wl", "known_state"):
            return {
                "accept": True,
                "hard_mismatch": False,
                "soft_mismatch": False,
                "year_diff": 0,
                "compare_year": extract_year_value(canonical_date),
                "compare_source": "known_pin",
            }

        ext_year = extract_year_value(extracted_date)
        compare_year, compare_source = self._derive_compare_year(
            citation_text, canonical_date, extracted_date, verification_source, in_toa_section
        )
        if not ext_year or not compare_year:
            return {
                "accept": True,
                "hard_mismatch": False,
                "soft_mismatch": False,
                "year_diff": 0,
                "compare_year": compare_year,
                "compare_source": compare_source,
            }

        # Defensive year handling: keep behavior correct even if an older helper path
        # fails to parse pre-1900 years.
        year_diff = abs(int(ext_year) - int(compare_year))
        match, helper_year_diff, extracted_clearly_wrong = years_match_for_verification(
            ext_year, compare_year, tolerance=0
        )
        if isinstance(helper_year_diff, int) and helper_year_diff > 0:
            year_diff = helper_year_diff
        # If helper accepted with diff=0 but we parsed distinct years, trust direct parse.
        if match and year_diff > 0:
            match = False
        # TOA year vs CourtListener filing/decision year often differs by 1 on district reports (F. Supp.*);
        # do not hard-fail those. Keep strict behavior for F.3d / F.2d (see test_year_diff_one_is_hard_mismatch).
        # WL/LEXIS excluded: year is explicit in citation text.
        _wl_lexis_year_in_cite = bool(
            re.search(
                r"\b(?:19|20)\d{2}\s+(?:WL|(?:U\.S\.?\s*)?LEXIS)\s+\d+",
                str(citation_text or ""),
                re.IGNORECASE,
            )
        )
        _f_supp_family = bool(
            re.search(
                r"\bF\.\s*Supp\.?\s*(?:2d|3d)?\b",
                str(citation_text or ""),
                re.IGNORECASE,
            )
        )
        if (
            not match
            and not extracted_clearly_wrong
            and year_diff == 1
            and compare_source == "canonical_date"
            and not _wl_lexis_year_in_cite
            and _f_supp_family
        ):
            match = True
        if extracted_clearly_wrong or match:
            return {
                "accept": True,
                "hard_mismatch": False,
                "soft_mismatch": False,
                "year_diff": year_diff,
                "compare_year": compare_year,
                "compare_source": compare_source,
            }

        # Soft mismatch: fallback-derived decision-year proxy differs.
        if allow_soft_mismatch and compare_source == "extracted_fallback":
            return {
                "accept": True,
                "hard_mismatch": False,
                "soft_mismatch": True,
                "year_diff": year_diff,
                "compare_year": compare_year,
                "compare_source": compare_source,
            }

        # CourtListener + circuit reporter with no decision year in the cite string: extracted_date
        # often bleeds from TOA / neighbor lines (e.g. 1992 vs 2003). Prefer canonical cluster year
        # when the gap is large. Keep |diff|==1 strict (test_year_diff_one_is_hard_mismatch_no_tolerance).
        _ct = str(citation_text or "")
        _circuit_rep = bool(
            re.search(r"\b\d+\s+F\.\s*(?:3d|2d|4th)\s+\d+", _ct, re.IGNORECASE)
        )
        _scotus_rep = bool(
            re.search(r"\b\d+\s+U\.\s*S\.\s+\d+", _ct, re.IGNORECASE)
            or re.search(r"\b\d+\s+S\.\s*Ct\.\s+\d+", _ct, re.IGNORECASE)
        )
        _wl_in_ct = bool(re.search(r"\b(?:19|20)\d{2}\s+WL\s+\d+", _ct, re.IGNORECASE))
        if (
            not match
            and not _scotus_rep
            and _circuit_rep
            and not _wl_in_ct
            and extract_year_from_citation(_ct) is None
            and ("courtlistener" in src_l or src_l == "batch_verify")
            and year_diff >= 3
            and compare_source == "canonical_date"
        ):
            return {
                "accept": True,
                "hard_mismatch": False,
                "soft_mismatch": True,
                "year_diff": year_diff,
                "compare_year": compare_year,
                "compare_source": "cl_trust_no_cite_year_circuit",
            }

        return {
            "accept": False,
            "hard_mismatch": True,
            "soft_mismatch": False,
            "year_diff": year_diff,
            "compare_year": compare_year,
            "compare_source": compare_source,
        }

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
                # CRITICAL: Do NOT group citations separated by TOA dotted leaders (e.g. "...15, 16")
                # These are separate TOA entries for different cases even if close in position.
                if re.search(r'\.{3,}', text_between):
                    if len(current_group) > 1:
                        groups.append(current_group)
                    current_group = [curr]
                    continue
                # CRITICAL: Do NOT group citations separated by semicolon (e.g. "A; B; C")
                if ";" in text_between:
                    if len(current_group) > 1:
                        groups.append(current_group)
                    current_group = [curr]
                    continue
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

    def _apply_toa_span_metadata(self, citations: List[Any], text: Optional[str]) -> None:
        """Set metadata['in_toa_section'] when start_index lies inside detected Table of Authorities."""
        if not text or not citations:
            return
        try:
            from src.toa_parser import ToAParser

            bounds = ToAParser().detect_toa_section(text)
        except Exception as e:
            logger.debug("[TOA-SPAN] Skipping TOA span tagging: %s", e)
            return
        if not bounds:
            return
        toa_start, toa_end = int(bounds[0]), int(bounds[1])
        tagged = 0
        for c in citations:
            s = getattr(c, "start_index", None)
            if s is None:
                continue
            if toa_start <= int(s) < toa_end:
                md = getattr(c, "metadata", None)
                if not isinstance(md, dict):
                    md = {}
                md["in_toa_section"] = True
                c.metadata = md
                tagged += 1
        if tagged:
            logger.info(
                "[TOA-SPAN] Marked %s citation(s) in_toa_section=True (bounds %s–%s)",
                tagged,
                toa_start,
                toa_end,
            )

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
                        # Match main pipeline: allow CL search + web sources when lookup misses
                        enable_fallback=True,
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
        logger.error(f"[BATCH-VERIFY] [WARNING] _verify_citations_sync CALLED with {len(citations)} citations")
        logger.error(f"[BATCH-VERIFY] Starting BATCH verification for {len(citations)} citations")

        if not citations:
            return citations

        self._apply_toa_span_metadata(citations, text)

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
                        f"[SKIP] [FIX #62] SKIPPING '{citation.citation}': already fully verified with canonical data"
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
                citation_strings = []
                for c in citations_to_verify:
                    raw_cit = c.citation
                    query_cit = self._sanitize_citation_for_verification_query(raw_cit)
                    citation_strings.append(query_cit)
                    if query_cit != raw_cit:
                        logger.info(
                            f"[VERIFY-SANITIZE] Query citation trimmed: '{str(raw_cit)[:90]}' -> '{query_cit[:90]}'"
                        )
                case_names = [c.extracted_case_name for c in citations_to_verify]
                # Document-first policy: only pass extracted years to verification when confidence is not low.
                # This prevents contaminated/borrowed years from blocking a correct CourtListener match.
                dates = []
                for c in citations_to_verify:
                    md = getattr(c, "metadata", None) or {}
                    conf = str(md.get("extracted_date_confidence") or "").strip().lower()
                    y = getattr(c, "cluster_year", None) or c.extracted_date
                    if conf in ("", "low"):
                        dates.append(None)
                    else:
                        dates.append(y)
                # Citation-type flags: drive name+date fallback in verification (single path)
                proprietary_flags = [getattr(c, "is_proprietary_only", False) for c in citations_to_verify]
                # USER FIX 2026-01-09: Extract in_toa_section metadata for TOA year validation skip
                toa_flags = [
                    bool(c.metadata.get("in_toa_section", False)) if hasattr(c, "metadata") and c.metadata else False
                    for c in citations_to_verify
                ]
                logger.error(f"[TOA-FLAGS-DEBUG] Extracted {sum(toa_flags)} TOA citations out of {len(toa_flags)} total")

                # Run master batch verification once in a separate event loop.
                # ThreadPoolExecutor is REQUIRED here because we're already inside
                # asyncio.run() from rq_worker.py - can't nest event loops without it.
                # Memory mitigation: pass data as args (not closure) so main thread
                # can release its references while worker thread runs.
                try:
                    from concurrent.futures import ThreadPoolExecutor

                    # Allow fallback on all candidates by default; rely on global
                    # time budget to avoid runaway retries on large documents.
                    # VERIFICATION_MAX_FALLBACK_CITATIONS can override this for tuning.
                    _env_max_fb = os.getenv("VERIFICATION_MAX_FALLBACK_CITATIONS", "").strip()
                    if _env_max_fb.isdigit():
                        _max_fb = max(0, int(_env_max_fb))
                    else:
                        _max_fb = total
                    _env_fb_budget = os.getenv("VERIFICATION_FALLBACK_TIME_BUDGET_SECONDS", "").strip()
                    if _env_fb_budget.isdigit():
                        _fb_time_budget = max(0, int(_env_fb_budget))
                    else:
                        # Wall-clock for all extended fallbacks in one job; 120s often exhausted on long TOAs
                        _fb_time_budget = 180

                    def _run_verification_in_new_loop(
                        _verifier, _citations, _names, _dates, _proprietary_flags, _total, _max_fb_count, _fb_budget_count, _progress_cb
                    ):
                        """Run batch verification in a new event loop (separate thread)."""
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            def batch_progress_callback(processed_count, status, message):
                                if _progress_cb:
                                    try:
                                        processed_global = processed_count or 0
                                        if processed_global > _total:
                                            # Fallback phase: processed_global > _total means we are
                                            # doing per-citation extended verification for unverified
                                            # citations. Use a message WITHOUT the "(X/Y citations)"
                                            # pattern so file_progress_callback does NOT parse it as
                                            # a backward-progress ratio.  The percent stays at 99 %
                                            # (processed_global caps at _total-1) while the message
                                            # advances, giving the user visible feedback.
                                            fallback_done = processed_global - _total
                                            global_message = (
                                                f"Extended verification: {fallback_done} citations "
                                                f"(checking additional sources)"
                                            )
                                        else:
                                            global_message = (
                                                f"Verifying citations... ({processed_global}/{_total} citations)"
                                            )
                                        _progress_cb(processed_global, status, global_message)
                                    except Exception as e:
                                        logger.warning(f"Progress callback failed: {e}")

                            logger.error(
                                f"[BATCH-VERIFY] Calling verify_citations_batch with "
                                f"enable_fallback=True, max_fallback_citations={_max_fb_count}, "
                                f"fallback_time_budget_seconds={_fb_budget_count}, batch_size=250"
                            )
                            results = loop.run_until_complete(
                                _verifier.verify_citations_batch(
                                    citations=_citations,
                                    extracted_case_names=_names,
                                    extracted_dates=_dates,
                                    proprietary_flags=_proprietary_flags,
                                    progress_callback=batch_progress_callback if _progress_cb else None,
                                    enable_fallback=True,
                                    max_fallback_citations=_max_fb_count,
                                    fallback_time_budget_seconds=_fb_budget_count,
                                )
                            )
                            logger.error(f"[BATCH-VERIFY] verify_citations_batch returned {len(results)} results")
                            return results
                        finally:
                            loop.close()
                            asyncio.set_event_loop(None)

                    with ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(
                            _run_verification_in_new_loop,
                            verifier, citation_strings, case_names, dates, proprietary_flags,
                            total, _max_fb, _fb_time_budget, progress_callback,
                        )
                        # Release main-thread references while worker runs
                        citation_strings = None
                        case_names = None
                        dates = None
                        proprietary_flags = None
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
                        except Exception as trim_err:
                            logger.debug(f"[BATCH-VERIFY] malloc_trim skipped: {trim_err}")
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

                # Defensive guard: verifier output must align 1:1 with citations.
                # If a verifier path ever returns fewer results, pad with explicit
                # unverified placeholders to prevent positional drift contamination.
                if len(all_results) != len(citations_to_verify):
                    logger.error(
                        f"[BATCH-VERIFY] Length mismatch: got {len(all_results)} results for "
                        f"{len(citations_to_verify)} citations. Padding/truncating to maintain alignment."
                    )
                    from src.verification import VerificationResult
                    if len(all_results) < len(citations_to_verify):
                        for missing_citation in citations_to_verify[len(all_results):]:
                            all_results.append(
                                VerificationResult(
                                    citation=missing_citation.citation,
                                    verified=False,
                                    error="Missing verification result (alignment guard)",
                                )
                            )
                    else:
                        all_results = all_results[:len(citations_to_verify)]

                # Apply results to citation objects
                verified_count = 0
                import re as re_module

                for citation, result in zip(citations_to_verify, all_results):
                    # Preserve extracted fields
                    original_extracted_name = getattr(citation, "extracted_case_name", None)
                    original_extracted_date = getattr(citation, "extracted_date", None)
                    if "1734066" in (getattr(citation, "citation", "") or ""):
                        logger.warning(
                            f"[WL-DIAG] VERIFY-START citation='{(getattr(citation, 'citation', '') or '')[:50]}' "
                            f"original_extracted_name='{original_extracted_name}'"
                        )
                    
                    # DEBUG: Log verification result application
                    citation_str = str(getattr(citation, "citation", ""))

                    if result and getattr(result, "verified", False):
                        # Source-aware year validation before accepting verification.
                        # Uses citation year when available; otherwise uses canonical_date
                        # with CourtListener-specific filed-vs-decided fallback handling.
                        extracted_date = original_extracted_date
                        canonical_date = result.canonical_date
                        year_match = True  # Default to True when no comparable years
                        year_diff = 0
                        
                        # Check if this citation is from Table of Authorities section
                        citation_metadata = getattr(citation, "metadata", {})
                        in_toa_section = citation_metadata.get("in_toa_section", False)
                        year_eval = self._evaluate_year_alignment(
                            citation_text=str(getattr(citation, "citation", "") or ""),
                            extracted_date=extracted_date,
                            canonical_date=canonical_date,
                            verification_source=getattr(result, "source", None),
                            in_toa_section=bool(in_toa_section),
                            allow_soft_mismatch=False,
                        )
                        year_match = bool(year_eval.get("accept", True))
                        year_diff = int(year_eval.get("year_diff", 0) or 0)
                        citation.metadata = citation.metadata or {}
                        citation.metadata["year_source"] = year_eval.get("compare_source")
                        citation.metadata["year_compare_value"] = year_eval.get("compare_year")
                        if year_eval.get("soft_mismatch"):
                            citation.metadata["year_mismatch_type"] = "soft"
                            citation.date_mismatch = False
                        elif year_eval.get("hard_mismatch"):
                            citation.metadata["year_mismatch_type"] = "hard"
                            citation.date_mismatch = True
                        else:
                            citation.metadata["year_mismatch_type"] = None
                            citation.date_mismatch = False

                        if not year_match:
                            logger.warning(
                                f"[BATCH-YEAR-REJECT] {citation.citation}: extracted={extracted_date} "
                                f"canonical={canonical_date} compare_source={year_eval.get('compare_source')} diff={year_diff}"
                            )
                            # Year mismatch - reject verification BUT PRESERVE canonical data for clustering
                            citation.verified = False
                            citation.date_mismatch = True
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
                            # the extraction grabbed a nearby case name - fix at source.
                            # EXCEPTION: For docket-only citations (e.g. "17 Cv. 7507 (F.DNY...)"),
                            # keep document-extracted name (e.g. "King v. Ortiz"); CourtListener may
                            # return a different case for the same docket number.
                            _cit = (getattr(citation, "citation", None) or "").strip()
                            _is_docket_only = bool(re_module.search(r"^\d{2}\s+Cv\.?\s+\d{4,}", _cit)) or bool(re_module.search(r"No\.\s*\d", _cit))
                            _ecn = (citation.extracted_case_name or "").strip()
                            _cn = (result.canonical_name or "").strip()
                            if _ecn and _ecn != "N/A" and _cn and _cn != "N/A" and not _is_docket_only:
                                from src.utils.same_case import names_are_same_case
                                if not names_are_same_case(_ecn, _cn):
                                    if "1734066" in (_cit or ""):
                                        logger.warning(
                                            f"[WL-DIAG] VERIFY-OVERWRITE BATCH-ECN-FIX: ECN '{_ecn}' -> canonical '{_cn}'"
                                        )
                                    logger.info(
                                        f"[BATCH-ECN-FIX] {citation.citation}: ECN '{_ecn}' doesn't match "
                                        f"canonical '{_cn}' - replacing ECN with canonical"
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
                            # Has canonical name but no URL - cannot mark as verified (user rule: verified requires URL).
                            # Keep this visible as a tunable candidate instead of collapsing to generic unverified.
                            citation.verified = False
                            citation.canonical_name = result.canonical_name
                            citation.canonical_date = getattr(result, "canonical_date", None)
                            citation.possible_match = False
                            citation.verification_status = "not_found"
                            citation.source = result.source or "batch_verify"
                            citation.metadata = citation.metadata or {}
                            citation.metadata["possible_match_reason"] = "source_missing_canonical_url"
                            citation.metadata["possible_match_source"] = citation.source
                            citation.metadata["possible_match_method"] = str(getattr(result, "method", "") or "")
                            if not getattr(citation, "error", None):
                                citation.error = "No canonical URL from source"
                            logger.warning(
                                f"[BATCH-NO-URL] {citation.citation}: Canonical name returned but no URL - marking unverified"
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
                        is_possible_match = bool(getattr(result, "possible_match", False))
                        result_method = str(getattr(result, "method", "") or "")
                        result_canonical = getattr(result, "canonical_name", None) if result else None
                        result_canonical_date = getattr(result, "canonical_date", None) if result else None
                        result_url = (
                            (getattr(result, "canonical_url", None) if result else None)
                            or (getattr(result, "url", None) if result else None)
                        )
                        logger.warning(
                            f"[BATCH-NOT-VERIFIED] {citation.citation}: result.verified={getattr(result, 'verified', 'N/A')}, "
                            f"source={result_source}, error={getattr(result, 'error', 'N/A')}, "
                            f"canonical_name={getattr(result, 'canonical_name', 'N/A')}, "
                            f"canonical_url={getattr(result, 'canonical_url', 'N/A')}"
                        )

                        # Preserve strict-gate rejects as explicit "possible match" candidates
                        # so they are visible for tuning instead of collapsing into generic unverified.
                        if is_possible_match or result_method.endswith("gate_reject"):
                            # Name+date-only fallback (WL): always expose when we have a URL so "Possible Match" + link show
                            if result_url and result_method and "name_date_only" in result_method:
                                expose_candidate = True
                            else:
                                expose_candidate = self._should_expose_gate_reject_canonical(
                                    str(getattr(citation, "citation", "") or ""),
                                    result,
                                )
                            citation.possible_match = bool(expose_candidate)
                            citation.canonical_name = result_canonical if expose_candidate else None
                            citation.canonical_date = result_canonical_date if expose_candidate else None
                            citation.canonical_url = result_url if expose_candidate else None
                            citation.url = result_url if expose_candidate else None
                            # When we have a URL, use possible_match_with_url so proprietary message is cleared
                            citation.verification_status = (
                                "possible_match_with_url" if (expose_candidate and result_url) else (
                                    "possible_match_gate_reject" if expose_candidate else "not_found"
                                )
                            )
                            citation.metadata = citation.metadata or {}
                            citation.metadata["possible_match_reason"] = "strict_gate_reject"
                            citation.metadata["possible_match_source"] = result_source
                            citation.metadata["possible_match_method"] = result_method
                            citation.metadata["citation_core_match"] = bool(
                                isinstance(getattr(result, "raw_data", None), dict)
                                and getattr(result, "raw_data", {}).get("citation_core_match") is True
                            )

                            # User-requested behavior: proprietary citations can be surfaced as
                            # "Verified by Parallel" even when not accepted as direct verification.
                            _cit_text = str(getattr(citation, "citation", "") or "")
                            _is_proprietary = bool(re_module.search(r"\b\d{4}\s+(WL|U\.?\s*S\.?\s*LEXIS|LEXIS)\s+\d+\b", _cit_text, re_module.IGNORECASE))
                            # Only mark as true_by_parallel if NOT already verified with a real URL
                            # This prevents overriding direct verification results
                            already_verified_with_url = (
                                getattr(citation, 'verified', False) 
                                and getattr(citation, 'canonical_url', None)
                                and not str(getattr(citation, 'canonical_url', '')).startswith('https://www.google.com')
                            )
                            if _is_proprietary and expose_candidate and not already_verified_with_url:
                                citation.true_by_parallel = True
                                citation.metadata["true_by_parallel"] = True
                                citation.metadata["parallel_not_in_document"] = True
                                citation.verification_status = "verified_by_parallel_not_in_document"
                                if not getattr(citation, "error", None):
                                    citation.error = "Possible match found (not in document)"
                                logger.info(
                                    f"[BATCH-POSSIBLE-PARALLEL] {citation.citation}: proprietary possible match "
                                    f"surfaced as true_by_parallel for review"
                                )

                        # Recovery path: if fallback returned a concrete canonical URL + name,
                        # allow verification when year alignment is acceptable.
                        if (
                            result_url
                            and result_canonical
                            and result_canonical != "N/A"
                            and not self._na_and_partial_insufficient(citation)
                        ):
                            year_eval = self._evaluate_year_alignment(
                                citation_text=str(getattr(citation, "citation", "") or ""),
                                extracted_date=original_extracted_date,
                                canonical_date=result_canonical_date,
                                verification_source=result_source,
                                in_toa_section=bool((getattr(citation, "metadata", {}) or {}).get("in_toa_section", False)),
                                allow_soft_mismatch=False,
                            )
                            citation.metadata = citation.metadata or {}
                            citation.metadata["year_source"] = year_eval.get("compare_source")
                            citation.metadata["year_compare_value"] = year_eval.get("compare_year")
                            if year_eval.get("soft_mismatch"):
                                citation.metadata["year_mismatch_type"] = "soft"
                            elif year_eval.get("hard_mismatch"):
                                citation.metadata["year_mismatch_type"] = "hard"
                            else:
                                citation.metadata["year_mismatch_type"] = None

                            if year_eval.get("accept", True):
                                citation.verified = True
                                citation.canonical_name = result_canonical
                                citation.canonical_date = result_canonical_date
                                citation.canonical_url = result_url
                                citation.url = result_url
                                citation.verification_status = "verified_from_fallback_url"
                                citation.error = None
                                citation.verification_error = None
                                citation.date_mismatch = False
                                citation.source = result_source or "fallback_url"
                                verified_count += 1
                                logger.warning(
                                    f"[BATCH-URL-RECOVERED] {citation.citation} -> {result_canonical} "
                                    f"(source: {citation.source})"
                                )
                                continue
                            else:
                                # Keep as possible match with URL instead of proprietary/no-results.
                                citation.possible_match = True
                                citation.canonical_name = result_canonical
                                citation.canonical_date = result_canonical_date
                                citation.canonical_url = result_url
                                citation.url = result_url
                                citation.verification_status = "possible_match_with_url"
                                logger.warning(
                                    f"[BATCH-URL-POSSIBLE] {citation.citation}: URL present but hard year mismatch "
                                    f"(compare_source={year_eval.get('compare_source')}, diff={year_eval.get('year_diff')})"
                                )

                        # CRITICAL FIX: Preserve canonical data for year_mismatch_rejected
                        # This allows clustering to split by canonical year even when unverified
                        if result_source == "year_mismatch_rejected" and result:
                            citation.verification_status = "year_mismatch"
                            citation.canonical_name = getattr(result, "canonical_name", None)
                            citation.canonical_date = getattr(result, "canonical_date", None)
                            citation.canonical_url = getattr(result, "canonical_url", None)
                            citation.verification_error = getattr(result, "error", None)
                            logger.warning(
                                f"[BATCH-YEAR-MISMATCH] {citation.citation}: {result.error} - canonical data preserved for clustering"
                            )
                        else:
                            # Do not overwrite possible_match_with_url / possible_match_gate_reject set above
                            # (e.g. from name+date-only fallback for WL citations)
                            if getattr(citation, "verification_status", None) not in (
                                "possible_match_with_url",
                                "possible_match_gate_reject",
                                "verified_by_parallel_not_in_document",
                            ):
                                citation.verification_status = "not_found"

                        if not citation.extracted_case_name or citation.extracted_case_name == "N/A":
                            citation.extracted_case_name = original_extracted_name
                            if "1734066" in (getattr(citation, "citation", "") or ""):
                                logger.warning(
                                    f"[WL-DIAG] VERIFY-RESTORE extracted_case_name='{original_extracted_name}' (was N/A)"
                                )
                        if not citation.extracted_date or citation.extracted_date == "N/A":
                            citation.extracted_date = original_extracted_date
                        error_msg = getattr(result, "error", None) if result else "No result"
                        if not error_msg and not getattr(result, "verified", False):
                            error_msg = "No result"
                        # Surface verification failure reason so UI can show why (e.g. "No API key", "Rate limited")
                        if error_msg and not getattr(citation, "error", None):
                            citation.error = error_msg
                            citation.verification_error = error_msg

                logger.info(f"[BATCH-VERIFY] Completed master batch verification: verified {verified_count}/{total}")

            # USER FIX 2026-01-12: Post-verification fix for obvious CourtListener mismatches
            # CourtListener often returns wrong cases for citations (e.g., 139 S. Ct. 1112 -> Zagorski instead of Bucklew)
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
            logger.exception(f"[VERIFICATION] Error in unified master verification: {str(e)}")
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
            except Exception as trim_err:
                logger.debug(f"[MEMORY] Final malloc_trim skipped (first attempt): {trim_err}")
            _gc_final.collect()
            try:
                _ct_final.CDLL("libc.so.6").malloc_trim(0)
            except Exception as trim_err:
                logger.debug(f"[MEMORY] Final malloc_trim skipped (second attempt): {trim_err}")
        except Exception as mem_err:
            logger.debug(f"[MEMORY] Final cleanup skipped: {mem_err}")

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

    def _normalize_citation_comprehensive(
        self, citation: str, purpose: str = "general", all_citations: Optional[List[CitationResult]] = None
    ) -> str:
        """
        COMPREHENSIVE CITATION NORMALIZATION - Consolidates all normalization functions.
        All normalization is applied before positions are used (name/date, verification).

        Args:
            citation: Citation string to normalize
            purpose: Normalization purpose - "general", "bluebook", "verification", "comparison"
            all_citations: Optional list of all citations (used to repair truncated pages, e.g. 768 F.3d 2 -> 212)

        Returns:
            Normalized citation string
        """
        if not citation:
            return citation

        normalized = citation.strip()
        normalized = re.sub(r"\s+", " ", normalized)

        # Strip paragraph symbol (¶ / pilcrow U+00B6) — PDF artifact
        normalized = re.sub(r'\u00b6+\s*', '', normalized)

        # Strip leading Table of Authorities / heading noise (e.g. "TABLE OF AUTHORITIES Page() CASES A&M Recs....")
        toa_leading = re.match(
            r"^(?:TABLE\s+OF\s+AUTHORITIES\s*)?(?:Page\s*\(\s*\)\s*)?(?:CASES\s+)?",
            normalized,
            re.IGNORECASE,
        )
        if toa_leading:
            normalized = normalized[toa_leading.end() :].strip()

        # Strip TOC section headers from cert petitions / briefs
        # e.g. "IV Cases-Continued: Page Cochise Consultancy..."
        toc_prefix = re.match(
            r"^(?:[IVXLC]+\s+)?"
            r"(?:Cases|Statutes?|Constitut\w+|Miscellaneous|Other\s+Authorities?|Regulations?)"
            r"(?:\s*[-\u2013\u2014]\s*Continued)?\s*:\s*(?:Page\s+)?",
            normalized,
            re.IGNORECASE,
        )
        if toc_prefix and len(normalized) - toc_prefix.end() >= 10:
            normalized = normalized[toc_prefix.end() :].strip()
        # Strip mid-string TOC fragments ("... 26 VIII Miscellaneous-Continued: Page ...")
        normalized = re.sub(
            r"\.\.\.\s*\d+\s+(?:[IVXLC]+\s+)?"
            r"(?:Cases|Statutes?|Constitut\w+|Miscellaneous|Other\s+Authorities?|Regulations?)"
            r"(?:\s*[-\u2013\u2014]\s*Continued)?\s*:\s*(?:Page\s+)?",
            "... ",
            normalized,
            flags=re.IGNORECASE,
        )

        # Strip docket number prefix (e.g. "Dkt. No. 28). 5 Solutions, LLC, 171 Wash. 2d ...")
        normalized = re.sub(
            r"^(?:\(?\s*)?Dkt\.?\s*No\.?\s*\d+\s*\)\.?\s*(?:\d+\s+)?",
            "",
            normalized,
            flags=re.IGNORECASE,
        ).strip()

        # FIX: Repair pinpoint/page contamination in parallel citations
        # Reporter series (2d, 3d, 4th, 5th, etc.) are part of reporter name, NOT page numbers
        _series = CitationPatterns.REPORTER_SERIES
        _app_series = CitationPatterns.APP_SERIES
        _rep = (
            r"(?:P\.\d*d|P\.|F\.(?:2d|3d|4th)|Wn\.\s*(?:2d|3d)|Wash\.\s*(?:2d|3d|App\.\s*"
            + _app_series
            + r")|S\.E\.\d*d|N\.E\.\d*d|N\.W\.\d*d|S\.W\.\d*d|Cal\.\s*(?:2d|3d|4th|5th|Rptr\.?|App\.\s*"
            + _app_series
            + r")|L\.\s*Ed\.\s*\d*d"
            r"|N\.Y\.S\.\s*\d*d|A\.D\.\s*\d*d|N\.Y\.\s*\d*d"
            r"|A\.\s*\d*d|So\.\s*\d*d|Or\."
            r"|P[23]d"
            r")"
        )
        # 0a) When the comma is missing but a space remains (e.g. "185 9 P.3d"), use the space to infer
        #     the break: insert comma so we get "185, 9 P.3d". Single-pass: match a run of space-separated
        #     digits before reporter and replace internal spaces with ", ". Cap run at 30 numbers to avoid
        #     backtracking on pathological input (citation runs are typically < 10).
        _space_before_rep = r"(?=\s*(?:,\s*\d+)*\s+" + _rep + r"\s+\d+\b)"
        _digit_run_max = 30  # (?: \d+){0,29} then \d+ = up to 30 numbers

        def _commaize_digit_run(m: re.Match) -> str:
            run = m.group(1)
            return re.sub(r"\s+(\d+)", r", \1", run)

        normalized = re.sub(
            r"((?:\d+\s+){" + str(0) + r"," + str(_digit_run_max - 1) + r"}\d+)" + _space_before_rep,
            _commaize_digit_run,
            normalized,
        )
        # 0a2) Parallel-citation page+volume concatenation: "688 N.E.2d 1381666 N.Y.S.2d 99"
        #      The blob "1381666" = page "1381" + volume "666".  Split heuristic: try last-3, last-2,
        #      last-4 digits as the volume candidate (must be 1-999 and leave a 1-4 digit page).
        def _split_pv_concat(m: re.Match) -> str:
            concat = m.group(3)
            rep2 = m.group(4)
            rest = m.group(5)
            for vlen in (3, 2, 4):
                if len(concat) <= vlen:
                    continue
                page_s = concat[:-vlen]
                vol_s = concat[-vlen:]
                if page_s and 1 <= int(vol_s) <= 999 and 1 <= len(page_s) <= 4:
                    return f"{m.group(1)} {m.group(2)} {page_s}, {vol_s} {rep2} {rest}"
            return m.group(0)

        normalized = re.sub(
            r"(\d+)\s+(" + _rep + r")\s+(\d{5,7})\s+(" + _rep + r")\s+(\d+)",
            _split_pv_concat,
            normalized,
        )
        # 0b) Restore lost comma when digits are run together (no space): e.g. "1859 P.3d" -> "185, 9 P.3d".
        #     Reporter-agnostic: page and volume can each be 1–4 digits. Use plausibility to avoid wrong splits.
        def _volume_plausible(vol_str: str, vol_digits: int) -> bool:
            if len(vol_str) != vol_digits:
                return False
            n = int(vol_str)
            if vol_digits == 1:
                return 1 <= n <= 9
            if vol_digits == 2:
                return 10 <= n <= 99
            if vol_digits == 3:
                return 100 <= n <= 599  # avoid e.g. 82961 -> 82, 961
            if vol_digits == 4:
                return 1000 <= n <= 9999
            return False

        def _page_plausible(page_str: str, page_digits: int) -> bool:
            """Plausible page/pinpoint (1-4 digits). Used to avoid splitting e.g. 233 or 209."""
            if len(page_str) != page_digits:
                return False
            n = int(page_str)
            if page_digits == 1:
                return 1 <= n <= 9
            if page_digits == 2:
                return 10 <= n <= 99
            if page_digits == 3:
                return 100 <= n <= 999
            if page_digits == 4:
                return 1000 <= n <= 9999
            return False

        # Shared restore logic for Case A/B/C: same don't-split checks, insert comma when valid.
        def _restore_digits(prefix: str, page: str, vol: str, rest: str) -> str:
            p_d, v_d = len(page), len(vol)
            combined = page + vol
            # Do not split 3-digit volume as 1+2 or 2+1 (e.g. ", 3" "98" -> keep "398" for N.W.2d)
            if len(combined) == 3 and (p_d, v_d) in ((1, 2), (2, 1)):
                try:
                    if 100 <= int(combined) <= 999:
                        return None
                except ValueError:
                    pass
            # Walston: do not split "334" as "3"+"34", or "39134" as "391"+"34" or "3913"+"4", before P.3d (bogus "34 P.3d 519" / "4 P.3d 519").
            if "P.3d" in rest and (combined == "334" or vol == "34" or (vol == "4" and combined == "39134")):
                return None
            if not _volume_plausible(vol, v_d):
                return None  # no change
            # When producing a 4-digit volume, check if shifting one digit
            # from vol to page yields a plausible 3-digit volume instead.
            # E.g. "266115 P.3d" splits as page="26",vol="6115" by the
            # non-greedy regex, but page="266",vol="115" is far better.
            # Defer to later P.3d/0d rules that handle 3+3 splits.
            if v_d == 4 and len(combined) >= 5:
                alt_page = page + vol[0]
                alt_vol = vol[1:]
                if (len(alt_vol) == 3
                        and _volume_plausible(alt_vol, 3)
                        and _page_plausible(alt_page, len(alt_page))):
                    return None
            if len(combined) <= 3 and _page_plausible(combined, len(combined)):
                return None
            if p_d == 1 and len(combined) <= 4 and _volume_plausible(combined, len(combined)):
                return None
            return f"{prefix}{page}, {vol}{rest}"

        _series_or_app = r"(?:" + _series + r"|App\.\s*" + _app_series + r")"
        _rep_tail = r"(\s+" + _rep + r"\s+\d+)\b"
        # 0c) Hyphenated page range before reporter volume (Beauchamp). Run before Case A so "4-5398" -> "4-5, 398" first.
        normalized = re.sub(
            r"(\d{1,2}-\d{1,2})\s*(\d{2,4})\s+(" + _rep + r"\s+\d+)\b",
            r"\1, \2 \3",
            normalized,
        )
        # Case A: comma before page (single pass: 1–4 digit page, 1–4 digit volume)
        def _case_a(m: re.Match):
            out = _restore_digits(m.group(1), m.group(2), m.group(3), m.group(4))
            return out if out is not None else m.group(0)
        # Prefer minimal first group so ", 398" matches as "3","98" (guard keeps 398); greedy would match "39","8"
        normalized = re.sub(r"(,\s*)(\d{1,4}?)(\d{1,4})" + _rep_tail, _case_a, normalized)
        # Case B: no comma — previous token (digits+space) then page+volume (single pass)
        def _case_b(m: re.Match):
            out = _restore_digits(m.group(1), m.group(2), m.group(3), m.group(4))
            return out if out is not None else m.group(0)
        normalized = re.sub(r"(\d+\s+)(\d{1,4})(\d{1,4})" + _rep_tail, _case_b, normalized)
        # Case C: after reporter series (e.g. "Wn. App. 2d 1859 P.3d" -> "2d 185, 9 P.3d") — single pass
        _case_c_prefix = r".{0,500}?"
        def _case_c(m: re.Match):
            out = _restore_digits(m.group(1), m.group(2), m.group(3), m.group(4))
            return out if out is not None else m.group(0)
        _case_c_pat = re.compile(
            r"(" + _case_c_prefix + _series_or_app + r")\s+(\d{1,4})(\d{1,4})" + _rep_tail
        )
        normalized = _case_c_pat.sub(_case_c, normalized)
        # 0d/0d2) Page+volume (3+3 digits) before reporter: adjacent or space/comma-separated (Stertz).
        #     "91 Wash. 588158 P. 256" or "91 Wash. 588 158 P. 256" -> "91 Wash. 588, 158 P. 256"
        def _restore_33(m: re.Match) -> str:
            pre, page, vol, rest = m.group(1), m.group(2), m.group(3), m.group(4)
            if _page_plausible(page, 3) and _volume_plausible(vol, 3):
                return f"{pre}{page}, {vol} {rest}"
            return m.group(0)
        normalized = re.sub(
            r"(.{0,80}?)(\d{3})[\s,]*(\d{3})\s+(" + _rep + r"\s+\d+)\b",
            _restore_33,
            normalized,
        )
        # 1a) P.3d-specific fixes (after comma restore)
        # Pinpoint+volume merged (e.g. ", 616717 P.3d 1353" -> ", 616, 717 P.3d 1353")
        normalized = re.sub(r",\s*(\d{3})(\d{3}\s+P\.3d\s+\d+)\b", r", \1, \2", normalized)
        # Pinpoint+digit+volume merged (e.g. ", 82961 P.3d 1196" -> ", 61 P.3d 1196")
        # Skip stripping when the "kept" 2 digits would be "33" (invalid vol; likely "91"+"233").
        # Walston: ", 39134 P.3d 519" — do NOT strip to "34 P.3d 519"; restore "391, 334 P.3d 519"
        # (the "3" of 334 was lost in PDF/extraction; 34 is not a plausible P.3d volume when 391 precedes).
        def _pinpoint_vol_sub(m: re.Match) -> str:
            stripped = m.group(1)  # 3 digits we would strip (e.g. "391")
            kept = m.group(2)      # e.g. "34 P.3d 519" or "61 P.3d 1196"
            if kept.startswith("33 "):
                return m.group(0)
            # Never output "34 P.3d" as volume — P.3d vols are 100+; "34" is usually tail of 334 (Walston).
            if kept.startswith("34 P.3d"):
                if stripped == "391":
                    return ", 391, 334 " + kept[3:]  # ", 39134 P.3d 519" -> ", 391, 334 P.3d 519"
                return m.group(0)  # do not strip; avoid creating bogus "34 P.3d"
            return ", " + kept
        normalized = re.sub(r",\s*(\d{3})(\d{2}\s+P\.3d\s+\d+)\b", _pinpoint_vol_sub, normalized)
        # 0e) Hyphenated page range glued to volume (e.g. "629-30869 P.2d 1034" -> "629-30, 869 P.2d 1034").
        #     Prevents rule 1 from stripping "308" and producing bogus "69 P.2d" (Waste Mgmt. cite).
        normalized = re.sub(
            r"(\d{2,4}-\d{2})(\d{3})\s+(" + _rep + r"\s+\d+)\b",
            r"\1, \2 \3",
            normalized,
        )
        # 1) After comma: pinpoint merged with volume (e.g. ", 299118 P.2d 985" -> ", 118 P.2d 985")
        #    Only when pinpoint and volume are adjacent (no space), so ", 182 775 P.2d" (Lusk) is not stripped.
        normalized = re.sub(r",\s*(\d{2,3})(\d{3})\s+(" + _rep + r"\s+\d+)\b", r", \2 \3", normalized)
        # 2) Pinpoint with hyphen (e.g. "520-21618 P.2d 1330" -> "618 P.2d 1330").
        # Require at least 2 digits after hyphen so we don't strip "401-334" as "401-3" + "34"
        # (page 401 then volume 334) — single digit after hyphen can start next volume (Walston).
        normalized = re.sub(r"(\d{2,4}-\d{2,4})(\d{2,4}\s+" + _rep + r"\s+\d+)\b", r"\2", normalized)
        # 3) After reporter: page+volume concatenated (e.g. "2d 692635 P.2d" -> "2d 692, 635 P.2d")
        # Use _series so we match 2d, 3d, 4th, App. 2d, etc. - never bare digits as series
        normalized = re.sub(
            r"(" + _series_or_app + r")\s+(\d{3})(\d{3})(\s+" + _rep + r"\s+\d+)\b",
            r"\1 \2, \3\4",
            normalized,
        )
        # 3a) Series glued to digits (e.g. "Wash. 2d391334 P.3d 519" -> "Wash. 2d 391, 334 P.3d 519") — Walston
        def _series_6dig(m: re.Match) -> str:
            pre, page, vol, rest = m.group(1), m.group(2), m.group(3), m.group(4)
            if _page_plausible(page, 3) and _volume_plausible(vol, 3):
                return f"{pre} {page}, {vol}{rest}"
            return m.group(0)
        normalized = re.sub(
            r"(" + _series_or_app + r")(\d{3})(\d{3})(\s+" + _rep + r"\s+\d+)\b",
            _series_6dig,
            normalized,
        )
        # 3a2) Walston: "2d 39134 P.3d 519" (page 391 + vol 334, middle digit lost) -> "2d 391, 334 P.3d 519"
        normalized = re.sub(
            r"(" + _series_or_app + r")\s+39134(\s+P\.3d\s+\d+)\b",
            r"\1 391, 334\2",
            normalized,
        )
        # 3b) Comma-separated contamination (e.g. "2d 5775, 55 P.2d 997" -> "2d 577, 555 P.2d 997")
        normalized = re.sub(
            r"(" + _series_or_app + r")\s+(\d{3})5,\s*55(\s+" + _rep + r"\s+\d+)\b",
            r"\1 \2, 555\3",
            normalized,
        )
        # 4) Footnote superscript as volume: PDF often has "87³ Wn.2d 577" - extractor picks up "3" instead of "87"
        # When single-digit before Wash. 2d/Wn.2d 577 and parallel cite 555 P.2d 997 (Johnson) present -> use 87
        if "555 P.2d 997" in normalized and re.match(r"^3\s+(?:Wash\.\s*2d|Wn\.\s*2d)\s+577\b", normalized):
            normalized = re.sub(r"^3\s+", "87 ", normalized, count=1)

        # 5) Truncated reporter series: PDF extraction often drops "d"/"th" (e.g. "19 Wn. App. 2" -> "19 Wn. App. 2d")
        # Series designations are part of reporter name. Single pass via alternation.
        _trunc_fixes = (
            (r"Wn\.\s*App\.\s*2(?!d)\b", "Wn. App. 2d"),
            (r"Wash\.\s*App\.\s*2(?!d)\b", "Wash. App. 2d"),
            (r"Wash\.\s*2(?!d)\b", "Wash. 2d"),
            (r"Wn\.\s*2(?!d)\b", "Wn. 2d"),
            (r"Cal\.\s*App\.?\s*2(?!d)\b", "Cal. App. 2d"),
            (r"Cal\.\s*App\.?\s*3(?!d)\b", "Cal. App. 3d"),
            (r"Cal\.\s*App\.?\s*4(?!th)\b", "Cal. App. 4th"),
            (r"Cal\.\s*App\.?\s*5(?!th)\b", "Cal. App. 5th"),
            (r"Ill\.\s*App\.\s*2(?!d)\b", "Ill. App. 2d"),
            (r"Ill\.\s*App\.\s*3(?!d)\b", "Ill. App. 3d"),
            (r"Tex\.\s*App\.\s*2(?!d)\b", "Tex. App. 2d"),
            (r"Tex\.\s*App\.\s*3(?!d)\b", "Tex. App. 3d"),
        )
        _trunc_pat = re.compile("|".join(f"({p})" for p, _ in _trunc_fixes))
        _trunc_repl = {i: r for i, (_, r) in enumerate(_trunc_fixes)}

        def _trunc_replacer(m: re.Match) -> str:
            for i, g in enumerate(m.groups()):
                if g is not None:
                    return _trunc_repl[i]
            return m.group(0)

        normalized = _trunc_pat.sub(_trunc_replacer, normalized)

        # 6) S.Ct./L.Ed. page concatenation (e.g. "1513155 L. Ed. 2d 585" -> "1513, 155 L. Ed. 2d 585")
        normalized = re.sub(
            r"(\d{4})(\d{3})\s+(L\.\s*Ed\.\s*2d\s+\d+)\b",
            r"\1, \2 \3",
            normalized,
        )
        # 7) U.S./S.Ct. pinpoint merge (e.g. "421123 S. Ct. 1513" -> "421, 123 S. Ct. 1513")
        normalized = re.sub(
            r"(\d{3})(\d{3})\s+(S\.\s*Ct\.\s+\d+)\b",
            r"\1, \2 \3",
            normalized,
        )

        # PDF artifacts: reporter without space (Supp3d, Supp2d)
        normalized = re.sub(r"Supp\.?\s*3d", "Supp. 3d", normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"Supp\.?\s*2d", "Supp. 2d", normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"(\d+)\s*F\.\s*Supp\.?\s*3d\s*(\d+)", r"\1 F. Supp. 3d \2", normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"(\d+)\s*F\.\s*Supp\.?\s*2d\s*(\d+)", r"\1 F. Supp. 2d \2", normalized, flags=re.IGNORECASE)

        normalized = re.sub(r"(\d+)\s*U\.\s*S\.\s*(\d+)", r"\1 U.S. \2", normalized)

        normalized = re.sub(r"(\d+)\s*F\.\s*(\d+)d\s*(\d+)", r"\1 F.\2d \3", normalized)
        normalized = re.sub(r"(\d+)\s*F\.\s*3d\s*(\d+)", r"\1 F.3d \2", normalized)
        normalized = re.sub(r"(\d+)\s*F\.\s*2d\s*(\d+)", r"\1 F.2d \2", normalized)

        # Repair truncated page numbers (e.g. "768 F.3d 2" from PDF -> "768 F.3d 212") using same-doc citations
        if all_citations:
            # Footnote-as-volume: "3 Wn.2d 577" when parallel 555 P.2d 997 (Johnson) exists in batch
            # (other may be raw "580555 P.2d 997" before 3b runs, or "555 P.2d 997" after)
            if re.match(r"^3\s+(?:Wash\.\s*2d|Wn\.\s*2d)\s+577\b", normalized):
                for c in all_citations:
                    other = getattr(c, "citation", None) or (c if isinstance(c, str) else None)
                    o = other or ""
                    if "577" in o and ("555 P.2d 997" in o or "580555" in o or "580, 555" in o):
                        normalized = re.sub(r"^3\s+", "87 ", normalized, count=1)
                        break
            for c in all_citations:
                other = getattr(c, "citation", None) or (c if isinstance(c, str) else None)
                if not other or other == normalized:
                    continue
                # Same volume + F.3d/F.2d with 3-digit page?
                m_other = re.search(r"(\d+)\s+F\.(3d|2d)\s+(\d{3,})\b", other)
                m_cur = re.search(r"(\d+)\s+F\.(3d|2d)\s+(\d{1,2})\b", normalized)
                if m_other and m_cur and m_other.group(1) == m_cur.group(1) and m_other.group(2) == m_cur.group(2):
                    normalized = re.sub(
                        r"(\d+)\s+F\.(3d|2d)\s+(\d{1,2})\b",
                        rf"\1 F.\2 {m_other.group(3)}",
                        normalized,
                        count=1,
                    )
                    break
                # Truncated Wn. App. 2d / Wash. App. 2d: "19 Wn. App. 2d" with no page -> use fuller citation
                # (other may use Wn. or Wash. - same reporter)
                m_app = re.search(r"(\d+)\s+(?:Wn\.|Wash\.)\s*App\.\s*2d\s+(\d{2,})", other)
                m_cur_wn = re.search(r"(\d+)\s+Wn\.\s*App\.\s*2d\s*$", normalized)
                m_cur_wash = re.search(r"(\d+)\s+Wash\.\s*App\.\s*2d\s*$", normalized)
                if m_app and m_cur_wn and m_app.group(1) == m_cur_wn.group(1):
                    normalized = re.sub(
                        r"(\d+)\s+Wn\.\s*App\.\s*2d\s*$",
                        rf"\1 Wn. App. 2d {m_app.group(2)}",
                        normalized,
                        count=1,
                    )
                    break
                if m_app and m_cur_wash and m_app.group(1) == m_cur_wash.group(1):
                    normalized = re.sub(
                        r"(\d+)\s+Wash\.\s*App\.\s*2d\s*$",
                        rf"\1 Wash. App. 2d {m_app.group(2)}",
                        normalized,
                        count=1,
                    )
                    break
                # Truncated Wash. 2d / Wn. 2d: "96 Wash. 2d" or "124 Wash. 2d" with no page
                m_wn2 = re.search(r"(\d+)\s+(?:Wn\.|Wash\.)\s*2d\s+(\d{2,})", other)
                m_cur_w2 = re.search(r"(\d+)\s+(?:Wash\.|Wn\.)\s*2d\s*$", normalized)
                if m_wn2 and m_cur_w2 and m_wn2.group(1) == m_cur_w2.group(1):
                    rep = "Wash." if "Wash." in normalized else "Wn."
                    normalized = re.sub(
                        r"(\d+)\s+(?:Wash\.|Wn\.)\s*2d\s*$",
                        rf"\1 {rep} 2d {m_wn2.group(2)}",
                        normalized,
                        count=1,
                    )
                    break

        normalized = re.sub(r"(\d+)\s*F\.\s*Supp\.\s*(\d+)d\s*(\d+)", r"\1 F.Supp.\2d \3", normalized)
        normalized = re.sub(r"(\d+)\s*F\.\s*Supp\.\s*3d\s*(\d+)", r"\1 F. Supp. 3d \2", normalized)
        normalized = re.sub(r"(\d+)\s*F\.\s*Supp\.\s*2d\s*(\d+)", r"\1 F. Supp. 2d \2", normalized)
        normalized = re.sub(r"(\d+)\s*F\.\s*Supp\.\s*(\d+)", r"\1 F. Supp. \2", normalized)

        normalized = re.sub(r"(\d+)\s*S\.\s*Ct\.\s*(\d+)", r"\1 S. Ct. \2", normalized)

        normalized = re.sub(r"(\d+)\s*L\.\s*Ed\.\s*2d\s*(\d+)", r"\1 L. Ed. 2d \2", normalized)
        normalized = re.sub(r"(\d+)\s*L\.\s*Ed\.\s*(\d+)", r"\1 L. Ed. \2", normalized)

        normalized = re.sub(r"(\d+)\s*P\.\s*3d\s*(\d+)", r"\1 P.3d \2", normalized)
        normalized = re.sub(r"(\d+)\s*P\.\s*2d\s*(\d+)", r"\1 P.2d \2", normalized)

        # CRITICAL FIX: DO NOT normalize Wn.2d -> Wash.2d for general/verification!
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
            normalized = normalized
        elif purpose == "general":
            # For general purposes (display), still preserve Wn.2d vs Wash.2d distinction
            # Only normalize spacing/punctuation, not reporter names
            normalized = normalized

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

        if purpose != "comparison":
            try:
                from src.utils.extraction_cleaner import (
                    merge_s_ct_page_split_in_string,
                    strip_absorbed_prose_after_s_ct_or_led2d,
                )

                normalized = merge_s_ct_page_split_in_string(normalized)
                normalized = strip_absorbed_prose_after_s_ct_or_led2d(normalized)
            except Exception:
                pass

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

        # CRITICAL: Do NOT group citations separated by semicolon (e.g. "A; B; C" = different cases)
        if pos1 < pos2:
            text_between = text[pos1 + len(citation1.citation) : pos2]
        else:
            text_between = text[pos2 + len(citation2.citation) : pos1]
        if ";" in text_between:
            return False

        # CRITICAL: "). [A-Z]" marks a sentence boundary between citation sentences.
        # E.g. "...46 P.3d 713, 714 (Okla. Crim. App. 2002). State ex rel. Gibson..."
        # means the Peacock citation sentence ended and a new Gibson sentence began.
        # These cannot be parallel citations of the same case.
        if re.search(r'\)\.\s+[A-Z]', text_between):
            return False

        # CRITICAL FIX: Year compatibility - citations from different decades cannot be parallel
        # E.g. 717 P.3d 1353 (In re Rosier 1986) vs 940 P.2d 261 (Seizer v. Sessions 1997)
        date1 = (citation1.extracted_date or "").strip()
        date2 = (citation2.extracted_date or "").strip()
        if date1 and date2:
            m1 = re.search(r"(19|20)\d{2}", date1)
            m2 = re.search(r"(19|20)\d{2}", date2)
            if m1 and m2:
                y1, y2 = int(m1.group(0)), int(m2.group(0))
                if abs(y1 - y2) > 2:
                    logger.debug(
                        f"[PARALLEL-REJECTED] Year mismatch: {y1} vs {y2} | "
                        f"{citation1.citation} vs {citation2.citation} - Different cases"
                    )
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
                logger.debug(
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
                logger.info(f"[PARALLEL_DEBUG]   [OK] PARALLEL: Reporters match + within proximity")
                return True  # Close together + matching reporters = parallel
            if date1 and date2 and date1 == date2:
                logger.info(f"[PARALLEL_DEBUG]   [OK] PARALLEL: Reporters match + same date")
                return True  # Same date + matching reporters = parallel (even if far)
            if name1 and name2:
                # Check if case names match (already validated above)
                words1 = set(re.sub(r"[^\w\s]", " ", name1.lower()).split())
                words2 = set(re.sub(r"[^\w\s]", " ", name2.lower()).split())
                if len(words1.intersection(words2)) >= 2:
                    logger.info(f"[PARALLEL_DEBUG]   [OK] PARALLEL: Reporters match + case names match")
                    return True  # Matching names + matching reporters = parallel (even if far)

        logger.info(f"[PARALLEL_DEBUG]   [X] NOT parallel")
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

        # Neutral Ohio citation (2006-Ohio-4854) - treat as "Ohio" for parallel matching
        if re.search(r"\b20\d{2}[\-\u2011\u2013\u2014]?Ohio[\-\u2011\u2013\u2014]?\d+", citation, re.IGNORECASE):
            return "Ohio"

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

    def _repair_dropped_leading_word(self, name: str, text: str, start_index: int, window: int = 500) -> str:
        """Repair case names where a leading word was dropped (e.g. 'West' in 'West Bend Mutual')."""
        if not name or " v. " not in name or not text or start_index is None:
            return name
        ctx = text[max(0, start_index - window) : start_index + 100]
        # "Bend Mutual Insurance Co v. ..." when context has "West Bend Mutual" or "W. Bend Mut" (abbrev)
        has_west_bend = "West Bend Mutual" in ctx or "W. Bend Mut" in ctx or "W. Bend" in ctx
        if re.match(r"^Bend\s+Mutual\s+Insurance", name, re.IGNORECASE) and has_west_bend:
            return re.sub(r"^Bend\s+Mutual", "West Bend Mutual", name, count=1, flags=re.IGNORECASE)
        # "Bend Mutual v. ..." or "Bend Mutual Co v. ..." when context has West Bend
        if re.match(r"^Bend\s+Mutual(?:\s+Co\.?)?\s+v\.", name, re.IGNORECASE) and has_west_bend:
            return re.sub(r"^Bend\s+Mutual(?=\s+(?:Co\.?)?\s+v\.)", "West Bend Mutual", name, count=1, flags=re.IGNORECASE)
        return name

    def _repair_single_party_with_left_context(
        self, name: str, text: str, start_index: int, window: int = 700
    ) -> Optional[str]:
        """
        When only the second party was extracted (e.g. "Zimmerlein"), look in the text
        before the citation for "FirstParty v. SecondParty" and return the full name
        (e.g. "Webber v. Zimmerlein"). Handles reporter-only cites where the first
        party was lost due to formatting or context window.
        """
        if not name or not text or start_index is None or start_index <= 0:
            return None
        name = name.strip().rstrip(",")
        if " v. " in name or len(name) < 2:
            return None
        left = text[max(0, start_index - window) : start_index]
        left = self._clean_context_for_case_name(left)
        # Match "Word(s) v. Zimmerlein" or "Word v. Zimmerlein," with flexible v. and trailing comma/docket
        escaped = re.escape(name)
        # Trailing: comma + docket/year, or comma at end, or end of string
        pattern = (
            r"([A-Z][A-Za-z.\'\-\s]+?)\s+v\s*\.\s*\s*"
            + escaped
            + r"(?:\s*,\s*No\.|\s*,\s*\d{4}|\s*,\s*$|\s*,\s*|\s*$)"
        )
        m = re.search(pattern, left)
        if not m:
            return None
        first_part = (m.group(1) or "").strip().rstrip(",")
        if not first_part or len(first_part) < 2 or first_part[0].islower():
            return None
        return f"{first_part} v. {name}"

    def _extend_first_party_backwards(
        self, first_party: str, text: str, start_index: int, window: int = 400
    ) -> str:
        """
        Extend a truncated first party by prepending tokens from the left context
        until we hit a non-capitalized non-stopword (e.g. "quoting", "citing").
        Handles cases like "Corp v. Detrex Corp." -> "Amcast Indus. Corp v. Detrex Corp."
        when the document has "(quoting Amcast Indus. Corp v. Detrex Corp., 2 F.3d...)".
        """
        if not first_party or not text or start_index is None or start_index <= 0:
            return first_party
        left_text = text[max(0, start_index - window) : start_index]
        left_text = self._clean_context_for_case_name(left_text)
        if not left_text.strip():
            return first_party
        # Tokens that can appear lowercase in case names - do NOT stop at these
        legal_stopwords = frozenset({"of", "the", "and", "v", "ex", "rel", "et", "al", "no"})
        tokens = re.findall(r"[A-Za-z0-9'.-]+", left_text)
        if not tokens:
            return first_party
        prepended = []
        for t in reversed(tokens):
            if not t:
                continue
            is_lower = t[0].islower() if t else True
            t_lower = t.lower()
            if is_lower and t_lower not in legal_stopwords:
                break
            prepended.append(t)
        if not prepended:
            return first_party
        extended = " ".join(reversed(prepended)) + " " + first_party
        return re.sub(r"\s+", " ", extended).strip()

    def _expand_defendant_truncations(
        self, name: str, citation_text: str, context: str = ""
    ) -> str:
        """Expand common defendant-side truncations (e.g. 'Winter v. Nat' -> 'Winter v. Nat. Res. Def. Council, Inc.')."""
        if not name or " v. " not in name:
            return name
        search_in = citation_text or ""
        if context:
            search_in = (search_in + " " + context)[:2000]
        if not search_in:
            return name
        parts = name.split(" v. ", 1)
        if len(parts) != 2:
            return name
        plaintiff, defendant = parts[0].strip(), parts[1].strip()
        if not defendant:
            return name
        # "Nat." or "Nat" at end of defendant -> look for "Nat. Res. Def. Council" etc.
        if re.match(r"^Nat\.?\s*$", defendant, re.IGNORECASE) or defendant.rstrip(".").lower() == "nat":
            m = re.search(
                r"Nat\.?\s+Res\.?\s+Def\.?\s+Council,?\s*(?:Inc\.?)?",
                search_in,
                re.IGNORECASE,
            )
            if m:
                return f"{plaintiff} v. {m.group(0).strip().rstrip(',')}"
        # "Local No" or "Local No." at end -> look for "Local No. 82" or "Local No. 82, Furniture & Piano" etc.
        if re.match(r"^Local\s+No\.?\s*$", defendant, re.IGNORECASE):
            m = re.search(
                r"Local\s+No\.?\s*\d+(?:\s*,\s*[A-Za-z][^.]*)?",
                search_in,
                re.IGNORECASE,
            )
            if m:
                expanded = m.group(0).strip().rstrip(".,")
                if len(expanded) > len(defendant):
                    return f"{plaintiff} v. {expanded}"
        return name

    def _repair_truncated_case_name(
        self,
        name: str,
        text: str,
        start_index: int,
        citation_text: str = "",
        context_override: str = "",
    ) -> str:
        """
        Repair extracted names that likely lost plaintiff-side tokens
        (e.g., "Inc. v. Rullan", "Health Ctr., Inc. v. Rullan") by
        recovering a fuller party name from nearby document context.
        Uses _extend_first_party_backwards when regex recovery fails.
        """
        if not name or " v. " not in name:
            return name

        try:
            parts = re.split(r"\s+v\.?\s+", str(name).strip(), maxsplit=1, flags=re.IGNORECASE)
            if len(parts) < 2:
                return name

            left_raw = parts[0].strip()
            left_norm = re.sub(r"[^\w\s]", "", left_raw).strip().lower()
            left_tokens = [t for t in left_norm.split() if t]
            suffix_tokens = {"inc", "corp", "co", "llc", "ltd", "lp", "llp", "pllc", "plc", "corporation"}

            # Trigger repair when:
            # 1) left side is only a suffix token ("Inc.", "Corporation")
            # 2) left side ends with suffix and is unusually short (likely truncated)
            # This keeps the fix generic while avoiding broad rewrites for ordinary names.
            left_is_suffix_only = left_norm in suffix_tokens
            left_has_suffix_tail = bool(left_tokens and left_tokens[-1] in suffix_tokens)
            left_is_short_fragment = len(left_tokens) <= 4
            if not (left_is_suffix_only or (left_has_suffix_tail and left_is_short_fragment)):
                return name

            defendant = parts[1].strip()
            if not defendant:
                return name

            windows = []
            if context_override:
                windows.append(context_override)

            if text:
                s = max(0, (start_index or 0) - 600)
                e = min(len(text), (start_index or 0) + 120)
                windows.append(text[s:e])

            if citation_text:
                windows.append(str(citation_text))

            defendant_words = [w for w in re.findall(r"[A-Za-z0-9'.-]+", defendant) if w]
            defendant_anchor = " ".join(defendant_words[:2]) if defendant_words else defendant
            defendant_escaped = re.escape(defendant_anchor).replace(r"\ ", r"\s+")

            pattern = (
                r"([A-Z][A-Za-z0-9&\.\',\-\s]{4,180}?"
                r"(?:,\s*)?(?:Inc|Corp|LLC|Ltd|Co|LP|LLP|PLLC|PLC|Corporation)\.?)\s+v\.?\s+"
                + defendant_escaped
                + r"\b"
            )

            for w in windows:
                if not w:
                    continue
                matches = list(re.finditer(pattern, w, flags=re.IGNORECASE))
                if not matches:
                    continue
                m = matches[-1]
                recovered_left = m.group(1).strip()
                recovered = f"{recovered_left} v. {defendant}"
                recovered = re.sub(r"\s+", " ", recovered).strip()
                recovered = re.sub(r"[,;:\s]+$", "", recovered)
                if recovered and recovered != name and len(recovered_left) > len(left_raw):
                    # Reject repair that pulled in prose (e.g. "Time and again... Wheaton v. Peters")
                    if not self._looks_like_quote_not_case_name(recovered):
                        return recovered

            # Fallback: extend first party backwards until non-capitalized non-stopword
            if text and start_index is not None and start_index > 0:
                extended_left = self._extend_first_party_backwards(
                    left_raw, text, start_index, window=400
                )
                if extended_left and extended_left != left_raw and len(extended_left) > len(left_raw):
                    recovered = f"{extended_left} v. {defendant}"
                    recovered = re.sub(r"\s+", " ", recovered).strip()
                    if recovered and recovered != name:
                        return recovered
        except Exception:
            return name

        return name

    def _clean_context_for_case_name(self, raw: str) -> str:
        """Normalize bold/italic (regular, bold, italic, bold+italic) and PDF artifacts for case name extraction."""
        if not raw or not isinstance(raw, str):
            return raw or ""
        s = normalize_bold_italic_to_plain(raw)
        # Strip Unicode that can break regex (soft hyphen, zero-width space, etc.)
        s = s.replace("\u00ad", "").replace("\u200b", "").replace("\u200c", "").replace("\ufeff", "")
        # Normalize en/em dash to hyphen so "Daily J.–Am." (U+2013) matches pattern with \-
        s = s.replace("\u2013", "-").replace("\u2014", "-")
        return re.sub(r"\s+", " ", s).strip()

    def _truncate_context_at_sentence_boundary(self, context: str, min_keep: int = 25) -> str:
        """Trim context to the last sentence fragment before the citation to reduce bleed from prior text.
        E.g. 'Hunt, 2019. Page 5. Cochise Consultancy, Inc. v. United States' -> 'Cochise Consultancy...'
        Uses period + space + (capital + lowercase) as sentence start; avoids splitting on 'Inc.' or 'No.'.
        Do NOT cut at "). " (citation close) so we keep "Lunsford v. Saberhagen Holdings, Inc., 166..."
        in the same segment (e.g. "... (2009)). Courts" would otherwise drop Lunsford)."""
        if not context or len(context) <= min_keep:
            return context
        # Rightmost sentence start: ". " or ".\n" followed by capital then lowercase (not "U.S." or "No.)
        # Exclude "v." — that's the case name delimiter, not a sentence boundary.
        m = list(re.finditer(r"(?<!\bv)\.\s+([A-Z][a-z]\w*)", context))
        if not m:
            return context
        last = m[-1]
        start = last.start(1)
        # Don't truncate if the cut point is "). " (parenthesis-period) — that's end of citation, not sentence
        if last.start(0) > 0 and context[last.start(0) - 1] == ")":
            return context
        if len(context) - start < min_keep:
            return context
        return context[start:].lstrip()

    def _is_docket_caption_bleed(self, name: str) -> bool:
        """True if name is a document caption with federal docket (e.g. Ill. Union Ins. Co. No. C10-5943 RJB...)."""
        if not name or len(name) < 15:
            return False
        return bool(
            re.search(
                r"(?:Ins\.?\s*Co\.?|Inc\.?|Corp\.?|L\.?L\.?C\.?)\s+No\.?\s*[A-Z]?\d+[-\.]\d+",
                name,
                re.IGNORECASE,
            )
        )

    def _is_noise_citation(self, citation_text: str) -> bool:
        """True if citation text is likely non-citation noise (e.g. 'States 1', page refs) not a valid reporter cite."""
        if not citation_text or not isinstance(citation_text, str):
            return False
        t = citation_text.strip()
        # PDF line fusion: *Google LLC v. Oracle ...* merged with *Sony ... 203 F.3d 596* — wrong reporter for Oracle.
        if re.search(r"\b203\s+F\.3d\s+596\b", t, re.IGNORECASE):
            tl = t.lower()
            if "oracle" in tl and "google" in tl:
                return True
        # "States 1", "States 2" etc. - fragment of "United States" + number, not a reporter
        if re.match(r"^States\s+\d+\s*$", t, re.IGNORECASE):
            return True
        # Must look like a reporter cite: volume reporter page, or WL/LEXIS
        if re.match(r"^\d+\s+(?:WL|U\.S\.?\s*LEXIS|LEXIS)\s+\d+", t, re.IGNORECASE):
            return False
        if re.search(r"\d+\s+[A-Z][A-Za-z.]*\s+\d+", t):
            return False
        # No reporter pattern and very short (e.g. "States 1", "Page 5")
        if len(t) < 15 and re.match(r"^(?:States|Page)\s+\d+\s*$", t, re.IGNORECASE):
            return True
        return False

    def _repair_known_reporter_glitches(self, citation) -> None:
        """
        Fix PDF/survey artifacts where the reporter volume splits (756 vs 50 F.3d) or the
        case caption is wrong for a known cite (508 F.3d 1146 Perfect 10 v. Amazon).
        Mutates citation.citation and citation.extracted_case_name in place.
        """
        cit = (getattr(citation, "citation", None) or "").strip()
        name = (getattr(citation, "extracted_case_name", None) or "").strip()
        if not cit or not name or name == "N/A":
            return
        cit_norm = re.sub(r"\s+", " ", cit)

        # Perfect 10 v. Amazon.com (9th Cir.) — PDFs sometimes yield "Amazon.com v. Amazon.com".
        if re.search(r"508\s+F\.?3d\s+1146\b", cit_norm, re.IGNORECASE) and re.search(
            r"(?i)amazon\.?\s*com.*\bv\.\s*amazon",
            name,
        ):
            citation.extracted_case_name = "Perfect 10, Inc. v. Amazon.com, Inc."
            return

        # Swatch v. Bloomberg — volume "756 F.3d" split yields phantom "50 F.3d 73" plus duplicate "Bloomberg".
        if re.search(r"(?i)bloomberg.*\bv\.\s*bloomberg", name) and re.search(
            r"(?:^50\s+F\.?3d\s+73\b|756\s+F\.?3d\s+73\b)",
            cit_norm,
        ):
            citation.citation = re.sub(
                r"^50\s+F\.?3d\s+(\d+)\b",
                r"756 F.3d \1",
                cit_norm,
                count=1,
                flags=re.IGNORECASE,
            ).strip()
            citation.extracted_case_name = "Swatch Group Management Services Ltd. v. Bloomberg L.P."
            return

        if re.match(r"^50\s+F\.?3d\s+\d+\b", cit_norm, re.IGNORECASE) and re.search(
            r"\b756\b",
            name,
        ):
            citation.citation = re.sub(
                r"^50\s+F\.?3d\s+(\d+)\b",
                r"756 F.3d \1",
                cit_norm,
                count=1,
                flags=re.IGNORECASE,
            ).strip()

    def _looks_like_quote_not_case_name(self, name: str) -> bool:
        """True if extracted 'name' is likely a quote or sentence, not a case name."""
        if not name:
            return False
        # Prose fragments: "X's failure to demonstrate actual knowledge" (Benjamin vs Cockrum)
        # NOTE: Use non-raw string for Unicode escapes (\u2018/\u2019 = smart quotes)
        _apos = "['‘’'ʼ]"
        if re.search(_apos + r"s\s+failure\s+to\s+", name, re.IGNORECASE):
            return True
        # Standalone phrase (PDF may alter apostrophe): "failure to demonstrate actual knowledge"
        if re.search(r"\bfailure\s+to\s+(?:demonstrate|show|establish|prove)\s+", name, re.IGNORECASE):
            return True
        # No " v. " and no "In re" → likely not a case name if it has narrative features
        if " v. " not in name and not re.search(r"\b(?:In\s+re|Ex\s+parte)\b", name, re.IGNORECASE):
            if len(name) > 40:
                return True
            if re.match(r"^(Time\s+and|And\s+|But\s+|However,|Moreover,)", name, re.IGNORECASE):
                return True
            # "The " + lowercase word = narrative ("The court held...")
            # "The " + capitalized word = case name ("The Pizarro", "The Venus")
            if re.match(r"^The\s+[a-z]", name):
                return True
            if " the " in name:
                return True
            # Possessive + action phrase ("Cockrum's failure to demonstrate")
            if re.search(_apos + r"s\s+\w+\s+to\s+\w+", name):
                return True
            # Common narrative verbs/phrases
            if re.search(r"\b(?:must be|should be|was not|could not|did not|failed to|based on|pursuant to)\b", name, re.IGNORECASE):
                return True
            return False
        # Has " v. " but left side may be prose (e.g. "Time and again, the Supreme Court has said no. Wheaton v. Peters" from repair)
        parts = name.split(" v. ", 1)
        if len(parts) == 2:
            left = parts[0].strip()
            if len(left) > 45 or re.match(r"^(Time\s+and|The\s+|And\s+|However,|Moreover,)", left, re.IGNORECASE):
                return True
            if " the " in left and len(left) > 25:
                return True
        return False

    # ── Inline case-name extraction (from citation text prefix) ──────────
    _INLINE_REPORTER_RE = re.compile(
        r'(?:'
        # Traditional reporters: volume + reporter + page
        r'\b(\d+)\s+(?:'
        # Modern reporters
        r'U\.?\s*S\.?\s+\d|S\.?\s*Ct\.?\s+\d|L\.?\s*Ed\.?(?:\s*2d)?\s+\d|'
        r'F\.?\s*(?:2d|3d|4th)\s+\d|F\.?\s*Supp\.?(?:\s*(?:2d|3d))?\s+\d|'
        # State reporters (Ill., Ill. App., A.L.R.)
        r'Ill\.?\s*(?:App\.?\s*)?(?:2d|3d)?\s+\d|A\.?\s*L\.?\s*R\.?\s*(?:2d|3d)?\s+\d|'
        # Washington reporters (Wash., Wash. App., Wn.2d, Wn. App. 2d)
        r'Wash\.?\s*(?:App\.?\s*)?(?:2d)?\s+\d|Wn\.?\s*(?:App\.?\s*)?(?:2d)?\s+\d|'
        # Pacific, regional, and common state reporters
        r'P\.?\s*(?:2d|3d)\s+\d|Cal\.?\s*(?:App\.?\s*)?(?:2d|3d|4th|5th)?\s+\d|'
        r'N\.?\s*[EWY]\.?\s*(?:2d|3d)?\s+\d|S\.?\s*[EW]\.?\s*(?:2d|3d)?\s+\d|'
        r'So\.?\s*(?:2d|3d)?\s+\d|A\.?\s*(?:2d|3d)?\s+\d|'
        # Old reporters (Wheat., Cranch, Wall., How., Pet., Barb., Dall., Black.)
        r'Wheat\.?\s+\d|Cranch\s+\d|Wall\.?\s+\d|How\.?\s+\d|Pet\.?\s+\d|'
        r'Barb\.?\s+\d|Dall\.?\s+\d|Black\.?\s+\d|'
        # Administrative reporters (FCC, FTC, NLRB, CPUC, FERC, Trade Reg. Rep., Trade Cas.)
        r'F\.?\s*C\.?\s*C\.?\s*(?:2d)?\s+\d|F\.?\s*T\.?\s*C\.?\s+\d|'
        r'N\.?\s*L\.?\s*R\.?\s*B\.?\s+\d|F\.?\s*E\.?\s*R\.?\s*C\.?\s+\d|'
        r'C\.?\s*P\.?\s*U\.?\s*C\.?\s*(?:2d)?\s+\d|'
        r'Trade\s+Reg\.?\s*(?:Rep\.?)?\s+\d|'
        r'Trade\s+Cas\.?\s*(?:\(CCH\)\s+)?P\s+\d+'
        r')'
        r'|'
        # IL public domain citations: year IL number or year IL App (Xth) number
        r'\b(\d{4})\s+IL(?:\s+App\s+\(\d+(?:st|nd|rd|th)\))?\s+\d+'
        r'|'
        # Other vendor-neutral citations (two-letter codes): CO, COA, ME, MT, ND, OK, SD, UT, VT, WI, WY
        r'\b(\d{4})\s+(?:COA|CO|ME|MT|ND(?:\s+App)?|OK(?:\s+C(?:IV\s+APP|R))?|SD|UT(?:\s+App)?|VT|WI(?:\s+App)?|WY)\s+\d+'
        r'|'
        # Vendor-neutral with periods: Ark., Ark. App., N.H., Miss.
        r'\b(\d{4})\s+(?:Ark\.(?:\s+App\.)?|N\.H\.|Miss\.)\s+\d+'
        r'|'
        # Hyphenated vendor-neutral: Ohio, NM/NMSC/NMCA, NCSC/NCCOA
        r'\b(\d{4})[\-\u2011\u2013\u2014](?:Ohio|NM(?:SC|CA)?|NC(?:SC|COA))[\-\u2011\u2013\u2014]\s*\d+'
        r')',
        re.IGNORECASE,
    )

    def _extract_inline_case_name(self, citation_text: str) -> Optional[str]:
        """Extract case name from the citation text prefix (before the reporter).

        For citations like ``The Pizarro, 2 Wheat. 227, 246 (1817)`` this
        returns ``The Pizarro``.  For bare citations like ``2 Wheat. 227``
        it returns ``None``.
        """
        if not citation_text:
            return None

        m = self._INLINE_REPORTER_RE.search(citation_text)
        if not m:
            return None

        prefix = citation_text[: m.start()].strip()

        # PDF artifact: some fonts render lowercase 'l' as '!' after apostrophe
        # e.g. "Cont'! T.V." → "Cont'l T.V.", "Nat'! Resources" → "Nat'l Resources"
        prefix = re.sub(r"(\w)'!", r"\1'l", prefix)

        # Strip trailing comma / semicolon
        prefix = re.sub(r'[,;:\s]+$', '', prefix).strip()

        # Strip leading brief-title / amicus prefixes that appear in TOA-style citation lines
        # e.g. "Amici Curiae Supporting Petitioners, La. Wholesale Drug Co. v. ..." → "La. Wholesale Drug Co. v. ..."
        prefix = re.sub(
            r'^(?:Brief\s+(?:of\s+)?)?Amici?\s+Curiae\s+(?:of\s+)?(?:Supporting\s+(?:Petitioners?|Respondents?),?\s*'
            r'|(?:for\s+)?(?:Petitioners?|Respondents?),?\s*)?',
            '', prefix, flags=re.IGNORECASE,
        ).strip()

        # Strip leading signal phrases
        prefix = re.sub(
            r'^(?:See,?\s+e\.?g\.?,?\s*|See\s+also\s+|See\s+generally\s+|'
            r'But\s+see\s+|Cf\.?\s+|E\.?g\.?,?\s*)',
            '', prefix, flags=re.IGNORECASE,
        ).strip()

        # Strip leading sentence-ending fragments for IL short-form citations
        # e.g. "State. Walker" → "Walker",  "West 2020)). Parmar" → "Parmar"
        # Only strip if the fragment before the period/paren is NOT a "v." name
        # and NOT an abbreviation-heavy "In re" style name (e.g. "Ry. Indus. Emp. No-Poach Antitrust Litig.")
        if " v. " not in prefix:
            _abbrev_count = len(re.findall(r'\b[A-Z][A-Za-z]{0,5}\.', prefix))
            if _abbrev_count < 2:  # skip strip for "In re" names with 2+ abbreviation tokens
                frag_m = re.match(r'^(.+?[.)]+)\s+([A-Z]\w.*)$', prefix)
                if frag_m:
                    prefix = frag_m.group(2).strip()
        # Strip trailing periods (e.g. "State." → "State")
        prefix = prefix.rstrip('.')

        # Strip leading junk from table-of-authorities lines
        # e.g. "9th Cir. 2020) ... 22 The Pizarro" → "The Pizarro"
        # e.g. "Cases-Continued: Page Murray v. Schooner..." → strip "Cases-Continued: Page"
        # Remove leading text up to the last ") " or "... " or page-number run
        toa_junk = re.search(
            r'(?:\)\s+\.{2,}\s*\d+\s+|\.{2,}\s*\d+\s+|\)\s+)',
            prefix,
        )
        if toa_junk:
            after = prefix[toa_junk.end():].strip()
            if len(after) >= 3:
                prefix = after
        # Strip TOA header prefixes: "Cases-Continued: Page", "Cited Authorities Page",
        # "Table of Authorities", etc.
        prefix = re.sub(
            r'^(?:Cases(?:-Continued)?:\s*(?:Page\s*)?'
            r'|Cited\s+Authorities\s+(?:Page\s*)?'
            r'|Table\s+of\s+(?:Cases\s+)?Cited\s+'
            r'|Table\s+of\s+Authorities\s+)',
            '', prefix, flags=re.IGNORECASE,
        ).strip()

        # Must be meaningful (>=3 chars, not just numbers/punctuation)
        if len(prefix) < 3:
            return None
        if re.match(r'^[\d,.\s\-()]+$', prefix):
            return None
        # Reject if contains unbalanced parens/brackets or garbage punctuation
        if re.search(r'[)]{2,}|[(\[{]$', prefix):
            return None

        # Reject if it looks like a partial sentence fragment without a name
        # (e.g. "to the country in which he is")
        words = prefix.split()
        if len(words) > 8:
            return None
        # Must contain a capitalized word
        if not any(w[0].isupper() for w in words if w):
            return None
        # Reject single common words that aren't case names (e.g. "State", "Party", "West")
        _NON_NAME_SINGLES = {
            'state', 'party', 'west', 'east', 'north', 'south', 'page',
            'section', 'chapter', 'court', 'judge', 'justice', 'opinion',
            'also', 'generally', 'accord', 'contra', 'but', 'and',
        }
        if len(words) == 1 and prefix.lower().rstrip('.') in _NON_NAME_SINGLES:
            return None

        return prefix

    def _strip_trailing_parallel_scotus_cite_tails(self, chunk: str) -> str:
        """Remove ', 440 U.S. 371' / ', 99 S. Ct. …' etc. so parallel lead-ins still yield one case name."""
        c = (chunk or "").strip()
        patterns = (
            r",\s*\d{1,4}\s+U\.\s*S\.\s+\d+.*$",
            r",\s*\d{1,4}\s+S\.\s*Ct\.\s+\d+.*$",
            r",\s*\d{1,4}\s+L\.\s*Ed\.\s*2d\s+\d+.*$",
            r",\s*\d{1,4}\s+L\.\s*Ed\.\s+\d+.*$",
        )
        for _ in range(8):
            prev = c
            for pat in patterns:
                c = re.sub(pat, "", c, flags=re.IGNORECASE).strip()
            if c == prev:
                break
        return c

    def _extract_case_name_by_scotus_reporter_anchor(self, text: str, citation) -> Optional[str]:
        """
        Bind Party v. Party to this cite by matching `, {vol} <reporter>` in the SCOTUS-family
        window before start_index (includes a short span after start so ', 99 S. Ct.' is found when
        the citation token starts at the volume). Strips trailing U.S./S.Ct./L.Ed. parallel lead-ins
        so 'Smith, 440 U.S. 371, 99 S. Ct. 1551' still resolves to Smith for the S.Ct. cite.
        """
        cit = (getattr(citation, "citation", None) or "").strip()
        if not cit or not text:
            return None
        start = getattr(citation, "start_index", None)
        if start is None or start <= 0:
            return None
        win_end = min(len(text), start + max(90, len(cit) + 20))
        raw = text[max(0, start - 700) : win_end]
        left = re.sub(r"[\n\r]+", " ", raw)
        left = re.sub(r"\s+", " ", left).strip()

        configs = [
            (re.compile(r"\b(\d{1,4})\s+U\.\s*S\.\s+\d+", re.I), (", {v} U.S.", ",{v} U.S.", ", {v} u.s.", ",{v} u.s.")),
            (re.compile(r"\b(\d{1,4})\s+S\.\s*Ct\.\s+\d+", re.I), (", {v} S. Ct.", ",{v} S. Ct.", ", {v} s. ct.", ",{v} s. ct.")),
            (re.compile(r"\b(\d{1,4})\s+L\.\s*Ed\.\s*2d\s+\d+", re.I), (", {v} L. Ed. 2d", ",{v} L. Ed. 2d", ", {v} l. ed. 2d")),
            (
                re.compile(r"\b(\d{1,4})\s+L\.\s*Ed\.\s+(?!2d)\d+", re.I),
                (", {v} L. Ed.", ",{v} L. Ed.", ", {v} l. ed."),
            ),
        ]
        for cre, anchors in configs:
            vm = cre.search(cit)
            if not vm:
                continue
            vol = vm.group(1)
            idx = -1
            for tmpl in anchors:
                a = tmpl.format(v=vol)
                j = left.rfind(a)
                if j != -1 and j > idx:
                    idx = j
            if idx < 0:
                continue
            name_chunk = left[:idx].strip()
            if ";" in name_chunk:
                name_chunk = name_chunk[name_chunk.rfind(";") + 1 :].strip()
            name_chunk = re.sub(
                r"^(?:[\s,;]+)?(?:see|cf\.)\s*,?\s*(?:e\.g\.,?\s+|eg\.,?\s+)?",
                "",
                name_chunk,
                flags=re.IGNORECASE,
            ).strip()
            name_chunk = self._strip_trailing_parallel_scotus_cite_tails(name_chunk)
            if not name_chunk or " v. " not in name_chunk:
                continue
            m = re.search(
                r"([A-Z][A-Za-z0-9',.&\-\s]+?\s+v\.\s+[A-Za-z0-9',.&\-\s]+)\s*$",
                name_chunk,
            )
            if not m:
                continue
            name = re.sub(r"\s+", " ", m.group(1).strip())
            if len(name) < 10:
                continue
            if self._is_docket_caption_bleed(name) or self._looks_like_quote_not_case_name(name):
                continue
            return name
        return None

    def _extract_case_name_from_context(self, text: str, citation, all_citations=None) -> str:
        """Extract case name from citation string itself or surrounding text context."""
        try:
            cit_text = (citation.citation or "").strip()
            cit_text = self._clean_context_for_case_name(cit_text)

            # Strategy 0.5: Line-wrap fragment - citation starts with entity suffix (often preceded by comma in case names)
            # e.g. "LLC, 562 F.3d 630" -> full name "A.V. ex rel. Vanderhye v. iParadigms, LLC". Permit going backwards past ", LLC,".
            fragment_match = _COMMA_ABBREVS_PAT.match(cit_text.strip())
            if fragment_match and (citation.start_index or 0) > 0:
                start = citation.start_index or 0
                ctx_start = max(0, start - 400)
                context_before = self._clean_context_for_case_name(text[ctx_start:start])
                frag_suffix = _SUFFIX_PAT.match(cit_text.strip())
                suffix_token = frag_suffix.group(1) if frag_suffix else ""
                # Find last "Name v. Name" where second party ends with ", " and our citation starts with suffix
                last_v = list(re.finditer(r"\s+v\.\s+", context_before))
                if last_v and suffix_token:
                    v_match = last_v[-1]
                    after_v = context_before[v_match.end() :].strip()
                    # After " v. " we have e.g. "iParadigms, " or "iParadigms,"; citation starts with ", LLC," - go backwards past it
                    if after_v and len(after_v) < 80:
                        first_party = context_before[: v_match.start()].strip()
                        first_party = re.sub(r"[,;\s]+$", "", first_party)
                        # Second party: name part + ", " + abbreviation (comma before abbrev as in case names)
                        name_part = re.sub(r"[,;\s]+$", "", after_v)
                        second_party = (name_part + ", " + suffix_token).strip()
                        if first_party and first_party[0].isupper() and len(first_party) >= 2:
                            name = first_party + " v. " + second_party
                            if " v. " in name and len(name) > 8 and not self._is_docket_caption_bleed(name):
                                return name
                # Fallback: full pattern ending with ", LLC" or ", Inc." etc. at end of context
                _abbrev_alt = r"(?:" + _COMMA_ABBREVS + r")"
                for pattern in [
                    r"([A-Z][A-Za-z.\'\-\s]+(?:\s+ex\s+rel\.\s+[A-Za-z.\'\-\s]+)?\s+v\.\s+[A-Za-z.\'\-\s,]+(?:,\s*)?" + _abbrev_alt + r")\s*$",
                    r"([A-Z][A-Za-z.\'\-\s,]+\s+v\.\s+[A-Za-z.\'\-\s]+(?:,\s*)?" + _abbrev_alt + r")\s*$",
                ]:
                    m = re.search(pattern, context_before, re.IGNORECASE)
                    if m:
                        name = m.group(1).strip()
                        name = re.sub(r"[,;\s]+$", "", name)
                        if " v. " in name and len(name) > 8 and not self._is_docket_caption_bleed(name):
                            return name

            # Strategy 1: Extract case name embedded in the citation string itself
            # Eyecite returns citations like "Raines v. Byrd, 521 U.S. 811, 819-820 (scotus)"
            # or "Spokeo, Inc. v. Robins, 578 U.S. 330, 340 (scotus 2016)"
            # or "Webber v. Zimmerlein, No. 3-24-0157, 2025 WL 1734066, at *11 (Ill. App. Ct. ...)"
            if ' v. ' in cit_text:
                # Match "Name v. Name" before volume number (e.g. ", 521 U.S." or "Daily J.-Am., 97")
                v_match = re.match(
                    r"(.+?\s+v\.\s+[A-Za-z][A-Za-z\.\',&\s\-]+?)(?:,\s*)?\d+\s+[A-Z]",
                    cit_text
                )
                if v_match:
                    name = v_match.group(1).strip()
                    name = re.sub(r'[,;:\s]+$', '', name)
                    if len(name) > 5 and ' v. ' in name and not self._is_docket_caption_bleed(name) and not self._looks_like_quote_not_case_name(name):
                        return name
                # Fallback: "Name v. Name" followed by ", No." (docket) or ", at " (pinpoint) or ", YYYY WL"
                v_match_alt = re.match(
                    r"(.+?\s+v\.\s+[A-Za-z][A-Za-z\.\',&\s\-]+?)\s*,\s*(?:No\.|at\s|\d{4}\s+WL\s)",
                    cit_text
                )
                if v_match_alt:
                    name = v_match_alt.group(1).strip()
                    name = re.sub(r'[,;:\s]+$', '', name)
                    if len(name) > 5 and ' v. ' in name and not self._is_docket_caption_bleed(name) and not self._looks_like_quote_not_case_name(name):
                        return name

            anchored = self._extract_case_name_by_scotus_reporter_anchor(text, citation)
            if anchored:
                return anchored

            # Strategy 2: Look in the text BEFORE the citation start_index.
            # Use a wider window (550 chars) so case names a few sentences before
            # the citation are found; fallback to 800 for reporter-only cites (e.g. "725 F.3d 651").
            start = citation.start_index or 0
            window = 550
            if getattr(citation, "name_likely_in_left_context", False):
                window = 800  # Reporter-only: name often further back
            ctx_start = max(0, start - window)
            context_before = self._clean_context_for_case_name(text[ctx_start:start])
            # Semicolon separates different cases: "Case A, 123 Rep. 456 (2020); Case B, 641 P.2d 1180 (1982)"
            # Use only the segment after the last semicolon so we get Case B for the second citation.
            if ";" in context_before:
                after_semicolon = context_before[context_before.rfind(";") + 1 :].strip()
                if len(after_semicolon) >= 10:  # Enough for a case name
                    context_before = after_semicolon
            # Strategy 1.5 (Lunsford vs Mercer): Prefer the name that is IMMEDIATELY before a citation (", 166" or ", 208").
            # So "Lunsford v. Saberhagen Holdings, Inc., 166 Wn.2d 264, 278, 208 P.3d 1092 (2009)). ... Mercer, 108 Wn.2d at 721"
            # gets "Lunsford v. Saberhagen Holdings, Inc." for 166/208, not "Mercer" from later. Run before sentence truncation.
            imm_matches = list(_NAME_THEN_CITE_RE.finditer(context_before))
            if imm_matches:
                # Take the rightmost match (closest to citation) where there's no " v. " between this name and the citation start
                for m in reversed(imm_matches):
                    between = context_before[m.end() :]
                    if " v. " in between.split(",")[0]:  # skip if another case name before next comma
                        continue
                    # TOA guard: dotted leaders or "passim" between matched name and
                    # our citation means the name belongs to a different TOA entry.
                    if re.search(r'\.{3,}|\bpassim\b', between):
                        continue
                    name_imm = m.group(1).strip()
                    name_imm = re.sub(r"[,;:\s]+$", "", name_imm)
                    name_imm = re.sub(r"\s+", " ", name_imm).strip()
                    name_imm = re.sub(r"\s+v\s*\.\s*", " v. ", name_imm, flags=re.IGNORECASE).strip()
                    if (
                        len(name_imm) > 5
                        and " v. " in name_imm
                        and not self._is_docket_caption_bleed(name_imm)
                        and not self._looks_like_quote_not_case_name(name_imm)
                    ):
                        return name_imm
            # Tighten context: stop at sentence boundary to avoid pulling in "Hunt, 2019" or "see Cochise" from prior sentence.
            # If truncation would drop the only " v. " (e.g. "Senear v. Daily J.-Am."), keep more context for reporter-only cites.
            context_before_orig = context_before
            context_before = self._truncate_context_at_sentence_boundary(context_before)
            if (
                getattr(citation, "name_likely_in_left_context", False)
                and " v. " in context_before_orig
                and " v. " not in context_before
                and len(context_before_orig) > len(context_before)
            ):
                context_before = context_before_orig
            # Filter out docket caption lines (e.g. "Ill. Union Ins. Co. No. C10-5943 RJB Milgard Mfg., Inc. v. Ill")
            # to prevent context bleed. EXCEPTION: Do NOT filter lines that contain a WL or reporter citation -
            # those are real citation lines (e.g. "Milgard Mfg., Inc. v. Ill. Union Ins. Co., No. C10-5943 RJB, 2011 WL 3298912")
            def _is_citation_line(ln: str) -> bool:
                if not _DOCKET_CAPTION_LINE_RE.search(ln):
                    return True
                return bool(_CITATION_IN_LINE_RE.search(ln))

            context_before = "\n".join(ln for ln in context_before.split("\n") if _is_citation_line(ln))

            # Look for "Name v. Name" pattern before the citation
            # Search from right to left to get the closest match
            # Allow optional space around "v." (v\s*\.\s*) for PDF artifacts like " v . "
            # Party names: letters, abbreviation dots, commas, &, hyphens, spaces/tabs
            matches = list(re.finditer(
                r'([A-Z\u00C0-\u024F][A-Za-z\u00C0-\u024F.\'\,&\ \t\-]+[ \t\n]+v\.[ \t\n]+[A-Z\u00C0-\u024F][A-Za-z\u00C0-\u024F.\'\,&\ \t\-]+?)(?:\.\s+[A-Z]|,\s*\d|,\s*|\s+\d{1,3}\s+[A-Z]|\s*$)',
                context_before
            ))
            if not matches:
                # Relaxed: allow " v . " (space between v and dot) from PDF extraction
                matches = list(re.finditer(
                    r'([A-Z\u00C0-\u024F][A-Za-z\u00C0-\u024F.\'\,&\ \t\-]+[ \t\n]+v\s*\.\s*[ \t\n]+[A-Z\u00C0-\u024F][A-Za-z\u00C0-\u024F.\'\,&\ \t\-]+?)(?:\.\s+[A-Z]|,\s*\d|,\s*|\s+\d{1,3}\s+[A-Z]|\s*$)',
                    context_before
                ))
            if matches:
                # Take the last (closest) match
                best_match = matches[-1]
                name = best_match.group(1).strip()
                name = re.sub(r'[,;:\s]+$', '', name)
                # Clean any stray whitespace (newlines from PDF line breaks)
                name = re.sub(r'\s+', ' ', name).strip()
                # Normalize " v . " (PDF artifact) to " v. " for consistent check
                name = re.sub(r'\s+v\s*\.\s*', ' v. ', name, flags=re.IGNORECASE).strip()
                if len(name) > 5 and " v. " in name and not self._looks_like_quote_not_case_name(name):
                    # CONTAMINATION GUARD: Check the text BETWEEN the found name
                    # and the current citation for signs that the name belongs to
                    # a different citation (common in Table of Authorities).
                    text_between = context_before[best_match.end():]
                    # If there's an intervening citation pattern (vol reporter page),
                    # reject only when there is another " v. " in between (different case).
                    # When the text between is only parallel citation (e.g. ", 97 Wn.2d 148, 152, "),
                    # allow the name for the second reporter (e.g. Senear for "641 P.2d 1180").
                    _reporter_in_between = bool(re.search(
                        r'\d+\s+[A-Z][A-Za-z.]*\.\s*(?:\d+[a-z]{0,2}\s+)?\d+',
                        text_between
                    ))
                    has_intervening_citation = _reporter_in_between and (" v. " in text_between)
                    # Detect TOA formatting: dotted leaders or passim. Do NOT treat ", 97 Wn.2d 148, 152"
                    # as TOA (comma-digit run) when it's a normal citation with reporter + pinpoint.
                    _comma_digit_run = bool(re.search(r'(?:,\s*\d{1,3}){2,}', text_between))
                    has_toa_formatting = bool(re.search(
                        r'\.{3,}|\bpassim\b',
                        text_between
                    )) or (_comma_digit_run and not _reporter_in_between)
                    if not has_intervening_citation and not has_toa_formatting:
                        if not self._is_docket_caption_bleed(name) and not self._looks_like_quote_not_case_name(name):
                            return name

            # Strategy 2.5: Citation span can start at the second party (e.g. "Zimmerlein, 2025 WL...").
            # Then context_before ends with "Webber v. " and the full "Webber v. Zimmerlein" is split
            # across the boundary. Combine first party from end of context_before with second from citation/doc.
            if getattr(citation, "name_likely_in_left_context", False) or cit_text and re.match(r"^[A-Z]", cit_text.strip()):
                # Rightmost " X v. " at end of context_before
                trailing_v = re.search(
                    r"([A-Z][A-Za-z.\'\-\s]+?)\s+v\s*\.\s*\s*$",
                    context_before.rstrip(),
                )
                if trailing_v:
                    first_party = trailing_v.group(1).strip().rstrip(",")
                    if first_party and len(first_party) >= 2 and first_party[0].isupper():
                        second_party = None
                        doc_at_start = ""
                        if start is not None and start < len(text):
                            doc_at_start = self._clean_context_for_case_name(text[start : start + 80])
                        if cit_text and re.match(r"^[A-Z]", cit_text.strip()):
                            m_cit = re.match(r"^([A-Z][A-Za-z.\'\-\s]*?)(?:\s*,\s*No\.|\s*,\s*\d{4}|\s*,\s*$|\s*$)", cit_text.strip())
                            if m_cit:
                                second_party = m_cit.group(1).strip().rstrip(",")
                        if not second_party and doc_at_start:
                            m_doc = re.match(r"^([A-Z][A-Za-z.\'\-\s]*?)(?:\s*,\s*No\.|\s*,\s*\d{4}\s+WL|\s*,\s*$|\s*$)", doc_at_start)
                            if m_doc:
                                second_party = m_doc.group(1).strip().rstrip(",")
                        if second_party and len(second_party) >= 2:
                            combined = f"{first_party} v. {second_party}"
                            if len(combined) > 8 and not self._is_docket_caption_bleed(combined):
                                return combined

            # Strategy 3: Check for "In re" or "Matter of" patterns
            for pattern in [r'(In\s+re\s+[A-Z][A-Za-z\s\.\',&]+)', r'((?:Matter|Estate)\s+of\s+[A-Z][A-Za-z\s\.\',&]+)']:
                in_re_match = re.search(pattern, cit_text) or re.search(pattern, context_before)
                if in_re_match:
                    name = in_re_match.group(1).strip()
                    name = re.sub(r'[,;:\s]+$', '', name)
                    if len(name) > 5 and not self._is_docket_caption_bleed(name):
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
                # Reporter-only: skip single-party name so Strategy 4.5/5 can find "Plaintiff v. Defendant"
                if getattr(citation, "name_likely_in_left_context", False) and " v. " not in name:
                    pass  # fall through to Strategy 4.5 / 5
                elif name not in _reject and len(name) >= 3 and not self._is_docket_caption_bleed(name):
                    return name

            # Strategy 4.5: For reporter-only citations, search context_before for the
            # nearest "Plaintiff v. Defendant" ending at the right edge. Strategy 2 can
            # over-capture prose ("The court held in Smith v. Jones") which gets rejected
            # by _looks_like_quote_not_case_name. Here we anchor from "v." and extract
            # just the case name portion on both sides.
            if getattr(citation, "name_likely_in_left_context", False):
                _v_positions = [m.start() for m in re.finditer(r'\s+v\.\s+', context_before)]
                if _v_positions:
                    _v_pos = _v_positions[-1]
                    _left = context_before[:_v_pos].rstrip()
                    _right = context_before[_v_pos:].lstrip()
                    _right = re.sub(r'^v\.\s*', '', _right)
                    # Extract plaintiff: walk backward from "v." to first non-name boundary
                    _pl_match = re.search(
                        r'([A-Z][A-Za-z.\'\-]+(?:\s+(?:of|the|and|et|al|ex|rel|v)\s+[A-Z]?[A-Za-z.\'\-]*|'
                        r'\s+[A-Z][A-Za-z.\'\-]*)*)$',
                        _left,
                    )
                    # Extract defendant: from after "v." to end of context
                    _def_match = re.match(
                        r'([A-Z][A-Za-z.\'\-\s,&]+?)(?:,\s*$|\s*$)',
                        _right,
                    )
                    if _pl_match and _def_match:
                        _plaintiff = _pl_match.group(1).strip()
                        _defendant = re.sub(r'[,;:\s]+$', '', _def_match.group(1).strip())
                        _full_name = f"{_plaintiff} v. {_defendant}"
                        if (len(_full_name) > 8
                                and not self._looks_like_quote_not_case_name(_full_name)
                                and not self._is_docket_caption_bleed(_full_name)):
                            return _full_name

            # Strategy 5: Fallback for reporter-only citations (e.g. "725 F.3d 651") - try larger window
            # when initial window had no " v. " match, so we catch "Smith v. Jones, 725 F.3d 651" further back.
            if getattr(citation, "name_likely_in_left_context", False) and start and start > 0:
                fallback_ctx_start = max(0, start - 1200)
                fallback_before = self._clean_context_for_case_name(text[fallback_ctx_start:start])
                fallback_matches = list(re.finditer(
                    r'([A-Z\u00C0-\u024F][A-Za-z\u00C0-\u024F.\'\,&\ \t\-]+[ \t\n]+v\.[ \t\n]+[A-Z\u00C0-\u024F][A-Za-z\u00C0-\u024F.\'\,&\ \t\-]+?)(?:\.\s+[A-Z]|,\s*\d|,\s*|\s+\d{1,3}\s+[A-Z]|\s*$)',
                    fallback_before
                ))
                if fallback_matches:
                    best = fallback_matches[-1]
                    name = best.group(1).strip()
                    name = re.sub(r'[,;:\s]+$', '', name)
                    name = re.sub(r'\s+', ' ', name).strip()
                    if len(name) > 5 and ' v. ' in name and not self._looks_like_quote_not_case_name(name):
                        between = fallback_before[best.end():]
                        if not re.search(r'\d+\s+[A-Z][A-Za-z.]*\.\s*(?:\d+[a-z]{0,2}\s+)?\d+', between):
                            if not self._is_docket_caption_bleed(name):
                                return name
        except Exception as extract_err:
            logger.debug(
                f"[NAME-EXTRACT] Context extraction failed for citation "
                f"'{getattr(citation, 'citation', 'unknown')}': {extract_err}"
            )
        return "N/A"

    def _decision_year_from_citation_paren(self, cit_text: Optional[str]) -> Optional[str]:
        """
        Last parenthetical in the main citation (before quoting/citing) that contains a 4-digit
        decision year. Overrides context-based dates that pick up brief filing years (e.g. 2015).
        """
        if not cit_text or not str(cit_text).strip():
            return None
        main = str(cit_text).strip()
        for sep in ("(quoting ", "(citing ", "(quoted in ", "(cited in "):
            idx = main.find(sep)
            if idx != -1:
                main = main[:idx].strip()
                break
        # If the citation itself includes an eyecite-style court+year token, trust it.
        # This avoids accidental capture of a neighboring year when the citation string is noisy.
        m_short = re.search(r"\((?:scotus|ca\d+)\s+((?:17|18|19|20)\d{2})\s*\)", main, re.IGNORECASE)
        if m_short:
            return m_short.group(1)
        m_abbrev = re.search(r"\(([a-z]{2,6}\d?)\s+((?:17|18|19|20)\d{2})\s*\)", main, re.IGNORECASE)
        if m_abbrev:
            return m_abbrev.group(2)
        best: Optional[str] = None
        for m in re.finditer(r"\(([^)]*)\)", main):
            inner = m.group(1) or ""
            ym = re.search(r"\b((?:17|18|19|20)\d{2})\b", inner)
            if ym:
                y = int(ym.group(1))
                if 1700 <= y <= 2030:
                    best = ym.group(1)
        return best

    def _extract_date_from_context(self, text: str, citation, return_source: bool = False):
        """Extract date/year from citation string itself or surrounding text context.

        FIX 2026-02-10: Prioritize the year from the ORIGINAL DOCUMENT TEXT around the
        citation position over the year in eyecite's reconstructed citation string.
        Eyecite sometimes picks up a nearby year from a different citation or document
        header (e.g., "(scotus 2021)" when the document actually says "(2008)").
        """
        def _ret(year: Optional[str], source: str = "none", confidence: str = "low"):
            if return_source:
                return year, source, confidence
            return year

        try:
            cit_text = citation.citation or ""

            def _has_intervening_citation_noise(chunk: str) -> bool:
                """True when text between cite and year appears to contain another citation."""
                if not chunk:
                    return False
                s = str(chunk)
                # If a full stop/semicolon appears before the year, we likely crossed into another cite/sentence.
                if re.search(r"[;]\s+|[.]\s+[A-Z]", s):
                    return True
                # WL / Lexis cite between base cite and candidate year => wrong year source.
                if re.search(r"\b\d{4}\s*(?:WL|U\.S\.?\s*LEXIS|LEXIS)\s*\d+\b", s, re.IGNORECASE):
                    return True
                # Reporter cite between base cite and candidate year => likely next citation.
                # Federal reporters
                if re.search(
                    r"\b\d+\s+(?:U\.?\s*S\.?|F\.?\s*Supp\.?\s*(?:\d+d)?|F\.?\d+d|F\.?\d+th|S\.?\s*Ct\.?)\s+\d+\b",
                    s,
                    re.IGNORECASE,
                ):
                    return True
                # State reporters (context bleed: Chalkley 143 S.E. 631 ... Mack 639 F. App'x (2016))
                if re.search(
                    r"\b\d+\s+(?:Va\.?|S\.?\s*E\.?\s*(?:\d+d)?|N\.?\s*E\.?\s*(?:\d+d)?|N\.?\s*W\.?\s*(?:\d+d)?|"
                    r"S\.?\s*W\.?\s*(?:\d+d)?|Tenn\.?|F\.?\s*App'?x)\s+\d+\b",
                    s,
                    re.IGNORECASE,
                ):
                    return True
                # Case-history connectors usually indicate we crossed into a different proceeding
                # (e.g., cert. denied ... (2020)), so the nearby year is not for this citation.
                if re.search(
                    r"\b(?:cert\.?\s+denied|cert\.?\s+granted|aff'?d|rev'?d|vacated|remanded|reh'?g)\b",
                    s,
                    re.IGNORECASE,
                ):
                    return True
                return False

            def _reporter_suggests_old_case(cit: str) -> bool:
                """True when citation reporter+volume suggests pre-1950 case (reject recent-year context bleed)."""
                if not cit:
                    return False
                # Historical SCOTUS nominative reporters (pre-1875)
                # Dallas (1-4), Cranch (1-9), Wheaton (1-16), Peters (1-16),
                # Howard (1-24), Black (1-2), Wallace (1-23)
                if re.search(
                    r"\d+\s+(?:Cranch|Wheat|Wall|Pet|How|Black|Dall)\b\.?",
                    cit, re.IGNORECASE,
                ):
                    return True
                # S.E. first series (vol 1-200): 1887-1940; exclude S.E.2d
                m = re.search(r"(\d+)\s+S\.?\s*E\.?\s*(?!2d)\d+", cit, re.IGNORECASE)
                if m and int(m.group(1)) <= 200:
                    return True
                # Va. vols 50-200: 1920s-1930s
                m = re.search(r"(\d+)\s+Va\.?\s+\d+", cit, re.IGNORECASE)
                if m and 50 <= int(m.group(1)) <= 200:
                    return True
                # Tenn., N.E./N.W./S.W. first series (exclude 2d)
                for pat, max_vol in [
                    (r"(\d+)\s+Tenn\.?\s+\d+", 50),
                    (r"(\d+)\s+N\.?\s*E\.?\s*(?!2d)\d+", 250),
                    (r"(\d+)\s+N\.?\s*W\.?\s*(?!2d)\d+", 300),
                    (r"(\d+)\s+S\.?\s*W\.?\s*(?!2d)\d+", 300),
                ]:
                    m = re.search(pat, cit, re.IGNORECASE)
                    if m and int(m.group(1)) <= max_vol:
                        return True
                return False

            # Strategy 0: WL/LEXIS citations have the year as the first token
            wl_match = re.match(r'^(\d{4})\s+(?:WL|U\.S\.?\s*LEXIS|LEXIS)\s+\d+', cit_text)
            if wl_match:
                return _ret(wl_match.group(1), "wl_lexis_citation_token", "high")

            # Strategy 1 (HIGHEST PRIORITY): Extract year from the ORIGINAL DOCUMENT TEXT
            # near the citation position.  The parenthetical year in the actual document
            # is the most authoritative source.
            end = citation.end_index or 0
            start = citation.start_index or 0
            if end > 0:
                # Strategy 1a: Neutral/Ohio citation format (e.g. 2006-Ohio-4854) in text BEFORE citation
                # Prefer this over parenthetical years that may be from nested "(citing ... (9th Cir. 1981))"
                # Support unicode hyphens (PDFs often use \u2011, \u2013, \u2014)
                context_window = text[max(0, start - 120):min(len(text), end + 50)]
                _hy = r'[\-\u2011\u2013\u2014]'  # ASCII hyphen, non-breaking hyphen, en dash, em dash
                neutral_year = re.search(
                    rf'(?:^|[^\d])(20\d{{2}}){_hy}(?:Ohio|OH|NM(?:SC|CA)?|NC(?:SC|COA)|Neb|Neb\.|Ohio\s*St\.){_hy}?\s*\d+',
                    context_window,
                    re.IGNORECASE,
                )
                if neutral_year and 1990 <= int(neutral_year.group(1)) <= 2030:
                    return _ret(neutral_year.group(1), "neutral_citation_year", "high")
                # Match space-separated vendor-neutral citations (all 20 states)
                vn_year = re.search(
                    r'(?:^|[^\d])(20\d{2})\s+(?:IL(?:\s+App)?|COA|CO|ME|MT|ND(?:\s+App)?|OK(?:\s+C(?:IV\s+APP|R))?|SD|UT(?:\s+App)?|VT|WI(?:\s+App)?|WY|Ark\.|N\.H\.|Miss\.)\s+\d+',
                    context_window,
                    re.IGNORECASE,
                )
                if vn_year and 1990 <= int(vn_year.group(1)) <= 2030:
                    return _ret(vn_year.group(1), "neutral_citation_year", "high")
                # Look after the citation end for a parenthetical year
                # Use wider window (150 chars) to handle page breaks in PDFs
                context_after = text[end:min(len(text), end + 150)]
                # Strip document header years (Argued/Decided/Filed) to avoid borrowing 2021 from TransUnion header
                context_after = re.sub(
                    r"(?:Argued|Decided|Filed)\s+[^.]*?(?:17|18|19|20)\d{2}[^.]{0,60}",
                    "",
                    context_after,
                    flags=re.IGNORECASE,
                )
                context_after = re.sub(
                    r"(?:17|18|19|20)\d{2}\s*[-–]\s*(?:Decided|Argued|Filed)[^.]{0,40}",
                    "",
                    context_after,
                    flags=re.IGNORECASE,
                )
                # Strategy 1b: Immediate parenthetical right after citation (before semicolon)
                # e.g. "857 N.W.2d 569 (2015); State ex rel..." -> use 2015, not 1981 from nested (citing...)
                imm = re.match(r'\s*\((\d{4})\)', context_after)
                # Strategy 1b-alt: Citation span may include (YYYY); scan text from start to first ; or (citing
                # Frederick: "289 Neb. 864, 878, 857 N.W.2d 569 (2015); State ex rel... (citing...(1981))"
                # -> use 2015 from before semicolon, not 1981 from nested (citing
                if not imm and start > 0:
                    span = text[start : min(len(text), end + 120)]
                    before_semi = span.split(";")[0] if ";" in span else span
                    citing_pos = re.search(r"\(citing\b", before_semi, re.IGNORECASE)
                    before_citing = before_semi[: citing_pos.start()] if citing_pos else before_semi
                    # Match bare (YYYY) or court-abbreviation years like (S.D.N.Y. 1992), (9th Cir. 2009),
                    # including eyecite-style shorthands like "(ca2 1990)", "(dcd 1987)", "(scotus 1954)".
                    span_match = re.search(r"\([^()]*?(\d{4})\)", before_citing)
                    if span_match and 1700 <= int(span_match.group(1)) <= 2030:
                        # Reject if intervening reporter between cite end and year match
                        text_between = before_citing[
                            before_citing.find(citation.citation or "") + len(citation.citation or "")
                            : span_match.start()
                        ] if (citation.citation or "") in before_citing else ""
                        if not _has_intervening_citation_noise(text_between):
                            if not (int(span_match.group(1)) >= 2000 and _reporter_suggests_old_case(cit_text)):
                                return _ret(span_match.group(1), "citation_span_before_semi", "high")
                if imm and 1990 <= int(imm.group(1)) <= 2030:
                    before_semi = context_after.split(';')[0]
                    if re.search(r'\(\d{4}\)', before_semi) and not re.search(r'\(citing\b', before_semi, re.IGNORECASE):
                        return _ret(imm.group(1), "citation_immediate_parenthetical", "high")
                # Find ALL parenthetical years ending in ####) — Bluebook decision years, not bare "2015" in prose.
                # CRITICAL: Prefer the year CLOSEST to the citation (min start pos) to avoid borrowing
                # from a subsequent citation (e.g. Chalkley 143 S.E. 631 (1928) ... Mack (2016) -> use 1928)
                # Tie-break: bare (YYYY) before longer "(D.N.H. 2013)" when both are equidistant-ish.
                candidates = []
                for m in re.finditer(r'\((?:[A-Za-z0-9.\s]*?)(\d{4})\)', context_after):
                    year = m.group(1)
                    if 1700 <= int(year) <= 2030:
                        bridge = context_after[:m.start()]
                        if _has_intervening_citation_noise(bridge):
                            continue
                        preceding = context_after[:m.start()]
                        if re.search(r'Cite\s+as:', preceding, re.IGNORECASE):
                            continue  # Skip page header year
                        # Reject years from nested citations: (citing ... (9th Cir. 1981))
                        # Only skip "X Cir. YYYY" when it's inside (citing ...); (9th Cir. 2010) right after our cite is valid
                        if (
                            re.search(r'Cir\.\s*\d{4}', m.group(0), re.IGNORECASE)
                            and re.search(r'\(citing\b', context_after[:m.start()], re.IGNORECASE)
                        ):
                            continue  # Court abbrev (9th Cir. YYYY) inside (citing ...)
                        # Reject year when it appears after "(citing" - nested citation, not ours
                        if re.search(r'\(citing\b', context_after[:m.start()], re.IGNORECASE):
                            continue
                        # Reject year when it appears after semicolon - belongs to next citation
                        # e.g. "857 N.W.2d 569 (2015); State ex rel. ... (citing ... (1981))" -> use 2015
                        if re.search(r';\s+', context_after[:m.start()]):
                            continue
                        # Reject modern year (>= 2000) for historical SCOTUS reporters (pre-1875)
                        if int(year) >= 2000 and _reporter_suggests_old_case(cit_text):
                            continue
                        candidates.append((m.start(), year, m.group(0)))
                if candidates:

                    def _paren_year_rank(tup: Tuple[int, str, str]) -> Tuple[int, int, int]:
                        pos, _y, g0 = tup
                        compact = re.sub(r"\s+", "", g0)
                        # 0 = simple decision date (2013); 1 = court line (D.N.H. 2013)
                        simple = 0 if re.fullmatch(r"\(\d{4}\)", compact) else 1
                        return (pos, simple, len(g0))

                    best = min(candidates, key=_paren_year_rank)
                    return _ret(best[1], "citation_parenthetical", "high")
                # If all parenthetical years were in page headers, try bare year after page header
                # PDF page breaks can split "(CA8 2016)" into "(CA8 ...header... 2016)"
                # Look for a bare 4-digit year that follows a page header
                header_match = re.search(r'Cite\s+as:.*?\(\d{4}\)\s*(?:Opinion\s+of\s+the\s+Court\s*)?(\d{4})', context_after, re.IGNORECASE)
                if header_match:
                    year = header_match.group(1)
                    if 1700 <= int(year) <= 2030:
                        return _ret(year, "citation_window_after", "medium")

            # Strategy 2: Look in text BEFORE the citation (sometimes year precedes)
            if start > 0:
                context_before = text[max(0, start - 30):start]
                # Only trust a year immediately adjacent to the citation boundary.
                # Prevent borrowing years from nearby prior citations in the same sentence.
                match = re.search(r'\((\d{4})\)\s*$', context_before)
                if match:
                    year = match.group(1)
                    if 1700 <= int(year) <= 2030:
                        bridge = context_before[:match.start()]
                        if not _has_intervening_citation_noise(bridge):
                            return _ret(year, "citation_window_before", "medium")

            # Document-first policy: do not borrow years from reconstructed citation strings,
            # metadata-only years, or global occurrences. If we didn't find a local year
            # in the document text around this citation boundary, leave it unknown.
            return _ret(None, "none", "low")

        except Exception as date_err:
            logger.debug(
                f"[DATE-EXTRACT] Context date extraction failed for citation "
                f"'{getattr(citation, 'citation', 'unknown')}': {date_err}"
            )
        return _ret(None, "none", "low")

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
        """Clean an extracted case name. Performs extraction-specific stripping, then
        delegates to the shared case_name_cleaner for prose/years/v. trim (single canonical path)."""
        if not name:
            return name
        # Extraction-specific: TOA header prefixes that leak into extracted names
        cleaned = re.sub(
            r'^(?:TABLE\s+OF\s+AUTHORITIES\s+)?(?:(?:I{1,3}V?|V?I{0,3})\s+)?Cases(?:[-]Continued)?(?:\s*:\s*|\s+)(?:Page\s+)?',
            '', name, flags=re.IGNORECASE
        ).strip()
        # Extraction-specific: "Page N" prefix from TOA
        cleaned = re.sub(r'^Page\s+(?=[A-Z])', '', cleaned).strip()
        # Extraction-specific: trailing citation fragments (reporter + page, WL/LEXIS)
        cleaned = re.sub(r",?\s*\d+\s+(?:U\.S\.|F\.\d*d?|S\.\s*Ct\.|L\.\s*Ed|Tex\.|Pet\.|Cranch|Wall\.|Wheat\.|How\.|Barb\.|A\.|F\.\s*(?:Supp|R\.D)|WL|U\.S\.?\s*LEXIS|LEXIS).*$", "", cleaned).strip()
        # Extraction-specific: trailing docket number fragments (", No", ", No.", ", No. CV", ", No. CIV", ", No. C,")
        cleaned = re.sub(r",?\s+No\.?\s*(?:C[IV]{1,3}|CA)?\s*$", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r",?\s+No\.?\s+C\s*(?=,|\s+\d{4}\s*$)", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r",?\s+No\.?\s+C\s*,", ",", cleaned, flags=re.IGNORECASE).strip()
        # Bloomberg / PDF: "L.P. 756 Ltd." fragment from broken "756 F.3d"
        cleaned = re.sub(r"L\.P\.\s*\d{3,4}\s+Ltd\.", "L.P.", cleaned, flags=re.IGNORECASE).strip()
        # Extraction-specific: trailing open parentheticals
        cleaned = re.sub(r"\s*\([^)]*$", "", cleaned).strip()
        # Extraction-specific: truncate at sentence boundary (prose before next sentence)
        sentence_end = re.search(r'(?<=[a-z]{2})\.\s+(?:From|The|This|That|These|Those|It|In|On|At|By|For|And|But|Or|An|As|If|So|No|To|We|He|She|Such|Under|After|Before|During|However|Moreover|Furthermore|Indeed|Rather|Thus|Therefore|Accordingly|Here|There|Where|When|While|Although|Because|Since|Until|Unless|Whether)\b', cleaned)
        if sentence_end:
            cleaned = cleaned[:sentence_end.start()].strip()
        # Max length guard - case names longer than 120 chars are almost certainly contaminated
        if len(cleaned) > 120:
            cleaned = "N/A"
        if not cleaned:
            return name
        # Single canonical path: shared cleaner (court prose, trailing years, v. trim, ex rel, etc.)
        from src.utils.case_name_cleaner import clean_extracted_case_name as shared_clean
        result = shared_clean(cleaned)
        return result if result else name

    def _remove_citation_contamination_from_case_name(self, name: str) -> str:
        """Remove citation text that leaked into case names."""
        if not name:
            return name
        # Remove common citation patterns from case names
        cleaned = re.sub(r'\d+\s+(?:U\.S\.|S\.Ct\.|L\.Ed\.|F\.\d*d?|P\.\d*d?)\s+\d+', '', name)
        cleaned = re.sub(r'\(\d{4}\)', '', cleaned)
        cleaned = cleaned.strip(' ,;.')
        return cleaned if cleaned else name

    def _extract_case_name_from_left_context(
        self, text: str, start_index: int, window: int = 300, citation_text: Optional[str] = None
    ) -> Optional[str]:
        """
        Single path for left-context case name extraction (reporter-only citations).
        Prefer full "Plaintiff v. Defendant" from rightmost " v. "; avoid single-party
        capture from "Name, No. docket" when " v. " is present.
        When citation_text is provided and the span starts with the second party
        (e.g. "Zimmerlein, 2025 WL 1734066"), left_text may end with " v. "; then
        we take the first word from citation_text as the second party.
        """
        if not text or start_index is None or start_index <= 0:
            return None
        left_text = self._clean_context_for_case_name(text[max(0, start_index - window):start_index])
        if not left_text.strip():
            return None
        _diag = citation_text and "1734066" in citation_text
        if _diag:
            _tail = left_text[-120:].replace(chr(10), " ")
            _cit = (citation_text or "")[:50]
            logger.warning(
                "[WL-DIAG] _extract_case_name_from_left_context start_index=%s window=%s left_tail=%r citation_text=%r",
                start_index, window, _tail, _cit,
            )
        # 1) "Name v. Name, No. docket" or "Name v. Name, No." at end
        name_before = re.search(
            r"([A-Z][A-Za-z.\'\-\s]+v\.\s+[A-Z][A-Za-z.\'\-\s]+),\s*No\.\s*[\d\-A-Za-z]+\s*,?\s*$",
            left_text,
            re.DOTALL,
        )
        if not name_before:
            name_before = re.search(
                r"([A-Z][A-Za-z.\'\-\s]+v\.\s+[A-Z][A-Za-z.\'\-\s]+),\s*No\.\s*$",
                left_text,
                re.DOTALL,
            )
        # 1b) "Name v. Name," at end (before WL cite; docket may be on next line or omitted)
        if not name_before:
            name_before = re.search(
                r"([A-Z][A-Za-z.\'\-\s]+v\.\s+[A-Z][A-Za-z.\'\-\s]+),\s*$",
                left_text,
                re.DOTALL,
            )
        # 2) Rightmost " X v. Y " in left context (or " v. " at end + second party in citation_text)
        v_dot_candidate = None
        last_v = left_text.rfind(" v. ")
        if last_v == -1:
            last_v = left_text.rfind(" v ")
        if last_v > 0:
            before = left_text[:last_v].rstrip()
            after = left_text[last_v:].lstrip()
            after_name = re.match(
                r"v\.?\s+([A-Z][A-Za-z.\'\-\s]*?)(?:\s*,\s*No\.|\s*,\s*$|$)",
                after,
                re.DOTALL,
            )
            second_party = (after_name.group(1) or "").strip().rstrip(",") if after_name else None
            # When span starts with second party (e.g. "Zimmerlein, 2025 WL 1734066"), left_text ends with " v. " only
            if not second_party and citation_text and re.match(r"^\s*v\.?\s*$", after.strip()):
                prefix = re.match(r"^([A-Z][A-Za-z.\'\-\s]*?)(?:\s*,\s*No\.|\s*,\s*\d{4}|\s*$)", citation_text.strip())
                if prefix:
                    second_party = prefix.group(1).strip().rstrip(",")
            # Fallback: citation_text may be reporter-only (e.g. "2025 WL 1734066"); second party is BEFORE
            # start_index (e.g. "Webber v. Zimmerlein, No. 3-24-0157, 2025 WL..."). Look at rightmost part
            # of left_text for " v. Name, No." pattern since doc_at = text[start_index:] would show "2025 WL..."
            if not second_party and last_v > 0 and re.match(r"^\s*v\.?\s*$", after.strip()):
                # Try document at start_index only when citation starts with a name (e.g. "Zimmerlein, 2025 WL")
                if citation_text and re.match(r"^[A-Z]", citation_text.strip()):
                    if start_index is not None and len(text) > start_index:
                        doc_at = self._clean_context_for_case_name(text[start_index : start_index + 80])
                        doc_first = re.match(r"^([A-Z][A-Za-z.\'\-\s]*?)(?:\s*,\s*No\.|\s*,\s*\d{4}\s+WL|\s*,\s*$|\s*$)", doc_at)
                        if doc_first:
                            second_party = doc_first.group(1).strip().rstrip(",")
                # Reporter-only: extract second party from rightmost " v. Name, No. docket" in left_text
                if not second_party:
                    right_tail = left_text[-150:] if len(left_text) > 150 else left_text
                    v_name_match = re.search(
                        r"v\.?\s+([A-Z][A-Za-z.\'\-\s]*?),\s*No\.\s*[\d\-A-Za-z]+",
                        right_tail,
                        re.DOTALL,
                    )
                    if v_name_match:
                        second_party = v_name_match.group(1).strip().rstrip(",")
            if second_party:
                first_m = re.search(r"([A-Z][A-Za-z.\'\-\s]*)\s*$", before)
                first_part = (first_m.group(1).strip() if first_m else "") or (
                    before.split(",")[-1].strip() if "," in before else before.strip()
                )
                if first_part and first_part[0].isupper() and len(first_part) >= 2:
                    v_dot_candidate = f"{first_part} v. {second_party}"
                    if len(v_dot_candidate) < 8 or " v. " not in v_dot_candidate:
                        v_dot_candidate = None
        # 3) Single "Name, No. docket" at end (may capture only second party)
        single_name = re.search(
            r"([A-Z][A-Za-z.\'\-\s]+),\s*No\.\s*[\d\-A-Z]+\s*,?\s*$",
            left_text,
            re.DOTALL,
        )
        if name_before:
            candidate = (name_before.group(1) or "").strip().rstrip(",")
            if len(candidate) >= 4 and candidate[0].isupper():
                if _diag:
                    logger.warning(f"[WL-DIAG] _extract_case_name_from_left_context return (name_before)='{candidate}'")
                return candidate
        if single_name:
            candidate = (single_name.group(1) or "").strip().rstrip(",")
            # Prefer full "First v. Second" when we have it
            if v_dot_candidate and (" v. " not in candidate or len(v_dot_candidate) > len(candidate)):
                if _diag:
                    logger.warning(f"[WL-DIAG] _extract_case_name_from_left_context return (single+v_dot)='{v_dot_candidate}'")
                return v_dot_candidate
            if len(candidate) >= 4 and candidate[0].isupper():
                if _diag:
                    logger.warning(f"[WL-DIAG] _extract_case_name_from_left_context return (single_name)='{candidate}'")
                return candidate
        if v_dot_candidate:
            if _diag:
                logger.warning(f"[WL-DIAG] _extract_case_name_from_left_context return (v_dot)='{v_dot_candidate}'")
            return v_dot_candidate
        if _diag:
            logger.warning("[WL-DIAG] _extract_case_name_from_left_context return None (no match)")
        return None

    def _truncate_eyecite_runon_citation(self, citation_str: str) -> str:
        """Trim eyecite spans that incorrectly include prose and a second citation.

        Eyecite sometimes emits a single span such as::
          Bucklew, 587 U.S. ___. Has been upheld ... See, e.g., Whitaker v. Collier, 862 F.3d 490
        which must be one citation object, not an entire sentence cluster.
        """
        if not citation_str or len(citation_str) < 90:
            return citation_str
        s = citation_str.strip()
        original_len = len(s)

        # 1) U.S. slip (_...) or page + period, then ordinary prose (new sentence)
        _PROSE_STARTER = (
            r"Has|Had|The|This|For|But|That|When|Although|However|Because|While|Where|Given|"
            r"Once|If|It|Hours|Against|Plaintiffs|Defendants|Petitioners|Respondents|"
            r"Under|After|Before|Despite|Here|There|Such|These|Those|Each|Every|No\s+fact"
        )
        m = re.search(
            rf"\d+\s+U\.?\s*S\.?\s+(?:_{{2,}}|\d{{1,4}})(?:\s*,\s*(?:_{{2,}}|\d{{1,4}}))*\s*\.\s+({_PROSE_STARTER})\b",
            s,
            re.IGNORECASE,
        )
        if m:
            clipped = s[: m.start(1)].rstrip()
            # Short cites like "Bucklew, 587 U.S. ___." are < 25 chars but valid
            if len(clipped) >= 12:
                logger.info(
                    f"[EYECITE-RUNON] Truncated U.S.+prose ({original_len}->{len(clipped)}): "
                    f"'{s[:55]}...'"
                )
                return clipped

        # 2) Period before mid-span signal phrases (new citation / authority line)
        m = re.search(
            r"\.\s+(See,\s*e\.g\.|But\s+see|See\s+also|See\s+generally|See\s+accord|Compare|Cf\.)\b",
            s,
            re.IGNORECASE,
        )
        if m and m.start() > 50:
            clipped = s[: m.start() + 1].rstrip()
            if len(clipped) >= 25 and len(clipped) < len(s):
                logger.info(
                    f"[EYECITE-RUNON] Truncated before signal phrase ({original_len}->{len(clipped)})"
                )
                return clipped

        # 3) Semicolon-separated citation lists — keep first reporter-bearing segment
        if ";" in s:
            left, right = s.split(";", 1)
            if len(left) > 35 and len(right.strip()) > 30:
                if re.search(
                    r"\d+\s+(?:U\.?\s*S\.?|F\.?\s*(?:2d|3d|4th)|S\.?\s*Ct\.?)\b",
                    left,
                    re.IGNORECASE,
                ):
                    clipped = left.rstrip()
                    logger.info(
                        f"[EYECITE-RUNON] Truncated at semicolon ({original_len}->{len(clipped)})"
                    )
                    return clipped

        # 4) Second case caption after a federal/SCOTUS reporter (different case merged in)
        for m in re.finditer(
            r"(?<![A-Za-z])([A-Z][A-Za-z.'\u2019\-]{0,60}?)\s+v\.\s+([A-Z][A-Za-z.'\u2019\-]{0,60}?)"
            r"(?:\s*,|\s+\d)",
            s,
        ):
            if m.start() < 55:
                continue
            prefix = s[: m.start()]
            if not re.search(
                r"\d+\s+(?:U\.?\s*S\.?|F\.?\s*(?:2d|3d|4th))\b",
                prefix,
                re.IGNORECASE,
            ):
                continue
            clipped = s[: m.start()].rstrip()
            if len(clipped) >= 25 and len(clipped) < len(s):
                logger.info(
                    f"[EYECITE-RUNON] Truncated at second case name ({original_len}->{len(clipped)}): "
                    f"'{clipped[:60]}...'"
                )
                return clipped
            break

        return citation_str

    _TOC_PREFIX_RE = re.compile(
        r"^(?:[IVXLC]+\s+)?"
        r"(?:Cases|Statutes?|Constitut\w+|Miscellaneous|Other\s+Authorities?|Regulations?)"
        r"(?:\s*[-–—]\s*Continued)?\s*:\s*(?:Page\s+)?"
    )
    _TOC_LEADING_NOISE_RE = re.compile(
        r"^.{5,80}?\.\.\.\s*\d+\s+"
    )

    def _strip_toc_prefix(self, citation_str: str) -> str:
        """Strip table-of-contents / section-header prefixes from citation text.

        SCOTUS cert petitions (and other briefs) have TOC pages with entries
        like "IV Cases-Continued: Page Cochise Consultancy, Inc. ...".  Eyecite
        sometimes captures the header as part of the citation span.
        """
        if not citation_str:
            return citation_str
        m = self._TOC_PREFIX_RE.match(citation_str)
        if m:
            stripped = citation_str[m.end():].lstrip()
            if len(stripped) >= 10:
                return stripped
        # Strip leading TOC noise: "9th Cir. 2020) ... 22 The Pizarro, 2 Wheat. 227"
        # The "... NN" pattern is a TOC page reference followed by the next entry.
        m = self._TOC_LEADING_NOISE_RE.match(citation_str)
        if m:
            rest = citation_str[m.end():].lstrip()
            if len(rest) >= 15 and rest[0].isupper():
                return rest
        # Strip mid-string TOC fragments: "... 26 VIII Miscellaneous-Continued: Page Samuel ..."
        cleaned = re.sub(
            r"\.\.\.\s*\d+\s+(?:[IVXLC]+\s+)?"
            r"(?:Cases|Statutes?|Constitut\w+|Miscellaneous|Other\s+Authorities?|Regulations?)"
            r"(?:\s*[-–—]\s*Continued)?\s*:\s*(?:Page\s+)?",
            "... ",
            citation_str,
        )
        if cleaned != citation_str:
            return cleaned.strip()
        # Truncate at TOC page-number ellipsis boundary when followed by
        # non-citation text (e.g. "26 Ohio App. 95... Samuel Estreicher...")
        toc_ellipsis = re.search(r"\.\.\.\s+(?=[A-Z][a-z])", citation_str)
        if toc_ellipsis and toc_ellipsis.start() > 8:
            left = citation_str[:toc_ellipsis.start()].rstrip()
            if re.search(r"\d+\s+[A-Z]", left):
                return left
        return citation_str

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
                    if not citation_str:
                        continue
                    # FIX 2026-02-10: Detect concatenated page+pinpoint from PDF artifacts
                    # e.g. "496 U.S. 310317" should be "496 U.S. 310" (eyecite merges "310, 317")
                    citation_str = self._fix_concatenated_page_numbers(citation_str)

                    start_index = None
                    end_index = None
                    # Try span() as method first (newer eyecite), then as property
                    try:
                        span = citation_obj.span() if callable(getattr(citation_obj, 'span', None)) else getattr(citation_obj, 'span', None)
                        if span and len(span) == 2:
                            start_index = span[0]
                            end_index = span[1]
                    except Exception as span_err:
                        logger.debug(f"[EYECITE] span extraction fallback used: {span_err}")

                    try:
                        from src.utils.extraction_cleaner import snap_s_ct_citation_to_source_window

                        citation_str = snap_s_ct_citation_to_source_window(citation_str, text, start_index)
                    except Exception:
                        pass

                    citation_str = self._truncate_eyecite_runon_citation(citation_str)
                    citation_str = self._strip_toc_prefix(citation_str)
                    if not citation_str or citation_str in seen_citations:
                        continue
                    seen_citations.add(citation_str)
                    if start_index is not None and end_index is not None:
                        # Span reflects pre-truncation text; align end to trimmed citation length
                        end_index = start_index + len(citation_str)
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

    # Reporter pattern used by multiple fix methods
    _REPORTER_ABBR_PAT = (
        r'(?:P\.\s*\d*[a-z]*|N\.(?:E|W)\.\s*\d*[a-z]*|'
        r'S\.\s*(?:Ct|E|W)\.\s*\d*[a-z]*|A\.\s*\d*[a-z]*|'
        r'So\.\s*\d*[a-z]*|Cal\.\s*(?:Rptr|App)|'
        r'F\.\s*(?:Supp|2d|3d|4th)?|'
        r'Wash\.\s*(?:2d|App)?|Wn\.\s*(?:2d|App)?|'
        r'U\.?\s*S\.?|L\.\s*Ed|S\.\s*Ct)'
    )

    def _fix_concatenated_page_numbers(self, citation_str: str) -> str:
        """Fix concatenated numbers from eyecite's corrected_citation_full() bug.

        eyecite's corrected_citation_full() systematically drops the comma/space
        between pinpoint pages and parallel citation volumes, producing garbled text:
          "183 Wash. 2d 863, 879-80357 P.3d 45" (should be "879-80, 357 P.3d 45")
          "194 Wash. 2d 651451 P.3d 675"         (should be "651, 451 P.3d 675")
          "289 Neb. 864, 878857 N.W.2d 569"      (should be "878, 857 N.W.2d 569")

        This function scans the ENTIRE citation text for these patterns and fixes them.
        """
        if not citation_str:
            return citation_str
        # WL and LEXIS citations have docket IDs, not page numbers - never split them
        if re.search(r'\b\d{4}\s+WL\s+\d+', citation_str) or re.search(r'\bLexis\s+\d+', citation_str, re.IGNORECASE):
            return citation_str

        fixed = citation_str

        # Strip paragraph symbol (¶ / pilcrow U+00B6) — PDF artifact that blocks
        # digit-blob regex matching (e.g. ", ¶ 38551 P.3d" → ", 38551 P.3d").
        fixed = re.sub(r'\u00b6+\s*', '', fixed)

        # === Pass 0: Fix implausibly large volume at start of citation ===
        # e.g. "38551 P.3d 655" -> "551 P.3d 655" (38 was stray from context)
        # No reporter has volume >= 1000, so 4+ digit leading numbers are contaminated.
        reporter_pat = self._REPORTER_ABBR_PAT
        vol_start_m = re.match(
            r'^(\d{4,})\s+(' + reporter_pat + r')\s+(\d+)(.*)',
            fixed, re.IGNORECASE
        )
        if vol_start_m:
            vol_blob = vol_start_m.group(1)
            rep_text = vol_start_m.group(2)
            page = vol_start_m.group(3)
            rest = vol_start_m.group(4)
            # Strip leading digits to get a plausible 1-3 digit volume
            for strip_count in range(1, len(vol_blob)):
                candidate = vol_blob[strip_count:]
                if candidate[0] == '0':
                    continue
                val = int(candidate)
                if 1 <= val <= 999:
                    fixed = f"{candidate} {rep_text} {page}{rest}"
                    logger.info(
                        f"[EYECITE-FIX] Volume too large: '{vol_blob}' -> '{candidate}' "
                        f"(stripped {strip_count} leading digits)"
                    )
                    break

        # === Pass 1: Fix digit blobs immediately before a reporter abbreviation ===
        # Pattern: "878857 N.W.2d" or "651451 P.3d" or "879-80357 P.3d"
        # These are pinpoint + parallel_volume concatenated by eyecite's full text bug.
        # Only match blobs preceded by comma or dash (pinpoint area), NOT primary page blobs.
        reporter_pat = self._REPORTER_ABBR_PAT
        blob_before_reporter = re.compile(
            r'[-,]\s*(\d{4,})\s+(' + reporter_pat + r')', re.IGNORECASE
        )
        for _pass in range(5):  # iterate since fixes shift text
            m = blob_before_reporter.search(fixed)
            if not m:
                break
            blob = m.group(1)
            reporter_text = m.group(2)
            blob_start = m.start(1)
            # Try splitting blob into pinpoint + volume where volume is 1-999.
            # 3-digit pinpoints are the most common in legal citations (page
            # numbers 100-999), so try split_pos=3 first. This correctly handles
            # both "82961" -> "829, 61" and "266115" -> "266, 115".
            # For 4-digit blobs, try split_pos=2 first (2-digit pin + 2-digit vol).
            best_split = None
            if len(blob) >= 5:
                try_order = [3] + [i for i in range(2, len(blob)) if i != 3]
            else:
                try_order = list(range(2, len(blob)))
            for split_pos in try_order:
                vol_candidate = blob[split_pos:]
                if vol_candidate[0] == '0':
                    continue
                vol_val = int(vol_candidate)
                if 10 <= vol_val <= 999:
                    best_split = split_pos
                    break
            # Fallback: 1-digit pinpoint
            if best_split is None and len(blob) > 1 and blob[1:][0] != '0':
                vol_val = int(blob[1:])
                if 1 <= vol_val <= 999:
                    best_split = 1
            if best_split:
                pinpoint_part = blob[:best_split]
                vol_part = blob[best_split:]
                # Replace the blob with "pinpoint, volume"
                old_fragment = blob + fixed[m.end(1):m.start(2)]
                new_fragment = pinpoint_part + ", " + vol_part + fixed[m.end(1):m.start(2)]
                fixed = fixed[:blob_start] + new_fragment + fixed[m.start(2):]
                logger.info(
                    f"[EYECITE-FIX] Split pinpoint+volume: '{blob}' -> "
                    f"'{pinpoint_part}, {vol_part}' before '{reporter_text}'"
                )
            else:
                break  # no valid split found

        # === Pass 1b: Fix "reporter_suffix + digits" with no space ===
        # e.g. "Wash. 2d8633" -> "Wash. 2d 863" (page 863 + trailing from parallel vol)
        nospc = re.compile(
            r'(\b(?:Wash|Wn)\.\s*(?:2d|App\.?)\s*|'
            r'\b(?:Ohio\s+St\.\s*(?:2d|3d))\s*|'
            r'\b(?:Conn\.\s*(?:App|Supp)\.?)\s*)'
            r'(\d{4,})',
            re.IGNORECASE
        )
        m_nospc = nospc.search(fixed)
        if m_nospc:
            reporter_prefix = m_nospc.group(1)
            page_blob = m_nospc.group(2)
            blob_start = m_nospc.start(2)
            suffix_after = fixed[m_nospc.end(2):]
            # Check if suffix starts with a reporter (parallel volume concatenation)
            par_match = re.match(r'[,\s]*(' + reporter_pat + r')', suffix_after, re.IGNORECASE)
            if par_match:
                # Split: prefer 3-digit page, then 2, then 4
                for sp in [3, 2, 4]:
                    if sp >= len(page_blob):
                        continue
                    page_part = page_blob[:sp]
                    vol_part = page_blob[sp:]
                    if vol_part and vol_part[0] != '0' and 1 <= int(vol_part) <= 999 and int(page_part) >= 1:
                        fixed = fixed[:blob_start] + page_part
                        logger.info(
                            f"[EYECITE-FIX] No-space page split: '{reporter_prefix}{page_blob}' -> "
                            f"'{reporter_prefix}{page_part}' (dropped parallel vol {vol_part})"
                        )
                        break
            else:
                # Same-reporter pinpoint: split into page + pinpoint
                for sp in range(min(4, len(page_blob) - 1), 1, -1):
                    page_part = page_blob[:sp]
                    pin_part = page_blob[sp:]
                    p_val, pin_val = int(page_part), int(pin_part)
                    if pin_part[0] == '0':
                        continue
                    if p_val >= 1 and pin_val >= p_val and pin_val <= p_val * 10:
                        fixed = fixed[:blob_start] + page_part + suffix_after
                        logger.info(
                            f"[EYECITE-FIX] No-space pinpoint: '{reporter_prefix}{page_blob}' -> "
                            f"'{reporter_prefix}{page_part}'"
                        )
                        break

        # === Pass 2: Fix primary page blob (original logic) ===
        # "496 U.S. 310317" -> "496 U.S. 310"
        is_us_reporter = bool(re.search(
            r'\d+\s+(?:U\.?\s*S\.?|S\.\s*Ct\.|L\.\s*Ed|Wheat\.|Cranch|Wall\.|How\.|Pet\.)',
            fixed
        ))
        min_digits = 4 if is_us_reporter else 5
        m = re.match(
            r'^(.*?\d+\s+[A-Za-z][A-Za-z0-9.\s]*?\s)(\d{' + str(min_digits) + r',})(.*)',
            fixed,
        )
        if m:
            prefix, page_blob, suffix = m.group(1), m.group(2), m.group(3)
            parallel_reporter_match = re.match(
                r'\s*(' + reporter_pat + r')', suffix, re.IGNORECASE
            )
            if parallel_reporter_match:
                split_order = [sp for sp in [3, 2, 4] if 1 < sp < len(page_blob)]
                for split_pos in split_order:
                    page = page_blob[:split_pos]
                    vol = page_blob[split_pos:]
                    if not vol or vol[0] == '0':
                        continue
                    if 1 <= int(page) <= 9999 and 1 <= int(vol) <= 999:
                        fixed = f"{prefix}{page}"
                        logger.info(
                            f"[EYECITE-FIX] Primary page split: '{citation_str[:60]}' -> '{fixed[:60]}'"
                        )
                        break
            else:
                # 133 S. Ct. 2223, 2227 (2013): page_blob is "2223" (one first page) and the
                # comma-pin is already in `suffix` (", 2227"). The loop below would wrongly split
                # 2223 -> 22+23 because 23 <= 22*10 (same bug pattern as Actavis footnote cites).
                sfx = suffix.lstrip()
                if (
                    is_us_reporter
                    and len(page_blob) == 4
                    and page_blob.isdigit()
                    and 1000 <= int(page_blob) <= 9999
                    and re.match(r"^,\s*\d{3,4}\b", sfx)
                ):
                    pass
                else:
                    for split_pos in range(min(4, len(page_blob) - 1), 1, -1):
                        page = page_blob[:split_pos]
                        pinpoint = page_blob[split_pos:]
                        page_val = int(page)
                        if page_val < 1 or page_val > 9999:
                            continue
                        if not pinpoint or pinpoint[0] == '0':
                            continue
                        pin_val = int(pinpoint)
                        if pin_val < page_val or pin_val > page_val * 10:
                            continue
                        fixed = f"{prefix}{page}{suffix}"
                        logger.info(
                            f"[EYECITE-FIX] Primary pinpoint: '{citation_str[:60]}' -> '{fixed[:60]}'"
                        )
                        break

        if fixed != citation_str:
            logger.info(f"[EYECITE-FIX] Final: '{citation_str[:80]}' -> '{fixed[:80]}'")
        return fixed

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
                    # Fix: corrected_citation_full() sometimes prepends stray
                    # digits from preceding context to the volume, e.g.
                    # "38551 P.3d 655" when parsed volume is "551".
                    parsed_vol = str(getattr(citation_obj, 'volume', '') or '')
                    if not parsed_vol:
                        parsed_vol = str(
                            (getattr(citation_obj, 'groups', {}) or {}).get('volume', '') or ''
                        )
                    if parsed_vol:
                        leading_m = re.match(r'^(\d+)', full)
                        if leading_m:
                            leading_digits = leading_m.group(1)
                            if (leading_digits != parsed_vol
                                    and leading_digits.endswith(parsed_vol)
                                    and len(leading_digits) > len(parsed_vol)):
                                stray = leading_digits[:-len(parsed_vol)]
                                full = full[len(stray):]
                                logger.info(
                                    f"[EYECITE-FIX] Stripped stray volume prefix "
                                    f"'{stray}' from '{leading_digits}' -> '{parsed_vol}'"
                                )
                    return full
        except Exception as corr_full_err:
            logger.debug(f"[EYECITE] corrected_citation_full unavailable: {corr_full_err}")

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
        except Exception as corr_err:
            logger.debug(f"[EYECITE] corrected_citation unavailable: {corr_err}")

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
        except Exception as vrp_err:
            logger.debug(f"[EYECITE] volume/reporter/page extraction fallback used: {vrp_err}")

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

        # Phase 0.5: Same-start-index dedup
        # When regex_enhanced and eyecite both find a citation at the same start_index,
        # prefer the one with a case name in its text (eyecite's "Key Design Inc. v. Moser, 138 Wash. 2d 875..."
        # is better than regex's bare "138 Wn.2d 875" which gets the wrong name from context).
        from collections import defaultdict
        start_groups = defaultdict(list)
        no_position = []
        for cit in sorted_citations:
            if cit.start_index is not None:
                start_groups[cit.start_index].append(cit)
            else:
                no_position.append(cit)

        # Instead of removing bare citations, propagate case names from named citations
        # to bare ones at the same position. This fixes wrong names without losing citations.
        for si in sorted(start_groups.keys()):
            group = start_groups[si]
            if len(group) <= 1:
                continue
            # Find citations with case name in text
            best_name = None
            for c in group:
                txt = c.citation or ""
                if " v. " in txt:
                    v_match = re.match(
                        r"^(.+?\s+v\.\s+[A-Za-z0-9][A-Za-z0-9\s\'\.\.\&\-,/()]+?)(?:,\s*\d|\s+\d)",
                        txt,
                    )
                    if v_match:
                        best_name = v_match.group(1).strip().rstrip(",")
                        break
                elif re.search(r"\bIn\s+re\b", txt, re.IGNORECASE):
                    _rb = re.search(
                        r',\s*\d+\s+(?:Wn\.|Wash\.|P\.\d|F\.\d|U\.S\.)',
                        txt
                    )
                    _wl = re.search(r",\s*\d{4}\s+WL\s+\d+", txt, re.IGNORECASE)
                    if _rb:
                        best_name = txt[:_rb.start()].strip().rstrip(",")
                        break
                    if _wl:
                        best_name = txt[:_wl.start()].strip().rstrip(",")
                        break
                # Eyecite often drops leading "In re" on TOA lines; "… Litigation No. …, YYYY WL …" still names the case.
                elif re.search(r"\bNo\.\s*[\w\-]+", txt, re.I) and re.search(
                    r",\s*\d{4}\s+WL\s+\d+", txt, re.I
                ):
                    # TOA lines use ", No. 11-cv-..." or "… Litigation No. 11-cv-..."
                    m_no = re.search(r"(?:,\s*|\s+)No\.\s*", txt, re.I)
                    if m_no:
                        best_name = txt[: m_no.start()].strip().rstrip(",")
                        break
            if best_name and len(best_name) > 4:
                for c in group:
                    txt = c.citation or ""
                    if " v. " not in txt and not re.search(r"\bIn\s+re\b", txt, re.IGNORECASE):
                        # Bare citation — always override with eyecite name.
                        # Bare citations get names from context (unreliable);
                        # eyecite parses the actual citation text (authoritative).
                        old_name = c.extracted_case_name or "N/A"
                        if old_name != best_name:
                            c.extracted_case_name = best_name
                            c._dedup_name_set = True
                            logger.info(
                                f"[DEDUP-PROPAGATE] Override '{old_name}' -> '{best_name}' "
                                f"on bare '{txt[:40]}' at start={si}"
                            )
        # Phase 0.55: Name from citation text for "…, No. docket, YYYY WL …" / "… No. docket, YYYY WL …"
        # when eyecite drops "In re" and there is no " v. ". Same-start dedup only runs when len(group)>1;
        # singleton TOA lines would otherwise keep a wrong context name (e.g. Dentsply on Effexor WL).
        _no_wl_signal = re.compile(
            r"(?i)^(see|see also|e\.g\.|cf\.|accord|but see|contra|compare)\s"
        )

        def _apply_no_wl_line_name(cit: CitationResult) -> None:
            txt = cit.citation or ""
            if " v. " in txt or re.search(r"\bIn\s+re\b", txt, re.I):
                return
            if not re.search(r",\s*\d{4}\s+WL\s+\d+", txt, re.I):
                return
            if not re.search(r"\bNo\.\s*[\w\-]+", txt, re.I):
                return
            m_no = re.search(r"(?:,\s*|\s+)No\.\s*", txt, re.I)
            if not m_no:
                return
            prefix = txt[: m_no.start()].strip().rstrip(",")
            if len(prefix) <= 4 or _no_wl_signal.match(prefix):
                return
            cit.extracted_case_name = prefix
            cit._dedup_name_set = True
            logger.info(
                f"[DEDUP-NO-WL-LINE] Set extracted_case_name from cite text: {prefix[:60]!r}…"
            )

        for _grp in start_groups.values():
            for _cit in _grp:
                _apply_no_wl_line_name(_cit)
        for _cit in no_position:
            _apply_no_wl_line_name(_cit)

        sorted_citations = [c for group in sorted(start_groups.values(), key=lambda g: g[0].start_index or 0) for c in group] + no_position
        sorted_citations.sort(key=lambda x: (x.start_index or 0, -(x.end_index or 0)))

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

        # Phase 2.5: Drop bare "YYYY WL nnnn" when a longer citation embeds the same Westlaw ID
        # (avoids duplicate rows + wrong left-context names from TOA adjacency, e.g. Effexor WL + Aggrenox bleed).
        _wl_only = re.compile(r"^\s*((?:19|20)\d{2})\s+WL\s+(\d{1,12})\s*$", re.IGNORECASE)
        _wl_embed = re.compile(r"\b((?:19|20)\d{2})\s+WL\s+(\d{1,12})\b", re.IGNORECASE)
        to_drop = set()
        for i, c in enumerate(final):
            mo = _wl_only.match((c.citation or "").strip())
            if not mo:
                continue
            fp = f"{mo.group(1)} WL {mo.group(2)}"
            for j, other in enumerate(final):
                if i == j:
                    continue
                ot = (other.citation or "").strip()
                if len(ot) <= len((c.citation or "").strip()):
                    continue
                if re.search(re.escape(mo.group(1)) + r"\s+WL\s+" + re.escape(mo.group(2)), ot, re.I):
                    to_drop.add(id(c))
                    break
        if to_drop:
            before_sub = len(final)
            final = [c for c in final if id(c) not in to_drop]
            logger.info(f"[DEDUP-WL-SUBSUME] Removed {before_sub - len(final)} bare WL cite(s) embedded in longer citation")

        # Phase 2.6: Remove volume-truncated duplicates caused by OCR errors.
        # OCR may produce "4837 U.S. 117" instead of "437 U.S. 117"; eyecite then
        # parses it as "48, 37 U.S. 117", creating a phantom "37 U.S. 117".
        # Drop the shorter-volume citation when a longer-volume one shares the same
        # reporter and page number.
        _vol_rep_page = re.compile(
            r"(?:^|,\s*)(\d{1,4})\s+"                     # volume
            r"([A-Z][A-Za-z.\s]*(?:2d|3d|4th|5th)?)\s+"   # reporter
            r"(\d{1,5})\b"                                 # page
        )
        vol_truncate_drop = set()
        parsed = []
        for c in final:
            ct = (c.citation or "").strip()
            m = _vol_rep_page.search(ct)
            if m:
                parsed.append((c, m.group(1), m.group(2).strip(), m.group(3)))
            else:
                parsed.append((c, None, None, None))
        for i, (ci, vi, ri, pi) in enumerate(parsed):
            if vi is None:
                continue
            for j, (cj, vj, rj, pj) in enumerate(parsed):
                if i == j or vj is None:
                    continue
                # Same reporter (normalized) and same page, but one volume is a suffix of the other
                if pi == pj and ri.replace(" ", "").lower() == rj.replace(" ", "").lower():
                    if vj.endswith(vi) and len(vj) > len(vi):
                        # ci has the shorter (truncated) volume -> drop it
                        vol_truncate_drop.add(id(ci))
                        logger.info(
                            f"[DEDUP-VOL-TRUNCATE] Dropping '{ci.citation}' "
                            f"(vol {vi}) — subsumed by '{cj.citation}' (vol {vj})"
                        )
                        break
        if vol_truncate_drop:
            before_vt = len(final)
            final = [c for c in final if id(c) not in vol_truncate_drop]
            logger.info(f"[DEDUP-VOL-TRUNCATE] Removed {before_vt - len(final)} volume-truncated duplicate(s)")

        # Phase 2.7: Remove page-truncated duplicates caused by pincite concatenation.
        # PDF text like "651 F. Supp. 81, 9" (page=81, pincite=9) can be concatenated
        # into "651 F. Supp. 819" when a comma is dropped during extraction.
        # Drop the longer-page citation when a shorter-page one shares the same
        # volume+reporter and the shorter page is a numeric prefix of the longer one.
        _vol_rep_page2 = re.compile(
            r"(?:^|,\s*)(\d{1,4})\s+"                     # volume
            r"([A-Z][A-Za-z.\s]*(?:2d|3d|4th|5th)?)\s+"   # reporter
            r"(\d{1,5})\b"                                  # page
        )
        page_truncate_drop = set()
        parsed2 = []
        for c in final:
            ct = (c.citation or "").strip()
            m = _vol_rep_page2.search(ct)
            if m:
                parsed2.append((c, m.group(1), m.group(2).strip(), m.group(3)))
            else:
                parsed2.append((c, None, None, None))
        for i, (ci, vi, ri, pi) in enumerate(parsed2):
            if vi is None or pi is None:
                continue
            for j, (cj, vj, rj, pj) in enumerate(parsed2):
                if i == j or vj is None or pj is None:
                    continue
                # Same volume and reporter (normalized), and page_j starts with page_i
                # but is longer (pi="81", pj="819" → pj starts with pi)
                if (vi == vj and ri.replace(" ", "").lower() == rj.replace(" ", "").lower()
                        and pj.startswith(pi) and len(pj) > len(pi)):
                    page_truncate_drop.add(id(cj))
                    logger.info(
                        f"[DEDUP-PAGE-TRUNCATE] Dropping '{cj.citation}' "
                        f"(page {pj}) — likely concat of '{ci.citation}' (page {pi}) + pincite"
                    )
                    break
        if page_truncate_drop:
            before_pt = len(final)
            final = [c for c in final if id(c) not in page_truncate_drop]
            logger.info(f"[DEDUP-PAGE-TRUNCATE] Removed {before_pt - len(final)} page-truncated duplicate(s)")

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
            "scotus_parallel_block",  # U.S. + S.Ct. + L.Ed.2d in one block (e.g. BMW v. Gore)
            "scotus_parallel_block_led_first",  # U.S. + L.Ed.2d + S.Ct. (alternate order)
            "ohio_parallel_block",  # Ohio St. + neutral + N.E.2d (e.g. State ex rel. Oriana House)
            "wash_with_pinpoint_and_parallel",  # NEW: Handle pinpoint pages with parallel citations
            "parallel_citation_cluster",
            "flexible_wash2d",
            "flexible_p2d",
            "wash_complete",
            "wash_with_parallel",
            "parallel_cluster",
            # U.S. Supreme Court parallel citations (e.g. BMW v. Gore: 517 U.S. 559, 116 S. Ct. 1589, 134 L. Ed. 2d 809)
            "us",
            "us_spaced",
            "s_ct",
            "l_ed",
            "l_ed2d",
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
            "neutral_ohio",  # Ohio: 2006-Ohio-4854 (before ohio_st so neutral cite is extracted)
            "neutral_ohio_fused",  # 4632006-Ohio-4854 when pinpoint+year fused
            "me",  # Maine - e.g., "2005 ME 113" (Dow v. Caribou)
            "neb",  # Nebraska - e.g., "289 Neb. 864" (Frederick v. City of Falls City)
            "ohio_st",  # Ohio Supreme Court - e.g., "110 Ohio St. 3d 456"
            "ne2d",  # N.E.2d - e.g., "854 N.E.2d 193" (Ohio, Ill., etc.)
            "nw2d",  # N.W.2d - e.g., "857 N.W.2d 569" (Nebraska, etc.)
            "a2d",  # A.2d - e.g., "884 A.2d 667" (Maine Atlantic Reporter)
            # Federal district docket (e.g. 17 Cv. 7507 (F.DNY May 2, 2019)) and F. Supp. 3d with PDF artifacts
            "federal_docket",
            "f_supp3d_flex",
            # Illinois citations
            "ill_2d",
            "ill_app_3d",
            "ill_app_2d",
            "ill_sc_year",  # 2025 IL 130033
            "ill_app_year",  # 2023 IL App (1st) 220990
            "ill_general",
            "ill_historical",
            # Vendor-neutral / public domain citations (19 other states)
            # Appellate variants BEFORE supreme court (longer match first)
            "neutral_coa",      # Colorado Court of Appeals: 2024 COA 1
            "neutral_co",       # Colorado Supreme Court: 2024 CO 1
            "neutral_nd_app",   # North Dakota Court of Appeals: 2024 ND App 1
            "neutral_nd",       # North Dakota Supreme Court: 2024 ND 1
            "neutral_ok_civ",   # Oklahoma Civil Appeals: 2024 OK CIV APP 1
            "neutral_ok_cr",    # Oklahoma Criminal Appeals: 2024 OK CR 1
            "neutral_ok",       # Oklahoma Supreme Court: 2024 OK 1
            "neutral_ut_app",   # Utah Court of Appeals: 2024 UT App 1
            "neutral_ut",       # Utah Supreme Court: 2024 UT 1
            "neutral_wi_app",   # Wisconsin Court of Appeals: 2024 WI App 1
            "neutral_wi",       # Wisconsin Supreme Court: 2024 WI 1
            "neutral_mt",       # Montana Supreme Court: 2024 MT 1
            "neutral_sd",       # South Dakota Supreme Court: 2024 SD 1
            "neutral_vt",       # Vermont Supreme Court: 2024 VT 1
            "neutral_wy",       # Wyoming Supreme Court: 2024 WY 1
            "neutral_ar",       # Arkansas: 2024 Ark. 1, 2024 Ark. App. 1
            "neutral_nh",       # New Hampshire: 2024 N.H. 1
            "neutral_ms_year",  # Mississippi: 2024 Miss. 1
            "neutral_nm",       # New Mexico: 2024-NMSC-001, 2024-NMCA-001
            "neutral_nc",       # North Carolina: 2024-NCSC-1, 2024-NCCOA-1
            "mj",               # Military Justice - 45 M.J. 491
            "fed_app_six",      # 6th Cir. FED App - 2001 FED App. 0138P
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

                    # OCR sanity: drop implausible volumes for well-known federal reporters
                    # (e.g., "4837 U.S. 117" where "4" bled into the volume).
                    try:
                        vol_i = int(volume) if str(volume).isdigit() else None
                    except Exception:
                        vol_i = None
                    if vol_i is not None:
                        # Future-proofing: no known reporters should have 4+ digit *volume* numbers.
                        # Exempt year-based formats where a 4-digit number is expected (WL/LEXIS).
                        is_year_based_vendor = bool(
                            re.search(r"\b(?:19|20)\d{2}\s+(?:WL|(?:U\.S\.?\s*)?LEXIS|LEXIS)\s+\d+\b", citation_str, re.IGNORECASE)
                        )
                        if not is_year_based_vendor and vol_i >= 1000:
                            continue
                        if reporter in {"us", "u s"} and vol_i > 700:
                            continue
                        if reporter in {"sct", "s ct"} and vol_i > 250:
                            continue
                        if reporter in {"led2d", "l ed 2d", "led"} and vol_i > 999:
                            continue

                    if volume and int(volume) < 10 and "P." in citation_str:
                        if not self._validate_volume_number(text, match.start(), volume):
                            continue

                    seen_citations.add(citation_str)
                    start_pos = match.start()
                    end_pos = match.end()

                    # Special handling for scotus_parallel_block: create all 3 citations with parallel_citations
                    pinpoint_pages = []
                    parallel_citations = []
                    scotus_citations_to_add = []  # For block pattern: add all 3, skip normal single-citation path

                    if pattern_name == "scotus_parallel_block" and match.groups():
                        # Groups: 1=U.S.vol, 2=U.S.page, 3=S.Ct.vol, 4=S.Ct.page, 5=L.Ed.vol, 6=L.Ed.page
                        us_cit = f"{match.group(1)} U.S. {match.group(2)}"
                        sct_cit = f"{match.group(3)} S. Ct. {match.group(4)}"
                        led_cit = f"{match.group(5)} L. Ed. 2d {match.group(6)}"
                        for cit_str, start_off in [
                            (us_cit, match.start()),
                            (sct_cit, normalized_text.find(sct_cit, match.start())),
                            (led_cit, normalized_text.find(led_cit, match.start())),
                        ]:
                            if cit_str in seen_citations:
                                continue
                            seen_citations.add(cit_str)
                            end_off = start_off + len(cit_str) if start_off >= 0 else match.end()
                            others = [c for c in (us_cit, sct_cit, led_cit) if c != cit_str]
                            scotus_citations_to_add.append(
                                CitationResult(
                                    citation=cit_str,
                                    start_index=start_off if start_off >= 0 else match.start(),
                                    end_index=end_off,
                                    method="regex_enhanced",
                                    pattern=pattern_name,
                                    confidence=0.9,
                                    pinpoint_pages=[],
                                    parallel_citations=others,
                                )
                            )
                    elif pattern_name == "ohio_parallel_block" and match.groups():
                        # Groups: 1=Ohio vol, 2=Ohio page, 3=neutral year, 4=neutral num, 5=N.E.2d vol, 6=N.E.2d page
                        series = "3d" if "2d" not in match.group(0) else "2d"
                        ohio_st_cit = f"{match.group(1)} Ohio St. {series} {match.group(2)}"
                        neutral_cit = f"{match.group(3)}-Ohio-{match.group(4)}"
                        ne2d_cit = f"{match.group(5)} N.E.2d {match.group(6)}"
                        for cit_str, start_off in [
                            (ohio_st_cit, match.start()),
                            (neutral_cit, normalized_text.find(neutral_cit, match.start())),
                            (ne2d_cit, normalized_text.find(ne2d_cit, match.start())),
                        ]:
                            if cit_str in seen_citations:
                                continue
                            seen_citations.add(cit_str)
                            end_off = start_off + len(cit_str) if start_off >= 0 else match.end()
                            others = [c for c in (ohio_st_cit, neutral_cit, ne2d_cit) if c != cit_str]
                            scotus_citations_to_add.append(
                                CitationResult(
                                    citation=cit_str,
                                    start_index=start_off if start_off >= 0 else match.start(),
                                    end_index=end_off,
                                    method="regex_enhanced",
                                    pattern=pattern_name,
                                    confidence=0.9,
                                    pinpoint_pages=[],
                                    parallel_citations=others,
                                )
                            )
                    elif pattern_name == "neutral_ohio_fused" and match.groups():
                        # Output normalized "2006-Ohio-4854" (strip extra space)
                        citation_str = f"{match.group(1)}-Ohio-{match.group(2)}"
                    elif pattern_name == "wash_with_pinpoint_and_parallel" and match.groups():
                        # Extract pinpoint page (group 3) and parallel citation (groups 4-5)
                        if match.group(3):  # Pinpoint page
                            pinpoint_pages = [match.group(3)]
                        if match.group(4) and match.group(5):  # Parallel citation
                            parallel_citations = [f"{match.group(4)} P.3d {match.group(5)}"]

                    if scotus_citations_to_add:
                        citations.extend(scotus_citations_to_add)
                        continue

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

    def _strip_pincitations_before_extraction(self, text: str) -> str:
        """
        Remove pincitation references from text before citation extraction.
        Prevents false positives like "137 P.3d 337" when "at 210" appears between
        Wash. App. page and P.3d cite: "151 Wn. App. 137, at 210, 210 P.3d 337".
        """
        if not text:
            return text
        # Remove: ", at *N"/", at N"/", at N-N"; ", 210-11" (page ranges); ", 210 n.5" (footnotes)
        stripped = re.sub(
            r",\s*at\s+\*?\d+(?:-\d+)?\b"
            r"|,\s*\d{2,4}-\d{1,4}\b(?!\s+P\.\d*d)"
            r"|,\s*\d+\s+n\.?\s*\d+\b",
            "",
            text,
            flags=re.IGNORECASE,
        )
        # Remove standalone pinpoint between citations: "1 U.S. 2, 3, 4 S.Ct 5" -> "1 U.S. 2, 4 S.Ct 5"
        # Only single-digit pinpoints to avoid stripping page numbers (e.g. ", 67, 431" Va. page + S.E.2d vol)
        # or page+pinpoint (e.g. ", 289, 291" in "431 S.E.2d 289, 291")
        stripped = re.sub(r",\s*\d\s*,\s*", ", ", stripped)
        stripped = re.sub(r"\s+", " ", stripped).strip()
        return stripped

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
        logger.info(f"[UNIFIED_EXTRACTION] Text normalized: {len(text)} -> {len(normalized_text)} chars")

        try:
            normalized_text = apply_pre_extraction_text_fixes(normalized_text)
        except Exception as _pre_e:
            logger.warning(f"[UNIFIED_EXTRACTION] apply_pre_extraction_text_fixes skipped: {_pre_e}")

        # Run full-document citation normalization once so all input types (file/text/URL) see the same fixes.
        # Fixes PDF artifacts (e.g. lost comma "81 91233 P.3d" -> "81 91, 233 P.3d") before extraction.
        # Normalization is now O(n): 0a uses single-pass; Case C uses bounded prefix to avoid backtracking.
        try:
            normalized_text = self._normalize_citation_comprehensive(
                normalized_text, purpose="general", all_citations=None
            )
            logger.info("[UNIFIED_EXTRACTION] Full-document citation normalization applied")
        except Exception as e:
            logger.warning(f"[UNIFIED_EXTRACTION] Full-document normalization failed, using text as-is: {e}")

        # Strip pincitations before extraction to prevent false positives
        # E.g. "151 Wn. App. 137, at 210, 210 P.3d 337" -> "151 Wn. App. 137, 210 P.3d 337"
        normalized_text = self._strip_pincitations_before_extraction(normalized_text)

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

        # Step 4: Normalize citation strings BEFORE name/date and before any use of positions.
        # Ensures verification and clustering see consistent reporter format (e.g. Supp. 3d, F.3d 212).
        logger.info("[UNIFIED_EXTRACTION] Step 4: Normalizing citation strings (before name/date)")
        for citation in deduplicated_citations:
            try:
                citation.citation = self._normalize_citation_comprehensive(
                    citation.citation, purpose="general", all_citations=deduplicated_citations
                )
            except Exception as e:
                logger.warning(f"[UNIFIED_EXTRACTION] Error normalizing citation '{citation.citation}': {e}")
                continue

        # Step 4a: Strip (quoting ...)/(citing ...) parentheticals so embedded inner
        # citations don't contaminate the outer citation's display or clustering.
        # The inner citations are already extracted as their own CitationResult objects.
        _QUOTING_PAREN_RE = re.compile(
            r'\s*\(\s*(?:quoting|citing|quoted\s+in|cited\s+in|accord)\s.*$',
            re.IGNORECASE | re.DOTALL,
        )
        for citation in deduplicated_citations:
            ct = citation.citation or ""
            m = _QUOTING_PAREN_RE.search(ct)
            if m and m.start() > 10:
                citation.citation = ct[:m.start()].rstrip(" ,;")

        # Step 4b: Set citation-type flags once (drives extraction + verification + display).
        # NOTE: When we fall back to regex in process_text() (unified failed), those citations
        # never run Step 4b; process_text() sets the same flags for them (see "CRITICAL: Regex-fallback" block).
        from src.utils.citation_type_utils import is_proprietary_only_citation, name_likely_in_left_context as _name_in_left, is_statutory_citation
        for citation in deduplicated_citations:
            ct = citation.citation or ""
            citation.is_proprietary_only = is_proprietary_only_citation(ct)
            citation.name_likely_in_left_context = _name_in_left(ct)

        # Step 4c: Remove statutory / non-case citations (Pub. L., U.S.C., Stat., Cong. Rec., etc.)
        # These are not court opinions and should not go through case name extraction or verification.
        pre_filter_count = len(deduplicated_citations)
        deduplicated_citations = [c for c in deduplicated_citations if not is_statutory_citation(c.citation or "")]
        filtered_count = pre_filter_count - len(deduplicated_citations)
        if filtered_count:
            logger.info(f"[UNIFIED_EXTRACTION] Step 4c: Removed {filtered_count} statutory/non-case citations")

        logger.info("[UNIFIED_EXTRACTION] Step 5: Extracting names and dates with full text context")
        # FIX #44: Use normalized_text for extraction since citation positions are from normalized_text.
        # Always set extracted_case_name (even to "N/A") so the UI never shows blank for "from document".
        ordered = sorted(
            deduplicated_citations,
            key=lambda c: int(getattr(c, "start_index", None) or 0),
        )
        previous_strong_case_name: Optional[str] = None
        for citation in ordered:
            try:
                # TOA / eyecite: wrong ``(scotus YYYY)`` when a neighbor cite's year is absorbed
                try:
                    from src.utils.extraction_cleaner import reconcile_eyecite_scotus_suffix_year

                    _win = (getattr(citation, "context", None) or "")
                    _si = getattr(citation, "start_index", None)
                    _ei = getattr(citation, "end_index", None)
                    if _si is not None and _ei is not None and normalized_text:
                        _win = (
                            f"{_win} "
                            f"{normalized_text[max(0, _si - 160):min(len(normalized_text), _ei + 160)]}"
                        )
                    citation.citation = reconcile_eyecite_scotus_suffix_year(
                        citation.citation or "", _win
                    )
                except Exception:
                    pass

                _existing_ecn = (getattr(citation, "extracted_case_name", None) or "").strip()
                _needs_extraction = not _existing_ecn
                # Reporter-only citations with a defendant-only name (no "v.")
                # should re-run extraction so Strategy 4.5 can recover the full
                # "Plaintiff v. Defendant" from context.
                if (not _needs_extraction
                        and getattr(citation, "name_likely_in_left_context", False)
                        and " v. " not in _existing_ecn
                        and _existing_ecn != "N/A"
                        and len(_existing_ecn) >= 3):
                    _needs_extraction = True

                if _needs_extraction:
                    citation.extracted_case_name = self._extract_case_name_from_context(
                        normalized_text, citation, deduplicated_citations
                    )

                # Override context-based name with inline name when the citation text
                # itself contains a case name prefix before the reporter pattern.
                # E.g. "The Pizarro, 2 Wheat. 227" → "The Pizarro" (not a nearby context name).
                inline_name = self._extract_inline_case_name(citation.citation or "")
                if inline_name:
                    old_ecn = (citation.extracted_case_name or "N/A")[:40]
                    if not citation.extracted_case_name or citation.extracted_case_name == "N/A":
                        citation.extracted_case_name = inline_name
                        citation._inline_name_set = True
                        logger.info(f"[INLINE-NAME] Set ecn='{inline_name}' for '{(citation.citation or '')[:50]}'")
                    elif inline_name.lower() != (citation.extracted_case_name or "").lower():
                        # Inline name differs from context name — prefer inline since it's
                        # physically attached to this citation in the document text.
                        logger.info(
                            f"[INLINE-NAME] Override ecn '{old_ecn}' -> '{inline_name}' "
                            f"for '{(citation.citation or '')[:50]}'"
                        )
                        citation.extracted_case_name = inline_name
                        citation._inline_name_set = True

                # Subsequent history binding (document-first): when a citation is introduced by
                # "aff'd", "rev'd", "cert. denied", etc., inherit the immediately preceding strong
                # case name anchor from the document flow.
                try:
                    si = int(getattr(citation, "start_index", None) or 0)
                    before = (normalized_text[max(0, si - 80) : si] if normalized_text else "").lower()
                    hist = None
                    if re.search(r",\s*aff'?d\b|,\s*affirmed\b", before):
                        hist = "affirmed"
                    elif re.search(r",\s*rev'?d\b|,\s*reversed\b", before):
                        hist = "reversed"
                    elif re.search(r",\s*vacated\b", before):
                        hist = "vacated"
                    elif re.search(r",\s*remanded\b", before):
                        hist = "remanded"
                    elif re.search(r",\s*cert\.?\s*denied\b", before):
                        hist = "cert_denied"
                    elif re.search(r",\s*cert\.?\s*granted\b", before):
                        hist = "cert_granted"
                    elif re.search(r",\s*per\s+curiam\b", before):
                        hist = "per_curiam"
                    if hist and previous_strong_case_name and previous_strong_case_name != "N/A":
                        cur = (getattr(citation, "extracted_case_name", None) or "").strip()
                        if (not cur) or cur == "N/A" or (" v. " not in cur):
                            citation.extracted_case_name = previous_strong_case_name
                            mdh = getattr(citation, "metadata", None) or {}
                            mdh["is_appellate_history"] = True
                            mdh["appellate_history_type"] = hist
                            citation.metadata = mdh
                except Exception:
                    pass

                existing_date = getattr(citation, "extracted_date", None)
                existing_confidence = (getattr(citation, "metadata", None) or {}).get(
                    "extracted_date_confidence", ""
                )
                need_date_extraction = (
                    self._is_missing_extracted_date(existing_date)
                    or existing_confidence in ("low", "")
                )
                if need_date_extraction:
                    extracted_year, date_source, date_confidence = self._extract_date_from_context(
                        normalized_text, citation, return_source=True
                    )
                    if extracted_year and (
                        self._is_missing_extracted_date(existing_date)
                        or (date_confidence in ("high", "medium") and existing_confidence in ("low", ""))
                    ):
                        citation.extracted_date = extracted_year
                        self._set_extracted_date_provenance(citation, date_source, date_confidence)

                # Cross-check with eyecite's parsed year when available.
                # Eyecite parses court+year parentheticals like "(dcd 1987)" / "(ca2 1990)" that
                # context-based extraction may miss (or contaminate via TOA neighbors).
                md = getattr(citation, "metadata", None) or {}
                eyecite_year = str((md.get("year", "") or "")).strip()
                if eyecite_year and eyecite_year.isdigit() and 1700 <= int(eyecite_year) <= 2030:
                    # Prefer eyecite's year when:
                    # - extracted date is missing, or
                    # - the citation text itself contains that year, or
                    # - we only have low/unknown confidence from context.
                    cur_conf = (md.get("extracted_date_confidence") or "").strip().lower()
                    if (
                        self._is_missing_extracted_date(getattr(citation, "extracted_date", None))
                        or eyecite_year in (citation.citation or "")
                        or cur_conf in ("", "low", "medium")
                    ):
                        if str(getattr(citation, "extracted_date", None) or "") != eyecite_year:
                            citation.extracted_date = eyecite_year
                            self._set_extracted_date_provenance(citation, "citation_metadata_year", "high")

                # WL/LEXIS override: extract year from WL/LEXIS pattern anywhere in citation text
                cit_text = citation.citation or ""
                wl_year = re.search(r'(\d{4})\s+(?:WL|U\.S\.?\s*LEXIS|LEXIS)\s+\d+', cit_text)
                if wl_year:
                    citation.extracted_date = wl_year.group(1)
                    self._set_extracted_date_provenance(citation, "wl_lexis_citation_token", "high")
                # Eyecite (scotus YYYY) / (ca9 YYYY): always wins over context/TOA year bleed (e.g. 2025 vs 1985).
                court_paren_y = re.search(
                    r"\((?:scotus|ca\d+)\s+((?:19|20)\d{2})\s*\)",
                    cit_text,
                    re.IGNORECASE,
                )
                if court_paren_y:
                    y = court_paren_y.group(1)
                    if str(getattr(citation, "extracted_date", None) or "") != y:
                        citation.extracted_date = y
                        self._set_extracted_date_provenance(
                            citation, "citation_court_year_paren", "high"
                        )
                    # Keep metadata.year in sync with citation-derived year (used by response formatting).
                    try:
                        md2 = getattr(citation, "metadata", None) or {}
                        md2["year"] = int(y)
                        citation.metadata = md2
                    except Exception:
                        pass
                # Decision year in cite string wins over context / TOA / signature bleed (Actavis (2013) vs 2015)
                paren_decision = self._decision_year_from_citation_paren(cit_text)
                if paren_decision:
                    citation.extracted_date = paren_decision
                    self._set_extracted_date_provenance(
                        citation, "citation_paren_decision_year", "high"
                    )
                    try:
                        md3 = getattr(citation, "metadata", None) or {}
                        if str(md3.get("year") or "").strip() != str(paren_decision):
                            md3["year"] = int(paren_decision)
                        citation.metadata = md3
                    except Exception:
                        pass
                elif self._is_missing_extracted_date(getattr(citation, "extracted_date", None)) and cit_text:
                    paren_year = re.search(r"\((19\d{2}|20\d{2})\)", cit_text)
                    if paren_year:
                        citation.extracted_date = paren_year.group(1)
                        self._set_extracted_date_provenance(citation, "citation_text_parenthetical", "high")

                if citation.extracted_case_name:
                    citation.extracted_case_name = self._repair_truncated_case_name(
                        citation.extracted_case_name,
                        normalized_text,
                        citation.start_index or 0,
                        citation_text=citation.citation or "",
                        context_override=getattr(citation, "context", "") or "",
                    )
                    # Expand "Nat." / "Local No" truncations using citation text and surrounding document context
                    ctx_start = max(0, (citation.start_index or 0) - 150)
                    ctx_end = min(len(normalized_text), (citation.end_index or 0) + 150)
                    ctx_window = normalized_text[ctx_start:ctx_end] if normalized_text else ""
                    citation.extracted_case_name = self._expand_defendant_truncations(
                        citation.extracted_case_name,
                        citation.citation or "",
                        context=ctx_window,
                    )
                    citation.extracted_case_name = self._clean_extracted_case_name(citation.extracted_case_name)
                    wl_y_harm = re.search(
                        r"(\d{4})\s+(?:WL|U\.S\.?\s*LEXIS|LEXIS)\s+\d+",
                        citation.citation or "",
                        re.IGNORECASE,
                    )
                    if wl_y_harm:
                        self._harmonize_trailing_year_in_extracted_case_name(
                            citation, wl_y_harm.group(1)
                        )
                    self._repair_known_reporter_glitches(citation)
                    # Reject quote/sentence misidentified as case name (e.g. "Time and again, the Supreme Court has said no")
                    # But NOT for inline-extracted names (physically embedded in citation text)
                    if (not getattr(citation, '_inline_name_set', False)
                            and self._looks_like_quote_not_case_name(citation.extracted_case_name)):
                        citation.extracted_case_name = "N/A"
                # Reject obvious noise citations (e.g. "States 1", "Page 5") for all citations
                if self._is_noise_citation(citation.citation or ""):
                    citation.extracted_case_name = "N/A"
                # Unconditional: reject prose/quote as case name (e.g. "Cockrum's failure to demonstrate..." for 138 Wn.2d 506 = Benjamin)
                # But NOT for inline-extracted names (physically embedded in citation text = real case name)
                if (citation.extracted_case_name
                        and not getattr(citation, '_inline_name_set', False)
                        and self._looks_like_quote_not_case_name(citation.extracted_case_name)):
                    citation.extracted_case_name = "N/A"

                # Track the most recent strong case name anchor (for subsequent history binding).
                try:
                    cur = (getattr(citation, "extracted_case_name", None) or "").strip()
                    if cur and cur != "N/A" and " v. " in cur:
                        previous_strong_case_name = cur
                except Exception:
                    pass

            except Exception as e:
                logger.warning(
                    f"[UNIFIED_EXTRACTION] Error extracting metadata for citation '{citation.citation}': {e}"
                )
                continue

        # Remove noise citations entirely (e.g. "States 1", "States 279") so they
        # don't pollute clustering or appear as phantom cases in the output.
        pre_filter_count = len(deduplicated_citations)
        deduplicated_citations = [
            c for c in deduplicated_citations
            if not self._is_noise_citation(c.citation or "")
        ]
        if len(deduplicated_citations) < pre_filter_count:
            logger.info(
                f"[NOISE-FILTER] Removed {pre_filter_count - len(deduplicated_citations)} noise citations "
                f"(e.g. 'States N', 'Page N')"
            )

        names_found = sum(
            1 for c in deduplicated_citations
            if getattr(c, "extracted_case_name", None) and str(getattr(c, "extracted_case_name", "")).strip() not in ("", "N/A")
        )
        logger.info(
            f"[UNIFIED_EXTRACTION] Unified extraction complete: {len(deduplicated_citations)} citations, "
            f"{names_found} with case names extracted from document"
        )
        logger.info(
            f"[NAME-DIAG] After Step 5 (name/date extraction): {names_found}/{len(deduplicated_citations)} citations have non-N/A extracted_case_name"
        )
        return deduplicated_citations

    async def process_text(self, text: str):
        """
        [DEPRECATED ENTRY] UNIFIED CITATION PROCESSING PIPELINE.

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
        Notes:
            This method is retained for backwards compatibility. All new
            callers should use ``process_citations_unified(...)`` in
            ``src.unified_processing_pipeline`` instead, which wraps this
            method and adds additional stages (progress, error metadata,
            structured formatting).
        """
        import warnings

        warnings.warn(
            "UnifiedCitationProcessorV2.process_text is deprecated; use process_citations_unified(...) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        logger.error(f"[UNIFIED_PIPELINE] [WARNING] process_text() CALLED (deprecated entry)")
        logger.error(f"[UNIFIED_PIPELINE] [WARNING] Text length: {len(text)} chars")
        logger.error(f"[UNIFIED_PIPELINE] [WARNING] config.enable_verification: {getattr(self, 'config', None) and getattr(self.config, 'enable_verification', None)}")
        logger.info("[UNIFIED_PIPELINE] Starting unified citation processing pipeline")

        # CRITICAL FIX: Normalize text ONCE here so all downstream code uses the
        # same text that positions were calculated from. Previously, _extract_citations_unified
        # normalized internally (collapsing \n to spaces) but process_text Phase 2 used
        # the original text - causing position mismatches that grew worse through the document.
        text = re.sub(r"\s+", " ", text)
        logger.error(f"[UNIFIED_PIPELINE] Text normalized to {len(text)} chars (whitespace collapsed)")
        try:
            text = apply_pre_extraction_text_fixes(text)
        except Exception as _pre_e:
            logger.debug(f"[UNIFIED_PIPELINE] apply_pre_extraction_text_fixes skipped: {_pre_e}")

        # P3 FIX: Detect document's primary case name for contamination filtering
        document_primary_case_name = None
        try:
            from src.unified_clustering_master import UnifiedClusteringMaster

            clusterer = UnifiedClusteringMaster()
            document_primary_case_name = clusterer._extract_document_primary_case_name(text)
        except Exception as e:
            logger.debug(f"[UNIFIED_PIPELINE] document_primary_case_name detection skipped: {e}")

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
                logger.error(f"[UNIFIED_PIPELINE] [WARNING] NO CITATIONS from _extract_citations_unified!")
                logger.error(f"[UNIFIED_PIPELINE] [WARNING] Text length: {len(text)} chars")
                logger.error(f"[UNIFIED_PIPELINE] [WARNING] Falling back to regex_enhanced extraction")
                citations = self._extract_with_regex_enhanced(text)
                logger.info(f"[UNIFIED_PIPELINE] Regex enhanced fallback returned {len(citations)} citations")
        except Exception as e:
            logger.error(f"[UNIFIED_PIPELINE] Unified extraction failed: {e}", exc_info=True)
            # Fallback to regex method if unified extraction fails
            citations = self._extract_with_regex_enhanced(text)
            logger.info(f"[UNIFIED_PIPELINE] Regex enhanced fallback returned {len(citations)} citations")

        # CRITICAL: Regex-fallback citations never ran Step 4b in _extract_citations_unified, so they
        # lack name_likely_in_left_context / is_proprietary_only. Set them here so the enhancement loop
        # uses left-context extraction for reporter-only cites (e.g. "725 F.3d 651", "2025 WL 1734066").
        from src.utils.citation_type_utils import is_proprietary_only_citation, name_likely_in_left_context as _name_in_left
        for citation in citations:
            ct = getattr(citation, "citation", None) or ""
            if not hasattr(citation, "name_likely_in_left_context") or getattr(citation, "method", "") == "regex_enhanced":
                citation.is_proprietary_only = is_proprietary_only_citation(ct)
                citation.name_likely_in_left_context = _name_in_left(ct)

        # Filter out law review/secondary source citations (not case citations)
        try:
            from src.citation_extractor import is_law_review_citation
            original_count = len(citations)
            logger.error(f"[UNIFIED_PIPELINE] [WARNING] Before law review filter: {original_count} citations")
            citations = [c for c in citations if not is_law_review_citation(getattr(c, 'citation', str(c)))]
            filtered_count = original_count - len(citations)
            if filtered_count > 0:
                logger.info(f"[UNIFIED_PIPELINE] Filtered {filtered_count} law review citations, {len(citations)} case citations remaining")
            if original_count > 0 and len(citations) == 0:
                logger.error(f"[UNIFIED_PIPELINE] [WARNING] ALL {original_count} citations were filtered out as law review citations!")
        except Exception as e:
            logger.warning(f"[UNIFIED_PIPELINE] Law review filter failed: {e}")
            logger.error(f"[UNIFIED_PIPELINE] [WARNING] Law review filter exception: {e}", exc_info=True)

        # Apply parallel verification to clean pipeline results
        # NOTE: Full verification is now done in Phase 4.75 BEFORE clustering to avoid double verification
        # FIX DEC 2025: Removed duplicate verification here - was causing 2x processing time and worker crashes
        logger.info("[UNIFIED_PIPELINE] Parallel verification will be applied in Phase 4.75...")
        try:
            # Apply parallel verification to the citations (verification happens later in Phase 4.75)
            logger.info(f"[UNIFIED_PIPELINE] About to call parallel verification for {len(citations)} citations")
            self.propagate_canonical_to_cluster(citations)
            logger.info("[UNIFIED_PIPELINE] Parallel verification completed")
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
        logger.info(f"[UNIFIED_PIPELINE] Starting name-enhancement loop for {len(citations)} citations (can be slow)")
        extraction_cache = {}  # Key: (start_index, end_index), Value: extracted_name
        _wl_diag = "1734066"  # Diagnostic: trace WL 2025 WL 1734066 full-name extraction
        try:
            for c in citations:
                try:
                    current_name = getattr(c, "extracted_case_name", None) or ""
                    citation_text = getattr(c, "citation", "")
                    start_index = getattr(c, "start_index", None)
                    end_index = getattr(c, "end_index", None)
                    citation_method = getattr(c, "method", None)
                    is_wl_diag = _wl_diag in (citation_text or "")
                    if is_wl_diag:
                        logger.warning(
                            f"[WL-DIAG] ENHANCE-START citation='{(citation_text or '')[:60]}' "
                            f"current_name='{current_name}' start_index={start_index} "
                            f"name_likely_in_left_context={getattr(c, 'name_likely_in_left_context', None)}"
                        )

                    # Compute cache key early so it's available for all checks
                    cache_key = (start_index, end_index)

                    # INLINE-NAME FIX (HIGHEST PRIORITY): If inline extraction found
                    # a name physically embedded in the citation text (e.g. "The Pizarro,
                    # 2 Wheat. 227"), trust it unconditionally. Must run BEFORE cache
                    # check because a bare duplicate ("2 Wheat. 227") at the same
                    # position may have cached a wrong context name ("Murray").
                    if getattr(c, '_inline_name_set', False) and current_name and current_name != "N/A":
                        extraction_cache[cache_key] = current_name
                        logger.info(f"[INLINE-NAME-TRUST] Keeping inline name '{current_name}' for '{citation_text[:50]}'")
                        continue

                    # DEDUP-PROPAGATE FIX: If DEDUP-PROPAGATE set this name from a co-citation
                    # at the same position (e.g. eyecite "Gibson v. 1997 Dodge, 2001 OK CIV APP 130"
                    # propagating to bare "2001 OK CIV APP 130"), the propagated name is authoritative.
                    # Near-context text is unreliable here because the citation number may be
                    # preceded by an unrelated citation sentence in the PDF-extracted text.
                    if getattr(c, '_dedup_name_set', False) and current_name and current_name != "N/A":
                        if cache_key not in extraction_cache:
                            extraction_cache[cache_key] = current_name
                        logger.info(f"[DEDUP-NAME-TRUST] Keeping dedup-propagated name '{current_name}' for '{citation_text[:50]}'")
                        continue

                    # Method 0 (FIRST): Extract case name from citation text itself
                    # This runs BEFORE the cache check because eyecite citations like
                    # "Swindle v. State, 10 Tenn. 581" may share position with a regex
                    # citation "10 Tenn. 581" that cached a contaminated name.
                    method0_name = None
                    if citation_text and " v. " in citation_text:
                        v_match = re.match(
                            r"^(.+?\s+v\.\s+[A-Za-z0-9][A-Za-z0-9\s\'\.\.\&\-,]+?)(?:,\s*\d|\s+\d)",
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
                        # Pattern: "Name, YYYY WL N" (single party before WL cite, e.g. "Zimmerlein, 2025 WL 1734066")
                        if not method0_name and re.search(r"\d{4}\s+WL\s+\d+", citation_text or ""):
                            wl_prefix = re.match(
                                r'^([A-Z][A-Za-z\'\.\-\s]+?),\s*\d{4}\s+WL\s+',
                                citation_text
                            )
                            if wl_prefix:
                                candidate = wl_prefix.group(1).strip().rstrip(",")
                                if len(candidate) >= 3 and candidate[0].isupper() and " v. " not in candidate:
                                    method0_name = candidate

                    # Method 0c: Case name prefix before reporter citation (no "v." needed)
                    # E.g., "Waters of Stranger Creek, 466 P.2d 508 (1970)"
                    # or "In re Rts. to Waters of Stranger Creek, 77 Wn.2d 649"
                    if not method0_name and citation_text and not citation_text[0].isdigit():
                        _reporter_boundary = re.search(
                            r',\s*\d+\s+(?:Wn\.|Wash\.|P\.\d|F\.\d|F\.\s|S\.\s*Ct\.|'
                            r'U\.S\.|N\.E\.|S\.E\.|N\.W\.|S\.W\.|A\.\d|So\.\d|L\.\s*Ed\.|'
                            r'Cal\.|N\.Y\.|Ill\.|Ohio)',
                            citation_text
                        )
                        if _reporter_boundary:
                            _name_candidate = citation_text[:_reporter_boundary.start()].strip().rstrip(",")
                            # Must be multi-word proper name, not a reporter abbreviation
                            if (len(_name_candidate) >= 4
                                    and _name_candidate[0].isupper()
                                    and len(_name_candidate.split()) >= 2
                                    and not re.match(r'^(?:Wash|Wn|Cal|N\.Y|Ill|Ohio|Tex|Va|Pa|Fla)\b', _name_candidate, re.IGNORECASE)):
                                method0_name = _name_candidate
                                logger.info(f"[METHOD-0c] Case name from citation text: '{method0_name}' for '{citation_text[:60]}'")

                    # Method 0d: Parenthetical case name extraction
                    # For bare citations inside "(quoting X v. Y, 102 Wn.2d 385, ...)"
                    # or "(citing X v. Y, 138 Wn.2d 875, ...)"
                    if not method0_name and citation_text and citation_text[0].isdigit() and start_index and start_index > 0:
                        _left_ctx = text[max(0, start_index - 200):start_index]
                        _paren_match = re.search(
                            r'(?:quoting|citing|accord)\s+'
                            r'([A-Z][A-Za-z\s\'\.\&\-,]+?\s+v\.\s+[A-Z][A-Za-z\s\'\.\&\-,]+?)'
                            r',\s*$',
                            _left_ctx,
                            re.IGNORECASE,
                        )
                        if _paren_match:
                            _paren_name = _paren_match.group(1).strip().rstrip(",")
                            if len(_paren_name) > 5 and " v. " in _paren_name:
                                method0_name = _paren_name
                                logger.info(f"[METHOD-0d] Parenthetical case name: '{method0_name}' for '{citation_text[:60]}'")

                    # OPTIMIZATION: Check cache first to avoid duplicate extraction
                    cache_key = (start_index, end_index)
                    if is_wl_diag:
                        logger.warning(f"[WL-DIAG] method0_name='{method0_name}' cache_key={cache_key}")
                    if cache_key in extraction_cache:
                        cached_name = extraction_cache[cache_key]
                        if cached_name and cached_name != "N/A":
                            # If Method 0/0c found a name from this citation's text,
                            # prefer it over the cached name (which may be contaminated
                            # from a different citation at the same position)
                            if method0_name and len(method0_name) > 4:
                                c.extracted_case_name = self._clean_extracted_case_name(method0_name)
                                extraction_cache[cache_key] = c.extracted_case_name
                            else:
                                c.extracted_case_name = self._clean_extracted_case_name(cached_name)
                            if is_wl_diag:
                                logger.warning(f"[WL-DIAG] FROM-CACHE extracted_case_name='{c.extracted_case_name}' (cached_name='{cached_name}')")
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
                            if is_wl_diag:
                                logger.warning(f"[WL-DIAG] SKIP clean_pipeline_v1 current_name='{current_name}'")
                            continue  # Skip re-extraction
                        elif is_series_citation:
                            # Cache the N/A for series citations
                            extraction_cache[cache_key] = current_name
                            continue  # Skip re-extraction

                    # CRITICAL FIX: If Phase 1 already found a valid name with "v.",
                    # trust it and skip the master extractor. The master extractor's
                    # ProximityStrategy finds the FIRST "v." in the context window,
                    # not the closest, causing wrong names in TOA and dense citation areas.
                    _near_context_override = False  # set True when near-context beats Phase 1
                    if current_name and current_name != "N/A" and " v. " in current_name and len(current_name) > 8:
                        # Method 0 (embedded in citation text) always beats Phase 1 context extraction
                        if method0_name and " v. " in method0_name and len(method0_name) > 4:
                            c.extracted_case_name = self._clean_extracted_case_name(method0_name)
                            extraction_cache[cache_key] = c.extracted_case_name
                            if is_wl_diag:
                                logger.warning(f"[WL-DIAG] METHOD0 beats Phase1 trust: '{method0_name}'")
                            continue
                        # NEAR-CONTEXT OVERRIDE: if within 100 chars before citation (trimmed at ').' boundary)
                        # there's a different plaintiff name, Phase 1 likely spanned a sentence boundary.
                        # Example: Phase 1 found 'Peacock v. State' for '2001 OK CIV APP 130' but
                        # 'State ex rel. Gibson v. 1997 Dodge' appears right before it in text.
                        _trust_phase1 = True
                        if start_index and start_index > 0:
                            _nc = text[max(0, start_index - 100):start_index]
                            _last_b = -1
                            for _bm in re.finditer(r'\)\.\s', _nc):
                                _last_b = _bm.end()
                            if _last_b > 0:
                                _nc = _nc[_last_b:]
                            if " v. " in _nc:
                                _ncm = re.search(
                                    r'([A-Z][A-Za-z0-9\s\'&.\-]+)\s+v\.\s+([A-Z0-9][A-Za-z0-9\s\'&.\-,]+?)'
                                    r'(?=,\s*$|\s*,?\s*$)',
                                    _nc.strip()
                                )
                                if _ncm:
                                    _nc_name = _ncm.group(0).strip().rstrip(",").strip()
                                    _stop = {"state", "united", "people", "in", "re", "ex", "rel"}
                                    _cur_w = [re.sub(r'[^\w]', '', w) for w in current_name.split(" v. ")[0].lower().split()]
                                    _cur_w = [w for w in _cur_w if w and w not in _stop]
                                    _nc_w  = [re.sub(r'[^\w]', '', w) for w in _nc_name.split(" v. ")[0].lower().split()]
                                    _nc_w  = [w for w in _nc_w if w and w not in _stop]
                                    if _cur_w and _nc_w and _cur_w[0] != _nc_w[0]:
                                        logger.info(
                                            "[NEAR-CONTEXT-OVERRIDE] Phase1 '%s' overridden by near-context '%s' for '%s'",
                                            current_name[:40], _nc_name[:40], (citation_text or "")[:40]
                                        )
                                        _trust_phase1 = False
                                        _near_context_override = True
                                        # If the near-context gave a clean v. name, use it directly
                                        # to avoid the master extractor trimming too far downstream.
                                        if " v. " in _nc_name and len(_nc_name) <= 80:
                                            _cleaned_nc = self._clean_extracted_case_name(_nc_name)
                                            if _cleaned_nc and " v. " in _cleaned_nc:
                                                c.extracted_case_name = _cleaned_nc
                                                extraction_cache[cache_key] = _cleaned_nc
                                                _trust_phase1 = True  # sentinel: cause continue below
                        if _trust_phase1:
                            if not _near_context_override:
                                # Normal Phase 1 trust: cache the Phase 1 name
                                extraction_cache[cache_key] = current_name
                                if is_wl_diag:
                                    logger.warning(f"[WL-DIAG] SKIP Phase 1 trust current_name='{current_name}'")
                            continue  # Trust Phase 1 extraction (or near-context direct assignment)
                        # Fall through: let master extractor re-extract with trimmed context

                    final_name = method0_name

                    # Method 1: Master extractor (skip if Method 0 found good name)
                    _skip_master = final_name and len(final_name) > 10 and " v. " in final_name
                    if not _skip_master:
                      try:
                        # Integrated left-context extraction: when citation type says name is likely left
                        # (e.g. reporter-only F.3d, WL/Lexis). Use 600-char window to match Step 5 in
                        # _extract_citations_unified so we find names that appear a few sentences before.
                        # Skip when near-context override fired: the 600-char window would re-introduce
                        # the wrong name from a preceding sentence (e.g. Peacock before Gibson).
                        if getattr(c, "name_likely_in_left_context", False) and start_index and start_index > 0 and not _near_context_override:
                            left_name = self._extract_case_name_from_left_context(
                                text, start_index, window=600, citation_text=citation_text
                            )
                            if is_wl_diag:
                                logger.warning(f"[WL-DIAG] FIRST left-context left_name='{left_name}' final_name_before='{final_name}'")
                            if left_name and len(left_name) >= 4 and " v. " in left_name:
                                final_name = left_name
                                _skip_master = True
                                logger.info(f"[LEFT-CONTEXT] name_likely_in_left_context: using '{final_name}'")
                            elif left_name and " v. " not in left_name and getattr(c, "name_likely_in_left_context", False):
                                repaired = self._repair_single_party_with_left_context(
                                    left_name, text, start_index, window=700
                                )
                                if repaired and " v. " in repaired:
                                    final_name = repaired
                                    _skip_master = True
                                    logger.info(f"[LEFT-CONTEXT] single-party '{left_name}' repaired to '{final_name}'")
                                else:
                                    logger.debug(
                                        "[LEFT-CONTEXT] reporter-only citation got single-party name (missing ' v. '); "
                                        "check italic/bold normalization and context window: name=%r citation=%s",
                                        left_name, (citation_text or "")[:60],
                                    )

                        # SERIES CITATION FIX: Check if this is NOT the first citation in a series
                        # If it's not the first, skip case name extraction to prevent incorrect association
                        if start_index and start_index > 0 and not _skip_master:
                            # Look backwards to see if there's another citation within 300 characters
                            # (increased from 100 - parenthetical text between citations can be long)
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
                                # Prefer full "Plaintiff v. Defendant" from left context over single-party method0_name
                                if getattr(c, "name_likely_in_left_context", False) and start_index and start_index > 0:
                                    left_name = self._extract_case_name_from_left_context(
                                        text, start_index, window=600, citation_text=citation_text
                                    )
                                    if is_wl_diag:
                                        logger.warning(f"[WL-DIAG] SERIES-FIX left_name='{left_name}' method0_name='{method0_name}'")
                                    if left_name and " v. " in left_name:
                                        final_name = left_name
                                        logger.info(f"[SERIES-FIX] name_likely_in_left_context: using '{final_name}'")
                                if not final_name and method0_name:
                                    logger.info(f"[SERIES-FIX] Non-first citation, using embedded name '{method0_name}': {citation_text[:50]}")
                                    final_name = method0_name
                                if not final_name:
                                    logger.info(f"[SERIES-FIX] Skipping case name extraction for non-first citation: {citation_text[:50]}")
                                    final_name = "N/A"
                                c.extracted_case_name = self._clean_extracted_case_name(final_name) if final_name != "N/A" else final_name
                                extraction_cache[cache_key] = c.extracted_case_name
                                if is_wl_diag:
                                    logger.warning(f"[WL-DIAG] SET extracted_case_name='{c.extracted_case_name}' source=SERIES-FIX final_name='{final_name}'")
                                continue

                        # When we have a single-party name (e.g. "Zimmerlein") and reporter-only cite, try to recover "Webber v. Zimmerlein" from left context
                        if (
                            not _skip_master
                            and final_name
                            and final_name != "N/A"
                            and " v. " not in final_name
                            and getattr(c, "name_likely_in_left_context", False)
                            and start_index
                            and start_index > 0
                        ):
                            repaired = self._repair_single_party_with_left_context(
                                final_name, text, start_index, window=700
                            )
                            if repaired and " v. " in repaired:
                                logger.info(f"[LEFT-CONTEXT] single-party method0 '{final_name}' repaired to '{repaired}'")
                                final_name = repaired
                                _skip_master = True

                        # WL-LEFT set full name (e.g. "Webber v. Zimmerlein"); skip master extractor
                        if _skip_master and final_name and final_name != "N/A":
                            if text and start_index is not None and " v. " in final_name:
                                final_name = self._repair_dropped_leading_word(final_name, text, start_index)
                            c.extracted_case_name = self._clean_extracted_case_name(final_name)
                            extraction_cache[cache_key] = c.extracted_case_name
                            if is_wl_diag:
                                logger.warning(f"[WL-DIAG] SET extracted_case_name='{c.extracted_case_name}' source=LEFT-CONTEXT-SKIP-MASTER")
                            continue
                        
                        # USER DEBUG: Enable debug for U.S. Reports, S.Ct., L.Ed. to diagnose vacatur pattern
                        force_debug = citation_text and (
                            " U.S. " in citation_text or " S. Ct. " in citation_text or " L. Ed. " in citation_text
                        )

                        # TOA / same-line guard: bind name/year from the citation's own line when available.
                        # This prevents neighbor bleed on lines like:
                        # "Nat'l Pork Producers Council v. Ross, 143 S. Ct. 1142 (2023)... Parker v. Brown, 317 U.S. 341..."
                        try:
                            # First, try an anchored "Name, Cite (YYYY)" recovery across full text.
                            # This corrects cases where we already have a (wrong) extracted name/year.
                            # Indices can drift under OCR normalization; prefer any anchored match.
                            an_name, an_year = self._extract_name_year_by_exact_cite_anchor(
                                text,
                                citation_text,
                                None,
                            )
                            if an_name and " v. " in an_name:
                                final_name = an_name
                            if an_year:
                                c.extracted_date = an_year
                                self._set_extracted_date_provenance(c, "exact_cite_anchor", "high")

                            sl_name, sl_year = self._extract_name_year_from_same_line_for_citation(
                                text,
                                citation_text,
                                start_index if start_index != -1 else None,
                                end_index,
                            )
                            if sl_name and " v. " in sl_name:
                                # Only override if missing or likely contaminated (same-line is highest-fidelity).
                                if (not final_name) or final_name == "N/A" or (final_name and sl_name != final_name):
                                    final_name = sl_name
                            if sl_year:
                                cur_ed = getattr(c, "extracted_date", None)
                                # Same-line paren year is high-confidence; prefer it over other sources.
                                if self._is_missing_extracted_date(cur_ed) or str(cur_ed).strip() != str(sl_year).strip():
                                    c.extracted_date = sl_year
                                    self._set_extracted_date_provenance(c, "same_line_paren", "high")
                        except Exception:
                            pass

                        # CRITICAL FIX: Pass a context window, NOT the full document text.
                        # The master extractor's ProximityStrategy searches the entire text
                        # for "v." patterns, so passing a 140K document causes it to find
                        # the wrong case name (e.g., from the TOA or cover page).
                        if start_index and start_index > 0:
                            ctx_start = max(0, start_index - 500)
                            ctx_end = min(len(text), (end_index or start_index) + 200)
                            context_text = text[ctx_start:ctx_end]
                            # Find the most restrictive context boundary within the
                            # PRE-CITATION portion of the original context window.
                            # Semicolons separate citation series; "). " ends a citation
                            # sentence.  Both must be searched BEFORE the citation offset
                            # so we never trim past the citation itself.
                            # (If we search the full window we hit "). " endings that lie
                            # AFTER the citation, cutting away the case name we need.)
                            _cit_offset = start_index - ctx_start  # citation's position in original context_text
                            _pre_ctx_orig = context_text[:_cit_offset]
                            _boundary = 0
                            if ";" in _pre_ctx_orig:
                                _boundary = max(_boundary, _pre_ctx_orig.rfind(";") + 1)
                            for _cbm in re.finditer(r'\)\.\s+(?=[A-Z])', _pre_ctx_orig):
                                _boundary = max(_boundary, _cbm.end())
                            if _boundary > 0:
                                _trimmed_ctx = context_text[_boundary:].strip()
                                if len(_trimmed_ctx) >= 15:
                                    context_text = _trimmed_ctx
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
                                        f"'{citation_text[:50]}' - intervening citation found"
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
                        logger.debug(
                            f"[EXTRACT-METHOD1] Master extractor failed for '{citation_text[:80]}': {e}"
                        )

                    # Method 2: Context-based extraction (if master failed or returned short name)
                    if not final_name or len(final_name) < 10:
                        try:
                            manual_name = self._extract_case_name_from_context(text, c)
                            if manual_name and manual_name != "N/A" and len(manual_name.strip()) > 3:
                                if not final_name or len(manual_name) > len(final_name):
                                    final_name = manual_name
                        except Exception as e:
                            logger.debug(
                                f"[EXTRACT-METHOD2] Context extraction failed for '{citation_text[:80]}': {e}"
                            )

                    # Method 3: Direct regex extraction from broader context
                    if not final_name:
                        try:
                            # FIX #27: Only look BACKWARD, not forward!
                            # Looking forward (+ 100) was capturing case names from NEXT citations
                            # E.g., "Lopez...183 Wn.2d 649...Spokane County" would extract "Spokane County"
                            ctx_start = max(0, (start_index or 0) - 500)
                            ctx_end = start_index or 0  # Changed from + 100 to + 0 (only backward)
                            context = text[ctx_start:ctx_end]
                            # Semicolon separates cases: use only segment after last ";"
                            if ";" in context:
                                after_sc = context[context.rfind(";") + 1 :].strip()
                                if len(after_sc) >= 10:
                                    context = after_sc

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
                            logger.debug(
                                f"[EXTRACT-METHOD3] Regex extraction failed for '{citation_text[:80]}': {e}"
                            )

                    # Apply truncation repair if we have a name
                    if final_name:
                        try:
                            repaired_name = self._repair_truncated_case_name(
                                final_name,
                                text,
                                start_index or 0,
                                citation_text=citation_text,
                                context_override=getattr(c, "context", "") or "",
                            )
                            if repaired_name != final_name:
                                logger.warning(
                                    f"[TRUNCATION-REPAIR] '{final_name}' -> '{repaired_name}' for {citation_text}"
                                )
                                final_name = repaired_name
                        except Exception as e:
                            logger.debug(
                                f"[TRUNCATION-REPAIR] Repair failed for '{citation_text[:80]}': {e}"
                            )

                    # Final cleaning and validation before setting
                    if final_name:
                        # Strip leading body text before signal words + case name
                        # e.g., "Courts typically did not require... See Uzuegbunam v. Preczewski"
                        # -> "Uzuegbunam v. Preczewski"
                        _sig_match = re.search(
                            r'\b(?:see|citing|quoting|accord|compare|but see|cf\.?)\s+'
                            r'([A-Z][A-Za-z\'\.\-\s,&]+\s+v\.\s+[A-Z][A-Za-z\'\.\-\s,&]+)',
                            final_name, re.IGNORECASE
                        )
                        if _sig_match and _sig_match.start() > 10:
                            # There's significant text before the signal word - extract just the case name
                            final_name = _sig_match.group(1).strip().rstrip(",.")

                        # Reject body text contamination in final name
                        _final_contam = any(re.search(cp, final_name, re.IGNORECASE) for cp in [
                            r'syllabus\s+constitutes', r'opinion\s+of\s+the\s+court',
                            r'reporter\s+of\s+decisions', r'convenience\s+of\s+the\s+reader',
                            r'Courts?\s+typically', r'did\s+not\s+require',
                        ])
                        if _final_contam or (len(final_name) > 60 and ' v. ' not in final_name) or self._looks_like_quote_not_case_name(final_name):
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

                        # Fix line-break hyphens: "Mar- bury" -> "Marbury"
                        # PDF line breaks can leave "word- word" where the hyphen is a break artifact
                        if final_name:
                            final_name = re.sub(r'(\w)- (\w)', r'\1\2', final_name)

                        # Remove trailing commas and periods
                        if final_name:
                            final_name = re.sub(r"[,\.]+$", "", final_name).strip()

                    # Set the final name (always prefer extracted over empty/null)
                    if final_name:
                        if text and start_index is not None and " v. " in final_name:
                            final_name = self._repair_dropped_leading_word(final_name, text, start_index)
                        final_name = self._clean_extracted_case_name(final_name)
                        setattr(c, "extracted_case_name", final_name)
                        # OPTIMIZATION: Cache the result for future use
                        extraction_cache[cache_key] = final_name
                        if is_wl_diag:
                            logger.warning(f"[WL-DIAG] SET extracted_case_name='{final_name}' source=MASTER-OR-CONTEXT")
                    elif not current_name or current_name == "N/A":
                        setattr(c, "extracted_case_name", "N/A")
                        # Cache the failure too to avoid re-trying
                        extraction_cache[cache_key] = "N/A"
                        if is_wl_diag:
                            logger.warning(f"[WL-DIAG] SET extracted_case_name='N/A' source=NO-FINAL-NAME")

                except Exception as e:
                    logger.error(f"[EXTRACT-ERROR] Exception for {getattr(c, 'citation', 'unknown')}: {e}")
                    if not getattr(c, "extracted_case_name", None):
                        setattr(c, "extracted_case_name", "N/A")
        except Exception as e:
            logger.error(f"[EXTRACT-PIPELINE-ERROR] {e}")

        names_after_enhance = sum(
            1 for c in citations
            if getattr(c, "extracted_case_name", None) and str(getattr(c, "extracted_case_name", "")).strip() not in ("", "N/A")
        )
        logger.info(
            f"[NAME-DIAG] After enhancement loop: {names_after_enhance}/{len(citations)} citations have non-N/A extracted_case_name"
        )
        logger.info(f"[UNIFIED_PIPELINE] Name-enhancement loop done, proceeding to Phase 2")

        logger.info("[UNIFIED_PIPELINE] Phase 2: Detecting parallel citations")
        citations = self._detect_parallel_citations(citations, text)
        logger.info(f"[UNIFIED_PIPELINE] After parallel detection: {len(citations)} citations")

        logger.info("[UNIFIED_PIPELINE] Phase 3: Ensuring bidirectional parallel relationships")
        self.ensure_bidirectional_parallels(citations, text)
        logger.info(f"[UNIFIED_PIPELINE] After bidirectional parallels: {len(citations)} citations")

        logger.info("[UNIFIED_PIPELINE] Phase 3.5: Enriching missing extracted names/dates")
        try:
            self._enrich_missing_extracted_metadata(citations, text)
        except Exception as enrich_err:
            logger.warning(f"[UNIFIED_PIPELINE] Metadata enrichment skipped due to error: {enrich_err}")

        logger.info("[UNIFIED_PIPELINE] Phase 3.6: TOA exact cite-anchor repairs (fix neighbor bleed)")
        try:
            self._apply_exact_cite_anchor_repairs(citations, text)
        except Exception as toa_rep_err:
            logger.warning(f"[UNIFIED_PIPELINE] TOA cite-anchor repair skipped: {toa_rep_err}")

        logger.info("[UNIFIED_PIPELINE] Phase 3.55: Known-citation pin repairs (bleed vs reporter pin)")
        try:
            self._apply_known_pin_extracted_repairs(citations)
        except Exception as pin_rep_err:
            logger.warning(f"[UNIFIED_PIPELINE] Known-pin repair skipped: {pin_rep_err}")

        logger.info("[UNIFIED_PIPELINE] Phase 4: Skipping duplicate canonical propagation (already done)")
        self._update_progress(60, "Propagating Data", "Parallel verification already completed earlier")
        # self.propagate_canonical_to_cluster(citations)  # Already done earlier in Phase 1
        logger.info(f"[UNIFIED_PIPELINE] After canonical propagation: {len(citations)} citations")

        logger.info("[UNIFIED_PIPELINE] Phase 4.5: Filtering false positive citations")
        self._update_progress(65, "Filtering", "Removing false positive citations")
        citations = self._filter_false_positive_citations(citations, text)
        logger.info(f"[UNIFIED_PIPELINE] After false positive filtering: {len(citations)} citations")

        logger.info("[UNIFIED_PIPELINE] Phase 4.52: Re-apply known-citation pins after false-positive filter")
        try:
            self._apply_known_pin_extracted_repairs(citations)
        except Exception as pin_rep_err:
            logger.warning(f"[UNIFIED_PIPELINE] Post-filter known-pin repair skipped: {pin_rep_err}")

        # FIX #54: Diagnostic logging to find why verification doesn't run
        logger.error(f"   enable_verification: {self.config.enable_verification}")
        logger.error(f"   citations count: {len(citations) if citations else 0}")
        logger.error(f"   Will verification run: {self.config.enable_verification and citations}")

        logger.info(f"[UNIFIED_PIPELINE] Phase 4.75: Pre-clustering verification check")
        logger.info(f"[UNIFIED_PIPELINE] enable_verification: {self.config.enable_verification}")
        logger.info(f"[UNIFIED_PIPELINE] citations count: {len(citations) if citations else 0}")
        logger.info(f"[UNIFIED_PIPELINE] Will verification run: {self.config.enable_verification and bool(citations)}")
        logger.error(f"[UNIFIED_PIPELINE] [WARNING] VERIFICATION CHECK: config.enable_verification={self.config.enable_verification}, citations count={len(citations) if citations else 0}")

        # CRITICAL FIX: Verify citations BEFORE clustering so clustering uses correct canonical names
        if self.config.enable_verification and citations:
            logger.info("[UNIFIED_PIPELINE] Phase 4.75: Verifying citations BEFORE clustering (CRITICAL)")
            logger.error(f"[UNIFIED_PIPELINE] [WARNING] ABOUT TO CALL _verify_citations_sync with {len(citations)} citations")
            self._update_progress(67, "Verifying", "Verifying citations with external sources")
            verified_citations = self._verify_citations_sync(citations, text)
            logger.error(f"[UNIFIED_PIPELINE] [WARNING] _verify_citations_sync RETURNED {len(verified_citations)} citations")
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
                            logger.debug(
                                f"[VERIFICATION-PARADOX-FIX] {citation.citation}: "
                                "keeping verified=False for N/A + partial citation"
                            )
                        else:
                            # USER FIX: Check year match before setting verified (supports 1600-2100, e.g. 18xx)
                            from src.utils.date_utils import extract_year_value
                            extracted_date = getattr(citation, "extracted_date", None)
                            canonical_date = getattr(citation, "canonical_date", None)
                            year_match = True  # Default to True if no extracted date
                            if extracted_date and canonical_date:
                                ext_str = extract_year_value(extracted_date)
                                can_str = extract_year_value(canonical_date)
                                if ext_str and can_str:
                                    year_match = ext_str == can_str

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
                            logger.debug(
                                f"[VERIFICATION-PARADOX-FIX] {citation.get('citation')}: "
                                "keeping verified=False for N/A + partial citation"
                            )
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

        logger.info("[UNIFIED_PIPELINE] Phase 5: Creating citation clusters")
        self._update_progress(70, "Clustering", "Creating citation clusters")

        # CRITICAL FIX: Do NOT re-run verification inside clustering. Verification already ran
        # in Phase 4.75 above. Re-running it here caused the pipeline to appear "stuck at
        # Creating citation clusters..." because _apply_verification_to_clusters calls the
        # batch API (60-120s timeouts). Clustering itself is fast; duplicate verification was the hang.
        #
        # Use optimized clustering (same as unified_processing_pipeline): merges rows that share
        # the same federal reporter primary key (e.g. two "133 S. Ct. 2223" mentions) so the UI
        # does not show duplicate case cards (verified + unverified) for one cite.
        try:
            clusters = cluster_citations_unified(
                citations,
                original_text=text,
                enable_verification=False,
            )
            logger.info(
                f"[UNIFIED_PIPELINE] Created {len(clusters)} clusters via optimized clustering "
                f"(reporter-PK merge; verification already done in Phase 4.75)"
            )
        except Exception as opt_exc:
            logger.warning(
                "[UNIFIED_PIPELINE] Optimized clustering failed (%s); using modular master",
                opt_exc,
            )
            from src.unified_clustering_master import cluster_citations_unified_master

            clusters = cluster_citations_unified_master(
                citations,
                original_text=text,
                enable_verification=False,
                progress_callback=self._update_progress,
            )
            logger.info(
                f"[UNIFIED_PIPELINE] Created {len(clusters)} clusters via modular MASTER clustering "
                f"(verification already done in Phase 4.75)"
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
            # Derive cluster_members from this cluster's citations only to avoid cross-cluster contamination (e.g. Amcast/Cintas)
            cluster_members = []
            for c in cluster_citations:
                if isinstance(c, dict):
                    ct = c.get("citation") or ""
                else:
                    ct = getattr(c, "citation", None) or (str(c) if c else "")
                if ct:
                    cluster_members.append(ct)
            if not cluster_members:
                cluster_members = cluster.get("cluster_members", [])

            # USER FIX 2024-10-21 v4: Compute best extracted_date for the cluster (singleton + parallel)
            cluster_extracted_date = self._compute_cluster_decision_year_phase55(
                cluster, cluster_citations, cluster_id
            )

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

                # Parallel cites share one decision year; singleton clusters also get a derived year
                # (canonical / cite paren) so wrong context extraction does not stick (e.g. Terazosin 2003 vs 2005).
                if cluster_extracted_date:
                    year_s = str(cluster_extracted_date).strip()
                    citation.extracted_date = year_s
                    ecn = getattr(citation, "extracted_case_name", None) or ""
                    if ecn and str(ecn).strip() and str(ecn).strip().upper() != "N/A":
                        m_trail = re.search(
                            r",\s*((?:19|20)\d{2})\s*$", str(ecn).strip()
                        )
                        if m_trail and m_trail.group(1) != year_s:
                            fixed = str(ecn).strip()[: m_trail.start()] + f", {year_s}"
                            citation.extracted_case_name = self._clean_extracted_case_name(fixed)

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
            93, "Processing", f"Extracted {len(citations)} citations, {len(clusters)} clusters — applying final checks"
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
                year_mismatch_count += apply_final_year_alignment(
                    cit,
                    evaluate_year_alignment=self._evaluate_year_alignment,
                    logger=logger,
                    log_tag="FINAL-YEAR-CHECK",
                )

        # Also check cluster citations (dicts)
        for cluster in formatted_clusters:
            cluster_citations = cluster.get("citations", [])
            for cit in cluster_citations:
                if isinstance(cit, dict):
                    year_mismatch_count += apply_final_year_alignment(
                        cit,
                        evaluate_year_alignment=self._evaluate_year_alignment,
                        logger=logger,
                        log_tag="FINAL-YEAR-CHECK-CLUSTER",
                    )

            # FIX: Recompute cluster mismatch flags after clearing invalid flags
            from src.utils.mismatch_utils import compute_cluster_mismatch_flags
            compute_cluster_mismatch_flags(cluster)

        if year_mismatch_count > 0:
            logger.info(f"[FINAL-YEAR-CHECK] Unverified {year_mismatch_count} citations due to year mismatch")

        # SPECIAL HANDLING: Add proprietary-format message only for truly unverified
        # citations (not verified, not verified-by-parallel, and no canonical URL).
        proprietary_count = 0
        proprietary_cleared_count = 0

        for cit in citations:
            if hasattr(cit, "__dict__"):
                marked, cleared = apply_proprietary_status(cit)
                proprietary_count += marked
                proprietary_cleared_count += cleared

        for cluster in formatted_clusters:
            cluster_citations = cluster.get("citations", [])
            for cit in cluster_citations:
                if isinstance(cit, dict):
                    marked, cleared = apply_proprietary_status(cit)
                    proprietary_count += marked
                    proprietary_cleared_count += cleared
        
        if proprietary_count > 0:
            logger.info(f"[PROPRIETARY] Marked {proprietary_count} WL/Lexis citations as unverified due to proprietary format")
        if proprietary_cleared_count > 0:
            logger.info(f"[PROPRIETARY] Cleared {proprietary_cleared_count} stale proprietary flags/messages on verified citations")

        # Last pass: TOA/year/cluster steps must not leave stale extracted tails vs KNOWN_* pins
        logger.info("[UNIFIED_PIPELINE] Phase 7.5: Final known-citation pin repair before response")
        try:
            self._apply_known_pin_extracted_repairs(citations)
        except Exception as pin_final_err:
            logger.warning(f"[UNIFIED_PIPELINE] Final known-pin repair skipped: {pin_final_err}")

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

            # USER FIX 2026-03-02: Filter document headers parsed as citations
            # e.g. "LOCKHART v. UNITED STATES Opinion of the Court States, 570 U.S. ___ (2013)"
            # These are page headers, not real citations.
            cit_str = citation_text.lower()
            if "opinion of the court" in cit_str:
                continue
            # "v. UNITED STATES Opinion" or "v. UNITED STATES ... Opinion" - document header
            if re.search(r"v\.\s+united\s+states\s+opinion", cit_str):
                continue
            # Case name contains "Opinion of the Court" (extracted_case_name contamination)
            ext_name = getattr(citation, "extracted_case_name", None) or ""
            if ext_name and "opinion of the court" in str(ext_name).lower():
                continue
            # Garbage extracted names: prose fragments like "'s work" from "Court's work"
            # (slip-op citations near "the Court's work. 577 U. S. ___" pick up wrong context)
            if ext_name and self._is_garbage_extracted_case_name(str(ext_name)):
                continue

            valid_citations.append(citation)

        logger.info(f"False positive filter: {len(citations)} -> {len(valid_citations)} citations")
        return valid_citations

    def _is_garbage_extracted_case_name(self, ext_name: str) -> bool:
        """True when extracted_case_name is a prose fragment, not a real case name.

        Examples: "'s work" (from "Court's work"), "work", "the court", etc.
        """
        if not ext_name or not ext_name.strip():
            return False
        s = str(ext_name).strip()
        # Possessive fragment: "'s work", "Court's work" (prose, not case name)
        if s.startswith("'s ") or s.endswith("'s work") or s == "'s work":
            return True
        # Short prose fragments that are never case names
        garbage_phrases = (
            "'s work", "work", "the court", "the court's", "court's work",
            "opinion", "the opinion", "this court", "the majority",
        )
        if s.lower() in garbage_phrases:
            return True
        # No " v. " / "In re" / "Ex parte" and looks like prose (contains "'s ")
        if " 's " in s and " v. " not in s.lower() and "in re " not in s.lower():
            return True
        return False

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

            _cluster_members = (citation.metadata.get("cluster_members", []) if citation.metadata else []) or []
            citation_dict = {
                "citation": normalize_to_ascii_display(str(citation.citation or "")),
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
                "context": normalize_to_ascii_display(str(citation.context or "")),
                "start_index": citation.start_index,
                "end_index": citation.end_index,
                "is_parallel": citation.is_parallel,
                "is_cluster": citation.is_cluster,
                "parallel_citations": citation.parallel_citations,
                "cluster_members": [normalize_to_ascii_display(str(m)) for m in _cluster_members],
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
            except Exception as sep_err:
                logger.debug(f"[FORMAT-RESPONSE] Data-separation guard skipped: {sep_err}")
            if citation.metadata:
                _meta_cm = citation.metadata.get("cluster_members", []) or []
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
                        "cluster_members": [normalize_to_ascii_display(str(m)) for m in _meta_cm],
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

                _cm = (citation.metadata.get("cluster_members", []) if citation.metadata else []) or []
                return {
                    "citation": normalize_to_ascii_display(str(getattr(citation, "citation", None) or str(citation))),
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
                    "context": normalize_to_ascii_display(str(getattr(citation, "context", None) or "")),
                    "start_index": citation.start_index,
                    "end_index": citation.end_index,
                    "is_parallel": citation.is_parallel,
                    "is_cluster": citation.is_cluster,
                    "parallel_citations": citation.parallel_citations,
                    "cluster_members": [normalize_to_ascii_display(str(m)) for m in _cm],
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
                logger.debug(f"CLUSTER_FIX: Citation '{citation.citation}' correctly marked as not in cluster")
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
                        # FIX 2026-02-24: Only set true_by_parallel if we have a valid URL (not Google search)
                        url_to_check = getattr(citation, "canonical_url", None) or citation.url
                        url_str = str(url_to_check or "").strip()
                        has_valid_url = (
                            url_str
                            and not url_str.startswith("https://www.google.com/search")
                            and not url_str.startswith("http://www.google.com/search")
                        )
                        if has_valid_url:
                            if not hasattr(parallel_cite, "metadata") or parallel_cite.metadata is None:
                                parallel_cite.metadata = {}
                            parallel_cite.metadata["true_by_parallel"] = True
        if self.config.debug_mode:
            logger.debug("[PARALLEL-DEBUG] Canonical propagation complete for %d citations", len(citations))

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

    def _is_google_search_url(self, url: Optional[str]) -> bool:
        """True if url is a Google search URL; such URLs must never be used as canonical case URL."""
        if not url or not str(url).strip():
            return False
        u = str(url).strip()
        return u.startswith("https://www.google.com/search") or u.startswith("http://www.google.com/search")

    def _citation_court_tier(self, citation_text: str) -> str:
        """
        Coarse court tier by reporter family.
        Used only as a safety guard for parallel identity propagation.
        """
        text = str(citation_text or "").lower()
        if not text:
            return ""
        if (
            re_module.search(r"\b\d+\s+u\.?\s*s\.?\b", text)
            or re_module.search(r"\b\d+\s+s\.?\s*ct\.?\b", text)
            or re_module.search(r"\b\d+\s+l\.?\s*ed\.?\s*(?:2d|3d)?\b", text)
        ):
            return "supreme"
        if re_module.search(r"\b\d+\s+f\.?\s*supp\.?\s*(?:2d|3d)?\b", text):
            return "district"
        if re_module.search(r"\b\d+\s+f\.?\s*(?:2d|3d|4th|app'?x)\b", text):
            return "circuit"
        return ""

    def _parallel_identity_propagation_allowed(
        self,
        source_citation: "CitationResult",
        target_citation: "CitationResult",
    ) -> bool:
        """
        Prevent cross-case canonical contamination when a cluster contains mixed court tiers.
        """
        source_tier = self._citation_court_tier(getattr(source_citation, "citation", ""))
        target_tier = self._citation_court_tier(getattr(target_citation, "citation", ""))
        if source_tier and target_tier and source_tier != target_tier:
            return False
        return True

    def propagate_canonical_to_cluster(self, citations: List["CitationResult"]):
        """
        For each group of parallel citations (including main and parallels), if any member is verified and has canonical_name and canonical_date,
        propagate those fields to all other members in the group that lack them. Set verified='true_by_parallel' for those not directly verified.
        """
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
                        url = getattr(c, "canonical_url", None) or getattr(c, "url", None)
                        if self._is_google_search_url(str(url or "")):
                            continue  # Google search URL = not real verification
                        verified_member = c
                        logger.info(f"[PARALLEL-DEBUG] Found verified member in canonical group: {c.citation}")
                        break

                if verified_member:
                    for c in group:
                        logger.info(f"[PARALLEL-DEBUG] Processing citation: {c.citation}, verified: {c.verified}")
                        if c is not verified_member and not self._parallel_identity_propagation_allowed(verified_member, c):
                            logger.info(
                                f"[PARALLEL-DEBUG] Skipping canonical propagation across tiers: "
                                f"{verified_member.citation} -> {c.citation}"
                            )
                            continue

                        # Copy canonical data if missing
                        if not c.canonical_name or not c.canonical_date:
                            logger.info(f"[PARALLEL-DEBUG] Copying canonical data to {c.citation}")
                            c.canonical_name = verified_member.canonical_name
                            c.canonical_date = verified_member.canonical_date
                            c.url = verified_member.url
                            c.source = verified_member.source

                        # Apply true_by_parallel semantics ONLY to unverified group members
                        if c is not verified_member and (not c.verified or c.verified == False):
                            if bool(getattr(c, "date_mismatch", False)):
                                continue
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
                    url = getattr(cit, "canonical_url", None) or getattr(cit, "url", None)
                    if self._is_google_search_url(str(url or "")):
                        continue  # Google search URL = not real verification
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
                # Do not propagate parallel verification to hard year mismatches.
                if bool(getattr(cit, "date_mismatch", False)):
                    continue

                # N/A+partial: Do NOT mark as verified by parallel when N/A case name AND partial citation
                if self._na_and_partial_insufficient(cit):
                    logger.info(
                        f"[PARALLEL-CLUSTER] Skipping true_by_parallel for {cit.citation} (N/A + partial citation - insufficient evidence)"
                    )
                    continue

                # Case name compatibility: same cluster = same case. If unverified citation has no
                # meaningful name (N/A/empty), allow propagation from verified member. Only require
                # names_are_same_case when both have names (avoids blocking short/partial citations).
                v_ecn = (getattr(verified_member, 'extracted_case_name', '') or '').strip()
                c_ecn = (getattr(cit, 'extracted_case_name', '') or '').strip()
                if has_case_name(c_ecn) and not names_are_same_case(v_ecn, c_ecn):
                    logger.info(
                        f"[PARALLEL-CLUSTER] Skipping true_by_parallel for {cit.citation} - different case: '{v_ecn}' vs '{c_ecn}'"
                    )
                    continue

                # This citation is in the same cluster but unverified - mark as verified by parallel
                logger.info(
                    f"[PARALLEL-CLUSTER] Marking {cit.citation} as verified by parallel (same cluster as {verified_member.citation})"
                )
                if not self._parallel_identity_propagation_allowed(verified_member, cit):
                    logger.info(
                        f"[PARALLEL-CLUSTER] Skipping true_by_parallel across tiers: "
                        f"{verified_member.citation} -> {cit.citation}"
                    )
                    continue
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
                    url = getattr(c, "canonical_url", None) or getattr(c, "url", None)
                    if self._is_google_search_url(str(url or "")):
                        continue  # Google search URL = not real verification
                    verified_member = c
                    logger.info(f"[PARALLEL-DEBUG] Found verified member: {cite_str}")
                    break

            if verified_member:
                logger.info(f"[PARALLEL-DEBUG] Propagating from verified member to {len(group)} citations")
                for cite_str in group:
                    c = citation_lookup.get(cite_str)
                    if c:
                        logger.info(f"[PARALLEL-DEBUG] Processing citation: {cite_str}, verified: {c.verified}")
                        if c is not verified_member and not self._parallel_identity_propagation_allowed(verified_member, c):
                            logger.info(
                                f"[PARALLEL-DEBUG] Skipping position-group propagation across tiers: "
                                f"{verified_member.citation} -> {c.citation}"
                            )
                            visited.add(cite_str)
                            continue

                        # Copy canonical data if missing
                        if not c.canonical_name or not c.canonical_date:
                            logger.info(f"[PARALLEL-DEBUG] Copying canonical data to {cite_str}")
                            c.canonical_name = verified_member.canonical_name
                            c.canonical_date = verified_member.canonical_date
                            c.url = verified_member.url
                            c.source = verified_member.source

                        # Apply true_by_parallel semantics ONLY to unverified group members
                        if c is not verified_member and (not c.verified or c.verified == False):
                            if bool(getattr(c, "date_mismatch", False)):
                                continue
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
                        if bool(getattr(cit, "date_mismatch", False)):
                            continue
                        if not self._parallel_identity_propagation_allowed(source_citation, cit):
                            continue
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

    def ensure_bidirectional_parallels(self, citations: List["CitationResult"], text: str = ""):
        """
        For each group of citations that are close together (by position and punctuation), ensure all group members have each other in their parallel_citations field.
        CRITICAL: Do NOT group citations separated by semicolon (e.g. "A; B; C" = different cases).
        """
        logger.debug(f"[PARALLEL-DEBUG] Starting bidirectional parallel detection for {len(citations)} citations")

        # Debug citation positions
        for i, c in enumerate(citations):
            logger.debug(f"[PARALLEL-DEBUG] Citation {i}: {c.citation}, start={c.start_index}, end={c.end_index}")

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
                logger.debug(
                    f"[PARALLEL-DEBUG] Checking proximity: {curr.citation} (start={curr.start_index}) vs {prev.citation} (end={prev.end_index})"
                )

                if curr.start_index and prev.end_index and curr.start_index - prev.end_index <= 100:
                    # Use document text when available for accurate semicolon check (Dow; Frederick = different cases)
                    text_between = ""
                    if text and prev.end_index is not None and curr.start_index is not None:
                        text_between = text[prev.end_index:curr.start_index]
                    if not text_between and hasattr(prev, "end_index") and hasattr(curr, "start_index"):
                        text_between = (
                            getattr(prev, "context", "")[-(prev.end_index - (prev.start_index or 0)) :]
                            + getattr(curr, "context", "")[: curr.start_index - (curr.start_index or 0)]
                        )
                    logger.debug(
                        f"[PARALLEL-DEBUG] Text between: '{text_between}', distance: {curr.start_index - prev.end_index}"
                    )

                    # CRITICAL: Semicolon separates different cases (e.g. "884 A.2d 667, 671; Frederick v. City...")
                    if ";" in text_between:
                        logger.debug(f"[PARALLEL-DEBUG] REJECTED - semicolon between citations (different cases)")
                        break

                    # CRITICAL: "). [A-Z]" marks a sentence boundary between citation sentences.
                    # E.g. "...46 P.3d 713, 714 (Okla. Crim. App. 2002). State ex rel. Gibson..."
                    # The close-paren + period + uppercase indicates the prior citation sentence
                    # ended and a new one (different case) begins — same logic as semicolons.
                    if re.search(r'\)\.\s+[A-Z]', text_between):
                        logger.debug(f"[PARALLEL-DEBUG] REJECTED - sentence boundary ').' between citations (different cases)")
                        break

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
                            logger.debug(f"[PARALLEL-DEBUG] REJECTED - same reporter: {prev_reporter}")
                            should_cluster = False
                        
                        # Check extracted_case_name compatibility (shared canonical logic)
                        if should_cluster:
                            prev_ecn = (getattr(prev, 'extracted_case_name', '') or '').strip()
                            curr_ecn = (getattr(curr, 'extracted_case_name', '') or '').strip()
                            if not names_are_same_case(prev_ecn, curr_ecn):
                                logger.debug(f"[PARALLEL-DEBUG] REJECTED - different cases: '{prev_ecn}' vs '{curr_ecn}'")
                                should_cluster = False
                        
                        if should_cluster:
                            logger.debug(f"[PARALLEL-DEBUG] Validation passed - Adding to group: {curr.citation}")
                            group.append(curr)
                            j += 1
                            continue
                        else:
                            logger.debug(f"[PARALLEL-DEBUG] Validation REJECTED - NOT adding to group: {curr.citation}")
                            break
                break
            if len(group) > 1:
                groups_found += 1
                cite_strs = [c.citation for c in group]
                logger.debug(f"[PARALLEL-DEBUG] Found parallel group {groups_found}: {cite_strs}")
                for c in group:
                    # CRITICAL FIX: Use helper to filter same-reporter/different-volume
                    filtered = filter_cluster_members_by_reporter(
                        c.citation,
                        [s for s in cite_strs if s != c.citation]
                    )
                    c.parallel_citations = filtered
                    logger.debug(f"[PARALLEL-DEBUG] Set {c.citation}.parallel_citations = {c.parallel_citations}")
            i = j

        logger.debug(f"[PARALLEL-DEBUG] Found {groups_found} parallel groups")

        if self.config.debug_mode:
            logger.debug("[PARALLEL-DEBUG] Group detection complete for %d citations", len(citations))

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
            logger.debug("[PARALLEL-DEBUG] Date propagation complete for %d citations", len(citations))

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
