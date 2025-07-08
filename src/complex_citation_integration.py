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
from collections import defaultdict

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
            # Extract case name first
            case_name = self._extract_case_name(text)
            
            # Check if this is a complex citation block that should be treated as a single unit
            if self._is_complex_citation_block(text):
                # Extract the full citation block as a single unit
                full_citation = self._extract_full_citation_block(text)
                primary_citation = full_citation
                parallel_citations = []
                
                logger.info(f"[parse_complex_citation] Treating as complex citation block: '{full_citation}'")
            else:
                # Extract all citations using the existing logic
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
    
    def _is_complex_citation_block(self, text: str) -> bool:
        """Check if text represents a complete complex citation block that should not be split."""
        # Look for patterns that indicate a complete citation block
        complex_block_patterns = [
            # Pattern: Case Name, citation, citation (year)
            r'[A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?,\s*\d+\s+[A-Za-z\.\s]+\d+.*?\(\d{4}\)',
            # Pattern: Case Name, citation, page, citation, page (year)
            r'[A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?,\s*\d+\s+[A-Za-z\.\s]+\d+.*?,\s*\d+.*?\(\d{4}\)',
            # Pattern: Case Name, citation (year)
            r'[A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?,\s*\d+\s+[A-Za-z\.\s]+\d+\s*\(\d{4}\)',
        ]
        
        for pattern in complex_block_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _extract_full_citation_block(self, text: str) -> str:
        """Extract the full citation block as a single unit."""
        # Look for the complete citation pattern
        full_citation_patterns = [
            # Pattern: Case Name, citation, citation (year)
            r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?,\s*\d+\s+[A-Za-z\.\s]+\d+.*?\(\d{4}\))',
            # Pattern: Case Name, citation, page, citation, page (year)
            r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?,\s*\d+\s+[A-Za-z\.\s]+\d+.*?,\s*\d+.*?\(\d{4}\))',
            # Pattern: Case Name, citation (year)
            r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?,\s*\d+\s+[A-Za-z\.\s]+\d+\s*\(\d{4}\))',
        ]
        
        for pattern in full_citation_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # If no full pattern matches, return the original text
        return text
    
    def enhance_verification_result(self, result: Dict, complex_data: ComplexCitationData) -> Dict:
        """Enhance a verification result with complex citation data."""
        enhanced = result.copy()
        
        # CRITICAL FIX: Ensure citation field is always set with the actual citation text
        if not enhanced.get('citation') or enhanced.get('citation') == 'N/A':
            # Try to get citation from various possible fields
            citation_text = (
                enhanced.get('canonical_citation') or 
                enhanced.get('primary_citation') or 
                complex_data.primary_citation or 
                enhanced.get('citation', 'N/A')
            )
            if citation_text and citation_text != 'N/A':
                enhanced['citation'] = citation_text
        
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
        
        # Use EnhancedCitationExtractor for better parallel citation detection
        try:
            from enhanced_citation_extractor import EnhancedCitationExtractor
            enhanced_extractor = EnhancedCitationExtractor()
            complex_citations = enhanced_extractor.extract_complex_citations(text)
        except ImportError:
            # Try importing from parent directory
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from enhanced_citation_extractor import EnhancedCitationExtractor
            enhanced_extractor = EnhancedCitationExtractor()
            complex_citations = enhanced_extractor.extract_complex_citations(text)
        
        logger.info(f"[process_text_with_complex_citations_original] Enhanced extractor found {len(complex_citations)} complex citations")
        
        # Process each complex citation
        for complex_citation in complex_citations:
            logger.info(f"[process_text_with_complex_citations_original] Processing complex citation: {complex_citation.case_name}")
            primary_result = None
            parallel_results = []
            # Verify the primary citation
            if complex_citation.primary_citation:
                try:
                    primary_result = verifier.verify_citation_unified_workflow(
                        complex_citation.primary_citation,
                        extracted_case_name=complex_citation.case_name
                    )
                    # Create enhanced result with parallel citations
                    enhanced_result = primary_result.copy()
                    enhanced_result['is_complex_citation'] = True
                    enhanced_result['parallel_citations'] = complex_citation.parallel_citations
                    enhanced_result['pinpoint_pages'] = complex_citation.pinpoint_pages
                    enhanced_result['docket_numbers'] = complex_citation.docket_numbers
                    enhanced_result['case_history'] = complex_citation.case_history
                    enhanced_result['publication_status'] = complex_citation.publication_status
                    enhanced_result['year'] = complex_citation.year
                    enhanced_result['context'] = context if context is not None else text
                    results.append(enhanced_result)
                except Exception as e:
                    logger.error(f"Error verifying primary citation '{complex_citation.primary_citation}': {e}")
                    # Add unverified primary citation
                    primary_result = {
                        'citation': complex_citation.primary_citation,
                        'verified': 'false',
                        'case_name': complex_citation.case_name,
                        'is_complex_citation': True,
                        'parallel_citations': complex_citation.parallel_citations,
                        'context': context if context is not None else text,
                        'error': str(e)
                    }
                    results.append(primary_result)
            # If there are parallel citations, verify them too
            for parallel_citation in complex_citation.parallel_citations:
                try:
                    parallel_result = verifier.verify_citation_unified_workflow(
                        parallel_citation,
                        extracted_case_name=complex_citation.case_name
                    )
                    # Mark as parallel citation
                    parallel_result['is_parallel_citation'] = True
                    parallel_result['primary_citation'] = complex_citation.primary_citation
                    parallel_result['is_complex_citation'] = True
                    parallel_result['context'] = context if context is not None else text
                    results.append(parallel_result)
                    parallel_results.append(parallel_result)
                except Exception as e:
                    logger.error(f"Error verifying parallel citation '{parallel_citation}': {e}")
                    # Add unverified parallel citation
                    unverified_parallel = {
                        'citation': parallel_citation,
                        'verified': 'false',
                        'case_name': complex_citation.case_name,
                        'is_parallel_citation': True,
                        'primary_citation': complex_citation.primary_citation,
                        'is_complex_citation': True,
                        'context': context if context is not None else text,
                        'error': str(e)
                    }
                    results.append(unverified_parallel)
                    parallel_results.append(unverified_parallel)
            # --- Fallback logic: if primary is not verified, but any parallel is, mark as verified_by_parallel ---
            if primary_result and primary_result.get('verified') != 'true':
                for pr in parallel_results:
                    if pr.get('verified') == 'true':
                        # Find the enhanced_result in results and update it
                        for r in results:
                            if r.get('citation') == complex_citation.primary_citation:
                                r['verified'] = 'true_by_parallel'
                                r['verified_by_parallel'] = True
                                r['parallel_verified'] = pr.get('citation')
                                r['parallel_verified_result'] = pr
                        break
        
        # If no complex citations found, fall back to basic extraction
        if not complex_citations:
            logger.info("[process_text_with_complex_citations_original] No complex citations found, using basic extraction")
            from src.citation_extractor import CitationExtractor
            extractor = CitationExtractor(use_eyecite=False, use_regex=True, extract_case_names=True)
            extracted_citations = extractor.extract_citations(text)
            
            # Process basic citations
            for citation in extracted_citations:
                try:
                    result = verifier.verify_citation_unified_workflow(
                        citation.get('citation', ''),
                        extracted_case_name=citation.get('case_name')
                    )
                    result['context'] = context if context is not None else text
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error verifying basic citation '{citation.get('citation', '')}': {e}")
                    results.append({
                        'citation': citation.get('citation', ''),
                        'verified': 'false',
                        'case_name': citation.get('case_name'),
                        'context': context if context is not None else text,
                        'error': str(e)
                    })
        
        logger.info(f"[process_text_with_complex_citations_original] Returning {len(results)} results")

        # --- CLUSTERING AND DEDUPLICATION LOGIC ---
        # Group by case_name to cluster citations for the same case
        clusters = defaultdict(list)
        for res in results:
            # Ensure extraction fields are always present
            res['extracted_case_name'] = res.get('extracted_case_name') or res.get('case_name') or 'N/A'
            res['extracted_date'] = res.get('extracted_date') or res.get('year') or 'N/A'
            # Use case_name as the cluster key to group all citations for the same case
            key = (res.get('case_name') or '').strip().lower()
            clusters[key].append(res)

        clustered_results = []
        for key, group in clusters.items():
            if not key:  # Skip citations without case names
                continue
                
            # Select the main citation: prefer verified, most metadata, not is_parallel_citation
            def score(c):
                return (
                    c.get('verified') == 'true',
                    not c.get('is_parallel_citation', False),
                    len(str(c.get('canonical_name', ''))),
                    len(str(c.get('citation', '')))
                )
            main = sorted(group, key=score, reverse=True)[0]
            
            # Collect all parallel citations for this case
            all_parallels = []
            
            # First, add any parallel citations from the main result's parallel_citations field
            if main.get('parallel_citations'):
                for parallel in main['parallel_citations']:
                    if isinstance(parallel, dict):
                        parallel_citation = parallel.get('citation', '')
                    else:
                        parallel_citation = str(parallel)
                    
                    # Check if we have a verification result for this parallel citation
                    parallel_result = next((r for r in group if r.get('citation') == parallel_citation), None)
                    
                    if parallel_result:
                        # Use the actual verification result
                        all_parallels.append(parallel_result)
                    else:
                        # Create a minimal parallel citation object
                        all_parallels.append({
                            'citation': parallel_citation,
                            'verified': 'false',
                            'is_parallel_citation': True,
                            'primary_citation': main.get('citation'),
                            'case_name': main.get('case_name'),
                            'extracted_case_name': main.get('extracted_case_name', 'N/A'),
                            'extracted_date': main.get('extracted_date', 'N/A'),
                        })
            
            # Also add any other citations in the group that are marked as parallel
            for result in group:
                if result is not main and result.get('is_parallel_citation'):
                    all_parallels.append(result)
            
            # Remove duplicates based on citation text
            seen_citations = set()
            unique_parallels = []
            for parallel in all_parallels:
                citation_text = parallel.get('citation', '')
                if citation_text and citation_text not in seen_citations:
                    seen_citations.add(citation_text)
                    unique_parallels.append(parallel)
            
            main = main.copy()  # avoid mutating original
            # Patch: ensure each parallel has 'verified' and 'true_by_parallel' fields
            for parallel in unique_parallels:
                # If this parallel is the one that caused the main to be 'true_by_parallel', set true_by_parallel
                if main.get('verified') == 'true_by_parallel' and main.get('parallel_verified') == parallel.get('citation'):
                    parallel['true_by_parallel'] = True
                else:
                    parallel['true_by_parallel'] = False
                # Ensure 'verified' is present and is 'true', 'false', or 'true_by_parallel'
                if 'verified' not in parallel:
                    parallel['verified'] = 'false'
                # If this parallel is itself verified, set 'true_by_parallel' to False (only for main)
                if parallel.get('verified') == 'true':
                    parallel['true_by_parallel'] = False
            main['parallels'] = unique_parallels
            clustered_results.append(main)

        logger.info(f"[process_text_with_complex_citations_original] Returning {len(clustered_results)} clustered results (from {len(results)} raw results)")
        return clustered_results

    def _detect_complex_citation_blocks(self, text: str) -> List[str]:
        """Detect complex citation blocks that should be treated as single units."""
        blocks = []
        
        # Patterns for complex citation blocks
        complex_block_patterns = [
            # Pattern: Case Name, citation, citation (year)
            r'[A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?,\s*\d+\s+[A-Za-z\.\s]+\d+.*?\(\d{4}\)',
            # Pattern: Case Name, citation, page, citation, page (year)
            r'[A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?,\s*\d+\s+[A-Za-z\.\s]+\d+.*?,\s*\d+.*?\(\d{4}\)',
            # Pattern: Case Name, citation (year)
            r'[A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?,\s*\d+\s+[A-Za-z\.\s]+\d+\s*\(\d{4}\)',
        ]
        
        for pattern in complex_block_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                block = match.group(0)
                if len(block) > 20:  # Only consider substantial blocks
                    blocks.append(block)
        
        return blocks
    
    def _find_parallel_citations(self, primary_citation: dict, all_citations: list, text: str) -> List[dict]:
        """Find citations that are likely parallel citations for the same case."""
        parallel_group = [primary_citation]
        primary_text = primary_citation.get('citation', '')
        
        # Find the position of the primary citation
        primary_index = text.find(primary_text)
        if primary_index == -1:
            return parallel_group
        
        # Look for citations in close proximity (within 100 characters)
        start_pos = max(0, primary_index - 100)
        end_pos = min(len(text), primary_index + len(primary_text) + 100)
        vicinity_text = text[start_pos:end_pos]
        
        # Check if there's a case name in the vicinity
        case_name = self._extract_case_name_from_vicinity(vicinity_text)
        
        for citation in all_citations:
            citation_text = citation.get('citation', '')
            if citation_text == primary_text:
                continue
            
            # Check if this citation is in the same vicinity
            if citation_text in vicinity_text:
                # Additional checks to ensure they're actually parallel
                if self._are_likely_parallel(primary_text, citation_text, case_name):
                    parallel_group.append(citation)
        
        return parallel_group
    
    def _extract_case_name_from_vicinity(self, vicinity_text: str) -> Optional[str]:
        """Extract case name from the vicinity text."""
        case_name_patterns = [
            r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
            r'(In\s+re\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
            r'(State\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
        ]
        
        for pattern in case_name_patterns:
            match = re.search(pattern, vicinity_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _are_likely_parallel(self, citation1: str, citation2: str, case_name: Optional[str] = None) -> bool:
        """Check if two citations are likely parallel citations for the same case."""
        # If we have a case name, both citations should be associated with it
        if case_name:
            # Check if both citations appear in a pattern like "Case Name, citation1, citation2"
            pattern = rf'{re.escape(case_name)}\s*,\s*[^,]*{re.escape(citation1)}[^,]*,\s*[^,]*{re.escape(citation2)}'
            if re.search(pattern, case_name + ", " + citation1 + ", " + citation2, re.IGNORECASE):
                return True
        
        # Check if they're different reporters for the same case
        # Common parallel citation patterns
        parallel_patterns = [
            # Washington App + Pacific Reporter
            (r'(\d+)\s+Wn\.\s*App\.\s+(\d+)', r'(\d+)\s+P\.3d\s+(\d+)'),
            (r'(\d+)\s+Wn\.2d\s+(\d+)', r'(\d+)\s+P\.3d\s+(\d+)'),
            # U.S. Reports + Supreme Court Reporter
            (r'(\d+)\s+U\.\s*S\.\s+(\d+)', r'(\d+)\s+S\.\s*Ct\.\s+(\d+)'),
            # Federal Reporter variations
            (r'(\d+)\s+F\.3d\s+(\d+)', r'(\d+)\s+F\.\s*Supp\.\s+(\d+)'),
        ]
        
        for pattern1, pattern2 in parallel_patterns:
            match1 = re.search(pattern1, citation1)
            match2 = re.search(pattern2, citation2)
            if match1 and match2:
                # Check if they have the same year (if available)
                return True
        
        return False

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