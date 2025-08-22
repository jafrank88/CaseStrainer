"""
Citation Extractor

This module contains core citation extraction logic using both regex-based
and eyecite-based approaches.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from src.models import CitationResult
from src.citation_types import CitationMatch, CitationList, CitationDict
from src.citation_utils import (
    normalize_citation, extract_citation_components, 
    extract_context, is_valid_case_name
)

logger = logging.getLogger(__name__)

# Optional: Eyecite for enhanced extraction
try:
    import eyecite
    from eyecite import get_citations
    from eyecite.tokenizers import AhocorasickTokenizer
    EYECITE_AVAILABLE = True
    logger.info("Eyecite successfully imported")
except ImportError as e:
    EYECITE_AVAILABLE = False
    logger.warning(f"Eyecite not available - install with: pip install eyecite. Error: {e}")
except Exception as e:
    EYECITE_AVAILABLE = False
    logger.warning(f"Eyecite import failed with unexpected error: {e}")

class CitationExtractor:
    """Core citation extraction functionality."""
    
    def __init__(self):
        self._init_patterns()
        self._init_case_name_patterns()
        self._init_date_patterns()
    
    def _init_patterns(self):
        """Initialize citation patterns."""
        self.citation_patterns = [
            # Federal patterns
            r'\b\d+\s+U\.S\.\s+\d+\b',
            r'\b\d+\s+S\.Ct\.\s+\d+\b',
            r'\b\d+\s+F\.\d*d?\b',
            r'\b\d+\s+F\.Supp\.\d*d?\b',
            r'\b\d+\s+F\.App\'x\b',
            
            # State patterns
            r'\b\d+\s+P\.\d*d?\s+\d+\b',
            r'\b\d+\s+N\.W\.\d*d?\s+\d+\b',
            r'\b\d+\s+S\.W\.\d*d?\s+\d+\b',
            r'\b\d+\s+N\.E\.\d*d?\s+\d+\b',
            r'\b\d+\s+S\.E\.\d*d?\s+\d+\b',
            r'\b\d+\s+A\.\d*d?\s+\d+\b',
            r'\b\d+\s+So\.\d*d?\s+\d+\b',
            r'\b\d+\s+Cal\.\d*d?\s+\d+\b',
            r'\b\d+\s+Wash\.\d*d?\s+\d+\b',
            r'\b\d+\s+Wn\.\d*d?\s+\d+\b',
            
            # Regional patterns
            r'\b\d+\s+WL\s+\d+\b',
            r'\b\d{4}\s+LEXIS\s+\d+\b',
        ]
        
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.citation_patterns]
    
    def _init_case_name_patterns(self):
        """Initialize case name extraction patterns."""
        self.case_name_patterns = [
            # Standard v. patterns
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+vs\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+versus\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+&\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            # In re patterns
            r'In\s+re\s+([^,\.]+)',
            r'In\s+re\s+the\s+([^,\.]+)',
        ]
        
        self.compiled_case_patterns = [re.compile(pattern) for pattern in self.case_name_patterns]
    
    def _init_date_patterns(self):
        """Initialize date extraction patterns."""
        self.date_patterns = [
            r'\b(19|20)\d{2}\b',  # 4-digit years
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',  # MM/DD/YYYY or M/D/YY
            r'\b\d{1,2}-\d{1,2}-\d{2,4}\b',  # MM-DD-YYYY or M-D-YY
        ]
        
        self.compiled_date_patterns = [re.compile(pattern) for pattern in self.date_patterns]
    
    def extract_with_regex(self, text: str) -> CitationList:
        """Extract citations using regex patterns."""
        if not text:
            return []
        
        citations = []
        
        for pattern in self.compiled_patterns:
            for match in pattern.finditer(text):
                citation_text = match.group(0)
                start, end = match.span()
                
                logger.info(f"🔍 Extracted citation: '{citation_text}' at position {start}-{end}")
                
                # Create CitationResult object
                citation = CitationResult(
                    citation=citation_text,
                    start_index=start,
                    end_index=end,
                    extracted_case_name=None,
                    extracted_date=None,
                    canonical_name=None,
                    canonical_date=None,
                    url=None,
                    verified=False,
                    source="regex",
                    confidence=0.7,
                    metadata={}
                )
                
                # Extract case name from context
                context = extract_context(text, start, end)
                case_name = self._extract_case_name_from_context(context)
                if case_name:
                    citation.extracted_case_name = case_name
                
                # Extract year from citation text only (most reliable)
                citation_year = self._extract_year_from_citation(citation_text)
                if citation_year:
                    citation.extracted_date = citation_year
                # No fallback to context - let CourtListener provide canonical year
                
                citations.append(citation)
        
        return citations
    
    def extract_with_eyecite(self, text: str) -> CitationList:
        """Extract citations using eyecite library."""
        if not EYECITE_AVAILABLE or not text:
            return []
        
        try:
            citations = []
            eyecite_results = get_citations(text)
            
            for citation_obj in eyecite_results:
                citation_text = self._extract_citation_text_from_eyecite(citation_obj)
                if not citation_text:
                    continue
                
                # Create CitationResult object
                # Get position from eyecite object if available, otherwise use None
                start_pos = getattr(citation_obj, 'start', None)
                end_pos = getattr(citation_obj, 'end', None)
                
                citation = CitationResult(
                    citation=citation_text,
                    start_index=start_pos,
                    end_index=end_pos,
                    extracted_case_name=None,
                    extracted_date=None,
                    canonical_name=None,
                    canonical_date=None,
                    url=None,
                    verified=False,
                    source="eyecite",
                    confidence=0.8,
                    metadata={}
                )
                
                # Extract metadata from eyecite object
                self._extract_eyecite_metadata(citation, citation_obj)
                
                citations.append(citation)
            
            return citations
            
        except Exception as e:
            logger.error(f"Error extracting citations with eyecite: {e}")
            return []
    
    def _extract_citation_text_from_eyecite(self, citation_obj) -> Optional[str]:
        """Extract citation text from eyecite citation object."""
        try:
            if hasattr(citation_obj, 'citation'):
                return str(citation_obj.citation)
            elif hasattr(citation_obj, 'groups'):
                return ' '.join(str(g) for g in citation_obj.groups if g)
            else:
                return str(citation_obj)
        except Exception as e:
            logger.error(f"Error extracting citation text from eyecite object: {e}")
            return None
    
    def _extract_eyecite_metadata(self, citation: CitationResult, citation_obj):
        """Extract metadata from eyecite citation object."""
        try:
            # Extract case name if available
            if hasattr(citation_obj, 'case_name'):
                citation.extracted_case_name = str(citation_obj.case_name)
            
            # Extract date if available
            if hasattr(citation_obj, 'year'):
                citation.extracted_date = str(citation_obj.year)
            
            # Extract additional metadata
            if citation.metadata is None:
                citation.metadata = {}
            citation.metadata['eyecite_type'] = type(citation_obj).__name__
            
        except Exception as e:
            logger.error(f"Error extracting eyecite metadata: {e}")
    
    def _extract_case_name_from_context(self, context: str) -> Optional[str]:
        """Extract case name from context around citation."""
        if not context:
            return None
        
        # Look for case name patterns in context
        for i, pattern in enumerate(self.compiled_case_patterns):
            match = pattern.search(context)
            if match:
                if i < 4:  # Standard v. patterns (first 4 patterns)
                    case_name = f"{match.group(1)} v. {match.group(2)}"
                else:  # In re patterns (last 2 patterns)
                    case_name = f"In re {match.group(1)}"
                
                logger.info(f"🔍 Found case name pattern {i}: '{case_name}' from match: {match.groups()}")
                if is_valid_case_name(case_name):
                    logger.info(f"✅ Valid case name: '{case_name}'")
                    return case_name
                else:
                    logger.info(f"❌ Invalid case name: '{case_name}'")
        
        return None
    
    def _extract_date_from_context(self, context: str) -> Optional[str]:
        """Extract date from context around citation."""
        if not context:
            return None
        
        # Look for date patterns in context
        for pattern in self.compiled_date_patterns:
            match = pattern.search(context)
            if match:
                return match.group(0)
        
        return None
    
    def _extract_year_from_citation(self, citation_text: str) -> Optional[str]:
        """Extract year from citation text itself (more reliable than context)."""
        if not citation_text:
            return None
        
        # Look for year in parentheses at the end of citation
        year_match = re.search(r'\((\d{4})\)$', citation_text)
        if year_match:
            return year_match.group(1)
        
        # Look for 4-digit year anywhere in citation
        year_match = re.search(r'\b(19|20)\d{2}\b', citation_text)
        if year_match:
            return year_match.group(0)
        
        return None
    
    def extract_citations(self, text: str, use_eyecite: bool = True) -> CitationList:
        """Extract citations using both regex and eyecite methods."""
        if not text:
            return []
        
        citations = []
        
        # Extract with regex
        regex_citations = self.extract_with_regex(text)
        citations.extend(regex_citations)
        
        # Extract with eyecite if available and enabled
        if use_eyecite and EYECITE_AVAILABLE:
            eyecite_citations = self.extract_with_eyecite(text)
            citations.extend(eyecite_citations)
        
        # Remove duplicates based on citation text and position
        return self._deduplicate_citations(citations)
    
    def _deduplicate_citations(self, citations: CitationList) -> CitationList:
        """Remove duplicate citations based on text and position."""
        seen = set()
        unique_citations = []
        
        for citation in citations:
            # Create a key based on citation text and position
            key = (citation.citation, citation.start_index, citation.end_index)
            if key not in seen:
                seen.add(key)
                unique_citations.append(citation)
        
        return unique_citations 