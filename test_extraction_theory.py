#!/usr/bin/env python3
"""
Direct test of the extraction function to verify that it returns both extracted and canonical fields
when they differ (e.g., "Doe v. Wdae, 410 U.S. 113 (1901)" vs canonical "Roe v. Wade, 410 U.S. 113 (1973)")
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.case_name_extraction_core import extract_case_name_triple

def test_extraction_theory():
    """Test that extraction returns both extracted and canonical fields when they differ"""
    
    # Test data with intentionally wrong extracted name/date
    test_text = """
    The court considered the case of Doe v. Wdae, 410 U.S. 113 (1901) in determining the outcome.
    This case established important precedent for privacy rights.
    """
    
    test_citation = "Doe v. Wdae, 410 U.S. 113 (1901)"
    
    print("Testing extraction theory...")
    print(f"Input text: {test_text.strip()}")
    print(f"Test citation: {test_citation}")
    print()
    print("Expected behavior:")
    print("- Extracted name: 'Doe v. Wdae' (what's written in the document)")
    print("- Extracted date: '1901' (what's written in the document)")
    print("- Canonical name: Should be different (if verification finds the correct case)")
    print("- Canonical date: Should be different (if verification finds the correct case)")
    print()
    
    # Test 1: Direct extraction function
    print("=== Test 1: Direct extraction function ===")
    try:
        extraction_result = extract_case_name_triple(
            text=test_text,
            citation=test_citation,
            api_key=None,
            context_window=200
        )
        
        print("Extraction result:")
        print(f"  extracted_name: '{extraction_result.get('extracted_name', 'N/A')}'")
        print(f"  extracted_date: '{extraction_result.get('extracted_date', 'N/A')}'")
        print(f"  canonical_name: '{extraction_result.get('canonical_name', 'N/A')}'")
        print(f"  canonical_date: '{extraction_result.get('canonical_date', 'N/A')}'")
        print(f"  case_name: '{extraction_result.get('case_name', 'N/A')}'")
        print()
        
        # Check if extracted fields are present
        extracted_name = extraction_result.get('extracted_name', 'N/A')
        extracted_date = extraction_result.get('extracted_date', 'N/A')
        
        if extracted_name != 'N/A' and extracted_name:
            print(f"✅ Extracted case name is present: '{extracted_name}'")
        else:
            print(f"❌ Extracted case name is missing or 'N/A'")
            
        if extracted_date != 'N/A' and extracted_date:
            print(f"✅ Extracted date is present: '{extracted_date}'")
        else:
            print(f"❌ Extracted date is missing or 'N/A'")
            
        print()
        
    except Exception as e:
        print(f"❌ Error in extraction: {e}")
        print()
    
    print("=== Summary ===")
    print("The theory is that when a citation has a changed name/date (like 'Doe v. Wdae, 410 U.S. 113 (1901)'),")
    print("the system should show:")
    print("1. The extracted name/date from the document text")
    print("2. The canonical name/date from verification (if found)")
    print("3. Both should be displayed in the frontend regardless of verification status")
    print()
    print("This allows users to see both what was actually written in their document")
    print("and what the correct citation should be.")
    print()
    print("Expected canonical result would be: 'Roe v. Wade, 410 U.S. 113 (1973)'")

if __name__ == "__main__":
    test_extraction_theory() 