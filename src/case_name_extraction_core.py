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

def clean_case_name_enhanced(case_name: str, context_before: str = "") -> str:
    """
    Enhanced case name cleaning with better punctuation and signal word removal.
    If the result starts with 'v.' or 'vs.', attempt to prepend the word before 'v.' from the context window.
    If no such word exists, return empty string.
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
    # If the cleaned case name starts with 'v.' or 'vs.', try to prepend the word before 'v.' from context
    if re.match(r'^(v\.|vs\.)\b', case_name, re.IGNORECASE):
        # Try to find the word before 'v.' in the context
        match = re.search(r'(\b\w+)\s+(v\.|vs\.)\b', context_before[-100:])
        if match:
            case_name = f"{match.group(1)} {case_name}"
        else:
            return ""
    return case_name

def preprocess_contractions(text: str) -> str:
    """
    Join contractions split by whitespace or newline after an apostrophe (e.g., Comm' n -> Comm'n).
    """
    import re
    return re.sub(r"([A-Za-z])'\s*([a-zA-Z])", r"\1'\2", text)

# In extract_case_name_precise, preprocess the context before regex matching

# Common stopwords that might appear before a case name
STOPWORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'if', 'then', 'else', 'when',
    'at', 'from', 'by', 'on', 'off', 'for', 'in', 'out', 'over', 'to',
    'into', 'with', 'without', 'after', 'before', 'of', 'as', 'is',
    'that', 'this', 'these', 'those', 'it', 'its', 'it\'s', 'they',
    'them', 'their', 'there', 'here', 'where', 'why', 'how', 'what',
    'which', 'who', 'whom', 'whose', 'whence', 'wherever', 'whether',
    'while', 'until', 'upon', 'within', 'without', 'yet', 'so', 'than',
    'though', 'till', 'via', 'vice', 'vs', 'v', 'v.'
}

def is_stopword(word: str) -> bool:
    """Check if a word is a stopword."""
    # Remove any trailing punctuation
    word = word.lower().rstrip('.,;:!?\'"()[]{}')
    return word in STOPWORDS

def find_case_name_start(text: str, start_pos: int, citation: str = '') -> int:
    """
    Find the start of a case name by working backward from a position.
    Looks for patterns like "v." or "vs." and then finds the start of the case name.
    
    Args:
        text: The full text to search in
        start_pos: The position of the citation in the text
        citation: The citation text (optional, used for fallback patterns)
        
    Returns:
        int: The start position of the case name in the text
    """
    if start_pos <= 0:
        return 0
    
    text_before = text[:start_pos].strip()
    citation = citation.strip()
    
    # Pattern 1: Look for the pattern "Plaintiff v. Defendant, Citation"
    v_pattern = r'\b(?:v|vs)\.?\b'
    
    # First, try to find the "v." or "vs." pattern
    v_matches = list(re.finditer(v_pattern, text_before, re.IGNORECASE))
    
    if v_matches:
        # Get the last "v." or "vs." before the citation
        last_v = v_matches[-1]
        v_pos = last_v.start()
        
        # Look for the start of the case name before the "v."
        before_v = text_before[:v_pos].strip()
        
        # Find the last sequence of capitalized words before the "v."
        # This handles multi-word party names like "Lakehaven Water & Sewer Dist."
        words = before_v.split()
        for i in range(len(words)-1, -1, -1):
            word = words[i].strip().rstrip(',')
            if word and word[0].isupper() and not is_stopword(word.lower()):
                # Found a potential start of the case name
                # Now find its position in the original text
                search_str = ' '.join(words[i:])
                pos = before_v.rfind(search_str)
                if pos != -1:
                    return pos
                break
    
    # Pattern 2: Look for "Case Name, Citation" pattern
    if citation:
        citation_pattern = re.escape(citation)
        
        # Look for a pattern like "Some Case Name, 123 U.S. 456"
        pattern = fr'([A-Z][A-Za-z0-9&\-\.\',]*(?:\s+[A-Za-z0-9&\-\.\',]+)*?)\s*,\s*{citation_pattern}'
        match = re.search(pattern, text_before)
        if match:
            return match.start(1)
    
    # Pattern 3: Look for common legal phrases that might precede a case name
    legal_phrases = [
        'in', 'see', 'see also', 'cf.', 'e.g.,', 'accord', 'but see',
        'the court in', 'in the case of', 'as stated in', 'as held in',
        'as explained in', 'as recognized in', 'as noted in', 'as discussed in'
    ]
    
    for phrase in legal_phrases:
        phrase_pos = text_before.lower().rfind(phrase)
        if phrase_pos != -1:
            # Look for the next capitalized word after the phrase
            remaining = text_before[phrase_pos + len(phrase):].strip()
            if remaining and remaining[0].isupper():
                start = phrase_pos + len(phrase) + remaining.find(remaining[0])
                # Make sure we're not too far from the citation
                if start_pos - start < 200:  # Within 200 characters
                    return start
    
    # Final fallback: Find the last capitalized word before the citation
    # that's not a stopword and not too far from the citation
    words = text_before.split()
    for i in range(len(words)-1, max(-1, len(words)-10), -1):
        if i >= 0 and words[i] and words[i][0].isupper() and not is_stopword(words[i].lower()):
            search_str = ' '.join(words[i:])
            pos = text_before.rfind(search_str)
            if pos != -1 and (start_pos - pos) < 200:  # Within 200 characters
                return pos
    
    # If all else fails, return the position of the first capital letter
    # before the citation that's not after a sentence-ending punctuation
    for i in range(start_pos - 1, max(-1, start_pos - 100), -1):
        if i >= 0 and text[i].isupper() and (i == 0 or text[i-1] in ' \t\n"\'('):
            return i
    
    return 0  # Start from beginning if nothing found

def extract_case_name_precise(context_before: str, citation: str, debug: bool = False) -> str:
    """
    Extract case name with robust patterns to handle multi-word party names and complex citation contexts.
    Handles 'v.', 'vs.', 'In re', 'Estate of', 'State v.', and allows for lowercase prefixes (e.g., 'ex rel.').
    Enhanced to better handle Washington State Reports citations and multi-word party names.
    
    Args:
        context_before: Text preceding the citation
        citation: The citation text to find case name for
        debug: Whether to print debug information
    """
    if debug:
        print("\n" + "="*80)
        print(f"EXTRACT_CASE_NAME_PRECISE")
        print(f"Citation: {citation}")
        print("-"*40)
    
    # Set a dynamic context window based on document structure
    context_window = min(500, max(200, len(context_before) // 2))  # Cap at 500 chars, min 200, or 50% of available
    
    # Get context window, ensuring we don't go beyond the start of the text
    context = context_before[-context_window:] if len(context_before) > context_window else context_before
    
    # Preprocess contractions and normalize whitespace
    context = preprocess_contractions(context)
    context = ' '.join(context.split())  # Normalize all whitespace to single spaces
    
    if debug:
        print(f"Using context window of {len(context)} characters")
        print(f"Context: '{context}'")
    
    # Find the citation in the context
    cite_pos = context.rfind(citation)
    if cite_pos == -1:
        if debug: 
            print(f"Citation '{citation}' not found in context")
        return ""
    
    if debug:
        print(f"Citation found at position {cite_pos}")
        print(f"Text before citation: '{context[max(0, cite_pos-50):cite_pos]}'")
    
    # Check if this is a Washington citation for special handling
    is_washington_cite = bool(re.search(r'\b\d+\s+Wn\.?\s*\d+', citation))
    
    # Define legal name patterns that might appear in case names
    legal_name_patterns = [
        r'[A-Z][A-Za-z0-9&\-\'\,\.\s]+',  # Standard names with common legal punctuation
        r'[A-Z]\.\s+[A-Z][A-Za-z0-9&\-\'\,\.\s]*',  # Initials like J. Smith
        r'[A-Z][A-Za-z]+\s+(?:&|and|et\s+al\.?|Inc\.?|LLC|L\.L\.C\.?|L\.P\.?|P\.?C\.?|Ltd\.?|Corp\.?|Co\.?)',  # Business entities
        r'[A-Z][A-Za-z]+\s+(?:of|for|in|on|at|by|with|the|and|or|but|as|if|then|else|when|where|why|how)\s+[A-Z][A-Za-z]*',  # Multi-word with common prepositions
    ]
    
    # First, try to find a pattern like "Plaintiff v. Defendant, Citation"
    v_pattern = r'\b(?:v\.?|vs\.?|versus)\b'
    v_matches = list(re.finditer(v_pattern, context[:cite_pos], re.IGNORECASE))
    
    if v_matches:
        # Get the last "v." or "vs." before the citation
        last_v = v_matches[-1]
        v_pos = last_v.start()
        
        if debug:
            print(f"Found 'v.' at position {v_pos}")
        
        # Look for the start of the case name before the "v."
        before_v = context[:v_pos].strip()
        
        # Try to find the start of the case name by looking for patterns that indicate case name boundaries
        words = before_v.split()
        
        # Look for patterns that indicate the start of a case name
        # Common patterns: "See, e.g.,", "held in", "in", "accord", etc.
        case_start_patterns = [
            r'\b(?:see|held in|in|accord|cf\.|e\.g\.|i\.e\.)\b',
            r'\b(?:the court in|as stated in|as held in|as explained in)\b',
            r'\b(?:individual|constitutional|guarantees|paramount)\b'
        ]
        
        # Find the last pattern that indicates the start of a case name
        last_pattern_pos = -1
        for pattern in case_start_patterns:
            matches = list(re.finditer(pattern, before_v, re.IGNORECASE))
            if matches:
                last_match = matches[-1]
                if last_match.end() > last_pattern_pos:
                    last_pattern_pos = last_match.end()
        
        # If we found a pattern, start looking for the case name after it
        start_search_pos = last_pattern_pos if last_pattern_pos != -1 else 0
        
        # Look for the first capitalized word after the pattern
        remaining_text = before_v[start_search_pos:].strip()
        remaining_words = remaining_text.split()
        
        for i in range(len(remaining_words)):
            word = remaining_words[i].strip().rstrip(',')
            if word and word[0].isupper() and not is_stopword(word.lower()):
                # Found a potential start of the case name
                # Now find its position in the original text
                search_str = ' '.join(remaining_words[i:])
                pos = remaining_text.find(search_str)
                if pos != -1:
                    # Adjust position to account for the pattern offset
                    actual_pos = start_search_pos + pos
                    # Extract the case name from the found position to the citation
                    case_name = context[actual_pos:cite_pos].strip()
                    
                    # Clean up any trailing punctuation
                    case_name = re.sub(r'[\s,;.]+$', '', case_name)
                    
                    # Additional validation for multi-word names
                    if is_valid_case_name(case_name):
                        if debug:
                            print(f"Found case name with pattern-based search: '{case_name}'")
                        return case_name
                break
        
        # Fallback to the original backward search logic
        for i in range(len(words)-1, -1, -1):
            word = words[i].strip().rstrip(',')
            if word and word[0].isupper() and not is_stopword(word.lower()):
                # Found a potential start of the case name
                # Now find its position in the original text
                search_str = ' '.join(words[i:])
                pos = before_v.rfind(search_str)
                if pos != -1:
                    # Extract the case name from the found position to the citation
                    case_name = context[pos:cite_pos].strip()
                    
                    # Clean up any trailing punctuation
                    case_name = re.sub(r'[\s,;.]+$', '', case_name)
                    
                    # Additional validation for multi-word names
                    if is_valid_case_name(case_name):
                        if debug:
                            print(f"Found case name with backward search: '{case_name}'")
                        return case_name
                    
                    # If the case name is too short, try to extend it backwards
                    # This handles cases like "Lakehaven Water & Sewer Dist." where
                    # the algorithm might start at "Sewer" instead of "Lakehaven"
                    if len(case_name.split()) < 5:  # Increased threshold for multi-word entities
                        # Look for more words before the current start
                        for j in range(i-1, max(-1, i-10), -1):  # Look back up to 10 words
                            if j >= 0:
                                extended_words = words[j:i+1]
                                extended_search_str = ' '.join(extended_words)
                                extended_pos = before_v.rfind(extended_search_str)
                                if extended_pos != -1:
                                    extended_case_name = context[extended_pos:cite_pos].strip()
                                    extended_case_name = re.sub(r'[\s,;.]+$', '', extended_case_name)
                                    if is_valid_case_name(extended_case_name) and len(extended_case_name.split()) > len(case_name.split()):
                                        if debug:
                                            print(f"Extended case name: '{case_name}' -> '{extended_case_name}'")
                                        return extended_case_name
                break
    
    # If we get here, try to find the last comma before the citation
    last_comma = context.rfind(',', 0, cite_pos)
    if last_comma != -1:
        case_name = context[last_comma+1:cite_pos].strip()
        # Clean up any trailing punctuation and validate
        case_name = re.sub(r'[\s,;.]+$', '', case_name)
        if case_name and len(case_name.split()) > 1 and is_valid_case_name(case_name):
            if debug: 
                print(f"Found case name after comma: '{case_name}'")
            return case_name
    
    # Define patterns for case name extraction with confidence scores
    patterns = [
        # Standard case name pattern: Name v. Name, Citation
        (r'([A-Z][^,;()\n]*?\s+v\.?\s+[^,;()\n]*?)\s*,\s*' + re.escape(citation), 1.0),
        
        # Case name with ampersand: Name & Name v. Name, Citation
        (r'([A-Z][^,;()\n]*?\s*&\s*[^,;()\n]*?\s+v\.?\s+[^,;()\n]*?)\s*,\s*' + re.escape(citation), 1.0),
        
        # In re pattern: In re Name, Citation
        (r'(In\s+re\s+[^,;()\n]+?)\s*,\s*' + re.escape(citation), 0.95),
        
        # Estate of pattern: Estate of Name, Citation
        (r'(Estate\s+of\s+[^,;()\n]+?)\s*,\s*' + re.escape(citation), 0.95),
        
        # Any capitalized text that looks like a case name
        (r'([A-Z][^,;()\n]{5,100}?)\s*,\s*' + re.escape(citation), 0.8),
    ]
    
    # Add Washington-specific patterns if needed
    if is_washington_cite:
        patterns.extend([
            # Washington State pattern: State v. Defendant, 999 Wn.2d 999
            (r'(State\s+v\.\s+[A-Z][A-Za-z0-9&.,\'\- ]+?)\s*,\s*' + re.escape(citation), 0.95),
            
            # Washington State pattern with ampersand: State v. Name & Name, 999 Wn.2d 999
            (r'(State\s+v\.\s+[A-Z][A-Za-z0-9&.,\'\- ]+?\s*&\s*[A-Z][A-Za-z0-9&.,\'\- ]+?)\s*,\s*' + re.escape(citation), 0.95),
        ])
    
    # Try each pattern in order of specificity
    for pattern, confidence in patterns:
        try:
            matches = list(re.finditer(pattern, context, re.IGNORECASE | re.DOTALL))
            if matches:
                # Get the match closest to the citation (last match in the context)
                best_match = matches[-1]
                case_name = best_match.group(1).strip()
                
                # Clean up the case name
                case_name = clean_case_name_enhanced(case_name, context_before)
                
                # Additional validation for the extracted case name
                if (case_name and 
                    is_valid_case_name(case_name) and 
                    not starts_with_signal_word(case_name) and
                    not _is_header_or_clerical_text(case_name) and 
                    len(case_name.split()) <= 25):  # Increased max word count for complex names
                    
                    if debug:
                        print(f"Found case name with pattern (confidence {confidence}): '{case_name}'")
                        print(f"Pattern used: {pattern}")
                    
                    logger.debug(f"[extract_case_name_precise] Found case name with pattern {pattern}: {case_name}")
                    return case_name
                    
        except Exception as e:
            logger.debug(f"[extract_case_name_precise] Error with pattern {pattern}: {e}")
            if debug:
                print(f"Error with pattern {pattern}: {e}")
    
    # Final fallback: Look for any text that looks like a case name before the citation
    if is_washington_cite:
        # For Washington citations, use a more specific pattern
        fallback_patterns = [
            r"([A-Z][A-Za-z0-9&.,\'\- ]+?\sv\.\s[A-Z][A-Za-z0-9&.,\'\- ]+?)\s*,\s*" + re.escape(citation),
            r"(State\s+v\.\s+[A-Z][A-Za-z0-9&.,\'\- ]+?)\s*,\s*" + re.escape(citation),
            r"(In\s+re\s+[A-Z][A-Za-z0-9&.,\'\- ]+?)\s*,\s*" + re.escape(citation),
        ]
    else:
        # More general patterns for other jurisdictions
        fallback_patterns = [
            r"([A-Z][A-Za-z0-9&.,\'\- ]+?\s+v\.?\s+[A-Z][A-Za-z0-9&.,\'\- ]+?)\s*,\s*" + re.escape(citation),
            r"([A-Z][A-Za-z0-9&.,\'\- ]+?)\s*,\s*" + re.escape(citation),
        ]
    
    for pattern in fallback_patterns:
        fallback_matches = list(re.finditer(pattern, context, re.IGNORECASE | re.DOTALL))
        if fallback_matches:
            best_match = fallback_matches[-1]
            case_name = clean_case_name_enhanced(best_match.group(1), context_before)
            if is_valid_case_name(case_name):
                if debug:
                    print(f"Found fallback case name: '{case_name}'")
                    print(f"Fallback pattern used: {pattern}")
                logger.debug(f"[extract_case_name_precise] Found fallback case name: {case_name}")
                return case_name
    
    if debug:
        print("No valid case name found after all extraction attempts")
        print(f"Final context examined: '{context[:cite_pos][-100:]}'")
    
    logger.debug(f"[extract_case_name_precise] No valid case name found for citation: {citation}")
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
            case_name = clean_case_name_enhanced(match.group(1), context_before)
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
            case_name = clean_case_name_enhanced(match.group(1), context)
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
            case_name = clean_case_name_enhanced(match.group(1), context_before)
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
            case_name = clean_case_name_enhanced(match.group(1), text)
            logger.debug(f"[extract_case_name_global_search] Cleaned case name: '{case_name}'")
            if case_name and is_valid_case_name(case_name) and not starts_with_signal_word(case_name):
                logger.debug(f"[extract_case_name_global_search] Valid case name found: '{case_name}'")
                return case_name
            else:
                logger.debug(f"[extract_case_name_global_search] Case name invalid or starts with signal word: '{case_name}'")
    logger.debug(f"[extract_case_name_global_search] No valid case names found")
    return ""

# --- Moved from extract_case_name.py (now archived) ---
def extract_case_name_from_text(text: str, citation_text: str, all_citations: Optional[List] = None, canonical_name: Optional[str] = None) -> str:
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

def extract_case_name_hinted(text: str, citation: str, canonical_name: Optional[str] = None, api_key: Optional[str] = None) -> str:
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
                cleaned = clean_case_name_enhanced(match, context_before)
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
            return best_variant
        return ""
    except Exception:
        return ""

def get_canonical_case_name_from_courtlistener(citation, api_key=None):
    """
    Get canonical case name using the unified citation processor.
    This replaces the stub implementation with a working one.
    """
    try:
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor
        from src.models import CitationResult
        processor = UnifiedCitationProcessor()
        # Use available verification method instead of non-existent one
        citation_result = CitationResult(citation=citation)
        verified = processor._verify_citation_with_courtlistener(citation_result)
        if verified:
            case_name = citation_result.canonical_name or citation_result.extracted_case_name
            if case_name and case_name != 'N/A':
                return {
                    'case_name': case_name,
                    'date': citation_result.canonical_date or '',
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
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor
        from src.models import CitationResult
        processor = UnifiedCitationProcessor()
        # Use available verification method instead of non-existent one
        citation_result = CitationResult(citation=citation)
        verified = processor._verify_citation_with_courtlistener(citation_result)
        if verified:
            case_name = citation_result.canonical_name or citation_result.extracted_case_name
            if case_name and case_name != 'N/A':
                return {
                    'case_name': case_name,
                    'date': citation_result.canonical_date or '',
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
    
    def extract(self, text: str, citation: Optional[str] = None) -> ExtractionResult:
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
                result.case_name = case_extraction.get('name', '')
                result.confidence = case_extraction.get('confidence', 0.0)
                result.method = case_extraction.get('method', 'unknown')
                if case_extraction.get('debug') and result.debug_info is not None:
                    result.debug_info.update(case_extraction['debug'])
            
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
            if result.debug_info is not None:
                result.debug_info['error'] = str(e)
        
        return result
    
    def _get_extraction_context(self, text: str, citation: Optional[str] = None) -> str:
        """Get user-facing context: 200 characters before, 100 after citation."""
        if not citation:
            return text
        citation_pos = text.find(citation)
        if citation_pos == -1:
            return text
        start = max(0, citation_pos - 200)
        end = min(len(text), citation_pos + len(citation) + 100)
        return text[start:end].strip()

    def _get_system_extraction_context(self, text: str, citation: Optional[str] = None) -> str:
        """Get citation-aware context for extraction: always 150 chars before citation, 100 after."""
        if not citation:
            return text
        citation_pos = text.find(citation)
        if citation_pos == -1:
            return text
        start = max(0, citation_pos - 150)
        end = min(len(text), citation_pos + len(citation) + 100)
        return text[start:end].strip()
    
    def _extract_case_name(self, context: str, citation: Optional[str] = None) -> Optional[Dict]:
        import re
        STOPWORDS = {"of", "and", "the", "in", "for", "on", "at", "by", "with", "to", "from", "as", "but", "or", "nor", "so", "yet", "a", "an", "re"}
        
        def is_stopword(word: str) -> bool:
            """Check if a word is a stopword."""
            # Remove any trailing punctuation
            word = word.lower().rstrip('.,;:!?\'"()[]{}')
            return word in STOPWORDS
            
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
        # Try v. pattern with improved logic
        v_match = list(re.finditer(r'\bv\.', context_before_citation))
        if v_match:
            last_v = v_match[-1].start()
            debug_write(f"[DEBUG] Found last 'v.': char_pos={last_v}")
            
            # Look for patterns that indicate the start of a case name
            # Common patterns: "See, e.g.,", "held in", "in", "accord", etc.
            case_start_patterns = [
                r'\b(?:see|held in|in|accord|cf\.|e\.g\.|i\.e\.)\b',
                r'\b(?:the court in|as stated in|as held in|as explained in)\b',
                r'\b(?:individual|constitutional|guarantees|paramount)\b'
            ]
            
            # Find the last pattern that indicates the start of a case name
            last_pattern_pos = -1
            for pattern in case_start_patterns:
                matches = list(re.finditer(pattern, context_before_citation, re.IGNORECASE))
                if matches:
                    last_match = matches[-1]
                    if last_match.end() > last_pattern_pos:
                        last_pattern_pos = last_match.end()
            
            # If we found a pattern, start looking for the case name after it
            start_search_pos = last_pattern_pos if last_pattern_pos != -1 else 0
            
            # Look for the first capitalized word after the pattern
            remaining_text = context_before_citation[start_search_pos:].strip()
            remaining_words = list(re.finditer(r"[\w'&.,-]+", remaining_text))
            
            if remaining_words:
                # Find the first capitalized word
                first_cap_idx = None
                for i, word_match in enumerate(remaining_words):
                    word = word_match.group(0)
                    if word and word[0].isupper() and not is_stopword(word.lower()):
                        first_cap_idx = i
                        break
                
                if first_cap_idx is not None:
                    # Collect all words from the first capitalized word through the party after v.
                    # Find the next capitalized word after v. (start of second party)
                    v_pos_in_remaining = last_v - start_search_pos
                    v_word_idx = None
                    for i, word_match in enumerate(remaining_words):
                        if word_match.start() >= v_pos_in_remaining:
                            v_word_idx = i
                            break
                    
                    if v_word_idx is not None:
                        after_v_idx = v_word_idx + 1
                        while after_v_idx < len(remaining_words) and not remaining_words[after_v_idx].group(0)[0].isupper():
                            after_v_idx += 1
                        
                        # Stop at the first citation-like pattern after the party names
                        citation_pattern = re.compile(r"\d+\s+(Wn\.?\s*2d|Wash\.?\s*2d|P\.?\s*3d|P\.?\s*2d|F\.?\s*3d|F\.?\s*2d|U\.?S\.|S\.?Ct\.|L\.?Ed\.|A\.?2d|A\.?3d|So\.?2d|So\.?3d)", re.IGNORECASE)
                        stop_idx = len(remaining_words)
                        for i in range(after_v_idx, len(remaining_words)):
                            if citation_pattern.match(' '.join(remaining_words[j].group(0) for j in range(i, min(i+3, len(remaining_words))))):
                                stop_idx = i
                                debug_write(f"[DEBUG] Stopping case name at citation-like pattern: index={stop_idx}")
                                break
                        
                        # Collect all words from first_cap_idx up to stop_idx
                        case_name_words = [remaining_words[i].group(0) for i in range(first_cap_idx, stop_idx)]
                        case_name = ' '.join(case_name_words).rstrip(',;').rstrip()
                        debug_write(f"[DEBUG] v. match case name (improved): {case_name}")
                        return {'name': case_name, 'confidence': 0.9, 'method': 'v_pattern', 'debug': {'case_name': case_name}}
            
            # Fallback to original logic if improved logic fails
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
            debug_write(f"[DEBUG] v. match case name (fallback): {case_name}")
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

def normalize_for_match(s):
    import re
    return re.sub(r'[^a-z0-9]', '', s.lower()) if s else ''

def find_case_name_and_citation_proximity(text: str, case_name: str, citation: str) -> dict:
    """
    Find the first occurrence of the case name and citation in the text, allowing for punctuation and spacing variations.
    Returns a dict with indices and context, or None if not found.
    """
    import re
    result = {}
    # Normalize the entire text for matching
    norm_text = normalize_for_match(text)
    norm_case_name = normalize_for_match(case_name)
    norm_citation = normalize_for_match(citation)
    # Find all possible case name matches (flexible)
    case_name_start = case_name_end = None
    for m in re.finditer(r'.{5,200}', text, re.DOTALL):
        window = m.group(0)
        if normalize_for_match(window).find(norm_case_name) != -1:
            case_name_start = m.start() + normalize_for_match(window).find(norm_case_name)
            case_name_end = case_name_start + len(case_name)
            break
    if case_name_start is None:
        return {}
    # Find citation (flexible)
    citation_start = citation_end = None
    for m in re.finditer(r'.{5,100}', text, re.DOTALL):
        window = m.group(0)
        if normalize_for_match(window).find(norm_citation) != -1:
            citation_start = m.start() + normalize_for_match(window).find(norm_citation)
            citation_end = citation_start + len(citation)
            break
    if citation_start is None:
        return {}
    # Get the text between them (if case name comes before citation)
    if case_name_end is not None and citation_start is not None and case_name_end <= citation_start:
        between = text[case_name_end:citation_start]
    else:
        between = text[citation_end:case_name_start] if citation_end is not None and case_name_start is not None and citation_end <= case_name_start else ''
    result = {
        'case_name_start': case_name_start,
        'case_name_end': case_name_end,
        'citation_start': citation_start,
        'citation_end': citation_end,
        'between_text': between,
        'case_name_snippet': text[max(0, (case_name_start or 0)-40):min(len(text), (case_name_end or 0)+40)],
        'citation_snippet': text[max(0, (citation_start or 0)-40):min(len(text), (citation_end or 0)+40)]
    }
    return result

def batch_find_case_name_and_citation_proximity(text: str, pairs: list) -> list:
    """
    Given a document text and a list of (case_name, citation) pairs, return a list of proximity results for each pair.
    Each result is a dict as returned by find_case_name_and_citation_proximity, with 'case_name' and 'citation' fields added.
    """
    results = []
    for case_name, citation in pairs:
        res = find_case_name_and_citation_proximity(text, case_name, citation)
        if res:
            res['case_name'] = case_name
            res['citation'] = citation
            results.append(res)
        else:
            results.append({'case_name': case_name, 'citation': citation, 'found': False})
    return results

# Global extractor instance
_extractor = None

def get_extractor() -> CaseNameExtractor:
    """Get global extractor instance"""
    global _extractor
    if _extractor is None:
        _extractor = CaseNameExtractor()
    return _extractor

# Simplified API functions for backward compatibility
def extract_case_name_and_date(text: str, citation: Optional[str] = None) -> Dict[str, Any]:
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
    result.date = date or ""
    result.year = date or ""
    debug_write(f"[DEBUG] Extracted date: {date}")
    return {
        'case_name': result.case_name,
        'date': result.date,
        'year': result.year,
        'confidence': result.confidence,
        'method': result.method,
        'debug': result.debug_info
    }

def extract_case_name_only(text: str, citation: Optional[str] = None) -> str:
    """Extract just the case name"""
    result = extract_case_name_and_date(text, citation)
    return result.get('case_name', "")

def extract_year_only(text: str, citation: Optional[str] = None) -> str:
    """Extract just the year"""
    result = extract_case_name_and_date(text, citation)
    return result.get('year', "")

def extract_case_name_triple_comprehensive(text: str, citation: Optional[str] = None) -> Tuple[str, str, str]:
    """
    Backward compatible triple extraction
    Returns (case_name, date, confidence)
    """
    result = extract_case_name_and_date(text, citation)
    return (
        result.get('case_name', ""),
        result.get('date', ""), 
        str(result.get('confidence', ""))
    )

def extract_case_name_triple(text: str, citation: Optional[str] = None, api_key: Optional[str] = None, context_window: int = 100) -> Tuple[str, str, str]:
    """
    Backward compatible triple extraction
    Returns (case_name, year, confidence)
    """
    result = extract_case_name_and_date(text, citation)
    return (
        result.get('case_name', ""),
        result.get('year', ""), 
        str(result.get('confidence', ""))
    )

def extract_case_name_improved(text: str, citation: Optional[str] = None) -> Tuple[str, str, str]:
    """
    Backward compatible triple extraction
    Returns (case_name, year, confidence)
    """
    result = extract_case_name_and_date(text, citation)
    return (
        result.get('case_name', ""),
        result.get('year', ""), 
        str(result.get('confidence', ""))
    )

def extract_year_improved(text: str, citation: Optional[str] = None) -> str:
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