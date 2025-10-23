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
        # Accept special case types (In re, Ex parte, In the matter) or adversarial cases (v.)
        lower = cleaned.lower()
        if lower.startswith("in re ") or lower.startswith("ex parte ") or lower.startswith("in the matter"):
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
            
            # Government patterns - made defendant pattern greedy to capture full names
            r'([A-Z][a-zA-Z\s\'&\-\.,]*?)\s+[Vv]\.?\s+(United\s+States|U\.S\.|UNITED\s+STATES)',
            r'(United\s+States|U\.S\.|UNITED\s+STATES)\s+[Vv]\.?\s+([A-Z][a-zA-Z\s\'&\-\.,]+)',  # Made greedy to get full defendant
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
        
        # USER FIX: Strategy -1 - Simple citation format (NEW - PREPROCESSING)
        # Handle case where user submits just "Case Name, Citation (Year)" without context
        # Pattern: "Carman v. Adventure Bound, 198 Cal.App.3d 449 (1986)"
        if citation:
            simple_pattern = r'^([A-Z][a-zA-Z\s\'&\-,\.]+\s+[Vv]\.?\s+[A-Z][a-zA-Z\s\'&\-,\.]+),\s+\d+\s+[A-Z][a-z\.]+\d*\s+\d+\s*\((\d{4})\)\s*$'
            match = re.match(simple_pattern, text.strip())
            if match:
                extracted_name = match.group(1).strip()
                extracted_year = match.group(2)
                logger.warning(f"✅ [SIMPLE-FORMAT] Extracted from standalone citation: '{extracted_name}' ({extracted_year})")
                return MasterExtractionResult(
                    case_name=extracted_name,
                    year=extracted_year,
                    confidence=0.95,
                    method="simple_citation_format",
                    debug_info={"pattern": "standalone_citation"},
                    extracted_case_name=extracted_name,
                    extracted_year=extracted_year
                )
        
        # FIX #69: Strategy 0 - Comma-anchored extraction (NEW - HIGHEST PRIORITY)
        # Use comma before citation as anchor to work backwards and find full case name
        # This fixes truncation issues like "E. Palo Alto v. U." → "Cmty. Legal Servs. in E. Palo Alto v. U.S. Dep't..."
        if citation and start_index is not None:
            if force_debug:
                logger.warning(f"🔍 FIX #69: Trying Strategy 0 - Comma-anchored extraction")
            result = self._extract_with_comma_anchor(text, citation, start_index, debug or force_debug)
            if result and result.case_name and result.case_name != 'N/A':
                # Validate extraction against canonical metadata
                self._validate_extraction(result, citation, debug or force_debug)
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
                # Validate extraction against canonical metadata if available
                self._validate_extraction(result, citation, debug or force_debug)
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
                # Validate extraction against canonical metadata
                self._validate_extraction(result, citation, debug)
                return result
        
        # Strategy 3: Pattern-based extraction (last resort)
        result = self._extract_with_patterns(normalized_text, citation, debug)
        if result and result.case_name and result.case_name != 'N/A':
            return result
        
        # No extraction succeeded
        logger.warning(f"⚠️ [EXTRACTION-FAILED] All strategies failed for citation: '{citation}'")
        
        # FIX #MISMATCH: Try to get canonical metadata as last resort
        if citation:
            canonical_metadata = self._get_canonical_metadata(citation)
            if canonical_metadata and canonical_metadata.get('canonical_name'):
                logger.warning(f"📚 [CANONICAL-FALLBACK] Using canonical name for failed extraction: {canonical_metadata['canonical_name']}")
                return MasterExtractionResult(
                    case_name=canonical_metadata['canonical_name'],
                    year=canonical_metadata.get('canonical_date', 'N/A'),
                    confidence=0.8,  # High confidence since it's from canonical source
                    method="canonical_fallback",
                    debug_info={"reason": "Extraction failed, used canonical metadata"},
                    canonical_name=canonical_metadata['canonical_name'],
                    canonical_year=canonical_metadata.get('canonical_date'),
                    extracted_case_name='N/A',  # Mark that extraction failed
                    extracted_year='N/A'
                )
        
        return MasterExtractionResult(
            case_name="N/A",
            year="N/A",
            confidence=0.0,
            method="extraction_failed",
            debug_info={"reason": "All extraction strategies failed and no canonical metadata available"}
        )
    
    def _validate_extraction(self, result: MasterExtractionResult, citation: str, debug: bool) -> None:
        """
        FIX #MISMATCH: Validate extracted name against canonical metadata.
        
        This helps identify extraction errors by comparing what we extracted
        with what the authoritative source says. Logs warnings for significant mismatches.
        
        Args:
            result: The extraction result to validate
            citation: The citation being validated
            debug: Enable debug logging
        """
        if not citation or not result.case_name or result.case_name == 'N/A':
            return
        
        # Get canonical metadata
        canonical_metadata = self._get_canonical_metadata(citation)
        if not canonical_metadata or not canonical_metadata.get('canonical_name'):
            return  # No canonical data to validate against
        
        canonical_name = canonical_metadata['canonical_name']
        extracted_name = result.case_name
        
        # Normalize for comparison
        norm_extracted = extracted_name.lower().strip().replace('  ', ' ')
        norm_canonical = canonical_name.lower().strip().replace('  ', ' ')
        
        # Check if names are similar (handle abbreviations)
        if norm_extracted == norm_canonical:
            return  # Perfect match
        
        # Check for common abbreviations
        abbreviations = {
            'ins': 'immigration and naturalization service',
            'dep\'t': 'department',
            'att\'y': 'attorney',
            'gen.': 'general'
        }
        
        exp_extracted = norm_extracted
        exp_canonical = norm_canonical
        for abbr, full in abbreviations.items():
            exp_extracted = exp_extracted.replace(abbr, full)
            exp_canonical = exp_canonical.replace(abbr, full)
        
        if exp_extracted == exp_canonical:
            return  # Match after abbreviation expansion
        
        # Check if extracted is contained in canonical (partial extraction)
        if len(norm_extracted) > 10 and norm_canonical.find(norm_extracted) >= 0:
            logger.info(f"ℹ️ [PARTIAL-MATCH] Extracted name is subset of canonical for {citation}")
            return  # Acceptable partial match
        
        # Check if canonical is contained in extracted (over-extraction)
        if len(norm_canonical) > 10 and norm_extracted.find(norm_canonical) >= 0:
            logger.info(f"ℹ️ [OVER-EXTRACTION] Extracted name contains canonical for {citation}")
            return  # Acceptable over-extraction
        
        # Check last names match (common for abbreviated forms)
        extracted_parts = norm_extracted.split(' v. ')
        canonical_parts = norm_canonical.split(' v. ')
        if len(extracted_parts) == 2 and len(canonical_parts) == 2:
            ext_last = extracted_parts[0].split()[-1]
            can_last = canonical_parts[0].split()[-1]
            if ext_last == can_last:
                logger.info(f"ℹ️ [LASTNAME-MATCH] Last names match for {citation}, likely abbreviation")
                return
        
        # Significant mismatch detected - log warning
        logger.warning(f"⚠️ [EXTRACTION-MISMATCH] Possible extraction error for {citation}")
        logger.warning(f"   Extracted: '{extracted_name}'")
        logger.warning(f"   Canonical: '{canonical_name}'")
        logger.warning(f"   Method: {result.method}")
        logger.warning(f"   Confidence: {result.confidence}")
        
        # Store canonical data in result for reference
        result.canonical_name = canonical_name
        result.canonical_year = canonical_metadata.get('canonical_date')
    
    def _filter_header_contamination(self, context: str, debug: bool) -> str:
        """
        FIX #67: Remove document headers and metadata that contaminate extraction.
        
        CRITICAL FIX: Only filter lines that are PURE headers, not case discussion.
        Lines with case names (containing "v.") should NEVER be filtered.
        
        Filters out lines containing:
        - Court identifiers IN ALL CAPS: "SUPREME COURT" (but not "Supreme Court")
        - Filing metadata headers: "FILED", "FILE ", "CLERK'S OFFICE"
        - Dates in header format
        - Pure all-caps lines (likely headers)
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
        
        # CRITICAL: Case name pattern - lines containing this should NEVER be filtered
        case_name_pattern = r'\bv\.\s+[A-Z]'  # " v. " followed by capital letter
        
        # Header patterns to exclude - ONLY for pure headers, not case discussion
        header_patterns = [
            r'^\s*[A-Z\s,\.\-]{10,}$',  # All-caps lines (at least 10 chars, only caps/spaces/punctuation)
            r'^\s*IN THE .+ COURT\s*$',  # Pure court header lines (start of line)
            r'^\s*FILED:?\s*\d',  # "FILED: 01/15/2024"
            r"^\s*CLERK['\']?S? OFFICE\s*$",  # Pure clerk line
            r'^\s*No\.\s+\d+-\d+\s*$',  # Pure case number like "No. 102976-4" (alone on line)
            r'^\s*\d{1,2}/\d{1,2}/\d{4}\s*$',  # Pure date stamps
            r'^\s*[A-Z]{3,}\s+\d{1,2},\s+\d{4}\s*$',  # "JUNE 12, 2025" (alone on line)
        ]
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # CRITICAL: Never filter lines containing case names (have " v. ")
            if re.search(case_name_pattern, line_stripped):
                filtered_lines.append(line)
                if debug:
                    logger.warning(f"[FIX #67] KEPT case name line: '{line_stripped[:80]}'")
                continue
                
            # Check if line matches any header pattern
            is_header = False
            for pattern in header_patterns:
                if re.search(pattern, line_stripped):
                    is_header = True
                    if debug:
                        logger.warning(f"[FIX #67] Filtering header line: '{line_stripped[:80]}'")
                    break
            
            # Also filter very short lines (< 8 chars) that are likely headers (lowered from 10)
            if not is_header and len(line_stripped) < 8:
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
        
        # FIX #9: Enhanced line break handling for citations split across lines
        # Handles: "17 F.\n4th 901" → "17 F. 4th 901"
        # Replace newlines with spaces
        # This allows case names that span multiple lines to be captured as a single string
        normalized = context.replace('\n', ' ')
        
        # Replace tabs with spaces
        normalized = normalized.replace('\t', ' ')
        
        # FIX #9b: Collapse multiple spaces that result from line break removal
        # "F.  4th" → "F. 4th" (ensures proper citation format)
        normalized = re.sub(r'\s{2,}', ' ', normalized)
        
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
        print(f"[PHASE6-ENTRY] Comma anchor called for: {citation} at pos {start_index}", flush=True)
        
        # Step 1: Find comma before citation (within 100 chars, allowing for whitespace and semicolons)
        # PHASE 6 FIX: Increased from 10 to 100 to handle:
        #   - Pinpoint citations like ", 157"
        #   - Semicolon-separated citation series (semicolon can be 40+ chars before citation)
        pre_citation_text = text[max(0, start_index - 100):start_index]
        
        # FIX #69 DEBUG: Log what we're checking for comma
        logger.error(f"[FIX #69 COMMA CHECK] Pre-citation text: '{pre_citation_text}'")
        logger.error(f"[FIX #69 COMMA CHECK] Text at citation pos: '{text[start_index:start_index+50]}'")
        
        if ',' not in pre_citation_text:
            logger.error(f"[FIX #69 FAIL] No comma found in '{pre_citation_text}' - falling back")
            print(f"[PHASE6-FAIL] No comma in 100 chars before {citation}: '{pre_citation_text}'", flush=True)
            return None  # No comma anchor, fall back to other methods
        else:
            print(f"[PHASE6-OK] Found comma in pre-text: '{pre_citation_text}'", flush=True)
        
        # PHASE 6 FIX: Check for semicolons FIRST (they separate different cases)
        # If there's a semicolon in the pre-text, only search for comma AFTER the last semicolon
        # Example: "Cayuga..., 761 F.3d 218; Oneida..., 605 F.3d 149"
        #                          comma1 ↑    semicolon ↑    comma2 ↑ (we want comma2)
        if ';' in pre_citation_text:
            # Find the LAST semicolon (in case there are multiple citation groups)
            last_semicolon_offset = pre_citation_text.rfind(';')
            print(f"[PHASE6] Semicolon found in pre-text - searching for comma after it", flush=True)
            
            # Only search for comma AFTER the last semicolon
            text_after_semicolon = pre_citation_text[last_semicolon_offset + 1:]
            if ',' in text_after_semicolon:
                comma_offset_after_semicolon = text_after_semicolon.rfind(',')
                # Calculate absolute position
                comma_pos = start_index - (len(pre_citation_text) - last_semicolon_offset - 1 - comma_offset_after_semicolon)
                print(f"[PHASE6] Found comma after semicolon", flush=True)
            else:
                print(f"[PHASE6] No comma after semicolon - falling back", flush=True)
                return None
        else:
            # No semicolon - just find the last comma in the pre-text
            comma_offset = pre_citation_text.rfind(',')
            comma_pos = start_index - (len(pre_citation_text) - comma_offset)
        
        # FIX #69 DEBUG: Always log comma position
        logger.error(f"[FIX #69 SUCCESS] Found comma at position {comma_pos} (citation at {start_index})")
        
        # Step 2: Detect subsequent history and expand context if needed
        # Subsequent history indicators: "affirmed by", "reversed by", "vacated by", etc.
        subsequent_history_phrases = [
            r'judgment\s+vacated\s+(?:and\s+opinion\s+)?(?:repudiated\s+)?by',
            r"(?:aff['\u2019]?d|affirmed)(?:\s+(?:in\s+part|by))?",
            r"(?:rev['\u2019]?d|reversed)(?:\s+(?:in\s+part|by))?",
            r'(?:vacated|remanded)(?:\s+(?:and\s+remanded|by))?',
            r'overruled\s+by',
            r'superseded\s+by',
            r'modified\s+by',
            r'cert\.\s+(?:denied|granted)(?:\s+by)?',
        ]
        
        # Check for subsequent history in the 200 chars before the citation
        check_window = text[max(0, comma_pos - 200):comma_pos]
        has_subsequent_history = False
        
        for phrase_pattern in subsequent_history_phrases:
            if re.search(phrase_pattern, check_window, re.IGNORECASE):
                has_subsequent_history = True
                logger.error(f"[FIX #7 SUBSEQUENT] Detected subsequent history: '{phrase_pattern}'")
                break
        
        # Expand context window for subsequent history citations
        # FIX #12: Increased standard window from 400 to 600 to catch more short-form citations
        # Standard: 600 chars, Subsequent history: 800 chars (to reach original case name)
        context_window = 800 if has_subsequent_history else 600
        search_start = max(0, comma_pos - context_window)
        potential_case_name = text[search_start:comma_pos]
        
        # FIX #69 DEBUG: Always log context
        logger.error(f"[FIX #69 CONTEXT] Length: {len(potential_case_name)} chars (window: {context_window})")
        logger.error(f"[FIX #69 CONTEXT] Last 100: '{potential_case_name[-100:]}'")
        
        # USER FIX: Handle "vacated and remanded" pattern  
        # When Supreme Court citations follow "vacated and remanded", extract case name from BEFORE vacatur
        vacatur_patterns = [
            r'vacated\s+and\s+remanded',
            r'vacated',
            r'aff\'d',
            r'affirmed', 
            r'reversed',
            r'rev\'d',
            r'remanded'
        ]
        
        if debug:
            logger.warning(f"🔍 VACATUR_COMMA_ANCHOR: Checking for vacatur patterns before citation '{citation}'")
        
        for vacatur_pattern in vacatur_patterns:
            vacatur_match = re.search(vacatur_pattern, potential_case_name, re.IGNORECASE)
            if debug:
                logger.warning(f"🔍 VACATUR_COMMA_ANCHOR: Pattern '{vacatur_pattern}' -> {'FOUND' if vacatur_match else 'NOT FOUND'}")
            
            if vacatur_match:
                # USER FIX: Check if there's a semicolon between vacatur and citation
                # Semicolons separate different cases - don't apply vacatur across this boundary
                text_after_vacatur = potential_case_name[vacatur_match.end():]
                if ';' in text_after_vacatur:
                    if debug:
                        logger.warning(f"🔍 VACATUR_COMMA_ANCHOR: SEMICOLON found between vacatur and citation - SKIPPING vacatur logic")
                    continue  # Skip this vacatur pattern - it's for a different case
                
                # Found vacatur - extract case name BEFORE it
                text_before_vacatur = potential_case_name[:vacatur_match.start()]
                
                # Look for case name pattern: "Name v. Name, ### F.3d"
                case_name_pattern = r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*(?:\s+of\s+[A-Z\.\s]+)*)\s+v\.\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*(?:\s+of\s+[A-Z\.\s]+)*),\s+\d+\s+F\.'
                case_matches = list(re.finditer(case_name_pattern, text_before_vacatur))
                
                if debug:
                    logger.warning(f"🔍 VACATUR_COMMA_ANCHOR: Found {len(case_matches)} matches before vacatur")
                    if case_matches:
                        for idx, match in enumerate(case_matches):
                            logger.warning(f"🔍 VACATUR_COMMA_ANCHOR: Match {idx+1}: '{match.group(0)}'")
                
                if case_matches:
                    # Take LAST match (closest to vacatur)
                    last_match = case_matches[-1]
                    plaintiff = last_match.group(1).strip()
                    defendant = last_match.group(2).strip()
                    
                    # Clean case names
                    from src.utils.text_normalizer import clean_extracted_case_name
                    plaintiff = clean_extracted_case_name(plaintiff)
                    defendant = clean_extracted_case_name(defendant)
                    vacatur_case_name = f"{plaintiff} v. {defendant}"
                    
                    if debug:
                        logger.warning(f"✅ VACATUR_COMMA_ANCHOR: Detected '{vacatur_pattern}'")
                        logger.warning(f"✅ VACATUR_COMMA_ANCHOR: Extracted '{vacatur_case_name}'")
                    
                    # Validate
                    if len(plaintiff) >= 3 and len(defendant) >= 3 and len(vacatur_case_name) > 10:
                        # USER FIX: For Supreme Court citations, look for year AFTER the current citation
                        # Example: "562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587 (2011)"
                        # The year (2011) is at the END of all parallel citations
                        
                        # Check if this is a Supreme Court citation (U.S., S.Ct., L.Ed.)
                        is_supreme_court = any(x in citation for x in ['U.S.', 'S. Ct.', 'L. Ed.']) if citation else False
                        
                        year = None
                        
                        if is_supreme_court:
                            # For Supreme Court citations, look for year AFTER current citation
                            # This handles parallel citations like "562 U.S. 42, 131 S. Ct. 704 (2011)"
                            after_citation_text = text[start_index:start_index + 200]
                            year = self._extract_year_from_context(after_citation_text, debug)
                            
                            if debug and year:
                                logger.warning(f"🔍 VACATUR_YEAR: Found Supreme Court year '{year}' after citation")
                        
                        # Fallback: Extract from Federal reporter citation
                        if not year:
                            fed_match_end_pos = last_match.end()
                            year_search_text = text_before_vacatur[fed_match_end_pos:fed_match_end_pos + 50]
                            year = self._extract_year_from_context(year_search_text, debug)
                            
                            if debug and year:
                                logger.warning(f"🔍 VACATUR_YEAR: Found year '{year}' from Federal citation")
                        
                        if debug:
                            logger.warning(f"🔍 VACATUR_YEAR: Final extracted year '{year}' for '{vacatur_case_name}'")
                        
                        logger.error(f"[VACATUR_SUCCESS] Returning: '{vacatur_case_name}' ({year}) for '{citation}'")
                        return MasterExtractionResult(
                            case_name=vacatur_case_name,
                            year=year or "Unknown",
                            confidence=0.98,
                            method="vacatur_comma_anchor",
                            debug_info={"vacatur_pattern": vacatur_pattern, "year": year},
                            extracted_case_name=vacatur_case_name,
                            extracted_year=year
                        )
                
                if debug:
                    logger.warning(f"🔍 VACATUR_COMMA_ANCHOR: Found '{vacatur_pattern}' but no case name match")
                break  # Only check first matching vacatur pattern
        
        # Step 3: Normalize whitespace and Unicode artifacts (Fix #68)
        potential_case_name = self._normalize_whitespace_for_extraction(potential_case_name, debug)
        logger.error(f"[FIX #69 NORMALIZED] Length: {len(potential_case_name)} chars")
        
        # FIX #11/#13: Clean case/docket numbers from context BEFORE pattern matching
        # This prevents header contamination like "No. 103430 -0 15" from breaking patterns
        # NOTE: Don't add digits to patterns - that would capture page numbers!
        context_cleaned = potential_case_name
        
        # FIX #13: More aggressive case number removal
        # Pattern: "No. 103430-0 15 v." where the case number has internal spaces/breaks
        # Strategy: Remove ANY sequence of "No." + [digits/hyphens/spaces] that ends before " v."
        # This handles: "Inc. No. 103430-0 15 v. Marston" → "Inc. v. Marston"
        context_cleaned = re.sub(r'\s+No\.\s+[\d\-\s]+(?=\s+v\.)', ' ', context_cleaned, flags=re.IGNORECASE)
        
        # Remove case numbers after "v." (from page headers)
        context_cleaned = re.sub(r'\s+\d+\s+No\.\s+[\d\-]+\s+', ' ', context_cleaned, flags=re.IGNORECASE)
        context_cleaned = re.sub(r'\s+No\.\s+[\d\-\s]+\-[\d\-\s]+\s+', ' ', context_cleaned, flags=re.IGNORECASE)
        
        if context_cleaned != potential_case_name:
            logger.error(f"[FIX #11] Cleaned case numbers from context")
            logger.error(f"[FIX #11] Before: '{potential_case_name[-100:]}'")
            logger.error(f"[FIX #11] After:  '{context_cleaned[-100:]}'")
        
        # Step 4: FIX #8 - Proximity-based case name extraction
        # Find ALL candidate case names and pick the CLOSEST one to the citation
        
        # Define patterns for case names (not anchored to end)
        # IMPORTANT: NO DIGITS in patterns - page numbers would match!
        patterns = [
            # Pattern 0: "See [Case Name]" - HIGHEST PRIORITY
            (r'(?:See|see|Citing|citing|Compare|compare)\s+([A-Z][a-zA-Z\s\'&\-\.,]{5,}\s+v\.\s+[A-Z][a-zA-Z\s\'&\-\.,]{5,})', 0, 'signal_word'),
            
            # Pattern 1: "In re" cases
            (r'(In\s+re\s+[A-Z][a-zA-Z\s\'&\-\.,]{3,})', 1, 'in_re'),
            
            # Pattern 2: "Ex parte" cases
            (r'(Ex\s+parte\s+[A-Z][a-zA-Z\s\'&\-\.,]{3,})', 1, 'ex_parte'),
            
            # Pattern 3: Full case name with "v."
            (r'([A-Z][a-zA-Z\s\'&\-\.,]{5,}\s+v\.\s+[A-Z][a-zA-Z\s\'&\-\.,]{5,})', 2, 'standard'),
            
            # Pattern 4: FIX #12 - Short-form citations (single party name at END)
            # Matches: "... that [Endnote 18] Marston" where full case appears earlier
            # Only matches if at very end of context (last 20 chars) to avoid false positives
            # Accepts single capitalized word of 4+ chars (Marston, Smith, etc.)
            (r'([A-Z][a-zA-Z]{3,}(?:\s+[A-Z][a-zA-Z]+)*)$', 10, 'short_form'),
        ]
        
        # Find all candidate case names with their positions
        # FIX #11: Use cleaned context for pattern matching AND position calculations
        candidates = []
        for pattern, priority, pattern_type in patterns:
            for match in re.finditer(pattern, context_cleaned, re.IGNORECASE):
                case_name = match.group(1).strip()
                # FIX #11b: Use cleaned context length for distance calculation
                distance_from_end = len(context_cleaned) - match.end()
                
                # FIX #8: Check if this crosses a section header boundary
                # FIX #11b: Use cleaned context for boundary check
                # PHASE 6 FIX: Add semicolon as boundary - semicolons separate different cases in legal citations
                # Example: "See Cayuga...; Oneida...; Hamaatsa..." - each case is separated by semicolon
                text_after_match = context_cleaned[match.end():]
                has_semicolon = ';' in text_after_match[:200]
                has_section_header = bool(re.search(r'\n\s*[A-Z][A-Z\s]{3,}\n', text_after_match[:200]))
                crosses_boundary = has_semicolon or has_section_header
                
                # PHASE 6 DEBUG
                if has_semicolon:
                    logger.error(f"[PHASE6] SEMICOLON detected after '{case_name[:30]}' - applying boundary penalty")
                
                candidates.append({
                    'name': case_name,
                    'distance': distance_from_end,
                    'priority': priority,
                    'pattern_type': pattern_type,
                    'position': match.start(),
                    'crosses_boundary': crosses_boundary
                })
        
        # FIX #8 DEBUG: Log all candidates
        if candidates:
            logger.error(f"[FIX #8] Found {len(candidates)} candidate case names")
            for idx, cand in enumerate(candidates):
                logger.error(f"  Candidate {idx+1}: '{cand['name'][:50]}' (distance: {cand['distance']}, priority: {cand['priority']}, boundary: {cand['crosses_boundary']})")
        
        # FIX #8: Score and sort candidates
        # Lower score = better match
        for cand in candidates:
            score = (
                cand['priority'] * 1000 +      # Pattern priority (0-2) x1000
                cand['distance'] +              # Distance from citation
                (10000 if cand['crosses_boundary'] else 0)  # Heavy penalty for crossing boundaries
            )
            cand['score'] = score
        
        # Sort by score (ascending - lower is better)
        candidates.sort(key=lambda x: x['score'])
        
        # Pick the best candidate
        best_match = None
        if candidates:
            best_match = candidates[0]
            logger.error(f"[FIX #8 SELECTED] Best match: '{best_match['name'][:50]}' (score: {best_match['score']})")
        
        if best_match:
            # Step 5: Extract and clean the best match
            case_name = best_match['name']
            
            # FIX #8 DEBUG: Log the selected case name
            logger.error(f"[FIX #8 EXTRACTED] Raw: '{case_name[:100]}'")
            
            # Step 6: Clean the case name
            case_name = self._clean_case_name(case_name)
            logger.error(f"[FIX #8 CLEANED] After clean: '{case_name[:100]}'")
            
            # Step 7: Remove common citation introducers
            introducer_patterns = [
                r'^(?:See|Citing|Quoting|Following|E\.g\.,)\s+',  # "quoting Kidwell..." → "Kidwell..."
                r'^(?:see|citing|quoting|following|e\.g\.,)\s+',  # lowercase versions
            ]
            
            original_name = case_name
            for intro_pattern in introducer_patterns:
                case_name = re.sub(intro_pattern, '', case_name, flags=re.IGNORECASE)
            
            if case_name != original_name:
                logger.error(f"[FIX #8 INTRODUCER] Removed introducer: '{original_name[:50]}' -> '{case_name[:50]}'")
            
            # Step 8: Validate it looks like a case name
            if not self._looks_like_case_name(case_name, debug):
                logger.error(f"[FIX #8 VALIDATION FAIL] Doesn't look like case name: '{case_name[:100]}'")
                return None  # No valid match found
            
            logger.error(f"[FIX #8 VALIDATION OK] Passed validation!")
            
            # Step 9: Extract year from context after citation
            year_context = text[start_index:start_index + 100]
            year = self._extract_year_from_context(year_context, debug)
            
            logger.error(f"[FIX #8 FINAL] Case name: '{case_name}' ({len(case_name)} chars), Year: {year}")
            
            # Step 10: Apply canonical preferences if available
            preferred_name, preferred_year, canonical_meta = self._apply_canonical_preferences(
                citation,
                case_name,
                year,
            )
            canonical_year_value = extract_year_value(
                canonical_meta.get("canonical_year") or canonical_meta.get("canonical_date")
            )
            
            print(f"[PHASE6-RETURN] Comma anchor returning: '{preferred_name or case_name}'", flush=True)
            return MasterExtractionResult(
                case_name=preferred_name or "N/A",
                year=preferred_year or "N/A",
                confidence=0.9,  # High confidence - proximity-based selection
                method="comma_anchored_proximity",
                context=f"...{potential_case_name[-100:]}",
                debug_info={
                    "comma_position": comma_pos,
                    "case_name_length": len(case_name),
                    "pattern_type": best_match['pattern_type'],
                    "distance": best_match['distance'],
                    "score": best_match['score'],
                    "canonical": canonical_meta
                },
                canonical_name=canonical_meta.get("canonical_name"),
                canonical_year=canonical_year_value,
                extracted_case_name=case_name,
                extracted_year=year,
            )
        
        # FIX #8 DEBUG: Log when no candidates found
        logger.error(f"[FIX #8 NO MATCH] No candidate case names found")
        logger.error(f"[FIX #8 NO MATCH] Context was: '{potential_case_name[-200:]}'")
        
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
        print(f"[PHASE6-VALIDATION-START] Checking: '{text}'", flush=True)
        
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
            print(f"[PHASE6-VALIDATION-FAIL] No v. or special case pattern", flush=True)
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
            print(f"[PHASE6-CONTAMINATION-CHECK] Primary case: '{self.document_primary_case_name}'", flush=True)
            contamination_result = self._is_document_case_contamination(text, True)  # Force debug
            if contamination_result:
                logger.error(f"[CONTAMINATION-FILTER] ✅ REJECTED: Matches document primary case")
                logger.error(f"[CONTAMINATION-FILTER]    Rejected text: '{text[:100]}'")
                print(f"[PHASE6-VALIDATION-FAIL] Contamination: matches primary case '{self.document_primary_case_name}'", flush=True)
                return False
            else:
                logger.error(f"[CONTAMINATION-FILTER] ⚠️  Passed (no match): '{text[:80]}'")
        else:
            logger.error(f"[CONTAMINATION-FILTER] ⚠️  SKIPPED: No document primary case name set!")
        
        logger.error(f"[FIX #69 VALIDATE] SUCCESS: All checks passed!")
        print(f"[PHASE6-VALIDATION-PASS] All checks passed!", flush=True)
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
            # PHASE 6 FIX: Added common organizational/tribal words to prevent false matches
            # (e.g., "Cayuga Indian Nation" vs "Oneida Indian Nation" should not match on "indian nation")
            common_parties = ['united states', 'state', 'county', 'city', 'government', 'people', 
                             'indian', 'nation', 'tribe', 'tribal', 'band', 'company', 'corporation',
                             'incorporated', 'limited', 'association', 'society']
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
            # PHASE 6 FIX: Use same extended list as plaintiff check
            common_parties_def = ['united states', 'state', 'county', 'city', 'government',
                                 'indian', 'nation', 'tribe', 'tribal', 'band']
            
            # FIX: Check for ANY distinctive word from defendant, not just full name
            # "MELONE Railroad" should match defendant "andrew melone" via "melone"
            defendant_words = [word for word in defendant.split() if len(word) > 4]  # Significant words only
            for def_word in defendant_words:
                if def_word not in common_parties_def and def_word in extracted_normalized:
                    if debug:
                        logger.warning(f"[CONTAMINATION-FILTER] Defendant word match:")
                        logger.warning(f"  Extracted: '{extracted_name}'")
                        logger.warning(f"  Matched word: '{def_word}' from defendant '{defendant}'")
                    return True
            
            # Also check full defendant name (original logic)
            if (len(defendant) > 8 and 
                defendant not in common_parties_def and 
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
        # USER FIX 2024-10-21: Increase to 300 chars for vacatur pattern detection
        # 150 chars wasn't enough to reach both "vacated and remanded" AND the case name before it
        # Example: "Oneida v. Madison, 605 F.3d 149...vacated and remanded, 562 U.S. 42" needs ~200+ chars
        # 300 chars should be safe while still avoiding contamination from distant citations
        context_start = max(0, start_index - 300)  # USER FIX: Increased from 150 to 300 for vacatur
        # FIX #38: ONLY look BACKWARD! Context must end at START of citation, not END!
        # Fix #32 used end_index which allowed 15 chars of forward context (citation length),
        # causing extraction of "Spokane County" (after citation) instead of "Lopez Demetrio" (before).
        context_end = start_index  # FIX #38: Context ends at citation START, not END!
        
        # FIX #42: CRITICAL - Log ACTUAL values used to create context
        if debug:
            logger.error(f"🔍 FIX #42: Creating context with:")
            logger.error(f"   start_index = {start_index}")
            logger.error(f"   end_index = {end_index}")
            logger.error(f"   context_start = {context_start} (start_index - 150)")
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
        
        # PHASE 6 FIX: Check for semicolons in context (they separate different cases)
        # If there's a semicolon, only use text AFTER the last semicolon
        # Example: "Cayuga..., 761 F.3d 218; Oneida..., 605 F.3d 149"
        #          We want "Oneida" (after semicolon), not "Cayuga" (before)
        if ';' in context:
            last_semicolon_pos = context.rfind(';')
            print(f"[PHASE6-POSITION] Semicolon found at position {last_semicolon_pos} in context - using text after it", flush=True)
            old_context = context
            context = context[last_semicolon_pos + 1:]  # Only use text AFTER last semicolon
            # Strip leading/trailing whitespace and commas to help patterns match
            context = context.strip().rstrip(',').strip()
            print(f"[PHASE6-POSITION] Old context: '{old_context[-80:]}'", flush=True)
            print(f"[PHASE6-POSITION] New context (trimmed): '{context}'", flush=True)
            
            # IMPORTANT: After trimming, context_start is no longer accurate!
            # The trimmed context ends at start_index and has length len(context)
            # So it starts at: start_index - len(context)
            context_start = start_index - len(context)
            print(f"[PHASE6-POSITION] Adjusted context_start from {max(0, start_index - 300)} to {context_start}", flush=True)
        
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
        
        # USER FIX: Handle "vacated and remanded" pattern
        # When Supreme Court citations follow appellate decisions with "vacated and remanded",
        # extract the case name from IMMEDIATELY BEFORE the vacatur phrase, not from earlier in the paragraph
        vacatur_patterns = [
            r'vacated\s+and\s+remanded',
            r'vacated',
            r'aff\'d',
            r'affirmed',
            r'reversed',
            r'rev\'d',
            r'remanded'
        ]
        
        if debug:
            logger.warning(f"🔍 VACATUR_DEBUG: Checking for vacatur patterns before citation '{citation}'")
            logger.warning(f"🔍 VACATUR_DEBUG: Search context ({len(context)} chars): '{context[-200:]}'")
        
        for vacatur_pattern in vacatur_patterns:
            vacatur_match = re.search(vacatur_pattern, context, re.IGNORECASE)
            if debug:
                logger.warning(f"🔍 VACATUR_DEBUG: Pattern '{vacatur_pattern}' -> {'FOUND' if vacatur_match else 'NOT FOUND'}")
            
            if vacatur_match:
                # USER FIX: Check if there's a semicolon between vacatur and citation
                # Semicolons separate different cases - don't apply vacatur across this boundary
                text_after_vacatur = context[vacatur_match.end():]
                if ';' in text_after_vacatur:
                    if debug:
                        logger.warning(f"🔍 VACATUR_DEBUG: SEMICOLON found between vacatur and citation - SKIPPING vacatur logic")
                    continue  # Skip this vacatur pattern - it's for a different case
                
                # Found vacatur language - now find the case name BEFORE it
                vacatur_pos_in_context = vacatur_match.start()
                text_before_vacatur = context[:vacatur_pos_in_context]
                
                # Look for case name pattern immediately before vacatur
                # Pattern: "Plaintiff Name v. Defendant Name, 123 F.3d 149" (or F.2d, F., etc.)
                # Handles multi-word names like "Oneida Indian Nation v. Madison County"
                case_name_pattern = r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*(?:\s+of\s+[A-Z\.\s]+)*)\s+v\.\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*(?:\s+of\s+[A-Z\.\s]+)*),\s+\d+\s+F\.'
                case_matches = list(re.finditer(case_name_pattern, text_before_vacatur))
                
                if debug:
                    logger.warning(f"🔍 VACATUR_DEBUG: Found {len(case_matches)} case name matches before vacatur")
                    if case_matches:
                        for idx, match in enumerate(case_matches):
                            logger.warning(f"🔍 VACATUR_DEBUG: Match {idx+1}: '{match.group(0)}'")
                    logger.warning(f"🔍 VACATUR_DEBUG: Text before vacatur ({len(text_before_vacatur)} chars): '{text_before_vacatur[-200:]}'")
                
                if case_matches:
                    # Take the LAST match (closest to vacatur phrase)
                    last_match = case_matches[-1]
                    plaintiff = last_match.group(1).strip()
                    defendant = last_match.group(2).strip()
                    
                    # Clean up case names
                    from src.utils.text_normalizer import clean_extracted_case_name
                    plaintiff = clean_extracted_case_name(plaintiff)
                    defendant = clean_extracted_case_name(defendant)
                    vacatur_case_name = f"{plaintiff} v. {defendant}"
                    
                    if debug:
                        logger.warning(f"✅ VACATUR_DETECTED: Found '{vacatur_pattern}' before citation")
                        logger.warning(f"✅ VACATUR_CASE: Extracted '{vacatur_case_name}' from text before vacatur")
                    
                    # Validate the case name
                    if len(plaintiff) >= 3 and len(defendant) >= 3 and len(vacatur_case_name) > 10:
                        # USER FIX: For Supreme Court citations, look for year AFTER the current citation
                        # Example: "562 U.S. 42, 131 S. Ct. 704, 178 L. Ed. 2d 587 (2011)"
                        # The year (2011) is at the END of all parallel citations
                        
                        # Check if this is a Supreme Court citation (U.S., S.Ct., L.Ed.)
                        is_supreme_court = any(x in citation for x in ['U.S.', 'S. Ct.', 'L. Ed.']) if citation else False
                        
                        year = None
                        
                        if is_supreme_court:
                            # For Supreme Court citations, look for year AFTER current citation
                            # This handles parallel citations like "562 U.S. 42, 131 S. Ct. 704 (2011)"
                            after_citation_text = text[start_index:start_index + 200]
                            year = self._extract_year_from_context(after_citation_text, debug)
                            
                            if debug and year:
                                logger.warning(f"🔍 VACATUR_YEAR: Found Supreme Court year '{year}' after citation")
                        
                        # Fallback: Extract from Federal reporter citation
                        if not year:
                            fed_match_end_pos = last_match.end()
                            year_search_text = text_before_vacatur[fed_match_end_pos:fed_match_end_pos + 50]
                            year = self._extract_year_from_context(year_search_text, debug)
                            
                            if debug and year:
                                logger.warning(f"🔍 VACATUR_YEAR: Found year '{year}' from Federal citation")
                        
                        if debug:
                            logger.warning(f"🔍 VACATUR_YEAR: Final extracted year '{year}' for '{vacatur_case_name}'")
                        
                        return MasterExtractionResult(
                            case_name=vacatur_case_name,
                            year=year or "Unknown",
                            confidence=0.98,
                            method="vacatur_pattern",
                            debug_info={"vacatur_pattern": vacatur_pattern, "case_name": vacatur_case_name, "year": year},
                            extracted_case_name=vacatur_case_name,
                            extracted_year=year
                        )
                
                if debug:
                    logger.warning(f"🔍 VACATUR_SKIP: Found '{vacatur_pattern}' but couldn't extract case name before it")
                break  # Only check first matching vacatur pattern
        
        # Try all patterns on the focused context
        print(f"[PHASE6-PATTERN] Starting pattern matching on context: '{context[:60]}'", flush=True)
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
                print(f"[PHASE6-PATTERN] Pattern {i} MATCHED! Extracting...", flush=True)
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
                
                # USER FIX 2024-10-16: Extract year from AFTER citation first, fallback to context
                # This prevents picking up years from previous citations
                year_context_after = text[end_index:end_index + 100]
                year = self._extract_year_from_context(year_context_after, debug)
                if not year:
                    # Fallback to context before citation
                    year = self._extract_year_from_context(context, debug)
                
                if case_name and len(case_name.strip()) > 3:
                    cleaned_name = self._clean_case_name(case_name)
                    if debug:
                        logger.warning(f"   Cleaned case name: '{cleaned_name}'")
                        # FIX #40B: Track if "Spokane" appears at this stage
                        if "Spokane" in cleaned_name:
                            logger.error(f"🚨 BUG: 'Spokane' in CLEANED case_name!")
                    
                    # USER FIX 2024-10-16: Add proximity validation
                    # Reject if extracted name is >100 chars away from citation
                    match_pos_in_original = context_start + match.start()
                    distance_from_citation = start_index - match_pos_in_original
                    
                    # PHASE 6 DEBUG
                    print(f"[PHASE6-PROXIMITY] match.start()={match.start()}, context_start={context_start}, match_pos={match_pos_in_original}, start_index={start_index}, distance={distance_from_citation}", flush=True)
                    
                    if distance_from_citation > 100:
                        print(f"[PHASE6-REJECT-PROXIMITY] Rejected: distance {distance_from_citation} > 100", flush=True)
                        if debug:
                            logger.warning(f"   ❌ REJECTED: Too far from citation ({distance_from_citation} chars away)")
                        continue  # Try next pattern
                    
                    # P3 FIX: CRITICAL - Validate to filter contamination BEFORE accepting extraction
                    if not self._looks_like_case_name(cleaned_name, debug):
                        print(f"[PHASE6-REJECT-VALIDATION] Rejected: name validation failed for '{cleaned_name}'", flush=True)
                        if debug:
                            logger.warning(f"   ❌ REJECTED by validation (contamination or invalid): '{cleaned_name[:100]}'")
                        continue  # Try next pattern
                    
                    print(f"[PHASE6-ACCEPT] Passed all validation! Returning: '{cleaned_name}'", flush=True)
                    
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
        
        print(f"[PHASE6-PATTERN] NO patterns matched context: '{context[:60]}' - returning None (will fallback)", flush=True)
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
                
                # USER FIX 2024-10-16: Extract year from AFTER citation first
                year_context_after = text[citation_pos:citation_pos + 100] if citation_pos >= 0 else ""
                year = self._extract_year_from_context(year_context_after, debug)
                if not year:
                    # Fallback to context before citation
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
    
    def _clean_case_name(self, case_name: str, context: str = None) -> str:
        """
        Clean and normalize case name using best practices from all implementations.
        
        Args:
            case_name: The extracted case name to clean
            context: Optional broader text context for finding full corporate names
        """
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
        # CRITICAL: Remove signal words first, before other cleaning
        contamination_prefixes = [
            # Signal words FIRST - these introduce citations but aren't part of the case name
            r'^(?:See|see|See also|see also|Citing|citing|Compare|compare|But see|but see|Cf\.|cf\.|quoting|Quoting|accord|Accord)\s+',
            r'^(?:The case of|As stated in|Following)\s+',
            
            # Phase 4 USER FIX: Additional contamination phrases
            r'^(?:The parties are|The parties were)\s+',
            r'^(?:The court in|The court held|The court decided|The defendant|The plaintiff)\s+',
            r'^(?:If in|As in)\s+',
            
            # Phase 4 USER FIX v2: Remove connecting phrases after signal words are removed
            r'^(?:this|that|such|the)\s+(?:precedent|case|decision|holding|rule|standard|doctrine),?\s+in\s+',
            r'^(?:precedent|case|decision|holding|rule|standard|doctrine),?\s+in\s+',
            
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
        
        # FIX #9: Remove case/docket numbers that appear due to page breaks
        # CRITICAL: Handle spaces within case numbers from line breaks: "No. 103430 -0 15"
        
        # Pattern 1: Before "v." - Standard case numbers
        cleaned = re.sub(r'\s+No\.\s+[\d\-]+\s+\d+(?=\s+v\.)', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s+No\.\s+[\d\-]+(?=\s+v\.)', '', cleaned, flags=re.IGNORECASE)
        
        # Pattern 1b: Complex case numbers with hyphens (continuous or with spaces)
        # "No. 103430-0-15" OR "No. 103430 -0 15" → remove before "v."
        cleaned = re.sub(r'\s+No\.\s+[\d\-\s]+\-[\d\-\s]+(?=\s+v\.)', '', cleaned, flags=re.IGNORECASE)
        
        # Pattern 1c: Case numbers with spaces from line breaks: "No. 103430 -0 15"
        # This specifically targets the problematic pattern with internal spaces
        cleaned = re.sub(r'\s+No\.\s+\d+\s+-\d+\s+\d+(?=\s+v\.)', '', cleaned, flags=re.IGNORECASE)
        
        # Pattern 2: After "v." - Page number contamination
        # "Inc. v. Band 6 No. 103430-0 Tribe" → "Inc. v. Band Tribe"
        cleaned = re.sub(r'\s+\d+\s+No\.\s+[\d\-]+\s+', ' ', cleaned, flags=re.IGNORECASE)
        
        # Pattern 2b: Complex case numbers after "v." (with or without spaces)
        cleaned = re.sub(r'\s+No\.\s+[\d\-\s]+\-[\d\-\s]+\s+', ' ', cleaned, flags=re.IGNORECASE)
        
        # Pattern 3: Standalone page numbers between words (page breaks)
        # "Band 6 Potawatomi" → "Band Potawatomi" (only if surrounded by capitals)
        cleaned = re.sub(r'([A-Z][a-z]+)\s+\d{1,2}\s+([A-Z][a-z]+)', r'\1 \2', cleaned)
        
        # USER FIX 2024-10-21: Strip whitespace before applying patterns
        # Ensures ^ anchor works correctly even if there's leading whitespace
        cleaned = cleaned.strip()
        
        for prefix in contamination_prefixes:
            before = cleaned
            cleaned = re.sub(prefix, '', cleaned, flags=re.IGNORECASE).strip()
            if before != cleaned:
                logger.error(f"[CLEAN_DEBUG] Removed prefix: '{before}' → '{cleaned}'")
        
        # NEW: Remove descriptive legal phrases and status words that contaminate case names
        # Strategy: If we detect contamination words, try to extract just the case name portion
        
        # First, remove common procedural introducers at the start
        # NOTE: Signal words are now handled in contamination_prefixes above
        procedural_prefixes = [
            r'^(?:under|applying|following|relying on)\s+',
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
        
        # USER FIX 2024-10-16: Remove citation patterns that got included
        # Example: "Inc. v. Stillaguamish Tribe of Indians, 31 Wn. App. 2d 343, 359-62"
        # Should be: "Inc. v. Stillaguamish Tribe of Indians"
        
        # USER FIX 2024-10-16 PM: Remove state reporter citations like "2017-NM-007"
        # Pattern: ", YYYY-STATE-NUMBER" where STATE is 2-letter code
        cleaned = re.sub(r',\s*\d{4}-[A-Z]{2}-\d+', '', cleaned)
        
        # Remove anything that looks like: ", [volume] [reporter] [page]"
        cleaned = re.sub(r',\s*\d+\s+[A-Z][a-z]*\.?\s*(?:App\.)?\s*\d*d?\s*\d+.*$', '', cleaned)
        # Also remove pin cites like ", 359-62"
        cleaned = re.sub(r',\s*\d+-\d+.*$', '', cleaned)
        # Remove standalone citations at end: "245 F.3d 889" or "31 Wn. App. 2d 343"
        cleaned = re.sub(r'\s+\d+\s+[A-Z][a-z]*\.?\s*(?:App\.)?\s*\d*d?\s*\d+.*$', '', cleaned)
        
        # Remove trailing punctuation except periods in abbreviations
        cleaned = re.sub(r'[,;:]+$', '', cleaned)
        
        # USER FIX 2024-10-16: Fix corporate name truncation
        # If name starts with corporate suffix (Inc., LLC, etc.), it's truncated
        # Example: "Inc. v. Stillaguamish" should be "Flying T Ranch, Inc. v. Stillaguamish"
        corporate_suffixes = [r'^Inc\.?\s+v\.', r'^LLC\.?\s+v\.', r'^Corp\.?\s+v\.', 
                             r'^Ltd\.?\s+v\.', r'^Co\.?\s+v\.', r'^L\.P\.?\s+v\.']
        
        is_truncated = any(re.match(pattern, cleaned, re.IGNORECASE) for pattern in corporate_suffixes)
        
        if is_truncated:
            # USER FIX 2024-10-16 PM: Search context first, then case_name
            # Try to find the full corporate name in context (if provided), then original case_name
            search_text = context if context else case_name
            # Look for pattern: [Company Name], Inc. v. [Defendant]
            corp_name_match = re.search(r'([A-Z][A-Za-z\s&\'\.\-]+(?:,\s*)?(?:Inc|LLC|Corp|Ltd|Co|L\.P\.)\.?)\s+v\.', 
                                       search_text, re.IGNORECASE)
            if corp_name_match:
                # Found the full corporate name, use it
                full_corp_name = corp_name_match.group(1).strip()
                # Replace truncated start with full name
                cleaned = re.sub(r'^(?:Inc|LLC|Corp|Ltd|Co|L\.P\.)\.?\s+', 
                               full_corp_name + ' ', cleaned, flags=re.IGNORECASE)
        
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
            logger.error(f"[CLEAN_DEBUG] REJECTED as header: '{cleaned}'")
            return "N/A"
        
        logger.error(f"[CLEAN_DEBUG] FINAL cleaned: '{cleaned}'")
        return cleaned.strip()
    
    def _is_document_header(self, text: str) -> bool:
        """Check if text looks like a document header rather than a case name."""
        if not text:
            return True
        
        # Document header patterns
        # CRITICAL: These should NOT match valid case names (containing " v. ")
        header_patterns = [
            r'^IN THE\s+(?!.*\s+v\.\s+)',  # "IN THE..." but not "IN THE MATTER OF X v. Y"
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
            r'^STATE OF\s+(?!.*\s+v\.\s+)',  # "STATE OF..." but not case name
            # CRITICAL FIX: Don't reject "United States v. X" as header!
            # Only reject standalone "UNITED STATES" or "UNITED STATES" followed by punctuation
            r'^UNITED STATES\s*[,;:\.]?\s*$',  # Standalone only
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
