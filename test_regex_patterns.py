#!/usr/bin/env python3
"""
Test script to check if regex patterns are matching citations properly.
"""

import re
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor

def test_regex_patterns():
    """Test if regex patterns match citations."""
    
    print("=== TESTING REGEX PATTERNS ===")
    print()
    
    # Initialize the processor
    processor = UnifiedCitationProcessor()
    
    # Test citations
    test_citations = [
        "171 Wash. 2d 486",
        "200 Wash. 2d 72", 
        "347 U.S. 483",
        "514 P.3d 643"
    ]
    
    test_text = """
    In State v. Smith, 171 Wash. 2d 486 (2011), the court held...
    The case was decided in State v. Johnson, 200 Wash. 2d 72 (2023).
    Brown v. Board of Education, 347 U.S. 483 (1954) established...
    The Pacific Reporter citation is 514 P.3d 643.
    """
    
    print(f"Test text: {test_text}")
    print()
    
    # Test each pattern individually
    for pattern_name, pattern in processor.primary_patterns.items():
        print(f"Pattern '{pattern_name}': {pattern.pattern}")
        matches = list(pattern.finditer(test_text))
        print(f"  Matches found: {len(matches)}")
        for match in matches:
            print(f"    Full match: '{match.group(0)}'")
            print(f"    Groups: {match.groups()}")
        print()
    
    # Test the full extraction
    print("=== TESTING FULL EXTRACTION ===")
    print()
    
    citations = processor.extract_citations(test_text)
    print(f"Total citations extracted: {len(citations)}")
    
    for i, citation in enumerate(citations, 1):
        print(f"Citation {i}:")
        print(f"  Text: {citation.citation}")
        print(f"  Method: {citation.method}")
        print(f"  Pattern: {citation.pattern}")
        print(f"  Extracted date: {citation.extracted_date}")
        print(f"  Year: {citation.year}")
        print()

def test_specific_patterns():
    """Test specific patterns that should match our citations."""
    
    print("=== TESTING SPECIFIC PATTERNS ===")
    print()
    
    # Test the wash2d pattern specifically
    wash2d_pattern = r'\b(\d+)\s+Wash\.2d\s+(\d+)\b'
    wash2d_compiled = re.compile(wash2d_pattern)
    
    test_cases = [
        "171 Wash. 2d 486",
        "200 Wash. 2d 72",
        "171 Wash.2d 486",  # No space after Wash
        "171 Wash. 2d 486 (2011)",  # With year
        "State v. Smith, 171 Wash. 2d 486",  # With case name
    ]
    
    for test_case in test_cases:
        print(f"Testing: '{test_case}'")
        matches = list(wash2d_compiled.finditer(test_case))
        print(f"  Matches: {len(matches)}")
        for match in matches:
            print(f"    Full: '{match.group(0)}'")
            print(f"    Groups: {match.groups()}")
        print()
    
    # Test with different spacing variations
    print("=== TESTING SPACING VARIATIONS ===")
    print()
    
    spacing_variations = [
        r'\b(\d+)\s+Wash\.\s*2d\s+(\d+)\b',  # Flexible spacing
        r'\b(\d+)\s+Wash\.2d\s+(\d+)\b',      # No space after Wash
        r'\b(\d+)\s+Wash\.\s+2d\s+(\d+)\b',   # Space after Wash
    ]
    
    for i, pattern in enumerate(spacing_variations, 1):
        print(f"Pattern {i}: {pattern}")
        compiled = re.compile(pattern)
        
        for test_case in test_cases:
            matches = list(compiled.finditer(test_case))
            if matches:
                print(f"  '{test_case}' -> MATCH: '{matches[0].group(0)}'")
            else:
                print(f"  '{test_case}' -> NO MATCH")
        print()

if __name__ == "__main__":
    test_regex_patterns()
    print("\n" + "="*80 + "\n")
    test_specific_patterns() 