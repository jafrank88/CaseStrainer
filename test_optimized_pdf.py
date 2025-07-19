#!/usr/bin/env python3
"""
Test script to benchmark optimized PDF extraction performance.
"""

import os
import sys
import time
import tempfile
import requests

# Add src to path
sys.path.insert(0, 'src')

from document_processing_unified import extract_text_from_pdf_optimized, benchmark_extraction_methods

def download_test_pdf():
    """Download a test PDF for benchmarking."""
    url = "https://www.courts.wa.gov/opinions/pdf/1029101.pdf"
    
    print(f"Downloading test PDF from: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(response.content)
            temp_path = f.name
        
        print(f"Downloaded {len(response.content)} bytes to: {temp_path}")
        return temp_path
        
    except Exception as e:
        print(f"Error downloading PDF: {e}")
        return None

def test_optimized_extraction():
    """Test the optimized PDF extraction."""
    print("=== Testing Optimized PDF Extraction ===")
    
    # Download test PDF
    pdf_path = download_test_pdf()
    if not pdf_path:
        print("Failed to download test PDF")
        return
    
    try:
        # Test optimized extraction
        print("\n--- Testing Optimized Extraction ---")
        start_time = time.time()
        
        text = extract_text_from_pdf_optimized(pdf_path)
        
        extraction_time = time.time() - start_time
        
        print(f"✅ Optimized extraction completed in {extraction_time:.2f} seconds")
        print(f"📄 Extracted {len(text)} characters")
        print(f"📊 Text preview: {text[:200]}...")
        
        # Benchmark against other methods
        print("\n--- Benchmarking Methods ---")
        results = benchmark_extraction_methods(pdf_path)
        
        for method, result in results.items():
            if 'error' in result:
                print(f"❌ {method}: {result['error']}")
            else:
                print(f"✅ {method}: {result['time']:.2f}s, {result['length']} chars, success={result['success']}")
        
        # Check for citations in extracted text
        citation_indicators = ['U.S.', 'S.Ct.', 'L.Ed.', 'F.', 'Wn.', 'Wash.']
        found_citations = []
        
        for indicator in citation_indicators:
            if indicator in text:
                found_citations.append(indicator)
        
        print(f"\n📋 Citation indicators found: {found_citations}")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        try:
            os.unlink(pdf_path)
            print(f"\n🧹 Cleaned up temporary file: {pdf_path}")
        except:
            pass

if __name__ == "__main__":
    test_optimized_extraction() 