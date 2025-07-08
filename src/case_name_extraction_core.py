from typing import Dict, List, Optional
import re
import difflib
import logging
from rapidfuzz import fuzz
import string

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Canonical Name ---
from src.extract_case_name import (
    get_canonical_case_name_from_courtlistener,
    get_canonical_case_name_from_google_scholar,
    extract_case_name_hinted,
    clean_case_name,
    is_valid_case_name,
    expand_abbreviations
)

def get_canonical_case_name(citation: str, api_key: str = None) -> Optional[str]:
    try:
        canonical = get_canonical_case_name_from_courtlistener(citation, api_key)
        if canonical:
            if isinstance(canonical, dict):
                return canonical.get('case_name', '') or ''
            if isinstance(canonical, str):
                return canonical
    except Exception as e:
        pass
    try:
        canonical = get_canonical_case_name_from_google_scholar(citation, api_key)
        if canonical:
            if isinstance(canonical, dict):
                return canonical.get('case_name', '') or ''
            if isinstance(canonical, str):
                return canonical
    except Exception as e:
        pass
    return ''

def extract_year_fixed(text: str, citation: str) -> str:
    citation_pos = text.find(citation)
    if citation_pos == -1:
        return ""
    after_citation = text[citation_pos + len(citation):]
    year_match = re.search(r'\s*\((\d{4})\)', after_citation)
    if year_match:
        return year_match.group(1)
    return ""

def extract_case_name_fixed(text: str, citation: str) -> str:
    citation_pos = text.find(citation)
    if citation_pos == -1:
        return ""
    before_citation = text[:citation_pos]
    before_citation = before_citation.strip()
    sentences = re.split(r'[.;]\s*', before_citation)
    if sentences:
        last_sentence = sentences[-1].strip()
        case_pattern = r'([A-Z][^,]*?\s+v\.?\s+[^,]*?)$'
        match = re.search(case_pattern, last_sentence)
        if match:
            case_name = match.group(1).strip()
            if len(case_name) > 5 and ' v' in case_name.lower():
                return case_name
    immediate_before = before_citation.split(';')[-1].strip()
    case_pattern = r'([A-Z][^,]*?\s+v\.?\s+[^,]*?)$'
    match = re.search(case_pattern, immediate_before)
    if match:
        case_name = match.group(1).strip()
        if len(case_name) > 5 and ' v' in case_name.lower():
            return case_name
    return ""

def extract_citations_and_cases_fixed(text: str) -> List[Dict[str, str]]:
    results = []
    citation_pattern = r'(\d+\s+Wn\.2d\s+\d+(?:\s*,\s*\d+)*(?:\s*,\s*\d+\s+[A-Z]\.\?[a-z]*\.?\s*(?:2d|3d)?\s+\d+)*)\s*\((\d{4})\)'
    matches = re.finditer(citation_pattern, text)
    for match in matches:
        full_citation = match.group(1) + f" ({match.group(2)})"
        citation_without_year = match.group(1)
        year = match.group(2)
        case_name = extract_case_name_fixed(text, citation_without_year)
        results.append({
            'citation': full_citation,
            'citation_without_year': citation_without_year,
            'case_name': case_name if case_name else "N/A",
            'year': year,
            'extraction_method': 'fixed_regex'
        })
    return results

# --- COMPATIBILITY WRAPPERS ---
def extract_case_name_from_text(text, citation, context_window=100, canonical_name: str = None):
    """
    Compatibility wrapper for extract_case_name_from_text.
    Now uses the improved extract_case_name_fixed function.
    """
    return extract_case_name_fixed(text, citation)

def extract_year_from_line(line: str) -> str:
    """
    Compatibility wrapper for extract_year_from_line.
    Now uses the improved extract_year_fixed function with the line as both text and citation.
    """
    # Look for year in parentheses in the line
    year_match = re.search(r'\((\d{4})\)', line)
    if year_match:
        return year_match.group(1)
    return ""

def extract_year_after_last_citation(line: str) -> str:
    """
    Compatibility wrapper for extract_year_after_last_citation.
    Now uses the improved extract_year_fixed function.
    """
    # Find the last citation pattern in the line and extract year after it
    citation_patterns = [
        r'\d+\s+[A-Z][a-z]*\.?\d*\s+\d+',  # 123 Wn.2d 456, 123 P.3d 789
        r'\d+\s+[A-Z]\.[a-z]*\.?\d*\s+\d+',  # 123 U.S. 456
        r'\d+\s+[A-Z][a-z]+\d+\s+\d+',  # 123 Wash2d 456
        r'\d+\s+[A-Z][a-z]+\s+\d+',  # 123 Wash 456
    ]
    
    last_citation_end = 0
    for pattern in citation_patterns:
        for match in re.finditer(pattern, line):
            last_citation_end = max(last_citation_end, match.end())
    
    if last_citation_end > 0:
        remaining_text = line[last_citation_end:]
        year_match = re.search(r'\((\d{4})\)', remaining_text)
        if year_match:
            return year_match.group(1)
    
    return extract_year_from_line(line)

def extract_year_near_citation(text: str, citation: str, max_tokens: int = 20) -> str:
    """
    Compatibility wrapper for extract_year_near_citation.
    Now uses the improved extract_year_fixed function.
    """
    return extract_year_fixed(text, citation)

def extract_case_name_triple(text: str, citation: str, api_key: str = None, context_window: int = 100) -> dict:
    """
    Fixed version that prioritizes extracted names from the actual document.
    Canonical names are kept separate and NOT used to replace extracted names.
    """
    import logging
    logger = logging.getLogger("case_name_extraction")
    
    # Initialize results
    result = {
        'canonical_name': "N/A",
        'extracted_name': "N/A", 
        'hinted_name': "N/A",
        'case_name': "N/A",  # This should ONLY be from the document
        'canonical_date': "N/A",
        'extracted_date': "N/A",
        'case_name_confidence': 0.0,
        'case_name_method': "none"
    }
    
    try:
        logger.debug(f"Extracting for citation: '{citation}'")
        
        # PRIORITY 1: Try fixed extraction from the actual document
        fixed_name = extract_case_name_fixed(text, citation)
        fixed_date = extract_year_fixed(text, citation)
        
        if fixed_name:
            result['extracted_name'] = fixed_name
            result['case_name'] = fixed_name  # Use what's actually in the document
            result['case_name_confidence'] = 0.9
            result['case_name_method'] = "fixed_extraction"
            logger.info(f"Fixed extraction found case name: {fixed_name}")
        
        if fixed_date:
            result['extracted_date'] = fixed_date
            logger.info(f"Fixed extraction found date: {fixed_date}")
        
        # PRIORITY 2: Try enhanced extraction if available (as fallback for document extraction)
        if result['case_name'] == "N/A":
            try:
                from src.enhanced_case_name_extraction import extract_case_name_enhanced
                match = extract_case_name_enhanced(text, citation, context_window=context_window)
                if match and hasattr(match, 'cleaned_name') and match.cleaned_name:
                    result['extracted_name'] = match.cleaned_name
                    result['case_name'] = match.cleaned_name  # Still from the document
                    result['case_name_confidence'] = getattr(match, 'confidence', 0.8)
                    result['case_name_method'] = getattr(match, 'extraction_method', "enhanced")
                    logger.info(f"Enhanced extraction found: {match.cleaned_name}")
            except (ImportError, Exception) as e:
                logger.warning(f"Enhanced extraction failed: {e}")
        
        # PRIORITY 3: Try hinted extraction (uses canonical as hint but extracts from document)
        if result['case_name'] == "N/A":
            try:
                # Get canonical name to use as a hint (but don't use it directly)
                canonical_result = get_canonical_case_name_with_date(citation, api_key)
                canonical_name = ""
                if canonical_result:
                    if isinstance(canonical_result, dict):
                        canonical_name = canonical_result.get('case_name', '') or ''
                        result['canonical_date'] = canonical_result.get('date', 'N/A') or 'N/A'
                    else:
                        canonical_name = str(canonical_result) or ''
                    result['canonical_name'] = canonical_name or 'N/A'
                
                # Use canonical as hint to find similar text in the document
                if canonical_name:
                    hinted_name = extract_case_name_hinted(text, citation, canonical_name, api_key)
                    if hinted_name:
                        result['hinted_name'] = hinted_name
                        result['case_name'] = hinted_name  # This is still from the document
                        result['case_name_confidence'] = 0.7
                        result['case_name_method'] = "hinted_from_document"
                        logger.info(f"Hinted extraction found: {hinted_name}")
                
            except Exception as e:
                logger.warning(f"Canonical lookup or hinted extraction failed: {e}")
        
        # Get canonical info separately (for reference only, not to replace extracted)
        if result['canonical_name'] == "N/A":
            try:
                canonical_result = get_canonical_case_name_with_date(citation, api_key)
                if canonical_result:
                    if isinstance(canonical_result, dict):
                        result['canonical_name'] = canonical_result.get('case_name', 'N/A') or 'N/A'
                        if result['canonical_date'] == "N/A":
                            result['canonical_date'] = canonical_result.get('date', 'N/A') or 'N/A'
                    else:
                        result['canonical_name'] = str(canonical_result) or 'N/A'
                    logger.info(f"Canonical lookup found: {result['canonical_name']}")
            except Exception as e:
                logger.warning(f"Canonical lookup failed: {e}")
        
        # Enhanced date extraction if needed
        if result['extracted_date'] == "N/A":
            try:
                from src.enhanced_date_extraction import extract_year_near_citation_enhanced
                enhanced_date = extract_year_near_citation_enhanced(text, citation, context_window=300)
                if enhanced_date:
                    result['extracted_date'] = enhanced_date
                    logger.info(f"Enhanced date extraction found: {enhanced_date}")
            except (ImportError, Exception) as e:
                logger.warning(f"Enhanced date extraction failed: {e}")
            
    except Exception as e:
        logger.error(f"Error in extract_case_name_triple: {e}")
    
    return result

def get_canonical_case_name_with_date(citation: str, api_key: str = None) -> Optional[dict]:
    import logging
    logger = logging.getLogger("case_name_extraction")
    citation_variants = _generate_citation_variants(citation)
    logger.debug(f"[get_canonical_case_name_with_date] Generated {len(citation_variants)} variants for citation: {citation}")
    for variant in citation_variants:
        try:
            canonical = get_canonical_case_name_from_courtlistener(variant, api_key)
            if canonical:
                logger.debug(f"[get_canonical_case_name_with_date] Found result with variant: {variant}")
                if isinstance(canonical, dict):
                    return canonical
                if isinstance(canonical, str):
                    return {'case_name': canonical, 'date': ''}
        except Exception as e:
            logger.debug(f"[get_canonical_case_name_with_date] CourtListener failed for variant '{variant}': {e}")
    try:
        canonical = get_canonical_case_name_from_google_scholar(citation, api_key)
        if canonical:
            if isinstance(canonical, dict):
                return canonical
            if isinstance(canonical, str):
                return {'case_name': canonical, 'date': ''}
    except Exception as e:
        logger.warning(f"Failed to get canonical name from Google Scholar: {e}")
    return None

def _generate_citation_variants(citation: str) -> List[str]:
    import re
    variants = [citation]
    try:
        from src.citation_format_utils import normalize_washington_synonyms
        from src.citation_patterns import normalize_washington_citation
        norm1 = normalize_washington_synonyms(citation)
        norm2 = normalize_washington_citation(citation)
        for form in (norm1, norm2):
            if form and form not in variants:
                variants.append(form)
    except ImportError:
        pass
    washington_variants = _generate_washington_variants(citation)
    variants.extend(washington_variants)
    generic_variants = set()
    generic_variants.add(re.sub(r"\bApp\.\b", "App", citation))
    generic_variants.add(re.sub(r"\bApp\b", "App.", citation))
    generic_variants.add(re.sub(r"\bDiv\.\b", "Div", citation))
    generic_variants.add(re.sub(r"\bDiv\b", "Div.", citation))
    generic_variants.add(re.sub(r"\bCal\.\b", "Cal", citation))
    generic_variants.add(re.sub(r"\bCal\b", "Cal.", citation))
    generic_variants.add(re.sub(r"\bN\.Y\.\b", "NY", citation))
    generic_variants.add(re.sub(r"\bNY\b", "N.Y.", citation))
    generic_variants.add(re.sub(r"\bIll\.\b", "Ill", citation))
    generic_variants.add(re.sub(r"\bIll\b", "Ill.", citation))
    generic_variants.add(re.sub(r"\bTex\.\b", "Tex", citation))
    generic_variants.add(re.sub(r"\bTex\b", "Tex.", citation))
    generic_variants.add(re.sub(r"\bPa\.\b", "Pa", citation))
    generic_variants.add(re.sub(r"\bPa\b", "Pa.", citation))
    base_citation = re.sub(r'\s+', ' ', citation).strip()
    spacing_variants = [
        base_citation,
        re.sub(r'(\d+)\s+([A-Z])', r'\1 \2', base_citation),
        re.sub(r'([A-Z])\s+(\d+)', r'\1 \2', base_citation),
        re.sub(r'(\d+)\s*([A-Z]{2,})\s*(\d+)', r'\1 \2 \3', base_citation),
    ]
    variants.extend(spacing_variants)
    reporter_variants = []
    if 'Wn.' in citation or 'Wn' in citation:
        reporter_variants.extend([
            re.sub(r'Wn\.?\s*', 'Wash. ', citation),
            re.sub(r'Wn\.?\s*', 'Washington ', citation),
            re.sub(r'Wn\.?\s*', 'Wn. ', citation),
        ])
    if 'F.' in citation or 'F.3d' in citation or 'F.2d' in citation:
        reporter_variants.extend([
            re.sub(r'F\.?\s*(\d+)d', r'F.\1d', citation),
            re.sub(r'F\.?\s*(\d+)d', r'F \1d', citation),
        ])
    if 'U.S.' in citation or 'US' in citation:
        reporter_variants.extend([
            re.sub(r'U\.?\s*S\.?', 'U.S.', citation),
            re.sub(r'U\.?\s*S\.?', 'US', citation),
        ])
    variants.extend(reporter_variants)
    variants.extend(generic_variants)
    variants = [form for form in variants if form and form.strip()]
    variants = list(dict.fromkeys(variants))
    return variants

def _generate_washington_variants(citation: str) -> List[str]:
    import re
    variants = []
    normalized_citation = citation.replace('Wn.', 'Wash.').replace('Wn ', 'Wash. ')
    washington_patterns = [
        (r'(\d+)\s+Wn\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wash. \2 \3'),
        (r'(\d+)\s+Wn\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Washington \2 \3'),
        (r'(\d+)\s+Wn\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wn. \2 \3'),
        (r'(\d+)\s+Wn\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wn \2 \3'),
        (r'(\d+)\s+Wn\.?\s*App\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wash. App. \2 \3'),
        (r'(\d+)\s+Wn\.?\s*App\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Washington App. \2 \3'),
        (r'(\d+)\s+Wn\.?\s*App\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wn. App. \2 \3'),
        (r'(\d+)\s+Wn\.?\s*2d\s+(\d+[a-z]?)\s+(\d+)', r'\1 Wash. 2d \2 \3'),
        (r'(\d+)\s+Wn\.?\s*2d\s+(\d+[a-z]?)\s+(\d+)', r'\1 Washington 2d \2 \3'),
        (r'(\d+)\s+Wash\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wn. \2 \3'),
        (r'(\d+)\s+Washington\s+(\d+[a-z]?)\s+(\d+)', r'\1 Wn. \2 \3'),
    ]
    for original, replacement in washington_patterns:
        variant = re.sub(original, replacement, citation, flags=re.IGNORECASE)
        if variant != citation:
            variants.append(variant)
        variant = re.sub(original, replacement, normalized_citation, flags=re.IGNORECASE)
        if variant != normalized_citation and variant not in variants:
            variants.append(variant)
    if normalized_citation != citation:
        variants.append(normalized_citation)
    if 'Wn.' in citation or 'Wn ' in citation:
        wash_variant = citation.replace('Wn.', 'Wash.').replace('Wn ', 'Wash. ')
        if wash_variant not in variants:
            variants.append(wash_variant)
        wash_full_variant = citation.replace('Wn.', 'Washington ').replace('Wn ', 'Washington ')
        if wash_full_variant not in variants:
            variants.append(wash_full_variant)
    return variants 