"""
Comprehensive test to identify remaining name matching issues
Tests various scenarios through the actual backend processing
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_name_matching_scenarios():
    """Test various name matching scenarios to identify issues"""
    
    # Import the actual backend functions
    from src.citation_extraction_endpoint import _names_equivalent
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
    
    print("=" * 80)
    print("TESTING BACKEND NAME MATCHING LOGIC")
    print("=" * 80)
    
    # Test cases from user's examples
    test_cases = [
        {
            "scenario": "Identical names (should match)",
            "canonical": "Erickson v. Pharmacia LLC",
            "extracted": "Erickson v. Pharmacia LLC",
            "expected": True,
            "category": "exact_match"
        },
        {
            "scenario": "Identical with date suffix (should match)",
            "canonical": "Erickson v. Pharmacia LLC",
            "extracted": "Erickson v. Pharmacia LLC, 2024",
            "expected": True,
            "category": "date_suffix"
        },
        {
            "scenario": "Date format difference (should match)",
            "canonical": "Singh v. Edwards Lifesciences Corp., 2009-07-06",
            "extracted": "Singh v. Edwards Lifesciences Corp., 2011",
            "expected": True,  # Names match, dates differ
            "category": "name_match_date_differ"
        },
        {
            "scenario": "Abbreviation - Western vs W.",
            "canonical": "Kammerer v. Western Gear Corp.",
            "extracted": "Kammerer v. W. Guar. Corp",
            "expected": False,  # "Gear" vs "Guar" is different!
            "category": "abbreviation_with_typo"
        },
        {
            "scenario": "Inc. abbreviation (should match)",
            "canonical": "Erwin v. Cotter Health Centers, Inc.",
            "extracted": "Erwin v. Cotter Health Centers, Inc.",
            "expected": True,
            "category": "inc_abbreviation"
        },
        {
            "scenario": "Co. vs Company (should match)",
            "canonical": "Rice v. Dow Chemical Co.",
            "extracted": "Rice v. Dow Chem. Co.",
            "expected": True,
            "category": "company_abbreviation"
        },
        {
            "scenario": "Corp. vs Corporation (should match)",
            "canonical": "Johnson v. Spider Staging Corp.",
            "extracted": "Johnson v. Spider Staging Corporation",
            "expected": True,
            "category": "corp_abbreviation"
        },
        {
            "scenario": "Dept. vs Department (should match)",
            "canonical": "Department of Ecology v. Campbell",
            "extracted": "Dept. of Ecology v. Campbell",
            "expected": True,
            "category": "dept_abbreviation"
        },
        {
            "scenario": "N/A extraction (should NOT match)",
            "canonical": "Erwin v. Cotter Health Centers, Inc.",
            "extracted": "N/A",
            "expected": False,
            "category": "extraction_failure"
        },
        {
            "scenario": "Cross-contamination (should NOT match)",
            "canonical": "Department of Ecology v. Campbell",
            "extracted": "Bolick v. Am. Barmag Corp",
            "expected": False,
            "category": "wrong_case"
        },
        {
            "scenario": "Technology vs Tech (should match)",
            "canonical": "Zenaida-Garcia v. Recovery Systems Technology, Inc.",
            "extracted": "Zenaida-Garcia v. Recovery Sys. Technology",
            "expected": True,
            "category": "tech_abbreviation"
        },
        {
            "scenario": "Construction vs Constr (should match)",
            "canonical": "Martin v. Humbert Construction, Inc.",
            "extracted": "Martin v. Humbert Constr",
            "expected": True,
            "category": "construction_abbreviation"
        },
    ]
    
    print("\n### Testing _names_equivalent() function ###\n")
    
    results = {
        "passed": 0,
        "failed": 0,
        "issues": []
    }
    
    for i, test in enumerate(test_cases, 1):
        canonical = test["canonical"]
        extracted = test["extracted"]
        expected = test["expected"]
        
        # Test with verified=True (more lenient)
        result_verified = _names_equivalent(extracted, canonical, verified=True)
        
        # Test with verified=False (strict)
        result_unverified = _names_equivalent(extracted, canonical, verified=False)
        
        # Determine if test passed
        passed = result_verified == expected
        
        print(f"\n{i}. {test['scenario']}")
        print(f"   Canonical:  '{canonical}'")
        print(f"   Extracted:  '{extracted}'")
        print(f"   Expected:   {expected}")
        print(f"   Result (verified):   {result_verified}")
        print(f"   Result (unverified): {result_unverified}")
        print(f"   Status: {'✅ PASS' if passed else '❌ FAIL'}")
        
        if passed:
            results["passed"] += 1
        else:
            results["failed"] += 1
            results["issues"].append({
                "test": test,
                "result_verified": result_verified,
                "result_unverified": result_unverified
            })
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {len(test_cases)}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Success Rate: {results['passed'] / len(test_cases) * 100:.1f}%")
    
    if results["issues"]:
        print("\n" + "=" * 80)
        print("ISSUES FOUND")
        print("=" * 80)
        for issue in results["issues"]:
            test = issue["test"]
            print(f"\n❌ {test['scenario']}")
            print(f"   Expected: {test['expected']}")
            print(f"   Got (verified): {issue['result_verified']}")
            print(f"   Category: {test['category']}")
            print(f"   Canonical: '{test['canonical']}'")
            print(f"   Extracted: '{test['extracted']}'")
    
    return results

def test_case_names_match():
    """Test the _case_names_match function used in verification"""
    
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
    
    print("\n" + "=" * 80)
    print("TESTING _case_names_match() function")
    print("=" * 80)
    
    processor = UnifiedCitationProcessorV2()
    
    test_cases = [
        ("Erickson v. Pharmacia LLC", "Erickson v. Pharmacia LLC, 2024", True, "date_suffix"),
        ("Singh v. Edwards Lifesciences Corp.", "Singh v. Edwards Lifesciences Corp., 2011", True, "date_suffix"),
        ("Rice v. Dow Chemical Co.", "Rice v. Dow Chem. Co.", True, "abbreviation"),
        ("Department of Ecology v. Campbell", "Dept. of Ecology v. Campbell", True, "dept_abbrev"),
        ("N/A", "Erwin v. Cotter Health Centers, Inc.", False, "na_extraction"),
        ("Department of Ecology v. Campbell", "Bolick v. Am. Barmag Corp", False, "wrong_case"),
    ]
    
    for name1, name2, expected, category in test_cases:
        result = processor._case_names_match(name1, name2)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"\n{status} [{category}]")
        print(f"  Name 1: '{name1}'")
        print(f"  Name 2: '{name2}'")
        print(f"  Expected: {expected}, Got: {result}")

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("BACKEND NAME MATCHING DIAGNOSTIC TEST")
    print("=" * 80)
    
    # Test _names_equivalent
    results = test_name_matching_scenarios()
    
    # Test _case_names_match
    test_case_names_match()
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    
    if results["failed"] > 0:
        print(f"\n⚠️  {results['failed']} issues found that need fixing!")
    else:
        print("\n✅ All tests passed!")
