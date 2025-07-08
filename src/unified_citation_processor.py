#!/usr/bin/env python3
"""
Unified Citation Processor for CaseStrainer

This module provides a comprehensive citation processing system that combines
all citation handling capabilities into a single, unified solution.

Features:
- Complex citation detection and parsing
- Parallel citation handling
- Eyecite integration
- API verification (CourtListener)
- Case name extraction and grouping
- Statistics calculation
- Frontend formatting
- Caching and batch processing
- Enhanced text cleaning and preprocessing
- Comprehensive regex patterns
- Date extraction from context
- Streaming support for large documents
"""

import re
import time
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import unicodedata
import json
from datetime import datetime

# Import existing components to merge
try:
    from eyecite import get_citations, resolve_citations, clean_text
    from eyecite.tokenizers import AhocorasickTokenizer
    EYECITE_AVAILABLE = True
except ImportError:
    EYECITE_AVAILABLE = False

from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
from src.cache_manager import get_cache_manager
from src.config import get_config_value
from src.enhanced_case_name_extractor import EnhancedCaseNameExtractor
from src.case_name_extraction_core import extract_case_name_triple
import warnings

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
            # Washington patterns
            'wn_app': r'\b(\d+)\s+Wn\.\s*App\.\s+(\d+)\b',
            'wn2d': r'\b(\d+)\s+Wn\.2d\s+(\d+)\b',
            'wash2d': r'\b(\d+)\s+Wash\.\s*2d\s+(\d+)\b',
            'wash_app': r'\b(\d+)\s+Wash\.\s*App\.\s+(\d+)\b',
            # Pacific Reporter patterns
            'p3d': r'\b(\d+)\s+P\.3d\s+(\d+)\b',
            'p2d': r'\b(\d+)\s+P\.2d\s+(\d+)\b',
            # Federal patterns
            'us': r'\b(\d+)\s+U\.\s*S\.\s+(\d+)\b',
            'f3d': r'\b(\d+)\s+F\.3d\s+(\d+)\b',
            'f2d': r'\b(\d+)\s+F\.2d\s+(\d+)\b',
            'f_supp': r'\b(\d+)\s+F\.\s*Supp\.\s+(\d+)\b',
            'f_supp2d': r'\b(\d+)\s+F\.\s*Supp\.\s*2d\s+(\d+)\b',
            # Supreme Court patterns
            's_ct': r'\b(\d+)\s+S\.\s*Ct\.\s+(\d+)\b',
            'l_ed': r'\b(\d+)\s+L\.\s*Ed\.\s+(\d+)\b',
            'l_ed2d': r'\b(\d+)\s+L\.\s*Ed\.\s*2d\s+(\d+)\b',
            # Atlantic Reporter patterns
            'a2d': r'\b(\d+)\s+A\.2d\s+(\d+)\b',
            'a3d': r'\b(\d+)\s+A\.3d\s+(\d+)\b',
            # Southern Reporter patterns
            'so2d': r'\b(\d+)\s+So\.\s*2d\s+(\d+)\b',
            'so3d': r'\b(\d+)\s+So\.\s*3d\s+(\d+)\b',
            # Additional variants for robustness
            'wash_2d_alt': r'\b(\d+)\s+Wash\.\s*2d\s+(\d+)\b',
            'wash_app_alt': r'\b(\d+)\s+Wash\.\s*App\.\s+(\d+)\b',
            'wn2d_alt': r'\b(\d+)\s+Wn\.2d\s+(\d+)\b',
            'wn_app_alt': r'\b(\d+)\s+Wn\.\s*App\.\s+(\d+)\b',
            'p3d_alt': r'\b(\d+)\s+P\.3d\s+(\d+)\b',
            'p2d_alt': r'\b(\d+)\s+P\.2d\s+(\d+)\b',
        }
        
        # Enhanced case name pattern (from enhanced_citation_processor)
        self.case_name_pattern = r'\b([A-Z][A-Za-z\s\.,&\'\"\(\)]+v\.\s+[A-Z][A-Za-z\s\.,&\'\"\(\)]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)'
        
        # Enhanced pinpoint page pattern
        self.pinpoint_pattern = r',\s*(\d+)(?=\s*[,;]|\s*\(|\s*$)'
        
        # Enhanced docket number pattern
        self.docket_pattern = r'No\.\s*([0-9\-]+)'
        
        # Enhanced case history pattern
        self.history_pattern = r'\(([A-Za-z\s]+(?:I|II|III|IV|V|VI|VII|VIII|IX|X))\)'
        
        # Enhanced publication status pattern
        self.status_pattern = r'\((unpublished|published|memorandum|per\s+curiam)\)'
        
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
        citations = []
        seen = set()
        
        for name, pattern in self.primary_patterns.items():
            try:
                matches = list(pattern.finditer(text))
                for match in matches:
                    citation_str = match.group(0)
                    if citation_str in seen:
                        continue
                    seen.add(citation_str)
                    
                    # Extract date from context if available
                    extracted_date = None
                    if match.start() is not None and match.end() is not None:
                        extracted_date = DateExtractor.extract_date_from_context(
                            text, match.start(), match.end()
                        )
                    
                    # Extract context around citation
                    context_start = max(0, match.start() - 200)
                    context_end = min(len(text), match.end() + 200)
                    context = text[context_start:context_end]
                    
                    citation = {
                        'citation': citation_str,
                        'method': 'regex',
                        'pattern': name,
                        'confidence': 0.7,
                        'start_index': match.start(),
                        'end_index': match.end(),
                        'context': context,
                        'year': extracted_date.split('-')[0] if extracted_date else None,
                        'metadata': {
                            'extracted_date': extracted_date,
                            'pattern_name': name
                        }
                    }
                    citations.append(citation)
                    
            except Exception as e:
                logger.warning(f"Regex extraction failed for {name}: {e}")
        
        return citations

class ComplexCitationDetector:
    """Detects and parses complex citation patterns."""
    
    def __init__(self):
        self._init_patterns()
    
    def _init_patterns(self):
        """Initialize regex patterns for different citation components."""
        
        # Enhanced primary citation patterns with comprehensive coverage
        self.primary_patterns = {
            # Washington jurisdiction patterns
            'wn_app': r'\b(\d+)\s+Wn\.\s*App\.\s+(\d+)\b',
            'wn2d': r'\b(\d+)\s+Wn\.2d\s+(\d+)\b',
            'wn3d': r'\b(\d+)\s+Wn\.3d\s+(\d+)\b',
            'wn_generic': r'\b(\d+)\s+Wn\.\s+(\d+)\b',
            'wash': r'\b(\d+)\s+Wash\.\s+(\d+)\b',
            'wash_app': r'\b(\d+)\s+Wash\.\s*App\.\s+(\d+)\b',
            'wash2d': r'\b(\d+)\s+Wash\.2d\s+(\d+)\b',
            
            # Pacific Reporter patterns
            'p3d': r'\b(\d+)\s+P\.3d\s+(\d+)\b',
            'p2d': r'\b(\d+)\s+P\.2d\s+(\d+)\b',
            'p_generic': r'\b(\d+)\s+P\.\s+(\d+)\b',
            
            # Federal patterns
            'us': r'\b(\d+)\s+U\.\s*S\.\s+(\d+)\b',
            'us_alt': r'\b(\d+)\s+United\s+States\s+(\d+)\b',
            'f3d': r'\b(\d+)\s+F\.3d\s+(\d+)\b',
            'f2d': r'\b(\d+)\s+F\.2d\s+(\d+)\b',
            'f4th': r'\b(\d+)\s+F\.4th\s+(\d+)\b',
            'f_supp': r'\b(\d+)\s+F\.\s*Supp\.\s+(\d+)\b',
            'f_supp2d': r'\b(\d+)\s+F\.\s*Supp\.\s*2d\s+(\d+)\b',
            'f_supp3d': r'\b(\d+)\s+F\.\s*Supp\.\s*3d\s+(\d+)\b',
            
            # Supreme Court patterns
            'sct': r'\b(\d+)\s+S\.\s*Ct\.\s+(\d+)\b',
            'sct_alt': r'\b(\d+)\s+Sup\.\s*Ct\.\s+(\d+)\b',
            
            # Lawyers' Edition
            'led': r'\b(\d+)\s+L\.\s*Ed\.\s+(\d+)\b',
            'led2d': r'\b(\d+)\s+L\.\s*Ed\.\s*2d\s+(\d+)\b',
            
            # Regional Reporters
            'a2d': r'\b(\d+)\s+A\.2d\s+(\d+)\b',
            'a3d': r'\b(\d+)\s+A\.3d\s+(\d+)\b',
            'ne2d': r'\b(\d+)\s+N\.E\.2d\s+(\d+)\b',
            'ne3d': r'\b(\d+)\s+N\.E\.3d\s+(\d+)\b',
            'nw2d': r'\b(\d+)\s+N\.W\.2d\s+(\d+)\b',
            'nw3d': r'\b(\d+)\s+N\.W\.3d\s+(\d+)\b',
            'se2d': r'\b(\d+)\s+S\.E\.2d\s+(\d+)\b',
            'se3d': r'\b(\d+)\s+S\.E\.3d\s+(\d+)\b',
            'sw2d': r'\b(\d+)\s+S\.W\.2d\s+(\d+)\b',
            'sw3d': r'\b(\d+)\s+S\.W\.3d\s+(\d+)\b',
            
            # California Reports
            'cal2d': r'\b(\d+)\s+Cal\.2d\s+(\d+)\b',
            'cal3d': r'\b(\d+)\s+Cal\.3d\s+(\d+)\b',
            'cal4th': r'\b(\d+)\s+Cal\.4th\s+(\d+)\b',
            
            # Westlaw and LEXIS
            'westlaw': r'\b(\d{4})\s+WL\s+(\d+)\b',
            'lexis': r'\b(\d{4})\s+[A-Za-z\.\s]+LEXIS\s+(\d+)\b',
            
            # State Reports (generic pattern)
            'state': r'\b(\d+)\s+[A-Z][a-z]+\.\s+(\d+)\b',
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
            
            group = [citation]
            processed.add(i)
            
            # Find similar citations
            for j, other in enumerate(citations):
                if j in processed:
                    continue
                
                if self._are_same_case(citation, other):
                    group.append(other)
                    processed.add(j)
            
            groups.append(group)
        
        return groups
    
    def _are_same_case(self, citation1: CitationResult, citation2: CitationResult) -> bool:
        """Check if two citations refer to the same case."""
        # Check case names
        if citation1.case_name and citation2.case_name:
            if self._normalize_case_name(citation1.case_name) == self._normalize_case_name(citation2.case_name):
                return True
        
        # Check URLs
        if citation1.url and citation2.url:
            if citation1.url == citation2.url:
                return True
        
        # Check docket numbers
        if citation1.docket_number and citation2.docket_number:
            if citation1.docket_number == citation2.docket_number:
                return True
        
        return False
    
    def _normalize_case_name(self, case_name: str) -> str:
        """Normalize case name for comparison."""
        if not case_name:
            return ""
        
        normalized = case_name.lower()
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized

class UnifiedCitationProcessor:
    """
    Unified citation processing system that combines all citation handling capabilities.
    """
    
    def __init__(self):
        self.complex_detector = ComplexCitationDetector()
        self.eyecite_processor = EyeciteProcessor()
        self.api_verifier = APIVerifier()
        # DEPRECATED: self.case_name_extractor = CaseNameExtractor()
        self.citation_grouper = CitationGrouper()
        self.verifier = EnhancedMultiSourceVerifier()
        self.cache_manager = get_cache_manager()
        self._init_patterns()
        warnings.warn("CaseNameExtractor is deprecated. Use extract_case_name_triple from src.case_name_extraction_core instead.", DeprecationWarning)
    
    def _init_patterns(self):
        """Initialize regex patterns for different citation components."""
        
        # Enhanced primary citation patterns with comprehensive coverage
        self.primary_patterns = {
            # Washington jurisdiction patterns
            'wn_app': r'\b(\d+)\s+Wn\.\s*App\.\s+(\d+)\b',
            'wn2d': r'\b(\d+)\s+Wn\.2d\s+(\d+)\b',
            'wn3d': r'\b(\d+)\s+Wn\.3d\s+(\d+)\b',
            'wn_generic': r'\b(\d+)\s+Wn\.\s+(\d+)\b',
            'wash': r'\b(\d+)\s+Wash\.\s+(\d+)\b',
            'wash_app': r'\b(\d+)\s+Wash\.\s*App\.\s+(\d+)\b',
            'wash2d': r'\b(\d+)\s+Wash\.2d\s+(\d+)\b',
            
            # Pacific Reporter patterns
            'p3d': r'\b(\d+)\s+P\.3d\s+(\d+)\b',
            'p2d': r'\b(\d+)\s+P\.2d\s+(\d+)\b',
            'p_generic': r'\b(\d+)\s+P\.\s+(\d+)\b',
            
            # Federal patterns
            'us': r'\b(\d+)\s+U\.\s*S\.\s+(\d+)\b',
            'us_alt': r'\b(\d+)\s+United\s+States\s+(\d+)\b',
            'f3d': r'\b(\d+)\s+F\.3d\s+(\d+)\b',
            'f2d': r'\b(\d+)\s+F\.2d\s+(\d+)\b',
            'f4th': r'\b(\d+)\s+F\.4th\s+(\d+)\b',
            'f_supp': r'\b(\d+)\s+F\.\s*Supp\.\s+(\d+)\b',
            'f_supp2d': r'\b(\d+)\s+F\.\s*Supp\.\s*2d\s+(\d+)\b',
            'f_supp3d': r'\b(\d+)\s+F\.\s*Supp\.\s*3d\s+(\d+)\b',
            
            # Supreme Court patterns
            'sct': r'\b(\d+)\s+S\.\s*Ct\.\s+(\d+)\b',
            'sct_alt': r'\b(\d+)\s+Sup\.\s*Ct\.\s+(\d+)\b',
            
            # Lawyers' Edition
            'led': r'\b(\d+)\s+L\.\s*Ed\.\s+(\d+)\b',
            'led2d': r'\b(\d+)\s+L\.\s*Ed\.\s*2d\s+(\d+)\b',
            
            # Regional Reporters
            'a2d': r'\b(\d+)\s+A\.2d\s+(\d+)\b',
            'a3d': r'\b(\d+)\s+A\.3d\s+(\d+)\b',
            'ne2d': r'\b(\d+)\s+N\.E\.2d\s+(\d+)\b',
            'ne3d': r'\b(\d+)\s+N\.E\.3d\s+(\d+)\b',
            'nw2d': r'\b(\d+)\s+N\.W\.2d\s+(\d+)\b',
            'nw3d': r'\b(\d+)\s+N\.W\.3d\s+(\d+)\b',
            'se2d': r'\b(\d+)\s+S\.E\.2d\s+(\d+)\b',
            'se3d': r'\b(\d+)\s+S\.E\.3d\s+(\d+)\b',
            'sw2d': r'\b(\d+)\s+S\.W\.2d\s+(\d+)\b',
            'sw3d': r'\b(\d+)\s+S\.W\.3d\s+(\d+)\b',
            
            # California Reports
            'cal2d': r'\b(\d+)\s+Cal\.2d\s+(\d+)\b',
            'cal3d': r'\b(\d+)\s+Cal\.3d\s+(\d+)\b',
            'cal4th': r'\b(\d+)\s+Cal\.4th\s+(\d+)\b',
            
            # Westlaw and LEXIS
            'westlaw': r'\b(\d{4})\s+WL\s+(\d+)\b',
            'lexis': r'\b(\d{4})\s+[A-Za-z\.\s]+LEXIS\s+(\d+)\b',
            
            # State Reports (generic pattern)
            'state': r'\b(\d+)\s+[A-Z][a-z]+\.\s+(\d+)\b',
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
    
    def process_text(self, text: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main entry point for citation processing.
        
        Args:
            text: The text to process
            options: Processing options
            
        Returns:
            Dictionary with results, statistics, and metadata
        """
        start_time = time.time()
        options = options or {}
        
        try:
            # Step 0: Clean and preprocess text
            cleaned_text = TextCleaner.clean_text(text, options.get('cleaning_steps'))
            
            # Step 1: Extract citations
            citations = self.extract_citations(cleaned_text)
            
            # Step 2: Verify citations
            verified_citations = self.verify_citations(citations, cleaned_text)
            
            # Step 3: Calculate statistics
            statistics = self.calculate_statistics(verified_citations)
            
            # Step 4: Format for frontend
            formatted_results = self.format_for_frontend(verified_citations)
            
            processing_time = time.time() - start_time
            
            return {
                'results': formatted_results,
                'statistics': statistics,
                'summary': {
                    'total_citations': statistics.total_citations,
                    'parallel_citations': statistics.parallel_citations,
                    'verified_citations': statistics.verified_citations,
                    'unverified_citations': statistics.unverified_citations,
                    'unique_cases': statistics.unique_cases
                },
                'metadata': {
                    'processing_time': processing_time,
                    'text_length': len(text),
                    'cleaned_text_length': len(cleaned_text)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in unified citation processing: {e}")
            return {
                'results': [],
                'statistics': CitationStatistics(),
                'summary': {},
                'metadata': {'error': str(e)},
                'error': str(e)
            }
    
    def process_large_document(self, file_path: str, chunk_size: int = 100000, extract_case_names: bool = True) -> Dict[str, Any]:
        """
        Process large documents in streaming fashion.
        
        Args:
            file_path: Path to the document file
            chunk_size: Size of each chunk to process
            extract_case_names: Whether to extract case names
            
        Returns:
            Dictionary with combined results from all chunks
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # For large documents, process in chunks
            if len(text) > chunk_size:
                return self._process_text_in_chunks(text, chunk_size, extract_case_names)
            else:
                return self.process_text(text, {'extract_case_names': extract_case_names})
                
        except Exception as e:
            logger.error(f"Error processing large document {file_path}: {e}")
            return {
                'results': [],
                'statistics': CitationStatistics(),
                'summary': {},
                'metadata': {'error': str(e)},
                'error': str(e)
            }
    
    def _process_text_in_chunks(self, text: str, chunk_size: int, extract_case_names: bool) -> Dict[str, Any]:
        """Process text in chunks and combine results."""
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        all_results = []
        all_statistics = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            result = self.process_text(chunk, {'extract_case_names': extract_case_names})
            all_results.extend(result.get('results', []))
            all_statistics.append(result.get('statistics', CitationStatistics()))
        
        # Combine statistics
        combined_stats = self._combine_statistics(all_statistics)
        
        # Deduplicate results
        unique_results = self._deduplicate_results(all_results)
        
        return {
            'results': unique_results,
            'statistics': combined_stats,
            'summary': {
                'total_citations': combined_stats.total_citations,
                'parallel_citations': combined_stats.parallel_citations,
                'verified_citations': combined_stats.verified_citations,
                'unverified_citations': combined_stats.unverified_citations,
                'unique_cases': combined_stats.unique_cases
            },
            'metadata': {
                'chunks_processed': len(chunks),
                'total_text_length': len(text)
            }
        }
    
    def _combine_statistics(self, statistics_list: List[CitationStatistics]) -> CitationStatistics:
        """Combine statistics from multiple chunks."""
        total_citations = sum(s.total_citations for s in statistics_list)
        parallel_citations = sum(s.parallel_citations for s in statistics_list)
        verified_citations = sum(s.verified_citations for s in statistics_list)
        unverified_citations = sum(s.unverified_citations for s in statistics_list)
        complex_citations = sum(s.complex_citations for s in statistics_list)
        individual_parallel_citations = sum(s.individual_parallel_citations for s in statistics_list)
        
        # For unique cases, we need to deduplicate across chunks
        unique_cases = set()
        for stats in statistics_list:
            # This is a simplified approach - in practice, you'd need to track case names
            unique_cases.add(stats.unique_cases)
        
        return CitationStatistics(
            total_citations=total_citations,
            parallel_citations=parallel_citations,
            verified_citations=verified_citations,
            unverified_citations=unverified_citations,
            unique_cases=len(unique_cases),
            complex_citations=complex_citations,
            individual_parallel_citations=individual_parallel_citations
        )
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate citation results."""
        seen = set()
        unique_results = []
        
        for result in results:
            citation_key = result.get('citation', '')
            if citation_key not in seen:
                seen.add(citation_key)
                unique_results.append(result)
        
        return unique_results
    
    def extract_citations(self, text: str) -> List[CitationResult]:
        """
        Extract citations from text using multiple methods.
        
        Args:
            text: The text to extract citations from
            
        Returns:
            List of CitationResult objects
        """
        if not text:
            return []
        
        all_citations = []
        
        # Method 1: Regex extraction
        if hasattr(self, 'extract_regex_citations'):
            regex_citations = self.extract_regex_citations(text)
            all_citations.extend(regex_citations)
        
        # Method 2: Eyecite extraction
        if hasattr(self, 'eyecite_processor'):
            try:
                eyecite_citations = self.eyecite_processor.extract_citations(text)
                all_citations.extend(eyecite_citations)
            except Exception as e:
                self.logger.warning(f"Eyecite extraction failed: {e}")
        
        # COMPREHENSIVE U.S.C. AND C.F.R. FILTERING
        filtered_citations = []
        for citation in all_citations:
            citation_text = citation.citation if hasattr(citation, 'citation') else str(citation)
            
            # Comprehensive filtering for U.S.C. and C.F.R. citations
            if any(pattern in citation_text.upper() for pattern in [
                "U.S.C.", "USC", "U.S.C", "U.S.C.A.", "USCA", "UNITED STATES CODE",
                "C.F.R.", "CFR", "C.F.R", "CODE OF FEDERAL REGULATIONS",
                "§", "SECTION", "TITLE", "CHAPTER"
            ]):
                continue  # Skip U.S.C. and C.F.R. citations
            
            # Additional regex checks for statute patterns
            if re.search(r'\d+\s+U\.?\s*S\.?\s*C\.?\s*[§]?\s*\d+', citation_text, re.IGNORECASE):
                continue  # Skip U.S.C. citations with section symbols
            
            if re.search(r'\d+\s+C\.?\s*F\.?\s*R\.?\s*[§]?\s*\d+', citation_text, re.IGNORECASE):
                continue  # Skip C.F.R. citations
            
            filtered_citations.append(citation)
        
        # CONSERVATIVE GROUPING: Only group citations that are explicitly together in source text
        # This prevents merging different cases that happen to have similar names
        if len(filtered_citations) > 1:
            grouped_citations = self.group_parallel_citations(filtered_citations)
            return grouped_citations
        
        return filtered_citations
    
    def verify_citations(self, citations: List[CitationResult], text: str) -> List[CitationResult]:
        """
        Verify and enrich citations with canonical and extracted case names and dates.
        """
        import logging
        logger = logging.getLogger("case_name_extraction")
        for citation in citations:
            try:
                # Use enhanced extraction functions for better results
                from src.enhanced_case_name_extraction import extract_case_name_enhanced
                from src.enhanced_date_extraction import extract_year_near_citation_enhanced
                
                # Enhanced case name extraction
                case_name_result = extract_case_name_enhanced(text, citation.citation)
                if case_name_result:
                    citation.extracted_case_name = case_name_result.cleaned_name
                    citation.case_name = case_name_result.cleaned_name
                    citation.confidence = case_name_result.confidence
                else:
                    # Fallback to original method
                    triple = extract_case_name_triple(text, citation.citation)
                    citation.canonical_name = triple.get('canonical_name')
                    citation.extracted_case_name = triple.get('extracted_name')
                    citation.hinted_case_name = triple.get('hinted_name')
                    citation.case_name = triple.get('case_name')
                    citation.canonical_date = triple.get('canonical_date')
                    citation.extracted_date = triple.get('extracted_date')
                
                # Enhanced date extraction
                extracted_date = extract_year_near_citation_enhanced(text, citation.citation)
                if extracted_date:
                    citation.extracted_date = extracted_date
                    citation.year = extracted_date
                
                logger.debug(f"[UnifiedCitationProcessor] Citation: {citation.citation} | canonical: {citation.canonical_name} | extracted: {citation.extracted_case_name} | hinted: {citation.hinted_case_name} | date: {citation.canonical_date} | extracted_date: {citation.extracted_date}")
            except Exception as e:
                logger.warning(f"[UnifiedCitationProcessor] Failed to extract case name/date for {citation.citation}: {e}")
        return citations
    
    def calculate_statistics(self, citations: List[CitationResult]) -> CitationStatistics:
        """Calculate comprehensive statistics."""
        total_citations = len(citations)
        individual_parallel_citations = sum(1 for c in citations if c.is_parallel)
        verified_citations = sum(1 for c in citations if c.verified)
        unverified_citations = total_citations - verified_citations
        complex_citations = sum(1 for c in citations if c.is_complex)
        
        # Count unique cases and parallel citation sets
        unique_cases = set()
        parallel_sets = 0
        processed_primary = set()
        
        for citation in citations:
            # Count unique cases
            case_name = citation.case_name or citation.canonical_name or citation.citation
            if case_name:
                unique_cases.add(self._normalize_case_name(case_name))
            
            # Count parallel citation sets
            if citation.parallel_citations:
                # This is a primary citation with parallel citations
                if citation.citation not in processed_primary:
                    parallel_sets += 1
                    processed_primary.add(citation.citation)
            elif citation.is_parallel and citation.primary_citation:
                # This is a parallel citation
                if citation.primary_citation not in processed_primary:
                    parallel_sets += 1
                    processed_primary.add(citation.primary_citation)
        
        return CitationStatistics(
            total_citations=total_citations,
            parallel_citations=parallel_sets,
            verified_citations=verified_citations,
            unverified_citations=unverified_citations,
            unique_cases=len(unique_cases),
            complex_citations=complex_citations,
            individual_parallel_citations=individual_parallel_citations
        )
    
    def format_for_frontend(self, citations: List[CitationResult]) -> List[Dict[str, Any]]:
        """Format results for frontend display, always showing both canonical and extracted names/dates."""
        formatted_results = []
        for citation in citations:
            formatted_result = {
                'citation': citation.citation,
                'valid': citation.verified,
                'verified': citation.verified,
                'case_name': citation.case_name if citation.case_name else 'N/A',
                'extracted_case_name': citation.extracted_case_name if getattr(citation, 'extracted_case_name', None) else 'N/A',
                'extracted_date': citation.extracted_date if getattr(citation, 'extracted_date', None) else 'N/A',
                'canonical_name': citation.canonical_name if citation.canonical_name else 'N/A',
                'canonical_date': citation.canonical_date if citation.canonical_date else 'N/A',
                'court': citation.court if citation.court else 'N/A',
                'docket_number': citation.docket_number if citation.docket_number else 'N/A',
                'confidence': citation.confidence,
                'source': citation.source,
                'url': citation.url,
                'canonical_urls': citation.canonical_urls,
                'is_complex_citation': citation.is_complex,
                'is_parallel_citation': citation.is_parallel,
                'display_text': citation.citation,  # Simplified for clarity
                'case_name_color': '#228B22' if citation.verified else '#B22222',
                'complex_features': {
                    'has_parallel_citations': bool(citation.parallel_citations),
                    'has_case_history': bool(citation.case_history),
                    'has_docket_numbers': bool(citation.docket_numbers),
                    'has_publication_status': bool(citation.publication_status),
                    'has_pinpoint_pages': bool(citation.pinpoint_pages)
                },
                'parallel_info': {
                    'is_parallel': citation.is_parallel,
                    'primary_citation': citation.primary_citation,
                    'verification_status': citation.verified,
                    'parallel_citations': citation.parallel_citations
                } if citation.is_parallel or citation.parallel_citations else {},
                'metadata': {
                    'method': citation.method,
                    'pattern': citation.pattern,
                    'error': citation.error
                }
            }
            formatted_results.append(formatted_result)
        return formatted_results
    
    def extract_regex_citations(self, text: str) -> List[CitationResult]:
        """Extract citations using comprehensive regex patterns."""
        citations = []
        seen = set()
        first_citation_found = False
        for pattern_name, pattern in self.primary_patterns.items():
            try:
                matches = list(pattern.finditer(text))
                for match in matches:
                    citation_str = match.group(0)
                    if citation_str in seen:
                        continue
                    seen.add(citation_str)
                    # Extract date from context if available
                    extracted_date = None
                    if match.start() is not None and match.end() is not None:
                        extracted_date = DateExtractor.extract_date_from_context(
                            text, match.start(), match.end()
                        )
                    # For first citation, check if context is only case name or empty
                    if not first_citation_found:
                        context_start = max(0, match.start() - 200)
                        context = text[context_start:match.start()].strip()
                        # Find case name as text up to first comma or citation
                        comma_idx = text.find(',')
                        if comma_idx != -1 and comma_idx < match.start():
                            case_name_literal = text[:comma_idx].strip()
                        else:
                            case_name_literal = text[:match.start()].strip()
                        # If context is empty or matches the case name, treat as N/A
                        if not context or context == case_name_literal:
                            context = 'N/A'
                        extracted_case_name = case_name_literal
                        first_citation_found = True
                    else:
                        # For subsequent citations, use normal context window
                        context_start = max(0, match.start() - 200)
                        context_end = min(len(text), match.end() + 200)
                        context = text[context_start:context_end]
                        # Fallback for extracted_case_name: 5 non-stop words before citation
                        extracted_case_name = None
                        candidates = self.extract_case_name_candidates(text, citation_str)
                        if candidates:
                            extracted_case_name = candidates[0]
                        else:
                            stopwords = set([
                                'the', 'of', 'and', 'a', 'an', 'in', 'to', 'for', 'on', 'at', 'by', 'with', 'from', 'as', 'is', 'was', 'were', 'be', 'been', 'are', 'or', 'that', 'this', 'it', 'but', 'not', 'which', 'who', 'whom', 'whose', 'can', 'could', 'should', 'would', 'may', 'might', 'will', 'shall', 'do', 'does', 'did', 'so', 'if', 'than', 'then', 'there', 'here', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'only', 'own', 'same', 'too', 'very', 's', 't', 'just', 'don', 'now'
                            ])
                            fallback_context = text[max(0, match.start()-200):match.start()]
                            words = fallback_context.split()
                            non_stop = []
                            for word in reversed(words):
                                if word.lower() not in stopwords and word.isalpha():
                                    non_stop.append(word)
                                if len(non_stop) == 5:
                                    break
                            non_stop = list(reversed(non_stop))
                            if non_stop:
                                literal_case = ' '.join(non_stop)
                                if not (literal_case.lower().startswith('in re') or literal_case.lower().startswith('ex parte')):
                                    extracted_case_name = literal_case
                    # Fallback for extracted_date: scan after citation for (YYYY)
                    if not extracted_date:
                        after = text[match.end():match.end()+50]
                        m = re.search(r'\((19|20)\d{2}\)', after)
                        if m:
                            extracted_date = f"{m.group(1)}-01-01"
                    citation = CitationResult(
                        citation=citation_str,
                        method='regex',
                        pattern=pattern_name,
                        confidence=0.7,
                        start_index=match.start(),
                        end_index=match.end(),
                        context=context,
                        extracted_case_name=extracted_case_name,
                        extracted_date=extracted_date,
                        year=extracted_date.split('-')[0] if extracted_date else None,
                        metadata={
                            'extracted_date': extracted_date,
                            'pattern_name': pattern_name
                        }
                    )
                    citations.append(citation)
            except Exception as e:
                logger.warning(f"Regex extraction failed for {pattern_name}: {e}")
        return citations
    
    def group_parallel_citations(self, citations: List[CitationResult]) -> List[CitationResult]:
        """
        Group parallel citations that refer to the same case.
        
        CONSERVATIVE APPROACH: Only group citations that are explicitly together in the source text.
        This prevents merging different cases that happen to have similar names or dates.
        
        Args:
            citations: List of CitationResult objects
            
        Returns:
            List of grouped CitationResult objects
        """
        if not citations or len(citations) <= 1:
            return citations
        
        # CONSERVATIVE GROUPING: Only group if citations are explicitly together
        # Look for citations that appear in the same text block or are separated by punctuation
        
        grouped = []
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
                
                # STRICT GROUPING CRITERIA:
                # 1. Same case name (exact match or very high similarity)
                # 2. Same context block (within 200 characters)
                # 3. Explicitly separated by commas/semicolons in source text
                
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
                        
                        if context_similarity > 0.8:  # Very high similarity threshold
                            # Additional check: are they explicitly separated by punctuation?
                            # Look for patterns like "case_name, citation1, citation2"
                            combined_text = f"{citation.citation} {other.citation}"
                            if re.search(r'[,;]\s*', combined_text) or context_similarity > 0.9:
                                group.append(other)
                                processed.add(j)
                                continue
                
                # Check for very high similarity (0.95+) but only if they're in the same context
                elif (citation.case_name and other.case_name):
                    similarity = self._calculate_case_name_similarity(
                        citation.case_name, other.case_name
                    )
                    
                    if similarity >= 0.95:  # Much higher threshold
                        # Additional requirement: they must be in the same context block
                        if (hasattr(citation, 'context') and hasattr(other, 'context') and
                            citation.context and other.context):
                            
                            context_similarity = self._calculate_context_similarity(
                                citation.context, other.context
                            )
                            
                            if context_similarity > 0.7:  # High context similarity
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
                grouped.append(primary)
            else:
                # Single citation, no grouping needed
                grouped.append(group[0])
        
        return grouped
    
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

# Global instance for easy access
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
            from src.case_name_extraction_core import extract_case_name_triple
            case_name_result = extract_case_name_triple(text, citation, api_key=api_key, context_window=300)
            result["stages"]["case_name"] = case_name_result
            self.log_step("CASE_NAME_EXTRACTION", case_name_result)
        except Exception as e:
            result["stages"]["case_name"] = {"error": str(e)}
            self.log_step("CASE_NAME_EXTRACTION_ERROR", str(e), level="error")
        # Stage 3: Date Extraction
        try:
            from src.enhanced_date_extraction import extract_year_near_citation_enhanced
            year_result = extract_year_near_citation_enhanced(text, citation, context_window=300)
            result["stages"]["date"] = year_result
            self.log_step("DATE_EXTRACTION", year_result)
        except Exception as e:
            result["stages"]["date"] = {"error": str(e)}
            self.log_step("DATE_EXTRACTION_ERROR", str(e), level="error")
        # Stage 4: Canonical Lookup (simulate or call real API if available)
        try:
            # This is a placeholder for actual canonical lookup logic
            result["stages"]["canonical_lookup"] = "(not implemented in debugger)"
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
        print("\n=== Extraction Debug Report ===")
        print(json.dumps(results, indent=2, default=str))
        print("\n=== Debug Log ===")
        for entry in self.debug_log:
            print(f"[{entry['timestamp']}] {entry['level'].upper()} {entry['step']}: {entry['data']}")

# Usage example for integration
def debug_extraction_pipeline(text: str, citations: List[str], api_key: str = None):
    debugger = ExtractionDebugger()
    results = debugger.debug_unified_pipeline(text, citations, api_key)
    debugger.print_debug_report(results)
    return results

if __name__ == "__main__":
    # Example: Use a real-world test case
    sample_text = '''
    Cockel v. Dep't of Lab. & Indus.,
    142 Wn.2d 801, 808, 16 P.3d 583 (2002)
    '''
    sample_citations = ["142 Wn.2d 801", "16 P.3d 583"]
    print("Running extraction debugger on sample input...")
    debug_extraction_pipeline(sample_text, sample_citations)