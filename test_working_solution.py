#!/usr/bin/env python3
"""
Working solution for case name extraction.
"""

import re

def extract_case_name_working(text: str, citation: str) -> str:
    """Working version of case name extraction."""
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
        
        # Look for case names right before the citation
        # Use more specific patterns that avoid common words
        patterns = [
            # Look for "v." or "vs." patterns (most common case name format)
            r'([A-Z][a-zA-Z\s]+(?:v\.|vs\.|v\s)[a-zA-Z\s]+?),\s*' + re.escape(citation),
            # Look for "In re" patterns
            r'(In re\s+[a-zA-Z\s]+?),\s*' + re.escape(citation),
            # Look for "State v." patterns
            r'(State v\.\s+[a-zA-Z\s]+?),\s*' + re.escape(citation),
            # Look for other patterns that start with capital letters
            r'([A-Z][a-zA-Z\s]+?),\s*' + re.escape(citation),
        ]
        
        for i, pattern in enumerate(patterns):
            print(f"  Pattern {i+1}: {pattern}")
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                case_name = match.group(1).strip()
                print(f"    Raw match: '{case_name}'")
                
                # Clean up the case name
                case_name = re.sub(r',\s*$', '', case_name).strip()
                case_name = re.sub(r'[,\s]+$', '', case_name).strip()
                case_name = case_name.rstrip('.,;:')
                
                print(f"    Cleaned: '{case_name}'")
                
                # Additional validation - check if it looks like a case name
                # Case names should not start with common words like "The", "A", "An"
                if (len(case_name) > 3 and 
                    any(char.isupper() for char in case_name) and
                    not case_name.lower().startswith(('the ', 'a ', 'an '))):
                    return case_name
                else:
                    print(f"    Rejected: '{case_name}' (fails validation)")
        
        # If no valid match found, try a more aggressive approach
        # Look for the actual case name pattern in the context
        print("  Trying aggressive pattern matching...")
        
        # Look for "v." patterns specifically
        v_pattern = r'([A-Z][a-zA-Z\s]+(?:v\.|vs\.|v\s)[a-zA-Z\s]+?),\s*' + re.escape(citation)
        match = re.search(v_pattern, context, re.IGNORECASE)
        if match:
            full_match = match.group(0)
            print(f"    Full match: '{full_match}'")
            
            # Try to extract just the case name part
            # Look for the last occurrence of a case name pattern before the citation
            case_name_match = re.search(r'([A-Z][a-zA-Z\s]+(?:v\.|vs\.|v\s)[a-zA-Z\s]+?)(?=,\s*' + re.escape(citation) + r')', context, re.IGNORECASE)
            if case_name_match:
                case_name = case_name_match.group(1).strip()
                case_name = case_name.rstrip('.,;:')
                print(f"    Extracted case name: '{case_name}'")
                
                if len(case_name) > 3 and any(char.isupper() for char in case_name):
                    return case_name
        
        return ""
        
    except Exception as e:
        print(f"Error: {e}")
        return ""

def test_working_extraction():
    """Test the working case name extraction."""
    
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
        
        result = extract_case_name_working(test_case['text'], test_case['citation'])
        print(f"Result: '{result}'")
        print(f"Expected: '{test_case['expected']}'")
        
        if result == test_case['expected']:
            print("✓ PASS")
        else:
            print("✗ FAIL")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    print("Testing Working Case Name Extraction")
    print("=" * 50)
    
    success = test_working_extraction()
    
    if success:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n❌ Some tests failed.") 