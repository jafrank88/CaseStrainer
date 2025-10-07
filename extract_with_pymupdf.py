#!/usr/bin/env python3
"""
Extract and analyze text from a PDF using PyMuPDF.
"""

import fitz  # PyMuPDF
import re

def extract_text_with_pymupdf(pdf_path: str) -> str:
    """Extract text from a PDF using PyMuPDF."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text with PyMuPDF: {e}")
        return ""

def analyze_text(text: str):
    """Analyze the extracted text for case names and citations."""
    print("\n=== TEXT ANALYSIS ===")
    
    # Print first 500 characters
    print("\nFirst 500 characters:")
    print("-" * 50)
    print(text[:500])
    print("-" * 50)
    
    # Look for case names
    print("\nPotential Case Names:")
    case_patterns = [
        r'([A-Z][a-zA-Z\s\,\&\']+\sv\.\s+[A-Z][a-zA-Z\s\,\&\']+)',
        r'In\s+re\s+([A-Z][a-zA-Z\s\,\&\']+)',
        r'Ex\s+parte\s+([A-Z][a-zA-Z\s\,\&\']+)',
    ]
    
    case_names = set()
    for pattern in case_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
        for match in matches:
            case_name = match.group(0).strip()
            # Clean up the case name
            case_name = re.sub(r'\s+', ' ', case_name)
            if len(case_name) > 10 and len(case_name) < 200:  # Reasonable length
                case_names.add(case_name)
    
    for i, name in enumerate(sorted(case_names)[:20], 1):  # Show first 20
        print(f"{i}. {name}")
    
    # Look for citations
    print("\nCitations Found:")
    citation_patterns = [
        r'\b\d+\s+Wn\.?\s*2d\s+\d+',
        r'\b\d+\s+P\.?\s*3d\s+\d+',
        r'\b\d+\s+U\.?S\.?\s+\d+',
        r'\b\d+\s+S\.?\s*Ct\.?\s+\d+',
        r'\b\d+\s+L\.?\s*Ed\.?\s*2d\s+\d+',
        r'\b\d+\s+Wash\.?\s*App\.?\s+\d+',
        r'\b\d+\s+Wash\.?\s*2d\s+\d+',
        r'\b\d+\s+P\.?\s*2d\s+\d+',
    ]
    
    citations = set()
    for pattern in citation_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            citations.add(match)
    
    for i, citation in enumerate(sorted(citations), 1):
        print(f"{i}. {citation}")
    
    # Try to find case names near citations
    if case_names and citations:
        print("\nPossible Case Name and Citation Matches:")
        for case in sorted(case_names)[:10]:  # Limit to first 10 cases
            case_clean = re.escape(case)
            # Look for citations within 100 characters of the case name
            for match in re.finditer(case_clean, text):
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context = text[start:end]
                
                # Check for citations in this context
                for citation in citations:
                    if citation in context:
                        # Clean up the context for display
                        context_display = context.replace('\n', ' ').strip()
                        print(f"\nCase: {case}")
                        print(f"Citation: {citation}")
                        print(f"Context: ...{context_display}...")
                        break  # Only show first citation per case
                break  # Only show first occurrence of each case

def main():
    pdf_path = r"D:\dev\casestrainer\1033940.pdf"
    print(f"Extracting text from: {pdf_path}")
    
    text = extract_text_with_pymupdf(pdf_path)
    if not text:
        print("No text could be extracted.")
        return
    
    print(f"Extracted {len(text):,} characters of text.")
    analyze_text(text)

if __name__ == "__main__":
    main()
