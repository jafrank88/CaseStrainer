#!/usr/bin/env python3
"""
Test script to demonstrate and fix the case name extraction issue.
The problem is that all citations are getting the same extracted case name.
"""

import re

def extract_case_name_for_citation(text: str, citation: str) -> str:
    """
    Extract case name for a specific citation with proper context isolation.
    This fixes the issue where all citations were getting the same case name.
    """
    if not citation:
        return "N/A"
    
    # Find the citation in the text
    citation_pos = text.find(citation)
    if citation_pos == -1:
        return "N/A"
    
    print(f"  DEBUG: Found citation '{citation}' at position {citation_pos}")
    
    # SIMPLE APPROACH: Look for case names in a large context window
    # Look back up to 800 characters for the case name
    start = max(0, citation_pos - 800)
    
    # Extract the context before the citation
    context_before = text[start:citation_pos].strip()
    print(f"  DEBUG: Context before citation: '{context_before}'")
    
    # Look for specific case name patterns in the context
    case_patterns = [
        # Party v. Party cases (most common)
        r'([A-Z][a-zA-Z0-9\s&\'\.-]+\s+v\.\s+[A-Z][a-zA-Z0-9\s&\'\.-]+)',
        # In re cases
        r'(In\s+re\s+[^,;\n]+)',
        # State v. cases
        r'(State\s+v\.\s+[A-Z][a-zA-Z\s&\'\.-]+)',
        # Department cases
        r'(Dep\'t\s+of\s+[^,;\n]+)',
    ]
    
    for pattern in case_patterns:
        matches = re.findall(pattern, context_before, re.IGNORECASE)
        if matches:
            # Return the last (most recent) match
            case_name = matches[-1].strip()
            # Clean up the case name
            case_name = re.sub(r'[,\s]+$', '', case_name)
            if len(case_name) > 5:  # Basic validation
                print(f"  DEBUG: Found case name with pattern {pattern}: '{case_name}'")
                return case_name
    
    # If no pattern match, try to find the case name by looking for the comma before the citation
    # This handles the pattern "Case Name, citation"
    for i in range(citation_pos - 1, max(0, citation_pos - 600), -1):
        if text[i] == ',':
            # Found a comma, extract text before it
            case_name = text[max(0, i-600):i].strip()
            
            # Look for the last sequence of capitalized words that looks like a case name
            words = case_name.split()
            if words:
                # Find the last sequence of capitalized words
                case_words = []
                for word in reversed(words):
                    if word and word[0].isupper() and len(word) > 2:
                        case_words.insert(0, word)
                    elif case_words and word.lower() in ['v', 'vs', 'versus']:
                        # Include connecting words like "v", "vs", "versus"
                        case_words.insert(0, word)
                    elif case_words and word.lower() in ['llc', 'inc', 'corp', 'co', 'company']:
                        # Include business suffixes
                        case_words.insert(0, word)
                    elif case_words:  # Stop if we hit a non-capitalized word after finding some
                        break
                
                if case_words:
                    case_name = ' '.join(case_words)
                    # Clean up the case name
                    case_name = re.sub(r'[,\s]+$', '', case_name)
                    print(f"  DEBUG: Found case name with comma method: '{case_name}'")
                    return case_name
            break
    
    print(f"  DEBUG: No case name found")
    return "N/A"

def test_case_extraction():
    """Test the case name extraction with the problematic text."""
    
    # Your test text
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)."""
    
    # The citations from your test
    citations = [
        "200 Wn.2d 72",
        "171 Wn.2d 486", 
        "146 Wn.2d 1"
    ]
    
    print("=== Testing Case Name Extraction Fix ===")
    print(f"Test text: {test_text[:100]}...")
    print()
    
    for citation in citations:
        print(f"Citation: {citation}")
        case_name = extract_case_name_for_citation(test_text, citation)
        print(f"  Final result: {case_name}")
        print()

if __name__ == "__main__":
    test_case_extraction()
