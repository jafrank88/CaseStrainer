"""
Enhanced Case Name Extraction Core
Provides contamination-free extraction of case names and dates from document text.
"""

import re
import logging
from typing import Dict, Optional, Any, List, Tuple
from datetime import datetime
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig

logger = logging.getLogger("case_name_extraction")

class DateExtractor:
    """
    Enhanced Date Extractor - Consolidated from across the codebase.
    
    This class consolidates the best date extraction functionality from:
    - src/standalone_citation_parser.py (DateExtractor class)
    - src/unified_citation_processor_v2.py (_extract_date_from_context)
    - src/enhanced_extraction_utils.py (extract_date_enhanced)
    - src/unified_citation_processor.py (DateExtractor class)
    
    Provides comprehensive date extraction with multiple strategies and formats.
    """
    
    def __init__(self):
        # Comprehensive date patterns from standalone_citation_parser.py
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
            
            # Additional patterns for legal context
            r'(?:opinion|decision|ruling)\s+(?:of|in)\s+(\d{4})\b',
            r'(?:case|matter)\s+(?:decided|filed)\s+(?:in\s+)?(\d{4})\b',
            r'(?:court|judge)\s+(?:decided|ruled)\s+(?:in\s+)?(\d{4})\b',
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
    
    def extract_date_from_context(self, text: str, citation_start: int, citation_end: int, context_window: int = 300) -> Optional[str]:
        """
        Extract date from context around citation position.
        
        Args:
            text: Full document text
            citation_start: Start position of citation in text
            citation_end: End position of citation in text
            context_window: Number of characters to look around citation
            
        Returns:
            Extracted date in ISO format (YYYY-MM-DD) or None if not found
        """
        try:
            # Extract context around citation
            context_start = max(0, citation_start - context_window)
            context_end = min(len(text), citation_end + context_window)
            context = text[context_start:context_end]
            
            # Try each date pattern
            for pattern_str in self.date_patterns:
                try:
                    pattern = re.compile(pattern_str, re.IGNORECASE)
                    matches = pattern.finditer(context)
                    
                    # Find the date closest to the citation
                    best_date = None
                    best_distance = float('inf')
                    
                    for match in matches:
                        date_str = self._parse_date_match(match, pattern_str)
                        if date_str:
                            # Calculate distance from citation
                            match_start = context_start + match.start()
                            distance = abs(match_start - citation_start)
                            
                            if distance < best_distance:
                                best_distance = distance
                                best_date = date_str
                    
                    if best_date:
                        return best_date
                        
                except Exception as e:
                    logger.debug(f"Error with date pattern {pattern_str}: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting date from context: {e}")
            return None
    
    def extract_date_from_citation(self, text: str, citation: str) -> Optional[str]:
        """
        Extract date using citation as context anchor.
        
        Args:
            text: Full document text
            citation: Citation text to use as anchor
            
        Returns:
            Extracted date in ISO format (YYYY-MM-DD) or None if not found
        """
        try:
            # Find citation in text
            citation_index = text.find(citation)
            if citation_index == -1:
                return self.extract_date_from_full_text(text)
            
            # Look for year in parentheses immediately after citation
            after_citation = text[citation_index + len(citation): citation_index + len(citation) + 20]
            match = re.search(r'\(\s*(\d{4})\s*\)', after_citation)
            if match:
                year = match.group(1)
                if 1900 <= int(year) <= 2100:
                    return f"{year}-01-01"
            
            # Fallback to context-based extraction
            return self.extract_date_from_context(text, citation_index, citation_index + len(citation))
            
        except Exception as e:
            logger.warning(f"Error extracting date from citation: {e}")
            return None
    
    def extract_date_from_full_text(self, text: str) -> Optional[str]:
        """
        Extract date from full text without citation context.
        
        Args:
            text: Full document text
            
        Returns:
            Extracted date in ISO format (YYYY-MM-DD) or None if not found
        """
        try:
            best_date = None
            best_confidence = 0
            
            for pattern_str in self.date_patterns:
                try:
                    pattern = re.compile(pattern_str, re.IGNORECASE)
                    matches = pattern.finditer(text)
                    
                    for match in matches:
                        date_str = self._parse_date_match(match, pattern_str)
                        if date_str:
                            confidence = self._calculate_date_confidence(pattern_str, match.groups())
                            if confidence > best_confidence:
                                best_date = date_str
                                best_confidence = confidence
                                
                except Exception as e:
                    logger.debug(f"Error with date pattern {pattern_str}: {e}")
                    continue
            
            return best_date
            
        except Exception as e:
            logger.warning(f"Error extracting date from full text: {e}")
            return None
    
    def extract_year_only(self, text: str, citation: str = None) -> Optional[str]:
        """
        Extract just the year from text.
        
        Args:
            text: Text to search for years
            citation: Optional citation to use for context positioning
            
        Returns:
            Extracted year as string or None if not found
        """
        try:
            if citation:
                date = self.extract_date_from_citation(text, citation)
            else:
                date = self.extract_date_from_full_text(text)
            
            if date:
                return date.split('-')[0]
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting year: {e}")
            return None
    
    def _parse_date_match(self, match, pattern_str: str) -> Optional[str]:
        """Parse date match and return ISO format date string."""
        try:
            groups = match.groups()
            
            if len(groups) == 3:
                # Full date pattern
                if 'January|February' in pattern_str:
                    # Month name format
                    month_name, day, year = groups
                    month = self.month_map.get(month_name.lower(), '01')
                elif pattern_str == r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b':
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
            logger.debug(f"Error parsing date match: {e}")
            return None
    
    def _calculate_date_confidence(self, pattern_str: str, groups: tuple) -> float:
        """Calculate confidence score for a date match."""
        confidence = 0.0
        
        # Base confidence by pattern type
        if 'January|February' in pattern_str:
            confidence += 0.9  # Full month name is very reliable
        elif pattern_str == r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b':
            confidence += 0.8  # ISO format is reliable
        elif pattern_str == r'\((\d{4})\)':
            confidence += 0.7  # Year in parentheses is common in citations
        elif 'decided|filed|issued' in pattern_str:
            confidence += 0.6  # Legal context words
        else:
            confidence += 0.5  # Basic pattern
        
        # Boost confidence for recent years (more likely to be relevant)
        if len(groups) >= 1:
            try:
                year = int(groups[0])
                if 2000 <= year <= datetime.now().year:
                    confidence += 0.1
            except (ValueError, TypeError):
                pass
        
        return min(confidence, 1.0)
    
    def validate_date(self, date_str: str) -> bool:
        """
        Validate if a date string is reasonable.
        
        Args:
            date_str: Date string to validate
            
        Returns:
            True if date is valid and reasonable
        """
        try:
            if not date_str:
                return False
            
            # Handle year-only format
            if re.match(r'^\d{4}$', date_str):
                year = int(date_str)
                return 1800 <= year <= datetime.now().year + 1
            
            # Handle ISO format
            if '-' in date_str:
                parts = date_str.split('-')
                if len(parts) >= 3:
                    year = int(parts[0])
                    month = int(parts[1])
                    day = int(parts[2])
                    return (1800 <= year <= datetime.now().year + 1 and 
                            1 <= month <= 12 and 
                            1 <= day <= 31)
                elif len(parts) >= 1:
                    year = int(parts[0])
                    return 1800 <= year <= datetime.now().year + 1
            
            return False
            
        except (ValueError, TypeError):
            return False
    
    def normalize_date_format(self, date_str: str) -> str:
        """
        Normalize date format to ISO standard.
        
        Args:
            date_str: Date string to normalize
            
        Returns:
            Normalized date string in ISO format
        """
        try:
            if not date_str:
                return "N/A"
            
            # If it's already in ISO format, return as is
            if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                return date_str
            
            # If it's just a year, convert to ISO format
            if re.match(r'^\d{4}$', date_str):
                year = int(date_str)
                if 1800 <= year <= datetime.now().year + 1:
                    return f"{year:04d}-01-01"
            
            # Try to parse other formats
            date = self.extract_date_from_full_text(date_str)
            if date:
                return date
            
            return "N/A"
            
        except Exception as e:
            logger.debug(f"Error normalizing date format: {e}")
            return "N/A"

# Create a global instance for easy access
date_extractor = DateExtractor()

def extract_case_name_fixed_comprehensive(text: str, citation: str) -> str:
    """
    Enhanced case name extraction using UnifiedCitationProcessorV2.
    Replaces the existing extract_case_name_fixed function.
    """
    try:
        # Use UnifiedCitationProcessorV2 for extraction
        config = ProcessingConfig(
            use_eyecite=False,  # Focus on regex extraction for case names
            use_regex=True,
            extract_case_names=True,
            extract_dates=False,  # We only need case names here
            enable_clustering=False
        )
        processor = UnifiedCitationProcessorV2(config)
        
        # Process the text to find citations and extract case names
        results = processor.process_text(text)
        
        # Find the result for our specific citation
        for result in results:
            if result.citation == citation:
                return result.case_name or ''
        
        return ''
    except Exception as e:
        import logging
        logging.error(f"Error in extract_case_name_fixed_comprehensive: {e}")
        return ""

def extract_year_fixed_comprehensive(text: str, citation: str) -> str:
    """
    Enhanced year extraction using UnifiedCitationProcessorV2.
    Replaces the existing extract_year_fixed function.
    """
    try:
        # Use UnifiedCitationProcessorV2 for extraction
        config = ProcessingConfig(
            use_eyecite=False,  # Focus on regex extraction for dates
            use_regex=True,
            extract_case_names=False,  # We only need dates here
            extract_dates=True,
            enable_clustering=False
        )
        processor = UnifiedCitationProcessorV2(config)
        
        # Process the text to find citations and extract dates
        results = processor.process_text(text)
        
        # Find the result for our specific citation
        for result in results:
            if result.citation == citation:
                return result.date or ''
        
        return ''
    except Exception as e:
        import logging
        logging.error(f"Error in extract_year_fixed_comprehensive: {e}")
        return ""

def extract_case_name_triple_comprehensive(text: str, citation: str, api_key: str = None, context_window: int = 100) -> dict:
    """
    COMPREHENSIVE CASE NAME AND DATE EXTRACTION FUNCTION
    
    This is the ONLY supported extraction function for all backend processing.
    All API endpoints, document processing, and citation verification should use this function.
    
    DO NOT use other extraction functions (extract_case_name_from_text, extract_case_name_hinted, etc.)
    in production code. This ensures consistent results across all code paths.
    
    Returns:
        dict: Contains extracted_name, extracted_date, case_name, canonical_name, canonical_date
    """
    """
    FIXED VERSION: Comprehensive extraction with strict contamination prevention.
    EXTRACTION ONLY - NO API CALLS.
    """
    import logging
    logger = logging.getLogger("case_name_extraction")
    
    # Initialize results
    result = {
        'canonical_name': "N/A",
        'extracted_name': "N/A", 
        'hinted_name': "N/A",
        'case_name': "N/A",
        'canonical_date': "N/A",
        'extracted_date': "N/A",
        'case_name_confidence': 0.0,
        'case_name_method': "none",
        'debug_info': {
            'full_citation_found': None,
            'extraction_method': None,
            'parser_result': None,
            'contamination_check': 'extraction_only_no_api'
        }
    }
    
    try:
        logger.debug(f"Comprehensive extraction for citation: '{citation}'")
        
        # PRIORITY 1: Use UnifiedCitationProcessorV2 for extraction (DOCUMENT TEXT ONLY)
        config = ProcessingConfig(
            use_eyecite=False,  # Focus on regex extraction
            use_regex=True,
            extract_case_names=True,
            extract_dates=True,
            enable_clustering=False
        )
        processor = UnifiedCitationProcessorV2(config)
        
        # Process the text to find citations and extract case names/dates
        processor_results = processor.process_text(text)
        
        # Find the result for our specific citation
        citation_result = None
        for proc_result in processor_results:
            if proc_result.citation == citation:
                citation_result = proc_result
                break
        
        if citation_result:
            result['debug_info']['parser_result'] = {
                'case_name': citation_result.case_name,
                'date': citation_result.date,
                'extraction_method': 'UnifiedCitationProcessorV2'
            }
            result['debug_info']['full_citation_found'] = True
            result['debug_info']['extraction_method'] = 'UnifiedCitationProcessorV2'
            
            # Extract case name from document text only
            extracted_case_name = citation_result.case_name
            if extracted_case_name:
                result['extracted_name'] = extracted_case_name
                result['case_name'] = extracted_case_name
                result['case_name_confidence'] = 0.95
                result['case_name_method'] = "UnifiedCitationProcessorV2"
                logger.info(f"UnifiedCitationProcessorV2 found case name: '{extracted_case_name}'")
            
            # Extract date from document text only
            extracted_year = citation_result.date
            if extracted_year:
                result['extracted_date'] = extracted_year
                logger.info(f"UnifiedCitationProcessorV2 found year: '{extracted_year}'")
        
        # CRITICAL: NO CANONICAL LOOKUP IN EXTRACTION FUNCTION
        # Canonical lookup should happen separately in verification workflow
        logger.info(f"Extraction complete - canonical lookup will be done separately")
        
        # Log final results
        logger.info(f"Final extraction result for '{citation}':")
        logger.info(f"  Extracted case name: '{result['extracted_name']}'")
        logger.info(f"  Extracted date: '{result['extracted_date']}'")
        logger.info(f"  Method: '{result['case_name_method']}'")
        logger.info(f"  Contamination check: '{result['debug_info']['contamination_check']}'")
            
    except Exception as e:
        logger.error(f"Error in extract_case_name_triple_comprehensive: {e}")
        result['debug_info']['extraction_method'] = f"error: {str(e)}"
    
    return result

# Helper functions for contamination-free extraction
def extract_case_name_from_text_isolated(text: str, citation: str) -> str:
    """
    Isolates case name extraction from the full text and citation using UnifiedCitationProcessorV2.
    """
    try:
        config = ProcessingConfig(
            use_eyecite=False,
            use_regex=True,
            extract_case_names=True,
            extract_dates=False,
            enable_clustering=False
        )
        processor = UnifiedCitationProcessorV2(config)
        results = processor.process_text(text)
        
        for result in results:
            if result.citation == citation:
                return result.case_name or ''
        return ''
    except Exception as e:
        import logging
        logging.error(f"Error in extract_case_name_from_text_isolated: {e}")
        return ""

def extract_year_from_context_isolated(text: str, citation: str) -> str:
    """
    Isolates year extraction from the full text and citation using UnifiedCitationProcessorV2.
    """
    try:
        config = ProcessingConfig(
            use_eyecite=False,
            use_regex=True,
            extract_case_names=False,
            extract_dates=True,
            enable_clustering=False
        )
        processor = UnifiedCitationProcessorV2(config)
        results = processor.process_text(text)
        
        for result in results:
            if result.citation == citation:
                return result.date or ''
        return ''
    except Exception as e:
        import logging
        logging.error(f"Error in extract_year_from_context_isolated: {e}")
        return ""

def _is_valid_case_name(name: str) -> bool:
    """
    Checks if a given name is a valid case name.
    """
    # Basic checks: not empty, not just whitespace, not "N/A"
    if not name or name.strip() == "N/A":
        return False
    # More sophisticated checks could involve regex for specific patterns
    # or a list of known valid case name formats.
    return True

def _is_valid_year(year: str) -> bool:
    """
    Checks if a given year is a valid year.
    """
    if not year or year.strip() == "N/A":
        return False
    # Basic regex for 4-digit year
    import re
    year_match = re.search(r'(\d{4})', year)
    if year_match:
        return True
    return False

def extract_case_name_triple(text, citation, api_key=None, context_window=100):
    """
    Extract case name, date, and citation from document text using enhanced patterns.
    
    Args:
        text (str): The full document text
        citation (str): The citation to search for
        api_key (str, optional): API key for external services
        context_window (int): Context window size for extraction
        
    Returns:
        dict: Dictionary with extraction results
    """
    logger = logging.getLogger("case_name_extraction")
    
    # Initialize results
    result = {
        'extracted_name': "N/A",
        'extracted_date': "N/A",
        'case_name': "N/A",
        'canonical_name': "N/A",
        'canonical_date': "N/A"
    }
    
    try:
        logger.debug(f"Extracting case name and date for citation: '{citation}'")
        
        # Use UnifiedCitationProcessorV2 for extraction
        config = ProcessingConfig(
            use_eyecite=False,
            use_regex=True,
            extract_case_names=True,
            extract_dates=True,
            enable_clustering=False
        )
        processor = UnifiedCitationProcessorV2(config)
        processor_results = processor.process_text(text)
        
        # Find the result for our specific citation
        citation_result = None
        for proc_result in processor_results:
            if proc_result.citation == citation:
                citation_result = proc_result
                break
        
        if citation_result:
            # Extract case name from document text
            extracted_case_name = citation_result.case_name
            if extracted_case_name:
                result['extracted_name'] = extracted_case_name
                result['case_name'] = extracted_case_name
                logger.info(f"Extracted case name: '{extracted_case_name}'")
            
            # Extract date from document text
            extracted_year = citation_result.date
            if extracted_year:
                result['extracted_date'] = extracted_year
                logger.info(f"Extracted year: '{extracted_year}'")
        
        # Note: Canonical lookup should be done separately in verification workflow
        logger.info(f"Extraction complete - canonical lookup will be done separately")
            
    except Exception as e:
        logger.error(f"Error in extract_case_name_triple: {e}")
    
    return result

def test_comprehensive_integration():
    """
    Test the comprehensive integration with your existing system.
    """
    text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2002)"""
    
    citations = [
        "200 Wash. 2d 72, 514 P.3d 643",
        "171 Wash. 2d 486 256 P.3d 321",
        "146 Wash. 2d 1 43 P.3d 4"
    ]
    
    print("=== COMPREHENSIVE INTEGRATION TEST ===")
    
    for citation in citations:
        print(f"\n--- Testing: {citation} ---")
        
        # Test individual functions
        case_name = extract_case_name_fixed_comprehensive(text, citation)
        year = extract_year_fixed_comprehensive(text, citation)
        
        print(f"Case Name: '{case_name}'")
        print(f"Year: '{year}'")
        
        # Test comprehensive triple function
        result = extract_case_name_triple_comprehensive(text, citation)
        
        print(f"Triple Result:")
        print(f"  case_name: '{result['case_name']}'")
        print(f"  extracted_date: '{result['extracted_date']}'")
        print(f"  method: '{result['case_name_method']}'")
        print(f"  full_citation: '{result['debug_info']['full_citation_found']}'")
        
        # Check for success
        if result['case_name'] != 'N/A' and result['extracted_date'] != 'N/A':
            print("✅ SUCCESS: Both case name and date extracted")
        elif result['case_name'] != 'N/A':
            print("⚠️  PARTIAL: Case name extracted, no date")
        elif result['extracted_date'] != 'N/A':
            print("⚠️  PARTIAL: Date extracted, no case name")
        else:
            print("❌ FAILED: No extraction")

# Usage instructions for integration:
"""
TO INTEGRATE INTO YOUR EXISTING CODE:

1. Add the CitationParser class to your codebase
2. Replace your existing extraction functions:
   - extract_case_name_fixed -> extract_case_name_fixed_comprehensive
   - extract_year_fixed -> extract_year_fixed_comprehensive  
   - extract_case_name_triple -> extract_case_name_triple_comprehensive

3. The new functions have the same signatures as your existing ones,
   so they're drop-in replacements.

4. The comprehensive parser handles:
   - Multiple citation formats (Wn.2d vs Wash.2d)
   - Pinpoint citations (486, 493)
   - Parallel citations (256 P.3d 321)
   - Complex patterns with multiple parallels
   - Various case name formats (Dep't, Department, In re, State v., etc.)

5. Your JSON will now show properly extracted case names and dates
   instead of N/A values.
"""

if __name__ == "__main__":
    test_comprehensive_integration()