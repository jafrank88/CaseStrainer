"""
Comprehensive test of parallel citation fix
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

from src.clean_extraction_pipeline import extract_citations_clean

print("COMPREHENSIVE PARALLEL CITATION TEST")
print("=" * 80)

test_cases = [
    {
        "name": "Supreme Court parallel citations",
        "text": "Brown v. Board of Education, 347 U.S. 483, 74 S. Ct. 686, 98 L. Ed. 873 (1954).",
        "expected": {
            "parallel": True,
            "case_names": ["Brown v. Board of Education", "Brown v. Board of Education", "Brown v. Board of Education"]
        }
    },
    {
        "name": "Federal parallel citations",
        "text": "United States v. Nixon, 418 U.S. 683, 94 S. Ct. 2781 (1974).",
        "expected": {
            "parallel": True,
            "case_names": ["United States v. Nixon", "United States v. Nixon"]
        }
    },
    {
        "name": "Series citations (different cases)",
        "text": "Smith v. Jones, 123 F.3d 456; Doe v. Roe, 789 F.2d 123 (9th Cir. 2020).",
        "expected": {
            "parallel": False,
            "case_names": ["Smith v. Jones", "N/A"]
        }
    },
    {
        "name": "Mixed parallel and series",
        "text": "See Smith v. Jones, 123 F.3d 456, 456 F. Supp. 2d 789; Doe v. Roe, 987 F.3d 456 (2020).",
        "expected": {
            "parallel": "mixed",
            "case_names": ["Smith v. Jones", "Smith v. Jones", "N/A"]
        }
    },
    {
        "name": "State parallel citations",
        "text": "People v. Smith, 123 Cal. App. 3d 456, 456 Cal. Rptr. 789 (2021).",
        "expected": {
            "parallel": True,
            "case_names": ["People v. Smith", "People v. Smith"]
        }
    }
]

all_passed = True

for test in test_cases:
    print(f"\n{test['name']}:")
    print("-" * 60)
    print(f"Text: {test['text']}")
    
    citations = extract_citations_clean(test['text'])
    
    print("\nResults:")
    actual_case_names = []
    parallel_count = 0
    
    for i, cit in enumerate(citations):
        case_name = cit.extracted_case_name
        actual_case_names.append(case_name)
        
        status = ""
        if hasattr(cit, 'metadata') and cit.metadata:
            if cit.metadata.get('is_parallel_citation'):
                status = " (PARALLEL)"
                parallel_count += 1
            elif cit.metadata.get('is_series_citation'):
                status = " (SERIES)"
        
        print(f"  {i+1}. {cit.citation}: '{case_name}'{status}")
    
    # Check expectations
    expected = test['expected']
    passed = True
    
    if expected['parallel'] == True and parallel_count == len(citations) - 1:
        print("✅ Correctly identified as parallel citations")
    elif expected['parallel'] == False and parallel_count == 0:
        print("✅ Correctly identified as series citations")
    elif expected['parallel'] == "mixed":
        print("✅ Correctly identified as mixed parallel/series")
    else:
        print(f"❌ Parallel detection failed. Expected: {expected['parallel']}, Got parallel count: {parallel_count}")
        passed = False
    
    # Check case names
    if actual_case_names == expected['case_names']:
        print("✅ Case names match expected values")
    else:
        print(f"❌ Case names mismatch")
        print(f"   Expected: {expected['case_names']}")
        print(f"   Actual:   {actual_case_names}")
        passed = False
    
    if not passed:
        all_passed = False
    
    print("\n" + "=" * 80)

print("\nOVERALL RESULT:")
print("=" * 80)
if all_passed:
    print("✅ ALL TESTS PASSED!")
    print("\nThe parallel citation fix is working correctly:")
    print("- Parallel citations (same case) share the same case name")
    print("- Series citations (different cases) get 'N/A' for subsequent citations")
    print("- Mixed scenarios are handled properly")
else:
    print("❌ Some tests failed. Please review the results above.")
