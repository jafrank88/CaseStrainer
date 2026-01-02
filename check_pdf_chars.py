#!/usr/bin/env python3
"""Check for problematic characters in PDF text"""

import requests
import sys
sys.path.insert(0, 'src')

from src.optimized_pdf_processor import OptimizedPDFProcessor
import tempfile
import os

def check_problematic_chars():
    """Check for characters that might cause encoding issues"""
    
    pdf_url = "https://www.courts.wa.gov/opinions/pdf/863215.pdf"
    print(f"Downloading PDF from: {pdf_url}")
    
    try:
        response = requests.get(pdf_url, timeout=30, verify=False)
        response.raise_for_status()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(response.content)
            temp_path = temp_file.name
        
        try:
            processor = OptimizedPDFProcessor()
            result = processor.process_pdf(temp_path)
            text = result.text if result else ""
            
            print(f"Extracted {len(text)} characters")
            
            # Check first 100 characters for issues
            sample = text[:100]
            print(f"\nFirst 100 characters (repr):")
            print(repr(sample))
            
            # Look for non-ASCII characters
            non_ascii = []
            for i, char in enumerate(text[:1000]):
                if ord(char) > 127:
                    non_ascii.append((i, char, ord(char)))
            
            print(f"\nNon-ASCII characters in first 1000 chars:")
            for pos, char, code in non_ascii[:20]:
                print(f"  Position {pos}: '{char}' (U+{code:04X})")
            
            # Try to find the specific character causing issues
            print("\nChecking for specific problematic patterns...")
            
            # Check for zero-width characters
            zero_width = [i for i, c in enumerate(text) if ord(c) in [0x200B, 0x200C, 0x200D, 0xFEFF]]
            if zero_width:
                print(f"Found zero-width characters at positions: {zero_width[:10]}")
            
            # Check for special Unicode quotes
            smart_quotes = [i for i, c in enumerate(text) if ord(c) in [0x201C, 0x201D, 0x2018, 0x2019]]
            if smart_quotes:
                print(f"Found smart quotes at positions: {smart_quotes[:10]}")
            
            # Check for em-dash
            em_dash = [i for i, c in enumerate(text) if ord(c) in [0x2013, 0x2014]]
            if em_dash:
                print(f"Found em-dash at positions: {em_dash[:10]}")
                
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_problematic_chars()
