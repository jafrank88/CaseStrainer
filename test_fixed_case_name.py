#!/usr/bin/env python3
"""
Test script with fixed case name extraction logic.
"""

import re
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def extract_case_name_fixed(text: str, citation: str) -> str:
    """Fixed version of case name extraction."""
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
        
        # Look for case name patterns right before the citation
        # More precise patterns that avoid capturing extra text
        patterns = [
            # Look for case names ending with comma followed by citation
            r'([A-Z][a-zA-Z\s]+(?:v\.|vs\.|v\s)[a-zA-Z\s]+?),\s*' + re.escape(citation),
            r'(In re\s+[a-zA-Z\s]+?),\s*' + re.escape(citation),
            r'(State v\.\s+[a-zA-Z\s]+?),\s*' + re.escape(citation),
            r'([A-Z][a-zA-Z\s]+?),\s*' + re.escape(citation),
        ]
        
        # Try to find the case name right before the citation
        # Look for patterns like "Case Name, citation" or "Case Name (citation"
        citation_patterns = [
            # More restrictive patterns that look for case names right before citation
            r'([A-Z][a-zA-Z\s]+(?:v\.|vs\.|v\s)[a-zA-Z\s]+?),\s*' + re.escape(citation),  # Standard v. cases
            r'(In re\s+[a-zA-Z\s]+?),\s*' + re.escape(citation),  # In re cases
            r'(State v\.\s+[a-zA-Z\s]+?),\s*' + re.escape(citation),  # State v. cases
            r'([A-Z][a-zA-Z\s]+?),\s*' + re.escape(citation),  # Generic pattern
        ]
        
        for pattern in citation_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                case_name = match.group(1).strip()
                # Clean up the case name
                case_name = re.sub(r',\s*$', '', case_name).strip()
                case_name = re.sub(r'[,\s]+$', '', case_name).strip()
                case_name = case_name.rstrip('.,;:')
                
                # Additional validation - make sure it looks like a case name
                if len(case_name) > 3 and any(char.isupper() for char in case_name):
                    return case_name
        
        # If no match found with comma pattern, try without comma
        no_comma_patterns = [
            r'([A-Z][a-zA-Z\s]+(?:v\.|vs\.|v\s)[a-zA-Z\s]+?)\s+' + re.escape(citation),
            r'(In re\s+[a-zA-Z\s]+?)\s+' + re.escape(citation),
            r'(State v\.\s+[a-zA-Z\s]+?)\s+' + re.escape(citation),
        ]
        
        for pattern in no_comma_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                case_name = match.group(1).strip()
                case_name = case_name.rstrip('.,;:')
                
                if len(case_name) > 3 and any(char.isupper() for char in case_name):
                    return case_name
        
        return ""
        
    except Exception as e:
        print(f"Error: {e}")
        return ""

def test_fixed_extraction():
    """Test the fixed case name extraction."""
    
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
        },
        {
            "text": "State v. Brown, 789 F.2d 123 (2021), established...",
            "citation": "789 F.2d 123",
            "expected": "State v. Brown"
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['citation']}")
        print(f"Text: {test_case['text']}")
        
        result = extract_case_name_fixed(test_case['text'], test_case['citation'])
        print(f"Result: '{result}'")
        print(f"Expected: '{test_case['expected']}'")
        
        if result == test_case['expected']:
            print("✓ PASS")
        else:
            print("✗ FAIL")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    print("Testing Fixed Case Name Extraction")
    print("=" * 50)
    
    success = test_fixed_extraction()
    
    if success:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n❌ Some tests failed.") 