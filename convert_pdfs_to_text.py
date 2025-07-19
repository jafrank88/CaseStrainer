#!/usr/bin/env python3
"""
Convert PDFs in wa_briefs folder to text files for inspection.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from document_processing_unified import extract_text_from_file

def convert_pdfs_to_text(briefs_dir: str = "wa_briefs", output_dir: str = "wa_briefs_text"):
    """
    Convert all PDFs in the briefs directory to text files.
    """
    briefs_path = Path(briefs_dir)
    output_path = Path(output_dir)
    
    if not briefs_path.exists():
        print(f"Briefs directory {briefs_dir} not found")
        return
    
    # Create output directory if it doesn't exist
    output_path.mkdir(exist_ok=True)
    
    pdf_files = list(briefs_path.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files to convert")
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"Converting {i}/{len(pdf_files)}: {pdf_file.name}")
        
        try:
            # Extract text from PDF
            text = extract_text_from_file(str(pdf_file))
            
            if not text:
                print(f"  No text extracted from {pdf_file.name}")
                continue
            
            # Create output filename
            text_filename = pdf_file.stem + ".txt"
            text_filepath = output_path / text_filename
            
            # Save text to file
            with open(text_filepath, 'w', encoding='utf-8') as f:
                f.write(text)
            
            print(f"  Saved {len(text)} characters to {text_filename}")
            
        except Exception as e:
            print(f"  Error converting {pdf_file.name}: {e}")
            continue
    
    print(f"\nConversion complete. Text files saved to {output_dir}/")

def search_for_toa_patterns(text_dir: str = "wa_briefs_text"):
    """
    Search through text files for common ToA patterns.
    """
    text_path = Path(text_dir)
    
    if not text_path.exists():
        print(f"Text directory {text_dir} not found")
        return
    
    # Common ToA patterns to search for
    toa_patterns = [
        r'TABLE\s+OF\s+AUTHORITIES',
        r'AUTHORITIES\s+CITED',
        r'CITED\s+AUTHORITIES',
        r'CASES\s+CITED',
        r'LEGAL\s+AUTHORITIES',
        r'CASE\s+AUTHORITIES',
        r'CITED\s+CASES'
    ]
    
    import re
    
    text_files = list(text_path.glob("*.txt"))
    print(f"Searching {len(text_files)} text files for ToA patterns...")
    
    found_files = []
    
    for text_file in text_files:
        try:
            with open(text_file, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Search for patterns
            for pattern in toa_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    found_files.append((text_file.name, pattern, len(matches)))
                    print(f"Found '{pattern}' in {text_file.name} ({len(matches)} matches)")
                    break
                    
        except Exception as e:
            print(f"Error reading {text_file.name}: {e}")
            continue
    
    if found_files:
        print(f"\nFound ToA patterns in {len(found_files)} files:")
        for filename, pattern, count in found_files:
            print(f"  {filename}: {pattern} ({count} matches)")
    else:
        print("\nNo ToA patterns found in any files.")

def main():
    """Main function."""
    print("Converting PDFs to text...")
    convert_pdfs_to_text()
    
    print("\nSearching for ToA patterns...")
    search_for_toa_patterns()

if __name__ == "__main__":
    main() 