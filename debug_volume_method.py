#!/usr/bin/env python3
"""
Debug script to test the volume-based method directly.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def debug_volume_method():
    """Debug the volume-based method directly."""
    
    try:
        from unified_case_name_extractor import UnifiedCaseNameExtractor
        
        # Create the extractor
        extractor = UnifiedCaseNameExtractor()
        
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
        
        print("=== Debug Volume Method ===")
        print(f"Test text: {test_text[:100]}...")
        print()
        
        # Test the Knight citation
        knight_citation = "178 Wn. App. 929"
        print(f"Testing Knight citation: '{knight_citation}'")
        print(f"Citation position in text: {test_text.find(knight_citation)}")
        
        # Show the exact text around the citation
        pos = test_text.find(knight_citation)
        print(f"Text before citation (200 chars): '{test_text[max(0, pos-200):pos]}'")
        print(f"Text after citation (50 chars): '{test_text[pos+len(knight_citation):pos+len(knight_citation)+50]}'")
        
        # Test the volume method directly
        result = extractor.extract_case_name_from_citation_volume(test_text, knight_citation)
        print(f"Volume method result: '{result}'")
        print()
        
        # Test the Black citation
        black_citation = "188 Wn.2d 114"
        print(f"Testing Black citation: '{black_citation}'")
        print(f"Citation position in text: {test_text.find(black_citation)}")
        
        # Show the exact text around the citation
        pos = test_text.find(black_citation)
        print(f"Text before citation (200 chars): '{test_text[max(0, pos-200):pos]}'")
        print(f"Text after citation (50 chars): '{test_text[pos+len(black_citation):pos+len(black_citation)+50]}'")
        
        # Test the volume method directly
        result = extractor.extract_case_name_from_citation_volume(test_text, black_citation)
        print(f"Volume method result: '{result}'")
        print()
        
        # Test the Blackmon citation
        blackmon_citation = "155 Wn. App. 715"
        print(f"Testing Blackmon citation: '{blackmon_citation}'")
        print(f"Citation position in text: {test_text.find(blackmon_citation)}")
        
        # Show the exact text around the citation
        pos = test_text.find(blackmon_citation)
        print(f"Text before citation (200 chars): '{test_text[max(0, pos-200):pos]}'")
        print(f"Text after citation (50 chars): '{test_text[pos+len(blackmon_citation):pos+len(blackmon_citation)+50]}'")
        
        # Test the volume method directly
        result = extractor.extract_case_name_from_citation_volume(test_text, blackmon_citation)
        print(f"Volume method result: '{result}'")
        print()
        
    except ImportError as e:
        print(f"Import error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_volume_method()
