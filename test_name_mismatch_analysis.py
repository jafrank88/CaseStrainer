"""
Test to analyze name mismatch issues from 1031351.pdf

Issues identified:
1. Too strict matching - minor variations flagged as mismatches
2. Cross-contamination - wrong case names extracted
3. Citation prefix contamination - "prod.liab.rep" prefix picked up
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from difflib import SequenceMatcher

def calculate_name_similarity(name1: str, name2: str) -> float:
    """Calculate similarity between two case names (from unified_citation_processor_v2.py)."""
    if not name1 or not name2:
        return 0.0
    
    similarity = SequenceMatcher(None, name1, name2).ratio()
    
    words1 = set(name1.split())
    words2 = set(name2.split())
    
    if words1 and words2:
        word_overlap = len(words1 & words2) / max(len(words1), len(words2))
        final_similarity = (similarity + word_overlap) / 2
    else:
        final_similarity = similarity
    
    return final_similarity

def test_name_matching_cases():
    """Test specific cases that are incorrectly flagged."""
    
    test_cases = [
        # Case 1: Minor variation - should match
        {
            "extracted": "Karpenski v. American General Life Companies, LLC",
            "canonical": "Karpenski v. American General Life Companies, LLC",
            "should_match": True,
            "description": "Identical names - should match"
        },
        # Case 2: With date in extracted
        {
            "extracted": "Karpenski v. American General Life Companies, LLC, 2014",
            "canonical": "Karpenski v. American General Life Companies, LLC",
            "should_match": True,
            "description": "Extracted has year suffix - should match"
        },
        # Case 3: Cross-contamination - should NOT match
        {
            "extracted": "State v. Johnson",
            "canonical": "BMW of North America, Inc. v. Gore",
            "should_match": False,
            "description": "Completely different cases - extraction error"
        },
        # Case 4: Citation prefix contamination
        {
            "extracted": "prod.liab.rep. (Cch) P 13,403 Juan Jaurequi v. John Deere Company and Deere & Company",
            "canonical": "prod.liab.rep. (Cch) P 13,403 Juan Jaurequi v. John Deere Company and Deere & Company",
            "should_match": True,
            "description": "Has citation prefix - needs cleaning"
        },
        # Case 5: Minor abbreviation differences
        {
            "extracted": "Erwin v. Cotter Health Centers, Inc.",
            "canonical": "Erwin v. Cotter Health Centers",
            "should_match": True,
            "description": "Minor Inc. suffix difference"
        },
        # Case 6: Similar but not same
        {
            "extracted": "Department of Ecology v. Campbell & Gwinn, L.L.C.",
            "canonical": "State, Dept. of Ecology v. Campbell & Gwinn",
            "should_match": True,
            "description": "Department vs Dept. abbreviation"
        },
    ]
    
    print("=" * 80)
    print("NAME MATCHING ANALYSIS")
    print("=" * 80)
    print()
    
    for i, case in enumerate(test_cases, 1):
        extracted = case["extracted"]
        canonical = case["canonical"]
        should_match = case["should_match"]
        description = case["description"]
        
        similarity = calculate_name_similarity(extracted, canonical)
        
        # Current thresholds:
        # - General: 0.6
        # - Verified: 0.5 (in _names_equivalent)
        
        matches_general = similarity >= 0.6
        matches_verified = similarity >= 0.5
        
        print(f"Case {i}: {description}")
        print(f"  Extracted: {extracted[:80]}...")
        print(f"  Canonical: {canonical[:80]}...")
        print(f"  Similarity: {similarity:.3f}")
        print(f"  Matches (0.6 threshold): {matches_general}")
        print(f"  Matches (0.5 threshold): {matches_verified}")
        print(f"  Should match: {should_match}")
        
        if should_match and not matches_verified:
            print(f"  ❌ FALSE NEGATIVE - Should match but doesn't")
        elif not should_match and matches_general:
            print(f"  ⚠️  FALSE POSITIVE - Shouldn't match but does")
        else:
            print(f"  ✅ CORRECT")
        print()

def test_contamination_patterns():
    """Test if contamination patterns catch citation prefixes."""
    import re
    
    # Current contamination patterns from unified_case_extraction_master.py
    contamination_prefixes = [
        # Signal words
        r'^(?:See|see|See also|see also|also|Also|Citing|citing|Compare|compare|But see|but see|Cf\.|cf\.|quoting|Quoting|accord|Accord|We review|we review|The court|the court|Under|under)\s+',
        r'^(?:The case of|As stated in|Following)\s+',
        # Additional patterns would go here...
    ]
    
    test_names = [
        "prod.liab.rep. (Cch) P 13,403 Juan Jaurequi v. John Deere Company and Deere & Company",
        "See Johnson v. Smith",
        "Compare United States v. Nixon",
        "Karpenski v. American General Life Companies, LLC",
    ]
    
    print("=" * 80)
    print("CONTAMINATION PATTERN ANALYSIS")
    print("=" * 80)
    print()
    
    for name in test_names:
        cleaned = name.strip()
        original = cleaned
        
        for prefix in contamination_prefixes:
            cleaned = re.sub(prefix, '', cleaned, flags=re.IGNORECASE).strip()
        
        if original != cleaned:
            print(f"Original:  {original}")
            print(f"Cleaned:   {cleaned}")
            print(f"✅ Pattern caught contamination")
        else:
            print(f"Name:      {name}")
            print(f"⚠️  No contamination pattern matched")
        print()

if __name__ == "__main__":
    test_name_matching_cases()
    test_contamination_patterns()
