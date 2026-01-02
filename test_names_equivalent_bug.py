"""
Test the actual _names_equivalent function to find the bug.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import the actual function
from citation_extraction_endpoint import _names_equivalent, _name_similarity

test_cases = [
    {
        "extracted": "Karpenski v. American General Life Companies, LLC",
        "canonical": "Karpenski v. American General Life Companies, LLC",
        "verified": True,
        "canonical_url": "https://www.courtlistener.com/opinion/2730965/karpenski-v-american-general-life-companies-llc/",
        "expected": True,
        "description": "Identical names - should be equivalent"
    },
    {
        "extracted": "State v. Johnson",
        "canonical": "BMW of North America, Inc. v. Gore",
        "verified": True,
        "canonical_url": "https://www.courtlistener.com/opinion/...",
        "expected": False,
        "description": "Completely different - should NOT be equivalent"
    },
    {
        "extracted": "Department of Ecology v. Campbell & Gwinn, L.L.C.",
        "canonical": "State, Dept. of Ecology v. Campbell & Gwinn",
        "verified": True,
        "canonical_url": "https://www.courtlistener.com/opinion/...",
        "expected": True,
        "description": "Department vs Dept. - should be equivalent"
    },
]

print("=" * 100)
print("TESTING _names_equivalent FUNCTION")
print("=" * 100)
print()

for i, case in enumerate(test_cases, 1):
    extracted = case["extracted"]
    canonical = case["canonical"]
    verified = case["verified"]
    canonical_url = case["canonical_url"]
    expected = case["expected"]
    description = case["description"]
    
    # Test the function
    result = _names_equivalent(extracted, canonical, verified=verified, canonical_url=canonical_url)
    similarity = _name_similarity(extracted, canonical)
    
    print(f"Case {i}: {description}")
    print(f"  Extracted: {extracted}")
    print(f"  Canonical: {canonical}")
    print(f"  Verified: {verified}")
    print(f"  Similarity: {similarity:.3f}")
    print(f"  _names_equivalent result: {result}")
    print(f"  Expected: {expected}")
    
    if result == expected:
        print(f"  ✅ CORRECT")
    else:
        print(f"  ❌ BUG FOUND - Expected {expected} but got {result}")
    print()

print()
print("=" * 100)
print("TESTING WITH EXACT DUPLICATES")
print("=" * 100)
print()

# Test with the exact same string
test_string = "Karpenski v. American General Life Companies, LLC"
result = _names_equivalent(test_string, test_string, verified=True, canonical_url="http://example.com")
print(f"Testing identical strings:")
print(f"  String: {test_string}")
print(f"  _names_equivalent(same, same): {result}")

if result:
    print(f"  ✅ Returns True for identical strings")
else:
    print(f"  ❌ BUG: Returns False for identical strings!")
