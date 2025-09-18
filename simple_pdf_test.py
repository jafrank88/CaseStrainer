#!/usr/bin/env python3
"""
Simple test to check PDF extraction and basic citation detection
"""

import sys
import os
import requests
import re
from io import BytesIO

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from optimized_pdf_processor import OptimizedPDFProcessor

def simple_pdf_test():
    """Simple test of the PDF that's not working"""
    url = "https://www.courts.wa.gov/opinions/pdf/400611_pub.pdf"
    
    print(f"Testing PDF: {url}")
    print("=" * 60)
    
    # Download PDF
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        print(f"✓ Downloaded PDF ({len(response.content)} bytes)")
    except Exception as e:
        print(f"✗ Download failed: {e}")
        return
    
    # Extract text
    try:
        pdf_processor = OptimizedPDFProcessor()
        
        temp_pdf_path = "temp_simple.pdf"
        with open(temp_pdf_path, 'wb') as f:
            f.write(response.content)
        
        result = pdf_processor.process_pdf(temp_pdf_path)
        
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
        
        if not result or not result.text:
            print("✗ No text extracted")
            return
            
        text = result.text
        print(f"✓ Extracted {len(text)} characters")
        print(f"Processor: {result.processor}")
        print(f"Confidence: {result.confidence}")
        
        # Show sample
        print("\nFirst 300 characters:")
        print("-" * 30)
        print(text[:300])
        print("-" * 30)
        
        # Look for citations with simple regex
        citation_patterns = [
            (r'\b\d+\s+Wn\.?\s*(?:2d|App\.?\s*2d)?\s+\d+', 'Washington'),
            (r'\b\d+\s+U\.?S\.?\s+\d+', 'US Supreme Court'),
            (r'\b\d+\s+P\.?\s*(?:2d|3d)\s+\d+', 'Pacific Reporter'),
            (r'\b\d+\s+F\.?\s*(?:2d|3d)?\s+\d+', 'Federal Reporter')
        ]
        
        print(f"\nCitation Analysis:")
        total_found = 0
        
        for pattern, name in citation_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            print(f"{name}: {len(matches)} found")
            if matches:
                for match in matches[:3]:  # Show first 3
                    print(f"  - {match}")
            total_found += len(matches)
        
        print(f"\nTotal potential citations: {total_found}")
        
        if total_found == 0:
            print("\n⚠️  No citations found with basic regex patterns")
            print("This could indicate:")
            print("1. PDF text extraction issues")
            print("2. Unusual citation formatting")
            print("3. Scanned/image-based PDF")
            
            # Look for any numbers that might be citations
            number_patterns = re.findall(r'\b\d+\s+[A-Z][a-z]*\.?\s*\d+', text)
            if number_patterns:
                print(f"\nPossible citation-like patterns found: {len(number_patterns)}")
                for pattern in number_patterns[:5]:
                    print(f"  - {pattern}")
        
    except Exception as e:
        print(f"✗ Processing failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simple_pdf_test()
