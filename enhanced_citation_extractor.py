#!/usr/bin/env python3
"""
Enhanced Citation Extractor for Complex Citation Strings

This module handles complex citation strings that include:
- Parallel citations (e.g., "199 Wn. App. 280, 399 P.3d 1195")
- Case history markers (e.g., "(Doe I)", "(Doe II)")
- Docket numbers (e.g., "No. 48000-0-II")
- Pinpoint pages (e.g., "283")
- Publication status (e.g., "(unpublished)")
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CitationComponent:
    """Represents a component of a complex citation."""
    type: str  # 'primary', 'parallel', 'pinpoint', 'docket', 'history', 'status'
    value: str
    start_pos: int
    end_pos: int

@dataclass
class ComplexCitation:
    """Represents a complete complex citation string."""
    full_text: str
    case_name: Optional[str]
    primary_citation: Optional[str]
    parallel_citations: List[str]
    pinpoint_pages: List[str]
    docket_numbers: List[str]
    case_history: List[str]
    publication_status: Optional[str]
    year: Optional[str]
    components: List[CitationComponent]

class EnhancedCitationExtractor:
    """Extract and parse complex citation strings."""
    
    def __init__(self):
        self._init_patterns()
    
    def _init_patterns(self):
        """Initialize regex patterns for different citation components."""
        
        # Primary citation patterns (volume reporter page)
        self.primary_patterns = {
            'wn_app': r'\b(\d+)\s+Wn\.\s*App\.\s+(\d+)\b',
            'wn2d': r'\b(\d+)\s+Wn\.2d\s+(\d+)\b',
            'p3d': r'\b(\d+)\s+P\.3d\s+(\d+)\b',
            'p2d': r'\b(\d+)\s+P\.2d\s+(\d+)\b',
            'us': r'\b(\d+)\s+U\.\s*S\.\s+(\d+)\b',
            'f3d': r'\b(\d+)\s+F\.3d\s+(\d+)\b',
        }
        
        # Case name pattern
        self.case_name_pattern = r'\b([A-Z][A-Za-z\s\.,&\'\"\(\)]+v\.\s+[A-Z][A-Za-z\s\.,&\'\"\(\)]+?)(?=\s*[,;]|\s*\d+\s+[A-Z])'
        
        # Pinpoint page pattern (single number after comma)
        self.pinpoint_pattern = r',\s*(\d+)(?=\s*[,;]|\s*\(|\s*$)'
        
        # Docket number pattern
        self.docket_pattern = r'No\.\s*([0-9\-]+)'
        
        # Case history pattern (e.g., "(Doe I)", "(Doe II)")
        self.history_pattern = r'\(([A-Za-z\s]+(?:I|II|III|IV|V|VI|VII|VIII|IX|X))\)'
        
        # Publication status pattern
        self.status_pattern = r'\((unpublished|published|memorandum|per\s+curiam)\)'
        
        # Year pattern
        self.year_pattern = r'\((\d{4})\)'
    
    def extract_complex_citations(self, text: str) -> List[ComplexCitation]:
        """Extract complex citation strings from text."""
        citations = []
        
        # Find potential citation blocks (text containing multiple citations)
        citation_blocks = self._find_citation_blocks(text)
        
        for block in citation_blocks:
            citation = self._parse_citation_block(block, text)
            if citation:
                citations.append(citation)
        
        return citations
    
    def _find_citation_blocks(self, text: str) -> List[str]:
        """Find potential citation blocks in text."""
        blocks = []
        
        # Pattern to find citation blocks (contains multiple citations or complex structure)
        block_patterns = [
            # Pattern for case name followed by multiple citations
            r'[A-Z][A-Za-z\s\.,&\'\"\(\)]+v\.\s+[A-Z][A-Za-z\s\.,&\'\"\(\)]+?,\s+\d+\s+[A-Za-z\.\s]+\d+.*?(?=\n|\.|;)',
            # Pattern for multiple citations separated by commas
            r'\d+\s+[A-Za-z\.\s]+\d+.*?(?:,\s*\d+\s+[A-Za-z\.\s]+\d+).*?(?=\n|\.|;)',
            # Pattern for citations with docket numbers
            r'\d+\s+[A-Za-z\.\s]+\d+.*?No\.\s*[0-9\-]+.*?(?=\n|\.|;)',
        ]
        
        for pattern in block_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                block = match.group(0).strip()
                if len(block) > 20:  # Only consider substantial blocks
                    blocks.append(block)
        
        return list(set(blocks))  # Remove duplicates
    
    def _parse_citation_block(self, block: str, full_text: str) -> Optional[ComplexCitation]:
        """Parse a citation block into structured components."""
        try:
            components = []
            
            # Extract case name
            case_name = self._extract_case_name(block)
            
            # Extract all citations (primary + parallels)
            all_citations = self._extract_parallel_citations(block)
            primary_citation = all_citations[0] if all_citations else None
            parallel_citations = all_citations[1:] if len(all_citations) > 1 else []
            
            # Extract pinpoint pages
            pinpoint_pages = self._extract_pinpoint_pages(block)
            
            # Extract docket numbers
            docket_numbers = self._extract_docket_numbers(block)
            
            # Extract case history
            case_history = self._extract_case_history(block)
            
            # Extract publication status
            publication_status = self._extract_publication_status(block)
            
            # Extract year
            year = self._extract_year(block)
            
            # Build components list
            if case_name:
                components.append(CitationComponent('case_name', case_name, 0, len(case_name)))
            
            if primary_citation:
                start = block.find(primary_citation)
                components.append(CitationComponent('primary', primary_citation, start, start + len(primary_citation)))
            
            for parallel in parallel_citations:
                start = block.find(parallel)
                components.append(CitationComponent('parallel', parallel, start, start + len(parallel)))
            
            for pinpoint in pinpoint_pages:
                start = block.find(pinpoint)
                components.append(CitationComponent('pinpoint', pinpoint, start, start + len(pinpoint)))
            
            for docket in docket_numbers:
                start = block.find(docket)
                components.append(CitationComponent('docket', docket, start, start + len(docket)))
            
            for history in case_history:
                start = block.find(history)
                components.append(CitationComponent('history', history, start, start + len(history)))
            
            if publication_status:
                start = block.find(publication_status)
                components.append(CitationComponent('status', publication_status, start, start + len(publication_status)))
            
            return ComplexCitation(
                full_text=block,
                case_name=case_name,
                primary_citation=primary_citation,
                parallel_citations=parallel_citations,
                pinpoint_pages=pinpoint_pages,
                docket_numbers=docket_numbers,
                case_history=case_history,
                publication_status=publication_status,
                year=year,
                components=components
            )
            
        except Exception as e:
            logger.error(f"Error parsing citation block '{block}': {e}")
            return None
    
    def _extract_case_name(self, text: str) -> Optional[str]:
        """Extract case name from citation block."""
        match = re.search(self.case_name_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_primary_citation(self, text: str) -> Optional[str]:
        """Extract the primary citation (first citation in the block)."""
        for pattern_name, pattern in self.primary_patterns.items():
            match = re.search(pattern, text)
            if match:
                volume, page = match.groups()
                # Properly format reporter names
                reporter_name = self._format_reporter_name(pattern_name)
                return f"{volume} {reporter_name} {page}"
        return None
    
    def _extract_parallel_citations(self, text: str) -> List[str]:
        """Extract parallel citations from the block."""
        parallel_citations = []
        
        # Find all citations in the text
        for pattern_name, pattern in self.primary_patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                volume, page = match.groups()
                # Properly format reporter names
                reporter_name = self._format_reporter_name(pattern_name)
                citation = f"{volume} {reporter_name} {page}"
                if citation not in parallel_citations:
                    parallel_citations.append(citation)
        
        return parallel_citations
    
    def _format_reporter_name(self, pattern_name: str) -> str:
        """Format reporter name from pattern name to proper citation format."""
        reporter_mapping = {
            'wn_app': 'Wn. App.',
            'wn2d': 'Wn.2d',
            'p3d': 'P.3d',
            'p2d': 'P.2d',
            'us': 'U.S.',
            'f3d': 'F.3d',
        }
        return reporter_mapping.get(pattern_name, pattern_name.replace('_', '.'))
    
    def _extract_pinpoint_pages(self, text: str) -> List[str]:
        """Extract pinpoint page numbers."""
        matches = re.findall(self.pinpoint_pattern, text)
        return [match for match in matches if match.isdigit()]
    
    def _extract_docket_numbers(self, text: str) -> List[str]:
        """Extract docket numbers."""
        matches = re.findall(self.docket_pattern, text)
        return matches
    
    def _extract_case_history(self, text: str) -> List[str]:
        """Extract case history markers."""
        matches = re.findall(self.history_pattern, text)
        return matches
    
    def _extract_publication_status(self, text: str) -> Optional[str]:
        """Extract publication status."""
        match = re.search(self.status_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
    
    def _extract_year(self, text: str) -> Optional[str]:
        """Extract year from citation."""
        match = re.search(self.year_pattern, text)
        if match:
            return match.group(1)
        return None
    
    def format_citation_summary(self, citation: ComplexCitation) -> Dict:
        """Format a complex citation into a summary for display."""
        return {
            'full_text': citation.full_text,
            'case_name': citation.case_name,
            'primary_citation': citation.primary_citation,
            'parallel_citations': citation.parallel_citations,
            'pinpoint_pages': citation.pinpoint_pages,
            'docket_numbers': citation.docket_numbers,
            'case_history': citation.case_history,
            'publication_status': citation.publication_status,
            'year': citation.year,
            'is_complex': len(citation.parallel_citations) > 1 or len(citation.case_history) > 0
        }

# Example usage
if __name__ == "__main__":
    extractor = EnhancedCitationExtractor()
    
    # Test with your complex citation
    test_text = """John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017) (Doe I), modified on other grounds on remand, No. 48000-0-II (Wash. Ct. App. Oct. 2, 2018) (Doe II) (unpublished)"""
    
    citations = extractor.extract_complex_citations(test_text)
    
    for citation in citations:
        summary = extractor.format_citation_summary(citation)
        print("Complex Citation Analysis:")
        print(f"Full Text: {summary['full_text']}")
        print(f"Case Name: {summary['case_name']}")
        print(f"Primary Citation: {summary['primary_citation']}")
        print(f"Parallel Citations: {summary['parallel_citations']}")
        print(f"Pinpoint Pages: {summary['pinpoint_pages']}")
        print(f"Docket Numbers: {summary['docket_numbers']}")
        print(f"Case History: {summary['case_history']}")
        print(f"Publication Status: {summary['publication_status']}")
        print(f"Year: {summary['year']}")
        print(f"Is Complex: {summary['is_complex']}")
        print("-" * 50) 