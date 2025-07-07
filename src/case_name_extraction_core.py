from typing import Dict, List, Optional
import re
import difflib
import logging
from rapidfuzz import fuzz
import string

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Utility imports from canonical module ---
from src.extract_case_name import clean_case_name, is_valid_case_name, expand_abbreviations
from src.extract_case_name import extract_case_name_hinted

# --- Canonical Name ---
def get_canonical_case_name(citation: str, api_key: str = None) -> Optional[str]:
    """
    Get the canonical (official) case name from external APIs.
    Tries CourtListener, then Google Scholar.
    """
    try:
        from src.extract_case_name import get_canonical_case_name_from_courtlistener
        canonical = get_canonical_case_name_from_courtlistener(citation, api_key)
        if canonical:
            # If it's a dict, extract the 'case_name' field
            if isinstance(canonical, dict):
                return canonical.get('case_name', '') or ''
            # If it's a string, return as is
            if isinstance(canonical, str):
                return canonical
    except Exception as e:
        logger.warning(f"Failed to get canonical name from CourtListener: {e}")
    
    try:
        from src.extract_case_name import get_canonical_case_name_from_google_scholar
        canonical = get_canonical_case_name_from_google_scholar(citation, api_key)
        if canonical:
            if isinstance(canonical, dict):
                return canonical.get('case_name', '') or ''
            if isinstance(canonical, str):
                return canonical
    except Exception as e:
        logger.warning(f"Failed to get canonical name from Google Scholar: {e}")
    
    return ''

# --- Extracted Name ---
def extract_case_name_from_text(text: str, citation: str, context_window: int = 100, canonical_name: str = None) -> str:
    """
    Extract case name from text around the citation.
    Returns cleaned/validated result.
    Uses narrow 100-character context window by default.
    """
    try:
        from src.extract_case_name import extract_case_name_from_text as extract_func
        extracted = extract_func(text, citation, context_window, canonical_name=canonical_name)
        if extracted and is_valid_case_name(extracted):
            return clean_case_name(extracted)
    except Exception as e:
        logger.warning(f"Failed to extract case name from text: {e}")
    
    return ""

# --- Hinted Name ---
#def extract_case_name_hinted(text: str, citation: str, canonical_name: str = None, api_key: str = None) -> str:
#    """
#    Extract hinted case name using canonical name as reference.
#    Returns cleaned/validated result.
#    """
#    try:
#        from src.extract_case_name import extract_case_name_hinted as hinted_func
#        hinted = hinted_func(text, citation, canonical_name, api_key)
#        if hinted and is_valid_case_name(hinted):
#            return clean_case_name(hinted)
#    except Exception as e:
#        logger.warning(f"Failed to extract hinted case name: {e}")
#    return ""

# --- Triple Extraction ---
def extract_year_from_line(line: str) -> str:
    """
    Extracts a 4-digit year in parentheses from a line, e.g., (2020)
    This is a simple fallback method
    """
    match = re.search(r'\((\d{4})\)', line)
    if match:
        return match.group(1)
    return ""

def extract_year_after_last_citation(line: str) -> str:
    """
    Extract year that appears after the last citation or page number in a line.
    Handles patterns like:
    - name, citation, year
    - name, citation, page, year  
    - name, citation, page, citation, year
    - name, citation, citation, year (parallel citations)
    - name, citation, page, citation, page, year
    etc.
    
    Args:
        line: The line containing citations and year
        
    Returns:
        The year as a string, or empty string if not found
    """
    if not line:
        return ""
    
    # Citation patterns to find
    citation_patterns = [
        r'\d+\s+[A-Z][a-z]*\.?\d*\s+\d+',  # 123 Wn.2d 456, 123 P.3d 789
        r'\d+\s+[A-Z]\.[a-z]*\.?\d*\s+\d+',  # 123 U.S. 456
        r'\d+\s+[A-Z][a-z]+\d+\s+\d+',  # 123 Wash2d 456
        r'\d+\s+[A-Z][a-z]+\s+\d+',  # 123 Wash 456
    ]
    
    # Page number patterns (pinpoint citations)
    page_patterns = [
        r',\s*\d+',  # , 459
        r'at\s+\d+',  # at 459
    ]
    
    # Find all matches and their positions
    all_matches = []
    
    # Find citations
    for pattern in citation_patterns:
        for match in re.finditer(pattern, line):
            all_matches.append((match.end(), match.group(), 'citation'))
    
    # Find page numbers
    for pattern in page_patterns:
        for match in re.finditer(pattern, line):
            all_matches.append((match.end(), match.group(), 'page'))
    
    # Sort by position (end of match)
    all_matches.sort(key=lambda x: x[0])
    
    if not all_matches:
        # No citations found, fall back to simple year extraction
        return extract_year_from_line(line)
    
    # Get the position after the last citation/page
    last_position = all_matches[-1][0]
    
    # Look for year in parentheses after the last citation/page
    remaining_text = line[last_position:]
    year_match = re.search(r'\((\d{4})\)', remaining_text)
    
    if year_match:
        return year_match.group(1)
    
    # If no year in parentheses, look for any 4-digit year
    year_match = re.search(r'\b(19|20)\d{2}\b', remaining_text)
    if year_match:
        return year_match.group(0)
    
    return ""

def extract_case_name_triple(text: str, citation: str, api_key: str = None, context_window: int = 100) -> dict:
    """
    Extract canonical, extracted, and hinted case names, plus canonical and extracted dates.
    Returns canonical_name, extracted_name, hinted_name, case_name, canonical_date, and extracted_date.
    Uses narrow 100-character context window by default.
    """
    canonical_result = get_canonical_case_name_with_date(citation, api_key)
    canonical_name = ""
    canonical_date = ""
    if canonical_result:
        if isinstance(canonical_result, dict):
            canonical_name = canonical_result.get('case_name', '') or ''
            canonical_date = canonical_result.get('date', '') or ''
        else:
            canonical_name = canonical_result or ''
    
    extracted_name = extract_case_name_from_text(text, citation, canonical_name=canonical_name) or ""
    
    # Extract hinted name using canonical name as hint
    hinted_name = ""
    if canonical_name:
        try:
            hinted_name = extract_case_name_hinted(text, citation, canonical_name, api_key) or ""
        except Exception as e:
            logger.warning(f"Failed to extract hinted case name: {e}")
    
    # Determine the best case name to use
    case_name = ""
    if canonical_name and canonical_name != "N/A":
        case_name = canonical_name
    elif extracted_name and extracted_name != "N/A":
        case_name = extracted_name
    elif hinted_name and hinted_name != "N/A":
        case_name = hinted_name
    else:
        case_name = "N/A"
    
    # Try to extract a year from the line containing the citation
    extracted_date = ""
    for line in text.splitlines():
        if citation in line:
            # Use the new robust year extraction function
            extracted_date = extract_year_after_last_citation(line)
            if extracted_date:
                break
    
    return {
        'canonical_name': canonical_name or "N/A",
        'extracted_name': extracted_name or "N/A",
        'hinted_name': hinted_name or "N/A",
        'case_name': case_name,
        'canonical_date': canonical_date or "N/A",
        'extracted_date': extracted_date or "N/A"
    }

def get_canonical_case_name_with_date(citation: str, api_key: str = None) -> Optional[dict]:
    """
    Get the canonical (official) case name and date from external APIs.
    Tries CourtListener first (which provides both name and date), then Google Scholar.
    """
    try:
        from src.extract_case_name import get_canonical_case_name_from_courtlistener
        canonical = get_canonical_case_name_from_courtlistener(citation, api_key)
        if canonical:
            # CourtListener returns dict with 'case_name' and 'date' fields
            if isinstance(canonical, dict):
                return canonical
            # If it's a string, return as case_name with no date
            if isinstance(canonical, str):
                return {'case_name': canonical, 'date': ''}
    except Exception as e:
        logger.warning(f"Failed to get canonical name from CourtListener: {e}")
    
    try:
        from src.extract_case_name import get_canonical_case_name_from_google_scholar
        canonical = get_canonical_case_name_from_google_scholar(citation, api_key)
        if canonical:
            if isinstance(canonical, dict):
                return canonical
            if isinstance(canonical, str):
                return {'case_name': canonical, 'date': ''}  # Google Scholar doesn't provide dates
    except Exception as e:
        logger.warning(f"Failed to get canonical name from Google Scholar: {e}")
    
    return None 