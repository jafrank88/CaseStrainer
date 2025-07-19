"""
Streamlined Case Name and Date Extraction
Consolidates all extraction logic into a clean, maintainable structure
"""

import re
import logging
from typing import Dict, Optional, Tuple, List
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ExtractionResult:
    """Structured result for case name and date extraction"""
    case_name: str = ""
    date: str = ""
    year: str = ""
    confidence: float = 0.0
    method: str = "unknown"
    debug_info: Dict = None
    
    def __post_init__(self):
        if self.debug_info is None:
            self.debug_info = {}
        
        # Extract year from date if not provided
        if self.date and not self.year:
            year_match = re.search(r'(\d{4})', self.date)
            if year_match:
                self.year = year_match.group(1)

class CaseNameExtractor:
    """
    Unified case name and date extraction with clear methodology
    """
    
    def __init__(self):
        self.date_extractor = DateExtractor()
        self._setup_patterns()
    
    def _setup_patterns(self):
        """Initialize extraction patterns"""
        self.case_patterns = [
            # High confidence patterns - Standard adversarial cases
            {
                'name': 'standard_v',
                'pattern': r'([A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?)\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?)(?=,\s*\d|\s*\(|$)',
                'confidence_base': 0.9,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}"
            },
            {
                'name': 'standard_vs',
                'pattern': r'([A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?)\s+vs\.\s+([A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?)(?=,\s*\d|\s*\(|$)',
                'confidence_base': 0.85,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}"
            },
            {
                'name': 'standard_versus',
                'pattern': r'([A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?)\s+versus\s+([A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?)(?=,\s*\d|\s*\(|$)',
                'confidence_base': 0.8,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}"
            },
            # Government/institutional cases
            {
                'name': 'state_v',
                'pattern': r'(State\s+(?:of\s+)?[A-Za-z\s]*)\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?)(?=,\s*\d|\s*\(|$)',
                'confidence_base': 0.9,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}"
            },
            {
                'name': 'us_v',
                'pattern': r'(United\s+States(?:\s+of\s+America)?)\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?)(?=,\s*\d|\s*\(|$)',
                'confidence_base': 0.9,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}"
            },
            {
                'name': 'people_v',
                'pattern': r'(People\s+(?:of\s+)?(?:the\s+)?(?:State\s+of\s+)?[A-Za-z\s]*)\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?)(?=,\s*\d|\s*\(|$)',
                'confidence_base': 0.9,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}"
            },
            {
                'name': 'commonwealth_v',
                'pattern': r'(Commonwealth\s+(?:of\s+)?[A-Za-z\s]*)\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?)(?=,\s*\d|\s*\(|$)',
                'confidence_base': 0.9,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}"
            },
            {
                'name': 'department_v',
                'pattern': r'((?:Dep\'t|Department)\s+of\s+[A-Za-z\s,&\.]+)\s+v\.\s+([A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?)(?=,\s*\d|\s*\(|$)',
                'confidence_base': 0.9,
                'format': lambda m: f"{m.group(1).strip()} v. {m.group(2).strip()}"
            },
            # Non-adversarial cases
            {
                'name': 'in_re',
                'pattern': r'(In\s+re\s+[A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?)(?=,\s*\d|\s*\(|$)',
                'confidence_base': 0.8,
                'format': lambda m: m.group(1).strip()
            },
            {
                'name': 'in_the_matter_of',
                'pattern': r'(In\s+the\s+Matter\s+of\s+[A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?)(?=,\s*\d|\s*\(|$)',
                'confidence_base': 0.8,
                'format': lambda m: m.group(1).strip()
            },
            {
                'name': 'matter_of',
                'pattern': r'(Matter\s+of\s+[A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?)(?=,\s*\d|\s*\(|$)',
                'confidence_base': 0.8,
                'format': lambda m: m.group(1).strip()
            },
            {
                'name': 'estate_of',
                'pattern': r'(Estate\s+of\s+[A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?)(?=,\s*\d|\s*\(|$)',
                'confidence_base': 0.8,
                'format': lambda m: m.group(1).strip()
            },
            {
                'name': 'ex_parte',
                'pattern': r'(Ex\s+parte\s+[A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?)(?=,\s*\d|\s*\(|$)',
                'confidence_base': 0.75,
                'format': lambda m: m.group(1).strip()
            }
        ]
    
    def extract(self, text: str, citation: str = None) -> ExtractionResult:
        """
        Main extraction method
        
        Args:
            text: Document text
            citation: Specific citation to search for (optional)
            
        Returns:
            ExtractionResult with case name, date, and metadata
        """
        result = ExtractionResult()
        
        try:
            # Step 1: Get context around citation if provided
            context = self._get_extraction_context(text, citation)
            
            # Step 2: Try case name extraction
            case_extraction = self._extract_case_name(context, citation)
            if case_extraction:
                result.case_name = case_extraction['name']
                result.confidence = case_extraction['confidence']
                result.method = case_extraction['method']
                result.debug_info.update(case_extraction.get('debug', {}))
            
            # Step 3: Try date extraction
            date_extraction = self.date_extractor.extract_date_from_context(
                text, citation
            ) if citation else self.date_extractor.extract_date_from_full_text(text)
            
            if date_extraction:
                result.date = date_extraction
                # Extract year from date
                year_match = re.search(r'(\d{4})', date_extraction)
                if year_match:
                    result.year = year_match.group(1)
            
            logger.info(f"Extraction complete: {result.case_name} ({result.year}) - {result.method}")
            
        except Exception as e:
            logger.error(f"Error in extraction: {e}")
            result.debug_info['error'] = str(e)
        
        return result
    
    def _get_extraction_context(self, text: str, citation: str = None) -> str:
        """Get relevant context for extraction"""
        if not citation:
            return text
        
        citation_pos = text.find(citation)
        if citation_pos == -1:
            return text
        
        # Use smaller, more focused context window around citation
        context_start = max(0, citation_pos - 150)
        context_end = min(len(text), citation_pos + 50)
        return text[context_start:context_end]
    
    def _extract_case_name(self, context: str, citation: str = None) -> Optional[Dict]:
        """Extract case name using pattern matching"""
        
        # Clean context
        context = re.sub(r'\s+', ' ', context.strip())
        
        best_match = None
        best_confidence = 0.0
        
        for pattern_info in self.case_patterns:
            pattern = re.compile(pattern_info['pattern'], re.IGNORECASE)
            
            for match in pattern.finditer(context):
                # Format the case name
                try:
                    case_name = pattern_info['format'](match)
                    cleaned_name = self._clean_case_name(case_name)
                    
                    if not self._validate_case_name(cleaned_name):
                        continue
                    
                    # Calculate confidence
                    confidence = self._calculate_confidence(
                        cleaned_name, 
                        pattern_info['confidence_base'],
                        match,
                        context
                    )
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = {
                            'name': cleaned_name,
                            'confidence': confidence,
                            'method': pattern_info['name'],
                            'debug': {
                                'pattern': pattern_info['name'],
                                'raw_match': match.group(0),
                                'match_position': match.span()
                            }
                        }
                        
                except Exception as e:
                    logger.debug(f"Error processing match: {e}")
                    continue
        
        return best_match
    
    def _clean_case_name(self, case_name: str) -> str:
        """Clean and normalize case name"""
        if not case_name:
            return ""
        
        # Remove citation fragments
        case_name = re.sub(r',\s*\d+\s+[A-Za-z.]+.*$', '', case_name)
        case_name = re.sub(r'\(\d{4}\).*$', '', case_name)
        
        # Normalize spacing
        case_name = re.sub(r'\s+', ' ', case_name.strip())
        case_name = case_name.strip(' ,;')
        
        # Normalize v. format
        case_name = re.sub(r'\s+v\.\s+', ' v. ', case_name)
        case_name = re.sub(r'\s+vs\.\s+', ' v. ', case_name)
        
        return case_name
    
    def _validate_case_name(self, case_name: str) -> bool:
        """Validate extracted case name"""
        if not case_name or len(case_name) < 3:
            return False
        
        # Must contain letters
        if not re.search(r'[a-zA-Z]', case_name):
            return False
        
        # Must start with capital letter
        if not case_name[0].isupper():
            return False
        
        # Check for valid case name indicators
        has_v = ' v. ' in case_name.lower()
        has_special = any(case_name.lower().startswith(prefix) 
                         for prefix in ['in re', 'estate of', 'state v.', 'united states v.'])
        
        return has_v or has_special
    
    def _calculate_confidence(self, case_name: str, base_confidence: float, 
                            match: re.Match, context: str) -> float:
        """Calculate confidence score for extraction"""
        confidence = base_confidence
        
        # Length bonus
        if len(case_name) > 20:
            confidence += 0.1
        elif len(case_name) < 10:
            confidence -= 0.1
        
        # Position bonus (closer to beginning is often better)
        position_ratio = match.start() / len(context)
        if position_ratio < 0.3:
            confidence += 0.05
        
        # Quality indicators
        if re.search(r'\b(Department|Dep\'t|State|United States)\b', case_name):
            confidence += 0.05
        
        return min(1.0, max(0.0, confidence))

class DateExtractor:
    """
    Streamlined date extraction focused on legal document patterns
    """
    
    def __init__(self):
        self.patterns = [
            # High priority patterns
            (r'\((\d{4})\)', 0.9),  # (2022)
            (r',\s*(\d{4})\s*(?=[A-Z]|$)', 0.8),  # , 2022
            (r'(\d{4})-\d{1,2}-\d{1,2}', 0.7),  # 2022-01-15
            (r'\d{1,2}/\d{1,2}/(\d{4})', 0.6),  # 01/15/2022
            (r'\b(19|20)\d{2}\b', 0.4),  # Simple 4-digit year
        ]
    
    def extract_date_from_context(self, text: str, citation: str) -> Optional[str]:
        """Extract date using citation as context anchor"""
        citation_pos = text.find(citation)
        if citation_pos == -1:
            return self.extract_date_from_full_text(text)
        
        # Get context around citation
        context_start = max(0, citation_pos - 100)
        context_end = min(len(text), citation_pos + len(citation) + 50)
        context = text[context_start:context_end]
        
        return self._extract_date_from_text(context)
    
    def extract_date_from_full_text(self, text: str) -> Optional[str]:
        """Extract date from full text"""
        return self._extract_date_from_text(text)
    
    def _extract_date_from_text(self, text: str) -> Optional[str]:
        """Internal date extraction logic"""
        best_date = None
        best_confidence = 0.0
        
        for pattern, base_confidence in self.patterns:
            for match in re.finditer(pattern, text):
                if pattern.endswith(r'\b'):  # Simple year pattern
                    year = match.group(0)
                else:
                    year = match.group(1)
                
                if self._validate_year(year):
                    if base_confidence > best_confidence:
                        best_confidence = base_confidence
                        best_date = year
        
        return best_date
    
    def _validate_year(self, year: str) -> bool:
        """Validate year is reasonable"""
        try:
            year_int = int(year)
            return 1800 <= year_int <= 2030
        except (ValueError, TypeError):
            return False

# Global extractor instance
_extractor = None

def get_extractor() -> CaseNameExtractor:
    """Get global extractor instance"""
    global _extractor
    if _extractor is None:
        _extractor = CaseNameExtractor()
    return _extractor

# Simplified API functions for backward compatibility
def extract_case_name_and_date(text: str, citation: str = None) -> Dict[str, str]:
    """
    Main extraction function - replaces all the complex variants
    
    Args:
        text: Document text
        citation: Citation to search for (optional)
        
    Returns:
        Dict with case_name, date, year, confidence, method
    """
    extractor = get_extractor()
    result = extractor.extract(text, citation)
    
    return {
        'case_name': result.case_name or "N/A",
        'date': result.date or "N/A", 
        'year': result.year or "N/A",
        'confidence': result.confidence,
        'method': result.method,
        'debug_info': result.debug_info
    }

def extract_case_name_only(text: str, citation: str = None) -> str:
    """Extract just the case name"""
    result = extract_case_name_and_date(text, citation)
    return result['case_name']

def extract_year_only(text: str, citation: str = None) -> str:
    """Extract just the year"""
    result = extract_case_name_and_date(text, citation)
    return result['year']

# Backward compatibility aliases
extract_case_name_fixed_comprehensive = extract_case_name_only
extract_year_fixed_comprehensive = extract_year_only

def extract_case_name_triple_comprehensive(text: str, citation: str = None) -> Tuple[str, str, str]:
    """
    Backward compatible triple extraction
    Returns (case_name, date, confidence)
    """
    result = extract_case_name_and_date(text, citation)
    return (
        result['case_name'],
        result['date'], 
        str(result['confidence'])
    )

def test_streamlined_extractor():
    """Test the streamlined extractor"""
    text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2002)"""
    
    citations = [
        "200 Wn.2d 72",
        "171 Wn.2d 486", 
        "146 Wn.2d 1"
    ]
    
    logger.info("=== Streamlined Extractor Test ===")
    
    for citation in citations:
        logger.info(f"\nTesting: {citation}")
        result = extract_case_name_and_date(text, citation)
        
        logger.info(f"  Case Name: {result['case_name']}")
        logger.info(f"  Year: {result['year']}")
        logger.info(f"  Method: {result['method']}")
        logger.info(f"  Confidence: {result['confidence']:.2f}")
        
        if result['case_name'] != "N/A" and result['year'] != "N/A":
            logger.info("  ✅ SUCCESS")
        else:
            logger.error("  ❌ PARTIAL/FAILED")

if __name__ == "__main__":
    test_streamlined_extractor()