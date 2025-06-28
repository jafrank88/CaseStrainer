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

logger = logging.getLogger(__name__)

@dataclass
class CitationResult:
    """Structured result for a single citation."""
    citation: str
    case_name: Optional[str] = None
    canonical_name: Optional[str] = None
    extracted_case_name: Optional[str] = None
    verified: bool = False
    url: Optional[str] = None
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
    def extract_date_from_context(text: str, citation_start: int, citation_end: int, context_window: int = 200) -> Optional[str]:
        """
        Extract date from context around a citation.
        
        Args:
            text: The full text document
            citation_start: Start position of the citation
            citation_end: End position of the citation
            context_window: Number of characters to look before and after citation
            
        Returns:
            Extracted date string in ISO format (YYYY-MM-DD) or None if not found
        """
        try:
            # Define context boundaries
            context_start = max(0, citation_start - context_window)
            context_end = min(len(text), citation_end + context_window)
            
            # Extract context around citation
            context_before = text[context_start:citation_start]
            context_after = text[citation_end:context_end]
            full_context = context_before + context_after
            
            # Date patterns to look for
            date_patterns = [
                # ISO format: 2024-01-15
                r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b',
                # US format: 01/15/2024, 1/15/2024
                r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',
                # US format with month names: January 15, 2024, Jan 15, 2024
                r'\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})\b',
                # Year only: (2024)
                r'\((\d{4})\)',
                # Year in citation context: decided in 2024
                r'(?:decided|filed|issued|released)\s+(?:in\s+)?(\d{4})\b',
                # Simple year pattern near citation
                r'\b(19|20)\d{2}\b'
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
                        # Full date pattern
                        if pattern == r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b':
                            # ISO format
                            year, month, day = groups
                        elif pattern == r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b':
                            # US format
                            month, day, year = groups
                        elif 'January|February' in pattern:
                            # Month name format
                            month_name, day, year = groups
                            month = month_map.get(month_name.lower(), '01')
                        else:
                            continue
                            
                        # Validate and format
                        try:
                            year = int(year)
                            month = int(month)
                            day = int(day)
                            
                            if 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                                return f"{year:04d}-{month:02d}-{day:02d}"
                        except (ValueError, TypeError):
                            continue
                            
                    elif len(groups) == 1:
                        # Year only pattern
                        year = groups[0]
                        try:
                            year_int = int(year)
                            if 1900 <= year_int <= 2100:
                                return f"{year_int:04d}-01-01"  # Default to January 1st
                        except (ValueError, TypeError):
                            continue
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting date from context: {e}")
            return None

class EnhancedRegexExtractor:
    """Enhanced regex extraction with comprehensive patterns from CitationExtractor."""
    
    def __init__(self):
        self.patterns = self._get_comprehensive_patterns()
    
    def _get_comprehensive_patterns(self) -> Dict[str, Any]:
        """Return comprehensive regex patterns for different citation formats."""
        return {
            # U.S. Supreme Court - comprehensive patterns
            'us': re.compile(r"\b\d+\s+U\.?\s*S\.?\s+\d+\b"),
            'us_alt': re.compile(r"\b\d+\s+U\.\s*S\.\s+\d+\b"),
            'us_alt2': re.compile(r"\b\d+\s+United\s+States\s+\d+\b"),
            
            # Federal Reporter - comprehensive patterns
            'f2d': re.compile(r"\b\d+\s+F\.2d\s+\d+\b"),
            'f3d': re.compile(r"\b\d+\s+F\.3d\s+\d+\b"),
            'f4th': re.compile(r"\b\d+\s+F\.4th\s+\d+\b"),
            'f_supp': re.compile(r"\b\d+\s+F\.\s*Supp\.\s+\d+\b"),
            'f_supp2d': re.compile(r"\b\d+\s+F\.\s*Supp\.\s*2d\s+\d+\b"),
            'f_supp3d': re.compile(r"\b\d+\s+F\.\s*Supp\.\s*3d\s+\d+\b"),
            
            # Supreme Court Reporter
            'sct': re.compile(r"\b\d+\s+S\.\s*Ct\.\s+\d+\b"),
            'sct_alt': re.compile(r"\b\d+\s+Sup\.\s*Ct\.\s+\d+\b"),
            
            # Lawyers' Edition
            'led': re.compile(r"\b\d+\s+L\.\s*Ed\.\s+\d+\b"),
            'led2d': re.compile(r"\b\d+\s+L\.\s*Ed\.\s*2d\s+\d+\b"),
            
            # Washington State Reports - comprehensive patterns
            'wn2d': re.compile(r"\b\d+\s+Wn\.2d\s+\d+\b"),
            'wn_app': re.compile(r"\b\d+\s+Wn\.\s*App\.\s+\d+\b"),
            'wn_app2d': re.compile(r"\b\d+\s+Wn\.\s*App\.\s*2d\s+\d+\b"),
            'wn_generic': re.compile(r"\b\d+\s+Wn\.\s+\d+\b"),
            'wash2d': re.compile(r"\b\d+\s+Wash\.2d\s+\d+\b"),
            'wash_app': re.compile(r"\b\d+\s+Wash\.\s*App\.\s+\d+\b"),
            'wash_generic': re.compile(r"\b\d+\s+Wash\.\s+\d+\b"),
            
            # Pacific Reporter - comprehensive patterns
            'p2d': re.compile(r"\b\d+\s+P\.2d\s+\d+\b"),
            'p3d': re.compile(r"\b\d+\s+P\.3d\s+\d+\b"),
            'p_generic': re.compile(r"\b\d+\s+P\.\s+\d+\b"),
            
            # Regional Reporters - comprehensive patterns
            'a2d': re.compile(r"\b\d+\s+A\.2d\s+\d+\b"),
            'a3d': re.compile(r"\b\d+\s+A\.3d\s+\d+\b"),
            'a_generic': re.compile(r"\b\d+\s+A\.\s+\d{2,}\b"),
            'ne2d': re.compile(r"\b\d+\s+N\.E\.2d\s+\d+\b"),
            'ne3d': re.compile(r"\b\d+\s+N\.E\.3d\s+\d+\b"),
            'ne_generic': re.compile(r"\b\d+\s+N\.E\.\s+\d{2,}\b"),
            'nw2d': re.compile(r"\b\d+\s+N\.W\.2d\s+\d+\b"),
            'nw3d': re.compile(r"\b\d+\s+N\.W\.3d\s+\d+\b"),
            'nw_generic': re.compile(r"\b\d+\s+N\.W\.\s+\d{2,}\b"),
            'se2d': re.compile(r"\b\d+\s+S\.E\.2d\s+\d+\b"),
            'se3d': re.compile(r"\b\d+\s+S\.E\.3d\s+\d+\b"),
            'se_generic': re.compile(r"\b\d+\s+S\.E\.\s+\d{2,}\b"),
            'sw2d': re.compile(r"\b\d+\s+S\.W\.2d\s+\d+\b"),
            'sw3d': re.compile(r"\b\d+\s+S\.W\.3d\s+\d+\b"),
            'sw_generic': re.compile(r"\b\d+\s+S\.W\.\s+\d{2,}\b"),
            
            # California Reports
            'cal2d': re.compile(r"\b\d+\s+Cal\.2d\s+\d+\b"),
            'cal3d': re.compile(r"\b\d+\s+Cal\.3d\s+\d+\b"),
            'cal4th': re.compile(r"\b\d+\s+Cal\.4th\s+\d+\b"),
            'cal_generic': re.compile(r"\b\d+\s+Cal\.\s+\d{2,}\b"),
            
            # Westlaw and LEXIS
            'westlaw': re.compile(r"\b\d{4}\s+WL\s+\d+\b"),
            'lexis': re.compile(r"\b\d{4}\s+[A-Za-z\.\s]+LEXIS\s+\d+\b"),
            
            # State Reports (generic pattern) - more specific
            'state': re.compile(r"\b\d+\s+[A-Z][a-z]+\.\s+\d+\b"),
            
            # Year-based citations
            'year_citation': re.compile(r"\b\d{4}\s+U\.S\.\s+\d+\b"),
            'year_citation_alt': re.compile(r"\b\d{4}\s+[A-Z][a-z]+\.\s+\d+\b"),
        }
    
    def extract_citations(self, text: str) -> List[Dict[str, Any]]:
        """Extract citations using comprehensive regex patterns."""
        citations = []
        seen = set()
        
        for name, pattern in self.patterns.items():
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

class CaseNameExtractor:
    """Extracts case names from citation context."""
    
    def extract_case_name(self, text: str, citation: str) -> Optional[str]:
        """Extract case name from context around a citation."""
        try:
            # Find citation in text
            citation_index = text.find(citation)
            if citation_index == -1:
                return None
            
            # Get context before citation
            context_start = max(0, citation_index - 500)
            context = text[context_start:citation_index]
            
            # Look for case name patterns
            case_patterns = [
                r'([A-Z][A-Za-z\s\.,&\'\"\(\)]+v\.\s+[A-Z][A-Za-z\s\.,&\'\"\(\)]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
                r'([A-Z][A-Za-z\s\.,&\'\"\(\)]+v\.\s+[A-Z][A-Za-z\s\.,&\'\"\(\)]+?)\s*,\s*\d+',
            ]
            
            for pattern in case_patterns:
                match = re.search(pattern, context, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
            
            return None
            
        except Exception as e:
            logger.warning(f"Case name extraction failed: {e}")
            return None

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
        self.case_name_extractor = CaseNameExtractor()
        self.citation_grouper = CitationGrouper()
        self.verifier = EnhancedMultiSourceVerifier()
        self.cache_manager = get_cache_manager()
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
        """Extract all citations using multiple methods."""
        citations = []
        
        # Method 1: Complex citation detection
        if self.complex_detector.is_complex_citation(text):
            complex_data = self.complex_detector.parse_complex_citation(text)
            
            # Create primary citation
            if complex_data['primary_citation']:
                primary = CitationResult(
                    citation=complex_data['primary_citation'],
                    case_name=complex_data['case_name'],
                    year=complex_data['year'],
                    is_complex=True,
                    parallel_citations=complex_data['parallel_citations'],
                    pinpoint_pages=complex_data['pinpoint_pages'],
                    docket_numbers=complex_data['docket_numbers'],
                    case_history=complex_data['case_history'],
                    publication_status=complex_data['publication_status'],
                    method='complex',
                    confidence=0.9
                )
                citations.append(primary)
                
                # Add parallel citations
                for parallel_citation in complex_data['parallel_citations']:
                    parallel = CitationResult(
                        citation=parallel_citation,
                        case_name=complex_data['case_name'],
                        year=complex_data['year'],
                        is_complex=True,
                        is_parallel=True,
                        primary_citation=complex_data['primary_citation'],
                        method='complex'
                    )
                    citations.append(parallel)
        
        # Method 2: Eyecite extraction
        eyecite_results = self.eyecite_processor.extract_eyecite_citations(text)
        citations.extend(eyecite_results)
        
        # Method 3: Regex extraction (fallback)
        regex_results = self.extract_regex_citations(text)
        citations.extend(regex_results)
        
        # Method 4: Enhanced case name extraction for citations without case names
        for citation in citations:
            if not citation.case_name and citation.citation:
                try:
                    # Extract case name from context around the citation
                    context_start = max(0, citation.start_index - 500 if citation.start_index else 0)
                    context_end = min(len(text), citation.end_index + 500 if citation.end_index else len(text))
                    context = text[context_start:context_end]
                    
                    # Use the case name extractor
                    if self.case_name_extractor:
                        extracted_name = self.case_name_extractor.extract_case_name(context, citation.citation)
                        if extracted_name:
                            citation.case_name = extracted_name
                except Exception as e:
                    logger.warning(f"Error extracting case name for {citation.citation}: {e}")
        
        # Remove duplicates based on citation text
        seen = set()
        unique_citations = []
        for citation in citations:
            if citation.citation not in seen:
                seen.add(citation.citation)
                unique_citations.append(citation)
        
        return unique_citations
    
    def verify_citations(self, citations: List[CitationResult], text: str) -> List[CitationResult]:
        """Verify citations using the enhanced verifier."""
        verified_citations = []
        
        for citation in citations:
            try:
                result = self.verifier.verify_citation_unified_workflow(
                    citation.citation,
                    extracted_case_name=citation.case_name,
                    full_text=text
                )
                
                citation.verified = result.get('verified', False)
                citation.url = result.get('url')
                citation.court = result.get('court')
                citation.docket_number = result.get('docket_number')
                citation.canonical_date = result.get('date_filed')
                citation.source = result.get('source', 'Local')
                citation.confidence = result.get('confidence', 0.5)
                
                verified_citations.append(citation)
                
            except Exception as e:
                logger.warning(f"Verification failed for {citation.citation}: {e}")
                citation.error = str(e)
                verified_citations.append(citation)
        
        return verified_citations
    
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
        """Format results for frontend display."""
        formatted_results = []
        
        for citation in citations:
            # Create display text that prominently shows parallel citations
            display_parts = []
            
            # Add case name prominently
            if citation.case_name:
                display_parts.append(f"<strong>{citation.case_name}</strong>")
            
            # Add primary citation
            display_parts.append(citation.citation)
            
            # Add pinpoint pages
            if citation.pinpoint_pages:
                display_parts.extend(citation.pinpoint_pages)
            
            # Add parallel citations prominently (not in dropdown)
            if citation.parallel_citations:
                parallel_text = ", ".join(citation.parallel_citations)
                display_parts.append(f"<em>Parallel: {parallel_text}</em>")
            
            # Add year
            if citation.year:
                display_parts.append(f"({citation.year})")
            
            # Add case history
            if citation.case_history:
                display_parts.extend([f"({history})" for history in citation.case_history])
            
            # Add publication status
            if citation.publication_status:
                display_parts.append(f"({citation.publication_status})")
            
            # Add docket numbers
            if citation.docket_numbers:
                docket_text = ", ".join(citation.docket_numbers)
                display_parts.append(f"<em>Docket: {docket_text}</em>")
            
            # For parallel citations, show they belong to the primary
            if citation.is_parallel and citation.primary_citation:
                display_parts.append(f"<em>(Parallel to {citation.primary_citation})</em>")
            
            formatted_result = {
                'citation': citation.citation,
                'valid': citation.verified,
                'verified': citation.verified,
                'case_name': citation.case_name,
                'extracted_case_name': citation.extracted_case_name,
                'canonical_name': citation.canonical_name,
                'canonical_date': citation.canonical_date,
                'court': citation.court,
                'docket_number': citation.docket_number,
                'confidence': citation.confidence,
                'source': citation.source,
                'url': citation.url,
                'is_complex_citation': citation.is_complex,
                'is_parallel_citation': citation.is_parallel,
                'display_text': ' '.join(display_parts),
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
        
        # Use all comprehensive patterns
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
                    
                    # Extract context around citation
                    context_start = max(0, match.start() - 200)
                    context_end = min(len(text), match.end() + 200)
                    context = text[context_start:context_end]
                    
                    citation = CitationResult(
                        citation=citation_str,
                        method='regex',
                        pattern=pattern_name,
                        confidence=0.7,
                        start_index=match.start(),
                        end_index=match.end(),
                        context=context,
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
        """Group citations that are likely parallel citations for the same case."""
        if not citations:
            return citations
        
        # Group by case name similarity
        grouped_citations = []
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
                
                if self._are_likely_parallel(citation, other):
                    group.append(other)
                    processed.add(j)
            
            # If we have a group with multiple citations, mark them as parallel
            if len(group) > 1:
                primary = group[0]
                primary.is_complex = True
                primary.parallel_citations = [c.citation for c in group[1:]]
                
                for parallel_citation in group[1:]:
                    parallel_citation.is_parallel = True
                    parallel_citation.primary_citation = primary.citation
                    parallel_citation.is_complex = True
                
                grouped_citations.extend(group)
            else:
                grouped_citations.append(citation)
        
        return grouped_citations
    
    def _are_likely_parallel(self, citation1: CitationResult, citation2: CitationResult) -> bool:
        """Check if two citations are likely parallel citations for the same case."""
        # Check if they have the same case name
        if citation1.case_name and citation2.case_name:
            if self._normalize_case_name(citation1.case_name) == self._normalize_case_name(citation2.case_name):
                return True
        
        # Check if they have the same year
        if citation1.year and citation2.year and citation1.year == citation2.year:
            # Additional check: are they different reporter types?
            if self._are_different_reporters(citation1.citation, citation2.citation):
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
    
    def _are_different_reporters(self, citation1: str, citation2: str) -> bool:
        """Check if two citations use different reporters."""
        # Extract reporter from citations
        reporter1 = self._extract_reporter(citation1)
        reporter2 = self._extract_reporter(citation2)
        
        return reporter1 != reporter2 and reporter1 and reporter2
    
    def _extract_reporter(self, citation: str) -> str:
        """Extract reporter from citation string."""
        # Common reporter patterns
        patterns = [
            r'\bWn\.\s*App\.\b',
            r'\bWn\.2d\b',
            r'\bWn\.3d\b',
            r'\bWash\.\s*App\.\b',
            r'\bWash\.2d\b',
            r'\bP\.3d\b',
            r'\bP\.2d\b',
            r'\bU\.\s*S\.\b',
            r'\bF\.3d\b',
            r'\bF\.2d\b',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, citation)
            if match:
                return match.group(0)
        
        return ""

# Global instance for easy access
unified_processor = UnifiedCitationProcessor() 