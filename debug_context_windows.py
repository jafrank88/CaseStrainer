#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.case_name_extraction_core import extract_case_name_and_date, CaseNameExtractor

def debug_context_windows():
    """Debug the context windows being used for case name extraction for both citations."""
    
    # Test text with both citations
    test_text = """
    Municipal corporations are not typically within the zone of interest of individual constitutional guarantees. 
    See, e.g., Lakehaven Water & Sewer Dist. v. City of Fed. Way, 195 Wn.2d 742, 773, 466 P.3d 213 (2020) 
    (sewer and water district lacked standing to challenge constitutional issues).
    
    The State has a duty to actively provide criminal defense services to those who cannot afford it. 
    See Davison v. State, 196 Wn.2d 285, 293, 466 P.3d 231 (2020) 
    ("The State plainly has a duty to provide indigent defense").
    """
    
    citations = [
        ("195 Wn. 2d 742", "Lakehaven Water & Sewer Dist. v. City of Fed. Way"),
        ("196 Wn. 2d 285", "Davison v. State"),
    ]
    
    extractor = CaseNameExtractor()
    
    for citation, expected in citations:
        print(f"\n=== CONTEXT WINDOW FOR: {citation} ===")
        context = extractor._get_system_extraction_context(test_text, citation)
        print(f"Context window (len={len(context)}):\n{context}\n")
        result = extract_case_name_and_date(context, citation)
        print(f"Extracted case name: {result.get('case_name')}")
        print(f"Expected: {expected}")

if __name__ == "__main__":
    debug_context_windows() 