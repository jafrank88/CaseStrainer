#!/usr/bin/env python3
"""
Direct test of case name extraction functions to debug the issue
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_case_name_extraction_direct():
    """Test case name extraction directly"""
    
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
    
    # The problematic citation
    problematic_citation = "392 P.3d 1041"
    
    print("=== Testing Case Name Extraction Directly ===")
    print(f"Citation: {problematic_citation}")
    print()
    
    try:
        # Test the main function that's actually being used
        from case_name_extraction_core import extract_case_name_and_date
        
        print("=== Testing extract_case_name_and_date ===")
        result = extract_case_name_and_date(test_text, problematic_citation)
        print(f"Result: {result}")
        print(f"Case Name: '{result.get('case_name', 'N/A')}'")
        print(f"Date: '{result.get('date', 'N/A')}'")
        print(f"Method: '{result.get('method', 'N/A')}'")
        print()
        
        # Test the extractor directly
        from case_name_extraction_core import CaseNameExtractor
        
        print("=== Testing CaseNameExtractor.extract ===")
        extractor = CaseNameExtractor()
        extraction_result = extractor.extract(test_text, problematic_citation)
        print(f"Extraction Result: {extraction_result}")
        print(f"Case Name: '{extraction_result.case_name}'")
        print(f"Method: '{extraction_result.method}'")
        print()
        
        # Test the precise function I modified
        from case_name_extraction_core import extract_case_name_precise
        
        print("=== Testing extract_case_name_precise (Modified Function) ===")
        
        # Find the citation position
        citation_pos = test_text.find(problematic_citation)
        if citation_pos != -1:
            context_before = test_text[:citation_pos]
            print(f"Context before citation ({len(context_before)} chars):")
            print(f"'{context_before[-200:]}'")  # Last 200 chars
            print()
            
            case_name = extract_case_name_precise(context_before, problematic_citation, debug=True)
            print(f"Precise extraction result: '{case_name}'")
        else:
            print("❌ Citation not found in text!")
        
        print()
        
        # Test the comprehensive function
        from case_name_extraction_core import extract_case_name_triple_comprehensive
        
        print("=== Testing extract_case_name_triple_comprehensive ===")
        case_name, date, confidence = extract_case_name_triple_comprehensive(test_text, problematic_citation)
        print(f"Comprehensive result: '{case_name}' | '{date}' | '{confidence}'")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_case_name_extraction_direct()
