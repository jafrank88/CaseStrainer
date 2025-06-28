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
        # Simplified pattern to avoid regex escape issues
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
            from src.citation_extractor import CitationExtractor
            extractor = CitationExtractor(use_eyecite=False, use_regex=True, extract_case_names=True)
            extracted_citations = extractor.extract_citations(text)
            
            # Debug: Log what citations were found
            logger.info(f"[parse_complex_citation] Found {len(extracted_citations)} citations: {[c.get('citation', 'N/A') for c in extracted_citations]}")
            
            # Handle the case where we have multiple citations
            if len(extracted_citations) >= 2:
                primary_citation = extracted_citations[0]['citation']
                parallel_citations = [citation['citation'] for citation in extracted_citations[1:]]
                logger.info(f"[parse_complex_citation] Primary: {primary_citation}, Parallels: {parallel_citations}")
            elif len(extracted_citations) == 1:
                primary_citation = extracted_citations[0]['citation']
                parallel_citations = []
                logger.info(f"[parse_complex_citation] Primary: {primary_citation}, No parallels")
            else:
                primary_citation = None
                parallel_citations = []
                logger.info(f"[parse_complex_citation] No citations found")
            
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
    
    def _extract_pinpoint_pages(self, text: str) -> List[str]:
        """Extract pinpoint pages from the citation block."""
        pages = re.findall(self.pinpoint_pattern, text)
        return pages
    
    def _extract_docket_numbers(self, text: str) -> List[str]:
        """Extract docket numbers from the citation block."""
        return re.findall(self.docket_pattern, text)
    
    def _extract_case_history(self, text: str) -> List[str]:
        """Extract case history from the citation block."""
        return re.findall(self.history_pattern, text)
    
    def _extract_publication_status(self, text: str) -> Optional[str]:
        """Extract publication status from the citation block."""
        match = re.search(self.status_pattern, text)
        if match:
            return match.group(1)
        return None
    
    def _extract_year(self, text: str) -> Optional[str]:
        """Extract year from the citation block."""
        match = re.search(self.year_pattern, text)
        if match:
            return match.group(1)
        return None
    
    def enhance_verification_result(self, result: Dict, complex_data: ComplexCitationData) -> Dict:
        """Enhance a verification result with complex citation data."""
        enhanced = result.copy()
        
        # Add complex citation metadata
        enhanced['complex_metadata'] = {
            'full_text': complex_data.full_text,
            'case_name': complex_data.case_name,
            'primary_citation': complex_data.primary_citation,
            'parallel_citations': complex_data.parallel_citations,
            'pinpoint_pages': complex_data.pinpoint_pages,
            'docket_numbers': complex_data.docket_numbers,
            'case_history': complex_data.case_history,
            'publication_status': complex_data.publication_status,
            'year': complex_data.year,
            'is_complex': complex_data.is_complex
        }
        
        # Add case name if not already present
        if complex_data.case_name and not enhanced.get('case_name'):
            enhanced['case_name'] = complex_data.case_name
            
        # Add year if not already present
        if complex_data.year and not enhanced.get('canonical_date'):
            enhanced['canonical_date'] = complex_data.year
            
        # Add parallel citations if this is the primary citation
        if complex_data.parallel_citations and enhanced.get('citation') == complex_data.primary_citation:
            enhanced['parallel_citations'] = complex_data.parallel_citations
            
        return enhanced
    
    def process_text_with_complex_citations_original(self, text: str, context: Optional[str] = None) -> List[Dict]:
        """Process a text with complex citations and return verification results."""
        # Initialize verifier
        from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
        verifier = EnhancedMultiSourceVerifier()
        
        results = []
        
        # First, extract all citations from the text
        from src.citation_extractor import CitationExtractor
        extractor = CitationExtractor(use_eyecite=False, use_regex=True, extract_case_names=True)
        extracted_citations = extractor.extract_citations(text)
        
        # Check if this is a complex citation (multiple citations or complex features)
        is_complex = self.is_complex_citation(text)
        
        # If this is a complex citation with multiple citations, process it as such
        if is_complex and len(extracted_citations) > 1:
            logger.debug(f"[process_text_with_complex_citations_original] Processing as complex citation with {len(extracted_citations)} citations")
            
            # Parse as complex citation
            complex_data = self.parse_complex_citation(text)
            # Use the full text as context if not provided
            citation_context = context if context is not None else text
            
            # Verify the primary citation
            if complex_data.primary_citation:
                try:
                    primary_result = verifier.verify_citation_unified_workflow(
                        complex_data.primary_citation,
                        extracted_case_name=complex_data.case_name
                    )
                    # Enhance with complex citation data
                    enhanced_result = self.enhance_verification_result(primary_result, complex_data)
                    # Attach context
                    enhanced_result['context'] = citation_context
                    enhanced_result['is_complex_citation'] = True
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
                            # Ensure the citation text is preserved
                            if not parallel_result.get('citation'):
                                parallel_result['citation'] = parallel_citation
                            # Mark as parallel citation
                            parallel_result['is_parallel_citation'] = True
                            parallel_result['primary_citation'] = complex_data.primary_citation
                            parallel_result['is_complex_citation'] = True
                            # Enhance with complex citation data
                            enhanced_parallel = self.enhance_verification_result(parallel_result, complex_data)
                            # Ensure citation text is still preserved after enhancement
                            if not enhanced_parallel.get('citation'):
                                enhanced_parallel['citation'] = parallel_citation
                            # Attach context and copy metadata from primary
                            enhanced_parallel['context'] = citation_context
                            enhanced_parallel['case_name'] = canonical_metadata['case_name']
                            enhanced_parallel['canonical_case_name'] = canonical_metadata['canonical_case_name']
                            enhanced_parallel['canonical_name'] = canonical_metadata['canonical_case_name']
                            # Set verification status
                            verified_status = enhanced_parallel.get('verified')
                            if enhanced_result.get('verified') == 'true':
                                if verified_status == True or verified_status == 'true':
                                    enhanced_parallel['verified'] = 'true'  # Directly verified
                                else:
                                    enhanced_parallel['verified'] = 'true_by_parallel'  # Inherited from primary
                            else:
                                if verified_status == True or verified_status == 'true':
                                    enhanced_parallel['verified'] = 'true'
                                else:
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
                                'verified': 'true_by_parallel' if enhanced_result.get('verified') == 'true' else 'false',
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
                                    if v:  # Only copy non-empty values
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
            
            return results
        
        if not extracted_citations:
            # If no citations found, try processing the text as a single complex citation
            if self.is_complex_citation(text):
                # Parse as complex citation
                complex_data = self.parse_complex_citation(text)
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
                        enhanced_result = self.enhance_verification_result(result, complex_data)
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
                                # Ensure the citation text is preserved
                                if not parallel_result.get('citation'):
                                    parallel_result['citation'] = parallel_citation
                                # Mark as parallel citation
                                parallel_result['is_parallel_citation'] = True
                                parallel_result['primary_citation'] = complex_data.primary_citation
                                parallel_result['is_complex_citation'] = True
                                # Enhance with complex citation data
                                enhanced_parallel = self.enhance_verification_result(parallel_result, complex_data)
                                # Ensure citation text is still preserved after enhancement
                                if not enhanced_parallel.get('citation'):
                                    enhanced_parallel['citation'] = parallel_citation
                                # Attach context and copy metadata from primary
                                enhanced_parallel['context'] = citation_context
                                enhanced_parallel['case_name'] = canonical_metadata['case_name']
                                enhanced_parallel['canonical_case_name'] = canonical_metadata['canonical_case_name']
                                enhanced_parallel['canonical_name'] = canonical_metadata['canonical_case_name']
                                # Set verification status
                                verified_status = enhanced_parallel.get('verified')
                                if enhanced_result.get('verified') == 'true':
                                    if verified_status == True or verified_status == 'true':
                                        enhanced_parallel['verified'] = 'true'  # Directly verified
                                    else:
                                        enhanced_parallel['verified'] = 'true_by_parallel'  # Inherited from primary
                                else:
                                    if verified_status == True or verified_status == 'true':
                                        enhanced_parallel['verified'] = 'true'
                                    else:
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
                    logger.debug(f"[process_text_with_complex_citations_original] Processing simple citation: {text}")
                    result = verifier.verify_citation_unified_workflow(
                        text,
                        extracted_case_name=None
                    )
                    logger.debug(f"[process_text_with_complex_citations_original] Raw verification result: {result}")
                    result['context'] = context if context is not None else text
                    
                    # Set verified as 'true' or 'false' - handle both string and boolean values
                    verified_status = result.get('verified')
                    logger.debug(f"[process_text_with_complex_citations_original] Original verified status: {verified_status} (type: {type(verified_status)})")
                    
                    if verified_status == True or verified_status == 'true':
                        result['verified'] = 'true'
                        logger.debug(f"[process_text_with_complex_citations_original] Set verified to 'true'")
                    else:
                        result['verified'] = 'false'
                        logger.debug(f"[process_text_with_complex_citations_original] Set verified to 'false'")
                    
                    logger.debug(f"[process_text_with_complex_citations_original] Final result: citation={result.get('citation')}, verified={result.get('verified')}")
                    results.append(result)
                except Exception as e:
                    logger.error(f"[process_text_with_complex_citations_original] Error processing simple citation {text}: {e}")
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
                        # Set verified as 'true' or 'false' - handle both string and boolean values
                        verified_status = result.get('verified')
                        if verified_status == True or verified_status == 'true':
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
                        # Set verification status
                        verified_status = primary_result.get('verified')
                        if verified_status == True or verified_status == 'true':
                            primary_result['verified'] = 'true'
                        else:
                            primary_result['verified'] = 'false'
                        results.append(primary_result)
                        
                        # For parallel citations in a group
                        for parallel_citation in group[1:]:
                            parallel_text = parallel_citation.get('citation', '')
                            try:
                                parallel_result = verifier.verify_citation_unified_workflow(
                                    parallel_text,
                                    extracted_case_name=parallel_citation.get('extracted_case_name')
                                )
                                parallel_result['is_parallel_citation'] = True
                                parallel_result['primary_citation'] = primary_text
                                parallel_result['is_complex_citation'] = True
                                parallel_result['context'] = context if context is not None else parallel_citation.get('context', '')
                                for key, value in canonical_metadata.items():
                                    if value:
                                        parallel_result[key] = value
                                # Set verification status
                                verified_status = parallel_result.get('verified')
                                if primary_result.get('verified') == 'true':
                                    if verified_status == True or verified_status == 'true':
                                        parallel_result['verified'] = 'true'  # Directly verified
                                    else:
                                        parallel_result['verified'] = 'true_by_parallel'  # Inherited from primary
                                else:
                                    if verified_status == True or verified_status == 'true':
                                        parallel_result['verified'] = 'true'
                                    else:
                                        parallel_result['verified'] = 'false'
                                results.append(parallel_result)
                            except Exception as e:
                                parallel_result = {
                                    'citation': parallel_text,
                                    'context': context if context is not None else parallel_citation.get('context', ''),
                                    'is_parallel_citation': True,
                                    'primary_citation': primary_text,
                                    'is_complex_citation': True,
                                    'verified': 'true_by_parallel' if primary_result.get('verified') == 'true' else 'false',
                                    'error': str(e)
                                }
                                for key, value in canonical_metadata.items():
                                    if value:
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

def format_complex_citation_for_frontend(complex_result: Dict) -> Dict:
    """
    Format complex citation results for frontend display.
    
    Args:
        complex_result: The complex citation result from processing
        
    Returns:
        Formatted result suitable for frontend display
    """
    formatted = {}
    
    # Copy essential fields
    essential_fields = [
        'citation', 'case_name', 'canonical_name', 'canonical_date', 
        'url', 'court', 'docket_number', 'source', 'confidence',
        'verified', 'error', 'context', 'method', 'pattern'
    ]
    
    for field in essential_fields:
        if field in complex_result:
            formatted[field] = complex_result[field]
    
    # Handle complex citation specific fields
    if complex_result.get('is_complex_citation'):
        formatted['is_complex_citation'] = True
        formatted['complex_metadata'] = {
            'full_text': complex_result.get('full_text', ''),
            'primary_citation': complex_result.get('primary_citation', ''),
            'parallel_citations': complex_result.get('parallel_citations', []),
            'pinpoint_pages': complex_result.get('pinpoint_pages', []),
            'docket_numbers': complex_result.get('docket_numbers', []),
            'case_history': complex_result.get('case_history', []),
            'publication_status': complex_result.get('publication_status', ''),
            'year': complex_result.get('year', '')
        }
    
    if complex_result.get('is_parallel_citation'):
        formatted['is_parallel_citation'] = True
        formatted['primary_citation'] = complex_result.get('primary_citation', '')
    
    # Ensure required fields have default values
    formatted.setdefault('verified', 'false')
    formatted.setdefault('canonical_name', 'N/A')
    formatted.setdefault('canonical_date', '')
    formatted.setdefault('url', '')
    formatted.setdefault('court', '')
    formatted.setdefault('docket_number', '')
    formatted.setdefault('source', 'Unknown')
    formatted.setdefault('confidence', 'medium')
    formatted.setdefault('method', 'complex_citation')
    formatted.setdefault('pattern', 'complex')
    
    return formatted 