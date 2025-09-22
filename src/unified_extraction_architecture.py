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
        
        # INTELLIGENT CASE NAME EXTRACTION: Use smart boundary detection instead of greedy regex
        # This will be handled by the new _extract_case_name_intelligent method
        self.context_patterns = [
            # PRIORITY: String citation patterns (most specific first)
            r'([A-Z][a-zA-Z\s\'&\-\.,]{2,60})\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.,]{2,60}),\s*(?:\d+\s+[A-Za-z\.]+\s+\d+,?\s*)*(?:\d+\s+[A-Za-z\.]+\s+\d+)',
            
            # COMPLEX ORGANIZATIONAL patterns
            r'([A-Z][a-zA-Z\s\'&\-\.,]+(?:Ord\.?|Aerie|No\.?\s+\d+|Lodge|Chapter|Council|Association|Society|Union|Federation|Alliance|Brotherhood|Sisterhood)[a-zA-Z\s\'&\-\.,]*)\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.,]{2,60})',
            
            # CORPORATE ENTITY patterns
            r'([A-Z][a-zA-Z\s\'&\-\.,]{2,50}(?:LLC|Inc\.?|Corp\.?|Ltd\.?|Co\.?|L\.P\.?|L\.L\.P\.?))\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.,]{2,50})',
            
            # GENERAL pattern (last resort to avoid early truncation)
            r'([A-Z][a-zA-Z\s\'&\-\.]{2,50})\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.]{2,50})',
        ]
        
        # Stopwords that typically appear before case names in legal text
        self.capitalized_stopwords = {
            'The', 'This', 'That', 'In', 'On', 'At', 'By', 'For', 'With', 'From', 'To',
            'Court', 'Judge', 'Justice', 'Chief', 'Associate', 'District', 'Circuit',
            'Supreme', 'Federal', 'State', 'County', 'Municipal', 'Appellate',
            'Plaintiff', 'Defendant', 'Petitioner', 'Respondent', 'Appellant', 'Appellee',
            'United', 'States', 'America', 'Government', 'Department', 'Agency',
            'See', 'Citing', 'Quoting', 'Accord', 'Compare', 'Contra', 'But',
            'Also', 'Moreover', 'Furthermore', 'However', 'Nevertheless', 'Nonetheless',
            'Held', 'Found', 'Ruled', 'Decided', 'Determined', 'Concluded'
        }
        
        self.fallback_patterns = [
            # STRING CITATION patterns - handle multiple citations in one sentence
            # Pattern: "Case v. Name, 123 Cite 456, 789 P.3d 012 (year)"
            r'([A-Z][a-zA-Z\s\'&\-\.,]{2,60})\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.,]{2,60}),\s*(?:\d+\s+[A-Za-z\.]+\s+\d+,?\s*)*(?:\d+\s+[A-Za-z\.]+\s+\d+)',
            
            # COMPLEX ORGANIZATIONAL NAME patterns
            # Pattern: "Fraternal Ord. of Eagles, Tenino Aerie No. 564 v. Grand Aerie"
            r'([A-Z][a-zA-Z\s\'&\-\.,]+(?:Ord\.?|Aerie|No\.?\s+\d+|Lodge|Chapter|Council|Association|Society|Union|Federation|Alliance|Brotherhood|Sisterhood)[a-zA-Z\s\'&\-\.,]*)\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.,]{2,60})',
            
            # COMPANY NAME patterns - handle "Company, Inc. v. Other Party" correctly
            # IMPROVED: Better handling of corporate suffixes and complex names
            r'([A-Z][a-zA-Z\s\'&\-\.,]{2,50}(?:LLC|Inc\.?|Corp\.?|Ltd\.?|Co\.?|L\.P\.?|L\.L\.P\.?))\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.,]{2,50})',
            r'([A-Z][a-zA-Z\s\'&\-\.,]{1,50})\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.,]{1,30}(?:LLC|Inc\.?|Corp\.?|Ltd\.?|Co\.?))',
            # DEPARTMENT patterns
            r'([A-Z][a-zA-Z\s\'&\-\.]{1,50})\s+v\.\s+(Dep\'t\s+of\s+[A-Z][a-zA-Z\s\'&\-\.]{1,50})',
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
                # Use advanced cleaning to prevent truncation and improve quality
                cleaned_case_name = self._clean_case_name_advanced(result.case_name, debug)
                result.case_name = cleaned_case_name
                if debug:
                    logger.warning(f"âœ… UNIFIED_EXTRACT: Context extraction successful: '{result.case_name}'")
                return result
        
        result = self._extract_with_patterns(normalized_text, citation, start_index or 0, end_index or len(normalized_text), debug)
        
        # Use advanced cleaning to prevent truncation and improve quality
        if result and result.case_name and result.case_name != 'N/A':
            cleaned_case_name = self._clean_case_name_advanced(result.case_name, debug)
            result.case_name = cleaned_case_name
        
        if debug:
            logger.warning(f"âœ… UNIFIED_EXTRACT: Pattern extraction result: '{result.case_name}'")
        
        return result
    
    def _try_patterns_on_context(self, context: str, citation: str, citation_start_in_context: int, citation_end_in_context: int, debug: bool) -> Optional[ExtractionResult]:
        """Try extraction patterns on a specific context window."""
        # Simple pattern for case names: "Name v. Name" or "In re Name"
        case_patterns = [
            r'([A-Z][a-zA-Z\'\.\&\s]*(?:\s+(?:of|the|and|&|v\.|vs\.|versus)\s+[A-Z][a-zA-Z\'\.\&\s]*)*)\s+v\.\s+([A-Z][a-zA-Z\'\.\&\s]*(?:\s+(?:of|the|and|&|[A-Z][a-zA-Z\'\.\&\s]*)*)*)',
            r'(In\s+re\s+[A-Z][a-zA-Z\'\.\&\s]*(?:\s+(?:of|the|and|&|[A-Z][a-zA-Z\'\.\&\s]*)*)*)',
            r'([A-Z][a-zA-Z\'\.\&\s]*(?:\s+(?:of|the|and|&)*\s*[A-Z][a-zA-Z\'\.\&\s]*)*)\s+v\.\s+([A-Z][a-zA-Z\'\.\&\s]*(?:\s+(?:of|the|and|&)*\s*[A-Z][a-zA-Z\'\.\&\s]*)*)'
        ]
        
        if debug:
            logger.warning(f"🔍 ADJUSTED_CONTEXT_EXTRACTION: Testing context: '{context}'")
        
        for i, pattern in enumerate(case_patterns):
            matches = list(re.finditer(pattern, context, re.IGNORECASE))
            
            if debug:
                logger.warning(f"🔍 PATTERN_{i+1}: Found {len(matches)} matches")
            
            if matches:
                # Find the closest match to the citation
                best_match = None
                min_distance = float('inf')
                
                for match in matches:
                    match_end_in_context = match.end()
                    distance = abs(match_end_in_context - citation_start_in_context)
                    
                    if debug:
                        logger.warning(f"🔍 MATCH: '{match.group(0)}' at distance {distance}")
                    
                    if distance < min_distance:
                        min_distance = distance
                        best_match = match
                
                if best_match:
                    # Extract case name from match
                    if best_match.group(0).startswith('In re'):
                        case_name = best_match.group(1) if best_match.lastindex >= 1 else best_match.group(0)
                    else:
                        # Standard "A v. B" format
                        plaintiff = best_match.group(1) if best_match.lastindex >= 1 else ""
                        defendant = best_match.group(2) if best_match.lastindex >= 2 else ""
                        if plaintiff and defendant:
                            case_name = f"{plaintiff.strip()} v. {defendant.strip()}"
                        else:
                            case_name = best_match.group(0)
                    
                    # Clean up the case name
                    case_name = case_name.strip()
                    case_name = re.sub(r'\s+', ' ', case_name)  # Normalize whitespace
                    
                    if debug:
                        logger.warning(f"✅ EXTRACTED_CASE_NAME: '{case_name}' using adjusted context")
                    
                    # Simple validation
                    if len(case_name) > 5 and 'v.' in case_name:
                        return ExtractionResult(
                            case_name=case_name,
                            year="Unknown",
                            confidence=0.9,
                            method=f"adjusted_context_pattern_{i+1}",
                            context=context[:100] + "..." if len(context) > 100 else context
                        )
        
        if debug:
            logger.warning(f"❌ NO_MATCH: No case name found in adjusted context")
        return None
    
    def _detect_string_citation(self, text: str, citation: str, start_index: int, end_index: int, debug: bool) -> Optional[ExtractionResult]:
        """Detect and parse string citations where multiple citations appear in one sentence."""
        try:
            # Look for string citation pattern: "Case v. Name, 123 Cite 456, 789 P.3d 012 (year)"
            # Extract a larger context to capture the full string citation
            context_start = max(0, start_index - 200)
            context_end = min(len(text), end_index + 50)
            context = text[context_start:context_end]
            
            import re
            
            # Pattern to match string citations with multiple citations
            string_pattern = r'([A-Z][a-zA-Z\s\'&\-\.,]{2,80})\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.,]{2,80}),\s*(?:[^,]+,\s*)*(?:[^,]*' + re.escape(citation) + r'[^,]*)'
            
            match = re.search(string_pattern, context, re.IGNORECASE)
            if match:
                plaintiff = match.group(1).strip()
                defendant = match.group(2).strip()
                
                # Clean up the case name parts
                plaintiff = re.sub(r'\s+', ' ', plaintiff).strip()
                defendant = re.sub(r'\s+', ' ', defendant).strip()
                
                case_name = f"{plaintiff} v. {defendant}"
                
                if debug:
                    logger.warning(f"✅ STRING_CITATION: Found string citation pattern: '{case_name}'")
                
                return ExtractionResult(
                    case_name=case_name,
                    year="Unknown",
                    confidence=0.9,
                    method="string_citation_parsing",
                    context=context[:100] + "..."
                )
            
            return None
            
        except Exception as e:
            if debug:
                logger.warning(f"❌ STRING_CITATION_ERROR: {e}")
            return None

    def _clean_case_name_advanced(self, case_name: str, debug: bool = False) -> str:
        """Advanced case name cleaning to prevent truncation and improve quality."""
        if not case_name or case_name == 'N/A':
            return case_name
            
        import re
        
        original = case_name
        
        # Remove leading/trailing whitespace and normalize spaces
        case_name = re.sub(r'\s+', ' ', case_name.strip())
        
        # CRITICAL FIX: Prevent truncation of company names
        # If case name starts with corporate suffix, it's likely truncated
        corporate_prefixes = r'^(Inc\.?|Corp\.?|LLC|Ltd\.?|Co\.?|L\.P\.?|L\.L\.P\.?)\s+v\.'
        if re.match(corporate_prefixes, case_name, re.IGNORECASE):
            if debug:
                logger.warning(f"🚨 TRUNCATION_DETECTED: Case name '{case_name}' appears truncated (starts with corporate suffix)")
            # This indicates truncation - we should reject this extraction
            return 'N/A'
        
        # Clean up common issues
        # Remove leading articles and prepositions that got captured
        leading_words = r'^(The|A|An|In|On|At|By|For|With|From|To|See|Citing|Quoting)\s+'
        case_name = re.sub(leading_words, '', case_name, flags=re.IGNORECASE)
        
        # Remove trailing punctuation except periods in abbreviations
        case_name = re.sub(r'[,;:]+$', '', case_name)
        
        # Ensure proper "v." formatting
        case_name = re.sub(r'\s+v\s+', ' v. ', case_name, flags=re.IGNORECASE)
        case_name = re.sub(r'\s+vs\s+', ' v. ', case_name, flags=re.IGNORECASE)
        
        # Remove excessive punctuation
        case_name = re.sub(r'\.{2,}', '.', case_name)
        case_name = re.sub(r',{2,}', ',', case_name)
        
        # Final cleanup
        case_name = case_name.strip()
        
        if debug and case_name != original:
            logger.warning(f"🧹 CASE_NAME_CLEANED: '{original}' → '{case_name}'")
        
        return case_name

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
            # FIRST: Try string citation detection
            string_result = self._detect_string_citation(text, citation, start_index, end_index, debug)
            if string_result:
                return string_result
            # IMPROVED NESTED CITATION DETECTION
            # First, check if this citation is in a "quoting" context
            text_before_citation = text[:start_index]
            text_after_citation = text[end_index:end_index + 200]  # Look ahead for context
            
            # Look for "quoting" pattern with case name
            import re
            quoting_match = re.search(r'quoting\s+([A-Z][^,]+v\.\s+[A-Z][^,]+)', text_before_citation)
            
            if quoting_match:
                quoted_case_name = quoting_match.group(1).strip()
                quoting_pos = quoting_match.start()
                distance_to_citation = start_index - quoting_pos
                
                if debug:
                    logger.warning(f"🔍 QUOTING_DETECTED: Found 'quoting {quoted_case_name}' at distance {distance_to_citation}")
                
                # CRITICAL FIX: Only apply quoted case name to citations that come AFTER the "quoting" keyword
                # Citations that come BEFORE "quoting" belong to the citing case, not the quoted case
                if distance_to_citation < 200 and distance_to_citation > 0:
                    # Check if this citation appears to be part of the quoted case (after "quoting")
                    # Look for the citation text in the context after "quoting"
                    text_after_quoting = text_before_citation[quoting_pos:]
                    
                    if citation in text_after_quoting:
                        if debug:
                            logger.warning(f"✅ NESTED_CITATION_SUCCESS: Citation '{citation}' found after 'quoting', using quoted case name '{quoted_case_name}'")
                        
                        return ExtractionResult(
                            case_name=quoted_case_name,
                            year="Unknown",
                            confidence=0.95,
                            method="nested_quoting_pattern",
                            context=f"quoting {quoted_case_name}"
                        )
                    else:
                        if debug:
                            logger.warning(f"🔍 QUOTING_SKIP: Citation '{citation}' appears before 'quoting', not part of quoted case")
                else:
                    if debug:
                        logger.warning(f"🔍 QUOTING_SKIP: Distance {distance_to_citation} outside valid range for quoting pattern")
            
            # NEW: Try intelligent case name extraction first
            intelligent_result = self._extract_case_name_intelligent(text, citation, start_index, end_index, debug)
            if intelligent_result:
                return intelligent_result
            
            # Fallback to original context-based extraction
            context_start = max(0, start_index - 500)
            context_end = min(len(text), end_index + 100)
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
        return None
    
    def _extract_case_name_intelligent(self, text: str, citation: str, start_index: int, end_index: int, debug: bool) -> Optional[ExtractionResult]:
        """
        INTELLIGENT CASE NAME EXTRACTION using smart boundary detection.
        
        Algorithm:
        1. Find "v." patterns in the context around the citation
        2. For each "v.", go backwards until hitting a capitalized stopword or non-capitalized non-stopword
        3. Start case name from the next word forward
        """
        import re
        
        # Extract context around the citation
        context_start = max(0, start_index - 200)
        context_end = min(len(text), end_index + 100)
        context = text[context_start:context_end]
        
        if debug:
            logger.warning(f"🧠 INTELLIGENT: Analyzing context: '{context}'")
        
        # Find all "v." patterns in the context
        v_patterns = list(re.finditer(r'\bv\.\s*', context, re.IGNORECASE))
        
        if not v_patterns:
            return None
        
        best_case_name = None
        best_distance = float('inf')
        
        for v_match in v_patterns:
            v_start = v_match.start()
            v_end = v_match.end()
            
            # Calculate distance from citation
            citation_start_in_context = start_index - context_start
            distance = abs(v_end - citation_start_in_context)
            
            # Extract plaintiff (go backwards from "v.")
            plaintiff = self._extract_plaintiff_backwards(context, v_start, debug)
            
            # Extract defendant (go forwards from "v.")  
            defendant = self._extract_defendant_forwards(context, v_end, debug)
            
            if plaintiff and defendant:
                case_name = f"{plaintiff} v. {defendant}"
                
                if debug:
                    logger.warning(f"🧠 INTELLIGENT: Extracted case name: '{case_name}' at distance {distance}")
                
                # Choose the closest valid case name to the citation
                if distance < best_distance and self._is_valid_case_name(case_name):
                    best_case_name = case_name
                    best_distance = distance
        
        if best_case_name:
            year = self._extract_year_from_context(context, citation)
            
            return ExtractionResult(
                case_name=best_case_name,
                year=year,
                confidence=0.98,
                method="intelligent_boundary_detection",
                start_index=start_index,
                end_index=end_index,
                context=context
            )
        
        return None
    
    def _extract_plaintiff_backwards(self, context: str, v_start: int, debug: bool) -> Optional[str]:
        """
        Extract plaintiff by going backwards from 'v.' until hitting a boundary.
        
        Algorithm:
        1. Go backwards from 'v.' until hitting a capitalized stopword (like "In", "The", "Court")
        2. Once we hit the boundary, go FORWARD to the next word to start the plaintiff name
        3. Continue forward until we reach 'v.' to get the complete plaintiff name
        
        Example: "In Smith, Inc. v. Jones"
        - Go backwards from 'v.': "Inc." -> "Smith," -> "In" (STOP - capitalized stopword)
        - Go forward from "In": start with "Smith" (first word of plaintiff)
        - Continue to 'v.': "Smith, Inc." (complete plaintiff)
        """
        import re
        
        before_v = context[:v_start]
        words = re.findall(r'\S+', before_v)
        
        if not words:
            return None
        
        # Step 1: Go backwards to find the boundary (capitalized stopword)
        boundary_index = None
        
        for i, word in enumerate(reversed(words)):
            clean_word = re.sub(r'[^\w\.\&\'-]', '', word)
            
            if not clean_word:
                continue
            
            # RULE 1: Stop at capitalized stopwords
            if clean_word[0].isupper() and clean_word in self.capitalized_stopwords:
                boundary_index = len(words) - 1 - i  # Convert back to forward index
                if debug:
                    logger.warning(f"🧠 PLAINTIFF: Hit CAPITALIZED STOPWORD boundary at word '{word}' (index {boundary_index})")
                break
            
            # RULE 2: Stop at non-capitalized non-stopwords (prose words)
            if not clean_word[0].isupper():
                # Define stopwords that CAN be part of case names (don't stop for these)
                case_name_stopwords = {'of', 'the', 'and', 'for', 'in', 'on', 'at', 'by', 'with', 'v', 'vs'}
                if clean_word.lower() not in case_name_stopwords:
                    # This is a non-capitalized non-stopword - STOP
                    boundary_index = len(words) - 1 - i  # Convert back to forward index
                    if debug:
                        logger.warning(f"🧠 PLAINTIFF: Hit NON-CAPITALIZED NON-STOPWORD boundary at word '{word}' (index {boundary_index})")
                    break
                else:
                    if debug:
                        logger.warning(f"🧠 PLAINTIFF: Continuing through non-capitalized stopword '{word}' (part of case name)")
            else:
                if debug:
                    logger.warning(f"🧠 PLAINTIFF: Continuing through capitalized non-stopword '{word}'")
        
        # Step 2: Go forward from the boundary to find the NEXT CAPITALIZED WORD
        plaintiff_words = []
        start_index = (boundary_index + 1) if boundary_index is not None else 0
        found_first_capital = False
        
        for i in range(start_index, len(words)):
            word = words[i]
            clean_word = re.sub(r'[^\w\.\&\'-]', '', word)
            
            if not clean_word:
                continue
            
            # FIXED: Go to the next capitalized word to start the plaintiff name
            if not found_first_capital:
                if clean_word[0].isupper():
                    found_first_capital = True
                    plaintiff_words.append(word)
                    if debug:
                        logger.warning(f"🧠 PLAINTIFF: Found first capital word '{word}' - starting plaintiff name")
                else:
                    if debug:
                        logger.warning(f"🧠 PLAINTIFF: Skipping non-capital word '{word}' before plaintiff name")
                    continue
            else:
                # We've found the first capital word, now continue building the name
                if self._should_include_in_plaintiff_name(clean_word):
                    plaintiff_words.append(word)
                    if debug:
                        logger.warning(f"🧠 PLAINTIFF: Added word '{word}' (continuing plaintiff name)")
                else:
                    if debug:
                        logger.warning(f"🧠 PLAINTIFF: Skipping word '{word}' (not part of case name)")
                    # Don't break - continue to include all words until v.
        
        if plaintiff_words:
            plaintiff = ' '.join(plaintiff_words).strip(' ,')
            if debug:
                logger.warning(f"🧠 PLAINTIFF: Final result: '{plaintiff}'")
            return plaintiff
        
        return None
    
    def _extract_defendant_forwards(self, context: str, v_end: int, debug: bool) -> Optional[str]:
        """Extract defendant by going forwards from 'v.' until hitting a boundary."""
        import re
        
        after_v = context[v_end:]
        words = re.findall(r'\S+', after_v)
        
        if not words:
            return None
        
        defendant_words = []
        found_first_capital = False
        
        for word in words:
            clean_word = re.sub(r'[^\w\.\&\'-]', '', word)
            
            if not clean_word:
                continue
            
            # FIXED: Go to the next capitalized word to start the defendant name
            if not found_first_capital:
                if clean_word[0].isupper():
                    found_first_capital = True
                    defendant_words.append(word)
                    if debug:
                        logger.warning(f"🧠 DEFENDANT: Found first capital word '{word}' - starting defendant name")
                else:
                    if debug:
                        logger.warning(f"🧠 DEFENDANT: Skipping non-capital word '{word}' before defendant name")
                    continue
            else:
                # We've found the first capital word, now continue building the name
                # FIXED: Stop at obvious boundaries like numbers, lowercase prose words, etc.
                if self._should_include_in_defendant_name(clean_word):
                    defendant_words.append(word)
                    if debug:
                        logger.warning(f"🧠 DEFENDANT: Added word '{word}'")
                else:
                    if debug:
                        logger.warning(f"🧠 DEFENDANT: Hit boundary at word '{word}' - stopping")
                    break
        
        if defendant_words:
            defendant = ' '.join(defendant_words).strip(' ,')
            if debug:
                logger.warning(f"🧠 DEFENDANT: Final result: '{defendant}'")
            return defendant
        
        return None
    
    def _should_include_in_case_name(self, word: str) -> bool:
        """Determine if a word should be included in the case name."""
        clean_word = word.strip('.,;:!?()[]{}"\'-')
        
        if not clean_word:
            return False
        
        # Check if it's a capitalized stopword
        if clean_word in self.capitalized_stopwords:
            return False
        
        # Check if it's a non-capitalized word (likely prose)
        if not clean_word[0].isupper():
            case_name_words = {'of', 'the', 'and', 'for', 'in', 'on', 'at', 'by', 'with'}
            if clean_word.lower() not in case_name_words:
                return False
        
        return True
    
    def _should_include_in_defendant_name(self, word: str) -> bool:
        """Determine if a word should be included in the defendant name (more restrictive)."""
        clean_word = word.strip('.,;:!?()[]{}"\'-')
        
        if not clean_word:
            return False
        
        # Stop at numbers (like citation numbers)
        if clean_word.isdigit():
            return False
        
        # Stop at obvious legal/prose words
        stop_words = {
            'in', 'the', 'that', 'this', 'and', 'or', 'but', 'for', 'with', 'from', 'to',
            'held', 'decided', 'ruled', 'found', 'court', 'favor', 'against', 'plaintiff', 'defendant'
        }
        
        if clean_word.lower() in stop_words:
            return False
        
        # Allow capitalized words and common case name connectors
        if clean_word[0].isupper():
            return True
        
        # Allow specific lowercase words that can be part of case names
        case_name_words = {'of', 'and', 'v', 'vs'}
        return clean_word.lower() in case_name_words
    
    def _should_include_in_plaintiff_name(self, word: str) -> bool:
        """Determine if a word should be included in the plaintiff name."""
        clean_word = word.strip('.,;:!?()[]{}"\'-')
        
        if not clean_word:
            return False
        
        # Skip obvious prose words that aren't part of case names
        skip_words = {'in', 'at', 'on', 'by', 'with', 'from', 'to', 'for', 'under', 'over'}
        
        if clean_word.lower() in skip_words:
            return False
        
        # Allow capitalized words (proper nouns, company names, etc.)
        if clean_word[0].isupper():
            return True
        
        # Allow specific lowercase words that can be part of case names
        case_name_words = {'of', 'the', 'and', 'v', 'vs'}
        return clean_word.lower() in case_name_words

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

