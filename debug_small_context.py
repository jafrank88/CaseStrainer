#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.case_name_extraction_core import extract_case_name_and_date

def debug_small_context():
    """Test with a very small context window."""
    
    # Test text with both citations
    test_text = """
    Municipal corporations are not typically within the zone of interest of individual constitutional guarantees. 
    See, e.g., Lakehaven Water & Sewer Dist. v. City of Fed. Way, 195 Wn.2d 742, 773, 466 P.3d 213 (2020) 
    (sewer and water district lacked standing to challenge constitutional issues).
    
    The State has a duty to actively provide criminal defense services to those who cannot afford it. 
    See Davison v. State, 196 Wn.2d 285, 293, 466 P.3d 231 (2020) 
    ("The State plainly has a duty to provide indigent defense").
    """
    
    citation = "196 Wn.2d 285"
    
    print("=== SMALL CONTEXT TEST ===")
    print(f"Citation: {citation}")
    print()
    
    # Test with different context window sizes
    context_sizes = [50, 100, 150, 200, 300]
    
    for size in context_sizes:
        print(f"--- Context window: {size} characters ---")
        
        # Find citation position
        citation_pos = test_text.find(citation)
        if citation_pos == -1:
            print(f"❌ Citation not found")
            continue
            
        # Calculate context window
        context_start = max(0, citation_pos - size)
        context_end = min(len(test_text), citation_pos + len(citation) + 100)
        context = test_text[context_start:context_end]
        
        print(f"Context: {repr(context)}")
        
        # Check what case names are in the context
        if "Lakehaven" in context:
            print(f"⚠️  'Lakehaven' found in context")
        if "Davison" in context:
            print(f"✅ 'Davison' found in context")
            
        # Extract case name
        result = extract_case_name_and_date(context, citation)
        case_name = result.get('case_name') if result else 'None'
        print(f"Extracted case name: {case_name}")
        
        if "Davison" in case_name:
            print(f"✅ CORRECT: Davison found in extracted case name")
        else:
            print(f"❌ INCORRECT: Davison not found in extracted case name")
        print()

if __name__ == "__main__":
    debug_small_context() 