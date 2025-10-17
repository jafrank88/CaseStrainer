#!/usr/bin/env python3
"""Test PDF extraction speed with different libraries"""
import time
import sys
from src.robust_pdf_extractor import RobustPDFExtractor

pdf_file = "1034300.pdf"

# Test with robust extractor (tries all methods)
print("="*60)
print("Testing PDF Extraction Speed")
print("="*60)

extractor = RobustPDFExtractor(verbose=True)
print(f"\nAvailable libraries: {extractor.available_libraries}")

start = time.time()
text, library_used = extractor.extract_text(pdf_file)
elapsed = time.time() - start

print("\n" + "="*60)
print(f"✅ RESULT:")
print(f"  Library used: {library_used}")
print(f"  Time: {elapsed:.1f} seconds")
print(f"  Text extracted: {len(text):,} characters")
print(f"  Speed: {len(text)/elapsed:,.0f} chars/sec")
print("="*60)

# Test individual libraries
print("\n" + "="*60)
print("Individual Library Benchmarks:")
print("="*60)

for lib in extractor.available_libraries:
    try:
        print(f"\nTesting {lib}...")
        start = time.time()
        
        if lib == 'fitz':
            text = extractor._extract_fitz(pdf_file, None)
        elif lib == 'pdfminer':
            text = extractor._extract_pdfminer(pdf_file, None)
        elif lib == 'pdfplumber':
            text = extractor._extract_pdfplumber(pdf_file, None)
        elif lib == 'pypdf':
            text = extractor._extract_pypdf(pdf_file, None)
        elif lib == 'PyPDF2':
            text = extractor._extract_pypdf2(pdf_file, None)
        
        elapsed = time.time() - start
        print(f"  ✅ {lib}: {elapsed:.1f}s, {len(text):,} chars ({len(text)/elapsed:,.0f} chars/sec)")
    except Exception as e:
        print(f"  ❌ {lib}: Failed - {e}")

print("\n" + "="*60)
