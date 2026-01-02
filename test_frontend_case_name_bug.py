#!/usr/bin/env python3
"""
Test the exact case name extraction bug shown in the frontend
"""

import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

def test_frontend_case_name_bug():
    """Test the specific case name mismatches from the frontend"""
    
    print("🔍 TESTING FRONTEND CASE NAME EXTRACTION BUG")
    print("=" * 60)
    print("Issue: Citations getting wrong case names from other parts of document")
    print()
    
    # Test document with multiple cases (similar to the PDF causing issues)
    test_document = """
    SUPREME COURT OF WASHINGTON
    
    Foss v. Nat'l Marine Fisheries Serv., 1998
    
    In the case concerning environmental regulations, the court considered 
    various precedents. One key citation is 161 F.3d 584 which addressed 
    marine conservation issues.
    
    In a separate matter, Berst v. Snohomish County, 2002-11-04 involved 
    county liability questions. The relevant citations are 114 Wn. App. 245 
    and 57 P.3d 273 from that case.
    
    Additionally, State v. Manussier, 1996-08-08 dealt with criminal procedure 
    matters. The citation 129 Wn.2d 652 was central to that decision.
    
    Finally, City of Bellevue v. Lorang addressed municipal liability in 
    both 2002 and 1996 decisions.
    """
    
    # Test each problematic citation
    test_cases = [
        {
            "citation": "161 F.3d 584",
            "expected_context": "environmental regulations",
            "wrong_case": "Foss v. Nat'l Marine Fisheries Serv.",
            "description": "Should get case name from environmental context, not document header"
        },
        {
            "citation": "114 Wn. App. 245", 
            "expected_context": "Berst v. Snohomish County",
            "wrong_case": "City of Bellevue v. Lorang",
            "description": "Should get Berst case name, not Lorang"
        },
        {
            "citation": "57 P.3d 273",
            "expected_context": "Berst v. Snohomish County", 
            "wrong_case": "City of Bellevue v. Lorang",
            "description": "Should get Berst case name, not Lorang"
        },
        {
            "citation": "129 Wn.2d 652",
            "expected_context": "State v. Manussier",
            "wrong_case": "City of Bellevue v. Lorang", 
            "description": "Should get Manussier case name, not Lorang"
        }
    ]
    
    print("📋 Testing case name extraction for each citation...")
    print()
    
    # Process the document
    processor = UnifiedCitationProcessorV2()
    
    # Manually set the document primary case name (like what should happen in real processing)
    processor.document_primary_case_name = "Foss v. Nat'l Marine Fisheries Serv."
    print(f"🔧 DEBUG: Set document_primary_case_name to: '{processor.document_primary_case_name}'")
    
    try:
        result = asyncio.run(processor.process_text(test_document))
        citations = result.get('citations', [])
        
        print(f"Found {len(citations)} citations in test document")
        print()
        
        # Check each test case
        for test_case in test_cases:
            citation_text = test_case["citation"]
            expected_context = test_case["expected_context"]
            wrong_case = test_case["wrong_case"]
            
            print(f"🔍 Testing: {citation_text}")
            print(f"   Expected context: {expected_context}")
            print(f"   Should NOT get: {wrong_case}")
            
            # Find the citation in results
            found_citation = None
            for cit in citations:
                if cit.citation == citation_text:
                    found_citation = cit
                    break
            
            if found_citation:
                extracted_case = getattr(found_citation, 'extracted_case_name', 'N/A')
                print(f"   Extracted case: '{extracted_case}'")
                
                # Check if it got the wrong case name
                if wrong_case.lower() in extracted_case.lower():
                    print(f"   ❌ BUG CONFIRMED: Got wrong case name (contains '{wrong_case}')")
                elif expected_context.lower() in extracted_case.lower():
                    print(f"   ✅ CORRECT: Got expected case name")
                elif extracted_case == 'N/A':
                    print(f"   ⚠️  NO EXTRACTION: Better than wrong case name")
                else:
                    print(f"   ⚠️  DIFFERENT: Got '{extracted_case}' (not contaminated)")
            else:
                print(f"   ❌ CITATION NOT FOUND in extraction results")
            
            print()
        
        # Show all extracted citations for analysis
        print("📊 ALL EXTRACTED CITATIONS:")
        for i, cit in enumerate(citations, 1):
            citation_text = getattr(cit, 'citation', 'N/A')
            case_name = getattr(cit, 'extracted_case_name', 'N/A')
            print(f"   {i}. {citation_text} → '{case_name}'")
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_frontend_case_name_bug()
