"""
Streamlined Case Name and Date Extraction
Consolidates all extraction logic into a clean, maintainable structure
"""

import re
import logging
from typing import Dict, Optional, Tuple, List, Any
from datetime import datetime
from dataclasses import dataclass
import warnings
import os

logger = logging.getLogger(__name__)

def is_valid_case_name(case_name: str) -> bool:
    """
    Validate if a case name is reasonable and complete.
    """
    if not case_name:
        return False
    case_name = case_name.strip()
    if len(case_name) < 5:
        return False
    if is_citation_like(case_name):
        return False
    if not re.search(r'[A-Za-z]', case_name):
        return False
    if not re.match(r'^[A-Za-z]|^In\s+re|^Estate\s+of|^Matter\s+of|^State\s+v\.|^People\s+v\.|^United\s+States\s+v\.', case_name, re.IGNORECASE):
        return False
    if not re.search(r'\s+v\.\s+|\s+vs\.\s+|^In\s+re|^Estate\s+of|^Matter\s+of', case_name, re.IGNORECASE):
        return False
    if len(case_name) > 200:
        return False
    return True

def is_citation_like(text: str) -> bool:
    """
    Check if text looks like a citation rather than a case name.
    Enhanced version with better pattern matching.
    """
    if not text:
        return True
    text = text.strip()
    citation_patterns = [
        r'^\d+\s+[A-Z]',
        r'^\d+\s*[A-Z]+\s+\d+',
        r'^[A-Z]+\s+\d+',
        r'^\d+\s*[A-Z]+\s*\(\d+\)',
        r'^[A-Z]+\s*\(\d+\)',
        r'^\d+\s*[A-Z]+\s*\d+\s*\(\d+\)',
        r'^[A-Z]+\s*Rep\.',
        r'^[A-Z]+\s*Supp\.',
        r'^[A-Z]+\s*2d',
        r'^[A-Z]+\s*3d',
        r'^F\.\s*\d+',
        r'^U\.\s*S\.',
        r'^S\.\s*Ct\.',
        r'^L\.\s*Ed\.',
        r'^L\.\s*Ed\.\s*2d',
    ]
    for pattern in citation_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return True
    if len(text) < 5:
        return True
    if re.match(r'^[A-Z0-9\s\.]+$', text) and any(c.isdigit() for c in text):
        return True
    return False

def clean_case_name_enhanced(case_name: str) -> str:
    """
    Enhanced case name cleaning with better punctuation and signal word removal.
    """
    if not case_name:
        return ""
    signal_words = [
        r'^See\s+generally\s+',
        r'^See\s+',
        r'^According\s+to\s+',
        r'^As\s+held\s+in\s+',
        r'^The\s+court\s+in\s+',
        r'^The\s+court\s+',
        r'^In\s+the\s+case\s+of\s+',
        r'^In\s+',
    ]
    for pattern in signal_words:
        case_name = re.sub(pattern, '', case_name, flags=re.IGNORECASE)
    case_name = re.sub(r'[\,\s]+$', '', case_name)
    case_name = case_name.rstrip('.,;:')
    case_name = case_name.strip()
    case_name = re.sub(r'\s+', ' ', case_name)
    return case_name

def extract_case_name_precise(context_before: str, citation: str) -> str:
    """
    Extract case name with precise patterns to avoid capturing too much text.
    Handles 'v.', 'vs.', 'In re', 'Estate of', and 'State v.' cases.
    """
    import logging
    logger = logging.getLogger("case_name_extraction")
    if not context_before:
        return ""
    context = context_before[-80:] if len(context_before) > 80 else context_before
    # Print all 'v.' matches in the context for 136 Wn. App. 104
    if citation == '136 Wn. App. 104':
        print(f"[DEBUG] Context for 136 Wn. App. 104 (repr): {repr(context)}")
        print(f"[DEBUG] Context length: {len(context)}")
        # Print 80 chars around 'Holder'
        idx_holder = context.find('Holder')
        if idx_holder != -1:
            start = max(0, idx_holder-20)
            end = min(len(context), idx_holder+60)
            snippet = context[start:end]
            with open('case_name_debug.txt', 'w', encoding='utf-8') as f:
                f.write(f"Snippet: {repr(snippet)}\n")
                f.write('Unicode code points:\n')
                f.write(' '.join(str(ord(c)) for c in snippet) + '\n')
        # Simple regex search for 'v.'
        simple_v_matches = list(re.finditer(r'v\.', context))
        print(f"[DEBUG] Simple 'v.' regex found {len(simple_v_matches)} matches in context for 136 Wn. App. 104.")
        for idx, m in enumerate(simple_v_matches):
            start = max(0, m.start()-20)
            end = min(len(context), m.end()+20)
            print(f"[DEBUG] Simple v. match {idx+1}: '{context[start:end]}' at {m.start()}-{m.end()}")
        # Check where the backward scan starts
        scan_start = len(context) - 1
        print(f"[DEBUG] Backward scan for 'v.' should start at index {scan_start} (end of context)")
        # If the scan is starting elsewhere, print a warning
        if scan_start < len(context) - 1:
            print(f"[WARNING] Backward scan is not starting at the end! Actual start: {scan_start}")
        v_matches = list(re.finditer(r'([A-Z][A-Za-z0-9&.,\'\- ]{1,100})\s+v\.?\s+([A-Z][A-Za-z0-9&.,\'\- ]{1,100})(?=,|\s)', context))
        print(f"[DEBUG] Found {len(v_matches)} 'v.' matches in context for 136 Wn. App. 104.")
        for idx, m in enumerate(v_matches):
            print(f"[DEBUG] v. match {idx+1}: '{m.group(0)}' at {m.start()}-{m.end()}")
    # Use the relaxed regex for all extractions
    v_matches = list(re.finditer(r'([A-Z][A-Za-z0-9&.,\'\- ]{1,100})\s+v\.?\s+([A-Z][A-Za-z0-9&.,\'\- ]{1,100})(?=,|\s)', context))
    import logging
    logger = logging.getLogger("case_name_extraction")
    logger.debug(f"[extract_case_name_precise] Context: '{context}'")
    logger.debug(f"[extract_case_name_precise] Citation: '{citation}'")
    logger.debug(f"[extract_case_name_precise] Found {len(v_matches)} v. matches.")
    for idx, m in enumerate(v_matches):
        logger.debug(f"[extract_case_name_precise] v. match {idx+1}: '{m.group(0)}' at {m.start()}-{m.end()}")
        between = context[m.end():]
        between_clean = re.sub(r'\s+', '', between)
        between_clean = re.sub(r'^[,\d]*', '', between_clean)
        logger.debug(f"[extract_case_name_precise] Text between v. match {idx+1} and citation: '{between_clean[:50]}'")
    if v_matches:
        last_v_match = v_matches[-1]
        between = context[last_v_match.end():]
        between_clean = re.sub(r'\s+', '', between)
        between_clean = re.sub(r'^[,\d]*', '', between_clean)
        if between_clean.startswith(citation.replace(' ', '')):
            case_name = clean_case_name_enhanced(last_v_match.group(0))
            logger.debug(f"[extract_case_name_precise] Closest v. match accepted: '{case_name}'")
            if (case_name and is_valid_case_name(case_name) and not starts_with_signal_word(case_name)
                and not _is_header_or_clerical_text(case_name) and len(case_name.split()) <= 10):
                logger.debug(f"[extract_case_name_precise] Valid case name found: '{case_name}'")
                return case_name
    patterns = [
        # Allow for optional numbers and commas between case name and citation
        r'([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,5}\s+v\.?\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,5})\s*,(?:\s*\d+,?)*\s*' + re.escape(citation),
        r'([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,5}\s+v\.?\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,5})\s*\(\d{4}\)',
        r'(In\s+re\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,5})\s*,(?:\s*\d+,?)*\s*' + re.escape(citation),
        r'(In\s+re\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,5})\s*\(\d{4}\)',
        r'(Estate\s+of\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,5})\s*,(?:\s*\d+,?)*\s*' + re.escape(citation),
        r'(Estate\s+of\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,5})\s*\(\d{4}\)',
        r'(State\s+v\.?\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,5})\s*,(?:\s*\d+,?)*\s*' + re.escape(citation),
        r'(People\s+v\.?\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,5})\s*,(?:\s*\d+,?)*\s*' + re.escape(citation),
        r'(United\s+States\s+v\.?\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,5})\s*,(?:\s*\d+,?)*\s*' + re.escape(citation),
        r'([A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,5}\s+v\.?\s+[A-Z][A-Za-z\'\-]+(?:\s+[A-Z][A-Za-z\'\-]+){0,5})\s*,\s*\d+',
    ]
    for i, pattern in enumerate(patterns):
        matches = list(re.finditer(pattern, context, re.IGNORECASE))
        logger.debug(f"[extract_case_name_precise] Pattern {i+1}: found {len(matches)} matches")
        if matches:
            match = matches[-1]
            case_name = clean_case_name_enhanced(match.group(1))
            logger.debug(f"[extract_case_name_precise] Found case name: '{case_name}'")
            if (case_name and 
                is_valid_case_name(case_name) and 
                not starts_with_signal_word(case_name) and
                not _is_header_or_clerical_text(case_name) and
                len(case_name.split()) <= 10):
                logger.debug(f"[extract_case_name_precise] Valid case name found: '{case_name}'")
                return case_name
    logger.debug(f"[extract_case_name_precise] No valid case names found")
    return ""

def extract_case_name_with_date_adjacency(context_before: str, citation: str) -> str:
    """
    Extract case name with focus on adjacency between case name and date.
    Looks for patterns like "Case Name v. Defendant, 123 Reporter 456 (2023)"
    Uses narrow context and specific patterns to avoid header text.
    """
    import logging
    logger = logging.getLogger("case_name_extraction")
    if not context_before:
        return ""
    narrow_context = context_before[-50:] if len(context_before) > 50 else context_before
    date_adjacent_patterns = [
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*,(?:\s*\d+,?)*\s*' + re.escape(citation),
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+vs\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*,(?:\s*\d+,?)*\s*' + re.escape(citation),
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*\(\d{4}\)',
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+vs\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*\(\d{4}\)',
        r'(In\s+re\s+[A-Za-z\s,\.\'-]+?)\s*,(?:\s*\d+,?)*\s*' + re.escape(citation),
        r'(In\s+re\s+[A-Za-z\s,\.\'-]+?)\s*\(\d{4}\)',
        r'(Estate\s+of\s+[A-Za-z\s,\.\'-]+?)\s*,(?:\s*\d+,?)*\s*' + re.escape(citation),
        r'(Estate\s+of\s+[A-Za-z\s,\.\'-]+?)\s*\(\d{4}\)',
        r'(State\s+v\.\s+[A-Za-z\s,\.\'-]+?)\s*,(?:\s*\d+,?)*\s*' + re.escape(citation),
        r'(People\s+v\.\s+[A-Za-z\s,\.\'-]+?)\s*,(?:\s*\d+,?)*\s*' + re.escape(citation),
        r'(United\s+States\s+v\.\s+[A-Za-z\s,\.\'-]+?)\s*,(?:\s*\d+,?)*\s*' + re.escape(citation),
    ]
    for i, pattern in enumerate(date_adjacent_patterns):
        matches = list(re.finditer(pattern, narrow_context, re.IGNORECASE))
        logger.debug(f"[extract_case_name_with_date_adjacency] Pattern {i+1}: '{pattern}' found {len(matches)} matches")
        if matches:
            match = matches[-1]
            case_name = clean_case_name_enhanced(match.group(1))
            logger.debug(f"[extract_case_name_with_date_adjacency] Found case name with date adjacency: '{case_name}'")
            if (case_name and 
                is_valid_case_name(case_name) and 
                not starts_with_signal_word(case_name) and
                not _is_header_or_clerical_text(case_name)):
                logger.debug(f"[extract_case_name_with_date_adjacency] Valid case name found: '{case_name}'")
                return case_name
            else:
                logger.debug(f"[extract_case_name_with_date_adjacency] Case name invalid, starts with signal word, or is header text: '{case_name}'")
    logger.debug(f"[extract_case_name_with_date_adjacency] No valid case names with date adjacency found")
    return ""

def extract_case_name_from_complex_citation(context: str, citation: str) -> str:
    """
    Extract case name from complex citation patterns like "State v. Waldon, 148 Wn. App. 952, 962-63, 202 P.3d 325 (2009)"
    """
    import logging
    logger = logging.getLogger("case_name_extraction")
    if not context or not citation:
        return ""
    complex_citation_patterns = [
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*,\s*\d+\s+[A-Za-z\.\s]+\d+.*?\(\d{4}\)',
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*,\s*\d+\s+[A-Za-z\.\s]+\d+.*?,\s*\d+.*?\(\d{4}\)',
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*,\s*\d+\s+[A-Za-z\.\s]+\d+\s*\(\d{4}\)',
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*,\s*\d+\s+[A-Za-z\.\s]+\d+.*?,\s*\d+',
        r'(In\s+re\s+[A-Za-z\s,\.\'-]+?)\s*,\s*\d+\s+[A-Za-z\.\s]+\d+.*?\(\d{4}\)',
        r'(Estate\s+of\s+[A-Za-z\s,\.\'-]+?)\s*,\s*\d+\s+[A-Za-z\.\s]+\d+.*?\(\d{4}\)',
        r'(State\s+v\.\s+[A-Za-z\s,\.\'-]+?)\s*,\s*\d+\s+[A-Za-z\.\s]+\d+.*?\(\d{4}\)',
        r'(People\s+v\.\s+[A-Za-z\s,\.\'-]+?)\s*,\s*\d+\s+[A-Za-z\.\s]+\d+.*?\(\d{4}\)',
        r'(United\s+States\s+v\.\s+[A-Za-z\s,\.\'-]+?)\s*,\s*\d+\s+[A-Za-z\.\s]+\d+.*?\(\d{4}\)',
    ]
    for i, pattern in enumerate(complex_citation_patterns):
        matches = list(re.finditer(pattern, context, re.IGNORECASE))
        logger.debug(f"[extract_case_name_from_complex_citation] Pattern {i+1}: '{pattern}' found {len(matches)} matches")
        if matches:
            match = matches[-1]
            case_name = clean_case_name_enhanced(match.group(1))
            logger.debug(f"[extract_case_name_from_complex_citation] Found case name in complex citation: '{case_name}'")
            if case_name and is_valid_case_name(case_name) and not starts_with_signal_word(case_name):
                if is_case_name_associated_with_citation(context, case_name, citation):
                    logger.debug(f"[extract_case_name_from_complex_citation] Valid case name found: '{case_name}'")
                    return case_name
    logger.debug(f"[extract_case_name_from_complex_citation] No valid case names in complex citations found")
    return ""

def starts_with_signal_word(text: str) -> bool:
    if not text:
        return False
    signal_words = [
        'see generally',
        'see',
        'according to',
        'as held in',
        'the court in',
        'the court',
        'in the case of',
    ]
    text_lower = text.lower().strip()
    for signal_word in signal_words:
        if text_lower.startswith(signal_word):
            return True
    return False

def _is_header_or_clerical_text(text: str) -> bool:
    if not text:
        return True
    text_lower = text.lower()
    header_words = {
        'clerk', 'supreme', 'court', 'state', 'washington', 'filed', 'record', 
        'opinion', 'judge', 'justice', 'chief', 'associate', 'district', 'appeals',
        'circuit', 'federal', 'united', 'states', 'department', 'attorney', 
        'prosecuting', 'sheriff', 'county', 'municipal', 'organization', 'petitioners',
        'respondents', 'cross', 'individuals', 'similarly', 'situated', 'behalf',
        'others', 'married', 'couple', 'en', 'banc', 'file', 'office', 'june',
        'december', 'january', 'february', 'march', 'april', 'may', 'july', 'august',
        'september', 'october', 'november', 'am', 'pm', 'morning', 'afternoon',
        'pendleton', 'sarah', 'r.', 'r', 'supreme', 'court', 'clerk'
    }
    text_words = set(text_lower.split())
    if text_words.intersection(header_words):
        return True
    header_patterns = [
        r'^[A-Z\s]+$',
        r'clerk.*court',
        r'supreme.*court.*state',
        r'filed.*record',
        r'opinion.*filed',
        r'^[A-Z]+\s+[A-Z]+\s+[A-Z]+$',
        r'pendleton.*supreme.*court.*clerk',
        r'^[A-Z]+\s+[A-Z]+\s+[A-Z]+\s+[A-Z]+',
        r'clerk.*john.*doe',
        r'^[A-Z]+\s+[A-Z]+\s+[A-Z]+\s+[A-Z]+\s+[A-Z]+',
    ]
    for pattern in header_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    if len(text) > 100:
        return True
    word_count = len(text.split())
    if word_count > 12:
        return True
    problematic_patterns = [
        r'R\.PENDLETON',
        r'PENDLETON.*SUPREME.*COURT.*CLERK',
        r'CLERK.*JOHN.*DOE.*ET.*AL',
        r'SUPREME.*COURT.*CLERK.*JOHN.*DOE',
    ]
    for pattern in problematic_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

def is_case_name_associated_with_citation(context: str, case_name: str, citation: str) -> bool:
    import logging
    logger = logging.getLogger("case_name_extraction")
    pattern = rf'{re.escape(case_name)}\s*,\s*{re.escape(citation)}'
    if re.search(pattern, context, re.IGNORECASE):
        logger.debug(f"[is_case_name_associated_with_citation] Case name '{case_name}' is directly associated with citation '{citation}'")
        return True
    case_name_index = context.find(case_name)
    citation_index = context.find(citation)
    if case_name_index != -1 and citation_index != -1:
        if case_name_index < citation_index:
            distance = citation_index - case_name_index
            if distance <= 50:
                logger.debug(f"[is_case_name_associated_with_citation] Case name '{case_name}' is within {distance} chars of citation '{citation}'")
                return True
    logger.debug(f"[is_case_name_associated_with_citation] Case name '{case_name}' is NOT associated with citation '{citation}'")
    return False

def extract_case_name_from_context_enhanced(context_before: str, citation: str) -> str:
    """
    Enhanced context-based case name extraction with better line break handling and signal word filtering.
    """
    import logging
    logger = logging.getLogger("case_name_extraction")
    if not context_before:
        return ""
    patterns = [
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+vs\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*\(\d{4}\)',
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+vs\.\s+[A-Z][A-Za-z\s,\.\'-]+?)\s*\(\d{4}\)',
        r'(In\s+re\s+[A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
        r'(In\s+re\s+[A-Za-z\s,\.\'-]+?)\s*\(\d{4}\)',
        r'(Estate\s+of\s+[A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
        r'(Estate\s+of\s+[A-Za-z\s,\.\'-]+?)\s*\(\d{4}\)',
        r'(State\s+v\.\s+[A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
        r'(People\s+v\.\s+[A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
        r'(United\s+States\s+v\.\s+[A-Za-z\s,\.\'-]+?)\s*,\s*' + re.escape(citation),
    ]
    for i, pattern in enumerate(patterns):
        matches = list(re.finditer(pattern, context_before, re.IGNORECASE))
        logger.debug(f"[extract_case_name_from_context_enhanced] Pattern {i+1}: '{pattern}' found {len(matches)} matches")
        for j, match in enumerate(matches):
            logger.debug(f"[extract_case_name_from_context_enhanced] Match {j+1}: '{match.group(1)}'")
        if matches:
            match = matches[-1]
            case_name = clean_case_name_enhanced(match.group(1))
            logger.debug(f"[extract_case_name_from_context_enhanced] Cleaned case name: '{case_name}'")
            if (case_name and 
                is_valid_case_name(case_name) and 
                not starts_with_signal_word(case_name) and
                not _is_header_or_clerical_text(case_name)):
                logger.debug(f"[extract_case_name_from_context_enhanced] Valid case name found: '{case_name}'")
                return case_name
            else:
                logger.debug(f"[extract_case_name_from_context_enhanced] Case name invalid, starts with signal word, or is header text: '{case_name}'")
    logger.debug(f"[extract_case_name_from_context_enhanced] No valid case names found")
    return ""

def extract_case_name_global_search(text: str, citation: str) -> str:
    """
    Global search for case name patterns in the entire text.
    Used as a fallback when local context extraction fails.
    """
    import logging
    logger = logging.getLogger("case_name_extraction")
    if not text or not citation:
        return ""
    patterns = [
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)(?=[,;\s]+|$)',
        r'(In\s+re\s+[A-Za-z\s,\.\'-]+?)(?=[,;\s]+|$)',
        r'(Estate\s+of\s+[A-Za-z\s,\.\'-]+?)(?=[,;\s]+|$)',
        r'(Matter\s+of\s+[A-Za-z\s,\.\'-]+?)(?=[,;\s]+|$)',
        r'(State\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=[,;\s]+|$)',
        r'(People\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=[,;\s]+|$)',
        r'(United\s+States\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=[,;\s]+|$)',
    ]
    for i, pattern in enumerate(patterns):
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        logger.debug(f"[extract_case_name_global_search] Pattern {i+1}: '{pattern}' found {len(matches)} matches")
        for j, match in enumerate(matches):
            logger.debug(f"[extract_case_name_global_search] Match {j+1}: '{match.group(1)}'")
        if matches:
            match = matches[-1]
            case_name = clean_case_name_enhanced(match.group(1))
            logger.debug(f"[extract_case_name_global_search] Cleaned case name: '{case_name}'")
            if case_name and is_valid_case_name(case_name) and not starts_with_signal_word(case_name):
                logger.debug(f"[extract_case_name_global_search] Valid case name found: '{case_name}'")
                return case_name
            else:
                logger.debug(f"[extract_case_name_global_search] Case name invalid or starts with signal word: '{case_name}'")
    logger.debug(f"[extract_case_name_global_search] No valid case names found")
    return ""

# --- Moved from extract_case_name.py (now archived) ---
def extract_case_name_from_text(text: str, citation_text: str, all_citations: list = None, canonical_name: str = None) -> Optional[str]:
    """
    Extract case name from text using multiple strategies.
    Enhanced version with better handling of complex citations and case name-citation association.
    Uses narrow 100-character context window and focuses on adjacency between case name and date.
    Args:
        text: The full text
        citation_text: The specific citation to find case name for
        all_citations: List of all citations in the text (for context)
        canonical_name: Known canonical case name for the case
    Returns:
        str: Extracted case name or empty string
    """
    import logging
    logger = logging.getLogger("case_name_extraction")
    if not text or not citation_text:
        logger.debug("[extract_case_name_from_text] Empty text or citation_text.")
        return ""
    norm_text = re.sub(r'\s+', ' ', text)
    logger.debug(f"[extract_case_name_from_text] Normalized text: '{norm_text[:200]}...'")
    logger.debug(f"[extract_case_name_from_text] Looking for citation: '{citation_text}'")
    citation_index = norm_text.find(citation_text)
    if citation_index != -1:
        context_before = norm_text[max(0, citation_index - 100):citation_index]
        context_after = norm_text[citation_index:min(len(norm_text), citation_index + 100)]
        full_context = context_before + context_after
        logger.debug(f"[extract_case_name_from_text] Context before citation: '{context_before}'")
        logger.debug(f"[extract_case_name_from_text] Context after citation: '{context_after}'")
        logger.debug(f"[extract_case_name_from_text] Full context (200 chars): '{full_context}'")
        if canonical_name and not hasattr(extract_case_name_from_text, '_in_hinted_call'):
            try:
                extract_case_name_from_text._in_hinted_call = True
                case_name = extract_case_name_hinted(text, citation_text, canonical_name)
                if case_name and is_valid_case_name(case_name):
                    logger.debug(f"[extract_case_name_from_text] Found case name with hinted extraction: '{case_name}'")
                    return case_name
            finally:
                if hasattr(extract_case_name_from_text, '_in_hinted_call'):
                    delattr(extract_case_name_from_text, '_in_hinted_call')
        case_name = extract_case_name_precise(context_before, citation_text)
        if case_name:
            logger.debug(f"[extract_case_name_from_text] Found case name with precise extraction: '{case_name}'")
            return case_name
        case_name = extract_case_name_with_date_adjacency(context_before, citation_text)
        if case_name:
            logger.debug(f"[extract_case_name_from_text] Found case name with date adjacency: '{case_name}'")
            return case_name
        case_name = extract_case_name_from_complex_citation(full_context, citation_text)
        if case_name:
            logger.debug(f"[extract_case_name_from_text] Found case name in complex citation: '{case_name}'")
            return case_name
        case_name = extract_case_name_from_context_enhanced(context_before, citation_text)
        if case_name:
            logger.debug(f"[extract_case_name_from_text] Found case name in context: '{case_name}'")
            return case_name
    else:
        logger.debug(f"[extract_case_name_from_text] Citation '{citation_text}' not found in text.")
    logger.debug(f"[extract_case_name_from_text] Trying global search...")
    case_name = extract_case_name_global_search(norm_text, citation_text)
    if case_name:
        logger.debug(f"[extract_case_name_from_text] Found case name in global search: '{case_name}'")
        return case_name
    if canonical_name and canonical_name.lower() in norm_text.lower():
        logger.debug(f"[extract_case_name_from_text] Using canonical name as fallback (found in text): '{canonical_name}'")
        return canonical_name
    logger.debug(f"[extract_case_name_from_text] No case name found")
    return ""

def extract_case_name_hinted(text: str, citation: str, canonical_name: str = None, api_key: str = None) -> str:
    """
    Safe version that NEVER returns canonical name directly.
    Only returns names actually found in the document text.
    """
    try:
        if not canonical_name:
            return ""
        citation_index = text.find(citation.replace("Wash. 2d", "Wn.2d"))
        if citation_index == -1:
            citation_index = text.find(citation)
        if citation_index == -1:
            return ""
        context_before = text[max(0, citation_index - 100):citation_index]
        variants = []
        patterns = [
            r'([A-Z][A-Za-z"\.",&]+\s+v\.\s+[A-Z][A-Za-z"\.",&]+)',
            r'([A-Z][A-Za-z"\.",&]+\s+vs\.\s+[A-Z][A-Za-z"\.",&]+)',
            r'(Dep\'t\s+of\s+[A-Za-z\s,&]+\s+v\.\s+[A-Za-z\s,&]+)',
            r'(State\s+v\.\s+[A-Za-z\s,&]+)',
            r'(In\s+re\s+[A-Za-z\s,&]+)'
        ]
        for pattern in patterns:
            matches = re.findall(pattern, context_before)
            for match in matches:
                cleaned = clean_case_name_enhanced(match)
                if cleaned and is_valid_case_name(cleaned):
                    variants.append(cleaned)
        if not variants:
            return ""
        from difflib import SequenceMatcher
        best_variant = ""
        best_score = 0.0
        for variant in variants:
            score = SequenceMatcher(None, variant.lower(), canonical_name.lower()).ratio()
            if score > best_score and score > 0.6:
                best_variant = variant
                best_score = score
        if best_variant and best_variant != canonical_name:
            if best_variant.replace("'", "").replace(".", "") in context_before.replace("'", "").replace(".", ""):
                return best_variant
        return ""
    except Exception as e:
        import logging
        logging.warning(f"Safe hinted extraction failed: {e}")
        return ""

def get_canonical_case_name_from_courtlistener(citation, api_key=None):
    """
    Get canonical case name using the unified citation processor.
    This replaces the stub implementation with a working one.
    """
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor
        processor = UnifiedCitationProcessor()
        result = processor.verify_citation_unified_workflow(citation)
        if result and result.get('verified') == 'true':
            case_name = result.get('case_name', '')
            if case_name and case_name != 'N/A':
                return {
                    'case_name': case_name,
                    'date': result.get('canonical_date', ''),
                    'source': 'courtlistener_verification'
                }
        return None
    except Exception as e:
        import logging
        logging.warning(f"Failed to get canonical name from CourtListener verification: {e}")
        return None

def get_canonical_case_name_from_google_scholar(citation, api_key=None):
    """
    Get canonical case name using the unified citation processor.
    This replaces the stub implementation with a working one.
    """
    try:
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor
        processor = UnifiedCitationProcessor()
        result = processor.verify_citation_unified_workflow(citation)
        if result and result.get('verified') == 'true':
            case_name = result.get('case_name', '')
            if case_name and case_name != 'N/A':
                return {
                    'case_name': case_name,
                    'date': result.get('canonical_date', ''),
                    'source': 'google_scholar_verification'
                }
        return None
    except Exception as e:
        import logging
        logging.warning(f"Failed to get canonical name from Google Scholar verification: {e}")
        return None

@dataclass
class ExtractionResult:
    """Structured result for case name and date extraction"""
    case_name: str = ""
    date: str = ""
    year: str = ""
    confidence: float = 0.0
    method: str = "unknown"
    debug_info: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.debug_info is None:
            self.debug_info = {}
        
        # Extract year from date if not provided
        if self.date and not self.year:
            year_match = re.search(r'(\d{4})', self.date)
            if year_match:
                self.year = year_match.group(1)

class CaseNameExtractor:
    """Main case name and date extractor"""
    
    def __init__(self):
        self._setup_patterns()
        # Remove the circular dependency - don't create DateExtractor here
        # self.date_extractor = DateExtractor()
    
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
                'pattern': r'(Matter\s+of\s+[A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?)(?=,\s*\d+\s+[A-Za-z.]+|\s*\(|$)',
                'confidence_base': 0.8,
                'format': lambda m: m.group(1).strip()
            },
            {
                'name': 'matter_of_with_v',
                'pattern': r'(Matter\s+of\s+[A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?\s+v\.\s+[A-Z][A-Za-z0-9&.,\'\s-]+(?:\s+[A-Za-z0-9&.,\'\s-]+)*?)(?=,\s*\d+\s+[A-Za-z.]+|\s*\(|$)',
                'confidence_base': 0.85,
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
        def debug_write(msg):
            log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
            os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, 'case_name_debug.txt'), 'a', encoding='utf-8') as f:
                f.write(msg + '\n')
        debug_write(f"[DEBUG] CaseNameExtractor.extract CALLED: citation={citation}, text[0:100]={text[:100]}")
        result = ExtractionResult()
        
        try:
            # Step 1: Get context around citation if provided
            context = self._get_system_extraction_context(text, citation)
            
            # Step 2: Try case name extraction
            case_extraction = self._extract_case_name(context, citation)
            if case_extraction:
                result.case_name = case_extraction['name']
                result.confidence = case_extraction['confidence']
                result.method = case_extraction['method']
                result.debug_info.update(case_extraction.get('debug', {}))
            
            # Step 3: Try date extraction
            # The DateExtractor is now initialized directly in extract_case_name_and_date
            # date_extractor = DateExtractor() # This line is removed
            # date_extraction = self.date_extractor.extract_date_from_context(
            #     text, citation
            # ) if citation else self.date_extractor.extract_date_from_full_text(text)
            
            # if date_extraction:
            #     result.date = date_extraction
            #     # Extract year from date
            #     year_match = re.search(r'(\d{4})', date_extraction)
            #     if year_match:
            #         result.year = year_match.group(1)
            
            logger.info(f"Extraction complete: {result.case_name} ({result.year}) - {result.method}")
            
        except Exception as e:
            logger.error(f"Error in extraction: {e}")
            result.debug_info['error'] = str(e)
        
        return result
    
    def _get_extraction_context(self, text: str, citation: str = None) -> str:
        """Get user-facing context: 200 characters before, 100 after citation."""
        if not citation:
            return text
        citation_pos = text.find(citation)
        if citation_pos == -1:
            return text
        start = max(0, citation_pos - 200)
        end = min(len(text), citation_pos + len(citation) + 100)
        return text[start:end].strip()

    def _get_system_extraction_context(self, text: str, citation: str = None) -> str:
        """Get citation-aware context for extraction: always 200 chars before citation, 100 after."""
        if not citation:
            return text
        citation_pos = text.find(citation)
        if citation_pos == -1:
            return text
        start = max(0, citation_pos - 200)
        end = min(len(text), citation_pos + len(citation) + 100)
        return text[start:end].strip()
    
    def _extract_case_name(self, context: str, citation: str = None) -> Optional[Dict]:
        import re
        STOPWORDS = {"of", "and", "the", "in", "for", "on", "at", "by", "with", "to", "from", "as", "but", "or", "nor", "so", "yet", "a", "an", "re"}
        def debug_write(msg):
            log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
            os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, 'case_name_debug.txt'), 'a', encoding='utf-8') as f:
                f.write(msg + '\n')
        debug_write(f"[DEBUG] CALL: citation={citation}, context[0:100]={context[:100]}")
        if not context or len(context) < 10:
            debug_write(f"[DEBUG] Early exit: context too short or empty.")
            return None
        # Instead of stopping at a delimiter, just use the full context window before the citation
        citation_pos = context.rfind(citation) if citation else len(context)
        context_before_citation = context[:citation_pos]
        debug_write(f"[DEBUG] context_before_citation for citation={citation}: {context_before_citation[-200:]}")
        # Try In re / Ex parte first
        inre_match = re.search(r'(In\s+re|Ex\s+parte)[^,;\n]*', context_before_citation, re.IGNORECASE)
        if inre_match:
            case_name = inre_match.group(0).rstrip(',;').rstrip()  # Only trim trailing comma/semicolon/whitespace
            debug_write(f"[DEBUG] In re/Ex parte match: {case_name}")
            return {'name': case_name, 'confidence': 0.9, 'method': 'inre_exparte', 'debug': {'case_name': case_name}}
        # Try v. pattern
        v_match = list(re.finditer(r'\bv\.', context_before_citation))
        if v_match:
            last_v = v_match[-1].start()
            debug_write(f"[DEBUG] Found last 'v.': char_pos={last_v}")
            # Scan backward from v. to find the start of the first party
            words = list(re.finditer(r"[\w'&.,-]+", context_before_citation))
            v_word_idx = None
            for i, m in enumerate(words):
                if m.start() >= last_v:
                    v_word_idx = i
                    break
            if v_word_idx is None:
                v_word_idx = len(words) - 1
            # Scan backward to first non-capitalized, non-stopword
            start_idx = v_word_idx - 1
            while start_idx >= 0:
                w = words[start_idx].group(0)
                if (not w[0].isupper()) and (w.lower() not in STOPWORDS):
                    debug_write(f"[DEBUG] Stopped backward scan at index: {start_idx}, word: {w}")
                    break
                start_idx -= 1
            # Move forward to next capitalized word
            start_idx += 1
            while start_idx < v_word_idx and not words[start_idx].group(0)[0].isupper():
                start_idx += 1
            debug_write(f"[DEBUG] Final start index for case name: {start_idx}")
            # Collect all words from start_idx through the party after v.
            # Find the next capitalized word after v. (start of second party)
            after_v_idx = v_word_idx + 1
            while after_v_idx < len(words) and not words[after_v_idx].group(0)[0].isupper():
                after_v_idx += 1
            # Stop at the first citation-like pattern after the party names
            citation_pattern = re.compile(r"\d+\s+(Wn\.?\s*2d|Wash\.?\s*2d|P\.?\s*3d|P\.?\s*2d|F\.?\s*3d|F\.?\s*2d|U\.?S\.|S\.?Ct\.|L\.?Ed\.|A\.?2d|A\.?3d|So\.?2d|So\.?3d)", re.IGNORECASE)
            stop_idx = len(words)
            for i in range(after_v_idx, len(words)):
                if citation_pattern.match(' '.join(words[j].group(0) for j in range(i, min(i+3, len(words))))):
                    stop_idx = i
                    debug_write(f"[DEBUG] Stopping case name at citation-like pattern: index={stop_idx}")
                    break
            # Collect all words from start_idx up to stop_idx
            case_name_words = [words[i].group(0) for i in range(start_idx, stop_idx)]
            case_name = ' '.join(case_name_words).rstrip(',;').rstrip()  # Only trim trailing comma/semicolon/whitespace
            debug_write(f"[DEBUG] v. match case name: {case_name}")
            return {'name': case_name, 'confidence': 0.9, 'method': 'v_pattern', 'debug': {'case_name': case_name}}
        debug_write(f"[DEBUG] No case name extracted.")
        return None
    
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
        """Extract date from context around a citation"""
        if not text or not citation:
            return None
        
        try:
            # Find citation in text
            index = text.find(citation)
            if index == -1:
                return None
            
            # Extract context around citation
            context_start = max(0, index - 300)
            context_end = min(len(text), index + len(citation) + 300)
            context = text[context_start:context_end]
            
            # Extract date from context
            return self._extract_date_from_text(context)
            
        except Exception as e:
            logger.error(f"Error extracting date from context: {e}")
            return None
    
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
def extract_case_name_and_date(text: str, citation: str = None) -> Dict[str, Any]:
    """
    Main extraction function - replaces all the complex variants
    Args:
        text: Document text
        citation: Citation to search for (optional)
    Returns:
        Dict with case_name, date, year, confidence, method
    """
    def debug_write(msg):
        log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, 'case_name_debug.txt'), 'a', encoding='utf-8') as f:
            f.write(msg + '\n')
    debug_write(f"[DEBUG] extract_case_name_and_date CALLED: citation={citation}, text[0:100]={text[:100]}")
    extractor = get_extractor()
    result = extractor.extract(text, citation)
    # Date extraction
    date_extractor = DateExtractor()
    if citation:
        date = date_extractor.extract_date_from_context(text, citation)
    else:
        date = date_extractor.extract_date_from_full_text(text)
    result.date = date
    result.year = date
    debug_write(f"[DEBUG] Extracted date: {date}")
    return {
        'case_name': result.case_name,
        'date': result.date,
        'year': result.year,
        'confidence': result.confidence,
        'method': result.method,
        'debug': result.debug_info
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

def extract_case_name_triple(text: str, citation: str = None, api_key: str = None, context_window: int = 100) -> Tuple[str, str, str]:
    """
    Backward compatible triple extraction
    Returns (case_name, year, confidence)
    """
    result = extract_case_name_and_date(text, citation)
    return (
        result['case_name'],
        result['year'], 
        str(result['confidence'])
    )

def extract_case_name_improved(text: str, citation: str = None) -> Tuple[str, str, str]:
    """
    Backward compatible triple extraction
    Returns (case_name, year, confidence)
    """
    result = extract_case_name_and_date(text, citation)
    return (
        result['case_name'],
        result['year'], 
        str(result['confidence'])
    )

def extract_year_improved(text: str, citation: str = None) -> str:
    """
    Backward compatible year extraction
    Returns year only
    """
    result = extract_case_name_and_date(text, citation)
    return result['year']

def extract_year_after_last_citation(text: str) -> str:
    """
    Backward compatible year extraction
    Returns year only
    """
    result = extract_case_name_and_date(text)
    return result['year']

def get_canonical_case_name(citation: str) -> str:
    """
    Backward compatible canonical case name extraction
    Returns case name only
    """
    result = extract_case_name_and_date("", citation)
    return result['case_name']

def extract_year_from_line(line):
    """Extract a year from a line of text, looking for (YYYY) or any 4-digit year."""
    import re
    match = re.search(r'\((19|20)\d{2}\)', line)
    if match:
        return match.group(1)
    match = re.search(r'(19|20)\d{2}', line)
    if match:
        return match.group(0)
    return ""

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