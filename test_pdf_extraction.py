#!/usr/bin/env python3
"""Test UnifiedTextExtractor directly on the downloaded PDF"""

import requests
import os
from src.unified_text_extractor import extract_text_from_file_unified

def test_direct_extraction():
    """Test extraction directly with UnifiedTextExtractor"""
    
    pdf_url = "https://www.courts.wa.gov/opinions/pdf/1031351.pdf"
    
    print(f"Downloading PDF: {pdf_url}")
    
    # Download PDF
    try:
        response = requests.get(pdf_url, timeout=30, verify=False)
        response.raise_for_status()
        
        # Save to temp file
        temp_file = "d:\\dev\\casestrainer\\temp_test_1031351.pdf"
        with open(temp_file, 'wb') as f:
            f.write(response.content)
        
        print(f"Downloaded {len(response.content)} bytes")
        
    except Exception as e:
        print(f"Error downloading PDF: {e}")
        return False
    
    # Test extraction
    print("\nTesting UnifiedTextExtractor...")
    try:
        text, method = extract_text_from_file_unified(temp_file, verbose=True)
        
        print(f"Extraction method: {method}")
        print(f"Text length: {len(text)} characters")
        
        # Check for citations in the text
        import re
        citation_patterns = [
            r'\d+\s+Wn\.2d\s+\d+',
            r'\d+\s+F\.3d\s+\d+',
            r'\d+\s+F\.2d\s+\d+',
            r'\d+\s+U\.S\.\s+\d+',
            r'\d+\s+S\. Ct\.\s+\d+'
        ]
        
        citations_found = []
        for pattern in citation_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            citations_found.extend(matches)
        
        print(f"\nFound {len(citations_found)} potential citations:")
        for i, citation in enumerate(citations_found[:10], 1):
            print(f"  {i}. {citation}")
        
        # Show first 500 chars of text
        print(f"\nFirst 500 characters of extracted text:")
        print(text[:500])
        
        return len(citations_found) > 0
        
    except Exception as e:
        print(f"Extraction error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up
        try:
            os.remove(temp_file)
            print(f"\nCleaned up temp file")
        except:
            pass

if __name__ == "__main__":
    success = test_direct_extraction()
    if success:
        print("\nSUCCESS: UnifiedTextExtractor works!")
    else:
        print("\nFAILED: UnifiedTextExtractor has issues")
