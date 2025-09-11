"""
TOA-Based Citation Evaluator
Uses Table of Authorities to get canonical case names and evaluate text against known cases.

This approach solves the three main issues:
1. Context isolation problems - uses TOA as authoritative source
2. Case name truncation - gets complete names from TOA
3. Year cross-contamination - maps citations to specific years from TOA
"""

import re
from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from toa_parser import ImprovedToAParser

logger = logging.getLogger(__name__)

@dataclass
class CanonicalCase:
    """Represents a canonical case from the Table of Authorities."""
    case_name: str
    citations: List[str]
    years: List[str]
    confidence: float
    source_line: str

@dataclass
class CitationMatch:
    """Represents a citation found in text that matches a canonical case."""
    citation: str
    canonical_case: CanonicalCase
    case_name: str
    year: str
    confidence: float
    method: str

class ToABasedCitationEvaluator:
    """
    Evaluates citations in text using Table of Authorities as the authoritative source.
    """
    
    def __init__(self):
        self.toa_parser = ImprovedToAParser()
        self.canonical_cases: List[CanonicalCase] = []
        self.citation_to_case_map: Dict[str, CanonicalCase] = {}
        
    def load_toa_from_text(self, text: str) -> bool:
        """
        Load canonical cases from Table of Authorities in the text.
        
        Args:
            text: Full document text containing TOA section
            
        Returns:
            True if TOA was successfully loaded
        """
        try:
            logger.info("[TOA EVALUATOR] Loading TOA from text...")
            
            toa_bounds = self.toa_parser.detect_toa_section(text)
            if not toa_bounds:
                logger.warning("[TOA EVALUATOR] No TOA section found")
                return False
                
            start, end = toa_bounds
            toa_section = text[start:end]
            
            toa_entries = self.toa_parser.parse_toa_section_simple(toa_section)
            
            self.canonical_cases = []
            self.citation_to_case_map = {}
            
            for entry in toa_entries:
                canonical_case = CanonicalCase(
                    case_name=entry.case_name,
                    citations=entry.citations,
                    years=entry.years,
                    confidence=entry.confidence,
                    source_line=entry.source_line
                )
                self.canonical_cases.append(canonical_case)
                
                for citation in entry.citations:
                    self.citation_to_case_map[citation] = canonical_case
                    
            logger.info(f"[TOA EVALUATOR] Loaded {len(self.canonical_cases)} canonical cases with {len(self.citation_to_case_map)} citation mappings")
            return True
            
        except Exception as e:
            logger.error(f"[TOA EVALUATOR] Error loading TOA: {e}")
            return False
    
    def find_citations_in_text(self, text: str) -> List[str]:
        """
        Find all citation patterns in text.
        
        Args:
            text: Text to search for citations
            
        Returns:
            List of found citations
        """
        citations = []
        
        citation_patterns = [
            r'\d+\s+Wn\.\s*\d+\s*[A-Za-z]+\s*\d+',  # 200 Wn.2d 72
            r'\d+\s+Wn\.\s*App\.\s*\d+',              # 136 Wn. App. 104
            r'\d+\s+P\.\s*\d+\s*\d+',                 # 514 P.3d 643
            r'\d+\s+U\.S\.\s*\d+',                    # 548 U.S. 140
            r'\d+\s+S\.Ct\.\s*\d+',                   # 126 S.Ct. 2557
        ]
        
        for pattern in citation_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                citation = match.group(0).strip()
                if citation not in citations:
                    citations.append(citation)
        
        return citations
    
    def evaluate_citations_in_text(self, text: str) -> List[CitationMatch]:
        """
        Evaluate all citations found in text against canonical cases from TOA.
        
        Args:
            text: Text to evaluate
            
        Returns:
            List of citation matches with canonical information
        """
        if not self.canonical_cases:
            logger.warning("[TOA EVALUATOR] No canonical cases loaded. Call load_toa_from_text() first.")
            return []
        
        matches = []
        
        citations = self.find_citations_in_text(text)
        logger.info(f"[TOA EVALUATOR] Found {len(citations)} citations in text")
        
        for citation in citations:
            match = self.evaluate_single_citation(citation)
            if match:
                matches.append(match)
        
        return matches
    
    def evaluate_single_citation(self, citation: str) -> Optional[CitationMatch]:
        """
        Evaluate a single citation against canonical cases.
        
        Args:
            citation: Citation to evaluate
            
        Returns:
            CitationMatch if found, None otherwise
        """
        if citation in self.citation_to_case_map:
            canonical_case = self.citation_to_case_map[citation]
            
            year = self._get_best_year_for_citation(citation, canonical_case)
            
            return CitationMatch(
                citation=citation,
                canonical_case=canonical_case,
                case_name=canonical_case.case_name,
                year=year,
                confidence=canonical_case.confidence,
                method="toa_direct_match"
            )
        
        for canonical_case in self.canonical_cases:
            for canonical_citation in canonical_case.citations:
                if self._citations_match(citation, canonical_citation):
                    year = self._get_best_year_for_citation(citation, canonical_case)
                    
                    return CitationMatch(
                        citation=citation,
                        canonical_case=canonical_case,
                        case_name=canonical_case.case_name,
                        year=year,
                        confidence=canonical_case.confidence * 0.9,  # Slightly lower confidence for partial match
                        method="toa_partial_match"
                    )
        
        return None
    
    def _citations_match(self, citation1: str, citation2: str) -> bool:
        """
        Check if two citations refer to the same case.
        
        Args:
            citation1: First citation
            citation2: Second citation
            
        Returns:
            True if citations match
        """
        def normalize_citation(citation: str) -> str:
            normalized = re.sub(r',\s*\d+.*$', '', citation)  # Remove everything after first comma
            normalized = re.sub(r'\s+', ' ', normalized).strip()  # Normalize whitespace
            return normalized
        
        norm1 = normalize_citation(citation1)
        norm2 = normalize_citation(citation2)
        
        return norm1 == norm2
    
    def _get_best_year_for_citation(self, citation: str, canonical_case: CanonicalCase) -> str:
        """
        Get the best year for a citation from the canonical case.
        
        Args:
            citation: Citation to get year for
            canonical_case: Canonical case containing the citation
            
        Returns:
            Best year for the citation
        """
        if not canonical_case.years:
            return ""
        
        if len(canonical_case.years) == 1:
            return canonical_case.years[0]
        
        year_match = re.search(r'\((\d{4})\)', citation)
        if year_match:
            return year_match.group(1)
        
        return canonical_case.years[0]
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of loaded canonical cases and citation mappings.
        
        Returns:
            Summary dictionary
        """
        return {
            'canonical_cases_count': len(self.canonical_cases),
            'citation_mappings_count': len(self.citation_to_case_map),
            'canonical_cases': [
                {
                    'case_name': case.case_name,
                    'citations': case.citations,
                    'years': case.years,
                    'confidence': case.confidence
                }
                for case in self.canonical_cases
            ],
            'citation_mappings': list(self.citation_to_case_map.keys())
        }

def evaluate_text_with_toa(text: str) -> List[CitationMatch]:
    """
    Quick function to evaluate text using TOA without creating evaluator instance.
    
    Args:
        text: Text to evaluate
        
    Returns:
        List of citation matches
    """
    evaluator = ToABasedCitationEvaluator()
    if evaluator.load_toa_from_text(text):
        return evaluator.evaluate_citations_in_text(text)
    return []
