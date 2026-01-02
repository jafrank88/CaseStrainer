#!/usr/bin/env python3
"""
Debug script to test the contamination filtering logic
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_case_extraction_master import UnifiedCaseExtractionMaster

def test_contamination_filter():
    """Test the contamination filter with the problematic case name"""
    
    # The document's primary case name from the response.json
    document_primary_case = "R.PENDLETON SUPREME COURT CLERK John Doe P et al. v. Thurston County et al."
    
    # The extracted case name that's being applied to ALL citations (should be rejected)
    extracted_case_name = "R.PENDLETON SUPREME COURT CLERK John Doe P et al. v. Thurston County et al."
    
    print("🧪 TESTING CONTAMINATION FILTER")
    print("=" * 60)
    print(f"Document Primary Case: '{document_primary_case}'")
    print(f"Extracted Case Name:   '{extracted_case_name}'")
    print()
    
    # Create extractor with document primary case name
    extractor = UnifiedCaseExtractionMaster(document_primary_case_name=document_primary_case)
    
    # Test the contamination filter
    is_contaminated = extractor._is_document_case_contamination(extracted_case_name, debug=True)
    
    print(f"\n🎯 CONTAMINATION RESULT: {is_contaminated}")
    
    if is_contaminated:
        print("✅ CORRECT: Filter properly detected contamination and should reject this case name")
    else:
        print("❌ BUG: Filter FAILED to detect contamination - this is why all citations have the wrong case name!")
        print("🔧 The contamination filter needs to be fixed to properly reject matching case names")
    
    print("\n" + "=" * 60)
    print("EXPECTED BEHAVIOR:")
    print("- When extracted_case_name == document_primary_case_name, it should be REJECTED")
    print("- This prevents the document's own case name from being applied to all citations")
    print("- Each citation should get its own case name from its immediate context")

if __name__ == "__main__":
    test_contamination_filter()
