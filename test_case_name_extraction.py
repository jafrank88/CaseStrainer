#!/usr/bin/env python3
"""
Test case name extraction with problematic examples
"""
from src.unified_case_name_extractor_v2 import get_unified_extractor

# Test cases from actual async results
test_cases = [
    {
        'text': 'Northbrook Excess & Surplus Ins. Co. v. Procter & Gamble Co., 924 F.2d 633',
        'citation': '924 F.2d 633',
        'expected': 'Northbrook Excess & Surplus Ins. Co. v. Procter & Gamble Co.'
    },
    {
        'text': 'Flying T Ranch, Inc. v. Stillaguamish Tribe of Indians, 31 Wn. App. 2d 343, 359-62',
        'citation': '31 Wn. App. 2d 343',
        'expected': 'Flying T Ranch, Inc. v. Stillaguamish Tribe of Indians'
    },
    {
        'text': 'Five Corners Family Farmers, LLC v. State, 268 P.3d 892',
        'citation': '268 P.3d 892',
        'expected': 'Five Corners Family Farmers, LLC v. State'
    },
    {
        'text': 'Mgmt., LLC v. Nooksack Bus. Corp., 123 Wn.2d 456',
        'citation': '123 Wn.2d 456',
        'expected': 'Some Company Mgmt., LLC v. Nooksack Bus. Corp.'
    }
]

extractor = get_unified_extractor()

print("="*60)
print("CASE NAME EXTRACTION TEST")
print("="*60)

for i, test in enumerate(test_cases, 1):
    print(f"\nTest {i}:")
    print(f"  Text: {test['text'][:80]}...")
    print(f"  Citation: {test['citation']}")
    
    result = extractor.extract_case_name_and_date(
        text=test['text'],
        citation=test['citation'],
        debug=False
    )
    
    extracted = result.case_name or "N/A"
    expected = test['expected']
    
    print(f"  Expected: {expected}")
    print(f"  Extracted: {extracted}")
    
    if extracted == expected or (expected.endswith(extracted) or extracted.endswith(expected)):
        print(f"  ✅ PASS (or partial match)")
    else:
        print(f"  ❌ FAIL")
        print(f"  Method: {result.method}")
        print(f"  Confidence: {result.confidence}")

print("\n" + "="*60)
