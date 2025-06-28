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
def extract_case_name_from_text(text: str, citation: str, context_window: int = 500, canonical_name: str = None) -> str:
    """
    Extract case name from text around the citation.
    Returns cleaned/validated result.
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
def extract_case_name_hinted(text: str, citation: str, canonical_name: str = None, api_key: str = None) -> str:
    """
    Extract hinted case name using canonical name as reference.
    Returns cleaned/validated result.
    """
    try:
        from src.extract_case_name import extract_case_name_hinted as hinted_func
        hinted = hinted_func(text, citation, canonical_name, api_key)
        if hinted and is_valid_case_name(hinted):
            return clean_case_name(hinted)
    except Exception as e:
        logger.warning(f"Failed to extract hinted case name: {e}")
    
    return ""

# --- Triple Extraction ---
def extract_case_name_triple(text: str, citation: str, api_key: str = None, context_window: int = 500) -> Dict[str, str]:
    """
    Extract all three pieces: canonical, extracted, and hinted case names.
    Always returns cleaned/validated results.
    
    Improved logic:
    - If no canonical name (case not verified), show extracted name as case name
    - If canonical name exists, use it to improve extracted name and make that the final case name
    - Also extracts canonical date from CourtListener API
    """
    # Get canonical name and date from CourtListener
    canonical_result = get_canonical_case_name_with_date(citation, api_key)
    canonical_name = ""
    canonical_date = ""
    
    if canonical_result:
        if isinstance(canonical_result, dict):
            canonical_name = canonical_result.get('case_name', '') or ''
            canonical_date = canonical_result.get('date', '') or ''
        else:
            canonical_name = canonical_result or ''
    
    extracted_name = extract_case_name_from_text(text, citation, context_window, canonical_name=canonical_name) or ""
    hinted_name = extract_case_name_hinted(text, citation, canonical_name, api_key) or ""

    # Debug output for extraction
    if not extracted_name:
        logger.info(f"[extract_case_name_triple] No extracted_name found for citation '{citation}' in text context.")
        extracted_name = "N/A"
    else:
        logger.info(f"[extract_case_name_triple] Extracted name for citation '{citation}': {extracted_name}")
    if not hinted_name:
        logger.info(f"[extract_case_name_triple] No hinted_name found for citation '{citation}' in text context.")
        hinted_name = "N/A"
    else:
        logger.info(f"[extract_case_name_triple] Hinted name for citation '{citation}': {hinted_name}")

    case_name = ""
    similarity_hinted = 0
    similarity_extracted = 0
    if canonical_name:
        case_name = canonical_name
    elif hinted_name != "N/A" and canonical_name:
        similarity_hinted = fuzz.ratio(hinted_name, canonical_name)
        similarity_extracted = fuzz.ratio(extracted_name, canonical_name) if extracted_name != "N/A" else 0
        if similarity_hinted > similarity_extracted:
            case_name = hinted_name
        else:
            case_name = extracted_name
    elif extracted_name != "N/A":
        case_name = extracted_name
    else:
        case_name = "N/A"

    return {
        'canonical_name': canonical_name or "N/A",
        'extracted_name': extracted_name,
        'hinted_name': hinted_name,
        'case_name': case_name,
        'canonical_date': canonical_date or "N/A"
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