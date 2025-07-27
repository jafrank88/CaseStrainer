#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.case_name_extraction_core import extract_case_name_and_date

def debug_context_analysis():
    """Analyze the exact context being used for each citation."""
    
    # Test text with both citations
    test_text = """
    Municipal corporations are not typically within the zone of interest of individual constitutional guarantees. 
    See, e.g., Lakehaven Water & Sewer Dist. v. City of Fed. Way, 195 Wn.2d 742, 773, 466 P.3d 213 (2020) 
    (sewer and water district lacked standing to challenge constitutional issues).
    
    The State has a duty to actively provide criminal defense services to those who cannot afford it. 
    See Davison v. State, 196 Wn.2d 285, 293, 466 P.3d 231 (2020) 
    ("The State plainly has a duty to provide indigent defense").
    """
    
    citations = ["195 Wn. 2d 742", "196 Wn. 2d 285"]
    
    print("=== CONTEXT ANALYSIS ===")
    print(f"Full text length: {len(test_text)}")
    print(f"Full text: {repr(test_text)}")
    print()
    
    for citation in citations:
        print(f"--- Citation: {citation} ---")
        
        # Find citation position
        citation_pos = test_text.find(citation)
        if citation_pos == -1:
            print(f"❌ Citation not found")
            continue
            
        print(f"Citation position: {citation_pos}")
        
        # Calculate context window (300 chars before, 100 after)
        context_start = max(0, citation_pos - 300)
        context_end = min(len(test_text), citation_pos + len(citation) + 100)
        context = test_text[context_start:context_end]
        
        print(f"Context window: {context_start} to {context_end}")
        print(f"Context length: {len(context)}")
        print(f"Context: {repr(context)}")
        print()
        
        # Check what case names are in the context
        if "Lakehaven" in context:
            print(f"⚠️  'Lakehaven' found in context")
        if "Davison" in context:
            print(f"⚠️  'Davison' found in context")
            
        # Extract case name
        result = extract_case_name_and_date(context, citation)
        print(f"Extracted case name: {result.get('case_name') if result else 'None'}")
        print()

if __name__ == "__main__":
    debug_context_analysis() 