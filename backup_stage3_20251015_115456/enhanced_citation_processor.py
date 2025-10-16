#!/usr/bin/env python3
"""
Enhanced Citation Processor for Complex Citation Strings

This module handles complex citation strings that include:
- Parallel citations (e.g., "199 Wn. App. 280, 399 P.3d 1195")
- Case history markers (e.g., "(Doe I)", "(Doe II)")
- Docket numbers (e.g., "No. 48000-0-II")
- Pinpoint pages (e.g., "283")
- Publication status (e.g., "(unpublished)")
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)

@dataclass
class CitationComponent:
    """Represents a component of a complex citation."""
    type: str  # 'primary', 'parallel', 'pinpoint', 'docket', 'history', 'status'
    value: str
    start_pos: int
    end_pos: int
    confidence: float = 1.0

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
    is_complex: bool = False
    verification_attempts: List[Dict] = None

class EnhancedCitationProcessor:
    """Process and verify complex citation strings."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self._init_patterns()
        self.verification_cache = {}
    
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
            'f2d': r'\b(\d+)\s+F\.2d\s+(\d+)\b',
            'f_supp': r'\b(\d+)\s+F\.\s*Supp\.\s+(\d+)\b',
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
    
    def process_text(self, text: str) -> List[ComplexCitation]:
        """Process text and extract complex citations."""
        citations = []
        
        # Find potential citation blocks
        citation_blocks = self._find_citation_blocks(text)
        
        for block in citation_blocks:
            citation = self._parse_citation_block(block, text)
            if citation:
                # Determine if this is a complex citation
                citation.is_complex = (
                    len(citation.parallel_citations) > 1 or 
                    len(citation.case_history) > 0 or 
                    len(citation.docket_numbers) > 0 or
                    citation.publication_status is not None
                )
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
            # Pattern for citations with case history
            r'\d+\s+[A-Za-z\.\s]+\d+.*?\([A-Za-z\s]+(?:I|II|III|IV|V|VI|VII|VIII|IX|X)\).*?(?=\n|\.|;)',
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
            if case_name:
                start = block.find(case_name)
                components.append(CitationComponent('case_name', case_name, start, start + len(case_name)))
            
            # Extract all citations
            all_citations = self._extract_all_citations(block)
            primary_citation = all_citations[0] if all_citations else None
            parallel_citations = all_citations[1:] if len(all_citations) > 1 else []
            
            # Add citation components
            for citation in all_citations:
                start = block.find(citation)
                if start != -1:
                    components.append(CitationComponent('citation', citation, start, start + len(citation)))
            
            # Extract pinpoint pages
            pinpoint_pages = self._extract_pinpoint_pages(block)
            for pinpoint in pinpoint_pages:
                start = block.find(pinpoint)
                if start != -1:
                    components.append(CitationComponent('pinpoint', pinpoint, start, start + len(pinpoint)))
            
            # Extract docket numbers
            docket_numbers = self._extract_docket_numbers(block)
            for docket in docket_numbers:
                start = block.find(docket)
                if start != -1:
                    components.append(CitationComponent('docket', docket, start, start + len(docket)))
            
            # Extract case history
            case_history = self._extract_case_history(block)
            for history in case_history:
                start = block.find(history)
                if start != -1:
                    components.append(CitationComponent('history', history, start, start + len(history)))
            
            # Extract publication status
            publication_status = self._extract_publication_status(block)
            if publication_status:
                start = block.find(publication_status)
                components.append(CitationComponent('status', publication_status, start, start + len(publication_status)))
            
            # Extract year
            year = self._extract_year(block)
            
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
                components=components,
                verification_attempts=[]
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
    
    def _extract_all_citations(self, text: str) -> List[str]:
        """Extract all citations from the block."""
        citations = []
        
        # Find all citations in the text
        for pattern_name, pattern in self.primary_patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                volume, page = match.groups()
                citation = f"{volume} {pattern_name.replace('_', '.')} {page}"
                if citation not in citations:
                    citations.append(citation)
        
        return citations
    
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
    
    def verify_complex_citation(self, citation: ComplexCitation) -> Dict[str, Any]:
        """Verify a complex citation using multiple strategies."""
        verification_results = {
            'citation': citation.full_text,
            'is_complex': citation.is_complex,
            'verification_strategies': [],
            'best_result': None,
            'all_results': []
        }
        
        # Strategy 1: Try primary citation
        if citation.primary_citation:
            result = self._verify_single_citation(citation.primary_citation)
            verification_results['verification_strategies'].append({
                'strategy': 'primary_citation',
                'citation': citation.primary_citation,
                'result': result
            })
            verification_results['all_results'].append(result)
        
        # Strategy 2: Try parallel citations
        for parallel in citation.parallel_citations:
            result = self._verify_single_citation(parallel)
            verification_results['verification_strategies'].append({
                'strategy': 'parallel_citation',
                'citation': parallel,
                'result': result
            })
            verification_results['all_results'].append(result)
        
        # Strategy 3: Try with case name if available
        if citation.case_name:
            for citation_text in [citation.primary_citation] + citation.parallel_citations:
                if citation_text:
                    result = self._verify_with_case_name(citation.case_name, citation_text)
                    verification_results['verification_strategies'].append({
                        'strategy': 'with_case_name',
                        'case_name': citation.case_name,
                        'citation': citation_text,
                        'result': result
                    })
                    verification_results['all_results'].append(result)
        
        # Strategy 4: Try docket number if available
        for docket in citation.docket_numbers:
            result = self._verify_docket_number(docket)
            verification_results['verification_strategies'].append({
                'strategy': 'docket_number',
                'docket': docket,
                'result': result
            })
            verification_results['all_results'].append(result)
        
        # Find best result
        best_result = self._find_best_verification_result(verification_results['all_results'])
        verification_results['best_result'] = best_result
        
        return verification_results
    
    def _verify_single_citation(self, citation: str) -> Dict[str, Any]:
        """Verify a single citation using the existing verification system."""
        # This would integrate with your existing citation verification
        # For now, return a placeholder result
        return {
            'citation': citation,
            'verified': False,
            'source': 'enhanced_processor',
            'error': 'Integration with existing verification system needed',
            'confidence': 0.0
        }
    
    def _verify_with_case_name(self, case_name: str, citation: str) -> Dict[str, Any]:
        """Verify citation with case name context."""
        return {
            'citation': citation,
            'case_name': case_name,
            'verified': False,
            'source': 'enhanced_processor_with_case_name',
            'error': 'Integration with existing verification system needed',
            'confidence': 0.0
        }
    
    def _verify_docket_number(self, docket: str) -> Dict[str, Any]:
        """Verify using docket number."""
        return {
            'docket': docket,
            'verified': False,
            'source': 'enhanced_processor_docket',
            'error': 'Docket number verification not implemented',
            'confidence': 0.0
        }
    
    def _find_best_verification_result(self, results: List[Dict]) -> Optional[Dict]:
        """Find the best verification result from multiple attempts."""
        if not results:
            return None
        
        # Sort by confidence and verification status
        sorted_results = sorted(results, key=lambda x: (x.get('verified', False), x.get('confidence', 0)), reverse=True)
        return sorted_results[0]
    
    def format_for_display(self, citation: ComplexCitation, verification_results: Dict) -> Dict:
        """Format complex citation for display in the UI."""
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
            'is_complex': citation.is_complex,
            'verification_status': verification_results.get('best_result', {}).get('verified', False),
            'verification_source': verification_results.get('best_result', {}).get('source', 'unknown'),
            'verification_confidence': verification_results.get('best_result', {}).get('confidence', 0.0),
            'verification_error': verification_results.get('best_result', {}).get('error', ''),
            'verification_strategies': verification_results.get('verification_strategies', [])
        }

# Example usage and testing
if __name__ == "__main__":
    processor = EnhancedCitationProcessor()
    
    # Test with your complex citation
    test_text = """John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017) (Doe I), modified on other grounds on remand, No. 48000-0-II (Wash. Ct. App. Oct. 2, 2018) (Doe II) (unpublished)"""
    
    print("=== Enhanced Citation Processing ===")
    print(f"Input Text: {test_text}")
    print()
    
    # Process the text
    citations = processor.process_text(test_text)
    
    for i, citation in enumerate(citations):
        print(f"=== Citation {i+1} ===")
        print(f"Full Text: {citation.full_text}")
        print(f"Case Name: {citation.case_name}")
        print(f"Primary Citation: {citation.primary_citation}")
        print(f"Parallel Citations: {citation.parallel_citations}")
        print(f"Pinpoint Pages: {citation.pinpoint_pages}")
        print(f"Docket Numbers: {citation.docket_numbers}")
        print(f"Case History: {citation.case_history}")
        print(f"Publication Status: {citation.publication_status}")
        print(f"Year: {citation.year}")
        print(f"Is Complex: {citation.is_complex}")
        print()
        
        # Verify the citation
        verification_results = processor.verify_complex_citation(citation)
        display_format = processor.format_for_display(citation, verification_results)
        
        print("=== Verification Results ===")
        print(f"Verification Status: {display_format['verification_status']}")
        print(f"Verification Source: {display_format['verification_source']}")
        print(f"Verification Confidence: {display_format['verification_confidence']}")
        print(f"Verification Error: {display_format['verification_error']}")
        print()
        
        print("=== Verification Strategies ===")
        for strategy in display_format['verification_strategies']:
            print(f"Strategy: {strategy['strategy']}")
            if 'citation' in strategy:
                print(f"  Citation: {strategy['citation']}")
            if 'case_name' in strategy:
                print(f"  Case Name: {strategy['case_name']}")
            if 'docket' in strategy:
                print(f"  Docket: {strategy['docket']}")
            print(f"  Result: {strategy['result']}")
            print() 