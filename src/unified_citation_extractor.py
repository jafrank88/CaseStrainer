#!/usr/bin/env python3
"""
DEPRECATED: This module is deprecated in favor of src/unified_citation_processor_v2.py
Use UnifiedCitationProcessorV2 instead for all new development.

This module will be removed in a future version.
"""

import warnings
warnings.warn(
    "UnifiedCitationExtractor is deprecated. Use UnifiedCitationProcessorV2 from src/unified_citation_processor_v2.py instead.",
    DeprecationWarning,
    stacklevel=2
)

import re
import logging
import time
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass

# Try to import eyecite for enhanced extraction
try:
    from eyecite import get_citations
    EYECITE_AVAILABLE = True
except ImportError:
    EYECITE_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class CitationResult:
    """Standardized citation result structure."""
    citation: str
    source: str  # 'regex', 'eyecite', or 'combined'
    original: Optional[str] = None  # Original citation if normalized
    context: Optional[str] = None  # Context around citation
    line_number: Optional[int] = None  # Line number in text
    confidence: float = 1.0  # Confidence score (0.0 to 1.0)

class UnifiedCitationExtractor:
    """
    Unified citation extraction system that combines regex and eyecite approaches.
    
    This is the single source of truth for citation extraction across the entire codebase.
    """
    
    def __init__(self, 
                 use_eyecite: bool = True, 
                 use_regex: bool = True, 
                 chunk_large_text: bool = True,
                 max_chunk_size: int = 64000,
                 chunk_overlap: int = 40,
                 normalize_washington: bool = True,
                 extract_context: bool = False,
                 context_window: int = 250):
        """
        Initialize the unified citation extractor.
        
        Args:
            use_eyecite: Whether to use eyecite for extraction
            use_regex: Whether to use regex patterns for extraction
            chunk_large_text: Whether to chunk large text for processing
            max_chunk_size: Maximum chunk size in characters
            chunk_overlap: Overlap between chunks in characters
            normalize_washington: Whether to normalize Washington citations (Wn. -> Wash.)
            extract_context: Whether to extract context around citations
            context_window: Size of context window around citations
        """
        self.use_eyecite = use_eyecite and EYECITE_AVAILABLE
        self.use_regex = use_regex
        self.chunk_large_text = chunk_large_text
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap
        self.normalize_washington = normalize_washington
        self.extract_context = extract_context
        self.context_window = context_window
        
        # Initialize regex patterns
        self._init_regex_patterns()
        
        logger.info(f"UnifiedCitationExtractor initialized: eyecite={self.use_eyecite}, regex={self.use_regex}")
    
    def _init_regex_patterns(self):
        """Initialize comprehensive regex patterns for citation extraction."""
        
        # State court abbreviations (from University of Akron Bluebook Quick Reference)
        state_court_abbr_pattern = (
            r'\d+\s+(?:Ala\.|Alaska|Ariz\.|Ark\.|Cal\.|Colo\.|Conn\.|Del\.|D\.C\.|Fla\.|Ga\.|Haw\.|Idaho|Ill\.|Ind\.|Iowa|Kan\.|Ky\.|La\.|Me\.|Md\.|Mass\.|Mich\.|Minn\.|Miss\.|Mo\.|Mont\.|Neb\.|Nev\.|N\.H\.|N\.J\.|N\.M\.|N\.Y\.|N\.C\.|N\.D\.|Ohio|Okla\.|Or\.|Pa\.|R\.I\.|S\.C\.|S\.D\.|Tenn\.|Tex\.|Utah|Vt\.|Va\.|Wash\.|W\. Va\.|Wis\.|Wyo\.|Ala\. Civ\. App\.|Ala\. Crim\. App\.|Alaska Ct\. App\.|Ariz\. Ct\. App\.|Ark\. Ct\. App\.|Cal\. Ct\. App\.|Colo\. App\.|Conn\. App\. Ct\.|Del\. Ch\.|Fla\. Dist\. Ct\. App\.|Ga\. Ct\. App\.|Haw\. Ct\. App\.|Idaho Ct\. App\.|Ill\. App\. Ct\.|Ind\. Ct\. App\.|Iowa Ct\. App\.|Kan\. Ct\. App\.|Ky\. Ct\. App\.|La\. Ct\. App\.|Md\. App\. Ct\.|Md\. Ct\. Spec\. App\.|Mass\. App\. Ct\.|Mich\. Ct\. App\.|Minn\. Ct\. App\.|Miss\. Ct\. App\.|Mo\. Ct\. App\.|Neb\. Ct\. App\.|N\.J\. Super\. Ct\. App\. Div\.|N\.M\. Ct\. App\.|N\.Y\. App\. Div\.|N\.C\. Ct\. App\.|N\.D\. Ct\. App\.|Ohio Ct\. App\.|Okla\. Crim\. App\.|Okla\. Civ\. App\.|Or\. Ct\. App\.|Pa\. Super\. Ct\.|S\.C\. Ct\. App\.|Tenn\. Ct\. App\.|Tex\. Crim\. App\.|Tex\. App\.|Utah Ct\. App\.|Va\. Ct\. App\.|Wash\. Ct\. App\.|Wis\. Ct\. App\.)\s+\d+'
        )

        # Comprehensive regex patterns for Bluebook-style citations
        self.regex_patterns = [
            # Federal courts
            r'\d+\s+U\.S\.\s+\d+',  # Supreme Court
            r'\d+\s+S\. Ct\.\s+\d+',  # Supreme Court (alternative)
            r'\d+\s+F\.(?:2d|3d|4th|5th|6th|7th)\s+\d+',  # Federal Reporter
            r'\d+\s+F\.\s+\d{2,}',  # Federal Reporter (original series)
            r'\d+\s+F\. App\'?x\.\s+\d+',  # Federal Appendix
            r'\d+\s+F\. Supp\.(?:2d|3d|4th|5th|6th|7th)?\s+\d+',  # Federal Supplement
            r'\d+\s+F\. Supp\.\s+\d{2,}',  # Federal Supplement (original series)
            
            # Regional Reporters
            r'\d+\s+A\.(?:2d|3d|4th|5th|6th|7th)\s+\d+',  # Atlantic Reporter
            r'\d+\s+A\.\s+\d{2,}',  # Atlantic Reporter (original series)
            r'\d+\s+N\.E\.(?:2d|3d|4th|5th|6th|7th)\s+\d+',  # Northeastern Reporter
            r'\d+\s+N\.E\.\s+\d{2,}',  # Northeastern Reporter (original series)
            r'\d+\s+N\.W\.(?:2d|3d|4th|5th|6th|7th)\s+\d+',  # Northwestern Reporter
            r'\d+\s+N\.W\.\s+\d{2,}',  # Northwestern Reporter (original series)
            r'\d+\s+S\.E\.(?:2d|3d|4th|5th|6th|7th)\s+\d+',  # Southeastern Reporter
            r'\d+\s+S\.E\.\s+\d{2,}',  # Southeastern Reporter (original series)
            r'\d+\s+S\.W\.(?:2d|3d|4th|5th|6th|7th)\s+\d+',  # Southwestern Reporter
            r'\d+\s+S\.W\.\s+\d{2,}',  # Southwestern Reporter (original series)
            r'\d+\s+So\.(?:2d|3d|4th|5th|6th|7th)\s+\d+',  # Southern Reporter
            r'\d+\s+So\.\s+\d{2,}',  # Southern Reporter (original series)
            r'\d+\s+P\.(?:2d|3d|4th|5th|6th|7th)\s+\d+',  # Pacific Reporter
            r'\d+\s+P\.\s+\d{2,}',  # Pacific Reporter (original series)
            
            # State courts (comprehensive pattern)
            state_court_abbr_pattern,
            
            # Washington-specific patterns (both Wn. and Wash.)
            # Updated to support up to 5 digits for volume and up to 12 digits for page
            r'\d{1,5}\s+(?:Wash\.|Wn\.)\s*(?:2d|3d|4th|5th|6th|7th|8th|9th)?\s*(?:App\.)?\s+\d{1,12}',
            
            # California-specific patterns
            r'\d{1,5}\s+Cal\.(?:2d|3d|4th|5th|6th|7th)\s+\d{1,12}',
            r'\d{1,5}\s+Cal\.\s+\d{2,12}',
            
            # Westlaw
            r'\d{4}\s+WL\s+\d{1,12}',
            
            # LEXIS
            r'\d{4}\s+LEXIS\s+\d{1,12}',
        ]
        
        # Remove patterns that could match invalid series indicators
        self.regex_patterns = [pattern for pattern in self.regex_patterns 
                              if not re.search(r'\.\d+$', pattern)]
    
    def normalize_washington_citations(self, citation_text: str) -> str:
        """Normalize Washington citations from Wn. to Wash. format."""
        if not self.normalize_washington:
            return citation_text
            
        normalized = citation_text
        
        # Wn.2d -> Wash. 2d
        normalized = re.sub(r'\bWn\.2d\b', 'Wash. 2d', normalized)
        # Wn.3d -> Wash. 3d  
        normalized = re.sub(r'\bWn\.3d\b', 'Wash. 3d', normalized)
        # Wn. App. -> Wash. App.
        normalized = re.sub(r'\bWn\. App\.\b', 'Wash. App.', normalized)
        # Wn. -> Wash.
        normalized = re.sub(r'\bWn\.\b', 'Wash.', normalized)
        
        # Also normalize any Wash.2d to Wash. 2d format
        normalized = re.sub(r'\bWash\.2d\b', 'Wash. 2d', normalized)
        normalized = re.sub(r'\bWash\.3d\b', 'Wash. 3d', normalized)
        
        return normalized
    
    def extract_with_regex(self, text: str) -> List[CitationResult]:
        """Extract citations using regex patterns, including full case name and year."""
        if not self.use_regex:
            return []
        
        logger.info("Starting regex citation extraction...")
        start_time = time.time()
        found_citations = set()
        results = []

        # Working pattern that successfully matches case citations
        # Pattern: ^(.+? v\.[^,\n]+), (.+) \((\d{4})\)$
        # Group 1: Case name, Group 2: Citation(s), Group 3: Year
        working_case_pattern = re.compile(
            r"^(.+? v\.[^,\n]+), (.+) \((\d{4})\)$", 
            re.MULTILINE
        )
        
        print(f"[DEBUG] Trying working pattern: {working_case_pattern.pattern}")
        matches = list(working_case_pattern.finditer(text))
        print(f"[DEBUG] Working pattern matches found: {len(matches)}")
        
        for match in matches:
            case_name = match.group(1).strip()
            citation = match.group(2).strip()
            year = match.group(3).strip()
            key = f"{case_name}|{citation}|{year}"
            
            if key not in found_citations:
                found_citations.add(key)
                
                # Get context (2 lines before the match)
                start_pos = match.start()
                context_start = max(0, start_pos - 200)  # 200 chars before
                context_end = start_pos
                context = text[context_start:context_end]
                
                # Create full citation string
                full_citation = f"{case_name}, {citation} ({year})"
                
                results.append(CitationResult(
                    citation=full_citation,
                    source="regex_full",
                    original=None,
                    context=context,
                    line_number=self._get_line_number(text, start_pos),
                    confidence=0.95
                ))
                print(f"[REGEX_FULL] Found: {case_name}, {citation}, {year}")
                print(f"[REGEX_FULL] Full citation: {full_citation}")
        # Fallback to original patterns for other citations
        for pattern in self.regex_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                citation = match.group(0).strip()
                if citation not in found_citations:
                    found_citations.add(citation)
                    # Normalize Washington citations
                    normalized_citation = self.normalize_washington_citations(citation)
                    # Extract context if requested
                    context = None
                    if self.extract_context:
                        start = max(0, match.start() - self.context_window)
                        end = min(len(text), match.end() + self.context_window)
                        context = text[start:end]
                    results.append(CitationResult(
                        citation=normalized_citation,
                        source="regex",
                        original=citation if citation != normalized_citation else None,
                        context=context,
                        line_number=self._get_line_number(text, match.start()),
                        confidence=0.8  # Regex confidence
                    ))
        logger.info(f"Regex extraction found {len(results)} citations in {time.time() - start_time:.2f}s")
        return results
    
    def extract_with_eyecite(self, text: str) -> List[CitationResult]:
        """Extract citations using eyecite library."""
        if not self.use_eyecite:
            return []
            
        logger.info("Starting eyecite citation extraction...")
        start_time = time.time()
        
        try:
            citations = get_citations(text)
            results = []
            
            for citation in citations:
                # Extract the actual citation text from the eyecite object
                try:
                    # Try to get the citation as a clean string
                    if hasattr(citation, 'cite') and citation.cite:
                        citation_text = citation.cite
                    elif hasattr(citation, 'citation') and citation.citation:
                        citation_text = citation.citation
                    elif hasattr(citation, 'groups') and citation.groups:
                        # Try to reconstruct from groups
                        groups = citation.groups
                        volume = groups.get('volume', '')
                        reporter = groups.get('reporter', '')
                        page = groups.get('page', '')
                        if volume and reporter and page:
                            citation_text = f"{volume} {reporter} {page}"
                        else:
                            citation_text = str(citation)
                    else:
                        citation_text = str(citation)
                except Exception as e:
                    logger.warning(f"Failed to extract citation text from eyecite object: {e}")
                    citation_text = str(citation)
                
                print(f"[EYECITE] Found citation: {citation_text}")
                
                # Normalize Washington citations
                normalized_citation = self.normalize_washington_citations(citation_text)
                
                # Extract context if requested
                context = None
                span = citation.span() if callable(getattr(citation, 'span', None)) else citation.span if hasattr(citation, 'span') else None
                if self.extract_context and span:
                    start = max(0, span[0] - self.context_window)
                    end = min(len(text), span[1] + self.context_window)
                    context = text[start:end]
                
                results.append(CitationResult(
                    citation=normalized_citation,
                    source="eyecite",
                    original=citation_text if citation_text != normalized_citation else None,
                    context=context,
                    line_number=self._get_line_number(text, span[0]) if span else None,
                    confidence=0.9  # Eyecite confidence
                ))
            print(f"[EYECITE] Total citations found by eyecite: {len(results)}")
            
            logger.info(f"Eyecite extraction found {len(results)} citations in {time.time() - start_time:.2f}s")
            return results
            
        except Exception as e:
            logger.error(f"Eyecite extraction failed: {e}")
            return []
    
    def _get_line_number(self, text: str, position: int) -> Optional[int]:
        """Get line number for a position in text."""
        if position < 0 or position >= len(text):
            return None
        return text[:position].count('\n') + 1
    
    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks for processing large documents."""
        if not self.chunk_large_text or len(text) <= self.max_chunk_size:
            return [text]
        
        logger.info(f"Chunking text of {len(text)} characters into chunks of {self.max_chunk_size}")
        chunks = []
        i = 0
        
        while i < len(text):
            start = i - self.chunk_overlap if i > 0 else 0
            start = max(0, start)  # Ensure start is not negative
            end = min(i + self.max_chunk_size, len(text))
            chunks.append(text[start:end])
            i += self.max_chunk_size - self.chunk_overlap
        
        logger.info(f"Created {len(chunks)} chunks")
        return chunks
    
    def _deduplicate_citations(self, citations: List[CitationResult]) -> List[CitationResult]:
        """Remove duplicate citations while preserving the best source."""
        seen = {}
        unique_citations = []
        
        for citation in citations:
            # Use normalized citation as key
            key = citation.citation.lower().strip()
            
            if key not in seen:
                seen[key] = citation
                unique_citations.append(citation)
            else:
                # If we have a duplicate, prefer eyecite over regex
                existing = seen[key]
                if (citation.source == "eyecite" and existing.source == "regex") or \
                   (citation.confidence > existing.confidence):
                    # Replace existing with better citation
                    unique_citations.remove(existing)
                    seen[key] = citation
                    unique_citations.append(citation)
        
        logger.info(f"Deduplication: {len(citations)} -> {len(unique_citations)} unique citations")
        return unique_citations
    
    def extract_citations(self, text: str) -> List[CitationResult]:
        """
        Extract all citations from text using the unified approach.
        
        Args:
            text: The text to extract citations from
            
        Returns:
            List of CitationResult objects with extracted citations
        """
        if not text or not isinstance(text, str):
            logger.error("Invalid input: Text must be a non-empty string")
            return []
        
        logger.info(f"Starting unified citation extraction from text of {len(text)} characters")
        start_time = time.time()
        
        # Chunk text if needed
        chunks = self._chunk_text(text)
        all_citations = []
        
        # Extract from each chunk
        for i, chunk in enumerate(chunks):
            logger.debug(f"Processing chunk {i+1}/{len(chunks)} ({len(chunk)} characters)")
            
            # Extract with regex
            if self.use_regex:
                regex_citations = self.extract_with_regex(chunk)
                all_citations.extend(regex_citations)
            
            # Extract with eyecite
            if self.use_eyecite:
                eyecite_citations = self.extract_with_eyecite(chunk)
                all_citations.extend(eyecite_citations)
        
        # Deduplicate results
        unique_citations = self._deduplicate_citations(all_citations)
        
        # Sort by confidence and source preference
        unique_citations.sort(key=lambda x: (x.confidence, x.source == "eyecite"), reverse=True)
        
        total_time = time.time() - start_time
        logger.info(f"Unified extraction completed in {total_time:.2f}s: {len(unique_citations)} unique citations")
        
        return unique_citations
    
    def extract_citations_simple(self, text: str) -> List[str]:
        """
        Extract citations and return just the citation strings (for backward compatibility).
        
        Args:
            text: The text to extract citations from
            
        Returns:
            List of citation strings
        """
        results = self.extract_citations(text)
        return [result.citation for result in results]

# Global instance for easy access
_unified_extractor = None

def get_unified_extractor() -> UnifiedCitationExtractor:
    """Get the global unified extractor instance."""
    global _unified_extractor
    if _unified_extractor is None:
        _unified_extractor = UnifiedCitationExtractor()
    return _unified_extractor

def extract_all_citations(text: str, logger=None) -> List[Dict]:
    """
    Extract all citations from text using the unified extractor.
    
    This function now delegates to the unified citation extraction system
    for consistency across the codebase.
    
    Args:
        text: The text to extract citations from
        logger: Optional logger instance
        
    Returns:
        List of citation dictionaries with metadata
    """
    # DEPRECATED: from .citation_extractor import CitationExtractor
    
    # Initialize extractor with case name extraction enabled
    extractor = CitationExtractor(
        use_eyecite=True,
        use_regex=True,
        context_window=1000,
        deduplicate=True,
        extract_case_names=True
    )
    
    return extractor.extract(text)

def extract_citations_from_text(text: str, logger=None) -> List[str]:
    """
    Extract citations and return just the citation strings (backward compatibility).
    
    Args:
        text: The text to extract citations from
        logger: Optional logger instance
        
    Returns:
        List of citation strings
    """
    extractor = get_unified_extractor()
    return extractor.extract_citations_simple(text)

# Export the main functions for backward compatibility
__all__ = [
    'UnifiedCitationExtractor',
    'CitationResult',
    'extract_all_citations',
    'extract_citations_from_text',
    'get_unified_extractor'
] 