#!/usr/bin/env python3
"""
Direct Case Name and Date Extraction Test
Tests the unified case name and date extraction functionality.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_case_name_date_extraction():
    """Test case name and date extraction with real legal text."""
    
    try:
        # Import the unified case name extractor
        from unified_case_name_extractor import (
            extract_case_name_and_date_unified,
            extract_case_name_only_unified,
            extract_year_only_unified
        )
        
        # Test text with real legal citations
        test_text = """In Presidential Ests Apt. Assocs. v. Barrett, 129 Wn.2d 320, 325-26, 917 P.2d 100 (1996), the Washington Supreme Court held that a landlord's duty to provide a reasonably safe premises extends to protecting tenants from foreseeable criminal acts by third parties. The court in United States v. American Trucking Assns., Inc., 310 U. S. 534, 544 (1940), established the principle that administrative agencies must clearly articulate their statutory authority."""
        
        print("🔍 Testing Case Name and Date Extraction")
        print("=" * 60)
        print(f"Test Text: {test_text[:100]}...")
        print()
        
        # Test cases with known citation positions
        test_cases = [
            {
                "name": "Washington State Citation",
                "citation": "129 Wn.2d 320",
                "start": 46,
                "end": 59,
                "expected_case": "Presidential Ests Apt. Assocs. v. Barrett",
                "expected_year": "1996"
            },
            {
                "name": "U.S. Supreme Court Citation", 
                "citation": "310 U. S. 534",
                "start": 326,
                "end": 339,
                "expected_case": "United States v. American Trucking Assns., Inc.",
                "expected_year": "1940"
            }
        ]
        
        success_count = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"📋 Test {i}: {test_case['name']}")
            print(f"Citation: '{test_case['citation']}'")
            print(f"Position: {test_case['start']}-{test_case['end']}")
            print()
            
            # Test unified extraction
            result = extract_case_name_and_date_unified(
                text=test_text,
                citation=test_case['citation'],
                citation_start=test_case['start'],
                citation_end=test_case['end']
            )
            
            print("📝 Extraction Results:")
            print(f"  Case Name: '{result.get('case_name', 'N/A')}'")
            print(f"  Date/Year: '{result.get('year', 'N/A')}'")
            print(f"  Confidence: {result.get('confidence', 0.0):.2f}")
            print(f"  Method: {result.get('method', 'N/A')}")
            
            # Check results
            extracted_case = result.get('case_name', '')
            extracted_year = result.get('year', '')
            
            case_match = test_case['expected_case'].lower() in extracted_case.lower() if extracted_case else False
            year_match = test_case['expected_year'] in extracted_year if extracted_year else False
            
            print()
            print("✅ Validation:")
            print(f"  Expected Case: '{test_case['expected_case']}'")
            print(f"  Case Match: {'✅ YES' if case_match else '❌ NO'}")
            print(f"  Expected Year: '{test_case['expected_year']}'")
            print(f"  Year Match: {'✅ YES' if year_match else '❌ NO'}")
            
            if case_match and year_match:
                success_count += 1
                print(f"  🎯 Test {i}: PASSED")
            else:
                print(f"  ❌ Test {i}: FAILED")
            
            print("-" * 60)
        
        # Test individual extraction functions
        print("\n🔧 Testing Individual Extraction Functions:")
        
        # Test case name only
        case_only = extract_case_name_only_unified(
            text=test_text,
            citation="129 Wn.2d 320",
            citation_start=46,
            citation_end=59
        )
        print(f"Case Name Only: '{case_only}'")
        
        # Test year only
        year_only = extract_year_only_unified(
            text=test_text,
            citation="129 Wn.2d 320", 
            citation_start=46,
            citation_end=59
        )
        print(f"Year Only: '{year_only}'")
        
        # Overall results
        print(f"\n🎯 Overall Results: {success_count}/{len(test_cases)} tests passed")
        
        return success_count == len(test_cases)
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_case_name_date_extraction()
    if success:
        print("\n✅ Case name and date extraction test PASSED")
    else:
        print("\n❌ Case name and date extraction test FAILED")
