#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.case_name_extraction_core import extract_case_name_and_date

def test_both_extractions():
    """Test case name extraction for both citations to see why they're getting the same result."""
    
    # Test text with both citations
    test_text = """
    Municipal corporations are not typically within the zone of interest of individual constitutional guarantees. 
    See, e.g., Lakehaven Water & Sewer Dist. v. City of Fed. Way, 195 Wn.2d 742, 773, 466 P.3d 213 (2020) 
    (sewer and water district lacked standing to challenge constitutional issues).
    
    The State has a duty to actively provide criminal defense services to those who cannot afford it. 
    See Davison v. State, 196 Wn.2d 285, 293, 466 P.3d 231 (2020) 
    ("The State plainly has a duty to provide indigent defense").
    """
    
    citations = ["195 Wn. 2d 742", "196 Wn. 2d 285"]
    
    print("=== TESTING BOTH CASE NAME EXTRACTIONS ===")
    print(f"Full text: {test_text}")
    print()
    
    for citation in citations:
        print(f"--- Testing citation: {citation} ---")
        
        try:
            result = extract_case_name_and_date(test_text, citation)
            
            print(f"Result: {result}")
            print(f"Case name: {result.get('case_name') if result else 'None'}")
            print(f"Year: {result.get('year') if result else 'None'}")
            print()
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            print()

if __name__ == "__main__":
    test_both_extractions() 