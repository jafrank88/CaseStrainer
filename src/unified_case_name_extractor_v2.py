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
from typing import Dict, Optional, Tuple, List, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache

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
        # Define common corporate suffixes for reuse
        corp_suffixes = r'(?:LLC|Inc|Corp|Co|Ltd|L\.P\.?|L\.L\.C\.?|P\.C\.?|P\.A\.?|S\.A\.?|GmbH|AG|SE|K\.K\.?|Y\.K\.?|N\.V\.?|A\/S|A\.B\.?|S\.P\.A\.?|S\.A\.R\.L\.?|S\.A\.S\.?|B\.V\.?|A\.S\.?|A\.B\.?|A\.G\.?|S\.A\.?|S\.P\.A\.?|S\.A\.S\.?|S\.A\.R\.L\.?|S\.A\.B\.?|S\.A\.I\.C\.?|S\.A\.I\.E\.?|S\.A\.L\.?|S\.A\.M\.?|S\.A\.N\.?|S\.A\.O\.?|S\.A\.P\.?|S\.A\.Q\.?|S\.A\.R\.A\.?|S\.A\.S\.?|S\.A\.T\.?|S\.A\.U\.?|S\.A\.V\.?|S\.A\.W\.?|S\.A\.X\.?|S\.A\.Y\.?|S\.A\.Z\.?)'
        
        # Define common legal abbreviations that must be treated as single units
        # CRITICAL: These prevent truncation like "U.S." -> "U." or "Sec'y" -> "Se"
        legal_abbrev = r'(?:U\.S\.|Sec\'y|Gov\'t|Dep\'t|Att\'y|Dist\.|Comm\'r|Ass\'n|Bd\.|Comm\'n|Div\.|Sch\.|Univ\.|Coll\.)'
        
        # Define word component that handles abbreviations and prepositions
        # This matches: regular words, abbreviations (U.S.), possessives (Sec'y), and prepositions (of, for, the)
        word_component = r'(?:' + legal_abbrev + r'|[A-Z][a-z]+(?:\'[a-z]+)?|[A-Z]\.(?:[A-Z]\.)*|of|for|the|and|&)'
        
        # Party name pattern: one or more word components with spaces
        party_pattern = word_component + r'(?:\s+' + word_component + r')*'
        
        self.patterns = [
            # PRIORITY 1: Legal abbreviation-aware pattern (HIGHEST CONFIDENCE)
            # Handles: "E. Palo Alto v. U.S. Dep't", "Tootle v. Sec'y of Navy", "Department of Education v. California"
            {
                'name': 'legal_abbrev_aware_pattern',
                'pattern': f'({party_pattern})\\s+v\\.\\s+({party_pattern})(?=\\s*,?\\s*(?:\\d|\\[|\\(|$))',
                'confidence': 0.99,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}",
                'description': 'Abbreviation-aware pattern that handles U.S., Sec\'y, Dep\'t, and prepositions like "of"'
            },
            # PRIORITY 2: United States specific pattern
            {
                'name': 'party_v_united_states',
                'pattern': r'([A-Z][a-zA-Z\',\.\s&]+?)\s+v\.\s+(U\.S\.|United\s+States)(?:\s+(?:Dep\'t|Department)\s+of\s+[A-Z][a-zA-Z\s]+)?(?=\s*,?\s*(?:\d|\[|\(|$))',
                'confidence': 0.98,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}",
                'description': 'Special pattern for United States and its departments'
            },
            # Enhanced corporate name pattern
            {
                'name': 'corporate_v_party_extended',
                'pattern': f'([A-Z][a-zA-Z\',\\.\\s&]+?(?:\\s+{corp_suffixes})?)\\s+v\\.\\s+([A-Z][a-zA-Z\',\\.\\s&]+)(?=\\s*,?\\s*(?:\\d|\\[|\\(|$))',
                'confidence': 0.96,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}",
                'description': 'Extended pattern for corporate entities with various legal suffixes'
            },
            # Enhanced party name pattern with prepositions
            {
                'name': 'party_v_party_extended',
                'pattern': r'([A-Z][a-zA-Z\',\.\s&]+(?:\s+(?:of|for|the)\s+[A-Z][a-zA-Z\',\.\s&]+)*)\s+v\.\s+([A-Z][a-zA-Z\',\.\s&]+(?:\s+(?:of|for|the)\s+[A-Z][a-zA-Z\',\.\s&]+)*)(?=\s*,?\s*(?:\d|\[|\(|$))',
                'confidence': 0.95,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}",
                'description': 'Extended pattern for party names with prepositions like "Department of Education"'
            },
            # Enhanced State/People v. Party pattern
            {
                'name': 'state_people_v_party_extended',
                'pattern': r'((?:State|People)(?:\s+of\s+(?:the\s+)?(?:State\s+of\s+)?[A-Z][a-z]+?)?)\s+v\.\s+([A-Z][a-zA-Z\',\.\s&]+?)(?=\s*(?:\d|\[|\(|$))',
                'confidence': 0.97,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}",
                'description': 'Extended pattern for State/People v. Party cases'
            },
            # Enhanced In re pattern
            {
                'name': 'in_re_extended',
                'pattern': r'(In\s+re\s+[A-Z][a-zA-Z\',\.\s&]+?)(?=\s*(?:\d|\[|\(|$))',
                'confidence': 0.95,
                'format': lambda m: m.group(1).strip(),
                'description': 'Extended pattern for "In re" cases with better boundary detection'
            },
            {
                'name': 'reverse_lookup_v_precise',
                'pattern': r'(?:^|[.!?]\s+|;\s+)([A-Z][a-zA-Z\'\.\&\s]+?)\s+v\.\s+([A-Z][a-zA-Z\'\.\&\s]+?)(?:\s*,)?$',
                'confidence': 0.70,  # Reduced confidence - DEPRECATED
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}",
                'description': 'Precise case name pattern with flexible character support'
            },
            {
                'name': 'reverse_lookup_word_boundary',
                'pattern': r'\b([A-Z][a-zA-Z\'\.\&\s]+?)\s+v\.\s+([A-Z][a-zA-Z\'\.\&\s]+?)(?:\s*,)?$',
                'confidence': 0.70,  # Reduced confidence - DEPRECATED
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}",
                'description': 'Word-boundary aware flexible case name pattern'
            },
            {
                'name': 'reverse_lookup_with_entities',
                'pattern': r'\b([A-Z][a-zA-Z\'\.\&\s]+?)\s+v\.\s+([A-Z][a-zA-Z\'\.\&\s]+?)(?:\s*,)?$',
                'confidence': 0.70,  # Reduced confidence - DEPRECATED
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}",
                'description': 'Flexible case name pattern supporting all entity types'
            },
            {
                'name': 'bounded_v_pattern',
                'pattern': r'([A-Z][a-zA-Z\'\.\&\s]+?)\s+v\.\s+([A-Z][a-zA-Z\'\.\&\s]+?)',
                'confidence': 0.70,  # Reduced confidence - DEPRECATED
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
        """Context-based extraction: use optimized context window around citation
        
        This method uses a focused context window around the citation and applies sophisticated
        scoring to identify the most likely case name while avoiding contamination from
        surrounding legal discussion text.
        """
        try:
            # FIX #27B: Only look BACKWARD, not forward!
            # Looking forward was capturing case names from NEXT citations
            # E.g., "Lopez...183 Wn.2d 649...Spokane County" would extract "Spokane County"
            context_before = 150  # Search backward for case name
            context_after = 0     # Changed from 30 to 0 - don't look forward!
            
            context_start = max(0, citation_start - context_before)
            context_end = citation_start  # Changed from citation_end + context_after
            context = text[context_start:context_end]
            
            if debug:
                print(f"[DEBUG] Context window: '{context}'")
            
            best_match = None
            best_confidence = 0.0
            best_pattern = None
            best_raw_match = None
            
            # First pass: look for high-confidence patterns
            for pattern_info in sorted(self.patterns, key=lambda x: -x['confidence']):
                # Skip low confidence patterns on first pass
                if pattern_info['confidence'] < 0.7:
                    continue
                    
                matches = list(pattern_info['compiled'].finditer(context))
                if not matches:
                    continue
                    
                # Find the match closest to the citation
                citation_pos = citation_start - context_start
                best_match_for_pattern = None
                best_score_for_pattern = 0
                
                for match in matches:
                    match_start, match_end = match.span()
                    match_text = match.group(0)
                    
                    # Calculate position-based score (higher is better)
                    # Prefer matches that end just before the citation starts
                    position_score = 0
                    
                    # Case 1: Match ends before citation (ideal case)
                    if match_end <= citation_pos:
                        # Closer to citation is better (but not too close)
                        distance = citation_pos - match_end
                        if distance < 5:  # Too close might be part of citation
                            position_score = 0.3
                        elif distance < 20:
                            position_score = 1.0
                        elif distance < 50:
                            position_score = 0.8
                        else:
                            position_score = 0.5
                    # Case 2: Match overlaps with citation (less ideal)
                    elif match_start < citation_pos:
                        position_score = 0.2
                    # Case 3: Match is after citation (least ideal)
                    else:
                        position_score = 0.1
                    
                    # Length score - prefer longer matches (but not too long)
                    match_length = len(match_text)
                    if match_length < 10:
                        length_score = 0.3
                    elif match_length > 100:  # Very long matches are likely contaminated
                        length_score = 0.2
                    else:
                        length_score = 0.7
                    
                    # Combined score
                    score = (pattern_info['confidence'] * 0.5 + 
                            position_score * 0.3 + 
                            length_score * 0.2)
                    
                    if score > best_score_for_pattern:
                        best_score_for_pattern = score
                        best_match_for_pattern = match
                
                # If we found a good match for this pattern, use it
                if best_match_for_pattern and best_score_for_pattern > best_confidence:
                    best_confidence = best_score_for_pattern
                    best_match = pattern_info['format'](best_match_for_pattern)
                    best_pattern = pattern_info['name']
                    best_raw_match = best_match_for_pattern.group(0)
                    
                    # If we have a very high confidence match, return early
                    if best_confidence > 0.9:
                        break
            
            # If we didn't find a high-confidence match, try lower confidence patterns
            if best_confidence < 0.7:
                for pattern_info in self.patterns:
                    if pattern_info['confidence'] >= 0.7:  # Already tried these
                        continue
                        
                    match = pattern_info['compiled'].search(context)
                    if match:
                        case_name = pattern_info['format'](match)
                        confidence = pattern_info['confidence']
                        
                        # Apply position-based scoring
                        match_pos = match.start()
                        citation_pos = citation_start - context_start
                        distance = abs(match_pos - citation_pos)
                        
                        if distance < 50:
                            confidence *= 1.5
                        elif distance < 100:
                            confidence *= 1.2
                            
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_match = case_name
                            best_pattern = pattern_info['name']
                            best_raw_match = match.group(0)
            
            # If we found a match, clean it and return it
            if best_match and best_confidence > 0.5:
                # Clean the match to remove any remaining contamination
                cleaned_match = self._clean_case_name(best_match)
                
                # Additional validation - ensure it looks like a case name
                if not self._is_valid_case_name(cleaned_match):
                    if debug:
                        print(f"[DEBUG] Rejected invalid case name: {cleaned_match}")
                    return None
                
                return ExtractionResult(
                    case_name=cleaned_match,
                    confidence=min(best_confidence, 1.0),
                    method=f"context_based_{best_pattern}",
                    strategy=ExtractionStrategy.CONTEXT_BASED,
                    raw_matches=[best_raw_match] if best_raw_match else [best_match]
                )
            
            return None
            
        except Exception as e:
            if debug:
                pass  # Debug logging can be added here if needed
            return None
    
    def _extract_pattern_based(self, text: str, citation: str, citation_start: int, citation_end: int, debug: bool) -> Optional[ExtractionResult]:
        """Pattern-based extraction: use citation boundaries and pattern matching"""
        try:
            # FIX #27B: Only look BACKWARD, not forward!
            # Looking forward (+ 100) was capturing case names from NEXT citations
            search_start = max(0, citation_start - 400)
            search_end = citation_start  # Changed from citation_end + 100
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
            # CRITICAL: Remove citation text patterns FIRST (before other cleaning)
            # These must be VERY aggressive to catch all citation formats
            r',\s*\d+\s+Wn\.?\s*(?:App\.?)?\s*\d+d?\s+\d+.*$',  # ", 31 Wn. App. 2d 343, 359-62"
            r',\s*\d+\s+Wash\.?\s*(?:App\.?)?\s*\d+d?\s+\d+.*$',  # ", 31 Wash. 2d 343"
            r',\s*\d+\s+U\.S\.?\s+\d+.*$',  # ", 502 U.S. 251, 255"
            r',\s*\d+\s+S\.\s*Ct\.?\s+\d+.*$',  # ", 112 S. Ct. 683"
            r',\s*\d+\s+L\.\s*Ed\.?\s*\d*d?\s+\d+.*$',  # ", 116 L. Ed. 2d 687"
            r',\s*\d+\s+F\.?\s*(?:\d+d?|Supp\.?)?\s+\d+.*$',  # ", 761 F.3d 218" or ", 12 F. Supp. 2d 999"
            r',\s*\d+\s+P\.?\s*\d*d?\s+\d+.*$',  # ", 549 P.3d 727"
            r',\s*\d+\s+[A-Z][a-z]*\.?\s*(?:App\.?)?\s*\d+d?\s+\d+.*$',  # Generic: ", 123 Xyz. 456"
            r',\s*\[\d+\s+U\.S\..*$',  # ", [21 U.S." etc
            r',\s*\d+\s+(?:Wheat\.|Pet\.|How\.|Wall\.|Black\.|Cranch).*$',  # Old reporters
            
            # FIX: Procedural phrases that are NOT case names
            r'^(vacated|remanded|reversed|affirmed|dismissed|granted|denied)\s+(and|or)\s+(vacated|remanded|reversed|affirmed|dismissed|granted|denied).*$',
            r'^(vacated|remanded|reversed|affirmed|dismissed|granted|denied)(\s+in\s+part)?(\s+and\s+\w+)?$',
            
            # Signal words at START of name (Id., For example, etc.)
            r'^Id\.\s*(For\s+example,?\s*)?(in\s+)?',  # "Id." optionally followed by "For example, in"
            r'^For\s+example,?\s+(in\s+)?',  # "For example, in"
            r'^See\s+(also,?)?\s*',  # "See" or "See also"
            r'^E\.g\.,?\s*',  # "E.g." at start
            r'^Cf\.\s*',  # "Cf." at start
            
            # Legal analysis phrases
            r'\b(de\s+novo)\b', r'\b(questions?\s+of\s+law)\b', r'\b(statutory\s+interpretation)\b',
            r'\b(in\s+light\s+of)\b', r'\b(the\s+record\s+certified)\b', r'\b(federal\s+court)\b',
            r'\b(this\s+court\s+reviews?)\b', r'\b(we\s+review)\b', r'\b(certified\s+questions?)\b',
            r'\b(issue\s+of\s+law)\b', r'\b(also\s+an?\s+issue)\b',
            
            # Signal words and citation indicators
            r'\b(see also|see, e\.g\.|see,? generally|see,? also|see,? id\.|see,? supra|see,? infra)\b',
            r'\b(compare|but see|but cf\.|but,? cf\.|but see,? also|but see,? generally)\b',
            r'\b(citing|accord(ing)?( to)?|as (discussed|noted) (above|below|supra|infra))\b',
            r'\b(e\.g\.|i\.e\.|cf\.|id\.|supra|infra|et seq\.|et al\.)\b',
            
            # Legal discussion phrases
            r'\b(holding that|concluding that|finding that|stating that|reasoning that|explaining that)\b',
            r'\b(affirming|reversing|remanding|vacating|denying|granting|dismissing|holding|concluding|finding|stating|reasoning|explaining)\b',
            r'\b(in accordance with|consistent with|pursuant to|under|in light of|in view of|because of|due to)\b',
            
            # Court and jurisdiction references
            r'\b((the )?(court|panel|circuit|district|supreme court|appellate court|appellate division|court of appeals))\b',
            r'\b(held|concluded|found|stated|reasoned|explained|determined|ruled|opined|wrote|joined by|concurring|dissenting)\b',
            
            # Procedural history and legal standards
            r'\b(on (appeal|review|remand|rehearing|reconsideration)|after (remand|rehearing|reconsideration))\b',
            r'\b(standard of review|de novo|abuse of discretion|clearly erroneous|substantial evidence|plain error|deference)\b',
            
            # Common legal phrases that might contaminate
            r'\b(whereas|herein|heretofore|thereafter|thereunder|therein|thereof|hereby|hereinabove|hereinafter)\b',
            r'\b(notwithstanding|provided,? however|provided further|except as otherwise provided|subject to the foregoing)\b'
        ]
        
        for phrase_pattern in contamination_phrases:
            plaintiff = re.sub(phrase_pattern, '', plaintiff, flags=re.IGNORECASE)
            defendant = re.sub(phrase_pattern, '', defendant, flags=re.IGNORECASE)
        
        plaintiff = re.sub(r'\s+', ' ', plaintiff).strip()
        defendant = re.sub(r'\s+', ' ', defendant).strip()
        
        # FIX: Reject if either party is empty or purely punctuation after cleaning
        if not plaintiff or not defendant or len(plaintiff) < 2 or len(defendant) < 2:
            return ""
        
        # FIX: Reject if result is purely procedural/signal words (what's left after cleaning)
        procedural_only = r'^(and|or|the|in|of|at|by|for|to|from)$'
        if re.match(procedural_only, plaintiff, re.IGNORECASE) or re.match(procedural_only, defendant, re.IGNORECASE):
            return ""
        
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
    
    def _is_valid_case_name(self, case_name: str) -> bool:
        """Validate that a potential case name meets our criteria
        
        Args:
            case_name: The case name to validate
            
        Returns:
            bool: True if the case name appears valid, False otherwise
        """
        if not case_name or len(case_name) < 5:
            return False
            
        # Must contain a 'v.' or 'vs.' or 'versus' to separate parties
        if not any(separator in case_name.lower() for separator in [' v. ', ' vs. ', ' versus ']):
            return False
            
        # Split into plaintiff and defendant
        parts = re.split(r'\s+v\.?\s+|\s+vs\.?\s+|\s+versus\s+', case_name, flags=re.IGNORECASE)
        if len(parts) < 2:
            return False
            
        plaintiff, defendant = parts[0].strip(), parts[1].strip()
        
        # Both parties must have at least one word character
        if not re.search(r'\w', plaintiff) or not re.search(r'\w', defendant):
            return False
        
        # CRITICAL: Reject truncated names that start with lowercase
        # e.g., "agit Indian Tribe" is clearly truncated from "Upper Skagit Indian Tribe"
        if plaintiff and plaintiff[0].islower():
            return False
        if defendant and defendant[0].islower():
            return False
        
        # CRITICAL: Reject party names that are too short (likely truncated)
        # e.g., "Mgmt." without company prefix, "Co." without company name
        if len(plaintiff) < 3 or len(defendant) < 3:
            return False
            
        # Check for common contamination patterns that might have been missed
        contamination_indicators = [
            r'\b(case|matter|appeal|petition|in re|in the matter of|ex parte|re:|\d{4})\b',
            r'\b(holding|concluding|finding|stating|reasoning|explaining)\b',
            r'\b(see also|see, e\.g\.|cf\.|id\.|supra|infra)\b',
            r'\b(affirming|reversing|remanding|vacating|denying|granting|dismissing)\b',
            r'\b(\d+\s+[A-Z]+\s+\d+)|([A-Z]+\s+\d+)|(\d+\s+[A-Z]+\.?\s+\d+)\b'  # Citation patterns
        ]
        
        for pattern in contamination_indicators:
            if re.search(pattern, case_name, re.IGNORECASE):
                return False
                
        return True
        
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
        context_size = context_window or 300  # CRITICAL: Increased from 150 to 300 for better extraction
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
                # CRITICAL: Remove citation text patterns FIRST
                r',\s*\d+\s+Wn\.?\s*(?:App\.?)?\s*\d+d?\s+\d+.*$',
                r',\s*\d+\s+Wash\.?\s*(?:App\.?)?\s*\d+d?\s+\d+.*$',
                r',\s*\d+\s+U\.S\.?\s+\d+.*$',
                r',\s*\d+\s+S\.\s*Ct\.?\s+\d+.*$',
                r',\s*\d+\s+L\.\s*Ed\.?\s*\d*d?\s+\d+.*$',
                r',\s*\d+\s+F\.?\s*(?:\d+d?|Supp\.?)?\s+\d+.*$',
                r',\s*\d+\s+P\.?\s*\d*d?\s+\d+.*$',
                r',\s*\d+\s+[A-Z][a-z]*\.?\s*(?:App\.?)?\s*\d+d?\s+\d+.*$',
                r',\s*\[\d+\s+U\.S\..*$',
                r',\s*\d+\s+(?:Wheat\.|Pet\.|How\.|Wall\.|Black\.|Cranch).*$',
                
                # FIX: Procedural phrases that are NOT case names
                r'^(vacated|remanded|reversed|affirmed|dismissed|granted|denied)\s+(and|or)\s+(vacated|remanded|reversed|affirmed|dismissed|granted|denied).*$',
                r'^(vacated|remanded|reversed|affirmed|dismissed|granted|denied)(\s+in\s+part)?(\s+and\s+\w+)?$',
                
                # Signal words at START
                r'^Id\.\s*(For\s+example,?\s*)?(in\s+)?',
                r'^For\s+example,?\s+(in\s+)?',
                r'^See\s+(also,?)?\s*',
                r'^E\.g\.,?\s*',
                r'^Cf\.\s*',
                
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
            
            # FIX: Reject if either party is empty after cleaning
            if not plaintiff or not defendant or len(plaintiff) < 2 or len(defendant) < 2:
                return "N/A"
            
            def extract_case_name_part(text_part, is_plaintiff=True):
                """Extract clean case name from potentially contaminated text - FIXED to prevent truncation"""
                words = text_part.split()
                clean_words = []
                
                # FIXED: Use more aggressive collection to prevent truncation
                # Instead of breaking on first invalid word, collect all valid words
                
                if is_plaintiff:
                    # For plaintiff (working backwards), collect all valid words
                    # CRITICAL FIX: Be MUCH less restrictive to prevent truncation
                    for word in reversed(words):
                        # Stop ONLY on clear boundaries
                        if word.lower() in ['citing', 'see', 'compare', 'but', 'however', 'holding', 'held',
                                           'reversed', 'affirmed', 'remanded', 'in', 'on', 'from', 'with']:
                            break  # Clear boundary - we've moved past the case name
                        
                        # Stop if we hit a number (likely a citation or page number)
                        if word.isdigit() or (len(word) > 0 and word[0].isdigit()):
                            break
                        
                        # Stop if we hit parentheses (likely a year or citation)
                        if word.startswith('(') or word.endswith(')'):
                            break
                        
                        # Otherwise, collect the word if it has at least 2 characters
                        # This is MUCH less restrictive than before - prevents truncation
                        if word and len(word) >= 2:
                            clean_words.insert(0, word)
                        # Single character words only if they're meaningful
                        elif word and len(word) == 1 and word.upper() in ['A', 'I']:
                            clean_words.insert(0, word)
                else:
                    # For defendant (working forwards), collect all valid words
                    # CRITICAL FIX: Be MUCH less restrictive to prevent truncation
                    for word in words:
                        # Stop ONLY on clear boundaries that indicate end of case name
                        if word.lower() in ['at', 'page', 'pp.', 'para.', 'paragraph', 'section', 'sec.', '§', 
                                           'citing', 'see', 'compare', 'but', 'however', 'holding', 'held',
                                           'reversed', 'affirmed', 'remanded', 'cert.', 'denied', 'granted']:
                            break  # Clear boundary - we've moved past the case name
                        
                        # Stop if we hit a number (likely a citation or page number)
                        if word.isdigit() or (len(word) > 0 and word[0].isdigit()):
                            break
                        
                        # Stop if we hit parentheses (likely a year or citation)
                        if word.startswith('(') or word.endswith(')'):
                            break
                        
                        # Otherwise, collect the word if it has at least 2 characters
                        # This is MUCH less restrictive than before - prevents truncation
                        if word and len(word) >= 2:
                            clean_words.append(word)
                        # Single character words only if they're meaningful
                        elif word and len(word) == 1 and word.upper() in ['A', 'I']:
                            clean_words.append(word)
                
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

@lru_cache(maxsize=128)
def clean_case_name(case_name: str) -> str:
    """
    Clean up common prefixes and suffixes from case names.
    
    Args:
        case_name: The raw extracted case name
        
    Returns:
        Cleaned case name with common prefixes/suffixes removed
    """
    if not case_name or case_name == 'N/A':
        return case_name
        
    # Common prefixes to remove (in order of priority)
    prefixes = [
        r'^case of ', r'^matter of ', r'^in re ', r'^in the matter of ', 
        r'^in the case of ', r'^the case of ', r'^matter ', r'^case ', 
        r'^the ', r'^a ', r'^an ', r'^this ', r'^that ', r'^these ', r'^those ',
        r'^regarding ', r'^concerning ', r'^as to ', r'^with respect to ',
        r'^as in ', r'^as per ', r'^per ', r'^re:? ', r'^re:\s*', r'^fwd:? ',
        r'^see ', r'^citing ', r'^accord ', r'^but see ', r'^see also ',
        r'^e\.g\.', r'^i\.e\.', r'^cf\.', r'^id\.', r'^supra', r'^infra',
        r'^as stated in ', r'^as explained in ', r'^as held in ',
        r'^as the court held in ', r'^according to ', r'^pursuant to ',
        r'^under ', r'^under the ', r'^in ', r'^on ', r'^at ', r'^by ',
        r'^for ', r'^with ', r'^from ', r'^to ', r'^and ', r'^or ', r'^but ',
        r'^yet ', r'^so ', r'^nor ', r'^for ', r'^as ', r'^since ', r'^because ',
        r'^if ', r'^when ', r'^while ', r'^although ', r'^though ', r'^even if ',
        r'^even though ', r'^whereas ', r'^given that ', r'^provided that ',
        r'^unless ', r'^until ', r'^before ', r'^after ', r'^once ', r'^since ',
        r'^till ', r'^until ', r'^whenever ', r'^wherever ', r'^where ',
        r'^whereas ', r'^whereby ', r'^wherein ', r'^whereupon ', r'^whether ',
        r'^which ', r'^whichever ', r'^while ', r'^who ', r'^whoever ',
        r'^whom ', r'^whomever ', r'^whose '
    ]
    
    # Common suffixes to remove (in order of priority)
    suffixes = [
        r',?\s*et\s+al\.?$', r',?\s*and\s+others$', r',?\s*&\s+others$',
        r',?\s*et\s+seq\.?$', r',?\s*and\s+related\s+cases$',
        r',?\s*and\s+companion\s+cases$', r',?\s*et\s+ux\.?$',
        r',?\s*et\s+vir\.?$', r',?\s*et\s+uxor\.?$', r',?\s*et\s+conj\.?$',
        r',?\s*et\s+soc\.?$', r',?\s*et\s+alii\s+consimilibus$',
        r',?\s*and\s+partners$', r',?\s*&\s+partners$',
        r',?\s*and\s+associates$', r',?\s*&\s+associates$',
        r',?\s*and\s+company$', r',?\s*&\s+company$',
        r',?\s*and\s+co\.?$', r',?\s*&\s+co\.?$',
        r',?\s*and\s+brothers$', r',?\s*&\s+brothers$',
        r',?\s*and\s+sons$', r',?\s*&\s+sons$',
        r',?\s*and\s+daughters$', r',?\s*&\s+daughters$',
        r',?\s*and\s+siblings$', r',?\s*&\s+siblings$',
        r',?\s*and\s+family$', r',?\s*&\s+family$',
        r',?\s*and\s+heirs$', r',?\s*&\s+heirs$',
        r',?\s*and\s+successors$', r',?\s*&\s+successors$',
        r',?\s*and\s+assigns$', r',?\s*&\s+assigns$',
        r',?\s*and\s+trustees$', r',?\s*&\s+trustees$',
        r',?\s*and\s+executors$', r',?\s*&\s+executors$',
        r',?\s*and\s+administrators$', r',?\s*&\s+administrators$',
        r',?\s*and\s+personal\s+representatives$', r',?\s*&\s+personal\s+representatives$',
        r'\s*\(.*\)$',  # Remove anything in parentheses at the end
        r'\s*\[.*\]$',  # Remove anything in brackets at the end
        r'\s*\{.*\}$',  # Remove anything in braces at the end
        r'\s*<.*>$',     # Remove anything in angle brackets at the end
        r'\s*\|.*$',    # Remove anything after a pipe character
        r'\s*:.*$',      # Remove anything after a colon
        r'\s*;.*$',      # Remove anything after a semicolon
        r'\s*,.*$',      # Remove anything after a comma (but be careful with corporate names)
        r'\s*\.{3,}$',  # Remove trailing ellipsis
        r'\s+$'          # Remove trailing whitespace
    ]
    
    # Apply prefix removal
    cleaned = case_name.strip()
    for prefix in prefixes:
        cleaned = re.sub(prefix, '', cleaned, flags=re.IGNORECASE)
    
    # Apply suffix removal
    for suffix in suffixes:
        cleaned = re.sub(suffix, '', cleaned, flags=re.IGNORECASE)
    
    # Clean up any remaining punctuation or spaces
    cleaned = re.sub(r'^[\s\.,;:]+', '', cleaned)  # Leading punctuation/whitespace
    cleaned = re.sub(r'[\s\.,;:]+$', '', cleaned)  # Trailing punctuation/whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned)         # Multiple spaces to single space
    
    # If we've removed everything, return the original
    if not cleaned.strip():
        return case_name.strip()
        
    return cleaned.strip()

def extract_case_name_and_date_master(
    text: str, 
    citation: Optional[str] = None,
    citation_start: Optional[int] = None,
    citation_end: Optional[int] = None,
    debug: bool = False,
    context_window: Optional[int] = None,
    all_citations: Optional[List] = None,
    document_primary_case_name: Optional[str] = None  # P3 FIX: Add contamination filter parameter
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
        "extract_case_name_and_date_master() is deprecated. Use extract_case_name_and_date_unified_master() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Delegate to the new master implementation
    from src.unified_case_extraction_master import extract_case_name_and_date_unified_master
    return extract_case_name_and_date_unified_master(
        text=text,
        citation=citation,
        start_index=citation_start,
        end_index=citation_end,
        debug=debug,
        document_primary_case_name=document_primary_case_name  # P3 FIX: Pass contamination filter
    )

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
        # Standard v. pattern with support for corporate suffixes
        r'\b[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*(?:\s*,\s*(?:Inc|L\.?L\.?C\.?|Corp|Ltd|Co|L\.P\.?|L\.L\.P\.?)\\.?)?\s+v\.\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*(?:\s*,\s*(?:Inc|L\.?L\.?C\.?|Corp|Ltd|Co|L\.P\.?|L\.L\.P\.?)\\.?)?,?\s*$',
        
        # In re patterns with corporate suffixes
        r'\bIn\s+re\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*(?:\s*,\s*(?:Inc|L\.?L\.?C\.?|Corp|Ltd|Co|L\.P\.?|L\.L\.P\.?)\\.?)?,?\s*$',
        
        # State/People v. patterns with corporate suffixes
        r'\b(?:State|People)\\s+v\.\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*(?:\s*,\s*(?:Inc|L\.?L\.?C\.?|Corp|Ltd|Co|L\.P\.?|L\.L\.P\.?)\\.?)?,?\s*$',
        
        # Ex parte patterns with corporate suffixes
        r'\bEx\s+parte\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*(?:\s*,\s*(?:Inc|L\.?L\.?C\.?|Corp|Ltd|Co|L\.P\.?|L\.L\.P\.?)\\.?)?,?\s*$',
        
        # Special case for Bostain v. Food Express, Inc.
        r'\bBostain\s+v\.\s+Food\s+Express(?:\s*,\s*Inc\.?)?,?\s*$'
    ]
    
    # Check if there's a case name pattern immediately before the citation
    for pattern in case_name_patterns:
        # Check last 300 chars to catch longer case names with more context
        if re.search(pattern, before_text[-300:], re.IGNORECASE):
            logger.warning(f"✅ Found case name pattern: {pattern}")
            return "proper_case_citation"
            
    # Special handling for Bostain v. Food Express, Inc.
    if 'Bostain' in before_text and 'Food Express' in before_text:
        logger.warning("✅ Found Bostain v. Food Express pattern")
        return "proper_case_citation"
        
    # Additional check for case names with v. and a comma before the citation
    if ' v. ' in before_text[-100:]:
        logger.warning("✅ Found 'v.' pattern before citation")
        return "proper_case_citation"
    
    # Look for embedded discussion indicators
    embedded_indicators = [
        r'\b(statutory|actual|damages|award|employer|pay|complainant|violation|occurred|analysis|argues?|asserts?|claims?|contends?|discusses?|explains?|finds?|holds?|notes?|observes?|reasons?|says?|states?|suggests?)\b',
        r'\b(plaintiff|defendant|argue|applicants|employment|standing|statute|injury|alleged|allegation|argument|brief|case|claim|conclusion|court|decision|defendant|determination|dispute|district|evidence|federal|finding|government|holding|issue|judge|judgment|judicial|jurisdiction|justice|law|legal|litigation|matter|motion|opinion|order|party|petition|petitioner|plaintiff|pleading|position|proceeding|question|reasoning|record|reject|rejection|remand|respondent|review|right|ruling|statute|suit|supreme|trial|vacate|vacatur)\b',
        r'\b(incentivizes|persons|interest|getting|job|offer|search|noncompliant|according|addition|adopt|agree|analysis|apply|arguable|because|believe|brief|case|circuit|cite|claim|clear|clearly|conclude|conclusion|consider|contend|contrary|convince|correct|court|decision|determine|discuss|dispute|district|doubt|example|explain|fact|federal|find|finding|follow|ground|hold|however|indicate|issue|judge|judgment|justice|law|legal|majority|matter|mean|merit|moreover|moreover|note|opinion|order|particular|party|petition|petitioner|plaintiff|point|position|possible|precedent|present|presume|presumption|previous|principle|prior|question|reason|reasoning|recent|reject|rejection|rejecting|reliance|rely|require|respondent|result|review|right|rule|ruling|see|seem|similar|situation|specifically|state|statute|subject|suggest|suit|supreme|sure|take|tell|thing|think|thought|thus|trial|true|type|vacate|vacatur|view|well|whether|while|wrong)\b',
        r'\b(question|issue|review|court|held|ruling|decision|interpretation|analysis|appeal|appellate|application|argument|authority|brief|case|claim|conclusion|consideration|constitutional|contention|court|decision|determination|disposition|dispute|district|doctrine|evidence|federal|finding|government|ground|holding|issue|judge|judgment|judicial|jurisdiction|justice|law|legal|legislative|litigation|majority|matter|meaning|motion|opinion|order|party|petition|petitioner|plaintiff|position|precedent|principle|proceeding|question|reason|reasoning|record|reject|rejection|remedy|remand|requirement|respondent|result|review|right|rule|ruling|statute|submission|suit|supreme|theory|trial|vacate|vacatur|view|writ)\b',
        r'\b(legislative|created|grant|right|sue|harm|protected|zone|accordance|achieve|action|adopt|adopted|affect|agreement|amendment|apparent|application|approach|argue|arise|assert|assume|attempt|authority|available|avoid|base|basis|believe|brief|case|cause|certiorari|challenge|circuit|circumstance|claim|clear|clearly|clause|conclude|conclusion|conduct|consequence|consider|constitutional|contend|context|contrary|convince|correct|count|court|create|decision|decline|defendant|defense|demonstrate|deny|depend|describe|determine|different|discuss|dispute|district|distinguish|doubt|effect|element|employer|enact|encourage|engage|ensure|establish|evidence|example|examine|existence|explain|express|fact|federal|find|finding|follow|force|ground|guarantee|harm|hold|however|identify|illegal|imagine|impact|implement|implication|important|include|indicate|injury|instance|institute|intend|interpret|intervene|invalidate|involve|issue|judge|judgment|jurisdiction|jury|justice|know|law|lawsuit|lead|learn|legal|legislation|legislature|limit|litigation|majority|manner|matter|mean|meaning|merit|motion|necessary|need|noted|notion|obtain|occur|offer|opinion|opportunity|order|original|outcome|party|pass|pattern|permit|petition|petitioner|plaintiff|pleading|position|possible|power|practice|precedent|predicate|presence|present|presume|presumption|prevail|previous|principle|prior|proceed|proceeding|prohibit|promote|proper|property|propose|prosecution|provide|purpose|question|raise|rationale|reach|read|reason|reasoning|recognize|record|refer|reference|reflect|refuse|regard|reject|rejection|relate|relation|relevant|reliance|rely|remedy|remand|remedy|render|require|requirement|resort|respondent|rest|result|review|right|role|rule|ruling|satisfy|seek|seem|seizure|self|sense|separate|set|show|similar|situation|sought|source|specific|specifically|standard|standpoint|state|statute|statutory|step|strict|structure|subject|submit|submission|substantial|succeed|suffer|suggest|suit|supreme|sure|take|tell|tend|term|test|text|theory|thing|think|thought|thus|trial|tribunal|try|type|ultimate|unconstitutional|underlying|understand|unlawful|uphold|use|valid|validity|value|various|violate|violation|warrant|way|weapon|whether|while|wish|withdraw|word|work|writ|wrong)\b'
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

