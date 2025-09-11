#!/usr/bin/env python3
"""
Debug the regex patterns to see why they're not matching correctly
"""

import re

def debug_regex_patterns():
    """Debug the regex patterns"""
    
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
    
    # Test the current patterns
    patterns = [
        # Pattern 1: Case name immediately before specific Washington citation (most specific)
        r'([A-Z][a-zA-Z\',\.\&]*(?:\s+[A-Z][a-zA-Z\',\.\&]*)*)\s+v\.\s+([A-Z][a-zA-Z\',\.\&]*(?:\s+[A-Z][a-zA-Z\',\.\&]*)*),\s*(\d+)\s+Wn\.(?:2d\s+\d+)?',
        # Pattern 2: Case name immediately before specific Pacific citation (most specific)
        r'([A-Z][a-zA-Z\',\.\&]*(?:\s+[A-Z][a-zA-Z\',\.\&]*)*)\s+v\.\s+([A-Z][a-zA-Z\',\.\&]*(?:\s+[A-Z][a-zA-Z\',\.\&]*)*),\s*(\d+)\s+P\.(?:3d\s+\d+)?',
    ]
    
    print("Testing regex patterns on the full text:")
    print(f"Text length: {len(test_text)}")
    print()
    
    for i, pattern in enumerate(patterns, 1):
        print(f"=== Pattern {i} ===")
        print(f"Pattern: {pattern}")
        
        matches = list(re.finditer(pattern, test_text, re.IGNORECASE))
        print(f"Found {len(matches)} matches:")
        
        for j, match in enumerate(matches):
            print(f"  {j+1}. '{match.group(0)}'")
            print(f"     Groups: {match.groups()}")
            print(f"     Position: {match.start()}-{match.end()}")
            
            # Show context around the match
            context_start = max(0, match.start() - 50)
            context_end = min(len(test_text), match.end() + 50)
            context = test_text[context_start:context_end]
            print(f"     Context: ...{context}...")
            print()
    
    # Test specific problematic text
    print("=== Testing specific problematic text ===")
    problematic_text = "Spokane Cnty. v. Wash. Dep't of Fish & Wildlife, 192 Wn.2d 453, 430 P.3d 655 (2018)"
    print(f"Text: {problematic_text}")
    
    for i, pattern in enumerate(patterns, 1):
        print(f"\nPattern {i}:")
        matches = list(re.finditer(pattern, problematic_text, re.IGNORECASE))
        print(f"Found {len(matches)} matches:")
        for match in matches:
            print(f"  '{match.group(0)}'")
            print(f"  Groups: {match.groups()}")

if __name__ == "__main__":
    debug_regex_patterns()

