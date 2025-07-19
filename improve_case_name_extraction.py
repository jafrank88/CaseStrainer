#!/usr/bin/env python3
"""
Improved case name extraction that addresses the issues found in analysis.
"""

import re
from typing import Optional, Tuple

def extract_case_name_improved_v2(text: str, citation: str) -> str:
    """
    Improved case name extraction that addresses greedy matching and other issues.
    
    Args:
        text: The full text content
        citation: The citation to search for
        
    Returns:
        Extracted case name or empty string
    """
    if not text or not citation:
        return ""
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Find citation in text
    citation_index = text.find(citation)
    if citation_index == -1:
        return ""
    
    # Get context that INCLUDES the citation (200 chars before + citation + 50 chars after)
    context_start = max(0, citation_index - 200)
    context_end = min(len(text), citation_index + len(citation) + 50)
    context = text[context_start:context_end]
    
    print(f"DEBUG: Looking for citation '{citation}' in context: '{context}'")
    
    # IMPROVED PATTERNS - More precise to avoid greedy matching
    
    # Pattern 1: Standard case names with flexible spacing and business entities
    # FIXED: Use word boundaries to avoid capturing leading text
    pattern1 = (
        r'\b([A-Z][A-Za-z\s,\.&\'-]+?'  # First part of case name (non-greedy) with word boundary
        r'\s+(?:v\.|vs\.|v\s)'        # Flexible "v." matching
        r'\s+[A-Z][A-Za-z\s,\.&\'-]+?'  # Second part of case name (non-greedy)
        r'(?:\s+(?:LLC|Inc\.?|Corp\.?|L\.P\.|L\.L\.C\.))?'  # Optional business suffixes
        r')\s*[,;]?\s*(?:\d+\s*,\s*)?' + re.escape(citation)  # Allow comma/semicolon and optional page numbers
    )
    
    # Pattern 2: Department cases with word boundary
    pattern2 = (
        r'\b(Dep\'t\s+of\s+[A-Za-z\s,\.&\'-]+?'  # Department cases with word boundary
        r'\s+(?:v\.|vs\.|v\s)'
        r'\s+[A-Za-z\s,\.&\'-]+?'
        r'(?:\s+(?:LLC|Inc\.?|Corp\.?|L\.P\.|L\.L\.C\.))?'
        r')\s*[,;]?\s*(?:\d+\s*,\s*)?' + re.escape(citation)
    )
    
    # Pattern 3: In re cases with word boundary
    pattern3 = (
        r'\b(In\s+re\s+[A-Za-z\s,\.&\'-]+?'  # In re cases with word boundary
        r'(?:\s+(?:LLC|Inc\.?|Corp\.?|L\.P\.|L\.L\.C\.))?'
        r')\s*[,;]?\s*(?:\d+\s*,\s*)?' + re.escape(citation)
    )
    
    # Pattern 4: Estate cases with word boundary
    pattern4 = (
        r'\b(Estate\s+of\s+[A-Za-z\s,\.&\'-]+?'  # Estate cases with word boundary
        r'(?:\s+(?:LLC|Inc\.?|Corp\.?|L\.P\.|L\.L\.C\.))?'
        r')\s*[,;]?\s*(?:\d+\s*,\s*)?' + re.escape(citation)
    )
    
    # Pattern 5: State/People cases with word boundary
    pattern5 = (
        r'\b(State\s+(?:v\.|vs\.|v\s)\s+[A-Za-z\s,\.&\'-]+?'  # State v. cases with word boundary
        r'(?:\s+(?:LLC|Inc\.?|Corp\.?|L\.P\.|L\.L\.C\.))?'
        r')\s*[,;]?\s*(?:\d+\s*,\s*)?' + re.escape(citation)
    )
    
    # Pattern 6: United States cases with word boundary
    pattern6 = (
        r'\b(United\s+States\s+(?:v\.|vs\.|v\s)\s+[A-Za-z\s,\.&\'-]+?'  # U.S. v. cases with word boundary
        r'(?:\s+(?:LLC|Inc\.?|Corp\.?|L\.P\.|L\.L\.C\.))?'
        r')\s*[,;]?\s*(?:\d+\s*,\s*)?' + re.escape(citation)
    )
    
    # Pattern 7: More flexible pattern for cases with year in parentheses
    pattern7 = (
        r'\b([A-Z][A-Za-z\s,\.&\'-]+?'  # First part with word boundary
        r'\s+(?:v\.|vs\.|v\s)'
        r'\s+[A-Z][A-Za-z\s,\.&\'-]+?'  # Second part
        r'(?:\s+(?:LLC|Inc\.?|Corp\.?|L\.P\.|L\.L\.C\.))?'
        r')\s*\(\d{4}\)'  # Year in parentheses
    )
    
    patterns = [pattern1, pattern2, pattern3, pattern4, pattern5, pattern6, pattern7]
    
    for i, pattern in enumerate(patterns):
        print(f"DEBUG: Trying pattern {i+1}: {pattern}")
        matches = list(re.finditer(pattern, context, re.IGNORECASE))
        if matches:
            # Take the last (closest to citation) match
            match = matches[-1]
            case_name = clean_case_name_improved(match.group(1))
            print(f"DEBUG: Pattern {i+1} matched: '{match.group(1)}' -> cleaned: '{case_name}'")
            if is_valid_case_name_improved(case_name):
                print(f"DEBUG: Valid case name found: '{case_name}'")
                return case_name
            else:
                print(f"DEBUG: Invalid case name: '{case_name}'")
        else:
            print(f"DEBUG: Pattern {i+1} no matches")
    
    # If no exact citation match, try broader patterns
    print("DEBUG: Trying broader patterns...")
    return extract_case_name_broader(context, citation)

def clean_case_name_improved(case_name: str) -> str:
    """Clean and validate case name with improved rules."""
    if not case_name:
        return ""
    
    # FIXED: Remove common leading phrases that shouldn't be part of case names
    # But be careful not to remove "In" when it's part of "In re"
    leading_phrases_to_remove = [
        r'^The court held in\s+',
        r'^As established in\s+',
        r'^As held in\s+',
        r'^According to\s+',
        # Don't remove "In" if it's followed by "re" (In re cases)
        r'^The\s+(?!re\b)',
        r'^A\s+(?!re\b)',
        r'^An\s+(?!re\b)',
    ]
    
    for phrase in leading_phrases_to_remove:
        case_name = re.sub(phrase, '', case_name, flags=re.IGNORECASE)
    
    # Remove citation text that might have been included
    citation_patterns = [
        r',\s*\d+\s+[A-Za-z.]+(?:\s+\d+)*.*$',  # Remove ", 200 Wn.2d 72, 73, 514 P.3d 643 (2022)"
        r',\s*\d+\s+[A-Za-z.]+.*$',  # Remove ", 200 Wn.2d 72"
        r',\s*\d+.*$',  # Remove ", 200"
        r'\(\d{4}\).*$',  # Remove "(2022)" and everything after
    ]
    
    for pattern in citation_patterns:
        case_name = re.sub(pattern, '', case_name, flags=re.IGNORECASE)
    
    # Clean up whitespace and punctuation
    case_name = re.sub(r'\s+', ' ', case_name.strip())
    case_name = case_name.strip(' ,;')
    
    # Normalize "v." spacing
    case_name = re.sub(r'\s+v\.\s+', ' v. ', case_name)
    case_name = re.sub(r'\s+vs\.\s+', ' v. ', case_name)
    case_name = re.sub(r'\s+v\s+', ' v. ', case_name)
    
    return case_name

def is_valid_case_name_improved(case_name: str) -> bool:
    """Improved validation for case names."""
    print(f"DEBUG VALIDATION: Checking '{case_name}'")
    
    if not case_name or len(case_name) < 3:
        print(f"DEBUG VALIDATION: Failed - too short or empty")
        return False
    
    # Must contain "v." or be an "In re" or "Estate of" case
    # FIXED: Use a more flexible regex that handles "v." with various spacing
    has_v = re.search(r'\bv\.?\b', case_name, re.IGNORECASE) or ' v. ' in case_name
    has_in_re = case_name.lower().startswith('in re')
    has_estate = case_name.lower().startswith('estate of')
    
    if not (has_v or has_in_re or has_estate):
        print(f"DEBUG VALIDATION: Failed - no 'v.' or 'in re' or 'estate of'")
        print(f"DEBUG VALIDATION: has_v={has_v}, has_in_re={has_in_re}, has_estate={has_estate}")
        return False
    
    # Check that the first word starts with a capital letter
    words = case_name.split()
    if not words or not words[0] or not words[0][0].isupper():
        print(f"DEBUG VALIDATION: Failed - first word doesn't start with capital")
        return False
    
    # Must contain at least one letter
    if not re.search(r'[a-zA-Z]', case_name):
        print(f"DEBUG VALIDATION: Failed - no letters")
        return False
    
    # Avoid all-caps text (likely headers)
    if re.match(r'^[A-Z\s]+$', case_name):
        print(f"DEBUG VALIDATION: Failed - all caps")
        return False
    
    # FIXED: Don't reject case names that start with common legal phrases
    # These are valid case name patterns:
    valid_prefixes = [
        'state v.', 'united states v.', 'people v.', 'in re', 'estate of',
        'department of', 'dep\'t of', 'county of', 'city of'
    ]
    
    case_name_lower = case_name.lower()
    for prefix in valid_prefixes:
        if case_name_lower.startswith(prefix):
            print(f"DEBUG VALIDATION: Passed - valid prefix '{prefix}'")
            return True
    
    # For other cases, check that they contain "v." and have reasonable structure
    if ' v. ' in case_name:
        # Split by "v." and check both parts
        parts = case_name.split(' v. ')
        if len(parts) == 2:
            plaintiff = parts[0].strip()
            defendant = parts[1].strip()
            
            # Both parts should have at least one word starting with capital letter
            if (plaintiff and defendant and 
                plaintiff[0].isupper() and defendant[0].isupper()):
                print(f"DEBUG VALIDATION: Passed - valid v. structure")
                return True
            else:
                print(f"DEBUG VALIDATION: Failed - invalid v. structure: plaintiff='{plaintiff}', defendant='{defendant}'")
    
    print(f"DEBUG VALIDATION: Failed - no valid pattern matched")
    return False

def extract_case_name_broader(context: str, citation: str) -> str:
    """Broader extraction when exact citation matching fails."""
    
    # Look for case names in the last 150 characters
    recent_context = context[-150:] if len(context) > 150 else context
    
    print(f"DEBUG: Broader context: '{recent_context}'")
    
    # Broader patterns that don't require exact citation matching
    broader_patterns = [
        # Standard cases with flexible ending
        r'([A-Z][A-Za-z\s,\.&\'-]+?\s+(?:v\.|vs\.|v\s)\s+[A-Z][A-Za-z\s,\.&\'-]+?)(?=\s*,|\s*$|\s*\d)',
        # Department cases
        r'(Dep\'t\s+of\s+[A-Za-z\s,\.&\'-]+?\s+(?:v\.|vs\.|v\s)\s+[A-Za-z\s,\.&\'-]+?)(?=\s*,|\s*$|\s*\d)',
        # In re cases
        r'(In\s+re\s+[A-Za-z\s,\.&\'-]+?)(?=\s*,|\s*$|\s*\d)',
        # State cases
        r'(State\s+(?:v\.|vs\.|v\s)\s+[A-Za-z\s,\.&\'-]+?)(?=\s*,|\s*$|\s*\d)',
        # United States cases
        r'(United\s+States\s+(?:v\.|vs\.|v\s)\s+[A-Za-z\s,\.&\'-]+?)(?=\s*,|\s*$|\s*\d)',
    ]
    
    for i, pattern in enumerate(broader_patterns):
        print(f"DEBUG: Broader pattern {i+1}: {pattern}")
        matches = list(re.finditer(pattern, recent_context, re.IGNORECASE))
        if matches:
            match = matches[-1]  # Take the last (closest) match
            case_name = clean_case_name_improved(match.group(1))
            print(f"DEBUG: Broader pattern {i+1} matched: '{match.group(1)}' -> cleaned: '{case_name}'")
            if is_valid_case_name_improved(case_name):
                print(f"DEBUG: Valid case name found in broader search: '{case_name}'")
                return case_name
            else:
                print(f"DEBUG: Invalid case name in broader search: '{case_name}'")
        else:
            print(f"DEBUG: Broader pattern {i+1} no matches")
    
    return ""

def test_improved_extraction():
    """Test the improved extraction on the examples from analysis."""
    
    test_cases = [
        {
            'context': "The court held in Smith v. Jones, 200 Wn.2d 72, 73, 514 P.3d 643 (2022) that...",
            'citation': "200 Wn.2d 72",
            'expected': "Smith v. Jones"
        },
        {
            'context': "As established in Department of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)...",
            'citation': "146 Wn.2d 1",
            'expected': "Department of Ecology v. Campbell & Gwinn, LLC"
        },
        {
            'context': "In re Estate of Smith, 170 Wn.2d 614, 316 P.3d 1020 (2010)...",
            'citation': "170 Wn.2d 614",
            'expected': "In re Estate of Smith"
        },
        {
            'context': "State v. Johnson, 93 Wn.2d 31, 604 P.2d 1293 (2002)...",
            'citation': "93 Wn.2d 31",
            'expected': "State v. Johnson"
        },
        {
            'context': "United States v. Smith, 446 U.S. 544 (1980)...",
            'citation': "446 U.S. 544",
            'expected': "United States v. Smith"
        }
    ]
    
    print("Testing Improved Case Name Extraction:")
    print("=" * 60)
    
    success_count = 0
    for i, test_case in enumerate(test_cases):
        result = extract_case_name_improved_v2(test_case['context'], test_case['citation'])
        success = result == test_case['expected']
        if success:
            success_count += 1
        
        print(f"Test {i+1}:")
        print(f"  Context: '{test_case['context']}'")
        print(f"  Citation: '{test_case['citation']}'")
        print(f"  Expected: '{test_case['expected']}'")
        print(f"  Result:   '{result}'")
        print(f"  Status:   {'✓ PASS' if success else '✗ FAIL'}")
        print()
    
    print(f"Overall Success Rate: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.1f}%)")

if __name__ == "__main__":
    test_improved_extraction() 