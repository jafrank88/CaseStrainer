#!/usr/bin/env python3
"""
Test script to investigate citation-to-case-name association bug
The issue: citations might be getting case names from the wrong citations in the document
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_case_extraction_master import extract_case_name_and_date_unified_master

def test_citation_association():
    """Test if citations are getting case names from the wrong citations"""
    
    # Simulate a document with multiple cases and citations
    test_document = """
    SUPREME COURT OF WASHINGTON
    
    John Doe P et al. v. Thurston County, No. 47604-7
    
    In the landmark case of City of Bellevue v. Lorang, the court addressed 
    municipal liability issues. The ruling in City of Bellevue v. Lorang, 
    140 Wn.2d 19, 32, 992 P.2d 496 (2000) established important precedent.
    
    However, in a different matter, Seattle Times Co v. Ishikawa dealt with 
    media freedom. The court's decision in Seattle Times Co v. Ishikawa, 
    97 Wash. 2d 30 (1982) provided additional guidance.
    
    The court also considered Berst v. Snohomish County, which involved 
    county liability. See Berst v. Snohomish County, 114 Wn. App. 245 (1993).
    """
    
    print("🔍 INVESTIGATING CITATION-TO-CASE-NAME ASSOCIATION BUG")
    print("=" * 70)
    print("Testing if citations get case names from the WRONG citations")
    print()
    
    # Test cases where we need to verify correct association
    test_cases = [
        {
            "citation": "140 Wn.2d 19",
            "expected_case": "City of Bellevue v. Lorang",
            "wrong_case": "John Doe P et al. v. Thurston County",
            "description": "Should get Lorang case, not document header case"
        },
        {
            "citation": "97 Wash. 2d 30", 
            "expected_case": "Seattle Times Co v. Ishikawa",
            "wrong_case": "City of Bellevue v. Lorang",
            "description": "Should get Ishikawa case, not Lorang case"
        },
        {
            "citation": "114 Wn. App. 245",
            "expected_case": "Berst v. Snohomish County", 
            "wrong_case": "Seattle Times Co v. Ishikawa",
            "description": "Should get Berst case, not Ishikawa case"
        }
    ]
    
    # Test each citation
    for i, test_case in enumerate(test_cases, 1):
        citation = test_case["citation"]
        expected = test_case["expected_case"]
        wrong_case = test_case["wrong_case"]
        description = test_case["description"]
        
        print(f"🧪 Test {i}: {citation}")
        print(f"   Description: {description}")
        print(f"   Expected: '{expected}'")
        print(f"   Should NOT get: '{wrong_case}'")
        
        # Find citation in document
        citation_pos = test_document.find(citation)
        if citation_pos == -1:
            print(f"   ❌ Citation not found in document")
            continue
        
        # Extract case name for this citation
        result = extract_case_name_and_date_unified_master(
            text=test_document,
            citation=citation,
            start_index=citation_pos,
            end_index=citation_pos + len(citation),
            debug=True,
            document_primary_case_name="John Doe P et al. v. Thurston County"  # Document header
        )
        
        extracted_case = result.get('extracted_case_name', 'N/A')
        method = result.get('method', 'unknown')
        
        print(f"   Method: {method}")
        print(f"   Extracted: '{extracted_case}'")
        
        # Analyze the result
        if extracted_case == expected:
            print(f"   ✅ CORRECT: Got expected case name")
        elif extracted_case == wrong_case:
            print(f"   ❌ ASSOCIATION BUG: Got case name from WRONG citation!")
            print(f"      This citation is associated with '{wrong_case}' instead of '{expected}'")
        elif extracted_case == 'N/A':
            print(f"   ⚠️  NO EXTRACTION: Could not extract case name")
        else:
            print(f"   ⚠️  UNEXPECTED: Got '{extracted_case}' (different from both expected and wrong)")
        
        print()
    
    print("=" * 70)
    print("🔍 ANALYSIS:")
    print("If citations are getting case names from the wrong citations,")
    print("this indicates a context isolation or association bug in the extraction logic.")
    print("The system needs to ensure each citation gets the case name from its")
    print("immediate context, not from other citations in the document.")

if __name__ == "__main__":
    test_citation_association()
