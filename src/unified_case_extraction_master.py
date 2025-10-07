"""
Unified Case Extraction Master
=============================

This module provides THE SINGLE, AUTHORITATIVE case name extraction function
that consolidates the best features from all duplicate functions across the codebase.

ALL OTHER EXTRACTION FUNCTIONS SHOULD BE DEPRECATED AND REPLACED WITH THIS ONE.

Key Features:
- Position-aware extraction (prevents bleeding)
- Context-optimized windows (prevents contamination)
- Advanced pattern matching (handles all citation formats)
- Comprehensive fallback logic (minimizes N/A results)
- Unicode-aware text processing
- Performance optimized
"""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

from src.utils.canonical_metadata import (
    normalize_citation_key,
    get_canonical_metadata,
    prefer_canonical_name,
    prefer_canonical_year,
    extract_year_value,
    fetch_canonical_metadata_on_demand,
)

logger = logging.getLogger(__name__)

@dataclass
class MasterExtractionResult:
    """Standardized result from the master extraction function."""
    case_name: str
    year: str
    confidence: float
    method: str
    start_index: Optional[int] = None
    end_index: Optional[int] = None
    context: str = ""
    debug_info: Dict[str, Any] = None
    canonical_name: Optional[str] = None
    canonical_year: Optional[str] = None
    extracted_case_name: Optional[str] = None
    extracted_year: Optional[str] = None

class UnifiedCaseExtractionMaster:
    """
    THE SINGLE, AUTHORITATIVE case name extraction implementation.
    
    This class consolidates the best features from:
    - extract_case_name_and_date_master()
    - extract_case_name_and_year_unified()
    - _extract_case_name_enhanced()
    - All other duplicate functions
    
    ALL extraction should go through this class.
    """
    
    def __init__(self):
        """Initialize the master extraction engine."""
        self._setup_patterns()
        logger.info("UnifiedCaseExtractionMaster initialized - all duplicates deprecated")
        self.citation_metadata_cache: Dict[str, Dict[str, Any]] = {}

    def _get_canonical_metadata(self, citation: Optional[str]) -> Dict[str, Any]:
        metadata = get_canonical_metadata(citation, self.citation_metadata_cache)
        if metadata:
            return metadata

        fetched = fetch_canonical_metadata_on_demand(citation) if citation else {}
        if fetched:
            self._update_canonical_cache(
                citation,
                canonical_name=fetched.get("canonical_name"),
                canonical_date=fetched.get("canonical_date"),
            )
            return fetched

        return {}

    def _update_canonical_cache(
        self,
        citation: Optional[str],
        canonical_name: Optional[str] = None,
        canonical_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        key = normalize_citation_key(citation)
        if not key:
            return {}

        existing = self.citation_metadata_cache.get(key, {}).copy()

        if canonical_name is None and canonical_date is None:
            return existing

        if canonical_name is not None:
            existing['canonical_name'] = canonical_name
        if canonical_date is not None:
            existing['canonical_date'] = canonical_date
        if existing:
            self.citation_metadata_cache[key] = existing
        return existing

    def _apply_canonical_preferences(
        self,
        citation: Optional[str],
        extracted_name: Optional[str],
        extracted_year: Optional[str],
    ) -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
        canonical_meta = self._get_canonical_metadata(citation) if citation else {}
        preferred_name = prefer_canonical_name(extracted_name, canonical_meta, self._is_valid_case_name)
        preferred_year = prefer_canonical_year(extracted_year, canonical_meta)
        return preferred_name or extracted_name, preferred_year or extracted_year, canonical_meta

    def _is_valid_case_name(self, case_name: Optional[str]) -> bool:
        if not case_name:
            return False
        cleaned = case_name.strip()
        if len(cleaned) < 5:
            return False
        if cleaned.lower().startswith("in re "):
            return True
        return " v. " in cleaned
    
    def _setup_patterns(self):
        """Setup the most comprehensive, battle-tested regex patterns."""
        
        # Unicode-aware character classes (from unified_extraction_architecture.py)
        self.apostrophe_chars = r'[\'\u2019\u2018\u201A\u201B\u2032\u2035\u201C\u201D\u201E\u201F\u2033\u2034\u2036\u2037\u2039\u203A\u00B4\u0060\u02B9\u02BB\u02BC\u02BD\u02BE\u02BF\u055A\u055B\u055C\u055D\u055E\u055F\u05F3]'
        self.ampersand_chars = r'[&\u0026\uFF06\u204A\u214B]'
        self.hyphen_chars = r'[-\u002D\u2010\u2011\u2012\u2013\u2014\u2015\u2212\uFE58\uFE63\uFF0D]'
        self.period_chars = r'[.\u002E\u2024\u2025\u2026\u2027]'
        self.space_chars = r'[\s\u0020\u00A0\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200A\u200B\u200C\u200D\u200E\u200F\u2028\u2029\u202A\u202B\u202C\u202D\u202E\u202F]'
        
        # Comprehensive legal character class
        self.legal_chars = f'[a-zA-Z0-9{self.apostrophe_chars[1:-1]}{self.ampersand_chars[1:-1]}{self.hyphen_chars[1:-1]}{self.period_chars[1:-1]}{self.space_chars[1:-1]}]'
        
        # Best patterns from all implementations
        self.case_name_patterns = [
            # PRIORITY 1: Standard citation format - match case name immediately before citation
            # Use word boundary or sentence end to prevent over-matching
            # Matches: "Spokeo, Inc. v. Robins, 578 U.S. 330" or "Raines v. Byrd, 521 U.S. 811"
            r'(?:^|[.!?]\s+)([A-Z][a-zA-Z\s\'&\-\.,]*?(?:,\s*(?:Inc|Corp|LLC|Ltd|Co|L\.P\.|L\.L\.P\.)\.?)?)\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.,]+?)(?:,\s*\d+)',
            
            # PRIORITY 2: Corporate patterns with full name capture
            r'([A-Z][a-zA-Z\s\'&\-\.,]+?,\s*(?:Inc|Corp|LLC|Ltd|Co|L\.P\.|L\.L\.P\.)\.?)\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.,]+?)(?:\s*,)',
            
            # PRIORITY 3: Standard v. patterns with comma
            r'(?:In\s+re\s+)?([A-Z][a-zA-Z\'\.\&\s\-,]{2,50})\s+v\.\s+([A-Z][a-zA-Z\'\.\&\s\-,]{2,50})(?:\s*,)',
            
            # PRIORITY 4: Enhanced patterns (from clustering)
            r'(?:In\s+re\s+)?([A-Z][a-zA-Z\s\'&\-\.,]{2,80})\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.,]{2,80})',
            
            # In re patterns
            r'In\s+re\s+([A-Z][a-zA-Z\s\'&\-\.,]{2,80})',
            r'In\s+re\s+(?:Marriage\s+of\s+)?([A-Z][a-zA-Z\s\'&\-\.,]{2,60})',
            
            # State patterns
            r'State\s+(?:of\s+)?([A-Z][a-zA-Z\s]{2,30})\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.,]{2,50})',
            r'([A-Z][a-zA-Z\s\'&\-\.,]{2,50})\s+v\.\s+State\s+(?:of\s+)?([A-Z][a-zA-Z\s]{2,30})',
            
            # Government patterns
            r'([A-Z][a-zA-Z\s\'&\-\.,]*?)\s+v\.\s+(United\s+States|U\.S\.)',
            r'(United\s+States|U\.S\.)\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.,]*?)',
        ]
        
        # Context detection patterns - MUST match case name format (Name v. Name)
        self.context_patterns = [
            # Standard format: "Case Name, Citation"
            r'([A-Z][a-zA-Z\s\'&\-\.,]+\s+v\.\s+[A-Z][a-zA-Z\s\'&\-\.,]+?),\s*\d+\s+[A-Za-z.]+\s+\d+',
            # With year: "Case Name, Citation (Year)"
            r'([A-Z][a-zA-Z\s\'&\-\.,]+\s+v\.\s+[A-Z][a-zA-Z\s\'&\-\.,]+?)\s*,\s*\d+\s+[A-Za-z.]+(?:\s+\d+)?\s*\(\d{4}\)',
            # Signal words: "See Case Name, Citation"
            r'(?:In|The case of|As stated in|Citing|Following|See)\s+([A-Z][a-zA-Z\s\'&\-\.,]+\s+v\.\s+[A-Z][a-zA-Z\s\'&\-\.,]+?),\s*\d+',
        ]
        
        # Year patterns
        self.year_patterns = [
            r'\((\d{4})\)',  # (2020)
            r',\s*(\d{4})',  # , 2020
            r'(\d{4})\s*\)',  # 2020)
        ]
    
    def extract_case_name_and_date(
        self,
        text: str,
        citation: Optional[str] = None,
        start_index: Optional[int] = None,
        end_index: Optional[int] = None,
        debug: bool = False
    ) -> MasterExtractionResult:
        """
        THE MASTER EXTRACTION FUNCTION
        
        This is THE ONLY function that should be used for case name extraction.
        It consolidates all the best features from duplicate functions.
        
        Args:
            text: Full document text
            citation: Citation text (if available)
            start_index: Start position of citation
            end_index: End position of citation
            debug: Enable debug logging
            
        Returns:
            MasterExtractionResult with extracted case name and date
        """
        if debug:
            logger.warning(f"🎯 MASTER_EXTRACT: Starting unified extraction for '{citation}' at {start_index}-{end_index}")
        
        # Normalize text to handle Unicode issues
        normalized_text = self._normalize_text(text)
        
        # Strategy 1: Position-aware extraction (best accuracy)
        if start_index is not None and end_index is not None:
            result = self._extract_with_position(normalized_text, citation, start_index, end_index, debug)
            if result and result.case_name and result.case_name != 'N/A':
                return result
        
        # Strategy 2: Context-based extraction (fallback)
        if citation:
            result = self._extract_with_citation_context(normalized_text, citation, debug)
            if result and result.case_name and result.case_name != 'N/A':
                return result
        
        # Strategy 3: Pattern-based extraction (last resort)
        result = self._extract_with_patterns(normalized_text, citation, debug)
        if result and result.case_name and result.case_name != 'N/A':
            return result
        
        # No extraction succeeded
        return MasterExtractionResult(
            case_name="N/A",
            year="N/A",
            confidence=0.0,
            method="extraction_failed",
            debug_info={"reason": "All extraction strategies failed"}
        )
    
    def _extract_with_position(self, text: str, citation: str, start_index: int, end_index: int, debug: bool) -> Optional[MasterExtractionResult]:
        """Position-aware extraction with optimized context window."""
        # CRITICAL FIX: Increase context window to capture case names in standard format
        # Standard format: "Case Name, Citation, Year" requires looking back ~200 chars
        context_start = max(0, start_index - 200)  # Increased from 60 to 200
        context_end = min(len(text), end_index + 50)  # Increased from 20 to 50
        context = text[context_start:context_end]
        
        if debug:
            logger.warning(f"🔍 POSITION_EXTRACT: Context ({len(context)} chars): '{context[:100]}...'")
        
        # Try all patterns on the focused context
        for i, pattern in enumerate(self.case_name_patterns):
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                if debug:
                    logger.warning(f"✅ Pattern {i} matched: {pattern[:60]}...")
                    logger.warning(f"   Groups: {match.groups()}")
                case_name = self._build_case_name_from_match(match, pattern, debug)
                if debug:
                    logger.warning(f"   Built case name: '{case_name}'")
                year = self._extract_year_from_context(context, debug)
                
                if case_name and len(case_name.strip()) > 3:
                    cleaned_name = self._clean_case_name(case_name)
                    preferred_name, preferred_year, canonical_meta = self._apply_canonical_preferences(
                        citation,
                        cleaned_name,
                        year,
                    )
                    canonical_year_value = extract_year_value(
                        canonical_meta.get("canonical_year") or canonical_meta.get("canonical_date")
                    )
                    return MasterExtractionResult(
                        case_name=preferred_name or "N/A",
                        year=preferred_year or "N/A",
                        confidence=0.9 - (i * 0.1),  # Higher confidence for earlier patterns
                        method=f"position_pattern_{i}",
                        start_index=start_index,
                        end_index=end_index,
                        context=context[:100] + "...",
                        debug_info={
                            "pattern": pattern,
                            "raw_match": match.groups(),
                            "canonical": canonical_meta,
                        },
                        canonical_name=canonical_meta.get("canonical_name"),
                        canonical_year=canonical_year_value,
                        extracted_case_name=cleaned_name,
                        extracted_year=year,
                    )
        
        return None
    
    def _extract_with_citation_context(self, text: str, citation: str, debug: bool) -> Optional[MasterExtractionResult]:
        """Context-based extraction around citation."""
        # Find citation in text
        citation_pos = text.find(citation)
        if citation_pos == -1:
            return None
        
        # CRITICAL FIX: Increase context window to capture standard citation format
        # "Case Name, Citation, Year" format requires looking back ~200 chars
        context_start = max(0, citation_pos - 200)  # Increased from 30 to 200
        context_end = min(len(text), citation_pos + len(citation) + 50)  # Increased from 10 to 50
        context = text[context_start:context_end]
        
        # Try context patterns
        for pattern in self.context_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                case_name = match.group(1).strip()
                year = self._extract_year_from_context(context, debug)
                
                if len(case_name) > 3:
                    cleaned_name = self._clean_case_name(case_name)
                    preferred_name, preferred_year, canonical_meta = self._apply_canonical_preferences(
                        citation,
                        cleaned_name,
                        year,
                    )
                    canonical_year_value = extract_year_value(
                        canonical_meta.get("canonical_year") or canonical_meta.get("canonical_date")
                    )
                    return MasterExtractionResult(
                        case_name=preferred_name or "N/A",
                        year=preferred_year or "N/A",
                        confidence=0.7,
                        method="citation_context",
                        context=context[:100] + "...",
                        debug_info={
                            "pattern": pattern,
                            "citation_pos": citation_pos,
                            "canonical": canonical_meta,
                        },
                        canonical_name=canonical_meta.get("canonical_name"),
                        canonical_year=canonical_year_value,
                        extracted_case_name=cleaned_name,
                        extracted_year=year,
                    )
        
        return None
    
    def _extract_with_patterns(self, text: str, citation: Optional[str], debug: bool) -> Optional[MasterExtractionResult]:
        """Pattern-based extraction as last resort."""
        # Use broader context but still reasonable
        sample_text = text[:2000]  # First 2000 chars
        
        for pattern in self.case_name_patterns:
            match = re.search(pattern, sample_text, re.IGNORECASE)
            if match:
                case_name = self._build_case_name_from_match(match, pattern, debug)
                year = self._extract_year_from_context(sample_text[:500], debug)
                
                if case_name and len(case_name.strip()) > 3:
                    cleaned_name = self._clean_case_name(case_name)
                    preferred_name, preferred_year, canonical_meta = self._apply_canonical_preferences(
                        citation,
                        cleaned_name,
                        year,
                    )
                    canonical_year_value = extract_year_value(
                        canonical_meta.get("canonical_year") or canonical_meta.get("canonical_date")
                    )
                    return MasterExtractionResult(
                        case_name=preferred_name or "N/A",
                        year=preferred_year or "N/A",
                        confidence=0.5,
                        method="pattern_fallback",
                        context=sample_text[:100] + "...",
                        debug_info={"pattern": pattern, "canonical": canonical_meta},
                        canonical_name=canonical_meta.get("canonical_name"),
                        canonical_year=canonical_year_value,
                        extracted_case_name=cleaned_name,
                        extracted_year=year,
                    )
        
        return None
    
    def _build_case_name_from_match(self, match, pattern: str, debug: bool) -> str:
        """Build case name from regex match groups."""
        groups = match.groups()
        
        if len(groups) == 1:
            # Single group (In re cases)
            return groups[0].strip()
        elif len(groups) >= 2:
            # Two groups (plaintiff v. defendant)
            plaintiff = groups[0].strip()
            defendant = groups[1].strip()
            return f"{plaintiff} v. {defendant}"
        
        return match.group(0).strip()
    
    def _extract_year_from_context(self, context: str, debug: bool) -> Optional[str]:
        """Extract year from context using comprehensive patterns."""
        for pattern in self.year_patterns:
            match = re.search(pattern, context)
            if match:
                year = match.group(1)
                if 1800 <= int(year) <= 2030:  # Reasonable year range
                    return year
        
        return None
    
    def _clean_case_name(self, case_name: str) -> str:
        """Clean and normalize case name using best practices from all implementations."""
        if not case_name:
            return "N/A"
        
        # Remove leading/trailing whitespace and normalize spaces
        cleaned = re.sub(r'\s+', ' ', case_name.strip())
        
        # Remove common prefixes that indicate contamination
        contamination_prefixes = [
            r'^(?:In|The case of|As stated in|Citing|Following|See)\s+',
            r'^(?:court held that|established|the defendant)\s*[.\s]*',
            r'^(?:of\s+law)[\s\.]*',
        ]
        
        for prefix in contamination_prefixes:
            cleaned = re.sub(prefix, '', cleaned, flags=re.IGNORECASE)
        
        # Remove trailing punctuation except periods in abbreviations
        cleaned = re.sub(r'[,;:]+$', '', cleaned)
        
        # Fix common corporate abbreviation issues
        cleaned = re.sub(r'\bInc\b(?!\.)(?!\s+v\.)', 'Inc.', cleaned)
        cleaned = re.sub(r'\bCorp\b(?!\.)(?!\s+v\.)', 'Corp.', cleaned)
        cleaned = re.sub(r'\bLLC\b(?!\.)(?!\s+v\.)', 'LLC', cleaned)
        cleaned = re.sub(r'\bLtd\b(?!\.)(?!\s+v\.)', 'Ltd.', cleaned)
        
        # If we've removed everything, return original
        if not cleaned.strip():
            return case_name.strip()
        
        # Check if this looks like a document header
        if self._is_document_header(cleaned):
            return "N/A"
        
        return cleaned.strip()
    
    def _is_document_header(self, text: str) -> bool:
        """Check if text looks like a document header rather than a case name."""
        if not text:
            return True
        
        # Document header patterns
        header_patterns = [
            r'^IN THE\s+',
            r'^CASE NO\.\s*',
            r'^NO\.\s*\d+',
            r'^FILED:\s*',
            r'^DATE:\s*',
            r'^COURT:\s*',
            r'^DISTRICT:\s*',
            r'^CIRCUIT:\s*',
            r'^APPEAL:\s*',
            r'^APPELLATE:\s*',
            r'^SUPREME:\s*',
            r'^STATE OF\s+',
            r'^UNITED STATES\s+',
            r'^PLAINTIFFS,?\s*$',
            r'^DEFENDANTS\.?\s*$',
            r'^PLAINTIFFS-APPELLEES,?\s*$',
            r'^DEFENDANT-APPELLANT\.?\s*$',
            r'^THOMSON REUTERS',
            r'^WEST PUBLISHING',
            r'^ROSS INTELLIGENCE',
            r'^ENTERPRISE CENTRE',
            r'^CORPORATION,?\s*$',
            r'^GMBH\s*$',
            r'^INC\.?\s*$',
            r'^LLC\s*$',
            r'^LTD\.?\s*$',
            r'^CO\.?\s*$',
        ]
        
        for pattern in header_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # Check for very long text that's likely a document header
        if len(text) > 100:
            return True
        
        # Check for text that's mostly uppercase (document headers)
        if len(text) > 10 and sum(1 for c in text if c.isupper()) / len(text) > 0.7:
            return True
        
        # Check for text with too many commas (document headers)
        if text.count(',') > 3:
            return True
        
        return False
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text to handle Unicode and encoding issues."""
        if not text:
            return ""
        
        # Handle common Unicode issues
        text = text.replace('\u2019', "'")  # Smart apostrophe
        text = text.replace('\u201c', '"').replace('\u201d', '"')  # Smart quotes
        text = text.replace('\u2013', '-').replace('\u2014', '-')  # En/em dashes
        text = text.replace('\u00a0', ' ')  # Non-breaking space
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text

# Global singleton instance
_master_extractor = None

def get_master_extractor() -> UnifiedCaseExtractionMaster:
    """Get the singleton master extractor instance."""
    global _master_extractor
    if _master_extractor is None:
        _master_extractor = UnifiedCaseExtractionMaster()
    return _master_extractor

def extract_case_name_and_date_unified_master(
    text: str,
    citation: Optional[str] = None,
    start_index: Optional[int] = None,
    end_index: Optional[int] = None,
    debug: bool = False,
    canonical_name: Optional[str] = None,
    canonical_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    THE SINGLE, UNIFIED EXTRACTION FUNCTION
    
    This function replaces ALL 120+ duplicate extraction functions.
    Use this instead of:
    - extract_case_name_and_date_master()
    - extract_case_name_and_year_unified()
    - _extract_case_name_enhanced()
    - All other duplicate functions
    
    Returns:
        Dictionary with case_name, year, confidence, method, and debug_info
    """
    extractor = get_master_extractor()

    if citation:
        extractor._update_canonical_cache(
            citation,
            canonical_name=canonical_name,
            canonical_date=canonical_date,
        )
        cached_meta = extractor._get_canonical_metadata(citation)
        if (
            cached_meta.get('canonical_name')
            and cached_meta.get('canonical_date')
        ):
            return {
                'case_name': cached_meta['canonical_name'],
                'year': cached_meta['canonical_date'],
                'date': cached_meta['canonical_date'],
                'confidence': 1.0,
                'method': 'canonical_metadata_cache',
                'start_index': start_index,
                'end_index': end_index,
                'context': text[:100] + "...",
                'debug_info': {'canonical_source': 'cache'},
            }

    result = extractor.extract_case_name_and_date(text, citation, start_index, end_index, debug)

    if citation:
        extractor._update_canonical_cache(
            citation,
            canonical_name=result.canonical_name,
            canonical_date=result.canonical_year,
        )

    return {
        'case_name': result.case_name,
        'year': result.year,
        'date': result.year,
        'confidence': result.confidence,
        'method': result.method,
        'start_index': result.start_index,
        'end_index': result.end_index,
        'context': result.context,
        'debug_info': result.debug_info or {},
        'canonical_name': result.canonical_name,
        'canonical_year': result.canonical_year,
        'extracted_case_name': result.extracted_case_name or result.case_name,
        'extracted_year': result.extracted_year or result.year,
    }
