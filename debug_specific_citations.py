#!/usr/bin/env python3
"""
Debug the specific citations that are failing
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from unified_extraction_architecture import UnifiedExtractionArchitecture

def debug_specific_citations():
    """Debug the specific citations that are failing"""
    
    # The text that should contain the problematic citations
    test_text = """We review a trial court's findings of fact for substantial evidence, generally 
deferring to the trier of fact on questions of witness credibility, conflicting 
testimony, and persuasiveness of the evidence. In re Vulnerable Adult Petition 
for Knight, 178 Wn. App. 929, 936-37, 317 P.3d 1068 (2014). Evidence is 
substantial when sufficient to persuade a fair-minded person of the truth of the 
matter asserted. In re Marriage of Black, 188 Wn.2d 114, 127, 392 P.3d 1041 
(2017). "Competent evidence sufficient to support the trial court's decision to 
grant . . . a domestic violence protection order may contain hearsay or be wholly 
documentary." Blackmon v. Blackmon, 155 Wn. App. 715, 722, 230 P.3d 233 
(2010). We have long held that pro se litigants are bound by the same rules of procedure and substantive law as licensed attorneys. Holder v. City of Vancouver, 136 Wn. App. 104, 106, 147 P.3d 641 (2006); In re Marriage of Olson, 69 Wn. App. 621, 626, 850 P.2d 527 (1993) (noting courts are "under no obligation to grant special favors to . . . a pro se litigant."). Thus, a pro se appellant's failure to "identify any specific legal issues . . . cite any authority" or comply with procedural rules may still preclude appellate review. State v. Marintorres, 93 Wn. App. 442, 452, 969 P.2d 501 (1999). Lopez Demetrio v. Sakuma Bros. Farms, 183 Wn.2d 649, 355 P.3d 258 (2015). Spokane Cnty. v. Wash. Dep't of Fish & Wildlife, 192 Wn.2d 453, 430 P.3d 655 (2018)."""
    
    # Find the positions of the problematic citations
    citations_to_test = [
        ("183 Wn.2d 649", "Lopez Demetrio v. Sakuma Bros. Farms"),
        ("192 Wn.2d 453", "Spokane Cnty. v. Wash. Dep't of Fish & Wildlife"),
        ("355 P.3d 258", "Lopez Demetrio v. Sakuma Bros. Farms"),
        ("430 P.3d 655", "Spokane Cnty. v. Wash. Dep't of Fish & Wildlife"),
    ]
    
    extractor = UnifiedExtractionArchitecture()
    
    for citation_text, expected_case in citations_to_test:
        print(f"\n=== Testing: {citation_text} ===")
        print(f"Expected: {expected_case}")
        
        # Find the position of the citation in the text
        start_pos = test_text.find(citation_text)
        if start_pos == -1:
            print(f"❌ Citation not found in text")
            continue
            
        end_pos = start_pos + len(citation_text)
        print(f"Position: {start_pos}-{end_pos}")
        
        # Show context around the citation
        context_start = max(0, start_pos - 100)
        context_end = min(len(test_text), end_pos + 100)
        context = test_text[context_start:context_end]
        print(f"Context: ...{context}...")
        
        # Test extraction
        result = extractor.extract_case_name_and_year(
            text=test_text,
            citation=citation_text,
            start_index=start_pos,
            end_index=end_pos,
            debug=True
        )
        
        print(f"Extracted: {result.case_name}")
        print(f"Year: {result.year}")
        print(f"Confidence: {result.confidence}")
        print(f"Method: {result.method}")
        
        if result.case_name == expected_case:
            print("✅ CORRECT")
        else:
            print("❌ INCORRECT")

if __name__ == "__main__":
    debug_specific_citations()

