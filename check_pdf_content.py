#!/usr/bin/env python3
"""Check the PDF content to see if it has citations"""

import requests
import io

try:
    import pypdf
except ImportError:
    import PyPDF2 as pypdf

# Download PDF
pdf_url = "https://www.courts.wa.gov/opinions/pdf/863215.pdf"
print(f"Downloading PDF from: {pdf_url}")

pdf_response = requests.get(pdf_url, timeout=30, verify=False)
if pdf_response.status_code == 200:
    # Extract text
    pdf_file = io.BytesIO(pdf_response.content)
    pdf_reader = pypdf.PdfReader(pdf_file)
    
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    
    print(f"\nFirst 2000 characters of PDF:")
    print("=" * 80)
    print(text[:2000])
    print("=" * 80)
    
    # Check for citation patterns
    import re
    
    # Look for U.S. citations
    us_citations = re.findall(r'\d+\s+U\.S\.\s+\d+', text)
    print(f"\nFound {len(us_citations)} U.S. citations:")
    for cit in us_citations[:5]:
        print(f"  - {cit}")
    
    # Look for F.3d citations
    f3d_citations = re.findall(r'\d+\s+F\.\d+d\s+\d+', text)
    print(f"\nFound {len(f3d_citations)} F.3d citations:")
    for cit in f3d_citations[:5]:
        print(f"  - {cit}")
    
    # Look for Wn.2d citations
    wn2d_citations = re.findall(r'\d+\s+Wn\.?\d*d\s+\d+', text)
    print(f"\nFound {len(wn2d_citations)} Wn.2d citations:")
    for cit in wn2d_citations[:5]:
        print(f"  - {cit}")
    
    # Look for "v." patterns
    v_patterns = re.findall(r'\b[\w\s,\.]+ v\. [\w\s,\.]+', text[:5000])
    print(f"\nFound {len(v_patterns)} 'v.' patterns in first 5000 chars:")
    for pat in v_patterns[:5]:
        print(f"  - {pat.strip()}")
else:
    print(f"Failed to download PDF: {pdf_response.status_code}")
