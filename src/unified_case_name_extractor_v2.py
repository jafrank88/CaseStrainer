"""
Unified Case Name Extractor V2 - The One True Extractor
=======================================================

This module consolidates ALL case name extraction logic from 47+ existing functions
into ONE comprehensive, high-quality extraction function.

ANALYSIS OF EXISTING FUNCTIONS:
==============================

1. PROBLEMS IDENTIFIED:
   - 47+ different extraction functions doing similar work
   - Inconsistent regex patterns causing case name truncation exact same codepunctuationass that to the 
   
   - Multiple extraction attempts overriding each other
   - Performance issues from redundant processing
   - Maintenance nightmare with scattered logic

2. BEST PATTERNS FOUND:
   - Standard v. pattern: r'([A-Z][A-Za-z0-9&.\'\\s-]+(?:\\s+[A-Za-z0-9&.\'\\s-]+)*?)\\s+v\\.\\s+([A-Z][A-Za-z0-9&.\'\\s-]+(?:\\s+[A-Za-z0-9&.\'\\s-]+)*?)(?=\\s*,|\\s*\\(|$)'
   - Context window: 800-1000 characters for comprehensive coverage
   - Multi-strategy approach: volume-based, context-based, pattern-based
   - Confidence scoring and validation

3. IMPROVEMENTS IMPLEMENTED:
   - Single extraction function with configurable strategies
   - Consistent regex patterns across all extraction methods
   - Intelligent context window sizing
   - Comprehensive validation and cleaning
   - Performance optimizations with caching
   - Detailed debugging and logging
"""

import re
from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

import logging
import time
from typing import Dict, Optional, Tuple, List, Any, Union
from dataclasses import dataclass, field
from enum import Enum

try:
    import os
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'extractor_debug.log')
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file)
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized successfully to {log_file}")
    
except Exception as e:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    logger.warning(f"File logging failed ({e}), using basic logging instead")

class ExtractionStrategy(Enum):
    """Available extraction strategies"""
    VOLUME_BASED = "volume_based"
    CONTEXT_BASED = "context_based"
    PATTERN_BASED = "pattern_based"
    GLOBAL_SEARCH = "global_search"
    FALLBACK = "fallback"

@dataclass
class ExtractionResult:
    """Comprehensive result for case name extraction"""
    case_name: str = ""
    date: str = ""
    year: str = ""
    confidence: float = 0.0
    method: str = "unknown"
    strategy: ExtractionStrategy = ExtractionStrategy.FALLBACK
    extraction_time: float = 0.0
    debug_info: Dict[str, Any] = field(default_factory=dict)
    raw_matches: Optional[List[str]] = None
    validation_errors: Optional[List[str]] = None

class UnifiedCaseNameExtractorV2:
    """
    DEPRECATED: Use extract_case_name_and_date_master() instead.
    
    This class is deprecated and will be removed in v3.0.0.
    Use extract_case_name_and_date_master() for consistent extraction results.
    
    The ONE and ONLY case name extraction function that should be used.
    
    This consolidates all the best practices from:
    - case_name_extraction_core.py (47+ functions)
    - unified_case_name_extractor.py
    - enhanced_sync_processor.py
    - enhanced_clustering.py
    - unified_citation_processor_v2.py
    - standalone_citation_parser.py
    - citation_extractor.py
    - And all other extraction functions
    
    FEATURES:
    - Single extraction function with multiple strategies
    - Consistent regex patterns (no more truncation!)
    - Intelligent context window sizing
    - Comprehensive validation
    - Performance optimizations
    - Detailed debugging
    """
    
    def __init__(self, enable_cache: bool = False, max_cache_size: int = 1000):  # Disable cache temporarily
        self.enable_cache = enable_cache
        self._cache = {} if enable_cache else {}
        self._max_cache_size = max_cache_size
        self._setup_patterns()
        self._setup_validation_rules()
        
    def _setup_patterns(self):
        """Initialize improved regex patterns that avoid over-matching"""
        self.patterns = [
            {
                'name': 'reverse_lookup_v_precise',
                'pattern': r'(?:^|[.!?]\s+|;\s+)([A-Z][a-zA-Z\'\.\&\s]+?)\s+v\.\s+([A-Z][a-zA-Z\'\.\&\s]+?)(?:\s*,)?$',
                'confidence': 0.99,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}",
                'description': 'Precise case name pattern with flexible character support'
            },
            {
                'name': 'reverse_lookup_word_boundary',
                'pattern': r'\b([A-Z][a-zA-Z\'\.\&\s]+?)\s+v\.\s+([A-Z][a-zA-Z\'\.\&\s]+?)(?:\s*,)?$',
                'confidence': 0.98,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}",
                'description': 'Word-boundary aware flexible case name pattern'
            },
            {
                'name': 'reverse_lookup_with_entities',
                'pattern': r'\b([A-Z][a-zA-Z\'\.\&\s]+?)\s+v\.\s+([A-Z][a-zA-Z\'\.\&\s]+?)(?:\s*,)?$',
                'confidence': 0.97,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}",
                'description': 'Flexible case name pattern supporting all entity types'
            },
            {
                'name': 'bounded_v_pattern',
                'pattern': r'([A-Z][a-zA-Z\'\.\&\s]+?)\s+v\.\s+([A-Z][a-zA-Z\'\.\&\s]+?)',
                'confidence': 0.97,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}",
                'description': 'Flexible Party v. Party pattern'
            },
            {
                'name': 'word_bounded_v',
                'pattern': r'\b([A-Z][a-zA-Z\'\.\&\s]+?)\s+v\.\s+([A-Z][a-zA-Z\'\.\&\s]+?)\b',
                'confidence': 0.96,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}",
                'description': 'Word-bounded flexible case name pattern'
            },
            {
                'name': 'standard_vs_bounded',
                'pattern': r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+[A-Z][a-z]+\.)*)\s+vs\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+[A-Z][a-z]+\.)*)',
                'confidence': 0.95,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}",
                'description': 'Capitalized words only Party vs. Party pattern'
            },
            {
                'name': 'standard_versus_bounded',
                'pattern': r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+[A-Z][a-z]+\.)*)\s+versus\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+[A-Z][a-z]+\.)*)',
                'confidence': 0.95,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}",
                'description': 'Capitalized words only Party versus Party pattern'
            },
            
            {
                'name': 'state_v_bounded',
                'pattern': r'(State(?:\s+of\s+[A-Z][a-z]+)?)\s+v\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                'confidence': 0.98,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}",
                'description': 'Capitalized words only State v. Party pattern'
            },
            {
                'name': 'us_v_bounded',
                'pattern': r'(United\s+States(?:\s+of\s+America)?)\s+v\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                'confidence': 0.98,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}",
                'description': 'Capitalized words only United States v. Party pattern'
            },
            {
                'name': 'people_v_bounded',
                'pattern': r'(People(?:\s+of\s+(?:the\s+)?State\s+of\s+[A-Z][a-z]+)?)\s+v\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                'confidence': 0.95,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}",
                'description': 'Capitalized words only People v. Party pattern'
            },
            
            {
                'name': 'in_re_bounded',
                'pattern': r'(In\s+re\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                'confidence': 0.95,
                'format': lambda m: m.group(1).strip(),
                'description': 'Capitalized words only In re cases'
            },
            {
                'name': 'estate_of_bounded',
                'pattern': r'(Estate\s+of\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                'confidence': 0.95,
                'format': lambda m: m.group(1).strip(),
                'description': 'Capitalized words only Estate of cases'
            },
            {
                'name': 'matter_of_bounded',
                'pattern': r'(Matter\s+of\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                'confidence': 0.95,
                'format': lambda m: m.group(1).strip(),
                'description': 'Capitalized words only Matter of cases'
            },
            {
                'name': 'ex_parte_bounded',
                'pattern': r'(Ex\s+parte\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                'confidence': 0.90,
                'format': lambda m: m.group(1).strip(),
                'description': 'Capitalized words only Ex parte cases'
            },
            
            {
                'name': 'llc_v_bounded',
                'pattern': r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:LLC|Inc|Corp|Co|Ltd))\s+v\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                'confidence': 0.90,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}",
                'description': 'Capitalized words only LLC/Corp v. Party pattern'
            },
            
            {
                'name': 'fallback_v_short',
                'pattern': r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+v\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})',
                'confidence': 0.70,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}",
                'description': 'Short fallback Party v. Party pattern - capitalized words only'
            },
            {
                'name': 'fallback_in_re_short',
                'pattern': r'(In\s+re\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})',
                'confidence': 0.70,
                'format': lambda m: m.group(1).strip(),
                'description': 'Short fallback In re pattern - capitalized words only'
            }
        ]
        
        for pattern_info in self.patterns:
            pattern_info['compiled'] = re.compile(pattern_info['pattern'], re.IGNORECASE)
    
    def _setup_validation_rules(self):
        """Setup comprehensive validation rules"""
        self.validation_rules = {
            'min_length': 5,
            'max_length': 200,
            'required_indicators': ['v.', 'vs.', 'versus', 'In re', 'Estate of', 'Matter of', 'Ex parte'],
            'forbidden_patterns': [
                r'^\d+',  # Starts with number
                r'[A-Z]{3,}',  # All caps (likely acronym)
                r'^\s*[.,;:]',  # Starts with punctuation
                r'\s*[.,;:]\s*$',  # Ends with punctuation
            ],
            'citation_indicators': [
                r'\d+\s+[A-Z]+\s+\d+',  # Volume Reporter Page
                r'[A-Z]+\s+\d+',  # Reporter Page
                r'\(\d{4}\)',  # Year in parentheses
            ]
        }
    
    def extract_case_name_and_date(
        self, 
        text: str, 
        citation: Optional[str] = None,
        citation_start: Optional[int] = None,
        citation_end: Optional[int] = None,
        strategies: Optional[List[ExtractionStrategy]] = None,
        debug: bool = False
    ) -> ExtractionResult:
        """
        THE ONE AND ONLY case name extraction function.
        
        This replaces ALL 47+ existing extraction functions with one comprehensive,
        high-quality extraction function that uses the best practices from all systems.
        
        Args:
            text: Full document text
            citation: Citation text to search for (optional)
            citation_start: Start index of citation in text (optional)
            citation_end: End index of citation in text (optional)
            strategies: List of extraction strategies to try (default: all)
            debug: Enable detailed debugging output
            
        Returns:
            ExtractionResult with comprehensive extraction data
        """
        start_time = time.time()
        
        if debug:
            logger.info(f"[UNIFIED_EXTRACTOR] Starting extraction for citation: {citation}")
            logger.info(f"[UNIFIED_EXTRACTOR] Text length: {len(text)} characters")
        
        result = ExtractionResult(
            debug_info={
                'extraction_time': 0.0,
                'strategies_tried': [],
                'context_windows': {},
                'pattern_matches': [],
                'validation_results': []
            }
        )
        
        try:
            normalized_text = text.replace('\n', ' ').replace('\r', ' ')
            normalized_text = normalized_text.replace('\u2019', "'")
            normalized_text = re.sub(r'\s+', ' ', normalized_text).strip()
            
            if citation_start is None or citation_end is None:
                if citation:
                    citation_start = normalized_text.find(citation)
                    if citation_start != -1:
                        citation_end = citation_start + len(citation)
                        text = normalized_text
                    else:
                        result.method = "citation_not_found"
                        result.debug_info['error'] = "Citation not found in text (even after normalizing newlines)"
                        return result
                else:
                    result.method = "no_citation_provided"
                    result.debug_info['error'] = "No citation provided"
                    return result
            
            if strategies is None:
                strategies = [
                    ExtractionStrategy.CONTEXT_BASED,     # First: context-based (better proximity)
                    ExtractionStrategy.VOLUME_BASED,      # Second: volume-based (fallback)
                    ExtractionStrategy.PATTERN_BASED,     # Third: pattern-based (last resort)
                    ExtractionStrategy.GLOBAL_SEARCH,
                    ExtractionStrategy.FALLBACK
                ]
            
            for strategy in strategies:
                if debug:
                    logger.info(f"[UNIFIED_EXTRACTOR] Trying strategy: {strategy.value}")
                
                result.debug_info['strategies_tried'].append(strategy.value)
                
                if strategy == ExtractionStrategy.VOLUME_BASED:
                    extraction_result = self._extract_volume_based(text, citation or "", citation_start, citation_end, debug)
                elif strategy == ExtractionStrategy.CONTEXT_BASED:
                    extraction_result = self._extract_context_based(text, citation or "", citation_start, citation_end, debug)
                elif strategy == ExtractionStrategy.PATTERN_BASED:
                    extraction_result = self._extract_pattern_based(text, citation or "", citation_start, citation_end, debug)
                elif strategy == ExtractionStrategy.GLOBAL_SEARCH:
                    extraction_result = self._extract_global_search(text, citation or "", debug)
                else:  # FALLBACK
                    extraction_result = self._extract_fallback(text, citation or "", debug)
                
                if extraction_result and extraction_result.case_name:
                    result.case_name = extraction_result.case_name
                    result.date = extraction_result.date or ""
                    result.year = extraction_result.year or ""
                    result.confidence = extraction_result.confidence
                    result.method = extraction_result.method
                    result.strategy = strategy
                    result.raw_matches = extraction_result.raw_matches
                    
                    if debug:
                        logger.info(f" [UNIFIED_EXTRACTOR] Strategy {strategy.value} succeeded: '{result.case_name}' (confidence: {result.confidence})")
                    
                    break
                else:
                    if debug:
                        logger.info(f" [UNIFIED_EXTRACTOR] Strategy {strategy.value} failed")
            
            validation_result = self._validate_case_name(result.case_name, text, citation or "")
            result.validation_errors = validation_result.get('errors', [])
            result.debug_info['validation_results'].append(validation_result)
            
            if result.validation_errors:
                result.confidence *= 0.8  # Reduce confidence for validation issues
            
            if result.case_name and not result.date:
                date_result = self._extract_date_from_case_context(text, result.case_name, citation_start, citation_end)
                result.date = date_result.get('date', '')
                result.year = date_result.get('year', '')
            
            result.extraction_time = time.time() - start_time
            result.debug_info['extraction_time'] = result.extraction_time
            
            if debug:
                logger.info(f" [UNIFIED_EXTRACTOR] Final result: '{result.case_name}' (confidence: {result.confidence:.2f}, method: {result.method})")
                logger.info(f"⏱ [UNIFIED_EXTRACTOR] Extraction completed in {result.extraction_time:.3f}s")
            
            return result
            
        except Exception as e:
            logger.error(f" [UNIFIED_EXTRACTOR] Error in extraction: {e}")
            result.method = "error"
            result.debug_info['error'] = str(e)
            return result
    
    def _extract_volume_based(self, text: str, citation: str, citation_start: int, citation_end: int, debug: bool) -> Optional[ExtractionResult]:
        """Volume-based extraction: look backwards from citation volume number with improved reverse lookup"""
        try:
            volume_match = re.search(r'(\d+)', citation)
            if not volume_match:
                return None
            
            volume_number = volume_match.group(1)
            volume_pos = citation.find(volume_number)
            if volume_pos == -1:
                return None
            
            volume_text_pos = citation_start + volume_pos
            
            lookback_start = max(0, volume_text_pos - 100)
            before_text = text[lookback_start:volume_text_pos].strip()
            
            if debug:
                pass  # Debug logging can be added here if needed
            
            reverse_patterns = [p for p in self.patterns if 'reverse_lookup' in p['name']]
            for pattern_info in reverse_patterns:
                match = pattern_info['compiled'].search(before_text)
                if match:
                    case_name = pattern_info['format'](match)
                    confidence = pattern_info['confidence'] * 1.2  # Boost for volume-based extraction
                    
                    if debug:
                        pass  # Debug logging can be added here if needed
                    
                    return ExtractionResult(
                        case_name=case_name,
                        confidence=min(confidence, 1.0),
                        method=f"volume_based_{pattern_info['name']}",
                        strategy=ExtractionStrategy.VOLUME_BASED,
                        raw_matches=[case_name]
                    )
            
            for pattern_info in self.patterns:
                if pattern_info['confidence'] < 0.8 or 'reverse_lookup' in pattern_info['name']:
                    continue
                
                match = pattern_info['compiled'].search(before_text)
                if match:
                    case_name = pattern_info['format'](match)
                    confidence = pattern_info['confidence']
                    
                    match_pos = match.start()
                    distance = len(before_text) - match_pos  # Distance from citation
                    
                    if distance < 50:
                        confidence *= 1.3  # 30% boost for very close matches
                    elif distance < 100:
                        confidence *= 1.1  # 10% boost for close matches
                    
                    return ExtractionResult(
                        case_name=case_name,
                        confidence=min(confidence, 1.0),
                        method=f"volume_based_{pattern_info['name']}",
                        strategy=ExtractionStrategy.VOLUME_BASED,
                        raw_matches=[case_name]
                    )
            
            if debug:
                pass  # Debug logging can be added here if needed
            return None
            
        except Exception as e:
            if debug:
                pass  # Debug logging can be added here if needed
            return None
    
    def _extract_context_based(self, text: str, citation: str, citation_start: int, citation_end: int, debug: bool) -> Optional[ExtractionResult]:
        """Context-based extraction: use optimized context window around citation"""
        try:
            context_start = max(0, citation_start - 200)
            context_end = min(len(text), citation_end + 50)
            context = text[context_start:context_end]
            
            best_match = None
            best_confidence = 0.0
            best_pattern = None
            
            for pattern_info in self.patterns:
                match = pattern_info['compiled'].search(context)
                if match:
                    case_name = pattern_info['format'](match)
                    confidence = pattern_info['confidence']
                    
                    match_pos = match.start()
                    citation_pos = citation_start - context_start
                    distance = abs(match_pos - citation_pos)
                    
                    if distance < 100:
                        confidence *= 1.5  # 50% boost for very close matches
                    elif distance < 200:
                        confidence *= 1.3  # 30% boost for close matches
                    elif distance < 300:
                        confidence *= 1.1  # 10% boost for medium matches
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = case_name
                        best_pattern = pattern_info['name']
            
            if best_match:
                return ExtractionResult(
                    case_name=best_match,
                    confidence=min(best_confidence, 1.0),
                    method=f"context_based_{best_pattern}",
                    strategy=ExtractionStrategy.CONTEXT_BASED,
                    raw_matches=[best_match]
                )
            
            return None
            
        except Exception as e:
            if debug:
                pass  # Debug logging can be added here if needed
            return None
    
    def _extract_pattern_based(self, text: str, citation: str, citation_start: int, citation_end: int, debug: bool) -> Optional[ExtractionResult]:
        """Pattern-based extraction: use citation boundaries and pattern matching"""
        try:
            search_start = max(0, citation_start - 400)
            search_end = min(len(text), citation_end + 100)
            search_text = text[search_start:search_end]
            
            for pattern_info in self.patterns:
                if pattern_info['confidence'] < 0.7:  # Skip very low confidence patterns
                    continue
                
                matches = list(pattern_info['compiled'].finditer(search_text))
                if matches:
                    citation_pos = citation_start - search_start
                    best_match = None
                    best_distance = float('inf')
                    
                    for match in matches:
                        distance = abs(match.start() - citation_pos)
                        if distance < best_distance:
                            best_distance = distance
                            best_match = match
                    
                    if best_match:
                        case_name = pattern_info['format'](best_match)
                        
                        return ExtractionResult(
                            case_name=case_name,
                            confidence=pattern_info['confidence'],
                            method=f"pattern_based_{pattern_info['name']}",
                            strategy=ExtractionStrategy.PATTERN_BASED,
                            raw_matches=[case_name]
                        )
            
            return None
            
        except Exception as e:
            if debug:
                logger.error(f"Pattern-based extraction failed: {e}")
            return None
    
    def _extract_global_search(self, text: str, citation: str, debug: bool) -> Optional[ExtractionResult]:
        """Global search: search entire text for case name patterns"""
        try:
            for pattern_info in self.patterns:
                if pattern_info['confidence'] < 0.8:  # Only high-confidence patterns
                    continue
                
                matches = list(pattern_info['compiled'].finditer(text))
                if matches:
                    case_name = pattern_info['format'](matches[0])
                    
                    return ExtractionResult(
                        case_name=case_name,
                        confidence=pattern_info['confidence'] * 0.9,  # Slightly reduce confidence for global search
                        method=f"global_search_{pattern_info['name']}",
                        strategy=ExtractionStrategy.GLOBAL_SEARCH,
                        raw_matches=[case_name]
                    )
            
            return None
            
        except Exception as e:
            if debug:
                logger.error(f"Global search extraction failed: {e}")
            return None
    
    def _extract_fallback(self, text: str, citation: str, debug: bool) -> Optional[ExtractionResult]:
        """Fallback extraction: use basic patterns and heuristics"""
        try:
            for pattern_info in self.patterns:
                if pattern_info['confidence'] >= 0.7:  # Only basic patterns
                    continue
                
                match = pattern_info['compiled'].search(text)
                if match:
                    case_name = pattern_info['format'](match)
                    
                    return ExtractionResult(
                        case_name=case_name,
                        confidence=pattern_info['confidence'] * 0.8,  # Reduce confidence for fallback
                        method=f"fallback_{pattern_info['name']}",
                        strategy=ExtractionStrategy.FALLBACK,
                        raw_matches=[case_name]
                    )
            
            return None
            
        except Exception as e:
            if debug:
                logger.error(f"Fallback extraction failed: {e}")
            return None
    
    def _validate_case_name(self, case_name: str, text: str, citation: str) -> Dict[str, Any]:
        """Comprehensive validation of extracted case name"""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'score': 1.0
        }
        
        if not case_name:
            validation_result['is_valid'] = False
            validation_result['errors'].append("Empty case name")
            validation_result['score'] = 0.0
            return validation_result
        
        if len(case_name) < self.validation_rules['min_length']:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Case name too short: {len(case_name)} characters")
            validation_result['score'] *= 0.5
        
        if len(case_name) > self.validation_rules['max_length']:
            validation_result['warnings'].append(f"Case name very long: {len(case_name)} characters")
            validation_result['score'] *= 0.8
        
        has_required_indicator = any(indicator.lower() in case_name.lower() for indicator in self.validation_rules['required_indicators'])
        if not has_required_indicator:
            validation_result['warnings'].append("No required case indicators found")
            validation_result['score'] *= 0.7
        
        for pattern in self.validation_rules['forbidden_patterns']:
            if re.search(pattern, case_name):
                validation_result['errors'].append(f"Forbidden pattern found: {pattern}")
                validation_result['score'] *= 0.3
        
        for pattern in self.validation_rules['citation_indicators']:
            if re.search(pattern, case_name):
                validation_result['errors'].append(f"Citation pattern found in case name: {pattern}")
                validation_result['score'] *= 0.2
        
        if validation_result['score'] < 0.5:
            validation_result['is_valid'] = False
        
        return validation_result
    
    def _clean_case_name_result(self, match) -> str:
        """Clean and format case name result to remove extra text while preserving name structure"""
        if not match or len(match.groups()) < 2:
            return ""
            
        plaintiff = self._clean_party_name(match.group(1))
        defendant = self._clean_party_name(match.group(2))
        
        contamination_phrases = [
            r'\b(de\s+novo)\b', r'\b(questions?\s+of\s+law)\b', r'\b(statutory\s+interpretation)\b',
            r'\b(in\s+light\s+of)\b', r'\b(the\s+record\s+certified)\b', r'\b(federal\s+court)\b',
            r'\b(this\s+court\s+reviews?)\b', r'\b(we\s+review)\b', r'\b(certified\s+questions?)\b',
            r'\b(issue\s+of\s+law)\b', r'\b(also\s+an?\s+issue)\b'
        ]
        
        for phrase_pattern in contamination_phrases:
            plaintiff = re.sub(phrase_pattern, '', plaintiff, flags=re.IGNORECASE)
            defendant = re.sub(phrase_pattern, '', defendant, flags=re.IGNORECASE)
        
        plaintiff = re.sub(r'\s+', ' ', plaintiff).strip()
        defendant = re.sub(r'\s+', ' ', defendant).strip()
        
        plaintiff = self._extract_last_case_name_part(plaintiff)
        defendant = self._extract_last_case_name_part(defendant)
        
        for prefix in ['De', 'La', 'Van', 'Von', 'Mc', 'Mac', "O'"]:
            plaintiff = re.sub(f'({prefix})\\s+([A-Z])', f'{prefix}\\2', plaintiff, flags=re.IGNORECASE)
            defendant = re.sub(f'({prefix})\\s+([A-Z])', f'{prefix}\\2', defendant, flags=re.IGNORECASE)
        
        for prefix in ['De', 'La', 'Van', 'Von', 'Mc', 'Mac', "O'"]:
            pattern = re.compile(f'(?<=\b)({prefix})([a-z])', re.IGNORECASE)
            plaintiff = pattern.sub(lambda m: f'{m.group(1).capitalize()}{m.group(2).lower()}', plaintiff)
            defendant = pattern.sub(lambda m: f'{m.group(1).capitalize()}{m.group(2).lower()}', defendant)
        
        result = f"{plaintiff} v. {defendant}"
        
        if len(result) < 5 or not (' v. ' in result):
            return ""
            
        return result
    
    def _extract_last_case_name_part(self, text: str) -> str:
        """Extract the last part of text that looks like a case name"""
        if not text:
            return ""
        
        patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)\s+v\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)$',  # Last v. pattern
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)\s+vs\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)$',  # Last vs. pattern
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)\s+versus\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)$',  # Last versus pattern
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return f"{match.group(1).strip()} v. {match.group(2).strip()}"
        
        parts = re.split(r'[.,;:]|\s+(?:v\.|vs\.|versus)\s+', text)
        for part in reversed(parts):
            part = part.strip()
            if part and re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$', part):
                return part
        
        return text.strip()
    
    def _clean_party_name(self, party_name: str) -> str:
        """Clean individual party names to remove extra text while preserving name prefixes"""
        if not party_name:
            return ""
            
        name_prefixes = ['De', 'La', 'Van', 'Von', 'Mc', 'Mac', 'O\'']
        prefixes_to_remove = ['In re ', 'In the Matter of ', 'Matter of ']
        
        cleaned = party_name
        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
                break
        
        cleaned = re.sub(r'[.,;:]$', '', cleaned).strip()
        
        return cleaned
    
    def _extract_date_from_case_context(self, text: str, case_name: str, citation_start: int, citation_end: int) -> Dict[str, str]:
        """Extract date from context around case name"""
        try:
            case_pos = text.find(case_name)
            if case_pos == -1:
                return {'date': '', 'year': ''}
            
            context_start = max(0, case_pos - 100)
            context_end = min(len(text), case_pos + len(case_name) + 200)  # Reduced from 500 to 200
            context = text[context_start:context_end]
            
            year_patterns = [
                r'\((\d{4})\)',  # (2022) - highest priority
                r'(\d{4})',      # 2022 - medium priority
            ]
            
            for pattern in year_patterns:
                matches = re.finditer(pattern, context)
                for match in matches:
                    year = match.group(1) if match.groups() else match.group(0)
                    if 1900 <= int(year) <= 2030:
                        match_pos = match.start()
                        case_pos_in_context = case_pos - context_start
                        distance = abs(match_pos - case_pos_in_context)
                        
                        if distance < 300:  # Only accept dates within 300 characters
                            return {'date': year, 'year': year}
            
            return {'date': '', 'year': ''}
            
        except Exception as e:
            return {'date': '', 'year': ''}

_unified_extractor = None

def get_unified_extractor() -> UnifiedCaseNameExtractorV2:
    """Get global unified extractor instance"""
    global _unified_extractor
    if _unified_extractor is None:
        _unified_extractor = UnifiedCaseNameExtractorV2()
    return _unified_extractor

def extract_case_name_and_date_unified(
    text: str, 
    citation: Optional[str] = None,
    citation_start: Optional[int] = None,
    citation_end: Optional[int] = None,
    debug: bool = False,
    context_window: Optional[int] = None,
    all_citations: Optional[List] = None
) -> Dict[str, Any]:
    """
    DEPRECATED: Use extract_case_name_and_date_master() instead.
    
    This function is deprecated and will be removed in v3.0.0.
    Use extract_case_name_and_date_master() for consistent extraction results.
    
    Convenience function for backward compatibility.
    UPDATED: Use context window approach that works correctly.
    """
    import warnings
    warnings.warn(
        "extract_case_name_and_date_unified() is deprecated. Use extract_case_name_and_date_master() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    logger.info(f"[DEBUG] citation_start parameter: {citation_start}, citation: '{citation}'")
    if citation_start is not None:
        context_size = context_window or 150
        start_pos = max(0, citation_start - context_size)
        context = text[start_pos:citation_start].strip()
        
        logger.info(f"[CONTEXT_EXTRACT] Using context window approach for '{citation}' at position {citation_start}")
        logger.info(f"[CONTEXT_EXTRACT] Context: '{context[:100]}...'")
        
        if debug:
            logger.info(f"[CONTEXT_EXTRACT] Full context: '{context}'")
        
        patterns = [
            # Fixed: Handle Washington citation format with .2d, .3d, etc.
            # Also handle multiple citations after case name (e.g., "Case v. Name, 123 Wn.2d 456, 789 P.3d 101")
            r'([A-Z][a-zA-Z\',\.\&\s]+?)\s+v\.\s+([A-Z][a-zA-Z\',\.\&\s]+?)(?=\s*,\s*\d+\s+Wn\.\d+|\s+\d+\s+Wn\.\d+)',
            r'([A-Z][a-zA-Z\',\.\&\s]+?)\s+v\.\s+([A-Z][a-zA-Z\',\.\&\s]+?)(?=\s*,\s*\d+\s+P\.\d+|\s+\d+\s+P\.\d+)',
            r'([A-Z][a-zA-Z\',\.\&\s]+?)\s+v\.\s+([A-Z][a-zA-Z\',\.\&\s]+?)(?=\s*,\s*\d+|\s+\d+)',
            # Special pattern for "Dep't of" cases with multiple citations
            r'([A-Z][a-zA-Z\',\.\&\s]+?)\s+v\.\s+(Dep\'t\s+of\s+[A-Z][a-zA-Z\',\.\&\s]+?)(?=\s*,\s*\d+\s+Wn\.\d+.*?,\s*\d+\s+P\.\d+|$)',
            r'(State(?:\s+of\s+[A-Z][a-zA-Z\',\.\&\s]+?)?)\s+v\.\s+([A-Z][a-zA-Z\',\.\&\s]+?)(?=\s*,\s*\d+|\s+\d+\s+Wn\.\d+|\s+\d+\s+P\.\d+|$)',
            r'([A-Z][a-zA-Z\',\.\&\s]+?)\s+v\.\s+([A-Z][a-zA-Z\',\.\&\s]+?)(?=\s*,\s*\d+|\s+\d+\s+Wn\.\d+|\s+\d+\s+P\.\d+|$)',
        ]
        
        all_matches = []
        for pattern in patterns:
            for match in re.finditer(pattern, context, re.IGNORECASE):
                distance_to_citation = len(context) - match.end()
                all_matches.append((match, distance_to_citation))
        
        all_matches.sort(key=lambda x: x[1])
        
        match = all_matches[0][0] if all_matches else None
        
        if match:
            plaintiff = match.group(1).strip()
            defendant = match.group(2).strip()
            
            contamination_phrases = [
                r'\b(de\s+novo)\b', r'\b(questions?\s+of\s+law)\b', r'\b(statutory\s+interpretation)\b',
                r'\b(in\s+light\s+of)\b', r'\b(the\s+record\s+certified)\b', r'\b(federal\s+court)\b',
                r'\b(this\s+court\s+reviews?)\b', r'\b(we\s+review)\b', r'\b(certified\s+questions?)\b',
                r'\b(issue\s+of\s+law)\b', r'\b(also\s+an?\s+issue)\b', r'\b(reviews?\s+de\s+novo)\b',
                r'\b(see|citing|quoting|accord|id\.|ibid\.)\b', r'\b(brief\s+at|opening\s+br\.|reply\s+br\.)\b',
                r'\b(internal\s+quotation\s+marks)\b', r'\b(alteration\s+in\s+original)\b',
                r'\b(may\s+ask\s+this\s+court)\b', r'\b(resolution\s+of\s+that\s+question)\b',
                r'\b(necessary\s+to\s+resolve)\b', r'\b(case\s+before\s+the)\b'
            ]
            
            for phrase_pattern in contamination_phrases:
                plaintiff = re.sub(phrase_pattern, '', plaintiff, flags=re.IGNORECASE)
                defendant = re.sub(phrase_pattern, '', defendant, flags=re.IGNORECASE)
            
            plaintiff = re.sub(r'\s+', ' ', plaintiff).strip()
            defendant = re.sub(r'\s+', ' ', defendant).strip()
            
            def extract_case_name_part(text_part, is_plaintiff=True):
                """Extract clean case name from potentially contaminated text"""
                words = text_part.split()
                clean_words = []
                
                if is_plaintiff:
                    for word in reversed(words):
                        if (word and (word[0].isupper() or 
                                    word.lower() in ['v.', 'vs.', '&', 'of', 'the', 'and', 'inc', 'llc', 'corp', 'ltd', 'co.', 'bros.', 'farms'] or
                                    "'" in word or '.' in word)):
                            clean_words.insert(0, word)
                        else:
                            if clean_words:  # Only stop if we already have some words
                                break
                else:
                    for word in words:
                        if (word and (word[0].isupper() or 
                                    word.lower() in ['&', 'of', 'the', 'and', 'inc', 'llc', 'corp', 'ltd', 'co.', 'bros.', 'farms', 'fish', 'wildlife', 'dep\'t'] or
                                    "'" in word or '.' in word)):
                            clean_words.append(word)
                        elif clean_words and word.lower() not in ['and', 'or', 'at', 'in', 'on']:
                            break
                
                return ' '.join(clean_words) if clean_words else text_part
            
            clean_plaintiff = extract_case_name_part(plaintiff, is_plaintiff=True)
            clean_defendant = extract_case_name_part(defendant, is_plaintiff=False)
            
            case_name = f"{clean_plaintiff} v. {clean_defendant}"
            
            case_name = re.sub(r'^[.\s,;:]+', '', case_name)  # Remove leading punctuation
            case_name = re.sub(r'^(the|a|an)\s+', '', case_name, flags=re.IGNORECASE)  # Remove leading articles
            case_name = re.sub(r'\s+', ' ', case_name).strip()  # Clean up whitespace
            
            case_name = re.sub(r'^\.\s*', '', case_name)  # Remove leading period and any following spaces
            case_name = re.sub(r'^(and|or|but)\s+', '', case_name, flags=re.IGNORECASE)  # Remove leading conjunctions
            case_name = re.sub(r'^(?:that\s+and\s+by\s+the\s+|that\s+and\s+|is\s+also\s+an\s+|also\s+an\s+|also\s+|that\s+|this\s+is\s+|this\s+)\.?\s*', '', case_name, flags=re.IGNORECASE)
            
            year_context = text[max(0, citation_start - 50):citation_start + 100] if citation_start else ""
            year_match = re.search(r'\((\d{4})\)', year_context)
            year = year_match.group(1) if year_match else ""
            
            if debug:
                logger.info(f"[CONTEXT_EXTRACT] Extracted: '{case_name}' (year: {year})")
            
            # Clean the case name to remove trailing punctuation
            from src.utils.case_name_cleaner import clean_extracted_case_name
            cleaned_case_name = clean_extracted_case_name(case_name) if case_name else case_name
            
            return {
                'case_name': cleaned_case_name,
                'date': year,
                'year': year,
                'confidence': 0.95,
                'method': 'context_window',
                'debug_info': {'context': context, 'pattern_match': True}
            }
    
    extractor = get_unified_extractor()
    result = extractor.extract_case_name_and_date(text, citation, citation_start, citation_end, debug=debug)
    
    # Clean the case name to remove trailing punctuation
    from src.utils.case_name_cleaner import clean_extracted_case_name
    cleaned_case_name = clean_extracted_case_name(result.case_name) if result.case_name else result.case_name
    
    return {
        'case_name': cleaned_case_name,
        'date': result.date,
        'year': result.year,
        'confidence': result.confidence,
        'method': result.method,
        'debug_info': result.debug_info
    }

def extract_case_name_only_unified(text: str, citation: Optional[str] = None, debug: bool = False) -> str:
    """
    Convenience function for backward compatibility.
    Use get_unified_extractor().extract_case_name_and_date() for new code.
    """
    extractor = get_unified_extractor()
    result = extractor.extract_case_name_and_date(text, citation, debug=debug)
    return result.case_name

def _deprecation_warning(old_function_name: str, new_function_name: str):
    """Show deprecation warning"""
    import warnings
    warnings.warn(
        f"Function '{old_function_name}' is deprecated. Use '{new_function_name}' instead.",
        DeprecationWarning,
        stacklevel=3
    )

def extract_case_name_and_date_master(
    text: str, 
    citation: Optional[str] = None,
    citation_start: Optional[int] = None,
    citation_end: Optional[int] = None,
    debug: bool = False,
    context_window: Optional[int] = None,
    all_citations: Optional[List] = None
) -> Dict[str, Any]:
    """
    MASTER EXTRACTION FUNCTION - Now uses unified architecture
    
    This is the single source of truth for case name and date extraction.
    All other extraction functions should delegate to this function.
    
    ARCHITECTURE UPDATE: Now uses the unified extraction architecture
    for consistent, accurate extraction across all processing paths.
    """
    import traceback
    caller_info = traceback.extract_stack()[-2]  # Get the calling function
    logger.warning(f"🎯 MASTER_EXTRACT: Starting extraction for citation '{citation}' at position {citation_start} (called from {caller_info.filename}:{caller_info.lineno})")
    
    try:
        # NEW APPROACH: Extract focused context around the citation
        if citation_start is not None and citation_end is not None:
            # Extract context window around the citation
            context_start = max(0, citation_start - 1000)  # EXPANDED: 1000 chars before citation
            context_end = min(len(text), citation_end + 200)   # EXPANDED: 200 chars after citation
            context_text = text[context_start:context_end]
            
            # Adjust citation position within the context
            citation_start_in_context = citation_start - context_start
            citation_end_in_context = citation_end - context_start
            
            logger.warning(f"🔍 MASTER_EXTRACT: Text length: {len(text)}, Citation position: {citation_start}-{citation_end}")
            logger.warning(f"🔍 MASTER_EXTRACT: Context calculation: start={context_start}, end={context_end}")
            logger.warning(f"🔍 MASTER_EXTRACT: Extracted context length: {len(context_text)}")
            logger.warning(f"🔍 MASTER_EXTRACT: Extracted context: '{context_text}'")
            
            # IMPROVED: Classify citation type to improve extraction accuracy
            citation_type = _classify_citation_context(context_text, citation_start_in_context, citation)
            logger.warning(f"🔍 MASTER_EXTRACT: Citation type classified as: {citation_type}")
            logger.warning(f"🔍 MASTER_EXTRACT: Citation position in context: {citation_start_in_context}-{citation_end_in_context}")
            logger.warning(f"🔍 MASTER_EXTRACT: Citation text: '{citation}'")
            
            # IMPROVED: Skip extraction for embedded discussion citations
            if citation_type == "embedded_discussion":
                logger.warning(f"⚠️ MASTER_EXTRACT: Skipping extraction for embedded discussion citation '{citation}'")
                return {
                    'case_name': 'N/A',
                    'year': 'N/A',
                    'date': 'N/A',
                    'confidence': 0.0,
                    'method': 'skipped_embedded',
                    'debug_info': {'citation_type': citation_type, 'reason': 'embedded_in_discussion'}
                }
            
            # Use the unified architecture with the focused context
            from src.unified_extraction_architecture import extract_case_name_and_year_unified
            
            result = extract_case_name_and_year_unified(
                text=context_text,  # Use focused context instead of full text
                citation=citation or "",
                start_index=citation_start_in_context,
                end_index=citation_end_in_context,
                debug=debug
            )
            
            # Add citation type to debug info
            if result and isinstance(result, dict):
                if 'debug_info' not in result:
                    result['debug_info'] = {}
                result['debug_info']['citation_type'] = citation_type
            
            if result and result.get('case_name') and result['case_name'] != 'N/A':
                logger.warning(f"✅ MASTER_EXTRACT: Successfully extracted '{result['case_name']}' for citation '{citation}' using context approach")
            else:
                logger.warning(f"⚠️ MASTER_EXTRACT: No case name extracted for citation '{citation}' using context approach")
            
            return result
        else:
            # Fallback to original approach if no position info
            from src.unified_extraction_architecture import extract_case_name_and_year_unified
            
            result = extract_case_name_and_year_unified(
                text=text,
                citation=citation or "",
                start_index=citation_start,
                end_index=citation_end,
                debug=debug
            )
            
            if result and result.get('case_name') and result['case_name'] != 'N/A':
                logger.warning(f"✅ MASTER_EXTRACT: Successfully extracted '{result['case_name']}' for citation '{citation}'")
            else:
                logger.warning(f"⚠️ MASTER_EXTRACT: No case name extracted for citation '{citation}'")
            
            return result
        
    except Exception as e:
        logger.error(f"❌ MASTER_EXTRACT: Unified architecture failed: {e}")
        result = extract_case_name_and_date_unified(
            text=text,
            citation=citation,
            citation_start=citation_start,
            citation_end=citation_end,
            debug=debug,
            context_window=context_window,
            all_citations=all_citations
        )
        
        if result and result.get('case_name'):
            logger.warning(f"✅ MASTER_EXTRACT: Fallback extraction successful: '{result['case_name']}' for citation '{citation}'")
        else:
            logger.warning(f"⚠️ MASTER_EXTRACT: Fallback extraction failed for citation '{citation}'")
        
        return result

def _classify_citation_context(context_text: str, citation_position: int, citation: str) -> str:
    """
    Classify citation as 'proper_case_citation' or 'embedded_discussion'
    
    This helps improve extraction accuracy by identifying citations that appear
    within legal discussion text vs standalone case citations.
    """
    import re
    
    if not context_text or citation_position < 0:
        return "unknown"
    
    # Extract text before and after the citation
    before_text = context_text[:citation_position].strip()
    after_text = context_text[citation_position + len(citation):].strip()
    
    # Look for case name patterns before the citation
    case_name_patterns = [
        r'\b[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*\s+v\.\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*,?\s*$',
        r'\bIn\s+re\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*,?\s*$',
        r'\bState\s+v\.\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*,?\s*$',
        r'\bEx\s+parte\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*,?\s*$'
    ]
    
    # Check if there's a case name pattern immediately before the citation
    for pattern in case_name_patterns:
        if re.search(pattern, before_text[-100:]):  # Check last 100 chars
            return "proper_case_citation"
    
    # Look for embedded discussion indicators
    embedded_indicators = [
        r'\b(statutory|actual|damages|award|employer|pay|complainant|violation|occurred)\b',
        r'\b(plaintiff|defendant|argue|applicants|employment|standing|statute|injury)\b',
        r'\b(incentivizes|persons|interest|getting|job|offer|search|noncompliant)\b',
        r'\b(question|issue|review|court|held|ruling|decision|interpretation)\b',
        r'\b(legislative|created|grant|right|sue|harm|protected|zone)\b'
    ]
    
    # Count embedded indicators in surrounding context
    context_sample = (before_text[-200:] + " " + after_text[:200:]).lower()
    embedded_count = sum(1 for pattern in embedded_indicators if re.search(pattern, context_sample))
    
    if embedded_count >= 3:
        return "embedded_discussion"
    elif embedded_count >= 1:
        return "possible_embedded"
    else:
        return "proper_case_citation"

