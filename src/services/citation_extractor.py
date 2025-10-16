"""
DEPRECATED: Use `src.citation_extractor.CitationExtractor` instead.

This module previously provided a separate citation extractor service. The project now
standardizes on `src.citation_extractor.CitationExtractor` and `EnhancedSyncProcessor`
for extraction + propagation + clustering. Keep this module only for historical
reference; new code should not import from `src.services.citation_extractor`.
"""

import re
from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

import json
import os
import logging
from typing import List, Dict, Any, Optional, Tuple

try:
    import warnings as _warnings
    _warnings.warn(
        "src.services.citation_extractor is deprecated; use src.citation_extractor.CitationExtractor",
        DeprecationWarning,
        stacklevel=2,
    )
except Exception:
    pass
from dataclasses import dataclass
import unicodedata
from pathlib import Path

from .interfaces import ICitationExtractor, CitationResult, ProcessingConfig

logger = logging.getLogger(__name__)

try:
    from eyecite import get_citations
    from eyecite.tokenizers import AhocorasickTokenizer
    EYECITE_AVAILABLE = True
    logger.info("Eyecite successfully imported for CitationExtractor")
except ImportError as e:
    EYECITE_AVAILABLE = False
    logger.warning(f"Eyecite not available - install with: pip install eyecite. Error: {e}")

ADAPTIVE_LEARNING_AVAILABLE = False
AdaptiveLearningService = None  # type: ignore
create_adaptive_learning_service = None  # type: ignore

try:
    from .adaptive_learning_service import AdaptiveLearningService as ImportedAdaptiveLearningService, create_adaptive_learning_service as imported_create_service
    ADAPTIVE_LEARNING_AVAILABLE = True
    AdaptiveLearningService = ImportedAdaptiveLearningService  # type: ignore
    create_adaptive_learning_service = imported_create_service  # type: ignore
    logger.info("Adaptive learning service available for CitationExtractor")
except ImportError as e:
    logger.info("Adaptive learning service not available - using basic extraction only")
    class AdaptiveLearningService:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass
        def is_enabled(self):
            return False
        def enhance_citation_extraction(self, *args, **kwargs):  # type: ignore
            from dataclasses import dataclass
            @dataclass
            class DummyResult:
                improved_citations: Optional[List[Any]] = None
                learned_patterns: Optional[List[Any]] = None
                confidence_adjustments: Optional[Dict[str, Any]] = None
                case_name_mappings: Optional[Dict[str, Any]] = None
                performance_metrics: Optional[Dict[str, Any]] = None
                
                def __post_init__(self):
                    if self.improved_citations is None:
                        self.improved_citations = []
                    if self.learned_patterns is None:
                        self.learned_patterns = []
                    if self.confidence_adjustments is None:
                        self.confidence_adjustments = {}
                    if self.case_name_mappings is None:
                        self.case_name_mappings = {}
                    if self.performance_metrics is None:
                        self.performance_metrics = {}
            return DummyResult(improved_citations=[], learned_patterns=[], confidence_adjustments={}, case_name_mappings={}, performance_metrics={})
    
    def create_adaptive_learning_service(*args, **kwargs):  # type: ignore
        return AdaptiveLearningService()


class CitationExtractor(ICitationExtractor):
    """
    Pure citation extraction service using regex and eyecite methods.
    
    This service is responsible for:
    - Finding citation patterns in text
    - Extracting basic citation metadata
    - Normalizing citation formats
    - Context extraction for case names and dates
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the citation extractor with optional configuration."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.reporters = self._load_reporters()
        self.citation_pattern = None  # Will be initialized in _init_patterns
        self._init_patterns()
        self._init_case_name_patterns()
        self._init_date_patterns()
        
        self.adaptive_learning = None
        if ADAPTIVE_LEARNING_AVAILABLE and self.config.get('enable_adaptive_learning', True):
            try:
                self.adaptive_learning = create_adaptive_learning_service()
                if self.config.get('debug_mode', False):
                    logger.info(f"Adaptive learning enabled: {self.adaptive_learning.is_enabled()}")
            except Exception as e:
                logger.warning(f"Failed to initialize adaptive learning: {e}")
                self.adaptive_learning = None
        
        if self.config.get('debug_mode', False):
            logger.info(f"CitationExtractor initialized with eyecite: {EYECITE_AVAILABLE}, adaptive learning: {self.adaptive_learning is not None}")
    
    def _load_reporters(self) -> List[Dict[str, Any]]:
        """Load reporter patterns from the data file."""
        try:
            reporters_file = Path(__file__).parent / "data" / "reporters.json"
            if reporters_file.exists():
                with open(reporters_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    reporters = data.get('reporters', [])
                self.logger.info(f"Loaded {len(reporters)} reporter patterns")
                return reporters
            else:
                self.logger.warning(f"Reporters file not found: {reporters_file}")
                return []
        except Exception as e:
            self.logger.error(f"Error loading reporters: {e}")
            return []
    
    def _init_patterns(self) -> None:
        """Initialize citation patterns from loaded reporter data."""
        if not self.reporters:
            self.logger.warning("No reporter patterns loaded, using fallback patterns")
            self._init_fallback_patterns()
            return
            
        jurisdiction_patterns = {}
        
        for reporter in self.reporters:
            jurisdiction = reporter.get('jurisdiction', 'other')
            if jurisdiction not in jurisdiction_patterns:
                jurisdiction_patterns[jurisdiction] = []
                
            jurisdiction_patterns[jurisdiction].extend(reporter.get('patterns', []))
        
        self.patterns = {}
        
        for jurisdiction, patterns in jurisdiction_patterns.items():
            if patterns:
                try:
                    self.patterns[jurisdiction] = re.compile(
                        '|'.join(patterns),
                        re.IGNORECASE
                    )
                    self.logger.debug(f"Compiled {len(patterns)} patterns for {jurisdiction}")
                except re.error as e:
                    self.logger.error(f"Error compiling {jurisdiction} patterns: {str(e)}")
        
        all_patterns = []
        for patterns in jurisdiction_patterns.values():
            all_patterns.extend(patterns)
        
        # Add Westlaw (WL) citation patterns
        # Format: YYYY WL #######
        wl_pattern = r'\b(\d{4}\s+WL\s+\d+)\b'
        all_patterns.append(wl_pattern)
        self.logger.debug("Added Westlaw (WL) citation pattern")
            
        if all_patterns:
            try:
                self.patterns['all'] = re.compile(
                    '|'.join(all_patterns),
                    re.IGNORECASE
                )
                self.logger.info(f"Compiled {len(all_patterns)} total patterns")
            except re.error as e:
                self.logger.error(f"Error compiling combined patterns: {str(e)}")
                self._init_fallback_patterns()
        else:
            self._init_fallback_patterns()
    
    def _init_fallback_patterns(self) -> None:
        """Initialize fallback patterns when reporter data is not available."""
        self.logger.warning("Initializing fallback citation patterns")
        
        federal_patterns = [
            r'\b\d+\s+U\.\s+S\.\s+\d+',           # U.S. Reports
            r'\b\d+\s+S\.\s*Ct\.\s+\d+',       # Supreme Court Reporter
            r'\b\d+\s+L\.\s*Ed\.\s*2d\s+\d+',  # Lawyers' Edition
            r'\b\d+\s+F\.\s*3d\s+\d+',         # Federal Reporter 3d
            r'\b\d+\s+F\.\s*2d\s+\d+',         # Federal Reporter 2d
            r'\b\d+\s+F\.\s+\d+',              # Federal Reporter
            r'\b\d+\s+F\.\s*Supp\.\s*3d\s+\d+', # Federal Supplement 3d
            r'\b\d+\s+F\.\s*Supp\.\s*2d\s+\d+', # Federal Supplement 2d
            r'\b\d+\s+F\.\s*Supp\.\s+\d+'      # Federal Supplement
        ]
        
        # Enhanced Washington state citation patterns
        # These patterns handle various formats of Washington state citations
        # including different spacing, punctuation, and reporter abbreviations
        
        # Base components
        volume = r'(\d+)'  # Volume number
        reporter_wn = r'([Ww][Nn]\.?)'  # Wn or Wn.
        reporter_wash = r'([Ww][Aa][Ss][Hh]\.?)'  # Wash or Wash.
        series = r'(2d|3d|4th|App\.?)'  # Series (2d, 3d, 4th, App, App.)
        page = r'(\d+)'  # Page number
        
        # Common separators (space, comma, period, etc.)
        sep = r'[\s,\.\-]*'
        
        # Build patterns for different citation formats
        patterns = [
            # Format: 123 Wn.2d 456
            fr'\b{volume}{sep}{reporter_wn}{sep}{series}{sep}{page}\b',
            
            # Format: 123 Wn 2d 456 (with spaces)
            fr'\b{volume}{sep}{reporter_wn}{sep}{series[:1]}{sep}\d+{sep}{page}\b',
            
            # Format: 123Wn.2d456 (no spaces)
            fr'\b{volume}{reporter_wn}{series}{page}\b',
            
            # Format: 123 Wn. App. 456 (with App.)
            fr'\b{volume}{sep}{reporter_wn}{sep}App\.{sep}{page}\b',
            
            # Format: 123WnApp456 (no spaces with App)
            fr'\b{volume}{reporter_wn}App{page}\b',
            
            # Format: 123 Wash. 2d 456 (full word with spaces)
            fr'\b{volume}{sep}{reporter_wash}{sep}{series[:1]}{sep}\d+{sep}{page}\b',
            
            # Format: 123Wash.2d456 (full word, no spaces)
            fr'\b{volume}{reporter_wash}{series}{page}\b',
            
            # Format: 123 Wn. 456 (no series)
            fr'\b{volume}{sep}{reporter_wn}{sep}{page}\b',
            
            # Format: 123Wn456 (no series, no spaces)
            fr'\b{volume}{reporter_wn}{page}\b',
            
            # Format: 123 Wash. 456 (full word, no series)
            fr'\b{volume}{sep}{reporter_wash}{sep}{page}\b',
            
            # Format: 123Wash456 (full word, no series, no spaces)
            fr'\b{volume}{reporter_wash}{page}\b'
        ]
        
        # Combine all patterns into a single pattern with non-capturing groups
        state_patterns = [f'(?:{p})' for p in patterns]
        
        # Add other standard citation patterns
        state_patterns.extend([
            r'\b\d+\s+A\.\s*3d\s+\d+',
            r'\b\d+\s+A\.\s*2d\s+\d+',
            r'\b\d+\s+P\.\s*3d\s+\d+',
            r'\b\d+\s+P\.\s*2d\s+\d+',
            r'\b\d+\s+N\.E\.\s*3d\s+\d+',
            r'\b\d+\s+N\.E\.\s*2d\s+\d+',
            r'\b\d+\s+N\.W\.\s*2d\s+\d+',
            r'\b\d+\s+S\.E\.\s*2d\s+\d+',
            r'\b\d+\s+S\.W\.\s*3d\s+\d+',
            r'\b\d+\s+S\.W\.\s*2d\s+\d+'
        ])
        
        all_patterns = federal_patterns + state_patterns
        
        try:
            self.patterns = {
                'federal': re.compile('|'.join(federal_patterns), re.IGNORECASE),
                'state': re.compile('|'.join(state_patterns), re.IGNORECASE),
                'all': re.compile('|'.join(all_patterns), re.IGNORECASE)
            }
            self.logger.info("Initialized fallback patterns")
        except re.error as e:
            self.logger.error(f"Failed to initialize fallback patterns: {str(e)}")
            raise
    
    def _init_case_name_patterns(self) -> None:
        """Initialize case name extraction patterns."""
        # CRITICAL FIX: Do NOT use re.IGNORECASE with [A-Z] patterns!
        # IGNORECASE makes [A-Z] match lowercase too, causing it to match mid-word like "Ass'n" -> matches 'n'
        # Also must include unicode characters (\w) to handle special chars like 'Æ' in "AssÆn"
        # Must handle unicode quotes (ö, \u201d, \u02bc, etc) as sentence boundaries
        # Pattern: Match the last reasonable case name before the citation
        # Look for: Capital letter, then anything (including abbreviated words with periods)
        # up to " v. ", then the second party name
        # Must include both ' (U+0027 ASCII apostrophe) and ' (U+2019 smart quote) for abbreviations like "Ass'n"
        party_pattern = r'[A-Z][\w\s&,\.\'\u2019\-]+'
        
        self.case_name_patterns = [
            # Standard "X v. Y" pattern
            # Match the last occurrence of "Something v. Something" before comma or number
            re.compile(
                r'(' + party_pattern + r')\s+v\.\s+(' + party_pattern + r')(?=\s*,|\s*\d)',
                re.UNICODE
            ),
            
            # In re patterns
            re.compile(
                r'In\s+re\s+(' + party_pattern + r')(?=\s*,|\s*\d)',
                re.IGNORECASE | re.UNICODE
            ),
            
            # Ex parte patterns
            re.compile(
                r'Ex\s+parte\s+(' + party_pattern + r')(?=\s*,|\s*\d)',
                re.IGNORECASE | re.UNICODE
            ),
            
            # Matter of patterns
            re.compile(
                r'Matter\s+of\s+(' + party_pattern + r')(?=\s*,|\s*\d)',
                re.IGNORECASE | re.UNICODE
            )
        ]
    
    def _init_date_patterns(self) -> None:
        """Initialize date extraction patterns."""
        self.date_patterns = [
            re.compile(r'\((\d{4})\)'),
            
            re.compile(r'\b(\d{4})\b'),
            
            re.compile(r'\b(\d{1,2}/\d{1,2}/\d{4})\b'),
            re.compile(r'\b(\d{4}-\d{2}-\d{2})\b')
        ]
    
    def extract_citations(self, text: str, document_name: str = "") -> List[CitationResult]:
        """
        Extract citations from text using regex, eyecite, and adaptive learning methods.
        
        Args:
            text: The text to extract citations from
            document_name: Optional document identifier for adaptive learning
            
        Returns:
            List of CitationResult objects with enhanced extraction data
        """
        citations = []
        
        regex_citations = self._extract_with_regex(text)
        citations.extend(regex_citations)
        
        if EYECITE_AVAILABLE and self.config.get('use_eyecite', True):
            eyecite_citations = self._extract_with_eyecite(text)
            citations.extend(eyecite_citations)
        
        citations = self._deduplicate_citations(citations)
        
        # CRITICAL FIX: Must update citations in-place, not assign to local variable
        for i in range(len(citations)):
            citations[i] = self.extract_metadata(citations[i], text)
        
        if self.adaptive_learning and self.adaptive_learning.is_enabled():
            try:
                adaptive_result = self.adaptive_learning.enhance_citation_extraction(
                    text, document_name, citations
                )
                
                improved_citations = adaptive_result.improved_citations
                if improved_citations is not None:
                    citations = improved_citations
                
                if self.config.get('debug_mode', False):
                    learned_patterns = adaptive_result.learned_patterns or []
                    confidence_adjustments = adaptive_result.confidence_adjustments or {}
                    logger.info(f"Adaptive learning found {len(learned_patterns)} new patterns")
                    logger.info(f"Confidence adjustments: {len(confidence_adjustments)}")
                    
            except Exception as e:
                logger.warning(f"Error in adaptive learning enhancement: {e}")
        
        if self.config.get('debug_mode', False):
            logger.info(f"CitationExtractor found {len(citations)} citations (with adaptive learning: {self.adaptive_learning is not None})")
        
        return citations
    
    def extract_metadata(self, citation: CitationResult, text: str) -> CitationResult:
        """
        Extract metadata (case name, date, context) for a citation.
        
        Args:
            citation: Citation to extract metadata for
            text: Full text for context extraction
            
        Returns:
            Updated CitationResult with metadata
        """
        try:
            logger.warning(f"[META-EXTRACT] Processing {citation.citation}, existing name: {getattr(citation, 'extracted_case_name', 'None')}")
            
            case_name = self._extract_case_name_from_context(text, citation)
            logger.warning(f"[META-EXTRACT] Function returned: {case_name}")
            
            if case_name:
                citation.extracted_case_name = case_name
                logger.warning(f"[META-EXTRACT] Set extracted_case_name to: {case_name[:50]}...")
            
            date = self._extract_date_from_context(text, citation)
            if date:
                citation.extracted_date = date
            
            context = self._extract_context(text, citation.start_index or 0, citation.end_index or 0)
            if context:
                citation.context = context
            
            citation.confidence = self._calculate_confidence(citation, text)
            
        except Exception as e:
            logger.warning(f"Error extracting metadata for citation {citation.citation}: {e}")
        
        return citation
    
    def _extract_with_regex(self, text: str) -> List[CitationResult]:
        """Extract citations using regex patterns."""
        citations = []
        
        if self.config.get('debug_mode', False):
            logger.info(f"Extracting citations from text with length: {len(text)}")
        
        for match in self.patterns['all'].finditer(text):
            citation_text = match.group(0).strip()
            start_index = match.start(0)
            end_index = match.end(0)
            
            if self.config.get('debug_mode', False):
                logger.info(f"Found citation: {citation_text} at position {start_index}-{end_index}")
            
            citation = CitationResult(
                citation=citation_text,
                start_index=start_index,
                end_index=end_index,
                method="regex",
                pattern=self._get_matching_pattern(citation_text),
                confidence=0.8  # Base confidence for regex matches
            )
            
            citations.append(citation)
        
        if self.config.get('debug_mode', False):
            logger.info(f"Extracted {len(citations)} citations using regex")
        
        return citations
    
    def _extract_with_eyecite(self, text: str) -> List[CitationResult]:
        """Extract citations using eyecite library."""
        if not EYECITE_AVAILABLE:
            return []
        
        citations = []
        
        try:
            found_citations = get_citations(text)
            
            for eyecite_citation in found_citations:
                # CRITICAL FIX: Use original text from document, not eyecite's normalized version
                # Eyecite normalizes "Wn.2d" → "Wash.2d", but these are DIFFERENT citations
                # in CourtListener! We must preserve the exact text from the document.
                
                # First, try to get the span from eyecite
                start_index = None
                end_index = None
                citation_text = None
                
                if hasattr(eyecite_citation, 'span'):
                    # eyecite provides (start, end) span
                    start_index = eyecite_citation.span[0]
                    end_index = eyecite_citation.span[1]
                    citation_text = text[start_index:end_index].strip()
                
                # Fallback: use normalized text and find it in the document
                if not citation_text:
                    citation_text = self._extract_citation_text_from_eyecite(eyecite_citation)
                    start_index = text.find(citation_text)
                    end_index = start_index + len(citation_text) if start_index != -1 else 0
                
                citation = CitationResult(
                    citation=citation_text,
                    start_index=start_index if start_index is not None else 0,
                    end_index=end_index if end_index is not None else 0,
                    method="eyecite",
                    confidence=0.9  # Higher confidence for eyecite
                )
                
                self._extract_eyecite_metadata(citation, eyecite_citation)
                
                citations.append(citation)
                
        except Exception as e:
            logger.warning(f"Error in eyecite extraction: {e}")
        
        return citations
    
    def _extract_citation_text_from_eyecite(self, citation_obj) -> str:
        """Extract citation text from eyecite object."""
        try:
            if hasattr(citation_obj, 'corrected_citation_full'):
                return citation_obj.corrected_citation_full
            elif hasattr(citation_obj, 'corrected_citation'):
                return citation_obj.corrected_citation
            elif hasattr(citation_obj, 'cite'):
                return citation_obj.cite
            elif hasattr(citation_obj, 'text'):
                return citation_obj.text
            else:
                if hasattr(citation_obj, 'groups') and citation_obj.groups:
                    groups = citation_obj.groups()
                    if len(groups) >= 3:  # volume, reporter, page
                        return f"{groups[0]} {groups[1]} {groups[2]}"
                text = str(citation_obj)
                if not text.startswith(('FullCaseCitation(', 'ShortCaseCitation(', 'SupraCitation(')):
                    return text
                return ''
        except Exception as e:
            logger.warning(f"Error extracting citation text from eyecite object: {e}")
            return ''
    
    def _extract_eyecite_metadata(self, citation: CitationResult, citation_obj) -> None:
        """Extract metadata from eyecite citation object."""
        try:
            if hasattr(citation_obj, 'court'):
                citation.court = str(citation_obj.court)
            
            if hasattr(citation_obj, 'year') and citation_obj.year:
                citation.extracted_date = str(citation_obj.year)
            
            if hasattr(citation_obj, 'reporter'):
                citation.metadata = citation.metadata or {}
                citation.metadata['reporter'] = str(citation_obj.reporter)
                
        except Exception as e:
            logger.warning(f"Error extracting eyecite metadata: {e}")
    
    def _extract_case_name_from_context(self, text: str, citation: CitationResult) -> Optional[str]:
        """Extract case name from the context around a citation.
        
        CRITICAL: This method must extract the MAIN case name, not parenthetical citations.
        Example: "State v. M.Y.G., 199 Wn.2d 528 (2022) (quoting Am. Legion...)"
        Should extract: "State v. M.Y.G." NOT "Am. Legion"
        """
        logger.warning(f"[EXTRACT-START] Called for citation: {citation.citation if hasattr(citation, 'citation') else 'unknown'}")
        
        if not citation.start_index:
            logger.warning("[EXTRACT-START] No start_index, returning None")
            return None
        
        # CRITICAL FIX: Need at least 200 chars to capture full case names
        # Case names can be 80-100 characters long (e.g. "Ass'n of Wash. Spirits & Wine Distribs. v. Wash. State Liquor Control Bd.")
        start_search = max(0, citation.start_index - 200)
        search_text = text[start_search:citation.start_index]
        
        # FIX #27: Additional debug info to diagnose proximity extraction issues
        citation_text = citation.citation if hasattr(citation, 'citation') else 'unknown'
        logger.warning(f"[EXTRACT-FIX27] Citation: {citation_text} at position [{start_search}:{citation.start_index}]")
        logger.warning(f"[EXTRACT-FIX27] Next 50 chars after citation: '{text[citation.start_index:citation.start_index+50]}'")
        logger.warning(f"[EXTRACT-START] Searching {len(search_text)} chars before citation")
        logger.warning(f"[EXTRACT-START] Search text (last 100): '{search_text[-100:]}'")
        
        # CRITICAL FIX: Remove parenthetical content BEFORE searching for case names
        # This prevents extracting parenthetical citations like "(quoting Am. Legion...)"
        # which should NOT be treated as the main case name
        import re
        original_search_text = search_text
        
        # Track positions of parentheticals for distance calculation
        paren_positions = []
        for match in re.finditer(r'\([^)]*\)', search_text):
            paren_positions.append((match.start(), match.end()))
        
        # Remove parentheticals from search text
        search_text_no_parens = re.sub(r'\([^)]*\)', '', search_text)
        
        # Also check if we're in the middle of a citation string
        # E.g., "199 Wn.2d 528, 532, 509 P.3d 818" - don't extract from between citations
        # Look for pattern: citation_number, page_numbers, citation (current position)
        if re.search(r'\d+\s+[A-Za-z\.]+\s+\d+(?:,\s*\d+)*\s*$', search_text_no_parens):
            # We're in a multi-citation cluster, search earlier for the case name
            logger.warning("[EXTRACT-DEBUG] Detected multi-citation cluster, extending search")
            # Try to find the case name before the first citation in this cluster
            # Look for the last "v." before any numbers
            match = re.search(r'(.+?\s+v\.\s+.+?)\s*,?\s*\d+\s+[A-Za-z\.]+', search_text_no_parens)
            if match:
                case_name = match.group(1).strip()
                logger.warning(f"[EXTRACT-DEBUG] Extracted from multi-citation: '{case_name[:80]}...'")
                # Clean and return
                case_name = re.sub(r'\s+', ' ', case_name)
                return case_name
        
        logger.warning(f"[EXTRACT-START] Search text after removing parentheticals (last 100): '{search_text_no_parens[-100:]}'")
        logger.warning(f"[EXTRACT-START] Have {len(self.case_name_patterns)} patterns")
        
        # Find all potential case names and score them by position (prefer closer to citation)
        candidates = []
        
        for idx, pattern in enumerate(self.case_name_patterns):
            matches = list(pattern.finditer(search_text_no_parens))
            if matches:
                logger.warning(f"[EXTRACT-DEBUG] Pattern {idx+1} matched, found {len(matches)} matches")
                for match in matches:
                    if isinstance(match.groups(), tuple) and len(match.groups()) >= 2:
                        case_name = f"{match.group(1).strip()} v. {match.group(2).strip()}"
                    else:
                        case_name = match.group(0).strip()
                    
                    # Calculate distance from citation (prefer closer matches)
                    distance_from_citation = len(search_text_no_parens) - match.end()
                    
                    # Score: lower is better (closer to citation)
                    # Penalize if case name is very far from citation
                    score = distance_from_citation
                    
                    # Bonus: prefer case names on the same line (no newlines between)
                    text_between = search_text_no_parens[match.end():]
                    if '\n' not in text_between:
                        score -= 50  # Bonus for same line
                    
                    candidates.append({
                        'case_name': case_name,
                        'distance': distance_from_citation,
                        'score': score,
                        'pattern_idx': idx
                    })
                    logger.warning(f"[EXTRACT-DEBUG] Candidate: '{case_name[:50]}...' distance={distance_from_citation} score={score}")
        
        if not candidates:
            return None
        
        # Select the best candidate (lowest score = closest to citation)
        best_candidate = min(candidates, key=lambda x: x['score'])
        case_name = best_candidate['case_name']
        
        logger.warning(f"[EXTRACT-DEBUG] Selected best: '{case_name[:80]}...' (score={best_candidate['score']})")
        
        # Clean the extracted case name to remove sentence fragments
        # Check if case name starts with common abbreviated patterns (Ass'n, Dep't, etc.)
        # or contains state/location abbreviations near the start (Wash., Cal., etc.)
        # If so, DON'T clean - it's likely the full case name with abbreviations
        has_abbreviations = bool(re.search(
            r'^[A-Z][a-z]{0,5}[\'\u2019Æ]+n\b|'  # Ass'n, Dep't at start
            r'^\w+\s+of\s+[A-Z][a-z]{2,6}\.|'     # "X of Wash.", "X of Cal."
            r'\b[A-Z][a-z]{2,6}\.\s*\n',           # "Wash.\n" (abbreviated location + newline)
            case_name[:60],  # Check first 60 chars only
            re.UNICODE
        ))
        
        if not has_abbreviations:
            # Only clean if no abbreviations detected
            # Remove leading sentence fragments (text before the last sentence boundary)
            case_name_match = re.search(r'[.!?]\s{2,}([A-Z].+?\s+v\.\s+.+?)$', case_name)
            if case_name_match and ' v. ' in case_name_match.group(1):
                cleaned = case_name_match.group(1).strip()
                logger.warning(f"[EXTRACT-DEBUG] Cleaned sentence fragment: '{cleaned[:80]}...'")
                case_name = cleaned
        
        # Normalize whitespace
        case_name = re.sub(r'\s+', ' ', case_name)
        
        # CRITICAL FIX: Remove any citations that got included in the case name
        # Pattern matches: "123 Reporter 456" or "123 Reporter.2d 456" etc.
        # This prevents extracted names like "State v. M.Y.G., 199 Wn.2d 528, 532"
        # and cleans them to just "State v. M.Y.G."
        # Pattern requires: comma + space(s) + digits + space(s) + reporter + space(s) + page
        citation_pattern = r',\s+\d+\s+[A-Za-z\.\d]+\s+\d+(?:,\s+\d+)*'
        case_name = re.sub(citation_pattern, '', case_name).strip()
        
        # Also remove trailing commas or periods that might be left
        case_name = re.sub(r'[,\.\s]+$', '', case_name).strip()
        
        logger.warning(f"[EXTRACT-DEBUG] Final case name: '{case_name[:80]}...'")
        return case_name
    
    def _extract_date_from_context(self, text: str, citation: CitationResult) -> Optional[str]:
        """Extract date from the context around a citation."""
        if not citation.start_index:
            return None
        
        start_search = citation.start_index
        end_search = min(len(text), start_search + 300)
        search_text = text[start_search:end_search]
        
        
        for pattern in self.date_patterns:
            match = pattern.search(search_text)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_context(self, text: str, start: int, end: int) -> str:
        """Extract context around a citation."""
        context_start = max(0, start - 100)
        context_end = min(len(text), end + 100)
        return text[context_start:context_end].strip()
    
    def _calculate_confidence(self, citation: CitationResult, text: str) -> float:
        """Calculate confidence score for a citation."""
        confidence = 0.5  # Base confidence
        
        if citation.method == "eyecite":
            confidence += 0.3
        elif citation.method == "regex":
            confidence += 0.2
        
        if citation.extracted_case_name:
            confidence += 0.2
        
        if citation.extracted_date:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _get_matching_pattern(self, citation: str) -> str:
        """Get the pattern type that matched a citation."""
        if self.patterns['federal'].match(citation):
            return "federal"
        elif self.patterns['state'].match(citation):
            return "state"
        else:
            return "unknown"
    
    def _deduplicate_citations(self, citations: List[CitationResult]) -> List[CitationResult]:
        """Remove duplicate citations while preserving the best quality ones."""
        seen = {}
        deduplicated = []
        
        for citation in citations:
            normalized = self._normalize_citation_comprehensive(citation.citation, purpose="comparison")
            
            if normalized not in seen:
                seen[normalized] = citation
                deduplicated.append(citation)
            else:
                existing = seen[normalized]
                if citation.confidence > existing.confidence:
                    seen[normalized] = citation
                    deduplicated[deduplicated.index(existing)] = citation
        
        return deduplicated
    
    def _normalize_citation(self, citation: str) -> str:
        """Normalize citation for comparison."""
        normalized = re.sub(r'\s+', ' ', citation.strip().lower())
        
        replacements = {
            'wash.': 'wn.',
            'wash. 2d': 'wn. 2d',
            'wash. app.': 'wn. app.',
            's. ct.': 's.ct.',
            'l. ed.': 'l.ed.',
            'f. supp.': 'f.supp.'
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        return normalized
    
    def _normalize_citation_comprehensive(self, citation: str, purpose: str = "comparison") -> str:
        """
        Comprehensive citation normalization for different purposes.
        
        Args:
            citation: The citation string to normalize
            purpose: The purpose of normalization ("comparison", "similarity", "extraction")
            
        Returns:
            Normalized citation string
        """
        if not citation:
            return ""
        
        normalized = re.sub(r'\s+', ' ', citation.strip().lower())
        
        if purpose == "similarity":
            normalized = re.sub(r'[^\w\s]', '', normalized)
        elif purpose == "extraction":
            # but normalize common variations
            normalized = re.sub(r'[^\w\s\.]', '', normalized)
        else:  # comparison (default)
            pass
        
        replacements = {
            'wash.': 'wn.',
            'wash. 2d': 'wn. 2d',
            'wash. app.': 'wn. app.',
            's. ct.': 's.ct.',
            'l. ed.': 'l.ed.',
            'f. supp.': 'f.supp.',
            'p.': 'p',
            'p2d': 'p2d',
            'p3d': 'p3d',
            'f.': 'f',
            'f2d': 'f2d',
            'f3d': 'f3d',
            'u.s.': 'us',
            'sup. ct.': 'supct'
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        return normalized
