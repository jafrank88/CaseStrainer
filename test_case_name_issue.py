#!/usr/bin/env python3
"""
Test script to reproduce and debug the case name extraction issue.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig
import re

def test_case_name_extraction_issue():
    """Test the specific case name extraction issue."""
    print("=== Testing Case Name Extraction Issue ===")
    
    # The problematic text from the JSON
    test_text = """ton law 
when a resolution of that question is necessary to resolve a case before the 
federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d
72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review
de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 
(2011). We also review the meaning of a statute de novo. Dep't of Ecology v.
Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    # Create processor with debug mode
    config = ProcessingConfig(
        debug_mode=True,
        enable_verification=False  # Disable verification to focus on extraction
    )
    processor = UnifiedCitationProcessorV2(config)
    
    print(f"Processing text: {repr(test_text)}")
    print(f"Text length: {len(test_text)}")
    
    # Process the text
    results = processor.process_text(test_text)
    
    print(f"\nFound {len(results)} citations:")
    for i, citation in enumerate(results, 1):
        print(f"\n{i}. Citation: {citation.citation}")
        print(f"   Start index: {citation.start_index}")
        print(f"   End index: {citation.end_index}")
        print(f"   Extracted case name: {citation.extracted_case_name}")
        print(f"   Extracted date: {citation.extracted_date}")
        print(f"   Context: {repr(citation.context)}")
        
        # Show the exact position of the citation in the text
        if citation.start_index is not None and citation.end_index is not None:
            before = test_text[max(0, citation.start_index-50):citation.start_index]
            after = test_text[citation.end_index:min(len(test_text), citation.end_index+50)]
            print(f"   Before: {repr(before)}")
            print(f"   After: {repr(after)}")

def test_individual_citation_extraction():
    """Test extraction of individual citations to isolate the issue."""
    print("\n=== Testing Individual Citation Extraction ===")
    
    # Test the specific citation that's getting the wrong case name
    test_text = """Certified questions are questions of law we review
de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 
(2011). We also review the meaning of a statute de novo."""
    
    config = ProcessingConfig(debug_mode=True, enable_verification=False)
    processor = UnifiedCitationProcessorV2(config)
    
    print(f"Testing text: {repr(test_text)}")
    results = processor.process_text(test_text)
    
    for i, citation in enumerate(results, 1):
        print(f"\n{i}. Citation: {citation.citation}")
        print(f"   Extracted case name: {citation.extracted_case_name}")
        print(f"   Expected case name: Carlson v. Glob. Client Sols., LLC")

def test_regex_patterns_directly():
    """Test the regex patterns directly on the problematic text."""
    print("\n=== Testing Regex Patterns Directly ===")
    
    # The context that should contain the case name
    context = ". Certified questions are questions of law we review\nde novo. Carlson v. Glob. Client Sols., LLC, 17"
    
    print(f"Testing context: {repr(context)}")
    
    # Test each pattern
    patterns = [
        r'([A-Z][A-Za-z0-9&.,\'\\-]*(?:\s+[A-Za-z0-9&.,\'\\-]+)*\s+(?:v\.|vs\.|versus)\s+[A-Z][A-Za-z0-9&.,\'\\-]*(?:\s+[A-Za-z0-9&.,\'\\-]+)*)',
        r'((?:[A-Za-z0-9&.,\'\\-]+\s+)+(?:v\.|vs\.|versus)\s+(?:[A-Za-z0-9&.,\'\\-]+\s*)+)',
        r'(?:^|[\n\r]|[\.\!\?]\s+)([A-Z][A-Za-z&.,\'\\-]*(?:\s+[A-Za-z&.,\'\\-]+)*\s+(?:v\.|vs\.|versus)\s+[A-Za-z&.,\'\\-]+(?:\s+[A-Za-z&.,\'\\-]+)*)',
    ]
    
    for i, pattern in enumerate(patterns, 1):
        print(f"\nPattern {i}: {pattern}")
        matches = re.finditer(pattern, context, re.IGNORECASE)
        for match in matches:
            print(f"  Match: {repr(match.group(1))}")

if __name__ == "__main__":
    test_case_name_extraction_issue()
    test_individual_citation_extraction()
    test_regex_patterns_directly() 