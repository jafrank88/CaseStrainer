#!/usr/bin/env python3
"""
Direct test of extraction patterns for case names with years in parentheses.
"""
import re
import sys
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class TestCase:
    text: str
    expected: List[str]
    description: str = ""

def test_patterns() -> Tuple[bool, List[Tuple[str, bool, str]]]:
    """Test regex patterns for case name extraction."""
    # Test patterns
    patterns = [
        # Standard v. pattern with year in parentheses
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(\d{4}\)|\s*$)',
        # State v. pattern with year in parentheses
        r'(State\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(\d{4}\)|\s*$)',
    ]
    
    test_cases = [
        TestCase(
            "State v. Gentry (1995)", 
            ["State v. Gentry"],
            "Basic case with year in parentheses"
        ),
        TestCase(
            "In State v. Gentry (1995), the court held...", 
            ["State v. Gentry"],
            "Case at start of sentence with year in parentheses"
        ),
        TestCase(
            "See State v. Gentry (1995), 11 Cal.4th 1", 
            ["State v. Gentry"],
            "Case with citation after year"
        ),
        TestCase(
            "Compare State v. Gentry (1995) with People v. Smith (2000)",
            ["State v. Gentry", "People v. Smith"],
            "Multiple cases in one sentence"
        ),
        TestCase(
            "State v. Gentry, 11 Cal.4th 1 (1995)", 
            ["State v. Gentry"],
            "Case with citation before year"
        ),
        TestCase(
            "As established in Smith v. Jones (1990) and later in State v. Gentry (1995)",
            ["Smith v. Jones", "State v. Gentry"],
            "Multiple cases with years in different positions"
        ),
        TestCase(
            "See State v. Gentry (1995) 11 Cal.4th 1, 900 P.2d 1, 44 Cal.Rptr.2d 441",
            ["State v. Gentry"],
            "Case with parallel citations"
        )
    ]
    
    results = []
    all_passed = True
    
    for test_case in test_cases:
        found = []
        for pattern in patterns:
            matches = re.finditer(pattern, test_case.text, re.IGNORECASE)
            for match in matches:
                case_name = match.group(1).strip()
                # Clean up any trailing punctuation
                case_name = re.sub(r'[\s,;:.]+$', '', case_name)
                if case_name not in found:
                    found.append(case_name)
        
        # Check if all expected cases were found
        missing = set(test_case.expected) - set(found)
        passed = not bool(missing)
        
        if not passed:
            all_passed = False
            
        results.append((
            test_case.description or test_case.text,
            passed,
            f"Expected: {test_case.expected}, Found: {found}"
        ))
    
    return all_passed, results

def print_results(success: bool, results: List[Tuple[str, bool, str]]) -> None:
    """Print test results in a formatted way."""
    print("\n" + "="*80)
    print("TEST RESULTS")
    print("="*80)
    
    for i, (desc, passed, details) in enumerate(results, 1):
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"\nTest {i}: {desc}")
        print(f"Status: {status}")
        if not passed:
            print(f"Details: {details}")
    
    print("\n" + "="*80)
    if success:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*80)

if __name__ == "__main__":
    print("Testing case name extraction patterns...")
    success, results = test_patterns()
    print_results(success, results)
    
    if not success:
        sys.exit(1)
