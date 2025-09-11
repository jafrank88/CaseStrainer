#!/usr/bin/env python3
"""
Test citation patterns to see what's actually in the TOA section.
"""

import sys
import os
import re

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from toa_parser import ImprovedToAParser

def test_citation_patterns():
    """Test citation patterns step by step."""
    print("=" * 80)
    print("TESTING CITATION PATTERNS")
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
    
    print(f"\nTOA section length: {len(toa_section):,} characters")
    print(f"TOA preview: {toa_section[:500]}...")
    
    # Test different citation patterns
    patterns = [
        # Pattern 1: Washington Supreme Court
        (r'\d+\s+Wn\.\s*\d+\s*[A-Za-z]+\s*\d+[^)]*\(\d{4}\)', "Washington Supreme Court"),
        # Pattern 2: Washington Court of Appeals  
        (r'\d+\s+Wn\.\s*App\.\s*\d+[^)]*\(\d{4}\)', "Washington Court of Appeals"),
        # Pattern 3: Pacific Reporter
        (r'\d+\s+P\.\s*\d+\s*\d+[^)]*\(\d{4}\)', "Pacific Reporter"),
        # Pattern 4: General pattern
        (r'\d+\s+[A-Za-z\.]+\s+\d+[^)]*\(\d{4}\)', "General"),
    ]
    
    for pattern, description in patterns:
        print(f"\nTesting {description} pattern: {pattern}")
        matches = list(re.finditer(pattern, toa_section))
        print(f"Found {len(matches)} matches")
        
        for i, match in enumerate(matches[:3]):  # Show first 3
            citation = match.group(0)
            print(f"  {i+1}. {citation}")
            
            # Show context around the citation
            start_pos = max(0, match.start() - 50)
            end_pos = min(len(toa_section), match.end() + 50)
            context = toa_section[start_pos:end_pos]
            print(f"     Context: ...{context}...")

if __name__ == "__main__":
    test_citation_patterns()
