"""
Citation Extractor Service

This service handles pure citation extraction logic, separated from verification and clustering.
It consolidates regex-based and eyecite-based extraction methods.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import unicodedata

from .interfaces import ICitationExtractor
from src.models import CitationResult, ProcessingConfig

logger = logging.getLogger(__name__)

# Optional: Eyecite for enhanced extraction
try:
    import eyecite
    from eyecite import get_citations
    from eyecite.tokenizers import AhocorasickTokenizer
    EYECITE_AVAILABLE = True
    logger.info("Eyecite successfully imported for CitationExtractor")
except ImportError as e:
    EYECITE_AVAILABLE = False
    logger.warning(f"Eyecite not available - install with: pip install eyecite. Error: {e}")


class CitationExtractor(ICitationExtractor):
    """
    Pure citation extraction service using regex and eyecite methods.
    
    This service is responsible for:
    - Finding citation patterns in text
    - Extracting basic citation metadata
    - Normalizing citation formats
    - Context extraction for case names and dates
    """
    
    def __init__(self, config: Optional[ProcessingConfig] = None):
        """Initialize the citation extractor with configuration."""
        self.config = config or ProcessingConfig()
        self._init_patterns()
        self._init_case_name_patterns()
        self._init_date_patterns()
        
        if self.config.debug_mode:
            logger.info(f"CitationExtractor initialized with eyecite: {EYECITE_AVAILABLE}")
    
    def _init_patterns(self) -> None:
        """Initialize comprehensive citation patterns with proper Bluebook spacing."""
        # Federal patterns
        federal_patterns = [
            r'\b\d+\s+U\.S\.\s+\d+',           # U.S. Reports
            r'\b\d+\s+S\.\s*Ct\.\s+\d+',       # Supreme Court Reporter
            r'\b\d+\s+L\.\s*Ed\.\s*2d\s+\d+',  # Lawyers' Edition
            r'\b\d+\s+F\.\s*3d\s+\d+',         # Federal Reporter 3d
            r'\b\d+\s+F\.\s*2d\s+\d+',         # Federal Reporter 2d
            r'\b\d+\s+F\.\s+\d+',              # Federal Reporter
            r'\b\d+\s+F\.\s*Supp\.\s*3d\s+\d+', # Federal Supplement 3d
            r'\b\d+\s+F\.\s*Supp\.\s*2d\s+\d+', # Federal Supplement 2d
            r'\b\d+\s+F\.\s*Supp\.\s+\d+'      # Federal Supplement
        ]
        
        # State patterns (comprehensive)
        state_patterns = [
            # Washington
            r'\b\d+\s+Wash\.\s*2d\s+\d+',
            r'\b\d+\s+Wn\.\s*2d\s+\d+',
            r'\b\d+\s+Wash\.\s+\d+',
            r'\b\d+\s+Wn\.\s+\d+',
            r'\b\d+\s+Wash\.\s*App\.\s+\d+',
            r'\b\d+\s+Wn\.\s*App\.\s+\d+',
            
            # California
            r'\b\d+\s+Cal\.\s*4th\s+\d+',
            r'\b\d+\s+Cal\.\s*3d\s+\d+',
            r'\b\d+\s+Cal\.\s*2d\s+\d+',
            r'\b\d+\s+Cal\.\s+\d+',
            r'\b\d+\s+Cal\.\s*App\.\s*4th\s+\d+',
            r'\b\d+\s+Cal\.\s*App\.\s*3d\s+\d+',
            r'\b\d+\s+Cal\.\s*App\.\s*2d\s+\d+',
            
            # New York
            r'\b\d+\s+N\.Y\.\s*3d\s+\d+',
            r'\b\d+\s+N\.Y\.\s*2d\s+\d+',
            r'\b\d+\s+N\.Y\.\s+\d+',
            r'\b\d+\s+A\.D\.\s*3d\s+\d+',
            r'\b\d+\s+A\.D\.\s*2d\s+\d+',
            
            # Texas
            r'\b\d+\s+S\.W\.\s*3d\s+\d+',
            r'\b\d+\s+S\.W\.\s*2d\s+\d+',
            r'\b\d+\s+S\.W\.\s+\d+',
            r'\b\d+\s+Tex\.\s+\d+',
            
            # Florida
            r'\b\d+\s+So\.\s*3d\s+\d+',
            r'\b\d+\s+So\.\s*2d\s+\d+',
            r'\b\d+\s+So\.\s+\d+',
            r'\b\d+\s+Fla\.\s+\d+',
            
            # Regional reporters
            r'\b\d+\s+A\.\s*3d\s+\d+',         # Atlantic 3d
            r'\b\d+\s+A\.\s*2d\s+\d+',         # Atlantic 2d
            r'\b\d+\s+A\.\s+\d+',              # Atlantic
            r'\b\d+\s+P\.\s*3d\s+\d+',         # Pacific 3d
            r'\b\d+\s+P\.\s*2d\s+\d+',         # Pacific 2d
            r'\b\d+\s+P\.\s+\d+',              # Pacific
            r'\b\d+\s+N\.E\.\s*3d\s+\d+',      # North Eastern 3d
            r'\b\d+\s+N\.E\.\s*2d\s+\d+',      # North Eastern 2d
            r'\b\d+\s+N\.E\.\s+\d+',           # North Eastern
            r'\b\d+\s+N\.W\.\s*2d\s+\d+',      # North Western 2d
            r'\b\d+\s+N\.W\.\s+\d+',           # North Western
            r'\b\d+\s+S\.E\.\s*2d\s+\d+',      # South Eastern 2d
            r'\b\d+\s+S\.E\.\s+\d+',           # South Eastern
            r'\b\d+\s+S\.W\.\s*3d\s+\d+',      # South Western 3d
            r'\b\d+\s+S\.W\.\s*2d\s+\d+',      # South Western 2d
            r'\b\d+\s+S\.W\.\s+\d+'            # South Western
        ]
        
        # Combine all patterns
        all_patterns = federal_patterns + state_patterns
        
        # Create compiled regex pattern
        self.citation_pattern = re.compile('|'.join(all_patterns), re.IGNORECASE)
        
        # Individual patterns for specific matching
        self.patterns = {
            'federal': re.compile('|'.join(federal_patterns), re.IGNORECASE),
            'state': re.compile('|'.join(state_patterns), re.IGNORECASE),
            'all': self.citation_pattern
        }
    
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
    
    def extract_citations(self, text: str) -> List[CitationResult]:
        """
        Extract citations from text using both regex and eyecite methods.
        
        Args:
            text: The text to extract citations from
            
        Returns:
            List of CitationResult objects with basic extraction data
        """
        citations = []
        
        # Method 1: Regex extraction
        regex_citations = self._extract_with_regex(text)
        citations.extend(regex_citations)
        
        # Method 2: Eyecite extraction (if available)
        if EYECITE_AVAILABLE and self.config.use_eyecite:
            eyecite_citations = self._extract_with_eyecite(text)
            citations.extend(eyecite_citations)
        
        # Deduplicate citations
        citations = self._deduplicate_citations(citations)
        
        # Extract metadata for all citations
        for citation in citations:
            citation = self.extract_metadata(citation, text)
        
        if self.config.debug_mode:
            logger.info(f"CitationExtractor found {len(citations)} citations")
        
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
        
        for match in self.citation_pattern.finditer(text):
            citation_text = match.group().strip()
            start_index = match.start()
            end_index = match.end()
            
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
            normalized = self._normalize_citation(citation.citation)
            
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
