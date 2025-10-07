"""
Citation Extractor

This module contains core citation extraction logic using both regex-based
and eyecite-based approaches.
"""

import re
from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

import logging
from typing import List, Dict, Any, Optional
from src.models import CitationResult
from src.citation_types import CitationMatch, CitationList, CitationDict
from src.citation_utils import (
    normalize_citation, extract_citation_components, 
    extract_context, is_valid_case_name
)

logger = logging.getLogger(__name__)

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
        self._init_citation_block_patterns()
    
    def _init_patterns(self):
        """Initialize citation patterns."""
        self.citation_patterns = [
            # WL (WestLaw) citations - high priority since they're very specific
            r'\b(\d{4})\s+WL\s+(\d+)\b',
            
            # Federal Reporter (e.g., 123 F.3d 456, 123 F.2d 456, 123 F. Supp. 2d 456)
            r'\b(\d+)\s+F\.?\s*(?:Supp\.?|App\.x)?\s*(?:\d+\s*)?(?:d|D)\.?\s+\d+\b',
            r'\b\d+\s+A\.(?:\s*\d*d?\s+\d+\b|\s*\d+\.\d+\b)',  # Atlantic Reporter
            r'\b\d+\s+So\.(?:\s*\d*d?\s+\d+\b|\s*\d+\.\d+\b)',  # Southern Reporter
            r'\b\d+\s+Cal\.(?:\s*\d*d?\s+\d+\b|\s*\d+\.\d+\b)'  # California Reporter
            
            r'\b\d+\s+WL\s+\d+\b',
            r'\b\d{4}\s+LEXIS\s+\d+\b',
        ]
        
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.citation_patterns]
    
    def _init_case_name_patterns(self):
        """Initialize case name extraction patterns."""
        self.case_name_patterns = [
            r'(State(?:\s+of\s+[A-Z][a-z]+)?)\s+v\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            
            r'In\s+re\s+([A-Z][a-zA-Z\s&.,\'-]+)',
            r'In\s+re\s+the\s+([A-Z][a-zA-Z\s&.,\'-]+)',
            
            r'([A-Z][a-zA-Z&.\'-]+(?:\s+[A-Z][a-zA-Z&.\'-]+)*)\s+v\.\s+([A-Z][a-zA-Z&.\'-]+(?:\s+[A-Z][a-zA-Z&.\'-]+)*)',
            r'([A-Z][a-zA-Z&.\'-]+(?:\s+[A-Z][a-zA-Z&.\'-]+)*)\s+vs\.\s+([A-Z][a-zA-Z&.\'-]+(?:\s+[A-Z][a-zA-Z&.\'-]+)*)',
            r'([A-Z][a-zA-Z&.\'-]+(?:\s+[A-Z][a-zA-Z&.\'-]+)*)\s+versus\s+([A-Z][a-zA-Z&.\'-]+(?:\s+[A-Z][a-zA-Z&.\'-]+)*)',
            
            r'([A-Z][a-zA-Z&.\'-]+(?:\s+[A-Z][a-zA-Z&.\'-]+)*)\s+&\s+([A-Z][a-zA-Z&.\'-]+(?:\s+[A-Z][a-zA-Z&.\'-]+)*)'
        ]
        
        self.compiled_case_patterns = [re.compile(pattern) for pattern in self.case_name_patterns]
    
    def _init_citation_block_patterns(self):
        """Initialize patterns for identifying the start of a citation block."""
        self.citation_block_patterns = [
            r'\b\d+\s+U\.S\.\s+\d+\b',
            r'\b\d+\s+S\.Ct\.\s+\d+\b',
            r'\b\d+\s+F\.\d*d?\b',
            r'\b\d+\s+F\.Supp\.\d*d?\b',
            r'\b\d+\s+F\.App\'x\b',
            r'\b\d+\s+P\.\d*d?\s+\d+\b',
            r'\b\d+\s+N\.W\.\d*d?\s+\d+\b',
            r'\b\d+\s+S\.W\.\d*d?\s+\d+\b',
            r'\b\d+\s+N\.E\.\d*d?\s+\d+\b',
            r'\b\d+\s+S\.E\.\d*d?\s+\d+\b',
            r'\b\d+\s+A\.\d*d?\s+\d+\b',
            r'\b\d+\s+So\.\d*d?\s+\d+\b',
            r'\b\d+\s+Cal\.\d*d?\s+\d+\b',
            # Washington Supreme Court (e.g., 183 Wash.2d 649, 183 Wn.2d 649, 183 Wash. 2d 649)
            r'\b(\d+)\s+(?:Wash\.|Wn\.)(?:\s*2d|2d)\s+(\d+)\b',  # Handles both 'Wash.2d' and 'Wash. 2d'
            r'\b(\d+)\s+Wash\.(?:\s*2d|2d)\s+(\d+)\b',  # Specific for 'Wash.'
            r'\b(\d+)\s+Wn\.(?:\s*2d|2d)\s+(\d+)\b',   # Specific for 'Wn.'
            
            # Washington Court of Appeals (e.g., 12 Wash. App. 2d 345, 12 Wn. App. 2d 345, 12 Wash. App. 2d 345)
            r'\b(\d+)\s+(?:Wash\.|Wn\.)\s*App\.(?:\s*2d|2d)?\s*(\d+)\b',
            r'\b(\d+)\s+Wash\.\s*App\.(?:\s*2d|2d)?\s*(\d+)\b',
            r'\b(\d+)\s+Wn\.\s*App\.(?:\s*2d|2d)?\s*(\d+)\b',
            
            # Pacific Reporter (e.g., 355 P.3d 258, 278 P.3d 173, 976 P.2d 1229)
            # Handles various formats: P.3d, P. 3d, P3d, etc.
            r'\b(\d+)\s+P\.(?:\s*3d|3d|\s*2d|2d|\s*d\.)?\s*(\d+)\b',
            r'\b(\d+)\s+P(?:\s*3d|3d|\s*2d|2d|\s*d\.)?\s+(\d+)\b',  # Handles 'P3d', 'P 3d', etc.
            r'\b(\d+)\s+P\.?\s*(?:3d|2d|d\.)?\s*(\d+)\b',  # Handles 'P.3d', 'P. 3d', 'P3d', etc.
            r'\b\d+\s+WL\s+\d+\b',
            r'\b\d{4}\s+LEXIS\s+\d+\b',
        ]
        self.compiled_citation_block_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.citation_block_patterns]
    
    def _extract_citation_blocks(self, text: str) -> CitationList:
        """
        Extract complete citation blocks: case name + all parallel citations + year.
        This handles cases like "DeSean v. Sanger, 2 Wn. 3d 329, 334-35, 536 P.3d 191 (2023)"
        """
        if not text:
            return []
        
        logger.info(f"🔍 [CITATION_BLOCKS] Starting citation block extraction for text: '{text[:200]}...'")
        citations = []
        
        citation_block_pattern = re.compile(
            r'([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*\s+v\.\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*|'  # Enhanced v. pattern - REQUIRES subsequent words to be capitalized
            r'State(?:\s+of\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*)??\s+v\.\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*|'  # Enhanced State v. pattern
            r'In\s+re\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*)'  # Enhanced In re pattern
            r'[,\s]*'  # Optional comma and whitespace after case name
            r'([^()]+)'  # All citations and content between case name and year
            r'\((\d{4})\)'  # Year in parentheses
        )
        
        matches = list(citation_block_pattern.finditer(text))
        logger.info(f"🔍 [CITATION_BLOCKS] Pattern found {len(matches)} matches")
        for i, match in enumerate(matches):
            logger.info(f"🔍 [CITATION_BLOCKS] Match {i+1}: '{match.group(0)}'")
        
        for match in citation_block_pattern.finditer(text):
            case_name = match.group(1).strip().rstrip(',')  # Remove trailing comma
            
            contamination_phrases = [
                r'\b(de\s+novo)\b', r'\b(questions?\s+of\s+law)\b', r'\b(statutory\s+interpretation)\b',
                r'\b(in\s+light\s+of)\b', r'\b(the\s+record\s+certified)\b', r'\b(federal\s+court)\b',
                r'\b(this\s+court\s+reviews?)\b', r'\b(we\s+review)\b', r'\b(certified\s+questions?)\b',
                r'\b(issue\s+of\s+law)\b', r'\b(also\s+an?\s+issue)\b', r'\b(are\s+that)\b', r'\b(and\s+by)\b',
                r'\b(is\s+also)\b', r'\b(an\s+issue)\b'
            ]
            
            for phrase_pattern in contamination_phrases:
                case_name = re.sub(phrase_pattern, '', case_name, flags=re.IGNORECASE)
            
            case_name_clean_patterns = [
                r'([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*)\s+v\.\s+([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*)',
                r'(State(?:\s+of\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*)?\s+v\.\s+([A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*)',
                r'(In\s+re\s+[A-Z][a-zA-Z\'\.\&]*(?:\s+(?:[A-Z][a-zA-Z\'\.\&]*|of|the|and|&))*)'
            ]
            
            cleaned_name = None
            for clean_pattern in case_name_clean_patterns:
                clean_match = re.search(clean_pattern, case_name)
                if clean_match:
                    if len(clean_match.groups()) >= 2:
                        cleaned_name = f"{clean_match.group(1).strip()} v. {clean_match.group(2).strip()}"
                    else:
                        cleaned_name = clean_match.group(1).strip()
                    break
            
            if cleaned_name:
                case_name = cleaned_name
            
            case_name = re.sub(r'\s+', ' ', case_name).strip()
            case_name = re.sub(r'^[.\s,;:]+', '', case_name)
            case_name = re.sub(r'^(the|a|an)\s+', '', case_name, flags=re.IGNORECASE)
            
            citations_text = match.group(2).strip()
            year = match.group(3)
            start, end = match.span()
            
            logger.info(f"🔍 Found citation block: '{case_name}' with citations '{citations_text}' year {year}")
            
            individual_citations = self._extract_citations_from_block(citations_text)
            
            for citation_text in individual_citations:
                citation_start = text.find(citation_text, start)
                citation_end = citation_start + len(citation_text) if citation_start != -1 else start
                
                citation = CitationResult(
                    citation=citation_text,
                    start_index=citation_start,
                    end_index=citation_end,
                    extracted_case_name=case_name,
                    extracted_date=year,
                    canonical_name=None,
                    canonical_date=None,
                    url=None,
                    verified=False,
                    source="citation_block",
                    confidence=0.9,  # Higher confidence for block extraction
                    metadata={
                        'block_case_name': case_name,
                        'block_year': year,
                        'parallel_citations': individual_citations
                    }
                )
                
                
                citations.append(citation)
        
        return citations
    
    def _extract_citations_from_block(self, citations_text: str) -> List[str]:
        """Extract individual citations from a citation block text."""
        citations = []
        
        parts = [part.strip() for part in citations_text.split(',')]
        
        for part in parts:
            if not part or len(part) < 5:  # Skip very short parts
                continue
            
            for pattern in self.compiled_patterns:
                if pattern.search(part):
                    citations.append(part)
                    break
        
        return citations
    
    def _extract_case_name_proximity_based(self, text: str, start: int, end: int, citation_text: str) -> Optional[str]:
        """Extract case name based on proximity to citation."""
        # Look for case name in the 200 characters before the citation
        search_start = max(0, start - 200)
        search_text = text[search_start:start]
        
        # Try each case name pattern
        for pattern in self.compiled_case_patterns:
            matches = list(pattern.finditer(search_text))
            if matches:
                # Get the closest match to the citation
                closest_match = matches[-1]  # Last match is closest to citation
                if len(closest_match.groups()) >= 2:
                    return f"{closest_match.group(1).strip()} v. {closest_match.group(2).strip()}"
                else:
                    return closest_match.group(1).strip()
        
        return None

    def extract_with_regex(self, text: str) -> CitationList:
        """Extract citations using regex patterns."""
        if not text:
            return []
        
        citation_blocks = self._extract_citation_blocks(text)
        if citation_blocks:
            logger.info(f"🔍 Extracted {len(citation_blocks)} citation blocks")
            return citation_blocks
        
        citations = []
        
        for pattern in self.compiled_patterns:
            for match in pattern.finditer(text):
                citation_text = match.group(0)
                start, end = match.span()
                
                logger.info(f"🔍 Extracted citation: '{citation_text}' at position {start}-{end}")
                
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
                
                case_name = self._extract_case_name_proximity_based(text, start, end, citation_text)
                
                if case_name:
                    citation.extracted_case_name = case_name
                
                citation_year = self._extract_year_from_citation(citation_text, text, start)
                if citation_year:
                    citation.extracted_date = citation_year
                
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
    
    def _extract_eyecite_metadata(self, citation: CitationResult, citation_obj) -> None:
        """Extract metadata from eyecite citation object."""
        if not citation or not citation_obj:
            return
            
        # Extract basic metadata
        metadata = citation.metadata or {}
        metadata.update({
            'eyecite_type': type(citation_obj).__name__,
            'matched_text': getattr(citation_obj, 'matched_text', ''),
            'groups': getattr(citation_obj, 'groups', {}),
        })
        
        # Special handling for WL citations
        wl_match = re.match(r'^(\d{4})\s+WL\s+(\d+)$', citation.citation)
        if wl_match:
            metadata.update({
                'citation_type': 'westlaw',
                'year': wl_match.group(1),
                'document_number': wl_match.group(2),
                'full_citation': f"{wl_match.group(1)} WL {wl_match.group(2)}"
            })
            
            # If we don't have a year yet, use the one from the WL citation
            if not citation.extracted_date:
                citation.extracted_date = wl_match.group(1)
                
        citation.metadata = metadata
    
    def _extract_year_from_citation(self, citation_text: str, text: str, start_index: int) -> Optional[str]:
        """Enhanced year extraction with multiple strategies."""
        # Check for WL citation format (e.g., 2006 WL 3801910)
        wl_match = re.match(r'^(\d{4})\s+WL\s+\d+$', citation_text)
        if wl_match:
            return wl_match.group(1)
            
        # Check for LEXIS citation format (e.g., 2023 U.S. LEXIS 1234)
        lexis_match = re.search(r'^(\d{4})\s+LEXIS\s+\d+$', citation_text)
        if lexis_match:
            return lexis_match.group(1)
        
        # Check if year is already in the citation (e.g., 123 F.3d 456 (2023))
        year_match = re.search(r'\(\s*(\d{4})\s*\)', citation_text)
        if year_match:
            return year_match.group(1)
        
        # Look for year in surrounding text (50 characters before and after)
        context_start = max(0, start_index - 50)
        context_end = min(len(text), start_index + len(citation_text) + 50)
        context = text[context_start:context_end]
        
        # Look for year in parentheses after the citation
        year_after = re.search(r'\b(?:\d{4})\b', context[len(citation_text):])
        if year_after:
            return year_after.group(0)
            
        # Look for year in the citation itself (e.g., 2023 U.S. LEXIS 1234)
        year_in_cite = re.search(r'\b(19|20)\d{2}\b', citation_text)
        if year_in_cite:
            return year_in_cite.group(0)
            
        return None
    
    def extract_wl_citations(self, text: str) -> List[CitationResult]:
        """Extract WL citations from text using specific WL pattern."""
        pattern = r'\b(\d{4})\s+WL\s+(\d+)\b'
        citations = []
        
        for match in re.finditer(pattern, text):
            year = match.group(1)
            doc_number = match.group(2)
            citation_text = match.group(0)
            start, end = match.span()
            
            # Extract context around the citation
            context_start = max(0, start - 100)
            context_end = min(len(text), end + 100)
            context = text[context_start:context_end]
            
            citation = CitationResult(
                citation=citation_text,
                start_index=start,
                end_index=end,
                extracted_case_name=None,
                extracted_date=year,
                canonical_name=None,
                canonical_date=None,
                url=None,
                verified=False,
                source="wl_regex",
                confidence=0.95,  # High confidence for WL citations
                context=context,
                metadata={
                    'citation_type': 'westlaw',
                    'year': year,
                    'document_number': doc_number,
                    'full_citation': citation_text
                }
            )
            citations.append(citation)
        
        return citations

    def extract_citations(self, text: str, use_eyecite: bool = True) -> CitationList:
        """Extract citations using both regex and eyecite methods."""
        if not text:
            return CitationList()
            
        citations = []
        
        # Extract WL citations first (high priority)
        wl_citations = self.extract_wl_citations(text)
        citations.extend(wl_citations)
        
        regex_citations = self.extract_with_regex(text)
        citations.extend(regex_citations)
        
        if use_eyecite and EYECITE_AVAILABLE:
            eyecite_citations = self.extract_with_eyecite(text)
            citations.extend(eyecite_citations)
        
        return self._deduplicate_citations(citations)
    
    def _deduplicate_citations(self, citations: CitationList) -> CitationList:
        """Remove duplicate citations based on text and position."""
        seen = set()
        unique_citations = []
        
        for citation in citations:
            key = (citation.citation, citation.start_index, citation.end_index)
            if key not in seen:
                seen.add(key)
                unique_citations.append(citation)
        
        return unique_citations 