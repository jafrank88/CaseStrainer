#!/usr/bin/env python3
"""
Test case name extraction on the actual problematic text.
"""

import re

STOP_WORDS = set([
    'of', 'the', 'in', 'and', 'for', 'on', 'at', 'by', 'to', 'from', 'with', 'without', 'under', 'over', 'above', 'below', 'before', 'after', 'during', 'while', 'when', 'where', 'why', 'how', 'what', 'which', 'who', 'whose', 'whom', 'a', 'an', 'as', 'but', 'or', 'nor', 'so', 'yet', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'that', 'this', 'these', 'those', 'it', 'its', 'their', 'his', 'her', 'our', 'your', 'my', 'me', 'you', 'he', 'she', 'they', 'them', 'we', 'us', 'do', 'does', 'did', 'has', 'have', 'had', 'can', 'could', 'will', 'would', 'shall', 'should', 'may', 'might', 'must', 'not', 'if', 'because', 'than', 'then', 'once', 'about', 'into', 'through', 'over', 'after', 'again', 'further', 'off', 'out', 'up', 'down', 'more', 'most', 'some', 'such', 'no', 'nor', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'just', 'don', 'now'
])

V_PATTERNS = [
    # More inclusive pattern that captures full party names with punctuation
    r'([A-Z][A-Za-z0-9\'\-\s&,\.]*(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9\'\-\s&,\.]+)',
    # Fallback pattern
    r'([A-Z][A-Za-z0-9\'\-]*(?:\s+[A-Za-z0-9\'\-]+)*\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9\'\-]*(?:\s+[A-Za-z0-9\'\-]+)*)',
]

def extract_case_name(text):
    # Clean up the text first
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    
    print(f"DEBUG: Cleaned text: '{text}'")
    
    # Find all v.-style matches
    for pattern in V_PATTERNS:
        matches = list(re.finditer(pattern, text))
        print(f"DEBUG: Found {len(matches)} matches with pattern")
        
        for match in matches:
            match_text = match.group(1)
            print(f"DEBUG: Match: '{match_text}'")
            
            # Clean up the match
            match_text = re.sub(r'\s+', ' ', match_text).strip()
            
            # Split into words and find the v. position
            words = match_text.split()
            v_index = None
            for i, w in enumerate(words):
                if w.lower() in {'v.', 'vs.', 'versus'}:
                    v_index = i
                    break
            
            if v_index is None:
                continue
            
            print(f"DEBUG: Words: {words}")
            print(f"DEBUG: V index: {v_index}")
            
            # For the start, look for the first capitalized word that's not a stop word
            # or a sequence starting with a capitalized word
            start = 0
            for i in range(v_index):
                word = words[i]
                if word.istitle() and word.lower() not in STOP_WORDS:
                    start = i
                    break
                elif i > 0 and words[i-1].istitle() and word.lower() in STOP_WORDS:
                    # This is part of a multi-word name like "Dep't of Ecology"
                    start = i-1
                    break
            
            # For the end, find the last capitalized word or stop at the first non-capitalized, non-stop word
            end = len(words)
            for i in range(v_index + 1, len(words)):
                word = words[i]
                if not word.istitle() and word.lower() not in STOP_WORDS:
                    end = i
                    break
            
            case_name = ' '.join(words[start:end])
            print(f"DEBUG: Extracted case name: '{case_name}'")
            return case_name.strip()
    
    return None

def find_citation_regex(text, citation):
    # Build a regex pattern to match the citation with optional trailing pages and reporter info
    # Example: '200 Wn.2d 72' should match '200 Wn.2d 72, 73, 514 P.3d 643'
    citation_pattern = re.escape(citation)
    # Allow for optional comma, spaces, numbers, and reporter info after the citation
    citation_pattern += r'(?:[\s,0-9A-Za-z.]+)?'
    match = re.search(citation_pattern, text)
    if match:
        return match.start()
    return -1

def extract_case_name_for_citation(text, citation):
    # Normalize text and citation
    norm_text = re.sub(r'\s+', ' ', text).strip()
    norm_citation = re.sub(r'\s+', ' ', citation).strip()
    
    # Find citation position using regex
    citation_pos = find_citation_regex(norm_text, norm_citation)
    if citation_pos == -1:
        print(f"ERROR: Citation '{citation}' not found in text")
        return None
    
    # Only consider matches before the citation
    matches = []
    for pattern in V_PATTERNS:
        for m in re.finditer(pattern, norm_text):
            if m.end() <= citation_pos:
                matches.append(m)
    print(f"DEBUG: Found {len(matches)} matches before citation '{citation}'")
    if not matches:
        return None
    
    # Use the last match before the citation
    last = matches[-1]
    match_text = last.group(1)
    print(f"DEBUG: Match before citation: '{match_text}'")
    
    # Clean up the match and split into words
    match_text = re.sub(r'\s+', ' ', match_text).strip()
    words = match_text.split()
    
    # Find the v. position
    v_index = None
    for i, w in enumerate(words):
        if w.lower() in {'v.', 'vs.', 'versus'}:
            v_index = i
            break
    if v_index is None:
        return None
    
    print(f"DEBUG: Words: {words}")
    print(f"DEBUG: V index: {v_index}")
    
    # Find the start: work backwards from v_index-1 to find the first non-capitalized, non-stop word or punctuation boundary
    start = 0
    for i in range(v_index-1, -1, -1):
        word = words[i]
        is_capitalized = word.istitle() or word.isupper()
        print(f"DEBUG: Checking start word '{word}' at index {i}: capitalized={is_capitalized}, stop_word={word.lower() in STOP_WORDS}")
        # If the word is a punctuation boundary, stop here
        if any(punct in word for punct in [';', '.', ':']):
            start = i + 1
            print(f"DEBUG: Hit punctuation boundary at index {i}, start at {start}")
            break
        if not is_capitalized and word.lower() not in STOP_WORDS:
            start = i + 1  # Start at the next word after this one
            print(f"DEBUG: Found start at index {start}")
            break
    
    # Find the end: scan forward from v_index+1 to find the last capitalized word
    end = len(words)
    for i in range(v_index+1, len(words)):
        word = words[i]
        is_capitalized = word.istitle() or word.isupper()
        print(f"DEBUG: Checking end word '{word}' at index {i}: capitalized={is_capitalized}, stop_word={word.lower() in STOP_WORDS}")
        if not is_capitalized and word.lower() not in STOP_WORDS:
            end = i  # Stop at this word (don't include it)
            print(f"DEBUG: Found end at index {end}")
            break
    
    case_name = ' '.join(words[start:end])
    print(f"DEBUG: Extracted case name: '{case_name}'")
    return case_name.strip()

def main():
    # The actual problematic text from the API response
    text = """ton law 
when a resolution of that question is necessary to resolve a case before the 
federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d
72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review
de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 
(2011). We also review the meaning of a statute de novo. Dep't of Ecology v.
Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    citations = [
        ("200 Wn.2d 72", "Convoyant, LLC v. DeepThink, LLC"),
        ("171 Wn.2d 486", "Carlson v. Glob. Client Sols., LLC"),
        ("146 Wn.2d 1", "Dep't of Ecology v. Campbell & Gwinn, LLC")
    ]
    for citation_text, expected_case_name in citations:
        print(f"\nTesting citation: {citation_text}")
        print(f"Expected: {expected_case_name}")
        extracted_name = extract_case_name_for_citation(text, citation_text)
        print(f"Extracted: {extracted_name}")
        if extracted_name == expected_case_name:
            print("✅ PASS")
        else:
            print("❌ FAIL")
        print("-" * 40)

if __name__ == "__main__":
    main() 