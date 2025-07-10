# DEBUG CASE EXTRACTION

"""
Debug case name extraction step by step.
"""

import sys
import os
import re

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_case_extraction():
    """Test case name extraction step by step"""
    
    test_text = """
    Certified questions are questions of law we review de novo. 
    Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011).
    """
    
    test_citation = "171 Wn.2d 486"
    
    print("=== TESTING CASE EXTRACTION ===")
    
    try:
        import standalone_citation_parser
        
        parser = standalone_citation_parser.CitationParser()
        
        # Find citation in text
        citation_index = test_text.find(test_citation)
        print(f"Citation found at index: {citation_index}")
        
        if citation_index != -1:
            # Get context before citation
            context_start = max(0, citation_index - 200)
            context = test_text[context_start:citation_index]
            print(f"Context: '{context}'")
            
            # Test each pattern
            for i, pattern in enumerate(parser.case_name_patterns):
                print(f"\nPattern {i+1}: {pattern}")
                matches = list(re.finditer(pattern, context, re.IGNORECASE))
                
                if matches:
                    print(f"  Found {len(matches)} matches:")
                    for match in matches:
                        raw_case_name = match.group(1)
                        print(f"    Raw: '{raw_case_name}'")
                        
                        # Clean the case name
                        cleaned = parser._clean_case_name(raw_case_name)
                        print(f"    Cleaned: '{cleaned}'")
                        
                        # Extract just the case name
                        extracted = parser._extract_just_case_name(cleaned)
                        print(f"    Extracted: '{extracted}'")
                        
                        # Validate
                        is_valid = parser._is_valid_case_name(extracted)
                        print(f"    Valid: {is_valid}")
                        
                        if is_valid:
                            print(f"    ✅ FINAL CASE NAME: '{extracted}'")
                            return extracted
                else:
                    print(f"  No matches")
        
        print("❌ No valid case name found")
        return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_case_extraction() 