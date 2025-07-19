#!/usr/bin/env python3
"""
Debug case name extraction
"""

import sys
import os
import re

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def debug_case_name_extraction():
    """Debug case name extraction step by step"""
    try:
        from case_name_extraction_core import CaseNameExtractor
        
        # Test text
        text = "In Punx v Smithers, 123 Wash. 2d 456, 789 P.2d 123 (1990), the court held that..."
        citation = "123 Wash. 2d 456, 789 P.2d 123"
        
        print(f"🔍 Debugging Case Name Extraction")
        print(f"Text: '{text}'")
        print(f"Citation: '{citation}'")
        print()
        
        # Check if citation is found
        citation_pos = text.find(citation)
        print(f"📋 Citation Search:")
        print(f"   Citation position: {citation_pos}")
        print(f"   Citation found: {citation_pos != -1}")
        
        if citation_pos == -1:
            print(f"   ❌ Citation not found in text!")
            print(f"   Text contains: '{text}'")
            print(f"   Looking for: '{citation}'")
            
            # Try different variations
            variations = [
                "123 Wash. 2d 456, 789 P.2d 123 (1990)",
                "123 Wash. 2d 456",
                "789 P.2d 123",
                "123 Wash. 2d 456, 789 P.2d 123 (1990)"
            ]
            
            for var in variations:
                pos = text.find(var)
                print(f"   Variation '{var}': position {pos}")
        
        print()
        
        # Create extractor
        extractor = CaseNameExtractor()
        
        # Step 1: Get context
        context = extractor._get_extraction_context(text, citation)
        print(f"📋 Step 1 - Context:")
        print(f"   Context: '{context}'")
        print(f"   Context length: {len(context)}")
        print()
        
        # Step 2: Try each pattern
        print(f"📋 Step 2 - Pattern Matching:")
        for i, pattern_info in enumerate(extractor.case_patterns):
            pattern = re.compile(pattern_info['pattern'], re.IGNORECASE)
            matches = list(pattern.finditer(context))
            
            print(f"   Pattern {i+1}: {pattern_info['name']}")
            print(f"     Pattern: {pattern_info['pattern']}")
            print(f"     Matches: {len(matches)}")
            
            # Special debug for standard_v pattern
            if pattern_info['name'] == 'standard_v':
                print(f"     🔍 Special debug for standard_v pattern:")
                print(f"       Context: '{context}'")
                print(f"       Looking for: 'Punx v Smithers'")
                
                # Test a simpler pattern
                simple_pattern = r'([A-Z][a-z]+)\s+v\.\s+([A-Z][a-z]+)'
                simple_matches = list(re.finditer(simple_pattern, context))
                print(f"       Simple pattern '{simple_pattern}': {len(simple_matches)} matches")
                for match in simple_matches:
                    print(f"         Match: '{match.group(0)}'")
                    print(f"         Group 1: '{match.group(1)}'")
                    print(f"         Group 2: '{match.group(2)}'")
            
            for j, match in enumerate(matches):
                print(f"       Match {j+1}: '{match.group(0)}'")
                try:
                    case_name = pattern_info['format'](match)
                    print(f"         Formatted: '{case_name}'")
                    
                    # Test validation
                    cleaned_name = extractor._clean_case_name(case_name)
                    print(f"         Cleaned: '{cleaned_name}'")
                    
                    is_valid = extractor._validate_case_name(cleaned_name)
                    print(f"         Valid: {is_valid}")
                    
                    if is_valid:
                        confidence = extractor._calculate_confidence(
                            cleaned_name, 
                            pattern_info['confidence_base'],
                            match,
                            context
                        )
                        print(f"         Confidence: {confidence}")
                    
                except Exception as e:
                    print(f"         Error: {e}")
            print()
        
        # Step 3: Test the full extraction
        print(f"📋 Step 3 - Full Extraction:")
        result = extractor.extract(text, citation)
        print(f"   Case name: '{result.case_name}'")
        print(f"   Date: '{result.date}'")
        print(f"   Year: '{result.year}'")
        print(f"   Confidence: {result.confidence}")
        print(f"   Method: '{result.method}'")
        print(f"   Debug info: {result.debug_info}")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_case_name_extraction() 