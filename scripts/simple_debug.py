#!/usr/bin/env python3
"""
Simple debug script to test extraction without missing imports.
Save this as scripts/simple_debug.py and run it.
"""

import sys
import os
import re

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def debug_extraction_simple():
    """
    Simple debug without importing missing functions.
    """
    
    # Your actual text
    text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2002)"""
    
    # Citations from your JSON (what the system is looking for)
    json_citations = [
        "171 Wash. 2d 486 256 P.3d 321", 
        "146 Wash. 2d 1 43 P.3d 4"
    ]
    
    print("=== EXTRACTION DEBUG TEST ===")
    print(f"Text length: {len(text)}")
    print(f"Text: {text[:100]}...")
    print()
    
    for i, citation in enumerate(json_citations):
        print(f"--- TESTING CITATION {i+1}: {citation} ---")
        
        # Test 1: Can we find this citation in text?
        pos = text.find(citation)
        print(f"Direct find: {pos}")
        
        # Test 2: Try converted citation
        converted = citation.replace("Wash. 2d", "Wn.2d")
        pos_converted = text.find(converted)
        print(f"Converted citation: {converted}")
        print(f"Converted find: {pos_converted}")
        
        # Test 3: Look for similar patterns
        volume = citation.split()[0]  # "171" or "146"
        print(f"Looking for volume {volume} in text...")
        
        pattern = rf'{volume}\s+Wn\.2d\s+\d+[,\s\d]*'
        matches = re.findall(pattern, text)
        print(f"Volume pattern matches: {matches}")
        
        if matches:
            actual_citation = matches[0]
            actual_pos = text.find(actual_citation)
            print(f"Found actual citation: '{actual_citation}' at position {actual_pos}")
            
            # Get context and try to extract case name
            if actual_pos != -1:
                context_before = text[max(0, actual_pos - 100):actual_pos]
                print(f"Context before: '{context_before}'")
                
                # Look for case name patterns
                case_patterns = [
                    r'([A-Z][A-Za-z\'\.\s,&]+\s+v\.\s+[A-Z][A-Za-z\'\.\s,&]+)',
                    r'(Dep\'t\s+of\s+[A-Za-z\s,&]+\s+v\.\s+[A-Za-z\s,&]+)',
                ]
                
                for pattern in case_patterns:
                    case_matches = re.findall(pattern, context_before)
                    if case_matches:
                        case_name = case_matches[-1].strip()
                        print(f"✅ FOUND CASE NAME: '{case_name}'")
                        break
                else:
                    print("❌ No case name found")
                
                # Look for year
                year_match = re.search(r'\((\d{4})\)', text[actual_pos:actual_pos+50])
                if year_match:
                    year = year_match.group(1)
                    print(f"✅ FOUND YEAR: '{year}'")
                else:
                    print("❌ No year found")
        else:
            print("❌ No similar citation pattern found")
        
        print()

def test_existing_functions():
    """
    Test the existing functions that should work.
    """
    print("=== TESTING EXISTING FUNCTIONS ===")
    
    try:
        # Try importing the core module
        from src.case_name_extraction_core import extract_case_name_triple
        print("✅ Successfully imported extract_case_name_triple")
        
        text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2002)"""
        
        citation = "171 Wash. 2d 486 256 P.3d 321"
        
        print(f"Testing with citation: {citation}")
        print(f"Text length: {len(text)}")
        
        result = extract_case_name_triple(text, citation, api_key=None)
        print(f"Result: {result}")
        
        # Check what the function actually returned
        print("\nResult breakdown:")
        for key, value in result.items():
            print(f"  {key}: '{value}'")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Execution error: {e}")

def test_manual_extraction():
    """
    Manual extraction to see what should work.
    """
    print("=== MANUAL EXTRACTION TEST ===")
    
    text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2002)"""
    
    # Find all case names in the text
    print("All case names in text:")
    case_pattern = r'([A-Z][A-Za-z\'\.\s,&]+\s+v\.\s+[A-Z][A-Za-z\'\.\s,&]+)'
    all_cases = re.findall(case_pattern, text)
    for i, case in enumerate(all_cases):
        print(f"  {i+1}. '{case.strip()}'")
    
    # Find all years in text
    print("\nAll years in text:")
    year_pattern = r'\((\d{4})\)'
    all_years = re.findall(year_pattern, text)
    for i, year in enumerate(all_years):
        print(f"  {i+1}. {year}")
    
    # Find all citations in text
    print("\nAll citations in text:")
    citation_pattern = r'(\d+\s+Wn\.2d\s+\d+[,\s\d]*[A-Z\.\d\s]*\(\d{4}\))'
    all_citations = re.findall(citation_pattern, text)
    for i, citation in enumerate(all_citations):
        print(f"  {i+1}. '{citation.strip()}'")

if __name__ == "__main__":
    debug_extraction_simple()
    print("\n" + "="*60 + "\n")
    test_manual_extraction()
    print("\n" + "="*60 + "\n")
    test_existing_functions() 