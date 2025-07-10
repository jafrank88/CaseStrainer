#!/usr/bin/env python3
"""
Debug script specifically for Dep't of Ecology case
"""

import re
from src.standalone_citation_parser import CitationParser

def debug_dep_case():
    """Debug the Dep't of Ecology case extraction."""
    
    # Full text with the Dep't case
    full_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2002)"""
    
    citation = "146 Wn.2d 1"
    
    print("=== DEBUGGING DEP'T OF ECOLOGY CASE ===")
    print(f"Citation: {citation}")
    print()
    
    # Step 1: Find citation position
    citation_index = full_text.find(citation)
    print(f"Citation found at index: {citation_index}")
    
    # Step 2: Get context before citation
    context_start = max(0, citation_index - 200)
    context_before = full_text[context_start:citation_index]
    print(f"Context before citation ({len(context_before)} chars):")
    print(f"'{context_before}'")
    print()
    
    # Step 3: Test individual patterns
    patterns = [
        r'(Dep\'t\s+of\s+[A-Za-z\s,\.\'-]{1,80}?\s+v\.\s+[A-Za-z\s,\.\'-]{1,80}?)(?=\s*[,;:.]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
        r'(Dep\'t\s+of\s+[A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;:.]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
        r'(Dep\'t\s+of\s+[A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Za-z\s,\.\'-]+?)',
        r'(Dep\'t\s+of\s+[A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;:.]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
    ]
    
    search_text = context_before + citation
    print(f"Search text: '{search_text}'")
    print()
    
    for i, pattern in enumerate(patterns):
        print(f"--- Testing Pattern {i+1} ---")
        print(f"Pattern: {pattern}")
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            case_name = match.group(1).strip()
            print(f"✅ Matched: '{case_name}'")
        else:
            print("❌ No match")
        print()
    
    # Step 4: Test the actual parser
    print("--- Testing Actual Parser ---")
    parser = CitationParser()
    result = parser.extract_from_text(full_text, citation)
    print(f"Parser result: {result}")

if __name__ == "__main__":
    debug_dep_case() 