#!/usr/bin/env python3
"""
Debug TOA line parsing to see exact content and test patterns.
"""

import sys
import os
import re

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from toa_parser import ImprovedToAParser

def debug_toa_line():
    """Debug TOA line parsing step by step."""
    print("=" * 80)
    print("DEBUGGING TOA LINE PARSING")
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
    
    # Find TOA section
    toa_bounds = parser.detect_toa_section(text)
    if not toa_bounds:
        print("✗ No TOA section found")
        return
        
    start, end = toa_bounds
    toa_section = text[start:end]
    
    # Split into lines and examine specific lines
    lines = toa_section.split('\n')
    
    print(f"\nFound {len(lines)} lines in TOA section")
    
    # Look for lines with case names
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or len(line) < 20:
            continue
            
        # Check if line contains case name patterns
        if re.search(r'In\s+re\s+[A-Z]', line) or re.search(r'State\s+v\.', line) or re.search(r'[A-Z].*v\.', line):
            print(f"\nLine {i}: {line}")
            
            # Test case name extraction
            case_patterns = [
                r'(In\s+re\s+[A-Z][A-Za-z\'\-\s\.]+)',
                r'(State\s+v\.\s+[A-Z][A-Za-z\'\-\s\.]+)',
                r'([A-Z][A-Za-z\'\-\s\.]+? v\.? [A-Z][A-Za-z\'\-\s\.]+?)',
            ]
            
            case_name = None
            for pattern in case_patterns:
                match = re.search(pattern, line)
                if match:
                    case_name = match.group(1).strip()
                    print(f"  Case name: '{case_name}'")
                    break
            
            if case_name:
                # Test citation patterns
                citation_patterns = [
                    r'(\d+\s+Wn\.\s*\d+\s*[A-Za-z]+\s*\d+[^)]*\(\d{4}\))',
                    r'(\d+\s+Wn\.\s*App\.\s*\d+[^)]*\(\d{4}\))',
                    r'(\d+\s+[A-Za-z\.]+\s+\d+[^)]*\(\d{4}\))',
                ]
                
                for j, pattern in enumerate(citation_patterns):
                    match = re.search(pattern, line)
                    if match:
                        citation = match.group(1).strip()
                        print(f"  Citation pattern {j+1}: '{citation}'")
                    else:
                        print(f"  Citation pattern {j+1}: No match")
                
                # Show the full line for debugging
                print(f"  Full line: '{line}'")
                break

if __name__ == "__main__":
    debug_toa_line()
