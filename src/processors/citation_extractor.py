"""
Citation Extraction Module

This module handles the extraction of citations from text using various patterns
and filtering mechanisms to ensure high-quality citation detection.
"""

import re
import logging
from typing import List, Optional
from src.models import CitationResult
from .error_handler import handle_processor_errors, ProcessorErrorHandler, CitationExtractionProcessorError

logger = logging.getLogger(__name__)

class CitationExtractor:
    """Handles citation extraction from text with filtering and validation."""
    
    def __init__(self):
        self.citation_patterns = [
            r'\b\d+\s+Wn\.?\s*\d*d\s+\d+\b',  # Washington reports
            r'\b\d+\s+P\.?\s*\d*d\s+\d+\b',   # Pacific reports (single line)
            r'\b\d+\s*\n\s*P\.?\s*\d*d\s+\d+\b',  # Pacific reports (with newline)
            r'\b\d+\s+[A-Z]+\.?\s+\d+\b',     # General format
        ]
        self.error_handler = ProcessorErrorHandler("CitationExtractor")
    
    @handle_processor_errors("extract_citations_fast", default_return=[])
    def extract_citations_fast(self, text: str) -> List:
        """Extract citations using master extraction function for consistent results."""
        try:
            from src.unified_extraction_architecture import get_unified_extractor
            
            extractor = get_unified_extractor()
            citations = []
            processed_citations = set()
            
            for pattern in self.citation_patterns:
                for match in re.finditer(pattern, text):
                    citation_text = match.group(0)
                    start_pos = match.start()
                    end_pos = match.end()
                    
                    cleaned_citation_text = citation_text.replace('\n', ' ').replace('\r', ' ').strip()
                    cleaned_citation_text = ' '.join(cleaned_citation_text.split())
                    
                    citation_key = f"{cleaned_citation_text}_{start_pos}_{end_pos}"
                    
                    if citation_key in processed_citations:
                        continue
                    
                    processed_citations.add(citation_key)
                    
                    result = extractor.extract_case_name_and_year(
                        text=text,
                        citation=citation_text,
                        start_index=start_pos,
                        end_index=end_pos,
                        debug=False
                    )
                    
                    citation = CitationResult(
                        citation=cleaned_citation_text,
                        start_index=start_pos,
                        end_index=end_pos,
                        extracted_case_name=result.case_name,
                        extracted_date=result.year,
                        canonical_name=None,
                        canonical_date=None,
                        url=None,
                        verified=False,
                        source="unified_architecture",
                        confidence=result.confidence,
                        metadata={
                            'extraction_method': 'unified_architecture',
                            'method': result.method,
                            'debug_info': result.debug_info
                        }
                    )
                    
                    citations.append(citation)
            
            filtered_citations = self._filter_false_positive_citations(citations, text)
            return filtered_citations
            
        except Exception as e:
            logger.warning(f"Fast extraction failed, falling back to basic regex: {e}")
            return self._extract_citations_basic_regex(text)
    
    def _filter_false_positive_citations(self, citations: List, text: str) -> List:
        """Filter out false positive citations like standalone page numbers."""
        valid_citations = []
        
        for citation in citations:
            citation_text = str(citation) if not hasattr(citation, 'citation') else citation.citation
            
            if self._is_standalone_page_number(citation_text, text):
                continue
            
            if self._is_volume_without_reporter(citation_text):
                continue
            
            if len(citation_text.strip()) < 8:
                continue
            
            valid_citations.append(citation)
        
        return valid_citations
    
    def _is_standalone_page_number(self, citation_text: str, text: str) -> bool:
        """Check if citation is just a standalone page number."""
        if re.match(r'^\d+$', citation_text):
            pos = text.find(citation_text)
            if pos > 0:
                # Check if it's preceded by "page", "p.", "at", etc.
                context_before = text[max(0, pos-20):pos].lower()
                if any(word in context_before for word in ['page', 'p.', 'at', 'see']):
                    return True
        return False
    
    def _is_volume_without_reporter(self, citation_text: str) -> bool:
        """Check if citation is just a volume number without reporter."""
        # Pattern: just numbers (like "123" or "123 456")
        if re.match(r'^\d+\s*\d*$', citation_text.strip()):
            return True
        return False
    
    def _extract_citations_basic_regex(self, text: str) -> List:
        """Fallback citation extraction using basic regex patterns."""
        citations = []
        
        # Basic patterns for fallback
        basic_patterns = [
            r'\b\d+\s+Wn\.?\s*\d*d\s+\d+\b',
            r'\b\d+\s+P\.?\s*\d*d\s+\d+\b',
        ]
        
        for pattern in basic_patterns:
            for match in re.finditer(pattern, text):
                citation_text = match.group(0)
                start_pos = match.start()
                end_pos = match.end()
                
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
                    source="basic_regex",
                    confidence=0.5,
                    metadata={'extraction_method': 'basic_regex'}
                )
                
                citations.append(citation)
        
        return citations
