#!/usr/bin/env python3
"""
Debug script to test extraction logic step by step
"""

import re
from src.standalone_citation_parser import CitationParser

def test_extraction_step_by_step():
    """Test extraction logic step by step to see where it fails."""
    
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2002)"""
    
    test_citation = "146 Wn.2d 1"
    
    print("=== STEP-BY-STEP EXTRACTION DEBUG ===")
    print(f"Text: {test_text}")
    print(f"Citation: {test_citation}")
    print()
    
    # Step 1: Find citation in text
    citation_index = test_text.find(test_citation)
    print(f"Step 1 - Citation index: {citation_index}")
    
    if citation_index == -1:
        print("❌ Citation not found in text")
        return
    
    # Step 2: Get context before citation
    context_start = max(0, citation_index - 200)
    context_before = test_text[context_start:citation_index]
    print(f"Step 2 - Context before citation: '{context_before}'")
    
    # Step 3: Test the patterns from the parser
    patterns = [
        # Pattern 1: Full case names with LLC, Inc., etc. - most comprehensive
        r'([A-Z][A-Za-z\s,\.\'-]{1,80}?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]{1,80}?)(?=\s*[,;:.]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
        # Pattern 2: "Dep't of" cases (Department of)
        r'(Dep\'t\s+of\s+[A-Za-z\s,\.\'-]{1,80}?\s+v\.\s+[A-Za-z\s,\.\'-]{1,80}?)(?=\s*[,;:.]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
        # Pattern 3: "Department of" cases
        r'(Department\s+of\s+[A-Za-z\s,\.\'-]{1,80}?\s+v\.\s+[A-Za-z\s,\.\'-]{1,80}?)(?=\s*[,;:.]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
        # Pattern 4: In re cases with full names
        r'(In\s+re\s+[A-Za-z\s,\.\'-]{1,80}?)(?=\s*[,;:.]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
        # Pattern 5: State/People cases with full names
        r'(State\s+v\.\s+[A-Za-z\s,\.\'-]{1,80}?)(?=\s*[,;:.]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
        r'(People\s+v\.\s+[A-Za-z\s,\.\'-]{1,80}?)(?=\s*[,;:.]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
    ]
    
    search_text = context_before + test_citation
    print(f"Step 3 - Search text: '{search_text}'")
    
    for i, pattern in enumerate(patterns):
        print(f"\n--- Testing Pattern {i+1} ---")
        print(f"Pattern: {pattern}")
        match = re.search(pattern, search_text, re.IGNORECASE)
        if match:
            case_name = match.group(1).strip()
            case_name = re.sub(r',[\s]*$', '', case_name)
            print(f"✅ Matched: '{case_name}'")
        else:
            print("❌ No match")

if __name__ == "__main__":
    test_extraction_step_by_step() 