#!/usr/bin/env python3
"""
Complex Citation Integration for CaseStrainer

This module integrates the enhanced complex citation processing with the existing
CaseStrainer codebase, specifically working with the EnhancedMultiSourceVerifier.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ComplexCitationData:
    """Structured data for complex citations."""
    full_text: str
    case_name: Optional[str]
    primary_citation: Optional[str]
    parallel_citations: List[str]
    pinpoint_pages: List[str]
    docket_numbers: List[str]
    case_history: List[str]
    publication_status: Optional[str]
    year: Optional[str]
    is_complex: bool = False

class ComplexCitationIntegrator:
    """Integrates complex citation processing with existing CaseStrainer system."""
    
    def __init__(self):
        self._init_patterns()
    
    def _init_patterns(self):
        """Initialize regex patterns for different citation components."""
        
        # Enhanced primary citation patterns (volume reporter page)
        # Added more comprehensive Washington patterns and better parallel citation support
        self.primary_patterns = {
            # Washington jurisdiction patterns (primary)
            'wn_app': r'\b(\d+)\s+Wn\.\s*App\.\s+(\d+)\b',
            'wn2d': r'\b(\d+)\s+Wn\.2d\s+(\d+)\b',
            'wn3d': r'\b(\d+)\s+Wn\.3d\s+(\d+)\b',
            'wash': r'\b(\d+)\s+Wash\.\s+(\d+)\b',
            'wash_app': r'\b(\d+)\s+Wash\.\s*App\.\s+(\d+)\b',
            
            # Pacific Reporter patterns (parallel)
            'p3d': r'\b(\d+)\s+P\.3d\s+(\d+)\b',
            'p2d': r'\b(\d+)\s+P\.2d\s+(\d+)\b',
            
            # Federal patterns
            'us': r'\b(\d+)\s+U\.\s*S\.\s+(\d+)\b',
            'f3d': r'\b(\d+)\s+F\.3d\s+(\d+)\b',
            'f2d': r'\b(\d+)\s+F\.2d\s+(\d+)\b',
            'f_supp': r'\b(\d+)\s+F\.\s*Supp\.\s+(\d+)\b',
            'f_supp2d': r'\b(\d+)\s+F\.\s*Supp\.\s*2d\s+(\d+)\b',
        }
        
        # Enhanced case name pattern to better capture complex case names
        self.case_name_pattern = r'\b([A-Z][A-Za-z\s\.,&\'\"\(\)]+v\.\s+[A-Z][A-Za-z\s\.,&\'\"\(\)]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)'
        
        # Enhanced pinpoint page pattern to handle multiple pinpoint pages
        # Pattern 1: citation, page, citation, page (date)
        self.pinpoint_pattern = r',\s*(\d+)(?=\s*[,;]|\s*\(|\s*$)'
        
        # Enhanced parallel citation pattern to capture the full structure
        # Pattern 1: name, citation citation, citation (date)
        # Pattern 2: name, citation, page, citation, page, citation, page (date)
        self.parallel_citation_pattern = r'([A-Z][A-Za-z\s\.,&\'\"\(\)]+v\.\s+[A-Z][A-Za-z\s\.,&\'\"\(\)]+?)\s*,\s*([^,]+?)(?:\s*,\s*(\d+))?(?:\s*,\s*([^,]+?))?(?:\s*,\s*(\d+))?(?:\s*,\s*([^,]+?))?(?:\s*,\s*(\d+))?\s*\((\d{4})\)'
        
        # Docket number pattern
        self.docket_pattern = r'No\.\s*([0-9\-]+)'
        
        # Case history pattern (e.g., "(Doe I)", "(Doe II)")
        self.history_pattern = r'\(([A-Za-z\s]+(?:I|II|III|IV|V|VI|VII|VIII|IX|X))\)'
        
        # Publication status pattern
        self.status_pattern = r'\((unpublished|published|memorandum|per\s+curiam)\)'
        
        # Year pattern
        self.year_pattern = r'\((\d{4})\)'
    
    def is_complex_citation(self, text: str) -> bool:
        """Determine if a citation string is complex."""
        # Check for multiple citations
        citation_count = 0
        for pattern in self.primary_patterns.values():
            citation_count += len(re.findall(pattern, text))
        
        # Check for other complex features
        has_docket = bool(re.search(self.docket_pattern, text))
        has_history = bool(re.search(self.history_pattern, text))
        has_status = bool(re.search(self.status_pattern, text))
        has_pinpoint = bool(re.search(self.pinpoint_pattern, text))
        
        return (citation_count > 1 or has_docket or has_history or 
                has_status or has_pinpoint)
    
    def parse_complex_citation(self, text: str) -> ComplexCitationData:
        """Parse a complex citation into structured components."""
        try:
            # Extract case name
            case_name = self._extract_case_name(text)
            
            # Extract all citations
            all_citations = self._extract_all_citations(text)
            primary_citation = all_citations[0] if all_citations else None
            parallel_citations = all_citations[1:] if len(all_citations) > 1 else []
            
            # Extract other components
            pinpoint_pages = self._extract_pinpoint_pages(text)
            docket_numbers = self._extract_docket_numbers(text)
            case_history = self._extract_case_history(text)
            publication_status = self._extract_publication_status(text)
            year = self._extract_year(text)
            
            # Determine if complex
            is_complex = self.is_complex_citation(text)
            
            return ComplexCitationData(
                full_text=text,
                case_name=case_name,
                primary_citation=primary_citation,
                parallel_citations=parallel_citations,
                pinpoint_pages=pinpoint_pages,
                docket_numbers=docket_numbers,
                case_history=case_history,
                publication_status=publication_status,
                year=year,
                is_complex=is_complex
            )
            
        except Exception as e:
            logger.error(f"Error parsing complex citation '{text}': {e}")
            # Return basic structure on error
            return ComplexCitationData(
                full_text=text,
                case_name=None,
                primary_citation=None,
                parallel_citations=[],
                pinpoint_pages=[],
                docket_numbers=[],
                case_history=[],
                publication_status=None,
                year=None,
                is_complex=False
            )
    
    def _extract_case_name(self, text: str) -> Optional[str]:
        """Extract case name from citation block."""
        match = re.search(self.case_name_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_all_citations(self, text: str) -> List[str]:
        """Extract all citations from the block."""
        citations = []
        
        # First, try to match the specific parallel citation patterns
        parallel_match = self._extract_parallel_citation_pattern(text)
        if parallel_match:
            return parallel_match
        
        # Fallback to the original method
        # Find all citations in the text
        for pattern_name, pattern in self.primary_patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                volume, page = match.groups()
                # Use the actual matched text instead of pattern name to preserve formatting
                full_match = match.group(0)  # Get the full matched citation
                
                # Extract the reporter part by removing volume and page from the full match
                # The pattern is: volume + whitespace + reporter + whitespace + page
                # So we can extract reporter by removing volume and page
                volume_str = str(volume)
                page_str = str(page)
                
                # Remove volume from the beginning
                reporter_part = full_match[len(volume_str):].strip()
                # Remove page from the end
                if reporter_part.endswith(page_str):
                    reporter_part = reporter_part[:-len(page_str)].strip()
                
                # Clean up any extra spaces in the reporter
                reporter_part = re.sub(r'\s+', ' ', reporter_part).strip()
                
                if reporter_part:
                    citation = f"{volume} {reporter_part} {page}"
                else:
                    # Fallback to pattern name if reporter extraction fails
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
    
    def _extract_parallel_citation_pattern(self, text: str) -> List[str]:
        """
        Extract citations using the specific parallel citation patterns:
        1. name, citation citation, citation (date)
        2. name, citation, page, citation, page, citation, page (date)
        """
        citations = []
        
        # Pattern 1: name, citation citation, citation (date)
        # Example: "John Doe A v. Washington State Patrol, 185 Wn.2d 363, 374 P.3d 63 (2016)"
        pattern1 = r'([A-Z][A-Za-z\s\.,&\'\"\(\)]+v\.\s+[A-Z][A-Za-z\s\.,&\'\"\(\)]+?)\s*,\s*([^,]+?)\s*,\s*([^,]+?)\s*\((\d{4})\)'
        match1 = re.search(pattern1, text)
        if match1:
            case_name, citation1, citation2, year = match1.groups()
            # Clean up citations (remove extra whitespace)
            citation1 = re.sub(r'\s+', ' ', citation1.strip())
            citation2 = re.sub(r'\s+', ' ', citation2.strip())
            
            # Filter out pinpoint pages (numbers that don't look like citations)
            if self._is_valid_citation(citation1):
                citations.append(citation1)
            if self._is_valid_citation(citation2):
                citations.append(citation2)
            return citations
        
        # Pattern 2: name, citation, page, citation, page (date) - with pinpoint pages
        # Example: "John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017)"
        pattern2 = r'([A-Z][A-Za-z\s\.,&\'\"\(\)]+v\.\s+[A-Z][A-Za-z\s\.,&\'\"\(\)]+?)\s*,\s*([^,]+?)\s*,\s*(\d+)\s*,\s*([^,]+?)\s*\((\d{4})\)'
        match2 = re.search(pattern2, text)
        if match2:
            case_name, citation1, page1, citation2, year = match2.groups()
            # Clean up citations and add pinpoint pages
            citation1 = re.sub(r'\s+', ' ', citation1.strip())
            citation2 = re.sub(r'\s+', ' ', citation2.strip())
            
            # Filter out pinpoint pages
            if self._is_valid_citation(citation1):
                citations.append(citation1)
            if self._is_valid_citation(citation2):
                citations.append(citation2)
            return citations
        
        # Pattern 3: name, citation, page, citation, page (date) - 2 citations with pinpoint pages
        pattern3 = r'([A-Z][A-Za-z\s\.,&\'\"\(\)]+v\.\s+[A-Z][A-Za-z\s\.,&\'\"\(\)]+?)\s*,\s*([^,]+?)\s*,\s*(\d+)\s*,\s*([^,]+?)\s*,\s*(\d+)\s*\((\d{4})\)'
        match3 = re.search(pattern3, text)
        if match3:
            case_name, citation1, page1, citation2, page2, year = match3.groups()
            # Clean up citations
            citation1 = re.sub(r'\s+', ' ', citation1.strip())
            citation2 = re.sub(r'\s+', ' ', citation2.strip())
            
            # Filter out pinpoint pages
            if self._is_valid_citation(citation1):
                citations.append(citation1)
            if self._is_valid_citation(citation2):
                citations.append(citation2)
            return citations
        
        # Pattern 4: name, citation, citation, citation (date) - 3 citations
        pattern4 = r'([A-Z][A-Za-z\s\.,&\'\"\(\)]+v\.\s+[A-Z][A-Za-z\s\.,&\'\"\(\)]+?)\s*,\s*([^,]+?)\s*,\s*([^,]+?)\s*,\s*([^,]+?)\s*\((\d{4})\)'
        match4 = re.search(pattern4, text)
        if match4:
            case_name, citation1, citation2, citation3, year = match4.groups()
            # Clean up citations
            citation1 = re.sub(r'\s+', ' ', citation1.strip())
            citation2 = re.sub(r'\s+', ' ', citation2.strip())
            citation3 = re.sub(r'\s+', ' ', citation3.strip())
            
            # Filter out pinpoint pages
            if self._is_valid_citation(citation1):
                citations.append(citation1)
            if self._is_valid_citation(citation2):
                citations.append(citation2)
            if self._is_valid_citation(citation3):
                citations.append(citation3)
            return citations
        
        return []
    
    def _is_valid_citation(self, text: str) -> bool:
        """
        Check if a text string looks like a valid citation (not a pinpoint page).
        Valid citations should contain a reporter abbreviation.
        """
        if not text:
            return False
        
        # Check if it contains reporter abbreviations
        reporter_patterns = [
            r'\bWn\.\s*App\.\b',  # Wn. App.
            r'\bWn\.2d\b',        # Wn.2d
            r'\bWn\.3d\b',        # Wn.3d
            r'\bWash\.\b',        # Wash.
            r'\bP\.3d\b',         # P.3d
            r'\bP\.2d\b',         # P.2d
            r'\bU\.\s*S\.\b',     # U.S.
            r'\bF\.3d\b',         # F.3d
            r'\bF\.2d\b',         # F.2d
            r'\bF\.\s*Supp\.\b',  # F. Supp.
        ]
        
        for pattern in reporter_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # If it's just a number or number range, it's likely a pinpoint page
        if re.match(r'^\d+(-\d+)?$', text.strip()):
            return False
        
        return False
    
    def enhance_verification_result(self, original_result: Dict, complex_data: ComplexCitationData) -> Dict:
        """Enhance the original verification result with complex citation data."""
        enhanced_result = original_result.copy()
        
        # Add complex citation metadata
        enhanced_result['is_complex_citation'] = complex_data.is_complex
        enhanced_result['complex_metadata'] = {
            'full_text': complex_data.full_text,
            'case_name': complex_data.case_name,
            'primary_citation': complex_data.primary_citation,
            'parallel_citations': complex_data.parallel_citations,
            'pinpoint_pages': complex_data.pinpoint_pages,
            'docket_numbers': complex_data.docket_numbers,
            'case_history': complex_data.case_history,
            'publication_status': complex_data.publication_status,
            'year': complex_data.year
        }
        
        # Enhance case name if available
        if complex_data.case_name and not enhanced_result.get('case_name'):
            enhanced_result['case_name'] = complex_data.case_name
            enhanced_result['extracted_case_name'] = complex_data.case_name
        
        # Enhance year if available
        if complex_data.year and not enhanced_result.get('extracted_date'):
            enhanced_result['extracted_date'] = complex_data.year
            enhanced_result['canonical_date'] = complex_data.year
        
        # Add docket number if available
        if complex_data.docket_numbers and not enhanced_result.get('docket_number'):
            enhanced_result['docket_number'] = complex_data.docket_numbers[0]
        
        # Add publication status
        if complex_data.publication_status:
            enhanced_result['publication_status'] = complex_data.publication_status
        
        return enhanced_result

    def extract_citations_with_pinpoints(self, text: str) -> list:
        """
        Extract citations and pair each with its following pinpoint page/range (if present).
        Returns a list of (citation, pinpoint) tuples.
        """
        # Find all citations and their positions
        citation_matches = []
        for pattern_name, pattern in self.primary_patterns.items():
            for match in re.finditer(pattern, text):
                citation = match.group(0)
                end = match.end()
                citation_matches.append((citation, end))
        # Sort by position in text
        citation_matches.sort(key=lambda x: x[1])
        
        # Reporter abbreviations for lookahead
        reporter_abbrevs = [
            'Wn. App.', 'Wn.2d', 'Wn.3d', 'Wash.', 'P.3d', 'P.2d', 'U.S.', 'F.3d', 'F.2d', 'F. Supp.'
        ]
        reporter_regex = re.compile(r'^(%s)' % '|'.join([re.escape(r) for r in reporter_abbrevs]))
        
        results = []
        for i, (citation, end_pos) in enumerate(citation_matches):
            # Look ahead for a pinpoint: skip whitespace and commas
            pinpoint = None
            j = end_pos
            while j < len(text) and text[j] in [',', ' ', '\t', '\n']:
                j += 1
            # Try to match a pinpoint (number or number range)
            pinpoint_match = re.match(r'(\d+(?:-\d+)?)', text[j:])
            if pinpoint_match:
                # Look ahead after the pinpoint for a reporter abbreviation
                next_token_end = j + pinpoint_match.end()
                k = next_token_end
                # Skip whitespace and commas
                while k < len(text) and text[k] in [',', ' ', '\t', '\n']:
                    k += 1
                # Check for reporter abbreviation
                if not reporter_regex.match(text[k:]):
                    pinpoint = pinpoint_match.group(1)
            results.append((citation, pinpoint))
        return results

# Global instance for use throughout the application
complex_citation_integrator = ComplexCitationIntegrator()

def calculate_citation_statistics(results: list) -> dict:
    """
    Calculate comprehensive citation statistics for display.
    
    Args:
        results: List of citation verification results
        
    Returns:
        Dictionary with citation statistics
    """
    total_citations = len(results)
    parallel_citations = sum(1 for r in results if r.get('is_parallel_citation'))
    verified_citations = sum(1 for r in results if r.get('verified') in ['true', 'true_by_parallel'])
    unverified_citations = total_citations - verified_citations
    
    # Count unique cases (group by case name or primary citation)
    unique_cases = set()
    for result in results:
        case_name = result.get('case_name') or result.get('canonical_case_name') or result.get('citation', '')
        if case_name:
            unique_cases.add(case_name)
    
    # Count parallel citation sets (groups of citations that belong together)
    parallel_sets = 0
    processed_primary = set()
    for result in results:
        if result.get('is_parallel_citation'):
            primary = result.get('primary_citation')
            if primary and primary not in processed_primary:
                parallel_sets += 1
                processed_primary.add(primary)
    
    return {
        'total_citations': total_citations,
        'parallel_citations': parallel_sets,  # Number of parallel citation sets
        'verified_citations': verified_citations,
        'unverified_citations': unverified_citations,
        'unique_cases': len(unique_cases),
        'individual_parallel_citations': parallel_citations  # Individual parallel citations
    }

def format_complex_citation_for_frontend(result: Dict) -> Dict:
    """Format complex citation result for frontend display."""
    formatted = result.copy()
    
    # Ensure canonical_name is always present if canonical_case_name is set
    if 'canonical_case_name' in formatted and 'canonical_name' not in formatted:
        formatted['canonical_name'] = formatted['canonical_case_name']
    
    # Add complex citation display information
    if result.get('is_complex_citation'):
        complex_metadata = result.get('complex_metadata', {})
        
        # Create display text that prominently shows parallel citations
        display_parts = []
        
        # Add case name first if available
        case_name = (complex_metadata.get('case_name') or 
                    result.get('case_name') or 
                    result.get('canonical_case_name'))
        if case_name:
            display_parts.append(f"<strong>{case_name}</strong>")
        
        # Add primary citation
        primary_citation = complex_metadata.get('primary_citation') or result.get('citation', '')
        if primary_citation:
            display_parts.append(primary_citation)
        
        # Add pinpoint pages
        if complex_metadata.get('pinpoint_pages'):
            display_parts.extend(complex_metadata['pinpoint_pages'])
        
        # Add parallel citations prominently (not in dropdown)
        if complex_metadata.get('parallel_citations'):
            parallel_text = ", ".join(complex_metadata['parallel_citations'])
            display_parts.append(f"<em>Parallel: {parallel_text}</em>")
        
        # Add year
        year = complex_metadata.get('year') or result.get('year')
        if year:
            display_parts.append(f"({year})")
        
        # Add case history
        if complex_metadata.get('case_history'):
            display_parts.extend([f"({history})" for history in complex_metadata['case_history']])
        
        # Add publication status
        if complex_metadata.get('publication_status'):
            display_parts.append(f"({complex_metadata['publication_status']})")
        
        # Add docket numbers
        if complex_metadata.get('docket_numbers'):
            docket_text = ", ".join(complex_metadata['docket_numbers'])
            display_parts.append(f"<em>Docket: {docket_text}</em>")
        
        formatted['display_text'] = ' '.join(display_parts)
        formatted['complex_features'] = {
            'has_parallel_citations': bool(complex_metadata.get('parallel_citations')),
            'has_case_history': bool(complex_metadata.get('case_history')),
            'has_docket_numbers': bool(complex_metadata.get('docket_numbers')),
            'has_publication_status': bool(complex_metadata.get('publication_status')),
            'has_pinpoint_pages': bool(complex_metadata.get('pinpoint_pages'))
        }
        
        # Add parallel citation information for display
        if result.get('is_parallel_citation'):
            formatted['parallel_info'] = {
                'is_parallel': True,
                'primary_citation': result.get('primary_citation'),
                'verification_status': result.get('verified')
            }
    
    return formatted

def process_text_with_complex_citations(text: str, verifier, context: str = None) -> dict:
    """
    Process text with enhanced complex citation support and return comprehensive results.
    Args:
        text: The text to process
        verifier: The EnhancedMultiSourceVerifier instance
        context: Optional context string to attach to all results
    Returns:
        Dictionary with results and statistics
    """
    # Get the citation results
    citation_results = process_text_with_complex_citations_original(text, verifier, context)
    
    # Calculate comprehensive statistics
    statistics = calculate_citation_statistics(citation_results)
    
    # Format results for frontend
    formatted_results = [format_complex_citation_for_frontend(result) for result in citation_results]
    
    return {
        'results': formatted_results,
        'statistics': statistics,
        'summary': {
            'total_citations': statistics['total_citations'],
            'parallel_citations': statistics['parallel_citations'],
            'verified_citations': statistics['verified_citations'],
            'unverified_citations': statistics['unverified_citations'],
            'unique_cases': statistics['unique_cases']
        }
    }

# Rename the original function and create a new wrapper
def process_text_with_complex_citations_original(text: str, verifier, context: str = None) -> list:
    results = []
    
    # First, extract all citations from the text
    from src.citation_extractor import CitationExtractor
    extractor = CitationExtractor()
    extracted_citations = extractor.extract_citations(text)
    
    if not extracted_citations:
        # If no citations found, try processing the text as a single complex citation
        if complex_citation_integrator.is_complex_citation(text):
            # Parse as complex citation
            complex_data = complex_citation_integrator.parse_complex_citation(text)
            # Use the full text as context if not provided
            citation_context = context if context is not None else text
            # Verify the primary citation
            if complex_data.primary_citation:
                try:
                    result = verifier.verify_citation_unified_workflow(
                        complex_data.primary_citation,
                        extracted_case_name=complex_data.case_name
                    )
                    # Enhance with complex citation data
                    enhanced_result = complex_citation_integrator.enhance_verification_result(result, complex_data)
                    # Attach context
                    enhanced_result['context'] = citation_context
                    results.append(enhanced_result)
                    # Store canonical metadata for copying
                    canonical_metadata = {
                        'url': enhanced_result.get('url', ''),
                        'court': enhanced_result.get('court', ''),
                        'docket_number': enhanced_result.get('docket_number', ''),
                        'canonical_case_name': enhanced_result.get('canonical_name', ''),
                        'canonical_date': enhanced_result.get('canonical_date', ''),
                        'case_name': enhanced_result.get('case_name', ''),
                        'year': enhanced_result.get('year', ''),
                    }
                    # For each parallel citation, create a result with copied metadata
                    for parallel_citation in complex_data.parallel_citations:
                        try:
                            parallel_result = verifier.verify_citation_unified_workflow(
                                parallel_citation,
                                extracted_case_name=complex_data.case_name
                            )
                            # Mark as parallel citation
                            parallel_result['is_parallel_citation'] = True
                            parallel_result['primary_citation'] = complex_data.primary_citation
                            parallel_result['is_complex_citation'] = True
                            # Enhance with complex citation data
                            enhanced_parallel = complex_citation_integrator.enhance_verification_result(parallel_result, complex_data)
                            # Attach context and copy metadata from primary
                            enhanced_parallel['context'] = citation_context
                            enhanced_parallel['case_name'] = canonical_metadata['case_name']
                            enhanced_parallel['canonical_case_name'] = canonical_metadata['canonical_case_name']
                            enhanced_parallel['canonical_name'] = canonical_metadata['canonical_case_name']
                            # Set verified status based on primary citation verification
                            if enhanced_result.get('verified') == 'true':
                                # If primary is verified, parallel citations inherit verification unless directly verified
                                if parallel_result.get('verified') == 'true':
                                    enhanced_parallel['verified'] = 'true'  # Directly verified
                                else:
                                    enhanced_parallel['verified'] = 'true_by_parallel'  # Inherited from primary
                            else:
                                # If primary is not verified, parallel citations are not verified
                                enhanced_parallel['verified'] = 'false'
                            results.append(enhanced_parallel)
                        except Exception as e:
                            # Even if not verified, include with metadata copied from primary
                            results.append({
                                'citation': parallel_citation,
                                'case_name': canonical_metadata['case_name'],
                                'canonical_case_name': canonical_metadata['canonical_case_name'],
                                'canonical_name': canonical_metadata['canonical_case_name'],
                                'canonical_date': canonical_metadata['canonical_date'],
                                'year': canonical_metadata['year'],
                                'url': canonical_metadata['url'],
                                'court': canonical_metadata['court'],
                                'docket_number': canonical_metadata['docket_number'],
                                'context': citation_context,
                                'is_parallel_citation': True,
                                'primary_citation': complex_data.primary_citation,
                                'is_complex_citation': True,
                                'verified': 'true_by_parallel',
                                'error': str(e),
                                'complex_metadata': enhanced_result.get('complex_metadata', {})
                            })
                    # After processing all citations in the group, enforce only primary is 'true'
                    if enhanced_result.get('verified') == 'true':
                        # Gather canonical metadata from primary
                        canonical_fields = [
                            'case_name', 'canonical_case_name', 'canonical_date', 'year', 'url', 'court', 'docket_number', 'source', 'confidence', 'hinted_case_name', 'extracted_case_name', 'extracted_date', 'canonical_name'
                        ]
                        primary_metadata = {k: enhanced_result.get(k) for k in canonical_fields}
                        for result in results:
                            if result.get('is_parallel_citation') and result.get('primary_citation') == complex_data.primary_citation:
                                # If the parallel was marked as 'true', force to 'true_by_parallel'
                                if result.get('verified') == 'true':
                                    result['verified'] = 'true_by_parallel'
                                # Inherit all canonical metadata fields from primary
                                for k, v in primary_metadata.items():
                                    result[k] = v
                except Exception as e:
                    # Add fallback result for primary citation
                    results.append({
                        'citation': complex_data.primary_citation or text,
                        'case_name': complex_data.case_name,
                        'canonical_date': complex_data.year,
                        'year': complex_data.year,
                        'context': citation_context,
                        'is_complex_citation': True,
                        'verified': 'false',
                        'error': str(e),
                        'complex_metadata': {
                            'full_text': complex_data.full_text,
                            'case_name': complex_data.case_name,
                            'primary_citation': complex_data.primary_citation,
                            'parallel_citations': complex_data.parallel_citations,
                            'pinpoint_pages': complex_data.pinpoint_pages,
                            'docket_numbers': complex_data.docket_numbers,
                            'case_history': complex_data.case_history,
                            'publication_status': complex_data.publication_status,
                            'year': complex_data.year
                        }
                    })
                    # Add fallback for parallel citations
                    for parallel_citation in complex_data.parallel_citations:
                        results.append({
                            'citation': parallel_citation,
                            'case_name': complex_data.case_name,
                            'canonical_date': complex_data.year,
                            'year': complex_data.year,
                            'context': citation_context,
                            'is_parallel_citation': True,
                            'primary_citation': complex_data.primary_citation,
                            'is_complex_citation': True,
                            'verified': 'true_by_parallel',
                            'error': str(e),
                            'complex_metadata': {
                                'full_text': complex_data.full_text,
                                'case_name': complex_data.case_name,
                                'primary_citation': complex_data.primary_citation,
                                'parallel_citations': complex_data.parallel_citations,
                                'pinpoint_pages': complex_data.pinpoint_pages,
                                'docket_numbers': complex_data.docket_numbers,
                                'case_history': complex_data.case_history,
                                'publication_status': complex_data.publication_status,
                                'year': complex_data.year
                            }
                        })
        else:
            # Use existing processing for simple citations
            try:
                result = verifier.verify_citation_unified_workflow(
                    text,
                    extracted_case_name=None
                )
                result['context'] = context if context is not None else text
                # Set verified as 'true' or 'false'
                if result.get('verified') is True:
                    result['verified'] = 'true'
                else:
                    result['verified'] = 'false'
                results.append(result)
            except Exception as e:
                results.append({
                    'citation': text,
                    'context': context if context is not None else text,
                    'verified': 'false',
                    'error': str(e),
                    'is_complex_citation': False
                })
    else:
        # Process extracted citations as groups
        citation_groups = []
        processed_citations = set()
        
        # Group citations that appear together in the text
        for citation in extracted_citations:
            citation_text = citation.get('citation', '')
            if citation_text in processed_citations:
                continue
                
            # Find all citations that appear near this one (within 200 characters)
            citation_index = text.find(citation_text)
            if citation_index != -1:
                # Look for other citations in the vicinity
                start_pos = max(0, citation_index - 200)
                end_pos = min(len(text), citation_index + len(citation_text) + 200)
                vicinity_text = text[start_pos:end_pos]
                
                # Find all citations in this vicinity
                group_citations = []
                for other_citation in extracted_citations:
                    other_text = other_citation.get('citation', '')
                    if other_text in vicinity_text and other_text not in processed_citations:
                        group_citations.append(other_citation)
                        processed_citations.add(other_text)
                
                if len(group_citations) > 1:
                    # This is a complex citation group
                    citation_groups.append(group_citations)
                else:
                    # Single citation
                    citation_groups.append([citation])
                    processed_citations.add(citation_text)
        
        # Process each citation group
        for group in citation_groups:
            if len(group) == 1:
                # Single citation - process normally
                citation = group[0]
                citation_text = citation.get('citation', '')
                try:
                    result = verifier.verify_citation_unified_workflow(
                        citation_text,
                        extracted_case_name=citation.get('extracted_case_name')
                    )
                    result['context'] = context if context is not None else citation.get('context', '')
                    # Set verified as 'true' or 'false'
                    if result.get('verified') is True:
                        result['verified'] = 'true'
                    else:
                        result['verified'] = 'false'
                    results.append(result)
                except Exception as e:
                    results.append({
                        'citation': citation_text,
                        'context': context if context is not None else citation.get('context', ''),
                        'verified': 'false',
                        'error': str(e),
                        'is_complex_citation': False
                    })
            else:
                # Complex citation group - process as a group
                # Find the primary citation (usually the first one)
                primary_citation = group[0]
                primary_text = primary_citation.get('citation', '')
                
                try:
                    # Verify the primary citation
                    primary_result = verifier.verify_citation_unified_workflow(
                        primary_text,
                        extracted_case_name=primary_citation.get('extracted_case_name')
                    )
                    
                    # Store canonical metadata from primary
                    canonical_metadata = {
                        'url': primary_result.get('url', ''),
                        'court': primary_result.get('court', ''),
                        'docket_number': primary_result.get('docket_number', ''),
                        'canonical_case_name': primary_result.get('canonical_name', ''),
                        'canonical_date': primary_result.get('canonical_date', ''),
                        'case_name': primary_result.get('case_name', ''),
                        'year': primary_result.get('year', ''),
                        'source': primary_result.get('source', ''),
                        'confidence': primary_result.get('confidence', ''),
                        'hinted_case_name': primary_result.get('hinted_case_name', ''),
                        'extracted_case_name': primary_result.get('extracted_case_name', ''),
                        'extracted_date': primary_result.get('extracted_date', ''),
                        'canonical_name': primary_result.get('canonical_name', '')
                    }
                    
                    # Add primary citation
                    primary_result['context'] = context if context is not None else primary_citation.get('context', '')
                    primary_result['is_complex_citation'] = True
                    primary_result['primary_citation'] = primary_text
                    if primary_result.get('verified') is True:
                        primary_result['verified'] = 'true'
                    else:
                        primary_result['verified'] = 'false'
                    results.append(primary_result)
                    
                    # Add parallel citations with inherited metadata
                    for parallel_citation in group[1:]:
                        parallel_text = parallel_citation.get('citation', '')
                        try:
                            # Try to verify the parallel citation directly
                            parallel_result = verifier.verify_citation_unified_workflow(
                                parallel_text,
                                extracted_case_name=parallel_citation.get('extracted_case_name')
                            )
                            
                            # Mark as parallel citation
                            parallel_result['is_parallel_citation'] = True
                            parallel_result['primary_citation'] = primary_text
                            parallel_result['is_complex_citation'] = True
                            parallel_result['context'] = context if context is not None else parallel_citation.get('context', '')
                            
                            # Inherit metadata from primary
                            for key, value in canonical_metadata.items():
                                if value:  # Only copy non-empty values
                                    parallel_result[key] = value
                            
                            # Set verification status
                            if primary_result.get('verified') == 'true':
                                if parallel_result.get('verified') is True:
                                    parallel_result['verified'] = 'true'  # Directly verified
                                else:
                                    parallel_result['verified'] = 'true_by_parallel'  # Inherited from primary
                            else:
                                parallel_result['verified'] = 'false'
                            
                            results.append(parallel_result)
                            
                        except Exception as e:
                            # Add parallel citation with inherited metadata even if verification fails
                            parallel_result = {
                                'citation': parallel_text,
                                'context': context if context is not None else parallel_citation.get('context', ''),
                                'is_parallel_citation': True,
                                'primary_citation': primary_text,
                                'is_complex_citation': True,
                                'verified': 'true_by_parallel' if primary_result.get('verified') == 'true' else 'false',
                                'error': str(e)
                            }
                            
                            # Inherit metadata from primary
                            for key, value in canonical_metadata.items():
                                if value:  # Only copy non-empty values
                                    parallel_result[key] = value
                            
                            results.append(parallel_result)
                    
                except Exception as e:
                    # Add fallback results for the entire group
                    for citation in group:
                        citation_text = citation.get('citation', '')
                        results.append({
                            'citation': citation_text,
                            'context': context if context is not None else citation.get('context', ''),
                            'is_complex_citation': True,
                            'verified': 'false',
                            'error': str(e)
                        })
    
    return results 