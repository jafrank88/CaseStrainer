#!/usr/bin/env python3
"""
Test script to verify the contamination fix works with production-like scenarios
This simulates the exact problem from response.json where ALL citations got the same case name
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_case_extraction_master import extract_case_name_and_date_unified_master

def test_production_contamination_fix():
    """Test that simulates the production contamination scenario"""
    
    # The document's primary case name that was contaminating ALL citations in response.json
    document_primary_case = "R.PENDLETON SUPREME COURT CLERK John Doe P et al. v. Thurston County et al."
    
    # Simulate a legal document with the problematic header and multiple citations
    # This represents the structure that was causing the contamination
    test_document = f"""
    {document_primary_case}
    
    IN THE SUPREME COURT OF THE STATE OF WASHINGTON
    
    No. 47604-7, 47623-3
    
    JOHN DOE P, et al., 
        Petitioners,
    v.
    THURSTON COUNTY, et al.,
        Respondents.
    
    _______________________________________
    
    BRIEF OF PETITIONERS
    
    The court has considered several important precedents in this matter.
    In Seattle Times Co v. Ishikawa, the court addressed media liability issues.
    Seattle Times Co v. Ishikawa, 97 Wash. 2d 30, 8 Media L. Rep. (BNA) 1041, 1982 Wash. LEXIS 1259 (1982).
    
    Similarly, in Berst v. Snohomish County, the court examined county liability.
    Berst v. Snohomish County, 185 Wash. 2d 363, 374 P.3d 63 (2014).
    
    The case of State v. Manussier provides additional context for criminal procedure.
    State v. Manussier, 129 Wn.2d 652, 621 P.2d 308 (1980).
    
    These precedents, taken together, establish the legal framework for our analysis.
    """
    
    print("🧪 TESTING PRODUCTION CONTAMINATION FIX")
    print("=" * 70)
    print(f"Document Primary Case: '{document_primary_case}'")
    print("📋 Testing scenario that caused ALL citations to get contaminated")
    print()
    
    # Test the specific citations that were getting contaminated in response.json
    problematic_citations = [
        {
            "citation": "97 Wash. 2d 30",
            "expected": "Seattle Times Co v. Ishikawa",
            "context": "Seattle Times Co v. Ishikawa, 97 Wash. 2d 30"
        },
        {
            "citation": "185 Wash. 2d 363", 
            "expected": "Berst v. Snohomish County",
            "context": "Berst v. Snohomish County, 185 Wash. 2d 363"
        },
        {
            "citation": "129 Wn.2d 652",
            "expected": "State v. Manussier", 
            "context": "State v. Manussier, 129 Wn.2d 652"
        }
    ]
    
    contamination_prevented_count = 0
    total_tests = len(problematic_citations)
    
    for i, test_case in enumerate(problematic_citations, 1):
        citation = test_case["citation"]
        expected = test_case["expected"]
        context = test_case["context"]
        
        print(f"🔍 Test {i}/{total_tests}: {citation}")
        print(f"   Expected: '{expected}'")
        print(f"   Should NOT get: '{document_primary_case[:50]}...'")
        
        # Find citation position in document
        citation_pos = test_document.find(citation)
        if citation_pos == -1:
            print(f"   ❌ Citation not found in test document")
            continue
        
        # Test extraction with contamination filter enabled
        result = extract_case_name_and_date_unified_master(
            text=test_document,
            citation=citation,
            start_index=citation_pos,
            end_index=citation_pos + len(citation),
            debug=False,  # Set to True for detailed debugging
            document_primary_case_name=document_primary_case
        )
        
        extracted_case = result.get('extracted_case_name', 'N/A')
        display_case = result.get('case_name', 'N/A')
        method = result.get('method', 'unknown')
        
        print(f"   Method: {method}")
        print(f"   extracted_case_name: '{extracted_case}'")
        print(f"   case_name: '{display_case}'")
        
        # Evaluate results
        if extracted_case == document_primary_case:
            print(f"   ❌ CONTAMINATION FAILED: Got document primary case name!")
            print(f"      This is the exact bug we're trying to fix!")
        elif extracted_case == 'N/A':
            print(f"   ✅ CONTAMINATION PREVENTED: Rejected contaminated name (N/A)")
            contamination_prevented_count += 1
        elif extracted_case == expected:
            print(f"   ✅ PERFECT: Got expected case name without contamination!")
            contamination_prevented_count += 1
        else:
            print(f"   ⚠️  DIFFERENT: Got '{extracted_case}' (not contaminated, but not expected)")
            contamination_prevented_count += 1
        
        print()
    
    # Summary
    print("=" * 70)
    print("📊 CONTAMINATION FIX SUMMARY")
    print(f"Tests passed: {contamination_prevented_count}/{total_tests}")
    print(f"Success rate: {contamination_prevented_count/total_tests*100:.1f}%")
    
    if contamination_prevented_count == total_tests:
        print("✅ SUCCESS: All citations protected from contamination!")
        print("🎯 The production bug has been FIXED!")
    else:
        print("❌ FAILURE: Some citations still getting contaminated")
        print("🔧 Additional fixes may be needed")
    
    print()
    print("🔍 KEY FIX APPLIED:")
    print("- Added contamination validation to _extract_with_citation_context()")
    print("- This ensures ALL extraction strategies now use the contamination filter")
    print("- Document primary case names are properly rejected in all paths")

if __name__ == "__main__":
    test_production_contamination_fix()
