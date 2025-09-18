#!/usr/bin/env python3
"""
Debug script to test PDF URL processing for:
https://www.courts.wa.gov/opinions/pdf/400611_pub.pdf
"""

import sys
import os
import requests
import asyncio
from io import BytesIO

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from optimized_pdf_processor import OptimizedPDFProcessor
from unified_citation_processor_v2 import UnifiedCitationProcessorV2

def test_pdf_url():
    """Test the specific PDF URL that's not working"""
    url = "https://www.courts.wa.gov/opinions/pdf/400611_pub.pdf"
    
    print(f"Testing PDF URL: {url}")
    print("=" * 80)
    
    # Step 1: Download the PDF
    print("Step 1: Downloading PDF...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        print(f"✓ Downloaded PDF successfully ({len(response.content)} bytes)")
    except Exception as e:
        print(f"✗ Failed to download PDF: {e}")
        return
    
    # Step 2: Extract text from PDF
    print("\nStep 2: Extracting text from PDF...")
    try:
        pdf_processor = OptimizedPDFProcessor()
        
        # Save PDF to temporary file for processing
        temp_pdf_path = "temp_debug.pdf"
        with open(temp_pdf_path, 'wb') as f:
            f.write(response.content)
        
        result = pdf_processor.process_pdf(temp_pdf_path)
        extracted_text = result.text if result else ""
        
        # Clean up temp file
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
        
        if extracted_text:
            print(f"✓ Extracted text successfully ({len(extracted_text)} characters)")
            print(f"First 500 characters:")
            print("-" * 40)
            print(extracted_text[:500])
            print("-" * 40)
        else:
            print("✗ No text extracted from PDF")
            return
    except Exception as e:
        print(f"✗ Failed to extract text from PDF: {e}")
        return
    
    # Step 3: Look for potential citations in the text
    print("\nStep 3: Looking for potential citations in text...")
    
    # Simple regex patterns to look for citations
    import re
    
    # Washington citations
    wa_pattern = r'\b\d+\s+Wn\.?\s*(?:2d|App\.?\s*2d)?\s+\d+'
    wa_matches = re.findall(wa_pattern, extracted_text, re.IGNORECASE)
    
    # US citations
    us_pattern = r'\b\d+\s+U\.?S\.?\s+\d+'
    us_matches = re.findall(us_pattern, extracted_text, re.IGNORECASE)
    
    # Federal citations
    fed_pattern = r'\b\d+\s+F\.?\s*(?:2d|3d)?\s+\d+'
    fed_matches = re.findall(fed_pattern, extracted_text, re.IGNORECASE)
    
    # P.2d/P.3d citations
    p_pattern = r'\b\d+\s+P\.?\s*(?:2d|3d)\s+\d+'
    p_matches = re.findall(p_pattern, extracted_text, re.IGNORECASE)
    
    print(f"Washington citations found: {len(wa_matches)}")
    if wa_matches:
        for match in wa_matches[:5]:  # Show first 5
            print(f"  - {match}")
    
    print(f"US citations found: {len(us_matches)}")
    if us_matches:
        for match in us_matches[:5]:
            print(f"  - {match}")
    
    print(f"Federal citations found: {len(fed_matches)}")
    if fed_matches:
        for match in fed_matches[:5]:
            print(f"  - {match}")
    
    print(f"Pacific citations found: {len(p_matches)}")
    if p_matches:
        for match in p_matches[:5]:
            print(f"  - {match}")
    
    # Step 4: Test with CaseStrainer's citation processor
    print("\nStep 4: Testing with CaseStrainer's citation processor...")
    try:
        processor = UnifiedCitationProcessorV2()
        result = asyncio.run(processor.process_text(extracted_text))
        
        print(f"Citations found by processor: {len(result.get('citations', []))}")
        
        if result.get('citations'):
            print("Citations found:")
            for i, citation in enumerate(result['citations'][:10]):  # Show first 10
                print(f"  {i+1}. {citation.get('full_citation', 'N/A')}")
                if citation.get('extracted_case_name'):
                    print(f"      Case: {citation['extracted_case_name']}")
        else:
            print("No citations found by processor")
            
        # Check for any errors
        if result.get('errors'):
            print(f"Errors: {result['errors']}")
            
    except Exception as e:
        print(f"✗ Error with citation processor: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_url()
