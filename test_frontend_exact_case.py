#!/usr/bin/env python3
"""
Test the exact case from the frontend to see where the contamination is happening
"""

import sys
import os
import asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

def test_frontend_exact_case():
    """Test the exact case that's showing contamination in the frontend"""
    
    print("🔍 TESTING EXACT FRONTEND CASE")
    print("=" * 50)
    print("Frontend shows:")
    print("- 161 F.3d 584 → 'N/A, 1998' (should be clean)")
    print("- 114 Wn. App. 245 → 'Berst v. Snohomish County, 2002-11-04' (correct)")
    print("- 57 P.3d 273 → 'Berst v. Snohomish County, 2002-11-04' (correct)")
    print("- 129 Wn.2d 652 → 'State v. Manussier, 1996-08-08' (correct)")
    print()
    
    # Create a document that matches the PDF structure causing issues
    test_document = """
    IN THE COURT OF APPEALS OF THE STATE OF WASHINGTON
    DIVISION II
    
    CITY OF BELLEVUE v. LORANG
    
    No. 59366-1-II
    
    Filed: November 4, 2002
    
    In this case involving municipal liability, the court considered 
    precedent from Berst v. Snohomish County, 114 Wn. App. 245 and 
    related cases like 57 P.3d 273. Additionally, the court referenced 
    State v. Manussier, 129 Wn.2d 652 in its analysis.
    
    The court also considered federal precedent including 161 F.3d 584 
    in its environmental law analysis.
    """
    
    print("Test document structure:")
    print("- Primary case: CITY OF BELLEVUE v. LORANG")
    print("- Contains multiple citations with different case names")
    print("- Should extract each citation's local context, not the primary case")
    print()
    
    # Process the document
    processor = UnifiedCitationProcessorV2()
    processor.document_primary_case_name = "CITY OF BELLEVUE v. LORANG"
    
    print(f"Set document_primary_case_name: '{processor.document_primary_case_name}'")
    print()
    
    try:
        result = asyncio.run(processor.process_text(test_document))
        citations = result.get('citations', [])
        
        print(f"Found {len(citations)} citations:")
        for i, cit in enumerate(citations, 1):
            citation_text = getattr(cit, 'citation', 'N/A')
            case_name = getattr(cit, 'extracted_case_name', 'N/A')
            extracted_date = getattr(cit, 'extracted_date', 'N/A')
            
            print(f"  {i}. {citation_text}")
            print(f"     → Case: '{case_name}'")
            print(f"     → Date: '{extracted_date}'")
            
            # Check for contamination
            if 'BELLEVUE' in case_name.upper() or 'LORANG' in case_name.upper():
                print(f"     ❌ CONTAMINATION - Got primary case name instead of citation context!")
            elif case_name == 'N/A':
                print(f"     ⚠️  NO EXTRACTION - Better than contamination")
            else:
                print(f"     ✅ CLEAN - Got local context case name")
            print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_frontend_exact_case()
