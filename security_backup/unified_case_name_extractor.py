"""
Unified Case Name Extractor - Best of All Worlds
Combines the best features from all existing extraction systems into one unified, high-quality extractor.
This replaces all other case name extraction functions to ensure consistency and quality.
"""

import re
import logging
import time
from typing import Dict, Optional, Tuple, List, Any
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ExtractionResult:
    """Structured result for case name and date extraction"""
    case_name: str = ""
    date: str = ""
    year: str = ""
    confidence: float = 0.0
    method: str = "unknown"
    debug_info: Optional[Dict[str, Any]] = None

class UnifiedCaseNameExtractor:
    """
    Unified Case Name Extractor - Best of All Worlds
    
    Combines features from:
    - case_name_extraction_core.py: Advanced patterns, confidence scoring
    - websearch/extractor.py: Context window handling, validation
    - standalone_citation_parser.py: Precise boundary detection
    - unified_citation_processor_v2.py: Sentence boundary detection
    
    This is the ONE extraction function that should be used throughout the codebase.
    """
    
    def __init__(self):
        # Initialize compiled patterns
        self.compiled_patterns = []
        self._setup_patterns()
        self._setup_transitional_phrases()
        self._setup_stopwords()
        
        # Initialize cache
        self._cache = {}
        self._max_cache_size = 1000  # Maximum number of entries to cache
    
    def _setup_patterns(self):
        """Initialize comprehensive extraction patterns from all systems"""
        # Initialize case patterns and compile them
        self.case_patterns = [
            # High confidence patterns - Standard adversarial cases
            {
                'name': 'standard_v_precise',
                'pattern': r'([A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?)\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?)(?=\s*,\s*\d|\s*\(|$)',
                'confidence_base': 0.95,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}"
            },
            {
                'name': 'standard_vs',
                'pattern': r'([A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?)\s+vs\.\s+([A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?)(?=\s*,\s*\d|\s*\(|$)',
                'confidence_base': 0.9,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}"
            },
            {
                'name': 'standard_versus',
                'pattern': r'([A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?)\s+versus\s+([A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?)(?=\s*,\s*\d|\s*\(|$)',
                'confidence_base': 0.85,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}"
            },
            # Government/institutional cases
            {
                'name': 'state_v',
                'pattern': r'(State\s+(?:of\s+)?[A-Za-z\s]*)\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?)(?=\s*,\s*\d|\s*\(|$)',
                'confidence_base': 0.95,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}"
            },
            {
                'name': 'us_v',
                'pattern': r'(United\s+States(?:\s+of\s+America)?)\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?)(?=\s*,\s*\d|\s*\(|$)',
                'confidence_base': 0.95,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}"
            },
            # Special case types
            {
                'name': 'in_re',
                'pattern': r'(In\s+re\s+[A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?)(?=\s*,\s*\d|\s*\(|$)',
                'confidence_base': 0.9,
                'format': lambda m: m.group(1).strip()
            },
            {
                'name': 'estate_of',
                'pattern': r'(Estate\s+of\s+[A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?)(?=\s*,\s*\d|\s*\(|$)',
                'confidence_base': 0.9,
                'format': lambda m: m.group(1).strip()
            },
            {
                'name': 'matter_of',
                'pattern': r'(Matter\s+of\s+[A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?)(?=\s*,\s*\d|\s*\(|$)',
                'confidence_base': 0.9,
                'format': lambda m: m.group(1).strip()
            },
            # Department cases
            {
                'name': 'dept_v',
                'pattern': r'(Dep\'t\s+of\s+[A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=\s*,\s*\d|\s*\(|$)',
                'confidence_base': 0.9,
                'format': lambda m: m.group(1).strip()
            }
        ]
        
        # Compile date patterns for better performance
        self.date_patterns = [
            (r'\((\d{4})\)', 0.9),  # (2022)
            (r',\s*(\d{4})\s*(?=[A-Z]|$)', 0.8),  # , 2022
            (r'(\d{4})-\d{1,2}-\d{1,2}', 0.7),  # 2022-01-15
            (r'\d{1,2}/\d{1,2}/(\d{4})', 0.6),  # 01/15/2022
            (r'\b(19|20)\d{2}\b', 0.4),  # Simple 4-digit year
        ]
    
    def _setup_transitional_phrases(self):
        """Setup transitional phrases that should be filtered out"""
        self.transitional_phrases = [
            # Signal words and transitional phrases
            'in', 'see', 'see also', 'cf.', 'e.g.,', 'accord', 'but see', 'further',
            'similarly', 'additionally', 'moreover', 'furthermore', 'however',
            'nevertheless', 'nonetheless', 'therefore', 'thus', 'consequently',
            'accordingly', 'hence', 'meanwhile', 'subsequently', 'previously',
            'earlier', 'later', 'finally', 'ultimately', 'indeed', 'notably',
            'particularly', 'specifically', 'generally', 'typically', 'usually',
            # Legal transitional phrases
            'the court in', 'in the case of', 'as stated in', 'as held in',
            'as explained in', 'as recognized in', 'as noted in', 'as discussed in',
            'as decided in', 'as ruled in', 'as found in', 'as determined in',
            # Sentence fragments that shouldn't start case names
            'federal rules of evidence intend to protect against',
            'wyoming case law reinforces these principles',
            'this principle is supported by',
            'the reasoning in',
            'consistent with',
            'in accordance with'
        ]
    
    def _setup_stopwords(self):
        """Setup stopwords for filtering"""
        self.stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'must', 'shall', 'this', 'that',
            'these', 'those', 'it', 'its', 'they', 'them', 'their', 'there'
        }
    
    def extract_case_name_and_date(self, text: str, citation: Optional[str] = None, 
                                   citation_start: Optional[int] = None, 
                                   citation_end: Optional[int] = None) -> ExtractionResult:
        """
        Main extraction method - combines all best practices
        
        Args:
            text: Full document text
            citation: Citation text to search for (optional)
            citation_start: Start index of citation in text (optional)
            citation_end: End index of citation in text (optional)
            
        Returns:
            ExtractionResult with case name, date, and metadata
        """
        try:
            # Determine citation boundaries
            if citation_start is None or citation_end is None:
                if citation:
                    citation_start = text.find(citation)
                    if citation_start != -1:
                        citation_end = citation_start + len(citation)
                    else:
                        return ExtractionResult(method="citation_not_found")
                else:
                    return ExtractionResult(method="no_citation_provided")
            
            # Get optimized context for extraction
            context = self._get_extraction_context(text, citation_start, citation_end)
            
            # Extract case name using multiple strategies
            case_name, confidence, method = self._extract_case_name_unified(context, citation)
            
            # Extract date/year
            date, year = self._extract_date_unified(text, citation_start, citation_end)
            
            return ExtractionResult(
                case_name=case_name or "",
                date=date or "",
                year=year or "",
                confidence=confidence,
                method=method,
                debug_info={
                    'context_length': len(context),
                    'citation_start': citation_start,
                    'citation_end': citation_end
                }
            )
            
        except Exception as e:
            logger.error(f"Error in unified case name extraction: {e}")
            return ExtractionResult(method="error", debug_info={'error': str(e)})
    
    def _get_extraction_context(self, text: str, citation_start: int, citation_end: int) -> str:
        """
        Get optimized context for extraction using best practices from all systems
        """
        # Use larger context window to ensure we capture full case names
        base_window = 300
        max_window = 500
        
        # Start with a generous context window
        context_start = max(0, citation_start - base_window)
        
        # Look for case name patterns to ensure we don't cut them off
        case_name_pattern = re.compile(r'\b[A-Z][A-Za-z0-9&.,\'\s\-]+\s+v\.\s+[A-Z][A-Za-z0-9&.,\'\s\-]+')
        
        # Find potential case names in the context window
        potential_context = text[context_start:citation_start]
        case_matches = list(case_name_pattern.finditer(potential_context))
        
        if case_matches:
            # Start from the beginning of the last case name found
            last_case_start = case_matches[-1].start()
            context_start = context_start + last_case_start
        else:
            # Look for sentence boundaries, but be more conservative
            sentence_pattern = re.compile(r'[.!?]\s+[A-Z]')
            sentence_matches = list(sentence_pattern.finditer(text, context_start, citation_start))
            if sentence_matches and len(sentence_matches) > 1:
                # Use the second-to-last sentence boundary to avoid cutting off case names
                context_start = sentence_matches[-2].start() + 1
            elif sentence_matches:
                # If only one sentence boundary, check if it's far enough back
                boundary_pos = sentence_matches[-1].start() + 1
                if citation_start - boundary_pos > 50:  # Ensure at least 50 chars for case name
                    context_start = boundary_pos
        
        # Ensure we don't go too far back
        context_start = max(context_start, citation_start - max_window)
        
        # Context ends at citation start
        context = text[context_start:citation_start].strip()
        
        return context
    
    def _extract_case_name_unified(self, context: str, citation: Optional[str] = None) -> Tuple[Optional[str], float, str]:
        """
        Unified case name extraction using all best practices
        """
        if not context:
            return None, 0.0, "no_context"
        
        # Optimized context size for better performance
        MAX_CONTEXT_SIZE = 300  # Further reduced from 500 to 300 characters
        if len(context) > MAX_CONTEXT_SIZE:
            # Take the last 300 characters (closest to citation)
            context = context[-MAX_CONTEXT_SIZE:]
            logger.debug(f"[PERFORMANCE] Truncated context to {MAX_CONTEXT_SIZE} characters")
        
        # Check cache first with a more efficient key
        cache_key = f"{hash(context)}_{citation or ''}"
        if cache_key in self._cache:
            cached_result = self._cache[cache_key]
            logger.debug("[CACHE_HIT] Found cached result for context")
            return cached_result

        # Strategy 1: Pattern matching with confidence scoring
        best_case_name = None
        best_confidence = 0.0
        best_method = "none"
        
        # Quick check for case indicators (v., vs., v )
        has_case_indicators = ' v' in context or 'vs.' in context
        
        # Pre-compile common patterns once
        if not hasattr(self, '_common_patterns_compiled'):
            self._common_patterns_compiled = {
                'v.': re.compile(r'\bv\.', re.IGNORECASE),
                'vs.': re.compile(r'\bvs\.', re.IGNORECASE),
                ' v ': re.compile(r'\sv\s', re.IGNORECASE)
            }
        
        # Check for case indicators using pre-compiled patterns
        has_case_indicators = any(
            pattern.search(context) 
            for pattern in self._common_patterns_compiled.values()
        )
        
        # Pre-filter patterns that are likely to match
        patterns_to_use = []
        for pattern_info in self.case_patterns:
            # Skip patterns that require case indicators if none found
            if not has_case_indicators and not pattern_info.get('always_check', False):
                continue
                
            # Skip patterns that are too specific for this context
            if 'required_text' in pattern_info and pattern_info['required_text'] not in context:
                continue
                
            patterns_to_use.append(pattern_info)
            
            # Limit number of patterns to try for performance
            if len(patterns_to_use) >= 3:  # Reduced from 5 to 3
                break
        
        logger.debug(f"[PERF] Using {len(patterns_to_use)} patterns for matching")
        
        # Add a timeout for the entire matching process
        start_time = time.time()
        MAX_MATCH_TIME = 1.0  # 1 second max per pattern match
        
        for pattern_info in patterns_to_use:
            # Check if we're taking too long
            if time.time() - start_time > 5.0:  # 5 seconds total max
                logger.warning("[PERF] Exceeded max match time, breaking early")
                break
                
            pattern = pattern_info['pattern']
            confidence_base = pattern_info['confidence_base']
            format_func = pattern_info['format']
            method_name = pattern_info['name']
            
            try:
                # Get or compile the pattern
                compiled_pattern = None
                for cp in self.compiled_patterns:
                    if cp['name'] == method_name:
                        compiled_pattern = cp['compiled']
                        break
                
                if not compiled_pattern:
                    # Compile with a timeout
                    pattern_start_time = time.time()
                    compiled_pattern = re.compile(pattern, re.IGNORECASE)
                    self.compiled_patterns.append({
                        'name': method_name,
                        'compiled': compiled_pattern
                    })
                
                # Execute with timeout
                match_start_time = time.time()
                try:
                    match = compiled_pattern.search(context)
                    match_time = time.time() - match_start_time
                    
                    if match_time > 0.1:  # Log slow matches
                        logger.debug(f"[PERF] Pattern '{method_name}' took {match_time:.3f}s")
                    
                    if match:
                        # Format and clean the matched case name
                        raw_case_name = format_func(match)
                        clean_case_name = self._clean_case_name_unified(raw_case_name, context)
                        
                        if clean_case_name and self._validate_case_name_unified(clean_case_name):
                            # Calculate confidence based on position and quality
                            position_bonus = 0.1 if match.start() > len(context) * 0.7 else 0.0
                            quality_bonus = self._calculate_quality_bonus(clean_case_name)
                            final_confidence = min(1.0, confidence_base + position_bonus + quality_bonus)
                            
                            if final_confidence > best_confidence:
                                best_case_name = clean_case_name
                                best_confidence = final_confidence
                                best_method = method_name
                                
                                # Early exit if we have a high confidence match
                                if best_confidence >= 0.9:
                                    break
                except Exception as e:
                    logger.error(f"[ERROR] Pattern '{method_name}' matching failed: {e}")
                    continue
                
                if match:
                    matches = [match]
                    
                    # Add to cache if we found a match
                    if len(self._cache) < self._max_cache_size:
                        self._cache[cache_key] = (best_case_name, best_confidence, best_method)
                
            except Exception as e:
                logger.warning(f"[REGEX_ERROR] Pattern '{method_name}' failed: {e}")
                continue
            if matches:
                # Take the last (closest to citation) match
                match = matches[-1]
                raw_case_name = format_func(match)
                
                # Clean and validate
                clean_case_name = self._clean_case_name_unified(raw_case_name, context)
                if clean_case_name and self._validate_case_name_unified(clean_case_name):
                    # Calculate confidence based on position and quality
                    position_bonus = 0.1 if match.start() > len(context) * 0.7 else 0.0
                    quality_bonus = self._calculate_quality_bonus(clean_case_name)
                    final_confidence = min(1.0, confidence_base + position_bonus + quality_bonus)
                    
                    if final_confidence > best_confidence:
                        best_case_name = clean_case_name
                        best_confidence = final_confidence
                        best_method = method_name
        
        # Strategy 2: Fallback extraction for edge cases (only if no good match found)
        if not best_case_name or best_confidence < 0.7:  # Increased threshold from 0.5 to 0.7
            try:
                fallback_name, fallback_confidence = self._extract_fallback_case_name(context)
                if fallback_confidence > best_confidence:
                    best_case_name = fallback_name
                    best_confidence = fallback_confidence
                    best_method = "fallback"
                    
                    # Cache the fallback result
                    if len(self._cache) < self._max_cache_size:
                        self._cache[cache_key] = (best_case_name, best_confidence, best_method)
            except Exception as e:
                logger.warning(f"[FALLBACK_ERROR] Fallback extraction failed: {e}")
        
        return best_case_name, best_confidence, best_method
    
    def _clean_case_name_unified(self, case_name: str, context: str) -> Optional[str]:
        """
        Unified case name cleaning combining all best practices
        """
        if not case_name:
            return None
        
        # Basic cleanup
        case_name = case_name.strip()
        case_name = re.sub(r'\s+', ' ', case_name)  # Normalize whitespace
        case_name = re.sub(r'[,;\.]\s*$', '', case_name)  # Remove trailing punctuation
        
        # Remove transitional phrases from the beginning
        case_name_lower = case_name.lower()
        for phrase in self.transitional_phrases:
            if case_name_lower.startswith(phrase.lower()):
                # Remove the phrase and any following punctuation/whitespace
                remaining = case_name[len(phrase):].strip(' .,;:')
                if remaining and remaining[0].isupper():
                    case_name = remaining
                    break
        
        # Remove sentence fragments before case name
        # Look for patterns like "Text. Case Name v. Defendant"
        sentence_split = re.search(r'[.!?]\s*([A-Z][^.!?]*(?:v\.|vs\.|versus|In re|Estate of|Matter of)[^.!?]*)', case_name)
        if sentence_split:
            case_name = sentence_split.group(1).strip()
        
        # NEW: Extract just the case name part if we have context text
        # Look for "Case Name v. Defendant" pattern within the extracted text
        case_name_match = re.search(r'([A-Z][A-Za-z\s,\.\'-]+?)\s+v\.\s+([A-Za-z\s,\.\'-]+?)(?=\s*,|\s*$)', case_name)
        if case_name_match:
            plaintiff = case_name_match.group(1).strip()
            defendant = case_name_match.group(2).strip()
            case_name = f"{plaintiff} v. {defendant}"
        
        # Remove leading context phrases that might remain
        context_phrases = [
            'another important case is', 'the court decided in', 'this landmark case',
            'as held in', 'as stated in', 'in the case of', 'the case of',
            'decided in', 'ruled in', 'held in', 'found in'
        ]
        
        case_name_lower = case_name.lower()
        for phrase in context_phrases:
            if case_name_lower.startswith(phrase):
                remaining = case_name[len(phrase):].strip(' .,;:')
                if remaining and remaining[0].isupper():
                    case_name = remaining
                    break
        
        # Remove citation patterns that might be included
        case_name = re.sub(r',?\s*\d+\s+[A-Za-z.]+(?:\s+\d+)*.*$', '', case_name)
        case_name = re.sub(r'\(\d{4}\).*$', '', case_name)
        
        # Final cleanup
        case_name = case_name.strip(' .,;:')
        
        return case_name if case_name else None
    
    def _validate_case_name_unified(self, case_name: str) -> bool:
        """
        Unified validation combining all best practices
        """
        if not case_name:
            return False
        
        # Length validation
        if len(case_name) < 5 or len(case_name) > 200:
            return False
        
        # Must start with capital letter
        if not case_name[0].isupper():
            return False
        
        # Must contain legal case indicators
        case_lower = case_name.lower()
        if not any(indicator in case_lower for indicator in [
            'v.', 'vs.', 'versus', 'in re', 'estate of', 'matter of'
        ]):
            return False
        
        # Must contain at least one alphabetic character
        if not re.search(r'[A-Za-z]', case_name):
            return False
        
        # Should not look like a citation
        if re.match(r'^\d+\s+[A-Z]', case_name):
            return False
        
        # Should not be mostly stopwords
        words = re.findall(r'\b\w+\b', case_name.lower())
        if len(words) > 2:
            stopword_ratio = sum(1 for word in words if word in self.stopwords) / len(words)
            if stopword_ratio > 0.6:
                return False
        
        return True
    
    def _calculate_quality_bonus(self, case_name: str) -> float:
        """Calculate quality bonus based on case name characteristics"""
        bonus = 0.0
        
        # Bonus for proper case structure
        if re.search(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+v\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$', case_name):
            bonus += 0.1
        
        # Bonus for government cases
        if re.search(r'^(State|United States|U\.S\.|People)\s+v\.', case_name, re.IGNORECASE):
            bonus += 0.05
        
        # Penalty for very long names (likely includes extra text)
        if len(case_name) > 100:
            bonus -= 0.1
        
        return bonus
    
    def _extract_fallback_case_name(self, context: str) -> Tuple[Optional[str], float]:
        """
        Fallback extraction for edge cases
        """
        # Look for any "v." pattern in the last part of context
        recent_context = context[-150:] if len(context) > 150 else context
        
        # Simple v. pattern
        match = re.search(r'([A-Z][A-Za-z\s,\.\'-]+?)\s+v\.\s+([A-Za-z\s,\.\'-]+?)(?=\s|$)', recent_context)
        if match:
            case_name = f"{match.group(1).strip()} v. {match.group(2).strip()}"
            case_name = self._clean_case_name_unified(case_name, context)
            if case_name and self._validate_case_name_unified(case_name):
                return case_name, 0.3  # Low confidence fallback
        
        return None, 0.0
    
    def _extract_date_unified(self, text: str, citation_start: int, citation_end: int) -> Tuple[Optional[str], Optional[str]]:
        """
        Unified date extraction using best practices from all systems
        """
        # Look in context after citation (within 50 characters)
        context_end = min(len(text), citation_end + 50)
        context = text[citation_end:context_end]
        
        # Try patterns in order of confidence
        for pattern, confidence in self.date_patterns:
            match = re.search(pattern, context)
            if match:
                if pattern.endswith(r'\b'):
                    year = match.group(0)
                else:
                    year = match.group(1)
                
                # Validate year
                if self._validate_year(year):
                    return year, year
        
        return None, None
    
    def _validate_year(self, year: str) -> bool:
        """Validate that year is reasonable for legal documents"""
        try:
            year_int = int(year)
            current_year = datetime.now().year
            return 1600 <= year_int <= current_year + 1
        except ValueError:
            return False

# Global instance for easy access
_unified_extractor = None

def get_unified_extractor() -> UnifiedCaseNameExtractor:
    """Get global unified extractor instance"""
    global _unified_extractor
    if _unified_extractor is None:
        _unified_extractor = UnifiedCaseNameExtractor()
    return _unified_extractor

# Main API functions - these replace ALL other extraction functions
def extract_case_name_and_date_unified(text: str, citation: Optional[str] = None, 
                                      citation_start: Optional[int] = None, 
                                      citation_end: Optional[int] = None) -> Dict[str, Any]:
    """
    UNIFIED extraction function - replaces all others
    
    This is the ONE function that should be used throughout the codebase.
    """
    extractor = get_unified_extractor()
    result = extractor.extract_case_name_and_date(text, citation, citation_start, citation_end)
    
    return {
        'case_name': result.case_name,
        'date': result.date,
        'year': result.year,
        'confidence': result.confidence,
        'method': result.method,
        'debug_info': result.debug_info
    }

def extract_case_name_only_unified(text: str, citation: Optional[str] = None, 
                                  citation_start: Optional[int] = None, 
                                  citation_end: Optional[int] = None) -> str:
    """Extract just the case name using unified logic"""
    result = extract_case_name_and_date_unified(text, citation, citation_start, citation_end)
    return result.get('case_name', '')

def extract_year_only_unified(text: str, citation: Optional[str] = None, 
                             citation_start: Optional[int] = None, 
                             citation_end: Optional[int] = None) -> str:
    """Extract just the year using unified logic"""
    result = extract_case_name_and_date_unified(text, citation, citation_start, citation_end)
    return result.get('year', '')

# Backward compatibility functions (DEPRECATED - use unified functions above)
def extract_case_name_and_date(text: str, citation: Optional[str] = None) -> Dict[str, Any]:
    """DEPRECATED: Use extract_case_name_and_date_unified instead"""
    logger.warning("extract_case_name_and_date is DEPRECATED. Use extract_case_name_and_date_unified instead.")
    return extract_case_name_and_date_unified(text, citation)

def extract_case_name_only(text: str, citation: Optional[str] = None) -> str:
    """DEPRECATED: Use extract_case_name_only_unified instead"""
    logger.warning("extract_case_name_only is DEPRECATED. Use extract_case_name_only_unified instead.")
    return extract_case_name_only_unified(text, citation)

def extract_year_only(text: str, citation: Optional[str] = None) -> str:
    """DEPRECATED: Use extract_year_only_unified instead"""
    logger.warning("extract_year_only is DEPRECATED. Use extract_year_only_unified instead.")
    return extract_year_only_unified(text, citation)
