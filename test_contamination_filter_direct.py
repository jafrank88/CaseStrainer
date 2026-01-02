#!/usr/bin/env python3
"""
Test the contamination filter function directly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_contamination_filter_direct():
    """Test the contamination filter function directly"""
    
    print("🔍 TESTING CONTAMINATION FILTER FUNCTION DIRECTLY")
    print("=" * 60)
    
    from src.utils.unified_case_name_extractor import _is_document_case_contamination
    
    # Test cases
    test_cases = [
        # (extracted_name, document_primary_case_name, expected_result, description)
        ("City of Bellevue v. Lorang", "Cape George Land Company v. Jefferson County", False, "Different cases - should be allowed"),
        ("CITY OF BELLEVUE v. LORANG", "Cape George Land Company v. Jefferson County", False, "Different cases - should be allowed"),
        ("Cape George Land Company v. Jefferson County", "Cape George Land Company v. Jefferson County", True, "Same case - should be rejected"),
        ("CAPE GEORGE LAND COMPANY v. JEFFERSON COUNTY", "Cape George Land Company v. Jefferson County", True, "Same case normalized - should be rejected"),
        ("Berst v. Snohomish County", "Cape George Land Company v. Jefferson County", False, "Different cases - should be allowed"),
        ("Rozner v. Bellevue", "Cape George Land Company v. Jefferson County", False, "Different cases - should be allowed"),
        ("Jefferson County v. Cape George Land Company", "Cape George Land Company v. Jefferson County", True, "Reversed same case - should be rejected"),
    ]
    
    print("Testing contamination filter logic:")
    print("-" * 40)
    
    all_passed = True
    for extracted_name, document_primary_case, expected, description in test_cases:
        try:
            result = _is_document_case_contamination(extracted_name, document_primary_case)
            status = "✅ PASS" if result == expected else "❌ FAIL"
            if result != expected:
                all_passed = False
            
            action = "REJECTED" if result else "ALLOWED"
            expected_action = "REJECTED" if expected else "ALLOWED"
            
            print(f"{status} {description}")
            print(f"     Extracted: '{extracted_name}'")
            print(f"     Document:  '{document_primary_case}'")
            print(f"     Result:    {action} (expected: {expected_action})")
            print()
            
        except Exception as e:
            print(f"❌ ERROR testing '{extracted_name}' vs '{document_primary_case}': {e}")
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("🎉 ALL CONTAMINATION FILTER TESTS PASSED!")
        print("The contamination filter logic is working correctly.")
    else:
        print("❌ CONTAMINATION FILTER TESTS FAILED!")
        print("The contamination filter logic has bugs.")
    
    return all_passed

if __name__ == "__main__":
    test_contamination_filter_direct()
