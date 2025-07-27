#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.case_name_extraction_core import extract_case_name_and_date

def test_davison_extraction():
    """Test case name extraction for the Davison citation specifically."""
    
    # Test text with the Davison citation
    test_text = """
    The State has a duty to actively provide criminal defense services to those who cannot afford it. 
    See Davison v. State, 196 Wn.2d 285, 293, 466 P.3d 231 (2020) 
    ("The State plainly has a duty to provide indigent defense").
    """
    
    citation = "196 Wn. 2d 285"
    
    print("=== TESTING DAVISON CASE NAME EXTRACTION ===")
    print(f"Citation: {citation}")
    print(f"Context length: {len(test_text)}")
    print(f"Context: {repr(test_text)}")
    print()
    
    try:
        # Extract case name and date
        print("Calling extract_case_name_and_date...")
        result = extract_case_name_and_date(test_text, citation)
        print("Function call completed successfully")
        
        print("=== EXTRACTION RESULT ===")
        print(f"Result type: {type(result)}")
        print(f"Result: {result}")
        print(f"Case name: {result.get('case_name') if result else 'None'}")
        print(f"Year: {result.get('year') if result else 'None'}")
        print(f"Debug info: {result.get('debug') if result else 'None'}")
        print()
        
        # Check if it's correct
        if result:
            expected_case_name = "Davison v. State"
            extracted_case_name = result.get('case_name', '')
            
            if expected_case_name in extracted_case_name:
                print("✅ CORRECT: Davison v. State found in extracted case name")
            else:
                print("❌ INCORRECT: Davison v. State not found in extracted case name")
                print(f"   Expected: {expected_case_name}")
                print(f"   Got: {extracted_case_name}")
        else:
            print("❌ No result returned from extraction function")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_davison_extraction() 