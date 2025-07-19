"""
DEPRECATED: This module is deprecated in favor of src/unified_citation_processor_v2.py
Use UnifiedCitationProcessorV2 instead for all new development.

This module will be removed in a future version.
"""

import warnings
warnings.warn(
    "UnifiedCitationProcessor is deprecated. Use UnifiedCitationProcessorV2 from src/unified_citation_processor_v2.py instead. "
    "This file will be removed in the next release.",
    DeprecationWarning,
    stacklevel=2
)

# TODO: Remove this file in next release
# This file is kept only for backward compatibility and should not be used in new code.
# All functionality has been superseded by UnifiedCitationProcessorV2.

import re
import time
import logging
import os
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import unicodedata
import json
from datetime import datetime
import inspect
import hashlib
import copy

# Import existing components to merge
try:
    from eyecite import get_citations, resolve_citations, clean_text
    from eyecite.tokenizers import AhocorasickTokenizer
    EYECITE_AVAILABLE = True
except ImportError:
    EYECITE_AVAILABLE = False

from .cache_manager import get_cache_manager
from .config import get_config_value
from .case_name_extraction_core import extract_case_name_triple
from .extract_case_name import extract_case_name_precise_boundaries
import warnings
from .standalone_citation_parser import extract_year_enhanced

logger = logging.getLogger(__name__)
@dataclass
class CitationResult:
    """Structured result for a single citation."""
    citation: str
    case_name: Optional[str] = None
    canonical_name: Optional[str] = None
    extracted_case_name: Optional[str] = None
    extracted_date: Optional[str] = None
    verified: bool = False
    url: Optional[str] = None
    canonical_urls: List[str] = None  # Multiple canonical URLs from different sources
    court: Optional[str] = None
    docket_number: Optional[str] = None
    canonical_date: Optional[str] = None
    year: Optional[str] = None
    source: str = "Unknown"
    confidence: float = 0.0
    is_complex: bool = False
    is_parallel: bool = False
    primary_citation: Optional[str] = None
    parallel_citations: List[str] = None
    pinpoint_pages: List[str] = None
    docket_numbers: List[str] = None
    case_history: List[str] = None
    publication_status: Optional[str] = None
    context: str = ""
    method: str = "regex"
    pattern: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    start_index: Optional[int] = None
    end_index: Optional[int] = None
    cluster_members: List[str] = None
    is_cluster: bool = False
    
    def __post_init__(self):
        if self.parallel_citations is None:
            self.parallel_citations = []
        if self.pinpoint_pages is None:
            self.pinpoint_pages = []
        if self.docket_numbers is None:
            self.docket_numbers = []
        if self.case_history is None:
            self.case_history = []
        if self.canonical_urls is None:
            self.canonical_urls = []
        if self.metadata is None:
            self.metadata = {}
        if self.cluster_members is None:
            self.cluster_members = []

@dataclass
class CitationStatistics:
    """Comprehensive statistics for citation processing results."""
    total_citations: int = 0
    parallel_citations: int = 0
    verified_citations: int = 0
    unverified_citations: int = 0
    unique_cases: int = 0
    complex_citations: int = 0
    individual_parallel_citations: int = 0

class TextCleaner:
    """Enhanced text cleaning utilities from CitationProcessor."""
    
    @staticmethod
    def clean_text(text: str, steps: Optional[List[str]] = None) -> str:
        """
        Clean text using various preprocessing steps.
        
        Args:
            text: Text to clean
            steps: List of cleaning steps to apply. If None, applies all steps.
                   Options: 'whitespace', 'quotes', 'unicode', 'normalize'
        
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        if steps is None:
            steps = ['whitespace', 'quotes', 'unicode', 'normalize']
        
        cleaned = text
        
        if "whitespace" in steps:
            # Normalize whitespace
            cleaned = re.sub(r'\s+', ' ', cleaned)
            cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
            cleaned = cleaned.strip()
        
        if "quotes" in steps:
            # Normalize different types of quotes to straight quotes
            cleaned = re.sub(r"[\u2018\u2019]", "'", cleaned)  # Left/right single quotes
            cleaned = re.sub(r"[\u201C\u201D]", '"', cleaned)  # Left/right double quotes
        
        if "unicode" in steps:
            # Normalize unicode characters (e.g., accented characters)
            try:
                cleaned = unicodedata.normalize("NFKC", cleaned)
            except ImportError:
                pass
        
        if "normalize" in steps:
            # Additional normalization
            cleaned = re.sub(r'[^\w\s\.,&\'\"\(\)\[\]\{\}\-\+\=\*\/\\\|\<\>\?\:\;\!\@\#\$\%\^\&\*\(\)]', ' ', cleaned)
            cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned.strip()

class DateExtractor:
    """Date extraction utilities from CitationProcessor."""
    
    @staticmethod
    def extract_date_from_context_precise(text: str, citation_start: int, citation_end: int) -> Optional[str]:
        """Extract date with precise context to avoid wrong years."""
        
        # Strategy 1: Look immediately after citation (highest priority)
        immediate_after = text[citation_end:citation_end + 50]  # Increased window
        year_match = re.search(r'\((\d{4})\)', immediate_after)
        if year_match:
            year = year_match.group(1)
            if 1800 <= int(year) <= 2030:
                return f"{year}-01-01"
        
        # Strategy 2: Look in same sentence only (not entire document)
        # Find sentence boundaries around citation
        sentence_start = max(0, text.rfind('.', 0, citation_start) + 1)
        sentence_end = text.find('.', citation_end)
        if sentence_end == -1:
            sentence_end = len(text)
        
        sentence = text[sentence_start:sentence_end]
        
        # Look for year in this sentence only
        year_matches = re.findall(r'\((\d{4})\)', sentence)
        for year in year_matches:
            if 1800 <= int(year) <= 2030:
                return f"{year}-01-01"
        
        # Strategy 3: Look for year in broader context around citation
        context_start = max(0, citation_start - 100)
        context_end = min(len(text), citation_end + 100)
        context = text[context_start:context_end]
        
        year_matches = re.findall(r'\((\d{4})\)', context)
        for year in year_matches:
            if 1800 <= int(year) <= 2030:
                return f"{year}-01-01"
        
        return None

    @staticmethod
    def extract_date_from_context(text: str, citation_start: int, citation_end: int, context_window: int = 300) -> Optional[str]:
        """
        Extract date from context around a citation. Now with expanded patterns and larger window.
        Enhanced: If no date is found by regex, scan the 50 characters after the citation for a 4-digit year in parentheses or after a comma/semicolon.
        """
        try:
            context_start = max(0, citation_start - context_window)
            context_end = min(len(text), citation_end + context_window)
            context_before = text[context_start:citation_start]
            context_after = text[citation_end:context_end]
            full_context = context_before + context_after

            # Expanded date patterns
            date_patterns = [
                r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b',  # ISO
                r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',  # US
                r'\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})\b',
                r'\((\d{4})\)',  # (2024)
                r'(?:decided|filed|issued|released|argued|submitted|entered|adjudged|rendered|delivered|opinion\s+filed)\s+(?:on\s+)?(?:the\s+)?(?:day\s+of\s+)?([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{4})',
                r'\b(19|20)\d{2}\b',  # year
                r'\b(\d{4})\s+Wash\.\s+App\.',  # e.g. 1989 Wash. App.
                r'\b(\d{4})\s+LEXIS\b',  # e.g. 1989 LEXIS
                r'\b(\d{4})\s+WL\b',  # e.g. 1989 WL
            ]
            month_map = {
                'january': '01', 'jan': '01',
                'february': '02', 'feb': '02',
                'march': '03', 'mar': '03',
                'april': '04', 'apr': '04',
                'may': '05',
                'june': '06', 'jun': '06',
                'july': '07', 'jul': '07',
                'august': '08', 'aug': '08',
                'september': '09', 'sep': '09',
                'october': '10', 'oct': '10',
                'november': '11', 'nov': '11',
                'december': '12', 'dec': '12'
            }
            for pattern in date_patterns:
                matches = re.finditer(pattern, full_context, re.IGNORECASE)
                for match in matches:
                    groups = match.groups()
                    if len(groups) == 3:
                        if pattern == r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b':
                            year, month, day = groups
                        elif pattern == r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b':
                            month, day, year = groups
                        elif 'January|February' in pattern:
                            month_name, day, year = groups
                            month = month_map.get(month_name.lower(), '01')
                        else:
                            continue
                        try:
                            year = int(year)
                            month = int(month)
                            day = int(day)
                            if 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                                return f"{year:04d}-{month:02d}-{day:02d}"
                        except (ValueError, TypeError):
                            continue
                    elif len(groups) == 1:
                        year = groups[0]
                        try:
                            year_int = int(year)
                            if 1900 <= year_int <= 2100:
                                return f"{year_int:04d}-01-01"
                        except (ValueError, TypeError):
                            continue
            # --- NEW FALLBACK: scan after citation for (YYYY) or , YYYY or ; YYYY ---
            after = text[citation_end:citation_end+50]
            # Try (YYYY)
            m = re.search(r'\((19|20)\d{2}\)', after)
            if m:
                return f"{m.group(1)}-01-01"
            # Try , YYYY or ; YYYY
            m = re.search(r'[;,]\s*(19|20)\d{2}', after)
            if m:
                return f"{m.group(1)}-01-01"
            # Try just a 4-digit year
            m = re.search(r'(19|20)\d{2}', after)
            if m:
                return f"{m.group(1)}-01-01"
            return None
        except Exception as e:
            logger.warning(f"Error extracting date from context: {e}")
            return None

class EnhancedRegexExtractor:
    """Enhanced regex extractor with comprehensive patterns from enhanced_citation_processor."""
    
    def __init__(self):
        self._init_patterns()
    
    def _init_patterns(self):
        """Initialize comprehensive regex patterns including enhanced patterns."""
        
        # Comprehensive list of reporter abbreviations (from enhanced_citation_processor)
        self.REPORTERS = [
            # Short forms (most common in real citations)
            "Wash. 2d", "Wash. App.", "Wn.2d", "Wn. App.", "Cal. App.", "N.Y. App. Div.",
            "P.3d", "P.2d", "F.3d", "F.2d", "U.S.", "S. Ct.", "L. Ed.", "A.2d", "So. 2d",
            "Ill. App. Ct.", "Tex. App.", "Wis. 2d", "Va. App.", "Md. App.", "Ala. Civ. App.",
            "Ala. Crim. App.", "Ariz. App.", "Colo. App.", "Conn. App.", "Fla. Dist. Ct. App.",
            "Ga. App.", "Haw. App.", "Idaho App.", "Ind. App.", "Iowa App.", "Kan. App.",
            "Ky. App.", "La. App.", "Mass. App.", "Mich. App.", "Minn. App.", "Miss. App.",
            "Mo. App.", "Neb. App.", "N.J. Super. App. Div.", "N.M. App.", "N.C. App.",
            "N.D. App.", "Ohio App.", "Okla. Crim. App.", "Okla. Civ. App.", "Or. App.",
            "Pa. Super.", "S.C. App.", "S.D. App.", "Tenn. App.", "Tex. Crim. App.",
            "Utah App.", "Vt. App.", "Wis. App.", "Wyo. App.",
            # Long forms (for completeness)
            "Wash. Ct. App.", "Cal. Ct. App.", "N.Y. Ct. App. Div.", "Va. Ct. App.", "Md. Ct. App.",
            "Ill. App. Ct.", "Ala. Ct. Civ. App.", "Ala. Ct. Crim. App.", "Ariz. Ct. App.",
            "Colo. Ct. App.", "Conn. Ct. App.", "Fla. Dist. Ct. App.", "Ga. Ct. App.", "Haw. Ct. App.",
            "Idaho Ct. App.", "Ind. Ct. App.", "Iowa Ct. App.", "Kan. Ct. App.", "Ky. Ct. App.",
            "La. Ct. App.", "Mass. Ct. App.", "Mich. Ct. App.", "Minn. Ct. App.", "Miss. Ct. App.",
            "Mo. Ct. App.", "Neb. Ct. App.", "N.J. Super. Ct. App. Div.", "N.M. Ct. App.",
            "N.C. Ct. App.", "N.D. Ct. App.", "Ohio Ct. App.", "Okla. Ct. Crim. App.",
            "Okla. Ct. Civ. App.", "Or. Ct. App.", "Pa. Super. Ct.", "S.C. Ct. App.", "S.D. Ct. App.",
            "Tenn. Ct. App.", "Tex. Ct. Crim. App.", "Utah Ct. App.", "Vt. Ct. App.", "Wis. Ct. App.", "Wyo. Ct. App."
        ]
        
        # Build dynamic reporter regex
        escaped_reporters = [re.escape(r) for r in self.REPORTERS]
        self.reporter_pattern = "|".join(escaped_reporters)
        
        # Enhanced primary patterns (from enhanced_citation_processor)
        self.primary_patterns = {
            # Washington patterns (robust to all variants)
            # Updated to support up to 5 digits for volume and up to 12 digits for page
            'wn2d': r'\b(\d{1,5})\s+Wn\.2d\s+(\d{1,12})\b',
            'wn2d_space': r'\b(\d{1,5})\s+Wn\.\s*2d\s+(\d{1,12})\b',
            'wn_app': r'\b(\d{1,5})\s+Wn\.App\.\s+(\d{1,12})\b',
            'wn_app_space': r'\b(\d{1,5})\s+Wn\.\s*App\.\s+(\d{1,12})\b',
            'wash2d': r'\b(\d{1,5})\s+Wash\.2d\s+(\d{1,12})\b',
            'wash2d_space': r'\b(\d{1,5})\s+Wash\.\s*2d\s+(\d{1,12})\b',
            'wash_app': r'\b(\d{1,5})\s+Wash\.App\.\s+(\d{1,12})\b',
            'wash_app_space': r'\b(\d{1,5})\s+Wash\.\s*App\.\s+(\d{1,12})\b',
            # Pacific Reporter patterns
            'p3d': r'\b(\d{1,5})\s+P\.3d\s+(\d{1,12})\b',
            'p2d': r'\b(\d{1,5})\s+P\.2d\s+(\d{1,12})\b',
            # Federal patterns
            'us': r'\b(\d{1,5})\s+U\.\s*S\.\s+(\d{1,12})\b',
            'f3d': r'\b(\d{1,5})\s+F\.3d\s+(\d{1,12})\b',
            'f2d': r'\b(\d{1,5})\s+F\.2d\s+(\d{1,12})\b',
            'f_supp': r'\b(\d{1,5})\s+F\.\s*Supp\.\s+(\d{1,12})\b',
            'f_supp2d': r'\b(\d{1,5})\s+F\.\s*Supp\.\s*2d\s+(\d{1,12})\b',
            'f_supp3d': r'\b(\d{1,5})\s+F\.\s*Supp\.\s*3d\s+(\d{1,12})\b',
            # Supreme Court patterns
            's_ct': r'\b(\d{1,5})\s+S\.\s*Ct\.\s+(\d{1,12})\b',
            'l_ed': r'\b(\d{1,5})\s+L\.\s*Ed\.\s+(\d{1,12})\b',
            'l_ed2d': r'\b(\d{1,5})\s+L\.\s*Ed\.\s*2d\s+(\d{1,12})\b',
            # Atlantic Reporter patterns
            'a2d': r'\b(\d{1,5})\s+A\.2d\s+(\d{1,12})\b',
            'a3d': r'\b(\d{1,5})\s+A\.3d\s+(\d{1,12})\b',
            # Southern Reporter patterns
            'so2d': r'\b(\d+)\s+So\.\s*2d\s+(\d+)\b',
            'so3d': r'\b(\d+)\s+So\.\s*3d\s+(\d+)\b',
            # Additional variants for robustness
            'wash_2d_alt': r'\b(\d+)\s+Wash\.\s*2d\s+(\d+)\b',
            'wash_app_alt': r'\b(\d+)\s+Wash\.\s*App\.\s+(\d+)\b',
            'wn2d_alt': r'\b(\d+)\s+Wn\.2d\s+(\d+)\b',
            'wn2d_alt_space': r'\b(\d+)\s+Wn\.\s*2d\s+(\d+)\b',
            'wn_app_alt': r'\b(\d+)\s+Wn\.\s*App\.\s+(\d+)\b',
            'p3d_alt': r'\b(\d+)\s+P\.3d\s+(\d+)\b',
            'p2d_alt': r'\b(\d+)\s+P\.2d\s+(\d+)\b',
        }
        # Add enhanced patterns for complete and parallel citations
        enhanced_patterns = {
            'wash_complete': r'\b(\d+)\s+Wn\.2d\s+(\d+)(?:,\s*(\d+))?(?:,\s*(\d+)\s+P\.3d\s+(\d+))?\b',
            'wash_with_parallel': r'\b(\d+)\s+Wn\.2d\s+(\d+),\s*(\d+),\s*(\d+)\s+P\.3d\s+(\d+)\b',
            # Updated robust pattern for parallel/clustered citations
            'parallel_cluster': r'\b\d+\s+Wn\.2d\s+\d+(?:,\s*\d+)*(?:,\s*\d+\s+P\.3d\s+\d+)*(?:\s*\(\d{4}\))?\b'
        }
        self.primary_patterns.update(enhanced_patterns)
        # Compile all patterns
        for key, pattern in self.primary_patterns.items():
            self.primary_patterns[key] = re.compile(pattern)
        
        # Enhanced case name pattern (from enhanced_citation_processor)
        self.case_name_pattern = r'\b([A-Z][A-Za-z\s\.,&\'\"\(\)]+v\.\s+[A-Z][A-Za-z\s\.,&\'\"\(\)]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)'
        
        # Enhanced pinpoint page pattern
        self.pinpoint_pattern = re.compile(r',\s*(\d+)(?=\s*[,;]|\s*\(|\s*$)')
        
        # Enhanced docket number pattern
        self.docket_pattern = re.compile(r'No\.\s*([0-9\-]+)')
        
        # Enhanced case history pattern
        self.history_pattern = re.compile(r'\(([A-Za-z\s]+(?:I|II|III|IV|V|VI|VII|VIII|IX|X))\)')
        
        # Enhanced publication status pattern
        self.status_pattern = re.compile(r'\((unpublished|published|memorandum|per\s+curiam)\)')
        
        # Enhanced year pattern
        self.year_pattern = r'\((\d{4})\)'
        
        # Enhanced complex citation block patterns (from enhanced_citation_processor)
        self.complex_block_patterns = [
            # Pattern for case name followed by multiple citations
            r'[A-Z][A-Za-z\s\.,&\'\"\(\)]+v\.\s+[A-Z][A-Za-z\s\.,&\'\"\(\)]+?,\s+\d+\s+[A-Za-z\.\s]+\d+.*?(?=\n|\.|;)',
            # Pattern for multiple citations separated by commas
            r'\d+\s+[A-Za-z\.\s]+\d+.*?(?:,\s*\d+\s+[A-Za-z\.\s]+\d+).*?(?=\n|\.|;)',
            # Pattern for citations with docket numbers
            r'\d+\s+[A-Za-z\.\s]+\d+.*?No\.\s*[0-9\-]+.*?(?=\n|\.|;)',
            # Pattern for citations with case history
            r'\d+\s+[A-Za-z\.\s]+\d+.*?\([A-Za-z\s]+(?:I|II|III|IV|V|VI|VII|VIII|IX|X)\).*?(?=\n|\.|;)',
        ]
    
    def extract_citations(self, text: str) -> List[Dict[str, Any]]:
        """Extract citations using comprehensive regex patterns."""
        logger.warning("!!! TEST: Entered EnhancedRegexExtractor.extract_citations !!!")
        logger.info("[DEBUG] Entered EnhancedRegexExtractor.extract_citations")
        logger.info(f"[DEBUG] Input text (first 200 chars): {repr(text[:200])}")
        logger.info(f"[DEBUG] Input text length: {len(text)}")
        citations = []
        seen = set()
        
        for name, pattern in self.primary_patterns.items():
            try:
                matches = list(pattern.finditer(text))
                logger.info(f"[DEBUG] Pattern '{name}' found {len(matches)} matches.")
                for match in matches:
                    citation_str = match.group(0)
                    logger.info(f"[DEBUG] Processing citation string: {citation_str}")
                    if citation_str in seen:
                        continue
                    seen.add(citation_str)
                    
                    # Extract date from context if available
                    extracted_date = None
                    if match.start() is not None and match.end() is not None:
                        extracted_date = DateExtractor.extract_date_from_context(
                            text, match.start(), match.end()
                        )
                    
                    # Find sentence/block
                    sentence_start = text.rfind('.', 0, match.start()) + 1
                    sentence_end = text.find('.', match.end())
                    if sentence_end == -1:
                        sentence_end = len(text)
                    block = text[sentence_start:sentence_end].strip()
                    # Fallbacks for empty block
                    if not block or len(block) < 10:
                        # Try to expand to 300 chars around citation
                        block_start = max(0, match.start() - 150)
                        block_end = min(len(text), match.end() + 150)
                        block = text[block_start:block_end].strip()
                    
                    logger.info(f"[DEBUG] Processing block for citation '{citation_str}':")
                    logger.info(f"{block}")
                    logger.info("---")
                    
                    # Extract pinpoint pages, docket numbers, case history, publication status
                    pinpoint_pages = []
                    docket_numbers = []
                    case_history = []
                    publication_status = None
                    
                    # Apply regexes to the block
                    pinpoint_matches = self.pinpoint_pattern.findall(block)
                    if pinpoint_matches:
                        pinpoint_pages = pinpoint_matches
                        logger.info(f"[DEBUG] Pinpoint pages found: {pinpoint_pages}")
                    
                    docket_matches = self.docket_pattern.findall(block)
                    if docket_matches:
                        docket_numbers = docket_matches
                        logger.info(f"[DEBUG] Docket numbers found: {docket_numbers}")
                    
                    history_matches = self.history_pattern.findall(block)
                    if history_matches:
                        case_history = history_matches
                        logger.info(f"[DEBUG] Case history found: {case_history}")
                    
                    pub_match = self.status_pattern.search(block)
                    if pub_match:
                        publication_status = pub_match.group(1)
                        logger.info(f"[DEBUG] Publication status found: {publication_status}")
                    
                    # Extract case name from context
                    extracted_case_name = None
                    if match.start() is not None:
                        context_start = max(0, match.start() - 300)
                        context_end = min(len(text), match.end() + 300)
                        context = text[context_start:context_end]
                        
                        # Try to extract case name using existing patterns
                        case_name_patterns = [
                            r'([A-Z][A-Za-z&\s,\.\'\-]{1,120}?\s+v\.?\s+[A-Z][A-Za-z&\s,\.\'\-]{1,120}?)(?=\s*[,;:.]|\s*$)',
                            r'([A-Z][A-Za-z&\s,\.\'\-]{1,120}?\s+v\.?\s+[A-Z][A-Za-z&\s,\.\'\-]{1,120}?)(?=\s*[,;:.]|\s*$)'
                        ]
                        
                        for pattern_str in case_name_patterns:
                            pattern = re.compile(pattern_str, re.IGNORECASE)
                            matches = pattern.finditer(context)
                            for case_match in matches:
                                case_name = case_match.group(1).strip()
                                if case_name and len(case_name) > 5:  # Basic validation
                                    extracted_case_name = case_name
                                    break
                            if extracted_case_name:
                                break
                    
                    citations.append({
                        'citation': citation_str,
                        'extracted_case_name': extracted_case_name,
                        'extracted_date': extracted_date,
                        'start_index': match.start(),
                        'end_index': match.end(),
                        'context': block,
                        'method': 'enhanced_processor',
                        'pattern': name,
                        'pinpoint_pages': pinpoint_pages,
                        'docket_numbers': docket_numbers,
                        'case_history': case_history,
                        'publication_status': publication_status,
                        'metadata': {}
                    })
                    
            except Exception as e:
                logger.warning(f"Error processing pattern {name}: {e}")
                continue
        
        # NEW: Detect and create clusters from individual citations
        clusters = self._detect_clusters_from_individuals(citations, text)
        citations.extend(clusters)
        
        return citations
    
    def _detect_clusters_from_individuals(self, individual_citations: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
        """Detect clusters by finding individual citations that appear together."""
        clusters = []
        processed = set()
        
        # Sort citations by position in text
        sorted_citations = sorted(individual_citations, key=lambda x: x.get('start_index', 0))
        
        for i, citation in enumerate(sorted_citations):
            if i in processed:
                continue
            
            # Look for nearby citations that might form a cluster
            cluster_members = [citation]
            current_pos = citation.get('end_index', 0)
            
            # Check next few citations to see if they form a cluster
            for j in range(i + 1, min(i + 5, len(sorted_citations))):
                next_citation = sorted_citations[j]
                next_pos = next_citation.get('start_index', 0)
                
                # If citations are close together (within 50 chars) and separated by commas
                if next_pos - current_pos <= 50:
                    # Check if there are commas between them
                    text_between = text[current_pos:next_pos]
                    if ',' in text_between and len(text_between.strip()) < 30:
                        cluster_members.append(next_citation)
                        current_pos = next_citation.get('end_index', 0)
                        processed.add(j)
                    else:
                        break
                else:
                    break
            
            # If we found multiple citations, create a cluster
            if len(cluster_members) > 1:
                processed.add(i)
                
                # Create cluster citation string
                cluster_citations = [c['citation'] for c in cluster_members]
                cluster_str = ', '.join(cluster_citations)
                
                # Merge metadata from all members
                all_pinpoints = []
                all_dockets = []
                all_history = []
                all_contexts = []
                
                for member in cluster_members:
                    all_pinpoints.extend(member.get('pinpoint_pages', []))
                    all_dockets.extend(member.get('docket_numbers', []))
                    all_history.extend(member.get('case_history', []))
                    all_contexts.append(member.get('context', ''))
                
                # Use the first member's case name and date
                first_member = cluster_members[0]
                
                clusters.append({
                    'citation': cluster_str,
                    'extracted_case_name': first_member.get('extracted_case_name'),
                    'extracted_date': first_member.get('extracted_date'),
                    'start_index': first_member.get('start_index'),
                    'end_index': cluster_members[-1].get('end_index'),
                    'context': ' '.join(all_contexts),
                    'method': 'cluster_detection',
                    'pattern': 'cluster',
                    'pinpoint_pages': list(set(all_pinpoints)),  # Remove duplicates
                    'docket_numbers': list(set(all_dockets)),
                    'case_history': list(set(all_history)),
                    'publication_status': first_member.get('publication_status'),
                    'metadata': {
                        'cluster_members': cluster_citations,
                        'is_cluster': True
                    }
                })
        
        # NEW: Advanced semantic grouping for parallel citations
        semantic_clusters = self._detect_semantic_clusters(individual_citations, text)
        clusters.extend(semantic_clusters)
        
        return clusters
    
    def _detect_semantic_clusters(self, individual_citations: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
        """Detect clusters of citations that refer to the same case but appear in different formats."""
        semantic_clusters = []
        processed = set()
        
        for i, citation in enumerate(individual_citations):
            if i in processed:
                continue
            
            # Extract case components for comparison
            case_components = self._extract_case_components(citation['citation'])
            if not case_components:
                continue
            
            # Find other citations that might refer to the same case
            similar_citations = [citation]
            for j in range(i + 1, len(individual_citations)):
                if j in processed:
                    continue
                
                other_components = self._extract_case_components(individual_citations[j]['citation'])
                if not other_components:
                    continue
                
                # Check if they refer to the same case (same volume/page or same year)
                if self._is_same_case(case_components, other_components):
                    similar_citations.append(individual_citations[j])
                    processed.add(j)
            
            # If we found multiple similar citations, create a semantic cluster
            if len(similar_citations) > 1:
                processed.add(i)
                
                # Create cluster citation string
                cluster_citations = [c['citation'] for c in similar_citations]
                cluster_str = ' | '.join(cluster_citations)  # Use | to distinguish from comma clusters
                
                # Merge metadata
                all_pinpoints = []
                all_dockets = []
                all_history = []
                all_contexts = []
                
                for member in similar_citations:
                    all_pinpoints.extend(member.get('pinpoint_pages', []))
                    all_dockets.extend(member.get('docket_numbers', []))
                    all_history.extend(member.get('case_history', []))
                    all_contexts.append(member.get('context', ''))
                
                first_member = similar_citations[0]
                
                semantic_clusters.append({
                    'citation': cluster_str,
                    'extracted_case_name': first_member.get('extracted_case_name'),
                    'extracted_date': first_member.get('extracted_date'),
                    'start_index': first_member.get('start_index'),
                    'end_index': similar_citations[-1].get('end_index'),
                    'context': ' '.join(all_contexts),
                    'method': 'semantic_clustering',
                    'pattern': 'parallel',
                    'pinpoint_pages': list(set(all_pinpoints)),
                    'docket_numbers': list(set(all_dockets)),
                    'case_history': list(set(all_history)),
                    'publication_status': first_member.get('publication_status'),
                    'metadata': {
                        'cluster_members': cluster_citations,
                        'is_cluster': True,
                        'cluster_type': 'semantic'
                    }
                })
        
        return semantic_clusters
    
    def _extract_case_components(self, citation_str: str) -> Dict[str, str]:
        """Extract volume, page, and year from a citation string."""
        # Common patterns for extracting case components
        patterns = [
            r'(\d+)\s+Wn\.2d\s+(\d+)',  # 171 Wn.2d 486
            r'(\d+)\s+Wn\.\s*App\.\s+(\d+)',  # 199 Wn. App. 280
            r'(\d+)\s+P\.3d\s+(\d+)',  # 399 P.3d 1195
            r'(\d+)\s+U\.\s*S\.\s+(\d+)',  # 410 U.S. 113
        ]
        
        for pattern in patterns:
            match = re.search(pattern, citation_str)
            if match:
                return {
                    'volume': match.group(1),
                    'page': match.group(2),
                    'reporter': pattern.split(r'\s+')[1] if len(pattern.split(r'\s+')) > 1 else 'unknown'
                }
        
        return {}
    
    def _is_same_case(self, components1: Dict[str, str], components2: Dict[str, str]) -> bool:
        """Check if two citation components refer to the same case."""
        # Same volume and page (most reliable)
        if (components1.get('volume') == components2.get('volume') and 
            components1.get('page') == components2.get('page')):
            return True
        
        # Same volume, different pages (might be pinpoints)
        if (components1.get('volume') == components2.get('volume') and
            components1.get('reporter') == components2.get('reporter')):
            # Check if pages are close (within 10)
            try:
                page1 = int(components1.get('page', 0))
                page2 = int(components2.get('page', 0))
                if abs(page1 - page2) <= 10:
                    return True
            except ValueError:
                pass
        
        return False

class ComplexCitationDetector:
    """Detects and parses complex citation patterns."""
    
    def __init__(self):
        self._init_patterns()
    
    def _init_patterns(self):
        """Initialize regex patterns for different citation components."""
        
        # Enhanced primary citation patterns with comprehensive coverage
        self.primary_patterns = {
            # Washington jurisdiction patterns
            # Updated to support up to 5 digits for volume and up to 12 digits for page
            'wn_app': r'\b(\d{1,5})\s+Wn\.\s*App\.\s+(\d{1,12})\b',
            'wn2d': r'\b(\d{1,5})\s+Wn\.\s*2d\s+(\d{1,12})\b',
            'wn2d_no_space': r'\b(\d{1,5})\s+Wn\.2d\s+(\d{1,12})\b',
            'wn3d': r'\b(\d{1,5})\s+Wn\.3d\s+(\d{1,12})\b',
            'wn_generic': r'\b(\d{1,5})\s+Wn\.\s+(\d{1,12})\b',
            'wash': r'\b(\d{1,5})\s+Wash\.\s+(\d{1,12})\b',
            'wash_app': r'\b(\d{1,5})\s+Wash\.\s*App\.\s+(\d{1,12})\b',
            'wash2d': r'\b(\d{1,5})\s+Wash\.2d\s+(\d{1,12})\b',
            'wash2d_space': r'\b(\d{1,5})\s+Wash\.\s*2d\s+(\d{1,12})\b',
            
            # Pacific Reporter patterns
            'p3d': r'\b(\d{1,5})\s+P\.3d\s+(\d{1,12})\b',
            'p2d': r'\b(\d{1,5})\s+P\.2d\s+(\d{1,12})\b',
            'p_generic': r'\b(\d{1,5})\s+P\.\s+(\d{1,12})\b',
            
            # Federal patterns
            'us': r'\b(\d{1,5})\s+U\.\s*S\.\s+(\d{1,12})\b',
            'us_alt': r'\b(\d{1,5})\s+United\s+States\s+(\d{1,12})\b',
            'f3d': r'\b(\d{1,5})\s+F\.3d\s+(\d{1,12})\b',
            'f2d': r'\b(\d{1,5})\s+F\.2d\s+(\d{1,12})\b',
            'f4th': r'\b(\d{1,5})\s+F\.4th\s+(\d{1,12})\b',
            'f_supp': r'\b(\d{1,5})\s+F\.\s*Supp\.\s+(\d{1,12})\b',
            'f_supp2d': r'\b(\d{1,5})\s+F\.\s*Supp\.\s*2d\s+(\d{1,12})\b',
            'f_supp3d': r'\b(\d{1,5})\s+F\.\s*Supp\.\s*3d\s+(\d{1,12})\b',
            
            # Supreme Court patterns
            'sct': r'\b(\d{1,5})\s+S\.\s*Ct\.\s+(\d{1,12})\b',
            'sct_alt': r'\b(\d{1,5})\s+Sup\.\s*Ct\.\s+(\d{1,12})\b',
            
            # Lawyers' Edition
            'led': r'\b(\d{1,5})\s+L\.\s*Ed\.\s+(\d{1,12})\b',
            'led2d': r'\b(\d{1,5})\s+L\.\s*Ed\.\s*2d\s+(\d{1,12})\b',
            
            # Regional Reporters
            'a2d': r'\b(\d{1,5})\s+A\.2d\s+(\d{1,12})\b',
            'a3d': r'\b(\d{1,5})\s+A\.3d\s+(\d{1,12})\b',
            'ne2d': r'\b(\d{1,5})\s+N\.E\.2d\s+(\d{1,12})\b',
            'ne3d': r'\b(\d{1,5})\s+N\.E\.3d\s+(\d{1,12})\b',
            'nw2d': r'\b(\d{1,5})\s+N\.W\.2d\s+(\d{1,12})\b',
            'nw3d': r'\b(\d{1,5})\s+N\.W\.3d\s+(\d{1,12})\b',
            'se2d': r'\b(\d{1,5})\s+S\.E\.2d\s+(\d{1,12})\b',
            'se3d': r'\b(\d{1,5})\s+S\.E\.3d\s+(\d{1,12})\b',
            'sw2d': r'\b(\d{1,5})\s+S\.W\.2d\s+(\d{1,12})\b',
            'sw3d': r'\b(\d{1,5})\s+S\.W\.3d\s+(\d{1,12})\b',
            
            # California Reports
            'cal2d': r'\b(\d{1,5})\s+Cal\.2d\s+(\d{1,12})\b',
            'cal3d': r'\b(\d{1,5})\s+Cal\.3d\s+(\d{1,12})\b',
            'cal4th': r'\b(\d{1,5})\s+Cal\.4th\s+(\d{1,12})\b',
            
            # Westlaw and LEXIS
            'westlaw': r'\b(\d{4})\s+WL\s+(\d{1,12})\b',
            'lexis': r'\b(\d{4})\s+[A-Za-z\.\s]+LEXIS\s+(\d{1,12})\b',
            
            # State Reports (generic pattern)
            'state': r'\b(\d{1,5})\s+[A-Z][a-z]+\.\s+(\d{1,12})\b',
        }
        
        # Compile all patterns
        for key, pattern in self.primary_patterns.items():
            self.primary_patterns[key] = re.compile(pattern)
        
        # Complex citation patterns
        self.case_name_pattern = r'\b([A-Z][A-Za-z\s\.,&\'\"\(\)]+v\.\s+[A-Z][A-Za-z\s\.,&\'\"\(\)]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)'
        self.pinpoint_pattern = r',\s*(\d+)(?=\s*[,;]|\s*\(|\s*$)'
        self.docket_pattern = r'No\.\s*([0-9\-]+)'
        self.history_pattern = r'\(([A-Za-z\s]+(?:I|II|III|IV|V|VI|VII|VIII|IX|X))\)'
        self.status_pattern = r'\((unpublished|published|memorandum|per\s+curiam)\)'
        self.year_pattern = r'\((\d{4})\)'
        
        # Parallel citation patterns
        self.parallel_patterns = [
            # Pattern 1: name, citation citation, citation (date)
            r'([A-Z][A-Za-z\s\.,&\'\"\(\)]+v\.\s+[A-Z][A-Za-z\s\.,&\'\"\(\)]+?)\s*,\s*([^,]+?)\s*,\s*([^,]+?)\s*\((\d{4})\)',
            # Pattern 2: name, citation, page, citation, page (date)
            r'([A-Z][A-Za-z\s\.,&\'\"\(\)]+v\.\s+[A-Z][A-Za-z\s\.,&\'\"\(\)]+?)\s*,\s*([^,]+?)\s*,\s*(\d+)\s*,\s*([^,]+?)\s*\((\d{4})\)',
        ]
    
    def is_complex_citation(self, text: str) -> bool:
        """Check if text contains complex citation patterns."""
        # Check for multiple citations in close proximity
        citation_patterns = [
            r'\b\d+\s+Wn\.\s*App\.\s*\d+\b',
            r'\b\d+\s+Wn\.2d\s*\d+\b',
            r'\b\d+\s+Wn\.3d\s*\d+\b',
            r'\b\d+\s+Wash\.\s*App\.\s*\d+\b',
            r'\b\d+\s+Wash\.2d\s*\d+\b',
            r'\b\d+\s+P\.3d\s*\d+\b',
            r'\b\d+\s+P\.2d\s*\d+\b',
            r'\b\d+\s+U\.\s*S\.\s*\d+\b',
            r'\b\d+\s+F\.3d\s*\d+\b',
            r'\b\d+\s+F\.2d\s*\d+\b',
        ]
        
        citation_count = 0
        for pattern in citation_patterns:
            matches = re.findall(pattern, text)
            citation_count += len(matches)
        
        # If we have multiple citations, it's likely complex
        if citation_count > 1:
            return True
        
        # Check for specific complex patterns
        complex_patterns = [
            r'\b\d+\s+Wn\.\s*App\.\s*\d+.*\d+\s+P\.3d\s*\d+\b',  # Wn.App. + P.3d
            r'\b\d+\s+Wn\.2d\s*\d+.*\d+\s+P\.3d\s*\d+\b',       # Wn.2d + P.3d
            r'\b\d+\s+Wn\.\s*App\.\s*\d+.*\d+\s+Wn\.2d\s*\d+\b', # Wn.App. + Wn.2d
            r'No\.\s*\d+-\d+-\w+',  # Docket numbers
            r'\(\d{4}\)',           # Years in parentheses
            r'\(\w+\s+\d{4}\)',     # Publication status with year
        ]
        
        for pattern in complex_patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    def parse_complex_citation(self, text: str) -> Dict[str, Any]:
        """Parse a complex citation into structured components."""
        try:
            # Extract case name
            case_name_match = re.search(self.case_name_pattern, text, re.IGNORECASE)
            case_name = case_name_match.group(1).strip() if case_name_match else None
            
            # Extract all citations
            all_citations = self._extract_all_citations(text)
            primary_citation = all_citations[0] if all_citations else None
            parallel_citations = all_citations[1:] if len(all_citations) > 1 else []
            
            # Extract other components
            pinpoint_pages = re.findall(self.pinpoint_pattern, text)
            docket_numbers = re.findall(self.docket_pattern, text)
            case_history = re.findall(self.history_pattern, text)
            publication_status_match = re.search(self.status_pattern, text, re.IGNORECASE)
            publication_status = publication_status_match.group(1) if publication_status_match else None
            year_match = re.search(self.year_pattern, text)
            year = year_match.group(1) if year_match else None
            
            return {
                'case_name': case_name,
                'primary_citation': primary_citation,
                'parallel_citations': parallel_citations,
                'pinpoint_pages': pinpoint_pages,
                'docket_numbers': docket_numbers,
                'case_history': case_history,
                'publication_status': publication_status,
                'year': year,
                'is_complex': True
            }
            
        except Exception as e:
            logger.error(f"Error parsing complex citation '{text}': {e}")
            return {
                'case_name': None,
                'primary_citation': None,
                'parallel_citations': [],
                'pinpoint_pages': [],
                'docket_numbers': [],
                'case_history': [],
                'publication_status': None,
                'year': None,
                'is_complex': False
            }
    
    def _extract_all_citations(self, text: str) -> List[str]:
        """Extract all citations from the text."""
        citations = []
        
        # Try parallel citation patterns first
        for pattern in self.parallel_patterns:
            match = re.search(pattern, text)
            if match:
                # Extract citations from the match
                for group in match.groups()[1:]:  # Skip case name
                    if self._is_valid_citation(group):
                        citations.append(group.strip())
                if citations:
                    return citations
        
        # Fallback to individual citation extraction
        for pattern_name, pattern in self.primary_patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                citation = match.group(0)
                if citation not in citations:
                    citations.append(citation)
        
        return citations
    
    def _is_valid_citation(self, text: str) -> bool:
        """Check if text looks like a valid citation."""
        # Basic validation: should contain volume, reporter, and page
        return bool(re.search(r'\b\d+\s+[A-Za-z\. ]+\s+\d+\b', text))

class EyeciteProcessor:
    """Handles eyecite-based citation extraction."""
    
    def __init__(self):
        self.use_eyecite = EYECITE_AVAILABLE
    
    def extract_citations(self, text: str) -> List[Dict[str, Any]]:
        """Extract citations using eyecite."""
        if not self.use_eyecite:
            return []
        
        try:
            tokenizer = AhocorasickTokenizer()
            citations = get_citations(text, tokenizer=tokenizer)
            
            results = []
            for citation in citations:
                results.append({
                    'citation': str(citation),
                    'method': 'eyecite',
                    'confidence': 'high',
                    'metadata': {
                        'citation_type': type(citation).__name__,
                        'groups': citation.groups if hasattr(citation, 'groups') else None
                    }
                })
            
            return results
            
        except Exception as e:
            logger.warning(f"Eyecite extraction failed: {e}")
            return []

    def extract_eyecite_citations(self, text: str) -> List[CitationResult]:
        """Extract citations using eyecite."""
        if not EYECITE_AVAILABLE:
            return []
        try:
            tokenizer = AhocorasickTokenizer()
            citations = get_citations(text, tokenizer=tokenizer)
            results = []
            for citation in citations:
                # Extract the clean citation string from the eyecite object
                if hasattr(citation, 'citation') and citation.citation:
                    citation_str = citation.citation
                else:
                    citation_str = str(citation)
                # Extract case name from eyecite metadata if available
                case_name = None
                if hasattr(citation, 'metadata') and citation.metadata:
                    if hasattr(citation.metadata, 'plaintiff') and hasattr(citation.metadata, 'defendant'):
                        plaintiff = citation.metadata.plaintiff or ''
                        defendant = citation.metadata.defendant or ''
                        if plaintiff and defendant:
                            case_name = f"{plaintiff} v. {defendant}"
                
                # Extract year from metadata if available
                year = None
                if hasattr(citation, 'metadata') and citation.metadata:
                    if hasattr(citation.metadata, 'year') and citation.metadata.year:
                        year = str(citation.metadata.year)
                
                # Safely get start/end
                start = getattr(citation, 'start', None)
                end = getattr(citation, 'end', None)
                context_start = max(0, start - 200) if start is not None else 0
                context_end = min(len(text), end + 200) if end is not None else len(text)
                context = text[context_start:context_end]
                extracted_date = None
                if start is not None and end is not None:
                    extracted_date = DateExtractor.extract_date_from_context(text, start, end)
                
                # Create CitationResult with normalized string
                result = CitationResult(
                    citation=citation_str,  # Use the normalized string
                    case_name=case_name,
                    year=year,
                    method='eyecite',
                    confidence=0.8,
                    start_index=start,
                    end_index=end,
                    context=context,
                    metadata={
                        'eyecite_object': citation,
                        'extracted_date': extracted_date,
                        'original_citation': citation
                    }
                )
                
                # Handle parallel citations in the 'extra' field
                if hasattr(citation, 'metadata') and citation.metadata:
                    if hasattr(citation.metadata, 'extra') and citation.metadata.extra:
                        # Parse parallel citations from extra field
                        extra_citations = self._parse_parallel_citations(citation.metadata.extra)
                        result.parallel_citations = extra_citations
                        result.is_parallel = len(extra_citations) > 0
                
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in eyecite extraction: {e}")
            return []
    
    def _parse_parallel_citations(self, extra_text: str) -> List[str]:
        """Parse parallel citations from eyecite extra field."""
        if not extra_text:
            return []
        
        # Try to extract citations from the extra text
        citations = []
        
        # Look for citation patterns in the extra text
        citation_patterns = [
            r'\b\d+\s+[A-Z][a-z]+\.\s+\d+\b',
            r'\b\d+\s+[A-Z]\.[a-z]+\.\s+\d+\b',
            r'\b\d+\s+[A-Z][a-z]+\d+\s+\d+\b',
        ]
        
        for pattern in citation_patterns:
            matches = re.findall(pattern, extra_text)
            citations.extend(matches)
        
        return list(set(citations))  # Remove duplicates

class APIVerifier:
    """Handles API-based citation verification."""
    
    def __init__(self):
        self.api_key = get_config_value("COURTLISTENER_API_KEY")
        self.session = self._create_session()
        self.cache_manager = get_cache_manager()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        retry_strategy = Retry(
            total=2,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504, 522, 524],
            allowed_methods=["GET", "POST"],
            respect_retry_after_header=True,
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def verify_citation(self, citation: str, extracted_case_name: str = None) -> dict:
        """Verify a citation using the unified workflow (verify_citation_unified_workflow)."""
        return self.verifier.verify_citation_unified_workflow(citation, extracted_case_name=extracted_case_name)
    
    def _process_api_response(self, data: Dict, citation: str) -> Dict[str, Any]:
        """Process the API response into a standardized format."""
        if not data or 'results' not in data:
            return {'verified': False, 'error': 'No results found'}
        
        result = data['results'][0] if data['results'] else {}
        
        return {
            'verified': True,
            'case_name': result.get('case_name', ''),
            'url': result.get('absolute_url', ''),
            'court': result.get('court', ''),
            'docket_number': result.get('docket_number', ''),
            'date_filed': result.get('date_filed', ''),
            'parallel_citations': result.get('parallel_citations', []),
            'source': 'CourtListener'
        }

class CitationGrouper:
    """Groups citations by case similarity."""
    
    def group_citations(self, citations: List[CitationResult]) -> List[List[CitationResult]]:
        """Group citations that refer to the same case."""
        if not citations:
            return []
        
        groups = []
        processed = set()
        
        for i, citation in enumerate(citations):
            if i in processed:
                continue
            
            # Start a new group
            group = [citation]
            processed.add(i)
            
            # Look for citations that are explicitly together with this one
            for j, other in enumerate(citations):
                if j in processed:
                    continue
                
                # ENHANCED GROUPING CRITERIA:
                # 1. Same case name (exact match or very high similarity)
                # 2. Same context block (within 400 characters - increased for better detection)
                # 3. Explicitly separated by commas/semicolons in source text
                # 4. Same year (if available)
                
                # Check for exact case name match first
                if (citation.case_name and other.case_name and 
                    citation.case_name == other.case_name):
                    
                    # Check if they're in the same context block
                    if (hasattr(citation, 'context') and hasattr(other, 'context') and
                        citation.context and other.context):
                        
                        # Calculate context similarity
                        context_similarity = self._calculate_context_similarity(
                            citation.context, other.context
                        )
                        
                        if context_similarity > 0.6:  # Lowered threshold for better grouping
                            # Additional check: are they explicitly separated by punctuation?
                            # Look for patterns like "case_name, citation1, citation2"
                            combined_text = f"{citation.citation} {other.citation}"
                            if re.search(r'[,;]\s*', combined_text) or context_similarity > 0.7:
                                group.append(other)
                                processed.add(j)
                                continue
                
                # Check for very high similarity (0.85+) but only if they're in the same context
                elif (citation.case_name and other.case_name):
                    similarity = self._calculate_case_name_similarity(
                        citation.case_name, other.case_name
                    )
                    
                    if similarity >= 0.85:  # High threshold for similarity
                        # Additional requirement: they must be in the same context block
                        if (hasattr(citation, 'context') and hasattr(other, 'context') and
                            citation.context and other.context):
                            
                            context_similarity = self._calculate_context_similarity(
                                citation.context, other.context
                            )
                            
                            if context_similarity > 0.5:  # Lowered context similarity threshold
                                # Check for explicit grouping indicators
                                combined_context = f"{citation.context} {other.context}"
                                if re.search(r'[,;]\s*', combined_context):
                                    group.append(other)
                                    processed.add(j)
                                    continue
            
            # If we have multiple citations in the group, create a combined result
            if len(group) > 1:
                # Use the first citation as primary and add others as parallel citations
                primary = group[0]
                primary.parallel_citations = [c.citation for c in group[1:]]
                primary.is_parallel = True

                # Propagate verification status
                any_verified = any(c.verified for c in group)
                for c in group:
                    if c.verified:
                        c.verification_status = 'verified'
                    elif any_verified:
                        c.verification_status = 'true_by_parallel'
                    else:
                        c.verification_status = 'unverified'
                groups.append(group)
            else:
                # Single citation, no grouping needed
                citation.verification_status = 'verified' if citation.verified else 'unverified'
                groups.append(group)
        
        return groups
    
    def _calculate_context_similarity(self, context1: str, context2: str) -> float:
        """Calculate similarity between two context strings."""
        if not context1 or not context2:
            return 0.0
        
        # Simple Jaccard similarity on words
        words1 = set(context1.lower().split())
        words2 = set(context2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _calculate_case_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two case names."""
        if not name1 or not name2:
            return 0.0
        
        # Normalize names
        norm1 = self._normalize_case_name(name1)
        norm2 = self._normalize_case_name(name2)
        
        if not norm1 or not norm2:
            return 0.0
        
        # Check for exact match
        if norm1 == norm2:
            return 1.0
        
        # Check for one name being a substring of the other
        if norm1 in norm2 or norm2 in norm1:
            return 0.8
        
        # Get word sets
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if not words1 or not words2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _normalize_case_name(self, case_name: str) -> str:
        """Normalize case name for comparison."""
        if not case_name:
            return ""
        
        normalized = case_name.lower()
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _load_config(self):
        """Load configuration from config.json."""
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "config.json"
        )
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return {}
    
    def _normalize_citation(self, citation: str) -> str:
        """Normalize citation format for better matching."""
        if not citation:
            return ""

        # Replace multiple spaces with a single space
        normalized = re.sub(r"\s+", " ", citation.strip())

        # Normalize Washington citations
        normalized = re.sub(r"Wash\.\s*App\.", "Wn. App.", normalized)
        normalized = re.sub(r"Wash\.", "Wn.", normalized)

        # Normalize Pacific Reporter citations
        normalized = re.sub(r"P\.(\d+)d", "P.2d", normalized)
        normalized = re.sub(r"P\.(\d+)th", "P.3d", normalized)

        # Normalize Federal Reporter citations
        normalized = re.sub(r"F\.(\d+)d", "F.2d", normalized)
        normalized = re.sub(r"F\.(\d+)th", "F.3d", normalized)

        return normalized
    
    def _extract_citation_components(self, citation: str) -> Dict[str, str]:
        """Extract components from a citation for flexible matching."""
        components = {"volume": "", "reporter": "", "page": "", "court": "", "year": ""}

        # Extract volume, reporter, and page
        volume_reporter_page = re.search(r"(\d+)\s+([A-Za-z\.\s]+)\s+(\d+)", citation)
        if volume_reporter_page:
            components["volume"] = volume_reporter_page.group(1)
            components["reporter"] = volume_reporter_page.group(2).strip()
            components["page"] = volume_reporter_page.group(3)

        # Extract year
        year = re.search(r"\((\d{4})\)", citation)
        if year:
            components["year"] = year.group(1)

        # Extract court
        if "Wn. App." in citation or "Wash. App." in citation:
            components["court"] = "Washington Court of Appeals"
        elif "Wn." in citation or "Wash." in citation:
            components["court"] = "Washington Supreme Court"
        elif "U.S." in citation:
            components["court"] = "United States Supreme Court"
        elif "F." in citation:
            if "Supp." in citation:
                components["court"] = "United States District Court"
            else:
                components["court"] = "United States Court of Appeals"

        return components
    
    def _check_cache(self, citation: str) -> Optional[Dict]:
        """Check if the citation is in the cache."""
        cache_file = os.path.join(
            self.cache_dir,
            f"{self._normalize_citation(citation).replace(' ', '_')}.json",
        )
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading cache for citation '{citation}': {e}")
        return None
    
    def _save_to_cache(self, citation: str, result: Dict):
        """Save the verification result to the cache."""
        cache_file = os.path.join(
            self.cache_dir,
            f"{self._normalize_citation(citation).replace(' ', '_')}.json",
        )
        try:
            with open(cache_file, "w") as f:
                json.dump(result, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving cache for citation '{citation}': {e}")
    
    def _verify_with_courtlistener(self, citation: str) -> Dict:
        """Verify a citation using the CourtListener API."""
        if not self.courtlistener_api_key:
            return {
                "verified": False,
                "source": "CourtListener",
                "error": "No API key provided",
            }

        # Helper function to try verification with a specific citation
        def try_verify_with_citation(citation_to_try: str) -> Dict:
            try:
                # Extract components for flexible search
                components = self._extract_citation_components(citation_to_try)

                # Build the search query
                query = (
                    f"{components['volume']} {components['reporter']} {components['page']}"
                )

                # Make the API request
                headers = {"Authorization": f"Token {self.courtlistener_api_key}"}
                params = {"q": query, "format": "json"}
                response = requests.get(
                    "https://www.courtlistener.com/api/rest/v4/search/",
                    headers=headers,
                    params=params,
                )

                if response.status_code != 200:
                    return {
                        "verified": False,
                        "source": "CourtListener",
                        "error": f"API error: {response.status_code}",
                    }

                data = response.json()

                # Check if any results match the citation
                if data.get("count", 0) > 0:
                    for result in data.get("results", []):
                        # Check if volume, reporter, and page match
                        citation_string = result.get("citation", "")
                        if (
                            components["volume"] in citation_string
                            and components["reporter"] in citation_string
                            and components["page"] in citation_string
                        ):
                            return {
                                "verified": True,
                                "source": "CourtListener",
                                "case_name": result.get("case_name", ""),
                                "url": result.get("absolute_url", ""),
                                "court": result.get("court", ""),
                                "date_filed": result.get("date_filed", ""),
                            }

                return {
                    "verified": False,
                    "source": "CourtListener",
                    "error": "No matching results found",
                }

            except Exception as e:
                self.logger.error(
                    f"Error verifying citation '{citation_to_try}' with CourtListener: {e}"
                )
                return {"verified": False, "source": "CourtListener", "error": str(e)}

        # First, try with the original citation
        result = try_verify_with_citation(citation)
        if result.get("verified"):
            return result

        # If that fails and it looks like a cluster, try with the main citation
        import re
        if re.match(r'\d+\s+[A-Za-z\.]+\s+\d+(,\s*(\d+|\d+\s+[A-Za-z\.]+\s+\d+))+', citation):
            # Extract the main citation (first part before comma)
            main_citation_match = re.match(r'(\d+\s+[A-Za-z\.]+\s+\d+)', citation)
            if main_citation_match:
                main_citation = main_citation_match.group(1)
                result = try_verify_with_citation(main_citation)
                if result.get("verified"):
                    return result

        # If still no success, try with any parallel citations in the cluster
        if re.match(r'\d+\s+[A-Za-z\.]+\s+\d+(,\s*(\d+|\d+\s+[A-Za-z\.]+\s+\d+))+', citation):
            # Find all full citations in the cluster
            full_citations = re.findall(r'(\d+\s+[A-Za-z\.]+\s+\d+)', citation)
            for full_citation in full_citations:
                if full_citation != citation:  # Skip the original
                    result = try_verify_with_citation(full_citation)
                    if result.get("verified"):
                        return result

        # Return the original result if nothing worked
        return result
    
    def _verify_with_langsearch(self, citation: str) -> Dict:
        """Verify a citation using the LangSearch API."""
        if not self.langsearch_api_key:
            return {
                "verified": False,
                "source": "LangSearch",
                "error": "No API key provided",
            }

        try:
            # Extract components for flexible search
            components = self._extract_citation_components(citation)

            # Build the search query
            query = (
                f"{components['volume']} {components['reporter']} {components['page']}"
            )

            # Make the API request
            headers = {"Authorization": f"Bearer {self.langsearch_api_key}"}
            params = {"query": query, "limit": 10}
            response = requests.get(
                "https://api.langsearch.com/v1/search",
                headers=headers,
                params=params,
            )

            if response.status_code != 200:
                return {
                    "verified": False,
                    "source": "LangSearch",
                    "error": f"API error: {response.status_code}",
                }

            data = response.json()

            # Check if any results match the citation
            if data.get("results", []):
                for result in data.get("results", []):
                    # Check if volume, reporter, and page match
                    citation_string = result.get("citation", "")
                    if (
                        components["volume"] in citation_string
                        and components["reporter"] in citation_string
                        and components["page"] in citation_string
                    ):
                        return {
                            "verified": True,
                            "source": "LangSearch",
                            "case_name": result.get("case_name", ""),
                            "url": result.get("url", ""),
                            "court": result.get("court", ""),
                            "date": result.get("date", ""),
                        }

            return {
                "verified": False,
                "source": "LangSearch",
                "error": "No matching results found",
            }

        except Exception as e:
            self.logger.error(
                f"Error verifying citation '{citation}' with LangSearch: {e}"
            )
            return {"verified": False, "source": "LangSearch", "error": str(e)}
    
    def _verify_with_database(self, citation: str) -> Dict:
        """Verify a citation using the local database or fallback to canonical verification."""
        try:
            # Try to use the canonical verification workflow as fallback
            try:
                from unified_citation_processor_v2 import UnifiedCitationProcessorV2
            except ImportError:
                # Fallback if relative import fails
                import sys
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
                from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
                
            processor = UnifiedCitationProcessorV2()
            result = processor.verify_citation_unified_workflow(citation)
            
            if result.get("verified"):
                return {
                    "verified": True,
                    "source": "Database (via UnifiedProcessor)",
                    "case_name": result.get("case_name"),
                    "canonical_name": result.get("canonical_name"),
                    "canonical_date": result.get("canonical_date"),
                    "url": result.get("url"),
                    "confidence": result.get("confidence", 0.8)
                }
            
            return {
                "verified": False,
                "source": "Database",
                "error": "Citation not found in database or verification sources",
            }

        except Exception as e:
            self.logger.error(
                f"Error verifying citation '{citation}' with database: {e}"
            )
            return {"verified": False, "source": "Database", "error": str(e)}
    
    def _verify_with_landmark_cases(self, citation: str) -> Dict:
        """
        Verify citation using landmark cases database.
        Note: This method does not provide URLs, so it should not mark citations as verified.
        """
        try:
            # Define landmark cases (this could be expanded)
            landmark_cases = {
                "410 U.S. 113": {
                    "case_name": "Roe v. Wade",
                    "court": "United States Supreme Court",
                    "date": "1973"
                },
                "347 U.S. 483": {
                    "case_name": "Brown v. Board of Education",
                    "court": "United States Supreme Court", 
                    "date": "1954"
                }
                # Add more landmark cases as needed
            }
            
            if citation in landmark_cases:
                case_info = landmark_cases[citation]
                return {
                    "verified": False,  # Don't mark as verified without URL
                    "case_name": case_info["case_name"],
                    "url": None,  # No URL from landmark cases
                    "court": case_info["court"],
                    "date": case_info["date"],
                    "source": "Landmark Cases",
                    "error": None
                }
            else:
                return {
                    "verified": False,
                    "case_name": None,
                    "url": None,
                    "court": None,
                    "date": None,
                    "source": "Landmark Cases",
                    "error": "Not a landmark case"
                }
        except Exception as e:
            return {"verified": False, "source": "Landmark Cases", "error": str(e)}
    
    def _verify_with_fuzzy_matching(self, citation: str) -> Dict:
        """
        Verify citation using fuzzy matching against known patterns.
        Note: This method does not provide URLs, so it should not mark citations as verified.
        """
        try:
            # Extract components for fuzzy matching
            components = self._extract_citation_components(citation)
            
            # Basic validation - if it looks like a valid citation format
            if components.get('volume') and components.get('reporter') and components.get('page'):
                return {
                    "verified": False,  # Don't mark as verified without URL
                    "case_name": None,
                    "url": None,  # No URL from fuzzy matching
                    "court": None,
                    "date": components.get('year'),
                    "source": "Fuzzy Matching",
                    "error": None
                }
            else:
                return {
                    "verified": False,
                    "case_name": None,
                    "url": None,
                    "court": None,
                    "date": None,
                    "source": "Fuzzy Matching",
                    "error": "Invalid citation format"
                }
        except Exception as e:
            return {"verified": False, "source": "Fuzzy Matching", "error": str(e)}
    
    def verify_citation_unified_workflow(self, citation: str) -> Dict:
        """
        Verify a citation using multiple sources and techniques.
        Returns a comprehensive verification result.
        """
        if not citation:
            return {"verified": False, "error": "No citation provided"}

        self.logger.info(f"Verifying citation: {citation}")

        # Check cache first
        cached_result = self._check_cache(citation)
        if cached_result:
            self.logger.info(f"Found cached result for citation: {citation}")
            return cached_result

        # Initialize verification results
        verification_results = {
            "citation": citation,
            "normalized_citation": self._normalize_citation(citation),
            "components": self._extract_citation_components(citation),
            "verified": False,
            "verification_date": datetime.now().isoformat(),
            "sources": {},
        }

        # Verify with landmark cases first (fastest)
        landmark_result = self._verify_with_landmark_cases(citation)
        verification_results["sources"]["landmark_cases"] = landmark_result

        if landmark_result.get("verified", False):
            verification_results["verified"] = True
            verification_results["verified_by"] = "Landmark Cases"
            self._save_to_cache(citation, verification_results)
            return verification_results

        # Verify with fuzzy matching (fast)
        fuzzy_result = self._verify_with_fuzzy_matching(citation)
        verification_results["sources"]["fuzzy_matching"] = fuzzy_result

        if fuzzy_result.get("verified", False):
            verification_results["verified"] = True
            verification_results["verified_by"] = "Fuzzy Matching"
            self._save_to_cache(citation, verification_results)
            return verification_results

        # Verify with database (if available)
        database_result = self._verify_with_database(citation)
        verification_results["sources"]["database"] = database_result

        if database_result.get("verified", False):
            verification_results["verified"] = True
            verification_results["verified_by"] = "Database"
            self._save_to_cache(citation, verification_results)
            return verification_results

        # Verify with CourtListener (API call)
        courtlistener_result = self._verify_with_courtlistener(citation)
        verification_results["sources"]["courtlistener"] = courtlistener_result

        if courtlistener_result.get("verified", False):
            verification_results["verified"] = True
            verification_results["verified_by"] = "CourtListener"
            self._save_to_cache(citation, verification_results)
            return verification_results

        # Verify with LangSearch (API call)
        langsearch_result = self._verify_with_langsearch(citation)
        verification_results["sources"]["langsearch"] = langsearch_result

        if langsearch_result.get("verified", False):
            verification_results["verified"] = True
            verification_results["verified_by"] = "LangSearch"
            self._save_to_cache(citation, verification_results)
            return verification_results

        # If we get here, the citation could not be verified
        verification_results["verified"] = False
        verification_results["error"] = "Citation could not be verified by any source"

        # Save to cache
        self._save_to_cache(citation, verification_results)

        return verification_results
    
    def batch_verify_citations(self, citations: List[str]) -> List[Dict]:
        """
        Verify a batch of citations.
        Returns a list of verification results.
        """
        results = []

        for citation in citations:
            result = self.verify_citation_unified_workflow(citation)
            results.append(result)

            # Add a small delay to avoid rate limiting
            time.sleep(1.0)  # 1 second delay to handle 60 citations per minute

        return results

class OCRCorrector:
    """Handles OCR error correction for citation text."""
    
    def __init__(self):
        self.ocr_corrections = self._init_ocr_corrections()
        self.enabled = True
    
    def _init_ocr_corrections(self) -> Dict[str, str]:
        """Initialize common OCR error corrections."""
        return {
            # Common OCR errors in citations
            '0': 'O',  # Zero to O
            'O': '0',  # O to Zero (context-dependent)
            '1': 'l',  # One to lowercase L
            'l': '1',  # Lowercase L to One (context-dependent)
            '5': 'S',  # Five to S
            'S': '5',  # S to Five (context-dependent)
            '8': 'B',  # Eight to B
            'B': '8',  # B to Eight (context-dependent)
            '6': 'G',  # Six to G
            'G': '6',  # G to Six (context-dependent)
            'rn': 'm',  # rn to m
            'm': 'rn',  # m to rn (context-dependent)
            'cl': 'd',  # cl to d
            'd': 'cl',  # d to cl (context-dependent)
            'vv': 'w',  # vv to w
            'w': 'vv',  # w to vv (context-dependent)
            
            # Common reporter abbreviations
            'Wn.2d': 'Wn.2d',  # Ensure correct format
            'Wn.App.': 'Wn. App.',  # Fix spacing
            'Wn.App': 'Wn. App.',  # Fix spacing and period
            'P.3d': 'P.3d',  # Ensure correct format
            'P.2d': 'P.2d',  # Ensure correct format
            'U.S.': 'U.S.',  # Ensure correct format
            'F.3d': 'F.3d',  # Ensure correct format
            'F.2d': 'F.2d',  # Ensure correct format
            
            # Common case name OCR errors
            'v.': 'v.',  # Ensure correct format
            'v': 'v.',  # Add period
            'vs.': 'v.',  # Fix vs to v
            'versus': 'v.',  # Fix versus to v
        }
    
    def correct_text(self, text: str) -> str:
        """Apply OCR corrections to text."""
        if not self.enabled:
            return text
        
        corrected_text = text
        
        # Apply common OCR corrections
        for error, correction in self.ocr_corrections.items():
            corrected_text = corrected_text.replace(error, correction)
        
        # Apply context-specific corrections
        corrected_text = self._apply_context_corrections(corrected_text)
        
        return corrected_text
    
    def _apply_context_corrections(self, text: str) -> str:
        """Apply context-specific OCR corrections."""
        # Fix common citation patterns
        import re
        
        # Fix volume numbers (should be digits)
        text = re.sub(r'\b([A-Z])\s+([A-Za-z\.]+)\s+(\d+)\b', r'\1 \2 \3', text)
        
        # Fix page numbers (should be digits)
        text = re.sub(r'\b(\d+)\s+([A-Za-z\.]+)\s+([A-Z])\b', r'\1 \2 \3', text)
        
        # Fix reporter abbreviations
        text = re.sub(r'\bWn\.\s*2d\b', 'Wn.2d', text)
        text = re.sub(r'\bWn\.\s*App\.\b', 'Wn. App.', text)
        text = re.sub(r'\bP\.\s*3d\b', 'P.3d', text)
        text = re.sub(r'\bP\.\s*2d\b', 'P.2d', text)
        text = re.sub(r'\bU\.\s*S\.\b', 'U.S.', text)
        text = re.sub(r'\bF\.\s*3d\b', 'F.3d', text)
        text = re.sub(r'\bF\.\s*2d\b', 'F.2d', text)
        
        return text
    
    def enable(self):
        """Enable OCR correction."""
        self.enabled = True
    
    def disable(self):
        """Disable OCR correction."""
        self.enabled = False

class ConfidenceScorer:
    """Handles confidence scoring for citation extraction and verification."""
    
    def __init__(self):
        self.scoring_weights = {
            'pattern_match': 0.3,
            'context_quality': 0.2,
            'verification_result': 0.3,
            'case_name_match': 0.1,
            'date_consistency': 0.1
        }
    
    def calculate_citation_confidence(self, citation: Dict[str, Any], context: str = "") -> float:
        """Calculate confidence score for a citation."""
        confidence = 0.0
        
        # Pattern match confidence
        pattern_confidence = self._calculate_pattern_confidence(citation)
        confidence += pattern_confidence * self.scoring_weights['pattern_match']
        
        # Context quality confidence
        context_confidence = self._calculate_context_confidence(context)
        confidence += context_confidence * self.scoring_weights['context_quality']
        
        # Verification result confidence
        verification_confidence = self._calculate_verification_confidence(citation)
        confidence += verification_confidence * self.scoring_weights['verification_result']
        
        # Case name match confidence
        case_name_confidence = self._calculate_case_name_confidence(citation)
        confidence += case_name_confidence * self.scoring_weights['case_name_match']
        
        # Date consistency confidence
        date_confidence = self._calculate_date_confidence(citation)
        confidence += date_confidence * self.scoring_weights['date_consistency']
        
        return min(confidence, 1.0)  # Cap at 1.0
    
    def _calculate_pattern_confidence(self, citation: Dict[str, Any]) -> float:
        """Calculate confidence based on pattern match quality."""
        citation_str = citation.get('citation', '')
        method = citation.get('method', '')
        pattern = citation.get('pattern', '')
        
        # Base confidence by method
        method_scores = {
            'enhanced_processor': 0.9,
            'eyecite': 0.8,
            'cluster_detection': 0.7,
            'semantic_clustering': 0.6,
            'regex': 0.5
        }
        
        base_confidence = method_scores.get(method, 0.5)
        
        # Adjust based on pattern quality
        if 'complete' in pattern or 'enhanced' in pattern:
            base_confidence += 0.1
        elif 'alt' in pattern:
            base_confidence += 0.05
        
        # Adjust based on citation format
        if re.match(r'^\d+\s+[A-Za-z\.]+\s+\d+$', citation_str):
            base_confidence += 0.1  # Well-formed citation
        elif ',' in citation_str:
            base_confidence -= 0.1  # Complex citation
        
        return min(base_confidence, 1.0)
    
    def _calculate_context_confidence(self, context: str) -> float:
        """Calculate confidence based on context quality."""
        if not context:
            return 0.0
        
        confidence = 0.5  # Base confidence
        
        # Context length
        if len(context) > 200:
            confidence += 0.2
        elif len(context) > 100:
            confidence += 0.1
        
        # Presence of case name patterns
        case_name_patterns = [
            r'[A-Z][A-Za-z\s]+v\.\s+[A-Z][A-Za-z\s]+',
            r'[A-Z][A-Za-z\s]+vs\.\s+[A-Z][A-Za-z\s]+',
            r'[A-Z][A-Za-z\s]+versus\s+[A-Z][A-Za-z\s]+'
        ]
        
        for pattern in case_name_patterns:
            if re.search(pattern, context):
                confidence += 0.2
                break
        
        # Presence of date patterns
        date_patterns = [
            r'\(\d{4}\)',
            r'\d{4}',
            r'\b\d{1,2}/\d{1,2}/\d{4}\b'
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, context):
                confidence += 0.1
                break
        
        return min(confidence, 1.0)
    
    def _calculate_verification_confidence(self, citation: Dict[str, Any]) -> float:
        """Calculate confidence based on verification results."""
        verified = citation.get('verified', False)
        source = citation.get('source', '')
        confidence = citation.get('confidence', 0.0)
        
        if not verified:
            return 0.0
        
        # Source-based confidence
        source_scores = {
            'CourtListener': 0.9,
            'Landmark Cases': 0.8,
            'Database': 0.7,
            'Fuzzy Matching': 0.5
        }
        
        source_confidence = source_scores.get(source, 0.5)
        
        # Use provided confidence if available, otherwise use source confidence
        return confidence if confidence > 0 else source_confidence
    
    def _calculate_case_name_confidence(self, citation: Dict[str, Any]) -> float:
        """Calculate confidence based on case name extraction."""
        extracted_name = citation.get('extracted_case_name', '')
        canonical_name = citation.get('canonical_name', '')
        
        if not extracted_name or extracted_name == 'N/A':
            return 0.0
        
        confidence = 0.5  # Base confidence
        
        # Length of case name
        if len(extracted_name) > 20:
            confidence += 0.2
        elif len(extracted_name) > 10:
            confidence += 0.1
        
        # Presence of "v." or similar
        if 'v.' in extracted_name or 'vs.' in extracted_name or 'versus' in extracted_name:
            confidence += 0.2
        
        # Match with canonical name
        if canonical_name and canonical_name != 'N/A':
            # Simple similarity check
            if extracted_name.lower() in canonical_name.lower() or canonical_name.lower() in extracted_name.lower():
                confidence += 0.3
        
        return min(confidence, 1.0)
    
    def _calculate_date_confidence(self, citation: Dict[str, Any]) -> float:
        """Calculate confidence based on date consistency."""
        extracted_date = citation.get('extracted_date', '')
        canonical_date = citation.get('canonical_date', '')
        
        if not extracted_date or extracted_date == 'N/A':
            return 0.0
        
        confidence = 0.5  # Base confidence
        
        # Date format validation
        if re.match(r'^\d{4}$', extracted_date):
            confidence += 0.2
        elif re.match(r'^\d{4}-\d{2}-\d{2}$', extracted_date):
            confidence += 0.3
        
        # Consistency between extracted and canonical dates
        if canonical_date and canonical_date != 'N/A':
            if extracted_date == canonical_date:
                confidence += 0.3
            elif extracted_date[:4] == canonical_date[:4]:  # Same year
                confidence += 0.2
        
        return min(confidence, 1.0)

class StatuteFilter:
    """Handles filtering of statute citations (U.S.C., C.F.R., etc.)."""
    
    def __init__(self):
        self.statute_patterns = self._init_statute_patterns()
        self.enabled = True
        self.include_statutes = False  # Default to excluding statutes
    
    def _init_statute_patterns(self) -> List[Dict[str, Any]]:
        """Initialize patterns for detecting statute citations."""
        return [
            # U.S. Code patterns
            {
                'name': 'U.S.C.',
                'pattern': r'\b(\d+)\s+U\.\s*S\.\s*C\.\s*§?\s*(\d+[a-z]?(?:\(\d+\))?)',
                'example': '42 U.S.C. § 1983'
            },
            {
                'name': 'U.S.C. (no section symbol)',
                'pattern': r'\b(\d+)\s+U\.\s*S\.\s*C\.\s*(\d+[a-z]?(?:\(\d+\))?)',
                'example': '42 U.S.C. 1983'
            },
            {
                'name': 'U.S.C. (abbreviated)',
                'pattern': r'\b(\d+)\s+USC\s*§?\s*(\d+[a-z]?(?:\(\d+\))?)',
                'example': '42 USC § 1983'
            },
            
            # Code of Federal Regulations patterns
            {
                'name': 'C.F.R.',
                'pattern': r'\b(\d+)\s+C\.\s*F\.\s*R\.\s*§?\s*(\d+\.\d+)',
                'example': '28 C.F.R. § 0.85'
            },
            {
                'name': 'C.F.R. (no section symbol)',
                'pattern': r'\b(\d+)\s+C\.\s*F\.\s*R\.\s*(\d+\.\d+)',
                'example': '28 C.F.R. 0.85'
            },
            {
                'name': 'C.F.R. (abbreviated)',
                'pattern': r'\b(\d+)\s+CFR\s*§?\s*(\d+\.\d+)',
                'example': '28 CFR § 0.85'
            },
            
            # Washington State statutes
            {
                'name': 'RCW',
                'pattern': r'\bRCW\s*(\d+\.\d+\.\d+)',
                'example': 'RCW 9A.08.010'
            },
            {
                'name': 'WAC',
                'pattern': r'\bWAC\s*(\d+-\d+-\d+)',
                'example': 'WAC 296-800-100'
            },
            
            # Other common statutes
            {
                'name': 'Federal Rules',
                'pattern': r'\bFed\.\s*R\.\s*(?:Civ\.|Crim\.|App\.)\s*P\.\s*(\d+)',
                'example': 'Fed. R. Civ. P. 12'
            },
            {
                'name': 'Federal Rules (abbreviated)',
                'pattern': r'\bFRCP\s*(\d+)',
                'example': 'FRCP 12'
            }
        ]
    
    def is_statute_citation(self, citation_str: str) -> bool:
        """Check if a citation string is a statute citation."""
        if not self.enabled:
            return False
        
        citation_str = citation_str.strip()
        
        for pattern_info in self.statute_patterns:
            if re.search(pattern_info['pattern'], citation_str, re.IGNORECASE):
                return True
        
        return False
    
    def extract_statute_info(self, citation_str: str) -> Dict[str, Any]:
        """Extract information from a statute citation."""
        citation_str = citation_str.strip()
        
        for pattern_info in self.statute_patterns:
            match = re.search(pattern_info['pattern'], citation_str, re.IGNORECASE)
            if match:
                return {
                    'type': pattern_info['name'],
                    'pattern': pattern_info['pattern'],
                    'example': pattern_info['example'],
                    'match_groups': match.groups(),
                    'full_match': match.group(0)
                }
        
        return {}
    
    def filter_citations(self, citations: List[Dict[str, Any]], include_statutes: bool = None) -> List[Dict[str, Any]]:
        """Filter citations based on statute inclusion preference."""
        if not self.enabled:
            return citations
        
        if include_statutes is None:
            include_statutes = self.include_statutes
        
        filtered_citations = []
        
        for citation in citations:
            citation_str = citation.get('citation', '')
            is_statute = self.is_statute_citation(citation_str)
            
            # Include if it matches our preference
            if (include_statutes and is_statute) or (not include_statutes and not is_statute):
                # Add statute metadata if it's a statute
                if is_statute:
                    statute_info = self.extract_statute_info(citation_str)
                    citation['statute_info'] = statute_info
                    citation['is_statute'] = True
                else:
                    citation['is_statute'] = False
                
                filtered_citations.append(citation)
        
        return filtered_citations
    
    def enable(self):
        """Enable statute filtering."""
        self.enabled = True
    
    def disable(self):
        """Disable statute filtering."""
        self.enabled = False
    
    def set_include_statutes(self, include: bool):
        """Set whether to include or exclude statute citations."""
        self.include_statutes = include

class UnifiedCitationProcessor:
    """Unified citation processor that combines multiple extraction and verification methods."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the processor with optional API key."""
        self.api_key = api_key or get_config_value("COURTLISTENER_API_KEY")
        self.regex_extractor = EnhancedRegexExtractor()
        self.eyecite_processor = EyeciteProcessor()
        self.verifier = APIVerifier()
        self.citation_grouper = CitationGrouper()  # Add missing component
        self.statistics = CitationStatistics()
        self.cache_manager = get_cache_manager()
        
        # NEW: Debug and context configuration
        self.debug_mode = False
        self.context_window_size = 300  # Default context window
        self.verbose_logging = False
        
        # NEW: OCR correction
        self.ocr_corrector = OCRCorrector()
        self.ocr_correction_enabled = True
        
        # NEW: Confidence scoring
        self.confidence_scorer = ConfidenceScorer()
        self.confidence_scoring_enabled = True
        
        # NEW: Statute filtering
        self.statute_filter = StatuteFilter()
        self.statute_filtering_enabled = True
        self.include_statutes = False  # Default to excluding statutes
        
        logger.info("UnifiedCitationProcessor initialized")
    
    def set_debug_mode(self, enabled: bool = True, verbose: bool = False):
        """Enable or disable debug mode with optional verbose logging."""
        self.debug_mode = enabled
        self.verbose_logging = verbose
        if enabled:
            logger.info(f"Debug mode enabled (verbose: {verbose})")
    
    def set_context_window(self, size: int):
        """Set the context window size for citation extraction."""
        self.context_window_size = size
        logger.info(f"Context window size set to {size} characters")
    
    def enable_ocr_correction(self, enabled: bool = True):
        """Enable or disable OCR error correction."""
        self.ocr_correction_enabled = enabled
        if enabled:
            self.ocr_corrector.enable()
            logger.info("OCR correction enabled")
        else:
            self.ocr_corrector.disable()
            logger.info("OCR correction disabled")
    
    def enable_confidence_scoring(self, enabled: bool = True):
        """Enable or disable confidence scoring."""
        self.confidence_scoring_enabled = enabled
        if enabled:
            logger.info("Confidence scoring enabled")
        else:
            logger.info("Confidence scoring disabled")
    
    def enable_statute_filtering(self, enabled: bool = True, include_statutes: bool = False):
        """Enable or disable statute filtering and set inclusion preference."""
        self.statute_filtering_enabled = enabled
        self.include_statutes = include_statutes
        
        if enabled:
            self.statute_filter.enable()
            self.statute_filter.set_include_statutes(include_statutes)
            logger.info(f"Statute filtering enabled (include_statutes: {include_statutes})")
        else:
            self.statute_filter.disable()
            logger.info("Statute filtering disabled")
    
    def process_text(self, text: str, extract_case_names: bool = True, verify_citations: bool = True, api_key: str = None) -> Dict[str, Any]:
        """
        Process text and extract/verify citations with enhanced debugging and context.
        
        Args:
            text: Text to process
            extract_case_names: Whether to extract case names
            verify_citations: Whether to verify citations
            api_key: API key for verification services
            
        Returns:
            Dictionary with results and statistics
        """
        if not text:
            return {
                'results': [],
                'summary': {
                    'total_citations': 0,
                    'verified_citations': 0,
                    'unverified_citations': 0,
                    'unique_cases': 0
                },
                'error': 'No text provided'
            }
        
        try:
            # NEW: Debug logging
            if self.debug_mode:
                logger.info(f"Processing text of length {len(text)} characters")
                logger.info(f"Context window size: {self.context_window_size}")
                logger.info(f"Extract case names: {extract_case_names}")
                logger.info(f"Verify citations: {verify_citations}")
                logger.info(f"OCR correction enabled: {self.ocr_correction_enabled}")
                logger.info(f"Confidence scoring enabled: {self.confidence_scoring_enabled}")
                logger.info(f"Statute filtering enabled: {self.statute_filtering_enabled}")
                logger.info(f"Include statutes: {self.include_statutes}")
            
            # NEW: Apply OCR correction if enabled
            if self.ocr_correction_enabled:
                original_text = text
                text = self.ocr_corrector.correct_text(text)
                if self.debug_mode and text != original_text:
                    logger.info("OCR corrections applied to text")
                    if self.verbose_logging:
                        logger.debug(f"Original: {original_text[:100]}...")
                        logger.debug(f"Corrected: {text[:100]}...")
            
            # Clean text
            cleaned_text = TextCleaner.clean_text(text)
            if self.debug_mode:
                logger.info(f"Text cleaned, new length: {len(cleaned_text)} characters")
            
            # Extract citations using multiple methods
            citations = []
            
            # Method 1: Enhanced regex extraction
            regex_citations = self.regex_extractor.extract_citations(cleaned_text)
            citations.extend([CitationResult(**citation) for citation in regex_citations])
            
            if self.debug_mode:
                logger.info(f"Regex extraction found {len(regex_citations)} citations")
            
            # Method 2: Eyecite extraction (if available)
            if EYECITE_AVAILABLE:
                eyecite_citations = self.eyecite_processor.extract_eyecite_citations(cleaned_text)
                citations.extend(eyecite_citations)
                if self.debug_mode:
                    logger.info(f"Eyecite extraction found {len(eyecite_citations)} citations")
            
            # NEW: Enhanced context extraction with configurable window
            for citation in citations:
                if citation.start_index is not None and citation.end_index is not None:
                    context_start = max(0, citation.start_index - self.context_window_size)
                    context_end = min(len(cleaned_text), citation.end_index + self.context_window_size)
                    citation.context = cleaned_text[context_start:context_end]
                    
                    if self.debug_mode and self.verbose_logging:
                        logger.debug(f"Citation: {citation.citation}")
                        logger.debug(f"Context: {citation.context[:100]}...")

            # === NEW LOGIC: Extract and verify only individual citations, cluster for display ===
            import re
            citation_to_obj = {}
            singles = []
            clusters = []
            all_citations_by_norm = {}

            # Helper: is this a cluster (comma-separated citations)
            def is_cluster(citation_str):
                if ',' not in citation_str:
                    return False
                parts = citation_str.split(',')
                if len(parts) < 2:
                    return False
                first_part = parts[0].strip()
                if not re.match(r'^\d+\s+', first_part):
                    return False
                for part in parts[1:]:
                    part = part.strip()
                    if re.match(r'^\d+$', part) or re.match(r'^\d+\s+', part):
                        return True
                return False

            # Helper: expand cluster into all its component citations
            def extract_cluster_members(cluster_str):
                parts = [p.strip() for p in cluster_str.split(',')]
                if len(parts) < 2:
                    return [cluster_str]
                base = parts[0]
                members = []
                # If subsequent parts are just numbers, treat as pinpoints
                for part in parts[1:]:
                    if re.match(r'^\d+$', part):
                        # e.g. 171 Wn.2d 486, 493 => 171 Wn.2d 493
                        base_match = re.match(r'^(\d+\s+[A-Za-z\.]+\s+)', base)
                        if base_match:
                            members.append(f"{base_match.group(1)}{part}")
                    elif re.match(r'^\d+\s+[A-Za-z\.]+\s+\d+$', part):
                        members.append(part)
                # Always include the base
                members.insert(0, base)
                return members

            # First pass: classify and map all citations
            for citation in citations:
                norm = self._normalize_citation(citation.citation)
                if norm not in all_citations_by_norm:
                    all_citations_by_norm[norm] = []
                all_citations_by_norm[norm].append(citation)
                
                # Check if this is a cluster (either by string pattern or metadata)
                if is_cluster(citation.citation) or citation.metadata.get('is_cluster', False):
                    clusters.append(citation)
                    if citation.metadata.get('cluster_members'):
                        citation.cluster_members = citation.metadata['cluster_members']
                    else:
                        members = extract_cluster_members(citation.citation)
                        citation.cluster_members = members
                    citation.is_cluster = True
                    
                    if self.debug_mode:
                        logger.info(f"Detected cluster: {citation.citation}")
                        logger.info(f"Cluster members: {citation.cluster_members}")
                else:
                    singles.append(citation)
                    citation_to_obj[norm] = citation
                    citation.is_cluster = False
                    citation.cluster_members = []

            # Second pass: deduplicate - keep only singles (individual citations)
            deduped_citations = []
            seen_norms = set()
            for citation in singles:
                norm = self._normalize_citation(citation.citation)
                if norm not in seen_norms:
                    deduped_citations.append(citation)
                    seen_norms.add(norm)
            unique_citations = deduped_citations
            unique_citations.sort(key=lambda x: x.start_index or 0)
            
            if self.debug_mode:
                logger.info(f"Unique individual citations: {len(unique_citations)}")
                logger.info(f"Clusters detected: {len(clusters)}")

            # NEW: Apply statute filtering
            if self.statute_filtering_enabled:
                # Convert citations to dict format for filtering
                citation_dicts = []
                for citation in unique_citations:
                    citation_dict = {
                        'citation': citation.citation,
                        'start_index': citation.start_index,
                        'end_index': citation.end_index,
                        'context': citation.context,
                        'method': citation.method,
                        'pattern': citation.pattern
                    }
                    citation_dicts.append(citation_dict)
                
                filtered_dicts = self.statute_filter.filter_citations(
                    citation_dicts, self.include_statutes
                )
                
                # Update citations with statute info
                for citation in unique_citations:
                    for filtered_dict in filtered_dicts:
                        if filtered_dict['citation'] == citation.citation:
                            citation.is_statute = filtered_dict.get('is_statute', False)
                            citation.statute_info = filtered_dict.get('statute_info', {})
                            break
                
                if self.debug_mode:
                    statute_count = sum(1 for c in unique_citations if getattr(c, 'is_statute', False))
                    logger.info(f"Statute citations found: {statute_count}")

            # Extract case names and verify only for individual citations
            if extract_case_names or verify_citations:
                for citation in unique_citations:
                    if citation.start_index is not None and citation.end_index is not None:
                        # Use the enhanced context window
                        context_start = max(0, citation.start_index - self.context_window_size)
                        context_end = min(len(cleaned_text), citation.end_index + self.context_window_size)
                        context = cleaned_text[context_start:context_end]
                        
                        if self.debug_mode and self.verbose_logging:
                            logger.debug(f"Processing citation: {citation.citation}")
                            logger.debug(f"Context window: {len(context)} characters")
                        
                        if extract_case_names:
                            try:
                                extraction_result = extract_case_name_triple(
                                    text=context,
                                    citation=citation.citation,
                                    api_key=api_key or self.api_key,
                                    context_window=self.context_window_size
                                )
                                if extraction_result:
                                    citation.extracted_case_name = (
                                        extraction_result.get("extracted_name") or
                                        extraction_result.get("case_name") or
                                        extraction_result.get("extracted_case_name")
                                    )
                                    citation.extracted_date = (
                                        extraction_result.get("extracted_date") or
                                        extraction_result.get("date") or
                                        extraction_result.get("year")
                                    )
                                    citation.canonical_name = extraction_result.get("canonical_name")
                                    citation.canonical_date = extraction_result.get("canonical_date")
                                    if citation.canonical_name:
                                        citation.verified = True
                                        citation.confidence = extraction_result.get("case_name_confidence", 0.9)
                                        citation.source = "CourtListener"
                                        
                                        if self.debug_mode:
                                            logger.info(f"Verified citation: {citation.citation} -> {citation.canonical_name}")
                            except Exception as e:
                                logger.warning(f"Case name extraction failed for {citation.citation}: {e}")
                                if self.debug_mode:
                                    logger.error(f"Extraction error details: {e}")
                        if verify_citations and not citation.verified:
                            try:
                                verification_result = self.verify_citation_unified_workflow(citation.citation)
                                if verification_result.get('verified'):
                                    citation.verified = True
                                    citation.canonical_name = verification_result.get('case_name')
                                    citation.canonical_date = verification_result.get('year')
                                    citation.source = verification_result.get('verified_by', 'Unknown')
                                    citation.confidence = verification_result.get('confidence', 0.8)
                                    
                                    if self.debug_mode:
                                        logger.info(f"Verified citation: {citation.citation} -> {citation.canonical_name}")
                            except Exception as e:
                                logger.warning(f"Citation verification failed for {citation.citation}: {e}")
                                if self.debug_mode:
                                    logger.error(f"Verification error details: {e}")
                        
                        # NEW: Calculate confidence score if enabled
                        if self.confidence_scoring_enabled:
                            citation_dict = {
                                'citation': citation.citation,
                                'method': citation.method,
                                'pattern': citation.pattern,
                                'verified': citation.verified,
                                'source': citation.source,
                                'confidence': citation.confidence,
                                'extracted_case_name': citation.extracted_case_name,
                                'canonical_name': citation.canonical_name,
                                'extracted_date': citation.extracted_date,
                                'canonical_date': citation.canonical_date
                            }
                            calculated_confidence = self.confidence_scorer.calculate_citation_confidence(
                                citation_dict, citation.context
                            )
                            citation.confidence = calculated_confidence
                            
                            if self.debug_mode and self.verbose_logging:
                                logger.debug(f"Confidence score for {citation.citation}: {calculated_confidence:.3f}")

            # Group for display: clusters reference their member citations (by normalized form)
            # API output: clusters have is_cluster/cluster_members, but canonical/verification comes from individuals
            # (Frontend can use cluster_members to group for display)
            # Format results for frontend
            formatted_results = []
            # Add all singles (individuals)
            for citation in unique_citations:
                formatted_results.append({
                    'citation': citation.citation,
                    'is_cluster': False,
                    'cluster_members': [],
                    'extracted_case_name': citation.extracted_case_name or 'N/A',
                    'extracted_date': citation.extracted_date or 'N/A',
                    'canonical_name': citation.canonical_name or 'N/A',
                    'canonical_date': citation.canonical_date or 'N/A',
                    'verified': citation.verified,
                    'confidence': citation.confidence,
                    'source': citation.source,
                    'url': citation.url,
                    'error': citation.error,
                    'start_index': citation.start_index,
                    'end_index': citation.end_index,
                    'pinpoint_pages': citation.pinpoint_pages or [],
                    'docket_numbers': citation.docket_numbers or [],
                    'case_history': citation.case_history or [],
                    'publication_status': citation.publication_status or '',
                    'context': citation.context or '',
                    'is_statute': getattr(citation, 'is_statute', False),
                    'statute_info': getattr(citation, 'statute_info', {})
                })
            # Add clusters for display (metadata only)
            for cluster in clusters:
                formatted_results.append({
                    'citation': cluster.citation,
                    'is_cluster': True,
                    'cluster_members': cluster.cluster_members or [],
                    'extracted_case_name': cluster.extracted_case_name or 'N/A',
                    'extracted_date': cluster.extracted_date or 'N/A',
                    'canonical_name': None,  # Clusters don't get verified
                    'canonical_date': None,
                    'verified': None,
                    'confidence': None,
                    'source': None,
                    'url': None,
                    'error': None,
                    'start_index': cluster.start_index,
                    'end_index': cluster.end_index,
                    'pinpoint_pages': cluster.pinpoint_pages or [],
                    'docket_numbers': cluster.docket_numbers or [],
                    'case_history': cluster.case_history or [],
                    'publication_status': cluster.publication_status or '',
                    'context': cluster.context or '',
                    'is_statute': getattr(cluster, 'is_statute', False),
                    'statute_info': getattr(cluster, 'statute_info', {})
                })

            # Calculate statistics
            self._calculate_statistics(unique_citations)
            
            if self.debug_mode:
                logger.info(f"Final results: {len(formatted_results)} total entries")
                logger.info(f"Statistics: {self.statistics}")

            return {
                'results': formatted_results,
                'summary': {
                    'total_citations': self.statistics.total_citations,
                    'parallel_citations': self.statistics.parallel_citations,
                    'verified_citations': self.statistics.verified_citations,
                    'unverified_citations': self.statistics.unverified_citations,
                    'unique_cases': self.statistics.unique_cases,
                    'complex_citations': self.statistics.complex_citations
                },
                'statistics': self.statistics,
                'metadata': {
                    'text_length': len(text),
                    'processing_time': time.time(),
                    'methods_used': ['regex', 'eyecite'] if EYECITE_AVAILABLE else ['regex'],
                    'debug_mode': self.debug_mode,
                    'context_window_size': self.context_window_size,
                    'ocr_correction_enabled': self.ocr_correction_enabled,
                    'confidence_scoring_enabled': self.confidence_scoring_enabled,
                    'statute_filtering_enabled': self.statute_filtering_enabled,
                    'include_statutes': self.include_statutes
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing text: {e}")
            if self.debug_mode:
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                'results': [],
                'summary': {'total_citations': 0},
                'error': str(e)
            }
    
    def extract_regex_citations(self, text: str) -> List[CitationResult]:
        """Extract citations using enhanced regex patterns."""
        regex_citations = self.regex_extractor.extract_citations(text)
        return [CitationResult(**citation) for citation in regex_citations]
    
    def verify_citation_unified_workflow(self, citation: str) -> Dict[str, Any]:
        """
        Verify a citation using the unified workflow.
        
        This method combines multiple verification sources:
        1. Cache check
        2. CourtListener API
        3. Landmark cases database
        4. Fuzzy matching
        """
        # Check cache first
        cached_result = self._check_cache(citation)
        if cached_result:
            return cached_result
        
        # Initialize result
        result = {
            'citation': citation,
            'verified': False,
            'verified_by': None,
            'case_name': None,
            'court': None,
            'year': None,
            'confidence': 0.0,
            'sources': {},
            'error': None
        }
        
        try:
            # Try CourtListener API
            cl_result = self._verify_with_courtlistener(citation)
            result['sources']['courtlistener'] = cl_result
            if cl_result.get('verified'):
                result.update(cl_result)
                result['verified'] = True
                result['verified_by'] = 'CourtListener'
                self._save_to_cache(citation, result)
                return result
            
            # Try landmark cases
            landmark_result = self._verify_with_landmark_cases(citation)
            result['sources']['landmark_cases'] = landmark_result
            if landmark_result.get('verified'):
                result.update(landmark_result)
                result['verified'] = True
                result['verified_by'] = 'Landmark Cases'
                self._save_to_cache(citation, result)
                return result
            
            # Try fuzzy matching
            fuzzy_result = self._verify_with_fuzzy_matching(citation)
            result['sources']['fuzzy_matching'] = fuzzy_result
            if fuzzy_result.get('verified'):
                result.update(fuzzy_result)
                result['verified'] = True
                result['verified_by'] = 'Fuzzy Matching'
                self._save_to_cache(citation, result)
                return result
            
            # If no verification succeeded, save negative result
            result['error'] = 'Citation not found in any source'
            self._save_to_cache(citation, result)
            return result
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error in unified verification workflow for {citation}: {e}")
            return result
    
    def batch_verify_citations(self, citations: List[str]) -> List[Dict[str, Any]]:
        """Verify a batch of citations."""
        results = []
        
        for citation in citations:
            result = self.verify_citation_unified_workflow(citation)
            results.append(result)
            
            # Add delay to avoid rate limiting
            time.sleep(0.1)
        
        return results
    
    def _deduplicate_citations(self, citations: List[CitationResult]) -> List[CitationResult]:
        """Remove duplicate citations based on citation text."""
        seen = set()
        unique_citations = []
        
        for citation in citations:
            if citation.citation not in seen:
                seen.add(citation.citation)
                unique_citations.append(citation)
        
        return unique_citations
    
    def _calculate_statistics(self, citations: List[CitationResult]):
        """Calculate statistics from citations."""
        self.statistics = CitationStatistics()
        self.statistics.total_citations = len(citations)
        
        for citation in citations:
            if citation.verified:
                self.statistics.verified_citations += 1
            else:
                self.statistics.unverified_citations += 1
            
            if citation.is_parallel:
                self.statistics.parallel_citations += 1
                self.statistics.individual_parallel_citations += len(citation.parallel_citations or [])
            
            if citation.is_complex:
                self.statistics.complex_citations += 1
        
        # Count unique cases
        case_names = set()
        for citation in citations:
            if citation.case_name:
                case_names.add(citation.case_name)
            elif citation.extracted_case_name:
                case_names.add(citation.extracted_case_name)
        
        self.statistics.unique_cases = len(case_names)
    
    def _format_results_for_frontend(self, grouped_citations: List[List[CitationResult]]) -> List[Dict[str, Any]]:
        """Format citation results for frontend display."""
        formatted_results = []
        
        for group in grouped_citations:
            if not group:
                continue
            
            # Use the first citation as the primary one
            primary = group[0]
            
            formatted_result = {
                'citation': primary.citation,
                'case_name': primary.case_name or primary.extracted_case_name or 'N/A',
                'extracted_case_name': primary.extracted_case_name or 'N/A',
                'extracted_date': primary.extracted_date or 'N/A',
                'canonical_name': primary.canonical_name or 'N/A',
                'canonical_date': primary.canonical_date or 'N/A',
                'verified': primary.verified,
                'confidence': primary.confidence,
                'source': primary.source,
                'url': primary.url,
                'error': primary.error,
                'explanation': None,
                'parallel_citations': [c.citation for c in group[1:]] if len(group) > 1 else [],
                'display_text': self._create_display_text(primary, group)
            }
            
            formatted_results.append(formatted_result)
        
        return formatted_results
    
    def _create_display_text(self, primary: CitationResult, group: List[CitationResult]) -> str:
        """Create display text for a citation group."""
        if len(group) == 1:
            return primary.citation
        
        # For parallel citations, show primary + parallel
        parallel_text = ', '.join([c.citation for c in group[1:]])
        return f"{primary.citation}, {parallel_text}"
    
    def _process_text_in_chunks(self, text: str, chunk_size: int = 50000, 
                               extract_case_names: bool = True) -> Dict[str, Any]:
        """Process large text in chunks for memory efficiency."""
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        all_results = []
        total_citations = 0
        
        for i, chunk in enumerate(chunks):
            chunk_result = self.process_text(chunk, extract_case_names=extract_case_names)
            all_results.extend(chunk_result.get('results', []))
            total_citations += chunk_result.get('summary', {}).get('total_citations', 0)
        
        return {
            'results': all_results,
            'statistics': CitationStatistics(total_citations=total_citations),
            'metadata': {
                'chunks_processed': len(chunks),
                'chunk_size': chunk_size
            }
        }
    
    # Delegate methods to existing components
    def _check_cache(self, citation: str) -> Optional[Dict]:
        """Check cache for citation verification result."""
        return self.citation_grouper._check_cache(citation)
    
    def _save_to_cache(self, citation: str, result: Dict):
        """Save citation verification result to cache."""
        self.citation_grouper._save_to_cache(citation, result)
    
    def _verify_with_courtlistener(self, citation: str) -> Dict:
        """Verify citation with CourtListener API."""
        return self.citation_grouper._verify_with_courtlistener(citation)
    
    def _verify_with_landmark_cases(self, citation: str) -> Dict:
        """Verify citation with landmark cases database."""
        return self.citation_grouper._verify_with_landmark_cases(citation)
    
    def _verify_with_fuzzy_matching(self, citation: str) -> Dict:
        """Verify citation using fuzzy matching."""
        return self.citation_grouper._verify_with_fuzzy_matching(citation)
    
    def _normalize_citation(self, citation: str) -> str:
        """Normalize citation format."""
        return self.citation_grouper._normalize_citation(citation)
    
    def _extract_citation_components(self, citation: str) -> Dict[str, str]:
        """Extract components from citation."""
        return self.citation_grouper._extract_citation_components(citation)

unified_processor = UnifiedCitationProcessor()

# === DEBUGGING INTEGRATION ===
import logging
from typing import List

# --- BEGIN ExtractionDebugger ---
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
import json
from datetime import datetime

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("citation_debug")

class ExtractionDebugger:
    """
    Comprehensive debugging tool for your unified citation extraction pipeline
    """
    def __init__(self):
        self.debug_log = []
        self.extraction_results = {}
    def log_step(self, step: str, data: Any, level: str = "info"):
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "step": step,
            "data": data,
            "level": level
        }
        self.debug_log.append(log_entry)
        if level == "error":
            logger.error(f"{step}: {data}")
        elif level == "warning":
            logger.warning(f"{step}: {data}")
        else:
            logger.info(f"{step}: {data}")
    def debug_unified_pipeline(self, text: str, citations: List[str], api_key: str = None) -> Dict:
        self.log_step("PIPELINE_START", {
            "text_length": len(text),
            "citation_count": len(citations),
            "citations": citations
        })
        results = {
            "input": {
                "text_preview": text[:300] + "..." if len(text) > 300 else text,
                "citations": citations
            },
            "extraction_results": {},
            "debug_info": {},
            "issues_found": [],
            "recommendations": []
        }
        for i, citation in enumerate(citations):
            self.log_step(f"PROCESSING_CITATION_{i}", citation)
            citation_result = self._debug_single_citation(text, citation, api_key)
            results["extraction_results"][citation] = citation_result
        results["debug_info"] = self._analyze_results(results["extraction_results"])
        results["issues_found"] = self._identify_issues(results["extraction_results"])
        results["recommendations"] = self._generate_recommendations(results["issues_found"])
        return results
    def _debug_single_citation(self, text: str, citation: str, api_key: str = None) -> Dict:
        result = {
            "citation": citation,
            "stages": {},
            "final_result": {},
            "confidence_scores": {},
            "extraction_methods": {}
        }
        # Stage 1: Citation Location Analysis
        idx = text.find(citation)
        context = text[max(0, idx-300):idx+len(citation)+300] if idx != -1 else text
        result["stages"]["context"] = context
        self.log_step("CONTEXT_WINDOW", {"citation": citation, "context": context})
        # Stage 2: Case Name Extraction
        try:
            from .case_name_extraction_core import extract_case_name_triple
            case_name_result = extract_case_name_triple(text, citation, api_key=api_key, context_window=300)
            result["stages"]["case_name"] = case_name_result
            self.log_step("CASE_NAME_EXTRACTION", case_name_result)
        except Exception as e:
            result["stages"]["case_name"] = {"error": str(e)}
            self.log_step("CASE_NAME_EXTRACTION_ERROR", str(e), level="error")
        # Stage 3: Date Extraction
        try:
            from .enhanced_extraction_utils import extract_year_enhanced
            year_result = extract_year_enhanced(text, citation)
            result["stages"]["date"] = year_result
            self.log_step("DATE_EXTRACTION", year_result)
        except Exception as e:
            result["stages"]["date"] = {"error": str(e)}
            self.log_step("DATE_EXTRACTION_ERROR", str(e), level="error")
        # Stage 4: Canonical Lookup (use real verification workflow)
        try:
            try:
                from unified_citation_processor_v2 import UnifiedCitationProcessorV2
            except ImportError:
                # Fallback if relative import fails
                import sys
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
                from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
                
            processor = UnifiedCitationProcessorV2()
            verification_result = processor.verify_citation_unified_workflow(citation)
            
            result["stages"]["canonical_lookup"] = {
                "verified": verification_result.get("verified", False),
                "canonical_name": verification_result.get("canonical_name"),
                "canonical_date": verification_result.get("canonical_date"),
                "url": verification_result.get("url"),
                "source": verification_result.get("verified_by"),
                "confidence": verification_result.get("confidence", 0.0)
            }
            self.log_step("CANONICAL_LOOKUP", result["stages"]["canonical_lookup"])
        except Exception as e:
            result["stages"]["canonical_lookup"] = {"error": str(e)}
            self.log_step("CANONICAL_LOOKUP_ERROR", str(e), level="error")
        # Final result summary
        result["final_result"] = {
            "case_name": result["stages"].get("case_name"),
            "date": result["stages"].get("date"),
            "canonical": result["stages"].get("canonical_lookup")
        }
        return result
    def _analyze_results(self, extraction_results: Dict) -> Dict:
        # Simple analysis: check for missing names/dates
        issues = {}
        for citation, res in extraction_results.items():
            if not res["final_result"].get("case_name"):
                issues[citation] = issues.get(citation, []) + ["Missing case name"]
            if not res["final_result"].get("date"):
                issues[citation] = issues.get(citation, []) + ["Missing date"]
        return issues
    def _identify_issues(self, extraction_results: Dict) -> List[str]:
        issues = []
        for citation, res in extraction_results.items():
            if not res["final_result"].get("case_name"):
                issues.append(f"Citation {citation}: Missing case name")
            if not res["final_result"].get("date"):
                issues.append(f"Citation {citation}: Missing date")
        return issues
    def _generate_recommendations(self, issues: List[str]) -> List[str]:
        recs = []
        for issue in issues:
            if "Missing case name" in issue:
                recs.append("Check case name extraction regex and context window.")
            if "Missing date" in issue:
                recs.append("Check date extraction patterns and context window.")
        return recs
    def print_debug_report(self, results: Dict):
        logger.debug("\n=== Extraction Debug Report ===")
        logger.info(json.dumps(results, indent=2, default=str))
        logger.debug("\n=== Debug Log ===")
        for entry in self.debug_log:
            logger.info(f"[{entry['timestamp']}] {entry['level'].upper()} {entry['step']}: {entry['data']}")

# Usage example for integration
def debug_extraction_pipeline(text: str, citations: List[str], api_key: str = None):
    """Debug the extraction pipeline for a given text and citations."""
    debugger = ExtractionDebugger()
    return debugger.debug_unified_pipeline(text, citations, api_key)

if __name__ == "__main__":
    # Example: Use a real-world test case
    sample_text = '''
    Cockel v. Dep't of Lab. & Indus.,
    142 Wn.2d 801, 808, 16 P.3d 583 (2002)
    '''
    sample_citations = ["142 Wn.2d 801", "16 P.3d 583"]
    logger.debug("Running extraction debugger on sample input...")
    debug_extraction_pipeline(sample_text, sample_citations)

def safe_set_extracted_date(citation, new_date, source="unknown"):
    """Safely set extracted_date, preserving existing good values."""
    if not new_date:  # Don't overwrite with empty values
        logger.debug(f"Skipping empty date from {source} for {citation.citation}")
        return False
        
    if citation.extracted_date and len(str(citation.extracted_date)) >= len(str(new_date)):
        logger.debug(f"Keeping existing date {citation.extracted_date} over {new_date}")
        return False
        
    logger.info(f"Setting extracted_date to {new_date} from {source}")
    citation.extracted_date = new_date
    return True

def validate_citation_dates(citation):
    """Validate date fields haven't been corrupted."""
    issues = []
    
    if hasattr(citation, 'extracted_date'):
        if citation.extracted_date == "":
            issues.append("extracted_date is empty string (should be None or valid date)")
        if citation.extracted_date == "N/A":
            issues.append("extracted_date is 'N/A' (should be None)")
            
    if issues:
        logger.warning(f"Date validation issues for {citation.citation}: {issues}")
    
    return len(issues) == 0

# Add tracing for extracted_date assignments
original_setattr = None
def setup_date_tracing():
    """Setup tracing for extracted_date assignments to debug overwrites."""
    global original_setattr
    if original_setattr is None:
        original_setattr = CitationResult.__setattr__
        def traced_setattr(self, name, value):
            if name == 'extracted_date':
                caller = inspect.stack()[1]
                logger.debug(f"Setting extracted_date to '{value}' from {caller.filename}:{caller.lineno}")
            return original_setattr(self, name, value)
        CitationResult.__setattr__ = traced_setattr

def extract_case_name_with_better_boundaries(context, citation_position):
    """Extract case name with precise boundaries."""
    # Look backwards from citation for case name patterns
    case_patterns = [
        r'\b([A-Z][a-zA-Z&., ]+ v\. [A-Z][a-zA-Z&., ]+),?\s*$',
        r'\b(State v\. [A-Z][a-zA-Z&., ]+),?\s*$',
        r'\b(People v\. [A-Z][a-zA-Z&., ]+),?\s*$',
        r'\b(In re [A-Z][a-zA-Z&., ]+),?\s*$',
        r'\b(Department of [A-Z][a-zA-Z&., ]+ v\. [A-Z][a-zA-Z&., ]+),?\s*$'
    ]
    # Search in the last 100 characters before citation
    search_text = context[-100:] if len(context) > 100 else context
    for pattern in case_patterns:
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            case_name = match.group(1).strip().rstrip(',')
            # Validate length and format
            if 5 <= len(case_name) <= 100 and ' v. ' in case_name:
                return case_name
    return None

def group_parallel_citations(self, citations: List[CitationResult]) -> List[CitationResult]:
    """
    Group citations that are likely parallel citations for the same case.
    Enhanced to detect citations that appear together in the same context.
    """
    if not citations:
        return citations
    
    grouped = []  # Ensure grouped is defined
    processed = set()