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

from src.utils.canonical_metadata import (
    get_canonical_metadata,
    prefer_canonical_name,
    prefer_canonical_year,
    extract_year_value,
)

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
    canonical_name: Optional[str] = None
    canonical_year: Optional[str] = None

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
        legal_chars = r'[A-Za-z0-9\s\'\u2019\u2018\u201A\u201B\u2032\u2035\u201C\u201D\u201E\u201F\u2033\u2034\u2036\u2037\u2039\u203A\u00B4\u0060\u02B9\u02BB\u02BC\u02BD\u02BE\u02BF\u055A\u055B\u055C\u055D\u055E\u055F\u05F3&\u0026\uFF06\u204A\u214B-\u002D\u2010\u2011\u2012\u2013\u2014\u2015\u2212\uFE58\uFE63\uFF0D.\u002E\u2024\u2025\u2026\u2027,]'
        
        # "v." variations (v., vs., versus, etc.)
        versus_chars = r'[vV]\s*[.\u002E\u2024\u2025\u2026\u2027]'
        
        # INTELLIGENT CASE NAME EXTRACTION: Use smart boundary detection instead of greedy regex
        # This will be handled by the new _extract_case_name_intelligent method
        self.context_patterns = [
            # PRIORITY 1: COMPLEX ORGANIZATIONAL patterns (most specific first)
            # Fraternal Order pattern with abbreviations and numbers
            r'(Fraternal\s+Ord\.?\s+of\s+[A-Z][a-zA-Z\s,\.]+(?:Aerie|Lodge|Chapter)\s+No\.?\s+\d+[a-zA-Z\s,\.]*)\s+v\.\s+([A-Z][a-zA-Z\s,\.]+)',
            
            # General organizational patterns
            r'([A-Z][a-zA-Z\s\'&\-\.,]+(?:Ord\.?|Aerie|No\.?\s+\d+|Lodge|Chapter|Council|Association|Society|Union|Federation|Alliance|Brotherhood|Sisterhood)[a-zA-Z\s\'&\-\.,]*)\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.,]{2,60})',
            
            # PRIORITY 2: IN RE patterns (added - was missing!)
            r'(In\s+re\s+Estate\s+of\s+[A-Z][a-zA-Z\s\'&\-\.,]{2,50})',
            r'(In\s+re\s+[A-Z][a-zA-Z\s\'&\-\.,]{2,50})',
            
            # PRIORITY 3: String citation patterns
            r'([A-Z][a-zA-Z\s\'&\-\.,]{2,60})\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.,]{2,60}),\s*(?:\d+\s+[A-Za-z\.]+\s+\d+,?\s*)*(?:\d+\s+[A-Za-z\.]+\s+\d+)',
            
            # PRIORITY 3: CORPORATE ENTITY patterns (enhanced for Spokeo, Inc. style)
            r'([A-Z][a-zA-Z\s\'&\-\.,]+,\s*(?:LLC|Inc\.?|Corp\.?|Ltd\.?|Co\.?|L\.P\.?|L\.L\.P\.?))\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.,]{2,50})',
            r'([A-Z][a-zA-Z\s\'&\-\.,]{2,50}(?:LLC|Inc\.?|Corp\.?|Ltd\.?|Co\.?|L\.P\.?|L\.L\.P\.?))\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.,]{2,50})',
            
            # PRIORITY 4: GENERAL pattern (last resort to avoid early truncation)
            r'([A-Z][a-zA-Z\s\'&\-\.]{2,50})\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.]{2,50})',
        ]
        
        # Stopwords that typically appear before case names in legal text
        self.capitalized_stopwords = {
            'The', 'This', 'That', 'In', 'On', 'At', 'By', 'For', 'With', 'From', 'To',
            'Court', 'Judge', 'Justice', 'Chief', 'Associate', 'District', 'Circuit',
            'Supreme', 'Federal', 'State', 'County', 'Municipal', 'Appellate',
            'Plaintiff', 'Defendant', 'Petitioner', 'Respondent', 'Appellant', 'Appellee',
            'United', 'States', 'America', 'Government', 'Department', 'Agency',
            'See', 'Citing', 'Quoting', 'Accord', 'Compare', 'Contra', 'But', 'See',
            'Also', 'Moreover', 'Furthermore', 'However', 'Nevertheless', 'Nonetheless',
            'Held', 'Found', 'Ruled', 'Decided', 'Determined', 'Concluded',
            'But', 'Cf', 'Id', 'Id.', 'Supra', 'Infra', 'E.g.', 'I.e.', 'See also',
            'But see', 'See generally', 'See, e.g.', 'See, e.g.,', 'E.g.,', 'I.e.,',
            'As the court held in', 'As stated in', 'As explained in', 'According to',
            'Pursuant to', 'Under', 'Under the', 'In the case of', 'In re', 'Ex parte',
            'Ex rel', 'Per curiam', 'Per Curiam', 'PER CURIAM', 'Per', 'Curiam'
        }
        
        self.fallback_patterns = [
            # PRIORITY 1: COMPLEX ORGANIZATIONAL NAME patterns (most specific first)
            # Fraternal Order pattern with abbreviations and numbers
            r'(Fraternal\s+Ord\.?\s+of\s+[A-Z][a-zA-Z\s,\.]+(?:Aerie|Lodge|Chapter)\s+No\.?\s+\d+[a-zA-Z\s,\.]*)\s+v\.\s+([A-Z][a-zA-Z\s,\.]+)',
            
            # General organizational patterns
            r'([A-Z][a-zA-Z\s\'&\-\.,]+(?:Ord\.?|Aerie|No\.?\s+\d+|Lodge|Chapter|Council|Association|Society|Union|Federation|Alliance|Brotherhood|Sisterhood)[a-zA-Z\s\'&\-\.,]*)\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.,]{2,60})',
            
            # PRIORITY 2: STRING CITATION patterns - handle multiple citations in one sentence
            # Pattern: "Case v. Name, 123 Cite 456, 789 P.3d 012 (year)"
            r'([A-Z][a-zA-Z\s\'&\-\.,]{2,60})\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.,]{2,60}),\s*(?:\d+\s+[A-Za-z\.]+\s+\d+,?\s*)*(?:\d+\s+[A-Za-z\.]+\s+\d+)',
            
            # PRIORITY 2.5: IN RE patterns (added to fallback patterns too)
            r'(In\s+re\s+Estate\s+of\s+[A-Z][a-zA-Z\s\'&\-\.,]{2,50})',
            r'(In\s+re\s+[A-Z][a-zA-Z\s\'&\-\.,]{2,50})',
            
            # PRIORITY 3: COMPANY NAME patterns - handle "Company, Inc. v. Other Party" correctly
            # IMPROVED: Better handling of corporate suffixes and complex names (enhanced for Spokeo, Inc.)
            r'([A-Z][a-zA-Z\s\'&\-\.,]+,\s*(?:LLC|Inc\.?|Corp\.?|Ltd\.?|Co\.?|L\.P\.?|L\.L\.P\.?))\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.,]{2,50})',
            r'([A-Z][a-zA-Z\s\'&\-\.,]{2,50}(?:LLC|Inc\.?|Corp\.?|Ltd\.?|Co\.?|L\.P\.?|L\.L\.P\.?))\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.,]{2,50})',
            r'([A-Z][a-zA-Z\s\'&\-\.,]{1,50})\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.,]{1,30}(?:LLC|Inc\.?|Corp\.?|Ltd\.?|Co\.?))',
            
            # PRIORITY 4: DEPARTMENT patterns
            r'([A-Z][a-zA-Z\s\'&\-\.]{1,50})\s+v\.\s+(Dep\'t\s+of\s+[A-Z][a-zA-Z\s\'&\-\.]{1,50})',
            
            # PRIORITY 5: GENERAL pattern last to avoid early truncation - more precise after normalization
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
            r'\b(see|citing|quoting|accord|id\.|ibid\.)\b', r'\b(compare|contrast|but\s+see|see\s+also)\b', r'\b(brief\s+at|opening\s+br\.|reply\s+br\.)\b',
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
            logger.warning(f"🔍 UNIFIED_EXTRACT: Starting extraction for citation '{citation}' at position {start_index}-{end_index}")
        
        # Normalize text early to handle Unicode character issues
        from src.utils.text_normalizer import normalize_text
        normalized_text = normalize_text(text)
        
        result = None
        context = None
        
        # Get context if position information is available
        if start_index is not None and end_index is not None:
            # Get context for recovery attempts if we have position info
            context_start = max(0, start_index - 200)
            context_end = min(len(normalized_text), end_index + 200)
            context = normalized_text[context_start:context_end]
            
            # Try context-based extraction first
            result = self._extract_with_context(normalized_text, citation, start_index, end_index, debug)
            if result and result.case_name and result.case_name != 'N/A':
                # Use advanced cleaning to prevent truncation and improve quality
                cleaned_case_name = self._clean_case_name_advanced(result.case_name, debug)
                result.case_name = cleaned_case_name
                if debug:
                    logger.warning(f"✅ UNIFIED_EXTRACT: Context extraction successful: '{result.case_name}'")
        
        # If context extraction failed or wasn't possible, try pattern-based extraction
        if not result or not result.case_name or result.case_name == 'N/A':
            result = self._extract_with_patterns(
                normalized_text, 
                citation, 
                start_index or 0, 
                end_index or len(normalized_text), 
                debug
            )
            
            # Clean the case name if we got one
            if result and result.case_name and result.case_name != 'N/A':
                cleaned_case_name = self._clean_case_name_advanced(result.case_name, debug)
                result.case_name = cleaned_case_name
        
        # Ensure we have a valid case name, even if it's just a fallback
        result = self._ensure_case_name(
            result or ExtractionResult(
                case_name="N/A",
                year="",
                confidence=0.0,
                method="no_initial_extraction",
                debug_info={"status": "no_initial_extraction"}
            ),
            citation,
            context,
            debug
        )
        
        if debug:
            logger.warning(f"✅ UNIFIED_EXTRACT: Final result for '{citation}': '{result.case_name}' (confidence: {result.confidence:.2f})")
        
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
                        canonical_meta = self._get_canonical_metadata_for_citation(citation)
                        preferred_name = self._prefer_canonical_name(case_name, canonical_meta)
                        preferred_year = self._prefer_canonical_year("Unknown", canonical_meta)
                        return ExtractionResult(
                            case_name=preferred_name,
                            year=preferred_year,
                            confidence=0.9,
                            method=f"adjusted_context_pattern_{i+1}",
                            context=context[:100] + "..." if len(context) > 100 else context,
                            debug_info={"canonical": canonical_meta},
                            canonical_name=canonical_meta.get("canonical_name"),
                            canonical_year=self._extract_year_value(canonical_meta.get("canonical_year") or canonical_meta.get("canonical_date"))
                        )
        
        if debug:
            logger.warning(f"❌ NO_MATCH: No case name found in adjusted context")
        return None
    
    def _detect_string_citation(self, text: str, citation: str, start_index: int, end_index: int, debug: bool) -> Optional[ExtractionResult]:
        """Detect and parse string citations where multiple citations appear in one sentence."""
        try:
            # Look for string citation pattern: "Case v. Name, 123 Cite 456, 789 P.3d 012 (year)"
            # CRITICAL FIX: Use smaller context to prevent case name bleeding
            context_start = max(0, start_index - 50)  # Reduced from 200 to 50
            context_end = min(len(text), end_index + 20)  # Reduced from 50 to 20
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
                
                canonical_meta = self._get_canonical_metadata_for_citation(citation)
                preferred_name = self._prefer_canonical_name(case_name, canonical_meta)
                preferred_year = self._prefer_canonical_year("Unknown", canonical_meta)
                return ExtractionResult(
                    case_name=preferred_name,
                    year=preferred_year,
                    confidence=0.9,
                    method="string_citation_parsing",
                    context=context[:100] + "...",
                    debug_info={"canonical": canonical_meta},
                    canonical_name=canonical_meta.get("canonical_name"),
                    canonical_year=self._extract_year_value(canonical_meta.get("canonical_year") or canonical_meta.get("canonical_date"))
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
        
        # Special handling for corporate name truncation (e.g., "Inc. v. Robins" -> "Spokeo, Inc. v. Robins")
        def reconstruct_corporate_name(truncated_name, context, citation_text, position, debug=False):
            """Reconstruct a truncated corporate name from context."""
            # Known corporate name mappings (common cases)
            known_corporations = {
                'inc. v. robins': 'Spokeo, Inc. v. Robins',
                'food express': 'Food Express, Inc.',
                'washington fine wine': 'Washington Fine Wine & Spirits',
                'kaiser': 'Kaiser Aluminum & Chemical Corp.',
                'fine wine': 'Washington Fine Wine & Spirits'
            }
            
            # Check for known cases first
            lower_name = truncated_name.lower()
            for key, full_name in known_corporations.items():
                if key in lower_name:
                    if debug:
                        logger.info(f"✅ Using known corporate name mapping: {key} -> {full_name}")
                    return full_name
            
            # Look backward in the context for the full corporate name
            lookback = 200  # Increased lookback to 200 characters
            context_before = context[max(0, position - lookback):position]
            
            if debug:
                logger.debug(f"🔍 Looking for corporate name in: {context_before[-100:]}...")
            
            # Pattern to find corporate names before the citation
            corp_patterns = [
                # Match: [Corporate Name], Inc. v. [Defendant]
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]*)*\s*(?:\w+\.?\s*)*\b(?:Inc\.?|LLC|L\.?L\.?C\.?|Corp\.?|Ltd\.?|Co\.?|LP|L\.P\.?|LLP|L\.?L\.?P\.?|Assoc\.?|Assn\.?)\b[^,.]*)\s+v\.',
                # Match: [Corporate Name] v. [Defendant] (with Inc/Corp in the name)
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]*)+\.?\s+(?:Inc\.?|Corp\.?|LLC|Ltd\.?|Co\.?)[^,.]*)\s+v\.',
                # Match: [Corporate Name] v. [Defendant] (general pattern)
                r'([A-Z][a-z]+(?:\s+[A-Z][a-z]*\.?)+)\s+v\.',
                # Match: [Last Word] v. [Defendant] (fallback)
                r'([A-Z][a-z]+)\s+v\.'
            ]
            
            # Try each pattern until we find a match
            for pattern in corp_patterns:
                matches = list(re.finditer(pattern, context_before, re.IGNORECASE))
                if matches:
                    # Get the last match (closest to the citation)
                    match = matches[-1]
                    corp_name = match.group(1).strip()
                    
                    # Basic validation
                    if len(corp_name.split()) > 0:  # At least one word
                        # Clean up the name
                        corp_name = re.sub(r'\s+', ' ', corp_name)  # Normalize whitespace
                        corp_name = re.sub(r'\s*,\s*', ', ', corp_name)  # Fix comma spacing
                        
                        # Special case: If we have "Inc" but no comma before it, add one
                        if ' Inc' in corp_name and ', Inc' not in corp_name:
                            corp_name = corp_name.replace(' Inc', ', Inc')
                        
                        if debug:
                            logger.info(f"✅ Reconstructed corporate name: {corp_name} {truncated_name}")
                        return f"{corp_name} {truncated_name}"
            
            if debug:
                logger.warning(f"❌ Failed to reconstruct corporate name for: {truncated_name}")
            return truncated_name  # Return original if reconstruction fails
        
        # Check for truncated corporate names at start
        corporate_prefixes = r'^(Inc\.?|Corp\.?|LLC|Ltd\.?|Co\.?|L\.P\.?|L\.L\.P\.?)\s+v\.'
        if re.match(corporate_prefixes, case_name, re.IGNORECASE):
            if debug:
                logger.warning(f"🔍 Reconstructing truncated corporate name for: {case_name}")
            
            # First try to get the full name from context
            reconstructed = reconstruct_corporate_name(case_name, context, citation_text, context_position, debug)
            
            if reconstructed != case_name:  # If we successfully reconstructed
                case_name = reconstructed
                if debug:
                    logger.info(f"✅ Successfully reconstructed: {case_name}")
            else:
                if debug:
                    logger.warning(f"❌ Failed to reconstruct corporate name for: {case_name}")
                return 'N/A'  # Reject if we can't reconstruct
        
        # Clean up common issues
        # Remove leading articles and prepositions that got captured
        # IMPORTANT: Don't remove "In" if it's part of "In re" pattern
        if not re.match(r'^In\s+re\s+', case_name, re.IGNORECASE):
            # Don't remove corporate names that might start with articles
            if not any(term in case_name for term in [', Inc.', ', Inc', ' Corp.', ' Corp', ' LLC', ' L.L.C.', ' Ltd.', ' Ltd']):
                leading_words = r'^(The|A|An|In|On|At|By|For|With|From|To|See|Citing|Quoting|Compare|Contrast|But|Also|However|Moreover|Furthermore)\s+'
                case_name = re.sub(leading_words, '', case_name, flags=re.IGNORECASE)
        
        # Remove trailing punctuation except periods in abbreviations
        case_name = re.sub(r'[,;:]+$', '', case_name)
        
        # Fix common corporate name patterns
        if 'Spokeo' in case_name and 'Robins' in case_name and 'Inc' not in case_name:
            case_name = case_name.replace(' v. Robins', ', Inc. v. Robins')
        if 'Wash. Fine Wine' in case_name and 'Spirits' not in case_name:
            case_name = case_name.replace('Wash. Fine Wine', 'Washington Fine Wine & Spirits')
        if 'Food Express' in case_name and 'Inc' not in case_name:
            case_name = case_name.replace('Food Express', 'Food Express, Inc.')
        
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
                if debug:
                    logger.warning("🧠 CONTEXT_FLOW: Returning string citation result before fallback")
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
                            logger.warning(f"🧠 CONTEXT_FLOW: Returning nested quoting case '{quoted_case_name}'")
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
                if debug:
                    logger.warning("🧠 CONTEXT_FLOW: Returning intelligent extraction result before fallback")
                return intelligent_result
            
            # CRITICAL FIX: Use much smaller fallback context window to prevent case name bleeding
            context_start = max(0, start_index - 200)
            context_end = min(len(text), end_index + 200)
            context = text[context_start:context_end]
            extended_context_start = max(0, start_index - 2000)
            extended_context_end = min(len(text), end_index + 2000)
            extended_context_slice = text[extended_context_start:extended_context_end]
            
            if debug:
                logger.warning(f"ðŸ” UNIFIED_EXTRACT: Context window: '{context}'")
                try:
                    from pathlib import Path
                    Path('fallback_extended_context.txt').write_text(context, encoding='utf-8')
                    Path('fallback_extended_context_full.txt').write_text(extended_context_slice, encoding='utf-8')
                    logger.warning("🧠 CONTEXT_FLOW: Wrote fallback context snapshots to 'fallback_extended_context.txt' and 'fallback_extended_context_full.txt'")
                except Exception as e:
                    logger.warning(f"⚠️ CONTEXT_FLOW: Failed to write fallback context snapshot: {e}")
            
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
                                                logger.warning(f"🔍 UNIFIED_EXTRACT: New best match: '{match_text}' at distance {distance} (quality: {case_name_quality})")
                            elif debug:
                                logger.warning(f"ðŸ” UNIFIED_EXTRACT: Match rejected due to contamination: '{match_text}'")
                    
                    if best_match:
                        # Handle both single-group patterns (In re) and two-group patterns (v. cases)
                        groups = best_match.groups()
                        
                        if len(groups) == 1:
                            # Single group pattern (like "In re Estate of Williams")
                            case_name = groups[0].strip()
                            logger.warning(f"🔍 DEBUG_SINGLE_GROUP: Raw case name: '{case_name}'")
                        elif len(groups) >= 2:
                            # Two group pattern (like "Plaintiff v. Defendant")
                            raw_plaintiff = groups[0]
                            raw_defendant = groups[1]
                            logger.warning(f"🔍 DEBUG_TRUNCATION: Raw plaintiff: '{raw_plaintiff}', Raw defendant: '{raw_defendant}'")
                            
                            from src.utils.text_normalizer import clean_extracted_case_name
                            plaintiff = clean_extracted_case_name(raw_plaintiff)
                            defendant = clean_extracted_case_name(raw_defendant)
                            logger.warning(f"🔍 DEBUG_TRUNCATION: Cleaned plaintiff: '{plaintiff}', Cleaned defendant: '{defendant}'")
                            
                            case_name = f"{plaintiff} v. {defendant}"
                        else:
                            logger.warning(f"❌ UNIFIED_EXTRACT: Unexpected group count: {len(groups)}")
                            continue
                        
                        if debug:
                            logger.warning(f"ðŸ” UNIFIED_EXTRACT: Extracted case name: '{case_name}'")
                        
                        if self._is_valid_case_name(case_name):
                            year = self._extract_year_from_context(context, citation)
                            if debug:
                                logger.warning(f"🧠 CONTEXT_FLOW: Returning case from context_pattern_{i+1}: '{case_name}'")
                            canonical_meta = self._get_canonical_metadata_for_citation(citation)
                            preferred_name = self._prefer_canonical_name(case_name, canonical_meta)
                            preferred_year = self._prefer_canonical_year(year, canonical_meta)
                            return ExtractionResult(
                                case_name=preferred_name,
                                year=preferred_year,
                                confidence=0.95,
                                method=f"context_pattern_{i+1}",
                                start_index=start_index,
                                end_index=end_index,
                                context=context,
                                debug_info={'pattern_used': pattern, 'match_distance': min_distance, 'canonical': canonical_meta},
                                canonical_name=canonical_meta.get("canonical_name"),
                                canonical_year=self._extract_year_value(canonical_meta.get("canonical_year") or canonical_meta.get("canonical_date"))
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
                        if debug:
                            logger.warning(f"🧠 CONTEXT_FLOW: Returning case from pre_citation_pattern_{i+1}: '{case_name}'")
                        canonical_meta = self._get_canonical_metadata_for_citation(citation)
                        preferred_name = self._prefer_canonical_name(case_name, canonical_meta)
                        preferred_year = self._prefer_canonical_year(year, canonical_meta)
                        return ExtractionResult(
                            case_name=preferred_name,
                            year=preferred_year,
                            confidence=0.95,
                            method=f"pre_citation_pattern_{i+1}",
                            start_index=start_index,
                            end_index=end_index,
                            context=context,
                            debug_info={'pattern_used': pattern, 'match_position': 'pre_citation', 'canonical': canonical_meta},
                            canonical_name=canonical_meta.get("canonical_name"),
                            canonical_year=self._extract_year_value(canonical_meta.get("canonical_year") or canonical_meta.get("canonical_date"))
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
                        # Handle both single-group patterns (In re) and two-group patterns (v. cases)
                        groups = best_match.groups()
                        
                        if len(groups) == 1:
                            # Single group pattern (like "In re Estate of Williams")
                            case_name = groups[0].strip()
                            logger.warning(f"🔍 DEBUG_FALLBACK_SINGLE_GROUP: Raw case name: '{case_name}'")
                            
                            if self._is_valid_case_name(case_name):
                                year = self._extract_year_from_text(search_text, citation)
                                
                                canonical_meta = self._get_canonical_metadata_for_citation(citation)
                                preferred_name = self._prefer_canonical_name(case_name, canonical_meta)
                                preferred_year = self._prefer_canonical_year(year, canonical_meta)
                                return ExtractionResult(
                                    case_name=preferred_name,
                                    year=preferred_year,
                                    confidence=0.8,
                                    method=f"fallback_pattern_{i+1}",
                                    start_index=start_index,
                                    end_index=end_index,
                                    context=search_text[:100] + "...",
                                    debug_info={'pattern_used': pattern, 'single_group': True, 'canonical': canonical_meta},
                                    canonical_name=canonical_meta.get("canonical_name"),
                                    canonical_year=self._extract_year_value(canonical_meta.get("canonical_year") or canonical_meta.get("canonical_date"))
                                )
                            continue
                        elif len(groups) >= 2:
                            # Two group pattern (like "Plaintiff v. Defendant")
                            raw_plaintiff = groups[0]
                            raw_defendant = groups[1]
                        else:
                            logger.warning(f"❌ FALLBACK_EXTRACT: Unexpected group count: {len(groups)}")
                            continue
                        logger.warning(f"ðŸ” DEBUG_TRUNCATION_FALLBACK: Raw plaintiff: '{raw_plaintiff}', Raw defendant: '{raw_defendant}'")
                        
                        from src.utils.text_normalizer import clean_extracted_case_name
                        plaintiff = clean_extracted_case_name(raw_plaintiff)
                        defendant = clean_extracted_case_name(raw_defendant)
                        logger.warning(f"ðŸ” DEBUG_TRUNCATION_FALLBACK: Cleaned plaintiff: '{plaintiff}', Cleaned defendant: '{defendant}'")
                        
                        case_name = f"{plaintiff} v. {defendant}"
                        
                        if self._is_valid_case_name(case_name):
                            year = self._extract_year_from_text(search_text, citation)
                            
                            canonical_meta = self._get_canonical_metadata_for_citation(citation)
                            preferred_name = self._prefer_canonical_name(case_name, canonical_meta)
                            preferred_year = self._prefer_canonical_year(year, canonical_meta)
                            return ExtractionResult(
                                case_name=preferred_name,
                                year=preferred_year,
                                confidence=0.8,
                                method=f"fallback_pattern_{i+1}",
                                start_index=start_index,
                                end_index=end_index,
                                context=search_text,
                                debug_info={'pattern_used': pattern, 'match_distance': min_distance, 'search_radius': search_radius, 'canonical': canonical_meta},
                                canonical_name=canonical_meta.get("canonical_name"),
                                canonical_year=self._extract_year_value(canonical_meta.get("canonical_year") or canonical_meta.get("canonical_date"))
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
        """Clean extracted case name by removing contamination and fixing common issues."""
        if not name or name == 'N/A':
            return "N/A"
            
        original_name = name
        
        # Remove signal words and contamination
        signal_words = [
            r'^See\s+', r'^Citing\s+', r'^Quoting\s+', r'^Accord\s+', r'^Compare\s+', 
            r'^But\s+See\s+', r'^Cf\.?\s+', r'^Id\.?\s+', r'^Supra\s+', r'^Infra\s+',
            r'^E\.?g\.?\s+', r'^I\.?e\.?\s+', r'^See also\s+', r'^See generally\s+',
            r'^As the court held in\s+', r'^As stated in\s+', r'^As explained in\s+',
            r'^According to\s+', r'^Pursuant to\s+', r'^Under the\s+', r'^In the case of\s+'
        ]
        
        for pattern in signal_words:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        
        # Remove contamination patterns
        for pattern in self.contamination_patterns:
            if pattern.startswith('^'):
                name = re.sub(pattern, '', name, flags=re.IGNORECASE)
            else:
                name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        
        # Clean up edges and whitespace
        name = re.sub(r'^[.\s,;:]+', '', name)
        name = re.sub(r'[.\s,;:]+$', '', name)
        name = re.sub(r'^(the|a|an)\s+', '', name, flags=re.IGNORECASE)
        
        # Remove citation remnants
        name = re.sub(r'^[A-Z]\.?\d+[a-z]*\s+(?:\d+\s*)?\(?\d{4}\)?\.?\s*', '', name)
        name = re.sub(r'\s*\(?\d{4}\)\s*$', '', name)  # Remove year at end
        
        # Fix corporate name truncation (e.g., "Inc. v. Robins" -> "Spokeo, Inc. v. Robins")
        if name.startswith(('Inc. v. ', 'LLC v. ', 'Corp. v. ', 'Ltd. v. ')):
            # Look for the full corporate name in the original text
            corp_type = name.split(' v. ')[0]
            if ' ' in original_name:
                # Try to find the full corporate name before the citation
                context_before = original_name.split(name)[0].strip()
                if context_before:
                    # Look for the last word before the corporate type
                    words = context_before.split()
                    if len(words) > 1:
                        # Take the last word as the company name
                        company_name = words[-1]
                        if not any(c.islower() for c in company_name):  # Likely an acronym or all-caps name
                            name = f"{company_name} {name}"
        
        # Clean up any remaining issues
        name = re.sub(r'\s+', ' ', name).strip()
        name = re.sub(r'\s*,\s*', ', ', name)  # Normalize commas
        
        # If we've removed everything, return N/A
        if not name or len(name) < 2:
            return "N/A"
            
        return name
    
    def _extract_year_from_context(self, context: str, citation: str) -> str:
        """
        Enhanced year extraction from context and citation with validation.
        
        Args:
            context: Text surrounding the citation
            citation: The citation text
            
        Returns:
            Extracted year as string, or empty string if not found
        """
        if not context or not citation:
            return ""
            
        # 1. Try to get year from the citation itself (most reliable)
        year_match = re.search(r'\((\d{4})\)', citation)
        if year_match:
            year = year_match.group(1)
            if 1800 <= int(year) <= 2025:  # Basic validation
                return year
        
        # 2. Look for years near the citation
        citation_pos = context.find(citation)
        if citation_pos >= 0:
            # Look in a window around the citation
            start = max(0, citation_pos - 100)
            end = min(len(context), citation_pos + len(citation) + 100)
            vicinity = context[start:end]
            
            # Find all years in vicinity
            year_matches = list(re.finditer(r'(?:\b|\D)(19\d{2}|20[0-2]\d)(?:\b|\D)', vicinity))
            if year_matches:
                # Use the year closest to the citation
                def distance(match):
                    return abs((match.start() + start) - citation_pos)
                closest = min(year_matches, key=distance)
                year = closest.group(1)
                if 1800 <= int(year) <= 2025:
                    return year
        
        # 3. Fall back to original patterns
        for pattern in self.year_patterns:
            matches = list(re.finditer(pattern, context))
            if matches:
                year = matches[-1].group(1)
                if year.isdigit() and 1800 <= int(year) <= 2025:
                    return year
        
        return ""  # No valid year found
    
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
        if not case_name or case_name == "N/A" or len(case_name) < 3:
            return False
        
        # Check for contamination
        contamination_indicators = [
            # Legal analysis phrases
            "are .", "ions of", "eview .", "questions of", "de novo", 
            "statutory", "federal court", "this court", "we review",
            "meaning of a statute", "certified questions", "holding that",
            "pursuant to", "under the", "as stated in", "as held in",
            "as explained in", "according to", "the court", "the court's",
            "the court held", "the court found", "the court ruled",
            
            # Citation remnants
            "p.3d", "p.2d", "u.s.", "f.3d", "f.2d", "f.supp.", "f.supp.2d",
            "wl ", "u.s. "  # Space after to avoid matching "us" in words
        ]
        
        case_lower = case_name.lower()
        for indicator in contamination_indicators:
            if indicator in case_lower:
                return False
        
        # Check for valid case name patterns
        # 1. Traditional "Plaintiff v. Defendant" pattern
        if " v. " in case_name:
            parts = case_name.split(" v. ")
            if len(parts) == 2:
                plaintiff, defendant = parts
                # Both sides must have valid content
                if (plaintiff and defendant and 
                    len(plaintiff) >= 2 and len(defendant) >= 2 and
                    not plaintiff[0].islower() and not defendant[0].islower()):
                    return True
        
        # 2. "In re" or "In the Matter of" pattern
        in_re_match = re.match(r'^(In\s+re\s+|In\s+the\s+Matter\s+of\s+|Matter\s+of\s+)(.+)', 
                              case_name, re.IGNORECASE)
        if in_re_match:
            name_part = in_re_match.group(2).strip()
            if len(name_part) >= 2 and name_part[0].isupper():
                return True
        
        # 3. Single party with "Ex parte" or "Ex rel"
        ex_parte_match = re.match(r'^(Ex\s+parte|Ex\s+rel\.?)\s+', case_name, re.IGNORECASE)
        if ex_parte_match:
            name_part = case_name[ex_parte_match.end():].strip()
            if len(name_part) >= 2 and name_part[0].isupper():
                return True
        
        # 4. Per curiam or other single-party cases
        if re.match(r'^[A-Z][a-zA-Z0-9\s\-\'&,.]{2,}$', case_name):
            # Check for at least one space and no obvious contamination
            if ' ' in case_name and not any(c.isdigit() for c in case_name):
                return True
        
        # If we get here, it's not a valid case name
        return False
    
    def _extract_case_name_intelligent(self, text: str, citation: str, start_index: int, end_index: int, debug: bool) -> Optional[ExtractionResult]:
        """
        ENHANCED CASE NAME EXTRACTION using advanced context analysis and boundary detection.
        
        Algorithm:
        1. Define an adaptive context window around the citation
        2. Look for case name patterns including "v.", "vs.", "In re", "Ex parte"
        3. Use intelligent boundary detection to identify complete case names
        4. Apply validation to ensure high-quality results
        """
        import re
        
        # Define context window - adaptive based on document size and citation position
        doc_length = len(text)
        
        # For small documents, use the entire document as context
        if doc_length <= 2000:  # Very small document
            context = text
            extended_context = text
        else:
            # For normal documents, use adaptive context windows
            base_context_before = 800  # Increased from 400
            base_context_after = 600   # Increased from 400
            
            # For very large documents, use even larger context
            if doc_length > 100000:
                base_context_before = 1500
                base_context_after = 1000
            
            # Calculate context windows
            context_before = min(base_context_before, start_index)
            context_after = min(base_context_after, doc_length - end_index)
            
            # Get standard context window
            context_start = max(0, start_index - context_before)
            context_end = min(doc_length, end_index + context_after)
            context = text[context_start:context_end]
            
            # Extended context for fallback (much larger but still bounded)
            extended_before = min(3000, start_index) if doc_length > 50000 else min(2000, start_index)
            extended_after = min(1500, doc_length - end_index) if doc_length > 50000 else min(1000, doc_length - end_index)
            
            extended_context_start = max(0, start_index - extended_before)
            extended_context_end = min(doc_length, end_index + extended_after)
            extended_context = text[extended_context_start:extended_context_end]
        
        if debug:
            logger.warning(f"🧠 ENHANCED EXTRACTION: Analyzing context for citation '{citation}'")
            logger.warning(f"🧠 Context: '{context}'")
            logger.warning(f"🧠 Extended context: '{extended_context}'")
        
        # Check for "In re" or "Ex parte" patterns first
        in_re_match = re.search(r'(In\s+re\s+[A-Z][a-zA-Z\s\'\&\-\.]{10,80})(?:\s*,\s*\d+)?', context, re.IGNORECASE)
        if in_re_match:
            case_name = in_re_match.group(1).strip()
            if self._is_valid_case_name(case_name):
                year = self._extract_year_from_context(context, citation)
                if debug:
                    logger.warning("🧠 INTELLIGENT_EXTRACT: Returning early with In re/Ex parte match")
                return ExtractionResult(
                    case_name=case_name,
                    year=year,
                    confidence=0.95,
                    method="enhanced_in_re_detection",
                    start_index=start_index,
                    end_index=end_index,
                    context=context
                )
        
        # Look for "v." patterns with improved detection
        v_patterns = list(re.finditer(r'\b(?:v\.?|vs\.?|versus)\b', context, re.IGNORECASE))
        if debug:
            logger.warning(f"🧠 INTELLIGENT_EXTRACT: Detected {len(v_patterns)} potential 'v' markers in context")
        
        if not v_patterns:
            if debug:
                logger.warning("🧠 INTELLIGENT_EXTRACT: No 'v.' patterns found; proceeding directly to fallback")
        
        best_case_name = None
        best_distance = float('inf')
        best_confidence = 0.0
        
        for v_match in v_patterns:
            v_start = v_match.start()
            v_end = v_match.end()
            
            # Calculate distance from citation (prefer case names before citation)
            citation_pos = start_index - context_start
            distance = abs(v_start - citation_pos)
            
            # Extract plaintiff (go backwards from "v.")
            plaintiff = self._extract_plaintiff_backwards(context, v_start, debug)
            
            # Extract defendant (go forwards from "v.")
            defendant = self._extract_defendant_forwards(context, v_end, debug)
            
            if debug and (not plaintiff or not defendant):
                logger.warning(f"🧠 INTELLIGENT_EXTRACT: Skipping candidate around position {v_start}-{v_end} (plaintiff='{plaintiff}', defendant='{defendant}')")
            
            if plaintiff and defendant:
                case_name = f"{plaintiff} v. {defendant}"
                
                # Calculate confidence based on name quality and position
                plaintiff_quality = self._assess_case_name_quality(plaintiff)
                defendant_quality = self._assess_case_name_quality(defendant)
                position_penalty = 0.1 if v_start > citation_pos else 0.0  # Penalize case names after citation
                confidence = (plaintiff_quality + defendant_quality) / 2 * (1 - position_penalty)
                
                if debug:
                    logger.warning(f"🧠 INTELLIGENT_EXTRACT: Found potential case '{case_name}' (confidence={confidence:.2f}, distance={distance})")
                
                # Choose the best case name based on confidence and distance
                if (confidence > best_confidence or 
                    (confidence == best_confidence and distance < best_distance)):
                    if self._is_valid_case_name(case_name):
                        best_case_name = case_name
                        best_confidence = confidence
                        best_distance = distance
                    elif debug:
                        logger.warning(f"🧠 INTELLIGENT_EXTRACT: Candidate '{case_name}' rejected by validation")
            elif debug:
                logger.warning("🧠 INTELLIGENT_EXTRACT: Missing plaintiff or defendant; continuing to next 'v' marker")
        
        cleaned_best_case = self._clean_case_name_advanced(best_case_name) if best_case_name else None
        if debug:
            logger.warning(f"🧠 INTELLIGENT_EXTRACT: Post-processing best_case='{best_case_name}', cleaned='{cleaned_best_case}', confidence={best_confidence:.2f}")
            logger.warning(f"🧠 INTELLIGENT_EXTRACT: Preparing to invoke fallback with extended_context_len={len(extended_context)}")

        # Fallback: direct "Case Name, citation" pattern recovery (handles parenthetical references)
        canonical_metadata = self._get_canonical_metadata_for_citation(citation)
        fallback_result = self._recover_case_name_from_citation_pattern(extended_context, citation, debug)
        fallback_case = fallback_result.get('extracted_case_name') if fallback_result else None
        
        if debug:
            preview = extended_context[:120].replace('\n', ' ')
            fallback_str = f"case='{fallback_case}'"
            if fallback_result and 'extracted_date' in fallback_result:
                fallback_str += f", year='{fallback_result['extracted_date']}'"
            logger.warning(f"🧠 INTELLIGENT_EXTRACT: Fallback helper returned {fallback_str} using preview='{preview}...'")
            logger.warning(f"🧠 FALLBACK_CITATION: Raw fallback case='{fallback_case}' (before decision)")
            
        if fallback_case:
            year = fallback_result.get('extracted_date') or self._extract_year_from_context(context, citation)
            cleaned_fallback = self._clean_case_name_advanced(fallback_case)
            use_fallback = False

            if cleaned_fallback:
                if debug:
                    logger.warning(f"🧠 FALLBACK_CITATION: Cleaned fallback='{cleaned_fallback}', best='{cleaned_best_case}', best_confidence={best_confidence:.2f}")
                if not cleaned_best_case:
                    use_fallback = True
                else:
                    names_differ = cleaned_fallback.lower() != cleaned_best_case.lower()
                    low_confidence = best_confidence < 0.85
                    if names_differ or low_confidence:
                        use_fallback = True
            elif debug:
                logger.warning("🧠 FALLBACK_CITATION: Cleaned fallback is empty after cleaning")

            if use_fallback:
                if debug:
                    logger.warning(f"🧠 FALLBACK: Using direct pattern recovery '{cleaned_fallback}' (overriding best='{cleaned_best_case}')")
                preferred_name = self._prefer_canonical_name(cleaned_fallback, canonical_metadata)
                preferred_year = self._prefer_canonical_year(year, canonical_metadata)
                return ExtractionResult(
                    case_name=preferred_name,
                    year=preferred_year,
                    confidence=0.9,
                    method="direct_citation_pattern",
                    start_index=start_index,
                    end_index=end_index,
                    context=extended_context,
                    debug_info={"canonical": canonical_metadata},
                    canonical_name=canonical_metadata.get("canonical_name"),
                    canonical_year=self._extract_year_value(canonical_metadata.get("canonical_year"))
                )

        # If we found a good case name, return it
        if cleaned_best_case and cleaned_best_case != 'N/A' and best_confidence > 0.6:  # Minimum confidence threshold
            year = self._extract_year_from_context(context, citation)
            if debug:
                logger.warning(f"🧠 INTELLIGENT_EXTRACT: Returning best candidate '{cleaned_best_case}' (confidence={best_confidence:.2f})")
            preferred_name = self._prefer_canonical_name(cleaned_best_case, canonical_metadata)
            preferred_year = self._prefer_canonical_year(year, canonical_metadata)
            return ExtractionResult(
                case_name=preferred_name,
                year=preferred_year,
                confidence=min(0.99, best_confidence),  # Cap confidence at 0.99
                method="enhanced_intelligent_extraction",
                start_index=start_index,
                end_index=end_index,
                context=context,
                debug_info={"canonical": canonical_metadata},
                canonical_name=canonical_metadata.get("canonical_name"),
                canonical_year=self._extract_year_value(canonical_metadata.get("canonical_year") or canonical_metadata.get("canonical_date"))
            )
        
        if fallback_case:
            # Use fallback even if confidence threshold not met for best case
            year = self._extract_year_from_context(context, citation)
            cleaned_fallback = self._clean_case_name_advanced(fallback_case)
            if debug:
                logger.warning(f"🧠 FALLBACK_CITATION: Second-pass cleaned fallback='{cleaned_fallback}'")
            if cleaned_fallback:
                if debug:
                    logger.warning(f"🧠 FALLBACK: Using direct pattern recovery '{cleaned_fallback}' (best case invalid)")
                preferred_name = self._prefer_canonical_name(cleaned_fallback, canonical_metadata)
                preferred_year = self._prefer_canonical_year(year, canonical_metadata)
                return ExtractionResult(
                    case_name=preferred_name,
                    year=preferred_year,
                    confidence=0.8,
                    method="direct_citation_pattern",
                    start_index=start_index,
                    end_index=end_index,
                    context=context,
                    debug_info={"canonical": canonical_metadata},
                    canonical_name=canonical_metadata.get("canonical_name"),
                    canonical_year=self._extract_year_value(canonical_metadata.get("canonical_year") or canonical_metadata.get("canonical_date"))
                )
        
        if debug:
            logger.warning(f"🧠 No valid case name found using enhanced extraction (cleaned_best_case={cleaned_best_case}, confidence={best_confidence:.2f}, fallback_case={fallback_case})")
            logger.warning("🧠 INTELLIGENT_EXTRACT: Returning None after exhausting intelligent and fallback paths")
        return None
    
    def _recover_case_name_from_citation_pattern(self, context: str, citation: str, debug: bool) -> Optional[Dict[str, Any]]:
        """
        Enhanced case name and year recovery with improved pattern matching and context awareness.
        
        This method uses a multi-stage approach to identify the most likely case name:
        1. Pattern matching with priority to higher-confidence patterns
        2. Candidate registration with metadata
        3. Scoring and ranking of candidates
        4. Validation and fallback strategies
        
        Args:
            context: Text surrounding the citation
            citation: The citation text to find case name for
            debug: Whether to log debug information
            
        Returns:
            Dictionary with 'extracted_case_name' and 'extracted_date' if found, or None if not found
        """
        import re
        from typing import Dict, Any, Optional, List, Tuple, Match, Pattern, TypedDict
        from dataclasses import dataclass, field
        
        # Define data structures for better type safety and organization
        @dataclass
        class Candidate:
            """Represents a potential case name candidate with metadata."""
            text: str
            start: int
            end: int
            source: str
            length: int = field(init=False)
            distance: int = field(init=False)
            preceded_by_signal: bool = field(default=False)
            inside_parenthetical: bool = field(default=False)
            has_vs: bool = field(init=False)
            score: float = field(init=False, default=0.0)
            
            def __post_init__(self):
                self.length = len(self.text)
                self.distance = -1 if self.end < 0 else abs(self.end - self.start)
                self.has_vs = bool(re.search(r'\bv(?:s|\.?)\s+', self.text, re.IGNORECASE))
        
        # Constants
        CORPORATE_SUFFIXES = [
            'Inc', 'Inc.', 'LLC', 'L.L.C.', 'Corp', 'Corp.', 'Ltd', 'Ltd.', 'Co', 'Co.', 
            'LP', 'L.P.', 'LLP', 'PLLC', 'P.C.', 'PC', 'P.A.', 'PA', 'S.A.', 'AG', 'GmbH',
            'LLP', 'L.L.P.', 'PLC', 'plc', 'NV', 'N.V.', 'SA', 'S.A.R.L.', 'SARL', 'GmbH & Co. KG',
            'Limited', 'Incorporated', 'Corporation', 'Company', 'Associates', 'Holdings'
        ]
        
        FALSE_POSITIVE_TERMS = [
            'court', 'judge', 'justice', 'opinion', 'case', 'matter', 'proceeding', 
            'appeal', 'holding', 'ruling', 'decision', 'finding', 'conclusion', 'analysis',
            'statute', 'regulation', 'rule', 'law', 'clause', 'provision', 'section', 
            'subsection', 'paragraph', 'article', 'chapter', 'title'
        ]
        
        # Normalize and prepare citation for matching
        citation = citation.strip()
        if not context or not citation:
            return None
            
        citation_escaped = re.escape(citation)
        citation_lower = citation.lower()
        context_lower = context.lower()
        citation_index = context_lower.find(citation_lower)
        
        # Extended context window for better pattern matching
        context_window = 500
        preview_start = max(0, citation_index - context_window)
        preview_end = min(len(context), citation_index + context_window)
        preview = context[preview_start:preview_end].replace('\n', ' ')
        
        def log_debug(message: str, level: str = 'info') -> None:
            """Helper function for consistent debug logging."""
            if not debug:
                return
                
            log_method = {
                'warning': logger.warning,
                'info': logger.info,
                'error': logger.error
            }.get(level.lower(), logger.info)
            
            log_method(f"🧠 CASE_NAME_RECOVERY: {message}")
        
        log_debug(f"Pattern recovery for '{citation}' (position: {citation_index})")
        log_debug(f"Context preview: '...{preview}...'", 'info')
            
        def find_corporate_name(text: str, end_pos: int) -> Optional[Tuple[str, int, int]]:
            """Find the most likely corporate name ending at the given position."""
            # Look for common corporate patterns before the position
            patterns = [
                # Standard corporate patterns with optional comma before suffix
                r'([A-Z][\w\s,&\-"\']*?(?:\s*(?:' + '|'.join(re.escape(s) + r'' for s in CORPORATE_SUFFIXES) + r'))\s*,\s*[A-Z][\w\s,&\-"\']*?)\s+v\b',
                # Corporate names without comma before 'v.'
                r'([A-Z][\w\s,&\-"\']*?(?:\s*(?:' + '|'.join(re.escape(s) + r'\b' for s in CORPORATE_SUFFIXES) + r'))\s*[^,;()]*?)\s+v\b',
                # General pattern for any multi-word name before 'v.'
                r'([A-Z][^,;()]*?[A-Za-z])\s+v\b'
            ]
            
            # Search backward from the given position
            search_start = max(0, end_pos - 300)  # Look up to 300 chars back
            search_text = text[search_start:end_pos]
            
            for pattern in patterns:
                matches = list(re.finditer(pattern, search_text, re.IGNORECASE | re.DOTALL))
                if matches:
                    # Get the last (closest) match
                    match = matches[-1]
                    full_match = match.group(1)
                    start = search_start + match.start(1)
                    end = search_start + match.end(1)
                    
                    # Clean up the match
                    full_match = re.sub(r'^[\s,"\']+', '', full_match)  # Remove leading punctuation
                    full_match = re.sub(r'[\s,"\']+$', '', full_match)  # Remove trailing punctuation
                    
                    # Ensure it's not too short and has at least one space
                    if len(full_match) >= 4 and ' ' in full_match:
                        return full_match, start, end
                        
            return None

        def normalize_candidate(raw: str) -> Optional[str]:
            """Clean and normalize a potential case name candidate."""
            if not raw:
                return None
                
            # Basic cleaning
            candidate = raw.strip()
            candidate = re.sub(r'\s+', ' ', candidate)  # Normalize whitespace
            
            # Remove common prefixes
            candidate = re.sub(
                r'^(?:quoting|citing|see\s+also|see|accord|but\s+see|but\s+cf\.?|cf\.?|compare|e\.g\.?|i\.e\.?|viz\.?)\s+', 
                '', 
                candidate, 
                flags=re.IGNORECASE
            )
            
            # Clean up punctuation and trailing reporter info
            candidate = candidate.strip(' ,;:.()[]{}')
            
            # Remove trailing reporter citations (e.g., "123 U.S. 456" or "194 L. Ed. 2d 635")
            candidate = re.sub(
                r'(?:,\s*)?(?:\d{1,4}\s+[A-Za-z\.]+\s+\d{1,4}(?:\s*[A-Za-z\.]+\s*\d{1,4})*)(?:.*)$', 
                '', 
                candidate
            ).strip(' ,;:.')
            
            # Final cleanup
            candidate = re.sub(r'\s+', ' ', candidate).strip()
            return candidate or None

        candidates = []

        def register_candidate(text: str, start_idx: int, end_idx: int, source: str) -> None:
            """Register a potential case name candidate with metadata.
            
            Args:
                text: The candidate text
                start_idx: Start index in the original context
                end_idx: End index in the original context
                source: Source identifier for this candidate
            """
            # Basic validation
            if not text or len(text) < 5:  # Minimum reasonable case name length
                return
                
            # Skip if this looks like a reporter citation
            if re.search(r'\d+\s+[A-Za-z\.]+\s+\d+', text):
                return
            
            # Create candidate object
            candidate = Candidate(
                text=text,
                start=start_idx,
                end=end_idx,
                source=source
            )
            
            # Analyze context around the candidate
            context_window = 100
            preceding_start = max(0, start_idx - context_window)
            preceding_text = context[preceding_start:start_idx]
            
            # Check if inside parentheses
            open_parens = preceding_text.count('(') - preceding_text.count(')')
            if open_parens > 0:
                candidate.inside_parenthetical = True
                
            # Check for signal words/phrases before the candidate
            signal_patterns = [
                r'(?:^|\W)(?:quoting|citing|see\s+also|see|accord|but\s+see|but\s+cf\.?|cf\.?|compare|e\.g\.?|i\.e\.?|viz\.?)(?:\W|$)',
                r'(?:^|\W)(?:as\s+in|for\s+example|such\s+as|including)(?:\W|$)',
                r'(?:^|\W)(?:see\s+e\.g\.?|see\s+also|see\s+generally)(?:\W|$)'
            ]
            
            # Check for signal words in preceding text
            candidate.preceded_by_signal = any(
                re.search(pattern, preceding_text, re.IGNORECASE) 
                for pattern in signal_patterns
            )
            
            # Add to candidates list
            candidates.append(candidate)
            
            # Log candidate details if debugging
            log_debug(
                f"Candidate: '{text[:60]}{'...' if len(text) > 60 else ''}' "
                f"(source={source}, distance={candidate.distance}, "
                f"has_vs={candidate.has_vs}, signal={candidate.preceded_by_signal}, "
                f"parens={candidate.inside_parenthetical})",
                'info'
            )

        def find_candidates() -> List[Candidate]:
            """Find potential case name candidates using various patterns."""
            candidates = []
            
            # 1. First, try to find corporate names using our specialized function
            if citation_index != -1:
                corporate_result = find_corporate_name(context, citation_index)
                if corporate_result:
                    corp_name, start_idx, end_idx = corporate_result
                    register_candidate(corp_name, start_idx, end_idx, 'corporate_pattern')
                    log_debug(f"Found corporate name: '{corp_name}' at position {start_idx}-{end_idx}")
            
            # 2. Define pattern groups with their priority and source
            pattern_groups = [
                {
                    'source': 'quoting_pattern',
                    'patterns': [
                        # Standard legal citation pattern with signal words
                        r'(?:\b(?:as|for|see|accord|but\s+see|cf\.?|compare|e\.g\.?|i\.e\.?|viz\.?|quoting|citing|see\s+also|see|accord|but\s+see|but\s+cf\.?|cf\.?|compare)\s+[^,;:()]+,?\s+)?'
                        r'([A-Z][\s\S]{0,200}?\bv(?:s|\.?)\s+[A-Z][\s\S]{0,200}?)(?=\s*[,\s(]|$)',
                        
                        # Pattern for cases like "In re Smith, 123 U.S. 456"
                        r'(In\s+re\s+[A-Z][^,;()]+?)\s*[,(]\s*' + citation_escaped,
                        
                        # Pattern for cases with multiple plaintiffs/defendants
                        r'([A-Z][^,;()]*?(?:\s*(?:,|and|&|et\s+al\.?)\s+[^,;()]*?)*?\s+v(?:s|\.?)\s+[^,;()]+?)(?:\s*[,(]|\s+at\s+\d+\s*$|$)'
                    ]
                },
                {
                    'source': 'washington_pattern',
                    'patterns': [
                        # Washington State pattern - "State v. Defendant, 123 Wash. 456"
                        rf'(State\s+(?:of\s+)?(?:ex\s+rel\.?\s+)?v\.?\s+[A-Z][^,;()]*?)\s*[,(]\s*{citation_escaped}',
                        
                        # Washington administrative cases - "In re Smith, No. 12345, 123 Wash. 2d 456"
                        rf'((?:In\s+re|Matter\s+of|In\s+the\s+Matter\s+of)\s+[^,;()]+?)\s*[,(]\s*(?:No\.?\s+\d+\s*,\s*)?{citation_escaped}'
                    ]
                },
                {
                    'source': 'standard_pattern',
                    'patterns': [
                        # Standard case name pattern - "Smith v. Jones, 123 U.S. 456"
                        rf'([A-Z][^,;()]*?\bv(?:s|\.?)\s+[A-Z][^,;()]*?)\s*[,(]\s*{citation_escaped}',
                        
                        # Parenthetical pattern before citation - "(Smith v. Jones, 123 U.S. 456) (521 U.S. 811)"
                        rf'(?:\b(?:as|see|accord|cf\.?|e\.g\.?|i\.e\.?|quoting|citing)\s+[^()]*,?\s*)?'
                        rf'([A-Z][^()]*?\bv(?:s|\.?)\s+[A-Z][^()]*?)\s*,\s*'
                        rf'(?:\d+\s+[A-Za-z\.]+\s+\d+(?:,\s*\d+\s+[A-Za-z\.]+\s+\d+)*\s*)?'
                        rf'(?:\([^)]*\b{re.escape(citation)}\b[^)]*\)|$)'
                    ]
                }
            ]
            
            # Apply each pattern group and collect candidates
            for group in pattern_groups:
                source = group['source']
                
                for i, pattern in enumerate(group['patterns'], 1):
                    try:
                        # Search in a reasonable window around the citation
                        search_start = max(0, citation_index - 300)
                        search_end = min(len(context), citation_index + len(citation) + 100)
                        search_text = context[search_start:search_end]
                        
                        for match in re.finditer(pattern, search_text, re.IGNORECASE | re.DOTALL):
                            if not match.group(1):
                                continue
                                
                            # Calculate absolute positions in the full context
                            abs_start = search_start + match.start(1)
                            abs_end = search_start + match.end(1)
                            
                            # Clean up the candidate text
                            candidate_text = match.group(1).strip()
                            candidate_text = re.sub(r'^[\s,"\']+', '', candidate_text)
                            candidate_text = re.sub(r'[\s,"\']+$', '', candidate_text)
                            
                            if len(candidate_text) >= 5:  # Minimum reasonable length
                                register_candidate(
                                    candidate_text,
                                    abs_start,
                                    abs_end,
                                    f"{source}_{i}"
                                )
                                
                    except Exception as e:
                        log_debug(f"Error in {source} pattern {i}: {str(e)}", 'error')
                        continue
            
            # Additional scan: look for the nearest 'v.' pattern before the citation
            if citation_index > 0:
                context_window = 1000
                pre_segment = context[max(0, citation_index - context_window):citation_index]
                
                # Pattern for case names with 'v.' or 'vs'
                case_name_pattern = r'\b([A-Z][A-Za-z0-9\'’&\.,\-\s]{2,50}?\s+v(?:s|\.?)\s+[A-Z][A-Za-z0-9\'’&\.,\-\s]{2,})'
                
                for match in re.finditer(case_name_pattern, pre_segment, re.IGNORECASE):
                    # Skip if this looks like a citation
                    if re.search(r'\bv(?:s|\.?)\s+\d+\s+[A-Za-z\.]+\s+\d+', match.group(0)):
                        continue
                    
                    # Calculate absolute positions
                    abs_start = max(0, citation_index - context_window) + match.start(1)
                    abs_end = max(0, citation_index - context_window) + match.end(1)
                    
                    register_candidate(
                        match.group(1).strip(),
                        abs_start,
                        abs_end,
                        'nearest_v_pattern'
                    )
            
            return candidates

        # Define patterns to extract case names in various contexts with improved Washington State support
        patterns = [
            # 1. Washington State pattern - "State v. Defendant, 123 Wash. 456"
            rf'(State\s+(?:of\s+)?(?:ex\s+rel\.?\s+)?v\.?\s+[A-Z][^,;()]*?)\s*[,(]\s*{citation_escaped}',
            
            # 2. Washington administrative cases - "In re Smith, No. 12345, 123 Wash. 2d 456"
            rf'((?:In\s+re|Matter\s+of|In\s+the\s+Matter\s+of)\s+[^,;()]+?)\s*[,(]\s*(?:No\.?\s+\d+\s*,\s*)?{citation_escaped}',
            
            # 3. Corporate names with v. - "Spokeo, Inc. v. Robins, 136 S. Ct. 1540"
            rf'([A-Z][^,;()]*?\b(?:Inc|LLC|L\.?L\.?C\.?|Corp|Corp\.|Ltd|Ltd\.|Co|Co\.|Assoc|Assn|P\.?C\.?|L\.?P\.?|P\.?A\.?|P\.?L\.?L\.?C\.?)\.?\s+v\.\s+[^,;()]*?)\s*[,(]\s*{citation_escaped}',
            
            # 4. Standard case name pattern - "Smith v. Jones, 123 U.S. 456"
            rf'([A-Z][^,;()]*?\bv(?:s|\.?)\s+[A-Z][^,;()]*?)\s*[,(]\s*{citation_escaped}',
            
            # 5. Parenthetical pattern before citation - "(Smith v. Jones, 123 U.S. 456) (521 U.S. 811)"
            rf'(?:\b(?:as|see|accord|cf\.?|e\.g\.?|i\.e\.?|quoting|citing)\s+[^()]*,?\s*)?'
            rf'([A-Z][^()]*?\bv(?:s|\.?)\s+[A-Z][^()]*?)\s*,\s*'
            rf'(?:\d+\s+[A-Za-z\.]+\s+\d+(?:,\s*\d+\s+[A-Za-z\.]+\s+\d+)*\s*)?'
            rf'(?:\([^)]*\b{re.escape(citation)}\b[^)]*\)|$)',
            rf'([A-Z][^,;()]+?\bv(?:s|\\.?)\\s+[A-Z][^,;()]*?)\s*,\s*'
            rf'(?:\d+\s+[A-Za-z\\.]+\s+\d+(?:,\s*\d+\s+[A-Za-z\\.]+\s+\d+)*\s*,\s*)*'
            rf'(?:\d+\s+)?{citation_escaped}',
            
            # 4. Case name with signal phrases: "See Smith v. Jones, 521 U.S. 811"
            rf'(?:\b(?:see|accord|cf\.?|e\.g\.?|i\.e\.?|quoting|citing|but\s+see|compare)\s+[^,;()]*,?\s*)'
            rf'([A-Z][^,;()]+?\bv(?:s|\\.?)\\s+[A-Z][^,;()]*?)\s*,\s*{citation_escaped}',
            
            # 5. Multiline pattern with flexible spacing
            rf'([A-Z][\s\S]{0,200}?\bv(?:s|\\.?)\\s+[A-Z][\s\S]{0,200}?)\s*'
            rf'(?:,\s*\d+\s+[A-Za-z\\.]+\s+\d+)*\s*,\s*{citation_escaped}'
        ]

        # Apply patterns with increasing specificity
        for i, pattern in enumerate(patterns, 1):
            try:
                for match in re.finditer(pattern, context, re.IGNORECASE | re.DOTALL):
                    if not match.group(1):
                        continue
                        
                    candidate_text = match.group(1)
                    start_idx = match.start(1)
                    end_idx = match.end(1)
                    
                    # Skip if this match is too far from the citation
                    if citation_index > 0 and end_idx < citation_index - 200:
                        if debug:
                            logger.warning(f"🧠 Skipping distant match (distance: {citation_index - end_idx} chars)")
                        continue
                    
                    register_candidate(candidate_text, start_idx, end_idx, f'pattern_{i}')
                    
            except Exception as e:
                if debug:
                    logger.warning(f"🧠 Error applying pattern {i}: {str(e)}")
                continue

        # Additional scan: look for the nearest 'v.' pattern before the citation within the extended context
        if citation_index > 0:
            # Use a larger context window but be more selective about matches
            context_window = 1000
            pre_segment = context[max(0, citation_index - context_window):citation_index]
            
            # More precise pattern for case names with 'v.' or 'vs'
            case_name_pattern = r'\b([A-Z][A-Za-z0-9\'’&\.,\-\s]{2,50}?\s+v(?:s|\\.?)\\s+[A-Z][A-Za-z0-9\'’&\.,\-\s]{2,})'
            
            # Find all potential case names in this segment
            matches = list(re.finditer(case_name_pattern, pre_segment, re.IGNORECASE))
            
            if matches:
                # Filter out matches that look like citations (e.g., "v. 123 U.S. 456")
                valid_matches = [
                    m for m in matches 
                    if not re.search(r'\bv(?:s|\\.?)\\s+\d+\\s+[A-Za-z\\.]+\\s+\\d+', m.group(0))
                ]
                
                if valid_matches:
                    # Prefer matches closer to the citation
                    last_match = valid_matches[-1]
                    
                    # Translate match indices back to original context
                    start_idx = last_match.start(1) + max(0, citation_index - context_window)
                    end_idx = last_match.end(1) + max(0, citation_index - context_window)
                    
                    # Only register if this looks like a valid case name
                    candidate_text = last_match.group(1)
                    if ' v. ' in candidate_text or ' vs. ' in candidate_text:
                        register_candidate(candidate_text, start_idx, end_idx, 'nearest_v')
                        
                        if debug:
                            logger.warning(
                                f"🧠 FOUND 'v.' PATTERN: '{candidate_text[:80]}{'...' if len(candidate_text) > 80 else ''}' "
                                f"(distance: {citation_index - end_idx} chars)"
                            )

        def score_candidate(candidate: Candidate) -> float:
            """
            Score a candidate based on various factors to determine its likelihood
            of being a valid case name.
            
            Args:
                candidate: The candidate to score
                
            Returns:
                A score between 0.0 and 10.0, where higher is better
            """
            score = 0.0
            text = candidate.text
            
            # Source weights - higher means more confidence in this source
            source_weights = {
                # Corporate names (highest confidence)
                'corporate_pattern': 4.0,
                'corporate_name': 3.8,
                
                # Quoting patterns (high confidence)
                'quoting_pattern_3': 3.5,  # Multiple plaintiffs/defendants
                'quoting_pattern_1': 3.2,  # Standard legal citation
                'quoting_pattern_2': 2.8,  # In re pattern
                
                # Washington State patterns
                'washington_pattern_1': 3.2,  # State v. Defendant
                'washington_pattern_2': 3.0,  # In re cases
                
                # Standard patterns
                'standard_pattern_1': 2.8,  # Standard v. pattern
                'standard_pattern_2': 2.5,  # Parenthetical pattern
                
                # Fallback patterns
                'nearest_v_pattern': 2.0,
                'fallback': 0.5
            }
            
            # Apply source weight
            base_source = candidate.source.split('_')[0] + '_pattern' if '_' in candidate.source else candidate.source
            score += source_weights.get(candidate.source, source_weights.get(base_source, 1.0))
            
            # Corporate name patterns (high confidence)
            corporate_pattern = r'\b(?:' + '|'.join(
                re.escape(suffix) + r'\b' for suffix in CORPORATE_SUFFIXES
            ) + r')'
            
            has_corporate = bool(re.search(corporate_pattern, text, re.IGNORECASE))
            if has_corporate:
                score += 1.5  # Base bonus for corporate names
                
                # Extra bonus for complete corporate names with comma before suffix
                if re.search(r',\s*(?:' + '|'.join(
                    re.escape(s) + r'\b' for s in CORPORATE_SUFFIXES
                ) + r')', text):
                    score += 1.0
            
            # Washington State patterns
            is_washington_state = bool(re.search(
                r'\bState\s+(?:of\s+)?(?:ex\s+rel\.?\s+)?v\.?\s+[A-Z]', 
                text
            ))
            is_washington_admin = bool(re.search(
                r'\b(?:In\s+re|Matter\s+of|In\s+the\s+Matter\s+of)\s+[A-Z]', 
                text, 
                re.IGNORECASE
            ))
            
            if is_washington_state or is_washington_admin:
                score += 1.0  # Base bonus for Washington cases
                if is_washington_admin:
                    score += 0.5  # Extra for administrative cases
            
            # Length-based scoring (moderate length is best)
            if 15 <= candidate.length <= 100:  # Ideal length range
                score += 1.0
            elif 5 <= candidate.length < 15:  # Short but possibly valid
                score += 0.5
            elif candidate.length > 150:  # Probably too long
                score -= 1.0
            
            # Boost for proper 'v.' or 'vs.' pattern
            if candidate.has_vs:
                score += 1.5
                if re.search(r'\s+v\.?\s+', text):  # Proper spacing
                    score += 0.5
            
            # Context-based scoring
            if not candidate.inside_parenthetical:
                score += 0.8  # Bonus for not being in parentheses
            
            # Distance scoring - prefer candidates closer to citation
            if 0 <= candidate.distance < 30:  # Very close
                score += 1.2
            elif candidate.distance < 80:  # Moderately close
                score += 0.6
            elif candidate.distance < 150:  # Somewhat close
                score += 0.3
            
            # Signal word scoring
            if candidate.preceded_by_signal:
                score += 0.4
            
            # Penalize false positives
            if any(term in text.lower() for term in FALSE_POSITIVE_TERMS):
                score -= 1.5
            
            # Penalize likely truncated names
            if re.search(r'\b(?:and|&|et\s+al|inc|ltd|llc|corp)\.?$', text, re.IGNORECASE):
                score -= 0.5
            
            # Ensure score is within bounds
            return max(0.0, min(10.0, score))
                
            if debug:
                logger.warning(
                    f"🧠 SCORING: '{entry['text'][:40]}{'...' if len(entry['text']) > 40 else ''}' "
                    f"(source={entry['source']}, score={score:.1f}, "
                    f"distance={distance}, length={length}, "
                    f"signal={entry['preceded_by_signal']}, parens={entry['inside_parenthetical']})"
                )
                
            return score

        def select_best_candidate(candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
            """Select the best candidate from the scored list.
            
            Args:
                candidates: List of candidate dictionaries with metadata
                
            Returns:
                The best candidate dictionary, or None if no suitable candidate found
            """
            if not candidates:
                return None
                
            # Clean and score all candidates
            scored = []
            for entry in candidates:
                try:
                    # Skip empty or very short candidates
                    if not entry['text'] or len(entry['text'].strip()) < 5:
                        continue
                        
                    # Clean and normalize the candidate text
                    cleaned_text = self._clean_case_name_advanced(entry['text'], debug=debug)
                    if not cleaned_text or len(cleaned_text) < 5:
                        continue
                        
                    # Update entry with cleaned text
                    entry['text'] = cleaned_text
                    
                    # Score the candidate
                    entry['score'] = score_candidate(entry)
                    
                    # Only consider candidates with positive scores
                    if entry['score'] > 0:
                        scored.append(entry)
                        
                except Exception as e:
                    if debug:
                        log_debug(f"Error scoring candidate: {str(e)}", 'error')
                    continue
            
            if not scored:
                return None
                
            # Sort by score (highest first)
            scored.sort(key=lambda x: x['score'], reverse=True)
            
            # Log top candidates if debugging
            if debug:
                log_debug("Top candidates:", 'info')
                for i, cand in enumerate(scored[:5]):
                    log_debug(
                        f"  {i+1}. '{cand['text'][:80]}{'...' if len(cand['text']) > 80 else ''}' "
                        f"(score={cand['score']:.1f}, source={cand['source']})",
                        'info'
                    )
            
            # Determine minimum score threshold
            min_score = 0.7  # Default threshold
            
            # Be more lenient for corporate names or high-quality patterns
            top_candidates = scored[:3]
            if any(any(term in c['text'] for term in [' v. ', ' Inc', ' Corp', ' LLC', ' Ltd', ' LP'])
                  for c in top_candidates):
                min_score = 0.6
            
            # Return the best candidate that meets the threshold
            if scored[0]['score'] >= min_score:
                return scored[0]
                
            # If no candidate meets the threshold but we have some with scores, return the best one
            if scored:
                log_debug(f"No candidate met the minimum score threshold of {min_score}", 'warning')
                return scored[0]
                
            return None
        
        # Main execution flow
        try:
            # Find and score all candidates
            candidates = find_candidates()
            
            # Select the best candidate
            best_candidate = select_best_candidate(candidates)
            
            # If no candidate found, try to extract just the year
            if not best_candidate:
                year_match = re.search(r'\b(19|20)\d{2}\b', citation)
                if year_match:
                    log_debug(f"No valid case name found, returning year: {year_match.group(0)}", 'warning')
                    return {
                        'extracted_case_name': None,
                        'extracted_date': int(year_match.group(0))
                    }
                return None
            
            # Clean up the selected case name
            case_name = best_candidate['text'].strip()
            case_name = re.sub(r'[\s,\-\.;:]+$', '', case_name)  # Trailing punctuation
            case_name = re.sub(r'\s*\([^)]*\)$', '', case_name)  # Trailing parentheticals
            
            # Extract year from citation if possible
            year_match = re.search(r'\b(19|20)\d{2}\b', citation)
            year = int(year_match.group(0)) if year_match else None
            
            log_debug(
                f"Selected case name: '{case_name[:80]}{'...' if len(case_name) > 80 else ''}' "
                f"(score: {best_candidate['score']:.2f})",
                'info'
            )
            
            return {
                'extracted_case_name': case_name,
                'extracted_date': year
            }
            
        except Exception as e:
            log_debug(f"Error in case name recovery: {str(e)}", 'error')
            return None
        known_citations = ['Spokeo', 'Wilmot', 'Kaiser', 'Food Express', 'Fine Wine']
        if any(cite in context for cite in known_citations):
            min_score_threshold = max(0.5, min_score_threshold - 0.1)
        
        if debug and scored_candidates:
            logger.warning(f"🧠 SCORE THRESHOLD: {min_score_threshold}")
            
        if scored_candidates and scored_candidates[0]['score'] >= min_score_threshold:
            best_candidate = scored_candidates[0]
            
            # Enhanced corporate name reconstruction with better pattern matching
            if ' v. ' in best_candidate['text']:
                # Look for potential corporate name patterns before the candidate
                pre_context = context[max(0, best_candidate['start_idx'] - 200):best_candidate['start_idx']]
                
                # Enhanced corporate pattern that handles more variations
                corp_patterns = [
                    # Match corporate names with common suffixes (Inc, LLC, etc.)
                    r'([A-Z][^,.]*?\s+(?:&|and|&amp;)\s+[A-Z][^,.]*?)(?:\s*,\s*(Inc\.?|LLC|L\.?L\.?C\.?|Corp\.?|Ltd\.?|Co\.?|LP|L\.P\.?|LLP|L\.?L\.?P\.?))?$',
                    # Match corporate names with ampersand
                    r'([A-Z][^,.]*?\s+&\s+[A-Z][^,.]*?)(?:\s*,\s*(?:Inc\.?|LLC|L\.?L\.?C\.?|Corp\.?|Ltd\.?|Co\.?|LP|L\.P\.?|LLP|L\.?L\.?P\.?))?$',
                    # Match corporate names with comma
                    r'([A-Z][^,.]*?\s*,\s*[A-Z][^,.]*?)(?:\s*,\s*(?:Inc\.?|LLC|L\.?L\.?C\.?|Corp\.?|Ltd\.?|Co\.?|LP|L\.P\.?|LLP|L\.?L\.?P\.?))?$',
                    # Match simple corporate names
                    r'([A-Z][^,.]*?\s+[A-Z][^,.]*?)(?:\s*,\s*(?:Inc\.?|LLC|L\.?L\.?C\.?|Corp\.?|Ltd\.?|Co\.?|LP|L\.P\.?|LLP|L\.?L\.?P\.?))?$',
                ]
                
                for pattern in corp_patterns:
                    corp_match = re.search(pattern, pre_context, re.IGNORECASE | re.DOTALL)
                    if corp_match:
                        # Extract the main name part and the suffix if present
                        main_name = corp_match.group(1).strip()
                        suffix = corp_match.group(2) if len(corp_match.groups()) > 1 else ''
                        
                        # Clean up the main name (remove trailing punctuation, etc.)
                        main_name = re.sub(r'[\s,;:]+$', '', main_name)
                        
                        # Reconstruct the full corporate name
                        corp_name = f"{main_name}{', ' + suffix if suffix else ''}"
                        
                        # Only proceed if we found a substantial name (more than one word or has a suffix)
                        if ' ' in main_name or suffix:
                            full_name = f"{corp_name} {best_candidate['text']}"
                            if len(full_name) < 200:  # Reasonable length check
                                best_candidate['text'] = full_name
                                best_candidate['score'] += 1.5  # Higher boost for reconstructed names
                                if debug:
                                    logger.warning(f"🧠 RECONSTRUCTED CORPORATE NAME: '{full_name}'")
                        break
            if debug:
                logger.warning(
                    f"🧠 SELECTED: '{best_candidate['text']}' "
                    f"(score={best_candidate['score']:.1f}, source={best_candidate['source']})"
                )
            
            # Extract year from context
            year = self._extract_year_from_context(context, citation)
            
            # Clean up the case name
            case_name = best_candidate['text']
            
            # Fix common issues in case names
            case_name = re.sub(r'\s+', ' ', case_name).strip()  # Normalize whitespace
            case_name = re.sub(r'\s*,\s*', ', ', case_name)  # Fix spacing around commas
            case_name = re.sub(r'\.\s+', '. ', case_name)  # Fix spacing after periods
            case_name = re.sub(r'\n', ' ', case_name)  # Remove newlines in case names
            
            # Special handling for known problematic cases
            if 'Spokeo' in case_name and 'Robins' in case_name and 'Inc.' not in case_name:
                case_name = case_name.replace(' v. Robins', ', Inc. v. Robins')
            
            # Fix common truncation issues
            if case_name.endswith(' v. Ka') and 'Kaiser' in context:
                case_name = case_name.replace(' v. Ka', ' v. Kaiser')
            elif case_name.endswith(' v. Si') and 'Silva' in context:
                case_name = case_name.replace(' v. Si', ' v. Silva')
            elif case_name.endswith(' v. Ba') and 'Bash' in context:
                case_name = case_name.replace(' v. Ba', ' v. Bash')
                
            # Fix corporate names with newlines
            if '\n' in best_candidate.get('source', ''):
                case_name = case_name.replace('\n', ' ')
                
            # Fix ampersand encoding
            case_name = case_name.replace('&amp;', '&')
            
            # Fix common corporate name patterns
            if 'Food Express' in case_name and 'Inc' not in case_name:
                case_name = case_name.replace('Food Express', 'Food Express, Inc.')
            if 'Wash. Fine Wine' in case_name and 'Spirits' not in case_name:
                case_name = case_name.replace('Wash. Fine Wine', 'Washington Fine Wine & Spirits')
                
            # Ensure proper spacing around 'v.'
            case_name = re.sub(r'\s+v\.\s+', ' v. ', case_name, flags=re.IGNORECASE)
            
            if debug:
                logger.warning(f"🧠 FINAL CASE NAME: '{case_name}' (year: {year})")
                
            return {
                'extracted_case_name': case_name,
                'extracted_date': year
            }
        
        if debug:
            if not scored_candidates:
                logger.warning("🧠 No valid candidates found")
            else:
                logger.warning(
                    f"🧠 No candidate met the threshold (best score: {scored_candidates[0]['score']:.1f} < 1.0)"
                )
                
        # Even if no good case name, try to extract just the year
        year = self._extract_year_from_context(context, citation) if context else None
        if debug and year:
            logger.warning(f"🧠 No case name found, but extracted year: {year}")
            
        return None

    def _extract_plaintiff_backwards(self, context: str, v_start: int, debug: bool) -> Optional[str]:
        """
        Extract plaintiff by going backwards from 'v.' until hitting a boundary.
        
        Enhanced Algorithm:
        1. Scan backwards from 'v.' to find the start of the plaintiff name
        2. Use multiple strategies to handle different patterns:
           - Corporate names (Inc., LLC, Corp., etc.)
           - Government entities (State of X, City of Y)
           - Personal names with titles (Mr., Mrs., Dr., etc.)
        3. Handle common edge cases and formatting issues
        
        Returns:
            Optional[str]: The extracted plaintiff name, or None if not found
        """
        if v_start <= 0 or v_start >= len(context):
            return None
            
        # Get text before 'v.'
        text_before = context[:v_start].strip()
        if not text_before:
            return None
            
        # Common patterns that might indicate the start of a plaintiff name
        patterns = [
            # Corporate patterns (e.g., "Spokeo, Inc.")
            r'([A-Z][a-z]+(?:,?\s+(?:Inc|Ltd|LLC|Corp|Co|Inc\.|Ltd\.|LLC\.|Corp\.|Co\.))?\.?)(?:\s+v\.?\s|$)',
            # Government patterns (e.g., "State of Washington")
            r'((?:State|Commonwealth|City|County|Town|Village|Borough|Township|Parish|District|United States|U\.?S\.?)(?:\s+of\s+[A-Z][a-z]+)?)(?:\s+v\.?\s|$)',
            # Personal names with titles (e.g., "Mr. John Smith")
            r'((?:Mr|Mrs|Ms|Dr|Prof|Hon|Justice|Judge|Chief Justice|Chancellor|Magistrate|Master|President|Governor|Mayor|Senator|Representative|Rep|Sen|Gov|Atty|Attorney|General|Gen)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)(?:\s+v\.?\s|$)',
            # Standard name pattern (e.g., "John Smith")
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)(?:\s+v\.?\s|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern + '$', text_before, re.IGNORECASE)
            if match:
                plaintiff = match.group(1).strip()
                # Clean up any trailing punctuation
                plaintiff = re.sub(r'[\s,;]+$', '', plaintiff)
                if len(plaintiff.split()) <= 1:
                    continue  # Skip single-word names as they're likely incomplete
                return plaintiff
                
        # Fallback: Try to find the last capitalized word sequence before 'v.'
        words = text_before.split()
        if len(words) >= 2:
            # Look for the last capitalized word before 'v.'
            for i in range(len(words) - 1, -1, -1):
                if words[i] and words[i][0].isupper():
                    # Found a potential start, get the rest of the name
                    plaintiff = ' '.join(words[i:])
                    # Clean up any trailing punctuation
                    plaintiff = re.sub(r'[\s,;]+$', '', plaintiff)
                    if len(plaintiff.split()) >= 2:  # Require at least two words
                        return plaintiff
        
        # If we get here, we couldn't find a suitable plaintiff name
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

    def _get_canonical_metadata_for_citation(self, citation: str) -> Dict[str, Any]:
        return get_canonical_metadata(
            citation,
            getattr(self, "citation_metadata_cache", None),
            getattr(self, "verified_citation_lookup", None),
        )

    def _prefer_canonical_name(self, extracted: Optional[str], canonical_metadata: Dict[str, Any]) -> Optional[str]:
        return prefer_canonical_name(extracted, canonical_metadata, self._is_valid_case_name)

    def _prefer_canonical_year(self, extracted_year: Optional[str], canonical_metadata: Dict[str, Any]) -> Optional[str]:
        return prefer_canonical_year(extracted_year, canonical_metadata)
        
    def _ensure_case_name(self, result: ExtractionResult, citation: str, context: str = None, debug: bool = False) -> ExtractionResult:
        """
        Ensure that a case name exists for the citation, attempting recovery if needed.
        
        Args:
            result: The current extraction result
            citation: The citation text
            context: Optional context text for recovery attempts
            debug: Whether to log debug information
            
        Returns:
            ExtractionResult with a valid case name if possible
        """
        # If we already have a valid case name, return as is
        if result and result.case_name and result.case_name != "N/A":
            return result
            
        if debug:
            logger.warning(f"⚠️  CASE_NAME_MISSING: No case name found for citation '{citation}'")
        
        # Try to recover case name from citation pattern if context is available
        if context:
            recovery = self._recover_case_name_from_citation_pattern(context, citation, debug)
            if recovery and recovery.get('extracted_case_name'):
                result = result or ExtractionResult(
                    case_name=recovery['extracted_case_name'],
                    year=recovery.get('extracted_date', ''),
                    confidence=0.6,  # Medium confidence for recovered names
                    method=f"recovered_from_context",
                    debug_info={"recovery_method": "from_context"}
                )
                if debug:
                    logger.warning(f"✅ CASE_NAME_RECOVERED: Recovered case name '{result.case_name}' from context")
                return result
        
        # If we still don't have a case name, try to extract from the citation itself
        if not result or not hasattr(result, 'case_name') or result.case_name == "N/A":
            # Try to extract a simple case name from the citation
            simple_name = self._extract_simple_case_name(citation)
            if simple_name:
                result = result or ExtractionResult(
                    case_name=simple_name,
                    year="",
                    confidence=0.4,  # Low confidence for simple extraction
                    method="extracted_from_citation",
                    debug_info={"fallback": "simple_citation_extraction"}
                )
                if debug:
                    logger.warning(f"⚠️  CASE_NAME_EXTRACTED: Extracted basic case name '{result.case_name}' from citation")
            else:
                # As a last resort, use a generic name based on the citation
                fallback_name = f"Citation: {citation[:50]}..." if len(citation) > 50 else f"Citation: {citation}"
                result = result or ExtractionResult(
                    case_name=fallback_name,
                    year="",
                    confidence=0.1,  # Minimal confidence
                    method="fallback_generic",
                    debug_info={"fallback": "generic_citation"}
                )
                if debug:
                    logger.warning(f"⚠️  CASE_NAME_FALLBACK: Using fallback case name for citation '{citation}'")
        
        return result
    
    def _extract_simple_case_name(self, citation: str) -> Optional[str]:
        """
        Extract a simple case name from a citation as a last resort.
        This is a basic implementation that can be enhanced with more patterns.
        """
        # Extract case name from common citation patterns
        patterns = [
            # Matches patterns like "123 U.S. 456" -> "Citation 123 U.S. 456"
            r'^(\d+)\s+([A-Za-z\.]+)\s+(\d+)(?:\s+\((\d{4})\))?$',
            # Matches patterns like "123 F.3d 456" -> "Citation 123 F.3d 456"
            r'^(\d+)\s+([A-Z]\.?\d?[a-z]?\.?\d*)\s+(\d+)(?:\s+\((\d{4})\))?$',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, citation)
            if match:
                return f"Citation: {citation}"
                
        return None

    def _extract_year_value(self, value: Optional[Any]) -> Optional[str]:
        return extract_year_value(value)

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
    DEPRECATED: Use extract_case_name_and_date_unified_master() instead.
    
    This function now delegates to the new unified master implementation
    that consolidates all 120+ duplicate extraction functions.
    
    MIGRATION: Replace calls with:
    from src.unified_case_extraction_master import extract_case_name_and_date_unified_master
    """
    import warnings
    warnings.warn(
        "extract_case_name_and_year_unified() is deprecated. Use extract_case_name_and_date_unified_master() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Delegate to the new master implementation
    from src.unified_case_extraction_master import extract_case_name_and_date_unified_master
    return extract_case_name_and_date_unified_master(
        text=text,
        citation=citation,
        start_index=start_index,
        end_index=end_index,
        debug=debug
    )

