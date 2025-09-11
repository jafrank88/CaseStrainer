#!/usr/bin/env python3
"""
Test script to verify that the volume-based case name extraction method 
is now integrated into the unified extractor and being called.
"""

import sys
import os
import logging
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_volume_integration():
    """Test that the volume-based method is now integrated and working."""
    
    try:
        from unified_case_name_extractor import extract_case_name_and_date_unified
        
        # Test text with the problematic cases
        test_text = """We review a trial court's findings of fact for substantial evidence, generally 
deferring to the trier of fact on questions of witness credibility, conflicting 
testimony, and persuasiveness of the evidence. In re Vulnerable Adult Petition 
for Knight, 178 Wn. App. 929, 936-37, 317 P.3d 1068 (2014). Evidence is 
substantial when sufficient to persuade a fair-minded person of the truth of the 
matter asserted. In re Marriage of Black, 188 Wn.2d 114, 127, 392 P.3d 1041 
(2017). "Competent evidence sufficient to support the trial court's decision to 
grant . . . a domestic violence protection order may contain hearsay or be wholly 
documentary." Blackmon v. Blackmon, 155 Wn. App. 715, 722, 230 P.3d 233 
(2010)."""
        
        print("=== Volume Method Integration Test ===")
        print(f"Test text: {test_text[:100]}...")
        print()
        
        # Test the Knight citation
        knight_citation = "178 Wn. App. 929"
        print(f"Testing Knight citation: '{knight_citation}'")
        print(f"Citation position in text: {test_text.find(knight_citation)}")
        print(f"Text around citation: '{test_text[test_text.find(knight_citation)-50:test_text.find(knight_citation)+50]}'")
        print("Calling extract_case_name_and_date_unified...")
        result = extract_case_name_and_date_unified(test_text, knight_citation)
        print(f"Result: {result}")
        print()
        
        # Test the Black citation
        black_citation = "188 Wn.2d 114"
        print(f"Testing Black citation: '{black_citation}'")
        print(f"Citation position in text: {test_text.find(black_citation)}")
        print(f"Text around citation: '{test_text[test_text.find(black_citation)-50:test_text.find(black_citation)+50]}'")
        print("Calling extract_case_name_and_date_unified...")
        result = extract_case_name_and_date_unified(test_text, black_citation)
        print(f"Result: {result}")
        print()
        
        # Test the Blackmon citation
        blackmon_citation = "155 Wn. App. 715"
        print(f"Testing Blackmon citation: '{blackmon_citation}'")
        print(f"Citation position in text: {test_text.find(blackmon_citation)}")
        print(f"Text around citation: '{test_text[test_text.find(blackmon_citation)-50:test_text.find(blackmon_citation)+50]}'")
        print("Calling extract_case_name_and_date_unified...")
        result = extract_case_name_and_date_unified(test_text, blackmon_citation)
        print(f"Result: {result}")
        print()
        
        # Check if volume-based method was used
        if any('volume_based' in str(result.get('method', '')) for result in [result]):
            print("✅ SUCCESS: Volume-based method is being used!")
        else:
            print("❌ ISSUE: Volume-based method is not being used.")
            
    except ImportError as e:
        print(f"Import error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_volume_integration()
