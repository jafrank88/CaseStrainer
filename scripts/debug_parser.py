#!/usr/bin/env python3
"""
Debug version of the comprehensive parser to see what's happening.
"""

import re

def debug_citation_finding():
    """Debug why citations aren't being found."""
    
    text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2002)"""
    
    print("=== DEBUGGING CITATION FINDING ===")
    print(f"Text: {text}")
    print()
    
    # Test citations
    test_citations = [
        "171 Wash. 2d 486 256 P.3d 321",
        "146 Wash. 2d 1 43 P.3d 4"
    ]
    
    for citation in test_citations:
        print(f"--- Testing: {citation} ---")
        
        # Parse the JSON citation
        parts = citation.split()
        print(f"Parts: {parts}")
        
        if len(parts) >= 4:
            volume = parts[0]
            # Handle multi-part reporters like "Wash. 2d"
            if len(parts) > 4 and parts[2].isdigit():
                reporter = f"{parts[1]} {parts[2]}"
                page = parts[3]
            else:
                reporter = parts[1]
                page = parts[2]
            
            print(f"Volume: {volume}")
            print(f"Reporter: {reporter}")
            print(f"Page: {page}")
            
            # Try to find in text with different patterns
            search_reporters = []
            if 'Wash.' in reporter:
                search_reporters.extend(['Wn.2d', 'Wn. 2d', 'Wash. 2d', 'Wash.2d'])
            elif 'Wn.' in reporter:
                search_reporters.extend(['Wn.2d', 'Wn. 2d', 'Wash. 2d', 'Wash.2d'])
            else:
                search_reporters.append(reporter)
            
            print(f"Search reporters: {search_reporters}")
            
            for search_reporter in search_reporters:
                print(f"  Trying reporter: {search_reporter}")
                
                # Simple pattern first
                simple_pattern = rf'{volume}\s+{re.escape(search_reporter)}\s+{page}'
                print(f"    Simple pattern: {simple_pattern}")
                
                matches = re.findall(simple_pattern, text)
                print(f"    Matches: {matches}")
                
                if matches:
                    print(f"    ✅ FOUND with simple pattern!")
                    # Now try to get the full citation with year
                    full_pattern = rf'{volume}\s+{re.escape(search_reporter)}\s+{page}[^()]*\(\d{{4}}\)'
                    full_matches = re.findall(full_pattern, text)
                    print(f"    Full citation matches: {full_matches}")
                    break
                else:
                    print(f"    ❌ No match with simple pattern")
        else:
            print("❌ Not enough parts in citation")
        
        print()

def test_manual_extraction():
    """Test manual extraction to see what should work."""
    print("=== MANUAL EXTRACTION TEST ===")
    
    text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2002)"""
    
    # Find all citations in text manually
    print("All citations found in text:")
    citation_pattern = r'(\d+\s+Wn\.2d\s+\d+[^()]*\(\d{4}\))'
    all_citations = re.findall(citation_pattern, text)
    for i, citation in enumerate(all_citations):
        print(f"  {i+1}. '{citation.strip()}'")
    
    # Find all case names
    print("\nAll case names found in text:")
    case_pattern = r'([A-Z][A-Za-z\'\.\s,&]*\s+v\.?\s+[A-Z][A-Za-z\'\.\s,&]*?)(?:\s*,\s*)?'
    all_cases = re.findall(case_pattern, text)
    for i, case_name in enumerate(all_cases):
        print(f"  {i+1}. '{case_name.strip()}'")
    
    # Find all years
    print("\nAll years found in text:")
    year_pattern = r'\((\d{4})\)'
    all_years = re.findall(year_pattern, text)
    for i, year in enumerate(all_years):
        print(f"  {i+1}. {year}")

if __name__ == "__main__":
    debug_citation_finding()
    print("\n" + "="*60 + "\n")
    test_manual_extraction() 