#!/usr/bin/env python3
"""
Debug script to examine ToA section boundaries and see what's being detected.
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from toa_parser import ToAParser

BRIEF_TEXT_FILE = "wa_briefs_text/003_COA  Appellant Brief.txt"

def main():
    if not os.path.exists(BRIEF_TEXT_FILE):
        print(f"Text file {BRIEF_TEXT_FILE} not found")
        return

    with open(BRIEF_TEXT_FILE, 'r', encoding='utf-8') as f:
        text = f.read()

    print(f"Total text length: {len(text)} characters")
    
    # --- 1. Find "TABLE OF AUTHORITIES" manually ---
    toa_pos = text.find("TABLE OF AUTHORITIES")
    print(f"Manual search for 'TABLE OF AUTHORITIES': position {toa_pos}")
    
    if toa_pos != -1:
        print(f"Context around position {toa_pos}:")
        start = max(0, toa_pos - 100)
        end = min(len(text), toa_pos + 200)
        print(text[start:end])
    
    # --- 2. Test ToA parser detection ---
    toa_parser = ToAParser()
    toa_section = toa_parser.detect_toa_section(text)
    
    if toa_section:
        start, end = toa_section
        print(f"\nToA parser detected section: {start} to {end}")
        print(f"ToA section length: {end - start}")
        
        # Show what's being detected as ToA
        print(f"\nToA section preview (first 500 chars):")
        print("=" * 80)
        print(text[start:start+500])
        print("=" * 80)
        
        # Show what comes after the detected ToA
        print(f"\nText after ToA (first 500 chars):")
        print("=" * 80)
        print(text[end:end+500])
        print("=" * 80)
        
        # Check if there's more content after the ToA
        remaining_text = text[end:]
        print(f"\nRemaining text after ToA: {len(remaining_text)} characters")
        
        # Look for citations in the remaining text
        import re
        pattern = r'\d+\s+[A-Za-z\.\s]+\d+\s*\(\d{4}\)'
        matches = re.findall(pattern, remaining_text)
        print(f"Citations found in remaining text: {len(matches)}")
        if matches:
            print(f"  Examples: {matches[:5]}")
    
    # --- 3. Look for the actual argument section ---
    print(f"\nLooking for argument section...")
    argument_patterns = [
        r'III\.ARGUMENT',
        r'ARGUMENT',
        r'I\.ASSIGNMENT OF ERRORS',
        r'II\.STATEMENT OF FACTS'
    ]
    
    for pattern in argument_patterns:
        match = re.search(pattern, text)
        if match:
            print(f"Found '{pattern}' at position {match.start()}")
            # Show context
            start = max(0, match.start() - 50)
            end = min(len(text), match.start() + 200)
            print(f"Context: {text[start:end]}")

if __name__ == "__main__":
    main() 