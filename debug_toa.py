#!/usr/bin/env python3
"""
Debug the TOA parser to see what's happening.
"""

import sys
import os
import re

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from toa_parser import ImprovedToAParser

def debug_toa_detection():
    """Debug TOA detection step by step."""
    print("=" * 80)
    print("DEBUGGING TOA DETECTION")
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
    
    # Step 1: Check TOA section detection
    print("\n1. CHECKING TOA SECTION DETECTION...")
    
    # Look for TOA patterns manually
    toa_patterns = [
        r'TABLE\s+OF\s+AUTHORITIES',
        r'State\s+Cases',
        r'Federal\s+Cases'
    ]
    
    for pattern in toa_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            print(f"   Found '{pattern}' at position {match.start()}: '{text[match.start():match.start()+50]}...'")
    
    # Step 2: Check the actual TOA section
    print("\n2. CHECKING ACTUAL TOA SECTION...")
    
    # Look for the TOA section manually
    toa_start = text.find('TABLE OF AUTHORITIES')
    if toa_start != -1:
        print(f"   Found 'TABLE OF AUTHORITIES' at position {toa_start}")
        
        # Get the next 1000 characters to see the TOA content
        toa_section = text[toa_start:toa_start + 1000]
        print(f"   TOA section preview:")
        print(f"   {toa_section[:200]}...")
        
        # Look for case entries
        case_pattern = r'([A-Z][A-Za-z\'\-\s\.]+),?\s+([\dA-Za-z\.\s]+\(\d{4}\))'
        case_matches = re.finditer(case_pattern, toa_section)
        
        print(f"\n   Found case entries:")
        for i, match in enumerate(case_matches):
            if i < 10:  # Show first 10
                print(f"     {i+1}. {match.group(1)} -> {match.group(2)}")
    else:
        print("   ✗ 'TABLE OF AUTHORITIES' not found")
        
        # Try alternative search
        alt_patterns = ['State Cases', 'Federal Cases', 'Cases Cited']
        for pattern in alt_patterns:
            pos = text.find(pattern)
            if pos != -1:
                print(f"   Found '{pattern}' at position {pos}")
                print(f"   Preview: {text[pos:pos+100]}...")
    
    # Step 3: Test the parser's detect_toa_section method
    print("\n3. TESTING PARSER'S TOA DETECTION...")
    try:
        toa_bounds = parser.detect_toa_section(text)
        if toa_bounds:
            start, end = toa_bounds
            print(f"   Parser found TOA at {start}:{end}")
            print(f"   TOA content preview: {text[start:start+200]}...")
        else:
            print("   ✗ Parser returned no TOA bounds")
    except Exception as e:
        print(f"   ✗ Parser error: {e}")

if __name__ == "__main__":
    debug_toa_detection()
