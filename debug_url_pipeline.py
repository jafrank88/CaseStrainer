#!/usr/bin/env python3
"""
Debug script to test the URL processing pipeline step by step.
This will help identify where the process is failing for the Washington court PDF.
"""

import sys
import os
import tempfile
import requests
import time

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.enhanced_validator_production import extract_text_from_url
from src.citation_processor import CitationProcessor

def test_url_pipeline(url):
    """Test the URL processing pipeline step by step."""
    print(f"\n{'='*60}")
    print(f"TESTING URL PIPELINE: {url}")
    print(f"{'='*60}")
    
    # Step 1: Test URL download and text extraction
    print("\n1. Testing URL download and text extraction...")
    start_time = time.time()
    
    text_result = extract_text_from_url(url)
    elapsed_time = time.time() - start_time
    
    print(f"   Time taken: {elapsed_time:.2f} seconds")
    print(f"   Status: {text_result.get('status', 'unknown')}")
    
    if text_result.get('status') == 'success':
        text = text_result.get('text', '')
        print(f"   Text length: {len(text)} characters")
        print(f"   Content type: {text_result.get('content_type', 'unknown')}")
        
        # Show first 500 characters
        if text:
            print(f"   First 500 characters:")
            print(f"   {'-'*40}")
            print(text[:500])
            print(f"   {'-'*40}")
            
            # Step 2: Test citation extraction
            print("\n2. Testing citation extraction...")
            citation_processor = CitationProcessor()
            
            # Extract citations from the text
            citations = citation_processor.extract_citations(text)
            print(f"   Found {len(citations)} citations")
            
            if citations:
                print("   Citations found:")
                for i, citation in enumerate(citations[:10], 1):  # Show first 10
                    print(f"   {i}. {citation}")
                if len(citations) > 10:
                    print(f"   ... and {len(citations) - 10} more")
            else:
                print("   No citations found!")
                
                # Let's try a simple regex test
                print("\n3. Testing simple citation regex...")
                import re
                
                # Common citation patterns
                patterns = [
                    r'\b\d+\s+U\.S\.\s+\d+',  # U.S. Supreme Court
                    r'\b\d+\s+S\.Ct\.\s+\d+',  # Supreme Court Reporter
                    r'\b\d+\s+F\.\d+\s+\d+',   # Federal Reporter
                    r'\b\d+\s+F\.Supp\.\s+\d+', # Federal Supplement
                    r'\b\d+\s+Wn\.\d+\s+\d+',  # Washington Reports
                    r'\b\d+\s+P\.\d+\s+\d+',   # Pacific Reporter
                    r'\b\d+\s+N\.W\.\d+\s+\d+', # Northwestern Reporter
                    r'\b\d+\s+N\.E\.\d+\s+\d+', # Northeastern Reporter
                    r'\b\d+\s+S\.E\.\d+\s+\d+', # Southeastern Reporter
                    r'\b\d+\s+Cal\.\d+\s+\d+',  # California Reports
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        print(f"   Pattern {pattern}: {len(matches)} matches")
                        for match in matches[:3]:  # Show first 3 matches
                            print(f"     - {match}")
        else:
            print("   ERROR: No text extracted!")
            
    else:
        error = text_result.get('error', 'Unknown error')
        print(f"   ERROR: {error}")
        if 'details' in text_result:
            print(f"   Details: {text_result['details']}")

def test_local_pdf():
    """Test with a local copy of the PDF if available."""
    local_pdf = "1029764.pdf"
    if os.path.exists(local_pdf):
        print(f"\n{'='*60}")
        print(f"TESTING LOCAL PDF: {local_pdf}")
        print(f"{'='*60}")
        
        from src.file_utils import extract_text_from_file
        
        print("\n1. Testing local PDF text extraction...")
        start_time = time.time()
        
        text_result, case_name = extract_text_from_file(local_pdf)
        elapsed_time = time.time() - start_time
        
        print(f"   Time taken: {elapsed_time:.2f} seconds")
        print(f"   Text length: {len(text_result) if isinstance(text_result, str) else 0} characters")
        print(f"   Case name: {case_name}")
        
        if isinstance(text_result, str) and not text_result.startswith("Error:"):
            print(f"   First 500 characters:")
            print(f"   {'-'*40}")
            print(text_result[:500])
            print(f"   {'-'*40}")
            
            # Test citation extraction
            print("\n2. Testing citation extraction from local PDF...")
            citation_processor = CitationProcessor()
            citations = citation_processor.extract_citations(text_result)
            print(f"   Found {len(citations)} citations")
            
            if citations:
                print("   Citations found:")
                for i, citation in enumerate(citations[:10], 1):
                    print(f"   {i}. {citation}")
            else:
                print("   No citations found!")

if __name__ == "__main__":
    url = "https://www.courts.wa.gov/opinions/pdf/1029764.pdf"
    
    # Test URL pipeline
    test_url_pipeline(url)
    
    # Test local PDF if available
    test_local_pdf()
    
    print(f"\n{'='*60}")
    print("DEBUG COMPLETE")
    print(f"{'='*60}") 