#!/usr/bin/env python
"""Test PDF text extraction from the actual file"""
import sys
sys.path.insert(0, 'd:/dev/casestrainer')

# Try all three PDF extraction methods
def test_pypdf2(pdf_path):
    """Test PyPDF2 extraction"""
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        return f"ERROR: {e}"

def test_pdfminer(pdf_path):
    """Test pdfminer extraction"""
    try:
        from pdfminer.high_level import extract_text
        return extract_text(pdf_path)
    except Exception as e:
        return f"ERROR: {e}"

def test_pdfplumber(pdf_path):
    """Test pdfplumber extraction"""
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        return f"ERROR: {e}"

pdf_path = r"D:\dev\casestrainer\1034300.pdf"
print(f"Testing PDF extraction: {pdf_path}")
print("=" * 60)

methods = [
    ("PyPDF2", test_pypdf2),
    ("pdfminer", test_pdfminer),
    ("pdfplumber", test_pdfplumber)
]

for name, func in methods:
    print(f"\n🔍 Testing {name}:")
    result = func(pdf_path)
    if isinstance(result, str) and not result.startswith("ERROR"):
        print(f"  ✅ Extracted: {len(result)} characters")
        print(f"  First 200 chars: {result[:200]}")
        # Count citation-like patterns
        import re
        citations = re.findall(r'\d+\s+(?:Wn\.2d|P\.3d|U\.S\.)\s+\d+', result)
        print(f"  Found {len(citations)} citation patterns")
    else:
        print(f"  ❌ {result}")
