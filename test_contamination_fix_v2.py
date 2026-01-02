#!/usr/bin/env python3
"""
Test script to verify the contamination fix works correctly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_case_extraction_master import extract_case_name_and_date_unified_master

def test_contamination_fix():
    """Test that the contamination filter now works in all extraction strategies"""
    
    # The document's primary case name that was contaminating all citations
    document_primary_case = "R.PENDLETON SUPREME COURT CLERK John Doe P et al. v. Thurston County et al."
    
    # Sample text that might appear in the problematic document
    test_text = """
    In the case of R.PENDLETON SUPREME COURT CLERK John Doe P et al. v. Thurston County et al., 
    the court considered various precedents. See Seattle Times Co v. Ishikawa, 97 Wash. 2d 30 (1982).
    Another important case is Berst v. Snohomish County, 114 Wn. App. 245 (1993).
    """
    
    print("🧪 TESTING CONTAMINATION FIX")
    print("=" * 60)
    print(f"Document Primary Case: '{document_primary_case}'")
    print(f"Test text contains citations that should NOT get the primary case name")
    print()
    
    # Test extraction for a citation in the text
    citations_to_test = [
        ("97 Wash. 2d 30", "Seattle Times Co v. Ishikawa"),
        ("114 Wn. App. 245", "Berst v. Snohomish County"),
    ]
    
    for citation, expected_case in citations_to_test:
        print(f"🔍 Testing citation: {citation}")
        print(f"   Expected: {expected_case}")
        print(f"   Should NOT get: '{document_primary_case}'")
        
        # Find citation position in text
        citation_pos = test_text.find(citation)
        if citation_pos == -1:
            print(f"   ❌ Citation not found in test text")
            continue
        
        # Test extraction
        result = extract_case_name_and_date_unified_master(
            text=test_text,
            citation=citation,
            start_index=citation_pos,
            end_index=citation_pos + len(citation),
            debug=True,
            document_primary_case_name=document_primary_case
        )
        
        extracted_case = result.get('extracted_case_name', 'N/A')
        display_case = result.get('case_name', 'N/A')
        
        print(f"   Result extracted_case_name: '{extracted_case}'")
        print(f"   Result case_name: '{display_case}'")
        
        # Check if contamination was prevented
        if extracted_case == document_primary_case:
            print(f"   ❌ CONTAMINATION FAILED: Still getting document primary case name!")
        elif extracted_case == 'N/A':
            print(f"   ✅ CONTAMINATION PREVENTED: Rejected contaminated case name (returned N/A)")
        else:
            print(f"   ✅ CONTAMINATION PREVENTED: Got different case name (not contaminated)")
        
        print()

if __name__ == "__main__":
    test_contamination_fix()
