"""
Updated Legal Case Extractor - Integrated with Streamlined Extraction
Combines the enhanced case extraction patterns with the new streamlined core
"""

import re
import logging
from typing import List, Dict, Optional, NamedTuple, Any
from dataclasses import dataclass
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

# Import the streamlined extractor
from case_name_extraction_core import (
    extract_case_name_and_date, 
    CaseNameExtractor,
    ExtractionResult
)

@dataclass
class CaseExtraction:
    """Enhanced case extraction result - integrated with streamlined core"""
    full_match: str
    case_name: str
    party_1: Optional[str] = None
    party_2: Optional[str] = None
    volume: Optional[str] = None
    reporter: Optional[str] = None
    page: Optional[str] = None
    pincite: Optional[str] = None
    year: Optional[str] = None
    date_info: Optional[Dict] = None
    case_type: Optional[str] = None  # 'standard', 'in_re', 'ex_parte'
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None
    confidence: float = 0.0
    extraction_method: str = "regex"

class LegalCaseExtractorIntegrated:
    """
    Enhanced legal case extractor integrated with streamlined case name extraction
    
    This combines:
    - Your existing citation pattern matching (volume, reporter, page)
    - The new streamlined case name extraction
    - Enhanced date extraction
    """
    
    def __init__(self):
        self.patterns = self._compile_patterns()
        self.case_name_extractor = CaseNameExtractor()
        
        # Enhanced reporter patterns
        self.reporter_patterns = self._get_enhanced_reporter_patterns()
        
        # Court abbreviations for enhanced date parsing
        self.court_abbreviations = self._get_court_abbreviations()
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile all regex patterns for citation extraction"""
        patterns = {}
        
        # Standard adversarial cases (Party v. Party)
        patterns['standard'] = re.compile(
            r'([A-Z][^,]*?(?:Inc\.|Corp\.|LLC|Co\.|Ltd\.|et al\.)?)'  # Party 1
            r'\s+v\.\s+'  # " v. "
            r'([^,]+?(?:Inc\.|Corp\.|LLC|Co\.|Ltd\.|et al\.)?)'  # Party 2
            r',\s*'  # Comma separator
            r'(\d+)\s+'  # Volume
            r'([A-Z]+\.?\d*[a-z]*)\s+'  # Reporter
            r'(\d+)'  # Page
            r'(?:,\s*(\d+))?'  # Optional pincite
            r'(?:.*?)'  # Optional additional citation info
            r'(?:\s*\(([^)]*\d{4}[^)]*)\))?',  # Optional year in parentheses
            re.IGNORECASE
        )
        
        # In re cases
        patterns['in_re'] = re.compile(
            r'In re\s+'  # "In re "
            r'([^,]+?)'  # Case subject
            r',\s*'  # Comma separator
            r'(\d+)\s+'  # Volume
            r'([A-Z]+\.?\d*[a-z]*)\s+'  # Reporter
            r'(\d+)'  # Page
            r'(?:,\s*(\d+))?'  # Optional pincite
            r'(?:.*?)'  # Optional additional citation info
            r'(?:\s*\(([^)]*\d{4}[^)]*)\))?',  # Optional year in parentheses
            re.IGNORECASE
        )
        
        # Ex parte cases
        patterns['ex_parte'] = re.compile(
            r'Ex parte\s+'  # "Ex parte "
            r'([^,]+?)'  # Case subject
            r',\s*'  # Comma separator
            r'(\d+)\s+'  # Volume
            r'([A-Z]+\.?\d*[a-z]*)\s+'  # Reporter
            r'(\d+)'  # Page
            r'(?:,\s*(\d+))?'  # Optional pincite
            r'(?:.*?)'  # Optional additional citation info
            r'(?:\s*\(([^)]*\d{4}[^)]*)\))?',  # Optional year in parentheses
            re.IGNORECASE
        )
        
        # Matter of cases
        patterns['matter_of'] = re.compile(
            r'Matter of\s+'  # "Matter of "
            r'([^,]+?)'  # Case subject
            r',\s*'  # Comma separator
            r'(\d+)\s+'  # Volume
            r'([A-Z]+\.?\d*[a-z]*)\s+'  # Reporter
            r'(\d+)'  # Page
            r'(?:,\s*(\d+))?'  # Optional pincite
            r'(?:.*?)'  # Optional additional citation info
            r'(?:\s*\(([^)]*\d{4}[^)]*)\))?',  # Optional year in parentheses
            re.IGNORECASE
        )
        
        # Simple citation pattern (fallback)
        patterns['simple_citation'] = re.compile(
            r'(\d+)\s+'  # Volume
            r'([A-Z]+\.?\d*[a-z]*)\s+'  # Reporter
            r'(\d+)'  # Page
            r'(?:,\s*(\d+))?'  # Optional pincite
            r'(?:.*?)'  # Optional additional citation info
            r'(?:\s*\(([^)]*\d{4}[^)]*)\))?',  # Optional year in parentheses
            re.IGNORECASE
        )
        
        return patterns
    
    def _get_enhanced_reporter_patterns(self) -> Dict[str, List[str]]:
        """Enhanced reporter patterns"""
        return {
            'federal': [
                'F\\.', 'F\\.2d', 'F\\.3d', 'F\\.4th',
                'F\\.Supp\\.', 'F\\.Supp\\.2d', 'F\\.Supp\\.3d',
                'F\\.R\\.D\\.', 'Fed\\. R\\.'
            ],
            'supreme_court': [
                'U\\.S\\.', 'S\\.Ct\\.', 'L\\.Ed\\.', 'L\\.Ed\\.2d'
            ],
            'washington': [
                'Wn\\.', 'Wn\\.2d', 'Wn\\.App\\.', 'Wash\\.',
                'Wash\\.2d', 'Wash\\.App\\.'
            ],
            'pacific': [
                'P\\.', 'P\\.2d', 'P\\.3d'
            ],
            'state': [
                'A\\.', 'A\\.2d', 'A\\.3d',
                'N\\.E\\.', 'N\\.E\\.2d', 'N\\.E\\.3d',
                'S\\.E\\.', 'S\\.E\\.2d', 'S\\.E\\.3d',
                'S\\.W\\.', 'S\\.W\\.2d', 'S\\.W\\.3d',
                'So\\.', 'So\\.2d', 'So\\.3d',
                'N\\.W\\.', 'N\\.W\\.2d', 'N\\.W\\.3d'
            ]
        }
    
    def _get_court_abbreviations(self) -> Dict[str, str]:
        """Enhanced court abbreviation mapping"""
        return {
            # Federal Courts
            'Cir\\.': 'Circuit Court of Appeals',
            'D\\.': 'District Court',
            'S\\.D\\.': 'Southern District',
            'N\\.D\\.': 'Northern District',
            'E\\.D\\.': 'Eastern District',
            'W\\.D\\.': 'Western District',
            'C\\.D\\.': 'Central District',
            'M\\.D\\.': 'Middle District',
            
            # Washington Courts
            'Wn\\.': 'Washington',
            'Wash\\.': 'Washington',
            
            # Supreme Court
            'U\\.S\\.': 'United States Supreme Court'
        }
    
    def extract_cases(self, text: str) -> List[CaseExtraction]:
        """
        Extract all legal cases from text using integrated approach
        
        Combines citation pattern matching with streamlined case name extraction
        """
        extractions = []
        
        for case_type, pattern in self.patterns.items():
            matches = pattern.finditer(text)
            
            for match in matches:
                extraction = self._parse_match_integrated(match, case_type, text)
                if extraction:
                    extractions.append(extraction)
        
        # Remove duplicates and sort by position
        extractions = self._deduplicate_extractions(extractions)
        return sorted(extractions, key=lambda x: x.start_pos or 0)
    
    def _parse_match_integrated(self, match: re.Match, case_type: str, full_text: str) -> Optional[CaseExtraction]:
        """
        Parse a regex match using integrated case name extraction
        
        This method combines:
        1. Citation component extraction (volume, reporter, page)
        2. Streamlined case name extraction
        3. Enhanced date parsing
        """
        try:
            groups = match.groups()
            
            # Extract citation components
            if case_type == 'standard':
                volume = groups[2] if len(groups) > 2 else None
                reporter = groups[3] if len(groups) > 3 else None
                page = groups[4] if len(groups) > 4 else None
                pincite = groups[5] if len(groups) > 5 else None
                date_string = groups[6] if len(groups) > 6 else None
            else:  # in_re, ex_parte, matter_of
                volume = groups[1] if len(groups) > 1 else None
                reporter = groups[2] if len(groups) > 2 else None
                page = groups[3] if len(groups) > 3 else None
                pincite = groups[4] if len(groups) > 4 else None
                date_string = groups[5] if len(groups) > 5 else None
            
            # Build citation string for streamlined extraction
            citation_parts = [volume, reporter, page]
            citation = ' '.join(filter(None, citation_parts))
            
            # Use streamlined case name extraction
            case_extraction = extract_case_name_and_date(full_text, citation)
            
            # Extract case name with fallback to pattern-based extraction
            if case_extraction['case_name'] != 'N/A':
                case_name = case_extraction['case_name']
                extraction_method = f"streamlined_{case_extraction['method']}"
                confidence = case_extraction['confidence']
            else:
                # Fallback to pattern-based extraction
                case_name = self._extract_case_name_from_pattern(groups, case_type)
                extraction_method = f"pattern_{case_type}"
                confidence = 0.5  # Lower confidence for pattern-only
            
            # Extract year with fallback
            year = None
            if case_extraction['year'] != 'N/A':
                year = case_extraction['year']
            elif date_string:
                year = self._extract_year_from_date_string(date_string)
            
            # Parse party information for standard cases
            party_1, party_2 = None, None
            if case_type == 'standard' and case_name and ' v. ' in case_name:
                parts = case_name.split(' v. ', 1)
                if len(parts) == 2:
                    party_1, party_2 = parts[0].strip(), parts[1].strip()
            
            return CaseExtraction(
                full_match=match.group(0),
                case_name=case_name,
                party_1=party_1,
                party_2=party_2,
                volume=volume,
                reporter=reporter,
                page=page,
                pincite=pincite,
                year=year,
                date_info=self._parse_date_info(date_string) if date_string else None,
                case_type=case_type,
                start_pos=match.start(),
                end_pos=match.end(),
                confidence=confidence,
                extraction_method=extraction_method
            )
            
        except Exception as e:
            import logging
            logging.error(f"Error parsing match: {e}")
            return None
    
    def _extract_case_name_from_pattern(self, groups: tuple, case_type: str) -> str:
        """Fallback case name extraction from regex groups"""
        try:
            if case_type == 'standard' and len(groups) >= 2:
                return f"{groups[0]} v. {groups[1]}"
            elif case_type == 'in_re' and len(groups) >= 1:
                return f"In re {groups[0]}"
            elif case_type == 'ex_parte' and len(groups) >= 1:
                return f"Ex parte {groups[0]}"
            elif case_type == 'matter_of' and len(groups) >= 1:
                return f"Matter of {groups[0]}"
        except (IndexError, TypeError):
            pass
        return ""
    
    def _extract_year_from_date_string(self, date_string: str) -> Optional[str]:
        """Extract year from date string"""
        if not date_string:
            return None
        
        year_match = re.search(r'(\d{4})', date_string)
        return year_match.group(1) if year_match else None
    
    def _parse_date_info(self, date_string: str) -> Dict:
        """Parse date string into structured information"""
        if not date_string:
            return {}
        
        info = {'original': date_string}
        
        # Extract year
        year_match = re.search(r'(\d{4})', date_string)
        if year_match:
            info['year'] = year_match.group(1)
        
        # Extract court information
        court_info = re.sub(r'\d{4}', '', date_string).strip(' ()')
        if court_info:
            info['court'] = court_info
        
        return info
    
    def _deduplicate_extractions(self, extractions: List[CaseExtraction]) -> List[CaseExtraction]:
        """Remove duplicate extractions based on position overlap"""
        if not extractions:
            return []
        
        # Sort by start position and confidence
        sorted_extractions = sorted(extractions, key=lambda x: (x.start_pos or 0, -x.confidence))
        deduplicated = [sorted_extractions[0]]
        
        for extraction in sorted_extractions[1:]:
            # Check if this extraction overlaps with any existing one
            overlaps = False
            for existing in deduplicated:
                if (extraction.start_pos is not None and existing.end_pos is not None and
                    extraction.end_pos is not None and existing.start_pos is not None and
                    extraction.start_pos < existing.end_pos and 
                    extraction.end_pos > existing.start_pos):
                    overlaps = True
                    break
            
            if not overlaps:
                deduplicated.append(extraction)
        
        return deduplicated
    
    def get_extraction_stats(self, extractions: List[CaseExtraction]) -> Dict[str, Any]:
        """Get comprehensive statistics about extractions"""
        if not extractions:
            return {
                'total': 0,
                'by_type': {},
                'by_method': {},
                'confidence_distribution': {'high': 0, 'medium': 0, 'low': 0},
                'with_case_names': 0,
                'with_years': 0,
                'with_pincites': 0,
                'average_confidence': 0.0
            }
        
        stats = {
            'total': len(extractions),
            'by_type': {},
            'by_method': {},
            'confidence_distribution': {
                'high': 0,  # >0.8
                'medium': 0,  # 0.5-0.8
                'low': 0  # <0.5
            },
            'with_case_names': len([e for e in extractions if e.case_name]),
            'with_years': len([e for e in extractions if e.year]),
            'with_pincites': len([e for e in extractions if e.pincite]),
            'average_confidence': sum(e.confidence for e in extractions) / len(extractions)
        }
        
        # Count by type
        for extraction in extractions:
            case_type = extraction.case_type or 'unknown'
            stats['by_type'][case_type] = stats['by_type'].get(case_type, 0) + 1
            
            method = extraction.extraction_method or 'unknown'
            stats['by_method'][method] = stats['by_method'].get(method, 0) + 1
            
            # Confidence distribution
            if extraction.confidence > 0.8:
                stats['confidence_distribution']['high'] += 1
            elif extraction.confidence >= 0.5:
                stats['confidence_distribution']['medium'] += 1
            else:
                stats['confidence_distribution']['low'] += 1
        
        return stats

# Convenience functions for backward compatibility
def extract_cases_from_text(text: str) -> List[CaseExtraction]:
    """Extract all cases from text using integrated extractor"""
    extractor = LegalCaseExtractorIntegrated()
    return extractor.extract_cases(text)

def extract_single_case(text: str, citation: str) -> Optional[CaseExtraction]:
    """Extract a specific case from text"""
    extractions = extract_cases_from_text(text)
    
    # Find the extraction that best matches the citation
    for extraction in extractions:
        if citation in extraction.full_match:
            return extraction
    
    return None

# Integration with your existing legal case extractor
def update_existing_extractor():
    """
    Instructions for updating your existing LegalCaseExtractor class
    
    Replace the _parse_match method with _parse_match_integrated
    Add the streamlined case name extraction as a fallback
    """
    sample_integration = """
    # In your existing LegalCaseExtractor class:
    
    def __init__(self):
        # ... existing initialization ...
        from case_name_extraction_core import CaseNameExtractor
        self.case_name_extractor = CaseNameExtractor()
    
    def _parse_match(self, match: re.Match, case_type: str) -> Optional[CaseExtraction]:
        # Replace with _parse_match_integrated from above
        return self._parse_match_integrated(match, case_type, self.current_text)
    """
    return sample_integration

def test_integrated_extractor():
    """Test the integrated extractor"""
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2002)"""
    
    logger.info("=== Integrated Extractor Test ===")
    
    extractor = LegalCaseExtractorIntegrated()
    extractions = extractor.extract_cases(test_text)
    
    logger.info(f"Found {len(extractions)} cases:")
    for i, extraction in enumerate(extractions, 1):
        logger.info(f"\n{i}. {extraction.case_name}")
        logger.info(f"   Citation: {extraction.volume} {extraction.reporter} {extraction.page}")
        logger.info(f"   Year: {extraction.year}")
        logger.info(f"   Method: {extraction.extraction_method}")
        logger.info(f"   Confidence: {extraction.confidence:.2f}")
        logger.info(f"   Type: {extraction.case_type}")
    
    # Show statistics
    stats = extractor.get_extraction_stats(extractions)
    logger.info(f"\n=== Statistics ===")
    logger.info(f"Total extractions: {stats['total']}")
    logger.info(f"With case names: {stats['with_case_names']}")
    logger.info(f"With years: {stats['with_years']}")
    logger.info(f"Average confidence: {stats['average_confidence']:.2f}")
    logger.info(f"By method: {stats['by_method']}")

if __name__ == "__main__":
    test_integrated_extractor() 