#!/usr/bin/env python3
"""Test script to verify Westlaw citation extraction with updated patterns."""

import re
import PyPDF2
from src.unified_citation_processor import UnifiedCitationProcessor

def test_westlaw_extraction():
    """Test Westlaw citation extraction from the PDF."""
    
    # Read the PDF
    print("Reading PDF...")
    reader = PyPDF2.PdfReader('gov.uscourts.wyd.64014.141.0_1.pdf')
    text = ""
    for page in reader.pages[:3]:  # First 3 pages
        text += page.extract_text()
    
    print(f"Extracted {len(text)} characters of text")
    
    # Test regex pattern directly
    print("\nTesting regex pattern directly...")
    wl_pattern = r'\b\d{4}\s+WL\s+\d{1,12}\b'
    wl_matches = re.findall(wl_pattern, text)
    print(f"Found {len(wl_matches)} Westlaw citations with regex:")
    for match in wl_matches[:5]:
        print(f"  {match}")
    
    # Test with UnifiedCitationProcessor
    print("\nTesting with UnifiedCitationProcessor...")
    processor = UnifiedCitationProcessor()
    results = processor.process_text(text)  # Use the correct method name
    
    wl_results = [r for r in results if 'WL' in r['citation']]
    print(f"Found {len(wl_results)} Westlaw citations with processor:")
    for result in wl_results[:5]:
        print(f"  {result['citation']}")
    
    # Test volume and page number patterns
    print("\nTesting volume and page number patterns...")
    test_citations = [
        "12345 F.3d 123456789012",  # 5-digit volume, 12-digit page
        "1234 U.S. 123456789012",   # 4-digit volume, 12-digit page
        "2020 WL 123456789012",     # Westlaw with 12-digit number
        "2020 WL 1234567",          # Westlaw with 7-digit number
    ]
    
    for citation in test_citations:
        # Test various patterns
        patterns = [
            r'\b\d{1,5}\s+F\.3d\s+\d{1,12}\b',
            r'\b\d{1,5}\s+U\.\s*S\.\s+\d{1,12}\b',
            r'\b\d{4}\s+WL\s+\d{1,12}\b',
        ]
        
        for pattern in patterns:
            if re.match(pattern, citation):
                print(f"  ✓ {citation} matches {pattern}")
                break
        else:
            print(f"  ✗ {citation} doesn't match any pattern")

if __name__ == "__main__":
    test_westlaw_extraction() 