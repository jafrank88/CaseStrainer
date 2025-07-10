#!/usr/bin/env python3
"""
Debug script for testing citation extraction logic.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.case_name_extraction_core import extract_case_name_triple, extract_case_name_fixed, extract_year_enhanced

def debug_extraction_not_happening(text, citation):
    """
    Debug why extraction functions return N/A even when text contains case names.
    """
    print("=== EXTRACTION DEBUG ===")
    print(f"Text length: {len(text)}")
    print(f"Citation being used: '{citation}'")
    print(f"Text preview: '{text[:200]}...'")
    
    # Test 1: Can we find ANY citation format in the text?
    citation_variants = [
        citation,  # Original citation
        citation.replace("Wash. 2d", "Wn.2d"),  # Convert back to text format
        citation.replace("Wash. 2d", "Wn. 2d"),  # With space
    ]
    
    print("\n=== CITATION FINDING TEST ===")
    for i, variant in enumerate(citation_variants):
        pos = text.find(variant)
        print(f"Variant {i+1}: '{variant}' -> Found at position {pos}")
        if pos != -1:
            context = text[max(0, pos-50):pos+50]
            print(f"  Context: '{context}'")
    
    # Test 2: Look for case name patterns anywhere in text
    import re
    print("\n=== CASE NAME PATTERN TEST ===")
    case_patterns = [
        r'([A-Z][A-Za-z\'\.\s,&]+\s+v\.\s+[A-Z][A-Za-z\'\.\s,&]+)',
        r'(Dep\'t\s+of\s+[A-Za-z\s,&]+\s+v\.\s+[A-Za-z\s,&]+)',
        r'([A-Z][A-Za-z\s,&]+\s+v\.\s+[A-Z][A-Za-z\s,&]+)',
    ]
    
    for i, pattern in enumerate(case_patterns):
        matches = re.findall(pattern, text)
        print(f"Pattern {i+1}: Found {len(matches)} matches")
        for j, match in enumerate(matches):
            print(f"  Match {j+1}: '{match}'")
    
    # Test 3: Look for years anywhere in text
    print("\n=== YEAR PATTERN TEST ===")
    year_patterns = [
        r'\((\d{4})\)',  # Years in parentheses
        r'\b(\d{4})\b',  # Any 4-digit year
    ]
    
    for i, pattern in enumerate(year_patterns):
        matches = re.findall(pattern, text)
        print(f"Year pattern {i+1}: Found years: {matches}")
    
    # Test 4: Manual extraction test
    print("\n=== MANUAL EXTRACTION TEST ===")
    
    # Try to find citation in text with flexible matching
    citation_pos = -1
    working_citation = None
    
    for variant in citation_variants:
        pos = text.find(variant)
        if pos != -1:
            citation_pos = pos
            working_citation = variant
            break
    
    if citation_pos != -1:
        print(f"Found citation '{working_citation}' at position {citation_pos}")
        
        # Get context before citation
        context_before = text[max(0, citation_pos - 100):citation_pos]
        print(f"Context before citation: '{context_before}'")
        
        # Try to extract case name manually
        for pattern in case_patterns:
            matches = re.findall(pattern, context_before)
            if matches:
                case_name = matches[-1].strip()
                print(f"✅ MANUAL EXTRACTION SUCCESS - Case name: '{case_name}'")
                break
        else:
            print("❌ No case name found in context before citation")
        
        # Try to extract year manually
        context_after = text[citation_pos:citation_pos + 100]
        year_match = re.search(r'\((\d{4})\)', context_after)
        if year_match:
            year = year_match.group(1)
            print(f"✅ MANUAL EXTRACTION SUCCESS - Year: '{year}'")
        else:
            print("❌ No year found in context after citation")
    else:
        print("❌ No citation variant found in text")
    
    # Test 5: Test actual extraction functions
    print("\n=== TESTING ACTUAL EXTRACTION FUNCTIONS ===")
    
    try:
        # Test with original citation
        result1 = extract_case_name_fixed(text, citation)
        print(f"extract_case_name_fixed(original): '{result1}'")
        
        # Test with converted citation
        converted = citation.replace("Wash. 2d", "Wn.2d")
        result2 = extract_case_name_fixed(text, converted)
        print(f"extract_case_name_fixed(converted): '{result2}'")
        
        # Test year extraction
        year1 = extract_year_enhanced(text, citation)
        print(f"extract_year_enhanced(original): '{year1}'")
        
        year2 = extract_year_enhanced(text, converted)
        print(f"extract_year_enhanced(converted): '{year2}'")
        
        # Test triple extraction
        triple_result = extract_case_name_triple(text, citation)
        print(f"extract_case_name_triple(original): {triple_result}")
        
    except Exception as e:
        print(f"❌ Extraction function error: {e}")

def main():
    # Test with your actual data
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2002)"""

    test_citations = [
        "171 Wash. 2d 486 256 P.3d 321",
        "146 Wash. 2d 1 43 P.3d 4"
    ]

    for citation in test_citations:
        print(f"\n{'='*60}")
        print(f"TESTING CITATION: {citation}")
        print('='*60)
        debug_extraction_not_happening(test_text, citation)

if __name__ == "__main__":
    main() 