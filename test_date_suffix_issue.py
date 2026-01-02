"""
Test if date suffixes in extracted names cause false mismatches.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from citation_extraction_endpoint import _names_equivalent, _name_similarity

test_cases = [
    # Date suffix cases
    ("Karpenski v. American General Life Companies, LLC, 2014", "Karpenski v. American General Life Companies, LLC", True),
    ("Erwin v. Cotter Health Centers, Inc., 2007", "Erwin v. Cotter Health Centers, Inc.", True),
    ("Richardson v. Pacific Power & Light Co., 1941", "Richardson v. Pacific Power & Light Co.", True),
    
    # The Bolick contamination case
    ("Bolick v. Am. Barmag Corp", "Department of Ecology v. Campbell & Gwinn, L.L.C.", False),
]

print("=" * 100)
print("TESTING DATE SUFFIX HANDLING")
print("=" * 100)
print()

for extracted, canonical, should_match in test_cases:
    result = _names_equivalent(extracted, canonical, verified=True, canonical_url="http://example.com")
    similarity = _name_similarity(extracted, canonical)
    
    status = "PASS" if (result == should_match) else "FAIL"
    print(f"{status} | Similarity: {similarity:.3f} | Equivalent: {result} | Expected: {should_match}")
    print(f"  Extracted: {extracted}")
    print(f"  Canonical: {canonical}")
    print()
