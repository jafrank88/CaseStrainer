#!/usr/bin/env python3

import requests
import json
import re

def debug_structural_pattern():
    """Debug the structural pattern recognition in detail."""
    
    text = "Lopez Demetrio v. Sakuma Bros. Farms, 183 Wn.2d 649, 655, 355 P.3d 258 (2015)."
    
    print("STRUCTURAL PATTERN RECOGNITION DEBUG")
    print("=" * 60)
    print(f"Text: {text}")
    print(f"Text length: {len(text)}")
    print()
    
    # Test the regex pattern
    pattern = r'([A-Z][^,]+v\.\s+[A-Z][^,]+),\s*([^()]+)\((\d{4})\)'
    matches = list(re.finditer(pattern, text, re.IGNORECASE))
    
    if matches:
        match = matches[0]
        case_name = match.group(1).strip()
        citations_text = match.group(2).strip()
        year = match.group(3)
        match_start = match.start()
        match_end = match.end()
        
        print("REGEX PATTERN MATCH:")
        print(f"  Case Name: '{case_name}'")
        print(f"  Citations Text: '{citations_text}'")
        print(f"  Year: {year}")
        print(f"  Pattern Position: {match_start}-{match_end}")
        print(f"  Pattern Text: '{text[match_start:match_end]}'")
        print()
        
        # Now get actual citations from API to see their positions
        print("GETTING ACTUAL CITATIONS FROM API:")
        url = "http://localhost:5000/casestrainer/api/analyze"
        data = {"text": text, "type": "text"}
        
        try:
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                citations = result.get('citations', [])
                
                print(f"Found {len(citations)} citations:")
                print()
                
                for i, citation in enumerate(citations, 1):
                    citation_text = citation.get('citation', '')
                    start_index = citation.get('start_index', 'N/A')
                    end_index = citation.get('end_index', 'N/A')
                    
                    print(f"Citation {i}: '{citation_text}'")
                    print(f"  Position: {start_index}-{end_index}")
                    
                    if start_index != 'N/A' and end_index != 'N/A':
                        actual_text = text[start_index:end_index]
                        print(f"  Actual Text: '{actual_text}'")
                        
                        # Check position criteria
                        within_pattern = (start_index >= match_start and end_index <= match_end)
                        print(f"  Within Pattern Boundaries: {within_pattern}")
                        
                        # Check text criteria  
                        in_citations_text = citation_text in citations_text
                        print(f"  In Citations Text: {in_citations_text}")
                        
                        if within_pattern and in_citations_text:
                            print("  ✅ SHOULD BE GROUPED")
                        else:
                            print("  ❌ WILL NOT BE GROUPED")
                            if not within_pattern:
                                print(f"    - Position issue: {start_index}-{end_index} not within {match_start}-{match_end}")
                            if not in_citations_text:
                                print(f"    - Text issue: '{citation_text}' not found in '{citations_text}'")
                    print()
                    
            else:
                print(f"API Error: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"API Request failed: {e}")
    else:
        print("❌ No regex pattern match found!")

if __name__ == "__main__":
    debug_structural_pattern()
