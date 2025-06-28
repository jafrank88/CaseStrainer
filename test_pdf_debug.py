#!/usr/bin/env python3

import re
import logging
from src.document_processing import process_document
import sys
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pdf_citation_extraction():
    print("Testing PDF citation extraction...")
    
    # Test the specific PDF
    url = 'https://www.courts.wa.gov/opinions/pdf/1029764.pdf'
    
    try:
        from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
        from src.complex_citation_integration import process_text_with_complex_citations
        
        print(f"Processing URL: {url}")
        
        # First, let's test the complex citation processing directly
        print("\n=== Testing complex citation processing directly ===")
        verifier = EnhancedMultiSourceVerifier()
        
        # Get the text first
        from src.enhanced_validator_production import extract_text_from_url
        text_result = extract_text_from_url(url)
        text = text_result.get('text', '')
        print(f"Extracted text length: {len(text)} characters")
        
        # Test complex citation processing on the entire text
        complex_results_data = process_text_with_complex_citations(text, verifier)
        complex_results = complex_results_data.get('results', [])
        print(f"Complex citation processing returned {len(complex_results)} results")
        
        if complex_results:
            print("Sample complex results:")
            for i, result in enumerate(complex_results[:3], 1):
                print(f"  {i}. Citation: {result.get('citation', 'N/A')}")
                print(f"     Verified: {result.get('verified', 'N/A')}")
                print(f"     Case name: {result.get('case_name', 'N/A')}")
        else:
            print("No complex results found!")
        
        # Now test the full process_document
        print("\n=== Testing full process_document ===")
        result = process_document(url=url, extract_case_names=True)
        
        print(f"\nResults:")
        print(f"Success: {result.get('success', 'N/A')}")
        print(f"Total citations: {len(result.get('citations', []))}")
        
        if result.get('citations'):
            print("\nSample citations:")
            for i, citation in enumerate(result.get('citations', [])[:5], 1):
                print(f"  {i}. {citation.get('citation', 'N/A')} (verified={citation.get('verified', 'N/A')})")
                if citation.get('case_name'):
                    print(f"     Case: {citation.get('case_name')}")
        else:
            print("No citations found in final result!")
            
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

def test_citation_filtering():
    """Test the citation filtering logic"""
    print("\nTesting citation filtering logic...")
    
    # Sample citations that might be extracted
    test_citations = [
        "410 U.S. 113",
        "93 S. Ct. 705", 
        "35 L. Ed. 2d 147",
        "1973 U.S. LEXIS 159",
        "Roe v. Wade",
        "410 U.S. 113, 93 S. Ct. 705",
        "410 U.S. 113, 93 S. Ct. 705, 35 L. Ed. 2d 147"
    ]
    
    def is_probable_legal_citation(citation_text):
        # Loosened pattern: number + reporter + number, allow extra numbers, commas, parentheses
        return bool(re.search(r"\b\d+\s+[A-Za-z\. ]+\s+\d+([,\s\d\(\)\.]*)\b", citation_text))
    
    print("Citation filtering test:")
    for citation in test_citations:
        is_valid = is_probable_legal_citation(citation)
        print(f"  '{citation}' -> {'VALID' if is_valid else 'FILTERED OUT'}")

if __name__ == "__main__":
    test_citation_filtering()
    test_pdf_citation_extraction() 