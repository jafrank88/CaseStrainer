"""
Consolidated Citation Utilities
Combines citation normalization, formatting, and validation functions from multiple files.
"""

import re
from typing import List, Dict, Any
from eyecite import get_citations
from eyecite.tokenizers import AhocorasickTokenizer


def normalize_citation(citation: str) -> str:
    """
    Normalize a legal citation for best compatibility with external APIs.
    Handles Washington, federal, regional, and international reporters, plus general cleanup.
    """
    if not citation or not isinstance(citation, str):
        return ""

    # Replace multiple spaces with a single space and trim
    normalized = re.sub(r"\s+", " ", citation.strip())

    # Washington-specific normalization
    normalized = re.sub(r"Wn\.\s*App\.", "Wash. App.", normalized)
    normalized = re.sub(r"Wn\.\s*2d", "Wash. 2d", normalized)
    normalized = re.sub(r"Wn\.\s*3d", "Wash. 3d", normalized)
    normalized = re.sub(r"Wn\.", "Wash.", normalized)

    # Standardize regional/state reporters
    normalized = re.sub(r"Cal\.\s*App\.", "Cal. App.", normalized)
    normalized = re.sub(r"Cal\.\s*Rptr\.", "Cal. Rptr.", normalized)
    normalized = re.sub(r"N\.Y\.\s*App\.", "N.Y. App.", normalized)
    normalized = re.sub(r"Tex\.\s*App\.", "Tex. App.", normalized)
    normalized = re.sub(r"Fla\.\s*App\.", "Fla. App.", normalized)
    normalized = re.sub(r"Ill\.\s*App\.", "Ill. App.", normalized)
    normalized = re.sub(r"Ohio\s*App\.", "Ohio App.", normalized)
    normalized = re.sub(r"Mich\.\s*App\.", "Mich. App.", normalized)
    normalized = re.sub(r"Pa\.\s*Super\.", "Pa. Super.", normalized)
    normalized = re.sub(r"Mass\.\s*App\.", "Mass. App.", normalized)

    # International reporters
    normalized = re.sub(r"UKSC", "UKSC", normalized)
    normalized = re.sub(r"EWCA\s+Civ", "EWCA Civ", normalized)
    normalized = re.sub(r"EWHC", "EWHC", normalized)
    normalized = re.sub(r"SCC", "SCC", normalized)
    normalized = re.sub(r"FCA", "FCA", normalized)
    normalized = re.sub(r"FC", "FC", normalized)
    normalized = re.sub(r"HCA", "HCA", normalized)

    # General cleanup
    normalized = re.sub(r"[\u2013\u2014]", "-", normalized)  # em/en dashes
    normalized = re.sub(r"[\u2018\u2019]", "'", normalized)  # smart single quotes
    normalized = re.sub(r"[\u201C\u201D]", '"', normalized)  # smart double quotes
    normalized = re.sub(r"[\u00A0]", " ", normalized)  # non-breaking spaces
    normalized = re.sub(r"\s*,\s*", ", ", normalized)  # commas
    normalized = re.sub(r"\s+v\.?\s+", " v. ", normalized)  # v.
    normalized = re.sub(r"\s+&\.?\s+", " & ", normalized)  # &
    normalized = re.sub(r"\s+vs\.?\s+", " v. ", normalized)  # vs.
    normalized = re.sub(r"\s+versus\s+", " v. ", normalized)  # versus
    normalized = re.sub(r"\(\s*", "(", normalized)  # space after (
    normalized = re.sub(r"\s*\)", ")", normalized)  # space before )
    normalized = re.sub(r"\[\s*", "[", normalized)  # space after [
    normalized = re.sub(r"\s*\]", "]", normalized)  # space before ]
    normalized = re.sub(r"\.\s*\.", "..", normalized)  # double periods
    normalized = re.sub(r"\.\s*\.\s*\.", "...", normalized)  # triple periods

    return normalized


def generate_citation_variants(citation: str) -> List[str]:
    """
    Generate all plausible variants of a citation for fallback/parallel search.
    Includes Washington-specific, normalized, and expanded forms.
    """
    variants = set()
    if not citation or not isinstance(citation, str):
        return []

    # Start with the original and normalized forms
    normalized = normalize_citation(citation)
    variants.add(citation)
    variants.add(normalized)

    # Washington-specific patterns
    washington_patterns = [
        # Standard Washington patterns (Wn. -> Wash.)
        (r'(\d+)\s+Wn\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wash. \2 \3'),
        (r'(\d+)\s+Wn\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Washington \2 \3'),
        (r'(\d+)\s+Wn\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wn. \2 \3'),
        (r'(\d+)\s+Wn\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wn \2 \3'),
        # Washington App patterns (Wn. App. -> Wash. App.)
        (r'(\d+)\s+Wn\.?\s*App\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wash. App. \2 \3'),
        (r'(\d+)\s+Wn\.?\s*App\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Washington App. \2 \3'),
        (r'(\d+)\s+Wn\.?\s*App\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wn. App. \2 \3'),
        # Washington 2d patterns (Wn. 2d -> Wash. 2d)
        (r'(\d+)\s+Wn\.?\s*2d\s+(\d+[a-z]?)\s+(\d+)', r'\1 Wash. 2d \2 \3'),
        (r'(\d+)\s+Wn\.?\s*2d\s+(\d+[a-z]?)\s+(\d+)', r'\1 Washington 2d \2 \3'),
        # Handle cases where Wn. is already in the citation
        (r'(\d+)\s+Wash\.?\s*(\d+[a-z]?)\s+(\d+)', r'\1 Wn. \2 \3'),
        (r'(\d+)\s+Washington\s+(\d+[a-z]?)\s+(\d+)', r'\1 Wn. \2 \3'),
    ]
    for original, replacement in washington_patterns:
        variant = re.sub(original, replacement, citation, flags=re.IGNORECASE)
        if variant != citation:
            variants.add(variant)
        variant = re.sub(original, replacement, normalized, flags=re.IGNORECASE)
        if variant != normalized:
            variants.add(variant)

    # Add specific Washington variants for better search
    if 'Wn.' in citation or 'Wn ' in citation:
        wash_variant = citation.replace('Wn.', 'Wash.').replace('Wn ', 'Wash. ')
        variants.add(wash_variant)
        wash_full_variant = citation.replace('Wn.', 'Washington ').replace('Wn ', 'Washington ')
        variants.add(wash_full_variant)

    return list(variants)


def apply_washington_spacing_rules(citation: str) -> str:
    """
    Apply Washington citation spacing rules according to the Washington style sheet.
    
    Rules:
    - Washington Reports: "Wn.2d" (no space between Wn. and 2d)
    - Washington Appellate Reports: "Wn. App." (space between Wn. and App.)
    
    Args:
        citation: The citation text to format
        
    Returns:
        str: The citation with proper Washington spacing
    """
    # Always ensure a space between Wash. and 2d/3d
    citation = re.sub(r'Wash\.\s*2d', 'Wash. 2d', citation, flags=re.IGNORECASE)
    citation = re.sub(r'Wash\.\s*3d', 'Wash. 3d', citation, flags=re.IGNORECASE)
    citation = re.sub(r'Wn\.\s*2d', 'Wash. 2d', citation, flags=re.IGNORECASE)
    citation = re.sub(r'Wn\.\s*3d', 'Wash. 3d', citation, flags=re.IGNORECASE)
    # Handle Washington Appellate Reports: ensure space between Wn. and App.
    citation = re.sub(r'Wn\.\s*App\.', 'Wash. App.', citation, flags=re.IGNORECASE)
    citation = re.sub(r'Wash\.\s*App\.', 'Wash. App.', citation, flags=re.IGNORECASE)
    return citation


def washington_state_to_bluebook(citation: str) -> str:
    """
    Converts Washington state court citation format to Bluebook format.
    Handles both Supreme Court (Wn.2d) and Court of Appeals (Wn. App.)
    """
    # Apply Washington spacing rules first
    citation = apply_washington_spacing_rules(citation)
    
    # Supreme Court: Wn.2d -> Wash. 2d
    citation = re.sub(r"Wn\.2d", "Wash. 2d", citation)
    # Court of Appeals: Wn. App. -> Wash. App.
    citation = re.sub(r"Wn\. App\.", "Wash. App.", citation)

    # Add court in parenthetical if not present
    # Extract year from parenthetical if present
    match = re.search(r"\((\d{4})\)", citation)
    year = match.group(1) if match else None
    # Determine court type
    if "Wash. App." in citation:
        parenthetical = "(Wash. Ct. App."
    elif "Wash. 2d" in citation:
        parenthetical = "(Wash."
    else:
        parenthetical = None

    # Replace parenthetical with Bluebook style
    if parenthetical and year:
        citation = re.sub(r"\(\d{4}\)", f"{parenthetical} {year})", citation)
    elif parenthetical:
        citation = citation.rstrip(")") + f" {parenthetical})"

    return citation


def normalize_illinois_oklahoma(citation: str) -> str:
    """
    For Illinois and Oklahoma, remove paragraph markers (¶ 12, ¶ 15, etc) for deduplication.
    """
    # Remove paragraph markers (¶ 12, ¶ 15, etc)
    citation = re.sub(r",?\s*¶+\s*\d+", "", citation)
    return citation


def normalize_washington_synonyms(citation: str) -> str:
    """
    Normalize Washington synonyms for deduplication (Wn.2d <-> Wash. 2d, Wn. App. <-> Wash. App.)
    """
    # Apply Washington spacing rules first
    citation = apply_washington_spacing_rules(citation)
    
    citation = citation.replace("Wn.2d", "Wash. 2d")
    citation = citation.replace("Wn. App.", "Wash. App.")
    return citation


def normalize_for_deduplication(citation: str, state: str) -> str:
    """
    Normalize a citation string for deduplication, handling state-specific quirks.
    """
    state = state.lower()
    if state == "washington":
        return normalize_washington_synonyms(citation)
    elif state in ("illinois", "oklahoma"):
        return normalize_illinois_oklahoma(citation)
    else:
        return citation


def validate_citation(citation_text: str) -> Dict[str, Any]:
    """
    Validate a citation using eyecite.
    
    Args:
        citation_text: The citation text to validate
        
    Returns:
        Dict containing validation results and metadata
    """
    # Initialize the tokenizer
    tokenizer = AhocorasickTokenizer()

    # Get citations
    citations = get_citations(citation_text, tokenizer=tokenizer)

    # Process the results
    if citations:
        citation = citations[0]  # Get the first citation
        return {
            "valid": True,
            "citation_text": citation.matched_text(),
            "corrected_citation": (
                citation.corrected_citation()
                if hasattr(citation, "corrected_citation")
                else None
            ),
            "citation_type": type(citation).__name__,
            "metadata": {
                "reporter": getattr(citation, "reporter", None),
                "volume": getattr(citation, "volume", None),
                "page": getattr(citation, "page", None),
                "year": getattr(citation, "year", None),
                "court": getattr(citation, "court", None),
            },
        }
    else:
        return {"valid": False, "error": "No valid citation found"}


def extract_date_multi_pattern(text, citation_start, citation_end):
    """
    Use multiple detection strategies for date extraction.
    Extracted from enhanced_extraction_utils.py - provides comprehensive date extraction
    with multiple fallback strategies.
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


def get_adaptive_context(text, citation_start, citation_end):
    """
    Get adaptive context around citation for extraction.
    Extracted from enhanced_extraction_utils.py.
    """
    # Get context before and after citation
    context_before = text[max(0, citation_start-200):citation_start]
    context_after = text[citation_end:min(len(text), citation_end+200)]
    
    # Combine context
    context = context_before + " " + context_after
    
    # Clean up context
    context = re.sub(r'\s+', ' ', context).strip()
    
    return context


def calculate_extraction_confidence(case_name, date, context, citation_text):
    """
    Calculate confidence scores for extracted data.
    Returns a dict with confidence scores and reasoning.
    Extracted from enhanced_extraction_utils.py.
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
    Extracted from enhanced_extraction_utils.py.
    """
    import logging
    logger = logging.getLogger(__name__)
    
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
            result = strategy()
            if result and (result.get('case_name') or result.get('date')):
                logger.info(f"Fallback strategy {i+1} succeeded")
                return result
            else:
                failed_strategies.append(f"Strategy {i+1}: No results")
        except Exception as e:
            failed_strategies.append(f"Strategy {i+1}: {str(e)}")
            logger.warning(f"Fallback strategy {i+1} failed: {e}")
    
    logger.warning(f"All fallback strategies failed: {failed_strategies}")
    return {'case_name': None, 'date': None, 'year': None}


def cross_validate_extraction_results(text, start, end):
    """
    Cross-validate extraction results using multiple methods.
    Extracted from enhanced_extraction_utils.py.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    citation_text = text[start:end]
    logger.info(f"Cross-validating extraction results for: '{citation_text}'")
    
    # Method 1: Multi-pattern date extraction
    date_multi = extract_date_multi_pattern(text, start, end)
    
    # Method 2: Fallback pipeline
    fallback_result = fallback_extraction_pipeline(text, start, end)
    
    # Method 3: Basic regex extraction
    basic_date = None
    date_match = re.search(r'(19|20)\d{2}', citation_text)
    if date_match:
        basic_date = f"{date_match.group(0)}-01-01"
    
    # Compare results
    results = {
        'multi_pattern_date': date_multi,
        'fallback_date': fallback_result.get('date'),
        'basic_date': basic_date,
        'fallback_case_name': fallback_result.get('case_name'),
        'consensus_date': None,
        'confidence': 0.0
    }
    
    # Find consensus date
    dates = [d for d in [date_multi, fallback_result.get('date'), basic_date] if d]
    if dates:
        # If all dates are the same, high confidence
        if len(set(dates)) == 1:
            results['consensus_date'] = dates[0]
            results['confidence'] = 0.9
        # If dates are similar (same year), medium confidence
        elif len(set([d.split('-')[0] for d in dates])) == 1:
            results['consensus_date'] = dates[0]
            results['confidence'] = 0.7
        # If dates differ, use the most common or first
        else:
            results['consensus_date'] = dates[0]
            results['confidence'] = 0.3
    
    logger.info(f"Cross-validation results: {results}")
    return results


def validate_extraction_quality(result):
    """
    Validate the quality of extraction results.
    Extracted from enhanced_extraction_utils.py.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    quality_score = 0.0
    issues = []
    warnings = []
    
    # Check if we have any results
    if not result:
        issues.append("No extraction results provided")
        return {'quality_score': 0.0, 'issues': issues, 'warnings': warnings}
    
    # Check case name quality
    case_name = result.get('case_name')
    if case_name:
        if len(case_name) < 5:
            issues.append("Case name too short")
            quality_score -= 0.2
        elif len(case_name) > 200:
            warnings.append("Case name very long")
            quality_score -= 0.1
        
        if ' v. ' not in case_name and ' v ' not in case_name:
            warnings.append("Case name missing 'v.' pattern")
            quality_score -= 0.1
    else:
        issues.append("No case name extracted")
        quality_score -= 0.3
    
    # Check date quality
    date = result.get('date')
    if date:
        try:
            year = int(date.split('-')[0])
            if year < 1800 or year > 2100:
                issues.append("Date year out of reasonable range")
                quality_score -= 0.3
            else:
                quality_score += 0.3
        except:
            issues.append("Invalid date format")
            quality_score -= 0.3
    else:
        issues.append("No date extracted")
        quality_score -= 0.2
    
    # Check citation text quality
    citation_text = result.get('citation_text', '')
    if citation_text:
        if len(citation_text) < 5:
            issues.append("Citation text too short")
            quality_score -= 0.1
        elif len(citation_text) > 100:
            warnings.append("Citation text very long")
            quality_score -= 0.05
    else:
        issues.append("No citation text provided")
        quality_score -= 0.1
    
    # Normalize quality score
    quality_score = max(0.0, min(1.0, quality_score + 0.5))  # Base score of 0.5
    
    logger.info(f"Quality validation: score={quality_score}, issues={issues}, warnings={warnings}")
    
    return {
        'quality_score': quality_score,
        'issues': issues,
        'warnings': warnings,
        'is_acceptable': quality_score >= 0.5
    }


# Cache management functions
_extraction_cache = {}

def get_cache_key(text, start, end, context_window=300):
    """
    Generate cache key for extraction results.
    Extracted from enhanced_extraction_utils.py.
    """
    import hashlib
    # Create a hash of the relevant text portion
    text_portion = text[max(0, start-context_window):min(len(text), end+context_window)]
    key_data = f"{start}:{end}:{text_portion}"
    return hashlib.md5(key_data.encode()).hexdigest()


def clear_extraction_cache():
    """
    Clear the extraction cache.
    Extracted from enhanced_extraction_utils.py.
    """
    global _extraction_cache
    _extraction_cache.clear()


def get_cache_stats():
    """
    Get cache statistics.
    Extracted from enhanced_extraction_utils.py.
    """
    global _extraction_cache
    return {
        'cache_size': len(_extraction_cache),
        'cache_keys': list(_extraction_cache.keys())
    }


def optimize_extraction_early_termination(result):
    """
    Optimize extraction by implementing early termination.
    Extracted from enhanced_extraction_utils.py.
    """
    if not result:
        return result
    
    # If we have high confidence results, we can terminate early
    case_name = result.get('case_name')
    date = result.get('date')
    
    if case_name and date:
        # Check if we have good quality results
        quality = validate_extraction_quality(result)
        if quality['quality_score'] >= 0.8:
            # High quality results, no need for further processing
            result['early_termination'] = True
            result['termination_reason'] = 'High quality results achieved'
    
    return result


def efficient_context_extraction(text, start, end):
    """
    Efficient context extraction with optimized boundaries.
    Extracted from enhanced_extraction_utils.py.
    """
    # Optimize context window based on text characteristics
    base_window = 200
    
    # Adjust window based on text length
    if len(text) < 1000:
        window = min(base_window, len(text) // 4)
    elif len(text) > 10000:
        window = base_window * 2
    else:
        window = base_window
    
    # Extract context
    context_start = max(0, start - window)
    context_end = min(len(text), end + window)
    
    context = text[context_start:context_end]
    
    # Clean context
    context = re.sub(r'\s+', ' ', context).strip()
    
    return {
        'context': context,
        'context_start': context_start,
        'context_end': context_end,
        'window_size': window
    }


def extract_case_info_enhanced_with_position(text: str, start: int, end: int, context_window: int = 300) -> dict:
    """
    Enhanced case info extraction with position awareness.
    Extracted from enhanced_extraction_utils.py.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    citation_text = text[start:end]
    logger.info(f"Enhanced extraction with position for: '{citation_text}'")
    
    # Get efficient context
    context_info = efficient_context_extraction(text, start, end)
    context = context_info['context']
    
    # Try multiple extraction methods
    results = {}
    
    # Method 1: Multi-pattern date extraction
    results['date_multi'] = extract_date_multi_pattern(text, start, end)
    
    # Method 2: Fallback pipeline
    fallback_result = fallback_extraction_pipeline(text, start, end)
    results.update(fallback_result)
    
    # Method 3: Cross-validation
    cross_validation = cross_validate_extraction_results(text, start, end)
    results.update(cross_validation)
    
    # Method 4: Quality validation
    quality = validate_extraction_quality(results)
    results['quality'] = quality
    
    # Method 5: Early termination optimization
    results = optimize_extraction_early_termination(results)
    
    # Add metadata
    results['citation_text'] = citation_text
    results['start_position'] = start
    results['end_position'] = end
    results['context_info'] = context_info
    results['extraction_method'] = 'enhanced_with_position'
    
    logger.info(f"Enhanced extraction completed: {results}")
    return results


# Example test cases
if __name__ == "__main__":
    print("=== Citation Normalization ===")
    test_citation = "123 Wn. 2d 456 (2015)"
    normalized = normalize_citation(test_citation)
    print(f"Original: {test_citation}")
    print(f"Normalized: {normalized}")
    
    print("\n=== Citation Validation ===")
    validation_result = validate_citation("National Cable & Telecommunications Assn. v. Brand X Internet Services, 545 U. S. 967, 982")
    print(f"Valid: {validation_result['valid']}")
    if validation_result['valid']:
        print(f"Matched text: {validation_result['citation_text']}")
        print(f"Citation type: {validation_result['citation_type']}")
    
    print("\n=== Washington Spacing Rules ===")
    spacing_examples = [
        "123 Wn. 2d 456",
        "123 Wn.2d 456", 
        "123 Wash. 2d 456",
        "123 Wash.2d 456",
        "45 Wn.App. 678",
        "45 Wn. App. 678",
    ]
    for ex in spacing_examples:
        formatted = apply_washington_spacing_rules(ex)
        print(f"Original: {ex} -> Formatted: {formatted}") 

# OCR Correction and Confidence Scoring Classes (extracted from unified_citation_processor.py)

class OCRCorrector:
    """
    Handles OCR error correction for citation text.
    Extracted from unified_citation_processor.py.
    """
    
    def __init__(self):
        self.ocr_corrections = self._init_ocr_corrections()
        self.enabled = True
    
    def _init_ocr_corrections(self) -> Dict[str, str]:
        """Initialize common OCR error corrections."""
        return {
            # Common OCR errors in citations
            '0': 'O',  # Zero to O
            'O': '0',  # O to Zero (context-dependent)
            '1': 'l',  # One to lowercase L
            'l': '1',  # Lowercase L to One (context-dependent)
            '5': 'S',  # Five to S
            'S': '5',  # S to Five (context-dependent)
            '8': 'B',  # Eight to B
            'B': '8',  # B to Eight (context-dependent)
            '6': 'G',  # Six to G
            'G': '6',  # G to Six (context-dependent)
            'rn': 'm',  # rn to m
            'm': 'rn',  # m to rn (context-dependent)
            'cl': 'd',  # cl to d
            'd': 'cl',  # d to cl (context-dependent)
            'vv': 'w',  # vv to w
            'w': 'vv',  # w to vv (context-dependent)
            
            # Common reporter abbreviations
            'Wn.2d': 'Wn.2d',  # Ensure correct format
            'Wn.App.': 'Wn. App.',  # Fix spacing
            'Wn.App': 'Wn. App.',  # Fix spacing and period
            'P.3d': 'P.3d',  # Ensure correct format
            'P.2d': 'P.2d',  # Ensure correct format
            'U.S.': 'U.S.',  # Ensure correct format
            'F.3d': 'F.3d',  # Ensure correct format
            'F.2d': 'F.2d',  # Ensure correct format
            
            # Common case name OCR errors
            'v.': 'v.',  # Ensure correct format
            'v': 'v.',  # Add period
            'vs.': 'v.',  # Fix vs to v
            'versus': 'v.',  # Fix versus to v
        }
    
    def correct_text(self, text: str) -> str:
        """Apply OCR corrections to text."""
        if not self.enabled:
            return text
        
        corrected_text = text
        
        # Apply common OCR corrections
        for error, correction in self.ocr_corrections.items():
            corrected_text = corrected_text.replace(error, correction)
        
        # Apply context-specific corrections
        corrected_text = self._apply_context_corrections(corrected_text)
        
        return corrected_text
    
    def _apply_context_corrections(self, text: str) -> str:
        """Apply context-specific OCR corrections."""
        # Fix common citation patterns
        
        # Fix volume numbers (should be digits)
        text = re.sub(r'\b([A-Z])\s+([A-Za-z\.]+)\s+(\d+)\b', r'\1 \2 \3', text)
        
        # Fix page numbers (should be digits)
        text = re.sub(r'\b(\d+)\s+([A-Za-z\.]+)\s+([A-Z])\b', r'\1 \2 \3', text)
        
        # Fix reporter abbreviations
        text = re.sub(r'\bWn\.\s*2d\b', 'Wn.2d', text)
        text = re.sub(r'\bWn\.\s*App\.\b', 'Wn. App.', text)
        text = re.sub(r'\bP\.\s*3d\b', 'P.3d', text)
        text = re.sub(r'\bP\.\s*2d\b', 'P.2d', text)
        text = re.sub(r'\bU\.\s*S\.\b', 'U.S.', text)
        text = re.sub(r'\bF\.\s*3d\b', 'F.3d', text)
        text = re.sub(r'\bF\.\s*2d\b', 'F.2d', text)
        
        return text
    
    def enable(self):
        """Enable OCR correction."""
        self.enabled = True
    
    def disable(self):
        """Disable OCR correction."""
        self.enabled = False


class ConfidenceScorer:
    """
    Handles confidence scoring for citation extraction and verification.
    Extracted from unified_citation_processor.py.
    """
    
    def __init__(self):
        self.scoring_weights = {
            'pattern_match': 0.3,
            'context_quality': 0.2,
            'verification_result': 0.3,
            'case_name_match': 0.1,
            'date_consistency': 0.1
        }
    
    def calculate_citation_confidence(self, citation: Dict[str, Any], context: str = "") -> float:
        """Calculate confidence score for a citation."""
        confidence = 0.0
        
        # Pattern match confidence
        pattern_confidence = self._calculate_pattern_confidence(citation)
        confidence += pattern_confidence * self.scoring_weights['pattern_match']
        
        # Context quality confidence
        context_confidence = self._calculate_context_confidence(context)
        confidence += context_confidence * self.scoring_weights['context_quality']
        
        # Verification result confidence
        verification_confidence = self._calculate_verification_confidence(citation)
        confidence += verification_confidence * self.scoring_weights['verification_result']
        
        # Case name match confidence
        case_name_confidence = self._calculate_case_name_confidence(citation)
        confidence += case_name_confidence * self.scoring_weights['case_name_match']
        
        # Date consistency confidence
        date_confidence = self._calculate_date_confidence(citation)
        confidence += date_confidence * self.scoring_weights['date_consistency']
        
        return min(confidence, 1.0)  # Cap at 1.0
    
    def _calculate_pattern_confidence(self, citation: Dict[str, Any]) -> float:
        """Calculate confidence based on pattern match quality."""
        citation_str = citation.get('citation', '')
        method = citation.get('method', '')
        pattern = citation.get('pattern', '')
        
        # Base confidence by method
        method_scores = {
            'enhanced_processor': 0.9,
            'eyecite': 0.8,
            'cluster_detection': 0.7,
            'semantic_clustering': 0.6,
            'regex': 0.5
        }
        
        base_confidence = method_scores.get(method, 0.5)
        
        # Adjust based on pattern quality
        if 'complete' in pattern or 'enhanced' in pattern:
            base_confidence += 0.1
        elif 'alt' in pattern:
            base_confidence += 0.05
        
        # Adjust based on citation format
        if re.match(r'^\d+\s+[A-Za-z\.]+\s+\d+$', citation_str):
            base_confidence += 0.1  # Well-formed citation
        elif ',' in citation_str:
            base_confidence -= 0.1  # Complex citation
        
        return min(base_confidence, 1.0)
    
    def _calculate_context_confidence(self, context: str) -> float:
        """Calculate confidence based on context quality."""
        if not context:
            return 0.0
        
        confidence = 0.5  # Base confidence
        
        # Context length
        if len(context) > 200:
            confidence += 0.2
        elif len(context) > 100:
            confidence += 0.1
        
        # Presence of case name patterns
        case_name_patterns = [
            r'[A-Z][A-Za-z\s]+v\.\s+[A-Z][A-Za-z\s]+',
            r'[A-Z][A-Za-z\s]+vs\.\s+[A-Z][A-Za-z\s]+',
            r'[A-Z][A-Za-z\s]+versus\s+[A-Z][A-Za-z\s]+'
        ]
        
        for pattern in case_name_patterns:
            if re.search(pattern, context):
                confidence += 0.2
                break
        
        # Presence of date patterns
        date_patterns = [
            r'\(\d{4}\)',
            r'\d{4}',
            r'\b\d{1,2}/\d{1,2}/\d{4}\b'
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, context):
                confidence += 0.1
                break
        
        return min(confidence, 1.0)
    
    def _calculate_verification_confidence(self, citation: Dict[str, Any]) -> float:
        """Calculate confidence based on verification results."""
        verified = citation.get('verified', False)
        source = citation.get('source', '')
        url = citation.get('url')
        
        if verified:
            confidence = 0.8  # Base confidence for verified citations
            
            # Adjust based on source quality
            source_scores = {
                'CourtListener': 0.9,
                'Landmark Cases': 0.8,
                'Database': 0.7,
                'Fuzzy Match': 0.6,
                'Unknown': 0.5
            }
            
            confidence = source_scores.get(source, 0.7)
            
            # Bonus for having URL
            if url:
                confidence += 0.1
            
            return min(confidence, 1.0)
        else:
            return 0.2  # Low confidence for unverified citations
    
    def _calculate_case_name_confidence(self, citation: Dict[str, Any]) -> float:
        """Calculate confidence based on case name quality."""
        case_name = citation.get('case_name', '')
        extracted_case_name = citation.get('extracted_case_name', '')
        
        if not case_name and not extracted_case_name:
            return 0.0
        
        confidence = 0.5  # Base confidence
        
        # Check if we have both canonical and extracted names
        if case_name and extracted_case_name:
            # Calculate similarity
            similarity = self._calculate_name_similarity(case_name, extracted_case_name)
            confidence += similarity * 0.3
            
            # Bonus for exact match
            if case_name.lower() == extracted_case_name.lower():
                confidence += 0.2
        
        # Check case name format
        if case_name:
            if ' v. ' in case_name or ' vs. ' in case_name:
                confidence += 0.1
            if len(case_name) > 10:
                confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _calculate_date_confidence(self, citation: Dict[str, Any]) -> float:
        """Calculate confidence based on date consistency."""
        extracted_date = citation.get('extracted_date')
        canonical_date = citation.get('canonical_date')
        year = citation.get('year')
        
        if not extracted_date and not canonical_date and not year:
            return 0.0
        
        confidence = 0.5  # Base confidence
        
        # Check if dates are consistent
        if extracted_date and canonical_date:
            if extracted_date == canonical_date:
                confidence += 0.3
            elif extracted_date.split('-')[0] == canonical_date.split('-')[0]:
                confidence += 0.2  # Same year
        
        # Check if year is reasonable
        if year:
            try:
                year_int = int(year)
                if 1800 <= year_int <= 2100:
                    confidence += 0.2
            except:
                pass
        
        return min(confidence, 1.0)
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two case names."""
        if not name1 or not name2:
            return 0.0
        
        # Simple similarity calculation
        name1_clean = re.sub(r'[^\w\s]', '', name1.lower())
        name2_clean = re.sub(r'[^\w\s]', '', name2.lower())
        
        words1 = set(name1_clean.split())
        words2 = set(name2_clean.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0


# Utility functions for date handling (extracted from unified_citation_processor.py)

def safe_set_extracted_date(citation, new_date, source="unknown"):
    """
    Safely set extracted date with source tracking.
    Extracted from unified_citation_processor.py.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if not citation:
        return
    
    try:
        # Validate date format
        if new_date and isinstance(new_date, str):
            # Check if it's a valid date format
            if re.match(r'^\d{4}-\d{2}-\d{2}$', new_date):
                citation['extracted_date'] = new_date
                citation['date_source'] = source
                logger.debug(f"Set extracted date: {new_date} (source: {source})")
            elif re.match(r'^\d{4}$', new_date):
                citation['extracted_date'] = f"{new_date}-01-01"
                citation['date_source'] = source
                logger.debug(f"Set extracted date: {new_date}-01-01 (source: {source})")
            else:
                logger.warning(f"Invalid date format: {new_date}")
    except Exception as e:
        logger.error(f"Error setting extracted date: {e}")


def validate_citation_dates(citation):
    """
    Validate dates in citation for consistency.
    Extracted from unified_citation_processor.py.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if not citation:
        return
    
    try:
        extracted_date = citation.get('extracted_date')
        canonical_date = citation.get('canonical_date')
        year = citation.get('year')
        
        # Check for date consistency
        if extracted_date and canonical_date:
            if extracted_date != canonical_date:
                logger.warning(f"Date mismatch: extracted={extracted_date}, canonical={canonical_date}")
        
        # Validate year format
        if year:
            try:
                year_int = int(year)
                if year_int < 1800 or year_int > 2100:
                    logger.warning(f"Year out of reasonable range: {year}")
            except:
                logger.warning(f"Invalid year format: {year}")
        
        # Validate date formats
        for date_field in ['extracted_date', 'canonical_date']:
            date_value = citation.get(date_field)
            if date_value and isinstance(date_value, str):
                if not re.match(r'^\d{4}(-\d{2}-\d{2})?$', date_value):
                    logger.warning(f"Invalid date format in {date_field}: {date_value}")
    
    except Exception as e:
        logger.error(f"Error validating citation dates: {e}")


def extract_case_name_with_better_boundaries(context, citation_position):
    """
    Extract case name with improved boundary detection.
    Extracted from unified_citation_processor.py.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Look for case name patterns before the citation
        pre_context = context[:citation_position]
        
        # Multiple patterns to try
        patterns = [
            r'([A-Z][A-Za-z0-9\s,\.&\'-]+?\s+v\.\s+[A-Za-z0-9\s,\.&\'-]+?)(?=\s*[,;]|\s*$)',
            r'([A-Z][A-Za-z0-9\s,\.&\'-]+?\s+vs\.\s+[A-Za-z0-9\s,\.&\'-]+?)(?=\s*[,;]|\s*$)',
            r'(In\s+re\s+[A-Za-z0-9\s,\.&\'-]+?)(?=\s*[,;]|\s*$)',
            r'(State\s+v\.\s+[A-Za-z0-9\s,\.&\'-]+?)(?=\s*[,;]|\s*$)',
        ]
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, pre_context, re.IGNORECASE))
            if matches:
                # Take the last (most recent) match
                match = matches[-1]
                case_name = match.group(1).strip()
                
                # Clean up the case name
                case_name = re.sub(r'\s+', ' ', case_name)
                case_name = case_name.rstrip('.,;:')
                
                if len(case_name) > 5:
                    logger.debug(f"Extracted case name: {case_name}")
                    return case_name
        
        return None
    
    except Exception as e:
        logger.error(f"Error extracting case name with better boundaries: {e}")
        return None


def group_parallel_citations(citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Group parallel citations together.
    Extracted from unified_citation_processor.py.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        if not citations:
            return []
        
        # Group citations by similarity
        groups = []
        used_indices = set()
        
        for i, citation in enumerate(citations):
            if i in used_indices:
                continue
            
            group = [citation]
            used_indices.add(i)
            
            # Find similar citations
            for j, other_citation in enumerate(citations[i+1:], i+1):
                if j in used_indices:
                    continue
                
                # Check if citations are similar (same case, different reporters)
                if _are_parallel_citations(citation, other_citation):
                    group.append(other_citation)
                    used_indices.add(j)
            
            if len(group) > 1:
                # Mark as parallel group
                for cit in group:
                    cit['is_parallel'] = True
                    cit['parallel_citations'] = [c['citation'] for c in group]
                
                groups.append(group)
            else:
                groups.append([citation])
        
        logger.debug(f"Grouped {len(citations)} citations into {len(groups)} groups")
        return [cit for group in groups for cit in group]
    
    except Exception as e:
        logger.error(f"Error grouping parallel citations: {e}")
        return citations


def _are_parallel_citations(citation1: Dict[str, Any], citation2: Dict[str, Any]) -> bool:
    """
    Check if two citations are parallel (same case, different reporters).
    Extracted from unified_citation_processor.py.
    """
    try:
        # Check if they have similar case names
        name1 = citation1.get('case_name', '').lower()
        name2 = citation2.get('case_name', '').lower()
        
        if not name1 or not name2:
            return False
        
        # Simple similarity check
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        if len(words1) < 2 or len(words2) < 2:
            return False
        
        # Check for significant overlap
        intersection = words1.intersection(words2)
        if len(intersection) >= min(len(words1), len(words2)) * 0.7:
            return True
        
        return False
    
    except Exception:
        return False 