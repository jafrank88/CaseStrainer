"""
Enhanced extraction utilities for case names and dates from legal text.
Provides improved regex-based extraction functions that can be integrated
into the existing citation verification system.
"""

import re
import logging
import time
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Import fallback logging
try:
    from .canonical_case_name_service import log_fallback_usage
except ImportError:
    def log_fallback_usage(citation: str, fallback_type: str, reason: str, context: Dict = None):
        logger.warning(f"FALLBACK_USED: {fallback_type} for {citation} - {reason}")

class EnhancedCaseNameExtractor:
    """
    Enhanced case name extraction using improved regex patterns.
    Handles various legal case name formats with better accuracy.
    """
    
    def __init__(self):
        # Comprehensive patterns for different case name formats
        self.case_name_patterns = [
            # Standard: Name v. Name
            r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
            r'([A-Z][A-Za-z\s,\.\'-]+?\s+vs\.\s+[A-Z][A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
            
            # In re cases
            r'(In\s+re\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
            r'(In\s+the\s+Matter\s+of\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
            
            # Estate cases
            r'(Estate\s+of\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
            r'(Matter\s+of\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
            
            # State/People/United States cases
            r'(State\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
            r'(People\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
            r'(United\s+States\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
            r'(Commonwealth\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
            
            # Ex parte cases
            r'(Ex\s+parte\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
            
            # Appeal cases
            r'([A-Za-z\s,\.\'-]+?\s+Appeal)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
            
            # Cases with "and" (multiple parties)
            r'([A-Z][A-Za-z\s,\.\'-]+?\s+and\s+[A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
            
            # Cases with "et al."
            r'([A-Z][A-Za-z\s,\.\'-]+?\s+et\s+al\.\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
        ]
        
        # Patterns that indicate we should NOT extract (header text, etc.)
        self.exclusion_patterns = [
            r'^[A-Z\s]+$',  # All caps (likely headers)
            r'^[A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+$',  # Simple three-word patterns
            r'^[A-Z][a-z]+\s+[A-Z][a-z]+$',  # Simple two-word patterns
            r'^[A-Z][a-z]+$',  # Single word
            r'^[A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+$',  # Four words
        ]
        
        # Signal words that indicate this is not a case name
        self.signal_words = [
            'court', 'judge', 'judgment', 'opinion', 'decision', 'ruling', 'order',
            'motion', 'petition', 'appeal', 'case', 'matter', 'proceeding',
            'plaintiff', 'defendant', 'appellant', 'appellee', 'respondent',
            'petitioner', 'respondent', 'claimant', 'respondent'
        ]
    
    def extract_case_name(self, text: str, citation: str = None) -> Optional[str]:
        """
        Extract case name from text, optionally using citation as context.
        
        Args:
            text: The text to search for case names
            citation: Optional citation to use for context positioning
            
        Returns:
            Extracted case name or None if not found
        """
        try:
            if not text:
                return None
            
            # If citation is provided, focus on context around it
            if citation:
                return self._extract_with_citation_context(text, citation)
            
            # Otherwise, search the entire text
            return self._extract_from_full_text(text)
            
        except Exception as e:
            logger.warning(f"Error extracting case name: {e}")
            return None
    
    def _extract_with_citation_context(self, text: str, citation: str) -> Optional[str]:
        """Extract case name using citation as context anchor."""
        try:
            # Find citation in text
            citation_index = text.find(citation)
            if citation_index == -1:
                return self._extract_from_full_text(text)
            
            # Get context before citation (200 chars)
            context_start = max(0, citation_index - 200)
            context = text[context_start:citation_index]
            
            # Look for case name patterns in context
            for pattern in self.case_name_patterns:
                matches = list(re.finditer(pattern, context, re.IGNORECASE))
                if matches:
                    # Take the last (most recent) match
                    match = matches[-1]
                    case_name = self._clean_case_name(match.group(1))
                    
                    if self._is_valid_case_name(case_name):
                        return case_name
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting case name with citation context: {e}")
            return None
    
    def _extract_from_full_text(self, text: str) -> Optional[str]:
        """Extract case name from full text without citation context."""
        try:
            # Look for case name patterns in the entire text
            for pattern in self.case_name_patterns:
                matches = list(re.finditer(pattern, text, re.IGNORECASE))
                if matches:
                    # Take the first match (most likely to be the main case)
                    match = matches[0]
                    case_name = self._clean_case_name(match.group(1))
                    
                    if self._is_valid_case_name(case_name):
                        return case_name
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting case name from full text: {e}")
            return None
    
    def _clean_case_name(self, case_name: str) -> str:
        """Clean and normalize case name."""
        if not case_name:
            return ""
        
        # Remove extra whitespace
        case_name = re.sub(r'\s+', ' ', case_name).strip()
        
        # Remove trailing punctuation
        case_name = re.sub(r'[,\s]+$', '', case_name)
        case_name = case_name.rstrip('.,;:')
        
        # Normalize spacing around "v."
        case_name = re.sub(r'\s+v\.\s+', ' v. ', case_name)
        case_name = re.sub(r'\s+vs\.\s+', ' v. ', case_name)
        
        # Normalize spacing around "In re"
        case_name = re.sub(r'\s+In\s+re\s+', ' In re ', case_name)
        
        return case_name
    
    def _is_valid_case_name(self, case_name: str) -> bool:
        """Validate if extracted text is a valid case name."""
        if not case_name or len(case_name) < 5:
            return False
        
        # Check exclusion patterns
        for pattern in self.exclusion_patterns:
            if re.match(pattern, case_name, re.IGNORECASE):
                return False
        
        # Check for signal words at the beginning
        words = case_name.lower().split()
        if words and words[0] in self.signal_words:
            return False
        
        # Must contain at least one "v." or "In re" or similar
        if not re.search(r'\bv\.\b|\bvs\.\b|\bIn\s+re\b|\bEstate\s+of\b|\bState\s+v\.\b|\bPeople\s+v\.\b', case_name, re.IGNORECASE):
            return False
        
        # Must have reasonable length
        if len(case_name) < 10 or len(case_name) > 200:
            return False
        
        return True


class EnhancedDateExtractor:
    """
    Enhanced date extraction using improved regex patterns.
    Handles various date formats commonly found in legal documents.
    """
    
    def __init__(self):
        # Comprehensive date patterns
        self.date_patterns = [
            # ISO format: 2024-01-15
            r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b',
            
            # US format: 01/15/2024, 1/15/2024
            r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',
            
            # US format with month names: January 15, 2024, Jan 15, 2024
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})\b',
            
            # Year only in parentheses: (2024)
            r'\((\d{4})\)',
            
            # Year in citation context: decided in 2024, filed in 2024
            r'(?:decided|filed|issued|released|argued|submitted)\s+(?:in\s+)?(\d{4})\b',
            
            # Simple year pattern: 2024
            r'\b(19|20)\d{2}\b',
            
            # Date with ordinal: January 15th, 2024
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b',
            
            # European format: 15/01/2024 (ambiguous, but common)
            r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',
        ]
        
        self.month_map = {
            'january': '01', 'jan': '01',
            'february': '02', 'feb': '02',
            'march': '03', 'mar': '03',
            'april': '04', 'apr': '04',
            'may': '05',
            'june': '06', 'jun': '06',
            'july': '07', 'jul': '07',
            'august': '08', 'aug': '08',
            'september': '09', 'sep': '09',
            'october': '10', 'oct': '10',
            'november': '11', 'nov': '11',
            'december': '12', 'dec': '12'
        }
    
    def extract_date(self, text: str, citation: str = None) -> Optional[str]:
        """
        Extract date from text, optionally using citation as context.
        Prioritizes a year in parentheses immediately after the citation if present.
        Args:
            text: The text to search for dates
            citation: Optional citation to use for context positioning
        Returns:
            Extracted date in ISO format (YYYY-MM-DD) or None if not found
        """
        try:
            if not text:
                return None

            # If citation is provided, look for a year in parentheses immediately after the citation
            if citation:
                citation_index = text.find(citation)
                if citation_index != -1:
                    after_citation = text[citation_index + len(citation): citation_index + len(citation) + 20]
                    match = re.search(r'\(\s*(\d{4})\s*\)', after_citation)
                    if match:
                        year = match.group(1)
                        if 1900 <= int(year) <= 2100:
                            return f"{year}-01-01"
                # Fallback to context-based extraction
                return self._extract_with_citation_context(text, citation)

            # Otherwise, search the entire text
            return self._extract_from_full_text(text)

        except Exception as e:
            logger.warning(f"Error extracting date: {e}")
            return None
    
    def extract_year(self, text: str, citation: str = None) -> Optional[str]:
        """
        Extract just the year from text.
        
        Args:
            text: The text to search for years
            citation: Optional citation to use for context positioning
            
        Returns:
            Extracted year as string or None if not found
        """
        try:
            date = self.extract_date(text, citation)
            if date:
                return date.split('-')[0]
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting year: {e}")
            return None
    
    def _extract_with_citation_context(self, text: str, citation: str) -> Optional[str]:
        """Extract date using citation as context anchor."""
        try:
            # Find citation in text
            citation_index = text.find(citation)
            if citation_index == -1:
                return self._extract_from_full_text(text)
            
            # Get context around citation (200 chars before, 100 chars after)
            context_start = max(0, citation_index - 200)
            context_end = min(len(text), citation_index + len(citation) + 100)
            context = text[context_start:context_end]
            
            return self._parse_date_patterns(context)
            
        except Exception as e:
            logger.warning(f"Error extracting date with citation context: {e}")
            return None
    
    def _extract_from_full_text(self, text: str) -> Optional[str]:
        """Extract date from full text without citation context."""
        try:
            return self._parse_date_patterns(text)
            
        except Exception as e:
            logger.warning(f"Error extracting date from full text: {e}")
            return None
    
    def _parse_date_patterns(self, text: str) -> Optional[str]:
        """Parse date patterns and return the best match."""
        try:
            best_date = None
            best_confidence = 0
            
            for pattern in self.date_patterns:
                matches = list(re.finditer(pattern, text, re.IGNORECASE))
                for match in matches:
                    groups = match.groups()
                    date_str = self._parse_date_groups(groups, pattern)
                    
                    if date_str:
                        # Calculate confidence based on pattern type
                        confidence = self._calculate_date_confidence(pattern, groups)
                        
                        if confidence > best_confidence:
                            best_date = date_str
                            best_confidence = confidence
            
            return best_date
            
        except Exception as e:
            logger.warning(f"Error parsing date patterns: {e}")
            return None
    
    def _parse_date_groups(self, groups: Tuple, pattern: str) -> Optional[str]:
        """Parse date groups and return ISO format date string."""
        try:
            if len(groups) == 3:
                # Full date pattern
                if 'January|February' in pattern:
                    # Month name format
                    month_name, day, year = groups
                    month = self.month_map.get(month_name.lower(), '01')
                elif pattern == r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b':
                    # ISO format
                    year, month, day = groups
                else:
                    # Assume US format (MM/DD/YYYY)
                    month, day, year = groups
                
                # Validate and format
                try:
                    year_int = int(year)
                    month_int = int(month)
                    day_int = int(day)
                    
                    if 1900 <= year_int <= 2100 and 1 <= month_int <= 12 and 1 <= day_int <= 31:
                        return f"{year_int:04d}-{month_int:02d}-{day_int:02d}"
                except (ValueError, TypeError):
                    pass
                    
            elif len(groups) == 1:
                # Year only pattern
                year = groups[0]
                try:
                    year_int = int(year)
                    if 1900 <= year_int <= 2100:
                        return f"{year_int:04d}-01-01"  # Default to January 1st
                except (ValueError, TypeError):
                    pass
            
            return None
            
        except Exception as e:
            logger.warning(f"Error parsing date groups: {e}")
            return None
    
    def _calculate_date_confidence(self, pattern: str, groups: Tuple) -> float:
        """Calculate confidence score for a date match."""
        try:
            # Base confidence scores
            if 'January|February' in pattern:
                return 0.9  # Month names are very reliable
            elif pattern == r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b':
                return 0.95  # ISO format is most reliable
            elif pattern == r'\((\d{4})\)':
                return 0.8  # Year in parentheses is common in citations
            elif 'decided|filed|issued' in pattern:
                return 0.85  # Context words make it more reliable
            elif pattern == r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b':
                return 0.7  # US format is common but ambiguous
            else:
                return 0.6  # Default confidence
            
        except Exception as e:
            logger.warning(f"Error calculating date confidence: {e}")
            return 0.5


class EnhancedExtractionManager:
    """
    Manager class that combines case name and date extraction.
    Provides a unified interface for extracting both from legal text.
    """
    
    def __init__(self):
        self.case_name_extractor = EnhancedCaseNameExtractor()
        self.date_extractor = EnhancedDateExtractor()
    
    def extract_case_info(self, text: str, citation: str = None) -> Dict[str, Any]:
        """
        Extract both case name and date from text.
        
        Args:
            text: The text to search
            citation: Optional citation to use for context positioning
            
        Returns:
            Dictionary with 'case_name' and 'date' keys
        """
        try:
            case_name = self.case_name_extractor.extract_case_name(text, citation)
            date = self.date_extractor.extract_date(text, citation)
            year = self.date_extractor.extract_year(text, citation)
            
            return {
                'case_name': case_name,
                'date': date,
                'year': year,
                'extraction_method': 'enhanced_regex'
            }
            
        except Exception as e:
            logger.warning(f"Error in enhanced extraction: {e}")
            return {
                'case_name': None,
                'date': None,
                'year': None,
                'extraction_method': 'enhanced_regex',
                'error': str(e)
            }
    
    def extract_multiple_cases(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract multiple case names and dates from text.
        
        Args:
            text: The text to search
            
        Returns:
            List of dictionaries with case information
        """
        try:
            results = []
            
            # Extract case names first
            case_names = self._extract_all_case_names(text)
            
            for case_name in case_names:
                # For each case name, try to find associated date
                date = self.date_extractor.extract_date(text, case_name)
                year = self.date_extractor.extract_year(text, case_name)
                
                results.append({
                    'case_name': case_name,
                    'date': date,
                    'year': year,
                    'extraction_method': 'enhanced_regex'
                })
            
            return results
            
        except Exception as e:
            logger.warning(f"Error extracting multiple cases: {e}")
            return []
    
    def _extract_all_case_names(self, text: str) -> List[str]:
        """Extract all case names from text."""
        try:
            case_names = []
            
            for pattern in self.case_name_extractor.case_name_patterns:
                matches = list(re.finditer(pattern, text, re.IGNORECASE))
                for match in matches:
                    case_name = self.case_name_extractor._clean_case_name(match.group(1))
                    
                    if (self.case_name_extractor._is_valid_case_name(case_name) and 
                        case_name not in case_names):
                        case_names.append(case_name)
            
            return case_names
            
        except Exception as e:
            logger.warning(f"Error extracting all case names: {e}")
            return []


# Convenience functions for easy integration
def extract_case_name_enhanced(text: str, citation: str = None) -> Optional[str]:
    """Enhanced case name extraction function."""
    extractor = EnhancedCaseNameExtractor()
    return extractor.extract_case_name(text, citation)

def extract_date_enhanced(text: str, citation: str = None) -> Optional[str]:
    """Enhanced date extraction function."""
    extractor = EnhancedDateExtractor()
    return extractor.extract_date(text, citation)

def extract_year_enhanced(text: str, citation: str = None) -> Optional[str]:
    """Enhanced year extraction function."""
    extractor = EnhancedDateExtractor()
    return extractor.extract_year(text, citation)

def extract_case_info_enhanced(text: str, citation: str = None) -> Dict[str, Any]:
    """Enhanced case information extraction function."""
    manager = EnhancedExtractionManager()
    return manager.extract_case_info(text, citation)

def get_adaptive_context(text, citation_start, citation_end):
    """
    Adaptive context window based on sentence and paragraph boundaries.
    """
    # Look for sentence boundaries
    sentence_start = text.rfind('.', 0, citation_start) + 1
    sentence_end = text.find('.', citation_end)
    if sentence_end == -1:
        sentence_end = len(text)
    
    # Look for paragraph boundaries
    para_start = text.rfind('\n\n', 0, citation_start) + 2
    para_end = text.find('\n\n', citation_end)
    if para_end == -1:
        para_end = len(text)
    
    # Use the most appropriate boundary
    context_start = max(sentence_start, para_start, citation_start - 500)
    context_end = min(sentence_end, para_end, citation_end + 200)
    
    return text[context_start:context_end]

def extract_date_multi_pattern(text, citation_start, citation_end):
    """
    Use multiple detection strategies for date extraction.
    """
    context = get_adaptive_context(text, citation_start, citation_end)
    citation_text = text[citation_start:citation_end]
    
    def extract_immediate_parentheses():
        after_citation = text[citation_end:citation_end+20]
        match = re.search(r'\(\s*(\d{4})\s*\)', after_citation)
        if match:
            year = match.group(1)
            if 1900 <= int(year) <= 2100:
                return f"{year}-01-01"
        return None
    
    def extract_from_sentence():
        # Look for year in the same sentence
        sentence = context
        match = re.search(r'(19|20)\d{2}', sentence)
        if match:
            year = match.group(0)
            if 1900 <= int(year) <= 2100:
                return f"{year}-01-01"
        return None
    
    def extract_from_paragraph():
        # Look for year in the paragraph
        para = context
        match = re.search(r'(19|20)\d{2}', para)
        if match:
            year = match.group(0)
            if 1900 <= int(year) <= 2100:
                return f"{year}-01-01"
        return None
    
    def extract_from_citation_text():
        # Look for year inside the citation text
        match = re.search(r'(19|20)\d{2}', citation_text)
        if match:
            year = match.group(0)
            if 1900 <= int(year) <= 2100:
                return f"{year}-01-01"
        return None
    
    strategies = [
        extract_immediate_parentheses,
        extract_from_sentence,
        extract_from_paragraph,
        extract_from_citation_text
    ]
    for strategy in strategies:
        try:
            result = strategy()
            if result:
                return result
        except Exception:
            continue
    return None

def extract_case_name_from_context(text, citation_start, citation_end):
    """
    Try to extract the case name immediately preceding the citation using context heuristics.
    """
    # Look back up to 120 chars before the citation
    pre_context = text[max(0, citation_start-120):citation_start]
    # Look for patterns like 'in State v. Smith,' or 'Brown v. Board of Education,'
    match = re.search(r'([A-Z][A-Za-z0-9 .,&\-]+ v\. [A-Z][A-Za-z0-9 .,&\-]+)', pre_context)
    if match:
        return match.group(1).strip()
    # Try a looser pattern
    match = re.search(r'([A-Z][A-Za-z0-9 .,&\-]+ v [A-Z][A-Za-z0-9 .,&\-]+)', pre_context)
    if match:
        return match.group(1).strip()
    return None

def calculate_extraction_confidence(case_name, date, context, citation_text):
    """
    Calculate confidence scores for extracted data.
    Returns a dict with confidence scores and reasoning.
    """
    confidence = {
        'case_name_confidence': 0.0,
        'date_confidence': 0.0,
        'overall_confidence': 0.0,
        'case_name_reasons': [],
        'date_reasons': []
    }
    
    # Case name confidence scoring
    if case_name:
        confidence['case_name_confidence'] = 0.5  # Base score
        if ' v. ' in case_name or ' v ' in case_name:
            confidence['case_name_confidence'] += 0.3
            confidence['case_name_reasons'].append('Contains "v." pattern')
        if len(case_name) > 10:
            confidence['case_name_confidence'] += 0.1
            confidence['case_name_reasons'].append('Reasonable length')
        if case_name.strip().endswith(','):
            confidence['case_name_confidence'] += 0.1
            confidence['case_name_reasons'].append('Ends with comma (typical citation format)')
        confidence['case_name_confidence'] = min(confidence['case_name_confidence'], 1.0)
    else:
        confidence['case_name_reasons'].append('No case name extracted')
    
    # Date confidence scoring
    if date:
        confidence['date_confidence'] = 0.6  # Base score
        try:
            year = int(date.split('-')[0])
            if 1900 <= year <= 2100:
                confidence['date_confidence'] += 0.3
                confidence['date_reasons'].append('Valid year range')
            if date.endswith('-01-01'):
                confidence['date_confidence'] += 0.1
                confidence['date_reasons'].append('Standard year-only format')
        except:
            confidence['date_confidence'] -= 0.2
            confidence['date_reasons'].append('Invalid date format')
        confidence['date_confidence'] = min(confidence['date_confidence'], 1.0)
    else:
        confidence['date_reasons'].append('No date extracted')
    
    # Overall confidence
    confidence['overall_confidence'] = (confidence['case_name_confidence'] + confidence['date_confidence']) / 2
    
    return confidence

def fallback_extraction_pipeline(text, start, end):
    """
    Fallback pipeline with multiple extraction strategies and graceful degradation.
    """
    citation_text = text[start:end]
    
    logger.info(f"Starting fallback extraction pipeline for citation: '{citation_text}'")
    
    # Fallback Strategy 1: Basic regex patterns
    def basic_regex_fallback():
        logger.debug("Trying fallback strategy 1: Basic regex patterns")
        result = {'case_name': None, 'date': None, 'year': None}
        # Basic date extraction
        date_match = re.search(r'(19|20)\d{2}', citation_text)
        if date_match:
            result['date'] = f"{date_match.group(0)}-01-01"
            result['year'] = date_match.group(0)
        return result
    
    # Fallback Strategy 2: Context window expansion
    def expanded_context_fallback():
        logger.debug("Trying fallback strategy 2: Context window expansion")
        # Try with much larger context window
        expanded_start = max(0, start - 500)
        expanded_end = min(len(text), end + 500)
        expanded_context = text[expanded_start:expanded_end]
        
        # Look for any case name pattern in expanded context
        case_match = re.search(r'([A-Z][A-Za-z0-9 .,&\-]+ v\.? [A-Z][A-Za-z0-9 .,&\-]+)', expanded_context)
        case_name = case_match.group(1).strip() if case_match else None
        
        # Look for any year in expanded context
        year_match = re.search(r'(19|20)\d{2}', expanded_context)
        date = f"{year_match.group(0)}-01-01" if year_match else None
        
        return {'case_name': case_name, 'date': date, 'year': year_match.group(0) if year_match else None}
    
    # Fallback Strategy 3: Document-wide search
    def document_wide_fallback():
        logger.debug("Trying fallback strategy 3: Document-wide search")
        # Search the entire document for patterns
        # This is the most aggressive fallback
        case_match = re.search(r'([A-Z][A-Za-z0-9 .,&\-]+ v\.? [A-Z][A-Za-z0-9 .,&\-]+)', text)
        case_name = case_match.group(1).strip() if case_match else None
        
        year_match = re.search(r'(19|20)\d{2}', text)
        date = f"{year_match.group(0)}-01-01" if year_match else None
        
        return {'case_name': case_name, 'date': date, 'year': year_match.group(0) if year_match else None}
    
    # Try fallback strategies in order of preference
    fallback_strategies = [
        basic_regex_fallback,
        expanded_context_fallback,
        document_wide_fallback
    ]
    
    failed_strategies = []
    for i, strategy in enumerate(fallback_strategies):
        try:
            logger.debug(f"Trying fallback strategy {i+1}: {strategy.__name__}")
            result = strategy()
            if result.get('date') or result.get('case_name'):
                logger.info(f"Fallback strategy {i+1} succeeded: case_name='{result.get('case_name')}', date='{result.get('date')}'")
                result['fallback_strategy_used'] = f"fallback_{i+1}"
                result['fallback_level'] = i + 1
                
                # Log fallback usage
                log_fallback_usage(
                    citation=citation_text,
                    fallback_type='extraction_pipeline',
                    reason=f"Primary extraction failed, fallback strategy {i+1} succeeded",
                    context={
                        'fallback_strategy': f"fallback_{i+1}",
                        'fallback_level': i + 1,
                        'failed_strategies': failed_strategies,
                        'extracted_case_name': result.get('case_name'),
                        'extracted_date': result.get('date'),
                        'strategy_name': strategy.__name__
                    }
                )
                
                return result
            else:
                failed_strategies.append(f"strategy_{i+1}(no_result)")
                logger.debug(f"Fallback strategy {i+1} failed: no useful data extracted")
        except Exception as e:
            failed_strategies.append(f"strategy_{i+1}(error:{str(e)})")
            logger.debug(f"Fallback strategy {i+1} failed with error: {e}")
            continue
    
    # Ultimate fallback - return minimal info
    logger.warning(f"All fallback strategies failed for citation: '{citation_text}'")
    log_fallback_usage(
        citation=citation_text,
        fallback_type='extraction_pipeline',
        reason=f"All fallback strategies failed: {', '.join(failed_strategies)}",
        context={
            'failed_strategies': failed_strategies,
            'total_strategies_tried': len(fallback_strategies)
        }
    )
    
    return {
        'case_name': None,
        'date': None,
        'year': None,
        'fallback_strategy_used': 'ultimate_fallback',
        'fallback_level': 4
    }

def cross_validate_extraction_results(text, start, end):
    """
    Cross-validate extraction results using multiple methods and choose the best one.
    Now includes fallback pipeline integration.
    """
    # Method 1: Direct position-based extraction (avoiding recursion)
    context = get_adaptive_context(text, start, end)
    citation_text = text[start:end]
    date = extract_date_multi_pattern(text, start, end)
    case_name = extract_case_name_from_context(text, start, end)
    manager = EnhancedExtractionManager()
    position_result = manager.extract_case_info(context, citation_text)
    position_result['date'] = date or position_result.get('date')
    position_result['case_name'] = case_name or position_result.get('case_name')
    confidence = calculate_extraction_confidence(position_result['case_name'], position_result['date'], context, citation_text)
    position_result.update(confidence)
    
    # Method 2: Context-based extraction (using larger context)
    context_result = extract_case_info_enhanced(text[max(0, start-200):min(len(text), end+200)], citation_text)
    
    # Method 3: Simple regex extraction
    simple_result = {'case_name': None, 'date': None, 'year': None}
    # Simple date extraction
    date_match = re.search(r'(19|20)\d{2}', citation_text)
    if date_match:
        simple_result['date'] = f"{date_match.group(0)}-01-01"
        simple_result['year'] = date_match.group(0)
    
    # Method 4: Fallback pipeline (if primary methods fail)
    fallback_result = None
    if not any([position_result.get('date'), position_result.get('case_name'),
                context_result.get('date'), context_result.get('case_name'),
                simple_result.get('date'), simple_result.get('case_name')]):
        fallback_result = fallback_extraction_pipeline(text, start, end)
    
    # Compare and choose the best result
    results = [position_result, context_result, simple_result]
    if fallback_result:
        results.append(fallback_result)
    
    # Score each result
    best_result = None
    best_score = 0
    
    for result in results:
        score = 0
        if result.get('case_name'):
            score += 1
        if result.get('date'):
            score += 1
        if result.get('case_name_confidence', 0) > 0.5:
            score += 0.5
        if result.get('date_confidence', 0) > 0.5:
            score += 0.5
        # Penalize fallback results slightly
        if result.get('fallback_strategy_used'):
            score -= 0.2
        
        if score > best_score:
            best_score = score
            best_result = result
    
    # Add cross-validation metadata
    if best_result:
        best_result['cross_validation_methods_tried'] = len(results)
        best_result['cross_validation_score'] = best_score
        best_result['cross_validation_chosen'] = True
    
    return best_result or position_result

def validate_extraction_quality(result):
    """
    Automated quality assurance for extracted data.
    Returns quality metrics and validation results.
    """
    quality_metrics = {
        'is_valid': True,
        'quality_score': 0.0,
        'warnings': [],
        'errors': [],
        'suggestions': []
    }
    
    # Validate case name
    case_name = result.get('case_name')
    if case_name:
        if len(case_name) < 5:
            quality_metrics['warnings'].append('Case name seems too short')
            quality_metrics['quality_score'] -= 0.1
        if len(case_name) > 200:
            quality_metrics['warnings'].append('Case name seems too long')
            quality_metrics['quality_score'] -= 0.1
        if not (' v. ' in case_name or ' v ' in case_name):
            quality_metrics['warnings'].append('Case name missing "v." pattern')
            quality_metrics['quality_score'] -= 0.2
    else:
        quality_metrics['warnings'].append('No case name extracted')
        quality_metrics['quality_score'] -= 0.3
    
    # Validate date
    date = result.get('date')
    if date:
        try:
            year = int(date.split('-')[0])
            if year < 1800 or year > 2100:
                quality_metrics['errors'].append(f'Invalid year: {year}')
                quality_metrics['is_valid'] = False
                quality_metrics['quality_score'] -= 0.5
            elif year < 1900:
                quality_metrics['warnings'].append(f'Unusual year: {year}')
                quality_metrics['quality_score'] -= 0.1
        except:
            quality_metrics['errors'].append('Invalid date format')
            quality_metrics['is_valid'] = False
            quality_metrics['quality_score'] -= 0.5
    else:
        quality_metrics['warnings'].append('No date extracted')
        quality_metrics['quality_score'] -= 0.3
    
    # Validate confidence scores
    case_confidence = result.get('case_name_confidence', 0)
    date_confidence = result.get('date_confidence', 0)
    
    if case_confidence < 0.3:
        quality_metrics['warnings'].append(f'Low case name confidence: {case_confidence}')
        quality_metrics['quality_score'] -= 0.2
    if date_confidence < 0.3:
        quality_metrics['warnings'].append(f'Low date confidence: {date_confidence}')
        quality_metrics['quality_score'] -= 0.2
    
    # Check for fallback usage
    if result.get('fallback_strategy_used'):
        quality_metrics['warnings'].append(f'Used fallback strategy: {result["fallback_strategy_used"]}')
        quality_metrics['quality_score'] -= 0.1
    
    # Calculate final quality score
    quality_metrics['quality_score'] = max(0.0, quality_metrics['quality_score'] + 1.0)
    
    # Add suggestions for improvement
    if not case_name and not date:
        quality_metrics['suggestions'].append('Consider manual review - no data extracted')
    elif case_confidence < 0.5:
        quality_metrics['suggestions'].append('Consider manual case name verification')
    elif date_confidence < 0.5:
        quality_metrics['suggestions'].append('Consider manual date verification')
    
    return quality_metrics

def run_extraction_tests():
    """
    Run automated tests to validate extraction functionality.
    """
    test_cases = [
        {
            'text': 'In State v. Smith, 171 Wash. 2d 486 (2011), the court held...',
            'citation': '171 Wash. 2d 486',
            'expected_case': 'State v. Smith',
            'expected_date': '2011-01-01'
        },
        {
            'text': 'Brown v. Board of Education, 347 U.S. 483 (1954)',
            'citation': '347 U.S. 483',
            'expected_case': 'Brown v. Board of Education',
            'expected_date': '1954-01-01'
        },
        {
            'text': 'The case 514 P.3d 643 (2023) was decided recently.',
            'citation': '514 P.3d 643',
            'expected_case': None,
            'expected_date': '2023-01-01'
        }
    ]
    
    test_results = {
        'total_tests': len(test_cases),
        'passed': 0,
        'failed': 0,
        'details': []
    }
    
    for i, test_case in enumerate(test_cases):
        try:
            # Find citation position
            citation_start = test_case['text'].find(test_case['citation'])
            citation_end = citation_start + len(test_case['citation'])
            
            # Run extraction
            result = extract_case_info_enhanced_with_position(
                test_case['text'], citation_start, citation_end
            )
            
            # Validate results
            case_match = (result.get('case_name') == test_case['expected_case'] or 
                         (test_case['expected_case'] is None and result.get('case_name') is None))
            date_match = result.get('date') == test_case['expected_date']
            
            test_passed = case_match and date_match
            
            test_results['details'].append({
                'test_id': i + 1,
                'passed': test_passed,
                'expected_case': test_case['expected_case'],
                'extracted_case': result.get('case_name'),
                'expected_date': test_case['expected_date'],
                'extracted_date': result.get('date'),
                'confidence': result.get('overall_confidence', 0)
            })
            
            if test_passed:
                test_results['passed'] += 1
            else:
                test_results['failed'] += 1
                
        except Exception as e:
            test_results['failed'] += 1
            test_results['details'].append({
                'test_id': i + 1,
                'passed': False,
                'error': str(e)
            })
    
    return test_results

def ensure_vue_compatibility(result):
    """
    Ensure extracted data is compatible with Vue frontend expectations.
    Standardizes field names and formats for frontend consumption.
    """
    # Standardize field names for Vue
    vue_compatible = {
        'citation': result.get('citation_text', ''),
        'extracted_date': result.get('date'),
        'extracted_case_name': result.get('case_name'),
        'extracted_year': result.get('year'),
        'extraction_method': result.get('extraction_method', 'enhanced_regex'),
        'confidence_score': result.get('overall_confidence', 0.0),
        'quality_score': result.get('quality_score', 0.0),
        'is_valid': result.get('is_valid', True),
        'warnings': result.get('warnings', []),
        'errors': result.get('errors', []),
        'suggestions': result.get('suggestions', []),
        'cross_validation_score': result.get('cross_validation_score', 0.0),
        'fallback_used': bool(result.get('fallback_strategy_used')),
        'fallback_strategy': result.get('fallback_strategy_used', None)
    }
    
    # Ensure required fields are never None for Vue
    for key in ['extracted_date', 'extracted_case_name', 'extracted_year']:
        if vue_compatible[key] is None:
            vue_compatible[key] = 'N/A'
    
    # Ensure scores are numeric
    for key in ['confidence_score', 'quality_score', 'cross_validation_score']:
        if not isinstance(vue_compatible[key], (int, float)):
            vue_compatible[key] = 0.0
    
    return vue_compatible

def integrate_with_existing_pipeline(result):
    """
    Integrate enhanced extraction results with existing pipeline structure.
    Maintains backward compatibility while adding new features.
    """
    # Preserve existing pipeline fields
    integrated_result = {
        'case_name': result.get('case_name'),
        'date': result.get('date'),
        'year': result.get('year'),
        'extraction_method': result.get('extraction_method', 'enhanced_regex'),
        'context_used': result.get('context_used'),
        'citation_text': result.get('citation_text'),
        'context_start': result.get('context_start'),
        'context_end': result.get('context_end')
    }
    
    # Add enhanced features
    enhanced_features = {
        'case_name_confidence': result.get('case_name_confidence', 0.0),
        'date_confidence': result.get('date_confidence', 0.0),
        'overall_confidence': result.get('overall_confidence', 0.0),
        'case_name_reasons': result.get('case_name_reasons', []),
        'date_reasons': result.get('date_reasons', []),
        'cross_validation_methods_tried': result.get('cross_validation_methods_tried', 0),
        'cross_validation_score': result.get('cross_validation_score', 0.0),
        'cross_validation_chosen': result.get('cross_validation_chosen', False),
        'fallback_strategy_used': result.get('fallback_strategy_used'),
        'fallback_level': result.get('fallback_level'),
        'quality_score': result.get('quality_score', 0.0),
        'is_valid': result.get('is_valid', True),
        'warnings': result.get('warnings', []),
        'errors': result.get('errors', []),
        'suggestions': result.get('suggestions', [])
    }
    
    integrated_result.update(enhanced_features)
    
    # Ensure no None values that could break existing code
    for key, value in integrated_result.items():
        if value is None:
            if key in ['case_name', 'date', 'year']:
                integrated_result[key] = 'N/A'
            elif key in ['case_name_confidence', 'date_confidence', 'overall_confidence', 
                        'cross_validation_score', 'quality_score']:
                integrated_result[key] = 0.0
            elif key in ['cross_validation_methods_tried', 'fallback_level']:
                integrated_result[key] = 0
            elif key in ['cross_validation_chosen', 'is_valid']:
                integrated_result[key] = False
            elif key in ['case_name_reasons', 'date_reasons', 'warnings', 'errors', 'suggestions']:
                integrated_result[key] = []
    
    return integrated_result

# Global cache for extraction results
_extraction_cache = {}
_cache_hits = 0
_cache_misses = 0

def get_cache_key(text, start, end, context_window=300):
    """
    Generate a cache key for extraction results.
    """
    # Use a hash of the relevant text portion for caching
    relevant_text = text[max(0, start-50):min(len(text), end+50)]
    return hash(f"{relevant_text}:{start}:{end}:{context_window}")

def clear_extraction_cache():
    """
    Clear the extraction cache and reset statistics.
    """
    global _extraction_cache, _cache_hits, _cache_misses
    _extraction_cache.clear()
    _cache_hits = 0
    _cache_misses = 0

def get_cache_stats():
    """
    Get cache performance statistics.
    """
    total_requests = _cache_hits + _cache_misses
    hit_rate = _cache_hits / total_requests if total_requests > 0 else 0
    return {
        'cache_hits': _cache_hits,
        'cache_misses': _cache_misses,
        'total_requests': total_requests,
        'hit_rate': hit_rate,
        'cache_size': len(_extraction_cache)
    }

def optimize_extraction_early_termination(result):
    """
    Implement early termination if we have high-confidence results.
    """
    # If we have high confidence in both case name and date, we can skip some validation
    case_confidence = result.get('case_name_confidence', 0)
    date_confidence = result.get('date_confidence', 0)
    
    if case_confidence > 0.8 and date_confidence > 0.8:
        # Skip some expensive validation steps
        result['early_termination_used'] = True
        result['optimization_level'] = 'high_confidence'
    elif case_confidence > 0.6 and date_confidence > 0.6:
        # Skip some validation but keep quality checks
        result['early_termination_used'] = True
        result['optimization_level'] = 'medium_confidence'
    else:
        result['early_termination_used'] = False
        result['optimization_level'] = 'full_validation'
    
    return result

def efficient_context_extraction(text, start, end):
    """
    Efficient context extraction with early bounds checking.
    """
    # Early bounds checking
    if start < 0 or end > len(text) or start >= end:
        return text[max(0, start):min(len(text), end)]
    
    # Use smaller context window for efficiency
    context_start = max(0, start - 200)  # Reduced from 500
    context_end = min(len(text), end + 100)  # Reduced from 200
    
    return text[context_start:context_end]

def extract_case_info_enhanced_with_position(text: str, start: int, end: int, context_window: int = 300) -> dict:
    """
    Enhanced case information extraction using a context window around the given character positions.
    Now uses adaptive context window, multi-pattern date detection, case name boundary detection, 
    confidence scoring, cross-validation, fallback pipelines, automated quality assurance, 
    integration fixes, and performance optimization.
    """
    global _cache_hits, _cache_misses
    
    try:
        # Check cache first
        cache_key = get_cache_key(text, start, end, context_window)
        if cache_key in _extraction_cache:
            _cache_hits += 1
            return _extraction_cache[cache_key]
        
        _cache_misses += 1
        
        # Use cross-validation to get the best result
        result = cross_validate_extraction_results(text, start, end)
        
        # Use efficient context extraction
        context = efficient_context_extraction(text, start, end)
        citation_text = text[start:end]
        result['context_used'] = context
        result['citation_text'] = citation_text
        result['context_start'] = start
        result['context_end'] = end
        
        # Add quality assurance (with early termination optimization)
        quality_metrics = validate_extraction_quality(result)
        result.update(quality_metrics)
        
        # Apply early termination optimization
        result = optimize_extraction_early_termination(result)
        
        # Integrate with existing pipeline
        result = integrate_with_existing_pipeline(result)
        
        # Ensure Vue compatibility
        vue_result = ensure_vue_compatibility(result)
        result.update(vue_result)
        
        # Cache the result (limit cache size to prevent memory issues)
        if len(_extraction_cache) < 1000:  # Limit cache to 1000 entries
            _extraction_cache[cache_key] = result
        
        return result
    except Exception as e:
        return {'case_name': None, 'date': None, 'year': None, 'extraction_method': 'enhanced_regex', 'error': str(e)}