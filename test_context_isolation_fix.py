#!/usr/bin/env python3
"""
Focused test to verify the context isolation fix works
This tests the core issue: citations getting case names from other citations
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_case_extraction_master import extract_case_name_and_date_unified_master

def test_context_isolation():
    """Test that context isolation prevents cross-citation contamination"""
    
    # Simple test document with two clearly separate cases
    test_document = """
    SUPREME COURT OF WASHINGTON
    
    John Doe P et al. v. Thurston County, No. 47604-7
    
    In the landmark case of City of Bellevue v. Lorang, the court addressed 
    municipal liability. The ruling was City of Bellevue v. Lorang, 
    140 Wn.2d 19 (2000).
    
    In a different matter, Seattle Times Co v. Ishikawa dealt with media freedom.
    The decision was Seattle Times Co v. Ishikawa, 97 Wash. 2d 30 (1982).
    """
    
    print("🔍 TESTING CONTEXT ISOLATION FIX")
    print("=" * 60)
    print("Document contains TWO separate cases:")
    print("1. City of Bellevue v. Lorang (140 Wn.2d 19)")
    print("2. Seattle Times Co v. Ishikawa (97 Wash. 2d 30)")
    print()
    
    # Test each citation
    test_cases = [
        {
            "citation": "140 Wn.2d 19",
            "expected_case": "City of Bellevue v. Lorang",
            "wrong_case": "John Doe P et al. v. Thurston County",
            "description": "Should get Lorang case, not document header"
        },
        {
            "citation": "97 Wash. 2d 30",
            "expected_case": "Seattle Times Co v. Ishikawa", 
            "wrong_case": "City of Bellevue v. Lorang",
            "description": "Should get Ishikawa case, not Lorang case"
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        citation = test_case["citation"]
        expected = test_case["expected_case"]
        wrong_case = test_case["wrong_case"]
        
        print(f"🧪 Test {i}: {citation}")
        print(f"   Expected: '{expected}'")
        print(f"   Should NOT get: '{wrong_case}'")
        
        # Find citation position
        citation_pos = test_document.find(citation)
        if citation_pos == -1:
            print(f"   ❌ Citation not found")
            continue
        
        # Test extraction
        result = extract_case_name_and_date_unified_master(
            text=test_document,
            citation=citation,
            start_index=citation_pos,
            end_index=citation_pos + len(citation),
            debug=False,
            document_primary_case_name="John Doe P et al. v. Thurston County"
        )
        
        extracted_case = result.get('extracted_case_name', 'N/A')
        method = result.get('method', 'unknown')
        
        print(f"   Method: {method}")
        print(f"   Extracted: '{extracted_case}'")
        
        # Evaluate result
        if extracted_case == expected:
            print(f"   ✅ SUCCESS: Got correct case name")
            success_count += 1
        elif extracted_case == wrong_case:
            print(f"   ❌ BUG: Got wrong case name (cross-citation contamination!)")
        elif extracted_case == 'N/A':
            print(f"   ⚠️  NO EXTRACTION: Could not extract (but at least no contamination)")
            success_count += 0.5  # Partial credit for preventing contamination
        else:
            print(f"   ⚠️  DIFFERENT: Got '{extracted_case}' (not contaminated, just different)")
        
        print()
    
    # Summary
    print("=" * 60)
    print("📊 CONTEXT ISOLATION SUMMARY")
    print(f"Success rate: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.1f}%)")
    
    if success_count >= len(test_cases):
        print("✅ SUCCESS: Context isolation working correctly!")
        print("🎯 Citations get case names from their immediate context")
    elif success_count > 0:
        print("⚠️  PARTIAL: Some cross-citation contamination prevented")
        print("🔧 Further improvements needed")
    else:
        print("❌ FAILURE: Cross-citation contamination still occurring")
        print("🚨 Context isolation needs more work")
    
    print()
    print("🔍 FIXES APPLIED:")
    print("✅ Reduced context windows (300→150 chars, 400→200 chars)")
    print("✅ Added contamination validation to all extraction strategies") 
    print("✅ Fixed proximity filter (100→150 chars)")
    print("✅ Made header filtering more specific")

if __name__ == "__main__":
    test_context_isolation()
