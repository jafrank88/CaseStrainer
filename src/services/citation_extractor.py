"""
Citation Extractor Service

This service handles pure citation extraction logic, separated from verification and clustering.
It consolidates regex-based and eyecite-based extraction methods.
"""

import re
import json
import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import unicodedata
from pathlib import Path

from .interfaces import ICitationExtractor, CitationResult, ProcessingConfig

logger = logging.getLogger(__name__)

# Optional eyecite import
try:
    from eyecite import get_citations
    from eyecite.tokenizers import AhocorasickTokenizer
    EYECITE_AVAILABLE = True
    logger.info("Eyecite successfully imported for CitationExtractor")
except ImportError as e:
    EYECITE_AVAILABLE = False
    logger.warning(f"Eyecite not available - install with: pip install eyecite. Error: {e}")

# Optional adaptive learning import
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
    # Create dummy classes for when adaptive learning is not available
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
        
        # Initialize adaptive learning service if available
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
            
        # Group patterns by jurisdiction
        jurisdiction_patterns = {}
        
        for reporter in self.reporters:
            jurisdiction = reporter.get('jurisdiction', 'other')
            if jurisdiction not in jurisdiction_patterns:
                jurisdiction_patterns[jurisdiction] = []
                
            jurisdiction_patterns[jurisdiction].extend(reporter.get('patterns', []))
        
        # Create compiled patterns for each jurisdiction
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
        
        # Combine all patterns for general matching
        all_patterns = []
        for patterns in jurisdiction_patterns.values():
            all_patterns.extend(patterns)
            
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
        
        # Federal patterns
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
        
        # State patterns (focused on Washington for now)
        state_patterns = [
            # Washington patterns
            r'\b(\d+)\s+Wn\.3d\s+(\d+)\b',
            r'\b(\d+)\s+Wn\.\s+3d\s+(\d+)\b',
            r'\b(\d+)\s+Wn\.\s+2d\s+(\d+)\b',
            r'\b(\d+)\s+Wn\.\s+App\.\s+(\d+)\b',
            r'\b(\d+)\s+Wn\.\s+(\d+)\b',
            r'\b(\d+)\s+Wash\.\s+3d\s+(\d+)\b',
            r'\b(\d+)\s+Wash\.\s+2d\s+(\d+)\b',
            r'\b(\d+)\s+Wash\.\s+App\.\s+(\d+)\b',
            r'\b(\d+)\s+Wash\.\s+(\d+)\b',
            
            # Regional reporters
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
        ]
        
        # Combine all patterns
        all_patterns = federal_patterns + state_patterns
        
        # Create compiled patterns
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
        self.case_name_patterns = [
            # Standard case name pattern: Party v. Party
            re.compile(r'\b([A-Z][a-zA-Z\s&,\.]+?)\s+v\.\s+([A-Z][a-zA-Z\s&,\.]+?)(?=\s*,|\s*\d)', re.IGNORECASE),
            
            # In re cases
            re.compile(r'\bIn\s+re\s+([A-Z][a-zA-Z\s&,\.]+?)(?=\s*,|\s*\d)', re.IGNORECASE),
            
            # Ex parte cases
            re.compile(r'\bEx\s+parte\s+([A-Z][a-zA-Z\s&,\.]+?)(?=\s*,|\s*\d)', re.IGNORECASE),
            
            # Matter of cases
            re.compile(r'\bMatter\s+of\s+([A-Z][a-zA-Z\s&,\.]+?)(?=\s*,|\s*\d)', re.IGNORECASE)
        ]
    
    def _init_date_patterns(self) -> None:
        """Initialize date extraction patterns."""
        self.date_patterns = [
            # Year in parentheses (most common)
            re.compile(r'\((\d{4})\)'),
            
            # Year after citation
            re.compile(r'\b(\d{4})\b'),
            
            # Full date patterns
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
        
        # Method 1: Regex extraction
        regex_citations = self._extract_with_regex(text)
        citations.extend(regex_citations)
        
        # Method 2: Eyecite extraction (if available)
        if EYECITE_AVAILABLE and self.config.get('use_eyecite', True):
            eyecite_citations = self._extract_with_eyecite(text)
            citations.extend(eyecite_citations)
        
        # Deduplicate citations
        citations = self._deduplicate_citations(citations)
        
        # Extract metadata for all citations
        for citation in citations:
            citation = self.extract_metadata(citation, text)
        
        # Method 3: Adaptive learning enhancement (if available)
        if self.adaptive_learning and self.adaptive_learning.is_enabled():
            try:
                adaptive_result = self.adaptive_learning.enhance_citation_extraction(
                    text, document_name, citations
                )
                
                # Use improved citations from adaptive learning
                improved_citations = adaptive_result.improved_citations
                if improved_citations is not None:
                    citations = improved_citations
                
                # Log learning information if in debug mode
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
            # Extract case name from context
            case_name = self._extract_case_name_from_context(text, citation)
            if case_name:
                citation.extracted_case_name = case_name
            
            # Extract date from context
            date = self._extract_date_from_context(text, citation)
            if date:
                citation.extracted_date = date
            
            # Extract context
            context = self._extract_context(text, citation.start_index or 0, citation.end_index or 0)
            if context:
                citation.context = context
            
            # Calculate confidence score
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
            # Get the full match (group 0 is the entire match)
            citation_text = match.group(0).strip()
            start_index = match.start(0)
            end_index = match.end(0)
            
            if self.config.get('debug_mode', False):
                logger.info(f"Found citation: {citation_text} at position {start_index}-{end_index}")
            
            # Create CitationResult
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
            # Use eyecite to find citations
            found_citations = get_citations(text)
            
            for eyecite_citation in found_citations:
                citation_text = self._extract_citation_text_from_eyecite(eyecite_citation)
                
                # Find position in text
                start_index = text.find(citation_text)
                end_index = start_index + len(citation_text) if start_index != -1 else 0
                
                # Create CitationResult
                citation = CitationResult(
                    citation=citation_text,
                    start_index=start_index,
                    end_index=end_index,
                    method="eyecite",
                    confidence=0.9  # Higher confidence for eyecite
                )
                
                # Extract additional metadata from eyecite
                self._extract_eyecite_metadata(citation, eyecite_citation)
                
                citations.append(citation)
                
        except Exception as e:
            logger.warning(f"Error in eyecite extraction: {e}")
        
        return citations
    
    def _extract_citation_text_from_eyecite(self, citation_obj) -> str:
        """Extract citation text from eyecite object."""
        try:
            # Try to get the actual citation text, not the object representation
            if hasattr(citation_obj, 'corrected_citation_full'):
                return citation_obj.corrected_citation_full
            elif hasattr(citation_obj, 'corrected_citation'):
                return citation_obj.corrected_citation
            elif hasattr(citation_obj, 'cite'):
                return citation_obj.cite
            elif hasattr(citation_obj, 'text'):
                return citation_obj.text
            else:
                # Fallback: try to extract from groups if it's a match object
                if hasattr(citation_obj, 'groups') and citation_obj.groups:
                    # Reconstruct citation from groups
                    groups = citation_obj.groups()
                    if len(groups) >= 3:  # volume, reporter, page
                        return f"{groups[0]} {groups[1]} {groups[2]}"
                # Last resort: convert to string but only if it doesn't look like an object repr
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
            # Extract court information
            if hasattr(citation_obj, 'court'):
                citation.court = str(citation_obj.court)
            
            # Extract year
            if hasattr(citation_obj, 'year') and citation_obj.year:
                citation.extracted_date = str(citation_obj.year)
            
            # Extract reporter information
            if hasattr(citation_obj, 'reporter'):
                citation.metadata = citation.metadata or {}
                citation.metadata['reporter'] = str(citation_obj.reporter)
                
        except Exception as e:
            logger.warning(f"Error extracting eyecite metadata: {e}")
    
    def _extract_case_name_from_context(self, text: str, citation: CitationResult) -> Optional[str]:
        """Extract case name from the context around a citation."""
        if not citation.start_index:
            return None
        
        # Look for case name in the 200 characters before the citation
        start_search = max(0, citation.start_index - 200)
        search_text = text[start_search:citation.start_index]
        
        # Try each case name pattern
        for pattern in self.case_name_patterns:
            matches = pattern.findall(search_text)
            if matches:
                # Take the last match (closest to citation)
                match = matches[-1]
                if isinstance(match, tuple):
                    # Standard "Party v. Party" format
                    return f"{match[0].strip()} v. {match[1].strip()}"
                else:
                    # Single party format (In re, Ex parte, etc.)
                    return match.strip()
        
        return None
    
    def _extract_date_from_context(self, text: str, citation: CitationResult) -> Optional[str]:
        """Extract date from the context around a citation."""
        if not citation.end_index:
            return None
        
        # Look for date in the 50 characters after the citation
        end_search = min(len(text), citation.end_index + 50)
        search_text = text[citation.end_index:end_search]
        
        # Try each date pattern
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
        
        # Boost confidence based on method
        if citation.method == "eyecite":
            confidence += 0.3
        elif citation.method == "regex":
            confidence += 0.2
        
        # Boost confidence if case name found
        if citation.extracted_case_name:
            confidence += 0.2
        
        # Boost confidence if date found
        if citation.extracted_date:
            confidence += 0.1
        
        # Cap at 1.0
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
            # Use comprehensive normalization with comparison purpose
            normalized = self._normalize_citation_comprehensive(citation.citation, purpose="comparison")
            
            if normalized not in seen:
                seen[normalized] = citation
                deduplicated.append(citation)
            else:
                # Keep the citation with higher confidence
                existing = seen[normalized]
                if citation.confidence > existing.confidence:
                    # Replace in both seen dict and deduplicated list
                    seen[normalized] = citation
                    deduplicated[deduplicated.index(existing)] = citation
        
        return deduplicated
    
    def _normalize_citation(self, citation: str) -> str:
        """Normalize citation for comparison."""
        # Remove extra whitespace and convert to lowercase
        normalized = re.sub(r'\s+', ' ', citation.strip().lower())
        
        # Standardize common abbreviations
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
