#!/usr/bin/env python3
"""
Simple test to extract PDF text and check for WL citations
"""

import sys
from pathlib import Path
import re
import os

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def extract_pdf_text_simple(pdf_path):
    """Extract text from PDF using available libraries."""
    
    # Try PyMuPDF first (most reliable)
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text() + "\n"
        doc.close()
        return text
    except ImportError:
        pass
    except Exception as e:
        print(f"PyMuPDF error: {e}")
    
    # Try pdfplumber
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except ImportError:
        pass
    except Exception as e:
        print(f"pdfplumber error: {e}")
    
    # Try PyPDF2
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
        return text
    except ImportError:
        pass
    except Exception as e:
        print(f"PyPDF2 error: {e}")
    
    return None

def main():
    pdf_path = r"D:\dev\casestrainer\gov.uscourts.wyd.64014.141.0_1.pdf"
    
    print("🔍 Simple WL Citation Test")
    print("=" * 50)
    print(f"File: {os.path.basename(pdf_path)}")
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return
    
    print(f"✅ File exists ({os.path.getsize(pdf_path)} bytes)")
    
    # Extract text
    text = extract_pdf_text_simple(pdf_path)
    
    if not text:
        print("❌ Could not extract text from PDF")
        return
    
    print(f"✅ Extracted {len(text)} characters")
    print()
    
    # Look for WL citations with multiple patterns
    wl_patterns = [
        r'\b\d{4}\s+WL\s+\d+\b',
        r'\b\d{4}\s+W\.L\.\s+\d+\b',
        r'\b\d{4}\s+Westlaw\s+\d+\b',
    ]
    
    found_any = False
    for i, pattern in enumerate(wl_patterns, 1):
        matches = re.findall(pattern, text, re.IGNORECASE)
        print(f"Pattern {i}: {pattern}")
        print(f"  Found: {len(matches)} matches")
        if matches:
            found_any = True
            for match in matches:
                print(f"    - {match}")
        print()
    
    # Show first few lines of text
    print("📄 First 10 lines of extracted text:")
    lines = text.splitlines()
    for i, line in enumerate(lines[:10]):
        if line.strip():
            print(f"  {i+1:2d}: {line.strip()}")
    print()
    
    # Look for any citation-like patterns
    citation_patterns = [
        r'\b\d+\s+[A-Z][a-z]*\.?\s*\d*d?\s+\d+\b',  # General citation pattern
        r'\b\d{4}\s+[A-Z]+\s+\d+\b',  # Year + abbreviation + number
        r'\bDoc\.\s*\d+\b',  # Document references
        r'\bRule\s+\d+\b',  # Rule references
    ]
    
    print("📋 Other citation-like patterns:")
    for pattern in citation_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            print(f"  {pattern}: {len(matches)} matches")
            for match in matches[:3]:
                print(f"    - {match}")
            if len(matches) > 3:
                print(f"    ... and {len(matches) - 3} more")
    print()
    
    # Final verdict
    if found_any:
        print("✅ WL citations FOUND in document!")
        print("   CaseStrainer should be detecting these.")
        print("   Need to investigate extraction pipeline.")
    else:
        print("❌ No WL citations found in document.")
        print("   This appears to be a procedural filing.")
        print("   Absence of WL citations is normal and expected.")
    
    # Show document type clues
    print("\n🔍 Document type analysis:")
    type_indicators = {
        'Motion in Limine': ['motion in limine', 'exclude', 'prejudicial', 'Rule 403'],
        'Brief': ['argument', 'precedent', 'authority', 'holding'],
        'Opinion': ['court finds', 'we hold', 'judgment', 'affirmed'],
        'Complaint': ['plaintiff', 'defendant', 'cause of action', 'damages'],
    }
    
    text_lower = text.lower()
    for doc_type, indicators in type_indicators.items():
        found_indicators = [ind for ind in indicators if ind in text_lower]
        if found_indicators:
            print(f"  {doc_type}: {len(found_indicators)}/{len(indicators)} indicators")
            print(f"    Found: {', '.join(found_indicators)}")

if __name__ == "__main__":
    main()
