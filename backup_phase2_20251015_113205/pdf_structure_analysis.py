#!/usr/bin/env python3
"""
Analyze the structure of a PDF file to understand its content.
"""

import fitz  # PyMuPDF
import sys

def analyze_pdf_structure(pdf_path):
    """Analyze the structure of a PDF file."""
    print(f"Analyzing PDF structure: {pdf_path}")
    
    try:
        doc = fitz.open(pdf_path)
        print(f"\nDocument Information:")
        print(f"  - Pages: {len(doc)}")
        print(f"  - Metadata: {doc.metadata}")
        
        # Analyze each page
        for page_num in range(min(3, len(doc))):  # First 3 pages
            page = doc[page_num]
            print(f"\n=== Page {page_num + 1} ===")
            
            # Get text blocks
            blocks = page.get_text("dict", sort=True)["blocks"]
            print(f"  - Contains {len(blocks)} text blocks")
            
            # Show first few blocks
            for i, block in enumerate(blocks[:5]):  # First 5 blocks
                if "lines" in block:
                    text = " ".join("".join(span["text"] for span in line["spans"]) 
                                  for line in block["lines"])
                    text = text[:200] + ("..." if len(text) > 200 else "")
                    print(f"\n  Block {i+1} (type: {block.get('type', '?')}):")
                    print(f"    {text}")
            
            # Extract all text as a fallback
            text = page.get_text()
            if text.strip():
                print("\n  Raw text (first 500 chars):")
                print("  " + "\n  ".join(text[:500].split("\n")) + "...")
            
    except Exception as e:
        print(f"Error analyzing PDF: {e}")
        return False
    
    return True

def main():
    pdf_path = r"D:\dev\casestrainer\1033940.pdf"
    if not analyze_pdf_structure(pdf_path):
        print("\nTrying alternative extraction method...")
        try:
            # Try a different extraction method
            doc = fitz.open(pdf_path)
            print("\nExtracted text (alternative method):")
            for page_num in range(min(3, len(doc))):  # First 3 pages
                page = doc[page_num]
                text = page.get_text("text")
                print(f"\n=== Page {page_num + 1} ===")
                print(text[:1000] + ("..." if len(text) > 1000 else ""))
        except Exception as e:
            print(f"Alternative extraction failed: {e}")

if __name__ == "__main__":
    main()
