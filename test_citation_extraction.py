#!/usr/bin/env python3
"""Test citation extraction from PDF."""

from src.citation_extractor import CitationExtractor
from src.file_utils import extract_text_from_file

def test_citation_extraction():
    """Test citation extraction from the uploaded PDF."""
    print("=== TESTING CITATION EXTRACTION ===")
    
    # Extract text from PDF
    text, case_name = extract_text_from_file('/app/uploads/gov.uscourts.wyd.64014.141.0_1.pdf')
    print(f"Extracted {len(text)} characters of text")
    print(f"Case name: {case_name}")
    
    # Check for citation patterns in text
    import re
    print("\n=== CHECKING FOR CITATION PATTERNS ===")
    
    # F.3d patterns
    f3d_patterns = [
        r'\b\d+\s+F\.3d\s+\d+\b',
        r'\b\d+\s+F\.\s*3d\s+\d+\b',
        r'\b\d+\s+F\.\s*3rd\s+\d+\b',
    ]
    
    for pattern in f3d_patterns:
        matches = re.findall(pattern, text)
        print(f"Pattern '{pattern}': {len(matches)} matches")
        if matches:
            print(f"  Examples: {matches[:3]}")
    
    # WL patterns
    wl_patterns = [
        r'\b\d{4}\s+WL\s+\d+\b',
        r'\b\d{4}\s*WL\s*\d+\b',
    ]
    
    for pattern in wl_patterns:
        matches = re.findall(pattern, text)
        print(f"Pattern '{pattern}': {len(matches)} matches")
        if matches:
            print(f"  Examples: {matches[:3]}")
    
    # Use the citation extractor
    print("\n=== USING CITATION EXTRACTOR ===")
    extractor = CitationExtractor()
    citations = extractor.extract(text)
    print(f"Citation extractor found {len(citations)} citations")
    
    for i, citation in enumerate(citations[:10]):
        citation_text = citation.get('citation', citation.get('citation_text', 'Unknown'))
        print(f"  {i+1}. {citation_text}")
    
    # Show sample of text around F.3d and WL
    print("\n=== TEXT SAMPLES ===")
    f3d_pos = text.find('F.3d')
    if f3d_pos != -1:
        start = max(0, f3d_pos - 50)
        end = min(len(text), f3d_pos + 50)
        print(f"F.3d context: ...{text[start:end]}...")
    
    wl_pos = text.find('WL')
    if wl_pos != -1:
        start = max(0, wl_pos - 50)
        end = min(len(text), wl_pos + 50)
        print(f"WL context: ...{text[start:end]}...")

if __name__ == "__main__":
    test_citation_extraction() 