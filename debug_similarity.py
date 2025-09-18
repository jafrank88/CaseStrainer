#!/usr/bin/env python3
"""
Debug script to test the similarity function
"""

import re
from difflib import SequenceMatcher

def _are_case_names_too_similar(canonical_name: str, extracted_name: str) -> bool:
    """Check if canonical name is too similar to extracted name (indicating contamination)."""
    if not canonical_name or not extracted_name:
        return False
    
    # Normalize names for comparison
    canonical_clean = re.sub(r'[^\w\s]', '', canonical_name.lower()).strip()
    extracted_clean = re.sub(r'[^\w\s]', '', extracted_name.lower()).strip()
    
    print(f"Canonical clean: '{canonical_clean}'")
    print(f"Extracted clean: '{extracted_clean}'")
    
    # If they're exactly the same, they're too similar
    if canonical_clean == extracted_clean:
        print("Too similar: exactly the same")
        return True
    
    # Check if one contains the other (indicating contamination)
    if canonical_clean in extracted_clean or extracted_clean in canonical_clean:
        print("Too similar: one contains the other")
        return True
    
    # Check for high similarity (more than 80% similar)
    similarity = SequenceMatcher(None, canonical_clean, extracted_clean).ratio()
    print(f"Similarity ratio: {similarity:.2f}")
    if similarity > 0.8:
        print("Too similar: high similarity")
        return True
    
    print("Not too similar")
    return False

def test_similarity():
    """Test the similarity function with our contaminated examples"""
    test_cases = [
        ("that and by the . Lopez Demetrio v. Sakuma Bros. Farms", "that and by the . Lopez Demetrio v. Sakuma Bros. Farms"),
        ("is also an . Spokane County v. Dep't of Fish", "is also an . Spokane County v. Dep't of Fish"),
        ("Lopez Demetrio v. Sakuma Bros. Farms", "that and by the . Lopez Demetrio v. Sakuma Bros. Farms"),
        ("Spokane Cnty. v. Wash. Dep't of Fish & Wildlife", "is also an . Spokane County v. Dep't of Fish"),
    ]
    
    for i, (canonical, extracted) in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Canonical: '{canonical}'")
        print(f"Extracted: '{extracted}'")
        result = _are_case_names_too_similar(canonical, extracted)
        print(f"Result: {result}")

if __name__ == '__main__':
    test_similarity()









