#!/usr/bin/env python3
"""
Debug script to test case name extraction for "392 P.3d 1041"
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from case_name_extraction_core import extract_case_name_triple_comprehensive

def test_case_name_extraction():
    """Test case name extraction with the problematic text"""
    
    # The exact text from the user's test paragraph
    test_text = """We review a trial court's findings of fact for substantial evidence, generally 
deferring to the trier of fact on questions of witness credibility, conflicting 
testimony, and persuasiveness of the evidence. In re Vulnerable Adult Petition 
for Knight, 178 Wn. App. 929, 936-37, 317 P.3d 1068 (2014). Evidence is 
substantial when sufficient to persuade a fair-minded person of the truth of the 
matter asserted. In re Marriage of Black, 188 Wn.2d 114, 127, 392 P.3d 1041 
(2017). "Competent evidence sufficient to support the trial court's decision to 
grant . . . a domestic violence protection order may contain hearsay or be wholly 
documentary." Blackmon v. Blackmon, 155 Wn. App. 715, 722, 230 P.3d 233 
(2010)."""
    
    # Test the problematic citation
    citation = "392 P.3d 1041"
    
    print("=== Testing Case Name Extraction ===")
    print(f"Text: {test_text}")
    print(f"Citation: {citation}")
    print()
    
    try:
        # Test the legacy function
        case_name, date, confidence = extract_case_name_triple_comprehensive(test_text, citation)
        print("=== Legacy Function Result ===")
        print(f"Case Name: '{case_name}'")
        print(f"Date: '{date}'")
        print(f"Confidence: '{confidence}'")
        print()
        
        # Test with different context windows
        print("=== Testing Different Context Windows ===")
        
        # Find the citation position
        citation_pos = test_text.find(citation)
        if citation_pos != -1:
            # Context before citation (200 chars)
            context_before = test_text[max(0, citation_pos - 200):citation_pos]
            print(f"Context before (200 chars): '{context_before}'")
            print()
            
            # Context after citation (100 chars)
            context_after = test_text[citation_pos + len(citation):citation_pos + len(citation) + 100]
            print(f"Context after (100 chars): '{context_after}'")
            print()
            
            # Test with just the context around the citation
            context_window = 300
            start_pos = max(0, citation_pos - context_window)
            end_pos = min(len(test_text), citation_pos + len(citation) + context_window)
            context_text = test_text[start_pos:end_pos]
            
            print(f"Context window ({context_window} chars): '{context_text}'")
            print()
            
            # Test extraction with context window
            case_name2, date2, confidence2 = extract_case_name_triple_comprehensive(context_text, citation)
            print("=== Context Window Result ===")
            print(f"Case Name: '{case_name2}'")
            print(f"Date: '{date2}'")
            print(f"Confidence: '{confidence2}'")
            
        else:
            print("❌ Citation not found in text!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_case_name_extraction()
