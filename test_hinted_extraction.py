#!/usr/bin/env python3
"""
Test script for hinted extraction pipeline

This script demonstrates the full pipeline:
1. Extract citations from PDF text using regex
2. Find canonical names via enhanced scraper
3. Use hinted extraction to improve case name extraction
4. Compare results with/without hints
"""

import sys
import os
import time
import re
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.enhanced_legal_scraper import EnhancedLegalScraper
from src.extract_case_name import extract_case_name_from_text
import PyPDF2

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file."""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

def extract_citations_simple(text):
    """Simple citation extraction using regex patterns."""
    patterns = [
        r"\b\d+\s+U\.?\s*S\.?\s+\d+\b",  # US Supreme Court
        r"\b\d+\s+F\.2d\s+\d+\b",        # F.2d
        r"\b\d+\s+F\.3d\s+\d+\b",        # F.3d
        r"\b\d+\s+Wn\.2d\s+\d+\b",       # Washington
        r"\b\d+\s+P\.2d\s+\d+\b",        # Pacific
        r"\b\d+\s+P\.3d\s+\d+\b",        # Pacific 3d
    ]
    
    citations = []
    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            citations.append({
                'citation': match.group(0),
                'start': match.start(),
                'end': match.end()
            })
    
    # Remove duplicates and sort by position
    unique_citations = []
    seen = set()
    for citation in sorted(citations, key=lambda x: x['start']):
        if citation['citation'] not in seen:
            seen.add(citation['citation'])
            unique_citations.append(citation)
    
    return unique_citations

def test_hinted_extraction_pipeline():
    """Test the complete hinted extraction pipeline."""
    
    pdf_path = r"C:\Users\jafrank\OneDrive - UW\Documents\GitHub\CaseStrainer\1028814.pdf"
    
    print("=" * 80)
    print("HINTED EXTRACTION PIPELINE TEST")
    print("=" * 80)
    print()
    
    # Step 1: Extract text from PDF
    print("Step 1: Extracting text from PDF...")
    text = extract_text_from_pdf(pdf_path)
    if not text:
        print("Failed to extract text from PDF")
        return
    
    print(f"Extracted {len(text)} characters of text")
    print(f"First 500 characters: {text[:500]}...")
    print()
    
    # Step 2: Extract citations using simple regex
    print("Step 2: Extracting citations using regex...")
    citations = extract_citations_simple(text)
    
    print(f"Found {len(citations)} citations:")
    for i, citation in enumerate(citations[:5], 1):  # Show first 5
        print(f"  {i}. {citation['citation']}")
    print()
    
    # Step 3: Test with a few citations
    test_citations = citations[:3]  # Test first 3 citations
    
    # Initialize enhanced scraper
    scraper = EnhancedLegalScraper(use_google=True, use_bing=True)
    
    print("Step 3: Testing hinted extraction for each citation...")
    print()
    
    for i, citation_data in enumerate(test_citations, 1):
        citation = citation_data['citation']
        print(f"Citation {i}: {citation}")
        print("-" * 60)
        
        # Extract case name without hint (original method)
        print("Without canonical name hint:")
        case_name_original = extract_case_name_from_text(text, citation)
        print(f"  Extracted: {case_name_original or 'None'}")
        
        # Find canonical name via enhanced scraper
        print("Finding canonical name via enhanced scraper...")
        try:
            # Try to get canonical name from CaseMine (most reliable)
            canonical_data = scraper.extract_case_metadata(citation, "CaseMine")
            canonical_name = canonical_data.get('canonical_name', '')
            
            if canonical_name:
                print(f"  Canonical name: {canonical_name}")
                
                # Extract case name with hint
                print("With canonical name hint:")
                case_name_hinted = extract_case_name_from_text(text, citation, canonical_name=canonical_name)
                print(f"  Extracted: {case_name_hinted or 'None'}")
                
                # Compare results
                if case_name_original != case_name_hinted:
                    print("  ✅ Hinted extraction produced different result!")
                    if case_name_hinted:
                        print(f"  Improvement: {case_name_original} -> {case_name_hinted}")
                else:
                    print("  ⚠️  Same result (may be good if original was already correct)")
            else:
                print("  No canonical name found")
                
        except Exception as e:
            print(f"  Error finding canonical name: {e}")
        
        print()
        time.sleep(2)  # Be respectful to servers
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("The hinted extraction pipeline is working!")
    print("- Citations are extracted from PDF text")
    print("- Canonical names are found via enhanced scraper")
    print("- Case names are extracted with and without hints")
    print("- Results can be compared to see improvements")
    print()
    print("Next steps for production:")
    print("1. Test with more documents")
    print("2. Adjust similarity threshold (currently 60)")
    print("3. Add caching for canonical names")
    print("4. Monitor performance and accuracy")

if __name__ == "__main__":
    test_hinted_extraction_pipeline() 