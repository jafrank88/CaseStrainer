#!/usr/bin/env python3
"""
Simple check for WL citations in PDF
"""

import re
import os

def extract_with_fitz(pdf_path):
    """Extract text using PyMuPDF."""
    try:
        import fitz
        doc = fitz.open(pdf_path)
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text() + "\n"
        doc.close()
        return text
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    pdf_path = r"D:\dev\casestrainer\gov.uscourts.wyd.64014.141.0_1.pdf"
    
    print("Checking for WL citations...")
    
    if not os.path.exists(pdf_path):
        print("File not found!")
        return
    
    text = extract_with_fitz(pdf_path)
    if not text:
        print("Could not extract text")
        return
    
    print(f"Extracted {len(text)} characters")
    
    # Look for WL citations
    wl_pattern = r'\b\d{4}\s+WL\s+\d+\b'
    matches = re.findall(wl_pattern, text, re.IGNORECASE)
    
    print(f"WL citations found: {len(matches)}")
    
    if matches:
        print("Found WL citations:")
        for i, match in enumerate(matches, 1):
            print(f"  {i}. {match}")
            
            # Show context
            pos = text.find(match)
            if pos != -1:
                start = max(0, pos - 50)
                end = min(len(text), pos + len(match) + 50)
                context = text[start:end].replace('\n', ' ')
                print(f"     Context: {context}")
            print()
    else:
        print("No WL citations found.")
        
        # Show some sample text to verify extraction worked
        print("\nSample text (first 500 chars):")
        print(text[:500])
        
        # Look for other citation patterns
        other_patterns = [
            (r'\bDoc\.\s*\d+\b', 'Document references'),
            (r'\bRule\s+\d+\b', 'Rule references'),
            (r'\b\d+\s+F\.\d*d?\s+\d+\b', 'Federal Reporter'),
        ]
        
        print("\nOther patterns found:")
        for pattern, name in other_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            print(f"  {name}: {len(matches)} matches")
            if matches:
                for match in matches[:3]:
                    print(f"    - {match}")

if __name__ == "__main__":
    main()
