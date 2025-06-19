import re
from typing import Optional, Tuple


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
    if not context_before:
        return ""
    
    # Normalize all whitespace (including newlines, tabs, multiple spaces) to a single space
    context_before = re.sub(r'\s+', ' ', context_before)
    
    # Look for common case name patterns in the last 500 chars (increased from 100)
    context = context_before[-500:]
    
    # Enhanced patterns for case name extraction - more robust to line breaks and whitespace
    patterns = [
        # Standard case names with "v." or "vs." - allow for whitespace, commas, or line breaks after the name
        r"(?:^|\s)([A-Z][A-Za-z'\-\s]+\s+v\.\s+[A-Z][A-Za-z'\-\s]+)\s*[\,\s\n\r]*$",
        r"(?:^|\s)([A-Z][A-Za-z'\-\s]+\s+vs\.\s+[A-Z][A-Za-z'\-\s]+)\s*[\,\s\n\r]*$",
        r"(?:^|\s)([A-Z][A-Za-z'\-\s]+\s+versus\s+[A-Z][A-Za-z'\-\s]+)\s*[\,\s\n\r]*$",
        # In re cases
        r"(?:^|\s)(In\s+re\s+[A-Z][A-Za-z'\-\s]+(?:\s+[A-Z][A-Za-z'\-\s]+)*)\s*[\,\s\n\r]*$",
        # Estate cases
        r"(?:^|\s)(Estate\s+of\s+[A-Z][A-Za-z'\-\s]+(?:\s+[A-Z][A-Za-z'\-\s]+)*)\s*[\,\s\n\r]*$",
        # Matter of cases
        r"(?:^|\s)(Matter\s+of\s+[A-Z][A-Za-z'\-\s]+(?:\s+[A-Z][A-Za-z'\-\s]+)*)\s*[\,\s\n\r]*$",
        # Ex parte cases
        r"(?:^|\s)(Ex\s+parte\s+[A-Z][A-Za-z'\-\s]+(?:\s+[A-Z][A-Za-z'\-\s]+)*)\s*[\,\s\n\r]*$",
        # Ex rel cases
        r"(?:^|\s)([A-Z][A-Za-z'\-\s]+\s+ex\s+rel\.\s+[A-Z][A-Za-z'\-\s]+)\s*[\,\s\n\r]*$",
        # People v. cases
        r"(?:^|\s)(People\s+v\.\s+[A-Z][A-Za-z'\-\s]+)\s*[\,\s\n\r]*$",
        r"(?:^|\s)(State\s+v\.\s+[A-Z][A-Za-z'\-\s]+)\s*[\,\s\n\r]*$",
        r"(?:^|\s)(United\s+States\s+v\.\s+[A-Z][A-Za-z'\-\s]+)\s*[\,\s\n\r]*$",
        # Cases with "et al." - more precise
        r"(?:^|\s)([A-Z][A-Za-z'\-\s]+\s+et\s+al\.\s+v\.\s+[A-Z][A-Za-z'\-\s]+)\s*[\,\s\n\r]*$",
        # Cases with "&" (partnerships, companies) - more precise
        r"(?:^|\s)([A-Z][A-Za-z'\-\s]+\s*&\s*[A-Z][A-Za-z'\-\s]+\s+v\.\s+[A-Z][A-Za-z'\-\s]+)\s*[\,\s\n\r]*$",
    ]
    
    for pattern in patterns:
        matches = list(re.finditer(pattern, context, re.IGNORECASE | re.DOTALL))
        if matches:
            # Return the last match (closest to citation)
            case_name = matches[-1].group(1).strip()
            # Clean up the case name
            case_name = clean_case_name(case_name)
            if case_name:
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


def extract_case_name_from_text(text: str, citation_text: str, all_citations: list = None) -> Optional[str]:
    """
    Extract potential case name from text surrounding a citation.
    Uses multiple patterns and heuristics to find the most likely case name.
    
    Args:
        text: The full text containing the citation
        citation_text: The specific citation to find context for
        all_citations: Optional list of all citations found in the text (for shared case name detection)
        
    Returns:
        str: The extracted case name or None if not found
    """
    if not text or not citation_text:
        return None
    
    # Find the citation in the text
    citation_index = text.find(citation_text)
    if citation_index <= 0:
        return None
    
    # If we have all citations, try to find a shared case name first
    if all_citations and len(all_citations) > 1:
        shared_case_names = find_shared_case_name_for_citations(text, all_citations)
        if citation_text in shared_case_names:
            return shared_case_names[citation_text]
    
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
    
    # If there are multiple citations nearby, use a smaller context window
    if citation_count > 2:
        context_window = 100  # Smaller window for lists
    else:
        context_window = 300  # Larger window for individual citations
    
    # Look for potential case name in the text before the citation
    pre_text = text[max(0, citation_index - context_window):citation_index]
    
    # Try the enhanced context extraction first
    case_name = extract_case_name_from_context(pre_text, citation_text)
    if case_name and not is_citation_like(case_name):
        return case_name
    
    # Fallback patterns for more complex cases
    fallback_patterns = [
        # Pattern 1: Case name with "v." or "vs." (most common format)
        r'([A-Z][\w\s\.,&\-]+\sv\.\s[\w\s\.,&\-]+)',
        
        # Pattern 2: Case name with "versus"
        r'([A-Z][\w\s\.,&\-]+\sversus\s[\w\s\.,&\-]+)',
        
        # Pattern 3: Case name with "v" (abbreviated format)
        r'([A-Z][\w\s\.,&\-]+\sv\s[\w\s\.,&\-]+)',
        
        # Pattern 4: Case name with "ex rel." format
        r'([A-Z][\w\s\.,&\-]+\sex rel\.\s[\w\s\.,&\-]+)',
        
        # Pattern 5: Case name with "In re" format
        r'(In re\s[\w\s\.,&\-]+)',
        
        # Pattern 6: Case name with "Matter of" format
        r'(Matter of\s[\w\s\.,&\-]+)',
        
        # Pattern 7: Case name with "Estate of" format
        r'(Estate of\s[\w\s\.,&\-]+)',
        
        # Pattern 8: Last resort - look for capitalized phrases that might be case names
        r'([A-Z][\w\s\.,&\-]+(?:,|\.|;)\s+\d)'
    ]
    
    # Try each pattern in order
    for pattern in fallback_patterns:
        matches = re.findall(pattern, pre_text)
        if matches:
            # Get the last match (closest to the citation)
            case_name = matches[-1].strip()
            # Clean up the case name (remove trailing punctuation)
            case_name = clean_case_name(case_name)
            if case_name and not is_citation_like(case_name):
                return case_name
    
    # --- NEW: Try robust line-based extraction as a final fallback ---
    # Get the full line containing the citation
    line_start = text.rfind('\n', 0, citation_index)
    line_end = text.find('\n', citation_index)
    if line_start == -1:
        line_start = 0
    else:
        line_start += 1  # move past the newline
    if line_end == -1:
        line_end = len(text)
    line = text[line_start:line_end]
    case_name = extract_case_name_from_citation_line(line)
    if case_name and not is_citation_like(case_name):
        return case_name

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
    
    return False


def clean_case_name(case_name: str) -> str:
    """
    Clean and normalize a case name by removing extra whitespace,
    punctuation, and other artifacts. Truncate to likely case name only.
    """
    if not case_name:
        return ""

    # Remove trailing punctuation
    case_name = re.sub(r'[\.,;]\s*$', '', case_name)

    # Normalize whitespace
    case_name = re.sub(r'\s+', ' ', case_name).strip()

    # Remove common introductory phrases (more comprehensive)
    intro_patterns = [
        r'^(?:the\s+)?(?:case\s+of\s+|supreme\s+court\s+in\s+|court\s+of\s+appeals\s+in\s+)',
        r'^(?:the\s+)?(?:washington\s+supreme\s+court\s+in\s+|washington\s+court\s+of\s+appeals\s+in\s+)',
        r'^(?:in\s+the\s+case\s+of\s+|in\s+the\s+matter\s+of\s+)',
        r'^(?:the\s+)?(?:matter\s+of\s+|proceeding\s+of\s+)',
        r'^(?:in\s+|the\s+case\s+)',
        r'^(?:and\s+the\s+court\s+of\s+appeals\s+in\s+)',
    ]
    for pattern in intro_patterns:
        case_name = re.sub(pattern, '', case_name, flags=re.IGNORECASE)

    # Remove common artifacts that might appear at the end
    case_name = re.sub(r'\s+(?:case|matter|proceeding|action|petition)\s*$', '', case_name, flags=re.IGNORECASE)

    # Remove trailing descriptive text
    case_name = re.sub(r'\s+(?:was\s+decided|established|addressed|dealt\s+with).*$', '', case_name, flags=re.IGNORECASE)

    # Truncate after the first likely case name pattern (v. or vs. or similar)
    # e.g., "In Woods v. BNSF Railway Co, UL 2272, ..." -> "Woods v. BNSF Railway Co"
    match = re.search(r'([A-Z][A-Za-z\'\-\s]+\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z\'\-\s]+)', case_name)
    if match:
        case_name = match.group(1).strip()

    # If the result is still too long, truncate to first 8 words
    words = case_name.split()
    if len(words) > 8:
        case_name = ' '.join(words[:8])

    # Ensure proper capitalization for common legal terms
    case_name = re.sub(r'\b(In re|Ex parte|Ex rel|Matter of|Estate of)\b', lambda m: m.group(1).title(), case_name, flags=re.IGNORECASE)

    # Final cleanup - remove any remaining trailing punctuation and whitespace
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
