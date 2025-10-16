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
    
    def __init__(self, document_primary_case_name: Optional[str] = None):
        """Initialize the master extraction engine.
        
        Args:
            document_primary_case_name: The primary case name of the document being analyzed.
                                       Used to filter out contamination where citations incorrectly
                                       extract the document's own case name.
        """
        self._setup_patterns()
        logger.info("UnifiedCaseExtractionMaster initialized - all duplicates deprecated")
        self.citation_metadata_cache: Dict[str, Dict[str, Any]] = {}
        self.document_primary_case_name = document_primary_case_name
        if document_primary_case_name:
            logger.warning(f"[CONTAMINATION-FILTER] Document primary case: '{document_primary_case_name}'")

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
        # FIX #37: Made ALL quantifiers NON-GREEDY (added ?) and reduced max lengths from 80 to 40
        # to prevent matching past the context window and capturing the NEXT case name instead of
        # the one BEFORE the citation. This was the root cause of "183 Wn.2d 649" extracting
        # "Spokane County" (116 chars AFTER) instead of "Lopez Demetrio" (40 chars BEFORE).
        self.case_name_patterns = [
            # PRIORITY 0A: ALL CAPS case names (common in court documents)
            # Matches: "CMTY. LEGAL SERVICES V . U.S. HHS" or "COMMUNITY LEGAL SERVICES V. UNITED STATES"
            r'([A-Z][A-Z\'\.\&\s\-,]{2,150})\s+[Vv]\.?\s+([A-Z][A-Z\'\.\&\s\-,]{2,150})',
            
            # PRIORITY 0B: Case name immediately before parallel citations (most accurate)
            # Matches: "Ass'n of Wash. Spirits & Wine Distribs. v. Wash. State Liquor Control Bd., 182 Wn.2d 342"
            # FIX #68D: Removed ? from quantifiers to make GREEDY (match full names, not minimum)
            # This captures "Cmty. Legal Servs. in E. Palo Alto v. U.S. Dep't" instead of just "E. Palo Alto v. U.S."
            r'([A-Z][a-zA-Z\'\.\&\s\-,]{2,150})\s+[Vv]\.?\s+([A-Z][a-zA-Z\'\.\&\s\-,]{2,150}),\s*\d+\s+[A-Z][a-z.]+\s+\d+',
            
            # PRIORITY 1: Standard citation format - match case name immediately before citation
            # Use lookbehind to ensure sentence boundary without capturing non-case-name text
            # Matches: "Spokeo, Inc. v. Robins, 578 U.S. 330" or "Raines v. Byrd, 521 U.S. 811"
            # FIX #68D: Removed ? to make greedy
            # FIX #69: Added [Vv]\.? to handle both "v." and "V ." variations
            r'(?:(?<=\.)\s+|(?<=\?)\s+|(?<=!)\s+|^)([A-Z][a-zA-Z\s\'&\-\.,]*(?:,\s*(?:Inc|Corp|LLC|Ltd|Co|L\.P\.|L\.L\.P\.)\.?)?)\s+[Vv]\.?\s+([A-Z][a-zA-Z\s\'&\-\.,]+)(?:,\s*\d+)',
            
            # PRIORITY 2: Corporate patterns with full name capture
            # FIX #68D: Removed ? to make greedy
            r'([A-Z][a-zA-Z\s\'&\-\.,]+,\s*(?:Inc|Corp|LLC|Ltd|Co|L\.P\.|L\.L\.P\.)\.?)\s+[Vv]\.?\s+([A-Z][a-zA-Z\s\'&\-\.,]+)(?:\s*,)',
            
            # PRIORITY 3: Standard v. patterns with comma
            # FIX #68D: Removed ? to make greedy
            r'(?:In\s+re\s+)?([A-Z][a-zA-Z\'\.\&\s\-,]{2,150})\s+[Vv]\.?\s+([A-Z][a-zA-Z\'\.\&\s\-,]{2,150})(?:\s*,)',
            
            # PRIORITY 4: Enhanced patterns (from clustering)
            # FIX #68D: Removed ? to make greedy
            r'(?:In\s+re\s+)?([A-Z][a-zA-Z\s\'&\-\.,]{2,150})\s+[Vv]\.?\s+([A-Z][a-zA-Z\s\'&\-\.,]{2,150})',
            
            # In re patterns (title case and all caps)
            r'In\s+re\s+([A-Z][a-zA-Z\s\'&\-\.,]{2,40}?)',
            r'In\s+re\s+(?:Marriage\s+of\s+)?([A-Z][a-zA-Z\s\'&\-\.,]{2,40}?)',
            r'IN\s+RE\s+([A-Z][A-Z\s\'&\-\.,]{2,40}?)',
            
            # State patterns (title case and all caps)
            r'State\s+(?:of\s+)?([A-Z][a-zA-Z\s]{2,30}?)\s+[Vv]\.?\s+([A-Z][a-zA-Z\s\'&\-\.,]{2,40}?)',
            r'([A-Z][a-zA-Z\s\'&\-\.,]{2,40}?)\s+[Vv]\.?\s+State\s+(?:of\s+)?([A-Z][a-zA-Z\s]{2,30}?)',
            r'STATE\s+(?:OF\s+)?([A-Z][A-Z\s]{2,30}?)\s+[Vv]\.?\s+([A-Z][A-Z\s\'&\-\.,]{2,40}?)',
            
            # Government patterns (ALREADY non-greedy)
            r'([A-Z][a-zA-Z\s\'&\-\.,]*?)\s+[Vv]\.?\s+(United\s+States|U\.S\.|UNITED\s+STATES)',
            r'(United\s+States|U\.S\.|UNITED\s+STATES)\s+[Vv]\.?\s+([A-Z][a-zA-Z\s\'&\-\.,]*?)',
        ]
        
        # Context detection patterns - MUST match case name format (Name v. Name)
        # FIX #37: Made quantifiers non-greedy to prevent overmatch
        # FIX #69: Added [Vv]\.? to handle both "v." and "V ." variations
        self.context_patterns = [
            # Standard format: "Case Name, Citation"
            r'([A-Z][a-zA-Z\s\'&\-\.,]+?\s+[Vv]\.?\s+[A-Z][a-zA-Z\s\'&\-\.,]+?),\s*\d+\s+[A-Za-z.]+\s+\d+',
            # With year: "Case Name, Citation (Year)"
            r'([A-Z][a-zA-Z\s\'&\-\.,]+?\s+[Vv]\.?\s+[A-Z][a-zA-Z\s\'&\-\.,]+?)\s*,\s*\d+\s+[A-Za-z.]+(?:\s+\d+)?\s*\(\d{4}\)',
            # Signal words: "See Case Name, Citation"
            r'(?:In|The case of|As stated in|Citing|Following|See)\s+([A-Z][a-zA-Z\s\'&\-\.,]+?\s+[Vv]\.?\s+[A-Z][a-zA-Z\s\'&\-\.,]+?),\s*\d+',
            # ALL CAPS format
            r'([A-Z][A-Z\s\'&\-\.,]+?\s+[Vv]\.?\s+[A-Z][A-Z\s\'&\-\.,]+?),\s*\d+\s+[A-Za-z.]+\s+\d+',
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
        # CRITICAL DEBUG: Log EVERY call to verify this method is being used
        logger.error(f"🎯🎯🎯 [MASTER_EXTRACT ENTRY] citation='{citation}', start_index={start_index}")
        
        # FIX #33: ALWAYS log for "183 Wn.2d 649" to trace the bug
        force_debug = citation and "183" in citation and "649" in citation
        if debug or force_debug:
            logger.warning(f"🎯 MASTER_EXTRACT: Starting unified extraction for '{citation}' at {start_index}-{end_index}")
            if force_debug:
                logger.warning(f"🔍 FIX #33 DEBUG: This is the problematic citation!")
                logger.warning(f"   Text at position: '{text[start_index:start_index+50] if start_index else 'N/A'}'")
                logger.warning(f"   Text before (50 chars): '{text[start_index-50:start_index] if start_index and start_index >= 50 else 'N/A'}'")
        
        # Normalize text to handle Unicode issues
        normalized_text = self._normalize_text(text)
        
        # FIX #69: Strategy 0 - Comma-anchored extraction (NEW - HIGHEST PRIORITY)
        # Use comma before citation as anchor to work backwards and find full case name
        # This fixes truncation issues like "E. Palo Alto v. U." → "Cmty. Legal Servs. in E. Palo Alto v. U.S. Dep't..."
        if citation and start_index is not None:
            if force_debug:
                logger.warning(f"🔍 FIX #69: Trying Strategy 0 - Comma-anchored extraction")
            result = self._extract_with_comma_anchor(text, citation, start_index, debug or force_debug)
            if result and result.case_name and result.case_name != 'N/A':
                if force_debug:
                    logger.warning(f"✅ FIX #69: Strategy 0 succeeded! Extracted: '{result.case_name}'")
                return result
        
        # Strategy 1: Position-aware extraction (best accuracy)
        if start_index is not None and end_index is not None:
            if force_debug:
                logger.warning(f"🔍 FIX #33: Trying Strategy 1 - Position-aware extraction")
            # FIX #43: CRITICAL - Use ORIGINAL text, not normalized!
            # Normalization removes line breaks (\n → space), shifting ALL positions!
            # Indices are calculated from original text, so MUST use original text for slicing!
            result = self._extract_with_position(text, citation, start_index, end_index, debug or force_debug)
            if result and result.case_name and result.case_name != 'N/A':
                if force_debug:
                    logger.warning(f"✅ FIX #33: Strategy 1 succeeded! Extracted: '{result.case_name}'")
                    logger.warning(f"   extracted_case_name: '{result.extracted_case_name}'")
                    logger.warning(f"   canonical_name: '{result.canonical_name}'")
                return result
        
        # Strategy 2: Context-based extraction (fallback)
        if citation:
            # FIX #43: Use ORIGINAL text for same reason as Strategy 1
            result = self._extract_with_citation_context(text, citation, debug)
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
    
    def _filter_header_contamination(self, context: str, debug: bool) -> str:
        """
        FIX #67: Remove document headers and metadata that contaminate extraction.
        
        Filters out lines containing:
        - Court identifiers: "SUPREME COURT", "COURT OF APPEALS", "CLERK"
        - Filing metadata: "FILED", "FILE ", "CLERK'S OFFICE"
        - Dates in header format
        - All-caps lines (likely headers)
        - Document numbers and case numbers in header format
        
        Args:
            context: Raw context text around citation
            debug: Enable debug logging
            
        Returns:
            Filtered context with headers removed
        """
        # ALWAYS log to confirm this is being called
        logger.error(f"[FIX #67] FILTERING CALLED! Context length: {len(context) if context else 0}")
        
        if not context or len(context.strip()) == 0:
            return context
        
        original_context = context
        lines = context.split('\n')
        filtered_lines = []
        
        # Header patterns to exclude
        header_patterns = [
            r'\bSUPREME COURT\b',
            r'\bCOURT OF APPEALS\b',
            r'\bCLERK\b',
            r'\bFILED\b',
            r'\bFILE\s',
            r"CLERK'S OFFICE",
            r'IN THE \w+ COURT',
            r'STATE OF \w+',
            r'No\.\s+\d+-\d+',  # Case numbers like "No. 102976-4"
            r'^\s*[A-Z\s,\.\-]+$',  # All-caps lines (headers)
            r'^\s*\d{1,2}/\d{1,2}/\d{4}\s*$',  # Date stamps
            r'^\s*[A-Z]{2,}\s+\d{1,2},\s+\d{4}\s*$',  # "JUNE 12, 2025"
        ]
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
                
            # Check if line matches any header pattern
            is_header = False
            for pattern in header_patterns:
                if re.search(pattern, line_stripped, re.IGNORECASE):
                    is_header = True
                    if debug:
                        logger.warning(f"[FIX #67] Filtering header line: '{line_stripped[:80]}'")
                    break
            
            # Also filter very short lines (< 10 chars) that are likely headers
            if not is_header and len(line_stripped) < 10:
                is_header = True
                if debug:
                    logger.warning(f"[FIX #67] Filtering short line: '{line_stripped}'")
            
            if not is_header:
                filtered_lines.append(line)
        
        filtered_context = '\n'.join(filtered_lines)
        
        if debug and filtered_context != original_context:
            logger.warning(f"[FIX #67] Context filtering:")
            logger.warning(f"  Original length: {len(original_context)} chars")
            logger.warning(f"  Filtered length: {len(filtered_context)} chars")
            logger.warning(f"  Removed: {len(original_context) - len(filtered_context)} chars")
        
        return filtered_context
    
    def _normalize_whitespace_for_extraction(self, context: str, debug: bool) -> str:
        """
        FIX #68: Normalize whitespace and PDF artifacts to handle PDF line breaks.
        
        PDF text extraction often inserts line breaks (\n) in the middle of case names
        that aren't visible in the rendered PDF. It also includes Unicode artifacts
        like � (U+FFFD replacement character) for smart quotes.
        
        Example issues:
            1. Line breaks: "E. Palo Alto v. U.S. Dep't\nof Health" → truncates at \n
            2. Unicode artifacts: "Dep�t" (should be "Dep't") → breaks regex patterns
        
        This method:
        1. Replaces all newlines with spaces
        2. Replaces common PDF Unicode artifacts (�) with apostrophes
        3. Normalizes various quote characters to standard quotes
        4. Collapses multiple spaces into single spaces
        5. Preserves punctuation and case
        
        Args:
            context: Context text (after header filtering)
            debug: Enable debug logging
            
        Returns:
            Context with normalized whitespace and characters
        """
        if not context or len(context.strip()) == 0:
            return context
        
        original_context = context
        
        # Replace newlines with spaces
        # This allows case names that span multiple lines to be captured as a single string
        normalized = context.replace('\n', ' ')
        
        # Replace tabs with spaces
        normalized = normalized.replace('\t', ' ')
        
        # FIX #68B: Replace common PDF Unicode artifacts
        # � (U+FFFD) is the Unicode replacement character used when PDF can't encode properly
        # These often appear in place of apostrophes or other special characters
        normalized = normalized.replace('\ufffd', "'")  # Unicode replacement character → apostrophe
        normalized = normalized.replace('�', "'")  # Also handle as direct character
        
        # Normalize various quote characters to standard ASCII quotes
        normalized = normalized.replace('\u2018', "'")  # Left single quote
        normalized = normalized.replace('\u2019', "'")  # Right single quote (smart apostrophe)
        normalized = normalized.replace('\u201c', '"')  # Left double quote
        normalized = normalized.replace('\u201d', '"')  # Right double quote
        normalized = normalized.replace('\u00b4', "'")  # Acute accent (often used as apostrophe)
        normalized = normalized.replace('\u0060', "'")  # Grave accent (often used as apostrophe)
        
        # Collapse multiple spaces into single spaces
        # Use regex to handle any sequence of whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Trim leading/trailing whitespace
        normalized = normalized.strip()
        
        if debug and normalized != original_context:
            logger.warning(f"[FIX #68] Whitespace/character normalization:")
            logger.warning(f"  Original: '{original_context[:100]}...'")
            logger.warning(f"  Normalized: '{normalized[:100]}...'")
            logger.warning(f"  Removed {original_context.count(chr(10))} newlines")
            if '�' in original_context or '\ufffd' in original_context:
                logger.warning(f"  Fixed Unicode replacement characters")
        
        return normalized
    
    def _extract_with_comma_anchor(self, text: str, citation: str, start_index: int, debug: bool) -> Optional[MasterExtractionResult]:
        """
        FIX #69: Extract case name using comma before citation as anchor.
        
        Most inline citations follow format: "Case Name, Citation"
        Example: "Cmty. Legal Servs. in E. Palo Alto v. U.S. Dep't of Health & Hum. Servs., 780 F. Supp. 3d 897"
        
        This method fixes the pattern start matching problem where regex incorrectly starts at "E. Palo Alto"
        instead of "Cmty. Legal Servs. in E. Palo Alto" because it sees ". E" as a sentence boundary.
        
        Strategy:
        1. Find comma immediately before citation (within 10 chars)
        2. Work backwards from comma to find case name
        3. Case name ends at comma, starts after sentence boundary or previous citation
        
        Args:
            text: Full document text (original, not normalized)
            citation: Citation string (e.g., "780 F. Supp. 3d 897")
            start_index: Position of citation in text
            debug: Enable debug logging
        
        Returns:
            MasterExtractionResult if extraction succeeds, None otherwise
        """
        # FIX #69 DEBUG: ALWAYS log entry to verify method is called
        logger.error(f"[FIX #69 ENTRY] Citation: '{citation}', Start: {start_index}, Text len: {len(text)}")
        
        # Step 1: Find comma before citation (within 10 chars, allowing for whitespace)
        pre_citation_text = text[max(0, start_index - 10):start_index]
        
        # FIX #69 DEBUG: Log what we're checking for comma
        logger.error(f"[FIX #69 COMMA CHECK] Pre-citation text: '{pre_citation_text}'")
        logger.error(f"[FIX #69 COMMA CHECK] Text at citation pos: '{text[start_index:start_index+50]}'")
        
        if ',' not in pre_citation_text:
            logger.error(f"[FIX #69 FAIL] No comma found in '{pre_citation_text}' - falling back")
            return None  # No comma anchor, fall back to other methods
        
        # Find position of the comma
        comma_offset = pre_citation_text.rfind(',')
        comma_pos = start_index - (len(pre_citation_text) - comma_offset)
        
        # FIX #69 DEBUG: Always log comma position
        logger.error(f"[FIX #69 SUCCESS] Found comma at position {comma_pos} (citation at {start_index})")
        
        # Step 2: Get context before comma (400 chars to capture full case name)
        search_start = max(0, comma_pos - 400)
        potential_case_name = text[search_start:comma_pos]
        
        # FIX #69 DEBUG: Always log context
        logger.error(f"[FIX #69 CONTEXT] Length: {len(potential_case_name)} chars")
        logger.error(f"[FIX #69 CONTEXT] Last 100: '{potential_case_name[-100:]}'")
        
        # Step 3: Normalize whitespace and Unicode artifacts (Fix #68)
        potential_case_name = self._normalize_whitespace_for_extraction(potential_case_name, debug)
        logger.error(f"[FIX #69 NORMALIZED] Length: {len(potential_case_name)} chars")
        
        # Step 4: Extract case name using right-anchored pattern
        # Pattern matches case name that ENDS at the comma position
        # Looks for: [Capital letter]...text... v. ...text...$ ($ = end of string)
        
        # Try multiple patterns in priority order
        # USER REQUESTED: Support "In re", "In the matter of", "Matter of", "Ex parte", "Estate of"
        patterns = [
            # Pattern 1: "In re" cases - greedy match to end of string
            r'(In\s+re\s+[A-Z][a-zA-Z\s\'&\-\.,]{3,})$',
            
            # Pattern 2: "In the matter of" cases (full form)
            r'(In\s+the\s+matter\s+of\s+[A-Z][a-zA-Z\s\'&\-\.,]{3,})$',
            
            # Pattern 3: "Matter of" cases (short form)
            r'(Matter\s+of\s+[A-Z][a-zA-Z\s\'&\-\.,]{3,})$',
            
            # Pattern 4: "Ex parte" cases
            r'(Ex\s+parte\s+[A-Z][a-zA-Z\s\'&\-\.,]{3,})$',
            
            # Pattern 5: "Estate of" cases
            r'(Estate\s+of\s+[A-Z][a-zA-Z\s\'&\-\.,]{3,})$',
            
            # Pattern 6: "In re" after sentence boundary
            r'(?:^|[.!?]\s+)(In\s+re\s+[A-Z][a-zA-Z\s\'&\-\.,]{3,})$',
            
            # Pattern 7: Full case name with "v." - greedy match to end of string
            r'([A-Z][a-zA-Z\s\'&\-\.,]{5,}\s+v\.\s+[A-Z][a-zA-Z\s\'&\-\.,]{5,})$',
            
            # Pattern 8: After sentence boundary (period, question, exclamation)
            r'(?:^|[.!?]\s+)([A-Z][a-zA-Z\s\'&\-\.,]{5,}\s+v\.\s+[A-Z][a-zA-Z\s\'&\-\.,]{5,})$',
            
            # Pattern 9: After quotation mark
            r'["\']?\s*([A-Z][a-zA-Z\s\'&\-\.,]{5,}\s+v\.\s+[A-Z][a-zA-Z\s\'&\-\.,]{5,})$',
        ]
        
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, potential_case_name, re.IGNORECASE)
            if match:
                case_name = match.group(1).strip()
                
                # FIX #69 DEBUG: Always log pattern matches
                logger.error(f"[FIX #69 MATCH] Pattern {i+1} matched! Raw: '{case_name[:100]}'")
                
                # Step 5: Clean the case name
                case_name = self._clean_case_name(case_name)
                logger.error(f"[FIX #69 CLEANED] After clean: '{case_name[:100]}'")
                
                # FIX #69: Remove common citation introducers
                introducer_patterns = [
                    r'^(?:See|Citing|Quoting|Following|E\.g\.,)\s+',  # "quoting Kidwell..." → "Kidwell..."
                    r'^(?:see|citing|quoting|following|e\.g\.,)\s+',  # lowercase versions
                ]
                
                original_name = case_name
                for intro_pattern in introducer_patterns:
                    case_name = re.sub(intro_pattern, '', case_name, flags=re.IGNORECASE)
                
                if case_name != original_name:
                    logger.error(f"[FIX #69 INTRODUCER] Removed introducer: '{original_name[:50]}' -> '{case_name[:50]}'")
                
                # Step 6: Validate it looks like a case name
                if not self._looks_like_case_name(case_name, debug):
                    logger.error(f"[FIX #69 VALIDATION FAIL] Doesn't look like case name: '{case_name[:100]}'")
                    continue  # Try next pattern
                
                logger.error(f"[FIX #69 VALIDATION OK] Passed validation!")
                
                # Step 7: Extract year from context after citation
                year_context = text[start_index:start_index + 100]
                year = self._extract_year_from_context(year_context, debug)
                
                logger.error(f"[FIX #69 FINAL] Case name: '{case_name}' ({len(case_name)} chars), Year: {year}")
                
                # FIX #69: Apply canonical preferences if available
                preferred_name, preferred_year, canonical_meta = self._apply_canonical_preferences(
                    citation,
                    case_name,
                    year,
                )
                canonical_year_value = extract_year_value(
                    canonical_meta.get("canonical_year") or canonical_meta.get("canonical_date")
                )
                
                return MasterExtractionResult(
                    case_name=preferred_name or "N/A",
                    year=preferred_year or "N/A",
                    confidence=0.9,  # High confidence - comma anchor is reliable
                    method="comma_anchored",
                    context=f"...{potential_case_name[-100:]}",
                    debug_info={
                        "comma_position": comma_pos,
                        "case_name_length": len(case_name),
                        "pattern_used": i + 1,
                        "canonical": canonical_meta
                    },
                    canonical_name=canonical_meta.get("canonical_name"),
                    canonical_year=canonical_year_value,
                    extracted_case_name=case_name,
                    extracted_year=year,
                )
        
        # FIX #69 DEBUG: Always log when no pattern matches
        logger.error(f"[FIX #69 NO MATCH] None of the {len(patterns)} patterns matched")
        logger.error(f"[FIX #69 NO MATCH] Context was: '{potential_case_name[-200:]}'")
        
        return None
    
    def _looks_like_case_name(self, text: str, debug: bool) -> bool:
        """
        FIX #69: Validate that extracted text looks like a real case name.
        
        Checks:
        1. Contains " v. " (plaintiff v. defendant) OR starts with "In re" (USER FIX)
        2. Starts with capital letter
        3. Has reasonable length (10-200 chars)
        4. Doesn't contain obvious contamination
        5. Has proper party name structure
        
        Args:
            text: Potential case name to validate
            debug: Enable debug logging
        
        Returns:
            True if text looks like a case name, False otherwise
        """
        # FIX #69 DEBUG: Always log validation attempts
        logger.error(f"[FIX #69 VALIDATE] Checking: '{text[:100] if text else 'None'}'")
        
        # USER FIX: Allow special case types in addition to " v. " cases
        # Support: "In re", "In the matter of", "Matter of", "Ex parte", "Estate of"
        text_lower = text.lower() if text else ''
        has_v_pattern = ' v. ' in text_lower
        is_special_case = (
            text_lower.startswith('in re ') or
            text_lower.startswith('in the matter of ') or
            text_lower.startswith('matter of ') or
            text_lower.startswith('ex parte ') or
            text_lower.startswith('estate of ')
        )
        
        if not text or (not has_v_pattern and not is_special_case):
            logger.error(f"[FIX #69 VALIDATE] FAIL: No ' v. ' or special case pattern in text")
            return False
        
        if len(text) < 10:
            logger.error(f"[FIX #69 VALIDATE] FAIL: Too short ({len(text)} chars)")
            return False
        
        if len(text) > 200:
            logger.error(f"[FIX #69 VALIDATE] FAIL: Too long ({len(text)} chars)")
            return False
        
        # Check if starts with capital letter
        if not text[0].isupper():
            logger.error(f"[FIX #69 VALIDATE] FAIL: Doesn't start with capital")
            return False
        
        # USER FIX: Only validate plaintiff/defendant structure for " v. " cases
        # For special cases, just validate they have content after the prefix
        if has_v_pattern:
            # Split into plaintiff and defendant
            v_lower = ' v. '
            if v_lower not in text.lower():
                return False
            
            # Find "v." case-insensitively
            v_pos = text.lower().find(v_lower)
            plaintiff = text[:v_pos].strip()
            defendant = text[v_pos + len(v_lower):].strip()
            
            # Both parts should have at least one word
            if len(plaintiff.split()) < 1 or len(defendant.split()) < 1:
                logger.error(f"[FIX #69 VALIDATE] FAIL: Plaintiff '{plaintiff}' or defendant '{defendant}' too short")
                return False
        elif is_special_case:
            # For special cases, validate content after prefix
            # Find which prefix it is and check content after it
            prefixes = {
                'in re ': 6,
                'in the matter of ': 17,
                'matter of ': 10,
                'ex parte ': 9,
                'estate of ': 10
            }
            
            for prefix, length in prefixes.items():
                if text_lower.startswith(prefix):
                    after_prefix = text[length:].strip()
                    if len(after_prefix) < 5:  # At least a few chars after prefix
                        logger.error(f"[FIX #69 VALIDATE] FAIL: '{prefix.strip()}' case too short after prefix")
                        return False
                    break
        
        # Check for obvious contamination
        contamination_indicators = [
            'held that', 'the court', 'established', 'determined',
            'argued that', 'concluded that', 'reasoned that',
            'in recent times', 'in this case', 'as discussed',
        ]
        
        # text_lower already defined above
        for indicator in contamination_indicators:
            if indicator in text_lower:
                logger.error(f"[FIX #69 VALIDATE] FAIL: Contains contamination '{indicator}'")
                return False
        
        # FIX: Check if extracted name matches document's primary case name (CONTAMINATION)
        if self.document_primary_case_name:
            logger.error(f"[CONTAMINATION-FILTER] Checking '{text[:80]}' against primary '{self.document_primary_case_name[:80]}'")
            contamination_result = self._is_document_case_contamination(text, True)  # Force debug
            if contamination_result:
                logger.error(f"[CONTAMINATION-FILTER] ✅ REJECTED: Matches document primary case")
                logger.error(f"[CONTAMINATION-FILTER]    Rejected text: '{text[:100]}'")
                return False
            else:
                logger.error(f"[CONTAMINATION-FILTER] ⚠️  Passed (no match): '{text[:80]}'")
        else:
            logger.error(f"[CONTAMINATION-FILTER] ⚠️  SKIPPED: No document primary case name set!")
        
        logger.error(f"[FIX #69 VALIDATE] SUCCESS: All checks passed!")
        return True
    
    def _is_document_case_contamination(self, extracted_name: str, debug: bool) -> bool:
        """
        FIX: Detect if extracted case name is contaminated with document's primary case name.
        
        Contamination occurs when the extraction picks up the current document's case name
        instead of the cited case name. This happens because the document's case name
        appears frequently throughout the text near citations.
        
        Examples of contamination:
            - Document: "Gopher Media LLC v. Melone"
            - Citation: 890 F.3d 828
            - Extracted (WRONG): "MELONE California state court..."
            - Extracted (WRONG): "GOPHER MEDIA LLC v. MELONE Pacific Pictures Corp"
        
        Args:
            extracted_name: The case name that was extracted
            debug: Enable debug logging
        
        Returns:
            True if contaminated (should be rejected), False if clean
        """
        if not self.document_primary_case_name or not extracted_name:
            return False
        
        # Normalize both for comparison (case-insensitive, ignore punctuation)
        def normalize_for_comparison(name):
            # Remove common case name punctuation and spacing variations
            normalized = name.lower()
            normalized = re.sub(r'[,\.\s]+', ' ', normalized)
            normalized = normalized.strip()
            return normalized
        
        extracted_normalized = normalize_for_comparison(extracted_name)
        primary_normalized = normalize_for_comparison(self.document_primary_case_name)
        
        # Strategy 1: Check if primary case name is CONTAINED in extracted name
        # Example: "GOPHER MEDIA LLC v. MELONE Pacific Pictures" contains "gopher media llc v melone"
        if primary_normalized in extracted_normalized:
            if debug:
                logger.warning(f"[CONTAMINATION-FILTER] Containment match:")
                logger.warning(f"  Extracted: '{extracted_name}'")
                logger.warning(f"  Primary: '{self.document_primary_case_name}'")
            return True
        
        # Strategy 2: Check if extracted name contains primary case's distinctive parts
        # Example: "MELONE Railroad Co." contains "melone" from "Gopher Media v. Melone"
        primary_parts = primary_normalized.split(' v ')
        if len(primary_parts) == 2:
            plaintiff = primary_parts[0].strip()
            defendant = primary_parts[1].strip()
            
            # If both plaintiff AND defendant appear in extracted name, it's contamination
            # Single match could be coincidence (e.g., "United States" appears often)
            if plaintiff in extracted_normalized and defendant in extracted_normalized:
                if debug:
                    logger.warning(f"[CONTAMINATION-FILTER] Both parties match:")
                    logger.warning(f"  Extracted: '{extracted_name}'")
                    logger.warning(f"  Primary plaintiff: '{plaintiff}', defendant: '{defendant}'")
                return True
            
            # FIX: Also check for distinctive words from PLAINTIFF
            common_parties = ['united states', 'state', 'county', 'city', 'government', 'people']
            plaintiff_words = [word for word in plaintiff.split() if len(word) > 5]  # Very distinctive words
            for plaint_word in plaintiff_words:
                if plaint_word not in common_parties and plaint_word in extracted_normalized:
                    if debug:
                        logger.warning(f"[CONTAMINATION-FILTER] Plaintiff word match:")
                        logger.warning(f"  Extracted: '{extracted_name}'")
                        logger.warning(f"  Matched word: '{plaint_word}' from plaintiff '{plaintiff}'")
                    return True
            
            # If defendant is distinctive (>8 chars, not common) and appears, likely contamination
            # Common defendants like "United States" don't count
            common_parties = ['united states', 'state', 'county', 'city', 'government']
            
            # FIX: Check for ANY distinctive word from defendant, not just full name
            # "MELONE Railroad" should match defendant "andrew melone" via "melone"
            defendant_words = [word for word in defendant.split() if len(word) > 4]  # Significant words only
            for def_word in defendant_words:
                if def_word not in common_parties and def_word in extracted_normalized:
                    if debug:
                        logger.warning(f"[CONTAMINATION-FILTER] Defendant word match:")
                        logger.warning(f"  Extracted: '{extracted_name}'")
                        logger.warning(f"  Matched word: '{def_word}' from defendant '{defendant}'")
                    return True
            
            # Also check full defendant name (original logic)
            if (len(defendant) > 8 and 
                defendant not in common_parties and 
                defendant in extracted_normalized):
                if debug:
                    logger.warning(f"[CONTAMINATION-FILTER] Full defendant match:")
                    logger.warning(f"  Extracted: '{extracted_name}'")
                    logger.warning(f"  Primary defendant: '{defendant}'")
                return True
        
        # Strategy 3: Check similarity ratio (fuzzy matching)
        # If names are >80% similar, likely contamination
        # Only check if both names have similar length (within 50%)
        len_ratio = min(len(extracted_normalized), len(primary_normalized)) / max(len(extracted_normalized), len(primary_normalized))
        if len_ratio > 0.5:  # Similar length
            # Calculate simple similarity (word overlap)
            extracted_words = set(extracted_normalized.split())
            primary_words = set(primary_normalized.split())
            
            if len(primary_words) > 0:
                overlap = len(extracted_words & primary_words)
                similarity = overlap / len(primary_words)
                
                if similarity > 0.8:  # >80% of primary case words appear in extracted
                    if debug:
                        logger.warning(f"[CONTAMINATION-FILTER] High similarity ({similarity:.2%}):")
                        logger.warning(f"  Extracted: '{extracted_name}'")
                        logger.warning(f"  Primary: '{self.document_primary_case_name}'")
                    return True
        
        return False
    
    def _extract_with_position(self, text: str, citation: str, start_index: int, end_index: int, debug: bool) -> Optional[MasterExtractionResult]:
        """Position-aware extraction with optimized context window."""
        # FIX #68: Increase context window to 400 chars to handle multi-line case names
        # Standard format: "Case Name, Citation, Year" requires looking back ~200 chars
        # But case names split across lines need more context to capture complete name
        context_start = max(0, start_index - 400)  # FIX #68: Increased from 200 to 400
        # FIX #38: ONLY look BACKWARD! Context must end at START of citation, not END!
        # Fix #32 used end_index which allowed 15 chars of forward context (citation length),
        # causing extraction of "Spokane County" (after citation) instead of "Lopez Demetrio" (before).
        context_end = start_index  # FIX #38: Context ends at citation START, not END!
        
        # FIX #42: CRITICAL - Log ACTUAL values used to create context
        if debug:
            logger.error(f"🔍 FIX #42: Creating context with:")
            logger.error(f"   start_index = {start_index}")
            logger.error(f"   end_index = {end_index}")
            logger.error(f"   context_start = {context_start} (start_index - 400)")
            logger.error(f"   context_end = {context_end} (should == start_index)")
            logger.error(f"   Slicing: text[{context_start}:{context_end}]")
        
        context = text[context_start:context_end]
        
        # FIX #67: Filter out document headers and metadata
        # Headers often contain text like "SUPREME COURT CLERK", "FILED", etc. that contaminate extraction
        context = self._filter_header_contamination(context, debug)
        
        # FIX #68: Normalize whitespace to handle PDF line breaks
        # PDF extraction adds \n in the middle of case names, causing severe truncation
        # Example: "E. Palo Alto v. U.S. Dep't\nof Health" → "E. Palo Alto v. U.S. Dep't of Health"
        context = self._normalize_whitespace_for_extraction(context, debug)
        
        # FIX #40: CRITICAL ASSERTION - Context must NOT include the citation itself!
        # This catches any bugs where context extends past start_index
        citation_snippet = citation[:min(10, len(citation))]  # First 10 chars of citation
        if citation_snippet in context:
            logger.error(f"🚨 CRITICAL BUG: Context includes citation '{citation_snippet}'!")
            logger.error(f"   Context window: [{context_start}:{context_end}]")
            logger.error(f"   Last 50 chars of context: '{context[-50:]}'")
            # Force context to end before citation
            context = text[context_start:start_index]
        
        if debug:
            logger.warning(f"🔍 POSITION_EXTRACT: Context ({len(context)} chars): '{context[:100]}...'")
            logger.warning(f"   Context window: [{context_start}:{context_end}]")
            logger.warning(f"   Full context: '{context}'")
            logger.warning(f"   Text AFTER citation (next 150 chars): '{text[end_index:end_index+150]}'")
        
        # Try all patterns on the focused context
        for i, pattern in enumerate(self.case_name_patterns):
            # FIX #41: CRITICAL - Log EXACTLY what's passed to regex.search
            if debug:
                logger.warning(f"🔍 FIX #41: About to search pattern {i}")
                logger.warning(f"   Context type: {type(context)}, length: {len(context)}")
                logger.warning(f"   Last 50 chars of context: {repr(context[-50:])}")
                if "Spokane" in context:
                    logger.error(f"🚨 FIX #41: 'Spokane' IS in context before regex!")
                else:
                    logger.warning(f"✅ FIX #41: 'Spokane' NOT in context before regex")
            
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                if debug:
                    logger.warning(f"✅ Pattern {i} matched: {pattern[:60]}...")
                    logger.warning(f"   Groups: {match.groups()}")
                    logger.warning(f"   Match position in context: {match.start()}-{match.end()}")
                    logger.warning(f"   Match text: '{match.group(0)}'")
                case_name = self._build_case_name_from_match(match, pattern, debug)
                if debug:
                    logger.warning(f"   Built case name: '{case_name}'")
                    # FIX #40B: Track if "Spokane" appears at this stage
                    if "Spokane" in case_name:
                        logger.error(f"🚨 BUG: 'Spokane' in BUILT case_name!")
                year = self._extract_year_from_context(context, debug)
                
                if case_name and len(case_name.strip()) > 3:
                    cleaned_name = self._clean_case_name(case_name)
                    if debug:
                        logger.warning(f"   Cleaned case name: '{cleaned_name}'")
                        # FIX #40B: Track if "Spokane" appears at this stage
                        if "Spokane" in cleaned_name:
                            logger.error(f"🚨 BUG: 'Spokane' in CLEANED case_name!")
                    
                    # P3 FIX: CRITICAL - Validate to filter contamination BEFORE accepting extraction
                    if not self._looks_like_case_name(cleaned_name, debug):
                        if debug:
                            logger.warning(f"   ❌ REJECTED by validation (contamination or invalid): '{cleaned_name[:100]}'")
                        continue  # Try next pattern
                    
                    preferred_name, preferred_year, canonical_meta = self._apply_canonical_preferences(
                        citation,
                        cleaned_name,
                        year,
                    )
                    if debug:
                        # FIX #40B: Track if "Spokane" appears at this stage
                        if "Spokane" in str(preferred_name):
                            logger.error(f"🚨 BUG: 'Spokane' in PREFERRED case_name!")
                    if debug:
                        logger.warning(f"   After canonical preferences:")
                        logger.warning(f"      preferred_name: '{preferred_name}'")
                        logger.warning(f"      canonical_meta: {canonical_meta}")
                    canonical_year_value = extract_year_value(
                        canonical_meta.get("canonical_year") or canonical_meta.get("canonical_date")
                    )
                    if debug:
                        logger.warning(f"   Creating result with:")
                        logger.warning(f"      case_name (display): '{preferred_name or 'N/A'}'")
                        logger.warning(f"      extracted_case_name: '{cleaned_name}'")
                        logger.warning(f"      canonical_name: '{canonical_meta.get('canonical_name')}'")
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
        
        # FIX #68: Increase context window to 400 chars to handle multi-line case names
        # "Case Name, Citation, Year" format requires looking back ~200 chars
        # But case names split across lines need more context to capture complete name
        context_start = max(0, citation_pos - 400)  # FIX #68: Increased from 200 to 400
        # FIX #38: Context must end at citation START, not END!
        # Using citation_pos + len(citation) includes the citation itself and text after it,
        # causing forward contamination. Context should end where citation BEGINS.
        context_end = citation_pos  # FIX #38: Context ends at citation START!
        context = text[context_start:context_end]
        
        # FIX #67: Filter out document headers and metadata
        context = self._filter_header_contamination(context, debug)
        
        # FIX #68: Normalize whitespace to handle PDF line breaks
        context = self._normalize_whitespace_for_extraction(context, debug)
        
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
        
        # FIX #67: Filter out document headers and metadata
        sample_text = self._filter_header_contamination(sample_text, debug)
        
        # FIX #68: Normalize whitespace to handle PDF line breaks
        sample_text = self._normalize_whitespace_for_extraction(sample_text, debug)
        
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
        
        # CRITICAL FIX: Remove sentence fragments BEFORE normalizing whitespace
        # Look for patterns like "scheme as a whole. Ass'n of..." and keep only "Ass'n of..."
        cleaned = case_name.strip()
        
        # FIX #68C: Match full case name, not just minimum
        # OLD: r'\.\s+([A-Z].+?\s+v\.\s+.+?)$' used NON-GREEDY .+? which truncated names
        # NEW: Use greedy .+ to capture complete case names
        # Match: sentence-ending period followed by spaces/newline, then case name with "v."
        # Look for the last occurrence of ". " followed by capital letter and a "v." pattern
        case_name_match = re.search(r'\.\s+([A-Z].+\s+v\.\s+.+)$', cleaned)
        if case_name_match:
            potential_name = case_name_match.group(1).strip()
            # Verify it looks like a case name (has "v." and starts with capital)
            if ' v. ' in potential_name:
                cleaned = potential_name
        
        # NOW normalize whitespace after we've extracted the case name
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # DEBUG: Log for contamination issue
        if 'Batzel' in cleaned or 'doctrine' in cleaned.lower():
            logger.error(f"[CONTAMINATION-DEBUG] Before cleaning: '{cleaned}'")
        
        # Remove common prefixes that indicate contamination
        # USER FIX: Protect special case type prefixes from removal
        contamination_prefixes = [
            r'^(?:The case of|As stated in|Citing|Following|See)\s+',
            r'^(?:court held that|established|the defendant)\s*[.\s]*',
            r'^(?:of\s+law)[\s\.]*',
            # Only remove "In " if NOT part of case type prefixes
            # Protect: "In re", "In the matter of"
            r'^In\s+(?!re\s|the\s+matter\s)',
            # Only remove "Matter " if NOT "Matter of"
            r'^Matter\s+(?!of\s)',
            # Only remove "Estate " if NOT "Estate of"  
            r'^Estate\s+(?!of\s)',
            # Only remove "Ex " if NOT "Ex parte"
            r'^Ex\s+(?!parte\s)',
        ]
        
        for prefix in contamination_prefixes:
            cleaned = re.sub(prefix, '', cleaned, flags=re.IGNORECASE)
        
        # NEW: Remove descriptive legal phrases and status words that contaminate case names
        # Strategy: If we detect contamination words, try to extract just the case name portion
        
        # First, remove common procedural introducers at the start
        procedural_prefixes = [
            r'^(?:under|applying|following|citing|relying on|See|see)\s+',
        ]
        for pattern in procedural_prefixes:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # If there's a "v." pattern, look for contamination words before it
        if ' v. ' in cleaned:
            # Check for contamination keywords
            contamination_words = ['doctrine', 'rule', 'test', 'standard', 'principle', 'holding', 
                                  'overruling', 'superseding', 'superseded', 'overruled', 'reversed', 
                                  'affirming', 'affirmed', 'modifying', 'modified']
            
            has_contamination = any(word in cleaned.lower() for word in contamination_words)
            
            if has_contamination:
                # Extract just the case name: find the pattern "PartyName v. PartyName"
                # Look for the last occurrence of a capital letter followed by party names and "v."
                case_match = re.search(r'\b([A-Z][\w\'\.\-]+(?:\s+(?:of|&|and|v\.)\s+[\w\'\.\-]+)*(?:\s+[A-Z][\w\'\.\-]+)*)\s+v\.\s+([A-Z][\w\'\.\-,\s&]+(?:Inc\.|Corp\.|LLC|Ltd\.|Co\.|Company|[A-Z][\w\'\.\-]+)*)(?:\s|$)', cleaned)
                if case_match:
                    plaintiff = case_match.group(1).strip()
                    defendant = case_match.group(2).strip()
                    
                    # Verify plaintiff doesn't start with a contamination word
                    first_word = plaintiff.split()[0].lower() if plaintiff.split() else ""
                    if first_word not in contamination_words:
                        cleaned = f"{plaintiff} v. {defendant}"
                        # Remove trailing punctuation that might have been captured
                        cleaned = re.sub(r'\s*[,;\.]+$', '', cleaned)
        
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
    canonical_date: Optional[str] = None,
    document_primary_case_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    THE SINGLE, UNIFIED EXTRACTION FUNCTION
    
    This function replaces ALL 120+ duplicate extraction functions.
    Use this instead of:
    - extract_case_name_and_date_master()
    - extract_case_name_and_year_unified()
    - _extract_case_name_enhanced()
    - All other duplicate functions
    
    Args:
        document_primary_case_name: The primary case name of the document being analyzed.
                                   Used to filter out contamination.
    
    Returns:
        Dictionary with case_name, year, confidence, method, and debug_info
    """
    extractor = get_master_extractor()
    
    # CRITICAL FIX: ALWAYS set document primary case name (even if None) to ensure consistency
    # across singleton extractor instance. Otherwise, old value persists across calls.
    extractor.document_primary_case_name = document_primary_case_name
    if document_primary_case_name:
        logger.warning(f"[CONTAMINATION-FILTER] Set document primary case: '{document_primary_case_name[:80]}'")

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
            # CRITICAL FIX: When returning cached canonical data, keep extracted fields separate
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
                'canonical_name': cached_meta['canonical_name'],
                'canonical_year': cached_meta['canonical_date'],
                'extracted_case_name': "N/A",  # No extraction performed when using cache
                'extracted_year': "N/A",  # No extraction performed when using cache
            }

    result = extractor.extract_case_name_and_date(text, citation, start_index, end_index, debug)

    if citation:
        extractor._update_canonical_cache(
            citation,
            canonical_name=result.canonical_name,
            canonical_date=result.canonical_year,
        )

    # CRITICAL FIX: extracted_case_name must ONLY contain text from document, NEVER canonical data
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
        'extracted_case_name': result.extracted_case_name or "N/A",  # NEVER use canonical
        'extracted_year': result.extracted_year or "N/A",  # NEVER use canonical
    }
