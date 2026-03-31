#!/usr/bin/env python3
"""Check the context around '554 U.S. 724' citation in the PDF."""
import re
import sys
import os

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    try:
        import PyPDF2
        HAS_PYPDF2 = True
    except ImportError:
        HAS_PYPDF2 = False

def extract_text_pymupdf(pdf_path):
    """Extract text using PyMuPDF (same as backend)."""
    doc = fitz.open(pdf_path)
    text_parts = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        rect = page.rect
        width, height = rect.width, rect.height
        # Same clipping as backend
        text_area = fitz.Rect(0, 65, width, height - 50)
        text = page.get_text("text", clip=text_area)
        if text.strip():
            text_parts.append(text)
    doc.close()
    
    full_text = "\n".join(text_parts)
    # Normalize like backend
    normalized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", full_text)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()

def extract_text_pypdf2(pdf_path):
    """Extract text using PyPDF2 (fallback)."""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        full_text = " ".join(text_parts)
        normalized = re.sub(r"\s+", " ", full_text)
        return normalized.strip()

def find_citation_context(text, citation_pattern, context_chars=500):
    """Find all occurrences of citation and show context."""
    matches = list(re.finditer(citation_pattern, text, re.IGNORECASE))
    
    if not matches:
        print(f"[ERROR] Citation pattern '{citation_pattern}' not found in document")
        return
    
    print(f"[OK] Found {len(matches)} occurrence(s) of '{citation_pattern}'\n")
    
    for i, match in enumerate(matches, 1):
        start = match.start()
        end = match.end()
        
        context_start = max(0, start - context_chars)
        context_end = min(len(text), end + context_chars)
        context = text[context_start:context_end]
        
        # Highlight the citation
        citation_start_in_context = start - context_start
        citation_end_in_context = end - context_start
        
        before = context[:citation_start_in_context]
        citation_text = context[citation_start_in_context:citation_end_in_context]
        after = context[citation_end_in_context:]
        
        print("=" * 100)
        print(f"OCCURRENCE {i} (position {start}-{end})")
        print("=" * 100)
        print(f"\nBEFORE: ...{before[-200:]}")
        print(f"\n{'CITATION:':<12} [{citation_text}]")
        print(f"\nAFTER:  {after[:300]}...")
        
        # Look for "2020" in context
        if "2020" in context:
            print(f"\n[WARNING] FOUND '2020' IN CONTEXT!")
            year_matches = list(re.finditer(r'\b2020\b', context))
            for ym in year_matches:
                year_pos = ym.start()
                year_context_start = max(0, year_pos - 150)
                year_context_end = min(len(context), year_pos + 150)
                year_context = context[year_context_start:year_context_end]
                print(f"   Position of '2020': {context_start + year_pos}")
                print(f"   Distance from citation start: {start - (context_start + year_pos)} chars")
                print(f"   Distance from citation end: {(context_start + year_pos) - end} chars")
                print(f"   Context around '2020': ...{year_context}...")
                
                # Check if "2020" is part of a case name pattern
                if "Davis" in year_context or "Federal Election" in year_context:
                    print(f"   [CRITICAL] '2020' appears near 'Davis' or 'Federal Election'!")
                    # Check if there's a pattern like "Davis v. Federal Election Comm'n, 2020"
                    davis_2020_pattern = re.search(r'Davis[^,]*Federal[^,]*Election[^,]*,\s*2020', year_context, re.IGNORECASE)
                    if davis_2020_pattern:
                        print(f"   [CRITICAL] Found pattern match: '{davis_2020_pattern.group()}'")
        
        # Look for "Davis" in context
        if "Davis" in context or "davis" in context.lower():
            davis_matches = list(re.finditer(r'\b[Dd]avis\b', context))
            for dm in davis_matches:
                davis_pos = dm.start()
                davis_context_start = max(0, davis_pos - 150)
                davis_context_end = min(len(context), davis_pos + 150)
                davis_context = context[davis_context_start:davis_context_end]
                print(f"\n   Found 'Davis' at position {context_start + davis_pos}")
                print(f"   Context: ...{davis_context}...")
        
        # Look for "Federal Election" in context
        if "Federal Election" in context or "federal election" in context.lower():
            fe_matches = list(re.finditer(r'\b[Ff]ederal\s+[Ee]lection\b', context))
            for fe in fe_matches:
                fe_pos = fe.start()
                fe_context_start = max(0, fe_pos - 150)
                fe_context_end = min(len(context), fe_pos + 200)
                fe_context = context[fe_context_start:fe_context_end]
                print(f"\n   Found 'Federal Election' at position {context_start + fe_pos}")
                print(f"   Context: ...{fe_context}...")
        
        print("\n" + "=" * 100 + "\n")

def main():
    pdf_path = r"D:\dev\casestrainer\20-297_4g25.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"[ERROR] PDF file not found: {pdf_path}")
        print("\nTrying to find PDF files with '20-297' in name...")
        import glob
        matches = glob.glob("**/*20-297*.pdf", recursive=True)
        if matches:
            print(f"Found: {matches[0]}")
            pdf_path = matches[0]
        else:
            print("No matching PDF found")
            return
    
    print(f"Extracting text from: {os.path.basename(pdf_path)}\n")
    
    # Try PyMuPDF first (same as backend), then PyPDF2
    if HAS_PYMUPDF:
        print("Using PyMuPDF (same as backend)...")
        text = extract_text_pymupdf(pdf_path)
    elif HAS_PYPDF2:
        print("Using PyPDF2 (fallback)...")
        text = extract_text_pypdf2(pdf_path)
    else:
        print("[ERROR] Neither PyMuPDF nor PyPDF2 available")
        return
    
    print(f"[OK] Extracted {len(text)} characters of text\n")
    
    # Look for the citation
    citation_patterns = [
        r"554\s+U\.?\s*S\.?\s+724",  # Standard format
        r"554\s+U\.S\.\s+724",        # With periods
        r"554\s+U\s+S\s+724",         # Without periods
    ]
    
    for pattern in citation_patterns:
        find_citation_context(text, pattern, context_chars=500)
        break  # Just check first pattern

if __name__ == "__main__":
    main()
