#!/usr/bin/env python3
"""
Debug TOA parsing step by step.
"""

import sys
import os
import re

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from toa_parser import ImprovedToAParser, ToAEntry

def debug_toa_parsing():
    """Debug TOA parsing step by step."""
    print("=" * 80)
    print("DEBUGGING TOA PARSING")
    print("=" * 80)
    
    # Load the brief
    brief_file = "wa_briefs_text/004_COA Respondent Brief.txt"
    
    try:
        with open(brief_file, 'r', encoding='utf-8') as f:
            text = f.read()
        print(f"✓ Loaded brief: {len(text):,} characters")
    except Exception as e:
        print(f"✗ Error loading brief: {e}")
        return
    
    # Create parser
    parser = ImprovedToAParser()
    
    # Step 1: Test TOA detection
    print("\n1. TESTING TOA DETECTION...")
    toa_bounds = parser.detect_toa_section(text)
    if toa_bounds:
        start, end = toa_bounds
        print(f"   ✓ TOA found at {start}:{end}")
        
        # Get TOA section
        toa_section = text[start:end]
        print(f"   TOA section length: {len(toa_section):,} characters")
        print(f"   TOA preview: {toa_section[:300]}...")
    else:
        print("   ✗ No TOA section found")
        return
    
    # Step 2: Test manual pattern matching
    print("\n2. TESTING MANUAL PATTERN MATCHING...")
    
    # Test the patterns manually
    patterns = [
        # Pattern 1: Standard v. cases
        r'([A-Z][A-Za-z\'\-\s\.]+? v\.? [A-Z][A-Za-z\'\-\s\.]+?)\s*,\s*([\dA-Za-z\.\s]+\(\d{4}\))',
        # Pattern 2: In re cases
        r'(In\s+re\s+[A-Z][A-Za-z\'\-\s\.]+)\s*,\s*([\dA-Za-z\.\s]+\(\d{4}\))',
        # Pattern 3: State v. cases
        r'(State\s+v\.\s+[A-Z][A-Za-z\'\-\s\.]+)\s*,\s*([\dA-Za-z\.\s]+\(\d{4}\))',
        # Pattern 4: Simple case names with citations (no comma required)
        r'([A-Z][A-Za-z\'\-\s\.]+)\s+([\dA-Za-z\.\s]+\(\d{4}\))',
    ]
    
    for i, pattern in enumerate(patterns):
        print(f"\n   Pattern {i+1}: {pattern}")
        matches = list(re.finditer(pattern, toa_section, re.MULTILINE))
        print(f"   Found {len(matches)} matches")
        
        for j, match in enumerate(matches[:3]):  # Show first 3
            case_name = match.group(1).strip()
            citation_text = match.group(2).strip()
            print(f"     {j+1}. Case: '{case_name}'")
            print(f"        Citation: '{citation_text}'")
    
    # Step 3: Test the parser's parse_toa_section_simple method
    print("\n3. TESTING PARSER'S PARSE METHOD...")
    try:
        entries = parser.parse_toa_section_simple(text)
        print(f"   Parser returned {len(entries)} entries")
        
        for i, entry in enumerate(entries[:5]):  # Show first 5
            print(f"     {i+1}. {entry.case_name}")
            print(f"        Citations: {entry.citations}")
            print(f"        Years: {entry.years}")
            
    except Exception as e:
        print(f"   ✗ Parser error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_toa_parsing()
