#!/usr/bin/env python3
"""
Debug case name extraction for the specific Spokeo citation.
"""

import re

def test_regex_patterns():
    """Test the regex patterns directly."""
    
    text = 'The Supreme Court held in Spokeo, Inc. v. Robins, 578 U.S. 330 (2016) (quoting Raines v. Byrd, 521 U.S. 811, 820 n.3, 117 S. Ct. 2312, 138 L. Ed. 2d 849 (1997)) that standing requirements cannot be erased.'
    
    # The patterns from unified_extraction_architecture.py
    patterns = [
        # COMPANY NAME patterns - handle "Company, Inc. v. Other Party" correctly
        r'([A-Z][a-zA-Z\s\'&\-\.,]+(?:LLC|Inc\.?|Corp\.?|Ltd\.?|Co\.?))\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.,]{1,50})',
        r'([A-Z][a-zA-Z\s\'&\-\.,]{1,50})\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.,]+(?:LLC|Inc\.?|Corp\.?|Ltd\.?|Co\.?))',
        # DEPARTMENT patterns
        r'([A-Z][a-zA-Z\s\'&\-\.]{1,50})\s+v\.\s+(Dep\'t\s+of\s+[A-Z][a-zA-Z\s\'&\-\.]{1,50})',
        # GENERAL pattern with length limits to avoid over-matching
        r'([A-Z][a-zA-Z\s\'&\-\.]{1,50})\s+v\.\s+([A-Z][a-zA-Z\s\'&\-\.]{1,50})',
    ]
    
    print("🔍 DEBUGGING CASE NAME EXTRACTION")
    print("=" * 60)
    print(f"📝 Text: {text}")
    print()
    
    # Find the 578 U.S. 330 citation position
    citation = "578 U.S. 330"
    start_pos = text.find(citation)
    end_pos = start_pos + len(citation)
    
    print(f"🎯 Target citation: {citation}")
    print(f"📍 Position: {start_pos}-{end_pos}")
    print()
    
    # Extract context around the citation
    context_start = max(0, start_pos - 500)
    context_end = min(len(text), end_pos + 100)
    context = text[context_start:context_end]
    
    print(f"📄 Context: '{context}'")
    print()
    
    # Test each pattern
    for i, pattern in enumerate(patterns):
        print(f"🔍 Testing pattern {i+1}: {pattern}")
        matches = list(re.finditer(pattern, context, re.IGNORECASE))
        print(f"   Found {len(matches)} matches")
        
        for j, match in enumerate(matches):
            plaintiff = match.group(1)
            defendant = match.group(2)
            full_match = match.group(0)
            match_start = match.start()
            match_end = match.end()
            
            print(f"   Match {j+1}:")
            print(f"     Full match: '{full_match}'")
            print(f"     Plaintiff: '{plaintiff}'")
            print(f"     Defendant: '{defendant}'")
            print(f"     Position in context: {match_start}-{match_end}")
            
            # Check if this match is close to our citation
            citation_start_in_context = start_pos - context_start
            distance = abs(match_end - citation_start_in_context)
            print(f"     Distance to citation: {distance}")
            
            # Apply case name cleaning
            from src.utils.text_normalizer import clean_extracted_case_name
            cleaned_plaintiff = clean_extracted_case_name(plaintiff)
            cleaned_defendant = clean_extracted_case_name(defendant)
            case_name = f"{cleaned_plaintiff} v. {cleaned_defendant}"
            
            print(f"     Cleaned case name: '{case_name}'")
            print()
        
        if not matches:
            print("   No matches found")
        print()

if __name__ == "__main__":
    test_regex_patterns()
