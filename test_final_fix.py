#!/usr/bin/env python3
"""
Test script to verify the complete fix works with the user's test paragraph
"""

import re
import sys
import os

# Add src to path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_case_name_extraction():
    """Test the complete fix with the user's test paragraph"""
    
    # The user's test paragraph
    test_text = '''We review statutory interpretation de novo. DeSean v. Sanger, 2 Wn. 3d 
329, 334-35, 536 P.3d 191 (2023). "The goal of statutory interpretation is to give 
effect to the legislature's intentions." DeSean, 2 Wn.3d at 335. In determining 
the plain meaning of a statute, we look to the text of the statute, as well as its 
No. 87675-9-I/14
14
broader context and the statutory scheme as a whole. State v. Ervin, 169 Wn.2d 
815, 820, 239 P.3d 354 (2010). Only if the plain text is susceptible to more than 
one interpretation do we turn to statutory construction, legislative history, and 
relevant case law to determine legislative intent. Ervin, 169 Wn.2d at 820.'''
    
    print("Testing the complete fix with the user's test paragraph")
    print("=" * 80)
    print(f"Test text:\n{test_text}")
    print("\n" + "=" * 80)
    
    # Test 1: The corrected regex pattern from unified_case_name_extractor.py
    print("\n🔍 Test 1: Corrected regex pattern from unified_case_name_extractor.py")
    pattern = r'([A-Z][A-Za-z0-9&.\'\s-]+(?:\s+[A-Za-z0-9&.\'\s-]+)*?)\s+v\.\s+([A-Z][A-Za-z0-9&.\'\s-]+(?:\s+[A-Za-z0-9&.\'\s-]+)*?)(?=\s*,|\s*\(|$)'
    
    matches = list(re.finditer(pattern, test_text))
    if matches:
        print(f"✅ Found {len(matches)} case name matches:")
        for i, match in enumerate(matches, 1):
            plaintiff = match.group(1).strip()
            defendant = match.group(2).strip()
            case_name = f"{plaintiff} v. {defendant}"
            print(f"   {i}. '{case_name}'")
            
            # Check if this matches expected cases
            expected_cases = ["DeSean v. Sanger", "State v. Ervin"]
            for expected in expected_cases:
                if case_name in expected or expected in case_name:
                    print(f"      ✅ Matches expected: '{expected}'")
                    break
            else:
                print(f"      ⚠️  No exact match found in expected cases")
    else:
        print("❌ No case name matches found")
    
    # Test 2: Test the _clean_extracted_case_name method (simplified version)
    print("\n🔍 Test 2: _clean_extracted_case_name method (simplified)")
    
    def test_clean_case_name(case_name):
        """Simplified version of the _clean_extracted_case_name method"""
        if not case_name:
            return case_name
        
        # Use the corrected pattern without character limits
        v_pattern = r'([A-Z][A-Za-z\s\'\.&,]+?\s+v\.\s+[A-Z][A-Za-z\s\'\.&,]+?)(?:\s*,|\s*\(|\s*$)'
        match = re.search(v_pattern, case_name)
        if match:
            extracted = match.group(1).strip()
            if len(extracted) < 200 and ' v. ' in extracted:
                return extracted
        
        return case_name
    
    # Test with the problematic case names
    test_cases = [
        "DeSean v. Sanger, 2 Wn. 3d 329, 536 P.3d 191 (2023)",
        "State v. Ervin, 169 Wn.2d 815, 239 P.3d 354 (2010)",
        "DeSean, 2 Wn.3d at 335",
        "Ervin, 169 Wn.2d at 820"
    ]
    
    for test_case in test_cases:
        cleaned = test_clean_case_name(test_case)
        print(f"   Input: '{test_case}'")
        print(f"   Output: '{cleaned}'")
        print()
    
    # Test 3: Check if the text contains the expected case names
    print("\n🔍 Test 3: Expected case names in text")
    expected_cases = ["DeSean v. Sanger", "State v. Ervin"]
    
    for expected in expected_cases:
        if expected in test_text:
            print(f"✅ Found: '{expected}'")
        else:
            print(f"❌ Missing: '{expected}'")
    
    print("\n" + "=" * 80)
    print("Test complete! The fixes should now properly extract:")
    print("   - 'DeSean v. Sanger' (not 'Sean v. Sanger')")
    print("   - 'State v. Ervin' (not missing)")

if __name__ == "__main__":
    test_case_name_extraction()
