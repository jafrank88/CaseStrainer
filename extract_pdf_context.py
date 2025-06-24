#!/usr/bin/env python3
"""
Script to extract actual context around Westlaw citations from the PDF
"""

import sys
import os
import re
import PyPDF2

def extract_pdf_text(pdf_path):
    """Extract text from PDF file."""
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + " "
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def find_citation_context(text, citation, context_chars=500):
    """Find the context around a specific citation."""
    print(f"\nLooking for citation: {citation}")
    
    # Find all occurrences of the citation
    matches = list(re.finditer(re.escape(citation), text))
    
    if not matches:
        print(f"Citation '{citation}' not found in text")
        return None
    
    print(f"Found {len(matches)} occurrence(s)")
    
    for i, match in enumerate(matches):
        start_pos = match.start()
        end_pos = match.end()
        
        # Extract context
        context_start = max(0, start_pos - context_chars)
        context_end = min(len(text), end_pos + context_chars)
        
        context_before = text[context_start:start_pos]
        context_after = text[end_pos:context_end]
        
        print(f"\nOccurrence {i+1}:")
        print(f"Position: {start_pos}-{end_pos}")
        print(f"Context before ({len(context_before)} chars):")
        print(f"'{context_before}'")
        print(f"Citation: '{citation}'")
        print(f"Context after ({len(context_after)} chars):")
        print(f"'{context_after}'")
        print("-" * 80)
        
        return {
            'context_before': context_before,
            'context_after': context_after,
            'full_context': context_before + citation + context_after
        }

def main():
    pdf_path = "gov.uscourts.wyd.64014.141.0_1.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return
    
    print(f"Extracting text from: {pdf_path}")
    text = extract_pdf_text(pdf_path)
    
    if not text:
        print("Failed to extract text from PDF")
        return
    
    print(f"Extracted {len(text)} characters of text")
    
    # Test the failing citations
    test_citations = [
        "2006 WL 3801910",
        "2018 WL 2446162", 
        "2019 WL 2516279",
        "2017 WL 3461055",
        "2010 WL 4683851",
        "2011 WL 2160468",
        "2016 WL 165971",
        "2018 WL 3037217",
        "534 F.3d 1290"
    ]
    
    print("\n" + "=" * 80)
    print("EXTRACTING CONTEXT FOR FAILING CITATIONS")
    print("=" * 80)
    
    for citation in test_citations:
        context_data = find_citation_context(text, citation)
        if context_data:
            print(f"\nFull context for '{citation}':")
            print(f"'{context_data['full_context']}'")
        print("\n" + "=" * 80)

if __name__ == "__main__":
    main() 