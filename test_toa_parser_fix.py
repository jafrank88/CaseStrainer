#!/usr/bin/env python3
"""
Test the updated ToA parser with actual brief text.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from toa_parser import ToAParser

def test_toa_parser():
    """Test the ToA parser with a brief that has a ToA section."""
    
    # Use the text file we know has a ToA
    text_file = "wa_briefs_text/003_COA  Appellant Brief.txt"
    
    if not os.path.exists(text_file):
        print(f"Text file {text_file} not found")
        return
    
    # Read the text
    with open(text_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    print(f"Testing ToA parser with {len(text)} characters of text")
    
    # Test the ToA parser
    toa_parser = ToAParser()
    
    # Detect ToA section
    toa_section = toa_parser.detect_toa_section(text)
    
    if toa_section:
        start, end = toa_section
        print(f"Found ToA section at positions {start} to {end}")
        
        # Extract the ToA text
        toa_text = text[start:end]
        print(f"ToA text length: {len(toa_text)}")
        print(f"ToA text preview: {toa_text[:500]}...")
        
        # Parse ToA entries
        entries = toa_parser.parse_toa_section(toa_text)
        
        print(f"\nParsed {len(entries)} ToA entries:")
        for i, entry in enumerate(entries[:10]):  # Show first 10
            print(f"{i+1}. Case: {entry.case_name}")
            print(f"   Citations: {entry.citations}")
            print(f"   Years: {entry.years}")
            print(f"   Confidence: {entry.confidence}")
            print()
        
        if len(entries) > 10:
            print(f"... and {len(entries) - 10} more entries")
            
    else:
        print("No ToA section detected")
        
        # Let's search for the pattern manually
        import re
        pattern = r'(?:^|\n)\s*[ivx]+\s+TABLE\s+OF\s+AUTHORITIES?\s*'
        matches = re.findall(pattern, text, re.IGNORECASE)
        print(f"Manual search found {len(matches)} matches for pattern: {pattern}")
        
        # Show the context around "TABLE OF AUTHORITIES"
        toa_pos = text.find("TABLE OF AUTHORITIES")
        if toa_pos != -1:
            context_start = max(0, toa_pos - 50)
            context_end = min(len(text), toa_pos + 100)
            context = text[context_start:context_end]
            print(f"Context around 'TABLE OF AUTHORITIES': {context}")

if __name__ == "__main__":
    test_toa_parser() 