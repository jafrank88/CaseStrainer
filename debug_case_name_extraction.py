#!/usr/bin/env python3
"""
Debug script to test case name extraction for "Valid but Not Verified" citations
"""

import re
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import src.citation_utils_consolidated as enhanced_extraction_utils

def test_case_name_patterns():
    """Test case name extraction patterns directly"""
    
    test_text = """
    Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022).
    Carlsen v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011).
    Smith v. Jones, 123 Wn.2d 456, 789 P.3d 123 (2020).
    """
    
    print("=== TESTING CASE NAME PATTERNS ===")
    
    # Test patterns from standalone parser
    patterns = [
        # Standard: Name v. Name
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Z][A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
        r'([A-Z][A-Za-z\s,\.\'-]+?\s+vs\.\s+[A-Z][A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
        
        # In re cases
        r'(In\s+re\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
        
        # State/People cases
        r'(State\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
        r'(People\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
    ]
    
    for i, pattern in enumerate(patterns):
        print(f"\nPattern {i+1}: {pattern}")
        matches = list(re.finditer(pattern, test_text, re.IGNORECASE))
        
        if matches:
            print(f"  ✅ Found {len(matches)} matches:")
            for match in matches:
                print(f"    '{match.group(1)}'")
        else:
            print(f"  ❌ No matches found")
    
    # Test simpler patterns
    print(f"\n=== TESTING SIMPLER PATTERNS ===")
    
    simple_patterns = [
        r'([A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;]|\s*\d+\s+[A-Z]|\s*\(|\s*$)',
        r'([A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Za-z\s,\.\'-]+?)',
        r'([A-Za-z\s,\.\'-]+?\s+v\.\s+[A-Za-z\s,\.\'-]+?)(?=\s*[,;])',
    ]
    
    for i, pattern in enumerate(simple_patterns):
        print(f"\nSimple Pattern {i+1}: {pattern}")
        matches = list(re.finditer(pattern, test_text, re.IGNORECASE))
        
        if matches:
            print(f"  ✅ Found {len(matches)} matches:")
            for match in matches:
                print(f"    '{match.group(1)}'")
        else:
            print(f"  ❌ No matches found")

def test_enhanced_extraction_utils():
    """Test enhanced extraction utils with debug output"""
    
    test_text = """
    Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022).
    """
    
    test_citation = "200 Wn.2d 72"
    
    print("\n=== TESTING ENHANCED EXTRACTION UTILS ===")
    
    try:
        # Test the function
        result = enhanced_extraction_utils.extract_case_info_enhanced(test_text, test_citation)
        print(f"Result: {result}")
        
        # Test individual extractors
        extractor = enhanced_extraction_utils.EnhancedCaseNameExtractor()
        case_name = extractor.extract_case_name(test_text, test_citation)
        print(f"Direct case name extraction: '{case_name}'")
        
        # Test with different context
        context = test_text[:test_text.find(test_citation)]
        print(f"Context before citation: '{context}'")
        case_name_from_context = extractor._extract_with_citation_context(test_text, test_citation)
        print(f"Case name from context: '{case_name_from_context}'")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_standalone_parser():
    """Test standalone parser with debug output"""
    
    test_text = """
    Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022).
    """
    
    test_citation = "200 Wn.2d 72"
    
    print("\n=== TESTING STANDALONE PARSER ===")
    
    try:
        import standalone_citation_parser
        
        parser = standalone_citation_parser.CitationParser()
        result = parser.extract_from_text(test_text, test_citation)
        print(f"Parser result: {result}")
        
        # Test context extraction
        citation_index = test_text.find(test_citation)
        if citation_index != -1:
            context_start = max(0, citation_index - 200)
            context = test_text[context_start:citation_index]
            print(f"Context: '{context}'")
            
            # Test case name extraction from context
            case_name = parser._extract_case_name_from_context(context)
            print(f"Case name from context: '{case_name}'")
            
            # Test each pattern individually
            for i, pattern in enumerate(parser.case_name_patterns):
                print(f"\nTesting pattern {i+1}: {pattern}")
                matches = list(re.finditer(pattern, context, re.IGNORECASE))
                if matches:
                    print(f"  ✅ Found {len(matches)} matches:")
                    for match in matches:
                        print(f"    '{match.group(1)}'")
                else:
                    print(f"  ❌ No matches")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def run_case_name_debug():
    """Run case name debugging tests"""
    
    print("🔍 CASE NAME EXTRACTION DEBUGGING")
    print("=" * 50)
    
    test_case_name_patterns()
    test_enhanced_extraction_utils()
    test_standalone_parser()
    
    print("\n" + "=" * 50)
    print("📋 CASE NAME DEBUGGING SUMMARY:")
    print("1. Tests regex patterns directly")
    print("2. Tests extraction functions with debug output")
    print("3. Identifies why case names aren't being extracted")

if __name__ == "__main__":
    run_case_name_debug() 