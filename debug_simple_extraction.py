#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.case_name_extraction_core import extract_case_name_and_date

def test_simple_extraction():
    """Test case name extraction with minimal context to isolate the issue."""
    
    # Test with minimal context around Davison citation
    test_text = "See Davison v. State, 196 Wn.2d 285, 293, 466 P.3d 231 (2020)"
    citation = "196 Wn. 2d 285"
    
    print("=== SIMPLE EXTRACTION TEST ===")
    print(f"Text: {test_text}")
    print(f"Citation: {citation}")
    print()
    
    try:
        result = extract_case_name_and_date(test_text, citation)
        print(f"Result: {result}")
        print(f"Case name: {result.get('case_name') if result else 'None'}")
        print(f"Year: {result.get('year') if result else 'None'}")
        
        if result and result.get('case_name'):
            case_name = result.get('case_name')
            if "Davison" in case_name:
                print("✅ CORRECT: Davison found in extracted case name")
            else:
                print("❌ INCORRECT: Davison not found in extracted case name")
        else:
            print("❌ No case name extracted")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_extraction() 