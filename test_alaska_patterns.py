#!/usr/bin/env python3
"""
Test Alaska citation patterns
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import re

def test_alaska_patterns():
    """Test Alaska citation patterns"""
    
    # Define the patterns
    patterns = {
        'alaska_aac': re.compile(r'\b(\d+)\s+AAC\s+(\d+)\b', re.IGNORECASE),
        'alaska_as': re.compile(r'\b(\d+)\s+AS\s+(\d+)\b', re.IGNORECASE),
        'alaska_slip': re.compile(r'\bNo\.\s+S-(\d{1,4})\s*\((\d{4})\)\b', re.IGNORECASE),
    }
    
    # Test text from the PDF
    test_text = """
    5 AAC 95 and 12 AS 16 are the relevant statutes.
    The case cites 11 AS 16 and 5 AAC 95 multiple times.
    See also No. S-19006 (2025) for the Supreme Court opinion.
    """
    
    print(f"Testing Alaska citation patterns...")
    print(f"Test text: {test_text.strip()}")
    
    for pattern_name, pattern in patterns.items():
        matches = list(pattern.finditer(test_text))
        print(f"\n{pattern_name}:")
        print(f"  Pattern: {pattern.pattern}")
        print(f"  Matches found: {len(matches)}")
        
        for match in matches:
            citation = match.group(0)
            print(f"  - {citation}")
    
    # Test with actual PDF content
    print(f"\n" + "="*50)
    print(f"Testing with actual PDF content...")
    
    from src.robust_pdf_extractor import RobustPDFExtractor
    
    pdf_path = r"D:\dev\casestrainer\sp-7788.pdf"
    extractor = RobustPDFExtractor()
    
    try:
        result = extractor.extract_text(pdf_path)
        if isinstance(result, tuple):
            text = result[0]
        else:
            text = result
            
        print(f"PDF text length: {len(text)} characters")
        
        for pattern_name, pattern in patterns.items():
            matches = list(pattern.finditer(text))
            print(f"\n{pattern_name} in PDF:")
            print(f"  Matches found: {len(matches)}")
            
            # Show unique matches
            unique_matches = list(set(match.group(0) for match in matches))
            for match in unique_matches[:10]:  # Show first 10
                print(f"  - {match}")
                
    except Exception as e:
        print(f"❌ Error processing PDF: {e}")

if __name__ == "__main__":
    test_alaska_patterns()
