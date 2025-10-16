#!/usr/bin/env python3
"""
Final attempt to extract text from the PDF using multiple methods.
"""

import fitz  # PyMuPDF
import PyPDF2
import io
import re

def try_pymupdf(pdf_path):
    """Try extracting text using PyMuPDF."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        return text.strip()
    except Exception as e:
        print(f"PyMuPDF error: {e}")
        return ""

def try_pypdf2(pdf_path):
    """Try extracting text using PyPDF2."""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
    except Exception as e:
        print(f"PyPDF2 error: {e}")
        return ""

def extract_citations(text):
    """Extract potential citations from text."""
    patterns = [
        r'\b\d+\s+Wn\.?\s*2d\s+\d+',
        r'\b\d+\s+P\.?\s*3d\s+\d+',
        r'\b\d+\s+U\.?S\.?\s+\d+',
        r'\b\d+\s+S\.?\s*Ct\.?\s+\d+',
        r'\b\d+\s+L\.?\s*Ed\.?\s*2d\s+\d+',
        r'\b\d+\s+Wash\.?\s*App\.?\s+\d+',
    ]
    
    citations = set()
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            citations.add(match)
    
    return sorted(citations)

def main():
    pdf_path = r"D:\dev\casestrainer\1033940.pdf"
    
    print(f"Extracting text from: {pdf_path}")
    
    # Try PyMuPDF first
    print("\n=== Trying PyMuPDF ===")
    text = try_pymupdf(pdf_path)
    if text:
        print(f"Extracted {len(text):,} characters")
        print("\nFirst 500 characters:")
        print("-" * 50)
        print(text[:500])
        print("-" * 50)
        
        citations = extract_citations(text)
        print("\nCitations found:")
        for i, citation in enumerate(citations, 1):
            print(f"{i}. {citation}")
    else:
        print("PyMuPDF extraction failed")
    
    # Try PyPDF2 as fallback
    print("\n=== Trying PyPDF2 ===")
    text = try_pypdf2(pdf_path)
    if text:
        print(f"Extracted {len(text):,} characters")
        print("\nFirst 500 characters:")
        print("-" * 50)
        print(text[:500])
        print("-" * 50)
        
        citations = extract_citations(text)
        print("\nCitations found:")
        for i, citation in enumerate(citations, 1):
            print(f"{i}. {citation}")
    else:
        print("PyPDF2 extraction failed")
    
    print("\n=== Analysis Complete ===")
    if not text:
        print("\nFailed to extract text. The PDF might be scanned or encrypted.")
        print("Try using OCR (Optical Character Recognition) software.")

if __name__ == "__main__":
    main()
