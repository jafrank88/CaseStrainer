import re
from typing import Optional, Tuple
import logging
import string
from rapidfuzz import fuzz

# Set up debug logging
logging.basicConfig(filename='case_name_debug.log', level=logging.DEBUG, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

def log_debug(message):
    """Helper function to log debug messages to file"""
    logging.debug(message)
    print(f"[DEBUG] {message}")

def extract_in_re_case_name_from_context(context_before: str, citation_text: str = "") -> str:
    """
    Specifically look for "in re" case names within 15 words before a citation.
    This handles cases where "in re" appears close to the citation without other citations in between.
    
    Args:
        context_before: Text that appears before the citation
        citation_text: The actual citation text (for additional context)
        
    Returns:
        str: The extracted "in re" case name or empty string if not found
    """
    if not context_before:
        return ""
    
    # Normalize whitespace
    context_before = re.sub(r'\s+', ' ', context_before)
    
    # Look at the last 300 characters (approximately 20 words) for longer case names
    context = context_before[-300:]
    
    # Pattern to find "in re" followed by a case name
    # This looks for "in re" (case insensitive) followed by capitalized words
    # and stops at common citation indicators or punctuation
    in_re_pattern = r'(?:^|\s)(in\s+re\s+[A-Z][A-Za-z\'\-\s]+(?:[A-Za-z\'\-\s]+)*)'
    
    matches = list(re.finditer(in_re_pattern, context, re.IGNORECASE | re.DOTALL))
    if matches:
        # Return the last match (closest to citation)
        case_name = matches[-1].group(1).strip()
        log_debug(f"Raw 'In re' match: {repr(case_name)}")
        # Clean up the case name
        case_name = clean_case_name(case_name)
        log_debug(f"Cleaned 'In re' case name: {repr(case_name)}")
        if case_name:
            return case_name
    
    # Also try a more flexible pattern that looks for "in re" anywhere in the context
    # but ensures it's not followed by another citation
    flexible_pattern = r'(?:^|\s)(in\s+re\s+[A-Z][A-Za-z\'\-\s]+(?:[A-Za-z\'\-\s]+)*)'
    
    matches = list(re.finditer(flexible_pattern, context, re.IGNORECASE | re.DOTALL))
    if matches:
        # Get the last match
        potential_case_name = matches[-1].group(1).strip()
        
        # Check if there are any citations between this "in re" and the target citation
        # by looking for citation patterns in the text after this match
        match_end = matches[-1].end()
        text_after_match = context[match_end:]
        
        # Citation patterns to check for - updated for proper Bluebook format
        citation_patterns = [
            r'\d+\s+[A-Z]\.\s*\d+',  # e.g., "123 F. 456"
            r'\d+\s+[A-Z]{2,}\.\s*\d+',  # e.g., "123 Wash. 456"
            r'\d+\s+U\.\s*S\.\s*\d+',  # e.g., "123 U. S. 456"
            r'\d+\s+S\.\s*Ct\.\s*\d+',  # e.g., "123 S. Ct. 456" or "123 S.Ct. 456"
            r'\d+\s+L\.\s*Ed\.\s*\d+\s*\w+',  # e.g., "123 L. Ed. 2d 456" or "123 L.Ed.2d 456"
            r'\d+\s+L\.\s*Ed\.\s*\d+',  # e.g., "123 L. Ed. 456" or "123 L.Ed. 456"
        ]
        
        # If no citations found between "in re" and target citation, use this case name
        has_intervening_citation = False
        for pattern in citation_patterns:
            if re.search(pattern, text_after_match):
                has_intervening_citation = True
                break
        
        if not has_intervening_citation:
            case_name = clean_case_name(potential_case_name)
            if case_name and not is_citation_like(case_name):
                return case_name
    
    return ""


# Add a global cache for recently extracted case names to handle "Id." citations
_recent_case_names = []

def extract_case_name_from_context(context_before: str, citation_text: str = "") -> str:
    """
    Attempt to extract a probable case name from the text before a citation.
    Looks for patterns like 'Smith v. Jones', 'In re Estate of ...', etc.
    Returns the case name if found, otherwise returns ''.
    
    Args:
        context_before: Text that appears before the citation
        citation_text: The actual citation text (for additional context)
        
    Returns:
        str: The extracted case name or empty string if not found
    """
    global _recent_case_names
    
    if not context_before:
        return ""
    
    # Check if this is an "Id." citation
    context_lower = context_before.lower().strip()
    if context_lower.startswith('id.') or context_lower == 'id':
        # Return the most recent case name if available
        if _recent_case_names:
            return _recent_case_names[-1]
        return ""
    
    # Normalize all whitespace (including newlines, tabs, multiple spaces) to a single space
    context_before = re.sub(r'\s+', ' ', context_before)
    
    # Look for v.-style case name in the last 500 characters before the citation
    context = context_before[-500:]
    
    # Token-based extraction for v.-style case names
    tokens = context.split()
    v_indices = [i for i, t in enumerate(tokens) if t.lower() in {'v.', 'vs.', 'versus'}]
    if v_indices:
        idx = v_indices[-1]
        # Take up to 7 tokens before and after 'v.'
        before = tokens[max(0, idx-7):idx]
        after = tokens[idx+1:idx+8]
        # Remove leading context words from before
        context_words = {'the', 'in', 'as', 'at', 'by', 'for', 'on', 'with', 'to', 'from', 'of', 'decision', 'court', 'case', 'held'}
        while before and before[0].lower().strip(string.punctuation) in context_words:
            before = before[1:]
        # Remove trailing punctuation from after
        after_clean = []
        # Expanded abbreviation set for legal contexts
        abbrev_set = {
            'U.S.', 'D.C.', 'N.Y.', 'Cal.', 'Fla.', 'Ill.', 'Tex.', 'Ala.', 'Ariz.', 'Ark.', 'Colo.', 'Conn.', 'Del.', 'Ga.', 
            'Idaho', 'Ind.', 'Iowa', 'Kan.', 'Ky.', 'La.', 'Md.', 'Mass.', 'Mich.', 'Minn.', 'Miss.', 'Mo.', 'Mont.', 'Neb.', 
            'Nev.', 'N.H.', 'N.J.', 'N.M.', 'N.C.', 'N.D.', 'Ohio', 'Okla.', 'Ore.', 'Pa.', 'R.I.', 'S.C.', 'S.D.', 'Tenn.', 
            'Vt.', 'Va.', 'Wash.', 'W.Va.', 'Wis.', 'Wyo.', 'Puget', 'Sound', 'Reg', 'Techsystems', 'Transportation', 'Ecology', 
            'Campbell', 'Gwinn', 'Holdings', 'Industries', 'Security', 'Retirement', 'Systems', 'Forfeiture', 'Chevrolet', 
            'Chevelle', 'Medical', 'Center', 'Building', 'Industry', 'Ass\'n', 'Robinson', 'Silva-Baltazar', 'Pierce', 'County',
            'Wilson', 'Court', 'Ltd.', 'Partnership', 'Tony', 'Maroni\'s', 'Wenatchee', 'Valley', 'Utter', 'Association'
        }
        for word in after:
            w = word.strip(',;:')
            if not w:
                continue
            after_clean.append(w)
            # Only break if the word ends with a period and is not a known abbreviation
            # Also check if it's a single character followed by period (like "v.")
            if w[-1] == '.' and w not in abbrev_set and len(w) > 2:
                break
            if w[-1] in ';,:':
                break
        if before and after_clean:
            case_name = ' '.join(before + [tokens[idx]] + after_clean)
            case_name = clean_case_name(case_name)
            if (len(case_name) > 5 and
                ' v.' in case_name and
                not any(word in case_name.lower() for word in ['exhibit', 'deposition', 'evidence', 'testimony', 'allowing', 'commentary', 'argument', 'federal rules'])):
                # Add to recent case names cache
                _recent_case_names.append(case_name)
                # Keep only the last 10 case names
                if len(_recent_case_names) > 10:
                    _recent_case_names = _recent_case_names[-10:]
                return case_name
    
    # Enhanced patterns for case name extraction - more robust to line breaks and whitespace
    patterns = [
        # Improved pattern to handle multi-word party names and trailing commas
        r"([A-Z][A-Za-z'\-\s,\.]+?\s+v\.\s+[A-Z][A-Za-z'\-\s,\.]+?)(?:\s*[,;]|\s*$)",
        r"([A-Z][A-Za-z'\-\s,\.]+?\s+vs\.\s+[A-Z][A-Za-z'\-\s,\.]+?)(?:\s*[,;]|\s*$)",
        r"([A-Z][A-Za-z'\-\s,\.]+?\s+versus\s+[A-Z][A-Za-z'\-\s,\.]+?)(?:\s*[,;]|\s*$)",
        # Original patterns as fallback
        r"([A-Z][^,\n]+?\s+v\.\s+[^,\n]+)",
        r"([A-Z][^,\n]+?\s+vs\.\s+[^,\n]+)",
        r"([A-Z][^,\n]+?\s+versus\s+[^,\n]+)",
        r"(?:^|\s)(In\s+re\s+[A-Z][A-Za-z'\-\s,\.]+(?:\s+[A-Z][A-Za-z'\-\s,\.]+)*)",
        r"(?:^|\s)(Estate\s+of\s+[A-Z][A-Za-z'\-\s,\.]+(?:\s+[A-Z][A-Za-z'\-\s,\.]+)*)",
        r"(?:^|\s)(Matter\s+of\s+[A-Z][A-Za-z'\-\s,\.]+(?:\s+[A-Z][A-Za-z'\-\s,\.]+)*)",
        r"(?:^|\s)(Ex\s+parte\s+[A-Z][A-Za-z'\-\s,\.]+(?:\s+[A-Z][A-Za-z'\-\s,\.]+)*)",
        r"(?:^|\s)([A-Z][A-Za-z'\-\s,\.]+\s+ex\s+rel\.\s+[A-Z][A-Za-z'\-\s,\.]+)",
        r"(?:^|\s)(People\s+v\.\s+[A-Z][A-Za-z'\-\s,\.]+)",
        r"(?:^|\s)(State\s+v\.\s+[A-Z][A-Za-z'\-\s,\.]+)",
        r"(?:^|\s)(United\s+States\s+v\.\s+[A-Z][A-Za-z'\-\s,\.]+)",
        r"(?:^|\s)([A-Z][A-Za-z'\-\s,\.]+\s+et\s+al\.\s+v\.\s+[A-Z][A-Za-z'\-\s,\.]+)",
        r"(?:^|\s)([A-Z][A-Za-z'\-\s,\.]+\s*&\s*[A-Z][A-Za-z'\-\s,\.]+\s+v\.\s+[A-Z][A-Za-z'\-\s,\.]+)",
    ]
    case_name_patterns = [
        r"([A-Z][A-Za-z'\-\s,\.]+\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z'\-\s,\.]+)",
        r"(In\s+re\s+[A-Z][A-Za-z'\-\s,\.]+(?:\s+[A-Z][A-Za-z'\-\s,\.]+)*)",
        r"(Estate\s+of\s+[A-Z][A-Za-z'\-\s,\.]+(?:\s+[A-Z][A-Za-z'\-\s,\.]+)*)",
        r"(Matter\s+of\s+[A-Z][A-Za-z'\-\s,\.]+(?:\s+[A-Z][A-Za-z'\-\s,\.]+)*)",
        r"(Ex\s+parte\s+[A-Z][A-Za-z'\-\s,\.]+(?:\s+[A-Z][A-Za-z'\-\s,\.]+)*)",
    ]
    for pattern in patterns:
        matches = list(re.finditer(pattern, context, re.IGNORECASE | re.DOTALL))
        if matches:
            case_name = matches[-1].group(1).strip()
            case_name = clean_case_name(case_name)
            if case_name:
                # Additional validation: make sure it looks like a case name
                if ' v. ' in case_name and not any(word in case_name.lower() for word in ['exhibit', 'deposition', 'evidence', 'testimony', 'allowing', 'commentary', 'argument']):
                    # Add to recent case names cache
                    _recent_case_names.append(case_name)
                    # Keep only the last 10 case names
                    if len(_recent_case_names) > 10:
                        _recent_case_names = _recent_case_names[-10:]
                    return case_name
    in_re_case_name = extract_in_re_case_name_from_context(context_before, citation_text)
    if in_re_case_name:
        # Add to recent case names cache
        _recent_case_names.append(in_re_case_name)
        # Keep only the last 10 case names
        if len(_recent_case_names) > 10:
            _recent_case_names = _recent_case_names[-10:]
        return in_re_case_name
    if citation_text:
        log_debug(f"Trying fallback extraction for citation: {citation_text}")
        citation_index = context_before.find(citation_text)
        if citation_index != -1:
            line_start = context_before.rfind('\n', 0, citation_index)
            line_end = context_before.find('\n', citation_index)
            if line_start == -1:
                line_start = 0
            else:
                line_start += 1
            if line_end == -1:
                line_end = len(context_before)
            line = context_before[line_start:line_end]
            log_debug(f"Extracted line: {repr(line)}")
            for pattern in patterns:
                matches = list(re.finditer(pattern, line, re.IGNORECASE | re.DOTALL))
                if matches:
                    case_name = matches[-1].group(1).strip()
                    case_name = clean_case_name(case_name)
                    if case_name:
                        log_debug(f"Found case name with pattern: {case_name}")
                        # Add to recent case names cache
                        _recent_case_names.append(case_name)
                        # Keep only the last 10 case names
                        if len(_recent_case_names) > 10:
                            _recent_case_names = _recent_case_names[-10:]
                        return case_name
            before_citation = line.split(citation_text)[0].strip()
            log_debug(f"Before citation: {repr(before_citation)}")
            fallback_pattern = r"([A-Z][A-Za-z0-9'\-\s,\.]+\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9'\-\s,\.]+)"
            log_debug(f"Using fallback pattern: {fallback_pattern}")
            matches = list(re.finditer(fallback_pattern, before_citation, re.IGNORECASE | re.DOTALL))
            log_debug(f"Found {len(matches)} matches with fallback pattern")
            if matches:
                case_name = matches[-1].group(1).strip()
                case_name = clean_case_name(case_name)
                if case_name:
                    log_debug(f"Matched case name: {repr(case_name)}")
                    # Add to recent case names cache
                    _recent_case_names.append(case_name)
                    # Keep only the last 10 case names
                    if len(_recent_case_names) > 10:
                        _recent_case_names = _recent_case_names[-10:]
                    return case_name
            else:
                log_debug("No matches found with fallback pattern")
            in_re_pattern = r"(In\s+re[\w\s,\.''\-]*)"
            log_debug(f"Using In re fallback pattern: {in_re_pattern}")
            in_re_matches = list(re.finditer(in_re_pattern, before_citation, re.IGNORECASE | re.DOTALL))
            log_debug(f"Found {len(in_re_matches)} In re matches with fallback pattern")
            if in_re_matches:
                in_re_case_name = in_re_matches[-1].group(1).strip()
                in_re_case_name = clean_case_name(in_re_case_name)
                if in_re_case_name:
                    log_debug(f"Matched In re case name: {repr(in_re_case_name)}")
                    # Add to recent case names cache
                    _recent_case_names.append(in_re_case_name)
                    # Keep only the last 10 case names
                    if len(_recent_case_names) > 10:
                        _recent_case_names = _recent_case_names[-10:]
                    return in_re_case_name
            else:
                log_debug("No In re matches found with fallback pattern")
        else:
            log_debug(f"Citation '{citation_text}' not found in context")
            # Try to find any case name in the broader context
            broader_context = context_before[-1000:]  # Look at last 1000 characters
            log_debug(f"Searching broader context for case names")
            
            # Try v.-style patterns in broader context
            v_patterns = [
                r"([A-Z][A-Za-z0-9'\-\s,\.]+\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9'\-\s,\.]+)",
                r"([A-Z][A-Za-z0-9'\-\s,\.]+\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9'\-\s,\.]+[A-Za-z0-9'\-\s,\.]*)",
            ]
            for pattern in v_patterns:
                matches = list(re.finditer(pattern, broader_context, re.IGNORECASE | re.DOTALL))
                if matches:
                    case_name = matches[-1].group(1).strip()
                    case_name = clean_case_name(case_name)
                    if case_name and len(case_name) > 5:
                        log_debug(f"Found case name in broader context: {case_name}")
                        # Add to recent case names cache
                        _recent_case_names.append(case_name)
                        # Keep only the last 10 case names
                        if len(_recent_case_names) > 10:
                            _recent_case_names = _recent_case_names[-10:]
                        return case_name
            
            # Try In re patterns in broader context
            in_re_patterns = [
                r"(In\s+re\s+[A-Z][A-Za-z'\-\s,\.]+)",
                r"(In\s+re\s+[A-Z][A-Za-z'\-\s,\.]+[A-Za-z'\-\s,\.]*)",
            ]
            for pattern in in_re_patterns:
                matches = list(re.finditer(pattern, broader_context, re.IGNORECASE | re.DOTALL))
                if matches:
                    case_name = matches[-1].group(1).strip()
                    case_name = clean_case_name(case_name)
                    if case_name and len(case_name) > 5:
                        log_debug(f"Found In re case name in broader context: {case_name}")
                        # Add to recent case names cache
                        _recent_case_names.append(case_name)
                        # Keep only the last 10 case names
                        if len(_recent_case_names) > 10:
                            _recent_case_names = _recent_case_names[-10:]
                        return case_name
    return ""


def find_shared_case_name_for_citations(text: str, citations: list) -> dict:
    """
    Find a shared case name for multiple citations that likely refer to the same case.
    Handles scenarios like "Smith v. Arizona, 602 U.S. 779, 144 S. Ct. 1785, 219 L. Ed. 2d 420 (2024)"
    and "John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017)".
    Groups comma-separated citations and pinpoints within the same parenthesis and assigns the case name before the first citation to all in the group.
    
    Args:
        text: The full text containing the citations
        citations: List of citation dictionaries with 'citation' and 'start_index' fields
        
    Returns:
        dict: Mapping of citation text to case name
    """
    if not citations or len(citations) < 2:
        return {}
    
    def get_start_index(citation):
        start_idx = citation.get('start_index')
        return start_idx if start_idx is not None else 0
    
    sorted_citations = sorted(citations, key=get_start_index)
    result = {}
    n = len(sorted_citations)
    i = 0
    while i < n:
        group = [sorted_citations[i]]
        start_idx = get_start_index(sorted_citations[i])
        open_paren = text.rfind('(', 0, start_idx)
        close_paren = text.find(')', start_idx)
        group_end = i
        for j in range(i+1, n):
            prev_end = get_start_index(sorted_citations[j-1])
            curr_start = get_start_index(sorted_citations[j])
            between = text[prev_end:curr_start]
            # Allow comma, whitespace, and numbers (pinpoints) between citations
            if re.match(r'^[,\s\d]*$', between) and (open_paren == -1 or (curr_start < close_paren or close_paren == -1)):
                group.append(sorted_citations[j])
                group_end = j
            else:
                break
        first_citation = group[0]
        first_citation_text = first_citation['citation']
        first_citation_index = get_start_index(first_citation)
        pre_text = text[max(0, first_citation_index - 500):first_citation_index]
        shared_case_name = extract_case_name_from_context(pre_text, first_citation_text)
        if shared_case_name and not is_citation_like(shared_case_name):
            for c in group:
                result[c['citation']] = shared_case_name
        i = group_end + 1
    return result


def extract_case_name_from_text(text: str, citation_text: str, all_citations: list = None, canonical_name: str = None) -> Optional[str]:
    """
    Extract potential case name from text surrounding a citation.
    Uses multiple patterns and heuristics to find the most likely case name.
    If canonical_name is provided, use it as a hint to select the best candidate.
    
    Args:
        text: The full text containing the citation
        citation_text: The specific citation to find context for
        all_citations: Optional list of all citations found in the text (for shared case name detection)
        canonical_name: Optional canonical case name for hinted extraction
        
    Returns:
        str: The extracted case name or None if not found
    """
    log_debug(f"Starting extraction for citation: {citation_text}")
    log_debug(f"Full text length: {len(text)}")
    
    if not text or not citation_text:
        log_debug("Empty text or citation_text")
        return None
    
    # Find the citation in the text
    citation_index = text.find(citation_text)
    if citation_index <= 0:
        log_debug(f"Citation not found in text")
        return None
    
    log_debug(f"Citation found at index: {citation_index}")
    
    # If we have all citations, try to find a shared case name first
    if all_citations and len(all_citations) > 1:
        shared_case_names = find_shared_case_name_for_citations(text, all_citations)
        if citation_text in shared_case_names:
            log_debug(f"Found shared case name: {shared_case_names[citation_text]}")
            return shared_case_names[citation_text]
    
    # --- Hinted extraction if canonical_name is provided ---
    if canonical_name:
        best_candidate, score = extract_case_name_hinted(text, citation_text, canonical_name)
        if best_candidate and score > 60:  # Only use if reasonably similar
            log_debug(f"Hinted extraction selected: {best_candidate} (score {score})")
            return best_candidate
    
    # --- PRIORITY: Check for "in re" cases within 15 words of citation ---
    # Look at the text within 15 words (approximately 200 characters) before the citation
    pre_text_15_words = text[max(0, citation_index - 200):citation_index]
    log_debug(f"15-word context: {repr(pre_text_15_words)}")
    in_re_case_name = extract_in_re_case_name_from_context(pre_text_15_words, citation_text)
    if in_re_case_name:
        log_debug(f"Found 'in re' case name: {in_re_case_name}")
        return in_re_case_name
    
    # Determine if this citation is in a list context
    # Look for patterns that suggest a list of citations
    list_indicators = [
        r'\d+\s+[A-Z]\.\s*\d+',  # Citation pattern
        r'\d+\s+[A-Z]{2,}\.\s*\d+',  # State citation pattern
        r'\d+\s+[A-Z]\.\s*App\.\s*\d+',  # Appellate citation pattern
    ]
    
    # Check if there are multiple citations nearby
    nearby_text = text[max(0, citation_index - 100):citation_index + 100]
    citation_count = 0
    for pattern in list_indicators:
        citation_count += len(re.findall(pattern, nearby_text))
    
    # Use a much larger context window for case name extraction
    # This is crucial for Westlaw citations where case names may appear further back
    if citation_count > 2:
        context_window = 1000  # Increased for complex cases with multiple citations
    else:
        context_window = 1500  # Increased significantly for better case name capture
    
    log_debug(f"Using context window: {context_window}, citation count: {citation_count}")
    
    # Look for potential case name in the text before the citation
    pre_text = text[max(0, citation_index - context_window):citation_index]
    log_debug(f"Context window text length: {len(pre_text)}")
    log_debug(f"Context window text (last 200 chars): {repr(pre_text[-200:])}")
    
    # Try the enhanced context extraction first
    case_name = extract_case_name_from_context(pre_text, citation_text)
    log_debug(f"Context extraction result: {repr(case_name)}")
    if case_name and not is_citation_like(case_name):
        log_debug(f"Returning context extraction result: {case_name}")
        return case_name
    
    # If no case name found in the large context window, try a more aggressive search
    # Look for case name patterns in the entire text before the citation
    log_debug("No case name found in context window, trying aggressive search...")
    
    # Search for case name patterns in a larger window
    aggressive_window = min(3000, citation_index)  # Up to 3000 characters before citation
    aggressive_pre_text = text[max(0, citation_index - aggressive_window):citation_index]
    
    # Look for the most recent case name pattern in this larger window
    patterns = [
        r"([A-Z][^,\n]+?\s+v\.\s+[^,\n]+)",
        r"([A-Z][^,\n]+?\s+vs\.\s+[^,\n]+)",
        r"([A-Z][^,\n]+?\s+versus\s+[^,\n]+)",
        r"(?:^|\s)(In\s+re\s+[A-Z][A-Za-z'\-\s,\.]+(?:\s+[A-Z][A-Za-z'\-\s,\.]+)*)",
        r"(?:^|\s)(Estate\s+of\s+[A-Z][A-Za-z'\-\s,\.]+(?:\s+[A-Z][A-Za-z'\-\s,\.]+)*)",
        r"(?:^|\s)(Matter\s+of\s+[A-Z][A-Za-z'\-\s,\.]+(?:\s+[A-Z][A-Za-z'\-\s,\.]+)*)",
        r"(?:^|\s)(Ex\s+parte\s+[A-Z][A-Za-z'\-\s,\.]+(?:\s+[A-Z][A-Za-z'\-\s,\.]+)*)",
        r"(?:^|\s)([A-Z][A-Za-z'\-\s,\.]+\s+ex\s+rel\.\s+[A-Z][A-Za-z'\-\s,\.]+)",
        r"(?:^|\s)(People\s+v\.\s+[A-Z][A-Za-z'\-\s,\.]+)",
        r"(?:^|\s)(State\s+v\.\s+[A-Z][A-Za-z'\-\s,\.]+)",
        r"(?:^|\s)(United\s+States\s+v\.\s+[A-Z][A-Za-z'\-\s,\.]+)",
        r"(?:^|\s)([A-Z][A-Za-z'\-\s,\.]+\s+et\s+al\.\s+v\.\s+[A-Z][A-Za-z'\-\s,\.]+)",
        r"(?:^|\s)([A-Z][A-Za-z'\-\s,\.]+\s*&\s*[A-Z][A-Za-z'\-\s,\.]+\s+v\.\s+[A-Z][A-Za-z'\-\s,\.]+)",
    ]
    
    for pattern in patterns:
        matches = list(re.finditer(pattern, aggressive_pre_text, re.IGNORECASE | re.DOTALL))
        if matches:
            # Get the last match (closest to citation)
            case_name = matches[-1].group(1).strip()
            case_name = clean_case_name(case_name)
            if case_name and not is_citation_like(case_name):
                log_debug(f"Found case name with aggressive search: {case_name}")
                return case_name
    
    # If still no case name found, try looking for the citation in a sentence context
    log_debug("Trying sentence-level context extraction...")
    
    # Find the sentence containing the citation
    sentence_start = citation_index
    sentence_end = citation_index
    
    # Look for sentence boundaries
    for i in range(citation_index, -1, -1):
        if text[i] in '.!?':
            sentence_start = i + 1
            break
        if i == 0:
            sentence_start = 0
            break
    
    for i in range(citation_index, len(text)):
        if text[i] in '.!?':
            sentence_end = i + 1
            break
        if i == len(text) - 1:
            sentence_end = len(text)
            break
    
    sentence = text[sentence_start:sentence_end].strip()
    log_debug(f"Extracted sentence: {repr(sentence)}")
    
    # Look for case name patterns in the sentence
    for pattern in patterns:
        matches = list(re.finditer(pattern, sentence, re.IGNORECASE | re.DOTALL))
        if matches:
            case_name = matches[-1].group(1).strip()
            case_name = clean_case_name(case_name)
            if case_name and not is_citation_like(case_name):
                log_debug(f"Found case name in sentence: {case_name}")
                return case_name
    
    log_debug("No case name found with any method")
    return None


def is_citation_like(text: str) -> bool:
    """
    Check if the extracted text looks like a citation rather than a case name.
    
    Args:
        text: The text to check
        
    Returns:
        bool: True if the text looks like a citation, False otherwise
    """
    if not text:
        return True
    
    # Check for citation patterns
    citation_patterns = [
        r'\d+\s+[A-Z]\.\s*\d+',  # e.g., "123 F. 456"
        r'\d+\s+[A-Z]{2,}\.\s*\d+',  # e.g., "123 Wash. 456"
        r'\d+\s+[A-Z]\.\s*App\.\s*\d+',  # e.g., "123 Wash. App. 456"
        r'\d+\s+U\.\s*S\.\s*\d+',  # e.g., "123 U. S. 456"
        r'\d+\s+S\.\s*Ct\.\s*\d+',  # e.g., "123 S. Ct. 456"
        r'\d+\s+L\.\s*Ed\.\s*\d+',  # e.g., "123 L. Ed. 456"
        r'\d+\s+P\.\s*\d+',  # e.g., "123 P. 456"
        # Add patterns for common reporter abbreviations
        r'[A-Z]\.\s*Supp\.',  # e.g., "F. Supp."
        r'[A-Z]\.\s*[A-Z]\.',  # e.g., "U. S.", "S. Ct."
        r'[A-Z]\.\s*App\.',  # e.g., "Wash. App."
        r'[A-Z]\.\s*[A-Z]\.\s*[A-Z]\.',  # e.g., "L. Ed. 2d"
    ]
    
    for pattern in citation_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    # Check if text is too short to be a meaningful case name
    if len(text.strip()) < 5:
        return True
    
    # Check if text contains mostly numbers and punctuation
    alphanumeric_ratio = len(re.findall(r'[A-Za-z]', text)) / len(text) if text else 0
    if alphanumeric_ratio < 0.3:  # Less than 30% letters
        return True
    
    # Check if text looks like a reporter abbreviation (e.g., "F. Supp. 5")
    if re.match(r'^[A-Z]\.\s*[A-Za-z]+\.?\s*\d*$', text.strip()):
        return True
    
    return False


def clean_case_name(case_name: str) -> str:
    """
    Clean and normalize a case name by removing extra whitespace,
    punctuation, and other artifacts. Truncate to likely case name only.
    """
    if not case_name:
        return ""

    # Normalize whitespace first
    case_name = re.sub(r'\s+', ' ', case_name).strip()

    # Remove common introductory phrases (more comprehensive)
    intro_patterns = [
        r'^(?:the\s+)?(?:case\s+of\s+|supreme\s+court\s+in\s+|court\s+of\s+appeals\s+in\s+)',
        r'^(?:the\s+)?(?:washington\s+supreme\s+court\s+in\s+|washington\s+court\s+of\s+appeals\s+in\s+)',
        r'^(?:in\s+the\s+case\s+of\s+|in\s+the\s+matter\s+of\s+)',
        r'^(?:the\s+)?(?:matter\s+of\s+|proceeding\s+of\s+)',
        r'^(?:in\s+(?!re\b)|the\s+case\s+)',  # Don't remove 'in' if it's followed by 're'
        r'^(?:and\s+the\s+court\s+of\s+appeals\s+in\s+)',
    ]
    for pattern in intro_patterns:
        case_name = re.sub(pattern, '', case_name, flags=re.IGNORECASE)

    # Remove common artifacts that might appear at the end
    case_name = re.sub(r'\s+(?:case|matter|proceeding|action|petition)\s*$', '', case_name, flags=re.IGNORECASE)

    # Remove trailing descriptive text
    case_name = re.sub(r'\s+(?:was\s+decided|established|addressed|dealt\s+with).*$', '', case_name, flags=re.IGNORECASE)

    # Enhanced: Find and extract the actual case name pattern, removing any text before it
    # This handles cases like "I respectfully concur. City of Seattle v. Wiggins"
    case_name_patterns = [
        r"([A-Z][A-Za-z'\-\s,\.]+\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z'\-\s,\.]+)",
        r"(In\s+re\s+[A-Z][A-Za-z'\-\s,\.]+(?:\s+[A-Z][A-Za-z'\-\s,\.]+)*)",
        r"(Estate\s+of\s+[A-Z][A-Za-z'\-\s,\.]+(?:\s+[A-Z][A-Za-z'\-\s,\.]+)*)",
        r"(Matter\s+of\s+[A-Z][A-Za-z'\-\s,\.]+(?:\s+[A-Z][A-Za-z'\-\s,\.]+)*)",
        r"(Ex\s+parte\s+[A-Z][A-Za-z'\-\s,\.]+(?:\s+[A-Z][A-Za-z'\-\s,\.]+)*)",
    ]
    
    for pattern in case_name_patterns:
        match = re.search(pattern, case_name, re.IGNORECASE)
        if match:
            case_name = match.group(1).strip()
            break

    # If the result is still too long, truncate to first 12 words (increased from 8 for complex names)
    words = case_name.split()
    if len(words) > 12:
        case_name = ' '.join(words[:12])

    # Ensure proper capitalization for common legal terms
    # Special handling for "In re" to preserve proper capitalization
    if case_name.lower().startswith('in re'):
        # Ensure "In re" is properly capitalized
        case_name = re.sub(r'^in\s+re\b', 'In re', case_name, flags=re.IGNORECASE)
    else:
        # For other legal terms, use title case
        case_name = re.sub(r'\b(Ex parte|Ex rel|Matter of|Estate of)\b', lambda m: m.group(1).title(), case_name, flags=re.IGNORECASE)

    # Final cleanup - remove trailing punctuation but be careful about periods and commas within the name
    # Only remove trailing punctuation if it's not part of a pattern like "M.D." or "P.C."
    case_name = re.sub(r'[\.,;]\s*$', '', case_name).strip()
    
    # Additional cleanup: remove trailing punctuation that's not part of abbreviations
    # This handles cases where we might have trailing punctuation after the case name
    case_name = re.sub(r'[\.,;]\s*$', '', case_name).strip()

    return case_name


def extract_case_name_and_citation(text: str, citation_text: str) -> Tuple[Optional[str], str]:
    """
    Extract both case name and citation from text, ensuring they're properly associated.
    
    Args:
        text: The full text to search in
        citation_text: The citation to find context for
        
    Returns:
        Tuple[Optional[str], str]: (case_name, citation_text)
    """
    case_name = extract_case_name_from_text(text, citation_text)
    return case_name, citation_text


def extract_case_name_from_citation_line(line: str) -> Optional[str]:
    """
    Extract the case name from a line containing a citation, handling leading numbers and
    extracting the last v.-style pattern before the first citation.
    Example:
        '5 Contra John Does 1 v. Seattle Police Dep't, 4 Wn.3d 343, 354, 563 P.3d 1037 (2025)'
        -> 'Contra John Does 1 v. Seattle Police Dep't'
    """
    # Step 1: Find the first citation (e.g., 4 Wn.3d 343)
    citation_match = re.search(r"\d+\s+[A-Za-z\.\'\'\-]+(?:\s+[A-Za-z\.\'\'\-]+)*\s+\d+", line)
    if not citation_match:
        return None

    # Step 2: Get text before the citation
    pre_citation = line[:citation_match.start()]

    # Step 3: Find the last "v."-style case name in pre_citation
    case_name_match = re.findall(r"([A-Z][A-Za-z0-9'\'\.\- ]+\s+v\.\s+[A-Z][A-Za-z0-9'\'\.\- ]+)", pre_citation)
    if not case_name_match:
        return None

    # Step 4: Clean up (remove leading numbers, extra spaces)
    case_name = case_name_match[-1].strip()
    case_name = re.sub(r"^\d+\s+", '', case_name)
    case_name = clean_case_name(case_name)
    return case_name


# Split-based approach: scan for all 'v.' occurrences and extract party names
def extract_case_name_from_context_split(context_before: str, citation_text: str = "") -> str:
    """
    Attempt to extract a probable case name from the text before a citation.
    Looks for patterns like 'Smith v. Jones', 'In re Estate of ...', etc.
    Returns the case name if found, otherwise returns ''.
    
    Args:
        context_before: Text that appears before the citation
        citation_text: The actual citation text (for additional context)
        
    Returns:
        str: The extracted case name or empty string if not found
    """
    if not context_before:
        return ""
    
    # Normalize all whitespace (including newlines, tabs, multiple spaces) to a single space
    context_before = re.sub(r'\s+', ' ', context_before)
    
    # Look for v.-style case name in the last 500 characters before the citation
    context = context_before[-500:]
    
    # Find all v.-style case names in the last 500 characters before the citation
    v_style_pattern = r"([A-Z][A-Za-z'\-\s,\.]+?\s+v\.\s+[A-Z][A-Za-z'\-\s,\.]+?)(?:\s*[,;]|\s*$)"
    matches = list(re.finditer(v_style_pattern, context, re.IGNORECASE | re.DOTALL))
    if matches:
        # Return the last match (closest to the citation)
        case_name = matches[-1].group(1).strip()
        case_name = clean_case_name(case_name)
        if (len(case_name) > 5 and
            ' v. ' in case_name and
            not any(word in case_name.lower() for word in ['exhibit', 'deposition', 'evidence', 'testimony', 'allowing', 'commentary', 'argument', 'federal rules'])):
            return case_name
    
    # Enhanced patterns for case name extraction - more robust to line breaks and whitespace
    patterns = [
        # Improved pattern to handle multi-word party names and trailing commas
        r"([A-Z][A-Za-z'\-\s,\.]+?\s+v\.\s+[A-Z][A-Za-z'\-\s,\.]+?)(?:\s*[,;]|\s*$)",
        r"([A-Z][A-Za-z'\-\s,\.]+?\s+vs\.\s+[A-Z][A-Za-z'\-\s,\.]+?)(?:\s*[,;]|\s*$)",
        r"([A-Z][A-Za-z'\-\s,\.]+?\s+versus\s+[A-Z][A-Za-z'\-\s,\.]+?)(?:\s*[,;]|\s*$)",
        # Original patterns as fallback
        r"([A-Z][^,\n]+?\s+v\.\s+[^,\n]+)",
        r"([A-Z][^,\n]+?\s+vs\.\s+[^,\n]+)",
        r"([A-Z][^,\n]+?\s+versus\s+[^,\n]+)",
        r"(?:^|\s)(In\s+re\s+[A-Z][A-Za-z'\-\s,\.]+(?:\s+[A-Z][A-Za-z'\-\s,\.]+)*)",
        r"(?:^|\s)(Estate\s+of\s+[A-Z][A-Za-z'\-\s,\.]+(?:\s+[A-Z][A-Za-z'\-\s,\.]+)*)",
        r"(?:^|\s)(Matter\s+of\s+[A-Z][A-Za-z'\-\s,\.]+(?:\s+[A-Z][A-Za-z'\-\s,\.]+)*)",
        r"(?:^|\s)(Ex\s+parte\s+[A-Z][A-Za-z'\-\s,\.]+(?:\s+[A-Z][A-Za-z'\-\s,\.]+)*)",
        r"(?:^|\s)([A-Z][A-Za-z'\-\s,\.]+\s+ex\s+rel\.\s+[A-Z][A-Za-z'\-\s,\.]+)",
        r"(?:^|\s)(People\s+v\.\s+[A-Z][A-Za-z'\-\s,\.]+)",
        r"(?:^|\s)(State\s+v\.\s+[A-Z][A-Za-z'\-\s,\.]+)",
        r"(?:^|\s)(United\s+States\s+v\.\s+[A-Z][A-Za-z'\-\s,\.]+)",
        r"(?:^|\s)([A-Z][A-Za-z'\-\s,\.]+\s+et\s+al\.\s+v\.\s+[A-Z][A-Za-z'\-\s,\.]+)",
        r"(?:^|\s)([A-Z][A-Za-z'\-\s,\.]+\s*&\s*[A-Z][A-Za-z'\-\s,\.]+\s+v\.\s+[A-Z][A-Za-z'\-\s,\.]+)",
    ]
    for pattern in patterns:
        matches = list(re.finditer(pattern, context, re.IGNORECASE | re.DOTALL))
        if matches:
            case_name = matches[-1].group(1).strip()
            case_name = clean_case_name(case_name)
            if case_name:
                # Additional validation: make sure it looks like a case name
                if ' v. ' in case_name and not any(word in case_name.lower() for word in ['exhibit', 'deposition', 'evidence', 'testimony', 'allowing', 'commentary', 'argument']):
                    return case_name
    in_re_case_name = extract_in_re_case_name_from_context(context_before, citation_text)
    if in_re_case_name:
        return in_re_case_name
    if citation_text:
        log_debug(f"Trying fallback extraction for citation: {citation_text}")
        citation_index = context_before.find(citation_text)
        if citation_index != -1:
            line_start = context_before.rfind('\n', 0, citation_index)
            line_end = context_before.find('\n', citation_index)
            if line_start == -1:
                line_start = 0
            else:
                line_start += 1
            if line_end == -1:
                line_end = len(context_before)
            line = context_before[line_start:line_end]
            log_debug(f"Extracted line: {repr(line)}")
            for pattern in patterns:
                matches = list(re.finditer(pattern, line, re.IGNORECASE | re.DOTALL))
                if matches:
                    case_name = matches[-1].group(1).strip()
                    case_name = clean_case_name(case_name)
                    if case_name:
                        log_debug(f"Found case name with pattern: {case_name}")
                        return case_name
            before_citation = line.split(citation_text)[0].strip()
            log_debug(f"Before citation: {repr(before_citation)}")
            fallback_pattern = r"([A-Z][A-Za-z0-9'\-\s,\.]+\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9'\-\s,\.]+)"
            log_debug(f"Using fallback pattern: {fallback_pattern}")
            matches = list(re.finditer(fallback_pattern, before_citation, re.IGNORECASE | re.DOTALL))
            log_debug(f"Found {len(matches)} matches with fallback pattern")
            if matches:
                case_name = matches[-1].group(1).strip()
                case_name = clean_case_name(case_name)
                if case_name:
                    log_debug(f"Matched case name: {repr(case_name)}")
                    return case_name
            else:
                log_debug("No matches found with fallback pattern")
            in_re_pattern = r"(In\s+re[\w\s,\.''\-]*)"
            log_debug(f"Using In re fallback pattern: {in_re_pattern}")
            in_re_matches = list(re.finditer(in_re_pattern, before_citation, re.IGNORECASE | re.DOTALL))
            log_debug(f"Found {len(in_re_matches)} In re matches with fallback pattern")
            if in_re_matches:
                in_re_case_name = in_re_matches[-1].group(1).strip()
                in_re_case_name = clean_case_name(in_re_case_name)
                if in_re_case_name:
                    log_debug(f"Matched In re case name: {repr(in_re_case_name)}")
                    return in_re_case_name
            else:
                log_debug("No In re matches found with fallback pattern")
        else:
            log_debug(f"Citation '{citation_text}' not found in context")
            # Try to find any case name in the broader context
            broader_context = context_before[-1000:]  # Look at last 1000 characters
            log_debug(f"Searching broader context for case names")
            
            # Try v.-style patterns in broader context
            v_patterns = [
                r"([A-Z][A-Za-z0-9'\-\s,\.]+\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9'\-\s,\.]+)",
                r"([A-Z][A-Za-z0-9'\-\s,\.]+\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9'\-\s,\.]+[A-Za-z0-9'\-\s,\.]*)",
            ]
            for pattern in v_patterns:
                matches = list(re.finditer(pattern, broader_context, re.IGNORECASE | re.DOTALL))
                if matches:
                    case_name = matches[-1].group(1).strip()
                    case_name = clean_case_name(case_name)
                    if case_name and len(case_name) > 5:
                        log_debug(f"Found case name in broader context: {case_name}")
                        # Add to recent case names cache
                        _recent_case_names.append(case_name)
                        # Keep only the last 10 case names
                        if len(_recent_case_names) > 10:
                            _recent_case_names = _recent_case_names[-10:]
                        return case_name
            
            # Try In re patterns in broader context
            in_re_patterns = [
                r"(In\s+re\s+[A-Z][A-Za-z'\-\s,\.]+)",
                r"(In\s+re\s+[A-Z][A-Za-z'\-\s,\.]+[A-Za-z'\-\s,\.]*)",
            ]
            for pattern in in_re_patterns:
                matches = list(re.finditer(pattern, broader_context, re.IGNORECASE | re.DOTALL))
                if matches:
                    case_name = matches[-1].group(1).strip()
                    case_name = clean_case_name(case_name)
                    if case_name and len(case_name) > 5:
                        log_debug(f"Found In re case name in broader context: {case_name}")
                        # Add to recent case names cache
                        _recent_case_names.append(case_name)
                        # Keep only the last 10 case names
                        if len(_recent_case_names) > 10:
                            _recent_case_names = _recent_case_names[-10:]
                        return case_name
    return ""


# Add this mapping for common legal abbreviations
ABBREVIATION_MAP = {
    'Dep': 'Department',
    'Emp': 'Employment',
    'Cent.': 'Central',
    'Reg': 'Regional',
    'Indus.': 'Industries',
    'Sec.': 'Security',
    'Ret.': 'Retirement',
    'Sys.': 'Systems',
    'Ass\'n': 'Association',
    'Inc.': 'Inc.',
    'Co.': 'Co.',
    'LLC': 'LLC',
    'Corp.': 'Corp.',
    'Ltd.': 'Ltd.',
    'L.L.C.': 'L.L.C.',
    'L.P.': 'L.P.',
    'P.S.': 'P.S.',
    'P.C.': 'P.C.',
    'P.A.': 'P.A.',
    'P.L.L.C.': 'P.L.L.C.',
    'L.L.P.': 'L.L.P.',
    'N.A.': 'N.A.',
    'N.V.': 'N.V.',
    'S.A.': 'S.A.',
    'S.p.A.': 'S.p.A.',
    'A.G.': 'A.G.',
    'B.V.': 'B.V.',
    'S.à r.l.': 'S.à r.l.',
    'PLC': 'PLC',
    'GmbH': 'GmbH',
    'SNC': 'SNC',
    'SCS': 'SCS',
    'SCA': 'SCA',
    'SAS': 'SAS',
    'S.A.S.': 'S.A.S.',
    'S.A.R.L.': 'S.A.R.L.',
    'S.A. de C.V.': 'S.A. de C.V.',
    'S.A.B. de C.V.': 'S.A.B. de C.V.'
}

def expand_abbreviations(case_name: str) -> str:
    """Expand common legal abbreviations at the end of party names."""
    tokens = case_name.split()
    # Only expand the last token if it's in the map
    if tokens and tokens[-1] in ABBREVIATION_MAP:
        tokens[-1] = ABBREVIATION_MAP[tokens[-1]]
    # Also expand the last token before a comma (e.g., 'Co.,')
    if len(tokens) > 1 and tokens[-2] in ABBREVIATION_MAP and tokens[-1].startswith(','):
        tokens[-2] = ABBREVIATION_MAP[tokens[-2]]
    return ' '.join(tokens)

def normalize_citation_format(citation_text: str) -> str:
    """Normalize citation format to handle Bluebook variations."""
    # Remove extra spaces in common citation formats
    normalized = citation_text
    
    # Handle L.Ed. variations
    normalized = re.sub(r'L\.\s*Ed\.\s*(\d+)\s*(\w+)', r'L.Ed.\1\2', normalized)
    normalized = re.sub(r'L\.\s*Ed\.\s*(\d+)', r'L.Ed.\1', normalized)
    
    # Handle S.Ct. variations
    normalized = re.sub(r'S\.\s*Ct\.\s*(\d+)', r'S.Ct.\1', normalized)
    
    # Handle U.S. variations
    normalized = re.sub(r'U\.\s*S\.\s*(\d+)', r'U.S.\1', normalized)
    
    return normalized

def extract_case_name_hinted(text, citation, canonical_name, window=300):
    """
    Extract the best-matching case name block from the text immediately before the citation,
    using the canonical name as a hint. Returns the best candidate and its similarity score.
    """
    # Find the citation in the text
    idx = text.find(citation)
    if idx == -1:
        return '', 0
    # Get a window of text before the citation
    start = max(0, idx - window)
    context = text[start:idx]
    # Find all candidate case names in the context (e.g., 'X v. Y' patterns)
    candidate_pattern = re.compile(r'([A-Z][A-Za-z0-9\'\-\. ]+ v\. [A-Z][A-Za-z0-9\'\-\. ]+)', re.MULTILINE)
    candidates = candidate_pattern.findall(context)
    # If no candidates, return empty
    if not candidates:
        return '', 0
    # Compare each candidate to the canonical name
    best_score = -1
    best_candidate = ''
    for candidate in candidates:
        score = fuzz.ratio(candidate.strip(), canonical_name.strip())
        if score > best_score:
            best_score = score
            best_candidate = candidate.strip()
    return best_candidate, best_score
