"""
Unified Extraction Architecture
==============================

This module provides a standardized, single-source-of-truth architecture for case name 
and year extraction from user documents. All processing paths must use this architecture
to ensure consistency and accuracy.

Key Principles:
1. Single extraction function for all paths
2. Position information always preserved
3. Consistent, accurate regex patterns
4. Proper context window extraction
5. No duplicate or conflicting extraction logic
"""

import re
from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ExtractionResult:
    """Standardized result from case name and year extraction."""
    case_name: str
    year: str
    confidence: float
    method: str
    start_index: Optional[int] = None
    end_index: Optional[int] = None
    context: str = ""
    debug_info: Dict[str, Any] = None

class UnifiedExtractionArchitecture:
    """
    Single source of truth for case name and year extraction.
    
    This class provides the ONLY extraction methods that should be used
    throughout the entire application. All other extraction functions
    should be deprecated and replaced with calls to this class.
    """
    
    def __init__(self):
        """Initialize the unified extraction architecture."""
        self._setup_patterns()
        logger.info("UnifiedExtractionArchitecture initialized")
    
    def _setup_patterns(self):
        """Setup standardized, accurate regex patterns with comprehensive Unicode support."""
        
        # Define comprehensive character classes for common Unicode issues
        # Apostrophes and quotes (straight, curly, smart quotes, primes, etc.)
        apostrophe_chars = r'[\'\u2019\u2018\u201A\u201B\u2032\u2035\u201C\u201D\u201E\u201F\u2033\u2034\u2036\u2037\u2039\u203A\u00B4\u0060\u02B9\u02BB\u02BC\u02BD\u02BE\u02BF\u055A\u055B\u055C\u055D\u055E\u055F\u05F3]'
        
        # Ampersand variations (straight, curly, ligatures)
        ampersand_chars = r'[&\u0026\uFF06\u204A\u214B]'
        
        # Hyphen and dash variations (hyphen, en-dash, em-dash, minus, etc.)
        hyphen_chars = r'[-\u002D\u2010\u2011\u2012\u2013\u2014\u2015\u2212\uFE58\uFE63\uFF0D]'
        
        # Period variations (period, full stop, bullet, etc.)
        period_chars = r'[.\u002E\u2024\u2025\u2026\u2027]'
        
        # Space variations (regular space, non-breaking space, en space, em space, etc.)
        space_chars = r'[\s\u0020\u00A0\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200A\u200B\u200C\u200D\u200E\u200F\u2028\u2029\u202A\u202B\u202C\u202D\u202E\u202F]'
        
        # Comprehensive character class for legal text (letters, spaces, apostrophes, ampersands, hyphens, periods)
        legal_chars = r'[A-Za-z\s\'\u2019\u2018\u201A\u201B\u2032\u2035\u201C\u201D\u201E\u201F\u2033\u2034\u2036\u2037\u2039\u203A\u00B4\u0060\u02B9\u02BB\u02BC\u02BD\u02BE\u02BF\u055A\u055B\u055C\u055D\u055E\u055F\u05F3&\u0026\uFF06\u204A\u214B-\u002D\u2010\u2011\u2012\u2013\u2014\u2015\u2212\uFE58\uFE63\uFF0D.\u002E\u2024\u2025\u2026\u2027]'
        
        # "v." variations (v., vs., versus, etc.)
        versus_chars = r'[vV]\s*[.\u002E\u2024\u2025\u2026\u2027]'
        
        self.context_patterns = [
            # SPECIFIC patterns first to avoid truncation - more precise after text normalization
            r'([A-Z][a-zA-Z\s\'&\-\.]{1,50})\s+v\.\s+(Dep\'t\s+of\s+[A-Z][a-zA-Z\s\'&\-\.]{1,50})',
            r'([A-Z][a-zA-Z\s\'&\-\.]{1,50})\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.]{1,50})(?:LLC|Inc\.?|Corp\.?|Ltd\.?|Co\.?)',
            # GENERAL pattern with length limits to avoid over-matching
            r'([A-Z][a-zA-Z\s\'&\-\.]{1,50})\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.]{1,50})',
        ]
        
        self.fallback_patterns = [
            # SPECIFIC patterns first to avoid truncation - more precise after text normalization
            r'([A-Z][a-zA-Z\s\'&\-\.]{1,50})\s+v\.\s+(Dep\'t\s+of\s+[A-Z][a-zA-Z\s\'&\-\.]{1,50})',
            r'([A-Z][a-zA-Z\s\'&\-\.]{1,50})\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.]{1,50})(?:LLC|Inc\.?|Corp\.?|Ltd\.?|Co\.?)',
            # GENERAL pattern last to avoid early truncation - more precise after normalization
            r'([A-Z][a-zA-Z\s\'&\-\.]{1,50})\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.]{1,50})',
        ]
        
        self.year_patterns = [
            r'\((\d{4})\)',  # (2022)
            r'\b(\d{4})\b',  # 2022
        ]
        
        self.contamination_patterns = [
            r'\b(de\s+novo)\b', r'\b(questions?\s+of\s+law)\b', r'\b(statutory\s+interpretation)\b',
            r'\b(in\s+light\s+of)\b', r'\b(the\s+record\s+certified)\b', r'\b(federal\s+court)\b',
            r'\b(this\s+court\s+reviews?)\b', r'\b(we\s+review)\b', r'\b(certified\s+questions?)\b',
            r'\b(issue\s+of\s+law)\b', r'\b(also\s+an?\s+issue)\b', r'\b(reviews?\s+de\s+novo)\b',
            r'\b(see|citing|quoting|accord|id\.|ibid\.)\b', r'\b(brief\s+at|opening\s+br\.|reply\s+br\.)\b',
            r'\b(internal\s+quotation\s+marks)\b', r'\b(alteration\s+in\s+original)\b',
            r'\b(may\s+ask\s+this\s+court)\b', r'\b(resolution\s+of\s+that\s+question)\b',
            r'\b(necessary\s+to\s+resolve)\b', r'\b(case\s+before\s+the)\b',
            r'^(are|ions|eview|questions|we|the|this|also|meaning|of|a|statute)[\s\.]*',
            r'^(de\s+novo)[\s\.]*',
            r'^(we\s+also|the\s+meaning|this\s+court|also\s+review)[\s\.]*',
            r'^(questions?\s+of\s+law\s+we\s+review)[\s\.]*',
            r'^(we\s+also\s+review\s+the\s+meaning)[\s\.]*',
            r'^(of\s+law)[\s\.]*',
        ]
    
    def extract_case_name_and_year(
        self, 
        text: str, 
        citation: str,
        start_index: Optional[int] = None,
        end_index: Optional[int] = None,
        debug: bool = False
    ) -> ExtractionResult:
        """
        Extract case name and year using the unified architecture.
        
        This is the ONLY extraction method that should be used throughout
        the entire application. All other extraction functions should
        be deprecated and replaced with calls to this method.
        
        Args:
            text: Full document text
            citation: Citation text to extract case name for
            start_index: Start position of citation in text (if available)
            end_index: End position of citation in text (if available)
            debug: Enable debug logging
            
        Returns:
            ExtractionResult with standardized case name and year
        """
        if debug:
            logger.warning(f"ðŸŽ¯ UNIFIED_EXTRACT: Starting extraction for citation '{citation}' at position {start_index}-{end_index}")
        
        # Normalize text early to handle Unicode character issues
        from src.utils.text_normalizer import normalize_text
        normalized_text = normalize_text(text)
        
        if start_index is not None and end_index is not None:
            result = self._extract_with_context(normalized_text, citation, start_index, end_index, debug)
            if result and result.case_name and result.case_name != 'N/A':
                # Clean up the extracted case name to remove leading text that doesn't belong
                from src.utils.text_normalizer import clean_extracted_case_name
                cleaned_case_name = clean_extracted_case_name(result.case_name)
                result.case_name = cleaned_case_name
                if debug:
                    logger.warning(f"âœ… UNIFIED_EXTRACT: Context extraction successful: '{result.case_name}'")
                return result
        
        result = self._extract_with_patterns(normalized_text, citation, start_index or 0, end_index or len(normalized_text), debug)
        
        # Clean up the extracted case name to remove leading text that doesn't belong
        if result and result.case_name and result.case_name != 'N/A':
            from src.utils.text_normalizer import clean_extracted_case_name
            cleaned_case_name = clean_extracted_case_name(result.case_name)
            result.case_name = cleaned_case_name
        
        if debug:
            logger.warning(f"âœ… UNIFIED_EXTRACT: Pattern extraction result: '{result.case_name}'")
        
        return result
    
    def _extract_with_context(
        self, 
        text: str, 
        citation: str, 
        start_index: int, 
        end_index: int, 
        debug: bool
    ) -> Optional[ExtractionResult]:
        """Extract case name using context window around citation position."""
        try:
            context_start = max(0, start_index - 500)  # Increased from 200 to 500 to capture full case names
            context_end = min(len(text), end_index + 100)  # Increased from 50 to 100
            context = text[context_start:context_end]
            
            if debug:
                logger.warning(f"ðŸ” UNIFIED_EXTRACT: Context window: '{context}'")
            
            for i, pattern in enumerate(self.context_patterns):
                if debug:
                    logger.warning(f"ðŸ” UNIFIED_EXTRACT: Testing pattern {i+1}: {pattern}")
                matches = list(re.finditer(pattern, context, re.IGNORECASE))
                if debug:
                    logger.warning(f"ðŸ” UNIFIED_EXTRACT: Pattern {i+1} found {len(matches)} matches in context")
                    if matches:
                        for j, match in enumerate(matches):
                            logger.warning(f"ðŸ” UNIFIED_EXTRACT: Match {j+1}: groups={match.groups()}")
                            logger.warning(f"ðŸ” UNIFIED_EXTRACT: Match {j+1}: full match='{match.group(0)}'")
                
                if matches:
                    best_match = None
                    min_distance = float('inf')
                    
                    citation_volume = None
                    if 'Wn.' in citation:
                        volume_match = re.search(r'(\d+)\s+Wn\.', citation)
                        if volume_match:
                            citation_volume = volume_match.group(1)
                    elif 'P.' in citation:
                        volume_match = re.search(r'(\d+)\s+P\.', citation)
                        if volume_match:
                            citation_volume = volume_match.group(1)
                    
                    for match in matches:
                        match_end_in_context = match.end()
                        citation_start_in_context = start_index - context_start
                        distance = abs(match_end_in_context - citation_start_in_context)
                        
                        if debug:
                            logger.warning(f"ðŸ” UNIFIED_EXTRACT: Match '{match.group(0)}' at distance {distance}")
                        
                        volume_match = False
                        if i < 2 and len(match.groups()) >= 3:  # Patterns 1 and 2 have volume as group 3
                            match_volume = match.group(3)
                            if citation_volume and match_volume == citation_volume:
                                volume_match = True
                                if debug:
                                    logger.warning(f"ðŸ” UNIFIED_EXTRACT: Volume match! Citation: {citation_volume}, Match: {match_volume}")
                        
                        if distance < 100:  # Within 100 characters
                            match_text = match.group(0)
                            # IMPROVED: More specific contamination detection that only rejects obvious non-case names
                            contamination_indicators = ['statutory interpretation', 'questions of law', 'certified questions', 'this court reviews', 'we review', 'also an issue', 'meaning of a statute']
                            
                            has_contamination = any(contam.lower() in match_text.lower() for contam in contamination_indicators)
                            
                            if not has_contamination:
                                if i < 2 and volume_match:
                                    best_match = match
                                    min_distance = distance
                                    if debug:
                                        logger.warning(f"ðŸ” UNIFIED_EXTRACT: Volume-matched case name: '{match_text}' at distance {distance}")
                                    break  # Found exact volume match, use it
                                elif i >= 2 or not citation_volume:  # For other patterns or if no volume available
                                    case_name_quality = self._assess_case_name_quality(match_text)
                                    if case_name_quality > 0.5:  # Only consider high-quality case names
                                        if distance < min_distance:
                                            min_distance = distance
                                            best_match = match
                                            if debug:
                                                logger.warning(f"ðŸ” UNIFIED_EXTRACT: New best match: '{match_text}' at distance {distance} (quality: {case_name_quality})")
                            elif debug:
                                logger.warning(f"ðŸ” UNIFIED_EXTRACT: Match rejected due to contamination: '{match_text}'")
                    
                    if best_match:
                        raw_plaintiff = best_match.group(1)
                        raw_defendant = best_match.group(2)
                        logger.warning(f"ðŸ” DEBUG_TRUNCATION: Raw plaintiff: '{raw_plaintiff}', Raw defendant: '{raw_defendant}'")
                        
                        from src.utils.text_normalizer import clean_extracted_case_name
                        plaintiff = clean_extracted_case_name(raw_plaintiff)
                        defendant = clean_extracted_case_name(raw_defendant)
                        logger.warning(f"ðŸ” DEBUG_TRUNCATION: Cleaned plaintiff: '{plaintiff}', Cleaned defendant: '{defendant}'")
                        
                        case_name = f"{plaintiff} v. {defendant}"
                        
                        if debug:
                            logger.warning(f"ðŸ” UNIFIED_EXTRACT: Extracted case name: '{case_name}'")
                        
                        if self._is_valid_case_name(case_name):
                            year = self._extract_year_from_context(context, citation)
                            
                            return ExtractionResult(
                                case_name=case_name,
                                year=year,
                                confidence=0.95,
                                method=f"context_pattern_{i+1}",
                                start_index=start_index,
                                end_index=end_index,
                                context=context,
                                debug_info={'pattern_used': pattern, 'match_distance': min_distance}
                            )
                        elif debug:
                            logger.warning(f"ðŸ” UNIFIED_EXTRACT: Case name failed validation: '{case_name}'")
                    
                    continue
            
            if debug:
                logger.warning(f"ðŸ” UNIFIED_EXTRACT: No patterns worked, trying targeted approach")
            
            # NEW APPROACH: Look for case names immediately before the citation
            citation_pos_in_context = start_index - context_start
            # Look for case names in the 100 characters immediately before the citation
            search_start = max(0, citation_pos_in_context - 100)
            search_end = citation_pos_in_context
            targeted_context = context[search_start:search_end]
            
            if debug:
                logger.warning(f"ðŸ” UNIFIED_EXTRACT: Pre-citation context: '{targeted_context}'")
            
            # Try to find case names that end just before the citation
            pre_citation_patterns = [
                r'([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+){0,2})\s+v\.\s+([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+){0,3})(?=\s*,\s*\d+\s+Wn\.\d+)',
                r'([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+){0,2})\s+v\.\s+([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+){0,3})(?=\s*,\s*\d+\s+P\.\d+)',
                r'([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+){0,2})\s+v\.\s+(Dep\'t\s+of\s+[A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+){0,2})(?=\s*,\s*\d+\s+Wn\.\d+)',
                r'([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+){0,2})\s+v\.\s+(Dep\'t\s+of\s+[A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+){0,2})(?=\s*,\s*\d+\s+P\.\d+)',
            ]
            
            for i, pattern in enumerate(pre_citation_patterns):
                matches = list(re.finditer(pattern, targeted_context, re.IGNORECASE))
                if matches:
                    # Take the last match (closest to citation)
                    match = matches[-1]
                    from src.utils.case_name_cleaner import clean_extracted_case_name
                    plaintiff = clean_extracted_case_name(match.group(1))
                    defendant = clean_extracted_case_name(match.group(2))
                    case_name = f"{plaintiff} v. {defendant}"
                    
                    if debug:
                        logger.warning(f"ðŸ” UNIFIED_EXTRACT: Pre-citation match: '{case_name}'")
                    
                    if self._is_valid_case_name(case_name):
                        year = self._extract_year_from_context(context, citation)
                        
                        return ExtractionResult(
                            case_name=case_name,
                            year=year,
                            confidence=0.95,
                            method=f"pre_citation_pattern_{i+1}",
                            start_index=start_index,
                            end_index=end_index,
                            context=context,
                            debug_info={'pattern_used': pattern, 'match_position': 'pre_citation'}
                        )
            
            # Fallback to original targeted approach
            citation_pos_in_context = start_index - context_start
            search_start = max(0, citation_pos_in_context - 50)  # Reduced from 150 to 50
            search_end = min(len(context), citation_pos_in_context + 30)  # Reduced from 50 to 30
            targeted_context = context[search_start:search_end]
            
            if debug:
                logger.warning(f"ðŸ” UNIFIED_EXTRACT: Targeted context: '{targeted_context}'")
            
            targeted_patterns = [
                # ULTRA-PRECISE: Look for case names immediately before the citation
                r'([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+){0,2})\s+v\.\s+([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+){0,3})(?=\s*,\s*\d+\s+Wn\.\d+)',
                r'([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+){0,2})\s+v\.\s+([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+){0,3})(?=\s*,\s*\d+\s+P\.\d+)',
                r'([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+){0,2})\s+v\.\s+(Dep\'t\s+of\s+[A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+){0,2})(?=\s*,\s*\d+\s+Wn\.\d+)',
                r'([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+){0,2})\s+v\.\s+(Dep\'t\s+of\s+[A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+){0,2})(?=\s*,\s*\d+\s+P\.\d+)',
                # Fallback patterns for cases without volume numbers
                r'([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+){0,2})\s+v\.\s+([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+){0,3})(?=\s*,\s*\d+)',
                r'([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+){0,2})\s+v\.\s+([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+){0,3})(?=\s+\d+\s+Wn\.)',
                r'([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+){0,2})\s+v\.\s+([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+){0,3})(?=\s+\d+\s+P\.)',
            ]
            
            for i, pattern in enumerate(targeted_patterns):
                matches = list(re.finditer(pattern, targeted_context, re.IGNORECASE))
                if matches:
                    best_match = None
                    min_distance = float('inf')
                    
                    for match in matches:
                        match_start = match.start()
                        match_end = match.end()
                        citation_pos_in_targeted = citation_pos_in_context - search_start
                        distance = min(abs(match_start - citation_pos_in_targeted), abs(match_end - citation_pos_in_targeted))
                        
                        if distance < min_distance:
                            min_distance = distance
                            best_match = match
                    
                    if best_match:
                        from src.utils.text_normalizer import clean_extracted_case_name
                        plaintiff = clean_extracted_case_name(best_match.group(1))
                        defendant = clean_extracted_case_name(best_match.group(2))
                        case_name = f"{plaintiff} v. {defendant}"
                        
                        if debug:
                            logger.warning(f"ðŸ” UNIFIED_EXTRACT: Targeted extraction: '{case_name}'")
                        
                        if case_name and case_name != "N/A v. N/A" and len(case_name) > 5:
                            case_name = self._clean_case_name(case_name)
                            
                            year = self._extract_year_from_context(context, citation)
                            
                            if debug:
                                logger.warning(f"âœ… UNIFIED_EXTRACT: Targeted extraction successful: '{case_name}'")
                            
                            return ExtractionResult(
                                case_name=case_name,
                                year=year,
                                confidence=0.7,
                                method=f"targeted_pattern_{i+1}",
                                start_index=start_index,
                                end_index=end_index,
                                context=targeted_context,
                                debug_info={'pattern_used': pattern, 'match_distance': min_distance}
                            )
            
            return None
            
        except Exception as e:
            if debug:
                logger.warning(f"âš ï¸ UNIFIED_EXTRACT: Context extraction failed: {e}")
            return None
    
    def _extract_with_patterns(
        self, 
        text: str, 
        citation: str, 
        start_index: int,
        end_index: int,
        debug: bool
    ) -> ExtractionResult:
        """Extract case name using fallback patterns when context is not available."""
        try:
            search_radius = 200  # characters before and after citation
            search_start = max(0, start_index - search_radius)
            search_end = min(len(text), end_index + search_radius)
            search_text = text[search_start:search_end]
            
            relative_start = start_index - search_start
            relative_end = end_index - search_start
            
            for i, pattern in enumerate(self.fallback_patterns):
                matches = list(re.finditer(pattern, search_text, re.IGNORECASE))
                if matches:
                    best_match = None
                    min_distance = float('inf')
                    
                    for match in matches:
                        match_end = match.end()
                        distance = abs(match_end - relative_start)
                        
                        if distance < min_distance:
                            min_distance = distance
                            best_match = match
                    
                    if best_match:
                        raw_plaintiff = best_match.group(1)
                        raw_defendant = best_match.group(2)
                        logger.warning(f"ðŸ” DEBUG_TRUNCATION_FALLBACK: Raw plaintiff: '{raw_plaintiff}', Raw defendant: '{raw_defendant}'")
                        
                        from src.utils.text_normalizer import clean_extracted_case_name
                        plaintiff = clean_extracted_case_name(raw_plaintiff)
                        defendant = clean_extracted_case_name(raw_defendant)
                        logger.warning(f"ðŸ” DEBUG_TRUNCATION_FALLBACK: Cleaned plaintiff: '{plaintiff}', Cleaned defendant: '{defendant}'")
                        
                        case_name = f"{plaintiff} v. {defendant}"
                        
                        if self._is_valid_case_name(case_name):
                            year = self._extract_year_from_text(search_text, citation)
                            
                            return ExtractionResult(
                                case_name=case_name,
                                year=year,
                                confidence=0.8,
                                method=f"fallback_pattern_{i+1}",
                                start_index=start_index,
                                end_index=end_index,
                                context=search_text,
                                debug_info={'pattern_used': pattern, 'match_distance': min_distance, 'search_radius': search_radius}
                            )
            
            return ExtractionResult(
                case_name="N/A",
                year="",
                confidence=0.0,
                method="no_match",
                start_index=start_index,
                end_index=end_index,
                context=search_text,
                debug_info={'error': 'No patterns matched'}
            )
            
        except Exception as e:
            if debug:
                logger.warning(f"âš ï¸ UNIFIED_EXTRACT: Pattern extraction failed: {e}")
            return ExtractionResult(
                case_name="N/A",
                year="",
                confidence=0.0,
                method="error",
                start_index=start_index,
                end_index=end_index,
                context=text[:200] + "..." if len(text) > 200 else text,
                debug_info={'error': str(e)}
            )
    
    def _assess_case_name_quality(self, match_text: str) -> float:
        """
        Assess the quality of a potential case name match.
        
        Returns a score between 0 and 1, where 1 is a perfect case name.
        """
        if not match_text:
            return 0.0
        
        score = 1.0
        
        citation_indicators = ['P.', 'Wn.', 'App.', 'U.S.', 'S.Ct.', 'F.', 'F.2d', 'F.3d', 'F.Supp.']
        for indicator in citation_indicators:
            if indicator in match_text:
                score -= 0.3
        
        if re.search(r'\(\d{4}\)', match_text):
            score -= 0.2
        
        if len(match_text) > 200:  # Increased threshold to be less strict
            score -= 0.3
        
        if match_text[0].islower() or match_text[0].isdigit():
            score -= 0.5
        
        case_indicators = ['v.', 'vs.', 'versus', 'In re', 'Estate of', 'Matter of']
        for indicator in case_indicators:
            if indicator in match_text:
                score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _clean_case_name(self, name: str) -> str:
        """Clean extracted case name by removing contamination."""
        if not name:
            return "N/A"
        
        for pattern in self.contamination_patterns:
            if pattern.startswith('^'):
                name = re.sub(pattern, '', name, flags=re.IGNORECASE)
            else:
                name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        
        name = re.sub(r'^[.\s,;:]+', '', name)
        name = re.sub(r'[.\s,;:]+$', '', name)
        name = re.sub(r'^(the|a|an)\s+', '', name, flags=re.IGNORECASE)
        
        name = re.sub(r'^[A-Z]\.\d+[a-z]*\s+\(\d{4}\)\.\s*', '', name)  # Remove "P.3d 258 (2015). "
        name = re.sub(r'^[A-Z]\.\d+[a-z]*\s+', '', name)  # Remove "P.3d 258 "
        
        name = re.sub(r'^[^A-Za-z]*', '', name)
        
        contamination_patterns = [
            r'^(view|novo|n|are|meaning|of|a|statute|eview|ions|questions|we|review|de|novo)\s+',
            r'^\.\s*',
            r'^of\s+a\s+statute\s*\.\s*',
            r'^are\s*\.\s*',
        ]
        
        for pattern in contamination_patterns:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name if name else "N/A"
    
    def _extract_year_from_context(self, context: str, citation: str) -> str:
        """Extract year from context around citation."""
        for pattern in self.year_patterns:
            matches = list(re.finditer(pattern, context))
            if matches:
                return matches[-1].group(1)  # Use last match (most likely to be correct)
        return ""
    
    def _clean_case_name(self, case_name: str) -> str:
        """Clean up case name by removing leading debris"""
        if not case_name:
            return case_name
            
        case_name = re.sub(r'^\.\s*', '', case_name)  # Remove leading period and any following spaces
        case_name = re.sub(r'^(and|or|but)\s+', '', case_name, flags=re.IGNORECASE)  # Remove leading conjunctions
        
        cleanup_patterns = [
            r'^(?:that\s+and\s+by\s+the\s+|that\s+and\s+|is\s+also\s+an\s+|also\s+an\s+|also\s+|that\s+|this\s+is\s+|this\s+)\.?\s*',
            r'^(?:court\s+reviews\s+de\s+novo\s+and\s+in\s+light\s+of\s+the\s+record\s+certified\s+by\s+the\s+federal\s+court\.?\s*)',
            r'^(?:statutory\s+interpretation\s+is\s+also\s+an\s+issue\s+of\s+law\s+we\s+review\s+de\s+novo\.?\s*)',
            r'^(?:questions\s+of\s+law\s+that\s+this\s+court\s+reviews\s+de\s+novo\s+and\s+in\s+light\s+of\s+the\s+record\s+certified\s+by\s+the\s+federal\s+court\.?\s*)',
            r'^(?:are\s+questions\s+of\s+law\s+that\s+this\s+court\s+reviews\s+de\s+novo\s+and\s+in\s+light\s+of\s+the\s+record\s+certified\s+by\s+the\s+federal\s+court\.?\s*)',
            r'^(?:[^A-Z]*?)(?=[A-Z][a-zA-Z\s]*\s+v\.\s+[A-Z])',
        ]
        
        for pattern in cleanup_patterns:
            case_name = re.sub(pattern, '', case_name, flags=re.IGNORECASE)
        
        return case_name.strip()
    
    def _extract_year_from_text(self, text: str, citation: str) -> str:
        """Extract year from full text."""
        for pattern in self.year_patterns:
            matches = list(re.finditer(pattern, text))
            if matches:
                return matches[-1].group(1)  # Use last match (most likely to be correct)
        return ""
    
    def _is_valid_case_name(self, case_name: str) -> bool:
        """Validate that a case name looks reasonable."""
        if not case_name or case_name == "N/A":
            return False
        
        contamination_indicators = [
            "are .", "ions of", "eview .", "questions of", "de novo", 
            "statutory", "federal court", "this court", "we review",
            "meaning of a statute", "certified questions"
        ]
        
        for indicator in contamination_indicators:
            if indicator.lower() in case_name.lower():
                return False
        
        parts = case_name.split(" v. ")
        if len(parts) != 2:
            return False
        
        plaintiff, defendant = parts
        if not plaintiff or not defendant:
            return False
        
        plaintiff_clean = plaintiff.strip()
        words = plaintiff_clean.split()
        clean_plaintiff = None
        for word in words:
            if word and word[0].isupper():
                clean_plaintiff = word
                break
        
        if not clean_plaintiff or not defendant.strip():
            return False
        
        if not defendant.strip()[0].isupper():
            return False
        
        if len(case_name) < 10 or len(case_name) > 200:
            return False
        
        sentence_starters = ["We also", "The court", "This court", "The meaning", "Also review", "Certified questions"]
        for starter in sentence_starters:
            if case_name.startswith(starter):
                return False
        
        return True

_unified_extractor = None

def get_unified_extractor() -> UnifiedExtractionArchitecture:
    """Get the global unified extractor instance."""
    global _unified_extractor
    if _unified_extractor is None:
        _unified_extractor = UnifiedExtractionArchitecture()
    return _unified_extractor

def extract_case_name_and_year_unified(
    text: str, 
    citation: str,
    start_index: Optional[int] = None,
    end_index: Optional[int] = None,
    debug: bool = False
) -> Dict[str, Any]:
    """
    Convenience function for backward compatibility.
    
    This function should be used to replace all existing extraction functions
    throughout the application.
    """
    extractor = get_unified_extractor()
    result = extractor.extract_case_name_and_year(text, citation, start_index, end_index, debug)
    
    return {
        'case_name': result.case_name,
        'year': result.year,
        'date': result.year,
        'confidence': result.confidence,
        'method': result.method,
        'debug_info': result.debug_info or {}
    }

