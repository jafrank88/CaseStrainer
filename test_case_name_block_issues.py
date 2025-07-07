#!/usr/bin/env python3
"""
Test script to demonstrate scenarios where extracted/hinted case names 
might not appear as complete blocks in the user-provided text.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.case_name_extraction_core import extract_case_name_triple

def test_case_name_block_issues():
    """Test scenarios where case names might not appear as complete blocks."""
    print("Testing Case Name Block Issues")
    print("=" * 80)
    
    test_cases = [
        {
            "text": "The court in John Doe P v. Thurston County, 199 Wn. App. 280, found that the principle applies.",
            "citation": "199 Wn. App. 280",
            "description": "Case name split across line breaks or formatting",
            "issue": "Line-based extraction might miss complete case name"
        },
        {
            "text": "In Smith v. Jones, the court held... See 123 U.S. 456 for more details.",
            "citation": "123 U.S. 456",
            "description": "Case name appears earlier in text, not near citation",
            "issue": "Context window might not capture the actual case name"
        },
        {
            "text": "The principle established in Brown v. Board of Education (347 U.S. 483) applies here.",
            "citation": "347 U.S. 483",
            "description": "Case name with parentheses around citation",
            "issue": "Parentheses might interfere with extraction patterns"
        },
        {
            "text": "As held in Roe v. Wade, 410 U.S. 113 (1973), the right to privacy...",
            "citation": "410 U.S. 113",
            "description": "Case name followed by citation with year",
            "issue": "Year in parentheses might be included in extraction"
        },
        {
            "text": "The court in Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017), found that...",
            "citation": "399 P.3d 1195",
            "description": "Parallel citation - case name might be far from this citation",
            "issue": "Context window might not reach the actual case name"
        },
        {
            "text": "See generally Smith v. Jones, 123 U.S. 456 (2020).",
            "citation": "123 U.S. 456",
            "description": "Case name with signal word 'See generally'",
            "issue": "Signal words might be included in extraction"
        },
        {
            "text": "The court in In re Estate of Johnson, 456 Wash. 789 (2019), the court...",
            "citation": "456 Wash. 789",
            "description": "In re case with 'the court' repeated",
            "issue": "Repetitive text might be included in extraction"
        },
        {
            "text": "According to State v. Smith, 123 U.S. 456, the defendant...",
            "citation": "123 U.S. 456",
            "description": "Case name with introductory phrase",
            "issue": "Introductory text might be included in extraction"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print(f"Issue: {test_case['issue']}")
        print(f"Text: {test_case['text']}")
        print(f"Citation: {test_case['citation']}")
        
        # Extract case name triple
        triple = extract_case_name_triple(test_case['text'], test_case['citation'])
        
        print(f"\nResults:")
        print(f"  Canonical name: '{triple['canonical_name']}'")
        print(f"  Extracted name: '{triple['extracted_name']}'")
        print(f"  Hinted name: '{triple['hinted_name']}'")
        print(f"  Final case name: '{triple['case_name']}'")
        
        # Check if the extracted/hinted names appear as complete blocks in the text
        extracted_in_text = triple['extracted_name'] in test_case['text'] if triple['extracted_name'] != "N/A" else False
        hinted_in_text = triple['hinted_name'] in test_case['text'] if triple['hinted_name'] != "N/A" else False
        
        print(f"\nBlock Analysis:")
        print(f"  Extracted name appears as block: {extracted_in_text}")
        print(f"  Hinted name appears as block: {hinted_in_text}")
        
        if not extracted_in_text and triple['extracted_name'] != "N/A":
            print(f"  ⚠️ WARNING: Extracted name '{triple['extracted_name']}' not found as complete block in text")
        
        if not hinted_in_text and triple['hinted_name'] != "N/A":
            print(f"  ⚠️ WARNING: Hinted name '{triple['hinted_name']}' not found as complete block in text")
        
        print("-" * 80)

def test_line_break_issues():
    """Test specific line break and formatting issues."""
    print("\nTesting Line Break and Formatting Issues")
    print("=" * 80)
    
    # Test case with line breaks
    text_with_breaks = """The court in John Doe P v. 
Thurston County, 199 Wn. App. 280, found that the principle applies."""
    
    print(f"Text with line breaks:")
    print(f"'{text_with_breaks}'")
    print(f"Citation: 199 Wn. App. 280")
    
    triple = extract_case_name_triple(text_with_breaks, "199 Wn. App. 280")
    
    print(f"\nResults:")
    print(f"  Extracted name: '{triple['extracted_name']}'")
    print(f"  Hinted name: '{triple['hinted_name']}'")
    print(f"  Final case name: '{triple['case_name']}'")
    
    # Check if the case name appears as a complete block
    extracted_in_text = triple['extracted_name'] in text_with_breaks if triple['extracted_name'] != "N/A" else False
    print(f"  Extracted name appears as block: {extracted_in_text}")
    
    if not extracted_in_text and triple['extracted_name'] != "N/A":
        print(f"  ❌ ISSUE: Extracted name not found as complete block due to line breaks")

def test_context_window_issues():
    """Test issues with context window limitations."""
    print("\nTesting Context Window Issues")
    print("=" * 80)
    
    # Test case where case name is far from citation
    text_with_distance = """The court in Smith v. Jones established an important principle. 
This principle was later applied in several cases. 
The court also considered the implications in other jurisdictions. 
Finally, the court addressed the specific issue in 123 U.S. 456."""
    
    print(f"Text with case name far from citation:")
    print(f"'{text_with_distance}'")
    print(f"Citation: 123 U.S. 456")
    
    triple = extract_case_name_triple(text_with_distance, "123 U.S. 456")
    
    print(f"\nResults:")
    print(f"  Extracted name: '{triple['extracted_name']}'")
    print(f"  Hinted name: '{triple['hinted_name']}'")
    print(f"  Final case name: '{triple['case_name']}'")
    
    # Check if the actual case name "Smith v. Jones" was found
    expected_case_name = "Smith v. Jones"
    found_expected = expected_case_name in [triple['extracted_name'], triple['hinted_name']]
    print(f"  Expected case name '{expected_case_name}' found: {found_expected}")
    
    if not found_expected:
        print(f"  ❌ ISSUE: Context window too small to capture case name far from citation")

def test_pattern_matching_issues():
    """Test issues with pattern matching."""
    print("\nTesting Pattern Matching Issues")
    print("=" * 80)
    
    test_patterns = [
        {
            "text": "The court in Doe P v. Thurston County, 199 Wn. App. 280, found that...",
            "citation": "199 Wn. App. 280",
            "expected": "Doe P v. Thurston County",
            "description": "Standard v. pattern"
        },
        {
            "text": "In re Estate of Johnson, 456 Wash. 789 (2019), the court...",
            "citation": "456 Wash. 789",
            "expected": "In re Estate of Johnson",
            "description": "In re pattern"
        },
        {
            "text": "State v. Smith, 123 U.S. 456, established...",
            "citation": "123 U.S. 456",
            "expected": "State v. Smith",
            "description": "State v. pattern"
        }
    ]
    
    for i, test_case in enumerate(test_patterns, 1):
        print(f"\nPattern Test {i}: {test_case['description']}")
        print(f"Text: {test_case['text']}")
        print(f"Citation: {test_case['citation']}")
        print(f"Expected: {test_case['expected']}")
        
        triple = extract_case_name_triple(test_case['text'], test_case['citation'])
        
        print(f"Results:")
        print(f"  Extracted: '{triple['extracted_name']}'")
        print(f"  Hinted: '{triple['hinted_name']}'")
        print(f"  Final: '{triple['case_name']}'")
        
        # Check if the expected case name was found
        found_expected = test_case['expected'] in [triple['extracted_name'], triple['hinted_name'], triple['case_name']]
        print(f"  Expected found: {found_expected}")
        
        if not found_expected:
            print(f"  ❌ ISSUE: Pattern matching failed to capture expected case name")

if __name__ == "__main__":
    print("Testing Case Name Block Issues")
    print("=" * 80)
    
    test_case_name_block_issues()
    test_line_break_issues()
    test_context_window_issues()
    test_pattern_matching_issues()
    
    print("\n" + "=" * 80)
    print("Summary of Potential Issues:")
    print("1. Line breaks can split case names across multiple lines")
    print("2. Context window limitations can miss case names far from citations")
    print("3. Pattern matching might include extra text (signal words, years, etc.)")
    print("4. Parentheses and formatting can interfere with extraction")
    print("5. Parallel citations might have case names far from the specific citation")
    print("6. Introductory phrases might be included in extraction")
    print("7. Repetitive text might be captured instead of just the case name") 