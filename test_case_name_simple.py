#!/usr/bin/env python3
"""
Simple test script to debug case name extraction issues without API calls.
"""

import os
import sys
import re

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Disable API calls for testing
os.environ['DISABLE_API_CALLS'] = '1'

from src.case_name_extraction_core import extract_case_name_from_text

def test_case_name_extraction_direct():
    """Test case name extraction function directly without API calls."""
    
    test_cases = [
        {
            'text': 'In State v. Smith, 123 Wn. App. 456, 789 P.3d 123 (2023), the court held...',
            'citation': '123 Wn. App. 456',
            'expected_case_name': 'State v. Smith'
        },
        {
            'text': 'The case of Johnson v. Brown, 456 P.3d 789 (2021) established...',
            'citation': '456 P.3d 789',
            'expected_case_name': 'Johnson v. Brown'
        },
        {
            'text': 'As held in Doe v. Roe, 789 Wn.2d 123, 456 P.3d 789 (2020), the standard is...',
            'citation': '789 Wn.2d 123',
            'expected_case_name': 'Doe v. Roe'
        },
        {
            'text': 'In the matter of In re Estate of Johnson, 456 P.3d 789 (2022), the court found...',
            'citation': '456 P.3d 789',
            'expected_case_name': 'In re Estate of Johnson'
        },
        {
            'text': 'The court in United States v. Wilson, 123 U.S. 456 (1999) ruled...',
            'citation': '123 U.S. 456',
            'expected_case_name': 'United States v. Wilson'
        },
        {
            'text': 'People v. Davis, 789 Cal. App. 2d 123 (2020) established...',
            'citation': '789 Cal. App. 2d 123',
            'expected_case_name': 'People v. Davis'
        },
        {
            'text': 'In Doe v. Wdae, 123 U.S. 456 (1973), the court ruled...',
            'citation': '123 U.S. 456',
            'expected_case_name': 'Doe v. Wdae'  # Misspelled party name
        }
    ]
    
    print("=== Testing Case Name Extraction Directly ===\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test Case {i}:")
        print(f"Text: {test_case['text']}")
        print(f"Citation: {test_case['citation']}")
        print(f"Expected Case Name: {test_case['expected_case_name']}")
        
        # Debug: Show context window around citation
        citation_index = test_case['text'].find(test_case['citation'])
        if citation_index != -1:
            context_before = test_case['text'][max(0, citation_index - 100):citation_index]
            context_after = test_case['text'][citation_index:min(len(test_case['text']), citation_index + 100)]
            print(f"Context before citation: '{context_before}'")
            print(f"Context after citation: '{context_after}'")
        else:
            print("Citation not found in text!")
        
        # Test the case name extraction function directly
        extracted_name = extract_case_name_from_text(test_case['text'], test_case['citation'])
        print(f"Extracted Case Name: '{extracted_name}'")
        
        # Check if extraction worked
        if extracted_name and extracted_name != "N/A":
            print("✅ PASS - Case name extraction worked")
        else:
            print("❌ FAIL - Case name extraction failed")
        
        print("\n" + "="*80 + "\n")

def test_case_name_patterns():
    """Test different case name patterns."""
    
    patterns = [
        ('State v. Smith', 'State v. Smith'),
        ('Johnson v. Brown', 'Johnson v. Brown'),
        ('Doe v. Roe', 'Doe v. Roe'),
        ('In re Estate of Johnson', 'In re Estate of Johnson'),
        ('United States v. Wilson', 'United States v. Wilson'),
        ('People v. Davis', 'People v. Davis'),
    ]
    
    print("=== Testing Case Name Patterns ===\n")
    
    for pattern, expected in patterns:
        text = f"In {pattern}, 123 Wn. App. 456 (2023), the court held..."
        citation = "123 Wn. App. 456"
        
        extracted = extract_case_name_from_text(text, citation)
        print(f"Pattern: '{pattern}' -> Expected: '{expected}' -> Got: '{extracted}'")
        
        if extracted and extracted != "N/A":
            print("✅ PASS")
        else:
            print("❌ FAIL")
        print()

def test_real_document_patterns():
    """Test with real document patterns."""
    
    real_text = """
    MEMORANDUM DECISION - UNPUBLISHED OPINION
    
    In State v. Johnson, 123 Wn. App. 456, 789 P.3d 123 (2023), the Washington Court of Appeals 
    held that the trial court did not err in admitting the evidence. The court found that the 
    defendant's motion to suppress was properly denied.
    
    Similarly, in Doe v. Smith, 456 P.3d 789 (2021), the Supreme Court established the standard 
    for determining when evidence should be excluded. The court emphasized the importance of 
    following proper procedures.
    
    The case of Brown v. Wilson, 789 Wn.2d 123, 456 P.3d 789 (2020) further clarified the 
    application of the exclusionary rule in Washington courts.
    
    Additionally, the court cited United States v. Smith, 123 U.S. 456 (1999) for the proposition
    that evidence obtained in violation of the Fourth Amendment must be excluded.
    """
    
    print("=== Testing Real Document Patterns ===\n")
    
    citations = [
        ('123 Wn. App. 456', 'State v. Johnson'),
        ('456 P.3d 789', 'Doe v. Smith'),  # Should find the first occurrence
        ('789 Wn.2d 123', 'Brown v. Wilson'),
        ('123 U.S. 456', 'United States v. Smith')
    ]
    
    for citation, expected in citations:
        print(f"Citation: {citation}")
        extracted = extract_case_name_from_text(real_text, citation)
        print(f"  Expected: '{expected}'")
        print(f"  Extracted: '{extracted}'")
        
        if extracted and extracted != "N/A":
            print("  ✅ PASS - Case name found")
        else:
            print("  ❌ FAIL - No case name found")
        print()

def test_edge_cases():
    """Test edge cases and difficult patterns."""
    
    edge_cases = [
        {
            'text': 'The court in Smith v. Jones, 123 Wn. App. 456, 789 P.3d 123, 2023 WL 1234567 (2023) ruled...',
            'citation': '123 Wn. App. 456',
            'expected': 'Smith v. Jones'
        },
        {
            'text': 'In re Estate of Johnson, 456 P.3d 789 (2022), the court found...',
            'citation': '456 P.3d 789',
            'expected': 'In re Estate of Johnson'
        },
        {
            'text': 'State v. Brown, 789 Wn.2d 123, 456 P.3d 789 (2020) further clarified...',
            'citation': '789 Wn.2d 123',
            'expected': 'State v. Brown'
        },
        {
            'text': 'The case of Doe v. Roe, 123 Wn. App. 456, 789 P.3d 123 (2023) established...',
            'citation': '123 Wn. App. 456',
            'expected': 'Doe v. Roe'
        }
    ]
    
    print("=== Testing Edge Cases ===\n")
    
    for i, test_case in enumerate(edge_cases, 1):
        print(f"Edge Case {i}:")
        print(f"Text: {test_case['text']}")
        print(f"Citation: {test_case['citation']}")
        print(f"Expected: {test_case['expected']}")
        
        extracted = extract_case_name_from_text(test_case['text'], test_case['citation'])
        print(f"Extracted: '{extracted}'")
        
        if extracted and extracted != "N/A":
            print("✅ PASS")
        else:
            print("❌ FAIL")
        print()

def test_no_case_name():
    """Test cases where no case name should be found."""
    
    no_name_cases = [
        {
            'text': 'The court held in 123 Wn. App. 456 (2023) that...',
            'citation': '123 Wn. App. 456',
            'description': 'Citation without case name'
        },
        {
            'text': 'As established in 456 P.3d 789 (2021), the standard is...',
            'citation': '456 P.3d 789',
            'description': 'Citation without case name'
        }
    ]
    
    print("=== Testing No Case Name Scenarios ===\n")
    
    for i, test_case in enumerate(no_name_cases, 1):
        print(f"No Name Case {i}:")
        print(f"Description: {test_case['description']}")
        print(f"Text: {test_case['text']}")
        print(f"Citation: {test_case['citation']}")
        
        extracted = extract_case_name_from_text(test_case['text'], test_case['citation'])
        print(f"Extracted: '{extracted}'")
        
        # In these cases, we expect no case name or "N/A"
        if not extracted or extracted == "N/A":
            print("✅ PASS - Correctly found no case name")
        else:
            print("❌ FAIL - Should not have found a case name")
        print()

if __name__ == "__main__":
    test_case_name_extraction_direct()
    test_case_name_patterns()
    test_real_document_patterns()
    test_edge_cases()
    test_no_case_name() 