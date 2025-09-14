"""
Unified Citation Extraction Service

This service consolidates all citation extraction logic into a single, 
authoritative implementation to eliminate duplicate functions and 
ensure consistent pattern application across the entire system.

Key Principles:
1. Single source of truth for extraction patterns
2. Strict separation of extracted vs canonical data
3. Consistent handling of legal entity names (apostrophes, ampersands, etc.)
4. No overwriting of document-extracted names with verification results
"""

import re
from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ExtractionResult:
    """Result of citation extraction from document text"""
    citation_text: str
    extracted_case_name: str
    extracted_date: str
    start_index: int
    end_index: int
    confidence: float = 0.9
    extraction_method: str = "unified_extraction_service"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            'citation': self.citation_text,
            'extracted_case_name': self.extracted_case_name,
            'extracted_date': self.extracted_date,
            'start_index': self.start_index,
            'end_index': self.end_index,
            'confidence': self.confidence,
            'extraction_method': self.extraction_method,
            'verified': False,  # Always False for extraction - verification is separate
            'canonical_name': None,  # Always None for extraction - verification sets this
            'canonical_date': None,  # Always None for extraction - verification sets this
            'canonical_url': None,  # Always None for extraction - verification sets this
        }

class UnifiedExtractionService:
    """
    DEPRECATED: Use extract_case_name_and_date_master() instead.
    
    This class is deprecated and will be removed in v3.0.0.
    Use extract_case_name_and_date_master() for consistent extraction results.
    
    Single authoritative service for citation extraction.
    
    This replaces all duplicate _extract_citation_blocks functions
    and ensures consistent pattern application.
    """
    
    def __init__(self):
        """Initialize the unified extraction service"""
        self._init_patterns()
        self._init_cleanup_patterns()
        logger.info("🔧 UnifiedExtractionService initialized with enhanced patterns")
    
    def _init_patterns(self):
        """Initialize enhanced extraction patterns that handle legal entity names"""
        
        self.citation_block_pattern = re.compile(
            r'([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*\s+v\.\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*|'  # Enhanced v. pattern
            r'State(?:\s+of\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*)?\s+v\.\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*|'  # Enhanced State v. pattern
            r'In\s+re\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*)'  # Enhanced In re pattern
            r'[,\s]*'  # Optional comma and whitespace after case name
            r'([^()]+)'  # All citations and content between case name and year
            r'\((\d{4})\)'  # Year in parentheses
        )
        
        self.individual_citation_patterns = [
            re.compile(r'\b\d+\s+[A-Z][a-z]+\.?\s*\d*d\s+\d+\b'),  # Washington reports: 192 Wn.2d 453
            re.compile(r'\b\d+\s+P\.?\s*\d*d\s+\d+\b'),  # Pacific reports: 430 P.3d 655
            re.compile(r'\b\d+\s+[A-Z]+\.?\s+\d+\b'),  # General format: 123 ABC 456
        ]
        
        logger.info("✅ Enhanced extraction patterns initialized")
    
    def _init_cleanup_patterns(self):
        """Initialize patterns for cleaning extracted case names"""
        
        self.contamination_phrases = [
            r'\b(?:de\s+novo|questions?\s+of\s+law|statutory\s+interpretation)\b',
            r'\b(?:certified\s+questions?|federal\s+court|this\s+court)\b',
            r'\b(?:reviews?\s+de\s+novo|in\s+light\s+of)\b',
            r'\b(?:record\s+certified\s+by|issue\s+of\s+law)\b',
            r'\b(?:brief\s+at|opening\s+br\.|reply\s+br\.)\b',
            r'\b(?:see|citing|quoting|accord|id\.)\b',
        ]
        
        self.compiled_cleanup_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.contamination_phrases
        ]
        
        logger.info("✅ Cleanup patterns initialized")
    
    def extract_citations_from_text(self, text: str) -> List[ExtractionResult]:
        """
        Main extraction method - extracts all citations from text.
        
        This is the single source of truth for citation extraction.
        All other extraction methods should use this function.
        """
        if not text or not text.strip():
            return []
        
        logger.info(f"🔍 Starting unified extraction for text length: {len(text)}")
        
        results = self._extract_citation_blocks(text)
        
        if not results:
            logger.info("📝 No citation blocks found, trying individual extraction")
            results = self._extract_individual_citations(text)
        
        for result in results:
            result.extracted_case_name = self._clean_case_name(result.extracted_case_name)
        
        logger.info(f"✅ Unified extraction completed: {len(results)} citations found")
        return results
    
    def _extract_citation_blocks(self, text: str) -> List[ExtractionResult]:
        """Extract complete citation blocks with case names and years"""
        results = []
        
        matches = list(self.citation_block_pattern.finditer(text))
        logger.info(f"🔍 Found {len(matches)} citation block matches")
        
        for match in matches:
            case_name = match.group(1).strip().rstrip(',')
            citations_text = match.group(2).strip()
            year = match.group(3)
            start, end = match.span()
            
            individual_citations = self._parse_citations_from_block(citations_text)
            
            for citation_text in individual_citations:
                results.append(ExtractionResult(
                    citation_text=citation_text.strip(),
                    extracted_case_name=case_name,
                    extracted_date=year,
                    start_index=start,
                    end_index=end,
                    confidence=0.9,
                    extraction_method="citation_block"
                ))
                
        
        return results
    
    def _extract_individual_citations(self, text: str) -> List[ExtractionResult]:
        """Extract individual citations when block extraction fails"""
        results = []
        
        for pattern in self.individual_citation_patterns:
            for match in pattern.finditer(text):
                citation_text = match.group(0)
                start, end = match.span()
                
                case_name = self._extract_case_name_from_context(text, start)
                extracted_date = self._extract_date_from_context(text, start)
                
                if case_name:  # Only add if we found a case name
                    results.append(ExtractionResult(
                        citation_text=citation_text,
                        extracted_case_name=case_name,
                        extracted_date=extracted_date or "N/A",
                        start_index=start,
                        end_index=end,
                        confidence=0.7,
                        extraction_method="individual_citation"
                    ))
        
        return results
    
    def _parse_citations_from_block(self, citations_text: str) -> List[str]:
        """Parse individual citations from a citation block"""
        citations = re.split(r'[,;]\s*', citations_text)
        
        cleaned_citations = []
        for citation in citations:
            citation = citation.strip()
            if citation and any(pattern.search(citation) for pattern in self.individual_citation_patterns):
                cleaned_citations.append(citation)
        
        return cleaned_citations
    
    def _extract_case_name_from_context(self, text: str, citation_position: int) -> Optional[str]:
        """Extract case name from context around a citation"""
        context_start = max(0, citation_position - 200)
        context = text[context_start:citation_position]
        
        case_name_patterns = [
            r'([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*)\s+v\.\s+([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*)',
            r'(In\s+re\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*)',
            r'(State(?:\s+of\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*)?)\s+v\.\s+([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*)',
        ]
        
        for pattern in case_name_patterns:
            matches = list(re.finditer(pattern, context))
            if matches:
                match = matches[-1]
                if len(match.groups()) == 2:  # v. pattern
                    return f"{match.group(1).strip()} v. {match.group(2).strip()}"
                else:  # In re pattern
                    return match.group(1).strip()
        
        return None
    
    def _extract_date_from_context(self, text: str, citation_position: int) -> Optional[str]:
        """Extract date from context around a citation"""
        context_start = max(0, citation_position - 50)
        context_end = min(len(text), citation_position + 100)
        context = text[context_start:context_end]
        
        year_match = re.search(r'\((\d{4})\)', context)
        return year_match.group(1) if year_match else None
    
    def _clean_case_name(self, case_name: str) -> str:
        """LEGACY cleaner wrapper (deprecated). Uses shared cleaner."""
        try:
            from src.utils.deprecation import deprecated
            from src.utils.case_name_cleaner import clean_extracted_case_name
            @deprecated(replacement='src.utils.case_name_cleaner.clean_extracted_case_name')
            def _proxy(val: str) -> str:
                return clean_extracted_case_name(val)
            return _proxy(case_name)
        except Exception:
            from src.utils.case_name_cleaner import clean_extracted_case_name
            return clean_extracted_case_name(case_name)
    
    def validate_extraction_integrity(self, extracted_name: str, canonical_name: str) -> bool:
        """
        Validate that canonical name hasn't contaminated extracted name.
        
        This is a critical check to ensure data separation.
        """
        if not extracted_name or not canonical_name:
            return True  # No contamination possible
        
        if extracted_name == canonical_name:
            logger.warning(f"⚠️ Potential contamination: extracted='{extracted_name}' == canonical='{canonical_name}'")
            return False
        
        return True

_extraction_service = None

def get_extraction_service() -> UnifiedExtractionService:
    """Get the global extraction service instance"""
    global _extraction_service
    if _extraction_service is None:
        _extraction_service = UnifiedExtractionService()
    return _extraction_service

def extract_citations_unified(text: str) -> List[Dict[str, Any]]:
    """
    Unified citation extraction function.
    
    This should replace all other citation extraction calls in the system.
    """
    service = get_extraction_service()
    # Use modern process_text instead of deprecated extract_citations_from_text
    results = service.process_text(text)
    return [result.to_dict() for result in results]

