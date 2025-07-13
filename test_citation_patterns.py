#!/usr/bin/env python3
"""
Test to check if citation patterns can find the citation in the text
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from document_processing_unified import UnifiedDocumentProcessor
import re

PDF_PATH = r'D:\dev\casestrainer\gov.uscourts.wyd.64014.141.0_1.pdf'

patterns = [
    (r'\d+\s+Wn\.?\s*(?:2d|3d)?\s*\d+', 'Washington Reporter'),
    (r'\d+\s+P\.?\s*(?:2d|3d)?\s*\d+', 'Pacific Reporter'),
    (r'\d+\s+U\.S\.\s*\d+', 'U.S. Supreme Court'),
    (r'\d+\s+S\.\s*Ct\.\s*\d+', 'Supreme Court Reporter'),
    (r'\d+\s+F\.?\s*(?:2d|3d)?\s*\d+', 'Federal Reporter'),
    (r'\d+\s+F\.\s*Supp\.?\s*\d+', 'Federal Supplement'),
]

def main():
    processor = UnifiedDocumentProcessor()
    print(f"Extracting text from: {PDF_PATH}")
    text = processor.extract_text_from_file(PDF_PATH)
    print(f"Extracted {len(text)} characters\n")

    for pattern, label in patterns:
        matches = re.findall(pattern, text)
        print(f"{label} ({pattern}): {len(matches)} matches")
        if matches:
            print(f"  Sample: {matches[:3]}")
    print("\nRunning citation extractor...\n")
    result = processor.process_document(file_path=PDF_PATH, extract_case_names=True, debug_mode=True)
    citations = result.get('citations', [])
    print(f"Citation extractor found {len(citations)} citations.")
    if citations:
        for i, citation in enumerate(citations[:5]):
            print(f"Citation {i+1}: {citation}")

if __name__ == "__main__":
    main() 