#!/usr/bin/env python3

import re

def test_regex_pattern():
    """Test the structural citation pattern regex."""
    
    text = "Lopez Demetrio v. Sakuma Bros. Farms, 183 Wn.2d 649, 655, 355 P.3d 258 (2015)."
    
    print("REGEX PATTERN TEST")
    print("=" * 50)
    print(f"Text: {text}")
    print()
    
    # The patterns from the code
    citation_structure_patterns = [
        # Standard pattern: Case v. Case, Citation1, Citation2 (Year)
        r'([A-Z][^,]+v\.\s+[A-Z][^,]+),\s*([^()]+)\((\d{4})\)',
        # Quoting pattern: (quoting Case v. Case, Citation1, Citation2 (Year))
        r'\(quoting\s+([A-Z][^,]+v\.\s+[A-Z][^,]+),\s*([^()]+)\((\d{4})\)\)',
        # Alternative pattern with "held in"
        r'held\s+in\s+([A-Z][^,]+v\.\s+[A-Z][^,]+),\s*([^()]+)\((\d{4})\)'
    ]
    
    for i, pattern in enumerate(citation_structure_patterns, 1):
        print(f"Pattern {i}: {pattern}")
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        found_match = False
        for match in matches:
            found_match = True
            case_name = match.group(1).strip()
            citations_text = match.group(2).strip()
            year = match.group(3)
            
            print(f"  ✅ MATCH FOUND!")
            print(f"    Case Name: '{case_name}'")
            print(f"    Citations Text: '{citations_text}'")
            print(f"    Year: {year}")
            print(f"    Position: {match.start()}-{match.end()}")
        
        if not found_match:
            print(f"  ❌ No match found")
        print()

if __name__ == "__main__":
    test_regex_pattern()
