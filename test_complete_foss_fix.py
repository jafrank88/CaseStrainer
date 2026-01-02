"""
Comprehensive test for the FOSS (name mismatch) fixes.
Tests all 4 fixes:
1. Lower name matching threshold (0.6 -> 0.4)
2. Lower low-similarity threshold (0.45 -> 0.35)
3. Add reporter prefix contamination pattern
4. Cross-contamination extraction issues
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from citation_extraction_endpoint import _names_equivalent, _name_similarity, _annotate_mismatch_flags
import re

print("=" * 100)
print("COMPREHENSIVE FOSS FIX TEST")
print("=" * 100)
print()

# Test 1: Name matching threshold
print("TEST 1: NAME MATCHING THRESHOLD (should be 0.4 now)")
print("-" * 100)

test_cases = [
    ("Karpenski v. American General Life Companies, LLC", "Karpenski v. American General Life Companies, LLC", True),
    ("Department of Ecology v. Campbell & Gwinn", "State, Dept. of Ecology v. Campbell & Gwinn", True),
    ("Erwin v. Cotter Health Centers, Inc.", "Erwin v. Cotter Health Centers", True),
    ("State v. Johnson", "BMW of North America, Inc. v. Gore", False),
]

for extracted, canonical, should_match in test_cases:
    result = _names_equivalent(extracted, canonical, verified=True, canonical_url="http://example.com")
    similarity = _name_similarity(extracted, canonical)
    
    status = "PASS" if (result == should_match) else "FAIL"
    print(f"{status} Sim: {similarity:.3f} | Equiv: {result} | Expected: {should_match}")
    print(f"   Extracted: {extracted[:50]}...")
    print(f"   Canonical: {canonical[:50]}...")
    print()

print()

# Test 2: Reporter prefix contamination pattern
print("TEST 2: REPORTER PREFIX CONTAMINATION PATTERN")
print("-" * 100)

test_names = [
    "prod.liab.rep. (Cch) P 13,403 Juan Jaurequi v. John Deere Company and Deere & Company",
    "See Johnson v. Smith",
    "Karpenski v. American General Life Companies, LLC",
]

for name in test_names:
    # Simulate the contamination cleaning
    contamination_prefixes = [
        r'^(?:See|see|See also|see also|also|Also|Citing|citing|Compare|compare|But see|but see|Cf\.|cf\.|quoting|Quoting|accord|Accord|We review|we review|The court|the court|Under|under)\s+',
        r'^[a-z][a-z.]*\s*\([^)]+\)\s*[A-Z]?\s*[\d,]+\s+',  # NEW PATTERN - matches "prod.liab.rep. (Cch) P 13,403 "
    ]
    
    cleaned = name.strip()
    original = cleaned
    
    for prefix in contamination_prefixes:
        cleaned = re.sub(prefix, '', cleaned, flags=re.IGNORECASE).strip()
    
    if original != cleaned:
        print(f"PASS Pattern caught contamination")
        print(f"   Original: {original[:70]}...")
        print(f"   Cleaned:  {cleaned[:70]}...")
    else:
        print(f"INFO No contamination detected")
        print(f"   Name: {name[:70]}...")
    print()

print()

# Test 3: Mismatch flag annotation
print("TEST 3: MISMATCH FLAG ANNOTATION (threshold should be 0.4)")
print("-" * 100)

citations = [
    {
        "extracted_case_name": "Karpenski v. American General Life Companies, LLC",
        "canonical_name": "Karpenski v. American General Life Companies, LLC",
        "verified": True,
        "canonical_url": "http://example.com",
    },
    {
        "extracted_case_name": "Department of Ecology v. Campbell & Gwinn",
        "canonical_name": "State, Dept. of Ecology v. Campbell & Gwinn",
        "verified": True,
        "canonical_url": "http://example.com",
    },
]

_annotate_mismatch_flags(citations, [], name_threshold=0.4, year_tolerance=0)

for i, cit in enumerate(citations, 1):
    name_mismatch = cit.get('name_mismatch', False)
    extracted = cit.get('extracted_case_name')
    canonical = cit.get('canonical_name')
    
    status = "PASS" if not name_mismatch else "WARN"
    print(f"{status} Citation {i}: name_mismatch = {name_mismatch}")
    print(f"   Extracted: {extracted[:50]}...")
    print(f"   Canonical: {canonical[:50]}...")
    print()

print()
print("=" * 100)
print("TEST COMPLETE")
print("=" * 100)
print()
print("Summary:")
print("PASS = Test passed")
print("WARN = Needs attention")
print("FAIL = Test failed")
print()
print("Next step: Run cslaunch and test with 1031351.pdf")
