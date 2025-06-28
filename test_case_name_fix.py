#!/usr/bin/env python3
"""
Test script to debug case name extraction issues.
"""

import re
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_case_name_extraction():
    """Test the case name extraction with the problematic examples."""
    
    # Test cases from the failing tests
    test_cases = [
        {
            "text": "In re Estate of Johnson, 456 Wash. 789 (2019), the court...",
            "citation": "456 Wash. 789",
            "expected": "In re Estate of Johnson"
        },
        {
            "text": "The court held in Smith v. Jones, 123 U.S. 456 (2020), that...",
            "citation": "123 U.S. 456",
            "expected": "Smith v. Jones"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}:")
        print(f"Text: {test_case['text']}")
        print(f"Citation: {test_case['citation']}")
        print(f"Expected: {test_case['expected']}")
        
        # Test the current extraction logic
        result = extract_case_name_from_text_simple(test_case['text'], test_case['citation'])
        print(f"Result: '{result}'")
        
        if result == test_case['expected']:
            print("✓ PASS")
        else:
            print("✗ FAIL")
            print(f"Difference: '{result}' vs '{test_case['expected']}'")

def extract_case_name_from_text_simple(text: str, citation: str) -> str:
    """Simplified version of case name extraction for debugging."""
    try:
        # Find the citation in the text
        citation_index = text.find(citation)
        if citation_index == -1:
            return ""
        
        # Get context around the citation
        context_window = 500
        start = max(0, citation_index - context_window)
        end = min(len(text), citation_index + len(citation) + context_window)
        context = text[start:end]
        
        print(f"Context: '{context}'")
        
        # Look for case name patterns before the citation
        patterns = [
            r'([A-Z][^,]+(?:v\.|vs\.|v\s)[^,]+?),\s*' + re.escape(citation),  # Standard v. cases
            r'(In re\s+[^,]+?),\s*' + re.escape(citation),  # In re cases
            r'(State v\.\s+[^,]+?),\s*' + re.escape(citation),  # State v. cases
            r'([A-Z][^,]+?),\s*' + re.escape(citation),  # Generic pattern
        ]
        
        for j, pattern in enumerate(patterns):
            print(f"  Pattern {j+1}: {pattern}")
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                case_name = match.group(1).strip()
                print(f"    Raw match: '{case_name}'")
                
                # Clean up the case name
                case_name = re.sub(r',\s*$', '', case_name).strip()
                case_name = re.sub(r'[,\s]+$', '', case_name).strip()
                case_name = case_name.rstrip('.,;:')
                
                print(f"    Cleaned: '{case_name}'")
                return case_name
        
        return ""
        
    except Exception as e:
        print(f"Error: {e}")
        return ""

if __name__ == "__main__":
    test_case_name_extraction() 